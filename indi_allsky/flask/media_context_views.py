"""Hybrid-owned media history, loop controls and recorded storage usage.

Classic compatibility pages reuse these contexts without owning their queries.
"""
import math
from datetime import datetime
from flask import request
from flask_login import login_required
from sqlalchemy import Integer, and_, cast, desc, func, literal_column, or_
from sqlalchemy import null as sa_null
from ..modern_admin_camera_diagnostics import ModernAdminAduHistoryPolicy
from . import db
from .base_views import TemplateView
from .forms import IndiAllskyLoopHistoryForm
from .models import (
    IndiAllSkyDbCameraTable, IndiAllSkyDbImageTable, IndiAllSkyDbFitsImageTable,
    IndiAllSkyDbRawImageTable, IndiAllSkyDbPanoramaImageTable,
    IndiAllSkyDbPanoramaVideoTable, IndiAllSkyDbVideoTable,
    IndiAllSkyDbStarTrailsVideoTable, IndiAllSkyDbThumbnailTable,
)


class HybridAduHistoryContextView(TemplateView):
    page_title = 'Historical ADU'
    decorators = [login_required]

    def get_context(self):
        context = super(HybridAduHistoryContextView, self).get_context()


        timestamp = int(request.args.get('timestamp', 0))
        ts_dt_minus_7d, ts_dt = ModernAdminAduHistoryPolicy().window_bounds(
            timestamp, self.camera_now, self.camera_time_offset,
        )


        if db.engine.dialect.name == 'mysql':
            createDate_s = func.unix_timestamp(IndiAllSkyDbImageTable.createDate)  # mysql

            # this should give us average exposure, adu in 15 minute sets, during the night
            rolling_adu_q = IndiAllSkyDbImageTable.query\
                .add_columns(
                    func.floor(createDate_s / 900).label('interval'),
                    IndiAllSkyDbImageTable.createDate.label('dt'),
                    func.count(IndiAllSkyDbImageTable.id).label('i_count'),
                    func.avg(IndiAllSkyDbImageTable.exposure).label('exposure_avg'),
                    func.avg(IndiAllSkyDbImageTable.adu).label('adu_avg'),
                    func.avg(IndiAllSkyDbImageTable.sqm).label('jsqm_avg'),
                    func.avg(IndiAllSkyDbImageTable.stars).label('stars_avg'),
                )\
                .join(IndiAllSkyDbImageTable.camera)\
                .filter(IndiAllSkyDbCameraTable.id == self.camera.id)\
                .filter(
                    and_(
                        IndiAllSkyDbImageTable.createDate < ts_dt,
                        IndiAllSkyDbImageTable.createDate > ts_dt_minus_7d,
                        or_(
                            IndiAllSkyDbImageTable.createDate_hour >= 22,  # night is normally between 10p and 4a, right?
                            IndiAllSkyDbImageTable.createDate_hour <= 4,
                        )
                    )
                )\
                .group_by('interval')\
                .order_by(desc('interval'))

        elif db.engine.dialect.name == 'postgresql':
            createDate_s = func.to_char(IndiAllSkyDbImageTable.createDate, '%s')  # postgres
            # fixme
        else:
            # assume sqlite
            createDate_s = cast(func.strftime('%s', IndiAllSkyDbImageTable.createDate), Integer)  # sqlite

            # this should give us average exposure, adu in 15 minute sets, during the night
            rolling_adu_q = IndiAllSkyDbImageTable.query\
                .add_columns(
                    IndiAllSkyDbImageTable.createDate.label('dt'),
                    func.count(IndiAllSkyDbImageTable.id).label('i_count'),
                    func.avg(IndiAllSkyDbImageTable.exposure).label('exposure_avg'),
                    func.avg(IndiAllSkyDbImageTable.adu).label('adu_avg'),
                    func.avg(IndiAllSkyDbImageTable.sqm).label('jsqm_avg'),
                    func.avg(IndiAllSkyDbImageTable.stars).label('stars_avg'),
                )\
                .join(IndiAllSkyDbImageTable.camera)\
                .filter(IndiAllSkyDbCameraTable.id == self.camera.id)\
                .filter(
                    and_(
                        IndiAllSkyDbImageTable.createDate < ts_dt,
                        IndiAllSkyDbImageTable.createDate > ts_dt_minus_7d,
                        or_(
                            IndiAllSkyDbImageTable.createDate_hour >= 22,  # night is normally between 10p and 4a, right?
                            IndiAllSkyDbImageTable.createDate_hour <= 4,
                        )
                    )
                )\
                .group_by(cast(createDate_s / 900, Integer))\
                .order_by(IndiAllSkyDbImageTable.createDate.desc())  # cast is slightly faster than floor


        context['rolling_adu_q'] = rolling_adu_q

        return context


class HybridLoopContextView(TemplateView):
    page_title = 'Loop'
    image_loop_view = 'indi_allsky.js_image_loop_view'

    def get_context(self):
        context = super(HybridLoopContextView, self).get_context()

        context['image_loop_view'] = self.image_loop_view

        context['timestamp'] = int(request.args.get('timestamp', 0))

        refreshInterval_ms = math.ceil(self.indi_allsky_config.get('CCD_EXPOSURE_MAX', 15.0)) * 1000
        context['refreshInterval'] = refreshInterval_ms + 1000  # additional time for exposures to download

        context['form_history'] = IndiAllskyLoopHistoryForm()

        return context


class HybridFileSpaceContextView(TemplateView):
    decorators = [login_required]

    page_title = 'File Space Usage'

    def get_context(self):
        context = super(HybridFileSpaceContextView, self).get_context()


        total_size = 0
        total_count = 0
        file_data_dict = dict()


        ### images
        days_fileSize_images = self.get_table_fileSize(IndiAllSkyDbImageTable, self.camera.id)
        image_total_size, image_total_count = self.update_dict(file_data_dict, days_fileSize_images, 'Images')
        total_size += image_total_size
        total_count += image_total_count


        ### panorama images
        days_fileSize_panorama_images = self.get_table_fileSize_nothumbs(IndiAllSkyDbPanoramaImageTable, self.camera.id)
        panorama_image_total_size, panorama_image_total_count = self.update_dict(file_data_dict, days_fileSize_panorama_images, 'Panoramas')
        total_size += panorama_image_total_size
        total_count += panorama_image_total_count


        ### timelapse videos
        days_fileSize_videos = self.get_table_fileSize_nothumbs(IndiAllSkyDbVideoTable, self.camera.id)
        videos_total_size, videos_total_count = self.update_dict(file_data_dict, days_fileSize_videos, 'Timelapses')
        total_size += videos_total_size
        total_count += videos_total_count


        ### panorama timelapses
        days_fileSize_panorama_videos = self.get_table_fileSize_nothumbs(IndiAllSkyDbPanoramaVideoTable, self.camera.id)
        panorama_videos_total_size, panorama_videos_total_count = self.update_dict(file_data_dict, days_fileSize_panorama_videos, 'Panorama Timelapses')
        total_size += panorama_videos_total_size
        total_count += panorama_videos_total_count


        # keograms are not a significant usage of sapce
        ### keograms
        #days_fileSize_keograms = self.get_table_fileSize_nothumbs(IndiAllSkyDbKeogramTable, self.camera.id)
        #keograms_total_size, keograms_total_count = self.update_dict(file_data_dict, days_fileSize_keograms, 'Keograms')
        #total_size += keograms_total_size
        #total_count += keograms_total_count


        # startrails are not a significant usage of sapce
        ### star trails
        #days_fileSize_startrails = self.get_table_fileSize_nothumbs(IndiAllSkyDbStarTrailsTable, self.camera.id)
        #startrails_total_size, startrails_total_count = self.update_dict(file_data_dict, days_fileSize_startrails, 'Star Trails')
        #total_size += startrails_total_size
        #total_count += startrails_total_count


        ### star trail timelapses
        days_fileSize_startrail_videos = self.get_table_fileSize_nothumbs(IndiAllSkyDbStarTrailsVideoTable, self.camera.id)
        startrail_videos_total_size, startrail_videos_total_count = self.update_dict(file_data_dict, days_fileSize_startrail_videos, 'Star Trail Timelapses')
        total_size += startrail_videos_total_size
        total_count += startrail_videos_total_count


        ### fits
        days_fileSize_fits = self.get_table_fileSize_nothumbs(IndiAllSkyDbFitsImageTable, self.camera.id)
        fits_total_size, fits_total_count = self.update_dict(file_data_dict, days_fileSize_fits, 'FITS')
        total_size += fits_total_size
        total_count += fits_total_count


        ### raw images
        days_fileSize_raw = self.get_table_fileSize_nothumbs(IndiAllSkyDbRawImageTable, self.camera.id)
        raw_total_size, raw_total_count = self.update_dict(file_data_dict, days_fileSize_raw, 'Raw Images')
        total_size += raw_total_size
        total_count += raw_total_count


        #app.logger.info('Data: %s', str(file_data_dict))

        context['days_fileSize_dict'] = file_data_dict


        return context


    def get_table_fileSize(self, table, camera_id):
        days_fileSize = db.session.query(
            func.distinct(table.dayDate).label('dayDate_distinct'),
            func.sum(table.fileSize).label('dayDate_sum'),
            table.night,
            func.count(table.id).label('file_count'),
            func.sum(IndiAllSkyDbThumbnailTable.fileSize).label('thumbnail_sum'),
            func.count(IndiAllSkyDbThumbnailTable.id).label('thumbnail_count'),
        )\
            .join(table.camera)\
            .outerjoin(IndiAllSkyDbThumbnailTable, IndiAllSkyDbThumbnailTable.uuid == table.thumbnail_uuid)\
            .filter(IndiAllSkyDbCameraTable.id == camera_id)\
            .filter(table.fileSize != sa_null())\
            .group_by(table.dayDate, table.night)\
            .order_by(table.dayDate.desc())

        return days_fileSize


    def get_table_fileSize_nothumbs(self, table, camera_id):
        days_fileSize = db.session.query(
            func.distinct(table.dayDate).label('dayDate_distinct'),
            func.sum(table.fileSize).label('dayDate_sum'),
            table.night,
            func.count(table.id).label('file_count'),
            literal_column('0').label('thumbnail_sum'),  # simulate data
            literal_column('0').label('thumbnail_count'),  # simulate data
        )\
            .join(table.camera)\
            .filter(IndiAllSkyDbCameraTable.id == camera_id)\
            .filter(table.fileSize != sa_null())\
            .group_by(table.dayDate, table.night)\
            .order_by(table.dayDate.desc())


        return days_fileSize


    def update_dict(self, file_dict, fileSize_query, label):
        total_size = 0
        total_count = 0


        for day in fileSize_query:
            day_size = 0
            day_count = 0

            if db.engine.dialect.name == 'mysql':
                # mysql returns a date object
                dayDate = day.dayDate_distinct
            else:
                # sqlite returns a string
                dayDate = datetime.strptime(day.dayDate_distinct, '%Y-%m-%d').date()


            dayDate_str = dayDate.strftime('%Y-%m-%d')


            if not file_dict.get(dayDate_str):
                file_dict[dayDate_str] = dict()


            if day.night:
                tod = 'Night'
            else:
                tod = 'Day'


            if not file_dict[dayDate_str].get(tod):
                file_dict[dayDate_str][tod] = {
                    'tod_fileSize' : 0,
                    'tod_count'    : 0,
                }


            # ensure initial 0 values for all types
            for x in ['Images', 'Panoramas', 'Timelapses', 'Panorama Timelapses', 'Keograms', 'Star Trails', 'Star Trail Timelapses', 'FITS', 'Raw Images', 'Thumbnails']:
                if not file_dict[dayDate_str][tod].get(x):
                    file_dict[dayDate_str][tod][x] = {
                        'fileSize' : 0,
                        'count'    : 0,
                    }


            file_data = {
                'fileSize' : day.dayDate_sum if day.dayDate_sum else 0,
                'count'    : day.file_count,
            }


            thumbnail_sum = day.thumbnail_sum if day.thumbnail_sum else 0
            thumbnail_count = day.thumbnail_count


            file_dict[dayDate_str][tod][label] = file_data
            file_dict[dayDate_str][tod]['Thumbnails']['fileSize'] += thumbnail_sum
            file_dict[dayDate_str][tod]['Thumbnails']['count'] += thumbnail_count


            day_size += file_data['fileSize']
            day_size += thumbnail_sum

            day_count += file_data['count']
            day_count += thumbnail_count


            # totals for time of day
            file_dict[dayDate_str][tod]['tod_fileSize'] += day_size
            file_dict[dayDate_str][tod]['tod_count'] += day_count


            # add to total
            total_size += file_dict[dayDate_str][tod]['tod_fileSize']
            total_count += file_dict[dayDate_str][tod]['tod_count']


        return total_size, total_count
