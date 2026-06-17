import os
from datetime import datetime
from datetime import timedelta
from datetime import timezone
import io
import tempfile
import json
from collections import OrderedDict
import time
import math
import base64
from pathlib import Path
import socket
import ipaddress
import re
import psutil
import dbus
import ephem
from pprint import pformat  # noqa: F401

from passlib.hash import argon2

from ..version import __version__
from .. import constants
from ..processing import ImageProcessor

from cryptography.fernet import InvalidToken

from flask import request
from flask import session
from flask import jsonify
from flask import Blueprint
from flask import redirect
from flask import flash
from flask import Response
from flask import url_for
from flask import send_from_directory
from flask import send_file
from flask import current_app as app

from flask_login import login_required
from flask_login import current_user

from .misc import login_optional_media

from . import db

from .models import IndiAllSkyDbCameraTable
from .models import IndiAllSkyDbImageTable
from .models import IndiAllSkyDbVideoTable
from .models import IndiAllSkyDbMiniVideoTable
from .models import IndiAllSkyDbKeogramTable
from .models import IndiAllSkyDbStarTrailsTable
from .models import IndiAllSkyDbStarTrailsVideoTable
from .models import IndiAllSkyDbDarkFrameTable
from .models import IndiAllSkyDbBadPixelMapTable
from .models import IndiAllSkyDbRawImageTable
from .models import IndiAllSkyDbFitsImageTable
from .models import IndiAllSkyDbPanoramaImageTable
from .models import IndiAllSkyDbPanoramaVideoTable
from .models import IndiAllSkyDbLongTermKeogramTable
from .models import IndiAllSkyDbThumbnailTable
from .models import IndiAllSkyDbTaskQueueTable
from .models import IndiAllSkyDbNotificationTable
from .models import IndiAllSkyDbUserTable
from .models import IndiAllSkyDbConfigTable
from .models import IndiAllSkyDbTleDataTable

from .models import TaskQueueQueue
from .models import TaskQueueState
from .models import NotificationCategory

from sqlalchemy import func
from sqlalchemy import literal_column
#from sqlalchemy import extract
from sqlalchemy import desc
from sqlalchemy import cast
from sqlalchemy import and_
from sqlalchemy import or_
#from sqlalchemy.types import DateTime
from sqlalchemy.types import Integer
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.sql.expression import true as sa_true
from sqlalchemy.sql.expression import false as sa_false
from sqlalchemy.sql.expression import null as sa_null

from .forms import IndiAllskyConfigForm
from .forms import IndiAllskyImageViewer
from .forms import IndiAllskyImageViewerPreload
from .forms import IndiAllskyFitsImageViewer
from .forms import IndiAllskyFitsImageViewerPreload
from .forms import IndiAllskyGalleryViewer
from .forms import IndiAllskyGalleryViewerPreload
from .forms import IndiAllskyVideoViewer
from .forms import IndiAllskyVideoViewerPreload
from .forms import IndiAllskyMiniVideoViewer
from .forms import IndiAllskyMiniVideoViewerPreload
from .forms import IndiAllskySystemInfoForm
from .forms import IndiAllskyLoopHistoryForm
from .forms import IndiAllskyChartHistoryForm
from .forms import IndiAllskySetDateTimeForm
from .forms import IndiAllskySetTimezoneForm
from .forms import IndiAllskyTimelapseGeneratorForm
from .forms import IndiAllskyFocusForm
from .forms import IndiAllskyLogViewerForm
from .forms import IndiAllskyUserInfoForm
from .forms import IndiAllskyImageExcludeForm
from .forms import IndiAllskyImageProcessingForm
from .forms import IndiAllskyCameraSimulatorForm
from .forms import IndiAllskyFocusControllerForm
from .forms import IndiAllskyMiniTimelapseForm
from .forms import IndiAllskyLongTermKeogramForm
from .forms import IndiAllskyNetworkManagerForm
from .forms import IndiAllskyDriveManagerForm
from .forms import IndiAllskyImageCircleHelperForm
from .forms import IndiAllskyVirtualSkyHelperForm
from .forms import IndiAllskyConfigRestoreForm
from .forms import IndiAllskyIndiServerChangeForm

from .base_views import BaseView
from .base_views import TemplateView
from .base_views import FormView
from .base_views import JsonView

from .youtube_views import YoutubeAuthorizeView
from .youtube_views import YoutubeCallbackView
from .youtube_views import YoutubeRefreshAuthView
from .youtube_views import YoutubeRevokeAuthView

from ..exceptions import ConfigSaveException
from ..exceptions import NotFound


bp_allsky = Blueprint(
    'indi_allsky',
    __name__,
    template_folder='templates',
    static_folder='static',
    #url_prefix='/',  # wsgi
    url_prefix='/indi-allsky',  # gunicorn
    static_url_path='static',
)


class AjaxStatusUpdateView(BaseView):
    methods = ['GET']

    def dispatch_request(self):
        camera_id = int(request.args['camera_id'])


        self.cameraSetup(camera_id=camera_id)

        # query the latest image entry
        camera_now_minus_15m = self.camera_now - timedelta(minutes=15)
        self.latest_image_entry = db.session.query(
            IndiAllSkyDbImageTable,
        )\
            .join(IndiAllSkyDbImageTable.camera)\
            .filter(IndiAllSkyDbCameraTable.id == self.camera.id)\
            .filter(IndiAllSkyDbImageTable.createDate > camera_now_minus_15m)\
            .order_by(IndiAllSkyDbImageTable.createDate.desc())\
            .first()


        status_data = dict()
        status_data.update(self.get_indi_allsky_status())
        status_data.update(self.get_camera_info())
        status_data.update(self.get_astrometric_info())
        status_data.update(self.get_smoke_info())
        status_data.update(self.get_aurora_info())
        status_data.update(self.get_image_data())


        status_data['uptime'] = int(time.time() - psutil.boot_time())
        status_data['uptime_str'] = self.getUptime()


        data = {
            'status_text' : self.get_status_text(status_data) + self.get_web_extra_text(),
        }

        return jsonify(data)


class IndexCanvasView(TemplateView):
    page_title = 'Latest'
    latest_image_view = 'indi_allsky.js_latest_image_view'


    def get_context(self):
        context = super(IndexCanvasView, self).get_context()

        context['latest_image_view'] = self.latest_image_view

        refreshInterval_ms = math.ceil(self.indi_allsky_config.get('CCD_EXPOSURE_MAX', 15.0)) * 1000
        context['refreshInterval'] = refreshInterval_ms + 1000  # additional time for exposures to download

        return context


class JsonLatestImageView(JsonView):
    model = IndiAllSkyDbImageTable
    latest_image_t = 'images/latest.{0}'


    def __init__(self, **kwargs):
        super(JsonLatestImageView, self).__init__(**kwargs)

        self.history_seconds = 900


    def get_objects(self):
        camera_id = int(request.args['camera_id'])
        history_seconds = int(request.args.get('limit_s', self.history_seconds))
        night = bool(int(request.args.get('night', 1)))

        # sanity check
        if history_seconds > 86400:
            history_seconds = 86400


        self.cameraSetup(camera_id=camera_id)


        no_image_message = 'No Image for 15 minutes'


        if self.web_nonlocal_images:
            no_image_message += '<br>(Non-local images enabled)'


        data = {
            'latest_image' : {
                'url'     : None,
                'message' : no_image_message,
                'width'   : 1,
                'height'  : 1,
            },
        }


        if self.indi_allsky_config.get('FOCUS_MODE', False):
            latest_image_uri = Path('images/latest.{0}'.format(self.indi_allsky_config.get('IMAGE_FILE_TYPE', 'jpg')))

            image_dir = Path(self.indi_allsky_config['IMAGE_FOLDER']).absolute()
            latest_image_p = image_dir.joinpath(latest_image_uri.name)

            if latest_image_p.exists():
                # use latest image if it exists
                max_age = self.camera_now - timedelta(seconds=history_seconds)
                if latest_image_p.stat().st_mtime > max_age.timestamp():

                    data['latest_image']['url'] = '{0:s}?{1:d}'.format(str(latest_image_uri), int(datetime.timestamp(self.camera_now)))
                    data['latest_image']['message'] = ''
                    return data
                else:
                    return data
            else:
                return data


        if self.capture_pause:
            data['latest_image']['message'] = 'Capture paused'
            return data


        if not night:
            ### day
            if not self.local_indi_allsky and self.daytime_capture and not self.daytime_capture_save:
                # remote cameras will not receive daytime images when save is disabled
                if self.sun_set_date:
                    utcnow = datetime.now(tz=timezone.utc)
                    delta_sun_set = self.sun_set_date - utcnow.replace(tzinfo=None)
                    data['latest_image']['message'] = 'Daytime capture disabled.<br><div class="text-warning">Night starts in {0:0.1f} hours.</div>'.format(delta_sun_set.total_seconds() / 3600)
                else:
                    data['latest_image']['message'] = 'Daytime capture disabled.<br><div class="text-warning">Sun never sets.</div>'

                return data
            elif not self.daytime_capture:
                if self.sun_set_date:
                    utcnow = datetime.now(tz=timezone.utc)
                    delta_sun_set = self.sun_set_date - utcnow.replace(tzinfo=None)
                    data['latest_image']['message'] = 'Daytime capture disabled.<br><div class="text-warning">Night starts in {0:0.1f} hours.</div>'.format(delta_sun_set.total_seconds() / 3600)
                else:
                    data['latest_image']['message'] = 'Daytime capture disabled.<br><div class="text-warning">Sun never sets.</div>'

            elif self.daytime_capture and not self.daytime_capture_save:
                if self.web_nonlocal_images:
                    if not self.verify_admin_network():
                        # only show locally hosted assets if coming from admin networks
                        return data

                # images are not stored in the DB in this condition
                latest_image_uri = Path(self.latest_image_t.format(self.indi_allsky_config.get('IMAGE_FILE_TYPE', 'jpg')))

                image_dir = Path(self.indi_allsky_config['IMAGE_FOLDER']).absolute()
                latest_image_p = image_dir.joinpath(latest_image_uri.name)


                if not latest_image_p.exists():
                    return data


                # use latest image if it exists
                data['latest_image']['url'] = '{0:s}?{1:d}'.format(str(latest_image_uri), int(time.time()))

                max_age = self.camera_now - timedelta(seconds=history_seconds)
                if latest_image_p.stat().st_mtime > max_age.timestamp():
                    data['latest_image']['message'] = ''
                else:
                    data['latest_image']['message'] = 'Image is out of date'

                return data


        # use database
        latest_image_data = self.getLatestImage(camera_id, history_seconds)
        if latest_image_data.get('url'):
            data['latest_image']['url'] = latest_image_data['url']
            data['latest_image']['width'] = latest_image_data['width']
            data['latest_image']['height'] = latest_image_data['height']
            data['latest_image']['message'] = ''


        return data


    def getLatestImage(self, camera_id, history_seconds):
        camera_now_minus_seconds = self.camera_now - timedelta(seconds=history_seconds)

        latest_image_q = self.model.query\
            .join(self.model.camera)\
            .filter(
                and_(
                    IndiAllSkyDbCameraTable.id == camera_id,
                    self.model.createDate > camera_now_minus_seconds,
                )
            )


        local = True  # default to local assets
        if self.web_nonlocal_images:
            if self.web_local_images_admin and self.verify_admin_network():
                pass
            else:
                local = False

                # Do not serve local assets
                latest_image_q = latest_image_q\
                    .filter(
                        or_(
                            self.model.remote_url != sa_null(),
                            self.model.s3_key != sa_null(),
                        )
                    )


        latest_image = latest_image_q\
            .order_by(self.model.createDate.desc())\
            .first()


        if not latest_image:
            return {'url': None}


        try:
            url = latest_image.getUrl(s3_prefix=self.s3_prefix, local=local)
        except ValueError as e:
            app.logger.error('Error determining relative file name: %s', str(e))
            return {'url': None}


        image_data = {
            'url' : str(url),
            'width' : latest_image.width,
            'height' : latest_image.height,
        }

        return image_data


class IndexImgView(TemplateView):
    page_title = 'Latest'
    latest_image_view = 'indi_allsky.js_latest_image_view'


    def get_context(self):
        context = super(IndexImgView, self).get_context()

        context['latest_image_view'] = self.latest_image_view

        refreshInterval_ms = math.ceil(self.indi_allsky_config.get('CCD_EXPOSURE_MAX', 15.0)) * 1000
        context['refreshInterval'] = refreshInterval_ms + 1000  # additional time for exposures to download

        return context


class VirtualSkyView(TemplateView):
    page_title = 'VirtualSky'
    image_loop_view = 'indi_allsky.js_image_loop_view'


    def get_context(self):
        context = super(VirtualSkyView, self).get_context()

        context['image_loop_view'] = self.image_loop_view


        timestamp = int(request.args.get('timestamp', 0))
        context['timestamp'] = timestamp


        data = {
            'AZIMUTH_ANGLE'         : self.camera.az,
            'IMAGE_CIRCLE_DIAMETER' : self.camera.data.get('vs_image_circle_diameter', 3500),
            'LATITUDE_OFFSET'       : self.camera.data.get('vs_latitude_offset', 0.0),
            'LONGITUDE_OFFSET'      : self.camera.data.get('vs_longitude_offset', 0.0),
            'OFFSET_X'              : self.camera.data.get('vs_offset_x', 0.0),
            'OFFSET_Y'              : self.camera.data.get('vs_offset_y', 0.0),
            'MAGNITUDE'             : self.camera.data.get('vs_magnitude', 6.0),
            'CONSTELLATIONS'        : self.camera.data.get('vs_constellations', True),
            'CONSTELLATIONLABELS'   : self.camera.data.get('vs_constellationlabels', False),
            'SHOWSTARS'             : self.camera.data.get('vs_showstars', True),
            'SHOWSTARLABELS'        : self.camera.data.get('vs_showstarlabels', True),
            'SHOWPLANETS'           : self.camera.data.get('vs_showplanets', True),
            'SHOWPLANETLABELS'      : self.camera.data.get('vs_showplanetlabels', True),
            #'FLIP_NS'               : self.camera.data.get('vs_flip_ns', False),
            #'FLIP_EW'               : self.camera.data.get('vs_flip_ew', False),
        }

        context['form_virtualsky'] = IndiAllskyVirtualSkyHelperForm(data=data)


        refreshInterval_ms = math.ceil(self.indi_allsky_config.get('CCD_EXPOSURE_MAX', 15.0)) * 1000
        context['refreshInterval'] = refreshInterval_ms + 1000  # additional time for exposures to download


        ### Camera DB settings
        if self.indi_allsky_config.get('PRIVACY_MODE'):
            # reduce precision for privacy
            context['camera_latitude'] = float(round(self.camera.latitude))
            context['camera_longitude'] = float(round(self.camera.longitude))
        else:
            context['camera_latitude'] = self.camera.latitude
            context['camera_longitude'] = self.camera.longitude


        ### Calculate time offset
        context['time_offset'] = self.camera.utc_offset - datetime.now().astimezone().utcoffset().total_seconds()


        return context


class RealtimeKeogramView(TemplateView):
    page_title = 'Realtime Keogram'


    def get_context(self):
        context = super(RealtimeKeogramView, self).get_context()

        context['keogram_uri'] = str(Path('images').joinpath('ccd_{0:s}'.format(self.camera.uuid), 'realtime_keogram.{0:s}'.format(self.indi_allsky_config.get('IMAGE_FILE_TYPE', 'jpg'))))

        refreshInterval_ms = math.ceil(self.indi_allsky_config.get('CCD_EXPOSURE_MAX', 15.0)) * 1000
        context['refreshInterval'] = refreshInterval_ms + 1000  # additional time for exposures to download

        return context


class LatestImageRedirect(BaseView):
    model = IndiAllSkyDbImageTable


    def dispatch_request(self):
        camera_id = int(request.args.get('camera_id', 0))
        night = request.args.get('night')  # can be None

        if not camera_id:
            camera = self.getLatestCamera()
            camera_id = camera.id


        self.cameraSetup(camera_id=camera_id)


        local = True
        if self.web_nonlocal_images:
            local = False


        image_entry = self.getLatestImage(camera_id, night=night)


        image_url = image_entry.getUrl(s3_prefix=self.s3_prefix, local=local)


        return redirect(image_url, code=302)


    def getLatestImage(self, camera_id, night=None):
        if isinstance(night, type(None)):
            latest_image_entry = self.model.query\
                .join(self.model.camera)\
                .filter(IndiAllSkyDbCameraTable.id == camera_id)\
                .order_by(self.model.createDate.desc())\
                .first()
        else:
            # filter based on night
            night_bool = bool(int(night))

            latest_image_entry = self.model.query\
                .join(self.model.camera)\
                .filter(IndiAllSkyDbCameraTable.id == camera_id)\
                .filter(self.model.night == night_bool)\
                .order_by(self.model.createDate.desc())\
                .first()


        return latest_image_entry


class LatestKeogramRedirect(LatestImageRedirect):
    model = IndiAllSkyDbKeogramTable


class LatestStartrailRedirect(LatestImageRedirect):
    model = IndiAllSkyDbStarTrailsTable


class LatestPanoramaImageRedirect(LatestImageRedirect):
    model = IndiAllSkyDbPanoramaImageTable


class LatestRawImageRedirect(LatestImageRedirect):
    model = IndiAllSkyDbRawImageTable


class LatestThumbnailRedirect(LatestImageRedirect):

    def getLatestImage(self, camera_id):
        latest_image_thumbnail_entry = db.session.query(
            IndiAllSkyDbImageTable,
            IndiAllSkyDbThumbnailTable,
        )\
            .join(IndiAllSkyDbImageTable.camera)\
            .join(IndiAllSkyDbThumbnailTable, IndiAllSkyDbImageTable.thumbnail_uuid == IndiAllSkyDbThumbnailTable.uuid)\
            .filter(IndiAllSkyDbCameraTable.id == camera_id)\
            .order_by(IndiAllSkyDbImageTable.createDate.desc())\
            .first()

        _, latest_thumbnail_entry = latest_image_thumbnail_entry

        return latest_thumbnail_entry


class LatestTimelapseVideoRedirect(BaseView):
    model = IndiAllSkyDbVideoTable

    def dispatch_request(self):
        camera_id = int(request.args.get('camera_id', 0))
        night = request.args.get('night')  # can be None


        if not camera_id:
            camera = self.getLatestCamera()
            camera_id = camera.id


        self.cameraSetup(camera_id=camera_id)


        local = True
        if self.web_nonlocal_images:
            local = False


        video_entry = self.getLatestVideo(camera_id, night=night)


        video_url = video_entry.getUrl(s3_prefix=self.s3_prefix, local=local)


        return redirect(video_url, code=302)


    def getLatestVideo(self, camera_id, night=None):
        if isinstance(night, type(None)):
            latest_video_entry = self.model.query\
                .join(self.model.camera)\
                .filter(IndiAllSkyDbCameraTable.id == camera_id)\
                .order_by(self.model.dayDate.desc())\
                .first()
        else:
            # filter based on night
            night_bool = bool(int(night))

            latest_video_entry = self.model.query\
                .join(self.model.camera)\
                .filter(IndiAllSkyDbCameraTable.id == camera_id)\
                .filter(self.model.night == night_bool)\
                .order_by(self.model.dayDate.desc())\
                .first()

        return latest_video_entry


class LatestStartrailVideoRedirect(LatestTimelapseVideoRedirect):
    model = IndiAllSkyDbStarTrailsVideoTable


class LatestPanoramaVideoRedirect(LatestTimelapseVideoRedirect):
    model = IndiAllSkyDbPanoramaVideoTable


class LatestImageViewRedirect(BaseView):
    model = IndiAllSkyDbImageTable
    view_view = 'indi_allsky.timelapse_image_view'


    def dispatch_request(self):
        camera_id = int(request.args.get('camera_id', 0))
        night = request.args.get('night')  # can be None


        if not camera_id:
            camera = self.getLatestCamera()
            camera_id = camera.id


        self.cameraSetup(camera_id=camera_id)


        image_entry = self.getLatestImage(camera_id, night=night)


        view_url = url_for(self.view_view, id=image_entry.id)


        return redirect(view_url, code=302)


    def getLatestImage(self, camera_id, night=None):
        if isinstance(night, type(None)):
            latest_image_entry = self.model.query\
                .join(self.model.camera)\
                .filter(IndiAllSkyDbCameraTable.id == camera_id)\
                .order_by(self.model.createDate.desc())\
                .first()
        else:
            # filter based on night
            night_bool = bool(int(night))

            latest_image_entry = self.model.query\
                .join(self.model.camera)\
                .filter(IndiAllSkyDbCameraTable.id == camera_id)\
                .filter(self.model.night == night_bool)\
                .order_by(self.model.createDate.desc())\
                .first()


        return latest_image_entry


class LatestKeogramViewRedirect(LatestImageViewRedirect):
    model = IndiAllSkyDbKeogramTable
    view_view = 'indi_allsky.keogram_image_view'


class LatestStartrailViewRedirect(LatestImageViewRedirect):
    model = IndiAllSkyDbStarTrailsTable
    view_view = 'indi_allsky.startrail_image_view'


class LatestPanoramaImageViewRedirect(LatestImageViewRedirect):
    model = IndiAllSkyDbPanoramaImageTable
    view_view = 'indi_allsky.panorama_image_view'


class LatestRawImageViewRedirect(LatestImageViewRedirect):
    model = IndiAllSkyDbRawImageTable
    view_view = 'indi_allsky.raw_image_view'


class LatestTimelapseVideoWatchRedirect(BaseView):
    model = IndiAllSkyDbVideoTable
    watch_view = 'indi_allsky.timelapse_video_view'


    def dispatch_request(self):
        camera_id = int(request.args.get('camera_id', 0))
        night = request.args.get('night')  # can be None


        if not camera_id:
            camera = self.getLatestCamera()
            camera_id = camera.id


        self.cameraSetup(camera_id=camera_id)


        video_entry = self.getLatestVideo(camera_id, night=night)


        view_url = url_for(self.watch_view, id=video_entry.id)


        return redirect(view_url, code=302)


    def getLatestVideo(self, camera_id, night=None):
        if isinstance(night, type(None)):
            latest_video_entry = self.model.query\
                .join(self.model.camera)\
                .filter(IndiAllSkyDbCameraTable.id == camera_id)\
                .order_by(self.model.dayDate.desc())\
                .first()
        else:
            # filter based on night
            night_bool = bool(int(night))

            latest_video_entry = self.model.query\
                .join(self.model.camera)\
                .filter(IndiAllSkyDbCameraTable.id == camera_id)\
                .filter(self.model.night == night_bool)\
                .order_by(self.model.dayDate.desc())\
                .first()


        return latest_video_entry


class LatestStartrailVideoWatchRedirect(LatestTimelapseVideoWatchRedirect):
    model = IndiAllSkyDbStarTrailsVideoTable
    watch_view = 'indi_allsky.startrail_video_view'


class LatestPanoramaVideoWatchRedirect(LatestTimelapseVideoWatchRedirect):
    model = IndiAllSkyDbPanoramaVideoTable
    watch_view = 'indi_allsky.panorama_video_view'


class LatestPanoramaCanvasView(IndexCanvasView):
    page_title = 'Panorama'
    latest_image_view = 'indi_allsky.js_latest_panorama_view'


class LatestPanoramaImgView(IndexImgView):
    page_title = 'Panorama'
    latest_image_view = 'indi_allsky.js_latest_panorama_view'


class JsonLatestPanoramaView(JsonLatestImageView):
    model = IndiAllSkyDbPanoramaImageTable
    latest_image_t = 'images/panorama.{0}'


class LatestRawImageCanvasView(IndexCanvasView):
    page_title = 'RAW Image'
    latest_image_view = 'indi_allsky.js_latest_rawimage_view'


class LatestRawImageImgView(IndexImgView):
    page_title = 'RAW Image'
    latest_image_view = 'indi_allsky.js_latest_rawimage_view'


class JsonLatestRawImageView(JsonLatestImageView):
    model = IndiAllSkyDbRawImageTable
    latest_image_t = 'na'


class PublicIndexView(BaseView):
    # Legacy redirect
    def dispatch_request(self):
        return redirect(url_for('indi_allsky.index_view'))


class MaskView(TemplateView):
    page_title = 'Mask Base'
    decorators = [login_required]

    def get_context(self):
        context = super(MaskView, self).get_context()

        mask_image_uri = Path('images/mask_base.png')

        context['mask_image_uri'] = str(mask_image_uri)


        image_dir = Path(self.indi_allsky_config['IMAGE_FOLDER']).absolute()
        mask_image_p = image_dir.joinpath(mask_image_uri.name)

        if mask_image_p.exists():
            mask_mtime = mask_image_p.stat().st_mtime
            mask_mtime_dt = datetime.fromtimestamp(mask_mtime)
            context['mask_date'] = mask_mtime_dt.strftime('%Y-%m-%d %H:%M:%S')
        else:
            context['mask_date'] = ''


        return context


class CamerasView(TemplateView):
    page_title = 'Cameras'
    decorators = [login_required]

    def get_context(self):
        context = super(CamerasView, self).get_context()

        context['camera_list'] = IndiAllSkyDbCameraTable.query\
            .all()

        return context


class DarkFramesView(TemplateView):
    page_title = 'Dark Frames'
    decorators = [login_required]

    def get_context(self):
        context = super(DarkFramesView, self).get_context()

        darkframe_list = IndiAllSkyDbDarkFrameTable.query\
            .join(IndiAllSkyDbCameraTable)\
            .filter(IndiAllSkyDbCameraTable.id == self.camera.id)\
            .order_by(
                IndiAllSkyDbCameraTable.id.desc(),
                IndiAllSkyDbDarkFrameTable.gain.asc(),
                IndiAllSkyDbDarkFrameTable.exposure.asc(),
            )

        bpm_list = IndiAllSkyDbBadPixelMapTable.query\
            .join(IndiAllSkyDbCameraTable)\
            .filter(IndiAllSkyDbCameraTable.id == self.camera.id)\
            .order_by(
                IndiAllSkyDbCameraTable.id.desc(),
                IndiAllSkyDbBadPixelMapTable.gain.asc(),
                IndiAllSkyDbBadPixelMapTable.exposure.asc(),
            )


        d_info_list = list()
        for d in darkframe_list:
            file_path = d.getFilesystemPath()

            try:
                file_size = file_path.stat().st_size
            except FileNotFoundError:
                file_size = 0

            d_info = {
                'id' : d.id,
                'camera_name'  : d.camera.name,
                'createDate'   : d.createDate,
                'active'       : d.active,
                'bitdepth'     : d.bitdepth,
                'gain'         : d.gain,
                'exposure'     : d.exposure,
                'binmode'      : d.binmode,
                'width'        : d.width,
                'height'       : d.height,
                'temp'         : d.temp,
                'adu'          : d.adu,
                'filename'     : d.filename,
                'url'          : d.getUrl(),
                'hot_pixels'   : d.data.get('hot_pixels', -1),
                'method'       : d.data.get('method', ''),
                'size_mb'      : file_size / 1024 / 1024,
            }

            d_info_list.append(d_info)


        b_info_list = list()
        for b in bpm_list:
            file_path = d.getFilesystemPath()

            try:
                file_size = file_path.stat().st_size
            except FileNotFoundError:
                file_size = 0

            b_info = {
                'id' : b.id,
                'camera_name'  : b.camera.name,
                'createDate'   : b.createDate,
                'active'       : b.active,
                'bitdepth'     : b.bitdepth,
                'gain'         : b.gain,
                'exposure'     : b.exposure,
                'binmode'      : b.binmode,
                'width'        : d.width,
                'height'       : d.height,
                'temp'         : b.temp,
                'adu'          : b.adu,
                'filename'     : b.filename,
                'url'          : b.getUrl(),
                'hot_pixels'   : d.data.get('hot_pixels', -1),
                'size_mb'      : file_size / 1024 / 1024,
            }

            b_info_list.append(b_info)


        context['darkframe_list'] = d_info_list
        context['bpm_list'] = b_info_list

        return context


class ImageLagView(TemplateView):
    page_title = 'Image Lag'
    decorators = [login_required]

    def get_context(self):
        context = super(ImageLagView, self).get_context()

        timestamp = int(request.args.get('timestamp', 0))
        if not timestamp:
            timestamp = int(datetime.timestamp(self.camera_now))


        ts_dt = datetime.fromtimestamp(timestamp) + timedelta(seconds=self.camera_time_offset)
        ts_dt_minus_3h = ts_dt - timedelta(hours=3)


        if db.engine.dialect.name == 'mysql':
            createDate_s = func.date_format('%s', IndiAllSkyDbImageTable.createDate)  # mysql
        elif db.engine.dialect.name == 'postgresql':
            createDate_s = func.to_char(IndiAllSkyDbImageTable.createDate, '%s')  # postgres
        else:
            # assume sqlite
            createDate_s = func.strftime('%s', IndiAllSkyDbImageTable.createDate)  # sqlite


        image_lag_q = IndiAllSkyDbImageTable.query\
            .add_columns(
                IndiAllSkyDbImageTable.id,
                IndiAllSkyDbImageTable.createDate,
                IndiAllSkyDbImageTable.exposure,
                IndiAllSkyDbImageTable.exp_elapsed,
                (IndiAllSkyDbImageTable.exp_elapsed - IndiAllSkyDbImageTable.exposure).label('delta'),
                IndiAllSkyDbImageTable.process_elapsed,
                (cast(createDate_s, Integer) - func.lag(createDate_s).over(order_by=IndiAllSkyDbImageTable.createDate)).label('lag_diff'),
            )\
            .join(IndiAllSkyDbImageTable.camera)\
            .filter(
                and_(
                    IndiAllSkyDbCameraTable.id == self.camera.id,
                    IndiAllSkyDbImageTable.createDate < ts_dt,
                    IndiAllSkyDbImageTable.createDate > ts_dt_minus_3h,
                )
            )\
            .order_by(IndiAllSkyDbImageTable.createDate.desc())\
            .limit(50)
        # filter is just to make it faster


        context['image_lag_q'] = image_lag_q

        return context


class RollingAduView(TemplateView):
    page_title = 'Historical ADU'
    decorators = [login_required]

    def get_context(self):
        context = super(RollingAduView, self).get_context()


        timestamp = int(request.args.get('timestamp', 0))
        if not timestamp:
            timestamp = int(datetime.timestamp(self.camera_now))


        ts_dt = datetime.fromtimestamp(timestamp) + timedelta(seconds=self.camera_time_offset)
        ts_dt_minus_7d = self.camera_now - timedelta(days=7)


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


class SqmView(TemplateView):
    page_title = 'SQM'

    def get_context(self):
        context = super(SqmView, self).get_context()

        refreshInterval_ms = math.ceil(self.indi_allsky_config.get('CCD_EXPOSURE_MAX', 15.0)) * 1000
        context['refreshInterval'] = refreshInterval_ms + 1000  # additional time for exposures to download

        return context


class ImageLoopCanvasView(TemplateView):
    page_title = 'Loop'
    image_loop_view = 'indi_allsky.js_image_loop_view'

    def get_context(self):
        context = super(ImageLoopCanvasView, self).get_context()

        context['image_loop_view'] = self.image_loop_view

        context['timestamp'] = int(request.args.get('timestamp', 0))

        refreshInterval_ms = math.ceil(self.indi_allsky_config.get('CCD_EXPOSURE_MAX', 15.0)) * 1000
        context['refreshInterval'] = refreshInterval_ms + 1000  # additional time for exposures to download

        context['form_history'] = IndiAllskyLoopHistoryForm()

        return context


class JsonImageLoopView(JsonView):
    model = IndiAllSkyDbImageTable

    def __init__(self, **kwargs):
        super(JsonImageLoopView, self).__init__(**kwargs)

        self.history_seconds = 900
        self.sqm_history_minutes = 30
        self.stars_history_minutes = 30
        self._limit = 1000  # sanity check


    def get_objects(self):
        history_seconds = int(request.args.get('limit_s', self.history_seconds))
        self.limit = int(request.args.get('limit', self._limit))
        timestamp = int(request.args.get('timestamp', 0))
        camera_id = int(request.args['camera_id'])

        self.cameraSetup(camera_id=camera_id)


        if not timestamp:
            timestamp = int(datetime.timestamp(self.camera_now))

        ts_dt = datetime.fromtimestamp(timestamp + 3)  # allow some jitter

        # sanity check, limit to 4 hours
        if history_seconds > 14400:
            history_seconds = 14400


        jsqm_data, camera_sqm_mag_data, camera_sqm_adu_data, device_sqm_mag_data = self.getSqmData(camera_id, ts_dt)

        data = {
            'message'    : '',
            'image_list' : self.getLoopImages(camera_id, ts_dt, history_seconds),
            'jsqm_data'  : jsqm_data,
            'stars_data' : self.getStarsData(camera_id, ts_dt),
            'camera_sqm_mag_data' : camera_sqm_mag_data,
            'camera_sqm_adu_data' : camera_sqm_adu_data,
            'device_sqm_mag_data' : device_sqm_mag_data,
        }

        if len(data['image_list']) == 0:
            data['message'] = 'No Timelapse Data'

        return data


    def getLoopImages(self, camera_id, loop_dt, history_seconds):
        ts_minus_seconds = loop_dt - timedelta(seconds=history_seconds)

        latest_images_q = self.model.query\
            .join(self.model.camera)\
            .filter(
                and_(
                    IndiAllSkyDbCameraTable.id == camera_id,
                    self.model.exclude == sa_false(),
                    self.model.createDate > ts_minus_seconds,
                    self.model.createDate < loop_dt,
                )
            )


        local = True  # default to local assets
        if self.web_nonlocal_images:
            if self.web_local_images_admin and self.verify_admin_network():
                pass
            else:
                local = False

                # Do not serve local assets
                latest_images_q = latest_images_q\
                    .filter(
                        or_(
                            self.model.remote_url != sa_null(),
                            self.model.s3_key != sa_null(),
                        )
                    )


        latest_images = latest_images_q\
            .order_by(self.model.createDate.desc())\
            .limit(self.limit)


        image_list = list()
        for i in latest_images:
            try:
                url = i.getUrl(s3_prefix=self.s3_prefix, local=local)
            except ValueError as e:
                app.logger.error('Error determining relative file name: %s', str(e))
                continue


            data = {
                'url'       : str(url),
                'width'     : i.width,
                'height'    : i.height,
                'timestamp' : int(i.createDate.timestamp()),
            }


            try:
                data['jsqm'] = i.sqm
                data['stars'] = i.stars
                data['detections'] = i.detections
            except AttributeError:
                # view is reused for panoramas
                data['jsqm'] = 0
                data['stars'] = 0
                data['detections'] = 0


            image_list.append(data)


        return image_list


    def getSqmData(self, camera_id, ts_dt):
        ts_minus_minutes = ts_dt - timedelta(minutes=self.sqm_history_minutes)

        sqm_images = self.model.query\
            .join(IndiAllSkyDbCameraTable)\
            .filter(
                and_(
                    IndiAllSkyDbCameraTable.id == camera_id,
                    self.model.exclude == sa_false(),
                    self.model.createDate > ts_minus_minutes,
                    self.model.createDate < ts_dt,
                )
            )\
            .order_by(self.model.createDate.desc())


        jsqm_list = list()
        camera_sqm_mag_list = list()
        camera_sqm_adu_list = list()
        device_sqm_mag_list = list()
        for i in sqm_images:
            try:
                jsqm = i.sqm
            except AttributeError:
                jsqm = 0


            jsqm_list.append(jsqm)
            camera_sqm_mag_list.append(i.data.get('sensor_user_8', 0.0))
            camera_sqm_adu_list.append(i.data.get('sensor_user_9', 0.0))
            device_sqm_mag_list.append(i.data.get('sensor_user_7', 0.0))


        try:
            jsqm_data = {
                'max'  : max(jsqm_list),
                'min'  : min(jsqm_list),
                'avg'  : sum(jsqm_list) / len(jsqm_list),
                'last' : jsqm_list[0],
            }

        except (ValueError, IndexError):
            # list is probably empty
            jsqm_data = {
                'max' : 0.0,
                'min' : 0.0,
                'avg' : 0.0,
                'last' : 0.0,
            }


        try:
            camera_sqm_mag_data = {
                'max'  : max(camera_sqm_mag_list),
                'min'  : min(camera_sqm_mag_list),
                'avg'  : sum(camera_sqm_mag_list) / len(camera_sqm_mag_list),
                'last' : camera_sqm_mag_list[0],
            }
        except (ValueError, IndexError):
            # list is probably empty
            camera_sqm_mag_data = {
                'max' : 0.0,
                'min' : 0.0,
                'avg' : 0.0,
                'last' : 0.0,
            }


        try:
            camera_sqm_adu_data = {
                'max'  : max(camera_sqm_adu_list),
                'min'  : min(camera_sqm_adu_list),
                'avg'  : sum(camera_sqm_adu_list) / len(camera_sqm_adu_list),
                'last' : camera_sqm_adu_list[0],
            }
        except (ValueError, IndexError):
            # list is probably empty
            camera_sqm_adu_data = {
                'max' : 0.0,
                'min' : 0.0,
                'avg' : 0.0,
                'last' : 0.0,
            }


        try:
            device_sqm_mag_data = {
                'max'  : max(device_sqm_mag_list),
                'min'  : min(device_sqm_mag_list),
                'avg'  : sum(device_sqm_mag_list) / len(device_sqm_mag_list),
                'last' : device_sqm_mag_list[0],
            }
        except (ValueError, IndexError):
            # list is probably empty
            device_sqm_mag_data = {
                'max' : 0.0,
                'min' : 0.0,
                'avg' : 0.0,
                'last' : 0.0,
            }


        return jsqm_data, camera_sqm_mag_data, camera_sqm_adu_data, device_sqm_mag_data


    def getStarsData(self, camera_id, ts_dt):
        ts_minus_minutes = ts_dt - timedelta(minutes=self.stars_history_minutes)

        stars_images = self.model.query\
            .add_columns(
                func.max(self.model.stars).label('image_max_stars'),
                func.min(self.model.stars).label('image_min_stars'),
                func.avg(self.model.stars).label('image_avg_stars'),
            )\
            .join(IndiAllSkyDbCameraTable)\
            .filter(
                and_(
                    IndiAllSkyDbCameraTable.id == camera_id,
                    self.model.exclude == sa_false(),
                    self.model.createDate > ts_minus_minutes,
                    self.model.createDate < ts_dt,
                )
            )\
            .first()


        stars_data = {
            'max' : stars_images.image_max_stars,
            'min' : stars_images.image_min_stars,
            'avg' : stars_images.image_avg_stars,
        }

        return stars_data


class ImageLoopImgView(TemplateView):
    page_title = 'Loop'
    image_loop_view = 'indi_allsky.js_image_loop_view'

    def get_context(self):
        context = super(ImageLoopImgView, self).get_context()

        context['image_loop_view'] = self.image_loop_view

        context['timestamp'] = int(request.args.get('timestamp', 0))

        refreshInterval_ms = math.ceil(self.indi_allsky_config.get('CCD_EXPOSURE_MAX', 15.0)) * 1000
        context['refreshInterval'] = refreshInterval_ms + 1000  # additional time for exposures to download

        context['form_history'] = IndiAllskyLoopHistoryForm()

        return context


class PanoramaLoopCanvasView(ImageLoopCanvasView):
    page_title = 'Panorama Loop'
    image_loop_view = 'indi_allsky.js_panorama_loop_view'


class PanoramaLoopImgView(ImageLoopImgView):
    page_title = 'Panorama Loop'
    image_loop_view = 'indi_allsky.js_panorama_loop_view'


class JsonPanoramaLoopView(JsonImageLoopView):
    model = IndiAllSkyDbPanoramaImageTable


    def getSqmData(self, *args):
        sqm_data = {
            'max'  : 0,
            'min'  : 0,
            'avg'  : 0,
            'last' : 0,
        }

        # jsqm, camera, device
        return sqm_data, sqm_data, sqm_data, sqm_data


    def getStarsData(self, *args):
        stars_data = {
            'max' : 0,
            'min' : 0,
            'avg' : 0,
        }

        return stars_data


class RawImageLoopCanvasView(ImageLoopCanvasView):
    page_title = 'RAW Image Loop'
    image_loop_view = 'indi_allsky.js_rawimage_loop_view'


class RawImageLoopImgView(ImageLoopImgView):
    page_title = 'RAW Image Loop'
    image_loop_view = 'indi_allsky.js_rawimage_loop_view'


class JsonRawImageLoopView(JsonImageLoopView):
    model = IndiAllSkyDbRawImageTable


    def getSqmData(self, *args):
        sqm_data = {
            'max'  : 0,
            'min'  : 0,
            'avg'  : 0,
            'last' : 0,
        }

        # jsqm, camera, device
        return sqm_data, sqm_data, sqm_data


    def getStarsData(self, *args):
        stars_data = {
            'max' : 0,
            'min' : 0,
            'avg' : 0,
        }

        return stars_data


class ChartView(TemplateView):
    page_title = 'Charts'

    def get_context(self):
        context = super(ChartView, self).get_context()

        context['timestamp'] = int(request.args.get('timestamp', 0))

        refreshInterval_ms = math.ceil(self.indi_allsky_config.get('CCD_EXPOSURE_MAX', 15.0)) * 1000
        context['refreshInterval'] = refreshInterval_ms + 1000  # additional time for exposures to download

        context['form_history'] = IndiAllskyChartHistoryForm()


        if self.camera.data:
            camera_data = dict(self.camera.data)
        else:
            camera_data = dict()


        custom_chart_1_key = camera_data.get('custom_chart_1_key', 'sensor_user_10')
        custom_chart_2_key = camera_data.get('custom_chart_2_key', 'sensor_user_11')
        custom_chart_3_key = camera_data.get('custom_chart_3_key', 'sensor_user_12')
        custom_chart_4_key = camera_data.get('custom_chart_4_key', 'sensor_user_13')
        custom_chart_5_key = camera_data.get('custom_chart_5_key', 'sensor_user_14')
        custom_chart_6_key = camera_data.get('custom_chart_6_key', 'sensor_user_15')
        custom_chart_7_key = camera_data.get('custom_chart_7_key', 'sensor_user_16')
        custom_chart_8_key = camera_data.get('custom_chart_8_key', 'sensor_user_17')
        custom_chart_9_key = camera_data.get('custom_chart_9_key', 'sensor_user_18')


        context['label_custom_chart_1'] = camera_data.get(custom_chart_1_key, 'Unset')
        context['min_custom_chart_1'] = camera_data.get('custom_chart_1_min', 0.0)
        context['label_custom_chart_2'] = camera_data.get(custom_chart_2_key, 'Unset')
        context['min_custom_chart_2'] = camera_data.get('custom_chart_2_min', 0.0)
        context['label_custom_chart_3'] = camera_data.get(custom_chart_3_key, 'Unset')
        context['min_custom_chart_3'] = camera_data.get('custom_chart_3_min', 0.0)
        context['label_custom_chart_4'] = camera_data.get(custom_chart_4_key, 'Unset')
        context['min_custom_chart_4'] = camera_data.get('custom_chart_4_min', 0.0)
        context['label_custom_chart_5'] = camera_data.get(custom_chart_5_key, 'Unset')
        context['min_custom_chart_5'] = camera_data.get('custom_chart_5_min', 0.0)
        context['label_custom_chart_6'] = camera_data.get(custom_chart_6_key, 'Unset')
        context['min_custom_chart_6'] = camera_data.get('custom_chart_6_min', 0.0)
        context['label_custom_chart_7'] = camera_data.get(custom_chart_7_key, 'Unset')
        context['min_custom_chart_7'] = camera_data.get('custom_chart_7_min', 0.0)
        context['label_custom_chart_8'] = camera_data.get(custom_chart_8_key, 'Unset')
        context['min_custom_chart_8'] = camera_data.get('custom_chart_8_min', 0.0)
        context['label_custom_chart_9'] = camera_data.get(custom_chart_9_key, 'Unset')
        context['min_custom_chart_9'] = camera_data.get('custom_chart_9_min', 0.0)


        return context


class JsonChartView(JsonView):
    def __init__(self, **kwargs):
        super(JsonChartView, self).__init__(**kwargs)

        self.chart_history_seconds = 900


    def get_objects(self):
        camera_id = int(request.args['camera_id'])
        history_seconds = int(request.args.get('limit_s', self.chart_history_seconds))
        timestamp = int(request.args.get('timestamp', 0))

        self.cameraSetup(camera_id=camera_id)

        if not timestamp:
            timestamp = int(datetime.timestamp(self.camera_now))

        ts_dt = datetime.fromtimestamp(timestamp + 3)  # allow some jitter

        # safety, limit history to 1 day
        if history_seconds > 86400:
            history_seconds = 86400

        data = {
            'chart_data' : self.getChartData(camera_id, ts_dt, history_seconds),
            'message' : '',
        }


        if len(data['chart_data']['jsqm']) == 0:
            data['message'] = 'No chart data in history range'


        return data


    def getChartData(self, camera_id, ts_dt, history_seconds):
        import numpy

        ts_minus_seconds = ts_dt - timedelta(seconds=history_seconds)

        chart_query = IndiAllSkyDbImageTable.query\
            .add_columns(
                IndiAllSkyDbImageTable.createDate,
                IndiAllSkyDbImageTable.sqm.label('jsqm'),
                func.avg(IndiAllSkyDbImageTable.stars).over(order_by=IndiAllSkyDbImageTable.createDate, rows=(-5, 0)).label('stars_rolling'),
                IndiAllSkyDbImageTable.temp,
                IndiAllSkyDbImageTable.gain,
                IndiAllSkyDbImageTable.exposure,
                IndiAllSkyDbImageTable.detections,
                #(IndiAllSkyDbImageTable.sqm - func.lag(IndiAllSkyDbImageTable.sqm).over(order_by=IndiAllSkyDbImageTable.createDate)).label('jsqm_diff'),
                IndiAllSkyDbImageTable.data,
            )\
            .join(IndiAllSkyDbCameraTable)\
            .filter(
                and_(
                    IndiAllSkyDbCameraTable.id == camera_id,
                    IndiAllSkyDbImageTable.createDate > ts_minus_seconds,
                    IndiAllSkyDbImageTable.createDate < ts_dt,
                )
            )\
            .order_by(IndiAllSkyDbImageTable.createDate.asc())


        #app.logger.info('Chart SQL: %s', str(chart_query))

        chart_data = {
            'jsqm'   : [],
            'jsqm_d' : [],
            'stars' : [],
            'temp'  : [],
            'gain'  : [],
            'exp'   : [],
            'detection' : [],
            'custom_1'  : [],
            'custom_2'  : [],
            'custom_3'  : [],
            'custom_4'  : [],
            'custom_5'  : [],
            'custom_6'  : [],
            'custom_7'  : [],
            'custom_8'  : [],
            'custom_9'  : [],
            'histogram' : {
                'red'   : [],
                'green' : [],
                'blue'  : [],
                'gray'  : [],
            },
        }


        if self.camera.data:
            camera_data = dict(self.camera.data)
        else:
            camera_data = dict()


        custom_chart_1_key = camera_data.get('custom_chart_1_key', 'sensor_user_10')
        custom_chart_2_key = camera_data.get('custom_chart_2_key', 'sensor_user_11')
        custom_chart_3_key = camera_data.get('custom_chart_3_key', 'sensor_user_12')
        custom_chart_4_key = camera_data.get('custom_chart_4_key', 'sensor_user_13')
        custom_chart_5_key = camera_data.get('custom_chart_5_key', 'sensor_user_14')
        custom_chart_6_key = camera_data.get('custom_chart_6_key', 'sensor_user_15')
        custom_chart_7_key = camera_data.get('custom_chart_7_key', 'sensor_user_16')
        custom_chart_8_key = camera_data.get('custom_chart_8_key', 'sensor_user_17')
        custom_chart_9_key = camera_data.get('custom_chart_9_key', 'sensor_user_18')


        for i in chart_query:
            x = i.createDate.strftime('%H:%M:%S')

            jsqm_data = {
                'x' : x,
                'y' : i.jsqm,
            }
            chart_data['jsqm'].append(jsqm_data)

            star_data = {
                'x' : x,
                'y' : int(i.stars_rolling),
            }
            chart_data['stars'].append(star_data)


            if self.indi_allsky_config.get('TEMP_DISPLAY') == 'f':
                sensortemp = ((i.temp * 9.0) / 5.0) + 32
            elif self.indi_allsky_config.get('TEMP_DISPLAY') == 'k':
                sensortemp = i.temp + 273.15
            else:
                sensortemp = i.temp

            temp_data = {
                'x' : x,
                'y' : sensortemp,
            }
            chart_data['temp'].append(temp_data)

            exp_data = {
                'x' : x,
                'y' : i.exposure,
            }
            chart_data['exp'].append(exp_data)

            gain_data = {
                'x' : x,
                'y' : i.gain,
            }
            chart_data['gain'].append(gain_data)

            #jsqm_d_data = {
            #    'x' : x,
            #    'y' : i.jsqm_diff,
            #}
            #chart_data['jsqm_d'].append(jsqm_d_data)


            if i.detections > 0:
                detection = 1
            else:
                detection = 0

            detection_data = {
                'x' : x,
                'y' : detection,
            }
            chart_data['detection'].append(detection_data)


            # custom chart 1
            try:
                custom_1_y = i.data[custom_chart_1_key]
            except KeyError:
                custom_1_y = 0

            custom_1_data = {
                'x' : x,
                'y' : custom_1_y,
            }
            chart_data['custom_1'].append(custom_1_data)


            # custom chart 2
            try:
                custom_2_y = i.data[custom_chart_2_key]
            except KeyError:
                custom_2_y = 0

            custom_2_data = {
                'x' : x,
                'y' : custom_2_y,
            }
            chart_data['custom_2'].append(custom_2_data)


            # custom chart 3
            try:
                custom_3_y = i.data[custom_chart_3_key]
            except KeyError:
                custom_3_y = 0

            custom_3_data = {
                'x' : x,
                'y' : custom_3_y,
            }
            chart_data['custom_3'].append(custom_3_data)


            # custom chart 4
            try:
                custom_4_y = i.data[custom_chart_4_key]
            except KeyError:
                custom_4_y = 0

            custom_4_data = {
                'x' : x,
                'y' : custom_4_y,
            }
            chart_data['custom_4'].append(custom_4_data)


            # custom chart 5
            try:
                custom_5_y = i.data[custom_chart_5_key]
            except KeyError:
                custom_5_y = 0

            custom_5_data = {
                'x' : x,
                'y' : custom_5_y,
            }
            chart_data['custom_5'].append(custom_5_data)


            # custom chart 6
            try:
                custom_6_y = i.data[custom_chart_6_key]
            except KeyError:
                custom_6_y = 0

            custom_6_data = {
                'x' : x,
                'y' : custom_6_y,
            }
            chart_data['custom_6'].append(custom_6_data)


            # custom chart 7
            try:
                custom_7_y = i.data[custom_chart_7_key]
            except KeyError:
                custom_7_y = 0

            custom_7_data = {
                'x' : x,
                'y' : custom_7_y,
            }
            chart_data['custom_7'].append(custom_7_data)


            # custom chart 8
            try:
                custom_8_y = i.data[custom_chart_8_key]
            except KeyError:
                custom_8_y = 0

            custom_8_data = {
                'x' : x,
                'y' : custom_8_y,
            }
            chart_data['custom_8'].append(custom_8_data)


            # custom chart 9
            try:
                custom_9_y = i.data[custom_chart_9_key]
            except KeyError:
                custom_9_y = 0

            custom_9_data = {
                'x' : x,
                'y' : custom_9_y,
            }
            chart_data['custom_9'].append(custom_9_data)


        # build last image histogram
        now_minus_seconds = ts_dt - timedelta(seconds=history_seconds)

        latest_image = IndiAllSkyDbImageTable.query\
            .join(IndiAllSkyDbImageTable.camera)\
            .filter(
                and_(
                    IndiAllSkyDbCameraTable.id == camera_id,
                    IndiAllSkyDbImageTable.createDate > now_minus_seconds,
                    IndiAllSkyDbImageTable.createDate < ts_dt,
                )
            )\
            .order_by(IndiAllSkyDbImageTable.createDate.desc())\
            .first()


        if not latest_image:
            return chart_data


        latest_image_p = latest_image.getFilesystemPath()
        if not latest_image_p.exists():
            app.logger.error('Image does not exist: %s', latest_image_p)
            return chart_data


        #image_start = time.time()


        if latest_image_p.suffix in ('.jpg', '.jpeg'):
            import simplejpeg

            try:
                with io.open(str(latest_image_p), 'rb') as f_img:
                    image_data = simplejpeg.decode_jpeg(f_img.read(), colorspace='BGR')
            except ValueError:
                app.logger.error('Unable to read %s', latest_image_p)
                return chart_data

        elif latest_image_p.suffix in ('.png', ):
            import cv2

            image_data = cv2.imread(str(latest_image_p), cv2.IMREAD_UNCHANGED)

            if isinstance(image_data, type(None)):
                app.logger.error('Unable to read %s', latest_image_p)
                return chart_data

        else:
            # pillow supports remaining types
            import cv2
            import PIL
            from PIL import Image

            try:
                with Image.open(str(latest_image_p)) as img_pil:
                    image_data = cv2.cvtColor(numpy.array(img_pil), cv2.COLOR_RGB2BGR)
            except PIL.UnidentifiedImageError:
                app.logger.error('Unable to read %s', latest_image_p)
                return chart_data


            app.logger.warning('Unsupported image format')
            return chart_data


        #image_elapsed_s = time.time() - image_start
        #app.logger.info('Image read in %0.4f s', image_elapsed_s)


        image_height, image_width = image_data.shape[:2]
        app.logger.info('Calculating histogram from RoI')

        #mask = numpy.zeros(image_data.shape[:2], numpy.uint8)
        numpy_mask = numpy.full(image_data.shape[:2], True, numpy.bool_)


        _sqm_mask = self._load_detection_mask(latest_image.binmode)


        if isinstance(_sqm_mask, type(None)):
            sqm_roi = self.indi_allsky_config.get('SQM_ROI', [])

            try:
                x1 = int(sqm_roi[0] / latest_image.binmode)
                y1 = int(sqm_roi[1] / latest_image.binmode)
                x2 = int(sqm_roi[2] / latest_image.binmode)
                y2 = int(sqm_roi[3] / latest_image.binmode)
            except IndexError:
                sqm_fov_div = self.indi_allsky_config.get('SQM_FOV_DIV', 4)
                x1 = int((image_width / 2) - (image_width / sqm_fov_div))
                y1 = int((image_height / 2) - (image_height / sqm_fov_div))
                x2 = int((image_width / 2) + (image_width / sqm_fov_div))
                y2 = int((image_height / 2) + (image_height / sqm_fov_div))


            #mask[y1:y2, x1:x2] = 255
            # True values will be masked
            numpy_mask[y1:y2, x1:x2] = False
        else:
            # True values will be masked
            numpy_mask = _sqm_mask == 0


        if len(image_data.shape) == 2:
            # mono
            #h_numpy = cv2.calcHist([image_data], [0], mask, [256], [0, 256])
            gray_ma = numpy.ma.masked_array(image_data, mask=numpy_mask)
            h_numpy = numpy.histogram(gray_ma.compressed(), bins=256, range=(0, 256))

            #for x, val in enumerate(h_numpy.tolist()):
            for x, val in enumerate(h_numpy[0].tolist()):
                h_data = {
                    'x' : str(x),
                    #'y' : val[0]
                    'y' : val,
                }
                chart_data['histogram']['gray'].append(h_data)

        else:
            # color
            color = ('blue', 'green', 'red')
            for i, col in enumerate(color):
                #h_numpy = cv2.calcHist([image_data], [i], mask, [256], [0, 256])
                col_ma = numpy.ma.masked_array(image_data[:, :, i], mask=numpy_mask)
                h_numpy = numpy.histogram(col_ma.compressed(), bins=256, range=(0, 256))

                #for x, val in enumerate(h_numpy.tolist()):
                for x, val in enumerate(h_numpy[0].tolist()):
                    h_data = {
                        'x' : str(x),
                        #'y' : val[0]
                        'y' : val,
                    }
                    chart_data['histogram'][col].append(h_data)


        return chart_data


class JsonSensorPanelView(JsonView):
    def __init__(self, **kwargs):
        super(JsonSensorPanelView, self).__init__(**kwargs)
        self.history_seconds = 900

    def get_objects(self):
        camera_id = int(request.args['camera_id'])

        # Setup camera context (needed for camera_now, db, etc.)
        self.cameraSetup(camera_id=camera_id)

        # Query latest image entry (same logic as TemplateView: last 15 min)
        camera_now_minus_15m = self.camera_now - timedelta(minutes=15)
        self.latest_image_entry = db.session.query(
            IndiAllSkyDbImageTable,
        )\
            .join(IndiAllSkyDbImageTable.camera)\
            .filter(IndiAllSkyDbCameraTable.id == self.camera.id)\
            .filter(IndiAllSkyDbImageTable.createDate > camera_now_minus_15m)\
            .order_by(IndiAllSkyDbImageTable.createDate.desc())\
            .first()

        data = self.get_image_data()

        # Pack values as arrays (index = slot number)
        sensor_user = [data.get(f'sensor_user_{i}', 0.0) for i in range(60)]
        sensor_temp = [data.get(f'sensor_temp_{i}', 0.0) for i in range(60)]

        if self.latest_image_entry:
            last_update = str(self.latest_image_entry.createDate)
            last_update_age_s = int((self.camera_now - self.latest_image_entry.createDate).total_seconds())
        else:
            last_update = None
            last_update_age_s = None

        return {
            'last_update': last_update,
            'last_update_age_s': last_update_age_s,
            'sensor_user': sensor_user,
            'sensor_temp': sensor_temp,
        }


class SensorPanelView(TemplateView):
    page_title = 'Sensor Panel'

    def get_context(self):
        context = super(SensorPanelView, self).get_context()

        # Use the latest image metadata as the "current" sensor values.
        # This updates at your exposure cadence, which is typically good enough for a live panel.
        image_data = self.get_image_data()

        if self.camera.data:
            camera_data = dict(self.camera.data)
        else:
            camera_data = dict()

        show_all = int(request.args.get('all', 0))

        # Build tables for user and temp sensor slots.
        user_rows = []
        temp_rows = []

        for i in range(60):
            key = f'sensor_user_{i}'
            label = camera_data.get(key, key)
            value = image_data.get(key, 0.0)

            default_label = f'User Slot {i}'
            if show_all or i < 10 or label != default_label or abs(value) > 0.0:
                user_rows.append({
                    'slot': key,
                    'index': i,
                    'label': label,
                    'value': value,
                })

        for i in range(60):
            key = f'sensor_temp_{i}'
            label = camera_data.get(key, key)
            value = image_data.get(key, 0.0)

            # Default naming in capture.py uses "Future Use" for 1..9.
            is_future_use = label.startswith('Future Use')

            if show_all or i == 0 or (not is_future_use) or abs(value) > 0.0:
                temp_rows.append({
                    'slot': key,
                    'index': i,
                    'label': label,
                    'value': value,
                })

        # Age of the "current" values
        if self.latest_image_entry:
            context['last_update'] = self.latest_image_entry.createDate
            context['last_update_age_s'] = int((self.camera_now - self.latest_image_entry.createDate).total_seconds())
        else:
            context['last_update'] = None
            context['last_update_age_s'] = None

        context['show_all'] = bool(show_all)
        context['refreshInterval'] = 5000  # ms
        context['user_rows'] = user_rows
        context['temp_rows'] = temp_rows

        return context


class ConfigView(FormView):
    page_title = 'Config'
    decorators = [login_required]

    def get_context(self):
        context = super(ConfigView, self).get_context()

        context['camera_minGain'] = self.camera.minGain
        context['camera_maxGain'] = self.camera.maxGain
        context['camera_minBinning'] = self.camera.minBinning
        context['camera_maxBinning'] = self.camera.maxBinning
        context['camera_minExposure'] = self.camera.minExposure

        if self.camera.maxExposure > 120:
            context['camera_maxExposure'] = 120
        else:
            context['camera_maxExposure'] = self.camera.maxExposure


        context['config_id'] = self.indi_allsky_config_id


        ### a few checks to start
        fits_enabled = self.indi_allsky_config.get('IMAGE_SAVE_FITS')
        fits_save_period = self.indi_allsky_config.get('IMAGE_SAVE_FITS_PERIOD', 7200)

        if fits_enabled and fits_save_period < 600:
            # Only warn if saving more often than every 10 minutes
            context['fits_enabled'] = fits_enabled


        context['mark_detections_enabled'] = self.indi_allsky_config.get('DETECT_DRAW')


        ### timezone validator
        if not self.validate_longitude_timezone():
            context['longitude_validation_message'] = '<span class="badge rounded-pill bg-warning text-dark">Warning</span><span class="text-warning"> Longitude validation failed.  Incorrect time, timezone, or longitude could cause this condition</span>'
        else:
            context['longitude_validation_message'] = ''


        if self.latest_image_entry:
            dh_level_default = self.indi_allsky_config.get('DEW_HEATER', {}).get('LEVEL_DEF', 0)
            dh_level_low = self.indi_allsky_config.get('DEW_HEATER', {}).get('LEVEL_LOW', 33)
            dh_level_med = self.indi_allsky_config.get('DEW_HEATER', {}).get('LEVEL_MED', 66)
            dh_level_high = self.indi_allsky_config.get('DEW_HEATER', {}).get('LEVEL_HIGH', 100)

            dh_thold_diff_low = self.indi_allsky_config.get('DEW_HEATER', {}).get('THOLD_DIFF_LOW', -15)
            dh_thold_diff_med = self.indi_allsky_config.get('DEW_HEATER', {}).get('THOLD_DIFF_MED', -10)
            dh_thold_diff_high = self.indi_allsky_config.get('DEW_HEATER', {}).get('THOLD_DIFF_HIGH', -5)


            fan_level_default = self.indi_allsky_config.get('FAN', {}).get('LEVEL_DEF', 0)
            fan_level_low = self.indi_allsky_config.get('FAN', {}).get('LEVEL_LOW', 33)
            fan_level_med = self.indi_allsky_config.get('FAN', {}).get('LEVEL_MED', 66)
            fan_level_high = self.indi_allsky_config.get('FAN', {}).get('LEVEL_HIGH', 100)

            fan_thold_diff_low = self.indi_allsky_config.get('FAN', {}).get('THOLD_DIFF_LOW', -10)
            fan_thold_diff_med = self.indi_allsky_config.get('FAN', {}).get('THOLD_DIFF_MED', -5)
            fan_thold_diff_high = self.indi_allsky_config.get('FAN', {}).get('THOLD_DIFF_HIGH', 0)


            dh_temp_slot_var = self.indi_allsky_config.get('DEW_HEATER', {}).get('TEMP_USER_VAR_SLOT', 'sensor_user_10')
            dh_dewpoint_slot_var = self.indi_allsky_config.get('DEW_HEATER', {}).get('DEWPOINT_USER_VAR_SLOT', 'sensor_user_2')

            fan_temp_slot_var = self.indi_allsky_config.get('FAN', {}).get('TEMP_USER_VAR_SLOT', 'sensor_user_10')


            raw_mag = self.latest_image_entry.data.get('camera_sqm_raw_mag', 0.0)
            if raw_mag:
                mag_offset = self.indi_allsky_config.get('CAMERA_SQM', {}).get('MAGNITUDE_OFFSET', 25.0)

                context['camera_sqm_raw_mag_str'] = '{0:0.2f}'.format(raw_mag)
                context['camera_sqm_calc_sqm_str'] = '{0:0.2f}'.format(mag_offset + raw_mag)  # raw_mag is negative
            else:
                context['camera_sqm_raw_mag_str'] = 'Not available'
                context['camera_sqm_calc_sqm_str'] = 'Not available'


            if self.latest_image_entry.data.get(dh_temp_slot_var):
                dh_temp = self.latest_image_entry.data[dh_temp_slot_var]
                context['dh_temp_str'] = '{0:0.1f}°'.format(dh_temp)
            else:
                dh_temp = None
                context['dh_temp_str'] = 'Not available'

            if self.latest_image_entry.data.get(dh_dewpoint_slot_var):
                dh_dewpoint = self.latest_image_entry.data[dh_dewpoint_slot_var]
                context['dh_dewpoint_str'] = '{0:0.1f}°'.format(dh_dewpoint)
            else:
                dh_dewpoint = None
                context['dh_dewpoint_str'] = 'Not available'


            dh_manual_target = self.indi_allsky_config.get('DEW_HEATER', {}).get('MANUAL_TARGET', 0.0)
            if not dh_manual_target:
                if not isinstance(dh_temp, type(None)) and not isinstance(dh_dewpoint, type(None)):
                    dh_temp_delta = dh_temp - dh_dewpoint
                    context['dh_temp_delta_str'] = 'Δ{0:+0.1f}°'.format(dh_temp_delta)

                    dh_target_low = dh_dewpoint + dh_thold_diff_low
                    dh_target_med = dh_dewpoint + dh_thold_diff_med
                    dh_target_high = dh_dewpoint + dh_thold_diff_high
                    context['dh_target_low_str'] = '{0:0.1f}°'.format(dh_target_low)
                    context['dh_target_med_str'] = '{0:0.1f}°'.format(dh_target_med)
                    context['dh_target_high_str'] = '{0:0.1f}°'.format(dh_target_high)


                    if dh_temp_delta <= dh_thold_diff_high:
                        # set dew heater to high
                        context['dh_status_str'] = '{0:d}% (High)'.format(dh_level_high)
                    elif dh_temp_delta <= dh_thold_diff_med:
                        # set dew heater to medium
                        context['dh_status_str'] = '{0:d}% (Medium)'.format(dh_level_med)
                    elif dh_temp_delta <= dh_thold_diff_low:
                        # set dew heater to low
                        context['dh_status_str'] = '{0:d}% (Low)'.format(dh_level_low)
                    else:
                        context['dh_status_str'] = '{0:d}% (Default)'.format(dh_level_default)

                else:
                    context['dh_temp_delta_str'] = 'Not available'
                    context['dh_target_low_str'] = 'n/a'
                    context['dh_target_med_str'] = 'n/a'
                    context['dh_target_high_str'] = 'n/a'
                    context['dh_status_str'] = 'n/a'
            else:
                if not isinstance(dh_temp, type(None)):
                    dh_temp_delta = dh_temp - dh_manual_target
                    context['dh_temp_delta_str'] = 'Δ{0:+0.1f}° (manual target)'.format(dh_temp_delta)

                    dh_target_low = dh_manual_target + dh_thold_diff_low
                    dh_target_med = dh_manual_target + dh_thold_diff_med
                    dh_target_high = dh_manual_target + dh_thold_diff_high
                    context['dh_target_low_str'] = '{0:0.1f}°'.format(dh_target_low)
                    context['dh_target_med_str'] = '{0:0.1f}°'.format(dh_target_med)
                    context['dh_target_high_str'] = '{0:0.1f}°'.format(dh_target_high)

                    if dh_temp_delta <= dh_thold_diff_high:
                        # set dew heater to high
                        context['dh_status_str'] = '{0:d}% (High)'.format(dh_level_high)
                    elif dh_temp_delta <= dh_thold_diff_med:
                        # set dew heater to medium
                        context['dh_status_str'] = '{0:d}% (Medium)'.format(dh_level_med)
                    elif dh_temp_delta <= dh_thold_diff_low:
                        # set dew heater to low
                        context['dh_status_str'] = '{0:d}% (Low)'.format(dh_level_low)
                    else:
                        context['dh_status_str'] = '{0:d}% (Default)'.format(dh_level_default)
                else:
                    context['dh_temp_delta_str'] = 'Not available'
                    context['dh_target_low_str'] = 'n/a'
                    context['dh_target_med_str'] = 'n/a'
                    context['dh_target_high_str'] = 'n/a'
                    context['dh_status_str'] = 'n/a'


            if self.latest_image_entry.data.get(fan_temp_slot_var):
                fan_temp = self.latest_image_entry.data[fan_temp_slot_var]
                context['fan_temp_str'] = '{0:0.1f}°'.format(fan_temp)
            else:
                fan_temp = None
                context['fan_temp_str'] = 'Not available'


            fan_target = self.indi_allsky_config.get('FAN', {}).get('TARGET', 30.0)
            if not isinstance(fan_temp, type(None)):
                fan_temp_delta = fan_temp - fan_target
                context['fan_temp_delta_str'] = 'Δ{0:+0.1f}°'.format(fan_temp_delta)

                fan_target_low = fan_target + fan_thold_diff_low
                fan_target_med = fan_target + fan_thold_diff_med
                fan_target_high = fan_target + fan_thold_diff_high
                context['fan_target_low_str'] = '{0:0.1f}°'.format(fan_target_low)
                context['fan_target_med_str'] = '{0:0.1f}°'.format(fan_target_med)
                context['fan_target_high_str'] = '{0:0.1f}°'.format(fan_target_high)


                if fan_temp_delta > fan_thold_diff_high:
                    # set fan to high
                    context['fan_status_str'] = '{0:d}% (High)'.format(fan_level_high)
                elif fan_temp_delta > fan_thold_diff_med:
                    # set fan to medium
                    context['fan_status_str'] = '{0:d}% (Medium)'.format(fan_level_med)
                elif fan_temp_delta > fan_thold_diff_low:
                    # set fan to low
                    context['fan_status_str'] = '{0:d}% (Low)'.format(fan_level_low)
                else:
                    context['fan_status_str'] = '{0:d}% (Default)'.format(fan_level_default)

            else:
                context['fan_temp_delta_str'] = 'Not available'
                context['fan_target_low_str'] = 'n/a'
                context['fan_target_med_str'] = 'n/a'
                context['fan_target_high_str'] = 'n/a'
                context['fan_status_str'] = 'n/a'
        else:
            context['camera_sqm_raw_mag_str'] = 'Not available'
            context['camera_sqm_calc_sqm_str'] = 'Not available'

            context['dh_temp_str'] = 'Not available'
            context['dh_dewpoint_str'] = 'Not available'
            context['dh_temp_delta_str'] = 'Not available'
            context['dh_target_low_str'] = 'n/a'
            context['dh_target_med_str'] = 'n/a'
            context['dh_target_high_str'] = 'n/a'
            context['dh_status_str'] = 'n/a'

            context['fan_temp_str'] = 'Not available'
            context['fan_temp_delta_str'] = 'Not available'
            context['fan_target_low_str'] = 'n/a'
            context['fan_target_med_str'] = 'n/a'
            context['fan_target_high_str'] = 'n/a'
            context['fan_status_str'] = 'n/a'


        form_data = {
            'CAMERA_INTERFACE'               : self.indi_allsky_config.get('CAMERA_INTERFACE', 'indi'),
            'INDI_SERVER'                    : self.indi_allsky_config.get('INDI_SERVER', 'localhost'),
            'INDI_PORT'                      : self.indi_allsky_config.get('INDI_PORT', 7624),
            'INDI_CAMERA_NAME'               : self.indi_allsky_config.get('INDI_CAMERA_NAME', ''),
            'WEBSITE__TITLE'                 : self.indi_allsky_config.get('WEBSITE', {}).get('TITLE', 'indi-allsky'),
            'OWNER'                          : self.indi_allsky_config.get('OWNER', ''),
            'LENS_NAME'                      : self.indi_allsky_config.get('LENS_NAME', 'AllSky Lens'),
            'LENS_FOCAL_LENGTH'              : self.indi_allsky_config.get('LENS_FOCAL_LENGTH', 2.5),
            'LENS_FOCAL_RATIO'               : self.indi_allsky_config.get('LENS_FOCAL_RATIO', 2.0),
            'LENS_IMAGE_CIRCLE'              : self.indi_allsky_config.get('LENS_IMAGE_CIRCLE', 3000),
            'LENS_OFFSET_X'                  : self.indi_allsky_config.get('LENS_OFFSET_X', 0),
            'LENS_OFFSET_Y'                  : self.indi_allsky_config.get('LENS_OFFSET_Y', 0),
            'LENS_ALTITUDE'                  : self.indi_allsky_config.get('LENS_ALTITUDE', 90.0),
            'LENS_AZIMUTH'                   : self.indi_allsky_config.get('LENS_AZIMUTH', 0.0),
            'CCD_CONFIG__NIGHT__GAIN'        : round(self.indi_allsky_config.get('CCD_CONFIG', {}).get('NIGHT', {}).get('GAIN', 100.0), 2),  # limit to 2 decimals
            'CCD_CONFIG__NIGHT__BINNING'     : self.indi_allsky_config.get('CCD_CONFIG', {}).get('NIGHT', {}).get('BINNING', 1),
            'CCD_CONFIG__MOONMODE__GAIN'     : round(self.indi_allsky_config.get('CCD_CONFIG', {}).get('MOONMODE', {}).get('GAIN', 75.0), 2),  # limit to 2 decimals
            'CCD_CONFIG__MOONMODE__BINNING'  : self.indi_allsky_config.get('CCD_CONFIG', {}).get('MOONMODE', {}).get('BINNING', 1),
            'CCD_CONFIG__DAY__GAIN'          : round(self.indi_allsky_config.get('CCD_CONFIG', {}).get('DAY', {}).get('GAIN', 0.0), 2),  # limit to 2 decimals
            'CCD_CONFIG__DAY__BINNING'       : self.indi_allsky_config.get('CCD_CONFIG', {}).get('DAY', {}).get('BINNING', 1),
            'CCD_CONFIG__AUTO_GAIN_ENABLE'   : self.indi_allsky_config.get('CCD_CONFIG', {}).get('AUTO_GAIN_ENABLE', False),
            'CCD_CONFIG__AUTO_GAIN_LEVELS'   : str(self.indi_allsky_config.get('CCD_CONFIG', {}).get('AUTO_GAIN_LEVELS', 8)),  # string in form, int in config
            'CCD_EXPOSURE_MAX'               : self.indi_allsky_config.get('CCD_EXPOSURE_MAX', 15.0),
            'CCD_EXPOSURE_DEF'               : '{0:.6f}'.format(self.indi_allsky_config.get('CCD_EXPOSURE_DEF', 0.0)),  # force 6 digits of precision
            'CCD_EXPOSURE_MIN'               : '{0:.6f}'.format(self.indi_allsky_config.get('CCD_EXPOSURE_MIN', 0.0)),
            'CCD_EXPOSURE_MIN_DAY'           : '{0:.6f}'.format(self.indi_allsky_config.get('CCD_EXPOSURE_MIN_DAY', 0.0)),
            'CCD_EXPOSURE_TIMEOUT'           : self.indi_allsky_config.get('CCD_EXPOSURE_TIMEOUT', 330),
            'CCD_BIT_DEPTH'                  : str(self.indi_allsky_config.get('CCD_BIT_DEPTH', 0)),  # string in form, int in config
            'EXPOSURE_PERIOD'                : self.indi_allsky_config.get('EXPOSURE_PERIOD', 15.0),
            'EXPOSURE_PERIOD_DAY'            : self.indi_allsky_config.get('EXPOSURE_PERIOD_DAY', 15.0),
            'CAMERA_SQM__ENABLE'             : self.indi_allsky_config.get('CAMERA_SQM', {}).get('ENABLE', False),
            'CAMERA_SQM__ENABLE_DAY'         : self.indi_allsky_config.get('CAMERA_SQM', {}).get('ENABLE_DAY', False),
            'CAMERA_SQM__EXPOSURE'           : '{0:.6f}'.format(self.indi_allsky_config.get('CAMERA_SQM', {}).get('EXPOSURE', 10.0)),  # force 6 digits of precision
            'CAMERA_SQM__GAIN'               : round(self.indi_allsky_config.get('CAMERA_SQM', {}).get('GAIN', 10.0), 2),  # limit to 2 decimals
            'CAMERA_SQM__BINNING'            : self.indi_allsky_config.get('CAMERA_SQM', {}).get('BINNING', 1),
            'CAMERA_SQM__EXPOSURE_PERIOD'    : self.indi_allsky_config.get('CAMERA_SQM', {}).get('EXPOSURE_PERIOD', 900),
            'CAMERA_SQM__MAGNITUDE_OFFSET'   : self.indi_allsky_config.get('CAMERA_SQM', {}).get('MAGNITUDE_OFFSET', 25.0),
            'FOCUS_MODE'                     : self.indi_allsky_config.get('FOCUS_MODE', False),
            'FOCUS_DELAY'                    : self.indi_allsky_config.get('FOCUS_DELAY', 4.0),
            'CFA_PATTERN'                    : self.indi_allsky_config.get('CFA_PATTERN', ''),
            'USE_NIGHT_COLOR'                : self.indi_allsky_config.get('USE_NIGHT_COLOR', True),
            'SCNR_ALGORITHM'                 : self.indi_allsky_config.get('SCNR_ALGORITHM', ''),
            'SCNR_ALGORITHM_DAY'             : self.indi_allsky_config.get('SCNR_ALGORITHM_DAY', ''),
            'SCNR_MTF_MIDTONES'              : self.indi_allsky_config.get('SCNR_MTF_MIDTONES', 0.55),
            'SCNR_MTF_MIDTONES_DAY'          : self.indi_allsky_config.get('SCNR_MTF_MIDTONES_DAY', 0.55),
            'IMAGE_DENOISE'                  : self.indi_allsky_config.get('IMAGE_DENOISE', ''),
            'IMAGE_DENOISE_DAY'              : self.indi_allsky_config.get('IMAGE_DENOISE_DAY', ''),
            'IMAGE_DENOISE_STRENGTH'         : self.indi_allsky_config.get('IMAGE_DENOISE_STRENGTH', 3),
            'IMAGE_DENOISE_STRENGTH_DAY'     : self.indi_allsky_config.get('IMAGE_DENOISE_STRENGTH_DAY', 3),
            'BILATERAL_SIGMA_COLOR'          : self.indi_allsky_config.get('BILATERAL_SIGMA_COLOR', 20),
            'BILATERAL_SIGMA_COLOR_DAY'      : self.indi_allsky_config.get('BILATERAL_SIGMA_COLOR_DAY', 20),
            'BILATERAL_SIGMA_SPACE'          : self.indi_allsky_config.get('BILATERAL_SIGMA_SPACE', 35),
            'BILATERAL_SIGMA_SPACE_DAY'      : self.indi_allsky_config.get('BILATERAL_SIGMA_SPACE_DAY', 35),
            'WBR_FACTOR'                     : self.indi_allsky_config.get('WBR_FACTOR', 1.0),
            'WBG_FACTOR'                     : self.indi_allsky_config.get('WBG_FACTOR', 1.0),
            'WBB_FACTOR'                     : self.indi_allsky_config.get('WBB_FACTOR', 1.0),
            'WBR_FACTOR_DAY'                 : self.indi_allsky_config.get('WBR_FACTOR_DAY', 1.0),
            'WBG_FACTOR_DAY'                 : self.indi_allsky_config.get('WBG_FACTOR_DAY', 1.0),
            'WBB_FACTOR_DAY'                 : self.indi_allsky_config.get('WBB_FACTOR_DAY', 1.0),
            'AUTO_WB'                        : self.indi_allsky_config.get('AUTO_WB', False),
            'AUTO_WB_DAY'                    : self.indi_allsky_config.get('AUTO_WB_DAY', False),
            'WBR_MTF_MIDTONES'               : self.indi_allsky_config.get('WBR_MTF_MIDTONES', 0.5),
            'WBG_MTF_MIDTONES'               : self.indi_allsky_config.get('WBG_MTF_MIDTONES', 0.5),
            'WBB_MTF_MIDTONES'               : self.indi_allsky_config.get('WBB_MTF_MIDTONES', 0.5),
            'WBR_MTF_MIDTONES_DAY'           : self.indi_allsky_config.get('WBR_MTF_MIDTONES_DAY', 0.5),
            'WBG_MTF_MIDTONES_DAY'           : self.indi_allsky_config.get('WBG_MTF_MIDTONES_DAY', 0.5),
            'WBB_MTF_MIDTONES_DAY'           : self.indi_allsky_config.get('WBB_MTF_MIDTONES_DAY', 0.5),
            'SATURATION_FACTOR'              : self.indi_allsky_config.get('SATURATION_FACTOR', 1.0),
            'SATURATION_FACTOR_DAY'          : self.indi_allsky_config.get('SATURATION_FACTOR_DAY', 1.0),
            'GAMMA_CORRECTION'               : self.indi_allsky_config.get('GAMMA_CORRECTION', 1.0),
            'GAMMA_CORRECTION_DAY'           : self.indi_allsky_config.get('GAMMA_CORRECTION_DAY', 1.0),
            'SHARPEN_AMOUNT'                 : self.indi_allsky_config.get('SHARPEN_AMOUNT', 0.0),
            'SHARPEN_AMOUNT_DAY'             : self.indi_allsky_config.get('SHARPEN_AMOUNT_DAY', 0.0),
            'CCD_COOLING'                    : self.indi_allsky_config.get('CCD_COOLING', False),
            'CCD_COOLING_DAY'                : self.indi_allsky_config.get('CCD_COOLING_DAY', False),
            'CCD_TEMP'                       : self.indi_allsky_config.get('CCD_TEMP', 15.0),
            'CCD_TEMP_DAY'                   : self.indi_allsky_config.get('CCD_TEMP_DAY', 35.0),
            'TEMP_DISPLAY'                   : self.indi_allsky_config.get('TEMP_DISPLAY', 'c'),
            'PRESSURE_DISPLAY'               : self.indi_allsky_config.get('PRESSURE_DISPLAY', 'hpa'),
            'WINDSPEED_DISPLAY'              : self.indi_allsky_config.get('WINDSPEED_DISPLAY', 'ms'),
            'CCD_TEMP_SCRIPT'                : self.indi_allsky_config.get('CCD_TEMP_SCRIPT', ''),
            'GPS_ENABLE'                     : self.indi_allsky_config.get('GPS_ENABLE', False),
            'TARGET_ADU'                     : self.indi_allsky_config.get('TARGET_ADU', 75),
            'TARGET_ADU_DAY'                 : self.indi_allsky_config.get('TARGET_ADU_DAY', 75),
            'TARGET_ADU_DEV'                 : self.indi_allsky_config.get('TARGET_ADU_DEV', 10),
            'TARGET_ADU_DEV_DAY'             : self.indi_allsky_config.get('TARGET_ADU_DEV_DAY', 20),
            'ADU_FOV_DIV'                    : str(self.indi_allsky_config.get('ADU_FOV_DIV', 4)),  # string in form, int in config
            'SQM_FOV_DIV'                    : str(self.indi_allsky_config.get('SQM_FOV_DIV', 4)),  # string in form, int in config
            'DETECT_STARS'                   : self.indi_allsky_config.get('DETECT_STARS', True),
            'DETECT_STARS_THOLD'             : self.indi_allsky_config.get('DETECT_STARS_THOLD', 0.6),
            'DETECT_METEORS'                 : self.indi_allsky_config.get('DETECT_METEORS', False),
            'DETECT_METEORS_THOLD'           : self.indi_allsky_config.get('DETECT_METEORS_THOLD', 125),
            'DETECT_MASK'                    : self.indi_allsky_config.get('DETECT_MASK', ''),
            'DETECT_DRAW'                    : self.indi_allsky_config.get('DETECT_DRAW', False),
            'LOGO_OVERLAY'                   : self.indi_allsky_config.get('LOGO_OVERLAY', ''),
            'HEALTHCHECK__DISK_USAGE'        : self.indi_allsky_config.get('HEALTHCHECK', {}).get('DISK_USAGE', 90.0),
            'HEALTHCHECK__SWAP_USAGE'        : self.indi_allsky_config.get('HEALTHCHECK', {}).get('SWAP_USAGE', 90.0),
            'LOCATION_NAME'                  : self.indi_allsky_config.get('LOCATION_NAME', ''),
            'LOCATION_LATITUDE'              : '{0:+0.3f}'.format(self.indi_allsky_config.get('LOCATION_LATITUDE', 0.0)),
            'LOCATION_LONGITUDE'             : '{0:+0.3f}'.format(self.indi_allsky_config.get('LOCATION_LONGITUDE', 0.0)),
            'LOCATION_ELEVATION'             : self.indi_allsky_config.get('LOCATION_ELEVATION', 0),
            'TIMELAPSE_ENABLE'               : self.indi_allsky_config.get('TIMELAPSE_ENABLE', True),
            'TIMELAPSE_SKIP_FRAMES'          : self.indi_allsky_config.get('TIMELAPSE_SKIP_FRAMES', 4),
            'TIMELAPSE__PRE_PROCESSOR'       : self.indi_allsky_config.get('TIMELAPSE', {}).get('PRE_PROCESSOR', 'standard'),
            'TIMELAPSE__PRE_PROCESSOR_DAY'   : self.indi_allsky_config.get('TIMELAPSE', {}).get('PRE_PROCESSOR_DAY', 'standard'),
            'TIMELAPSE__IMAGE_CIRCLE'        : self.indi_allsky_config.get('TIMELAPSE', {}).get('IMAGE_CIRCLE', 2000),
            'TIMELAPSE__KEOGRAM_RATIO'       : self.indi_allsky_config.get('TIMELAPSE', {}).get('KEOGRAM_RATIO', 0.15),
            'TIMELAPSE__PRE_SCALE'           : self.indi_allsky_config.get('TIMELAPSE', {}).get('PRE_SCALE', 50),
            'TIMELAPSE__FFMPEG_REPORT'       : self.indi_allsky_config.get('TIMELAPSE', {}).get('FFMPEG_REPORT', False),
            'TIMELAPSE__USE_NIGHT_CONFIG'    : self.indi_allsky_config.get('TIMELAPSE', {}).get('USE_NIGHT_CONFIG', True),
            'CAPTURE_PAUSE'                  : self.indi_allsky_config.get('CAPTURE_PAUSE', False),
            'DAYTIME_CAPTURE'                : self.indi_allsky_config.get('DAYTIME_CAPTURE', True),
            'DAYTIME_CAPTURE_SAVE'           : self.indi_allsky_config.get('DAYTIME_CAPTURE_SAVE', True),
            'DAYTIME_TIMELAPSE'              : self.indi_allsky_config.get('DAYTIME_TIMELAPSE', True),
            'DAYTIME_CONTRAST_ENHANCE'       : self.indi_allsky_config.get('DAYTIME_CONTRAST_ENHANCE', False),
            'NIGHT_CONTRAST_ENHANCE'         : self.indi_allsky_config.get('NIGHT_CONTRAST_ENHANCE', False),
            'CONTRAST_ENHANCE_16BIT'         : self.indi_allsky_config.get('CONTRAST_ENHANCE_16BIT', False),
            'CLAHE_CLIPLIMIT'                : self.indi_allsky_config.get('CLAHE_CLIPLIMIT', 3.0),
            'CLAHE_GRIDSIZE'                 : self.indi_allsky_config.get('CLAHE_GRIDSIZE', 8),
            'NIGHT_SUN_ALT_DEG'              : '{0:+0.1f}'.format(self.indi_allsky_config.get('NIGHT_SUN_ALT_DEG', -6.0)),
            'NIGHT_MOONMODE_ALT_DEG'         : '{0:+0.1f}'.format(self.indi_allsky_config.get('NIGHT_MOONMODE_ALT_DEG', 5.0)),
            'NIGHT_MOONMODE_PHASE'           : self.indi_allsky_config.get('NIGHT_MOONMODE_PHASE', 50.0),
            'WEB_STATUS_TEMPLATE'            : self.indi_allsky_config.get('WEB_STATUS_TEMPLATE', ''),
            'WEB_EXTRA_TEXT'                 : self.indi_allsky_config.get('WEB_EXTRA_TEXT', ''),
            'WEB_NONLOCAL_IMAGES'            : self.indi_allsky_config.get('WEB_NONLOCAL_IMAGES', False),
            'WEB_LOCAL_IMAGES_ADMIN'         : self.indi_allsky_config.get('WEB_LOCAL_IMAGES_ADMIN', False),
            'IMAGE_STRETCH__CLASSNAME'       : self.indi_allsky_config.get('IMAGE_STRETCH', {}).get('CLASSNAME', ''),
            'IMAGE_STRETCH__MODE1_GAMMA'     : self.indi_allsky_config.get('IMAGE_STRETCH', {}).get('MODE1_GAMMA', 3.0),
            'IMAGE_STRETCH__MODE1_STDDEVS'   : self.indi_allsky_config.get('IMAGE_STRETCH', {}).get('MODE1_STDDEVS', 2.25),
            'IMAGE_STRETCH__MODE2_SHADOWS'   : self.indi_allsky_config.get('IMAGE_STRETCH', {}).get('MODE2_SHADOWS', 0.0),
            'IMAGE_STRETCH__MODE2_MIDTONES'  : self.indi_allsky_config.get('IMAGE_STRETCH', {}).get('MODE2_MIDTONES', 0.35),
            'IMAGE_STRETCH__MODE2_HIGHLIGHTS': self.indi_allsky_config.get('IMAGE_STRETCH', {}).get('MODE2_HIGHLIGHTS', 1.0),
            'IMAGE_STRETCH__MODE3_BLACK_CLIP': self.indi_allsky_config.get('IMAGE_STRETCH', {}).get('MODE3_BLACK_CLIP', -2.8),
            'IMAGE_STRETCH__MODE3_SHADOWS'   : self.indi_allsky_config.get('IMAGE_STRETCH', {}).get('MODE3_SHADOWS', 0.0),
            'IMAGE_STRETCH__MODE3_MIDTONES'  : self.indi_allsky_config.get('IMAGE_STRETCH', {}).get('MODE3_MIDTONES', 0.25),
            'IMAGE_STRETCH__MODE3_HIGHLIGHTS': self.indi_allsky_config.get('IMAGE_STRETCH', {}).get('MODE3_HIGHLIGHTS', 1.0),
            'IMAGE_STRETCH__SPLIT'           : self.indi_allsky_config.get('IMAGE_STRETCH', {}).get('SPLIT', False),
            'IMAGE_STRETCH__MOONMODE'        : self.indi_allsky_config.get('IMAGE_STRETCH', {}).get('MOONMODE', False),
            'IMAGE_STRETCH__DAYTIME'         : self.indi_allsky_config.get('IMAGE_STRETCH', {}).get('DAYTIME', False),
            'KEOGRAM_ANGLE'                  : self.indi_allsky_config.get('KEOGRAM_ANGLE', 0.0),
            'KEOGRAM_H_SCALE'                : self.indi_allsky_config.get('KEOGRAM_H_SCALE', 100),
            'KEOGRAM_V_SCALE'                : self.indi_allsky_config.get('KEOGRAM_V_SCALE', 33),
            'KEOGRAM_CROP_TOP'               : self.indi_allsky_config.get('KEOGRAM_CROP_TOP', 0),
            'KEOGRAM_CROP_BOTTOM'            : self.indi_allsky_config.get('KEOGRAM_CROP_BOTTOM', 0),
            'KEOGRAM_LABEL'                  : self.indi_allsky_config.get('KEOGRAM_LABEL', True),
            'LONGTERM_KEOGRAM__ENABLE'       : self.indi_allsky_config.get('LONGTERM_KEOGRAM', {}).get('ENABLE', True),
            'LONGTERM_KEOGRAM__OFFSET_X'     : self.indi_allsky_config.get('LONGTERM_KEOGRAM', {}).get('OFFSET_X', 0),
            'LONGTERM_KEOGRAM__OFFSET_Y'     : self.indi_allsky_config.get('LONGTERM_KEOGRAM', {}).get('OFFSET_Y', 0),
            'LONGTERM_KEOGRAM__OPENCV_FONT_SCALE'    : self.indi_allsky_config.get('LONGTERM_KEOGRAM', {}).get('OPENCV_FONT_SCALE', 0.8),
            'LONGTERM_KEOGRAM__PIL_FONT_SIZE'        : self.indi_allsky_config.get('LONGTERM_KEOGRAM', {}).get('PIL_FONT_SIZE', 30),
            'LONGTERM_KEOGRAM__MONTH_LABEL_TEMPLATE' : self.indi_allsky_config.get('LONGTERM_KEOGRAM', {}).get('MONTH_LABEL_TEMPLATE', '{month:%B %Y}'),
            'REALTIME_KEOGRAM__MAX_ENTRIES'  : self.indi_allsky_config.get('REALTIME_KEOGRAM', {}).get('MAX_ENTRIES', 1000),
            'REALTIME_KEOGRAM__SAVE_INTERVAL': self.indi_allsky_config.get('REALTIME_KEOGRAM', {}).get('SAVE_INTERVAL', 25),
            'REALTIME_KEOGRAM__LABEL'        : self.indi_allsky_config.get('REALTIME_KEOGRAM', {}).get('LABEL', False),
            'STARTRAILS_SUN_ALT_THOLD'       : '{0:+0.1f}'.format(self.indi_allsky_config.get('STARTRAILS_SUN_ALT_THOLD', -15.0)),
            'STARTRAILS_MOONMODE_THOLD'      : self.indi_allsky_config.get('STARTRAILS_MOONMODE_THOLD', True),
            'STARTRAILS_MOON_ALT_THOLD'      : '{0:+0.1f}'.format(self.indi_allsky_config.get('STARTRAILS_MOON_ALT_THOLD', 91.0)),
            'STARTRAILS_MOON_PHASE_THOLD'    : self.indi_allsky_config.get('STARTRAILS_MOON_PHASE_THOLD', 101.0),
            'STARTRAILS_MAX_ADU'             : self.indi_allsky_config.get('STARTRAILS_MAX_ADU', 65),
            'STARTRAILS_MASK_THOLD'          : self.indi_allsky_config.get('STARTRAILS_MASK_THOLD', 255),
            'STARTRAILS_PIXEL_THOLD'         : self.indi_allsky_config.get('STARTRAILS_PIXEL_THOLD', 1.0),
            'STARTRAILS_MIN_STARS'           : self.indi_allsky_config.get('STARTRAILS_MIN_STARS', 0),
            'STARTRAILS_TIMELAPSE'           : self.indi_allsky_config.get('STARTRAILS_TIMELAPSE', True),
            'STARTRAILS_TIMELAPSE_MINFRAMES' : self.indi_allsky_config.get('STARTRAILS_TIMELAPSE_MINFRAMES', 250),
            'STARTRAILS_USE_DB_DATA'         : self.indi_allsky_config.get('STARTRAILS_USE_DB_DATA', True),
            'STARTRAILS__IMAGE_CIRCLE_MASK_ENABLE'  : self.indi_allsky_config.get('STARTRAILS', {}).get('IMAGE_CIRCLE_MASK_ENABLE', False),
            'STARTRAILS__IMAGE_CIRCLE_MASK_DIAMETER': self.indi_allsky_config.get('STARTRAILS', {}).get('IMAGE_CIRCLE_MASK_DIAMETER', 3000),
            'STARTRAILS__IMAGE_CIRCLE_MASK_BLUR'    : self.indi_allsky_config.get('STARTRAILS', {}).get('IMAGE_CIRCLE_MASK_BLUR', 35),
            'STARTRAILS__IMAGE_CIRCLE_MASK_OPACITY' : self.indi_allsky_config.get('STARTRAILS', {}).get('IMAGE_CIRCLE_MASK_OPACITY', 100),
            'IMAGE_CALIBRATE_DARK'           : self.indi_allsky_config.get('IMAGE_CALIBRATE_DARK', True),
            'IMAGE_CALIBRATE_BPM'            : self.indi_allsky_config.get('IMAGE_CALIBRATE_BPM', False),
            'IMAGE_CALIBRATE_FIX_HOLES'      : self.indi_allsky_config.get('IMAGE_CALIBRATE_FIX_HOLES', False),
            'IMAGE_CALIBRATE_HOLE_THOLD'     : self.indi_allsky_config.get('IMAGE_CALIBRATE_HOLE_THOLD', 30),
            'IMAGE_CALIBRATE_MANUAL_OFFSET'  : self.indi_allsky_config.get('IMAGE_CALIBRATE_MANUAL_OFFSET', 0),
            'IMAGE_SAVE_FITS_PRE_DARK'       : self.indi_allsky_config.get('IMAGE_SAVE_FITS_PRE_DARK', False),
            'PRIVACY_MODE'                   : self.indi_allsky_config.get('PRIVACY_MODE', False),
            'IMAGE_EXIF_PRIVACY'             : self.indi_allsky_config.get('IMAGE_EXIF_PRIVACY', False),
            'IMAGE_FILE_TYPE'                : self.indi_allsky_config.get('IMAGE_FILE_TYPE', 'jpg'),
            'IMAGE_FILE_COMPRESSION__JPG'    : self.indi_allsky_config.get('IMAGE_FILE_COMPRESSION', {}).get('jpg', 90),
            'IMAGE_FILE_COMPRESSION__PNG'    : self.indi_allsky_config.get('IMAGE_FILE_COMPRESSION', {}).get('png', 5),
            'IMAGE_FILE_COMPRESSION__TIF'    : 'LZW',
            'IMAGE_FOLDER'                   : self.indi_allsky_config.get('IMAGE_FOLDER', '/var/www/html/allsky/images'),
            'VARLIB_FOLDER'                  : self.indi_allsky_config.get('VARLIB_FOLDER', '/var/lib/indi-allsky'),
            'IMAGE_LABEL_TEMPLATE'           : self.indi_allsky_config.get('IMAGE_LABEL_TEMPLATE', ''),
            'IMAGE_EXTRA_TEXT'               : self.indi_allsky_config.get('IMAGE_EXTRA_TEXT', ''),
            'IMAGE_ROTATE'                   : self.indi_allsky_config.get('IMAGE_ROTATE', ''),
            'IMAGE_ROTATE_ANGLE'             : self.indi_allsky_config.get('IMAGE_ROTATE_ANGLE', 0),
            'IMAGE_ROTATE_KEEP_SIZE'         : self.indi_allsky_config.get('IMAGE_ROTATE_KEEP_SIZE', False),
            #'IMAGE_ROTATE_WITH_OFFSET'       : self.indi_allsky_config.get('IMAGE_ROTATE_WITH_OFFSET', False),
            'IMAGE_FLIP_V'                   : self.indi_allsky_config.get('IMAGE_FLIP_V', True),
            'IMAGE_FLIP_H'                   : self.indi_allsky_config.get('IMAGE_FLIP_H', True),
            'IMAGE_SCALE'                    : self.indi_allsky_config.get('IMAGE_SCALE', 100),
            'IMAGE_COLORMAP'                 : self.indi_allsky_config.get('IMAGE_COLORMAP', ''),
            'IMAGE_CIRCLE_MASK__ENABLE'      : self.indi_allsky_config.get('IMAGE_CIRCLE_MASK', {}).get('ENABLE', False),
            'IMAGE_CIRCLE_MASK__DIAMETER'    : self.indi_allsky_config.get('IMAGE_CIRCLE_MASK', {}).get('DIAMETER', 3000),
            'IMAGE_CIRCLE_MASK__OFFSET_X'    : self.indi_allsky_config.get('IMAGE_CIRCLE_MASK', {}).get('OFFSET_X', 0),
            'IMAGE_CIRCLE_MASK__OFFSET_Y'    : self.indi_allsky_config.get('IMAGE_CIRCLE_MASK', {}).get('OFFSET_Y', 0),
            'IMAGE_CIRCLE_MASK__BLUR'        : self.indi_allsky_config.get('IMAGE_CIRCLE_MASK', {}).get('BLUR', 35),
            'IMAGE_CIRCLE_MASK__OPACITY'     : self.indi_allsky_config.get('IMAGE_CIRCLE_MASK', {}).get('OPACITY', 100),
            'IMAGE_CIRCLE_MASK__OUTLINE'     : self.indi_allsky_config.get('IMAGE_CIRCLE_MASK', {}).get('OUTLINE', False),
            'IMAGE_CROP_IMAGE_CIRCLE'        : self.indi_allsky_config.get('IMAGE_CROP_IMAGE_CIRCLE', False),
            'FISH2PANO__ENABLE'              : self.indi_allsky_config.get('FISH2PANO', {}).get('ENABLE', True),
            'FISH2PANO__DIAMETER'            : self.indi_allsky_config.get('FISH2PANO', {}).get('DIAMETER', 3000),
            'FISH2PANO__OFFSET_X'            : self.indi_allsky_config.get('FISH2PANO', {}).get('OFFSET_X', 0),
            'FISH2PANO__OFFSET_Y'            : self.indi_allsky_config.get('FISH2PANO', {}).get('OFFSET_Y', 0),
            'FISH2PANO__ROTATE_ANGLE'        : self.indi_allsky_config.get('FISH2PANO', {}).get('ROTATE_ANGLE', -90),
            'FISH2PANO__SCALE'               : self.indi_allsky_config.get('FISH2PANO', {}).get('SCALE', 0.5),
            'FISH2PANO__MODULUS'             : self.indi_allsky_config.get('FISH2PANO', {}).get('MODULUS', 2),
            'FISH2PANO__FLIP_H'              : self.indi_allsky_config.get('FISH2PANO', {}).get('FLIP_H', False),
            'FISH2PANO__ENABLE_CARDINAL_DIRS': self.indi_allsky_config.get('FISH2PANO', {}).get('ENABLE_CARDINAL_DIRS', True),
            'FISH2PANO__DIRS_OFFSET_BOTTOM'  : self.indi_allsky_config.get('FISH2PANO', {}).get('DIRS_OFFSET_BOTTOM', 25),
            'FISH2PANO__OPENCV_FONT_SCALE'   : self.indi_allsky_config.get('FISH2PANO', {}).get('OPENCV_FONT_SCALE', 0.8),
            'FISH2PANO__PIL_FONT_SIZE'       : self.indi_allsky_config.get('FISH2PANO', {}).get('PIL_FONT_SIZE', 30),
            'IMAGE_SAVE_FITS'                : self.indi_allsky_config.get('IMAGE_SAVE_FITS', False),
            'IMAGE_SAVE_FITS_COMPRESSED'     : self.indi_allsky_config.get('IMAGE_SAVE_FITS_COMPRESSED', False),
            'IMAGE_SAVE_FITS_PERIOD'         : str(self.indi_allsky_config.get('IMAGE_SAVE_FITS_PERIOD', 7200)),  # string in form, int in config
            'NIGHT_GRAYSCALE'                : self.indi_allsky_config.get('NIGHT_GRAYSCALE', False),
            'DAYTIME_GRAYSCALE'              : self.indi_allsky_config.get('DAYTIME_GRAYSCALE', False),
            'MOON_OVERLAY__ENABLE'           : self.indi_allsky_config.get('MOON_OVERLAY', {}).get('ENABLE', True),
            'MOON_OVERLAY__X'                : self.indi_allsky_config.get('MOON_OVERLAY', {}).get('X', -500),
            'MOON_OVERLAY__Y'                : self.indi_allsky_config.get('MOON_OVERLAY', {}).get('Y', -200),
            'MOON_OVERLAY__SCALE'            : self.indi_allsky_config.get('MOON_OVERLAY', {}).get('SCALE', 0.5),
            'MOON_OVERLAY__DARK_SIDE_SCALE'  : self.indi_allsky_config.get('MOON_OVERLAY', {}).get('DARK_SIDE_SCALE', 0.4),
            'MOON_OVERLAY__FLIP_V'           : self.indi_allsky_config.get('MOON_OVERLAY', {}).get('FLIP_V', False),
            'MOON_OVERLAY__FLIP_H'           : self.indi_allsky_config.get('MOON_OVERLAY', {}).get('FLIP_H', False),
            'LIGHTGRAPH_OVERLAY__ENABLE'     : self.indi_allsky_config.get('LIGHTGRAPH_OVERLAY', {}).get('ENABLE', False),
            'LIGHTGRAPH_OVERLAY__GRAPH_HEIGHT' : self.indi_allsky_config.get('LIGHTGRAPH_OVERLAY', {}).get('GRAPH_HEIGHT', 30),
            'LIGHTGRAPH_OVERLAY__GRAPH_BORDER' : self.indi_allsky_config.get('LIGHTGRAPH_OVERLAY', {}).get('GRAPH_BORDER', 3),
            'LIGHTGRAPH_OVERLAY__Y'          : self.indi_allsky_config.get('LIGHTGRAPH_OVERLAY', {}).get('Y', 10),
            'LIGHTGRAPH_OVERLAY__OFFSET_X'   : self.indi_allsky_config.get('LIGHTGRAPH_OVERLAY', {}).get('OFFSET_X', 0),
            'LIGHTGRAPH_OVERLAY__SCALE'      : self.indi_allsky_config.get('LIGHTGRAPH_OVERLAY', {}).get('SCALE', 1.0),
            'LIGHTGRAPH_OVERLAY__NOW_MARKER_SIZE' : self.indi_allsky_config.get('LIGHTGRAPH_OVERLAY', {}).get('NOW_MARKER_SIZE', 8),
            'LIGHTGRAPH_OVERLAY__OPACITY'    : self.indi_allsky_config.get('LIGHTGRAPH_OVERLAY', {}).get('OPACITY', 100),
            'LIGHTGRAPH_OVERLAY__PIL_FONT_SIZE' : self.indi_allsky_config.get('LIGHTGRAPH_OVERLAY', {}).get('PIL_FONT_SIZE', 20),
            'LIGHTGRAPH_OVERLAY__OPENCV_FONT_SCALE' : self.indi_allsky_config.get('LIGHTGRAPH_OVERLAY', {}).get('OPENCV_FONT_SCALE', 0.5),
            'LIGHTGRAPH_OVERLAY__LABEL'      : self.indi_allsky_config.get('LIGHTGRAPH_OVERLAY', {}).get('LABEL', True),
            'LIGHTGRAPH_OVERLAY__HOUR_LINES' : self.indi_allsky_config.get('LIGHTGRAPH_OVERLAY', {}).get('HOUR_LINES', True),
            'IMAGE_OVERLAY__ENABLE'          : self.indi_allsky_config.get('IMAGE_OVERLAY', {}).get('ENABLE', False),
            'IMAGE_OVERLAY__LOAD_INTERVAL'   : self.indi_allsky_config.get('IMAGE_OVERLAY', {}).get('LOAD_INTERVAL', 600),
            'IMAGE_OVERLAY__A_URL'           : self.indi_allsky_config.get('IMAGE_OVERLAY', {}).get('A_URL', ''),
            'IMAGE_OVERLAY__A_IMAGE_FILE_TYPE' : self.indi_allsky_config.get('IMAGE_OVERLAY', {}).get('A_IMAGE_FILE_TYPE', 'jpg'),
            'IMAGE_OVERLAY__A_WIDTH'         : self.indi_allsky_config.get('IMAGE_OVERLAY', {}).get('A_WIDTH', 250),
            'IMAGE_OVERLAY__A_HEIGHT'        : self.indi_allsky_config.get('IMAGE_OVERLAY', {}).get('A_HEIGHT', 250),
            'IMAGE_OVERLAY__A_X'             : self.indi_allsky_config.get('IMAGE_OVERLAY', {}).get('A_X', 300),
            'IMAGE_OVERLAY__A_Y'             : self.indi_allsky_config.get('IMAGE_OVERLAY', {}).get('A_Y', -300),
            'IMAGE_OVERLAY__A_USERNAME'      : self.indi_allsky_config.get('IMAGE_OVERLAY', {}).get('A_USERNAME', ''),
            'IMAGE_OVERLAY__A_PASSWORD'      : self.indi_allsky_config.get('IMAGE_OVERLAY', {}).get('A_PASSWORD', ''),
            'IMAGE_EXPORT_RAW'               : self.indi_allsky_config.get('IMAGE_EXPORT_RAW', ''),
            'IMAGE_EXPORT_FOLDER'            : self.indi_allsky_config.get('IMAGE_EXPORT_FOLDER', '/var/www/html/allsky/images/export'),
            'IMAGE_EXPORT_FLIP_V'            : self.indi_allsky_config.get('IMAGE_EXPORT_FLIP_V', False),
            'IMAGE_EXPORT_FLIP_H'            : self.indi_allsky_config.get('IMAGE_EXPORT_FLIP_H', False),
            'IMAGE_STACK_METHOD'             : self.indi_allsky_config.get('IMAGE_STACK_METHOD', 'maximum'),
            'IMAGE_STACK_COUNT'              : str(self.indi_allsky_config.get('IMAGE_STACK_COUNT', 1)),  # string in form, int in config
            'IMAGE_STACK_ALIGN'              : self.indi_allsky_config.get('IMAGE_STACK_ALIGN', False),
            'IMAGE_ALIGN_DETECTSIGMA'        : self.indi_allsky_config.get('IMAGE_ALIGN_DETECTSIGMA', 5),
            'IMAGE_ALIGN_POINTS'             : self.indi_allsky_config.get('IMAGE_ALIGN_POINTS', 50),
            'IMAGE_ALIGN_SOURCEMINAREA'      : self.indi_allsky_config.get('IMAGE_ALIGN_SOURCEMINAREA', 10),
            'IMAGE_STACK_SPLIT'              : self.indi_allsky_config.get('IMAGE_STACK_SPLIT', False),
            'IMAGE_STACK_MOONMODE'           : self.indi_allsky_config.get('IMAGE_STACK_MOONMODE', False),
            'IMAGE_STACK_DAY'                : self.indi_allsky_config.get('IMAGE_STACK_DAY', False),
            'IMAGE_QUEUE_MAX'                : self.indi_allsky_config.get('IMAGE_QUEUE_MAX', 3),
            'IMAGE_QUEUE_MIN'                : self.indi_allsky_config.get('IMAGE_QUEUE_MIN', 1),
            'IMAGE_QUEUE_BACKOFF'            : self.indi_allsky_config.get('IMAGE_QUEUE_BACKOFF', 0.5),
            'IMAGE_SAVE_HOOK_PRE'            : self.indi_allsky_config.get('IMAGE_SAVE_HOOK_PRE', ''),
            'IMAGE_SAVE_HOOK_POST'           : self.indi_allsky_config.get('IMAGE_SAVE_HOOK_POST', ''),
            'IMAGE_SAVE_HOOK_TIMEOUT'        : self.indi_allsky_config.get('IMAGE_SAVE_HOOK_TIMEOUT', 5),
            'CAPTURE_HOOK_PRE'               : self.indi_allsky_config.get('CAPTURE_HOOK_PRE', ''),
            'CAPTURE_HOOK_TIMEOUT'           : self.indi_allsky_config.get('CAPTURE_HOOK_TIMEOUT', 5),
            'BACKUP_DB_PERIOD_DAYS'          : self.indi_allsky_config.get('BACKUP_DB_PERIOD_DAYS', 7),
            'IMAGE_EXPIRE_DAYS'              : self.indi_allsky_config.get('IMAGE_EXPIRE_DAYS', 10),
            'IMAGE_RAW_EXPIRE_DAYS'          : self.indi_allsky_config.get('IMAGE_RAW_EXPIRE_DAYS', 10),
            'IMAGE_FITS_EXPIRE_DAYS'         : self.indi_allsky_config.get('IMAGE_FITS_EXPIRE_DAYS', 10),
            'TIMELAPSE_EXPIRE_DAYS'          : self.indi_allsky_config.get('TIMELAPSE_EXPIRE_DAYS', 365),
            'TIMELAPSE_OVERWRITE'            : self.indi_allsky_config.get('TIMELAPSE_OVERWRITE', False),
            'FFMPEG_FRAMERATE'               : self.indi_allsky_config.get('FFMPEG_FRAMERATE', 25),
            'FFMPEG_FRAMERATE_DAY'           : self.indi_allsky_config.get('FFMPEG_FRAMERATE_DAY', 25),
            'FFMPEG_BITRATE'                 : self.indi_allsky_config.get('FFMPEG_BITRATE', '5000k'),
            'FFMPEG_BITRATE_DAY'             : self.indi_allsky_config.get('FFMPEG_BITRATE_DAY', '5000k'),
            'FFMPEG_VFSCALE'                 : self.indi_allsky_config.get('FFMPEG_VFSCALE', ''),
            'FFMPEG_VFSCALE_DAY'             : self.indi_allsky_config.get('FFMPEG_VFSCALE_DAY', ''),
            'FFMPEG_VFSCALE_STARTRAIL'       : self.indi_allsky_config.get('FFMPEG_VFSCALE_STARTRAIL', ''),
            'FFMPEG_CODEC'                   : self.indi_allsky_config.get('FFMPEG_CODEC', 'libx264'),
            'FFMPEG_EXTRA_OPTIONS'           : self.indi_allsky_config.get('FFMPEG_EXTRA_OPTIONS', '-level 3.1'),
            'FFMPEG_EXTRA_OPTIONS_DAY'       : self.indi_allsky_config.get('FFMPEG_EXTRA_OPTIONS_DAY', '-level 3.1'),
            'IMAGE_LABEL_SYSTEM'             : self.indi_allsky_config.get('IMAGE_LABEL_SYSTEM', 'pillow'),
            'TEXT_PROPERTIES__FONT_FACE'     : self.indi_allsky_config.get('TEXT_PROPERTIES', {}).get('FONT_FACE', 'FONT_HERSHEY_SIMPLEX'),
            'TEXT_PROPERTIES__FONT_SCALE'    : self.indi_allsky_config.get('TEXT_PROPERTIES', {}).get('FONT_SCALE', 0.8),
            'TEXT_PROPERTIES__FONT_THICKNESS': self.indi_allsky_config.get('TEXT_PROPERTIES', {}).get('FONT_THICKNESS', 1),
            'TEXT_PROPERTIES__FONT_OUTLINE'  : self.indi_allsky_config.get('TEXT_PROPERTIES', {}).get('FONT_OUTLINE', True),
            'TEXT_PROPERTIES__FONT_HEIGHT'   : self.indi_allsky_config.get('TEXT_PROPERTIES', {}).get('FONT_HEIGHT', 30),
            'TEXT_PROPERTIES__FONT_X'        : self.indi_allsky_config.get('TEXT_PROPERTIES', {}).get('FONT_X', 15),
            'TEXT_PROPERTIES__FONT_Y'        : self.indi_allsky_config.get('TEXT_PROPERTIES', {}).get('FONT_Y', 30),
            'TEXT_PROPERTIES__PIL_FONT_FILE' : self.indi_allsky_config.get('TEXT_PROPERTIES', {}).get('PIL_FONT_FILE', 'fonts-freefont-ttf/FreeSans.ttf'),
            'TEXT_PROPERTIES__PIL_FONT_CUSTOM' : self.indi_allsky_config.get('TEXT_PROPERTIES', {}).get('PIL_FONT_CUSTOM', ''),
            'TEXT_PROPERTIES__PIL_FONT_SIZE' : self.indi_allsky_config.get('TEXT_PROPERTIES', {}).get('PIL_FONT_SIZE', 30),
            'CARDINAL_DIRS__ENABLE'          : self.indi_allsky_config.get('CARDINAL_DIRS', {}).get('ENABLE', True),
            'CARDINAL_DIRS__SWAP_NS'         : self.indi_allsky_config.get('CARDINAL_DIRS', {}).get('SWAP_NS', False),
            'CARDINAL_DIRS__SWAP_EW'         : self.indi_allsky_config.get('CARDINAL_DIRS', {}).get('SWAP_EW', False),
            'CARDINAL_DIRS__CHAR_NORTH'      : self.indi_allsky_config.get('CARDINAL_DIRS', {}).get('CHAR_NORTH', 'N'),
            'CARDINAL_DIRS__CHAR_EAST'       : self.indi_allsky_config.get('CARDINAL_DIRS', {}).get('CHAR_EAST', 'E'),
            'CARDINAL_DIRS__CHAR_WEST'       : self.indi_allsky_config.get('CARDINAL_DIRS', {}).get('CHAR_WEST', 'W'),
            'CARDINAL_DIRS__CHAR_SOUTH'      : self.indi_allsky_config.get('CARDINAL_DIRS', {}).get('CHAR_SOUTH', 'S'),
            'CARDINAL_DIRS__DIAMETER'        : self.indi_allsky_config.get('CARDINAL_DIRS', {}).get('DIAMETER', 3000),
            'CARDINAL_DIRS__OFFSET_X'        : self.indi_allsky_config.get('CARDINAL_DIRS', {}).get('OFFSET_X', 0),
            'CARDINAL_DIRS__OFFSET_Y'        : self.indi_allsky_config.get('CARDINAL_DIRS', {}).get('OFFSET_Y', 0),
            'CARDINAL_DIRS__OFFSET_TOP'      : self.indi_allsky_config.get('CARDINAL_DIRS', {}).get('OFFSET_TOP', 15),
            'CARDINAL_DIRS__OFFSET_LEFT'     : self.indi_allsky_config.get('CARDINAL_DIRS', {}).get('OFFSET_LEFT', 15),
            'CARDINAL_DIRS__OFFSET_RIGHT'    : self.indi_allsky_config.get('CARDINAL_DIRS', {}).get('OFFSET_RIGHT', 15),
            'CARDINAL_DIRS__OFFSET_BOTTOM'   : self.indi_allsky_config.get('CARDINAL_DIRS', {}).get('OFFSET_BOTTOM', 15),
            'CARDINAL_DIRS__OPENCV_FONT_SCALE' : self.indi_allsky_config.get('CARDINAL_DIRS', {}).get('OPENCV_FONT_SCALE', 0.5),
            'CARDINAL_DIRS__PIL_FONT_SIZE'   : self.indi_allsky_config.get('CARDINAL_DIRS', {}).get('PIL_FONT_SIZE', 20),
            'CARDINAL_DIRS__OUTLINE_CIRCLE'  : self.indi_allsky_config.get('CARDINAL_DIRS', {}).get('OUTLINE_CIRCLE', False),
            'ORB_PROPERTIES__MODE'           : self.indi_allsky_config.get('ORB_PROPERTIES', {}).get('MODE', 'ha'),
            'ORB_PROPERTIES__RADIUS'         : self.indi_allsky_config.get('ORB_PROPERTIES', {}).get('RADIUS', 9),
            'ORB_PROPERTIES__AZ_OFFSET'      : self.indi_allsky_config.get('ORB_PROPERTIES', {}).get('AZ_OFFSET', 0.0),
            'ORB_PROPERTIES__RETROGRADE'     : self.indi_allsky_config.get('ORB_PROPERTIES', {}).get('RETROGRADE', False),
            'IMAGE_BORDER__TOP'              : self.indi_allsky_config.get('IMAGE_BORDER', {}).get('TOP', 0),
            'IMAGE_BORDER__LEFT'             : self.indi_allsky_config.get('IMAGE_BORDER', {}).get('LEFT', 0),
            'IMAGE_BORDER__RIGHT'            : self.indi_allsky_config.get('IMAGE_BORDER', {}).get('RIGHT', 0),
            'IMAGE_BORDER__BOTTOM'           : self.indi_allsky_config.get('IMAGE_BORDER', {}).get('BOTTOM', 0),
            'UPLOAD_WORKERS'                 : self.indi_allsky_config.get('UPLOAD_WORKERS', 2),
            'FILETRANSFER__CLASSNAME'        : self.indi_allsky_config.get('FILETRANSFER', {}).get('CLASSNAME', 'pycurl_sftp'),
            'FILETRANSFER__HOST'             : self.indi_allsky_config.get('FILETRANSFER', {}).get('HOST', ''),
            'FILETRANSFER__PORT'             : self.indi_allsky_config.get('FILETRANSFER', {}).get('PORT', 0),
            'FILETRANSFER__USERNAME'         : self.indi_allsky_config.get('FILETRANSFER', {}).get('USERNAME', ''),
            'FILETRANSFER__PASSWORD'         : self.indi_allsky_config.get('FILETRANSFER', {}).get('PASSWORD', ''),
            'FILETRANSFER__PRIVATE_KEY'      : self.indi_allsky_config.get('FILETRANSFER', {}).get('PRIVATE_KEY', ''),
            'FILETRANSFER__PUBLIC_KEY'       : self.indi_allsky_config.get('FILETRANSFER', {}).get('PUBLIC_KEY', ''),
            'FILETRANSFER__CONNECT_TIMEOUT'  : self.indi_allsky_config.get('FILETRANSFER', {}).get('CONNECT_TIMEOUT', 10.0),
            'FILETRANSFER__TIMEOUT'          : self.indi_allsky_config.get('FILETRANSFER', {}).get('TIMEOUT', 60.0),
            'FILETRANSFER__CERT_BYPASS'      : self.indi_allsky_config.get('FILETRANSFER', {}).get('CERT_BYPASS', True),
            'FILETRANSFER__ATOMIC_TRANSFERS' : self.indi_allsky_config.get('FILETRANSFER', {}).get('ATOMIC_TRANSFERS', False),
            'FILETRANSFER__FORCE_IPV4'       : self.indi_allsky_config.get('FILETRANSFER', {}).get('FORCE_IPV4', False),
            'FILETRANSFER__FORCE_IPV6'       : self.indi_allsky_config.get('FILETRANSFER', {}).get('FORCE_IPV6', False),
            'FILETRANSFER__REMOTE_IMAGE_NAME'         : self.indi_allsky_config.get('FILETRANSFER', {}).get('REMOTE_IMAGE_NAME', 'image_ccd{camera_id:d}_{ts:%Y%m%d_%H%M%S}.{ext}'),
            'FILETRANSFER__REMOTE_IMAGE_FOLDER'       : self.indi_allsky_config.get('FILETRANSFER', {}).get('REMOTE_IMAGE_FOLDER', '/home/allsky/upload/allsky/images/{day_date:%Y%m%d}/{timeofday:s}/{ts:%H}'),
            'FILETRANSFER__REMOTE_PANORAMA_NAME'      : self.indi_allsky_config.get('FILETRANSFER', {}).get('REMOTE_PANORAMA_NAME', 'panorama_ccd{camera_id:d}_{ts:%Y%m%d_%H%M%S}.{ext}'),
            'FILETRANSFER__REMOTE_PANORAMA_FOLDER'    : self.indi_allsky_config.get('FILETRANSFER', {}).get('REMOTE_PANORAMA_FOLDER', '/home/allsky/upload/allsky/panoramas/{day_date:%Y%m%d}/{timeofday:s}/{ts:%H}'),
            'FILETRANSFER__REMOTE_METADATA_NAME'      : self.indi_allsky_config.get('FILETRANSFER', {}).get('REMOTE_METADATA_NAME', 'latest_metadata.json'),
            'FILETRANSFER__REMOTE_METADATA_FOLDER'    : self.indi_allsky_config.get('FILETRANSFER', {}).get('REMOTE_METADATA_FOLDER', '/home/allsky/upload/allsky'),
            'FILETRANSFER__REMOTE_RAW_NAME'           : self.indi_allsky_config.get('FILETRANSFER', {}).get('REMOTE_RAW_NAME', 'raw_ccd{camera_id:d}_{ts:%Y%m%d_%H%M%S}.{ext}'),
            'FILETRANSFER__REMOTE_RAW_FOLDER'         : self.indi_allsky_config.get('FILETRANSFER', {}).get('REMOTE_RAW_FOLDER', '/home/allsky/upload/allsky/export/{day_date:%Y%m%d}/{timeofday:s}/{ts:%H}'),
            'FILETRANSFER__REMOTE_FITS_NAME'          : self.indi_allsky_config.get('FILETRANSFER', {}).get('REMOTE_FITS_NAME', 'image_ccd{camera_id:d}_{ts:%Y%m%d_%H%M%S}.{ext}'),
            'FILETRANSFER__REMOTE_FITS_FOLDER'        : self.indi_allsky_config.get('FILETRANSFER', {}).get('REMOTE_FITS_FOLDER', '/home/allsky/upload/allsky/fits/{day_date:%Y%m%d}/{timeofday:s}/{ts:%H}'),
            'FILETRANSFER__REMOTE_VIDEO_NAME'         : self.indi_allsky_config.get('FILETRANSFER', {}).get('REMOTE_VIDEO_NAME', 'allsky-timelapse_ccd{camera_id:d}_{day_date:%Y%m%d}_{timeofday:s}.{ext}'),
            'FILETRANSFER__REMOTE_VIDEO_FOLDER'       : self.indi_allsky_config.get('FILETRANSFER', {}).get('REMOTE_VIDEO_FOLDER', '/home/allsky/upload/allsky/videos/{day_date:%Y%m%d}'),
            'FILETRANSFER__REMOTE_MINI_VIDEO_NAME'    : self.indi_allsky_config.get('FILETRANSFER', {}).get('REMOTE_MINI_VIDEO_NAME', 'allsky-minitimelapse_ccd{camera_id:d}_{day_date:%Y%m%d}_{timeofday:s}.{ext}'),
            'FILETRANSFER__REMOTE_MINI_VIDEO_FOLDER'  : self.indi_allsky_config.get('FILETRANSFER', {}).get('REMOTE_MINI_VIDEO_FOLDER', '/home/allsky/upload/allsky/videos/{day_date:%Y%m%d}'),
            'FILETRANSFER__REMOTE_KEOGRAM_NAME'       : self.indi_allsky_config.get('FILETRANSFER', {}).get('REMOTE_KEOGRAM_NAME', 'allsky-keogram_ccd{camera_id:d}_{day_date:%Y%m%d}_{timeofday:s}.{ext}'),
            'FILETRANSFER__REMOTE_KEOGRAM_FOLDER'     : self.indi_allsky_config.get('FILETRANSFER', {}).get('REMOTE_KEOGRAM_FOLDER', '/home/allsky/upload/allsky/keograms/{day_date:%Y%m%d}'),
            'FILETRANSFER__REMOTE_STARTRAIL_NAME'     : self.indi_allsky_config.get('FILETRANSFER', {}).get('REMOTE_STARTRAIL_NAME', 'allsky-startrail_ccd{camera_id:d}_{day_date:%Y%m%d}_{timeofday:s}.{ext}'),
            'FILETRANSFER__REMOTE_STARTRAIL_FOLDER'   : self.indi_allsky_config.get('FILETRANSFER', {}).get('REMOTE_STARTRAIL_FOLDER', '/home/allsky/upload/allsky/startrails/{day_date:%Y%m%d}'),
            'FILETRANSFER__REMOTE_STARTRAIL_VIDEO_NAME'   : self.indi_allsky_config.get('FILETRANSFER', {}).get('REMOTE_STARTRAIL_VIDEO_NAME', 'allsky-startrail_timelapse_ccd{camera_id:d}_{day_date:%Y%m%d}_{timeofday:s}.{ext}'),
            'FILETRANSFER__REMOTE_STARTRAIL_VIDEO_FOLDER' : self.indi_allsky_config.get('FILETRANSFER', {}).get('REMOTE_STARTRAIL_VIDEO_FOLDER', '/home/allsky/upload/allsky/videos/{day_date:%Y%m%d}'),
            'FILETRANSFER__REMOTE_PANORAMA_VIDEO_NAME'    : self.indi_allsky_config.get('FILETRANSFER', {}).get('REMOTE_PANORAMA_VIDEO_NAME', 'allsky-panorama_timelapse_ccd{camera_id:d}_{day_date:%Y%m%d}_{timeofday:s}.{ext}'),
            'FILETRANSFER__REMOTE_PANORAMA_VIDEO_FOLDER'  : self.indi_allsky_config.get('FILETRANSFER', {}).get('REMOTE_PANORAMA_VIDEO_FOLDER', '/home/allsky/upload/allsky/videos/{day_date:%Y%m%d}'),
            'FILETRANSFER__REMOTE_REALTIME_KEOGRAM_NAME'  : self.indi_allsky_config.get('FILETRANSFER', {}).get('REMOTE_REALTIME_KEOGRAM_NAME', 'allsky-realtime_keogram_ccd{camera_id:d}.{ext}'),
            'FILETRANSFER__REMOTE_REALTIME_KEOGRAM_FOLDER': self.indi_allsky_config.get('FILETRANSFER', {}).get('REMOTE_REALTIME_KEOGRAM_FOLDER', '/home/allsky/upload/allsky'),
            'FILETRANSFER__REMOTE_ENDOFNIGHT_FOLDER'      : self.indi_allsky_config.get('FILETRANSFER', {}).get('REMOTE_ENDOFNIGHT_FOLDER', '/home/allsky/upload/allsky'),
            'FILETRANSFER__REMOTE_LATEST_FOLDER'          : self.indi_allsky_config.get('FILETRANSFER', {}).get('REMOTE_LATEST_FOLDER', '/home/allsky/upload/allsky'),
            'FILETRANSFER__REMOTE_DB_BACKUP_FOLDER'       : self.indi_allsky_config.get('FILETRANSFER', {}).get('REMOTE_DB_BACKUP_FOLDER', '/home/allsky/upload/backup'),
            'FILETRANSFER__UPLOAD_IMAGE'     : self.indi_allsky_config.get('FILETRANSFER', {}).get('UPLOAD_IMAGE', 0),
            'FILETRANSFER__UPLOAD_PANORAMA'  : self.indi_allsky_config.get('FILETRANSFER', {}).get('UPLOAD_PANORAMA', 0),
            'FILETRANSFER__UPLOAD_METADATA'  : self.indi_allsky_config.get('FILETRANSFER', {}).get('UPLOAD_METADATA', False),
            'FILETRANSFER__UPLOAD_RAW'       : self.indi_allsky_config.get('FILETRANSFER', {}).get('UPLOAD_RAW', False),
            'FILETRANSFER__UPLOAD_FITS'      : self.indi_allsky_config.get('FILETRANSFER', {}).get('UPLOAD_FITS', False),
            'FILETRANSFER__UPLOAD_VIDEO'     : self.indi_allsky_config.get('FILETRANSFER', {}).get('UPLOAD_VIDEO', False),
            'FILETRANSFER__UPLOAD_MINI_VIDEO': self.indi_allsky_config.get('FILETRANSFER', {}).get('UPLOAD_MINI_VIDEO', False),
            'FILETRANSFER__UPLOAD_KEOGRAM'   : self.indi_allsky_config.get('FILETRANSFER', {}).get('UPLOAD_KEOGRAM', False),
            'FILETRANSFER__UPLOAD_STARTRAIL' : self.indi_allsky_config.get('FILETRANSFER', {}).get('UPLOAD_STARTRAIL', False),
            'FILETRANSFER__UPLOAD_STARTRAIL_VIDEO' : self.indi_allsky_config.get('FILETRANSFER', {}).get('UPLOAD_STARTRAIL_VIDEO', False),
            'FILETRANSFER__UPLOAD_PANORAMA_VIDEO'  : self.indi_allsky_config.get('FILETRANSFER', {}).get('UPLOAD_PANORAMA_VIDEO', False),
            'FILETRANSFER__UPLOAD_REALTIME_KEOGRAM': self.indi_allsky_config.get('FILETRANSFER', {}).get('UPLOAD_REALTIME_KEOGRAM', 0),
            'FILETRANSFER__UPLOAD_ENDOFNIGHT'      : self.indi_allsky_config.get('FILETRANSFER', {}).get('UPLOAD_ENDOFNIGHT', False),
            'FILETRANSFER__UPLOAD_LATEST_IMAGE'    : self.indi_allsky_config.get('FILETRANSFER', {}).get('UPLOAD_LATEST_IMAGE', False),
            'FILETRANSFER__UPLOAD_LATEST_PANORAMA' : self.indi_allsky_config.get('FILETRANSFER', {}).get('UPLOAD_LATEST_PANORAMA', False),
            'FILETRANSFER__UPLOAD_LATEST_RAW'      : self.indi_allsky_config.get('FILETRANSFER', {}).get('UPLOAD_LATEST_RAW', False),
            'FILETRANSFER__UPLOAD_LATEST_VIDEO'    : self.indi_allsky_config.get('FILETRANSFER', {}).get('UPLOAD_LATEST_VIDEO', False),
            'FILETRANSFER__UPLOAD_DB_BACKUP'       : self.indi_allsky_config.get('FILETRANSFER', {}).get('UPLOAD_DB_BACKUP', False),
            'S3UPLOAD__CLASSNAME'            : self.indi_allsky_config.get('S3UPLOAD', {}).get('CLASSNAME', 'boto3_s3'),
            'S3UPLOAD__ENABLE'               : self.indi_allsky_config.get('S3UPLOAD', {}).get('ENABLE', False),
            'S3UPLOAD__ACCESS_KEY'           : self.indi_allsky_config.get('S3UPLOAD', {}).get('ACCESS_KEY', ''),
            'S3UPLOAD__SECRET_KEY'           : self.indi_allsky_config.get('S3UPLOAD', {}).get('SECRET_KEY', ''),
            'S3UPLOAD__CREDS_FILE'           : self.indi_allsky_config.get('S3UPLOAD', {}).get('CREDS_FILE', ''),
            'S3UPLOAD__BUCKET'               : self.indi_allsky_config.get('S3UPLOAD', {}).get('BUCKET', 'change-me'),
            'S3UPLOAD__REGION'               : self.indi_allsky_config.get('S3UPLOAD', {}).get('REGION', 'us-east-2'),
            'S3UPLOAD__NAMESPACE'            : self.indi_allsky_config.get('S3UPLOAD', {}).get('NAMESPACE', ''),
            'S3UPLOAD__HOST'                 : self.indi_allsky_config.get('S3UPLOAD', {}).get('HOST', 'amazonaws.com'),
            'S3UPLOAD__ENDPOINT_URL'         : self.indi_allsky_config.get('S3UPLOAD', {}).get('ENDPOINT_URL', ''),
            'S3UPLOAD__PORT'                 : self.indi_allsky_config.get('S3UPLOAD', {}).get('PORT', 0),
            'S3UPLOAD__CONNECT_TIMEOUT'      : self.indi_allsky_config.get('S3UPLOAD', {}).get('CONNECT_TIMEOUT', 10.0),
            'S3UPLOAD__TIMEOUT'              : self.indi_allsky_config.get('S3UPLOAD', {}).get('TIMEOUT', 60.0),
            'S3UPLOAD__URL_TEMPLATE'         : self.indi_allsky_config.get('S3UPLOAD', {}).get('URL_TEMPLATE', 'https://{bucket}.s3.{region}.{host}'),
            'S3UPLOAD__STORAGE_CLASS'        : self.indi_allsky_config.get('S3UPLOAD', {}).get('STORAGE_CLASS', 'STANDARD'),
            'S3UPLOAD__ACL'                  : self.indi_allsky_config.get('S3UPLOAD', {}).get('ACL', ''),
            'S3UPLOAD__TLS'                  : self.indi_allsky_config.get('S3UPLOAD', {}).get('TLS', True),
            'S3UPLOAD__CERT_BYPASS'          : self.indi_allsky_config.get('S3UPLOAD', {}).get('CERT_BYPASS', False),
            'S3UPLOAD__UPLOAD_FITS'          : self.indi_allsky_config.get('S3UPLOAD', {}).get('UPLOAD_FITS', False),
            'S3UPLOAD__UPLOAD_RAW'           : self.indi_allsky_config.get('S3UPLOAD', {}).get('UPLOAD_RAW', False),
            'MQTTPUBLISH__ENABLE'            : self.indi_allsky_config.get('MQTTPUBLISH', {}).get('ENABLE', False),
            'MQTTPUBLISH__TRANSPORT'         : self.indi_allsky_config.get('MQTTPUBLISH', {}).get('TRANSPORT', 'tcp'),
            'MQTTPUBLISH__PROTOCOL'          : self.indi_allsky_config.get('MQTTPUBLISH', {}).get('PROTOCOL', 'MQTTv5'),
            'MQTTPUBLISH__HOST'              : self.indi_allsky_config.get('MQTTPUBLISH', {}).get('HOST', 'localhost'),
            'MQTTPUBLISH__PORT'              : self.indi_allsky_config.get('MQTTPUBLISH', {}).get('PORT', 8883),
            'MQTTPUBLISH__USERNAME'          : self.indi_allsky_config.get('MQTTPUBLISH', {}).get('USERNAME', 'indi-allsky'),
            'MQTTPUBLISH__PASSWORD'          : self.indi_allsky_config.get('MQTTPUBLISH', {}).get('PASSWORD', ''),
            'MQTTPUBLISH__BASE_TOPIC'        : self.indi_allsky_config.get('MQTTPUBLISH', {}).get('BASE_TOPIC', 'indi-allsky'),
            'MQTTPUBLISH__QOS'               : self.indi_allsky_config.get('MQTTPUBLISH', {}).get('QOS', 0),
            'MQTTPUBLISH__TLS'               : self.indi_allsky_config.get('MQTTPUBLISH', {}).get('TLS', True),
            'MQTTPUBLISH__CERT_BYPASS'       : self.indi_allsky_config.get('MQTTPUBLISH', {}).get('CERT_BYPASS', True),
            'MQTTPUBLISH__PUBLISH_IMAGE'     : self.indi_allsky_config.get('MQTTPUBLISH', {}).get('PUBLISH_IMAGE', True),
            'SYNCAPI__ENABLE'                : self.indi_allsky_config.get('SYNCAPI', {}).get('ENABLE', False),
            'SYNCAPI__BASEURL'               : self.indi_allsky_config.get('SYNCAPI', {}).get('BASEURL', 'https://example.com/indi-allsky'),
            'SYNCAPI__USERNAME'              : self.indi_allsky_config.get('SYNCAPI', {}).get('USERNAME', ''),
            'SYNCAPI__APIKEY'                : self.indi_allsky_config.get('SYNCAPI', {}).get('APIKEY', ''),
            'SYNCAPI__CERT_BYPASS'           : self.indi_allsky_config.get('SYNCAPI', {}).get('CERT_BYPASS', False),
            'SYNCAPI__POST_S3'               : self.indi_allsky_config.get('SYNCAPI', {}).get('POST_S3', False),
            'SYNCAPI__EMPTY_FILE'            : self.indi_allsky_config.get('SYNCAPI', {}).get('EMPTY_FILE', False),
            'SYNCAPI__UPLOAD_IMAGE'          : self.indi_allsky_config.get('SYNCAPI', {}).get('UPLOAD_IMAGE', 1),
            'SYNCAPI__UPLOAD_PANORAMA'       : self.indi_allsky_config.get('SYNCAPI', {}).get('UPLOAD_PANORAMA', 1),
            'SYNCAPI__UPLOAD_VIDEO'          : True,  # cannot be changed
            'SYNCAPI__CONNECT_TIMEOUT'       : self.indi_allsky_config.get('SYNCAPI', {}).get('CONNECT_TIMEOUT', 10.0),
            'SYNCAPI__TIMEOUT'               : self.indi_allsky_config.get('SYNCAPI', {}).get('TIMEOUT', 60.0),
            'YOUTUBE__ENABLE'                : self.indi_allsky_config.get('YOUTUBE', {}).get('ENABLE', False),
            'YOUTUBE__SECRETS_FILE'          : self.indi_allsky_config.get('YOUTUBE', {}).get('SECRETS_FILE', ''),
            'YOUTUBE__PRIVACY_STATUS'        : self.indi_allsky_config.get('YOUTUBE', {}).get('PRIVACY_STATUS', 'private'),
            'YOUTUBE__TITLE_TEMPLATE'        : self.indi_allsky_config.get('YOUTUBE', {}).get('TITLE_TEMPLATE', 'Allsky {asset_label} - {day_date:%Y-%m-%d} - {timeofday}'),
            'YOUTUBE__DESCRIPTION_TEMPLATE'  : self.indi_allsky_config.get('YOUTUBE', {}).get('DESCRIPTION_TEMPLATE', ''),
            'YOUTUBE__CATEGORY'              : self.indi_allsky_config.get('YOUTUBE', {}).get('CATEGORY', 22),
            'YOUTUBE__UPLOAD_VIDEO'          : self.indi_allsky_config.get('YOUTUBE', {}).get('UPLOAD_VIDEO', False),
            'YOUTUBE__UPLOAD_MINI_VIDEO'     : self.indi_allsky_config.get('YOUTUBE', {}).get('UPLOAD_MINI_VIDEO', False),
            'YOUTUBE__UPLOAD_STARTRAIL_VIDEO': self.indi_allsky_config.get('YOUTUBE', {}).get('UPLOAD_STARTRAIL_VIDEO', False),
            'YOUTUBE__UPLOAD_PANORAMA_VIDEO' : self.indi_allsky_config.get('YOUTUBE', {}).get('UPLOAD_PANORAMA_VIDEO', False),
            'LIBCAMERA__IMAGE_FILE_TYPE'     : self.indi_allsky_config.get('LIBCAMERA', {}).get('IMAGE_FILE_TYPE', 'jpg'),
            'LIBCAMERA__IMAGE_FILE_TYPE_DAY' : self.indi_allsky_config.get('LIBCAMERA', {}).get('IMAGE_FILE_TYPE_DAY', 'jpg'),
            'LIBCAMERA__IMMEDIATE'           : self.indi_allsky_config.get('LIBCAMERA', {}).get('IMMEDIATE', True),
            'LIBCAMERA__IMMEDIATE_DAY'       : self.indi_allsky_config.get('LIBCAMERA', {}).get('IMMEDIATE_DAY', True),
            'LIBCAMERA__AWB'                 : self.indi_allsky_config.get('LIBCAMERA', {}).get('AWB', 'auto'),
            'LIBCAMERA__AWB_DAY'             : self.indi_allsky_config.get('LIBCAMERA', {}).get('AWB_DAY', 'auto'),
            'LIBCAMERA__AWB_ENABLE'          : self.indi_allsky_config.get('LIBCAMERA', {}).get('AWB_ENABLE', True),
            'LIBCAMERA__AWB_ENABLE_DAY'      : self.indi_allsky_config.get('LIBCAMERA', {}).get('AWB_ENABLE_DAY', True),
            'LIBCAMERA__CCM_DISABLE'         : self.indi_allsky_config.get('LIBCAMERA', {}).get('CCM_DISABLE', False),
            'LIBCAMERA__CCM_DISABLE_DAY'     : self.indi_allsky_config.get('LIBCAMERA', {}).get('CCM_DISABLE_DAY', False),
            'LIBCAMERA__CAMERA_ID'           : str(self.indi_allsky_config.get('LIBCAMERA', {}).get('CAMERA_ID', 0)),  # string in form, int in config
            'LIBCAMERA__EXTRA_OPTIONS'       : self.indi_allsky_config.get('LIBCAMERA', {}).get('EXTRA_OPTIONS', ''),
            'LIBCAMERA__EXTRA_OPTIONS_DAY'   : self.indi_allsky_config.get('LIBCAMERA', {}).get('EXTRA_OPTIONS_DAY', ''),
            'LIBCAMERA__MQTT_TRANSPORT'      : self.indi_allsky_config.get('LIBCAMERA', {}).get('MQTT_TRANSPORT', 'tcp'),
            'LIBCAMERA__MQTT_PROTOCOL'       : self.indi_allsky_config.get('LIBCAMERA', {}).get('MQTT_PROTOCOL', 'MQTTv5'),
            'LIBCAMERA__MQTT_HOST'           : self.indi_allsky_config.get('LIBCAMERA', {}).get('MQTT_HOST', 'localhost'),
            'LIBCAMERA__MQTT_PORT'           : self.indi_allsky_config.get('LIBCAMERA', {}).get('MQTT_PORT', 8883),
            'LIBCAMERA__MQTT_USERNAME'       : self.indi_allsky_config.get('LIBCAMERA', {}).get('MQTT_USERNAME', 'indi-allsky'),
            'LIBCAMERA__MQTT_PASSWORD'       : self.indi_allsky_config.get('LIBCAMERA', {}).get('MQTT_PASSWORD', ''),
            'LIBCAMERA__MQTT_QOS'            : self.indi_allsky_config.get('LIBCAMERA', {}).get('MQTT_QOS', 0),
            'LIBCAMERA__MQTT_TLS'            : self.indi_allsky_config.get('LIBCAMERA', {}).get('MQTT_TLS', True),
            'LIBCAMERA__MQTT_CERT_BYPASS'    : self.indi_allsky_config.get('LIBCAMERA', {}).get('MQTT_CERT_BYPASS', True),
            'LIBCAMERA__MQTT_EXPOSURE_TOPIC' : self.indi_allsky_config.get('LIBCAMERA', {}).get('MQTT_EXPOSURE_TOPIC', 'libcamera/exposure'),
            'LIBCAMERA__MQTT_IMAGE_TOPIC'    : self.indi_allsky_config.get('LIBCAMERA', {}).get('MQTT_IMAGE_TOPIC', 'libcamera/image'),
            'LIBCAMERA__MQTT_METADATA_TOPIC' : self.indi_allsky_config.get('LIBCAMERA', {}).get('MQTT_METADATA_TOPIC', 'libcamera/metadata'),
            'PYCURL_CAMERA__URL'             : self.indi_allsky_config.get('PYCURL_CAMERA', {}).get('URL', ''),
            'PYCURL_CAMERA__IMAGE_FILE_TYPE' : self.indi_allsky_config.get('PYCURL_CAMERA', {}).get('IMAGE_FILE_TYPE', 'jpg'),
            'PYCURL_CAMERA__USERNAME'        : self.indi_allsky_config.get('PYCURL_CAMERA', {}).get('USERNAME', ''),
            'PYCURL_CAMERA__PASSWORD'        : self.indi_allsky_config.get('PYCURL_CAMERA', {}).get('PASSWORD', ''),
            'ACCUM_CAMERA__SUB_EXPOSURE_MAX' : self.indi_allsky_config.get('ACCUM_CAMERA', {}).get('SUB_EXPOSURE_MAX', 1.0),
            'ACCUM_CAMERA__EVEN_EXPOSURES'   : self.indi_allsky_config.get('ACCUM_CAMERA', {}).get('EVEN_EXPOSURES', True),
            'ACCUM_CAMERA__CLAMP_16BIT'      : self.indi_allsky_config.get('ACCUM_CAMERA', {}).get('CLAMP_16BIT', False),
            'TEST_CAMERA__WIDTH'             : self.indi_allsky_config.get('TEST_CAMERA', {}).get('WIDTH', 4056),
            'TEST_CAMERA__HEIGHT'            : self.indi_allsky_config.get('TEST_CAMERA', {}).get('HEIGHT', 3040),
            'TEST_CAMERA__IMAGE_CIRCLE_DIAMETER': self.indi_allsky_config.get('TEST_CAMERA', {}).get('IMAGE_CIRCLE_DIAMETER', 3500),
            'TEST_CAMERA__IMAGE_CIRCLE_OFFSET_X': self.indi_allsky_config.get('TEST_CAMERA', {}).get('IMAGE_CIRCLE_OFFSET_X', 0),
            'TEST_CAMERA__IMAGE_CIRCLE_OFFSET_Y': self.indi_allsky_config.get('TEST_CAMERA', {}).get('IMAGE_CIRCLE_OFFSET_Y', 0),
            'TEST_CAMERA__ROTATING_STAR_COUNT'  : self.indi_allsky_config.get('TEST_CAMERA', {}).get('ROTATING_STAR_COUNT', 30000),
            'TEST_CAMERA__ROTATING_STAR_FACTOR' : self.indi_allsky_config.get('TEST_CAMERA', {}).get('ROTATING_STAR_FACTOR', 1.0),
            'TEST_CAMERA__BUBBLE_COUNT'      : self.indi_allsky_config.get('TEST_CAMERA', {}).get('BUBBLE_COUNT', 1000),
            'VIRTUALSKY__MAGNITUDE'          : self.indi_allsky_config.get('VIRTUALSKY', {}).get('MAGNITUDE', 6.0),
            'VIRTUALSKY__CONSTELLATIONS'     : self.indi_allsky_config.get('VIRTUALSKY', {}).get('CONSTELLATIONS', True),
            'VIRTUALSKY__CONSTELLATIONLABELS': self.indi_allsky_config.get('VIRTUALSKY', {}).get('CONSTELLATIONLABELS', False),
            'VIRTUALSKY__SHOWSTARS'          : self.indi_allsky_config.get('VIRTUALSKY', {}).get('SHOWSTARS', True),
            'VIRTUALSKY__SHOWSTARLABELS'     : self.indi_allsky_config.get('VIRTUALSKY', {}).get('SHOWSTARLABELS', True),
            'VIRTUALSKY__SHOWPLANETS'        : self.indi_allsky_config.get('VIRTUALSKY', {}).get('SHOWPLANETS', True),
            'VIRTUALSKY__SHOWPLANETLABELS'   : self.indi_allsky_config.get('VIRTUALSKY', {}).get('SHOWPLANETLABELS', True),
            'VIRTUALSKY__IMAGE_CIRCLE_DIAMETER' : self.indi_allsky_config.get('VIRTUALSKY', {}).get('IMAGE_CIRCLE_DIAMETER', 3500),
            'VIRTUALSKY__LATITUDE_OFFSET'    : self.indi_allsky_config.get('VIRTUALSKY', {}).get('LATITUDE_OFFSET', 0.0),
            'VIRTUALSKY__LONGITUDE_OFFSET'   : self.indi_allsky_config.get('VIRTUALSKY', {}).get('LONGITUDE_OFFSET', 0.0),
            'VIRTUALSKY__OFFSET_X'           : self.indi_allsky_config.get('VIRTUALSKY', {}).get('OFFSET_X', 0),
            'VIRTUALSKY__OFFSET_Y'           : self.indi_allsky_config.get('VIRTUALSKY', {}).get('OFFSET_Y', 0),
            #'VIRTUALSKY__FLIP_NS'            : self.indi_allsky_config.get('VIRTUALSKY', {}).get('FLIP_NS', False),
            #'VIRTUALSKY__FLIP_EW'            : self.indi_allsky_config.get('VIRTUALSKY', {}).get('FLIP_EW', False),
            'CIRCULAR_DISPLAY__ENABLE'       : self.indi_allsky_config.get('CIRCULAR_DISPLAY', {}).get('ENABLE', False),
            'CIRCULAR_DISPLAY__RESOLUTION'   : str(self.indi_allsky_config.get('CIRCULAR_DISPLAY', {}).get('RESOLUTION', 800)),  # string in form, int in config
            'CIRCULAR_DISPLAY__IMAGE_CIRCLE_DIAMETER' : self.indi_allsky_config.get('CIRCULAR_DISPLAY', {}).get('IMAGE_CIRCLE_DIAMETER', 3500),
            'FOCUSER__CLASSNAME'             : self.indi_allsky_config.get('FOCUSER', {}).get('CLASSNAME', ''),
            'FOCUSER__GPIO_PIN_1'            : self.indi_allsky_config.get('FOCUSER', {}).get('GPIO_PIN_1', 'D17'),
            'FOCUSER__GPIO_PIN_2'            : self.indi_allsky_config.get('FOCUSER', {}).get('GPIO_PIN_2', 'D18'),
            'FOCUSER__GPIO_PIN_3'            : self.indi_allsky_config.get('FOCUSER', {}).get('GPIO_PIN_3', 'D27'),
            'FOCUSER__GPIO_PIN_4'            : self.indi_allsky_config.get('FOCUSER', {}).get('GPIO_PIN_4', 'D22'),
            'FOCUSER__I2C_ADDRESS'           : self.indi_allsky_config.get('FOCUSER', {}).get('I2C_ADDRESS', '0x60'),
            'DEW_HEATER__CLASSNAME'          : self.indi_allsky_config.get('DEW_HEATER', {}).get('CLASSNAME', ''),
            'DEW_HEATER__I2C_ADDRESS'        : self.indi_allsky_config.get('DEW_HEATER', {}).get('I2C_ADDRESS', '0x10'),
            'DEW_HEATER__PIN_1'              : self.indi_allsky_config.get('DEW_HEATER', {}).get('PIN_1', 'D12'),
            'DEW_HEATER__INVERT_OUTPUT'      : self.indi_allsky_config.get('DEW_HEATER', {}).get('INVERT_OUTPUT', False),
            'DEW_HEATER__ENABLE_DAY'         : self.indi_allsky_config.get('DEW_HEATER', {}).get('ENABLE_DAY', False),
            'DEW_HEATER__LEVEL_DEF'          : self.indi_allsky_config.get('DEW_HEATER', {}).get('LEVEL_DEF', 100),
            'DEW_HEATER__THOLD_ENABLE'       : self.indi_allsky_config.get('DEW_HEATER', {}).get('THOLD_ENABLE', False),
            'DEW_HEATER__MANUAL_TARGET'      : self.indi_allsky_config.get('DEW_HEATER', {}).get('MANUAL_TARGET', 0.0),
            'DEW_HEATER__TEMP_USER_VAR_SLOT' : self.indi_allsky_config.get('DEW_HEATER', {}).get('TEMP_USER_VAR_SLOT', 'sensor_user_10'),
            'DEW_HEATER__DEWPOINT_USER_VAR_SLOT' : self.indi_allsky_config.get('DEW_HEATER', {}).get('DEWPOINT_USER_VAR_SLOT', 'sensor_user_2'),
            'DEW_HEATER__LEVEL_LOW'          : self.indi_allsky_config.get('DEW_HEATER', {}).get('LEVEL_LOW', 33),
            'DEW_HEATER__LEVEL_MED'          : self.indi_allsky_config.get('DEW_HEATER', {}).get('LEVEL_MED', 66),
            'DEW_HEATER__LEVEL_HIGH'         : self.indi_allsky_config.get('DEW_HEATER', {}).get('LEVEL_HIGH', 100),
            'DEW_HEATER__THOLD_DIFF_LOW'     : '{0:+d}'.format(self.indi_allsky_config.get('DEW_HEATER', {}).get('THOLD_DIFF_LOW', 15)),  # str for sign
            'DEW_HEATER__THOLD_DIFF_MED'     : '{0:+d}'.format(self.indi_allsky_config.get('DEW_HEATER', {}).get('THOLD_DIFF_MED', 10)),
            'DEW_HEATER__THOLD_DIFF_HIGH'    : '{0:+d}'.format(self.indi_allsky_config.get('DEW_HEATER', {}).get('THOLD_DIFF_HIGH', 5)),
            'DEW_HEATER__HOLD_SECONDS'       : self.indi_allsky_config.get('DEW_HEATER', {}).get('HOLD_SECONDS', 0),
            'DEW_HEATER__PWM_FREQUENCY'      : self.indi_allsky_config.get('DEW_HEATER', {}).get('PWM_FREQUENCY', 500),
            'FAN__CLASSNAME'                 : self.indi_allsky_config.get('FAN', {}).get('CLASSNAME', ''),
            'FAN__I2C_ADDRESS'               : self.indi_allsky_config.get('FAN', {}).get('I2C_ADDRESS', '0x11'),
            'FAN__PIN_1'                     : self.indi_allsky_config.get('FAN', {}).get('PIN_1', 'D13'),
            'FAN__INVERT_OUTPUT'             : self.indi_allsky_config.get('FAN', {}).get('INVERT_OUTPUT', False),
            'FAN__ENABLE_NIGHT'              : self.indi_allsky_config.get('FAN', {}).get('ENABLE_NIGHT', False),
            'FAN__LEVEL_DEF'                 : self.indi_allsky_config.get('FAN', {}).get('LEVEL_DEF', 100),
            'FAN__THOLD_ENABLE'              : self.indi_allsky_config.get('FAN', {}).get('THOLD_ENABLE', False),
            'FAN__TARGET'                    : self.indi_allsky_config.get('FAN', {}).get('TARGET', 30.0),
            'FAN__TEMP_USER_VAR_SLOT'        : self.indi_allsky_config.get('FAN', {}).get('TEMP_USER_VAR_SLOT', 'sensor_user_10'),
            'FAN__LEVEL_LOW'                 : self.indi_allsky_config.get('FAN', {}).get('LEVEL_LOW', 33),
            'FAN__LEVEL_MED'                 : self.indi_allsky_config.get('FAN', {}).get('LEVEL_MED', 66),
            'FAN__LEVEL_HIGH'                : self.indi_allsky_config.get('FAN', {}).get('LEVEL_HIGH', 100),
            'FAN__THOLD_DIFF_LOW'            : '{0:+d}'.format(self.indi_allsky_config.get('FAN', {}).get('THOLD_DIFF_LOW', -10)),  # str for sign
            'FAN__THOLD_DIFF_MED'            : '{0:+d}'.format(self.indi_allsky_config.get('FAN', {}).get('THOLD_DIFF_MED', -5)),
            'FAN__THOLD_DIFF_HIGH'           : '{0:+d}'.format(self.indi_allsky_config.get('FAN', {}).get('THOLD_DIFF_HIGH', 0)),
            'FAN__HOLD_SECONDS'              : self.indi_allsky_config.get('FAN', {}).get('HOLD_SECONDS', 0),
            'FAN__PWM_FREQUENCY'             : self.indi_allsky_config.get('FAN', {}).get('PWM_FREQUENCY', 500),
            'GENERIC_GPIO__A_CLASSNAME'      : self.indi_allsky_config.get('GENERIC_GPIO', {}).get('A_CLASSNAME', ''),
            'GENERIC_GPIO__A_I2C_ADDRESS'    : self.indi_allsky_config.get('GENERIC_GPIO', {}).get('A_I2C_ADDRESS', '0x12'),
            'GENERIC_GPIO__A_PIN_1'          : self.indi_allsky_config.get('GENERIC_GPIO', {}).get('A_PIN_1', 'D21'),
            'GENERIC_GPIO__A_INVERT_OUTPUT'  : self.indi_allsky_config.get('GENERIC_GPIO', {}).get('A_INVERT_OUTPUT', False),
            'MANUAL_GPIO__A_CLASSNAME'       : self.indi_allsky_config.get('MANUAL_GPIO', {}).get('A_CLASSNAME', ''),
            'MANUAL_GPIO__A_PIN_1'           : self.indi_allsky_config.get('MANUAL_GPIO', {}).get('A_PIN_1', '21'),
            'MANUAL_GPIO__A_PIN_2'           : self.indi_allsky_config.get('MANUAL_GPIO', {}).get('A_PIN_2', '25'),
            'MANUAL_GPIO__A_PIN_3'           : self.indi_allsky_config.get('MANUAL_GPIO', {}).get('A_PIN_3', '16'),
            'DEVICE__MQTT_TRANSPORT'         : self.indi_allsky_config.get('DEVICE', {}).get('MQTT_TRANSPORT', 'tcp'),
            'DEVICE__MQTT_PROTOCOL'          : self.indi_allsky_config.get('DEVICE', {}).get('MQTT_PROTOCOL', 'MQTTv5'),
            'DEVICE__MQTT_HOST'              : self.indi_allsky_config.get('DEVICE', {}).get('MQTT_HOST', 'localhost'),
            'DEVICE__MQTT_PORT'              : self.indi_allsky_config.get('DEVICE', {}).get('MQTT_PORT', 8883),
            'DEVICE__MQTT_USERNAME'          : self.indi_allsky_config.get('DEVICE', {}).get('MQTT_USERNAME', 'indi-allsky'),
            'DEVICE__MQTT_PASSWORD'          : self.indi_allsky_config.get('DEVICE', {}).get('MQTT_PASSWORD', ''),
            'DEVICE__MQTT_QOS'               : self.indi_allsky_config.get('DEVICE', {}).get('MQTT_QOS', 0),
            'DEVICE__MQTT_TLS'               : self.indi_allsky_config.get('DEVICE', {}).get('MQTT_TLS', True),
            'DEVICE__MQTT_CERT_BYPASS'       : self.indi_allsky_config.get('DEVICE', {}).get('MQTT_CERT_BYPASS', True),
            'TEMP_SENSOR__A_CLASSNAME'       : self.indi_allsky_config.get('TEMP_SENSOR', {}).get('A_CLASSNAME', ''),
            'TEMP_SENSOR__A_LABEL'           : self.indi_allsky_config.get('TEMP_SENSOR', {}).get('A_LABEL', 'Sensor A'),
            'TEMP_SENSOR__A_PIN_1'           : self.indi_allsky_config.get('TEMP_SENSOR', {}).get('A_PIN_1', 'D5'),
            'TEMP_SENSOR__A_PIN_2'           : self.indi_allsky_config.get('TEMP_SENSOR', {}).get('A_PIN_2', ''),
            'TEMP_SENSOR__A_I2C_ADDRESS'     : self.indi_allsky_config.get('TEMP_SENSOR', {}).get('A_I2C_ADDRESS', '0x77'),
            'TEMP_SENSOR__A_USER_VAR_SLOT'   : self.indi_allsky_config.get('TEMP_SENSOR', {}).get('A_USER_VAR_SLOT', 'sensor_user_10'),
            'TEMP_SENSOR__A_TITLE_TEMPLATE'  : self.indi_allsky_config.get('TEMP_SENSOR', {}).get('A_TITLE_TEMPLATE', '{name:s} - {label:s} - {probe:s}'),
            'TEMP_SENSOR__B_CLASSNAME'       : self.indi_allsky_config.get('TEMP_SENSOR', {}).get('B_CLASSNAME', ''),
            'TEMP_SENSOR__B_LABEL'           : self.indi_allsky_config.get('TEMP_SENSOR', {}).get('B_LABEL', 'Sensor B'),
            'TEMP_SENSOR__B_PIN_1'           : self.indi_allsky_config.get('TEMP_SENSOR', {}).get('B_PIN_1', 'D6'),
            'TEMP_SENSOR__B_PIN_2'           : self.indi_allsky_config.get('TEMP_SENSOR', {}).get('B_PIN_2', ''),
            'TEMP_SENSOR__B_I2C_ADDRESS'     : self.indi_allsky_config.get('TEMP_SENSOR', {}).get('B_I2C_ADDRESS', '0x76'),
            'TEMP_SENSOR__B_USER_VAR_SLOT'   : self.indi_allsky_config.get('TEMP_SENSOR', {}).get('B_USER_VAR_SLOT', 'sensor_user_20'),
            'TEMP_SENSOR__B_TITLE_TEMPLATE'  : self.indi_allsky_config.get('TEMP_SENSOR', {}).get('B_TITLE_TEMPLATE', '{name:s} - {label:s} - {probe:s}'),
            'TEMP_SENSOR__C_CLASSNAME'       : self.indi_allsky_config.get('TEMP_SENSOR', {}).get('C_CLASSNAME', ''),
            'TEMP_SENSOR__C_LABEL'           : self.indi_allsky_config.get('TEMP_SENSOR', {}).get('C_LABEL', 'Sensor C'),
            'TEMP_SENSOR__C_PIN_1'           : self.indi_allsky_config.get('TEMP_SENSOR', {}).get('C_PIN_1', 'D16'),
            'TEMP_SENSOR__C_PIN_2'           : self.indi_allsky_config.get('TEMP_SENSOR', {}).get('C_PIN_2', ''),
            'TEMP_SENSOR__C_I2C_ADDRESS'     : self.indi_allsky_config.get('TEMP_SENSOR', {}).get('C_I2C_ADDRESS', '0x40'),
            'TEMP_SENSOR__C_USER_VAR_SLOT'   : self.indi_allsky_config.get('TEMP_SENSOR', {}).get('C_USER_VAR_SLOT', 'sensor_user_30'),
            'TEMP_SENSOR__C_TITLE_TEMPLATE'  : self.indi_allsky_config.get('TEMP_SENSOR', {}).get('C_TITLE_TEMPLATE', '{name:s} - {label:s} - {probe:s}'),
            'TEMP_SENSOR__D_CLASSNAME'       : self.indi_allsky_config.get('TEMP_SENSOR', {}).get('D_CLASSNAME', ''),
            'TEMP_SENSOR__D_LABEL'           : self.indi_allsky_config.get('TEMP_SENSOR', {}).get('D_LABEL', 'Sensor D'),
            'TEMP_SENSOR__D_PIN_1'           : self.indi_allsky_config.get('TEMP_SENSOR', {}).get('D_PIN_1', 'D26'),
            'TEMP_SENSOR__D_PIN_2'           : self.indi_allsky_config.get('TEMP_SENSOR', {}).get('D_PIN_2', ''),
            'TEMP_SENSOR__D_I2C_ADDRESS'     : self.indi_allsky_config.get('TEMP_SENSOR', {}).get('D_I2C_ADDRESS', '0x50'),
            'TEMP_SENSOR__D_USER_VAR_SLOT'   : self.indi_allsky_config.get('TEMP_SENSOR', {}).get('D_USER_VAR_SLOT', 'sensor_user_40'),
            'TEMP_SENSOR__D_TITLE_TEMPLATE'  : self.indi_allsky_config.get('TEMP_SENSOR', {}).get('D_TITLE_TEMPLATE', '{name:s} - {label:s} - {probe:s}'),
            'TEMP_SENSOR__E_CLASSNAME'       : self.indi_allsky_config.get('TEMP_SENSOR', {}).get('E_CLASSNAME', ''),
            'TEMP_SENSOR__E_LABEL'           : self.indi_allsky_config.get('TEMP_SENSOR', {}).get('E_LABEL', 'Sensor E'),
            'TEMP_SENSOR__E_PIN_1'           : self.indi_allsky_config.get('TEMP_SENSOR', {}).get('E_PIN_1', 'D25'),
            'TEMP_SENSOR__E_PIN_2'           : self.indi_allsky_config.get('TEMP_SENSOR', {}).get('E_PIN_2', ''),
            'TEMP_SENSOR__E_I2C_ADDRESS'     : self.indi_allsky_config.get('TEMP_SENSOR', {}).get('E_I2C_ADDRESS', '0x51'),
            'TEMP_SENSOR__E_USER_VAR_SLOT'   : self.indi_allsky_config.get('TEMP_SENSOR', {}).get('E_USER_VAR_SLOT', 'sensor_user_50'),
            'TEMP_SENSOR__E_TITLE_TEMPLATE'  : self.indi_allsky_config.get('TEMP_SENSOR', {}).get('E_TITLE_TEMPLATE', '{name:s} - {label:s} - {probe:s}'),
            'TEMP_SENSOR__F_CLASSNAME'       : self.indi_allsky_config.get('TEMP_SENSOR', {}).get('F_CLASSNAME', ''),
            'TEMP_SENSOR__F_LABEL'           : self.indi_allsky_config.get('TEMP_SENSOR', {}).get('F_LABEL', 'Sensor F'),
            'TEMP_SENSOR__F_PIN_1'           : self.indi_allsky_config.get('TEMP_SENSOR', {}).get('F_PIN_1', 'D27'),
            'TEMP_SENSOR__F_PIN_2'           : self.indi_allsky_config.get('TEMP_SENSOR', {}).get('F_PIN_2', ''),
            'TEMP_SENSOR__F_I2C_ADDRESS'     : self.indi_allsky_config.get('TEMP_SENSOR', {}).get('F_I2C_ADDRESS', '0x52'),
            'TEMP_SENSOR__F_USER_VAR_SLOT'   : self.indi_allsky_config.get('TEMP_SENSOR', {}).get('F_USER_VAR_SLOT', 'sensor_user_55'),
            'TEMP_SENSOR__F_TITLE_TEMPLATE'  : self.indi_allsky_config.get('TEMP_SENSOR', {}).get('F_TITLE_TEMPLATE', '{name:s} - {label:s} - {probe:s}'),
            'TEMP_SENSOR__FC37_ACTIVE_LOW'   : self.indi_allsky_config.get('TEMP_SENSOR', {}).get('FC37_ACTIVE_LOW', True),
            'TEMP_SENSOR__OPENWEATHERMAP_APIKEY' : self.indi_allsky_config.get('TEMP_SENSOR', {}).get('OPENWEATHERMAP_APIKEY', ''),
            'TEMP_SENSOR__WUNDERGROUND_APIKEY'   : self.indi_allsky_config.get('TEMP_SENSOR', {}).get('WUNDERGROUND_APIKEY', ''),
            'TEMP_SENSOR__ASTROSPHERIC_APIKEY'   : self.indi_allsky_config.get('TEMP_SENSOR', {}).get('ASTROSPHERIC_APIKEY', ''),
            'TEMP_SENSOR__AMBIENTWEATHER_APIKEY'           : self.indi_allsky_config.get('TEMP_SENSOR', {}).get('AMBIENTWEATHER_APIKEY', ''),
            'TEMP_SENSOR__AMBIENTWEATHER_APPLICATIONKEY'   : self.indi_allsky_config.get('TEMP_SENSOR', {}).get('AMBIENTWEATHER_APPLICATIONKEY', ''),
            'TEMP_SENSOR__AMBIENTWEATHER_MACADDRESS'       : self.indi_allsky_config.get('TEMP_SENSOR', {}).get('AMBIENTWEATHER_MACADDRESS', ''),
            'TEMP_SENSOR__ECOWITT_APIKEY'           : self.indi_allsky_config.get('TEMP_SENSOR', {}).get('ECOWITT_APIKEY', ''),
            'TEMP_SENSOR__ECOWITT_APPLICATIONKEY'   : self.indi_allsky_config.get('TEMP_SENSOR', {}).get('ECOWITT_APPLICATIONKEY', ''),
            'TEMP_SENSOR__ECOWITT_MACADDRESS'       : self.indi_allsky_config.get('TEMP_SENSOR', {}).get('ECOWITT_MACADDRESS', ''),
            'TEMP_SENSOR__MQTT_TRANSPORT'    : self.indi_allsky_config.get('TEMP_SENSOR', {}).get('MQTT_TRANSPORT', 'tcp'),
            'TEMP_SENSOR__MQTT_PROTOCOL'     : self.indi_allsky_config.get('TEMP_SENSOR', {}).get('MQTT_PROTOCOL', 'MQTTv5'),
            'TEMP_SENSOR__MQTT_HOST'         : self.indi_allsky_config.get('TEMP_SENSOR', {}).get('MQTT_HOST', 'localhost'),
            'TEMP_SENSOR__MQTT_PORT'         : self.indi_allsky_config.get('TEMP_SENSOR', {}).get('MQTT_PORT', 8883),
            'TEMP_SENSOR__MQTT_USERNAME'     : self.indi_allsky_config.get('TEMP_SENSOR', {}).get('MQTT_USERNAME', 'indi-allsky'),
            'TEMP_SENSOR__MQTT_PASSWORD'     : self.indi_allsky_config.get('TEMP_SENSOR', {}).get('MQTT_PASSWORD', ''),
            'TEMP_SENSOR__MQTT_TLS'          : self.indi_allsky_config.get('TEMP_SENSOR', {}).get('MQTT_TLS', True),
            'TEMP_SENSOR__MQTT_CERT_BYPASS'  : self.indi_allsky_config.get('TEMP_SENSOR', {}).get('MQTT_CERT_BYPASS', True),
            'TEMP_SENSOR__DHT_USE_PULSEIO'   : self.indi_allsky_config.get('TEMP_SENSOR', {}).get('DHT_USE_PULSEIO', False),
            'TEMP_SENSOR__SHT3X_HEATER_NIGHT': self.indi_allsky_config.get('TEMP_SENSOR', {}).get('SHT3X_HEATER_NIGHT', False),
            'TEMP_SENSOR__SHT3X_HEATER_DAY'  : self.indi_allsky_config.get('TEMP_SENSOR', {}).get('SHT3X_HEATER_DAY', False),
            'TEMP_SENSOR__SHT4X_MODE_NIGHT'  : self.indi_allsky_config.get('TEMP_SENSOR', {}).get('SHT4X_MODE_NIGHT', 'NOHEAT_HIGHPRECISION'),
            'TEMP_SENSOR__SHT4X_MODE_DAY'    : self.indi_allsky_config.get('TEMP_SENSOR', {}).get('SHT4X_MODE_DAY', 'NOHEAT_HIGHPRECISION'),
            'TEMP_SENSOR__SI7021_HEATER_LEVEL_NIGHT' : str(self.indi_allsky_config.get('TEMP_SENSOR', {}).get('SI7021_HEATER_LEVEL_NIGHT', -1)),  # string in form, int in config
            'TEMP_SENSOR__SI7021_HEATER_LEVEL_DAY' : str(self.indi_allsky_config.get('TEMP_SENSOR', {}).get('SI7021_HEATER_LEVEL_DAY', -1)),  # string in form, int in config
            'TEMP_SENSOR__HTU31D_HEATER_NIGHT': self.indi_allsky_config.get('TEMP_SENSOR', {}).get('HTU31D_HEATER_NIGHT', False),
            'TEMP_SENSOR__HTU31D_HEATER_DAY'  : self.indi_allsky_config.get('TEMP_SENSOR', {}).get('HTU31D_HEATER_DAY', False),
            'TEMP_SENSOR__HDC302X_HEATER_NIGHT'  : self.indi_allsky_config.get('TEMP_SENSOR', {}).get('HDC302X_HEATER_NIGHT', 'OFF'),
            'TEMP_SENSOR__HDC302X_HEATER_DAY'    : self.indi_allsky_config.get('TEMP_SENSOR', {}).get('HDC302X_HEATER_DAY', 'OFF'),
            'TEMP_SENSOR__TSL2561_GAIN_NIGHT': str(self.indi_allsky_config.get('TEMP_SENSOR', {}).get('TSL2561_GAIN_NIGHT', 1)),  # string in form, int in config
            'TEMP_SENSOR__TSL2561_GAIN_DAY'  : str(self.indi_allsky_config.get('TEMP_SENSOR', {}).get('TSL2561_GAIN_DAY', 0)),  # string in form, int in config
            'TEMP_SENSOR__TSL2561_INT_NIGHT' : str(self.indi_allsky_config.get('TEMP_SENSOR', {}).get('TSL2561_INT_NIGHT', 1)),  # string in form, int in config
            'TEMP_SENSOR__TSL2561_INT_DAY'   : str(self.indi_allsky_config.get('TEMP_SENSOR', {}).get('TSL2561_INT_DAY', 1)),  # string in form, int in config
            'TEMP_SENSOR__TSL2561_DISABLE_DAY' : self.indi_allsky_config.get('TEMP_SENSOR', {}).get('TSL2561_DISABLE_DAY', False),
            'TEMP_SENSOR__TSL2591_GAIN_NIGHT': self.indi_allsky_config.get('TEMP_SENSOR', {}).get('TSL2591_GAIN_NIGHT', 'GAIN_MED'),
            'TEMP_SENSOR__TSL2591_GAIN_DAY'  : self.indi_allsky_config.get('TEMP_SENSOR', {}).get('TSL2591_GAIN_DAY', 'GAIN_LOW'),
            'TEMP_SENSOR__TSL2591_INT_NIGHT' : self.indi_allsky_config.get('TEMP_SENSOR', {}).get('TSL2591_INT_NIGHT', 'INTEGRATIONTIME_100MS'),
            'TEMP_SENSOR__TSL2591_INT_DAY'   : self.indi_allsky_config.get('TEMP_SENSOR', {}).get('TSL2591_INT_DAY', 'INTEGRATIONTIME_100MS'),
            'TEMP_SENSOR__TSL2591_DISABLE_DAY' : self.indi_allsky_config.get('TEMP_SENSOR', {}).get('TSL2591_DISABLE_DAY', False),
            'TEMP_SENSOR__VEML7700_GAIN_NIGHT': self.indi_allsky_config.get('TEMP_SENSOR', {}).get('VEML7700_GAIN_NIGHT', 'ALS_GAIN_1'),
            'TEMP_SENSOR__VEML7700_GAIN_DAY' : self.indi_allsky_config.get('TEMP_SENSOR', {}).get('VEML7700_GAIN_DAY', 'ALS_GAIN_1_8'),
            'TEMP_SENSOR__VEML7700_INT_NIGHT': self.indi_allsky_config.get('TEMP_SENSOR', {}).get('VEML7700_INT_NIGHT', 'ALS_100MS'),
            'TEMP_SENSOR__VEML7700_INT_DAY'  : self.indi_allsky_config.get('TEMP_SENSOR', {}).get('VEML7700_INT_DAY', 'ALS_100MS'),
            'TEMP_SENSOR__SI1145_VIS_GAIN_NIGHT' : self.indi_allsky_config.get('TEMP_SENSOR', {}).get('SI1145_VIS_GAIN_NIGHT', 'GAIN_ADC_CLOCK_DIV_32'),
            'TEMP_SENSOR__SI1145_VIS_GAIN_DAY'   : self.indi_allsky_config.get('TEMP_SENSOR', {}).get('SI1145_VIS_GAIN_DAY', 'GAIN_ADC_CLOCK_DIV_1'),
            'TEMP_SENSOR__SI1145_IR_GAIN_NIGHT'  : self.indi_allsky_config.get('TEMP_SENSOR', {}).get('SI1145_IR_GAIN_NIGHT', 'GAIN_ADC_CLOCK_DIV_32'),
            'TEMP_SENSOR__SI1145_IR_GAIN_DAY'    : self.indi_allsky_config.get('TEMP_SENSOR', {}).get('SI1145_IR_GAIN_DAY', 'GAIN_ADC_CLOCK_DIV_1'),
            'TEMP_SENSOR__LTR390_GAIN_NIGHT'     : self.indi_allsky_config.get('TEMP_SENSOR', {}).get('LTR390_GAIN_NIGHT', 'GAIN_9X'),
            'TEMP_SENSOR__LTR390_GAIN_DAY'       : self.indi_allsky_config.get('TEMP_SENSOR', {}).get('LTR390_GAIN_DAY', 'GAIN_1X'),
            'TEMP_SENSOR__INA3221_CH1_ENABLE'    : self.indi_allsky_config.get('TEMP_SENSOR', {}).get('INA3221_CH1_ENABLE', True),
            'TEMP_SENSOR__INA3221_CH2_ENABLE'    : self.indi_allsky_config.get('TEMP_SENSOR', {}).get('INA3221_CH2_ENABLE', True),
            'TEMP_SENSOR__INA3221_CH3_ENABLE'    : self.indi_allsky_config.get('TEMP_SENSOR', {}).get('INA3221_CH3_ENABLE', True),
            'TEMP_SENSOR__AS3935_OUTDOOR_MODE'   : self.indi_allsky_config.get('TEMP_SENSOR', {}).get('AS3935_OUTDOOR_MODE', True),
            'TEMP_SENSOR__AS3935_MASK_DISTURBER' : self.indi_allsky_config.get('TEMP_SENSOR', {}).get('AS3935_MASK_DISTURBER', False),
            'TEMP_SENSOR__AS3935_NOISE_LEVEL'    : self.indi_allsky_config.get('TEMP_SENSOR', {}).get('AS3935_NOISE_LEVEL', 2),
            'TEMP_SENSOR__AS3935_SPIKE_REJECTION': self.indi_allsky_config.get('TEMP_SENSOR', {}).get('AS3935_SPIKE_REJECTION', 2),
            'TEMP_SENSOR__LUX_MAGNITUDE_OFFSET'  : self.indi_allsky_config.get('TEMP_SENSOR', {}).get('LUX_MAGNITUDE_OFFSET', 26.0),
            'CHARTS__CUSTOM_SLOT_1'          : self.indi_allsky_config.get('CHARTS', {}).get('CUSTOM_SLOT_1', 'sensor_user_10'),
            'CHARTS__CUSTOM_SLOT_1_MIN'      : self.indi_allsky_config.get('CHARTS', {}).get('CUSTOM_SLOT_1_MIN', 0.0),
            'CHARTS__CUSTOM_SLOT_2'          : self.indi_allsky_config.get('CHARTS', {}).get('CUSTOM_SLOT_2', 'sensor_user_11'),
            'CHARTS__CUSTOM_SLOT_2_MIN'      : self.indi_allsky_config.get('CHARTS', {}).get('CUSTOM_SLOT_2_MIN', 0.0),
            'CHARTS__CUSTOM_SLOT_3'          : self.indi_allsky_config.get('CHARTS', {}).get('CUSTOM_SLOT_3', 'sensor_user_12'),
            'CHARTS__CUSTOM_SLOT_3_MIN'      : self.indi_allsky_config.get('CHARTS', {}).get('CUSTOM_SLOT_3_MIN', 0.0),
            'CHARTS__CUSTOM_SLOT_4'          : self.indi_allsky_config.get('CHARTS', {}).get('CUSTOM_SLOT_4', 'sensor_user_13'),
            'CHARTS__CUSTOM_SLOT_4_MIN'      : self.indi_allsky_config.get('CHARTS', {}).get('CUSTOM_SLOT_4_MIN', 0.0),
            'CHARTS__CUSTOM_SLOT_5'          : self.indi_allsky_config.get('CHARTS', {}).get('CUSTOM_SLOT_5', 'sensor_user_14'),
            'CHARTS__CUSTOM_SLOT_5_MIN'      : self.indi_allsky_config.get('CHARTS', {}).get('CUSTOM_SLOT_5_MIN', 0.0),
            'CHARTS__CUSTOM_SLOT_6'          : self.indi_allsky_config.get('CHARTS', {}).get('CUSTOM_SLOT_6', 'sensor_user_15'),
            'CHARTS__CUSTOM_SLOT_6_MIN'      : self.indi_allsky_config.get('CHARTS', {}).get('CUSTOM_SLOT_6_MIN', 0.0),
            'CHARTS__CUSTOM_SLOT_7'          : self.indi_allsky_config.get('CHARTS', {}).get('CUSTOM_SLOT_7', 'sensor_user_16'),
            'CHARTS__CUSTOM_SLOT_7_MIN'      : self.indi_allsky_config.get('CHARTS', {}).get('CUSTOM_SLOT_7_MIN', 0.0),
            'CHARTS__CUSTOM_SLOT_8'          : self.indi_allsky_config.get('CHARTS', {}).get('CUSTOM_SLOT_8', 'sensor_user_14'),
            'CHARTS__CUSTOM_SLOT_8_MIN'      : self.indi_allsky_config.get('CHARTS', {}).get('CUSTOM_SLOT_8_MIN', 0.0),
            'CHARTS__CUSTOM_SLOT_9'          : self.indi_allsky_config.get('CHARTS', {}).get('CUSTOM_SLOT_9', 'sensor_user_15'),
            'CHARTS__CUSTOM_SLOT_9_MIN'      : self.indi_allsky_config.get('CHARTS', {}).get('CUSTOM_SLOT_9_MIN', 0.0),
            'ADSB__ENABLE'                   : self.indi_allsky_config.get('ADSB', {}).get('ENABLE', False),
            'ADSB__DUMP1090_URL'             : self.indi_allsky_config.get('ADSB', {}).get('DUMP1090_URL', 'https://localhost/dump1090/data/aircraft.json'),
            'ADSB__USERNAME'                 : self.indi_allsky_config.get('ADSB', {}).get('USERNAME', ''),
            'ADSB__PASSWORD'                 : self.indi_allsky_config.get('ADSB', {}).get('PASSWORD', ''),
            'ADSB__CERT_BYPASS'              : self.indi_allsky_config.get('ADSB', {}).get('CERT_BYPASS', True),
            'ADSB__ALT_DEG_MIN'              : self.indi_allsky_config.get('ADSB', {}).get('ALT_DEG_MIN', 20.0),
            'ADSB__LABEL_ENABLE'             : self.indi_allsky_config.get('ADSB', {}).get('LABEL_ENABLE', True),
            'ADSB__LABEL_LIMIT'              : self.indi_allsky_config.get('ADSB', {}).get('LABEL_LIMIT', 10),
            'ADSB__AIRCRAFT_LABEL_TEMPLATE'  : self.indi_allsky_config.get('ADSB', {}).get('AIRCRAFT_LABEL_TEMPLATE', '{id:s} {distance:0.1f}km {alt:0.1f}\u00b0 {dir:s}'),
            'ADSB__IMAGE_LABEL_TEMPLATE_PREFIX' : self.indi_allsky_config.get('ADSB', {}).get('IMAGE_LABEL_TEMPLATE_PREFIX', '# xy:15,300 (Left)\n# anchor:la (Left Justified)\n# color:200,200,200\nAircraft'),
            'SATELLITE_TRACK__ENABLE'              : self.indi_allsky_config.get('SATELLITE_TRACK', {}).get('ENABLE', False),
            'SATELLITE_TRACK__DAYTIME_TRACK'       : self.indi_allsky_config.get('SATELLITE_TRACK', {}).get('DAYTIME_TRACK', False),
            'SATELLITE_TRACK__ALT_DEG_MIN'         : self.indi_allsky_config.get('SATELLITE_TRACK', {}).get('ALT_DEG_MIN', 20.0),
            'SATELLITE_TRACK__LABEL_ENABLE'        : self.indi_allsky_config.get('SATELLITE_TRACK', {}).get('LABEL_ENABLE', True),
            'SATELLITE_TRACK__LABEL_LIMIT'         : self.indi_allsky_config.get('SATELLITE_TRACK', {}).get('LABEL_LIMIT', 10),
            'SATELLITE_TRACK__SAT_LABEL_TEMPLATE'  : self.indi_allsky_config.get('SATELLITE_TRACK', {}).get('SAT_LABEL_TEMPLATE', '{label:s} {alt:0.1f}\u00b0 {dir:s}'),
            'SATELLITE_TRACK__IMAGE_LABEL_TEMPLATE_PREFIX' : self.indi_allsky_config.get('SATELLITE_TRACK', {}).get('IMAGE_LABEL_TEMPLATE_PREFIX', '# xy:-15,200 (Right)\n# anchor:ra (Right Justified)\n# color:200,200,200\nSatellites'),
            'RELOAD_ON_SAVE'                 : False,
            'CONFIG_NOTE'                    : '',
            'ENCRYPT_PASSWORDS'              : self.indi_allsky_config.get('ENCRYPT_PASSWORDS', False),  # do not adjust
        }


        # ADU_ROI
        ADU_ROI = self.indi_allsky_config.get('ADU_ROI', [])
        if ADU_ROI is None:
            ADU_ROI = []
        elif isinstance(ADU_ROI, bool):
            ADU_ROI = []

        try:
            form_data['ADU_ROI_X1'] = ADU_ROI[0]
        except IndexError:
            form_data['ADU_ROI_X1'] = 0

        try:
            form_data['ADU_ROI_Y1'] = ADU_ROI[1]
        except IndexError:
            form_data['ADU_ROI_Y1'] = 0

        try:
            form_data['ADU_ROI_X2'] = ADU_ROI[2]
        except IndexError:
            form_data['ADU_ROI_X2'] = 0

        try:
            form_data['ADU_ROI_Y2'] = ADU_ROI[3]
        except IndexError:
            form_data['ADU_ROI_Y2'] = 0


        # SQM_ROI
        SQM_ROI = self.indi_allsky_config.get('SQM_ROI', [])
        if SQM_ROI is None:
            SQM_ROI = []
        elif isinstance(SQM_ROI, bool):
            SQM_ROI = []

        try:
            form_data['SQM_ROI_X1'] = SQM_ROI[0]
        except IndexError:
            form_data['SQM_ROI_X1'] = 0

        try:
            form_data['SQM_ROI_Y1'] = SQM_ROI[1]
        except IndexError:
            form_data['SQM_ROI_Y1'] = 0

        try:
            form_data['SQM_ROI_X2'] = SQM_ROI[2]
        except IndexError:
            form_data['SQM_ROI_X2'] = 0

        try:
            form_data['SQM_ROI_Y2'] = SQM_ROI[3]
        except IndexError:
            form_data['SQM_ROI_Y2'] = 0


        # IMAGE_CROP_ROI
        IMAGE_CROP_ROI = self.indi_allsky_config.get('IMAGE_CROP_ROI', [])
        if IMAGE_CROP_ROI is None:
            IMAGE_CROP_ROI = []
        elif isinstance(IMAGE_CROP_ROI, bool):
            IMAGE_CROP_ROI = []

        try:
            form_data['IMAGE_CROP_ROI_X1'] = IMAGE_CROP_ROI[0]
        except IndexError:
            form_data['IMAGE_CROP_ROI_X1'] = 0

        try:
            form_data['IMAGE_CROP_ROI_Y1'] = IMAGE_CROP_ROI[1]
        except IndexError:
            form_data['IMAGE_CROP_ROI_Y1'] = 0

        try:
            form_data['IMAGE_CROP_ROI_X2'] = IMAGE_CROP_ROI[2]
        except IndexError:
            form_data['IMAGE_CROP_ROI_X2'] = 0

        try:
            form_data['IMAGE_CROP_ROI_Y2'] = IMAGE_CROP_ROI[3]
        except IndexError:
            form_data['IMAGE_CROP_ROI_Y2'] = 0


        # Font color
        text_properties__font_color = self.indi_allsky_config.get('TEXT_PROPERTIES', {}).get('FONT_COLOR', [200, 200, 200])
        form_data['TEXT_PROPERTIES__FONT_COLOR'] = ','.join([str(x) for x in text_properties__font_color])

        # Cardinal directions color
        cardinal_dirs__font_color = self.indi_allsky_config.get('CARDINAL_DIRS', {}).get('FONT_COLOR', [200, 0, 0])
        form_data['CARDINAL_DIRS__FONT_COLOR'] = ','.join([str(x) for x in cardinal_dirs__font_color])

        # Sun orb color
        orb_properties__sun_color = self.indi_allsky_config.get('ORB_PROPERTIES', {}).get('SUN_COLOR', [200, 200, 100])
        form_data['ORB_PROPERTIES__SUN_COLOR'] = ','.join([str(x) for x in orb_properties__sun_color])

        # Moon orb color
        orb_properties__moon_color = self.indi_allsky_config.get('ORB_PROPERTIES', {}).get('MOON_COLOR', [128, 128, 128])
        form_data['ORB_PROPERTIES__MOON_COLOR'] = ','.join([str(x) for x in orb_properties__moon_color])

        # Border color
        image_border__color = self.indi_allsky_config.get('IMAGE_BORDER', {}).get('COLOR', [0, 0, 0])
        form_data['IMAGE_BORDER__COLOR'] = ','.join([str(x) for x in image_border__color])

        # Lightgraph colors
        lightgraph_overlay__day_color = self.indi_allsky_config.get('LIGHTGRAPH_OVERLAY', {}).get('DAY_COLOR', [150, 150, 150])
        form_data['LIGHTGRAPH_OVERLAY__DAY_COLOR'] = ','.join([str(x) for x in lightgraph_overlay__day_color])

        lightgraph_overlay__dusk_color = self.indi_allsky_config.get('LIGHTGRAPH_OVERLAY', {}).get('DUSK_COLOR', [200, 100, 60])
        form_data['LIGHTGRAPH_OVERLAY__DUSK_COLOR'] = ','.join([str(x) for x in lightgraph_overlay__dusk_color])

        lightgraph_overlay__night_color = self.indi_allsky_config.get('LIGHTGRAPH_OVERLAY', {}).get('NIGHT_COLOR', [30, 30, 30])
        form_data['LIGHTGRAPH_OVERLAY__NIGHT_COLOR'] = ','.join([str(x) for x in lightgraph_overlay__night_color])

        lightgraph_overlay__moonmode_color = self.indi_allsky_config.get('LIGHTGRAPH_OVERLAY', {}).get('MOONMODE_COLOR', [50, 50, 50])
        form_data['LIGHTGRAPH_OVERLAY__MOONMODE_COLOR'] = ','.join([str(x) for x in lightgraph_overlay__moonmode_color])

        lightgraph_overlay__hour_color = self.indi_allsky_config.get('LIGHTGRAPH_OVERLAY', {}).get('HOUR_COLOR', [100, 15, 15])
        form_data['LIGHTGRAPH_OVERLAY__HOUR_COLOR'] = ','.join([str(x) for x in lightgraph_overlay__hour_color])

        lightgraph_overlay__border_color = self.indi_allsky_config.get('LIGHTGRAPH_OVERLAY', {}).get('BORDER_COLOR', [1, 1, 1])
        form_data['LIGHTGRAPH_OVERLAY__BORDER_COLOR'] = ','.join([str(x) for x in lightgraph_overlay__border_color])

        lightgraph_overlay__now_color = self.indi_allsky_config.get('LIGHTGRAPH_OVERLAY', {}).get('NOW_COLOR', [120, 120, 200])
        form_data['LIGHTGRAPH_OVERLAY__NOW_COLOR'] = ','.join([str(x) for x in lightgraph_overlay__now_color])

        lightgraph_overlay__font_color = self.indi_allsky_config.get('LIGHTGRAPH_OVERLAY', {}).get('FONT_COLOR', [150, 150, 150])
        form_data['LIGHTGRAPH_OVERLAY__FONT_COLOR'] = ','.join([str(x) for x in lightgraph_overlay__font_color])


        # Youtube
        youtube_tags = self.indi_allsky_config.get('YOUTUBE', {}).get('TAGS', [])
        form_data['YOUTUBE__TAGS_STR'] = ', '.join(youtube_tags)

        form_data['YOUTUBE__REDIRECT_URI'] = url_for('indi_allsky.youtube_oauth2callback_view', _external=True)

        try:
            self._miscDb.getState('YOUTUBE_CREDENTIALS')
            form_data['YOUTUBE__CREDS_STORED'] = True
        except NoResultFound:
            form_data['YOUTUBE__CREDS_STORED'] = False
        except InvalidToken:
            app.logger.error('Invalid Fernet decryption key')
            form_data['YOUTUBE__CREDS_STORED'] = False
        except ValueError as e:
            app.logger.error('Invalid Fernet decryption key: %s', str(e))
            form_data['YOUTUBE__CREDS_STORED'] = False


        # FITS headers
        fitsheaders = self.indi_allsky_config.get('FITSHEADERS', [])

        try:
            form_data['FITSHEADERS__0__KEY'] = str(fitsheaders[0][0]).upper()
            form_data['FITSHEADERS__0__VAL'] = str(fitsheaders[0][1])
        except IndexError:
            form_data['FITSHEADERS__0__KEY'] = 'INSTRUME'
            form_data['FITSHEADERS__0__VAL'] = 'indi-allsky'

        try:
            form_data['FITSHEADERS__1__KEY'] = str(fitsheaders[1][0]).upper()
            form_data['FITSHEADERS__1__VAL'] = str(fitsheaders[1][1])
        except IndexError:
            form_data['FITSHEADERS__1__KEY'] = 'OBSERVER'
            form_data['FITSHEADERS__1__VAL'] = ''

        try:
            form_data['FITSHEADERS__2__KEY'] = str(fitsheaders[2][0]).upper()
            form_data['FITSHEADERS__2__VAL'] = str(fitsheaders[2][1])
        except IndexError:
            form_data['FITSHEADERS__2__KEY'] = 'SITE'
            form_data['FITSHEADERS__2__VAL'] = ''

        try:
            form_data['FITSHEADERS__3__KEY'] = str(fitsheaders[3][0]).upper()
            form_data['FITSHEADERS__3__VAL'] = str(fitsheaders[3][1])
        except IndexError:
            form_data['FITSHEADERS__3__KEY'] = 'OBJECT'
            form_data['FITSHEADERS__3__VAL'] = ''

        try:
            form_data['FITSHEADERS__4__KEY'] = str(fitsheaders[4][0]).upper()
            form_data['FITSHEADERS__4__VAL'] = str(fitsheaders[4][1])
        except IndexError:
            form_data['FITSHEADERS__4__KEY'] = 'NOTES'
            form_data['FITSHEADERS__4__VAL'] = ''


        # libcurl options as json text
        filetransfer__libcurl_options = self.indi_allsky_config.get('FILETRANSFER', {}).get('LIBCURL_OPTIONS', {'VERBOSE' : 0})
        form_data['FILETRANSFER__LIBCURL_OPTIONS'] = json.dumps(filetransfer__libcurl_options, indent=4)


        # INDI config as json text
        indi_config_defaults = self.indi_allsky_config.get('INDI_CONFIG_DEFAULTS', {})
        form_data['INDI_CONFIG_DEFAULTS'] = json.dumps(indi_config_defaults, indent=4)

        indi_config_day = self.indi_allsky_config.get('INDI_CONFIG_DAY', {})
        form_data['INDI_CONFIG_DAY'] = json.dumps(indi_config_day, indent=4)


        # populated from flask config
        network_list = list()

        network_list.extend(app.config.get('ADMIN_NETWORKS', []))

        net_info = psutil.net_if_addrs()
        for dev, addr_info in net_info.items():
            if dev == 'lo':
                # skip loopback
                continue

            for addr in addr_info:
                if addr.family == socket.AF_INET:  # 2
                    cidr = ipaddress.IPv4Network('0.0.0.0/{0:s}'.format(addr.netmask)).prefixlen
                    network_cidr = '{0:s}/{1:d}'.format(addr.address, cidr)
                elif addr.family == socket.AF_INET6:  # 10
                    network_cidr = '{0:s}/{1:d}'.format(addr.address, 64)  # assume /64 for ipv6
                elif addr.family == socket.AF_PACKET:  # 17
                    continue
                else:
                    #app.logger.error('Unknown address family: %d', addr.family)
                    continue


                try:
                    network = ipaddress.ip_network(network_cidr, strict=False)
                    network_list.append('{0:s} [{1:s}]'.format(str(network), dev))
                except ValueError:
                    app.logger.error('Invalid network: %s', network_cidr)
                    continue


        admin_network_text = '\n'.join(network_list)
        form_data['ADMIN_NETWORKS_FLASK'] = admin_network_text

        context['form_config'] = IndiAllskyConfigForm(data=form_data)

        return context


class AjaxConfigView(BaseView):
    methods = ['POST']
    decorators = [login_required]

    def dispatch_request(self):
        form_config = IndiAllskyConfigForm(data=request.json)


        if not app.config['LOGIN_DISABLED']:
            if not current_user.is_admin:
                form_errors = form_config.errors  # this must be a property
                form_errors['form_global'] = ['You do not have permission to make configuration changes']
                return jsonify(form_errors), 400


        if not form_config.validate():
            form_errors = form_config.errors  # this must be a property
            form_errors['form_global'] = ['Please fix the errors above']
            return jsonify(form_errors), 400


        # form passed validation

        if not self.indi_allsky_config:
            return jsonify({}), 400


        # sanity check
        leaf_list = (
            'WEBSITE',
            'CCD_CONFIG',
            'CAMERA_SQM',
            'IMAGE_FILE_COMPRESSION',
            'IMAGE_CIRCLE_MASK',
            'FISH2PANO',
            'TEXT_PROPERTIES',
            'CARDINAL_DIRS',
            'IMAGE_STRETCH',
            'ORB_PROPERTIES',
            'IMAGE_BORDER',
            'FILETRANSFER',
            'S3UPLOAD',
            'MQTTPUBLISH',
            'SYNCAPI',
            'YOUTUBE',
            'LIBCAMERA',
            'PYCURL_CAMERA',
            'ACCUM_CAMERA',
            'TEST_CAMERA',
            'VIRTUALSKY',
            'CIRCULAR_DISPLAY',
            'FOCUSER',
            'DEW_HEATER',
            'FAN',
            'GENERIC_GPIO',
            'MANUAL_GPIO',
            'DEVICE',
            'TEMP_SENSOR',
            'THUMBNAILS',
            'HEALTHCHECK',
            'CHARTS',
            'TIMELAPSE',
            'MOON_OVERLAY',
            'LIGHTGRAPH_OVERLAY',
            'IMAGE_OVERLAY',
            'ADSB',
            'SATELLITE_TRACK',
            'LONGTERM_KEOGRAM',
            'REALTIME_KEOGRAM',
            'STARTRAILS',
        )

        for leaf in leaf_list:
            if not isinstance(self.indi_allsky_config.get(leaf), dict):
                self.indi_allsky_config[leaf] = dict()


        if not self.indi_allsky_config['CCD_CONFIG'].get('NIGHT'):
            self.indi_allsky_config['CCD_CONFIG']['NIGHT'] = {}

        if not self.indi_allsky_config['CCD_CONFIG'].get('MOONMODE'):
            self.indi_allsky_config['CCD_CONFIG']['MOONMODE'] = {}

        if not self.indi_allsky_config['CCD_CONFIG'].get('DAY'):
            self.indi_allsky_config['CCD_CONFIG']['DAY'] = {}


        if not self.indi_allsky_config.get('FITSHEADERS'):
            self.indi_allsky_config['FITSHEADERS'] = [['', ''], ['', ''], ['', ''], ['', ''], ['', '']]


        # update data
        self.indi_allsky_config['CAMERA_INTERFACE']                     = str(request.json['CAMERA_INTERFACE'])
        self.indi_allsky_config['INDI_SERVER']                          = str(request.json['INDI_SERVER'])
        self.indi_allsky_config['INDI_PORT']                            = int(request.json['INDI_PORT'])
        self.indi_allsky_config['INDI_CAMERA_NAME']                     = str(request.json['INDI_CAMERA_NAME'])
        self.indi_allsky_config['WEBSITE']['TITLE']                     = str(request.json['WEBSITE__TITLE'])
        self.indi_allsky_config['OWNER']                                = str(request.json['OWNER'])
        self.indi_allsky_config['LENS_NAME']                            = str(request.json['LENS_NAME'])
        self.indi_allsky_config['LENS_FOCAL_LENGTH']                    = float(request.json['LENS_FOCAL_LENGTH'])
        self.indi_allsky_config['LENS_FOCAL_RATIO']                     = float(request.json['LENS_FOCAL_RATIO'])
        self.indi_allsky_config['LENS_IMAGE_CIRCLE']                    = int(request.json['LENS_IMAGE_CIRCLE'])
        self.indi_allsky_config['LENS_OFFSET_X']                        = int(request.json['LENS_OFFSET_X'])
        self.indi_allsky_config['LENS_OFFSET_Y']                        = int(request.json['LENS_OFFSET_Y'])
        self.indi_allsky_config['LENS_ALTITUDE']                        = float(request.json['LENS_ALTITUDE'])
        self.indi_allsky_config['LENS_AZIMUTH']                         = float(request.json['LENS_AZIMUTH'])
        self.indi_allsky_config['CCD_CONFIG']['NIGHT']['GAIN']          = float(round(float(request.json['CCD_CONFIG__NIGHT__GAIN']), 2))  # limit to 2 decimals
        self.indi_allsky_config['CCD_CONFIG']['NIGHT']['BINNING']       = int(request.json['CCD_CONFIG__NIGHT__BINNING'])
        self.indi_allsky_config['CCD_CONFIG']['MOONMODE']['GAIN']       = float(round(float(request.json['CCD_CONFIG__MOONMODE__GAIN']), 2))  # limit to 2 decimals
        self.indi_allsky_config['CCD_CONFIG']['MOONMODE']['BINNING']    = int(request.json['CCD_CONFIG__MOONMODE__BINNING'])
        self.indi_allsky_config['CCD_CONFIG']['DAY']['GAIN']            = float(round(float(request.json['CCD_CONFIG__DAY__GAIN']), 2))  # limit to 2 decimals
        self.indi_allsky_config['CCD_CONFIG']['DAY']['BINNING']         = int(request.json['CCD_CONFIG__DAY__BINNING'])
        self.indi_allsky_config['CCD_CONFIG']['AUTO_GAIN_ENABLE']       = bool(request.json['CCD_CONFIG__AUTO_GAIN_ENABLE'])
        self.indi_allsky_config['CCD_CONFIG']['AUTO_GAIN_LEVELS']       = int(request.json['CCD_CONFIG__AUTO_GAIN_LEVELS'])
        self.indi_allsky_config['CCD_EXPOSURE_MAX']                     = float(round(float(request.json['CCD_EXPOSURE_MAX']), 6))
        self.indi_allsky_config['CCD_EXPOSURE_DEF']                     = float(round(float(request.json['CCD_EXPOSURE_DEF']), 6))
        self.indi_allsky_config['CCD_EXPOSURE_MIN']                     = float(round(float(request.json['CCD_EXPOSURE_MIN']), 6))
        self.indi_allsky_config['CCD_EXPOSURE_MIN_DAY']                 = float(round(float(request.json['CCD_EXPOSURE_MIN_DAY']), 6))
        self.indi_allsky_config['CCD_EXPOSURE_TIMEOUT']                 = int(request.json['CCD_EXPOSURE_TIMEOUT'])
        self.indi_allsky_config['CCD_BIT_DEPTH']                        = int(request.json['CCD_BIT_DEPTH'])
        self.indi_allsky_config['EXPOSURE_PERIOD']                      = float(request.json['EXPOSURE_PERIOD'])
        self.indi_allsky_config['EXPOSURE_PERIOD_DAY']                  = float(request.json['EXPOSURE_PERIOD_DAY'])
        self.indi_allsky_config['CAMERA_SQM']['ENABLE']                 = bool(request.json['CAMERA_SQM__ENABLE'])
        self.indi_allsky_config['CAMERA_SQM']['ENABLE_DAY']             = bool(request.json['CAMERA_SQM__ENABLE_DAY'])
        self.indi_allsky_config['CAMERA_SQM']['EXPOSURE']               = float(round(float(request.json['CAMERA_SQM__EXPOSURE']), 6))
        self.indi_allsky_config['CAMERA_SQM']['GAIN']                   = float(round(float(request.json['CAMERA_SQM__GAIN']), 2))  # limit to 2 decimals
        self.indi_allsky_config['CAMERA_SQM']['BINNING']                = int(request.json['CAMERA_SQM__BINNING'])
        self.indi_allsky_config['CAMERA_SQM']['EXPOSURE_PERIOD']        = int(request.json['CAMERA_SQM__EXPOSURE_PERIOD'])
        self.indi_allsky_config['CAMERA_SQM']['MAGNITUDE_OFFSET']       = float(request.json['CAMERA_SQM__MAGNITUDE_OFFSET'])
        self.indi_allsky_config['FOCUS_MODE']                           = bool(request.json['FOCUS_MODE'])
        self.indi_allsky_config['FOCUS_DELAY']                          = float(request.json['FOCUS_DELAY'])
        self.indi_allsky_config['CFA_PATTERN']                          = str(request.json['CFA_PATTERN'])
        self.indi_allsky_config['USE_NIGHT_COLOR']                      = bool(request.json['USE_NIGHT_COLOR'])
        self.indi_allsky_config['SCNR_ALGORITHM']                       = str(request.json['SCNR_ALGORITHM'])
        self.indi_allsky_config['SCNR_ALGORITHM_DAY']                   = str(request.json['SCNR_ALGORITHM_DAY'])
        self.indi_allsky_config['SCNR_MTF_MIDTONES']                    = float(request.json['SCNR_MTF_MIDTONES'])
        self.indi_allsky_config['SCNR_MTF_MIDTONES_DAY']                = float(request.json['SCNR_MTF_MIDTONES_DAY'])
        self.indi_allsky_config['IMAGE_DENOISE']                        = str(request.json['IMAGE_DENOISE'])
        self.indi_allsky_config['IMAGE_DENOISE_DAY']                    = str(request.json['IMAGE_DENOISE_DAY'])
        self.indi_allsky_config['IMAGE_DENOISE_STRENGTH']               = int(request.json['IMAGE_DENOISE_STRENGTH'])
        self.indi_allsky_config['IMAGE_DENOISE_STRENGTH_DAY']           = int(request.json['IMAGE_DENOISE_STRENGTH_DAY'])
        self.indi_allsky_config['BILATERAL_SIGMA_COLOR']                = int(request.json['BILATERAL_SIGMA_COLOR'])
        self.indi_allsky_config['BILATERAL_SIGMA_COLOR_DAY']            = int(request.json['BILATERAL_SIGMA_COLOR_DAY'])
        self.indi_allsky_config['BILATERAL_SIGMA_SPACE']                = int(request.json['BILATERAL_SIGMA_SPACE'])
        self.indi_allsky_config['BILATERAL_SIGMA_SPACE_DAY']            = int(request.json['BILATERAL_SIGMA_SPACE_DAY'])
        self.indi_allsky_config['WBR_FACTOR']                           = float(request.json['WBR_FACTOR'])
        self.indi_allsky_config['WBG_FACTOR']                           = float(request.json['WBG_FACTOR'])
        self.indi_allsky_config['WBB_FACTOR']                           = float(request.json['WBB_FACTOR'])
        self.indi_allsky_config['WBR_FACTOR_DAY']                       = float(request.json['WBR_FACTOR_DAY'])
        self.indi_allsky_config['WBG_FACTOR_DAY']                       = float(request.json['WBG_FACTOR_DAY'])
        self.indi_allsky_config['WBB_FACTOR_DAY']                       = float(request.json['WBB_FACTOR_DAY'])
        self.indi_allsky_config['WBR_MTF_MIDTONES']                     = float(request.json['WBR_MTF_MIDTONES'])
        self.indi_allsky_config['WBG_MTF_MIDTONES']                     = float(request.json['WBG_MTF_MIDTONES'])
        self.indi_allsky_config['WBB_MTF_MIDTONES']                     = float(request.json['WBB_MTF_MIDTONES'])
        self.indi_allsky_config['WBR_MTF_MIDTONES_DAY']                 = float(request.json['WBR_MTF_MIDTONES_DAY'])
        self.indi_allsky_config['WBG_MTF_MIDTONES_DAY']                 = float(request.json['WBG_MTF_MIDTONES_DAY'])
        self.indi_allsky_config['WBB_MTF_MIDTONES_DAY']                 = float(request.json['WBB_MTF_MIDTONES_DAY'])
        self.indi_allsky_config['SATURATION_FACTOR']                    = float(request.json['SATURATION_FACTOR'])
        self.indi_allsky_config['SATURATION_FACTOR_DAY']                = float(request.json['SATURATION_FACTOR_DAY'])
        self.indi_allsky_config['GAMMA_CORRECTION']                     = float(request.json['GAMMA_CORRECTION'])
        self.indi_allsky_config['GAMMA_CORRECTION_DAY']                 = float(request.json['GAMMA_CORRECTION_DAY'])
        self.indi_allsky_config['SHARPEN_AMOUNT']                       = float(request.json['SHARPEN_AMOUNT'])
        self.indi_allsky_config['SHARPEN_AMOUNT_DAY']                   = float(request.json['SHARPEN_AMOUNT_DAY'])
        self.indi_allsky_config['CCD_COOLING']                          = bool(request.json['CCD_COOLING'])
        self.indi_allsky_config['CCD_COOLING_DAY']                      = bool(request.json['CCD_COOLING_DAY'])
        self.indi_allsky_config['CCD_TEMP']                             = float(request.json['CCD_TEMP'])
        self.indi_allsky_config['CCD_TEMP_DAY']                         = float(request.json['CCD_TEMP_DAY'])
        self.indi_allsky_config['AUTO_WB']                              = bool(request.json['AUTO_WB'])
        self.indi_allsky_config['AUTO_WB_DAY']                          = bool(request.json['AUTO_WB_DAY'])
        self.indi_allsky_config['TEMP_DISPLAY']                         = str(request.json['TEMP_DISPLAY'])
        self.indi_allsky_config['PRESSURE_DISPLAY']                     = str(request.json['PRESSURE_DISPLAY'])
        self.indi_allsky_config['WINDSPEED_DISPLAY']                    = str(request.json['WINDSPEED_DISPLAY'])
        self.indi_allsky_config['GPS_ENABLE']                           = bool(request.json['GPS_ENABLE'])
        self.indi_allsky_config['CCD_TEMP_SCRIPT']                      = str(request.json['CCD_TEMP_SCRIPT'])
        self.indi_allsky_config['TARGET_ADU']                           = int(request.json['TARGET_ADU'])
        self.indi_allsky_config['TARGET_ADU_DAY']                       = int(request.json['TARGET_ADU_DAY'])
        self.indi_allsky_config['TARGET_ADU_DEV']                       = int(request.json['TARGET_ADU_DEV'])
        self.indi_allsky_config['TARGET_ADU_DEV_DAY']                   = int(request.json['TARGET_ADU_DEV_DAY'])
        self.indi_allsky_config['ADU_FOV_DIV']                          = int(request.json['ADU_FOV_DIV'])
        self.indi_allsky_config['SQM_FOV_DIV']                          = int(request.json['SQM_FOV_DIV'])
        self.indi_allsky_config['DETECT_STARS']                         = bool(request.json['DETECT_STARS'])
        self.indi_allsky_config['DETECT_STARS_THOLD']                   = float(request.json['DETECT_STARS_THOLD'])
        self.indi_allsky_config['DETECT_METEORS']                       = bool(request.json['DETECT_METEORS'])
        self.indi_allsky_config['DETECT_METEORS_THOLD']                 = int(request.json['DETECT_METEORS_THOLD'])
        self.indi_allsky_config['DETECT_MASK']                          = str(request.json['DETECT_MASK'])
        self.indi_allsky_config['DETECT_DRAW']                          = bool(request.json['DETECT_DRAW'])
        self.indi_allsky_config['LOGO_OVERLAY']                         = str(request.json['LOGO_OVERLAY'])
        self.indi_allsky_config['HEALTHCHECK']['DISK_USAGE']            = float(request.json['HEALTHCHECK__DISK_USAGE'])
        self.indi_allsky_config['HEALTHCHECK']['SWAP_USAGE']            = float(request.json['HEALTHCHECK__SWAP_USAGE'])
        self.indi_allsky_config['LOCATION_NAME']                        = str(request.json['LOCATION_NAME'])
        self.indi_allsky_config['LOCATION_LATITUDE']                    = float(round(float(request.json['LOCATION_LATITUDE']), 3))
        self.indi_allsky_config['LOCATION_LONGITUDE']                   = float(round(float(request.json['LOCATION_LONGITUDE']), 3))
        self.indi_allsky_config['LOCATION_ELEVATION']                   = int(request.json['LOCATION_ELEVATION'])
        self.indi_allsky_config['TIMELAPSE_ENABLE']                     = bool(request.json['TIMELAPSE_ENABLE'])
        self.indi_allsky_config['TIMELAPSE_SKIP_FRAMES']                = int(request.json['TIMELAPSE_SKIP_FRAMES'])
        self.indi_allsky_config['TIMELAPSE']['PRE_PROCESSOR']           = str(request.json['TIMELAPSE__PRE_PROCESSOR'])
        self.indi_allsky_config['TIMELAPSE']['PRE_PROCESSOR_DAY']       = str(request.json['TIMELAPSE__PRE_PROCESSOR_DAY'])
        self.indi_allsky_config['TIMELAPSE']['IMAGE_CIRCLE']            = int(request.json['TIMELAPSE__IMAGE_CIRCLE'])
        self.indi_allsky_config['TIMELAPSE']['KEOGRAM_RATIO']           = float(request.json['TIMELAPSE__KEOGRAM_RATIO'])
        self.indi_allsky_config['TIMELAPSE']['PRE_SCALE']               = int(request.json['TIMELAPSE__PRE_SCALE'])
        self.indi_allsky_config['TIMELAPSE']['FFMPEG_REPORT']           = bool(request.json['TIMELAPSE__FFMPEG_REPORT'])
        self.indi_allsky_config['TIMELAPSE']['USE_NIGHT_CONFIG']        = bool(request.json['TIMELAPSE__USE_NIGHT_CONFIG'])
        self.indi_allsky_config['CAPTURE_PAUSE']                        = bool(request.json['CAPTURE_PAUSE'])
        self.indi_allsky_config['DAYTIME_CAPTURE']                      = bool(request.json['DAYTIME_CAPTURE'])
        self.indi_allsky_config['DAYTIME_CAPTURE_SAVE']                 = bool(request.json['DAYTIME_CAPTURE_SAVE'])
        self.indi_allsky_config['DAYTIME_TIMELAPSE']                    = bool(request.json['DAYTIME_TIMELAPSE'])
        self.indi_allsky_config['DAYTIME_CONTRAST_ENHANCE']             = bool(request.json['DAYTIME_CONTRAST_ENHANCE'])
        self.indi_allsky_config['NIGHT_CONTRAST_ENHANCE']               = bool(request.json['NIGHT_CONTRAST_ENHANCE'])
        self.indi_allsky_config['CONTRAST_ENHANCE_16BIT']               = bool(request.json['CONTRAST_ENHANCE_16BIT'])
        self.indi_allsky_config['CLAHE_CLIPLIMIT']                      = float(request.json['CLAHE_CLIPLIMIT'])
        self.indi_allsky_config['CLAHE_GRIDSIZE']                       = int(request.json['CLAHE_GRIDSIZE'])
        self.indi_allsky_config['NIGHT_SUN_ALT_DEG']                    = float(request.json['NIGHT_SUN_ALT_DEG'])
        self.indi_allsky_config['NIGHT_MOONMODE_ALT_DEG']               = float(request.json['NIGHT_MOONMODE_ALT_DEG'])
        self.indi_allsky_config['NIGHT_MOONMODE_PHASE']                 = float(request.json['NIGHT_MOONMODE_PHASE'])
        self.indi_allsky_config['WEB_STATUS_TEMPLATE']                  = str(request.json['WEB_STATUS_TEMPLATE'])
        self.indi_allsky_config['WEB_EXTRA_TEXT']                       = str(request.json['WEB_EXTRA_TEXT'])
        self.indi_allsky_config['WEB_NONLOCAL_IMAGES']                  = bool(request.json['WEB_NONLOCAL_IMAGES'])
        self.indi_allsky_config['WEB_LOCAL_IMAGES_ADMIN']               = bool(request.json['WEB_LOCAL_IMAGES_ADMIN'])
        self.indi_allsky_config['IMAGE_STRETCH']['CLASSNAME']           = str(request.json['IMAGE_STRETCH__CLASSNAME'])
        self.indi_allsky_config['IMAGE_STRETCH']['MODE1_GAMMA']         = float(request.json['IMAGE_STRETCH__MODE1_GAMMA'])
        self.indi_allsky_config['IMAGE_STRETCH']['MODE1_STDDEVS']       = float(request.json['IMAGE_STRETCH__MODE1_STDDEVS'])
        self.indi_allsky_config['IMAGE_STRETCH']['MODE2_SHADOWS']       = float(request.json['IMAGE_STRETCH__MODE2_SHADOWS'])
        self.indi_allsky_config['IMAGE_STRETCH']['MODE2_MIDTONES']      = float(request.json['IMAGE_STRETCH__MODE2_MIDTONES'])
        self.indi_allsky_config['IMAGE_STRETCH']['MODE2_HIGHLIGHTS']    = float(request.json['IMAGE_STRETCH__MODE2_HIGHLIGHTS'])
        self.indi_allsky_config['IMAGE_STRETCH']['MODE3_BLACK_CLIP']    = float(request.json['IMAGE_STRETCH__MODE3_BLACK_CLIP'])
        self.indi_allsky_config['IMAGE_STRETCH']['MODE3_SHADOWS']       = float(request.json['IMAGE_STRETCH__MODE3_SHADOWS'])
        self.indi_allsky_config['IMAGE_STRETCH']['MODE3_MIDTONES']      = float(request.json['IMAGE_STRETCH__MODE3_MIDTONES'])
        self.indi_allsky_config['IMAGE_STRETCH']['MODE3_HIGHLIGHTS']    = float(request.json['IMAGE_STRETCH__MODE3_HIGHLIGHTS'])
        self.indi_allsky_config['IMAGE_STRETCH']['SPLIT']               = bool(request.json['IMAGE_STRETCH__SPLIT'])
        self.indi_allsky_config['IMAGE_STRETCH']['MOONMODE']            = bool(request.json['IMAGE_STRETCH__MOONMODE'])
        self.indi_allsky_config['IMAGE_STRETCH']['DAYTIME']             = bool(request.json['IMAGE_STRETCH__DAYTIME'])
        self.indi_allsky_config['KEOGRAM_ANGLE']                        = float(request.json['KEOGRAM_ANGLE'])
        self.indi_allsky_config['KEOGRAM_H_SCALE']                      = int(request.json['KEOGRAM_H_SCALE'])
        self.indi_allsky_config['KEOGRAM_V_SCALE']                      = int(request.json['KEOGRAM_V_SCALE'])
        self.indi_allsky_config['KEOGRAM_CROP_TOP']                     = int(request.json['KEOGRAM_CROP_TOP'])
        self.indi_allsky_config['KEOGRAM_CROP_BOTTOM']                  = int(request.json['KEOGRAM_CROP_BOTTOM'])
        self.indi_allsky_config['KEOGRAM_LABEL']                        = bool(request.json['KEOGRAM_LABEL'])
        self.indi_allsky_config['LONGTERM_KEOGRAM']['ENABLE']           = bool(request.json['LONGTERM_KEOGRAM__ENABLE'])
        self.indi_allsky_config['LONGTERM_KEOGRAM']['OFFSET_X']         = int(request.json['LONGTERM_KEOGRAM__OFFSET_X'])
        self.indi_allsky_config['LONGTERM_KEOGRAM']['OFFSET_Y']         = int(request.json['LONGTERM_KEOGRAM__OFFSET_Y'])
        self.indi_allsky_config['LONGTERM_KEOGRAM']['OPENCV_FONT_SCALE']    = float(request.json['LONGTERM_KEOGRAM__OPENCV_FONT_SCALE'])
        self.indi_allsky_config['LONGTERM_KEOGRAM']['PIL_FONT_SIZE']        = int(request.json['LONGTERM_KEOGRAM__PIL_FONT_SIZE'])
        self.indi_allsky_config['LONGTERM_KEOGRAM']['MONTH_LABEL_TEMPLATE'] = str(request.json['LONGTERM_KEOGRAM__MONTH_LABEL_TEMPLATE'])
        self.indi_allsky_config['REALTIME_KEOGRAM']['MAX_ENTRIES']      = int(request.json['REALTIME_KEOGRAM__MAX_ENTRIES'])
        self.indi_allsky_config['REALTIME_KEOGRAM']['SAVE_INTERVAL']    = int(request.json['REALTIME_KEOGRAM__SAVE_INTERVAL'])
        self.indi_allsky_config['REALTIME_KEOGRAM']['LABEL']            = bool(request.json['REALTIME_KEOGRAM__LABEL'])
        self.indi_allsky_config['STARTRAILS_SUN_ALT_THOLD']             = float(request.json['STARTRAILS_SUN_ALT_THOLD'])
        self.indi_allsky_config['STARTRAILS_MOONMODE_THOLD']            = bool(request.json['STARTRAILS_MOONMODE_THOLD'])
        self.indi_allsky_config['STARTRAILS_MOON_ALT_THOLD']            = float(request.json['STARTRAILS_MOON_ALT_THOLD'])
        self.indi_allsky_config['STARTRAILS_MOON_PHASE_THOLD']          = float(request.json['STARTRAILS_MOON_PHASE_THOLD'])
        self.indi_allsky_config['STARTRAILS_MAX_ADU']                   = int(request.json['STARTRAILS_MAX_ADU'])
        self.indi_allsky_config['STARTRAILS_MASK_THOLD']                = int(request.json['STARTRAILS_MASK_THOLD'])
        self.indi_allsky_config['STARTRAILS_PIXEL_THOLD']               = float(request.json['STARTRAILS_PIXEL_THOLD'])
        self.indi_allsky_config['STARTRAILS_MIN_STARS']                 = int(request.json['STARTRAILS_MIN_STARS'])
        self.indi_allsky_config['STARTRAILS_TIMELAPSE']                 = bool(request.json['STARTRAILS_TIMELAPSE'])
        self.indi_allsky_config['STARTRAILS_TIMELAPSE_MINFRAMES']       = int(request.json['STARTRAILS_TIMELAPSE_MINFRAMES'])
        self.indi_allsky_config['STARTRAILS_USE_DB_DATA']               = bool(request.json['STARTRAILS_USE_DB_DATA'])
        self.indi_allsky_config['STARTRAILS']['IMAGE_CIRCLE_MASK_ENABLE']   = bool(request.json['STARTRAILS__IMAGE_CIRCLE_MASK_ENABLE'])
        self.indi_allsky_config['STARTRAILS']['IMAGE_CIRCLE_MASK_DIAMETER'] = int(request.json['STARTRAILS__IMAGE_CIRCLE_MASK_DIAMETER'])
        self.indi_allsky_config['STARTRAILS']['IMAGE_CIRCLE_MASK_BLUR']     = int(request.json['STARTRAILS__IMAGE_CIRCLE_MASK_BLUR'])
        self.indi_allsky_config['STARTRAILS']['IMAGE_CIRCLE_MASK_OPACITY']  = int(request.json['STARTRAILS__IMAGE_CIRCLE_MASK_OPACITY'])
        self.indi_allsky_config['IMAGE_CALIBRATE_DARK']                 = bool(request.json['IMAGE_CALIBRATE_DARK'])
        self.indi_allsky_config['IMAGE_CALIBRATE_BPM']                  = bool(request.json['IMAGE_CALIBRATE_BPM'])
        self.indi_allsky_config['IMAGE_CALIBRATE_FIX_HOLES']            = bool(request.json['IMAGE_CALIBRATE_FIX_HOLES'])
        self.indi_allsky_config['IMAGE_CALIBRATE_HOLE_THOLD']           = int(request.json['IMAGE_CALIBRATE_HOLE_THOLD'])
        self.indi_allsky_config['IMAGE_CALIBRATE_MANUAL_OFFSET']        = int(request.json['IMAGE_CALIBRATE_MANUAL_OFFSET'])
        self.indi_allsky_config['IMAGE_SAVE_FITS_PRE_DARK']             = bool(request.json['IMAGE_SAVE_FITS_PRE_DARK'])
        self.indi_allsky_config['PRIVACY_MODE']                         = bool(request.json['PRIVACY_MODE'])
        self.indi_allsky_config['IMAGE_EXIF_PRIVACY']                   = bool(request.json['IMAGE_EXIF_PRIVACY'])
        self.indi_allsky_config['IMAGE_FILE_TYPE']                      = str(request.json['IMAGE_FILE_TYPE'])
        self.indi_allsky_config['IMAGE_FILE_COMPRESSION']['jpg']        = int(request.json['IMAGE_FILE_COMPRESSION__JPG'])
        self.indi_allsky_config['IMAGE_FILE_COMPRESSION']['jpeg']       = int(request.json['IMAGE_FILE_COMPRESSION__JPG'])  # duplicate
        self.indi_allsky_config['IMAGE_FILE_COMPRESSION']['png']        = int(request.json['IMAGE_FILE_COMPRESSION__PNG'])
        #self.indi_allsky_config['IMAGE_FILE_COMPRESSION']['tif']        = int(request.json['IMAGE_FILE_COMPRESSION__TIF'])  # not used anymore
        #self.indi_allsky_config['IMAGE_FILE_COMPRESSION']['tiff']       = int(request.json['IMAGE_FILE_COMPRESSION__TIF'])  # duplicate
        self.indi_allsky_config['IMAGE_FOLDER']                         = str(request.json['IMAGE_FOLDER'])
        self.indi_allsky_config['VARLIB_FOLDER']                        = str(request.json['VARLIB_FOLDER'])
        self.indi_allsky_config['IMAGE_LABEL_TEMPLATE']                 = str(request.json['IMAGE_LABEL_TEMPLATE'])
        self.indi_allsky_config['IMAGE_EXTRA_TEXT']                     = str(request.json['IMAGE_EXTRA_TEXT'])
        self.indi_allsky_config['IMAGE_ROTATE']                         = str(request.json['IMAGE_ROTATE'])
        self.indi_allsky_config['IMAGE_ROTATE_ANGLE']                   = int(request.json['IMAGE_ROTATE_ANGLE'])
        self.indi_allsky_config['IMAGE_ROTATE_KEEP_SIZE']               = bool(request.json['IMAGE_ROTATE_KEEP_SIZE'])
        #self.indi_allsky_config['IMAGE_ROTATE_WITH_OFFSET']             = bool(request.json['IMAGE_ROTATE_WITH_OFFSET'])
        self.indi_allsky_config['IMAGE_FLIP_V']                         = bool(request.json['IMAGE_FLIP_V'])
        self.indi_allsky_config['IMAGE_FLIP_H']                         = bool(request.json['IMAGE_FLIP_H'])
        self.indi_allsky_config['IMAGE_SCALE']                          = int(request.json['IMAGE_SCALE'])
        self.indi_allsky_config['IMAGE_COLORMAP']                       = str(request.json['IMAGE_COLORMAP'])
        self.indi_allsky_config['IMAGE_CIRCLE_MASK']['ENABLE']          = bool(request.json['IMAGE_CIRCLE_MASK__ENABLE'])
        self.indi_allsky_config['IMAGE_CIRCLE_MASK']['DIAMETER']        = int(request.json['IMAGE_CIRCLE_MASK__DIAMETER'])
        self.indi_allsky_config['IMAGE_CIRCLE_MASK']['OFFSET_X']        = int(request.json['IMAGE_CIRCLE_MASK__OFFSET_X'])
        self.indi_allsky_config['IMAGE_CIRCLE_MASK']['OFFSET_Y']        = int(request.json['IMAGE_CIRCLE_MASK__OFFSET_Y'])
        self.indi_allsky_config['IMAGE_CIRCLE_MASK']['BLUR']            = int(request.json['IMAGE_CIRCLE_MASK__BLUR'])
        self.indi_allsky_config['IMAGE_CIRCLE_MASK']['OPACITY']         = int(request.json['IMAGE_CIRCLE_MASK__OPACITY'])
        self.indi_allsky_config['IMAGE_CIRCLE_MASK']['OUTLINE']         = bool(request.json['IMAGE_CIRCLE_MASK__OUTLINE'])
        self.indi_allsky_config['IMAGE_CROP_IMAGE_CIRCLE']              = bool(request.json['IMAGE_CROP_IMAGE_CIRCLE'])
        self.indi_allsky_config['FISH2PANO']['ENABLE']                  = bool(request.json['FISH2PANO__ENABLE'])
        self.indi_allsky_config['FISH2PANO']['DIAMETER']                = int(request.json['FISH2PANO__DIAMETER'])
        self.indi_allsky_config['FISH2PANO']['OFFSET_X']                = int(request.json['FISH2PANO__OFFSET_X'])
        self.indi_allsky_config['FISH2PANO']['OFFSET_Y']                = int(request.json['FISH2PANO__OFFSET_Y'])
        self.indi_allsky_config['FISH2PANO']['ROTATE_ANGLE']            = int(request.json['FISH2PANO__ROTATE_ANGLE'])
        self.indi_allsky_config['FISH2PANO']['SCALE']                   = float(request.json['FISH2PANO__SCALE'])
        self.indi_allsky_config['FISH2PANO']['MODULUS']                 = int(request.json['FISH2PANO__MODULUS'])
        self.indi_allsky_config['FISH2PANO']['FLIP_H']                  = bool(request.json['FISH2PANO__FLIP_H'])
        self.indi_allsky_config['FISH2PANO']['ENABLE_CARDINAL_DIRS']    = bool(request.json['FISH2PANO__ENABLE_CARDINAL_DIRS'])
        self.indi_allsky_config['FISH2PANO']['DIRS_OFFSET_BOTTOM']      = int(request.json['FISH2PANO__DIRS_OFFSET_BOTTOM'])
        self.indi_allsky_config['FISH2PANO']['OPENCV_FONT_SCALE']       = float(request.json['FISH2PANO__OPENCV_FONT_SCALE'])
        self.indi_allsky_config['FISH2PANO']['PIL_FONT_SIZE']           = int(request.json['FISH2PANO__PIL_FONT_SIZE'])
        self.indi_allsky_config['IMAGE_SAVE_FITS']                      = bool(request.json['IMAGE_SAVE_FITS'])
        self.indi_allsky_config['IMAGE_SAVE_FITS_COMPRESSED']           = bool(request.json['IMAGE_SAVE_FITS_COMPRESSED'])
        self.indi_allsky_config['IMAGE_SAVE_FITS_PERIOD']               = int(request.json['IMAGE_SAVE_FITS_PERIOD'])
        self.indi_allsky_config['NIGHT_GRAYSCALE']                      = bool(request.json['NIGHT_GRAYSCALE'])
        self.indi_allsky_config['DAYTIME_GRAYSCALE']                    = bool(request.json['DAYTIME_GRAYSCALE'])
        self.indi_allsky_config['MOON_OVERLAY']['ENABLE']               = bool(request.json['MOON_OVERLAY__ENABLE'])
        self.indi_allsky_config['MOON_OVERLAY']['X']                    = int(request.json['MOON_OVERLAY__X'])
        self.indi_allsky_config['MOON_OVERLAY']['Y']                    = int(request.json['MOON_OVERLAY__Y'])
        self.indi_allsky_config['MOON_OVERLAY']['SCALE']                = float(request.json['MOON_OVERLAY__SCALE'])
        self.indi_allsky_config['MOON_OVERLAY']['DARK_SIDE_SCALE']      = float(request.json['MOON_OVERLAY__DARK_SIDE_SCALE'])
        self.indi_allsky_config['MOON_OVERLAY']['FLIP_V']               = bool(request.json['MOON_OVERLAY__FLIP_V'])
        self.indi_allsky_config['MOON_OVERLAY']['FLIP_H']               = bool(request.json['MOON_OVERLAY__FLIP_H'])
        self.indi_allsky_config['LIGHTGRAPH_OVERLAY']['ENABLE']         = bool(request.json['LIGHTGRAPH_OVERLAY__ENABLE'])
        self.indi_allsky_config['LIGHTGRAPH_OVERLAY']['GRAPH_HEIGHT']   = int(request.json['LIGHTGRAPH_OVERLAY__GRAPH_HEIGHT'])
        self.indi_allsky_config['LIGHTGRAPH_OVERLAY']['GRAPH_BORDER']   = int(request.json['LIGHTGRAPH_OVERLAY__GRAPH_BORDER'])
        self.indi_allsky_config['LIGHTGRAPH_OVERLAY']['Y']              = int(request.json['LIGHTGRAPH_OVERLAY__Y'])
        self.indi_allsky_config['LIGHTGRAPH_OVERLAY']['OFFSET_X']       = int(request.json['LIGHTGRAPH_OVERLAY__OFFSET_X'])
        self.indi_allsky_config['LIGHTGRAPH_OVERLAY']['SCALE']          = float(request.json['LIGHTGRAPH_OVERLAY__SCALE'])
        self.indi_allsky_config['LIGHTGRAPH_OVERLAY']['NOW_MARKER_SIZE']  = int(request.json['LIGHTGRAPH_OVERLAY__NOW_MARKER_SIZE'])
        self.indi_allsky_config['LIGHTGRAPH_OVERLAY']['OPACITY']        = int(request.json['LIGHTGRAPH_OVERLAY__OPACITY'])
        self.indi_allsky_config['LIGHTGRAPH_OVERLAY']['PIL_FONT_SIZE']  = int(request.json['LIGHTGRAPH_OVERLAY__PIL_FONT_SIZE'])
        self.indi_allsky_config['LIGHTGRAPH_OVERLAY']['OPENCV_FONT_SCALE'] = float(request.json['LIGHTGRAPH_OVERLAY__OPENCV_FONT_SCALE'])
        self.indi_allsky_config['LIGHTGRAPH_OVERLAY']['LABEL']          = bool(request.json['LIGHTGRAPH_OVERLAY__LABEL'])
        self.indi_allsky_config['LIGHTGRAPH_OVERLAY']['HOUR_LINES']     = bool(request.json['LIGHTGRAPH_OVERLAY__HOUR_LINES'])
        self.indi_allsky_config['IMAGE_OVERLAY']['ENABLE']              = bool(request.json['IMAGE_OVERLAY__ENABLE'])
        self.indi_allsky_config['IMAGE_OVERLAY']['LOAD_INTERVAL']       = int(request.json['IMAGE_OVERLAY__LOAD_INTERVAL'])
        self.indi_allsky_config['IMAGE_OVERLAY']['A_URL']               = str(request.json['IMAGE_OVERLAY__A_URL'])
        self.indi_allsky_config['IMAGE_OVERLAY']['A_IMAGE_FILE_TYPE']   = str(request.json['IMAGE_OVERLAY__A_IMAGE_FILE_TYPE'])
        self.indi_allsky_config['IMAGE_OVERLAY']['A_WIDTH']             = int(request.json['IMAGE_OVERLAY__A_WIDTH'])
        self.indi_allsky_config['IMAGE_OVERLAY']['A_HEIGHT']            = int(request.json['IMAGE_OVERLAY__A_HEIGHT'])
        self.indi_allsky_config['IMAGE_OVERLAY']['A_X']                 = int(request.json['IMAGE_OVERLAY__A_X'])
        self.indi_allsky_config['IMAGE_OVERLAY']['A_Y']                 = int(request.json['IMAGE_OVERLAY__A_Y'])
        self.indi_allsky_config['IMAGE_OVERLAY']['A_USERNAME']          = str(request.json['IMAGE_OVERLAY__A_USERNAME'])
        self.indi_allsky_config['IMAGE_OVERLAY']['A_PASSWORD']          = str(request.json['IMAGE_OVERLAY__A_PASSWORD'])
        self.indi_allsky_config['IMAGE_EXPORT_RAW']                     = str(request.json['IMAGE_EXPORT_RAW'])
        self.indi_allsky_config['IMAGE_EXPORT_FOLDER']                  = str(request.json['IMAGE_EXPORT_FOLDER'])
        self.indi_allsky_config['IMAGE_EXPORT_FLIP_V']                  = bool(request.json['IMAGE_EXPORT_FLIP_V'])
        self.indi_allsky_config['IMAGE_EXPORT_FLIP_H']                  = bool(request.json['IMAGE_EXPORT_FLIP_H'])
        self.indi_allsky_config['IMAGE_STACK_METHOD']                   = str(request.json['IMAGE_STACK_METHOD'])
        self.indi_allsky_config['IMAGE_STACK_COUNT']                    = int(request.json['IMAGE_STACK_COUNT'])
        self.indi_allsky_config['IMAGE_STACK_ALIGN']                    = bool(request.json['IMAGE_STACK_ALIGN'])
        self.indi_allsky_config['IMAGE_ALIGN_DETECTSIGMA']              = int(request.json['IMAGE_ALIGN_DETECTSIGMA'])
        self.indi_allsky_config['IMAGE_ALIGN_POINTS']                   = int(request.json['IMAGE_ALIGN_POINTS'])
        self.indi_allsky_config['IMAGE_ALIGN_SOURCEMINAREA']            = int(request.json['IMAGE_ALIGN_SOURCEMINAREA'])
        self.indi_allsky_config['IMAGE_STACK_SPLIT']                    = bool(request.json['IMAGE_STACK_SPLIT'])
        self.indi_allsky_config['IMAGE_STACK_MOONMODE']                 = bool(request.json['IMAGE_STACK_MOONMODE'])
        self.indi_allsky_config['IMAGE_STACK_DAY']                      = bool(request.json['IMAGE_STACK_DAY'])
        self.indi_allsky_config['IMAGE_QUEUE_MAX']                      = int(request.json['IMAGE_QUEUE_MAX'])
        self.indi_allsky_config['IMAGE_QUEUE_MIN']                      = int(request.json['IMAGE_QUEUE_MIN'])
        self.indi_allsky_config['IMAGE_QUEUE_BACKOFF']                  = float(request.json['IMAGE_QUEUE_BACKOFF'])
        self.indi_allsky_config['IMAGE_SAVE_HOOK_PRE']                  = str(request.json['IMAGE_SAVE_HOOK_PRE'])
        self.indi_allsky_config['IMAGE_SAVE_HOOK_POST']                 = str(request.json['IMAGE_SAVE_HOOK_POST'])
        self.indi_allsky_config['IMAGE_SAVE_HOOK_TIMEOUT']              = int(request.json['IMAGE_SAVE_HOOK_TIMEOUT'])
        self.indi_allsky_config['CAPTURE_HOOK_PRE']                     = str(request.json['CAPTURE_HOOK_PRE'])
        self.indi_allsky_config['CAPTURE_HOOK_TIMEOUT']                 = int(request.json['CAPTURE_HOOK_TIMEOUT'])
        self.indi_allsky_config['BACKUP_DB_PERIOD_DAYS']                = int(request.json['BACKUP_DB_PERIOD_DAYS'])
        self.indi_allsky_config['IMAGE_EXPIRE_DAYS']                    = int(request.json['IMAGE_EXPIRE_DAYS'])
        self.indi_allsky_config['IMAGE_RAW_EXPIRE_DAYS']                = int(request.json['IMAGE_RAW_EXPIRE_DAYS'])
        self.indi_allsky_config['IMAGE_FITS_EXPIRE_DAYS']               = int(request.json['IMAGE_FITS_EXPIRE_DAYS'])
        self.indi_allsky_config['TIMELAPSE_EXPIRE_DAYS']                = int(request.json['TIMELAPSE_EXPIRE_DAYS'])
        self.indi_allsky_config['TIMELAPSE_OVERWRITE']                  = bool(request.json['TIMELAPSE_OVERWRITE'])
        self.indi_allsky_config['FFMPEG_FRAMERATE']                     = int(request.json['FFMPEG_FRAMERATE'])
        self.indi_allsky_config['FFMPEG_FRAMERATE_DAY']                 = int(request.json['FFMPEG_FRAMERATE_DAY'])
        self.indi_allsky_config['FFMPEG_BITRATE']                       = str(request.json['FFMPEG_BITRATE'])
        self.indi_allsky_config['FFMPEG_BITRATE_DAY']                   = str(request.json['FFMPEG_BITRATE_DAY'])
        self.indi_allsky_config['FFMPEG_VFSCALE']                       = str(request.json['FFMPEG_VFSCALE'])
        self.indi_allsky_config['FFMPEG_VFSCALE_DAY']                   = str(request.json['FFMPEG_VFSCALE_DAY'])
        self.indi_allsky_config['FFMPEG_VFSCALE_STARTRAIL']             = str(request.json['FFMPEG_VFSCALE_STARTRAIL'])
        self.indi_allsky_config['FFMPEG_CODEC']                         = str(request.json['FFMPEG_CODEC'])
        self.indi_allsky_config['FFMPEG_EXTRA_OPTIONS']                 = str(request.json['FFMPEG_EXTRA_OPTIONS'])
        self.indi_allsky_config['FFMPEG_EXTRA_OPTIONS_DAY']             = str(request.json['FFMPEG_EXTRA_OPTIONS_DAY'])
        self.indi_allsky_config['IMAGE_LABEL_SYSTEM']                   = str(request.json['IMAGE_LABEL_SYSTEM'])
        self.indi_allsky_config['TEXT_PROPERTIES']['FONT_FACE']         = str(request.json['TEXT_PROPERTIES__FONT_FACE'])
        self.indi_allsky_config['TEXT_PROPERTIES']['FONT_SCALE']        = float(request.json['TEXT_PROPERTIES__FONT_SCALE'])
        self.indi_allsky_config['TEXT_PROPERTIES']['FONT_THICKNESS']    = int(request.json['TEXT_PROPERTIES__FONT_THICKNESS'])
        self.indi_allsky_config['TEXT_PROPERTIES']['FONT_OUTLINE']      = bool(request.json['TEXT_PROPERTIES__FONT_OUTLINE'])
        self.indi_allsky_config['TEXT_PROPERTIES']['FONT_HEIGHT']       = int(request.json['TEXT_PROPERTIES__FONT_HEIGHT'])
        self.indi_allsky_config['TEXT_PROPERTIES']['FONT_X']            = int(request.json['TEXT_PROPERTIES__FONT_X'])
        self.indi_allsky_config['TEXT_PROPERTIES']['FONT_Y']            = int(request.json['TEXT_PROPERTIES__FONT_Y'])
        self.indi_allsky_config['TEXT_PROPERTIES']['PIL_FONT_FILE']     = str(request.json['TEXT_PROPERTIES__PIL_FONT_FILE'])
        self.indi_allsky_config['TEXT_PROPERTIES']['PIL_FONT_CUSTOM']   = str(request.json['TEXT_PROPERTIES__PIL_FONT_CUSTOM'])
        self.indi_allsky_config['TEXT_PROPERTIES']['PIL_FONT_SIZE']     = int(request.json['TEXT_PROPERTIES__PIL_FONT_SIZE'])
        self.indi_allsky_config['CARDINAL_DIRS']['ENABLE']              = bool(request.json['CARDINAL_DIRS__ENABLE'])
        self.indi_allsky_config['CARDINAL_DIRS']['SWAP_NS']             = bool(request.json['CARDINAL_DIRS__SWAP_NS'])
        self.indi_allsky_config['CARDINAL_DIRS']['SWAP_EW']             = bool(request.json['CARDINAL_DIRS__SWAP_EW'])
        self.indi_allsky_config['CARDINAL_DIRS']['CHAR_NORTH']          = str(request.json['CARDINAL_DIRS__CHAR_NORTH'])
        self.indi_allsky_config['CARDINAL_DIRS']['CHAR_EAST']           = str(request.json['CARDINAL_DIRS__CHAR_EAST'])
        self.indi_allsky_config['CARDINAL_DIRS']['CHAR_WEST']           = str(request.json['CARDINAL_DIRS__CHAR_WEST'])
        self.indi_allsky_config['CARDINAL_DIRS']['CHAR_SOUTH']          = str(request.json['CARDINAL_DIRS__CHAR_SOUTH'])
        self.indi_allsky_config['CARDINAL_DIRS']['DIAMETER']            = int(request.json['CARDINAL_DIRS__DIAMETER'])
        self.indi_allsky_config['CARDINAL_DIRS']['OFFSET_X']            = int(request.json['CARDINAL_DIRS__OFFSET_X'])
        self.indi_allsky_config['CARDINAL_DIRS']['OFFSET_Y']            = int(request.json['CARDINAL_DIRS__OFFSET_Y'])
        self.indi_allsky_config['CARDINAL_DIRS']['OFFSET_TOP']          = int(request.json['CARDINAL_DIRS__OFFSET_TOP'])
        self.indi_allsky_config['CARDINAL_DIRS']['OFFSET_LEFT']         = int(request.json['CARDINAL_DIRS__OFFSET_LEFT'])
        self.indi_allsky_config['CARDINAL_DIRS']['OFFSET_RIGHT']        = int(request.json['CARDINAL_DIRS__OFFSET_RIGHT'])
        self.indi_allsky_config['CARDINAL_DIRS']['OFFSET_BOTTOM']       = int(request.json['CARDINAL_DIRS__OFFSET_BOTTOM'])
        self.indi_allsky_config['CARDINAL_DIRS']['OPENCV_FONT_SCALE']   = float(request.json['CARDINAL_DIRS__OPENCV_FONT_SCALE'])
        self.indi_allsky_config['CARDINAL_DIRS']['PIL_FONT_SIZE']       = int(request.json['CARDINAL_DIRS__PIL_FONT_SIZE'])
        self.indi_allsky_config['CARDINAL_DIRS']['OUTLINE_CIRCLE']      = bool(request.json['CARDINAL_DIRS__OUTLINE_CIRCLE'])
        self.indi_allsky_config['ORB_PROPERTIES']['MODE']               = str(request.json['ORB_PROPERTIES__MODE'])
        self.indi_allsky_config['ORB_PROPERTIES']['RADIUS']             = int(request.json['ORB_PROPERTIES__RADIUS'])
        self.indi_allsky_config['ORB_PROPERTIES']['AZ_OFFSET']          = float(request.json['ORB_PROPERTIES__AZ_OFFSET'])
        self.indi_allsky_config['ORB_PROPERTIES']['RETROGRADE']         = bool(request.json['ORB_PROPERTIES__RETROGRADE'])
        self.indi_allsky_config['IMAGE_BORDER']['TOP']                  = int(request.json['IMAGE_BORDER__TOP'])
        self.indi_allsky_config['IMAGE_BORDER']['LEFT']                 = int(request.json['IMAGE_BORDER__LEFT'])
        self.indi_allsky_config['IMAGE_BORDER']['RIGHT']                = int(request.json['IMAGE_BORDER__RIGHT'])
        self.indi_allsky_config['IMAGE_BORDER']['BOTTOM']               = int(request.json['IMAGE_BORDER__BOTTOM'])
        self.indi_allsky_config['UPLOAD_WORKERS']                       = int(request.json['UPLOAD_WORKERS'])
        self.indi_allsky_config['FILETRANSFER']['CLASSNAME']            = str(request.json['FILETRANSFER__CLASSNAME'])
        self.indi_allsky_config['FILETRANSFER']['HOST']                 = str(request.json['FILETRANSFER__HOST'])
        self.indi_allsky_config['FILETRANSFER']['PORT']                 = int(request.json['FILETRANSFER__PORT'])
        self.indi_allsky_config['FILETRANSFER']['USERNAME']             = str(request.json['FILETRANSFER__USERNAME'])
        self.indi_allsky_config['FILETRANSFER']['PASSWORD']             = str(request.json['FILETRANSFER__PASSWORD'])
        self.indi_allsky_config['FILETRANSFER']['PRIVATE_KEY']          = str(request.json['FILETRANSFER__PRIVATE_KEY'])
        self.indi_allsky_config['FILETRANSFER']['PUBLIC_KEY']           = str(request.json['FILETRANSFER__PUBLIC_KEY'])
        self.indi_allsky_config['FILETRANSFER']['CONNECT_TIMEOUT']      = float(request.json['FILETRANSFER__CONNECT_TIMEOUT'])
        self.indi_allsky_config['FILETRANSFER']['TIMEOUT']              = float(request.json['FILETRANSFER__TIMEOUT'])
        self.indi_allsky_config['FILETRANSFER']['CERT_BYPASS']          = bool(request.json['FILETRANSFER__CERT_BYPASS'])
        self.indi_allsky_config['FILETRANSFER']['ATOMIC_TRANSFERS']     = bool(request.json['FILETRANSFER__ATOMIC_TRANSFERS'])
        self.indi_allsky_config['FILETRANSFER']['FORCE_IPV4']           = bool(request.json['FILETRANSFER__FORCE_IPV4'])
        self.indi_allsky_config['FILETRANSFER']['FORCE_IPV6']           = bool(request.json['FILETRANSFER__FORCE_IPV6'])
        self.indi_allsky_config['FILETRANSFER']['REMOTE_IMAGE_NAME']        = str(request.json['FILETRANSFER__REMOTE_IMAGE_NAME'])
        self.indi_allsky_config['FILETRANSFER']['REMOTE_IMAGE_FOLDER']      = str(request.json['FILETRANSFER__REMOTE_IMAGE_FOLDER'])
        self.indi_allsky_config['FILETRANSFER']['REMOTE_PANORAMA_NAME']     = str(request.json['FILETRANSFER__REMOTE_PANORAMA_NAME'])
        self.indi_allsky_config['FILETRANSFER']['REMOTE_PANORAMA_FOLDER']   = str(request.json['FILETRANSFER__REMOTE_PANORAMA_FOLDER'])
        self.indi_allsky_config['FILETRANSFER']['REMOTE_METADATA_NAME']     = str(request.json['FILETRANSFER__REMOTE_METADATA_NAME'])
        self.indi_allsky_config['FILETRANSFER']['REMOTE_METADATA_FOLDER']   = str(request.json['FILETRANSFER__REMOTE_METADATA_FOLDER'])
        self.indi_allsky_config['FILETRANSFER']['REMOTE_RAW_NAME']          = str(request.json['FILETRANSFER__REMOTE_RAW_NAME'])
        self.indi_allsky_config['FILETRANSFER']['REMOTE_RAW_FOLDER']        = str(request.json['FILETRANSFER__REMOTE_RAW_FOLDER'])
        self.indi_allsky_config['FILETRANSFER']['REMOTE_FITS_NAME']         = str(request.json['FILETRANSFER__REMOTE_FITS_NAME'])
        self.indi_allsky_config['FILETRANSFER']['REMOTE_FITS_FOLDER']       = str(request.json['FILETRANSFER__REMOTE_FITS_FOLDER'])
        self.indi_allsky_config['FILETRANSFER']['REMOTE_VIDEO_NAME']        = str(request.json['FILETRANSFER__REMOTE_VIDEO_NAME'])
        self.indi_allsky_config['FILETRANSFER']['REMOTE_VIDEO_FOLDER']      = str(request.json['FILETRANSFER__REMOTE_VIDEO_FOLDER'])
        self.indi_allsky_config['FILETRANSFER']['REMOTE_MINI_VIDEO_NAME']   = str(request.json['FILETRANSFER__REMOTE_MINI_VIDEO_NAME'])
        self.indi_allsky_config['FILETRANSFER']['REMOTE_MINI_VIDEO_FOLDER'] = str(request.json['FILETRANSFER__REMOTE_MINI_VIDEO_FOLDER'])
        self.indi_allsky_config['FILETRANSFER']['REMOTE_KEOGRAM_NAME']      = str(request.json['FILETRANSFER__REMOTE_KEOGRAM_NAME'])
        self.indi_allsky_config['FILETRANSFER']['REMOTE_KEOGRAM_FOLDER']    = str(request.json['FILETRANSFER__REMOTE_KEOGRAM_FOLDER'])
        self.indi_allsky_config['FILETRANSFER']['REMOTE_STARTRAIL_NAME']    = str(request.json['FILETRANSFER__REMOTE_STARTRAIL_NAME'])
        self.indi_allsky_config['FILETRANSFER']['REMOTE_STARTRAIL_FOLDER']  = str(request.json['FILETRANSFER__REMOTE_STARTRAIL_FOLDER'])
        self.indi_allsky_config['FILETRANSFER']['REMOTE_STARTRAIL_VIDEO_NAME']   = str(request.json['FILETRANSFER__REMOTE_STARTRAIL_VIDEO_NAME'])
        self.indi_allsky_config['FILETRANSFER']['REMOTE_STARTRAIL_VIDEO_FOLDER'] = str(request.json['FILETRANSFER__REMOTE_STARTRAIL_VIDEO_FOLDER'])
        self.indi_allsky_config['FILETRANSFER']['REMOTE_PANORAMA_VIDEO_NAME']    = str(request.json['FILETRANSFER__REMOTE_PANORAMA_VIDEO_NAME'])
        self.indi_allsky_config['FILETRANSFER']['REMOTE_PANORAMA_VIDEO_FOLDER']  = str(request.json['FILETRANSFER__REMOTE_PANORAMA_VIDEO_FOLDER'])
        self.indi_allsky_config['FILETRANSFER']['REMOTE_REALTIME_KEOGRAM_NAME']  = str(request.json['FILETRANSFER__REMOTE_REALTIME_KEOGRAM_NAME'])
        self.indi_allsky_config['FILETRANSFER']['REMOTE_REALTIME_KEOGRAM_FOLDER'] = str(request.json['FILETRANSFER__REMOTE_REALTIME_KEOGRAM_FOLDER'])
        self.indi_allsky_config['FILETRANSFER']['REMOTE_ENDOFNIGHT_FOLDER']      = str(request.json['FILETRANSFER__REMOTE_ENDOFNIGHT_FOLDER'])
        self.indi_allsky_config['FILETRANSFER']['REMOTE_LATEST_FOLDER']          = str(request.json['FILETRANSFER__REMOTE_LATEST_FOLDER'])
        self.indi_allsky_config['FILETRANSFER']['REMOTE_DB_BACKUP_FOLDER']       = str(request.json['FILETRANSFER__REMOTE_DB_BACKUP_FOLDER'])
        self.indi_allsky_config['FILETRANSFER']['UPLOAD_IMAGE']         = int(request.json['FILETRANSFER__UPLOAD_IMAGE'])
        self.indi_allsky_config['FILETRANSFER']['UPLOAD_PANORAMA']      = int(request.json['FILETRANSFER__UPLOAD_PANORAMA'])
        self.indi_allsky_config['FILETRANSFER']['UPLOAD_METADATA']      = bool(request.json['FILETRANSFER__UPLOAD_METADATA'])
        self.indi_allsky_config['FILETRANSFER']['UPLOAD_VIDEO']         = bool(request.json['FILETRANSFER__UPLOAD_VIDEO'])
        self.indi_allsky_config['FILETRANSFER']['UPLOAD_MINI_VIDEO']    = bool(request.json['FILETRANSFER__UPLOAD_MINI_VIDEO'])
        self.indi_allsky_config['FILETRANSFER']['UPLOAD_RAW']           = bool(request.json['FILETRANSFER__UPLOAD_RAW'])
        self.indi_allsky_config['FILETRANSFER']['UPLOAD_FITS']          = bool(request.json['FILETRANSFER__UPLOAD_FITS'])
        self.indi_allsky_config['FILETRANSFER']['UPLOAD_KEOGRAM']       = bool(request.json['FILETRANSFER__UPLOAD_KEOGRAM'])
        self.indi_allsky_config['FILETRANSFER']['UPLOAD_STARTRAIL']     = bool(request.json['FILETRANSFER__UPLOAD_STARTRAIL'])
        self.indi_allsky_config['FILETRANSFER']['UPLOAD_STARTRAIL_VIDEO']  = bool(request.json['FILETRANSFER__UPLOAD_STARTRAIL_VIDEO'])
        self.indi_allsky_config['FILETRANSFER']['UPLOAD_PANORAMA_VIDEO']   = bool(request.json['FILETRANSFER__UPLOAD_PANORAMA_VIDEO'])
        self.indi_allsky_config['FILETRANSFER']['UPLOAD_REALTIME_KEOGRAM'] = int(request.json['FILETRANSFER__UPLOAD_REALTIME_KEOGRAM'])
        self.indi_allsky_config['FILETRANSFER']['UPLOAD_ENDOFNIGHT']       = bool(request.json['FILETRANSFER__UPLOAD_ENDOFNIGHT'])
        self.indi_allsky_config['FILETRANSFER']['UPLOAD_LATEST_IMAGE']     = bool(request.json['FILETRANSFER__UPLOAD_LATEST_IMAGE'])
        self.indi_allsky_config['FILETRANSFER']['UPLOAD_LATEST_PANORAMA']  = bool(request.json['FILETRANSFER__UPLOAD_LATEST_PANORAMA'])
        self.indi_allsky_config['FILETRANSFER']['UPLOAD_LATEST_RAW']       = bool(request.json['FILETRANSFER__UPLOAD_LATEST_RAW'])
        self.indi_allsky_config['FILETRANSFER']['UPLOAD_LATEST_VIDEO']     = bool(request.json['FILETRANSFER__UPLOAD_LATEST_VIDEO'])
        self.indi_allsky_config['FILETRANSFER']['UPLOAD_DB_BACKUP']        = bool(request.json['FILETRANSFER__UPLOAD_DB_BACKUP'])
        self.indi_allsky_config['S3UPLOAD']['CLASSNAME']                = str(request.json['S3UPLOAD__CLASSNAME'])
        self.indi_allsky_config['S3UPLOAD']['ENABLE']                   = bool(request.json['S3UPLOAD__ENABLE'])
        self.indi_allsky_config['S3UPLOAD']['ACCESS_KEY']               = str(request.json['S3UPLOAD__ACCESS_KEY'])
        self.indi_allsky_config['S3UPLOAD']['SECRET_KEY']               = str(request.json['S3UPLOAD__SECRET_KEY'])
        self.indi_allsky_config['S3UPLOAD']['CREDS_FILE']               = str(request.json['S3UPLOAD__CREDS_FILE'])
        self.indi_allsky_config['S3UPLOAD']['BUCKET']                   = str(request.json['S3UPLOAD__BUCKET'])
        self.indi_allsky_config['S3UPLOAD']['REGION']                   = str(request.json['S3UPLOAD__REGION'])
        self.indi_allsky_config['S3UPLOAD']['NAMESPACE']                = str(request.json['S3UPLOAD__NAMESPACE'])
        self.indi_allsky_config['S3UPLOAD']['HOST']                     = str(request.json['S3UPLOAD__HOST'])
        self.indi_allsky_config['S3UPLOAD']['ENDPOINT_URL']             = str(request.json['S3UPLOAD__ENDPOINT_URL'])
        self.indi_allsky_config['S3UPLOAD']['PORT']                     = int(request.json['S3UPLOAD__PORT'])
        self.indi_allsky_config['S3UPLOAD']['CONNECT_TIMEOUT']          = float(request.json['S3UPLOAD__CONNECT_TIMEOUT'])
        self.indi_allsky_config['S3UPLOAD']['TIMEOUT']                  = float(request.json['S3UPLOAD__TIMEOUT'])
        self.indi_allsky_config['S3UPLOAD']['URL_TEMPLATE']             = str(request.json['S3UPLOAD__URL_TEMPLATE'])
        self.indi_allsky_config['S3UPLOAD']['STORAGE_CLASS']            = str(request.json['S3UPLOAD__STORAGE_CLASS'])
        self.indi_allsky_config['S3UPLOAD']['ACL']                      = str(request.json['S3UPLOAD__ACL'])
        self.indi_allsky_config['S3UPLOAD']['TLS']                      = bool(request.json['S3UPLOAD__TLS'])
        self.indi_allsky_config['S3UPLOAD']['CERT_BYPASS']              = bool(request.json['S3UPLOAD__CERT_BYPASS'])
        self.indi_allsky_config['S3UPLOAD']['UPLOAD_FITS']              = bool(request.json['S3UPLOAD__UPLOAD_FITS'])
        self.indi_allsky_config['S3UPLOAD']['UPLOAD_RAW']               = bool(request.json['S3UPLOAD__UPLOAD_RAW'])
        self.indi_allsky_config['MQTTPUBLISH']['ENABLE']                = bool(request.json['MQTTPUBLISH__ENABLE'])
        self.indi_allsky_config['MQTTPUBLISH']['TRANSPORT']             = str(request.json['MQTTPUBLISH__TRANSPORT'])
        self.indi_allsky_config['MQTTPUBLISH']['PROTOCOL']              = str(request.json['MQTTPUBLISH__PROTOCOL'])
        self.indi_allsky_config['MQTTPUBLISH']['HOST']                  = str(request.json['MQTTPUBLISH__HOST'])
        self.indi_allsky_config['MQTTPUBLISH']['PORT']                  = int(request.json['MQTTPUBLISH__PORT'])
        self.indi_allsky_config['MQTTPUBLISH']['USERNAME']              = str(request.json['MQTTPUBLISH__USERNAME'])
        self.indi_allsky_config['MQTTPUBLISH']['PASSWORD']              = str(request.json['MQTTPUBLISH__PASSWORD'])
        self.indi_allsky_config['MQTTPUBLISH']['BASE_TOPIC']            = str(request.json['MQTTPUBLISH__BASE_TOPIC'])
        self.indi_allsky_config['MQTTPUBLISH']['QOS']                   = int(request.json['MQTTPUBLISH__QOS'])
        self.indi_allsky_config['MQTTPUBLISH']['TLS']                   = bool(request.json['MQTTPUBLISH__TLS'])
        self.indi_allsky_config['MQTTPUBLISH']['CERT_BYPASS']           = bool(request.json['MQTTPUBLISH__CERT_BYPASS'])
        self.indi_allsky_config['MQTTPUBLISH']['PUBLISH_IMAGE']         = bool(request.json['MQTTPUBLISH__PUBLISH_IMAGE'])
        self.indi_allsky_config['SYNCAPI']['ENABLE']                    = bool(request.json['SYNCAPI__ENABLE'])
        self.indi_allsky_config['SYNCAPI']['BASEURL']                   = str(request.json['SYNCAPI__BASEURL'])
        self.indi_allsky_config['SYNCAPI']['USERNAME']                  = str(request.json['SYNCAPI__USERNAME'])
        self.indi_allsky_config['SYNCAPI']['APIKEY']                    = str(request.json['SYNCAPI__APIKEY'])
        self.indi_allsky_config['SYNCAPI']['CERT_BYPASS']               = bool(request.json['SYNCAPI__CERT_BYPASS'])
        self.indi_allsky_config['SYNCAPI']['POST_S3']                   = bool(request.json['SYNCAPI__POST_S3'])
        self.indi_allsky_config['SYNCAPI']['EMPTY_FILE']                = bool(request.json['SYNCAPI__EMPTY_FILE'])
        self.indi_allsky_config['SYNCAPI']['UPLOAD_IMAGE']              = int(request.json['SYNCAPI__UPLOAD_IMAGE'])
        self.indi_allsky_config['SYNCAPI']['UPLOAD_PANORAMA']           = int(request.json['SYNCAPI__UPLOAD_PANORAMA'])
        #self.indi_allsky_config['SYNCAPI']['UPLOAD_VIDEO']              = bool(request.json['SYNCAPI__UPLOAD_VIDEO'])  # cannot be changed
        self.indi_allsky_config['SYNCAPI']['CONNECT_TIMEOUT']           = float(request.json['SYNCAPI__CONNECT_TIMEOUT'])
        self.indi_allsky_config['SYNCAPI']['TIMEOUT']                   = float(request.json['SYNCAPI__TIMEOUT'])
        self.indi_allsky_config['YOUTUBE']['ENABLE']                    = bool(request.json['YOUTUBE__ENABLE'])
        self.indi_allsky_config['YOUTUBE']['SECRETS_FILE']              = str(request.json['YOUTUBE__SECRETS_FILE'])
        self.indi_allsky_config['YOUTUBE']['PRIVACY_STATUS']            = str(request.json['YOUTUBE__PRIVACY_STATUS'])
        self.indi_allsky_config['YOUTUBE']['TITLE_TEMPLATE']            = str(request.json['YOUTUBE__TITLE_TEMPLATE'])
        self.indi_allsky_config['YOUTUBE']['DESCRIPTION_TEMPLATE']      = str(request.json['YOUTUBE__DESCRIPTION_TEMPLATE'])
        self.indi_allsky_config['YOUTUBE']['CATEGORY']                  = int(request.json['YOUTUBE__CATEGORY'])
        self.indi_allsky_config['YOUTUBE']['UPLOAD_VIDEO']              = bool(request.json['YOUTUBE__UPLOAD_VIDEO'])
        self.indi_allsky_config['YOUTUBE']['UPLOAD_MINI_VIDEO']         = bool(request.json['YOUTUBE__UPLOAD_MINI_VIDEO'])
        self.indi_allsky_config['YOUTUBE']['UPLOAD_STARTRAIL_VIDEO']    = bool(request.json['YOUTUBE__UPLOAD_STARTRAIL_VIDEO'])
        self.indi_allsky_config['YOUTUBE']['UPLOAD_PANORAMA_VIDEO']     = bool(request.json['YOUTUBE__UPLOAD_PANORAMA_VIDEO'])
        self.indi_allsky_config['FITSHEADERS'][0][0]                    = str(request.json['FITSHEADERS__0__KEY'])
        self.indi_allsky_config['FITSHEADERS'][0][1]                    = str(request.json['FITSHEADERS__0__VAL'])
        self.indi_allsky_config['FITSHEADERS'][1][0]                    = str(request.json['FITSHEADERS__1__KEY'])
        self.indi_allsky_config['FITSHEADERS'][1][1]                    = str(request.json['FITSHEADERS__1__VAL'])
        self.indi_allsky_config['FITSHEADERS'][2][0]                    = str(request.json['FITSHEADERS__2__KEY'])
        self.indi_allsky_config['FITSHEADERS'][2][1]                    = str(request.json['FITSHEADERS__2__VAL'])
        self.indi_allsky_config['FITSHEADERS'][3][0]                    = str(request.json['FITSHEADERS__3__KEY'])
        self.indi_allsky_config['FITSHEADERS'][3][1]                    = str(request.json['FITSHEADERS__3__VAL'])
        self.indi_allsky_config['FITSHEADERS'][4][0]                    = str(request.json['FITSHEADERS__4__KEY'])
        self.indi_allsky_config['FITSHEADERS'][4][1]                    = str(request.json['FITSHEADERS__4__VAL'])
        self.indi_allsky_config['LIBCAMERA']['IMAGE_FILE_TYPE']         = str(request.json['LIBCAMERA__IMAGE_FILE_TYPE'])
        self.indi_allsky_config['LIBCAMERA']['IMAGE_FILE_TYPE_DAY']     = str(request.json['LIBCAMERA__IMAGE_FILE_TYPE_DAY'])
        self.indi_allsky_config['LIBCAMERA']['IMMEDIATE']               = bool(request.json['LIBCAMERA__IMMEDIATE'])
        self.indi_allsky_config['LIBCAMERA']['IMMEDIATE_DAY']           = bool(request.json['LIBCAMERA__IMMEDIATE_DAY'])
        self.indi_allsky_config['LIBCAMERA']['AWB']                     = str(request.json['LIBCAMERA__AWB'])
        self.indi_allsky_config['LIBCAMERA']['AWB_DAY']                 = str(request.json['LIBCAMERA__AWB_DAY'])
        self.indi_allsky_config['LIBCAMERA']['AWB_ENABLE']              = bool(request.json['LIBCAMERA__AWB_ENABLE'])
        self.indi_allsky_config['LIBCAMERA']['AWB_ENABLE_DAY']          = bool(request.json['LIBCAMERA__AWB_ENABLE_DAY'])
        self.indi_allsky_config['LIBCAMERA']['CCM_DISABLE']             = bool(request.json['LIBCAMERA__CCM_DISABLE'])
        self.indi_allsky_config['LIBCAMERA']['CCM_DISABLE_DAY']         = bool(request.json['LIBCAMERA__CCM_DISABLE_DAY'])
        self.indi_allsky_config['LIBCAMERA']['CAMERA_ID']               = int(request.json['LIBCAMERA__CAMERA_ID'])
        self.indi_allsky_config['LIBCAMERA']['EXTRA_OPTIONS']           = str(request.json['LIBCAMERA__EXTRA_OPTIONS'])
        self.indi_allsky_config['LIBCAMERA']['EXTRA_OPTIONS_DAY']       = str(request.json['LIBCAMERA__EXTRA_OPTIONS_DAY'])
        self.indi_allsky_config['LIBCAMERA']['MQTT_TRANSPORT']          = str(request.json['LIBCAMERA__MQTT_TRANSPORT'])
        self.indi_allsky_config['LIBCAMERA']['MQTT_PROTOCOL']           = str(request.json['LIBCAMERA__MQTT_PROTOCOL'])
        self.indi_allsky_config['LIBCAMERA']['MQTT_HOST']               = str(request.json['LIBCAMERA__MQTT_HOST'])
        self.indi_allsky_config['LIBCAMERA']['MQTT_PORT']               = int(request.json['LIBCAMERA__MQTT_PORT'])
        self.indi_allsky_config['LIBCAMERA']['MQTT_USERNAME']           = str(request.json['LIBCAMERA__MQTT_USERNAME'])
        self.indi_allsky_config['LIBCAMERA']['MQTT_PASSWORD']           = str(request.json['LIBCAMERA__MQTT_PASSWORD'])
        self.indi_allsky_config['LIBCAMERA']['MQTT_QOS']                = int(request.json['LIBCAMERA__MQTT_QOS'])
        self.indi_allsky_config['LIBCAMERA']['MQTT_TLS']                = bool(request.json['LIBCAMERA__MQTT_TLS'])
        self.indi_allsky_config['LIBCAMERA']['MQTT_CERT_BYPASS']        = bool(request.json['LIBCAMERA__MQTT_CERT_BYPASS'])
        self.indi_allsky_config['LIBCAMERA']['MQTT_EXPOSURE_TOPIC']     = str(request.json['LIBCAMERA__MQTT_EXPOSURE_TOPIC'])
        self.indi_allsky_config['LIBCAMERA']['MQTT_IMAGE_TOPIC']        = str(request.json['LIBCAMERA__MQTT_IMAGE_TOPIC'])
        self.indi_allsky_config['LIBCAMERA']['MQTT_METADATA_TOPIC']     = str(request.json['LIBCAMERA__MQTT_METADATA_TOPIC'])
        self.indi_allsky_config['PYCURL_CAMERA']['URL']                 = str(request.json['PYCURL_CAMERA__URL'])
        self.indi_allsky_config['PYCURL_CAMERA']['IMAGE_FILE_TYPE']     = str(request.json['PYCURL_CAMERA__IMAGE_FILE_TYPE'])
        self.indi_allsky_config['PYCURL_CAMERA']['USERNAME']            = str(request.json['PYCURL_CAMERA__USERNAME'])
        self.indi_allsky_config['PYCURL_CAMERA']['PASSWORD']            = str(request.json['PYCURL_CAMERA__PASSWORD'])
        self.indi_allsky_config['ACCUM_CAMERA']['SUB_EXPOSURE_MAX']     = float(request.json['ACCUM_CAMERA__SUB_EXPOSURE_MAX'])
        self.indi_allsky_config['ACCUM_CAMERA']['EVEN_EXPOSURES']       = bool(request.json['ACCUM_CAMERA__EVEN_EXPOSURES'])
        self.indi_allsky_config['ACCUM_CAMERA']['CLAMP_16BIT']          = bool(request.json['ACCUM_CAMERA__CLAMP_16BIT'])
        self.indi_allsky_config['TEST_CAMERA']['WIDTH']                 = int(request.json['TEST_CAMERA__WIDTH'])
        self.indi_allsky_config['TEST_CAMERA']['HEIGHT']                = int(request.json['TEST_CAMERA__HEIGHT'])
        self.indi_allsky_config['TEST_CAMERA']['IMAGE_CIRCLE_DIAMETER'] = int(request.json['TEST_CAMERA__IMAGE_CIRCLE_DIAMETER'])
        self.indi_allsky_config['TEST_CAMERA']['IMAGE_CIRCLE_OFFSET_X'] = int(request.json['TEST_CAMERA__IMAGE_CIRCLE_OFFSET_X'])
        self.indi_allsky_config['TEST_CAMERA']['IMAGE_CIRCLE_OFFSET_Y'] = int(request.json['TEST_CAMERA__IMAGE_CIRCLE_OFFSET_Y'])
        self.indi_allsky_config['TEST_CAMERA']['ROTATING_STAR_COUNT']   = int(request.json['TEST_CAMERA__ROTATING_STAR_COUNT'])
        self.indi_allsky_config['TEST_CAMERA']['ROTATING_STAR_FACTOR']  = float(request.json['TEST_CAMERA__ROTATING_STAR_FACTOR'])
        self.indi_allsky_config['TEST_CAMERA']['BUBBLE_COUNT']          = int(request.json['TEST_CAMERA__BUBBLE_COUNT'])
        self.indi_allsky_config['VIRTUALSKY']['MAGNITUDE']              = float(request.json['VIRTUALSKY__MAGNITUDE'])
        self.indi_allsky_config['VIRTUALSKY']['CONSTELLATIONS']         = bool(request.json['VIRTUALSKY__CONSTELLATIONS'])
        self.indi_allsky_config['VIRTUALSKY']['CONSTELLATIONLABELS']    = bool(request.json['VIRTUALSKY__CONSTELLATIONLABELS'])
        self.indi_allsky_config['VIRTUALSKY']['SHOWSTARS']              = bool(request.json['VIRTUALSKY__SHOWSTARS'])
        self.indi_allsky_config['VIRTUALSKY']['SHOWSTARLABELS']         = bool(request.json['VIRTUALSKY__SHOWSTARLABELS'])
        self.indi_allsky_config['VIRTUALSKY']['SHOWPLANETS']            = bool(request.json['VIRTUALSKY__SHOWPLANETS'])
        self.indi_allsky_config['VIRTUALSKY']['SHOWPLANETLABELS']       = bool(request.json['VIRTUALSKY__SHOWPLANETLABELS'])
        self.indi_allsky_config['VIRTUALSKY']['IMAGE_CIRCLE_DIAMETER']  = int(request.json['VIRTUALSKY__IMAGE_CIRCLE_DIAMETER'])
        self.indi_allsky_config['VIRTUALSKY']['LATITUDE_OFFSET']        = float(request.json['VIRTUALSKY__LATITUDE_OFFSET'])
        self.indi_allsky_config['VIRTUALSKY']['LONGITUDE_OFFSET']       = float(request.json['VIRTUALSKY__LONGITUDE_OFFSET'])
        self.indi_allsky_config['VIRTUALSKY']['OFFSET_X']               = int(request.json['VIRTUALSKY__OFFSET_X'])
        self.indi_allsky_config['VIRTUALSKY']['OFFSET_Y']               = int(request.json['VIRTUALSKY__OFFSET_Y'])
        #self.indi_allsky_config['VIRTUALSKY']['FLIP_NS']                = bool(request.json['VIRTUALSKY__FLIP_NS'])
        #self.indi_allsky_config['VIRTUALSKY']['FLIP_EW']                = bool(request.json['VIRTUALSKY__FLIP_EW'])
        self.indi_allsky_config['CIRCULAR_DISPLAY']['ENABLE']           = bool(request.json['CIRCULAR_DISPLAY__ENABLE'])
        self.indi_allsky_config['CIRCULAR_DISPLAY']['RESOLUTION']       = int(request.json['CIRCULAR_DISPLAY__RESOLUTION'])
        self.indi_allsky_config['CIRCULAR_DISPLAY']['IMAGE_CIRCLE_DIAMETER'] = int(request.json['CIRCULAR_DISPLAY__IMAGE_CIRCLE_DIAMETER'])
        self.indi_allsky_config['FOCUSER']['CLASSNAME']                 = str(request.json['FOCUSER__CLASSNAME'])
        self.indi_allsky_config['FOCUSER']['GPIO_PIN_1']                = str(request.json['FOCUSER__GPIO_PIN_1'])
        self.indi_allsky_config['FOCUSER']['GPIO_PIN_2']                = str(request.json['FOCUSER__GPIO_PIN_2'])
        self.indi_allsky_config['FOCUSER']['GPIO_PIN_3']                = str(request.json['FOCUSER__GPIO_PIN_3'])
        self.indi_allsky_config['FOCUSER']['GPIO_PIN_4']                = str(request.json['FOCUSER__GPIO_PIN_4'])
        self.indi_allsky_config['FOCUSER']['I2C_ADDRESS']               = str(request.json['FOCUSER__I2C_ADDRESS'])
        self.indi_allsky_config['DEW_HEATER']['CLASSNAME']              = str(request.json['DEW_HEATER__CLASSNAME'])
        self.indi_allsky_config['DEW_HEATER']['I2C_ADDRESS']            = str(request.json['DEW_HEATER__I2C_ADDRESS'])
        self.indi_allsky_config['DEW_HEATER']['PIN_1']                  = str(request.json['DEW_HEATER__PIN_1'])
        self.indi_allsky_config['DEW_HEATER']['INVERT_OUTPUT']          = bool(request.json['DEW_HEATER__INVERT_OUTPUT'])
        self.indi_allsky_config['DEW_HEATER']['ENABLE_DAY']             = bool(request.json['DEW_HEATER__ENABLE_DAY'])
        self.indi_allsky_config['DEW_HEATER']['LEVEL_DEF']              = int(request.json['DEW_HEATER__LEVEL_DEF'])
        self.indi_allsky_config['DEW_HEATER']['THOLD_ENABLE']           = bool(request.json['DEW_HEATER__THOLD_ENABLE'])
        self.indi_allsky_config['DEW_HEATER']['MANUAL_TARGET']          = float(request.json['DEW_HEATER__MANUAL_TARGET'])
        self.indi_allsky_config['DEW_HEATER']['TEMP_USER_VAR_SLOT']     = str(request.json['DEW_HEATER__TEMP_USER_VAR_SLOT'])
        self.indi_allsky_config['DEW_HEATER']['DEWPOINT_USER_VAR_SLOT'] = str(request.json['DEW_HEATER__DEWPOINT_USER_VAR_SLOT'])
        self.indi_allsky_config['DEW_HEATER']['LEVEL_LOW']              = int(request.json['DEW_HEATER__LEVEL_LOW'])
        self.indi_allsky_config['DEW_HEATER']['LEVEL_MED']              = int(request.json['DEW_HEATER__LEVEL_MED'])
        self.indi_allsky_config['DEW_HEATER']['LEVEL_HIGH']             = int(request.json['DEW_HEATER__LEVEL_HIGH'])
        self.indi_allsky_config['DEW_HEATER']['THOLD_DIFF_LOW']         = int(request.json['DEW_HEATER__THOLD_DIFF_LOW'])
        self.indi_allsky_config['DEW_HEATER']['THOLD_DIFF_MED']         = int(request.json['DEW_HEATER__THOLD_DIFF_MED'])
        self.indi_allsky_config['DEW_HEATER']['THOLD_DIFF_HIGH']        = int(request.json['DEW_HEATER__THOLD_DIFF_HIGH'])
        self.indi_allsky_config['DEW_HEATER']['HOLD_SECONDS']           = int(request.json['DEW_HEATER__HOLD_SECONDS'])
        self.indi_allsky_config['DEW_HEATER']['PWM_FREQUENCY']          = int(request.json['DEW_HEATER__PWM_FREQUENCY'])
        self.indi_allsky_config['FAN']['CLASSNAME']                     = str(request.json['FAN__CLASSNAME'])
        self.indi_allsky_config['FAN']['I2C_ADDRESS']                   = str(request.json['FAN__I2C_ADDRESS'])
        self.indi_allsky_config['FAN']['PIN_1']                         = str(request.json['FAN__PIN_1'])
        self.indi_allsky_config['FAN']['INVERT_OUTPUT']                 = bool(request.json['FAN__INVERT_OUTPUT'])
        self.indi_allsky_config['FAN']['ENABLE_NIGHT']                  = bool(request.json['FAN__ENABLE_NIGHT'])
        self.indi_allsky_config['FAN']['LEVEL_DEF']                     = int(request.json['FAN__LEVEL_DEF'])
        self.indi_allsky_config['FAN']['THOLD_ENABLE']                  = bool(request.json['FAN__THOLD_ENABLE'])
        self.indi_allsky_config['FAN']['TARGET']                        = float(request.json['FAN__TARGET'])
        self.indi_allsky_config['FAN']['TEMP_USER_VAR_SLOT']            = str(request.json['FAN__TEMP_USER_VAR_SLOT'])
        self.indi_allsky_config['FAN']['LEVEL_LOW']                     = int(request.json['FAN__LEVEL_LOW'])
        self.indi_allsky_config['FAN']['LEVEL_MED']                     = int(request.json['FAN__LEVEL_MED'])
        self.indi_allsky_config['FAN']['LEVEL_HIGH']                    = int(request.json['FAN__LEVEL_HIGH'])
        self.indi_allsky_config['FAN']['THOLD_DIFF_LOW']                = int(request.json['FAN__THOLD_DIFF_LOW'])
        self.indi_allsky_config['FAN']['THOLD_DIFF_MED']                = int(request.json['FAN__THOLD_DIFF_MED'])
        self.indi_allsky_config['FAN']['THOLD_DIFF_HIGH']               = int(request.json['FAN__THOLD_DIFF_HIGH'])
        self.indi_allsky_config['FAN']['HOLD_SECONDS']                  = int(request.json['FAN__HOLD_SECONDS'])
        self.indi_allsky_config['FAN']['PWM_FREQUENCY']                 = int(request.json['FAN__PWM_FREQUENCY'])
        self.indi_allsky_config['GENERIC_GPIO']['A_CLASSNAME']          = str(request.json['GENERIC_GPIO__A_CLASSNAME'])
        self.indi_allsky_config['GENERIC_GPIO']['A_I2C_ADDRESS']        = str(request.json['GENERIC_GPIO__A_I2C_ADDRESS'])
        self.indi_allsky_config['GENERIC_GPIO']['A_PIN_1']              = str(request.json['GENERIC_GPIO__A_PIN_1'])
        self.indi_allsky_config['GENERIC_GPIO']['A_INVERT_OUTPUT']      = bool(request.json['GENERIC_GPIO__A_INVERT_OUTPUT'])
        self.indi_allsky_config['MANUAL_GPIO']['A_CLASSNAME']           = str(request.json['MANUAL_GPIO__A_CLASSNAME'])
        self.indi_allsky_config['MANUAL_GPIO']['A_PIN_1']               = str(request.json['MANUAL_GPIO__A_PIN_1'])
        self.indi_allsky_config['MANUAL_GPIO']['A_PIN_2']               = str(request.json['MANUAL_GPIO__A_PIN_2'])
        self.indi_allsky_config['MANUAL_GPIO']['A_PIN_3']               = str(request.json['MANUAL_GPIO__A_PIN_3'])
        self.indi_allsky_config['DEVICE']['MQTT_TRANSPORT']             = str(request.json['DEVICE__MQTT_TRANSPORT'])
        self.indi_allsky_config['DEVICE']['MQTT_PROTOCOL']              = str(request.json['DEVICE__MQTT_PROTOCOL'])
        self.indi_allsky_config['DEVICE']['MQTT_HOST']                  = str(request.json['DEVICE__MQTT_HOST'])
        self.indi_allsky_config['DEVICE']['MQTT_PORT']                  = int(request.json['DEVICE__MQTT_PORT'])
        self.indi_allsky_config['DEVICE']['MQTT_USERNAME']              = str(request.json['DEVICE__MQTT_USERNAME'])
        self.indi_allsky_config['DEVICE']['MQTT_PASSWORD']              = str(request.json['DEVICE__MQTT_PASSWORD'])
        self.indi_allsky_config['DEVICE']['MQTT_QOS']                   = int(request.json['DEVICE__MQTT_QOS'])
        self.indi_allsky_config['DEVICE']['MQTT_TLS']                   = bool(request.json['DEVICE__MQTT_TLS'])
        self.indi_allsky_config['DEVICE']['MQTT_CERT_BYPASS']           = bool(request.json['DEVICE__MQTT_CERT_BYPASS'])
        self.indi_allsky_config['TEMP_SENSOR']['A_CLASSNAME']           = str(request.json['TEMP_SENSOR__A_CLASSNAME'])
        self.indi_allsky_config['TEMP_SENSOR']['A_LABEL']               = str(request.json['TEMP_SENSOR__A_LABEL'])
        self.indi_allsky_config['TEMP_SENSOR']['A_PIN_1']               = str(request.json['TEMP_SENSOR__A_PIN_1'])
        self.indi_allsky_config['TEMP_SENSOR']['A_PIN_2']               = str(request.json['TEMP_SENSOR__A_PIN_2'])
        self.indi_allsky_config['TEMP_SENSOR']['A_USER_VAR_SLOT']       = str(request.json['TEMP_SENSOR__A_USER_VAR_SLOT'])
        self.indi_allsky_config['TEMP_SENSOR']['A_I2C_ADDRESS']         = str(request.json['TEMP_SENSOR__A_I2C_ADDRESS'])
        self.indi_allsky_config['TEMP_SENSOR']['A_TITLE_TEMPLATE']      = str(request.json['TEMP_SENSOR__A_TITLE_TEMPLATE'])
        self.indi_allsky_config['TEMP_SENSOR']['B_CLASSNAME']           = str(request.json['TEMP_SENSOR__B_CLASSNAME'])
        self.indi_allsky_config['TEMP_SENSOR']['B_LABEL']               = str(request.json['TEMP_SENSOR__B_LABEL'])
        self.indi_allsky_config['TEMP_SENSOR']['B_PIN_1']               = str(request.json['TEMP_SENSOR__B_PIN_1'])
        self.indi_allsky_config['TEMP_SENSOR']['B_PIN_2']               = str(request.json['TEMP_SENSOR__B_PIN_2'])
        self.indi_allsky_config['TEMP_SENSOR']['B_USER_VAR_SLOT']       = str(request.json['TEMP_SENSOR__B_USER_VAR_SLOT'])
        self.indi_allsky_config['TEMP_SENSOR']['B_I2C_ADDRESS']         = str(request.json['TEMP_SENSOR__B_I2C_ADDRESS'])
        self.indi_allsky_config['TEMP_SENSOR']['B_TITLE_TEMPLATE']      = str(request.json['TEMP_SENSOR__B_TITLE_TEMPLATE'])
        self.indi_allsky_config['TEMP_SENSOR']['C_CLASSNAME']           = str(request.json['TEMP_SENSOR__C_CLASSNAME'])
        self.indi_allsky_config['TEMP_SENSOR']['C_LABEL']               = str(request.json['TEMP_SENSOR__C_LABEL'])
        self.indi_allsky_config['TEMP_SENSOR']['C_PIN_1']               = str(request.json['TEMP_SENSOR__C_PIN_1'])
        self.indi_allsky_config['TEMP_SENSOR']['C_PIN_2']               = str(request.json['TEMP_SENSOR__C_PIN_2'])
        self.indi_allsky_config['TEMP_SENSOR']['C_USER_VAR_SLOT']       = str(request.json['TEMP_SENSOR__C_USER_VAR_SLOT'])
        self.indi_allsky_config['TEMP_SENSOR']['C_I2C_ADDRESS']         = str(request.json['TEMP_SENSOR__C_I2C_ADDRESS'])
        self.indi_allsky_config['TEMP_SENSOR']['C_TITLE_TEMPLATE']      = str(request.json['TEMP_SENSOR__C_TITLE_TEMPLATE'])
        self.indi_allsky_config['TEMP_SENSOR']['D_CLASSNAME']           = str(request.json['TEMP_SENSOR__D_CLASSNAME'])
        self.indi_allsky_config['TEMP_SENSOR']['D_LABEL']               = str(request.json['TEMP_SENSOR__D_LABEL'])
        self.indi_allsky_config['TEMP_SENSOR']['D_PIN_1']               = str(request.json['TEMP_SENSOR__D_PIN_1'])
        self.indi_allsky_config['TEMP_SENSOR']['D_PIN_2']               = str(request.json['TEMP_SENSOR__D_PIN_2'])
        self.indi_allsky_config['TEMP_SENSOR']['D_USER_VAR_SLOT']       = str(request.json['TEMP_SENSOR__D_USER_VAR_SLOT'])
        self.indi_allsky_config['TEMP_SENSOR']['D_I2C_ADDRESS']         = str(request.json['TEMP_SENSOR__D_I2C_ADDRESS'])
        self.indi_allsky_config['TEMP_SENSOR']['D_TITLE_TEMPLATE']      = str(request.json['TEMP_SENSOR__D_TITLE_TEMPLATE'])
        self.indi_allsky_config['TEMP_SENSOR']['E_CLASSNAME']           = str(request.json['TEMP_SENSOR__E_CLASSNAME'])
        self.indi_allsky_config['TEMP_SENSOR']['E_LABEL']               = str(request.json['TEMP_SENSOR__E_LABEL'])
        self.indi_allsky_config['TEMP_SENSOR']['E_PIN_1']               = str(request.json['TEMP_SENSOR__E_PIN_1'])
        self.indi_allsky_config['TEMP_SENSOR']['E_PIN_2']               = str(request.json['TEMP_SENSOR__E_PIN_2'])
        self.indi_allsky_config['TEMP_SENSOR']['E_USER_VAR_SLOT']       = str(request.json['TEMP_SENSOR__E_USER_VAR_SLOT'])
        self.indi_allsky_config['TEMP_SENSOR']['E_I2C_ADDRESS']         = str(request.json['TEMP_SENSOR__E_I2C_ADDRESS'])
        self.indi_allsky_config['TEMP_SENSOR']['E_TITLE_TEMPLATE']      = str(request.json['TEMP_SENSOR__E_TITLE_TEMPLATE'])
        self.indi_allsky_config['TEMP_SENSOR']['F_CLASSNAME']           = str(request.json['TEMP_SENSOR__F_CLASSNAME'])
        self.indi_allsky_config['TEMP_SENSOR']['F_LABEL']               = str(request.json['TEMP_SENSOR__F_LABEL'])
        self.indi_allsky_config['TEMP_SENSOR']['F_PIN_1']               = str(request.json['TEMP_SENSOR__F_PIN_1'])
        self.indi_allsky_config['TEMP_SENSOR']['F_PIN_2']               = str(request.json['TEMP_SENSOR__F_PIN_2'])
        self.indi_allsky_config['TEMP_SENSOR']['F_USER_VAR_SLOT']       = str(request.json['TEMP_SENSOR__F_USER_VAR_SLOT'])
        self.indi_allsky_config['TEMP_SENSOR']['F_I2C_ADDRESS']         = str(request.json['TEMP_SENSOR__F_I2C_ADDRESS'])
        self.indi_allsky_config['TEMP_SENSOR']['F_TITLE_TEMPLATE']      = str(request.json['TEMP_SENSOR__F_TITLE_TEMPLATE'])
        self.indi_allsky_config['TEMP_SENSOR']['FC37_ACTIVE_LOW']       = bool(request.json['TEMP_SENSOR__FC37_ACTIVE_LOW'])
        self.indi_allsky_config['TEMP_SENSOR']['OPENWEATHERMAP_APIKEY'] = str(request.json['TEMP_SENSOR__OPENWEATHERMAP_APIKEY'])
        self.indi_allsky_config['TEMP_SENSOR']['WUNDERGROUND_APIKEY']   = str(request.json['TEMP_SENSOR__WUNDERGROUND_APIKEY'])
        self.indi_allsky_config['TEMP_SENSOR']['ASTROSPHERIC_APIKEY']   = str(request.json['TEMP_SENSOR__ASTROSPHERIC_APIKEY'])
        self.indi_allsky_config['TEMP_SENSOR']['AMBIENTWEATHER_APIKEY']         = str(request.json['TEMP_SENSOR__AMBIENTWEATHER_APIKEY'])
        self.indi_allsky_config['TEMP_SENSOR']['AMBIENTWEATHER_APPLICATIONKEY'] = str(request.json['TEMP_SENSOR__AMBIENTWEATHER_APPLICATIONKEY'])
        self.indi_allsky_config['TEMP_SENSOR']['AMBIENTWEATHER_MACADDRESS']     = str(request.json['TEMP_SENSOR__AMBIENTWEATHER_MACADDRESS'])
        self.indi_allsky_config['TEMP_SENSOR']['ECOWITT_APIKEY']         = str(request.json['TEMP_SENSOR__ECOWITT_APIKEY'])
        self.indi_allsky_config['TEMP_SENSOR']['ECOWITT_APPLICATIONKEY'] = str(request.json['TEMP_SENSOR__ECOWITT_APPLICATIONKEY'])
        self.indi_allsky_config['TEMP_SENSOR']['ECOWITT_MACADDRESS']     = str(request.json['TEMP_SENSOR__ECOWITT_MACADDRESS'])
        self.indi_allsky_config['TEMP_SENSOR']['MQTT_TRANSPORT']        = str(request.json['TEMP_SENSOR__MQTT_TRANSPORT'])
        self.indi_allsky_config['TEMP_SENSOR']['MQTT_PROTOCOL']         = str(request.json['TEMP_SENSOR__MQTT_PROTOCOL'])
        self.indi_allsky_config['TEMP_SENSOR']['MQTT_HOST']             = str(request.json['TEMP_SENSOR__MQTT_HOST'])
        self.indi_allsky_config['TEMP_SENSOR']['MQTT_PORT']             = int(request.json['TEMP_SENSOR__MQTT_PORT'])
        self.indi_allsky_config['TEMP_SENSOR']['MQTT_USERNAME']         = str(request.json['TEMP_SENSOR__MQTT_USERNAME'])
        self.indi_allsky_config['TEMP_SENSOR']['MQTT_PASSWORD']         = str(request.json['TEMP_SENSOR__MQTT_PASSWORD'])
        self.indi_allsky_config['TEMP_SENSOR']['MQTT_TLS']              = bool(request.json['TEMP_SENSOR__MQTT_TLS'])
        self.indi_allsky_config['TEMP_SENSOR']['MQTT_CERT_BYPASS']      = bool(request.json['TEMP_SENSOR__MQTT_CERT_BYPASS'])
        self.indi_allsky_config['TEMP_SENSOR']['DHT_USE_PULSEIO']       = bool(request.json['TEMP_SENSOR__DHT_USE_PULSEIO'])
        self.indi_allsky_config['TEMP_SENSOR']['SHT3X_HEATER_NIGHT']    = bool(request.json['TEMP_SENSOR__SHT3X_HEATER_NIGHT'])
        self.indi_allsky_config['TEMP_SENSOR']['SHT3X_HEATER_DAY']      = bool(request.json['TEMP_SENSOR__SHT3X_HEATER_DAY'])
        self.indi_allsky_config['TEMP_SENSOR']['SHT4X_MODE_NIGHT']      = str(request.json['TEMP_SENSOR__SHT4X_MODE_NIGHT'])
        self.indi_allsky_config['TEMP_SENSOR']['SHT4X_MODE_DAY']        = str(request.json['TEMP_SENSOR__SHT4X_MODE_DAY'])
        self.indi_allsky_config['TEMP_SENSOR']['SI7021_HEATER_LEVEL_NIGHT'] = int(request.json['TEMP_SENSOR__SI7021_HEATER_LEVEL_NIGHT'])
        self.indi_allsky_config['TEMP_SENSOR']['SI7021_HEATER_LEVEL_DAY'] = int(request.json['TEMP_SENSOR__SI7021_HEATER_LEVEL_DAY'])
        self.indi_allsky_config['TEMP_SENSOR']['HTU31D_HEATER_NIGHT']   = bool(request.json['TEMP_SENSOR__HTU31D_HEATER_NIGHT'])
        self.indi_allsky_config['TEMP_SENSOR']['HTU31D_HEATER_DAY']     = bool(request.json['TEMP_SENSOR__HTU31D_HEATER_DAY'])
        self.indi_allsky_config['TEMP_SENSOR']['HDC302X_HEATER_NIGHT']  = str(request.json['TEMP_SENSOR__HDC302X_HEATER_NIGHT'])
        self.indi_allsky_config['TEMP_SENSOR']['HDC302X_HEATER_DAY']    = str(request.json['TEMP_SENSOR__HDC302X_HEATER_DAY'])
        self.indi_allsky_config['TEMP_SENSOR']['TSL2561_GAIN_NIGHT']    = int(request.json['TEMP_SENSOR__TSL2561_GAIN_NIGHT'])
        self.indi_allsky_config['TEMP_SENSOR']['TSL2561_GAIN_DAY']      = int(request.json['TEMP_SENSOR__TSL2561_GAIN_DAY'])
        self.indi_allsky_config['TEMP_SENSOR']['TSL2561_INT_NIGHT']     = int(request.json['TEMP_SENSOR__TSL2561_INT_NIGHT'])
        self.indi_allsky_config['TEMP_SENSOR']['TSL2561_INT_DAY']       = int(request.json['TEMP_SENSOR__TSL2561_INT_DAY'])
        self.indi_allsky_config['TEMP_SENSOR']['TSL2561_DISABLE_DAY']   = bool(request.json['TEMP_SENSOR__TSL2561_DISABLE_DAY'])
        self.indi_allsky_config['TEMP_SENSOR']['TSL2591_GAIN_NIGHT']    = str(request.json['TEMP_SENSOR__TSL2591_GAIN_NIGHT'])
        self.indi_allsky_config['TEMP_SENSOR']['TSL2591_GAIN_DAY']      = str(request.json['TEMP_SENSOR__TSL2591_GAIN_DAY'])
        self.indi_allsky_config['TEMP_SENSOR']['TSL2591_INT_NIGHT']     = str(request.json['TEMP_SENSOR__TSL2591_INT_NIGHT'])
        self.indi_allsky_config['TEMP_SENSOR']['TSL2591_INT_DAY']       = str(request.json['TEMP_SENSOR__TSL2591_INT_DAY'])
        self.indi_allsky_config['TEMP_SENSOR']['TSL2591_DISABLE_DAY']   = bool(request.json['TEMP_SENSOR__TSL2591_DISABLE_DAY'])
        self.indi_allsky_config['TEMP_SENSOR']['VEML7700_GAIN_NIGHT']   = str(request.json['TEMP_SENSOR__VEML7700_GAIN_NIGHT'])
        self.indi_allsky_config['TEMP_SENSOR']['VEML7700_GAIN_DAY']     = str(request.json['TEMP_SENSOR__VEML7700_GAIN_DAY'])
        self.indi_allsky_config['TEMP_SENSOR']['VEML7700_INT_NIGHT']    = str(request.json['TEMP_SENSOR__VEML7700_INT_NIGHT'])
        self.indi_allsky_config['TEMP_SENSOR']['VEML7700_INT_DAY']      = str(request.json['TEMP_SENSOR__VEML7700_INT_DAY'])
        self.indi_allsky_config['TEMP_SENSOR']['SI1145_VIS_GAIN_NIGHT'] = str(request.json['TEMP_SENSOR__SI1145_VIS_GAIN_NIGHT'])
        self.indi_allsky_config['TEMP_SENSOR']['SI1145_VIS_GAIN_DAY']   = str(request.json['TEMP_SENSOR__SI1145_VIS_GAIN_DAY'])
        self.indi_allsky_config['TEMP_SENSOR']['SI1145_IR_GAIN_NIGHT']  = str(request.json['TEMP_SENSOR__SI1145_IR_GAIN_NIGHT'])
        self.indi_allsky_config['TEMP_SENSOR']['SI1145_IR_GAIN_DAY']    = str(request.json['TEMP_SENSOR__SI1145_IR_GAIN_DAY'])
        self.indi_allsky_config['TEMP_SENSOR']['LTR390_GAIN_NIGHT']     = str(request.json['TEMP_SENSOR__LTR390_GAIN_NIGHT'])
        self.indi_allsky_config['TEMP_SENSOR']['LTR390_GAIN_DAY']       = str(request.json['TEMP_SENSOR__LTR390_GAIN_DAY'])
        self.indi_allsky_config['TEMP_SENSOR']['INA3221_CH1_ENABLE']    = bool(request.json['TEMP_SENSOR__INA3221_CH1_ENABLE'])
        self.indi_allsky_config['TEMP_SENSOR']['INA3221_CH2_ENABLE']    = bool(request.json['TEMP_SENSOR__INA3221_CH2_ENABLE'])
        self.indi_allsky_config['TEMP_SENSOR']['INA3221_CH3_ENABLE']    = bool(request.json['TEMP_SENSOR__INA3221_CH3_ENABLE'])
        self.indi_allsky_config['TEMP_SENSOR']['AS3935_OUTDOOR_MODE']   = bool(request.json['TEMP_SENSOR__AS3935_OUTDOOR_MODE'])
        self.indi_allsky_config['TEMP_SENSOR']['AS3935_MASK_DISTURBER'] = bool(request.json['TEMP_SENSOR__AS3935_MASK_DISTURBER'])
        self.indi_allsky_config['TEMP_SENSOR']['AS3935_NOISE_LEVEL']    = int(request.json['TEMP_SENSOR__AS3935_NOISE_LEVEL'])
        self.indi_allsky_config['TEMP_SENSOR']['AS3935_SPIKE_REJECTION'] = int(request.json['TEMP_SENSOR__AS3935_SPIKE_REJECTION'])
        self.indi_allsky_config['TEMP_SENSOR']['LUX_MAGNITUDE_OFFSET']  = float(request.json['TEMP_SENSOR__LUX_MAGNITUDE_OFFSET'])
        self.indi_allsky_config['CHARTS']['CUSTOM_SLOT_1']              = str(request.json['CHARTS__CUSTOM_SLOT_1'])
        self.indi_allsky_config['CHARTS']['CUSTOM_SLOT_1_MIN']          = float(request.json['CHARTS__CUSTOM_SLOT_1_MIN'])
        self.indi_allsky_config['CHARTS']['CUSTOM_SLOT_2']              = str(request.json['CHARTS__CUSTOM_SLOT_2'])
        self.indi_allsky_config['CHARTS']['CUSTOM_SLOT_2_MIN']          = float(request.json['CHARTS__CUSTOM_SLOT_2_MIN'])
        self.indi_allsky_config['CHARTS']['CUSTOM_SLOT_3']              = str(request.json['CHARTS__CUSTOM_SLOT_3'])
        self.indi_allsky_config['CHARTS']['CUSTOM_SLOT_3_MIN']          = float(request.json['CHARTS__CUSTOM_SLOT_3_MIN'])
        self.indi_allsky_config['CHARTS']['CUSTOM_SLOT_4']              = str(request.json['CHARTS__CUSTOM_SLOT_4'])
        self.indi_allsky_config['CHARTS']['CUSTOM_SLOT_4_MIN']          = float(request.json['CHARTS__CUSTOM_SLOT_4_MIN'])
        self.indi_allsky_config['CHARTS']['CUSTOM_SLOT_5']              = str(request.json['CHARTS__CUSTOM_SLOT_5'])
        self.indi_allsky_config['CHARTS']['CUSTOM_SLOT_5_MIN']          = float(request.json['CHARTS__CUSTOM_SLOT_5_MIN'])
        self.indi_allsky_config['CHARTS']['CUSTOM_SLOT_6']              = str(request.json['CHARTS__CUSTOM_SLOT_6'])
        self.indi_allsky_config['CHARTS']['CUSTOM_SLOT_6_MIN']          = float(request.json['CHARTS__CUSTOM_SLOT_6_MIN'])
        self.indi_allsky_config['CHARTS']['CUSTOM_SLOT_7']              = str(request.json['CHARTS__CUSTOM_SLOT_7'])
        self.indi_allsky_config['CHARTS']['CUSTOM_SLOT_7_MIN']          = float(request.json['CHARTS__CUSTOM_SLOT_7_MIN'])
        self.indi_allsky_config['CHARTS']['CUSTOM_SLOT_8']              = str(request.json['CHARTS__CUSTOM_SLOT_8'])
        self.indi_allsky_config['CHARTS']['CUSTOM_SLOT_8_MIN']          = float(request.json['CHARTS__CUSTOM_SLOT_8_MIN'])
        self.indi_allsky_config['CHARTS']['CUSTOM_SLOT_9']              = str(request.json['CHARTS__CUSTOM_SLOT_9'])
        self.indi_allsky_config['CHARTS']['CUSTOM_SLOT_9_MIN']          = float(request.json['CHARTS__CUSTOM_SLOT_9_MIN'])
        self.indi_allsky_config['ADSB']['ENABLE']                       = bool(request.json['ADSB__ENABLE'])
        self.indi_allsky_config['ADSB']['DUMP1090_URL']                 = str(request.json['ADSB__DUMP1090_URL'])
        self.indi_allsky_config['ADSB']['USERNAME']                     = str(request.json['ADSB__USERNAME'])
        self.indi_allsky_config['ADSB']['PASSWORD']                     = str(request.json['ADSB__PASSWORD'])
        self.indi_allsky_config['ADSB']['CERT_BYPASS']                  = bool(request.json['ADSB__CERT_BYPASS'])
        self.indi_allsky_config['ADSB']['ALT_DEG_MIN']                  = float(request.json['ADSB__ALT_DEG_MIN'])
        self.indi_allsky_config['ADSB']['LABEL_ENABLE']                 = bool(request.json['ADSB__LABEL_ENABLE'])
        self.indi_allsky_config['ADSB']['LABEL_LIMIT']                  = int(request.json['ADSB__LABEL_LIMIT'])
        self.indi_allsky_config['ADSB']['AIRCRAFT_LABEL_TEMPLATE']      = str(request.json['ADSB__AIRCRAFT_LABEL_TEMPLATE'])
        self.indi_allsky_config['ADSB']['IMAGE_LABEL_TEMPLATE_PREFIX']  = str(request.json['ADSB__IMAGE_LABEL_TEMPLATE_PREFIX'])
        self.indi_allsky_config['SATELLITE_TRACK']['ENABLE']            = bool(request.json['SATELLITE_TRACK__ENABLE'])
        self.indi_allsky_config['SATELLITE_TRACK']['DAYTIME_TRACK']     = bool(request.json['SATELLITE_TRACK__DAYTIME_TRACK'])
        self.indi_allsky_config['SATELLITE_TRACK']['ALT_DEG_MIN']       = float(request.json['SATELLITE_TRACK__ALT_DEG_MIN'])
        self.indi_allsky_config['SATELLITE_TRACK']['LABEL_ENABLE']      = bool(request.json['SATELLITE_TRACK__LABEL_ENABLE'])
        self.indi_allsky_config['SATELLITE_TRACK']['LABEL_LIMIT']       = int(request.json['SATELLITE_TRACK__LABEL_LIMIT'])
        self.indi_allsky_config['SATELLITE_TRACK']['SAT_LABEL_TEMPLATE'] = str(request.json['SATELLITE_TRACK__SAT_LABEL_TEMPLATE'])
        self.indi_allsky_config['SATELLITE_TRACK']['IMAGE_LABEL_TEMPLATE_PREFIX']  = str(request.json['SATELLITE_TRACK__IMAGE_LABEL_TEMPLATE_PREFIX'])

        self.indi_allsky_config['FILETRANSFER']['LIBCURL_OPTIONS']      = json.loads(str(request.json['FILETRANSFER__LIBCURL_OPTIONS']))
        self.indi_allsky_config['INDI_CONFIG_DEFAULTS']                 = json.loads(str(request.json['INDI_CONFIG_DEFAULTS']))
        self.indi_allsky_config['INDI_CONFIG_DAY']                      = json.loads(str(request.json['INDI_CONFIG_DAY']))
        self.indi_allsky_config['ENCRYPT_PASSWORDS']                    = bool(request.json['ENCRYPT_PASSWORDS'])


        ### never disable
        #self.indi_allsky_config['THUMBNAILS']['IMAGES_AUTO']            = True


        ### Not a config option
        reload_on_save                                                  = bool(request.json['RELOAD_ON_SAVE'])
        config_note                                                     = str(request.json['CONFIG_NOTE'])


        # ADU_ROI
        adu_roi_x1 = int(request.json['ADU_ROI_X1'])
        adu_roi_y1 = int(request.json['ADU_ROI_Y1'])
        adu_roi_x2 = int(request.json['ADU_ROI_X2'])
        adu_roi_y2 = int(request.json['ADU_ROI_Y2'])

        # the x2 and y2 values must be positive integers in order to be enabled and valid
        if adu_roi_x2 and adu_roi_y2:
            self.indi_allsky_config['ADU_ROI'] = [adu_roi_x1, adu_roi_y1, adu_roi_x2, adu_roi_y2]
        else:
            self.indi_allsky_config['ADU_ROI'] = []


        # SQM_ROI
        sqm_roi_x1 = int(request.json['SQM_ROI_X1'])
        sqm_roi_y1 = int(request.json['SQM_ROI_Y1'])
        sqm_roi_x2 = int(request.json['SQM_ROI_X2'])
        sqm_roi_y2 = int(request.json['SQM_ROI_Y2'])

        # the x2 and y2 values must be positive integers in order to be enabled and valid
        if sqm_roi_x2 and sqm_roi_y2:
            self.indi_allsky_config['SQM_ROI'] = [sqm_roi_x1, sqm_roi_y1, sqm_roi_x2, sqm_roi_y2]
        else:
            self.indi_allsky_config['SQM_ROI'] = []


        # IMAGE_CROP_ROI
        image_crop_roi_x1 = int(request.json['IMAGE_CROP_ROI_X1'])
        image_crop_roi_y1 = int(request.json['IMAGE_CROP_ROI_Y1'])
        image_crop_roi_x2 = int(request.json['IMAGE_CROP_ROI_X2'])
        image_crop_roi_y2 = int(request.json['IMAGE_CROP_ROI_Y2'])

        # the x2 and y2 values must be positive integers in order to be enabled and valid
        if image_crop_roi_x2 and image_crop_roi_y2:
            self.indi_allsky_config['IMAGE_CROP_ROI'] = [image_crop_roi_x1, image_crop_roi_y1, image_crop_roi_x2, image_crop_roi_y2]
        else:
            self.indi_allsky_config['IMAGE_CROP_ROI'] = []



        # TEXT_PROPERTIES FONT_COLOR
        font_color_str = str(request.json['TEXT_PROPERTIES__FONT_COLOR'])
        self.indi_allsky_config['TEXT_PROPERTIES']['FONT_COLOR'] = [int(x) for x in font_color_str.split(',')]

        # CARDINAL_DIRS FONT_COLOR
        cardinal_dirs_color_str = str(request.json['CARDINAL_DIRS__FONT_COLOR'])
        self.indi_allsky_config['CARDINAL_DIRS']['FONT_COLOR'] = [int(x) for x in cardinal_dirs_color_str.split(',')]

        # ORB_PROPERTIES SUN_COLOR
        sun_color_str = str(request.json['ORB_PROPERTIES__SUN_COLOR'])
        self.indi_allsky_config['ORB_PROPERTIES']['SUN_COLOR'] = [int(x) for x in sun_color_str.split(',')]

        # ORB_PROPERTIES MOON_COLOR
        moon_color_str = str(request.json['ORB_PROPERTIES__MOON_COLOR'])
        self.indi_allsky_config['ORB_PROPERTIES']['MOON_COLOR'] = [int(x) for x in moon_color_str.split(',')]

        # IMAGE_BORDER COLOR
        image_border__color_str = str(request.json['IMAGE_BORDER__COLOR'])
        self.indi_allsky_config['IMAGE_BORDER']['COLOR'] = [int(x) for x in image_border__color_str.split(',')]

        # LIGHTGRAPH COLORS
        lightgraph_overlay__day_color_str = str(request.json['LIGHTGRAPH_OVERLAY__DAY_COLOR'])
        self.indi_allsky_config['LIGHTGRAPH_OVERLAY']['DAY_COLOR'] = [int(x) for x in lightgraph_overlay__day_color_str.split(',')]

        lightgraph_overlay__dusk_color_str = str(request.json['LIGHTGRAPH_OVERLAY__DUSK_COLOR'])
        self.indi_allsky_config['LIGHTGRAPH_OVERLAY']['DUSK_COLOR'] = [int(x) for x in lightgraph_overlay__dusk_color_str.split(',')]

        lightgraph_overlay__night_color_str = str(request.json['LIGHTGRAPH_OVERLAY__NIGHT_COLOR'])
        self.indi_allsky_config['LIGHTGRAPH_OVERLAY']['NIGHT_COLOR'] = [int(x) for x in lightgraph_overlay__night_color_str.split(',')]

        lightgraph_overlay__moonmode_color_str = str(request.json['LIGHTGRAPH_OVERLAY__MOONMODE_COLOR'])
        self.indi_allsky_config['LIGHTGRAPH_OVERLAY']['MOONMODE_COLOR'] = [int(x) for x in lightgraph_overlay__moonmode_color_str.split(',')]

        lightgraph_overlay__hour_color_str = str(request.json['LIGHTGRAPH_OVERLAY__HOUR_COLOR'])
        self.indi_allsky_config['LIGHTGRAPH_OVERLAY']['HOUR_COLOR'] = [int(x) for x in lightgraph_overlay__hour_color_str.split(',')]

        lightgraph_overlay__border_color_str = str(request.json['LIGHTGRAPH_OVERLAY__BORDER_COLOR'])
        self.indi_allsky_config['LIGHTGRAPH_OVERLAY']['BORDER_COLOR'] = [int(x) for x in lightgraph_overlay__border_color_str.split(',')]

        lightgraph_overlay__now_color_str = str(request.json['LIGHTGRAPH_OVERLAY__NOW_COLOR'])
        self.indi_allsky_config['LIGHTGRAPH_OVERLAY']['NOW_COLOR'] = [int(x) for x in lightgraph_overlay__now_color_str.split(',')]

        lightgraph_overlay__font_color_str = str(request.json['LIGHTGRAPH_OVERLAY__FONT_COLOR'])
        self.indi_allsky_config['LIGHTGRAPH_OVERLAY']['FONT_COLOR'] = [int(x) for x in lightgraph_overlay__font_color_str.split(',')]


        # Youtube tags
        youtube__tags_str = str(request.json['YOUTUBE__TAGS_STR'])
        tags_set = set()
        for tag in youtube__tags_str.split(','):
            tag_s = tag.strip()

            if tag_s:
                tags_set.add(tag_s)

        self.indi_allsky_config['YOUTUBE']['TAGS'] = list(tags_set)


        # save new config
        if not app.config['LOGIN_DISABLED']:
            username = current_user.username
        else:
            username = 'system'


        try:
            self._indi_allsky_config_obj.save(username, config_note)
            app.logger.info('Saved new config')
        except ConfigSaveException as e:
            error_data = {
                'form_global' : [str(e)],
            }
            return jsonify(error_data), 400


        if reload_on_save:
            self._miscDb.setState('STATUS', constants.STATUS_RELOADING)

            task_reload = IndiAllSkyDbTaskQueueTable(
                queue=TaskQueueQueue.MAIN,
                state=TaskQueueState.MANUAL,
                priority=100,
                data={'action' : 'reload'},
            )

            db.session.add(task_reload)
            db.session.commit()

            message = {
                'success-message' : 'Saved new config,  Reloading indi-allsky service.',
            }
        else:
            message = {
                'success-message' : 'Saved new config',
            }


        return jsonify(message)


class AjaxSetTimeView(BaseView):
    methods = ['POST']
    decorators = [login_required]

    def dispatch_request(self):
        form_settime = IndiAllskySetDateTimeForm(data=request.json)


        if not app.config['LOGIN_DISABLED']:
            if not current_user.is_admin:
                form_errors = form_settime.errors  # this must be a property
                form_errors['form_settime_global'] = ['You do not have permission to make configuration changes']
                return jsonify(form_errors), 400


        if not form_settime.validate():
            form_errors = form_settime.errors  # this must be a property
            form_errors['form_settime_global'] = ['Please fix the errors above']
            return jsonify(form_errors), 400


        new_datetime_str = str(request.json['NEW_DATETIME'])

        new_datetime = datetime.strptime(new_datetime_str, '%Y-%m-%dT%H:%M:%S').astimezone()

        new_datetime_utc = new_datetime.astimezone(tz=timezone.utc)


        #systemtime_utc = datetime.now(tz=timezone.utc)

        #time_offset = systemtime_utc.timestamp() - new_datetime_utc.timestamp()
        #app.logger.info('Time offset: %ds', int(time_offset))

        #task_settime = IndiAllSkyDbTaskQueueTable(
        #    queue=TaskQueueQueue.MAIN,
        #    state=TaskQueueState.MANUAL,
        #    priority=100,
        #    data={
        #        'action'      : 'settime',
        #        'time_offset' : time_offset,
        #    },
        #)

        #db.session.add(task_settime)
        #db.session.commit()

        # form passed validation


        try:
            self.setTimeSystemd(new_datetime_utc)
        except dbus.exceptions.DBusException as e:
            app.logger.error('DBus Error: %s', str(e))
            errors = {
                'form_settime_global' : ['DBus Error: {0:s}'.format(str(e))],
            }
            return jsonify(errors), 400


        message = {
            'success-message' : 'System time updated.',
        }

        return jsonify(message)


    def setTimeSystemd(self, new_datetime_utc):
        app.logger.warning('Setting system time to %s (UTC)', new_datetime_utc)

        epoch = new_datetime_utc.timestamp() + 5  # add 5 due to sleep below
        epoch_msec = epoch * 1000000

        system_bus = dbus.SystemBus()
        timedate1 = system_bus.get_object('org.freedesktop.timedate1', '/org/freedesktop/timedate1')
        manager = dbus.Interface(timedate1, 'org.freedesktop.timedate1')

        app.logger.warning('Disabling NTP time sync')
        manager.SetNTP(False, False)  # disable time sync
        time.sleep(5.0)  # give enough time for time sync to diable

        r2 = manager.SetTime(epoch_msec, False, False)

        return r2


class AjaxSetTimezoneView(BaseView):
    methods = ['POST']
    decorators = [login_required]

    def dispatch_request(self):
        form_timezone = IndiAllskySetTimezoneForm(data=request.json)


        if not app.config['LOGIN_DISABLED']:
            if not current_user.is_admin:
                form_errors = form_timezone.errors  # this must be a property
                form_errors['form_timezone_global'] = ['You do not have permission to make configuration changes']
                return jsonify(form_errors), 400


        if not form_timezone.validate():
            form_errors = form_timezone.errors  # this must be a property
            form_errors['form_timezone_global'] = ['Please fix the errors above']
            return jsonify(form_errors), 400


        new_timezone_str = str(request.json['NEW_TIMEZONE'])


        try:
            self.setTimezoneSystemd(new_timezone_str)
        except dbus.exceptions.DBusException as e:
            app.logger.error('DBus Error: %s', str(e))
            errors = {
                'form_timezone_global' : ['DBus Error: {0:s}'.format(str(e))],
            }
            return jsonify(errors), 400


        message = {
            'success-message' : 'System timezone updated.',
        }

        return jsonify(message)


    def setTimezoneSystemd(self, new_timezone_str):
        app.logger.warning('Setting system timezone to %s', new_timezone_str)


        system_bus = dbus.SystemBus()
        timedate1 = system_bus.get_object('org.freedesktop.timedate1', '/org/freedesktop/timedate1')
        manager = dbus.Interface(timedate1, 'org.freedesktop.timedate1')

        r2 = manager.SetTimezone(new_timezone_str, False)

        return r2


class ImageViewerView(FormView):
    page_title = 'Image Viewer'
    decorators = [login_optional_media]

    def get_context(self):
        context = super(ImageViewerView, self).get_context()

        form_data = {
            'CAMERA_ID'    : self.camera.id,
            'YEAR_SELECT'  : None,
            'MONTH_SELECT' : None,
            'DAY_SELECT'   : None,
            'HOUR_SELECT'  : None,
            'FILTER_DETECTIONS' : None,
        }


        local = True  # default to local assets
        if self.web_nonlocal_images:
            if self.web_local_images_admin and self.verify_admin_network():
                pass
            else:
                local = False


        context['panorama__enable'] = int(self.indi_allsky_config.get('FISH2PANO', {}).get('ENABLE', 0))

        context['form_viewer'] = IndiAllskyImageViewerPreload(
            data=form_data,
            camera_id=self.camera.id,
            s3_prefix=self.s3_prefix,
            local=local,
        )

        context['form_image_exclude'] = IndiAllskyImageExcludeForm()

        return context


class AjaxImageViewerView(BaseView):
    methods = ['POST']
    decorators = [login_optional_media]

    def __init__(self, **kwargs):
        super(AjaxImageViewerView, self).__init__(**kwargs)


    def dispatch_request(self):
        camera_id  = int(request.json['CAMERA_ID'])
        form_year  = int(request.json.get('YEAR_SELECT', 0))
        form_month = int(request.json.get('MONTH_SELECT', 0))
        form_day   = int(request.json.get('DAY_SELECT', 0))
        form_hour  = int(request.json.get('HOUR_SELECT', -1))  # 0 is a real hour
        form_filter_detections = bool(request.json.get('FILTER_DETECTIONS'))

        self.cameraSetup(camera_id=camera_id)

        local = True  # default to local assets
        if self.web_nonlocal_images:
            if self.web_local_images_admin and self.verify_admin_network():
                pass
            else:
                local = False


        if form_filter_detections:
            # filter images that have a detection
            form_viewer = IndiAllskyImageViewer(
                data=request.json,
                camera_id=camera_id,
                detections_count=1,
                s3_prefix=self.s3_prefix,
                local=local,
            )
        else:
            form_viewer = IndiAllskyImageViewer(
                data=request.json,
                camera_id=camera_id,
                detections_count=0,
                s3_prefix=self.s3_prefix,
                local=local,
            )


        json_data = {}


        if form_hour >= 0:
            form_datetime = datetime.strptime('{0} {1} {2} {3}'.format(form_year, form_month, form_day, form_hour), '%Y %m %d %H')

            year = form_datetime.year
            month = form_datetime.month
            day = form_datetime.day
            hour = form_datetime.hour

            json_data['IMAGE_DATA'] = form_viewer.getImages(year, month, day, hour)

        elif form_day:
            form_datetime = datetime.strptime('{0} {1} {2}'.format(form_year, form_month, form_day), '%Y %m %d')

            year = form_datetime.year
            month = form_datetime.month
            day = form_datetime.day

            json_data['HOUR_SELECT'] = form_viewer.getHours(year, month, day)
            hour = json_data['HOUR_SELECT'][0][0]

            json_data['IMAGE_DATA'] = form_viewer.getImages(year, month, day, hour)

        elif form_month:
            form_datetime = datetime.strptime('{0} {1}'.format(form_year, form_month), '%Y %m')

            year = form_datetime.year
            month = form_datetime.month

            json_data['DAY_SELECT'] = form_viewer.getDays(year, month)
            day = json_data['DAY_SELECT'][0][0]

            json_data['HOUR_SELECT'] = form_viewer.getHours(year, month, day)
            hour = json_data['HOUR_SELECT'][0][0]

            json_data['IMAGE_DATA'] = form_viewer.getImages(year, month, day, hour)

        elif form_year:
            form_datetime = datetime.strptime('{0}'.format(form_year), '%Y')

            year = form_datetime.year

            json_data['MONTH_SELECT'] = form_viewer.getMonths(year)
            month = json_data['MONTH_SELECT'][0][0]

            json_data['DAY_SELECT'] = form_viewer.getDays(year, month)
            day = json_data['DAY_SELECT'][0][0]

            json_data['HOUR_SELECT'] = form_viewer.getHours(year, month, day)
            hour = json_data['HOUR_SELECT'][0][0]

            json_data['IMAGE_DATA'] = form_viewer.getImages(year, month, day, hour)

        else:
            # this happens when filtering images on detections
            json_data['YEAR_SELECT'] = form_viewer.getYears()

            if not json_data['YEAR_SELECT']:
                # No images returned
                json_data['YEAR_SELECT'] = (('', None),)
                json_data['MONTH_SELECT'] = (('', None),)
                json_data['DAY_SELECT'] = (('', None),)
                json_data['HOUR_SELECT'] = (('', None),)
                json_data['IMG_SELECT'] = (('', None),)

                return json_data


            year = json_data['YEAR_SELECT'][0][0]

            json_data['MONTH_SELECT'] = form_viewer.getMonths(year)
            month = json_data['MONTH_SELECT'][0][0]

            json_data['DAY_SELECT'] = form_viewer.getDays(year, month)
            day = json_data['DAY_SELECT'][0][0]

            json_data['HOUR_SELECT'] = form_viewer.getHours(year, month, day)
            hour = json_data['HOUR_SELECT'][0][0]

            json_data['IMAGE_DATA'] = form_viewer.getImages(year, month, day, hour)


        return jsonify(json_data)


class FitsImageViewerView(FormView):
    page_title = 'FITS Image Viewer'
    decorators = [login_required]

    def get_context(self):
        context = super(FitsImageViewerView, self).get_context()

        form_data = {
            'CAMERA_ID'    : self.camera.id,
            'YEAR_SELECT'  : None,
            'MONTH_SELECT' : None,
            'DAY_SELECT'   : None,
            'HOUR_SELECT'  : None,
        }


        context['form_fits_viewer'] = IndiAllskyFitsImageViewerPreload(
            data=form_data,
            camera_id=self.camera.id,
        )

        return context


class AjaxFitsImageViewerView(BaseView):
    methods = ['POST']
    decorators = [login_required]

    def __init__(self, **kwargs):
        super(AjaxFitsImageViewerView, self).__init__(**kwargs)


    def dispatch_request(self):
        camera_id  = int(request.json['CAMERA_ID'])
        form_year  = int(request.json.get('YEAR_SELECT', 0))
        form_month = int(request.json.get('MONTH_SELECT', 0))
        form_day   = int(request.json.get('DAY_SELECT', 0))
        form_hour  = int(request.json.get('HOUR_SELECT', -1))  # 0 is a real hour

        self.cameraSetup(camera_id=camera_id)


        form_viewer = IndiAllskyFitsImageViewer(
            data=request.json,
            camera_id=camera_id,
        )


        json_data = {}


        if form_hour >= 0:
            form_datetime = datetime.strptime('{0} {1} {2} {3}'.format(form_year, form_month, form_day, form_hour), '%Y %m %d %H')

            year = form_datetime.year
            month = form_datetime.month
            day = form_datetime.day
            hour = form_datetime.hour

            json_data['IMAGE_DATA'] = form_viewer.getImages(year, month, day, hour)

        elif form_day:
            form_datetime = datetime.strptime('{0} {1} {2}'.format(form_year, form_month, form_day), '%Y %m %d')

            year = form_datetime.year
            month = form_datetime.month
            day = form_datetime.day

            json_data['HOUR_SELECT'] = form_viewer.getHours(year, month, day)
            hour = json_data['HOUR_SELECT'][0][0]

            json_data['IMAGE_DATA'] = form_viewer.getImages(year, month, day, hour)

        elif form_month:
            form_datetime = datetime.strptime('{0} {1}'.format(form_year, form_month), '%Y %m')

            year = form_datetime.year
            month = form_datetime.month

            json_data['DAY_SELECT'] = form_viewer.getDays(year, month)
            day = json_data['DAY_SELECT'][0][0]

            json_data['HOUR_SELECT'] = form_viewer.getHours(year, month, day)
            hour = json_data['HOUR_SELECT'][0][0]

            json_data['IMAGE_DATA'] = form_viewer.getImages(year, month, day, hour)

        elif form_year:
            form_datetime = datetime.strptime('{0}'.format(form_year), '%Y')

            year = form_datetime.year

            json_data['MONTH_SELECT'] = form_viewer.getMonths(year)
            month = json_data['MONTH_SELECT'][0][0]

            json_data['DAY_SELECT'] = form_viewer.getDays(year, month)
            day = json_data['DAY_SELECT'][0][0]

            json_data['HOUR_SELECT'] = form_viewer.getHours(year, month, day)
            hour = json_data['HOUR_SELECT'][0][0]

            json_data['IMAGE_DATA'] = form_viewer.getImages(year, month, day, hour)

        else:
            # this happens when filtering images on detections
            json_data['YEAR_SELECT'] = form_viewer.getYears()

            if not json_data['YEAR_SELECT']:
                # No images returned
                json_data['YEAR_SELECT'] = (('', None),)
                json_data['MONTH_SELECT'] = (('', None),)
                json_data['DAY_SELECT'] = (('', None),)
                json_data['HOUR_SELECT'] = (('', None),)
                json_data['IMG_SELECT'] = (('', None),)

                return json_data


            year = json_data['YEAR_SELECT'][0][0]

            json_data['MONTH_SELECT'] = form_viewer.getMonths(year)
            month = json_data['MONTH_SELECT'][0][0]

            json_data['DAY_SELECT'] = form_viewer.getDays(year, month)
            day = json_data['DAY_SELECT'][0][0]

            json_data['HOUR_SELECT'] = form_viewer.getHours(year, month, day)
            hour = json_data['HOUR_SELECT'][0][0]

            json_data['IMAGE_DATA'] = form_viewer.getImages(year, month, day, hour)


        return jsonify(json_data)


class Fits2JpegView(BaseView):
    methods = ['GET']  # this allows the output to be cached by the browser
    decorators = [login_required]

    def __init__(self, **kwargs):
        super(Fits2JpegView, self).__init__(**kwargs)


    def dispatch_request(self):
        import cv2
        from astropy.io import fits
        #from PIL import Image
        from multiprocessing import Array

        fits_id = int(request.args['id'])


        table = IndiAllSkyDbFitsImageTable

        try:
            fits_entry = table.query\
                .filter(table.id == fits_id)\
                .one()
        except NoResultFound:
            return 'FITS not found', 404


        self.cameraSetup(camera_id=fits_entry.camera_id)


        filename_p = Path(fits_entry.getFilesystemPath())


        p_config = self.indi_allsky_config.copy()


        hdulist = fits.open(filename_p)

        exposure = float(hdulist[0].header.get('EXPTIME', 0))
        gain = float(hdulist[0].header.get('GAIN', 0))
        gain_av = Array('f', [gain])
        position_av = Array('f', [self.camera.latitude, self.camera.longitude, self.camera.elevation])
        binning = int(hdulist[0].header.get('XBINNING', 1))
        binning_av = Array('i', [binning])
        sensors_temp_av = Array('f', [float(hdulist[0].header.get('CCD-TEMP', 0))])
        sensors_user_av = Array('f', [float(hdulist[0].header.get('CCD-TEMP', 0)), 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0])
        night_av = Array('i', [1, 0])  # using night values for processing
        astro_av = Array('f', [0.0, 0.0, 0.0])

        hdulist.close()

        image_processor = ImageProcessor(
            p_config,
            position_av,
            gain_av,
            binning_av,
            sensors_temp_av,
            sensors_user_av,
            night_av,
            astro_av,
        )


        processing_start = time.time()


        # use mtime for date
        image_date = datetime.fromtimestamp(filename_p.stat().st_mtime)


        image_processor.update_astrometric_data(image_date)


        image_processor.add(
            filename_p,
            exposure,
            gain,
            binning,
            image_date,
            0.0,
            fits_entry.camera,
        )


        image_processor.debayer()  # populates self.opencv_data

        image_processor.stack()  # populates self.image

        image_processor.convert_16bit_to_8bit()


        # verticle flip
        if p_config.get('IMAGE_FLIP_V'):
            image_processor.flip_v()

        # horizontal flip
        if p_config.get('IMAGE_FLIP_H'):
            image_processor.flip_h()


        image_processor.colorize()


        processing_elapsed_s = time.time() - processing_start
        app.logger.info('Image processed in %0.4f s', processing_elapsed_s)


        image = image_processor.image


        ### OpenCV
        _, image_a = cv2.imencode('.jpg', image, [cv2.IMWRITE_JPEG_QUALITY, p_config['IMAGE_FILE_COMPRESSION']['jpg']])
        image_buffer = io.BytesIO(image_a.tobytes())


        ### pillow
        #image_buffer = io.BytesIO()
        #img = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
        #img.save(image_buffer, format='JPEG', quality=p_config['IMAGE_FILE_COMPRESSION']['jpg'])


        return Response(image_buffer.getvalue(), mimetype='image/jpeg')


class GalleryViewerView(FormView):
    page_title = 'Gallery'
    decorators = [login_optional_media]

    def get_context(self):
        context = super(GalleryViewerView, self).get_context()

        form_data = {
            'CAMERA_ID'    : self.camera.id,
            'YEAR_SELECT'  : None,
            'MONTH_SELECT' : None,
            'DAY_SELECT'   : None,
            'HOUR_SELECT'  : None,
            'FILTER_DETECTIONS' : None,
        }


        local = True  # default to local assets
        if self.web_nonlocal_images:
            if self.web_local_images_admin and self.verify_admin_network():
                pass
            else:
                local = False


        context['form_viewer'] = IndiAllskyGalleryViewerPreload(
            data=form_data,
            camera_id=self.camera.id,
            s3_prefix=self.s3_prefix,
            local=local,
        )

        return context


class AjaxGalleryViewerView(BaseView):
    methods = ['POST']
    decorators = [login_optional_media]

    def __init__(self, **kwargs):
        super(AjaxGalleryViewerView, self).__init__(**kwargs)


    def dispatch_request(self):
        camera_id  = int(request.json['CAMERA_ID'])
        form_year  = int(request.json.get('YEAR_SELECT', 0))
        form_month = int(request.json.get('MONTH_SELECT', 0))
        form_day   = int(request.json.get('DAY_SELECT', 0))
        form_hour  = int(request.json.get('HOUR_SELECT', -1))  # 0 is a real hour
        form_filter_detections = bool(request.json.get('FILTER_DETECTIONS'))

        self.cameraSetup(camera_id=camera_id)

        local = True  # default to local assets
        if self.web_nonlocal_images:
            if self.web_local_images_admin and self.verify_admin_network():
                pass
            else:
                local = False


        if form_filter_detections:
            # filter images that have a detection
            form_viewer = IndiAllskyGalleryViewer(
                data=request.json,
                camera_id=camera_id,
                detections_count=1,
                s3_prefix=self.s3_prefix,
                local=local,
            )
        else:
            form_viewer = IndiAllskyGalleryViewer(
                data=request.json,
                camera_id=camera_id,
                detections_count=0,
                s3_prefix=self.s3_prefix,
                local=local,
            )


        json_data = {}


        if form_hour >= 0:
            form_datetime = datetime.strptime('{0} {1} {2} {3}'.format(form_year, form_month, form_day, form_hour), '%Y %m %d %H')

            year = form_datetime.year
            month = form_datetime.month
            day = form_datetime.day
            hour = form_datetime.hour

            json_data['IMAGE_DATA'] = form_viewer.getImages(year, month, day, hour)

        elif form_day:
            form_datetime = datetime.strptime('{0} {1} {2}'.format(form_year, form_month, form_day), '%Y %m %d')

            year = form_datetime.year
            month = form_datetime.month
            day = form_datetime.day

            json_data['HOUR_SELECT'] = form_viewer.getHours(year, month, day)
            hour = json_data['HOUR_SELECT'][0][0]

            json_data['IMAGE_DATA'] = form_viewer.getImages(year, month, day, hour)

        elif form_month:
            form_datetime = datetime.strptime('{0} {1}'.format(form_year, form_month), '%Y %m')

            year = form_datetime.year
            month = form_datetime.month

            json_data['DAY_SELECT'] = form_viewer.getDays(year, month)
            day = json_data['DAY_SELECT'][0][0]

            json_data['HOUR_SELECT'] = form_viewer.getHours(year, month, day)
            hour = json_data['HOUR_SELECT'][0][0]

            json_data['IMAGE_DATA'] = form_viewer.getImages(year, month, day, hour)

        elif form_year:
            form_datetime = datetime.strptime('{0}'.format(form_year), '%Y')

            year = form_datetime.year

            json_data['MONTH_SELECT'] = form_viewer.getMonths(year)
            month = json_data['MONTH_SELECT'][0][0]

            json_data['DAY_SELECT'] = form_viewer.getDays(year, month)
            day = json_data['DAY_SELECT'][0][0]

            json_data['HOUR_SELECT'] = form_viewer.getHours(year, month, day)
            hour = json_data['HOUR_SELECT'][0][0]

            json_data['IMAGE_DATA'] = form_viewer.getImages(year, month, day, hour)

        else:
            # this happens when filtering images on detections
            json_data['YEAR_SELECT'] = form_viewer.getYears()

            if not json_data['YEAR_SELECT']:
                # No images returned
                json_data['YEAR_SELECT'] = (('', None),)
                json_data['MONTH_SELECT'] = (('', None),)
                json_data['DAY_SELECT'] = (('', None),)
                json_data['HOUR_SELECT'] = (('', None),)
                json_data['IMG_SELECT'] = (('', None),)

                return json_data


            year = json_data['YEAR_SELECT'][0][0]

            json_data['MONTH_SELECT'] = form_viewer.getMonths(year)
            month = json_data['MONTH_SELECT'][0][0]

            json_data['DAY_SELECT'] = form_viewer.getDays(year, month)
            day = json_data['DAY_SELECT'][0][0]

            json_data['HOUR_SELECT'] = form_viewer.getHours(year, month, day)
            hour = json_data['HOUR_SELECT'][0][0]

            json_data['IMAGE_DATA'] = form_viewer.getImages(year, month, day, hour)


        return jsonify(json_data)


class VideoViewerView(FormView):
    page_title = 'Timelapse Viewer'
    decorators = [login_optional_media]

    def get_context(self):
        context = super(VideoViewerView, self).get_context()

        context['youtube__enable'] = int(self.indi_allsky_config.get('YOUTUBE', {}).get('ENABLE', 0))

        form_data = {
            'CAMERA_ID'    : self.camera.id,
            'YEAR_SELECT'  : None,
            'MONTH_SELECT' : None,
        }


        local = True  # default to local assets
        if self.web_nonlocal_images:
            if self.web_local_images_admin and self.verify_admin_network():
                pass
            else:
                local = False


        context['form_video_viewer'] = IndiAllskyVideoViewerPreload(
            data=form_data,
            camera_id=self.camera.id,
            s3_prefix=self.s3_prefix,
            local=local,
        )

        return context


class AjaxVideoViewerView(BaseView):
    methods = ['POST']
    decorators = [login_optional_media]

    def __init__(self, **kwargs):
        super(AjaxVideoViewerView, self).__init__(**kwargs)


    def dispatch_request(self):
        camera_id      = int(request.json['CAMERA_ID'])
        form_year      = int(request.json.get('YEAR_SELECT', 0))
        form_month     = int(request.json.get('MONTH_SELECT', 0))
        form_timeofday = str(request.json.get('TIMEOFDAY_SELECT', ''))


        self.cameraSetup(camera_id=camera_id)


        local = True  # default to local assets
        if self.web_nonlocal_images:
            if self.web_local_images_admin and self.verify_admin_network():
                pass
            else:
                local = False


        form_video_viewer = IndiAllskyVideoViewer(
            data=request.json,
            camera_id=camera_id,
            s3_prefix=self.s3_prefix,
            local=local,
        )


        json_data = {}

        if form_month:
            form_datetime = datetime.strptime('{0} {1}'.format(form_year, form_month), '%Y %m')

            year = form_datetime.year
            month = form_datetime.month

            json_data['video_list'] = form_video_viewer.getVideos(year, month, form_timeofday)

        elif form_year:
            form_datetime = datetime.strptime('{0}'.format(form_year), '%Y')

            year = form_datetime.year

            json_data['MONTH_SELECT'] = form_video_viewer.getMonths(year)
            month = json_data['MONTH_SELECT'][0][0]

            json_data['video_list'] = form_video_viewer.getVideos(year, month, form_timeofday)
        else:
            # No entries in DB
            json_data['MONTH_SELECT'] = (('', 'None'),)
            json_data['video_list'] = tuple()


        return jsonify(json_data)


class MiniVideoViewerView(FormView):
    page_title = 'Mini-Timelapse Viewer'
    decorators = [login_optional_media]

    def get_context(self):
        context = super(MiniVideoViewerView, self).get_context()

        context['youtube__enable'] = int(self.indi_allsky_config.get('YOUTUBE', {}).get('ENABLE', 0))

        form_data = {
            'CAMERA_ID'    : self.camera.id,
            'YEAR_SELECT'  : None,
            'MONTH_SELECT' : None,
        }


        local = True  # default to local assets
        if self.web_nonlocal_images:
            if self.web_local_images_admin and self.verify_admin_network():
                pass
            else:
                local = False


        context['form_mini_video_viewer'] = IndiAllskyMiniVideoViewerPreload(
            data=form_data,
            camera_id=self.camera.id,
            s3_prefix=self.s3_prefix,
            local=local,
        )

        return context


class AjaxMiniVideoViewerView(BaseView):
    methods = ['POST']
    decorators = [login_optional_media]

    def __init__(self, **kwargs):
        super(AjaxMiniVideoViewerView, self).__init__(**kwargs)


    def dispatch_request(self):
        camera_id      = int(request.json['CAMERA_ID'])
        form_year      = int(request.json.get('YEAR_SELECT', 0))
        form_month     = int(request.json.get('MONTH_SELECT', 0))

        self.cameraSetup(camera_id=camera_id)

        local = True  # default to local assets
        if self.web_nonlocal_images:
            if self.web_local_images_admin and self.verify_admin_network():
                pass
            else:
                local = False


        form_mini_video_viewer = IndiAllskyMiniVideoViewer(
            data=request.json,
            camera_id=camera_id,
            s3_prefix=self.s3_prefix,
            local=local,
        )


        json_data = {}

        if form_month:
            form_datetime = datetime.strptime('{0} {1}'.format(form_year, form_month), '%Y %m')

            year = form_datetime.year
            month = form_datetime.month

            json_data['video_list'] = form_mini_video_viewer.getVideos(year, month)

        elif form_year:
            form_datetime = datetime.strptime('{0}'.format(form_year), '%Y')

            year = form_datetime.year

            json_data['MONTH_SELECT'] = form_mini_video_viewer.getMonths(year)
            month = json_data['MONTH_SELECT'][0][0]

            json_data['video_list'] = form_mini_video_viewer.getVideos(year, month)
        else:
            # No entries in DB
            json_data['MONTH_SELECT'] = (('', 'None'),)
            json_data['video_list'] = tuple()

        return jsonify(json_data)


class ModernAdminView(TemplateView):
    # Future entry point for the modern admin UI; keep it isolated from classic admin.
    page_title = 'Modern Admin'
    decorators = [login_required]

    def get_context(self):
        context = super(ModernAdminView, self).get_context()
        session['admin_mode'] = 'modern'

        camera_name = self.camera.friendlyName or self.camera.name or 'Unknown camera'
        camera_model = self.camera.driver or 'Model unavailable'

        context['modern_admin_mode'] = session.get('admin_mode', 'modern')
        context['modern_admin_nav'] = self.get_modern_admin_nav()
        context.update(self.get_modern_admin_topbar_context())
        context['modern_admin_camera_name'] = str(camera_name)
        context['modern_admin_camera_model'] = str(camera_model)
        context['modern_admin_capture_status'] = self.get_capture_status_label()
        context.update(self.get_storage_context())
        context['latest_image_url'] = None
        context['latest_image_updated'] = 'No recent image available'
        context['latest_image_age'] = 'No recent image'
        context['latest_image_status'] = 'Waiting for latest frame'

        if not self.latest_image_entry:
            return context

        # Reuse the existing latest image DB entry and URL rules used by classic image views.
        local = True
        if self.web_nonlocal_images:
            if self.web_local_images_admin and self.verify_admin_network():
                pass
            else:
                local = False
                if not self.latest_image_entry.remote_url and not self.latest_image_entry.s3_key:
                    return context

        try:
            context['latest_image_url'] = str(self.latest_image_entry.getUrl(s3_prefix=self.s3_prefix, local=local))
        except ValueError as e:
            app.logger.error('Error determining modern admin latest image URL: %s', str(e))
            return context

        last_update_age = self.format_image_age(self.latest_image_entry.createDate)

        context['latest_image_age'] = last_update_age
        context['latest_image_updated'] = 'Last frame {0:s}'.format(last_update_age)
        context['latest_image_status'] = self.latest_image_entry.createDate.strftime('%Y-%m-%d %H:%M:%S')

        return context


    def get_modern_admin_nav(self):
        # Navigation shell for the future modern admin UI; unfinished sections render read-only placeholders.
        nav_items = (
            ('Dashboard', 'indi_allsky.modern_admin_view'),
            ('Cameras', 'indi_allsky.modern_admin_cameras_view'),
            ('Storage', 'indi_allsky.modern_admin_storage_view'),
            ('Uploads', 'indi_allsky.modern_admin_uploads_view'),
            ('Observatory', 'indi_allsky.modern_admin_observatory_view'),
            ('System', 'indi_allsky.modern_admin_system_view'),
            ('Settings', 'indi_allsky.modern_admin_settings_view'),
            ('Updates', 'indi_allsky.modern_admin_updates_view'),
        )

        modern_admin_nav = list()
        for label, endpoint in nav_items:
            modern_admin_nav.append({
                'label'    : label,
                'endpoint' : endpoint,
                'enabled'  : True,
                'active'   : endpoint == getattr(self, 'modern_admin_active_endpoint', request.endpoint),
            })

        return modern_admin_nav


    def get_modern_admin_topbar_context(self):
        # Read-only runtime hint for the Modern Admin shell; no capture state is changed here.
        camera_id = getattr(getattr(self, 'camera', None), 'id', 0) or 0
        quick_action_url = None
        capture_action_url = None
        runtime_status = {
            'label' : 'Runtime: Unknown',
            'tone'  : 'muted',
        }

        try:
            quick_action_url = url_for('indi_allsky.ajax_system_view')
        except Exception as e:
            app.logger.error('Error determining modern admin quick action URL: %s', str(e))

        try:
            capture_action_url = url_for('indi_allsky.modern_admin_capture_service_action_view')
        except Exception as e:
            app.logger.error('Error determining modern admin capture action URL: %s', str(e))

        try:
            runtime_status = self.get_modern_admin_runtime_status()
        except Exception as e:
            app.logger.error('Error determining modern admin runtime status: %s', str(e))

        return {
            'modern_admin_quick_action_url'     : quick_action_url,
            'modern_admin_quick_action_camera'  : camera_id,
            'modern_admin_capture_action_url'   : capture_action_url,
            'modern_admin_runtime_status'       : runtime_status,
        }


    def get_modern_admin_runtime_status(self):
        try:
            multi_camera_enabled = bool(self.indi_allsky_config.get('MULTI_CAMERA_CAPTURE_ENABLE', False))
            multi_camera_config = self.indi_allsky_config.get('MULTI_CAMERA') or {}
            profile_configs = multi_camera_config.get('profiles') or []
            enabled_profiles = [p for p in profile_configs if p.get('enabled', False)]

            recent_camera_ids = self.get_recent_image_camera_ids()
            recent_camera_labels = self.get_recent_camera_labels(recent_camera_ids)

            if multi_camera_enabled:
                if len(recent_camera_ids) >= 2:
                    label = 'Runtime: Multi-camera active'
                    detail = self.format_runtime_camera_list(recent_camera_labels)
                    if detail:
                        label = '{0:s} · {1:s}'.format(label, detail)

                    return {
                        'label' : label,
                        'tone'  : 'good',
                    }

                if len(recent_camera_ids) == 1:
                    label = 'Runtime: Restart required or only one camera active'
                    detail = self.format_runtime_camera_list(recent_camera_labels)
                    if detail:
                        label = '{0:s} · {1:s}'.format(label, detail)

                    return {
                        'label' : label,
                        'tone'  : 'warn',
                    }

                profile_labels = self.get_multi_camera_profile_labels(enabled_profiles)
                label = 'Config: Multi-camera enabled · Restart may be required'
                detail = self.format_runtime_camera_list(profile_labels)
                if detail:
                    label = '{0:s} · {1:s}'.format(label, detail)

                return {
                    'label' : label,
                    'tone'  : 'warn',
                }

            if len(recent_camera_ids) >= 2:
                label = 'Runtime: Multi-camera still active · Config disabled, restart may be required'
                detail = self.format_runtime_camera_list(recent_camera_labels)
                if detail:
                    label = '{0:s} · {1:s}'.format(label, detail)

                return {
                    'label' : label,
                    'tone'  : 'warn',
                }

            if recent_camera_labels:
                label = 'Capture: Single camera · {0:s}'.format(recent_camera_labels[0])
            elif getattr(self, 'camera', None):
                label = 'Capture: Single camera · {0:s}'.format(self.get_runtime_camera_label(self.camera))
            else:
                label = 'Capture: Single camera'

            return {
                'label' : label,
                'tone'  : 'muted',
            }
        except Exception as e:
            app.logger.error('Error building modern admin runtime status: %s', str(e))
            return {
                'label' : 'Runtime: Unknown',
                'tone'  : 'muted',
            }


    def get_recent_image_camera_ids(self):
        recent_cutoff = datetime.now() - timedelta(minutes=10)

        try:
            recent_rows = db.session.query(IndiAllSkyDbImageTable.camera_id)\
                .filter(IndiAllSkyDbImageTable.createDate >= recent_cutoff)\
                .distinct()\
                .all()
        except Exception as e:
            app.logger.error('Error reading modern admin recent camera runtime status: %s', str(e))
            return list()

        return [r[0] for r in recent_rows if r[0]]


    def get_recent_camera_labels(self, camera_ids):
        if not camera_ids:
            return list()

        try:
            cameras = IndiAllSkyDbCameraTable.query\
                .filter(IndiAllSkyDbCameraTable.id.in_(camera_ids))\
                .all()
        except Exception as e:
            app.logger.error('Error reading modern admin recent camera labels: %s', str(e))
            return ['Camera {0:d}'.format(camera_id) for camera_id in camera_ids]

        camera_map = dict()
        for camera in cameras:
            camera_map[camera.id] = self.get_runtime_camera_label(camera)

        return [camera_map.get(camera_id, 'Camera {0:d}'.format(camera_id)) for camera_id in camera_ids]


    def get_runtime_camera_label(self, camera):
        return str(camera.friendlyName or camera.name or camera.driver or 'Unknown camera')


    def get_multi_camera_profile_labels(self, enabled_profiles):
        profile_labels = list()
        for profile_config in enabled_profiles:
            label = profile_config.get('label') \
                or profile_config.get('camera_name') \
                or profile_config.get('profile_id') \
                or profile_config.get('camera_interface')
            if label:
                profile_labels.append(str(label))

        return profile_labels


    def format_runtime_camera_list(self, camera_labels):
        if not camera_labels:
            return ''

        if len(camera_labels) <= 2:
            return ' + '.join(camera_labels)

        return '{0:s} + {1:d} more'.format(' + '.join(camera_labels[:2]), len(camera_labels) - 2)


    def get_capture_status_label(self):
        # Reuse the existing indi-allsky status source and normalize it for this read-only card.
        if self.capture_pause:
            return 'Paused'

        status_text = re.sub(r'<[^>]+>', '', self.get_indi_allsky_status().get('status', 'UNKNOWN')).strip().upper()

        if status_text in ('RUNNING', 'RELOADING', 'STARTING'):
            return 'Running'
        elif status_text in ('SLEEPING', 'STOPPING', 'STOPPED'):
            return 'Idle'
        elif status_text == 'PAUSED':
            return 'Paused'

        return 'Unknown'


    def get_storage_context(self):
        # Reuse psutil disk usage for the configured image filesystem; no background scan needed.
        image_folder = Path(app.config.get('INDI_ALLSKY_IMAGE_FOLDER', self.indi_allsky_config.get('IMAGE_FOLDER', '/')))
        storage_path = image_folder

        while not storage_path.exists() and storage_path != storage_path.parent:
            storage_path = storage_path.parent

        try:
            disk_usage = psutil.disk_usage(str(storage_path))
        except OSError as e:
            app.logger.error('Error determining modern admin storage usage: %s', str(e))
            return {
                'modern_admin_storage_percent' : 'Unknown',
                'modern_admin_storage_detail'  : 'Storage information unavailable.',
                'modern_admin_storage_path'    : str(image_folder),
            }

        return {
            'modern_admin_storage_percent' : '{0:0.0f}% Used'.format(disk_usage.percent),
            'modern_admin_storage_detail'  : 'Total {0:s}. Used {1:s}. Free {2:s}.'.format(
                self.format_storage_bytes(disk_usage.total),
                self.format_storage_bytes(disk_usage.used),
                self.format_storage_bytes(disk_usage.free),
            ),
            'modern_admin_storage_path' : str(storage_path),
        }


    def format_storage_bytes(self, size_b):
        size = float(size_b)
        for unit in ('B', 'KB', 'MB', 'GB'):
            if size < 1024.0:
                return '{0:0.1f} {1:s}'.format(size, unit)
            size /= 1024.0

        return '{0:0.1f} TB'.format(size)


    def format_image_age(self, create_date):
        age_s = max(0, int((self.camera_now - create_date).total_seconds()))

        if age_s < 60:
            return '{0:d}s ago'.format(age_s)
        elif age_s < 3600:
            return '{0:d}m ago'.format(int(age_s / 60))

        return '{0:d}h ago'.format(int(age_s / 3600))


class ModernAdminContextMixin(object):
    decorators = [login_required]
    modern_admin_active_endpoint = None

    def get_context(self):
        context = super(ModernAdminContextMixin, self).get_context()
        session['admin_mode'] = 'modern'

        context['modern_admin_mode'] = session.get('admin_mode', 'modern')
        context['modern_admin_nav'] = ModernAdminView.get_modern_admin_nav(self)
        context.update(ModernAdminView.get_modern_admin_topbar_context(self))

        return context


class ModernAdminCamerasView(ModernAdminView):
    # Future camera management entry point. This first version is read-only.
    page_title = 'Modern Admin Cameras'
    methods = ['GET', 'POST']

    def get_context(self):
        context = super(ModernAdminCamerasView, self).get_context()
        context['modern_admin_camera_switch_error'] = None
        context['modern_admin_camera_switch_success'] = None
        context['modern_admin_multi_camera_error'] = None
        context['modern_admin_multi_camera_success'] = None

        if request.method == 'POST':
            modern_admin_action = request.form.get('modern_admin_action')
            if modern_admin_action in ('multi_camera_enable', 'multi_camera_disable'):
                context.update(self.save_multi_camera_toggle_config(modern_admin_action))
            else:
                context.update(self.save_camera_switch_config())

        multi_camera_context = self.get_multi_camera_context()
        if multi_camera_context['enabled']:
            camera_list = self.get_multi_camera_runtime_camera_list(multi_camera_context['profiles'])
        else:
            camera_list = self.get_single_camera_runtime_camera_list()

        context['modern_admin_cameras'] = camera_list
        context['modern_admin_multi_camera'] = multi_camera_context
        context['modern_admin_section_links'] = (
            ('Add Camera', 'indi_allsky.modern_admin_camera_add_view'),
            ('Camera Info', 'indi_allsky.modern_admin_camera_info_view'),
            ('Image Lag', 'indi_allsky.modern_admin_image_lag_view'),
            ('ADU History', 'indi_allsky.modern_admin_adu_history_view'),
            ('Focus', 'indi_allsky.modern_admin_focus_view'),
            ('Image Circle Helper', 'indi_allsky.modern_admin_image_circle_helper_view'),
            ('Camera Simulator', 'indi_allsky.modern_admin_camera_simulator_view'),
            ('Dark Library', 'indi_allsky.modern_admin_dark_library_view'),
            ('Mask Base', 'indi_allsky.modern_admin_mask_view'),
        )

        return context


    def get_multi_camera_context(self):
        multi_camera_config = self.indi_allsky_config.get('MULTI_CAMERA') or {}
        profile_configs = multi_camera_config.get('profiles') or []

        profiles = list()
        enabled_count = 0
        for profile_config in profile_configs:
            enabled = bool(profile_config.get('enabled', False))
            if enabled:
                enabled_count += 1

            profiles.append({
                'profile_id'        : str(profile_config.get('profile_id') or 'unnamed'),
                'label'             : str(profile_config.get('label') or ''),
                'camera_name'       : str(profile_config.get('camera_name') or ''),
                'camera_id'         : profile_config.get('camera_id'),
                'camera_db_id'      : profile_config.get('camera_db_id'),
                'db_camera_id'      : profile_config.get('db_camera_id'),
                'indi_camera_name'  : str(profile_config.get('indi_camera_name') or ''),
                'indi'              : profile_config.get('indi') or {},
                'primary'           : bool(profile_config.get('primary', False)),
                'camera_interface'  : str(profile_config.get('camera_interface') or 'unknown'),
                'enabled'           : enabled,
            })

        multi_camera_enabled = bool(self.indi_allsky_config.get('MULTI_CAMERA_CAPTURE_ENABLE', False))
        enable_allowed = enabled_count >= 2

        if not profile_configs:
            enable_block_reason = 'At least two enabled multi-camera profiles are required.'
        elif not enable_allowed:
            enable_block_reason = 'At least two enabled multi-camera profiles are required.'
        else:
            enable_block_reason = ''

        return {
            'enabled'             : multi_camera_enabled,
            'status_label'        : 'Enabled' if multi_camera_enabled else 'Disabled',
            'mode_label'          : 'Images-only MVP',
            'profiles'            : profiles,
            'enabled_count'       : enabled_count,
            'enable_allowed'      : enable_allowed,
            'enable_block_reason' : enable_block_reason,
        }


    def get_single_camera_runtime_camera_list(self):
        cameras = IndiAllSkyDbCameraTable.query\
            .filter(IndiAllSkyDbCameraTable.hidden == sa_false())\
            .order_by(IndiAllSkyDbCameraTable.connectDate.desc())\
            .order_by(IndiAllSkyDbCameraTable.createDate.desc())\
            .all()

        camera_list = list()
        for camera in cameras:
            latest_image = self.get_latest_camera_image(camera.id)
            last_image_age = self.format_image_age(latest_image.createDate) if latest_image else 'No image'
            selected = camera.id == self.camera.id
            status = self.get_camera_status_label(camera, latest_image=latest_image)
            camera_list.append({
                'id'             : camera.id,
                'name'           : str(camera.friendlyName or camera.name or 'Unknown camera'),
                'driver'         : str(camera.driver or 'Driver unavailable'),
                'status'         : status,
                'last_image_age' : last_image_age,
                'selected'       : selected,
                'badge'          : 'Active' if selected else status,
                'role_badge'     : None,
                'enabled'        : True,
                'profile_id'     : None,
                'profile_mode'   : False,
                'switch_enabled' : not selected,
            })

        return camera_list


    def get_multi_camera_runtime_camera_list(self, profiles):
        camera_rows = self.get_modern_admin_visible_camera_rows()
        recent_camera_ids = set(self.get_recent_image_camera_ids())

        camera_list = list()
        for profile_index, profile in enumerate(profiles):
            camera_id = self.get_multi_camera_profile_camera_id(profile, camera_rows, profile_index)
            camera = self.get_camera_row_by_id(camera_rows, camera_id)
            latest_image = self.get_latest_camera_image(camera_id) if camera_id else None
            last_image_age = self.format_image_age(latest_image.createDate) if latest_image else 'No image'
            enabled = bool(profile.get('enabled', False))
            running = enabled and camera_id in recent_camera_ids
            status = self.get_multi_camera_profile_runtime_status(enabled, running)
            role_badge = 'Primary' if profile.get('primary') else 'Secondary'

            camera_list.append({
                'id'             : camera_id,
                'name'           : self.get_multi_camera_profile_camera_name(profile, camera),
                'driver'         : str(profile.get('camera_interface') or getattr(camera, 'driver', '') or 'unknown'),
                'status'         : status,
                'last_image_age' : last_image_age,
                'selected'       : running,
                'badge'          : status,
                'role_badge'     : role_badge,
                'enabled'        : enabled,
                'profile_id'     : str(profile.get('profile_id') or 'unnamed'),
                'profile_mode'   : True,
                'switch_enabled' : False,
            })

        return camera_list


    def get_modern_admin_visible_camera_rows(self):
        try:
            return IndiAllSkyDbCameraTable.query\
                .filter(IndiAllSkyDbCameraTable.hidden == sa_false())\
                .order_by(IndiAllSkyDbCameraTable.id.asc())\
                .all()
        except Exception as e:
            app.logger.error('Error loading modern admin camera rows: %s', str(e))
            return list()


    def get_latest_camera_image(self, camera_id):
        if not camera_id:
            return None

        try:
            return IndiAllSkyDbImageTable.query\
                .filter(IndiAllSkyDbImageTable.camera_id == camera_id)\
                .order_by(IndiAllSkyDbImageTable.createDate.desc())\
                .first()
        except Exception as e:
            app.logger.error('Error loading latest image for camera %s: %s', camera_id, str(e))
            return None


    def get_multi_camera_profile_runtime_status(self, enabled, running):
        if running:
            return 'Running'
        elif enabled:
            return 'Enabled'

        return 'Disabled'


    def get_multi_camera_profile_camera_id(self, profile, camera_rows, profile_index):
        for key in ('db_camera_id', 'camera_db_id', 'camera_id'):
            if key not in profile:
                continue

            try:
                return int(profile[key])
            except (TypeError, ValueError):
                continue

        matched_camera = self.get_multi_camera_profile_camera_match(profile, camera_rows)
        if matched_camera:
            return matched_camera.id

        if profile_index < len(camera_rows):
            return camera_rows[profile_index].id

        return None


    def get_multi_camera_profile_camera_match(self, profile, camera_rows):
        profile_terms = set()
        for key in ('profile_id', 'label', 'camera_name', 'camera_interface', 'indi_camera_name'):
            value = profile.get(key)
            if value:
                profile_terms.add(str(value).strip().lower())

        nested_indi = profile.get('indi') or {}
        if isinstance(nested_indi, dict):
            value = nested_indi.get('camera_name')
            if value:
                profile_terms.add(str(value).strip().lower())

        if not profile_terms:
            return None

        for camera in camera_rows:
            camera_terms = (
                camera.friendlyName,
                camera.name,
                camera.name_alt1,
                camera.name_alt2,
                camera.driver,
            )
            normalized_camera_terms = [
                str(term).strip().lower()
                for term in camera_terms
                if term
            ]

            for profile_term in profile_terms:
                for camera_term in normalized_camera_terms:
                    if profile_term == camera_term or profile_term in camera_term or camera_term in profile_term:
                        return camera

        return None


    def get_camera_row_by_id(self, camera_rows, camera_id):
        for camera in camera_rows:
            if camera.id == camera_id:
                return camera

        return None


    def get_multi_camera_profile_camera_name(self, profile, camera):
        if camera:
            return str(camera.friendlyName or camera.name or 'Unknown camera')

        return str(profile.get('camera_name') or profile.get('label') or profile.get('profile_id') or 'Unknown camera')


    def get_camera_status_label(self, camera, latest_image=None):
        if camera.id == self.camera.id:
            return self.get_capture_status_label()

        if latest_image:
            return 'Available'
        elif camera.connectDate:
            return 'Offline'

        return 'Unknown'


    def save_multi_camera_toggle_config(self, modern_admin_action):
        result = {
            'modern_admin_multi_camera_error'   : None,
            'modern_admin_multi_camera_success' : None,
        }

        if not app.config['LOGIN_DISABLED'] and not current_user.is_admin:
            result['modern_admin_multi_camera_error'] = 'Only an admin user can change multi-camera capture mode.'
            return result

        multi_camera_context = self.get_multi_camera_context()
        enable_requested = modern_admin_action == 'multi_camera_enable'

        if enable_requested and not multi_camera_context['enable_allowed']:
            result['modern_admin_multi_camera_error'] = multi_camera_context['enable_block_reason']
            return result

        new_config = json.loads(json.dumps(self.indi_allsky_config), object_pairs_hook=OrderedDict)
        new_config['MULTI_CAMERA_CAPTURE_ENABLE'] = bool(enable_requested)

        temp_config_p = None
        try:
            from ..config import IndiAllSkyConfigUtil

            with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json', encoding='utf-8') as temp_config_f:
                json.dump(new_config, temp_config_f, indent=4)
                temp_config_p = Path(temp_config_f.name)

            with io.open(str(temp_config_p), 'r', encoding='utf-8') as temp_config_f:
                # Reuse the existing Modern Admin camera config save path: load a complete config as a new active row.
                IndiAllSkyConfigUtil().load(config=temp_config_f, force=True)

            if enable_requested:
                result['modern_admin_multi_camera_success'] = 'Multi-camera images-only MVP enabled in config. Restart indi-allsky to start the multi-camera capture workers.'
            else:
                result['modern_admin_multi_camera_success'] = 'Multi-camera capture disabled in config. Restart indi-allsky to return to the normal single-camera runtime.'

            self.indi_allsky_config['MULTI_CAMERA_CAPTURE_ENABLE'] = bool(enable_requested)

        except Exception as e:
            db.session.rollback()
            app.logger.error('Error saving modern admin multi-camera toggle config: %s', str(e))
            result['modern_admin_multi_camera_error'] = 'Unable to save multi-camera capture configuration: {0:s}'.format(str(e))
        finally:
            if temp_config_p:
                try:
                    temp_config_p.unlink()
                except FileNotFoundError:
                    pass

        return result


    def save_camera_switch_config(self):
        result = {
            'modern_admin_camera_switch_error'   : None,
            'modern_admin_camera_switch_success' : None,
        }

        if not app.config['LOGIN_DISABLED'] and not current_user.is_admin:
            result['modern_admin_camera_switch_error'] = 'Only an admin user can switch the active camera configuration.'
            return result

        try:
            switch_camera_id = int(request.form.get('camera_id', 0))
        except ValueError:
            result['modern_admin_camera_switch_error'] = 'Invalid camera id.'
            return result

        camera = IndiAllSkyDbCameraTable.query\
            .filter(IndiAllSkyDbCameraTable.id == switch_camera_id)\
            .filter(IndiAllSkyDbCameraTable.hidden == sa_false())\
            .first()

        if not camera:
            result['modern_admin_camera_switch_error'] = 'Camera not found.'
            return result

        if camera.id == self.camera.id:
            result['modern_admin_camera_switch_error'] = 'This camera is already active.'
            return result

        new_config = json.loads(json.dumps(self.indi_allsky_config), object_pairs_hook=OrderedDict)
        driver = str(camera.driver or '')
        camera_name = str(camera.name or '')

        if driver.startswith('libcamera_') or driver.startswith('mqtt_') or driver in ('indi_passive', 'indi_accumulator'):
            new_config['CAMERA_INTERFACE'] = driver
        else:
            new_config['CAMERA_INTERFACE'] = 'indi'
            new_config['INDI_CAMERA_NAME'] = camera_name

        temp_config_p = None
        try:
            from ..config import IndiAllSkyConfigUtil

            with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json', encoding='utf-8') as temp_config_f:
                json.dump(new_config, temp_config_f, indent=4)
                temp_config_p = Path(temp_config_f.name)

            with io.open(str(temp_config_p), 'r', encoding='utf-8') as temp_config_f:
                # Reuse the Add Camera/config.py --force load behavior: save a complete config as a new active row.
                IndiAllSkyConfigUtil().load(config=temp_config_f, force=True)

            camera_label = camera.friendlyName or camera.name or 'selected camera'
            result['modern_admin_camera_switch_success'] = (
                'Saved a new active configuration for {0:s}. Restart indi-allsky to start capture with this camera.'.format(str(camera_label))
            )

        except Exception as e:
            db.session.rollback()
            app.logger.error('Error saving modern admin camera switch config: %s', str(e))
            result['modern_admin_camera_switch_error'] = 'Unable to save camera switch configuration: {0:s}'.format(str(e))
        finally:
            if temp_config_p:
                try:
                    temp_config_p.unlink()
                except FileNotFoundError:
                    pass

        return result


def get_modern_admin_supported_indi_drivers():
    setup_p = Path(__file__).resolve().parents[2].joinpath('setup.sh')

    try:
        setup_text = setup_p.read_text(encoding='utf-8')
    except OSError as e:
        app.logger.error('Unable to read supported INDI driver list from setup.sh: %s', str(e))
        return list()

    order_match = re.search(r'INDI_CCD_DRIVER_ORDER=\((.*?)\)', setup_text, re.S)
    if not order_match:
        return list()

    driver_names = re.findall(r'"([^"]+)"', order_match.group(1))
    driver_labels = dict(re.findall(r'INDI_CCD_DRIVER_MAP\[([^\]]+)\]="([^"]+)"', setup_text))

    supported_drivers = list()
    for driver_name in driver_names:
        supported_drivers.append({
            'value' : driver_name,
            'label' : driver_labels.get(driver_name, driver_name),
        })

    return supported_drivers


def get_modern_admin_supported_camera_interfaces():
    try:
        from .forms import IndiAllskyConfigForm
    except Exception as e:
        app.logger.error('Unable to read supported camera interface choices: %s', str(e))
        return list()

    supported_interfaces = list()
    for group_name, group_choices in IndiAllskyConfigForm.CAMERA_INTERFACE_choices.items():
        for interface_value, interface_label in group_choices:
            supported_interfaces.append({
                'group' : group_name,
                'value' : interface_value,
                'label' : interface_label,
            })

    return supported_interfaces


def get_modern_admin_supported_libcamera_interfaces():
    return [
        interface for interface in get_modern_admin_supported_camera_interfaces()
        if interface['value'].startswith('libcamera_')
    ]


def get_modern_admin_libcamera_interface_tokens():
    interface_tokens = list()

    for interface in get_modern_admin_supported_libcamera_interfaces():
        token_text = '{0:s} {1:s}'.format(interface['value'], interface['label']).lower()
        tokens = set(re.findall(r'(imx\d+|ov\d+)', token_text))
        if interface['value'] == 'libcamera_64mp_hawkeye':
            tokens.add('imx682')
        elif interface['value'] == 'libcamera_64mp_owlsight':
            tokens.add('ov64a40')

        interface_tokens.append({
            'interface' : interface,
            'tokens'    : tokens,
        })

    return interface_tokens


def match_modern_admin_libcamera_interface(camera_text):
    camera_text_l = camera_text.lower()

    for interface_entry in get_modern_admin_libcamera_interface_tokens():
        for token in interface_entry['tokens']:
            if token and token in camera_text_l:
                return interface_entry['interface']

    return None


def get_modern_admin_libcamera_sensor_tokens(camera):
    token_text = ' '.join([
        str(camera.get('interface') or ''),
        str(camera.get('name') or ''),
        str(camera.get('driver') or ''),
        ' '.join(str(p) for p in camera.get('properties', [])),
    ]).lower()

    tokens = set(re.findall(r'(imx\d+|ov\d+)', token_text))
    if camera.get('interface') == 'libcamera_64mp_hawkeye':
        tokens.add('imx682')
    elif camera.get('interface') == 'libcamera_64mp_owlsight':
        tokens.add('ov64a40')

    return tokens


def modern_admin_db_camera_matches_libcamera(db_camera, detected_camera):
    camera_interface = str(detected_camera.get('interface') or '')
    detected_tokens = get_modern_admin_libcamera_sensor_tokens(detected_camera)

    db_text = ' '.join([
        str(db_camera.name or ''),
        str(db_camera.name_alt1 or ''),
        str(db_camera.name_alt2 or ''),
        str(db_camera.friendlyName or ''),
        str(db_camera.driver or ''),
    ]).lower()

    if camera_interface and camera_interface in db_text:
        return True

    if str(db_camera.driver or '') == camera_interface:
        return True

    if str(db_camera.driver or '') == 'rpicam-still' and any(token in db_text or token in camera_interface for token in detected_tokens):
        return True

    return False


def detect_modern_admin_libcamera_cameras():
    cameras = list()
    message = 'No libcamera camera was detected.'

    try:
        import shutil
        import subprocess

        libcamera_bin = shutil.which('rpicam-still') or shutil.which('libcamera-still')
        if not libcamera_bin:
            return cameras, 'rpicam-still/libcamera-still was not found on this system.'

        libcamera_proc = subprocess.run(
            [libcamera_bin, '--list-cameras'],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            timeout=8,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return cameras, 'Timed out while listing libcamera cameras.'
    except OSError as e:
        return cameras, 'Unable to list libcamera cameras: {0:s}'.format(str(e))

    output = libcamera_proc.stdout.strip()
    if libcamera_proc.returncode != 0:
        if len(output) > 500:
            output = output[:500] + '...'
        return cameras, output or 'libcamera camera detection failed.'

    for line in output.splitlines():
        camera_match = re.match(r'^\s*(\d+)\s*:\s*([^\[\(]+)', line)
        if not camera_match:
            continue

        camera_id = int(camera_match.group(1))
        camera_name = camera_match.group(2).strip()
        interface = match_modern_admin_libcamera_interface(line)
        if not interface:
            cameras.append({
                'type'        : 'libcamera',
                'name'        : camera_name or 'libcamera camera {0:d}'.format(camera_id),
                'driver'      : 'Unsupported libcamera sensor',
                'interface'   : '',
                'camera_id'   : camera_id,
                'device_id'   : 'libcamera:unsupported:{0:d}'.format(camera_id),
                'properties'  : [line.strip()],
                'candidate'   : False,
                'selectable'  : False,
            })
            continue

        cameras.append({
            'type'        : 'libcamera',
            'name'        : camera_name or interface['label'],
            'driver'      : interface['value'],
            'interface'   : interface['value'],
            'camera_id'   : camera_id,
            'device_id'   : 'libcamera:{0:s}:{1:d}'.format(interface['value'], camera_id),
            'properties'  : [interface['label'], line.strip()],
            'candidate'   : True,
            'selectable'  : True,
        })

    if cameras:
        message = 'Detected {0:d} libcamera camera(s).'.format(len(cameras))

    return cameras, message


def get_modern_admin_active_db_camera_id(misc_db):
    try:
        return int(misc_db.getState('DB_CAMERA_ID'))
    except Exception:
        return None


def normalize_modern_admin_camera_name(camera_name):
    return str(camera_name or '').strip().lower()


def get_modern_admin_configured_camera_matches():
    cameras = IndiAllSkyDbCameraTable.query\
        .filter(IndiAllSkyDbCameraTable.hidden == sa_false())\
        .all()

    return cameras


def annotate_modern_admin_detected_cameras(detected_cameras, active_config, active_db_camera_id, indi_server=None, indi_port=None):
    configured_cameras = get_modern_admin_configured_camera_matches()
    active_interface = str(active_config.get('CAMERA_INTERFACE', '') or '')
    active_indi_name = normalize_modern_admin_camera_name(active_config.get('INDI_CAMERA_NAME', ''))
    active_indi_server = str(active_config.get('INDI_SERVER', 'localhost')).strip() or 'localhost'

    try:
        active_indi_port = int(active_config.get('INDI_PORT', 7624))
    except (TypeError, ValueError):
        active_indi_port = 7624

    try:
        active_libcamera_id = int(active_config.get('LIBCAMERA', {}).get('CAMERA_ID', 0))
    except (TypeError, ValueError):
        active_libcamera_id = 0

    detected_libcamera_counts = dict()
    for camera in detected_cameras:
        if camera.get('type') == 'libcamera' and camera.get('interface'):
            detected_libcamera_counts[camera['interface']] = detected_libcamera_counts.get(camera['interface'], 0) + 1

    for camera in detected_cameras:
        camera['db_match'] = ''
        camera['status_warning'] = ''
        camera['action_label'] = 'Add camera'

        if not camera.get('selectable', True):
            camera['status'] = 'Ambiguous match'
            camera['status_warning'] = 'This camera type is not supported by the current Modern Admin detection flow.'
            camera['action_label'] = ''
            camera['selectable'] = False
            continue

        camera_type = camera.get('type')
        if camera_type == 'libcamera':
            camera_interface = str(camera.get('interface') or '')
            camera_id = camera.get('camera_id')
            libcamera_db_matches = [
                db_camera for db_camera in configured_cameras
                if modern_admin_db_camera_matches_libcamera(db_camera, camera)
            ]

            if active_interface == camera_interface and active_libcamera_id == camera_id:
                camera['status'] = 'Active'
                camera['action_label'] = ''
                camera['selectable'] = False
            elif len(libcamera_db_matches) == 1 and detected_libcamera_counts.get(camera_interface, 0) == 1:
                camera['status'] = 'Already configured'
                camera['db_match'] = str(libcamera_db_matches[0].friendlyName or libcamera_db_matches[0].name or '')
                camera['action_label'] = 'Use this camera'
                camera['selectable'] = True
            elif len(libcamera_db_matches) > 0:
                camera['status'] = 'Ambiguous match'
                camera['status_warning'] = 'A libcamera DB row already uses this interface, but the DB does not store camera_id/USB path yet.'
                camera['action_label'] = ''
                camera['selectable'] = False
            else:
                camera['status'] = 'New camera'
                camera['action_label'] = 'Add camera'
                camera['selectable'] = True

        elif camera_type == 'indi':
            camera_name = normalize_modern_admin_camera_name(camera.get('name'))
            camera_driver = str(camera.get('driver') or '')
            exact_matches = list()
            name_matches = list()

            for db_camera in configured_cameras:
                db_names = {
                    normalize_modern_admin_camera_name(db_camera.name),
                    normalize_modern_admin_camera_name(db_camera.name_alt1),
                    normalize_modern_admin_camera_name(db_camera.name_alt2),
                }
                if camera_name not in db_names:
                    continue

                name_matches.append(db_camera)
                if camera_driver and str(db_camera.driver or '') == camera_driver:
                    exact_matches.append(db_camera)

            if active_interface == 'indi' and active_indi_name == camera_name and active_indi_server == (indi_server or active_indi_server) and active_indi_port == (indi_port or active_indi_port):
                camera['status'] = 'Active'
                camera['action_label'] = ''
                camera['selectable'] = False
            elif len(exact_matches) == 1:
                camera['status'] = 'Already configured'
                camera['db_match'] = str(exact_matches[0].friendlyName or exact_matches[0].name or '')
                camera['action_label'] = 'Use this camera'
                camera['selectable'] = True
            elif len(exact_matches) > 1 or name_matches:
                camera['status'] = 'Ambiguous match'
                camera['status_warning'] = 'A DB camera already has this INDI name, but driver/interface matching is not unique.'
                camera['action_label'] = ''
                camera['selectable'] = False
            else:
                camera['status'] = 'New camera'
                camera['action_label'] = 'Add camera'
                camera['selectable'] = True

        else:
            camera['status'] = 'Ambiguous match'
            camera['status_warning'] = 'Unknown detected camera type.'
            camera['action_label'] = ''
            camera['selectable'] = False

    return detected_cameras


def detect_modern_admin_usb_camera_driver():
    supported_driver_values = {driver['value'] for driver in get_modern_admin_supported_indi_drivers()}
    detection = {
        'detected'     : False,
        'camera_type'  : 'Unknown USB camera',
        'driver'       : '',
        'message'      : 'No known USB camera driver was auto-detected by lsusb. Choose one of the project-supported INDI drivers below.',
        'lsusb_output' : '',
    }

    try:
        import shutil
        import subprocess

        lsusb_bin = shutil.which('lsusb')
        if not lsusb_bin:
            detection['message'] = 'lsusb was not found on this system.'
            return detection

        lsusb_proc = subprocess.run(
            [lsusb_bin],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            timeout=5,
            check=False,
        )
    except subprocess.TimeoutExpired:
        detection['message'] = 'Timed out while running lsusb.'
        return detection
    except OSError as e:
        detection['message'] = 'Unable to run lsusb: {0:s}'.format(str(e))
        return detection

    output = lsusb_proc.stdout.strip()
    detection['lsusb_output'] = output

    if lsusb_proc.returncode != 0:
        detection['message'] = output or 'lsusb failed.'
        return detection

    output_l = output.lower()

    if ('03c3:' in output_l or 'zwo' in output_l) and 'indi_asi_ccd' in supported_driver_values:
        detection.update({
            'detected'    : True,
            'camera_type' : 'ZWO USB camera',
            'driver'      : 'indi_asi_ccd',
            'message'     : 'Detected ZWO camera from USB vendor 03c3.',
        })
    elif ('04a9:' in output_l or 'canon' in output_l) and 'indi_gphoto_ccd' in supported_driver_values:
        detection.update({
            'detected'    : True,
            'camera_type' : 'Canon USB camera',
            'driver'      : 'indi_gphoto_ccd',
            'message'     : 'Detected Canon camera from USB.',
        })
    elif ('04b0:' in output_l or 'nikon' in output_l) and 'indi_gphoto_ccd' in supported_driver_values:
        detection.update({
            'detected'    : True,
            'camera_type' : 'Nikon USB camera',
            'driver'      : 'indi_gphoto_ccd',
            'message'     : 'Detected Nikon camera from USB.',
        })
    elif ('054c:' in output_l or 'sony' in output_l) and 'indi_gphoto_ccd' in supported_driver_values:
        detection.update({
            'detected'    : True,
            'camera_type' : 'Sony USB camera',
            'driver'      : 'indi_gphoto_ccd',
            'message'     : 'Detected Sony camera from USB.',
        })

    return detection


class ModernAdminCameraAddView(ModernAdminView):
    # Future modern camera setup entry point; first version saves one active camera config at a time.
    page_title = 'Add Camera'
    modern_admin_active_endpoint = 'indi_allsky.modern_admin_cameras_view'
    methods = ['GET', 'POST']

    def get_context(self):
        context = super(ModernAdminCameraAddView, self).get_context()
        usb_detection = detect_modern_admin_usb_camera_driver()
        supported_indi_drivers = get_modern_admin_supported_indi_drivers()

        form_data = {
            'indi_server'      : self.indi_allsky_config.get('INDI_SERVER', 'localhost'),
            'indi_port'        : int(self.indi_allsky_config.get('INDI_PORT', 7624)),
            'indi_camera_name' : self.indi_allsky_config.get('INDI_CAMERA_NAME', ''),
            'driver_hint'      : usb_detection['driver'],
            'camera_type'      : '',
            'camera_interface' : '',
            'libcamera_id'     : self.indi_allsky_config.get('LIBCAMERA', {}).get('CAMERA_ID', 0),
        }

        context['modern_admin_add_camera_error'] = None
        context['modern_admin_add_camera_success'] = None
        context['modern_admin_add_camera_form'] = form_data
        context['modern_admin_current_config'] = {
            'id'               : self.indi_allsky_config_id,
            'camera_interface' : self.indi_allsky_config.get('CAMERA_INTERFACE', 'Unknown'),
            'indi_server'      : self.indi_allsky_config.get('INDI_SERVER', 'localhost'),
            'indi_port'        : self.indi_allsky_config.get('INDI_PORT', 7624),
            'indi_camera_name' : self.indi_allsky_config.get('INDI_CAMERA_NAME', ''),
        }
        context['modern_admin_configured_cameras'] = self.get_configured_cameras()
        context['modern_admin_usb_detection'] = usb_detection
        context['modern_admin_supported_indi_drivers'] = supported_indi_drivers
        context['modern_admin_supported_camera_interfaces'] = get_modern_admin_supported_camera_interfaces()

        if request.method == 'POST':
            context.update(self.save_indi_camera_config())

        return context


    def get_configured_cameras(self):
        cameras = IndiAllSkyDbCameraTable.query\
            .filter(IndiAllSkyDbCameraTable.hidden == sa_false())\
            .order_by(IndiAllSkyDbCameraTable.connectDate.desc())\
            .order_by(IndiAllSkyDbCameraTable.createDate.desc())\
            .all()

        camera_list = list()
        for camera in cameras:
            selected = camera.id == self.camera.id
            camera_list.append({
                'name'     : str(camera.friendlyName or camera.name or 'Unknown camera'),
                'driver'   : str(camera.driver or 'Driver unavailable'),
                'status'   : 'Active' if selected else 'Available',
                'selected' : selected,
            })

        return camera_list


    def save_indi_camera_config(self):
        form_data = {
            'indi_server'      : request.form.get('indi_server', 'localhost').strip() or 'localhost',
            'indi_port'        : request.form.get('indi_port', '7624').strip() or '7624',
            'indi_camera_name' : request.form.get('indi_camera_name', '').strip(),
            'driver_hint'      : request.form.get('driver_hint', '').strip(),
            'camera_type'      : request.form.get('camera_type', '').strip(),
            'camera_interface' : request.form.get('camera_interface', '').strip(),
            'libcamera_id'     : request.form.get('libcamera_id', '0').strip() or '0',
        }

        result = {
            'modern_admin_add_camera_form'    : form_data,
            'modern_admin_add_camera_error'   : None,
            'modern_admin_add_camera_success' : None,
        }

        if not app.config['LOGIN_DISABLED'] and not current_user.is_admin:
            result['modern_admin_add_camera_error'] = 'Only an admin user can create a new camera configuration.'
            return result

        try:
            indi_port = int(form_data['indi_port'])
        except ValueError:
            result['modern_admin_add_camera_error'] = 'INDI port must be a number.'
            return result

        if indi_port < 1 or indi_port > 65535:
            result['modern_admin_add_camera_error'] = 'INDI port must be between 1 and 65535.'
            return result

        if form_data['camera_type'] not in ('indi', 'libcamera'):
            result['modern_admin_add_camera_error'] = 'Select a detected camera before saving.'
            return result

        active_interface = self.indi_allsky_config.get('CAMERA_INTERFACE', '')

        if form_data['camera_type'] == 'indi':
            if not form_data['indi_camera_name']:
                result['modern_admin_add_camera_error'] = 'Select an INDI camera before saving.'
                return result

            active_server = str(self.indi_allsky_config.get('INDI_SERVER', 'localhost')).strip() or 'localhost'
            active_port = int(self.indi_allsky_config.get('INDI_PORT', 7624))
            active_camera_name = str(self.indi_allsky_config.get('INDI_CAMERA_NAME', '')).strip()
            detected_driver = form_data['driver_hint']

            if active_interface == 'indi' and active_server == form_data['indi_server'] and active_port == indi_port and active_camera_name == form_data['indi_camera_name']:
                result['modern_admin_add_camera_error'] = 'This INDI camera is already the active configuration. No new config was saved.'
                return result

            configured_cameras = get_modern_admin_configured_camera_matches()
            detected_name = normalize_modern_admin_camera_name(form_data['indi_camera_name'])
            exact_matches = list()
            name_matches = list()
            for db_camera in configured_cameras:
                db_names = {
                    normalize_modern_admin_camera_name(db_camera.name),
                    normalize_modern_admin_camera_name(db_camera.name_alt1),
                    normalize_modern_admin_camera_name(db_camera.name_alt2),
                }
                if detected_name not in db_names:
                    continue

                name_matches.append(db_camera)
                if detected_driver and str(db_camera.driver or '') == detected_driver:
                    exact_matches.append(db_camera)

            if len(exact_matches) > 1 or (name_matches and not exact_matches):
                result['modern_admin_add_camera_error'] = 'This INDI camera matches an existing DB name, but the driver/interface match is ambiguous. No config was saved.'
                return result

        elif form_data['camera_type'] == 'libcamera':
            supported_libcamera_values = {interface['value'] for interface in get_modern_admin_supported_libcamera_interfaces()}
            if form_data['camera_interface'] not in supported_libcamera_values:
                result['modern_admin_add_camera_error'] = 'Select a supported libcamera camera before saving.'
                return result

            try:
                libcamera_id = int(form_data['libcamera_id'])
            except ValueError:
                result['modern_admin_add_camera_error'] = 'libcamera camera id must be a number.'
                return result

            try:
                active_libcamera_id = int(self.indi_allsky_config.get('LIBCAMERA', {}).get('CAMERA_ID', 0))
            except ValueError:
                active_libcamera_id = 0

            if active_interface == form_data['camera_interface'] and active_libcamera_id == libcamera_id:
                result['modern_admin_add_camera_error'] = 'This libcamera camera is already the active configuration. No new config was saved.'
                return result

            detected_libcamera_camera = {
                'type'       : 'libcamera',
                'name'       : form_data['camera_interface'],
                'driver'     : form_data['camera_interface'],
                'interface'  : form_data['camera_interface'],
                'camera_id'  : libcamera_id,
                'properties' : [form_data['camera_interface']],
            }
            libcamera_db_matches = [
                db_camera for db_camera in get_modern_admin_configured_camera_matches()
                if modern_admin_db_camera_matches_libcamera(db_camera, detected_libcamera_camera)
            ]
            if len(libcamera_db_matches) > 1:
                result['modern_admin_add_camera_error'] = 'Multiple DB cameras already use this libcamera interface, and the DB does not store camera_id/USB path yet. No config was saved.'
                return result

        new_config = json.loads(json.dumps(self.indi_allsky_config), object_pairs_hook=OrderedDict)
        if form_data['camera_type'] == 'indi':
            new_config['CAMERA_INTERFACE'] = 'indi'
            new_config['INDI_SERVER'] = form_data['indi_server']
            new_config['INDI_PORT'] = indi_port
            new_config['INDI_CAMERA_NAME'] = form_data['indi_camera_name']
        else:
            new_config['CAMERA_INTERFACE'] = form_data['camera_interface']
            new_config.setdefault('LIBCAMERA', OrderedDict())
            new_config['LIBCAMERA']['CAMERA_ID'] = libcamera_id

        temp_config_p = None
        try:
            from ..config import IndiAllSkyConfigUtil

            with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json', encoding='utf-8') as temp_config_f:
                json.dump(new_config, temp_config_f, indent=4)
                temp_config_p = Path(temp_config_f.name)

            with io.open(str(temp_config_p), 'r', encoding='utf-8') as temp_config_f:
                # Match config.py --force load behavior: load a complete config into a new active config row.
                IndiAllSkyConfigUtil().load(config=temp_config_f, force=True)

            latest_config = IndiAllSkyDbConfigTable.query\
                .order_by(IndiAllSkyDbConfigTable.createDate.desc())\
                .first()

            result['modern_admin_current_config'] = {
                'id'               : latest_config.id if latest_config else self.indi_allsky_config_id,
                'camera_interface' : new_config['CAMERA_INTERFACE'],
                'indi_server'      : new_config.get('INDI_SERVER', form_data['indi_server']),
                'indi_port'        : new_config.get('INDI_PORT', indi_port),
                'indi_camera_name' : new_config.get('INDI_CAMERA_NAME', ''),
            }
            result['modern_admin_add_camera_success'] = (
                'Saved a new camera configuration. Restart indi-allsky to connect to the camera and create the DB camera row if needed.'
            )

        except Exception as e:
            db.session.rollback()
            app.logger.error('Error saving modern admin INDI camera config: %s', str(e))
            result['modern_admin_add_camera_error'] = 'Unable to save the INDI camera configuration: {0:s}'.format(str(e))
        finally:
            if temp_config_p:
                try:
                    temp_config_p.unlink()
                except FileNotFoundError:
                    pass

        return result


class ModernAdminIndiCameraDetectView(BaseView):
    methods = ['POST']
    decorators = [login_required]

    def dispatch_request(self):
        if not app.config['LOGIN_DISABLED'] and not current_user.is_admin:
            return jsonify({'error' : 'Only an admin user can detect cameras.'}), 403

        indi_server = request.json.get('indi_server', 'localhost').strip() or 'localhost'
        detected_cameras, libcamera_message = detect_modern_admin_libcamera_cameras()
        usb_detection = detect_modern_admin_usb_camera_driver()
        driver_hint = usb_detection['driver'] or request.json.get('driver_hint', '').strip()

        try:
            indi_port = int(request.json.get('indi_port', 7624))
        except ValueError:
            return jsonify({'error' : 'INDI port must be a number.'}), 400

        if indi_port < 1 or indi_port > 65535:
            return jsonify({'error' : 'INDI port must be between 1 and 65535.'}), 400

        try:
            import shutil
            import subprocess

            indi_getprop_bin = shutil.which('indi_getprop')
            if not indi_getprop_bin:
                detected_cameras = annotate_modern_admin_detected_cameras(detected_cameras, self.indi_allsky_config, get_modern_admin_active_db_camera_id(self._miscDb), indi_server=indi_server, indi_port=indi_port)
                return jsonify({
                    'cameras'           : detected_cameras,
                    'devices'           : detected_cameras,
                    'libcamera_message' : libcamera_message,
                    'indi_error'        : 'indi_getprop was not found on this system.',
                })

            detect_proc = subprocess.run(
                [indi_getprop_bin, '-h', indi_server, '-p', str(indi_port)],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                timeout=8,
                check=False,
            )
        except subprocess.TimeoutExpired:
            detected_cameras = annotate_modern_admin_detected_cameras(detected_cameras, self.indi_allsky_config, get_modern_admin_active_db_camera_id(self._miscDb), indi_server=indi_server, indi_port=indi_port)
            return jsonify({
                'cameras'           : detected_cameras,
                'devices'           : detected_cameras,
                'libcamera_message' : libcamera_message,
                'indi_error'        : 'Timed out waiting for indi_getprop.',
            })
        except OSError as e:
            detected_cameras = annotate_modern_admin_detected_cameras(detected_cameras, self.indi_allsky_config, get_modern_admin_active_db_camera_id(self._miscDb), indi_server=indi_server, indi_port=indi_port)
            return jsonify({
                'cameras'           : detected_cameras,
                'devices'           : detected_cameras,
                'libcamera_message' : libcamera_message,
                'indi_error'        : 'Unable to run indi_getprop: {0:s}'.format(str(e)),
            })

        if detect_proc.returncode != 0:
            output = detect_proc.stdout.strip()
            if 'connection refused' in output.lower():
                if detected_cameras:
                    detected_cameras = annotate_modern_admin_detected_cameras(detected_cameras, self.indi_allsky_config, get_modern_admin_active_db_camera_id(self._miscDb), indi_server=indi_server, indi_port=indi_port)
                    return jsonify({
                        'cameras'            : detected_cameras,
                        'devices'            : detected_cameras,
                        'libcamera_message'  : libcamera_message,
                        'indi_error'         : 'INDI server non raggiungibile su {0:s}:{1:d}. Verifica che indiserver sia attivo.'.format(indi_server, indi_port),
                        'connection_refused' : True,
                        'indi_server'        : indi_server,
                        'indi_port'          : indi_port,
                    })
                return jsonify({
                    'error'              : 'INDI server non raggiungibile su {0:s}:{1:d}. Verifica che indiserver sia attivo.'.format(indi_server, indi_port),
                    'connection_refused' : True,
                    'indi_server'        : indi_server,
                    'indi_port'          : indi_port,
                }), 400
            if len(output) > 500:
                output = output[:500] + '...'
            detected_cameras = annotate_modern_admin_detected_cameras(detected_cameras, self.indi_allsky_config, get_modern_admin_active_db_camera_id(self._miscDb), indi_server=indi_server, indi_port=indi_port)
            return jsonify({
                'cameras'           : detected_cameras,
                'devices'           : detected_cameras,
                'libcamera_message' : libcamera_message,
                'indi_error'        : output or 'indi_getprop failed.',
            })

        detected_cameras.extend(self.parse_indi_getprop_devices(detect_proc.stdout, driver_hint=driver_hint))
        detected_cameras = annotate_modern_admin_detected_cameras(detected_cameras, self.indi_allsky_config, get_modern_admin_active_db_camera_id(self._miscDb), indi_server=indi_server, indi_port=indi_port)
        return jsonify({
            'cameras'           : detected_cameras,
            'devices'           : detected_cameras,
            'libcamera_message' : libcamera_message,
        })


    def parse_indi_getprop_devices(self, output, driver_hint=''):
        device_map = OrderedDict()

        for line in output.splitlines():
            line = line.strip()
            if not line or line.startswith('#') or '.' not in line:
                continue

            prop_key, _, prop_value = line.partition('=')
            device_name, _, property_name = prop_key.partition('.')
            device_name = device_name.strip()
            property_name = property_name.strip()

            if not device_name or not property_name:
                continue

            if device_name not in device_map:
                device_map[device_name] = {
                    'name'       : device_name,
                    'type'       : 'indi',
                    'driver'     : driver_hint or '',
                    'interface'  : 'indi',
                    'camera_id'  : '',
                    'device_id'  : 'indi:{0:s}:{1:s}'.format(driver_hint or 'unknown', device_name),
                    'properties' : list(),
                    'selectable' : True,
                    'score'      : 0,
                }

            device_entry = device_map[device_name]
            if len(device_entry['properties']) < 8:
                device_entry['properties'].append('{0:s}={1:s}'.format(property_name, prop_value.strip()))

            score_text = '{0:s}.{1:s}'.format(device_name, property_name).upper()
            if any(token in score_text for token in ('ASI', 'ZWO', 'CCD_EXPOSURE', 'CCD_INFO', 'CCD_FRAME', 'CCD1')):
                device_entry['score'] += 1

        device_list = list(device_map.values())
        device_list.sort(key=lambda d: (d['score'] == 0, d['name'].lower()))

        for device in device_list:
            device['candidate'] = device['score'] > 0
            del device['score']

        return device_list


class ModernAdminIndiServerStartView(ModernAdminIndiCameraDetectView):
    methods = ['POST']
    decorators = [login_required]

    def dispatch_request(self):
        if not app.config['LOGIN_DISABLED'] and not current_user.is_admin:
            return jsonify({'error' : 'Only an admin user can start an INDI server.'}), 403

        indi_server = request.json.get('indi_server', 'localhost').strip() or 'localhost'
        if indi_server not in ('localhost', '127.0.0.1', '::1'):
            return jsonify({'error' : 'Starting indiserver is only supported for localhost in this first version.'}), 400

        try:
            indi_port = int(request.json.get('indi_port', 7624))
        except ValueError:
            return jsonify({'error' : 'INDI port must be a number.'}), 400

        if indi_port < 1 or indi_port > 65535:
            return jsonify({'error' : 'INDI port must be between 1 and 65535.'}), 400

        usb_detection = detect_modern_admin_usb_camera_driver()
        driver_hint = usb_detection['driver'] or request.json.get('driver_hint', '').strip()
        if not driver_hint:
            return jsonify({'error' : 'No USB camera driver was auto-detected. Choose a project-supported INDI driver in Advanced options.'}), 400

        supported_indi_drivers = get_modern_admin_supported_indi_drivers()
        supported_driver_values = {driver['value'] for driver in supported_indi_drivers}
        if driver_hint not in supported_driver_values:
            return jsonify({'error' : 'Unsupported INDI driver for this project: {0:s}'.format(driver_hint)}), 400

        try:
            import shutil
            import subprocess

            indiserver_bin = shutil.which('indiserver')
            if not indiserver_bin:
                return jsonify({'error' : 'indiserver was not found on this system.'}), 400

            if not shutil.which(driver_hint):
                return jsonify({'error' : 'INDI driver was not found: {0:s}'.format(driver_hint)}), 400

            indi_getprop_bin = shutil.which('indi_getprop')
            if not indi_getprop_bin:
                return jsonify({'error' : 'indi_getprop was not found on this system.'}), 400

            indiserver_socket_p = Path('/tmp/indiserver-modern-admin-{0:d}'.format(indi_port))
            try:
                indiserver_socket_p.unlink()
            except FileNotFoundError:
                pass

            indiserver_cmd = [
                indiserver_bin,
                '-v',
                '-p',
                str(indi_port),
                '-u',
                str(indiserver_socket_p),
                driver_hint,
            ]

            # Start only the local INDI server. Capture remains stopped/unchanged until the user restarts indi-allsky.
            indiserver_proc = subprocess.Popen(
                indiserver_cmd,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                start_new_session=True,
            )

            deadline = time.time() + 8
            last_output = ''
            while time.time() < deadline:
                if indiserver_proc.poll() is not None:
                    stdout, stderr = indiserver_proc.communicate(timeout=1)
                    return jsonify({
                        'error'   : 'indiserver exited before it became reachable.',
                        'command' : ' '.join(indiserver_cmd),
                        'stderr'  : (stderr or stdout or '').strip(),
                    }), 400

                detect_proc = subprocess.run(
                    [indi_getprop_bin, '-h', indi_server, '-p', str(indi_port)],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    timeout=3,
                    check=False,
                )

                if detect_proc.returncode == 0:
                    return jsonify({
                        'success' : 'INDI server started on {0:s}:{1:d}.'.format(indi_server, indi_port),
                        'command' : ' '.join(indiserver_cmd),
                        'devices' : self.parse_indi_getprop_devices(detect_proc.stdout),
                    })

                last_output = detect_proc.stdout.strip()
                time.sleep(0.8)

        except subprocess.TimeoutExpired:
            if 'indiserver_proc' in locals() and indiserver_proc.poll() is None:
                indiserver_proc.terminate()
            return jsonify({'error' : 'Timed out waiting for indi_getprop after starting indiserver.'}), 504
        except OSError as e:
            return jsonify({'error' : 'Unable to start indiserver: {0:s}'.format(str(e))}), 400

        if len(last_output) > 500:
            last_output = last_output[:500] + '...'

        if 'indiserver_proc' in locals() and indiserver_proc.poll() is None:
            indiserver_proc.terminate()

        return jsonify({
            'error'   : last_output or 'Started indiserver, but it did not become reachable before timeout.',
            'command' : ' '.join(indiserver_cmd) if 'indiserver_cmd' in locals() else '',
        }), 504


class ModernAdminPlaceholderView(ModernAdminView):
    # Read-only placeholder for future modern admin sections.
    page_title = 'Modern Admin'
    modern_admin_section = 'Modern Admin'
    modern_admin_message = 'This section is coming later.'
    modern_admin_links = tuple()

    def get_context(self):
        context = super(ModernAdminPlaceholderView, self).get_context()

        context['modern_admin_section'] = self.modern_admin_section
        context['modern_admin_message'] = self.modern_admin_message
        context['modern_admin_links'] = self.modern_admin_links

        return context


class ModernAdminStorageView(ModernAdminView):
    page_title = 'Modern Admin Storage'
    modern_admin_active_endpoint = 'indi_allsky.modern_admin_storage_view'

    def get_context(self):
        context = super(ModernAdminStorageView, self).get_context()

        context['modern_admin_section_links'] = (
            ('File Space Usage', 'indi_allsky.modern_admin_file_space_usage_view'),
            ('Drives', 'indi_allsky.modern_admin_drive_manager_view'),
            ('Gallery', 'indi_allsky.modern_admin_media_gallery_view'),
            ('Images', 'indi_allsky.modern_admin_media_images_view'),
            ('FITS Viewer', 'indi_allsky.modern_admin_media_fits_view'),
            ('Generate', 'indi_allsky.modern_admin_generate_view'),
            ('Process FITS', 'indi_allsky.modern_admin_image_processing_view'),
        )
        context['modern_admin_storage_counts'] = self.get_media_count_summary()

        return context


    def get_media_count_summary(self):
        count_models = (
            ('Images', IndiAllSkyDbImageTable),
            ('Panoramas', IndiAllSkyDbPanoramaImageTable),
            ('FITS', IndiAllSkyDbFitsImageTable),
            ('Timelapses', IndiAllSkyDbVideoTable),
        )

        summary = list()
        for label, model in count_models:
            try:
                count = model.query\
                    .join(model.camera)\
                    .filter(IndiAllSkyDbCameraTable.id == self.camera.id)\
                    .count()
            except Exception as e:
                app.logger.error('Error counting modern admin storage rows for %s: %s', label, str(e))
                count = 0

            summary.append({'label' : label, 'count' : count})

        return summary


class ModernAdminUploadsView(ModernAdminView):
    page_title = 'Modern Admin Uploads'
    modern_admin_active_endpoint = 'indi_allsky.modern_admin_uploads_view'

    def get_context(self):
        context = super(ModernAdminUploadsView, self).get_context()
        filetransfer_config = self.indi_allsky_config.get('FILETRANSFER', {})
        s3_config = self.indi_allsky_config.get('S3UPLOAD', {})
        youtube_config = self.indi_allsky_config.get('YOUTUBE', {})

        context['modern_admin_upload_targets'] = (
            {
                'label'  : 'File Transfer',
                'detail' : filetransfer_config.get('CLASSNAME', 'Not configured'),
                'status' : 'Configured' if filetransfer_config.get('HOST') else 'No host',
            },
            {
                'label'  : 'S3 Upload',
                'detail' : s3_config.get('CLASSNAME', 'Not configured'),
                'status' : 'Enabled' if s3_config.get('ENABLE') else 'Disabled',
            },
            {
                'label'  : 'YouTube',
                'detail' : 'Video uploads',
                'status' : 'Enabled' if youtube_config.get('UPLOAD_VIDEO') else 'Disabled',
            },
        )
        context['modern_admin_upload_tasks'] = self.get_task_queue_summary()
        context['modern_admin_upload_notifications'] = self.get_upload_notifications()

        return context


    def get_task_queue_summary(self):
        summary = list()
        for state in TaskQueueState:
            try:
                count = IndiAllSkyDbTaskQueueTable.query\
                    .filter(IndiAllSkyDbTaskQueueTable.state == state)\
                    .count()
            except Exception as e:
                app.logger.error('Error counting modern admin upload task queue rows: %s', str(e))
                count = 0

            summary.append({'label' : state.value, 'count' : count})

        return summary


    def get_upload_notifications(self):
        try:
            return IndiAllSkyDbNotificationTable.query\
                .filter(IndiAllSkyDbNotificationTable.category == NotificationCategory.UPLOAD)\
                .order_by(IndiAllSkyDbNotificationTable.createDate.desc())\
                .limit(6)\
                .all()
        except Exception as e:
            app.logger.error('Error loading modern admin upload notifications: %s', str(e))
            return list()


class ModernAdminObservatoryView(ModernAdminView):
    page_title = 'Modern Admin Observatory'
    modern_admin_active_endpoint = 'indi_allsky.modern_admin_observatory_view'

    def get_context(self):
        context = super(ModernAdminObservatoryView, self).get_context()
        image_data = self.get_image_data()

        context['modern_admin_section_links'] = (
            ('SQM', 'indi_allsky.modern_admin_sqm_view'),
            ('Charts', 'indi_allsky.modern_admin_charts_view'),
            ('Sensor Panel', 'indi_allsky.modern_admin_sensor_panel_view'),
            ('Astropanel', 'indi_allsky.modern_admin_astropanel_view'),
            ('VirtualSky', 'indi_allsky.modern_admin_virtualsky_view'),
            ('Realtime Keogram', 'indi_allsky.modern_admin_realtime_keogram_view'),
            ('Long Term Keogram', 'indi_allsky.modern_admin_longterm_keogram_view'),
        )
        context['modern_admin_observatory_metrics'] = (
            {'label' : 'SQM', 'value' : image_data.get('sqm', 'Unknown')},
            {'label' : 'Stars', 'value' : image_data.get('stars', 'Unknown')},
            {'label' : 'Moon Phase', 'value' : '{0:0.1f}%'.format(float(image_data.get('moon_phase', 0.0)))},
        )

        return context


class ModernAdminSystemView(ModernAdminView):
    page_title = 'Modern Admin System'
    modern_admin_active_endpoint = 'indi_allsky.modern_admin_system_view'

    def get_context(self):
        context = super(ModernAdminSystemView, self).get_context()

        context['modern_admin_section_links'] = (
            ('System Info', 'indi_allsky.modern_admin_system_info_view'),
            ('Support Info', 'indi_allsky.modern_admin_support_info_view'),
            ('Log', 'indi_allsky.modern_admin_log_view'),
            ('Settings Inventory', 'indi_allsky.modern_admin_settings_view'),
            ('Capture Basics', 'indi_allsky.modern_admin_capture_settings_view'),
            ('Camera Settings', 'indi_allsky.modern_admin_camera_settings_view'),
            ('Config', 'indi_allsky.modern_admin_config_view'),
            ('Network', 'indi_allsky.modern_admin_network_view'),
            ('GPIO Control', 'indi_allsky.modern_admin_manual_gpio_view'),
            ('Updates', 'indi_allsky.modern_admin_updates_view'),
        )
        context['modern_admin_system_metrics'] = (
            {'label' : 'CPU', 'value' : '{0:0.1f}%'.format(psutil.cpu_percent(interval=None))},
            {'label' : 'Memory', 'value' : '{0:0.1f}%'.format(psutil.virtual_memory().percent)},
            {'label' : 'Version', 'value' : __version__},
        )

        return context


class ModernAdminUpdatesView(ModernAdminView):
    page_title = 'Modern Admin Updates'
    modern_admin_active_endpoint = 'indi_allsky.modern_admin_updates_view'

    def get_context(self):
        context = super(ModernAdminUpdatesView, self).get_context()

        context['modern_admin_version'] = __version__
        context['modern_admin_update_rows'] = (
            {'label' : 'Installed Version', 'value' : __version__},
            {'label' : 'Update Mode', 'value' : 'Read-only'},
            {'label' : 'Classic Fallback', 'value' : 'Available'},
        )

        return context


class ModernAdminClassicPlaceholderView(ModernAdminPlaceholderView):
    page_title = 'Modern Admin Placeholder'

    modern_page_redirect_map = {
        'gallery'         : 'indi_allsky.modern_admin_media_gallery_view',
        'images'          : 'indi_allsky.modern_admin_media_images_view',
        'timelapses'      : 'indi_allsky.modern_admin_media_timelapses_view',
        'mini-timelapses' : 'indi_allsky.modern_admin_media_mini_timelapses_view',
        'panorama'        : 'indi_allsky.modern_admin_media_panorama_view',
        'panorama-loop'   : 'indi_allsky.modern_admin_media_panorama_loop_view',
        'fits-viewer'     : 'indi_allsky.modern_admin_media_fits_view',
        'loop'            : 'indi_allsky.modern_admin_loop_view',
        'realtime-keogram'  : 'indi_allsky.modern_admin_realtime_keogram_view',
        'long-term-keogram' : 'indi_allsky.modern_admin_longterm_keogram_view',
        'dark-library'      : 'indi_allsky.modern_admin_dark_library_view',
        'virtualsky'        : 'indi_allsky.modern_admin_virtualsky_view',
        'astropanel'        : 'indi_allsky.modern_admin_astropanel_view',
        'log'               : 'indi_allsky.modern_admin_log_view',
        'mask-base'         : 'indi_allsky.modern_admin_mask_view',
        'camera-simulator'  : 'indi_allsky.modern_admin_camera_simulator_view',
        'generate'          : 'indi_allsky.modern_admin_generate_view',
        'focus'             : 'indi_allsky.modern_admin_focus_view',
        'process-fits'      : 'indi_allsky.modern_admin_image_processing_view',
        'image-circle-helper' : 'indi_allsky.modern_admin_image_circle_helper_view',
        'config'            : 'indi_allsky.modern_admin_config_view',
        'network'           : 'indi_allsky.modern_admin_network_view',
        'drives'            : 'indi_allsky.modern_admin_drive_manager_view',
        'gpio-control'      : 'indi_allsky.modern_admin_manual_gpio_view',
    }

    classic_page_map = {
        'loop'                  : ('Dashboard', 'Loop is being folded into the modern Dashboard.', 'indi_allsky.modern_admin_view'),
        'gallery'               : ('Media', 'Modern media browsing is coming later.', None),
        'images'                : ('Media', 'Modern image browsing is coming later.', None),
        'timelapses'            : ('Media', 'Modern timelapse browsing is coming later.', None),
        'mini-timelapses'       : ('Media', 'Modern mini-timelapse browsing is coming later.', None),
        'panorama'              : ('Media', 'Modern panorama viewing is coming later.', None),
        'panorama-loop'         : ('Media', 'Modern panorama loop viewing is coming later.', None),
        'realtime-keogram'      : ('Observatory', 'Modern realtime keogram viewing is coming later.', 'indi_allsky.modern_admin_observatory_view'),
        'long-term-keogram'     : ('Observatory', 'Modern long term keogram viewing is coming later.', 'indi_allsky.modern_admin_observatory_view'),
        'fits-viewer'           : ('Media', 'Modern FITS viewing is coming later.', None),
        'dark-library'          : ('Cameras', 'Modern dark library viewing is coming later.', 'indi_allsky.modern_admin_cameras_view'),
        'virtualsky'            : ('Observatory', 'Modern VirtualSky viewing is coming later.', 'indi_allsky.modern_admin_observatory_view'),
        'camera-simulator'      : ('Cameras', 'Modern camera simulator safe view is available.', 'indi_allsky.modern_admin_camera_simulator_view'),
        'astropanel'            : ('Observatory', 'Modern AstroPanel viewing is coming later.', 'indi_allsky.modern_admin_observatory_view'),
        'generate'              : ('Storage', 'Modern generate safe view is available.', 'indi_allsky.modern_admin_generate_view'),
        'focus'                 : ('Cameras', 'Modern focus safe view is available.', 'indi_allsky.modern_admin_focus_view'),
        'process-fits'          : ('Storage', 'Modern FITS processing safe view is available.', 'indi_allsky.modern_admin_image_processing_view'),
        'image-circle-helper'   : ('Cameras', 'Modern image circle helper safe view is available.', 'indi_allsky.modern_admin_image_circle_helper_view'),
        'mask-base'             : ('Cameras', 'Modern mask tooling is coming later.', 'indi_allsky.modern_admin_cameras_view'),
        'log'                   : ('System', 'Modern log viewing is coming later.', 'indi_allsky.modern_admin_system_view'),
        'config'                : ('System', 'Modern config safe view is available.', 'indi_allsky.modern_admin_config_view'),
        'network'               : ('System', 'Modern network safe view is available.', 'indi_allsky.modern_admin_network_view'),
        'drives'                : ('Storage', 'Modern drives safe view is available.', 'indi_allsky.modern_admin_drive_manager_view'),
        'gpio-control'          : ('System', 'Modern GPIO safe view is available.', 'indi_allsky.modern_admin_manual_gpio_view'),
    }

    def dispatch_request(self, classic_page):
        if classic_page in self.modern_page_redirect_map:
            return redirect(url_for(self.modern_page_redirect_map[classic_page]))

        self.classic_page = classic_page
        section, message, active_endpoint = self.classic_page_map.get(
            classic_page,
            ('Modern Admin', 'This classic page has not been mapped yet.', None),
        )
        self.modern_admin_section = section
        self.modern_admin_message = message
        self.modern_admin_active_endpoint = active_endpoint
        return super(ModernAdminClassicPlaceholderView, self).dispatch_request()


class ModernAdminModeView(BaseView):
    # Stores the user's preferred admin shell while keeping classic admin fully available.
    decorators = [login_required]

    def dispatch_request(self, mode):
        if mode == 'classic':
            session['admin_mode'] = 'classic'
            return redirect(url_for('indi_allsky.config_view'))

        session['admin_mode'] = 'modern'
        return redirect(url_for('indi_allsky.modern_admin_view'))


class ModernAdminCaptureServiceActionView(BaseView):
    methods = ['POST']
    decorators = [login_required]

    service_name = 'indi-allsky.service'
    valid_commands = {
        'start' : 'started',
        'stop'  : 'stopped',
    }

    def dispatch_request(self):
        if not app.config['LOGIN_DISABLED'] and not current_user.is_admin:
            return self.get_response(
                False,
                'You do not have permission to control capture.',
                status_code=403,
            )

        command = self.get_requested_command()
        if command not in self.valid_commands:
            return self.get_response(
                False,
                'Invalid capture command.',
                status_code=400,
            )

        try:
            result = self.run_capture_service_command(command)
        except TimeoutError:
            return self.get_response(
                False,
                'Capture service command timed out.',
                status_code=504,
            )
        except OSError as e:
            app.logger.error('Capture service command failed to start: %s', str(e))
            return self.get_response(
                False,
                'Capture service command failed to start: {0:s}'.format(str(e)),
                status_code=500,
            )

        if result['returncode'] != 0:
            app.logger.error('Capture service %s failed: %s', command, result['output'])
            message = 'Capture service {0:s} failed.'.format(command)
            if result['output']:
                message = '{0:s} {1:s}'.format(message, result['output'])

            return self.get_response(False, message, status_code=500)

        message = 'Capture service {0:s}.'.format(self.valid_commands[command])
        return self.get_response(True, message)


    def get_requested_command(self):
        payload = request.get_json(silent=True) or {}
        if not payload:
            payload = request.form

        return str(payload.get('command', '')).strip().lower()


    def run_capture_service_command(self, command):
        import subprocess

        try:
            result = subprocess.run(
                ['systemctl', '--user', command, self.service_name],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                timeout=20,
                check=False,
            )
        except subprocess.TimeoutExpired:
            raise TimeoutError()

        return {
            'returncode' : result.returncode,
            'output'     : (result.stdout or '').strip(),
        }


    def get_redirect_url(self):
        payload = request.get_json(silent=True) or {}
        if not payload:
            payload = request.form

        next_url = payload.get('next') or request.headers.get('Referer') or ''
        if next_url.startswith('/') and not next_url.startswith('//'):
            return next_url

        if next_url.startswith(request.host_url):
            return next_url

        return url_for('indi_allsky.modern_admin_view')


    def get_response(self, success, message, status_code=200):
        flash(message, 'success' if success else 'danger')

        if request.is_json or 'application/json' in request.headers.get('Accept', ''):
            response_key = 'success-message' if success else 'failure-message'
            return jsonify({
                response_key    : message,
                'redirect-url'  : self.get_redirect_url(),
            }), status_code

        return redirect(self.get_redirect_url())


class SystemInfoView(TemplateView):
    page_title = 'System Info'
    decorators = [login_required]

    def get_context(self):
        import sys
        import platform
        import astropy
        import flask
        import numpy
        import cv2
        import gunicorn
        import cryptography

        try:
            import pycurl
        except ImportError:
            pycurl = None

        try:
            import paho.mqtt as paho_mqtt
        except ImportError:
            paho_mqtt = None

        #try:
        #    import PyIndi
        #except ImportError:
        #    PyIndi = None

        try:
            import skyfield
        except ImportError:
            skyfield = None

        context = super(SystemInfoView, self).get_context()

        context['release'] = str(__version__)

        context['uptime_str'] = self.getUptime()

        context['system_type'] = self.getSystemType()

        context['cpu_count'] = self.getCpuCount()
        context['cpu_usage'] = self.getCpuUsage()

        load5, load10, load15 = self.getLoadAverage()
        context['cpu_load5'] = load5
        context['cpu_load10'] = load10
        context['cpu_load15'] = load15

        mem_total, mem_usage = self.getMemoryUsage()
        context['mem_total'] = mem_total
        context['mem_usage'] = mem_usage

        swap_total, swap_usage = self.getSwapUsage()
        context['swap_total'] = swap_total
        context['swap_usage'] = swap_usage

        context['fs_data'] = self.getAllFsUsage()

        context['temp_list'] = self.getTemps()

        context['fan_list'] = self.getFans()

        context['net_list'] = self.getNetworkIps()

        context['systemd_target'] = self.getSystemdTarget()

        context['indiserver_service_activestate'], context['indiserver_service_unitstate'] = self.getSystemdUnitStatus(app.config['INDISERVER_SERVICE_NAME'])
        context['indiserver_timer_activestate'], context['indiserver_timer_unitstate'] = self.getSystemdUnitStatus(app.config['INDISERVER_TIMER_NAME'])
        context['indi_allsky_service_activestate'], context['indi_allsky_service_unitstate'] = self.getSystemdUnitStatus(app.config['ALLSKY_SERVICE_NAME'])
        context['indi_allsky_timer_activestate'], context['indi_allsky_timer_unitstate'] = self.getSystemdUnitStatus(app.config['ALLSKY_TIMER_NAME'])
        context['indiserver_next_trigger'] = self.getSystemdTimerTrigger(app.config['INDISERVER_TIMER_NAME'])
        context['indi_allsky_next_trigger'] = self.getSystemdTimerTrigger(app.config['ALLSKY_TIMER_NAME'])
        context['gunicorn_indi_allsky_service_activestate'], context['gunicorn_indi_allsky_service_unitstate'] = self.getSystemdUnitStatus(app.config['GUNICORN_SERVICE_NAME'])
        context['gunicorn_indi_allsky_socket_activestate'], context['gunicorn_indi_allsky_socket_unitstate'] = self.getSystemdUnitStatus(app.config['GUNICORN_SOCKET_NAME'])

        context['python_version'] = platform.python_version()
        context['python_platform'] = platform.machine()

        if sys.maxsize > 2147483648:
            context['cpu_bits'] = 64
        else:
            context['cpu_bits'] = 32

        context['gunicorn_version'] = str(getattr(gunicorn, '__version__', -1))
        context['cryptography_version'] = str(getattr(cryptography, '__version__', -1))
        context['cv2_version'] = str(getattr(cv2, '__version__', -1))
        context['ephem_version'] = str(getattr(ephem, '__version__', -1))
        context['numpy_version'] = str(getattr(numpy, '__version__', -1))
        context['astropy_version'] = str(getattr(astropy, '__version__', -1))
        context['flask_version'] = str(getattr(flask, '__version__', -1))
        context['dbus_version'] = str(getattr(dbus, '__version__', -1))


        if pycurl:
            context['pycurl_version'] = str(getattr(pycurl, 'version', -1))
        else:
            context['pycurl_version'] = 'Not installed'

        if paho_mqtt:
            context['pahomqtt_version'] = str(getattr(paho_mqtt, '__version__', -1))
        else:
            context['pahomqtt_version'] = 'Not installed'

        ### PyIndi no longer reports a version
        #if PyIndi:
        #    context['pyindi_version'] = '.'.join((
        #        str(getattr(PyIndi, 'INDI_VERSION_MAJOR', -1)),
        #        str(getattr(PyIndi, 'INDI_VERSION_MINOR', -1)),
        #        str(getattr(PyIndi, 'INDI_VERSION_RELEASE', -1)),
        #    ))
        #else:
        #    context['pyindi_version'] = 'Not installed'

        if skyfield:
            context['skyfield_version'] = str(getattr(skyfield, '__version__', -1))
        else:
            context['skyfield_version'] = 'Not installed'


        context['now'] = self.camera_now
        context['form_settime'] = IndiAllskySetDateTimeForm()


        timedate1_dict = self.getSystemdTimeDate()
        context['timedate1_dict'] = timedate1_dict


        timezone_data = {
            'NEW_TIMEZONE' : timedate1_dict['Timezone'],
        }
        context['form_timezone'] = IndiAllskySetTimezoneForm(data=timezone_data)


        if self.camera.driver:
            #app.logger.info('Current camera driver: %s', self.camera.driver)
            if self.camera.driver == 'rpicam-still':
                camera_driver = 'indi_simulator_ccd'
            else:
                camera_driver = self.camera.driver  # set the current camera driver as default
        else:
            camera_driver = 'indi_simulator_ccd'


        indiserver_form_data = {
            'CAMERA_SERVER_SELECT' : camera_driver,
            'GPS_SERVER_SELECT'    : '',
        }

        form_indiserver_change = IndiAllskyIndiServerChangeForm(data=indiserver_form_data)

        context['form_indiserver_change'] = form_indiserver_change


        return context


    def getUptime(self):
        uptime_s = time.time() - psutil.boot_time()

        days = int(uptime_s / 86400)
        uptime_s -= (days * 86400)

        hours = int(uptime_s / 3600)
        uptime_s -= (hours * 3600)

        minutes = int(uptime_s / 60)
        uptime_s -= (minutes * 60)

        #seconds = int(uptime_s)

        uptime_str = '{0:d} days, {1:d}:{2:d}'.format(days, hours, minutes)

        return uptime_str


    def getSystemType(self):
        # This is available for SBCs and systems using device trees
        model_p = Path('/proc/device-tree/model')

        try:
            if model_p.exists():
                with io.open(str(model_p), 'r') as f:
                    system_type = f.readline()  # only first line
            else:
                return 'Generic PC'
        except PermissionError as e:
            app.logger.error('Permission error: %s', str(e))
            return 'Unknown'


        system_type = system_type.strip()


        if not system_type:
            return 'Unknown'


        return str(system_type)


    def getCpuCount(self):
        return psutil.cpu_count()


    def getCpuUsage(self):
        c = psutil.cpu_times_percent()

        cpu_percent = {
            'user'    : c.user,
            'system'  : c.system,
            'idle'    : c.idle,
            'nice'    : c.nice,
            'iowait'  : c.iowait,
            'irq'     : c.irq,
            'softirq' : c.softirq,
        }

        return cpu_percent


    def getLoadAverage(self):
        return psutil.getloadavg()


    def getMemoryUsage(self):
        memory_info = psutil.virtual_memory()

        memory_total = memory_info.total
        #memory_free = memory_info.free

        memory_percent = {
            'user_percent'    : (memory_info.used / memory_total) * 100.0,
            'cached_percent'  : (memory_info.cached / memory_total) * 100.0,
        }

        memory_total_mb = int(memory_total / 1024.0 / 1024.0)

        #memory_percent = 100 - ((memory_free * 100) / memory_total)

        return memory_total_mb, memory_percent


    def getSwapUsage(self):
        swap_info = psutil.swap_memory()

        swap_total = int(swap_info[0] / 1024 / 1024)
        swap_usage = swap_info[3]

        return swap_total, swap_usage


    def getAllFsUsage(self):
        fs_list = psutil.disk_partitions(all=True)

        fs_data = list()
        for fs in fs_list:

            skip = False
            for p in ('/snap', '/sys', '/proc', '/run', '/dev'):
                if fs.mountpoint.startswith(p + '/'):
                    skip = True
                    break
                elif fs.mountpoint == p:
                    skip = True
                    break

            if skip:
                continue


            try:
                disk_usage = psutil.disk_usage(fs.mountpoint)
            except PermissionError as e:
                app.logger.error('PermissionError: %s', str(e))
                continue

            data = {
                'total_mb'   : disk_usage.total / 1024.0 / 1024.0,
                'mountpoint' : fs.mountpoint,
                'percent'    : disk_usage.percent,
            }

            fs_data.append(data)

        return fs_data


    def getTemps(self):
        temp_info = psutil.sensors_temperatures()

        temp_list = list()
        for t_key in sorted(temp_info):  # always return the keys in the same order
            for i, t in enumerate(temp_info[t_key]):
                temp_c = float(t.current)

                if self.indi_allsky_config.get('TEMP_DISPLAY') == 'f':
                    current_temp = (temp_c * 9.0 / 5.0) + 32
                    temp_sys = 'F'
                elif self.indi_allsky_config.get('TEMP_DISPLAY') == 'k':
                    current_temp = temp_c + 273.15
                    temp_sys = 'K'
                else:
                    current_temp = temp_c
                    temp_sys = 'C'

                # these names will match the mqtt topics
                if not t.label:
                    # use index for label name
                    label = str(i)
                else:
                    label = t.label

                topic = '{0:s}/{1:s}'.format(t_key, label)

                # no spaces, etc in topics
                topic_sub = re.sub(r'[#+\$\*\>\ ]', '_', topic)

                temp_list.append({
                    'name'   : topic_sub,
                    'temp'   : current_temp,
                    'sys'    : temp_sys,
                })

        return temp_list

    def getFans(self):
        fan_list = list()

        # 1) Standard: psutil sensors_fans()
        try:
            fan_info = psutil.sensors_fans()
        except Exception:
            fan_info = dict()

        for f_key in sorted(fan_info):  # stable ordering
            for i, f in enumerate(fan_info[f_key]):
                try:
                    rpm = float(getattr(f, 'current', 0.0) or 0.0)
                except Exception:
                    rpm = 0.0

                if not getattr(f, 'label', ''):
                    label = str(i)
                else:
                    label = f.label

                topic = '{0:s}/{1:s}'.format(f_key, label)
                topic_sub = re.sub(r'[#+\$\*\>\ ]', '_', topic)

                fan_list.append({
                    'name' : topic_sub,
                    'rpm'  : rpm,
                })

        # 2) Raspberry Pi 5 Active Cooler / fan connector fallback via sysfs
        # Typical path: /sys/devices/platform/cooling_fan/hwmon/hwmon*/fan1_input
        if not fan_list:
            try:
                base = Path('/sys/devices/platform/cooling_fan/hwmon')
                for fan_input in base.glob('hwmon*/fan1_input'):
                    try:
                        rpm = float(int(fan_input.read_text().strip()))
                        fan_list.append({
                            'name' : 'cooling_fan/fan1',
                            'rpm'  : rpm,
                        })
                    except Exception:
                        pass
                    break
            except Exception:
                pass

        return fan_list

    def getNetworkIps(self):
        net_info = psutil.net_if_addrs()

        net_list = list()
        for dev, addr_info in net_info.items():
            if dev == 'lo':
                # skip loopback
                continue


            dev_info = {
                'name'  : dev,
                'inet4' : [],
                'inet6' : [],
            }

            for addr in addr_info:
                if addr.family == socket.AF_INET:
                    cidr = ipaddress.IPv4Network('0.0.0.0/{0:s}'.format(addr.netmask)).prefixlen
                    dev_info['inet4'].append('{0:s}/{1:d}'.format(addr.address, cidr))

                elif addr.family == socket.AF_INET6:
                    dev_info['inet6'].append('{0:s}'.format(addr.address))

            net_list.append(dev_info)


        return net_list


    def getSystemdTarget(self):
        try:
            session_bus = dbus.SystemBus()
        except dbus.exceptions.DBusException:
            return 'D-Bus Unavailable'

        systemd1 = session_bus.get_object('org.freedesktop.systemd1', '/org/freedesktop/systemd1')
        manager = dbus.Interface(systemd1, 'org.freedesktop.systemd1.Manager')

        try:
            default_target = manager.GetDefaultTarget()
        except dbus.exceptions.DBusException:
            return 'D-Bus Exception'

        return str(default_target)


    def getSystemdTimeDate(self):
        try:
            session_bus = dbus.SystemBus()
        except dbus.exceptions.DBusException:
            # This happens in docker
            timedate1_dict = {
                'Timezone' : 'Unknown',
                'CanNTP'   : False,
                'NTP'      : False,
                'NTPSynchronized' : False,
                'LocalRTC' : False,
                'TimeUSec' : 1,
            }
            return timedate1_dict


        timedate1 = session_bus.get_object('org.freedesktop.timedate1', '/org/freedesktop/timedate1')
        manager = dbus.Interface(timedate1, 'org.freedesktop.DBus.Properties')

        timedate1_dict = dict()
        timedate1_dict['Timezone'] = str(manager.Get('org.freedesktop.timedate1', 'Timezone'))
        timedate1_dict['CanNTP'] = bool(manager.Get('org.freedesktop.timedate1', 'CanNTP'))
        timedate1_dict['NTP'] = bool(manager.Get('org.freedesktop.timedate1', 'NTP'))
        timedate1_dict['NTPSynchronized'] = bool(manager.Get('org.freedesktop.timedate1', 'NTPSynchronized'))
        timedate1_dict['LocalRTC'] = bool(manager.Get('org.freedesktop.timedate1', 'LocalRTC'))
        timedate1_dict['TimeUSec'] = int(manager.Get('org.freedesktop.timedate1', 'TimeUSec'))

        #app.logger.info('timedate1: %s', timedate1_dict)

        return timedate1_dict


class TaskQueueView(TemplateView):
    page_title = 'Task Queue'
    decorators = [login_required]

    def get_context(self):
        context = super(TaskQueueView, self).get_context()

        state_list = (
            TaskQueueState.MANUAL,
            TaskQueueState.QUEUED,
            TaskQueueState.RUNNING,
            TaskQueueState.SUCCESS,
            TaskQueueState.FAILED,
        )

        exclude_queues = (
            TaskQueueQueue.IMAGE,
            TaskQueueQueue.UPLOAD,
        )

        camera_now_minus_3d = self.camera_now - timedelta(days=3)

        tasks = IndiAllSkyDbTaskQueueTable.query\
            .filter(
                and_(
                    IndiAllSkyDbTaskQueueTable.createDate > camera_now_minus_3d,
                    IndiAllSkyDbTaskQueueTable.state.in_(state_list),
                    ~IndiAllSkyDbTaskQueueTable.queue.in_(exclude_queues),
                )
            )\
            .order_by(IndiAllSkyDbTaskQueueTable.createDate.desc())


        task_list = list()
        for task in tasks:
            if task.data:
                task_data = task.data
            else:
                task_data = {}

            t = {
                'id'         : task.id,
                'createDate' : task.createDate,
                'queue'      : task.queue.name,
                'state'      : task.state.name,
                'action'     : task_data.get('action', 'MISSING'),
                'result'     : task.result,
            }

            task_list.append(t)

        context['task_list'] = task_list

        return context


class AjaxSystemInfoView(BaseView):
    methods = ['POST']
    decorators = [login_required]

    def dispatch_request(self):
        form_system = IndiAllskySystemInfoForm(data=request.json)

        if not app.config['LOGIN_DISABLED']:
            if not current_user.is_admin:
                form_errors = form_system.errors  # this must be a property
                form_errors['form_global'] = ['You do not have permission to make configuration changes']
                return jsonify(form_errors), 400


        if not form_system.validate():
            form_errors = form_system.errors  # this must be a property
            return jsonify(form_errors), 400


        camera_id = int(request.json['CAMERA_ID'])
        service = request.json['SERVICE_HIDDEN']
        command = request.json['COMMAND_HIDDEN']

        self.cameraSetup(camera_id=camera_id)

        if service == app.config['INDISERVER_SERVICE_NAME']:
            if command == 'stop':
                r = self.stopSystemdUnit(app.config['INDISERVER_SERVICE_NAME'])
            elif command == 'start':
                r = self.startSystemdUnit(app.config['INDISERVER_SERVICE_NAME'])
            #elif command == 'disable':
            #    r = self.disableSystemdUnit(app.config['INDISERVER_SERVICE_NAME'])
            #elif command == 'enable':
            #    r = self.enableSystemdUnit(app.config['INDISERVER_SERVICE_NAME'])
            else:
                errors_data = {
                    'COMMAND_HIDDEN' : ['Unhandled command'],
                }
                return jsonify(errors_data), 400

        elif service == app.config['ALLSKY_SERVICE_NAME']:
            if command == 'hup':
                self._miscDb.setState('STATUS', constants.STATUS_RELOADING)

                task_reload = IndiAllSkyDbTaskQueueTable(
                    queue=TaskQueueQueue.MAIN,
                    state=TaskQueueState.MANUAL,
                    priority=100,
                    data={'action' : 'reload'},
                )

                db.session.add(task_reload)
                db.session.commit()

                r = 'Submitted reload task'

                #r = self.hupSystemdUnit(app.config['ALLSKY_SERVICE_NAME'])
            elif command == 'stop':
                r = self.stopSystemdUnit(app.config['ALLSKY_SERVICE_NAME'])
            elif command == 'start':
                r = self.startSystemdUnit(app.config['ALLSKY_SERVICE_NAME'])
            #elif command == 'disable':
            #    r = self.disableSystemdUnit(app.config['ALLSKY_SERVICE_NAME'])
            #elif command == 'enable':
            #    r = self.enableSystemdUnit(app.config['ALLSKY_SERVICE_NAME'])
            else:
                errors_data = {
                    'COMMAND_HIDDEN' : ['Unhandled command'],
                }
                return jsonify(errors_data), 400

        elif service == app.config['INDISERVER_TIMER_NAME']:
            if command == 'disable':
                r = self.disableSystemdUnit(app.config['INDISERVER_TIMER_NAME'])
            elif command == 'enable':
                r = self.enableSystemdUnit(app.config['INDISERVER_TIMER_NAME'])
            else:
                errors_data = {
                    'COMMAND_HIDDEN' : ['Unhandled command'],
                }
                return jsonify(errors_data), 400

        elif service == app.config['ALLSKY_TIMER_NAME']:
            if command == 'disable':
                r = self.disableSystemdUnit(app.config['ALLSKY_TIMER_NAME'])
            elif command == 'enable':
                r = self.enableSystemdUnit(app.config['ALLSKY_TIMER_NAME'])
            else:
                errors_data = {
                    'COMMAND_HIDDEN' : ['Unhandled command'],
                }
                return jsonify(errors_data), 400

        elif service == app.config['GUNICORN_SERVICE_NAME']:
            if command == 'stop':
                r = self.stopSystemdUnit(app.config['GUNICORN_SERVICE_NAME'])
            else:
                errors_data = {
                    'COMMAND_HIDDEN' : ['Unhandled command'],
                }
                return jsonify(errors_data), 400

        elif service == app.config['UPGRADE_ALLSKY_SERVICE_NAME']:
            if command == 'start':
                fs_list = psutil.disk_partitions(all=True)
                for fs in fs_list:
                    if fs.mountpoint not in ('/', '/var'):
                        continue

                    try:
                        disk_usage = psutil.disk_usage(fs.mountpoint)
                    except PermissionError as e:
                        app.logger.error('PermissionError: %s', str(e))
                        continue


                    fs_free_mb = disk_usage.total / 1024.0 / 1024.0
                    if fs_free_mb < 1000:
                        errors_data = {
                            'COMMAND_HIDDEN' : ['Not enough available space on {0:s} filesystem'.format(fs.mountpoint)],
                        }
                        return jsonify(errors_data), 400

                r = self.startSystemdUnit(app.config['UPGRADE_ALLSKY_SERVICE_NAME'])
            else:
                errors_data = {
                    'COMMAND_HIDDEN' : ['Unhandled command'],
                }
                return jsonify(errors_data), 400
        elif service == 'system':
            if command == 'reboot':
                # allowing rebooting from non-admin networks for now
                try:
                    r = self.rebootSystemd()
                except dbus.exceptions.DBusException as e:
                    json_data = {
                        'form_global' : [str(e)],
                    }
                    return jsonify(json_data), 400
            elif command == 'poweroff':
                if not self.verify_admin_network():
                    json_data = {
                        'form_global' : ['Request not from admin network (flask.json)'],
                    }
                    return jsonify(json_data), 400

                try:
                    r = self.poweroffSystemd()
                except dbus.exceptions.DBusException as e:
                    json_data = {
                        'form_global' : [str(e)],
                    }
                    return jsonify(json_data), 400
            elif command == 'validate_db':
                message_list = self.validateDbEntries()

                json_data = {
                    'success-message' : ''.join(message_list),
                }
                return jsonify(json_data)
            elif command == 'backup_db':
                task_backup_db = IndiAllSkyDbTaskQueueTable(
                    queue=TaskQueueQueue.VIDEO,
                    state=TaskQueueState.MANUAL,
                    priority=100,
                    data={
                        'action' : 'backupDatabase',
                        'kwargs' : {},
                    },
                )

                db.session.add(task_backup_db)
                db.session.commit()


                message_list = ['Submitted backup task']

                json_data = {
                    'success-message' : ''.join(message_list),
                }
                return jsonify(json_data)
            elif command == 'expire_data':
                task_expire = IndiAllSkyDbTaskQueueTable(
                    queue=TaskQueueQueue.VIDEO,
                    state=TaskQueueState.MANUAL,
                    priority=100,
                    data={
                        'action' : 'expireData',
                        'kwargs' : {
                            'camera_id' : camera_id,
                        },
                    },
                )

                db.session.add(task_expire)
                db.session.commit()

                message_list = ['Submitted expire task']

                json_data = {
                    'success-message' : ''.join(message_list),
                }
                return jsonify(json_data)
            elif command == 'flush_images':
                if not self.verify_admin_network():
                    json_data = {
                        'form_global' : ['Request not from admin network (flask.json)'],
                    }
                    return jsonify(json_data), 400

                image_count = self.flushImages(camera_id)

                json_data = {
                    'success-message' : '{0:d} Images Deleted'.format(image_count),
                }
                return jsonify(json_data)
            elif command == 'flush_16min_images':
                if not self.verify_admin_network():
                    json_data = {
                        'form_global' : ['Request not from admin network (flask.json)'],
                    }
                    return jsonify(json_data), 400

                image_count = self.flush16MinutesImages(camera_id)

                json_data = {
                    'success-message' : '{0:d} Images Deleted'.format(image_count),
                }
                return jsonify(json_data)
            elif command == 'flush_timelapses':
                if not self.verify_admin_network():
                    json_data = {
                        'form_global' : ['Request not from admin network (flask.json)'],
                    }
                    return jsonify(json_data), 400


                file_count = self.flushTimelapses(camera_id)

                json_data = {
                    'success-message' : '{0:d} Files Deleted'.format(file_count),
                }
                return jsonify(json_data)
            elif command == 'flush_daytime':
                if not self.verify_admin_network():
                    json_data = {
                        'form_global' : ['Request not from admin network (flask.json)'],
                    }
                    return jsonify(json_data), 400


                file_count = self.flushDaytime(camera_id)

                json_data = {
                    'success-message' : '{0:d} Files Deleted'.format(file_count),
                }
                return jsonify(json_data)

            else:
                errors_data = {
                    'COMMAND_HIDDEN' : ['Unhandled command'],
                }
                return jsonify(errors_data), 400


        else:
            errors_data = {
                'SERVICE_HIDDEN' : ['Unhandled service'],
            }
            return jsonify(errors_data), 400


        app.logger.info('Command return: %s', str(r))

        json_data = {
            'success-message' : 'Job submitted',
        }

        return jsonify(json_data)


    def rebootSystemd(self):
        system_bus = dbus.SystemBus()
        systemd1 = system_bus.get_object('org.freedesktop.login1', '/org/freedesktop/login1')
        manager = dbus.Interface(systemd1, 'org.freedesktop.login1.Manager')
        r = manager.Reboot(False)

        return r


    def poweroffSystemd(self):
        system_bus = dbus.SystemBus()
        systemd1 = system_bus.get_object('org.freedesktop.login1', '/org/freedesktop/login1')
        manager = dbus.Interface(systemd1, 'org.freedesktop.login1.Manager')
        r = manager.PowerOff(False)

        return r


    def flushImages(self, camera_id):
        ### Images
        image_query = IndiAllSkyDbImageTable.query\
            .join(IndiAllSkyDbImageTable.camera)\
            .filter(IndiAllSkyDbCameraTable.id == camera_id)\
            .order_by(IndiAllSkyDbImageTable.createDate.asc())


        ### FITS Images
        fits_image_query = IndiAllSkyDbFitsImageTable.query\
            .join(IndiAllSkyDbFitsImageTable.camera)\
            .filter(IndiAllSkyDbCameraTable.id == camera_id)\
            .order_by(IndiAllSkyDbFitsImageTable.createDate.asc())


        ### RAW Images
        raw_image_query = IndiAllSkyDbRawImageTable.query\
            .join(IndiAllSkyDbRawImageTable.camera)\
            .filter(IndiAllSkyDbCameraTable.id == camera_id)\
            .order_by(IndiAllSkyDbRawImageTable.createDate.asc())


        ### Panorama Images
        panorama_image_query = IndiAllSkyDbPanoramaImageTable.query\
            .join(IndiAllSkyDbPanoramaImageTable.camera)\
            .filter(IndiAllSkyDbCameraTable.id == camera_id)\
            .order_by(IndiAllSkyDbPanoramaImageTable.createDate.asc())


        ### Getting IDs first then deleting each file is faster than deleting all files with
        ### thumbnails with a single query.  Deleting associated thumbnails causes sqlalchemy
        ### to recache after every delete which cause a 1-5 second lag for each delete


        asset_lists = [
            (image_query, IndiAllSkyDbImageTable),
            (fits_image_query, IndiAllSkyDbFitsImageTable),
            (raw_image_query, IndiAllSkyDbRawImageTable),
            (panorama_image_query, IndiAllSkyDbPanoramaImageTable),
        ]


        delete_count = 0
        for asset_list, asset_table in asset_lists:
            while True:
                id_list = [entry.id for entry in asset_list.limit(500)]

                if not id_list:
                    break

                delete_count += self._deleteAssets(asset_table, id_list)


        return delete_count


    def flush16MinutesImages(self, camera_id):
        now = datetime.now()
        now_minus_x_minutes = now - timedelta(minutes=16)

        ### Images
        image_query_16 = IndiAllSkyDbImageTable.query\
            .join(IndiAllSkyDbImageTable.camera)\
            .filter(IndiAllSkyDbCameraTable.id == camera_id)\
            .filter(IndiAllSkyDbImageTable.createDate >= now_minus_x_minutes)\
            .order_by(IndiAllSkyDbImageTable.createDate.asc())


        ### Getting IDs first then deleting each file is faster than deleting all files with
        ### thumbnails with a single query.  Deleting associated thumbnails causes sqlalchemy
        ### to recache after every delete which cause a 1-5 second lag for each delete


        asset_lists = [
            (image_query_16, IndiAllSkyDbImageTable),
        ]


        delete_count = 0
        for asset_list, asset_table in asset_lists:
            while True:
                id_list = [entry.id for entry in asset_list.limit(500)]

                if not id_list:
                    break

                delete_count += self._deleteAssets(asset_table, id_list)


        return delete_count


    def flushTimelapses(self, camera_id):
        video_query = IndiAllSkyDbVideoTable.query\
            .join(IndiAllSkyDbVideoTable.camera)\
            .filter(IndiAllSkyDbCameraTable.id == camera_id)\
            .order_by(IndiAllSkyDbVideoTable.createDate.asc())

        mini_video_query = IndiAllSkyDbMiniVideoTable.query\
            .join(IndiAllSkyDbMiniVideoTable.camera)\
            .filter(IndiAllSkyDbCameraTable.id == camera_id)\
            .order_by(IndiAllSkyDbMiniVideoTable.createDate.asc())

        keogram_query = IndiAllSkyDbKeogramTable.query\
            .join(IndiAllSkyDbKeogramTable.camera)\
            .filter(IndiAllSkyDbCameraTable.id == camera_id)\
            .order_by(IndiAllSkyDbKeogramTable.createDate.asc())

        startrail_query = IndiAllSkyDbStarTrailsTable.query\
            .join(IndiAllSkyDbStarTrailsTable.camera)\
            .filter(IndiAllSkyDbCameraTable.id == camera_id)\
            .order_by(IndiAllSkyDbStarTrailsTable.createDate.asc())

        startrail_video_query = IndiAllSkyDbStarTrailsVideoTable.query\
            .join(IndiAllSkyDbStarTrailsVideoTable.camera)\
            .filter(IndiAllSkyDbCameraTable.id == camera_id)\
            .order_by(IndiAllSkyDbStarTrailsVideoTable.createDate.asc())

        panorama_video_query = IndiAllSkyDbPanoramaVideoTable.query\
            .join(IndiAllSkyDbPanoramaVideoTable.camera)\
            .filter(IndiAllSkyDbCameraTable.id == camera_id)\
            .order_by(IndiAllSkyDbPanoramaVideoTable.createDate.asc())


        ### Getting IDs first then deleting each file is faster than deleting all files with
        ### thumbnails with a single query.  Deleting associated thumbnails causes sqlalchemy
        ### to recache after every delete which cause a 1-5 second lag for each delete


        asset_lists = [
            (video_query, IndiAllSkyDbVideoTable),
            (mini_video_query, IndiAllSkyDbMiniVideoTable),
            (keogram_query, IndiAllSkyDbKeogramTable),
            (startrail_query, IndiAllSkyDbStarTrailsTable),
            (startrail_video_query, IndiAllSkyDbStarTrailsVideoTable),
            (panorama_video_query, IndiAllSkyDbPanoramaVideoTable),
        ]


        delete_count = 0
        for asset_list, asset_table in asset_lists:
            while True:
                id_list = [entry.id for entry in asset_list.limit(500)]

                if not id_list:
                    break

                delete_count += self._deleteAssets(asset_table, id_list)


        return delete_count


    def flushDaytime(self, camera_id):
        ### Images
        image_query = IndiAllSkyDbImageTable.query\
            .join(IndiAllSkyDbImageTable.camera)\
            .filter(IndiAllSkyDbCameraTable.id == camera_id)\
            .filter(IndiAllSkyDbImageTable.night == sa_false())\
            .order_by(IndiAllSkyDbImageTable.createDate.asc())


        ### FITS Images
        fits_image_query = IndiAllSkyDbFitsImageTable.query\
            .join(IndiAllSkyDbFitsImageTable.camera)\
            .filter(IndiAllSkyDbCameraTable.id == camera_id)\
            .filter(IndiAllSkyDbFitsImageTable.night == sa_false())\
            .order_by(IndiAllSkyDbFitsImageTable.createDate.asc())


        ### RAW Images
        raw_image_query = IndiAllSkyDbRawImageTable.query\
            .join(IndiAllSkyDbRawImageTable.camera)\
            .filter(IndiAllSkyDbCameraTable.id == camera_id)\
            .filter(IndiAllSkyDbRawImageTable.night == sa_false())\
            .order_by(IndiAllSkyDbRawImageTable.createDate.asc())


        ### Panorama Images
        panorama_image_query = IndiAllSkyDbPanoramaImageTable.query\
            .join(IndiAllSkyDbPanoramaImageTable.camera)\
            .filter(IndiAllSkyDbCameraTable.id == camera_id)\
            .filter(IndiAllSkyDbPanoramaImageTable.night == sa_false())\
            .order_by(IndiAllSkyDbPanoramaImageTable.createDate.asc())


        ### Timelapses
        video_query = IndiAllSkyDbVideoTable.query\
            .join(IndiAllSkyDbVideoTable.camera)\
            .filter(IndiAllSkyDbCameraTable.id == camera_id)\
            .filter(IndiAllSkyDbVideoTable.night == sa_false())\
            .order_by(IndiAllSkyDbVideoTable.createDate.asc())

        ### Not flushing daytime mini timelapses

        ### Keograms
        keogram_query = IndiAllSkyDbKeogramTable.query\
            .join(IndiAllSkyDbKeogramTable.camera)\
            .filter(IndiAllSkyDbCameraTable.id == camera_id)\
            .filter(IndiAllSkyDbKeogramTable.night == sa_false())\
            .order_by(IndiAllSkyDbKeogramTable.createDate.asc())


        ### Panorama Videos
        panorama_video_query = IndiAllSkyDbPanoramaVideoTable.query\
            .join(IndiAllSkyDbPanoramaVideoTable.camera)\
            .filter(IndiAllSkyDbCameraTable.id == camera_id)\
            .filter(IndiAllSkyDbPanoramaVideoTable.night == sa_false())\
            .order_by(IndiAllSkyDbPanoramaVideoTable.createDate.asc())

        ## no startrails
        ## no startrail videos


        ### Getting IDs first then deleting each file is faster than deleting all files with
        ### thumbnails with a single query.  Deleting associated thumbnails causes sqlalchemy
        ### to recache after every delete which cause a 1-5 second lag for each delete


        asset_lists = [
            (image_query, IndiAllSkyDbImageTable),
            (fits_image_query, IndiAllSkyDbFitsImageTable),
            (raw_image_query, IndiAllSkyDbRawImageTable),
            (panorama_image_query, IndiAllSkyDbPanoramaImageTable),
            (video_query, IndiAllSkyDbVideoTable),
            (keogram_query, IndiAllSkyDbKeogramTable),
            (panorama_video_query, IndiAllSkyDbPanoramaVideoTable),
        ]


        delete_count = 0
        for asset_list, asset_table in asset_lists:
            while True:
                id_list = [entry.id for entry in asset_list.limit(500)]

                if not id_list:
                    break

                delete_count += self._deleteAssets(asset_table, id_list)


        return delete_count


    def _deleteAssets(self, table, entry_id_list):
        delete_count = 0
        for entry_id in entry_id_list:
            entry = table.query\
                .filter(table.id == entry_id)\
                .one()

            app.logger.info('Removing %s entry: %s', entry.__class__.__name__, entry.filename)

            try:
                entry.deleteAsset()
            except OSError as e:
                app.logger.error('Cannot remove file: %s', str(e))
                continue

            db.session.delete(entry)
            db.session.commit()

            delete_count += 1

        return delete_count


    def validateDbEntries(self):
        message_list = list()

        ### Images
        image_entries = IndiAllSkyDbImageTable.query\
            .filter(IndiAllSkyDbImageTable.s3_key == sa_null())\
            .order_by(IndiAllSkyDbImageTable.createDate.asc())


        image_entries_count = image_entries.count()
        message_list.append('<p>Images: {0:d}</p>'.format(image_entries_count))

        app.logger.info('Searching %d images...', image_entries_count)
        image_notfound_list = list()
        for i in image_entries:
            if not i.validateFile():
                #logger.warning('Entry not found on filesystem: %s', i.filename)
                image_notfound_list.append(i)


        ### FITS Images
        fits_image_entries = IndiAllSkyDbFitsImageTable.query\
            .filter(IndiAllSkyDbFitsImageTable.s3_key == sa_null())\
            .order_by(IndiAllSkyDbFitsImageTable.createDate.asc())


        fits_image_entries_count = fits_image_entries.count()
        message_list.append('<p>FITS Images: {0:d}</p>'.format(fits_image_entries_count))

        app.logger.info('Searching %d fits images...', fits_image_entries_count)
        fits_image_notfound_list = list()
        for i in fits_image_entries:
            if not i.validateFile():
                #logger.warning('Entry not found on filesystem: %s', i.filename)
                fits_image_notfound_list.append(i)


        ### Raw Images
        raw_image_entries = IndiAllSkyDbRawImageTable.query\
            .filter(IndiAllSkyDbRawImageTable.s3_key == sa_null())\
            .order_by(IndiAllSkyDbRawImageTable.createDate.asc())


        raw_image_entries_count = raw_image_entries.count()
        message_list.append('<p>RAW Images: {0:d}</p>'.format(raw_image_entries_count))

        app.logger.info('Searching %d raw images...', raw_image_entries_count)
        raw_image_notfound_list = list()
        for i in raw_image_entries:
            if not i.validateFile():
                #logger.warning('Entry not found on filesystem: %s', i.filename)
                raw_image_notfound_list.append(i)


        ### Panorama Images
        panorama_image_entries = IndiAllSkyDbPanoramaImageTable.query\
            .filter(IndiAllSkyDbPanoramaImageTable.s3_key == sa_null())\
            .order_by(IndiAllSkyDbPanoramaImageTable.createDate.asc())


        panorama_image_entries_count = panorama_image_entries.count()
        message_list.append('<p>Panorama Images: {0:d}</p>'.format(panorama_image_entries_count))

        app.logger.info('Searching %d panorama images...', panorama_image_entries_count)
        panorama_image_notfound_list = list()
        for i in panorama_image_entries:
            if not i.validateFile():
                #logger.warning('Entry not found on filesystem: %s', i.filename)
                panorama_image_notfound_list.append(i)


        ### Bad Pixel Maps
        badpixelmap_entries = IndiAllSkyDbBadPixelMapTable.query\
            .order_by(IndiAllSkyDbBadPixelMapTable.createDate.asc())
        # fixme - need deal with non-local installs


        badpixelmap_entries_count = badpixelmap_entries.count()
        message_list.append('<p>Bad pixel maps: {0:d}</p>'.format(badpixelmap_entries_count))

        app.logger.info('Searching %d bad pixel maps...', badpixelmap_entries_count)
        badpixelmap_notfound_list = list()
        for b in badpixelmap_entries:
            if not b.validateFile():
                #logger.warning('Entry not found on filesystem: %s', b.filename)
                badpixelmap_notfound_list.append(b)


        ### Dark frames
        darkframe_entries = IndiAllSkyDbDarkFrameTable.query\
            .order_by(IndiAllSkyDbDarkFrameTable.createDate.asc())
        # fixme - need deal with non-local installs


        darkframe_entries_count = darkframe_entries.count()
        message_list.append('<p>Dark Frames: {0:d}</p>'.format(darkframe_entries_count))

        app.logger.info('Searching %d dark frames...', darkframe_entries_count)
        darkframe_notfound_list = list()
        for d in darkframe_entries:
            if not d.validateFile():
                #logger.warning('Entry not found on filesystem: %s', d.filename)
                darkframe_notfound_list.append(d)


        ### Videos
        video_entries = IndiAllSkyDbVideoTable.query\
            .filter(
                and_(
                    IndiAllSkyDbVideoTable.success == sa_true(),
                    IndiAllSkyDbVideoTable.s3_key == sa_null(),
                )
            )\
            .order_by(IndiAllSkyDbVideoTable.createDate.asc())

        video_entries_count = video_entries.count()
        message_list.append('<p>Timelapses: {0:d}</p>'.format(video_entries_count))

        app.logger.info('Searching %d videos...', video_entries_count)
        video_notfound_list = list()
        for v in video_entries:
            if not v.validateFile():
                #logger.warning('Entry not found on filesystem: %s', v.filename)
                video_notfound_list.append(v)


        ### Mini Videos
        mini_video_entries = IndiAllSkyDbMiniVideoTable.query\
            .filter(
                and_(
                    IndiAllSkyDbMiniVideoTable.success == sa_true(),
                    IndiAllSkyDbMiniVideoTable.s3_key == sa_null(),
                )
            )\
            .order_by(IndiAllSkyDbMiniVideoTable.createDate.asc())

        mini_video_entries_count = mini_video_entries.count()
        message_list.append('<p>Mini Timelapses: {0:d}</p>'.format(mini_video_entries_count))

        app.logger.info('Searching %d mini videos...', mini_video_entries_count)
        mini_video_notfound_list = list()
        for m in mini_video_entries:
            if not m.validateFile():
                #logger.warning('Entry not found on filesystem: %s', m.filename)
                mini_video_notfound_list.append(m)


        ### Keograms
        keogram_entries = IndiAllSkyDbKeogramTable.query\
            .filter(IndiAllSkyDbKeogramTable.s3_key == sa_null())\
            .order_by(IndiAllSkyDbKeogramTable.createDate.asc())

        keogram_entries_count = keogram_entries.count()
        message_list.append('<p>Keograms: {0:d}</p>'.format(keogram_entries_count))

        app.logger.info('Searching %d keograms...', keogram_entries_count)
        keogram_notfound_list = list()
        for k in keogram_entries:
            if not k.validateFile():
                #logger.warning('Entry not found on filesystem: %s', k.filename)
                keogram_notfound_list.append(k)


        ### Startrails
        startrail_entries = IndiAllSkyDbStarTrailsTable.query\
            .filter(
                and_(
                    IndiAllSkyDbStarTrailsTable.success == sa_true(),
                    IndiAllSkyDbStarTrailsTable.s3_key == sa_null(),
                )
            )\
            .order_by(IndiAllSkyDbStarTrailsTable.createDate.asc())

        startrail_entries_count = startrail_entries.count()
        message_list.append('<p>Star trails: {0:d}</p>'.format(startrail_entries_count))

        app.logger.info('Searching %d star trails...', startrail_entries_count)
        startrail_notfound_list = list()
        for s in startrail_entries:
            if not s.validateFile():
                #logger.warning('Entry not found on filesystem: %s', s.filename)
                startrail_notfound_list.append(s)


        ### Startrail videos
        startrail_video_entries = IndiAllSkyDbStarTrailsVideoTable.query\
            .filter(
                and_(
                    IndiAllSkyDbStarTrailsVideoTable.success == sa_true(),
                    IndiAllSkyDbStarTrailsVideoTable.s3_key == sa_null(),
                )
            )\
            .order_by(IndiAllSkyDbStarTrailsVideoTable.createDate.asc())

        startrail_video_entries_count = startrail_video_entries.count()
        message_list.append('<p>Star trail timelapses: {0:d}</p>'.format(startrail_video_entries_count))

        app.logger.info('Searching %d star trail timelapses...', startrail_video_entries_count)
        startrail_video_notfound_list = list()
        for s in startrail_video_entries:
            if not s.validateFile():
                #logger.warning('Entry not found on filesystem: %s', s.filename)
                startrail_video_notfound_list.append(s)


        ### Panorama videos
        panorama_video_entries = IndiAllSkyDbPanoramaVideoTable.query\
            .filter(
                and_(
                    IndiAllSkyDbPanoramaVideoTable.success == sa_true(),
                    IndiAllSkyDbPanoramaVideoTable.s3_key == sa_null(),
                )
            )\
            .order_by(IndiAllSkyDbPanoramaVideoTable.createDate.asc())

        panorama_video_entries_count = panorama_video_entries.count()
        message_list.append('<p>Panorama timelapses: {0:d}</p>'.format(panorama_video_entries_count))

        app.logger.info('Searching %d panorama timelapses...', panorama_video_entries_count)
        panorama_video_notfound_list = list()
        for p in panorama_video_entries:
            if not p.validateFile():
                #logger.warning('Entry not found on filesystem: %s', p.filename)
                panorama_video_notfound_list.append(p)


        ### Thumbnails
        thumbnail_entries = IndiAllSkyDbThumbnailTable.query\
            .filter(IndiAllSkyDbThumbnailTable.s3_key == sa_null())\
            .order_by(IndiAllSkyDbThumbnailTable.createDate.asc())

        thumbnail_entries_count = thumbnail_entries.count()
        message_list.append('<p>Thumbnails: {0:d}</p>'.format(thumbnail_entries_count))

        app.logger.info('Searching %d thumbnails...', thumbnail_entries_count)
        thumbnail_notfound_list = list()
        for t in thumbnail_entries:
            if not t.validateFile():
                #logger.warning('Entry not found on filesystem: %s', t.filename)
                thumbnail_notfound_list.append(t)



        app.logger.warning('Images not found: %d', len(image_notfound_list))
        app.logger.warning('FITS Images not found: %d', len(fits_image_notfound_list))
        app.logger.warning('RAW Images not found: %d', len(raw_image_notfound_list))
        app.logger.warning('Panorama Images not found: %d', len(panorama_image_notfound_list))
        app.logger.warning('Bad pixel maps not found: %d', len(badpixelmap_notfound_list))
        app.logger.warning('Dark frames not found: %d', len(darkframe_notfound_list))
        app.logger.warning('Videos not found: %d', len(video_notfound_list))
        app.logger.warning('Mini Videos not found: %d', len(mini_video_notfound_list))
        app.logger.warning('Keograms not found: %d', len(keogram_notfound_list))
        app.logger.warning('Star trails not found: %d', len(startrail_notfound_list))
        app.logger.warning('Star trail timelapses not found: %d', len(startrail_video_notfound_list))
        app.logger.warning('Panorama timelapses not found: %d', len(panorama_video_notfound_list))
        app.logger.warning('Thumbnails not found: %d', len(thumbnail_notfound_list))


        ### DELETE ###
        message_list.append('<p>Removed {0:d} missing image entries</p>'.format(len(image_notfound_list)))
        [db.session.delete(i) for i in image_notfound_list]


        message_list.append('<p>Removed {0:d} missing FITS image entries</p>'.format(len(fits_image_notfound_list)))
        [db.session.delete(i) for i in fits_image_notfound_list]


        message_list.append('<p>Removed {0:d} missing RAW image entries</p>'.format(len(raw_image_notfound_list)))
        [db.session.delete(i) for i in raw_image_notfound_list]


        message_list.append('<p>Removed {0:d} missing panorama image entries</p>'.format(len(panorama_image_notfound_list)))
        [db.session.delete(i) for i in panorama_image_notfound_list]


        message_list.append('<p>Removed {0:d} missing bad pixel map entries</p>'.format(len(badpixelmap_notfound_list)))
        [db.session.delete(b) for b in badpixelmap_notfound_list]


        message_list.append('<p>Removed {0:d} missing dark frame entries</p>'.format(len(darkframe_notfound_list)))
        [db.session.delete(d) for d in darkframe_notfound_list]


        message_list.append('<p>Removed {0:d} missing video entries</p>'.format(len(video_notfound_list)))
        [db.session.delete(v) for v in video_notfound_list]


        message_list.append('<p>Removed {0:d} missing mini video entries</p>'.format(len(mini_video_notfound_list)))
        [db.session.delete(m) for m in mini_video_notfound_list]


        message_list.append('<p>Removed {0:d} missing keogram entries</p>'.format(len(keogram_notfound_list)))
        [db.session.delete(k) for k in keogram_notfound_list]


        message_list.append('<p>Removed {0:d} missing star trail entries</p>'.format(len(startrail_notfound_list)))
        [db.session.delete(s) for s in startrail_notfound_list]


        message_list.append('<p>Removed {0:d} missing star trail timelapse entries</p>'.format(len(startrail_video_notfound_list)))
        [db.session.delete(sv) for sv in startrail_video_notfound_list]


        message_list.append('<p>Removed {0:d} missing panorama timelapse entries</p>'.format(len(panorama_video_notfound_list)))
        [db.session.delete(p) for p in panorama_video_notfound_list]


        message_list.append('<p>Removed {0:d} missing thumbnail entries</p>'.format(len(thumbnail_notfound_list)))
        [db.session.delete(t) for t in thumbnail_notfound_list]


        # finalize transaction
        db.session.commit()

        return message_list


class AjaxIndiServerChangeView(BaseView):
    methods = ['POST']
    decorators = [login_required]

    def dispatch_request(self):
        import shutil

        form_indiserver_change = IndiAllskyIndiServerChangeForm(data=request.json)

        if not app.config['LOGIN_DISABLED']:
            if not current_user.is_admin:
                form_errors = form_indiserver_change.errors  # this must be a property
                form_errors['form_global'] = ['You do not have permission to make configuration changes']
                return jsonify(form_errors), 400


        if not form_indiserver_change.validate():
            form_errors = form_indiserver_change.errors  # this must be a property
            return jsonify(form_errors), 400


        camera_server = str(request.json['CAMERA_SERVER_SELECT'])
        gps_server = str(request.json['GPS_SERVER_SELECT'])
        restart_indiserver = bool(request.json['RESTART_INDISERVER'])


        # find the indiserver
        if Path('/usr/local/bin/indiserver').exists():
            indiserver_p = Path('/usr/local/bin/indiserver')
        elif Path('/usr/bin/indiserver').exists():
            indiserver_p = Path('/usr/bin/indiserver')
        else:
            which_indiserver = shutil.which('indiserver')

            if which_indiserver:
                indiserver_p = Path(which_indiserver)
            else:
                raise Exception('indiserver not found')


        allsky_directory_p = Path(__file__).parent.parent.parent.absolute()


        with io.open(str(allsky_directory_p.joinpath('service', 'indiserver.service')), 'r') as f_service_tmpl:
            service_tmpl = f_service_tmpl.read()


        service_tmpl = service_tmpl.replace('%ALLSKY_DIRECTORY%', str(allsky_directory_p))\
            .replace('%INDI_DRIVER_PATH%', str(indiserver_p.parent.absolute()))\
            .replace('%INDI_PORT%', str(self.indi_allsky_config.get('INDI_PORT', 7624)))\
            .replace('%INDI_CCD_DRIVER%', camera_server)\
            .replace('%INDI_GPS_DRIVER%', gps_server)\
            .replace('%INDISERVER_USER%', os.getlogin())


        indiserver_service_p = Path(os.environ.get('HOME', '/home/{0:s}'.format(os.getlogin()))).joinpath('.config', 'systemd', 'user', app.config['INDISERVER_SERVICE_NAME'])

        with io.open(str(indiserver_service_p), 'w') as f_indiserver_service:
            f_indiserver_service.write(service_tmpl)


        indiserver_service_p.chmod(0o644)


        self.reloadSystemdUnits()


        success_message = 'Reconfigure completed.'


        if restart_indiserver:
            self.restartSystemdUnit(app.config['INDISERVER_SERVICE_NAME'])
            success_message += ' Restart complete'


        return jsonify({'success-message' : success_message})


    def reloadSystemdUnits(self, bus_type=dbus.SessionBus):
        try:
            bus = bus_type()
        except dbus.exceptions.DBusException:
            # This happens in docker
            return 'D-Bus Unavailable', 'D-Bus Unavailable'

        systemd1 = bus.get_object('org.freedesktop.systemd1', '/org/freedesktop/systemd1')
        manager = dbus.Interface(systemd1, 'org.freedesktop.systemd1.Manager')

        try:
            manager.Reload()
        except dbus.exceptions.DBusException:
            return 'UNKNOWN', 'UNKNOWN'


class TimelapseGeneratorView(TemplateView):
    page_title = 'Generate'
    decorators = [login_required]


    def get_context(self):
        context = super(TimelapseGeneratorView, self).get_context()

        form_data = {
            'CAMERA_ID' : self.camera.id,
        }

        context['form_timelapsegen'] = IndiAllskyTimelapseGeneratorForm(
            data=form_data,
            camera_id=self.camera.id,
        )

        # Lookup tasks
        state_list = (
            TaskQueueState.MANUAL,
            TaskQueueState.QUEUED,
            TaskQueueState.RUNNING,
            TaskQueueState.SUCCESS,
            TaskQueueState.FAILED,
        )

        queue_list = (
            TaskQueueQueue.VIDEO,
        )

        camera_now_minus_12h = self.camera_now - timedelta(hours=12)

        tasks_q = IndiAllSkyDbTaskQueueTable.query\
            .filter(
                and_(
                    IndiAllSkyDbTaskQueueTable.createDate > camera_now_minus_12h,
                    IndiAllSkyDbTaskQueueTable.state.in_(state_list),
                    IndiAllSkyDbTaskQueueTable.queue.in_(queue_list),
                )
            )\
            .order_by(IndiAllSkyDbTaskQueueTable.createDate.desc())


        task_list = list()
        for task in tasks_q:
            if task.data:
                task_data = task.data
            else:
                task_data = {}

            t = {
                'id'         : task.id,
                'createDate' : task.createDate,
                'queue'      : task.queue.name,
                'action'     : task_data.get('action', 'MISSING'),
                'state'      : task.state.name,
                'result'     : task.result,
            }

            task_list.append(t)

        context['task_list'] = task_list


        return context


class AjaxTimelapseGeneratorView(BaseView):
    methods = ['POST']
    decorators = [login_required]


    def __init__(self, **kwargs):
        super(AjaxTimelapseGeneratorView, self).__init__(**kwargs)


    def dispatch_request(self):
        if not current_user.is_admin:
            json_data = {
                'form_global' : ['User does not have permission to generate content'],
            }
            return jsonify(json_data), 400


        camera_id = int(request.json['CAMERA_ID'])

        form_timelapsegen = IndiAllskyTimelapseGeneratorForm(data=request.json, camera_id=camera_id)

        if not form_timelapsegen.validate():
            form_errors = form_timelapsegen.errors  # this must be a property
            return jsonify(form_errors), 400


        if not self.verify_admin_network():
            json_data = {
                'form_global' : ['Request not from admin network (flask.json)'],
            }
            return jsonify(json_data), 400


        action = request.json['ACTION_SELECT']
        day_select_str = request.json['DAY_SELECT']

        day_str, night_str = day_select_str.split('_')

        day_date = datetime.strptime(day_str, '%Y-%m-%d').date()

        if night_str == 'night':
            night = True
        else:
            night = False


        camera = IndiAllSkyDbCameraTable.query\
            .filter(IndiAllSkyDbCameraTable.id == camera_id)\
            .one()


        if action == 'delete_video_k_st_p':
            video_entry = IndiAllSkyDbVideoTable.query\
                .join(IndiAllSkyDbVideoTable.camera)\
                .filter(
                    and_(
                        IndiAllSkyDbCameraTable.id == camera.id,
                        IndiAllSkyDbVideoTable.dayDate == day_date,
                        IndiAllSkyDbVideoTable.night == night,
                    )
                )\
                .first()

            keogram_entry = IndiAllSkyDbKeogramTable.query\
                .join(IndiAllSkyDbKeogramTable.camera)\
                .filter(
                    and_(
                        IndiAllSkyDbCameraTable.id == camera.id,
                        IndiAllSkyDbKeogramTable.dayDate == day_date,
                        IndiAllSkyDbKeogramTable.night == night,
                    )
                )\
                .first()

            startrail_entry = IndiAllSkyDbStarTrailsTable.query\
                .join(IndiAllSkyDbStarTrailsTable.camera)\
                .filter(
                    and_(
                        IndiAllSkyDbCameraTable.id == camera.id,
                        IndiAllSkyDbStarTrailsTable.dayDate == day_date,
                        IndiAllSkyDbStarTrailsTable.night == night,
                    )
                )\
                .first()

            startrail_video_entry = IndiAllSkyDbStarTrailsVideoTable.query\
                .join(IndiAllSkyDbStarTrailsVideoTable.camera)\
                .filter(
                    and_(
                        IndiAllSkyDbCameraTable.id == camera.id,
                        IndiAllSkyDbStarTrailsVideoTable.dayDate == day_date,
                        IndiAllSkyDbStarTrailsVideoTable.night == night,
                    )
                )\
                .first()

            panorama_video_entry = IndiAllSkyDbPanoramaVideoTable.query\
                .join(IndiAllSkyDbPanoramaVideoTable.camera)\
                .filter(
                    and_(
                        IndiAllSkyDbCameraTable.id == camera.id,
                        IndiAllSkyDbPanoramaVideoTable.dayDate == day_date,
                        IndiAllSkyDbPanoramaVideoTable.night == night,
                    )
                )\
                .first()


            if video_entry:
                video_entry.deleteAsset()
                db.session.delete(video_entry)
                db.session.commit()

            if keogram_entry:
                keogram_entry.deleteAsset()
                db.session.delete(keogram_entry)
                db.session.commit()

            if startrail_entry:
                startrail_entry.deleteAsset()
                db.session.delete(startrail_entry)
                db.session.commit()

            if startrail_video_entry:
                startrail_video_entry.deleteAsset()
                db.session.delete(startrail_video_entry)
                db.session.commit()

            if panorama_video_entry:
                panorama_video_entry.deleteAsset()
                db.session.delete(panorama_video_entry)
                db.session.commit()


            message = {
                'success-message' : 'Files deleted',
            }

            return jsonify(message)


        elif action == 'delete_video':
            video_entry = IndiAllSkyDbVideoTable.query\
                .join(IndiAllSkyDbVideoTable.camera)\
                .filter(
                    and_(
                        IndiAllSkyDbCameraTable.id == camera.id,
                        IndiAllSkyDbVideoTable.dayDate == day_date,
                        IndiAllSkyDbVideoTable.night == night,
                    )
                )\
                .first()

            if video_entry:
                video_entry.deleteAsset()
                db.session.delete(video_entry)
                db.session.commit()


            message = {
                'success-message' : 'Timelapse deleted',
            }

            return jsonify(message)

        elif action == 'delete_panorama_video':
            panorama_video_entry = IndiAllSkyDbPanoramaVideoTable.query\
                .join(IndiAllSkyDbPanoramaVideoTable.camera)\
                .filter(
                    and_(
                        IndiAllSkyDbCameraTable.id == camera.id,
                        IndiAllSkyDbPanoramaVideoTable.dayDate == day_date,
                        IndiAllSkyDbPanoramaVideoTable.night == night,
                    )
                )\
                .first()

            if panorama_video_entry:
                panorama_video_entry.deleteAsset()
                db.session.delete(panorama_video_entry)
                db.session.commit()


            message = {
                'success-message' : 'Panorama Timelapse deleted',
            }

            return jsonify(message)

        if action == 'delete_k_st':
            keogram_entry = IndiAllSkyDbKeogramTable.query\
                .join(IndiAllSkyDbKeogramTable.camera)\
                .filter(
                    and_(
                        IndiAllSkyDbCameraTable.id == camera.id,
                        IndiAllSkyDbKeogramTable.dayDate == day_date,
                        IndiAllSkyDbKeogramTable.night == night,
                    )
                )\
                .first()

            startrail_entry = IndiAllSkyDbStarTrailsTable.query\
                .join(IndiAllSkyDbStarTrailsTable.camera)\
                .filter(
                    and_(
                        IndiAllSkyDbCameraTable.id == camera.id,
                        IndiAllSkyDbStarTrailsTable.dayDate == day_date,
                        IndiAllSkyDbStarTrailsTable.night == night,
                    )
                )\
                .first()

            startrail_video_entry = IndiAllSkyDbStarTrailsVideoTable.query\
                .join(IndiAllSkyDbStarTrailsVideoTable.camera)\
                .filter(
                    and_(
                        IndiAllSkyDbCameraTable.id == camera.id,
                        IndiAllSkyDbStarTrailsVideoTable.dayDate == day_date,
                        IndiAllSkyDbStarTrailsVideoTable.night == night,
                    )
                )\
                .first()


            if keogram_entry:
                keogram_entry.deleteAsset()
                db.session.delete(keogram_entry)
                db.session.commit()

            if startrail_entry:
                startrail_entry.deleteAsset()
                db.session.delete(startrail_entry)
                db.session.commit()

            if startrail_video_entry:
                startrail_video_entry.deleteAsset()
                db.session.delete(startrail_video_entry)
                db.session.commit()


            message = {
                'success-message' : 'Keogram/Star Trails deleted',
            }

            return jsonify(message)


        elif action == 'generate_video_k_st':
            timespec = day_date.strftime('%Y%m%d')

            if night:
                timeofday_str = 'night'
            else:
                timeofday_str = 'day'


            app.logger.warning('Generating %s time timelapse for %s camera %d', timeofday_str, timespec, camera.id)

            jobdata_video = {
                'action' : 'generateVideo',
                'kwargs' : {
                    'timespec'    : timespec,
                    'night'       : night,
                    'camera_id'   : camera.id,
                },
            }

            jobdata_kst = {
                'action' : 'generateKeogramStarTrails',
                'kwargs' : {
                    'timespec'    : timespec,
                    'night'       : night,
                    'camera_id'   : camera.id,
                },
            }


            task_video = IndiAllSkyDbTaskQueueTable(
                queue=TaskQueueQueue.VIDEO,
                state=TaskQueueState.MANUAL,
                priority=100,
                data=jobdata_video,
            )
            task_kst = IndiAllSkyDbTaskQueueTable(
                queue=TaskQueueQueue.VIDEO,
                state=TaskQueueState.MANUAL,
                priority=100,
                data=jobdata_kst,
            )


            db.session.add(task_kst)  # keogram/st first
            db.session.add(task_video)


            if self.indi_allsky_config.get('FISH2PANO', {}).get('ENABLE'):
                jobdata_panorama_video = {
                    'action' : 'generatePanoramaVideo',
                    'kwargs' : {
                        'timespec'    : timespec,
                        'night'       : night,
                        'camera_id'   : camera.id,
                    },
                }

                task_panorama_video = IndiAllSkyDbTaskQueueTable(
                    queue=TaskQueueQueue.VIDEO,
                    state=TaskQueueState.MANUAL,
                    priority=100,
                    data=jobdata_panorama_video,
                )

                db.session.add(task_panorama_video)


            db.session.commit()

            message = {
                'success-message' : 'Job submitted',
            }

            return jsonify(message)


        elif action == 'generate_video':
            timespec = day_date.strftime('%Y%m%d')

            if night:
                timeofday_str = 'night'
            else:
                timeofday_str = 'day'


            app.logger.warning('Generating %s time timelapse for %s camera %d', timeofday_str, timespec, camera.id)

            jobdata = {
                'action' : 'generateVideo',
                'kwargs' : {
                    'timespec'    : timespec,
                    'night'       : night,
                    'camera_id'   : camera.id,
                },
            }

            task = IndiAllSkyDbTaskQueueTable(
                queue=TaskQueueQueue.VIDEO,
                state=TaskQueueState.MANUAL,
                priority=100,
                data=jobdata,
            )
            db.session.add(task)
            db.session.commit()

            message = {
                'success-message' : 'Job submitted',
            }

            return jsonify(message)

        elif action == 'generate_panorama_video':
            if not self.indi_allsky_config.get('FISH2PANO', {}).get('ENABLE'):
                message = {
                    'success-message' : 'Panoramas disabled',
                }

                return jsonify(message)


            timespec = day_date.strftime('%Y%m%d')

            if night:
                timeofday_str = 'night'
            else:
                timeofday_str = 'day'


            app.logger.warning('Generating %s time panorama timelapse for %s camera %d', timeofday_str, timespec, camera.id)

            jobdata = {
                'action' : 'generatePanoramaVideo',
                'kwargs' : {
                    'timespec'    : timespec,
                    'night'       : night,
                    'camera_id'   : camera.id,
                },
            }

            task = IndiAllSkyDbTaskQueueTable(
                queue=TaskQueueQueue.VIDEO,
                state=TaskQueueState.MANUAL,
                priority=100,
                data=jobdata,
            )
            db.session.add(task)
            db.session.commit()

            message = {
                'success-message' : 'Job submitted',
            }

            return jsonify(message)

        elif action == 'generate_k_st':
            timespec = day_date.strftime('%Y%m%d')

            if night:
                timeofday_str = 'night'
            else:
                timeofday_str = 'day'


            app.logger.warning('Generating %s time timelapse for %s camera %d', timeofday_str, timespec, camera.id)

            jobdata = {
                'action' : 'generateKeogramStarTrails',
                'kwargs' : {
                    'timespec'    : timespec,
                    'night'       : night,
                    'camera_id'   : camera.id,
                },
            }

            task = IndiAllSkyDbTaskQueueTable(
                queue=TaskQueueQueue.VIDEO,
                state=TaskQueueState.MANUAL,
                priority=100,
                data=jobdata,
            )
            db.session.add(task)
            db.session.commit()

            message = {
                'success-message' : 'Job submitted',
            }

            return jsonify(message)

        elif action == 'upload_endofnight':
            app.logger.warning('Uploading end of night data for camera %d', camera.id)

            jobdata = {
                'action' : 'uploadAllskyEndOfNight',
                'kwargs' : {
                    'night'     : True,
                    'camera_id' : camera.id,
                },
            }

            task = IndiAllSkyDbTaskQueueTable(
                queue=TaskQueueQueue.VIDEO,
                state=TaskQueueState.MANUAL,
                priority=100,
                data=jobdata,
            )
            db.session.add(task)
            db.session.commit()

            message = {
                'success-message' : 'Job submitted',
            }

            return jsonify(message)

        if action == 'delete_images':
            image_list = IndiAllSkyDbImageTable.query\
                .join(IndiAllSkyDbImageTable.camera)\
                .filter(
                    and_(
                        IndiAllSkyDbCameraTable.id == camera.id,
                        IndiAllSkyDbImageTable.dayDate == day_date,
                        IndiAllSkyDbImageTable.night == night,
                    )
                )\
                .order_by(IndiAllSkyDbImageTable.createDate.asc())

            panorama_list = IndiAllSkyDbPanoramaImageTable.query\
                .join(IndiAllSkyDbPanoramaImageTable.camera)\
                .filter(
                    and_(
                        IndiAllSkyDbCameraTable.id == camera.id,
                        IndiAllSkyDbPanoramaImageTable.dayDate == day_date,
                        IndiAllSkyDbPanoramaImageTable.night == night,
                    )
                )\
                .order_by(IndiAllSkyDbPanoramaImageTable.createDate.asc())


            ### Getting IDs first then deleting each file is faster than deleting all files with
            ### thumbnails with a single query.  Deleting associated thumbnails causes sqlalchemy
            ### to recache after every delete which cause a 1-5 second lag for each delete

            image_id_list = list()
            for entry in image_list:
                image_id_list.append(entry.id)

            panorama_image_id_list = list()
            for entry in panorama_list:
                panorama_image_id_list.append(entry.id)


            delete_count = self._deleteAssets(IndiAllSkyDbImageTable, image_id_list)
            delete_count += self._deleteAssets(IndiAllSkyDbPanoramaImageTable, panorama_image_id_list)


            message = {
                'success-message' : '{0:d} images deleted'.format(delete_count),
            }
            return jsonify(message)
        else:
            # this should never happen
            message = {
                'failure-message' : 'Invalid'
            }
            return jsonify(message), 400


    def _deleteAssets(self, table, entry_id_list):
        delete_count = 0
        for entry_id in entry_id_list:
            entry = table.query\
                .filter(table.id == entry_id)\
                .one()

            app.logger.info('Removing old %s entry: %s', entry.__class__.__name__, entry.filename)

            try:
                entry.deleteAsset()
            except OSError as e:
                app.logger.error('Cannot remove file: %s', str(e))
                continue

            db.session.delete(entry)
            db.session.commit()

            delete_count += 1

        return delete_count


class FocusView(TemplateView):
    page_title = 'Focus'
    decorators = [login_required]

    def get_context(self):
        context = super(FocusView, self).get_context()

        context['form_focus'] = IndiAllskyFocusForm()

        context['focuser_device'] = int(bool(self.indi_allsky_config.get('FOCUSER', {}).get('CLASSNAME')))
        context['form_focuscontroller'] = IndiAllskyFocusControllerForm()

        return context


class JsonFocusView(JsonView):
    decorators = [login_required]

    def __init__(self, **kwargs):
        super(JsonFocusView, self).__init__(**kwargs)


    def dispatch_request(self):
        import cv2
        from ..stars import IndiAllSkyStars

        zoom = int(request.args.get('zoom', 2))
        x_offset = int(request.args.get('x_offset', 0))
        y_offset = int(request.args.get('y_offset', 0))


        sqm_mask = {
            1 : None,  # assume bin 1
        }

        stars_detect_o = IndiAllSkyStars(self.indi_allsky_config, mask=sqm_mask)


        json_data = dict()
        json_data['focus_mode'] = self.indi_allsky_config.get('FOCUS_MODE', False)

        image_dir = Path(self.indi_allsky_config['IMAGE_FOLDER']).absolute()
        latest_image_p = image_dir.joinpath('latest.{0:s}'.format(self.indi_allsky_config['IMAGE_FILE_TYPE']))
        #latest_image_p = image_dir.joinpath('focus.fit')
        #latest_image_p = image_dir.joinpath('focus.png')


        if not latest_image_p.exists():
            app.logger.error('Latest image does not exist')
            return jsonify({}), 400


        #focus_start = time.time()

        if latest_image_p.suffix in ('.jpg', '.jpeg'):
            import simplejpeg

            try:
                with io.open(str(latest_image_p), 'rb') as f_img:
                    image_data = simplejpeg.decode_jpeg(f_img.read(), colorspace='BGR')
            except ValueError:
                app.logger.error('Unable to read %s', latest_image_p)
                return jsonify({}), 400

        elif latest_image_p.suffix in ('.png',):
            # opencv is faster than Pillow with PNG
            # PNG encoding is very slow on Raspberry Pi
            image_data = cv2.imread(str(latest_image_p), cv2.IMREAD_COLOR)

            if isinstance(image_data, type(None)):
                app.logger.error('Unable to read %s', latest_image_p)
                return jsonify({}), 400
        elif latest_image_p.suffix in ('.fit', '.fits'):
            import numpy
            from astropy.io import fits

            try:
                hdulist = fits.open(latest_image_p)
            except OSError:
                app.logger.error('Unable to read %s', latest_image_p)
                return jsonify({}), 400

            # data should be RGB
            image_data = numpy.swapaxes(hdulist[0].data, 0, 2)
            image_data = numpy.swapaxes(image_data, 0, 1)
            image_data = cv2.cvtColor(image_data, cv2.COLOR_RGB2BGR)

        else:
            # Pillow supports remaining image types
            import numpy
            import PIL
            from PIL import Image

            try:
                with Image.open(str(latest_image_p)) as img_pil:
                    image_data = cv2.cvtColor(numpy.array(img_pil), cv2.COLOR_RGB2BGR)
            except PIL.UnidentifiedImageError:
                app.logger.error('Unable to read %s', latest_image_p)
                return jsonify({}), 400


        stars = stars_detect_o.detectObjects(image_data, 1)  # assume bin 1


        image_height, image_width = image_data.shape[:2]

        ### get ROI based on zoom
        x1 = int((image_width / 2) - (image_width / zoom) + x_offset)
        y1 = int((image_height / 2) - (image_height / zoom) - y_offset)
        x2 = int((image_width / 2) + (image_width / zoom) + x_offset)
        y2 = int((image_height / 2) + (image_height / zoom) - y_offset)

        image_roi = image_data[
            y1:y2,
            x1:x2,
        ]


        ### OpenCV
        _, json_image = cv2.imencode('.jpg', image_roi, [cv2.IMWRITE_JPEG_QUALITY, 90])
        #_, json_image = cv2.imencode('.png', image_roi, [cv2.IMWRITE_PNG_COMPRESSION, 5])
        json_image_buffer = io.BytesIO(json_image.tobytes())


        ### pillow
        #from PIL import Image
        #json_image_buffer = io.BytesIO()
        #img = Image.fromarray(cv2.cvtColor(image_roi, cv2.COLOR_BGR2RGB))
        #img.save(json_image_buffer, format='JPEG', quality=90)
        #img.save(json_image_buffer, format='PNG', compress_level=5)


        json_image_b64 = base64.b64encode(json_image_buffer.getvalue())

        json_data['image_b64'] = json_image_b64.decode('utf-8')


        ### Blur detection
        #vl_start = time.time()

        ### determine variance of laplacian
        blur_score = cv2.Laplacian(image_roi, cv2.CV_32F).var()
        json_data['blur_score'] = float(blur_score)
        json_data['star_count'] = len(stars)

        #vl_elapsed_s = time.time() - vl_start
        #app.logger.info('Variance of laplacien in %0.4f s', vl_elapsed_s)

        #focus_elapsed_s = time.time() - focus_start
        #app.logger.info('Focus processing in %0.4f s', focus_elapsed_s)

        return jsonify(json_data)


class AjaxFocusControllerView(BaseView):
    methods = ['POST']
    decorators = [login_required]


    def __init__(self, **kwargs):
        super(AjaxFocusControllerView, self).__init__(**kwargs)


    def dispatch_request(self):
        from ..focuser import IndiAllSkyFocuserInterface
        from ..devices.exceptions import DeviceControlException


        if not current_user.is_admin:
            json_data = {
                'focuser_error' : ['User does not have permission to adjust focus'],
            }
            return jsonify(json_data), 400


        form_focuscontroller = IndiAllskyFocusControllerForm(data=request.json)


        if not form_focuscontroller.validate():
            form_errors = form_focuscontroller.errors  # this must be a property
            return jsonify(form_errors), 400


        if not self.verify_admin_network():
            json_data = {
                'focuser_error' : ['Request not from admin network (flask.json)'],
            }
            return jsonify(json_data), 400


        direction = str(request.json['DIRECTION'])
        degrees = int(request.json['STEP_DEGREES'])

        app.logger.info('Focusing: {0:s}', direction)

        try:
            focuser_interface = IndiAllSkyFocuserInterface(self.indi_allsky_config)
        except SystemError as e:
            json_data = {
                'focuser_error' : ['Error initializing focuser: {0:s}'.format(str(e))],
            }
            return jsonify(json_data), 400
        except ValueError as e:
            json_data = {
                'focuser_error' : ['Error initializing focuser: {0:s}'.format(str(e))],
            }
            return jsonify(json_data), 400
        except DeviceControlException as e:
            json_data = {
                'focuser_error' : ['Error initializing focuser: {0:s}'.format(str(e))],
            }
            return jsonify(json_data), 400


        try:
            steps_offset = focuser_interface.move(direction, degrees)
        except DeviceControlException as e:
            json_data = {
                'focuser_error' : ['Error moving focuser: {0:s}'.format(str(e))],
            }
            return jsonify(json_data), 400


        # cleanup
        focuser_interface.deinit()


        r = {
            'steps' : steps_offset,
        }

        return jsonify(r)


class ManualGpioView(TemplateView):
    decorators = [login_required]
    page_title = 'Manual GPIO'


    def get_context(self):
        context = super(ManualGpioView, self).get_context()

        from ..devices import generic as indi_allsky_gpio
        from ..devices.exceptions import DeviceControlException


        gpio_class_str = self.indi_allsky_config.get('MANUAL_GPIO', {}).get('A_CLASSNAME')
        pin_1_str = self.indi_allsky_config.get('MANUAL_GPIO', {}).get('A_PIN_1', '-1')
        pin_2_str = self.indi_allsky_config.get('MANUAL_GPIO', {}).get('A_PIN_2', '-1')
        pin_3_str = self.indi_allsky_config.get('MANUAL_GPIO', {}).get('A_PIN_3', '-1')


        context['pin_names'] = [pin_1_str, pin_2_str, pin_3_str]

        if not gpio_class_str:
            context['gpio_class'] = ''
            context['pin_states'] = [-1, -1, -1]

            return context


        try:
            gpio_class = getattr(indi_allsky_gpio, gpio_class_str)
        except AttributeError:
            context['gpio_class'] = ''
            context['pin_states'] = [-1, -1, -1]

            return context


        pin_states = [None, None, None]

        try:
            pin_1 = gpio_class(self.indi_allsky_config, pin_1_name=pin_1_str)
            pin_states[0] = int(pin_1.state)
            #pin_1.deinit()  # deinit returns pin to default state
        except DeviceControlException:
            pin_states[0] = -1


        try:
            pin_2 = gpio_class(self.indi_allsky_config, pin_1_name=pin_2_str)
            pin_states[1] = int(pin_2.state)
            #pin_2.deinit()  # deinit returns pin to default state
        except DeviceControlException:
            pin_states[1] = -1


        try:
            pin_3 = gpio_class(self.indi_allsky_config, pin_1_name=pin_3_str)
            pin_states[2] = int(pin_3.state)
            #pin_3.deinit()  # deinit returns pin to default state
        except DeviceControlException:
            pin_states[2] = -1


        context['gpio_class'] = gpio_class_str
        context['pin_states'] = pin_states

        return context


class AjaxManualGpioView(BaseView):
    methods = ['POST']
    decorators = [login_required]

    def dispatch_request(self):
        if not app.config['LOGIN_DISABLED']:
            if not current_user.is_admin:
                message = {
                    'failure-message' : 'User is not an admin',
                }
                return jsonify({}), 400


        from ..devices import generic as indi_allsky_gpio


        pin_id = int(request.json['PIN_ID'])
        new_pin_state = request.json['NEW_PIN_STATE']


        gpio_class_str = self.indi_allsky_config.get('MANUAL_GPIO', {}).get('A_CLASSNAME')
        if not gpio_class_str:
            message = {
                'failure-message' : 'Manual GPIO not configured',
            }
            return jsonify(message), 400

        try:
            gpio_class = getattr(indi_allsky_gpio, gpio_class_str)
        except AttributeError:
            message = {
                'failure-message' : 'Invalid GPIO class',
            }
            return jsonify(), 400


        pin_str = self.indi_allsky_config.get('MANUAL_GPIO', {}).get('A_PIN_{0:d}'.format(pin_id))
        if not pin_str:
            message = {
                'failure-message' : 'Unknown pin'
            }
            return jsonify({}), 400


        pin = gpio_class(self.indi_allsky_config, pin_1_name=pin_str)
        pin.state = new_pin_state

        time.sleep(0.5)

        message = {
            'success-message' : 'Pin configured',
            'pin_name' : pin_str,
            'pin_id' : pin_id,
            'pin_state' : pin.state,
        }


        #pin.deinit()  # deinit returns pin to default state

        return jsonify(message)


class ImageProcessingView(TemplateView):
    page_title = 'Image Processing'
    decorators = [login_required]

    def get_context(self):
        context = super(ImageProcessingView, self).get_context()

        fits_id = int(request.args.get('id', 0))
        frame_type = str(request.args.get('type', 'light'))


        if frame_type == 'dark':
            # always have to request a specific dark ID
            pass
        elif frame_type == 'bpm':
            # always have to request a specific bpm ID
            pass
        else:
            # assume light frame
            if not fits_id:
                # just pick the last fits file is none specified
                fits_entry = IndiAllSkyDbFitsImageTable.query\
                    .join(IndiAllSkyDbFitsImageTable.camera)\
                    .filter(IndiAllSkyDbCameraTable.id == self.camera.id)\
                    .order_by(IndiAllSkyDbFitsImageTable.createDate.desc())\
                    .first()

                if fits_entry:
                    fits_id = fits_entry.id
                else:
                    fits_id = 0  # will not exist


        form_data = {
            'CAMERA_ID'                      : self.camera.id,
            'FRAME_TYPE'                     : frame_type,
            'FITS_ID'                        : fits_id,
            'LENS_IMAGE_CIRCLE'              : self.indi_allsky_config.get('LENS_IMAGE_CIRCLE', 3000),
            'LENS_OFFSET_X'                  : self.indi_allsky_config.get('LENS_OFFSET_X', 0),
            'LENS_OFFSET_Y'                  : self.indi_allsky_config.get('LENS_OFFSET_Y', 0),
            'LENS_AZIMUTH'                   : self.indi_allsky_config.get('LENS_AZIMUTH', 0.0),
            'CCD_BIT_DEPTH'                  : str(self.indi_allsky_config.get('CCD_BIT_DEPTH', 0)),  # string in form, int in config
            'NIGHT_CONTRAST_ENHANCE'         : self.indi_allsky_config.get('NIGHT_CONTRAST_ENHANCE', False),
            'CONTRAST_ENHANCE_16BIT'         : self.indi_allsky_config.get('CONTRAST_ENHANCE_16BIT', False),
            'CLAHE_CLIPLIMIT'                : self.indi_allsky_config.get('CLAHE_CLIPLIMIT', 3.0),
            'CLAHE_GRIDSIZE'                 : self.indi_allsky_config.get('CLAHE_GRIDSIZE', 8),
            'IMAGE_STRETCH__CLASSNAME'       : self.indi_allsky_config.get('IMAGE_STRETCH', {}).get('CLASSNAME', ''),
            'IMAGE_STRETCH__MODE1_GAMMA'     : self.indi_allsky_config.get('IMAGE_STRETCH', {}).get('MODE1_GAMMA', 3.0),
            'IMAGE_STRETCH__MODE1_STDDEVS'   : self.indi_allsky_config.get('IMAGE_STRETCH', {}).get('MODE1_STDDEVS', 2.25),
            'IMAGE_STRETCH__MODE2_SHADOWS'   : self.indi_allsky_config.get('IMAGE_STRETCH', {}).get('MODE2_SHADOWS', 0.0),
            'IMAGE_STRETCH__MODE2_MIDTONES'  : self.indi_allsky_config.get('IMAGE_STRETCH', {}).get('MODE2_MIDTONES', 0.35),
            'IMAGE_STRETCH__MODE2_HIGHLIGHTS': self.indi_allsky_config.get('IMAGE_STRETCH', {}).get('MODE2_HIGHLIGHTS', 1.0),
            'IMAGE_STRETCH__MODE3_BLACK_CLIP': self.indi_allsky_config.get('IMAGE_STRETCH', {}).get('MODE3_BLACK_CLIP', -2.8),
            'IMAGE_STRETCH__MODE3_SHADOWS'   : self.indi_allsky_config.get('IMAGE_STRETCH', {}).get('MODE3_SHADOWS', 0.0),
            'IMAGE_STRETCH__MODE3_MIDTONES'  : self.indi_allsky_config.get('IMAGE_STRETCH', {}).get('MODE3_MIDTONES', 0.25),
            'IMAGE_STRETCH__MODE3_HIGHLIGHTS': self.indi_allsky_config.get('IMAGE_STRETCH', {}).get('MODE3_HIGHLIGHTS', 1.0),
            'CFA_PATTERN'                    : self.indi_allsky_config.get('CFA_PATTERN', ''),
            'SCNR_ALGORITHM'                 : self.indi_allsky_config.get('SCNR_ALGORITHM', ''),
            'SCNR_MTF_MIDTONES'              : self.indi_allsky_config.get('SCNR_MTF_MIDTONES', 0.65),
            'IMAGE_DENOISE'                  : self.indi_allsky_config.get('IMAGE_DENOISE', ''),
            'IMAGE_DENOISE_STRENGTH'         : self.indi_allsky_config.get('IMAGE_DENOISE_STRENGTH', 3),
            'BILATERAL_SIGMA_COLOR'          : self.indi_allsky_config.get('BILATERAL_SIGMA_COLOR', 20),
            'BILATERAL_SIGMA_SPACE'          : self.indi_allsky_config.get('BILATERAL_SIGMA_SPACE', 35),
            'WBR_FACTOR'                     : self.indi_allsky_config.get('WBR_FACTOR', 1.0),
            'WBG_FACTOR'                     : self.indi_allsky_config.get('WBG_FACTOR', 1.0),
            'WBB_FACTOR'                     : self.indi_allsky_config.get('WBB_FACTOR', 1.0),
            'AUTO_WB'                        : self.indi_allsky_config.get('AUTO_WB', False),
            'WBR_MTF_MIDTONES'               : self.indi_allsky_config.get('WBR_MTF_MIDTONES', 0.5),
            'WBG_MTF_MIDTONES'               : self.indi_allsky_config.get('WBG_MTF_MIDTONES', 0.5),
            'WBB_MTF_MIDTONES'               : self.indi_allsky_config.get('WBB_MTF_MIDTONES', 0.5),
            'SATURATION_FACTOR'              : self.indi_allsky_config.get('SATURATION_FACTOR', 1.0),
            'GAMMA_CORRECTION'               : self.indi_allsky_config.get('GAMMA_CORRECTION', 1.0),
            'SHARPEN_AMOUNT'                 : self.indi_allsky_config.get('SHARPEN_AMOUNT', 0.0),
            'IMAGE_ROTATE'                   : self.indi_allsky_config.get('IMAGE_ROTATE', ''),
            'IMAGE_ROTATE_ANGLE'             : self.indi_allsky_config.get('IMAGE_ROTATE_ANGLE', 0),
            'IMAGE_FLIP_V'                   : self.indi_allsky_config.get('IMAGE_FLIP_V', True),
            'IMAGE_FLIP_H'                   : self.indi_allsky_config.get('IMAGE_FLIP_H', True),
            'IMAGE_COLORMAP'                 : '',
            'DETECT_MASK'                    : self.indi_allsky_config.get('DETECT_MASK', ''),
            'SQM_FOV_DIV'                    : str(self.indi_allsky_config.get('SQM_FOV_DIV', 4)),  # string in form, int in config
            'IMAGE_STACK_METHOD'             : self.indi_allsky_config.get('IMAGE_STACK_METHOD', 'maximum'),
            'IMAGE_STACK_COUNT'              : str(self.indi_allsky_config.get('IMAGE_STACK_COUNT', 1)),  # string in form, int in config
            'IMAGE_STACK_ALIGN'              : self.indi_allsky_config.get('IMAGE_STACK_ALIGN', False),
            'IMAGE_ALIGN_DETECTSIGMA'        : self.indi_allsky_config.get('IMAGE_ALIGN_DETECTSIGMA', 5),
            'IMAGE_ALIGN_POINTS'             : self.indi_allsky_config.get('IMAGE_ALIGN_POINTS', 50),
            'IMAGE_ALIGN_SOURCEMINAREA'      : self.indi_allsky_config.get('IMAGE_ALIGN_SOURCEMINAREA', 10),
            'FISH2PANO__ENABLE'              : False,
            'FISH2PANO__DIAMETER'            : self.indi_allsky_config.get('FISH2PANO', {}).get('DIAMETER', 3000),
            'FISH2PANO__ROTATE_ANGLE'        : self.indi_allsky_config.get('FISH2PANO', {}).get('ROTATE_ANGLE', 0),
            'FISH2PANO__SCALE'               : self.indi_allsky_config.get('FISH2PANO', {}).get('SCALE', 0.3),
            'FISH2PANO__FLIP_H'              : self.indi_allsky_config.get('FISH2PANO', {}).get('FLIP_H', False),
            'FISH2PANO__ENABLE_CARDINAL_DIRS': self.indi_allsky_config.get('FISH2PANO', {}).get('ENABLE_CARDINAL_DIRS', True),
            'FISH2PANO__DIRS_OFFSET_BOTTOM'  : self.indi_allsky_config.get('FISH2PANO', {}).get('DIRS_OFFSET_BOTTOM', 25),
            'FISH2PANO__OPENCV_FONT_SCALE'   : self.indi_allsky_config.get('FISH2PANO', {}).get('OPENCV_FONT_SCALE', 0.8),
            'FISH2PANO__PIL_FONT_SIZE'       : self.indi_allsky_config.get('FISH2PANO', {}).get('PIL_FONT_SIZE', 30),
            'PROCESSING_SPLIT_SCREEN'        : False,
            'IMAGE_CALIBRATE_DARK'           : False,  # darks are almost always already applied
            'IMAGE_CALIBRATE_BPM'            : False,
            'IMAGE_CALIBRATE_FIX_HOLES'      : self.indi_allsky_config.get('IMAGE_CALIBRATE_FIX_HOLES', False),
            'IMAGE_CALIBRATE_HOLE_THOLD'     : self.indi_allsky_config.get('IMAGE_CALIBRATE_HOLE_THOLD', 30),
            'IMAGE_CALIBRATE_MANUAL_OFFSET'  : self.indi_allsky_config.get('IMAGE_CALIBRATE_MANUAL_OFFSET', 0),
            'IMAGE_LABEL_TEMPLATE'           : self.indi_allsky_config.get('IMAGE_LABEL_TEMPLATE', ''),
            'IMAGE_EXTRA_TEXT'               : self.indi_allsky_config.get('IMAGE_EXTRA_TEXT'),
            'IMAGE_LABEL_SYSTEM'             : '',
            'TEXT_PROPERTIES__FONT_FACE'     : self.indi_allsky_config.get('TEXT_PROPERTIES', {}).get('FONT_FACE', 'FONT_HERSHEY_SIMPLEX'),
            'TEXT_PROPERTIES__FONT_SCALE'    : self.indi_allsky_config.get('TEXT_PROPERTIES', {}).get('FONT_SCALE', 0.8),
            'TEXT_PROPERTIES__FONT_THICKNESS': self.indi_allsky_config.get('TEXT_PROPERTIES', {}).get('FONT_THICKNESS', 1),
            'TEXT_PROPERTIES__FONT_OUTLINE'  : self.indi_allsky_config.get('TEXT_PROPERTIES', {}).get('FONT_OUTLINE', True),
            'TEXT_PROPERTIES__FONT_HEIGHT'   : self.indi_allsky_config.get('TEXT_PROPERTIES', {}).get('FONT_HEIGHT', 30),
            'TEXT_PROPERTIES__FONT_X'        : self.indi_allsky_config.get('TEXT_PROPERTIES', {}).get('FONT_X', 15),
            'TEXT_PROPERTIES__FONT_Y'        : self.indi_allsky_config.get('TEXT_PROPERTIES', {}).get('FONT_Y', 30),
            'TEXT_PROPERTIES__PIL_FONT_FILE' : self.indi_allsky_config.get('TEXT_PROPERTIES', {}).get('PIL_FONT_FILE', 'fonts-freefont-ttf/FreeSans.ttf'),
            'TEXT_PROPERTIES__PIL_FONT_CUSTOM': self.indi_allsky_config.get('TEXT_PROPERTIES', {}).get('PIL_FONT_CUSTOM', ''),
            'TEXT_PROPERTIES__PIL_FONT_SIZE' : self.indi_allsky_config.get('TEXT_PROPERTIES', {}).get('PIL_FONT_SIZE', 30),
            'CARDINAL_DIRS__ENABLE'          : False,
            'CARDINAL_DIRS__SWAP_NS'         : self.indi_allsky_config.get('CARDINAL_DIRS', {}).get('SWAP_NS', False),
            'CARDINAL_DIRS__SWAP_EW'         : self.indi_allsky_config.get('CARDINAL_DIRS', {}).get('SWAP_EW', False),
            'CARDINAL_DIRS__CHAR_NORTH'      : self.indi_allsky_config.get('CARDINAL_DIRS', {}).get('CHAR_NORTH', 'N'),
            'CARDINAL_DIRS__CHAR_EAST'       : self.indi_allsky_config.get('CARDINAL_DIRS', {}).get('CHAR_EAST', 'E'),
            'CARDINAL_DIRS__CHAR_WEST'       : self.indi_allsky_config.get('CARDINAL_DIRS', {}).get('CHAR_WEST', 'W'),
            'CARDINAL_DIRS__CHAR_SOUTH'      : self.indi_allsky_config.get('CARDINAL_DIRS', {}).get('CHAR_SOUTH', 'S'),
            'CARDINAL_DIRS__DIAMETER'        : self.indi_allsky_config.get('CARDINAL_DIRS', {}).get('DIAMETER', 3000),
            'CARDINAL_DIRS__OFFSET_X'        : self.indi_allsky_config.get('CARDINAL_DIRS', {}).get('OFFSET_X', 0),
            'CARDINAL_DIRS__OFFSET_Y'        : self.indi_allsky_config.get('CARDINAL_DIRS', {}).get('OFFSET_Y', 0),
            'CARDINAL_DIRS__OFFSET_TOP'      : self.indi_allsky_config.get('CARDINAL_DIRS', {}).get('OFFSET_TOP', 15),
            'CARDINAL_DIRS__OFFSET_LEFT'     : self.indi_allsky_config.get('CARDINAL_DIRS', {}).get('OFFSET_LEFT', 15),
            'CARDINAL_DIRS__OFFSET_RIGHT'    : self.indi_allsky_config.get('CARDINAL_DIRS', {}).get('OFFSET_RIGHT', 15),
            'CARDINAL_DIRS__OFFSET_BOTTOM'   : self.indi_allsky_config.get('CARDINAL_DIRS', {}).get('OFFSET_BOTTOM', 15),
            'CARDINAL_DIRS__OPENCV_FONT_SCALE' : self.indi_allsky_config.get('CARDINAL_DIRS', {}).get('OPENCV_FONT_SCALE', 0.5),
            'CARDINAL_DIRS__PIL_FONT_SIZE'   : self.indi_allsky_config.get('CARDINAL_DIRS', {}).get('PIL_FONT_SIZE', 20),
            'CARDINAL_DIRS__OUTLINE_CIRCLE'  : self.indi_allsky_config.get('CARDINAL_DIRS', {}).get('OUTLINE_CIRCLE', False),
            'IMAGE_CIRCLE_MASK__ENABLE'      : False,
            'IMAGE_CIRCLE_MASK__DIAMETER'    : self.indi_allsky_config.get('IMAGE_CIRCLE_MASK', {}).get('DIAMETER', 3000),
            'IMAGE_CIRCLE_MASK__OFFSET_X'    : self.indi_allsky_config.get('IMAGE_CIRCLE_MASK', {}).get('OFFSET_X', 0),
            'IMAGE_CIRCLE_MASK__OFFSET_Y'    : self.indi_allsky_config.get('IMAGE_CIRCLE_MASK', {}).get('OFFSET_Y', 0),
            'IMAGE_CIRCLE_MASK__BLUR'        : self.indi_allsky_config.get('IMAGE_CIRCLE_MASK', {}).get('BLUR', 35),
            'IMAGE_CIRCLE_MASK__OPACITY'     : self.indi_allsky_config.get('IMAGE_CIRCLE_MASK', {}).get('OPACITY', 100),
            'IMAGE_CIRCLE_MASK__OUTLINE'     : self.indi_allsky_config.get('IMAGE_CIRCLE_MASK', {}).get('OUTLINE', False),
            'IMAGE_CROP_IMAGE_CIRCLE'        : self.indi_allsky_config.get('IMAGE_CROP_IMAGE_CIRCLE', False),
            'MOON_OVERLAY__ENABLE'           : False,
            'MOON_OVERLAY__X'                : self.indi_allsky_config.get('MOON_OVERLAY', {}).get('X', -500),
            'MOON_OVERLAY__Y'                : self.indi_allsky_config.get('MOON_OVERLAY', {}).get('Y', -200),
            'MOON_OVERLAY__SCALE'            : self.indi_allsky_config.get('MOON_OVERLAY', {}).get('SCALE', 0.5),
            'MOON_OVERLAY__DARK_SIDE_SCALE'  : self.indi_allsky_config.get('MOON_OVERLAY', {}).get('DARK_SIDE_SCALE', 0.4),
            'MOON_OVERLAY__FLIP_V'           : self.indi_allsky_config.get('MOON_OVERLAY', {}).get('FLIP_V', False),
            'MOON_OVERLAY__FLIP_H'           : self.indi_allsky_config.get('MOON_OVERLAY', {}).get('FLIP_H', False),
            'LIGHTGRAPH_OVERLAY__ENABLE'     : False,
            'LIGHTGRAPH_OVERLAY__GRAPH_HEIGHT' : self.indi_allsky_config.get('LIGHTGRAPH_OVERLAY', {}).get('GRAPH_HEIGHT', 30),
            'LIGHTGRAPH_OVERLAY__GRAPH_BORDER' : self.indi_allsky_config.get('LIGHTGRAPH_OVERLAY', {}).get('GRAPH_BORDER', 3),
            'LIGHTGRAPH_OVERLAY__Y'          : self.indi_allsky_config.get('LIGHTGRAPH_OVERLAY', {}).get('Y', 10),
            'LIGHTGRAPH_OVERLAY__OFFSET_X'   : self.indi_allsky_config.get('LIGHTGRAPH_OVERLAY', {}).get('OFFSET_X', 0),
            'LIGHTGRAPH_OVERLAY__SCALE'      : self.indi_allsky_config.get('LIGHTGRAPH_OVERLAY', {}).get('SCALE', 1.0),
            'LIGHTGRAPH_OVERLAY__NOW_MARKER_SIZE' : self.indi_allsky_config.get('LIGHTGRAPH_OVERLAY', {}).get('NOW_MARKER_SIZE', 8),
            'LIGHTGRAPH_OVERLAY__OPACITY'    : self.indi_allsky_config.get('LIGHTGRAPH_OVERLAY', {}).get('OPACITY', 100),
            'LIGHTGRAPH_OVERLAY__PIL_FONT_SIZE' : self.indi_allsky_config.get('LIGHTGRAPH_OVERLAY', {}).get('PIL_FONT_SIZE', 20),
            'LIGHTGRAPH_OVERLAY__OPENCV_FONT_SCALE' : self.indi_allsky_config.get('LIGHTGRAPH_OVERLAY', {}).get('OPENCV_FONT_SCALE', 0.5),
            'LIGHTGRAPH_OVERLAY__LABEL'      : self.indi_allsky_config.get('LIGHTGRAPH_OVERLAY', {}).get('LABEL', True),
            'LIGHTGRAPH_OVERLAY__HOUR_LINES' : self.indi_allsky_config.get('LIGHTGRAPH_OVERLAY', {}).get('HOUR_LINES', True),
            'IMAGE_BORDER__TOP'              : self.indi_allsky_config.get('IMAGE_BORDER', {}).get('TOP', 0),
            'IMAGE_BORDER__LEFT'             : self.indi_allsky_config.get('IMAGE_BORDER', {}).get('LEFT', 0),
            'IMAGE_BORDER__RIGHT'            : self.indi_allsky_config.get('IMAGE_BORDER', {}).get('RIGHT', 0),
            'IMAGE_BORDER__BOTTOM'           : self.indi_allsky_config.get('IMAGE_BORDER', {}).get('BOTTOM', 0),
        }


        # SQM_ROI
        SQM_ROI = self.indi_allsky_config.get('SQM_ROI', [])
        if SQM_ROI is None:
            SQM_ROI = []
        elif isinstance(SQM_ROI, bool):
            SQM_ROI = []

        try:
            form_data['SQM_ROI_X1'] = SQM_ROI[0]
        except IndexError:
            form_data['SQM_ROI_X1'] = 0

        try:
            form_data['SQM_ROI_Y1'] = SQM_ROI[1]
        except IndexError:
            form_data['SQM_ROI_Y1'] = 0

        try:
            form_data['SQM_ROI_X2'] = SQM_ROI[2]
        except IndexError:
            form_data['SQM_ROI_X2'] = 0

        try:
            form_data['SQM_ROI_Y2'] = SQM_ROI[3]
        except IndexError:
            form_data['SQM_ROI_Y2'] = 0


        # Font color
        text_properties__font_color = self.indi_allsky_config.get('TEXT_PROPERTIES', {}).get('FONT_COLOR', [200, 200, 200])
        form_data['TEXT_PROPERTIES__FONT_COLOR'] = ','.join([str(x) for x in text_properties__font_color])

        # Cardinal directions color
        cardinal_dirs__font_color = self.indi_allsky_config.get('CARDINAL_DIRS', {}).get('FONT_COLOR', [200, 0, 0])
        form_data['CARDINAL_DIRS__FONT_COLOR'] = ','.join([str(x) for x in cardinal_dirs__font_color])

        # Border color
        image_border__color = self.indi_allsky_config.get('IMAGE_BORDER', {}).get('COLOR', [0, 0, 0])
        form_data['IMAGE_BORDER__COLOR'] = ','.join([str(x) for x in image_border__color])

        # Lightgraph colors
        lightgraph_overlay__day_color = self.indi_allsky_config.get('LIGHTGRAPH_OVERLAY', {}).get('DAY_COLOR', [150, 150, 150])
        form_data['LIGHTGRAPH_OVERLAY__DAY_COLOR'] = ','.join([str(x) for x in lightgraph_overlay__day_color])

        lightgraph_overlay__dusk_color = self.indi_allsky_config.get('LIGHTGRAPH_OVERLAY', {}).get('DUSK_COLOR', [200, 100, 60])
        form_data['LIGHTGRAPH_OVERLAY__DUSK_COLOR'] = ','.join([str(x) for x in lightgraph_overlay__dusk_color])

        lightgraph_overlay__night_color = self.indi_allsky_config.get('LIGHTGRAPH_OVERLAY', {}).get('NIGHT_COLOR', [30, 30, 30])
        form_data['LIGHTGRAPH_OVERLAY__NIGHT_COLOR'] = ','.join([str(x) for x in lightgraph_overlay__night_color])

        lightgraph_overlay__moonmode_color = self.indi_allsky_config.get('LIGHTGRAPH_OVERLAY', {}).get('MOONMODE_COLOR', [50, 50, 50])
        form_data['LIGHTGRAPH_OVERLAY__MOONMODE_COLOR'] = ','.join([str(x) for x in lightgraph_overlay__moonmode_color])

        lightgraph_overlay__hour_color = self.indi_allsky_config.get('LIGHTGRAPH_OVERLAY', {}).get('HOUR_COLOR', [100, 15, 15])
        form_data['LIGHTGRAPH_OVERLAY__HOUR_COLOR'] = ','.join([str(x) for x in lightgraph_overlay__hour_color])

        lightgraph_overlay__border_color = self.indi_allsky_config.get('LIGHTGRAPH_OVERLAY', {}).get('BORDER_COLOR', [1, 1, 1])
        form_data['LIGHTGRAPH_OVERLAY__BORDER_COLOR'] = ','.join([str(x) for x in lightgraph_overlay__border_color])

        lightgraph_overlay__now_color = self.indi_allsky_config.get('LIGHTGRAPH_OVERLAY', {}).get('NOW_COLOR', [120, 120, 200])
        form_data['LIGHTGRAPH_OVERLAY__NOW_COLOR'] = ','.join([str(x) for x in lightgraph_overlay__now_color])

        lightgraph_overlay__font_color = self.indi_allsky_config.get('LIGHTGRAPH_OVERLAY', {}).get('FONT_COLOR', [150, 150, 150])
        form_data['LIGHTGRAPH_OVERLAY__FONT_COLOR'] = ','.join([str(x) for x in lightgraph_overlay__font_color])


        context['form_image_processing'] = IndiAllskyImageProcessingForm(data=form_data)

        return context


class JsonImageProcessingView(JsonView):
    methods = ['POST']
    decorators = [login_required]

    def __init__(self, **kwargs):
        super(JsonImageProcessingView, self).__init__(**kwargs)


    def dispatch_request(self):
        import cv2
        from astropy.io import fits
        #from PIL import Image
        from multiprocessing import Array


        form_processing = IndiAllskyImageProcessingForm(data=request.json)
        if not form_processing.validate():
            form_errors = form_processing.errors  # this must be a property
            form_errors['form_global'] = ['Please fix the errors above']
            return jsonify(form_errors), 400


        disable_processing                  = bool(request.json['DISABLE_PROCESSING'])
        output_image_type                   = str(request.json['OUTPUT_IMAGE_TYPE'])
        camera_id                           = int(request.json['CAMERA_ID'])
        frame_type                          = str(request.json['FRAME_TYPE'])
        fits_id                             = int(request.json['FITS_ID'])

        self.cameraSetup(camera_id=camera_id)


        if frame_type == 'dark':
            table = IndiAllSkyDbDarkFrameTable
        elif frame_type == 'bpm':
            table = IndiAllSkyDbBadPixelMapTable
        else:
            table = IndiAllSkyDbFitsImageTable


        try:
            fits_entry = table.query\
                .join(table.camera)\
                .filter(
                    and_(
                        IndiAllSkyDbCameraTable.id == camera_id,
                        table.id == fits_id,
                    )
                )\
                .one()
        except NoResultFound:
            json_data = {
                'image_b64' : None,
                'processing_elapsed_s' : 0.0,
                'message' : 'No FITS images found',
            }
            return jsonify(json_data)



        filename_p = Path(fits_entry.getFilesystemPath())


        p_config = self.indi_allsky_config.copy()

        p_config['LENS_IMAGE_CIRCLE']                    = int(request.json['LENS_IMAGE_CIRCLE'])
        p_config['LENS_OFFSET_X']                        = int(request.json['LENS_OFFSET_X'])
        p_config['LENS_OFFSET_Y']                        = int(request.json['LENS_OFFSET_Y'])
        p_config['LENS_AZIMUTH']                         = float(request.json['LENS_AZIMUTH'])
        p_config['CCD_BIT_DEPTH']                        = int(request.json['CCD_BIT_DEPTH'])
        p_config['IMAGE_CALIBRATE_DARK']                 = bool(request.json['IMAGE_CALIBRATE_DARK'])
        p_config['IMAGE_CALIBRATE_BPM']                  = bool(request.json['IMAGE_CALIBRATE_BPM'])
        p_config['IMAGE_CALIBRATE_FIX_HOLES']            = bool(request.json['IMAGE_CALIBRATE_FIX_HOLES'])
        p_config['IMAGE_CALIBRATE_HOLE_THOLD']           = int(request.json['IMAGE_CALIBRATE_HOLE_THOLD'])
        p_config['IMAGE_CALIBRATE_MANUAL_OFFSET']        = int(request.json['IMAGE_CALIBRATE_MANUAL_OFFSET'])
        p_config['NIGHT_CONTRAST_ENHANCE']               = bool(request.json['NIGHT_CONTRAST_ENHANCE'])
        p_config['IMAGE_COLORMAP']                       = str(request.json['IMAGE_COLORMAP'])
        p_config['CONTRAST_ENHANCE_16BIT']               = bool(request.json['CONTRAST_ENHANCE_16BIT'])
        p_config['CLAHE_CLIPLIMIT']                      = float(request.json['CLAHE_CLIPLIMIT'])
        p_config['CLAHE_GRIDSIZE']                       = int(request.json['CLAHE_GRIDSIZE'])
        p_config['IMAGE_STRETCH']['CLASSNAME']           = str(request.json['IMAGE_STRETCH__CLASSNAME'])
        p_config['IMAGE_STRETCH']['MODE1_GAMMA']         = float(request.json['IMAGE_STRETCH__MODE1_GAMMA'])
        p_config['IMAGE_STRETCH']['MODE1_STDDEVS']       = float(request.json['IMAGE_STRETCH__MODE1_STDDEVS'])
        p_config['IMAGE_STRETCH']['MODE2_SHADOWS']       = float(request.json['IMAGE_STRETCH__MODE2_SHADOWS'])
        p_config['IMAGE_STRETCH']['MODE2_MIDTONES']      = float(request.json['IMAGE_STRETCH__MODE2_MIDTONES'])
        p_config['IMAGE_STRETCH']['MODE2_HIGHLIGHTS']    = float(request.json['IMAGE_STRETCH__MODE2_HIGHLIGHTS'])
        p_config['IMAGE_STRETCH']['MODE3_BLACK_CLIP']    = float(request.json['IMAGE_STRETCH__MODE3_BLACK_CLIP'])
        p_config['IMAGE_STRETCH']['MODE3_SHADOWS']       = float(request.json['IMAGE_STRETCH__MODE3_SHADOWS'])
        p_config['IMAGE_STRETCH']['MODE3_MIDTONES']      = float(request.json['IMAGE_STRETCH__MODE3_MIDTONES'])
        p_config['IMAGE_STRETCH']['MODE3_HIGHLIGHTS']    = float(request.json['IMAGE_STRETCH__MODE3_HIGHLIGHTS'])
        p_config['IMAGE_STRETCH']['SPLIT']               = False
        p_config['CFA_PATTERN']                          = str(request.json['CFA_PATTERN'])
        p_config['SCNR_ALGORITHM']                       = str(request.json['SCNR_ALGORITHM'])
        p_config['SCNR_MTF_MIDTONES']                    = float(request.json['SCNR_MTF_MIDTONES'])
        p_config['IMAGE_DENOISE']                        = str(request.json['IMAGE_DENOISE'])
        p_config['IMAGE_DENOISE_STRENGTH']               = int(request.json['IMAGE_DENOISE_STRENGTH'])
        p_config['BILATERAL_SIGMA_COLOR']                = int(request.json['BILATERAL_SIGMA_COLOR'])
        p_config['BILATERAL_SIGMA_SPACE']                = int(request.json['BILATERAL_SIGMA_SPACE'])
        p_config['WBR_FACTOR']                           = float(request.json['WBR_FACTOR'])
        p_config['WBG_FACTOR']                           = float(request.json['WBG_FACTOR'])
        p_config['WBB_FACTOR']                           = float(request.json['WBB_FACTOR'])
        p_config['WBR_MTF_MIDTONES']                     = float(request.json['WBR_MTF_MIDTONES'])
        p_config['WBG_MTF_MIDTONES']                     = float(request.json['WBG_MTF_MIDTONES'])
        p_config['WBB_MTF_MIDTONES']                     = float(request.json['WBB_MTF_MIDTONES'])
        p_config['AUTO_WB']                              = bool(request.json['AUTO_WB'])
        p_config['SATURATION_FACTOR']                    = float(request.json['SATURATION_FACTOR'])
        p_config['GAMMA_CORRECTION']                     = float(request.json['GAMMA_CORRECTION'])
        p_config['SHARPEN_AMOUNT']                       = float(request.json['SHARPEN_AMOUNT'])
        p_config['IMAGE_ROTATE']                         = str(request.json['IMAGE_ROTATE'])
        p_config['IMAGE_ROTATE_ANGLE']                   = int(request.json['IMAGE_ROTATE_ANGLE'])
        p_config['IMAGE_FLIP_V']                         = bool(request.json['IMAGE_FLIP_V'])
        p_config['IMAGE_FLIP_H']                         = bool(request.json['IMAGE_FLIP_H'])
        p_config['DETECT_MASK']                          = str(request.json['DETECT_MASK'])
        p_config['SQM_FOV_DIV']                          = int(request.json['SQM_FOV_DIV'])
        p_config['IMAGE_STACK_METHOD']                   = str(request.json['IMAGE_STACK_METHOD'])
        p_config['IMAGE_STACK_COUNT']                    = int(request.json['IMAGE_STACK_COUNT'])
        p_config['IMAGE_STACK_ALIGN']                    = bool(request.json['IMAGE_STACK_ALIGN'])
        p_config['IMAGE_ALIGN_DETECTSIGMA']              = int(request.json['IMAGE_ALIGN_DETECTSIGMA'])
        p_config['IMAGE_ALIGN_POINTS']                   = int(request.json['IMAGE_ALIGN_POINTS'])
        p_config['IMAGE_ALIGN_SOURCEMINAREA']            = int(request.json['IMAGE_ALIGN_SOURCEMINAREA'])
        p_config['IMAGE_STACK_SPLIT']                    = False
        p_config['FISH2PANO']['ENABLE']                  = bool(request.json['FISH2PANO__ENABLE'])
        p_config['FISH2PANO']['DIAMETER']                = int(request.json['FISH2PANO__DIAMETER'])
        p_config['FISH2PANO']['ROTATE_ANGLE']            = int(request.json['FISH2PANO__ROTATE_ANGLE'])
        p_config['FISH2PANO']['SCALE']                   = float(request.json['FISH2PANO__SCALE'])
        p_config['FISH2PANO']['FLIP_H']                  = bool(request.json['FISH2PANO__FLIP_H'])
        p_config['FISH2PANO']['ENABLE_CARDINAL_DIRS']    = bool(request.json['FISH2PANO__ENABLE_CARDINAL_DIRS'])
        p_config['FISH2PANO']['DIRS_OFFSET_BOTTOM']      = int(request.json['FISH2PANO__DIRS_OFFSET_BOTTOM'])
        p_config['FISH2PANO']['OPENCV_FONT_SCALE']       = float(request.json['FISH2PANO__OPENCV_FONT_SCALE'])
        p_config['FISH2PANO']['PIL_FONT_SIZE']           = int(request.json['FISH2PANO__PIL_FONT_SIZE'])
        p_config['PROCESSING_SPLIT_SCREEN']              = bool(request.json.get('PROCESSING_SPLIT_SCREEN', False))
        p_config['IMAGE_LABEL_TEMPLATE']                 = str(request.json['IMAGE_LABEL_TEMPLATE'])
        p_config['IMAGE_EXTRA_TEXT']                     = str(request.json['IMAGE_EXTRA_TEXT'])
        p_config['IMAGE_LABEL_SYSTEM']                   = str(request.json['IMAGE_LABEL_SYSTEM'])
        p_config['TEXT_PROPERTIES']['FONT_FACE']         = str(request.json['TEXT_PROPERTIES__FONT_FACE'])
        p_config['TEXT_PROPERTIES']['FONT_SCALE']        = float(request.json['TEXT_PROPERTIES__FONT_SCALE'])
        p_config['TEXT_PROPERTIES']['FONT_THICKNESS']    = int(request.json['TEXT_PROPERTIES__FONT_THICKNESS'])
        p_config['TEXT_PROPERTIES']['FONT_OUTLINE']      = bool(request.json['TEXT_PROPERTIES__FONT_OUTLINE'])
        p_config['TEXT_PROPERTIES']['FONT_HEIGHT']       = int(request.json['TEXT_PROPERTIES__FONT_HEIGHT'])
        p_config['TEXT_PROPERTIES']['FONT_X']            = int(request.json['TEXT_PROPERTIES__FONT_X'])
        p_config['TEXT_PROPERTIES']['FONT_Y']            = int(request.json['TEXT_PROPERTIES__FONT_Y'])
        p_config['TEXT_PROPERTIES']['PIL_FONT_FILE']     = str(request.json['TEXT_PROPERTIES__PIL_FONT_FILE'])
        p_config['TEXT_PROPERTIES']['PIL_FONT_CUSTOM']   = str(request.json['TEXT_PROPERTIES__PIL_FONT_CUSTOM'])
        p_config['TEXT_PROPERTIES']['PIL_FONT_SIZE']     = int(request.json['TEXT_PROPERTIES__PIL_FONT_SIZE'])
        p_config['CARDINAL_DIRS']['ENABLE']              = bool(request.json['CARDINAL_DIRS__ENABLE'])
        p_config['CARDINAL_DIRS']['SWAP_NS']             = bool(request.json['CARDINAL_DIRS__SWAP_NS'])
        p_config['CARDINAL_DIRS']['SWAP_EW']             = bool(request.json['CARDINAL_DIRS__SWAP_EW'])
        p_config['CARDINAL_DIRS']['CHAR_NORTH']          = str(request.json['CARDINAL_DIRS__CHAR_NORTH'])
        p_config['CARDINAL_DIRS']['CHAR_EAST']           = str(request.json['CARDINAL_DIRS__CHAR_EAST'])
        p_config['CARDINAL_DIRS']['CHAR_WEST']           = str(request.json['CARDINAL_DIRS__CHAR_WEST'])
        p_config['CARDINAL_DIRS']['CHAR_SOUTH']          = str(request.json['CARDINAL_DIRS__CHAR_SOUTH'])
        p_config['CARDINAL_DIRS']['DIAMETER']            = int(request.json['CARDINAL_DIRS__DIAMETER'])
        p_config['CARDINAL_DIRS']['OFFSET_X']            = int(request.json['CARDINAL_DIRS__OFFSET_X'])
        p_config['CARDINAL_DIRS']['OFFSET_Y']            = int(request.json['CARDINAL_DIRS__OFFSET_Y'])
        p_config['CARDINAL_DIRS']['OFFSET_TOP']          = int(request.json['CARDINAL_DIRS__OFFSET_TOP'])
        p_config['CARDINAL_DIRS']['OFFSET_LEFT']         = int(request.json['CARDINAL_DIRS__OFFSET_LEFT'])
        p_config['CARDINAL_DIRS']['OFFSET_RIGHT']        = int(request.json['CARDINAL_DIRS__OFFSET_RIGHT'])
        p_config['CARDINAL_DIRS']['OFFSET_BOTTOM']       = int(request.json['CARDINAL_DIRS__OFFSET_BOTTOM'])
        p_config['CARDINAL_DIRS']['OPENCV_FONT_SCALE']   = float(request.json['CARDINAL_DIRS__OPENCV_FONT_SCALE'])
        p_config['CARDINAL_DIRS']['PIL_FONT_SIZE']       = int(request.json['CARDINAL_DIRS__PIL_FONT_SIZE'])
        p_config['CARDINAL_DIRS']['OUTLINE_CIRCLE']      = bool(request.json['CARDINAL_DIRS__OUTLINE_CIRCLE'])
        p_config['IMAGE_CIRCLE_MASK']['ENABLE']          = bool(request.json['IMAGE_CIRCLE_MASK__ENABLE'])
        p_config['IMAGE_CIRCLE_MASK']['DIAMETER']        = int(request.json['IMAGE_CIRCLE_MASK__DIAMETER'])
        p_config['IMAGE_CIRCLE_MASK']['OFFSET_X']        = int(request.json['IMAGE_CIRCLE_MASK__OFFSET_X'])
        p_config['IMAGE_CIRCLE_MASK']['OFFSET_Y']        = int(request.json['IMAGE_CIRCLE_MASK__OFFSET_Y'])
        p_config['IMAGE_CIRCLE_MASK']['BLUR']            = int(request.json['IMAGE_CIRCLE_MASK__BLUR'])
        p_config['IMAGE_CIRCLE_MASK']['OPACITY']         = int(request.json['IMAGE_CIRCLE_MASK__OPACITY'])
        p_config['IMAGE_CIRCLE_MASK']['OUTLINE']         = bool(request.json['IMAGE_CIRCLE_MASK__OUTLINE'])
        p_config['IMAGE_CROP_IMAGE_CIRCLE']              = bool(request.json['IMAGE_CROP_IMAGE_CIRCLE'])
        p_config['IMAGE_BORDER']['TOP']                  = int(request.json['IMAGE_BORDER__TOP'])
        p_config['IMAGE_BORDER']['LEFT']                 = int(request.json['IMAGE_BORDER__LEFT'])
        p_config['IMAGE_BORDER']['RIGHT']                = int(request.json['IMAGE_BORDER__RIGHT'])
        p_config['IMAGE_BORDER']['BOTTOM']               = int(request.json['IMAGE_BORDER__BOTTOM'])
        p_config['MOON_OVERLAY']['ENABLE']               = bool(request.json['MOON_OVERLAY__ENABLE'])
        p_config['MOON_OVERLAY']['X']                    = int(request.json['MOON_OVERLAY__X'])
        p_config['MOON_OVERLAY']['Y']                    = int(request.json['MOON_OVERLAY__Y'])
        p_config['MOON_OVERLAY']['SCALE']                = float(request.json['MOON_OVERLAY__SCALE'])
        p_config['MOON_OVERLAY']['DARK_SIDE_SCALE']      = float(request.json['MOON_OVERLAY__DARK_SIDE_SCALE'])
        p_config['MOON_OVERLAY']['FLIP_V']               = bool(request.json['MOON_OVERLAY__FLIP_V'])
        p_config['MOON_OVERLAY']['FLIP_H']               = bool(request.json['MOON_OVERLAY__FLIP_H'])
        p_config['LIGHTGRAPH_OVERLAY']['ENABLE']         = bool(request.json['LIGHTGRAPH_OVERLAY__ENABLE'])
        p_config['LIGHTGRAPH_OVERLAY']['GRAPH_HEIGHT']   = int(request.json['LIGHTGRAPH_OVERLAY__GRAPH_HEIGHT'])
        p_config['LIGHTGRAPH_OVERLAY']['GRAPH_BORDER']   = int(request.json['LIGHTGRAPH_OVERLAY__GRAPH_BORDER'])
        p_config['LIGHTGRAPH_OVERLAY']['Y']              = int(request.json['LIGHTGRAPH_OVERLAY__Y'])
        p_config['LIGHTGRAPH_OVERLAY']['OFFSET_X']       = int(request.json['LIGHTGRAPH_OVERLAY__OFFSET_X'])
        p_config['LIGHTGRAPH_OVERLAY']['SCALE']          = float(request.json['LIGHTGRAPH_OVERLAY__SCALE'])
        p_config['LIGHTGRAPH_OVERLAY']['NOW_MARKER_SIZE']  = int(request.json['LIGHTGRAPH_OVERLAY__NOW_MARKER_SIZE'])
        p_config['LIGHTGRAPH_OVERLAY']['OPACITY']        = int(request.json['LIGHTGRAPH_OVERLAY__OPACITY'])
        p_config['LIGHTGRAPH_OVERLAY']['PIL_FONT_SIZE']  = int(request.json['LIGHTGRAPH_OVERLAY__PIL_FONT_SIZE'])
        p_config['LIGHTGRAPH_OVERLAY']['OPENCV_FONT_SCALE'] = float(request.json['LIGHTGRAPH_OVERLAY__OPENCV_FONT_SCALE'])
        p_config['LIGHTGRAPH_OVERLAY']['LABEL']          = bool(request.json['LIGHTGRAPH_OVERLAY__LABEL'])
        p_config['LIGHTGRAPH_OVERLAY']['HOUR_LINES']     = bool(request.json['LIGHTGRAPH_OVERLAY__HOUR_LINES'])

        # allow extended time for stacking/registration
        p_config['EXPOSURE_PERIOD'] = 120

        # disable these
        p_config['ADSB']['ENABLE']                       = False
        p_config['SATELLITE_TRACK']['ENABLE']            = False

        # SQM_ROI
        sqm_roi_x1 = int(request.json['SQM_ROI_X1'])
        sqm_roi_y1 = int(request.json['SQM_ROI_Y1'])
        sqm_roi_x2 = int(request.json['SQM_ROI_X2'])
        sqm_roi_y2 = int(request.json['SQM_ROI_Y2'])

        # the x2 and y2 values must be positive integers in order to be enabled and valid
        if sqm_roi_x2 and sqm_roi_y2:
            p_config['SQM_ROI'] = [sqm_roi_x1, sqm_roi_y1, sqm_roi_x2, sqm_roi_y2]
        else:
            p_config['SQM_ROI'] = []


        # TEXT_PROPERTIES FONT_COLOR
        font_color_str = str(request.json['TEXT_PROPERTIES__FONT_COLOR'])
        p_config['TEXT_PROPERTIES']['FONT_COLOR'] = [int(x) for x in font_color_str.split(',')]

        # CARDINAL_DIRS FONT_COLOR
        cardinal_dirs_color_str = str(request.json['CARDINAL_DIRS__FONT_COLOR'])
        p_config['CARDINAL_DIRS']['FONT_COLOR'] = [int(x) for x in cardinal_dirs_color_str.split(',')]

        # IMAGE_BORDER COLOR
        image_border__color_str = str(request.json['IMAGE_BORDER__COLOR'])
        p_config['IMAGE_BORDER']['COLOR'] = [int(x) for x in image_border__color_str.split(',')]

        # LIGHTGRAPH COLORS
        lightgraph_overlay__day_color_str = str(request.json['LIGHTGRAPH_OVERLAY__DAY_COLOR'])
        p_config['LIGHTGRAPH_OVERLAY']['DAY_COLOR'] = [int(x) for x in lightgraph_overlay__day_color_str.split(',')]

        lightgraph_overlay__dusk_color_str = str(request.json['LIGHTGRAPH_OVERLAY__DUSK_COLOR'])
        p_config['LIGHTGRAPH_OVERLAY']['DUSK_COLOR'] = [int(x) for x in lightgraph_overlay__dusk_color_str.split(',')]

        lightgraph_overlay__night_color_str = str(request.json['LIGHTGRAPH_OVERLAY__NIGHT_COLOR'])
        p_config['LIGHTGRAPH_OVERLAY']['NIGHT_COLOR'] = [int(x) for x in lightgraph_overlay__night_color_str.split(',')]

        lightgraph_overlay__moonmode_color_str = str(request.json['LIGHTGRAPH_OVERLAY__MOONMODE_COLOR'])
        p_config['LIGHTGRAPH_OVERLAY']['MOONMODE_COLOR'] = [int(x) for x in lightgraph_overlay__moonmode_color_str.split(',')]

        lightgraph_overlay__hour_color_str = str(request.json['LIGHTGRAPH_OVERLAY__HOUR_COLOR'])
        p_config['LIGHTGRAPH_OVERLAY']['HOUR_COLOR'] = [int(x) for x in lightgraph_overlay__hour_color_str.split(',')]

        lightgraph_overlay__border_color_str = str(request.json['LIGHTGRAPH_OVERLAY__BORDER_COLOR'])
        p_config['LIGHTGRAPH_OVERLAY']['BORDER_COLOR'] = [int(x) for x in lightgraph_overlay__border_color_str.split(',')]

        lightgraph_overlay__now_color_str = str(request.json['LIGHTGRAPH_OVERLAY__NOW_COLOR'])
        p_config['LIGHTGRAPH_OVERLAY']['NOW_COLOR'] = [int(x) for x in lightgraph_overlay__now_color_str.split(',')]

        lightgraph_overlay__font_color_str = str(request.json['LIGHTGRAPH_OVERLAY__FONT_COLOR'])
        p_config['LIGHTGRAPH_OVERLAY']['FONT_COLOR'] = [int(x) for x in lightgraph_overlay__font_color_str.split(',')]


        hdulist = fits.open(filename_p)

        exposure = float(hdulist[0].header.get('EXPTIME', 0))
        gain = float(hdulist[0].header.get('GAIN', 0))
        gain_av = Array('f', [gain])
        binning = int(hdulist[0].header.get('XBINNING', 1))
        binning_av = Array('i', [binning])
        position_av = Array('f', [self.camera.latitude, self.camera.longitude, self.camera.elevation])
        #sensors_temp_av = Array('f', [float(hdulist[0].header.get('CCD-TEMP', 0))])
        #sensors_user_av = Array('f', [float(hdulist[0].header.get('CCD-TEMP', 0))])
        sensors_temp_av = Array('f', [0.0 for x in range(60)])
        sensors_user_av = Array('f', [0.0 for x in range(110)])
        night_av = Array('i', [1, 0])  # using night values for processing
        astro_av = Array('f', [0.0, 0.0, 0.0])

        hdulist.close()

        image_processor = ImageProcessor(
            p_config,
            position_av,
            gain_av,
            binning_av,
            sensors_temp_av,
            sensors_user_av,
            night_av,
            astro_av,
        )


        processing_start = time.time()


        message_list = list()

        if disable_processing:
            # just return original image with no processing

            # use mtime for date
            image_date = datetime.fromtimestamp(filename_p.stat().st_mtime)

            image_processor.add(
                filename_p,
                exposure,
                gain,
                binning,
                image_date,
                0.0,
                fits_entry.camera,
            )

            image_processor.debayer()  # populates self.opencv_data

            image_processor.stack()  # populates self.image

            image_processor.convert_16bit_to_8bit()


            # rotation
            image_processor.rotate_90()
            image_processor.rotate_angle()


            # verticle flip
            image_processor.flip_v()

            # horizontal flip
            image_processor.flip_h()


            image_processor.colorize()


            message_list.append('Unprocessed image')

        else:
            if p_config['IMAGE_STACK_COUNT'] > 1:
                fits_image_query = IndiAllSkyDbFitsImageTable.query\
                    .join(IndiAllSkyDbFitsImageTable.camera)\
                    .filter(IndiAllSkyDbCameraTable.id == camera_id)\
                    .filter(IndiAllSkyDbFitsImageTable.createDate < fits_entry.createDate)\
                    .order_by(IndiAllSkyDbFitsImageTable.createDate.desc())\
                    .limit(p_config['IMAGE_STACK_COUNT'] - 1)

                for f_image in fits_image_query:
                    f_image_p = f_image.getFilesystemPath()

                    # use mtime for date
                    pre_image_date = datetime.fromtimestamp(f_image_p.stat().st_mtime)

                    alt_hdulist = fits.open(f_image_p)
                    alt_exposure = float(alt_hdulist[0].header.get('EXPTIME', 0))
                    alt_gain = float(alt_hdulist[0].header.get('GAIN', 0))
                    alt_binning = int(alt_hdulist[0].header.get('XBINNING', 1))
                    alt_hdulist.close()

                    i_ref_2 = image_processor.add(
                        f_image_p,
                        alt_exposure,
                        alt_gain,
                        alt_binning,
                        pre_image_date,
                        0.0,
                        f_image.camera,
                    )

                    image_processor._calibrate(i_ref_2)
                    i_ref_2.opencv_data = image_processor._debayer(i_ref_2)  # update opencv_data

                message_list.append('Stacked {0:d} images'.format(p_config['IMAGE_STACK_COUNT']))


            # use mtime for date
            image_date = datetime.fromtimestamp(filename_p.stat().st_mtime)


            image_processor.update_astrometric_data(image_date)


            # add image after preloading other images
            i_ref = image_processor.add(
                filename_p,
                exposure,
                gain,
                binning,
                datetime.now(),
                0.0,
                fits_entry.camera,
            )


            image_processor.calibrate()

            image_processor.fix_holes_early()

            image_processor.debayer()  # populates self.opencv_data

            image_processor.stack()  # populates self.image

            image_processor.denoise()

            image_processor.stretch()

            if p_config['NIGHT_CONTRAST_ENHANCE']:
                if p_config.get('CONTRAST_ENHANCE_16BIT'):
                    image_processor.contrast_clahe_16bit()

                    message_list.append('16-bit CLAHE')


            image_processor.convert_16bit_to_8bit()


            if p_config.get('IMAGE_ROTATE'):
                image_processor.rotate_90()


            # rotation
            if p_config.get('IMAGE_ROTATE_ANGLE'):
                image_processor.rotate_angle()


            # verticle flip
            if p_config.get('IMAGE_FLIP_V'):
                image_processor.flip_v()

            # horizontal flip
            if p_config.get('IMAGE_FLIP_H'):
                image_processor.flip_h()

            # crop
            image_processor.crop_image()

            # green removal
            image_processor.scnr()


            # white balance
            image_processor.white_balance_mtf()
            image_processor.white_balance_manual_bgr()
            image_processor.white_balance_auto_bgr()


            # saturation
            image_processor.saturation_adjust()


            # gamma correction
            image_processor.apply_gamma_correction()


            # sharpening (unsharp mask)
            image_processor.sharpen()


            if p_config['NIGHT_CONTRAST_ENHANCE']:
                if not p_config.get('CONTRAST_ENHANCE_16BIT'):
                    image_processor.contrast_clahe()

                    message_list.append('CLAHE Contrast Enhance')


            image_processor.colorize()


            image_processor.colormap()


            image_processor.apply_image_circle_mask(i_ref.binning)


            if not p_config.get('FISH2PANO', {}).get('ENABLE'):
                image_processor.add_border()

                image_processor.moon_overlay()

                image_processor.lightgraph_overlay()

                image_processor.cardinal_dirs_label()

                if p_config['IMAGE_LABEL_SYSTEM']:
                    image_processor.label_image()

            else:
                # no labels if converting to panorama
                pano_data = image_processor.fish2pano(i_ref.binning)


                if p_config.get('FISH2PANO', {}).get('FLIP_H'):
                    pano_data = image_processor._flip(pano_data, 1)


                if p_config.get('FISH2PANO', {}).get('ENABLE_CARDINAL_DIRS'):
                    pano_data = image_processor.fish2pano_cardinal_dirs_label(pano_data)


                image_processor.image = pano_data


        processing_elapsed_s = time.time() - processing_start
        app.logger.info('Image processed in %0.4f s', processing_elapsed_s)


        image = image_processor.image


        if output_image_type == 'png':
            png_compress_level = p_config['IMAGE_FILE_COMPRESSION']['png']

            ### OpenCV
            _, json_image = cv2.imencode('.jpg', image, [cv2.IMWRITE_PNG_COMPRESSION, png_compress_level])
            json_image_buffer = io.BytesIO(json_image.tobytes())

            ### pillow
            #json_image_buffer = io.BytesIO()
            #img = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
            #img.save(json_image_buffer, format='PNG', compress_level=png_compress_level)
        else:
            # jpeg default
            jpg_compress_level = p_config['IMAGE_FILE_COMPRESSION']['jpg']

            ### OpenCV
            _, json_image = cv2.imencode('.jpg', image, [cv2.IMWRITE_JPEG_QUALITY, jpg_compress_level])
            json_image_buffer = io.BytesIO(json_image.tobytes())

            ### pillow
            #json_image_buffer = io.BytesIO()
            #img = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
            #img.save(json_image_buffer, format='JPEG', compress_level=jpg_compress_level)


        json_image_b64 = base64.b64encode(json_image_buffer.getvalue())

        json_data = dict()
        json_data['image_b64'] = json_image_b64.decode('utf-8')
        json_data['processing_elapsed_s'] = round(processing_elapsed_s, 3)
        #json_data['message'] = ', '.join(message_list)
        json_data['message'] = ''  # Blank until I can get messages from all processing actions

        return jsonify(json_data)


class LogView(TemplateView):
    page_title = 'Log Viewer'
    decorators = [login_required]

    def get_context(self):
        context = super(LogView, self).get_context()

        context['form_logviewer'] = IndiAllskyLogViewerForm()

        return context


class JsonLogView(JsonView):
    methods = ['POST']
    decorators = [login_required]

    def dispatch_request(self):
        log_file_p = Path('/var/log/indi-allsky/indi-allsky.log')
        line_size = 150  # assuming lines have an average length


        lines = int(request.json.get('lines', 500))
        filter_str = str(request.json.get('filter', ''))[:30]  # limit to 30 characters


        json_data = dict()


        filter_regex = r'^[a-zA-Z0-9_\.\-\\\ ]*$'
        if not re.search(filter_regex, filter_str):
            json_data['log'] = 'ERROR: Log filter has illegal characters'
            return jsonify(json_data)


        if lines > 5000:
            # sanity check
            lines = 5000


        read_bytes = lines * line_size


        if not log_file_p.exists():
            # this can happen in docker
            json_data['log'] = 'ERROR: Log file missing'
            return jsonify(json_data)


        log_file_size = log_file_p.stat().st_size
        if log_file_size < read_bytes:
            # just read the whole file
            #app.logger.info('Returning %d bytes of log data', log_file_size)
            log_file_seek = 0
        else:
            #app.logger.info('Returning %d bytes of log data', read_bytes)
            log_file_seek = log_file_size - read_bytes


        try:
            with io.open(log_file_p, 'r') as log_file_f:
                log_file_f.seek(log_file_seek)
                log_lines = log_file_f.readlines()
        except PermissionError as e:
            log_lines = ['', 'PermissionError: {0:s}'.format(str(e))]


        try:
            log_lines.pop(0)  # skip the first partial line
            log_lines.reverse()  # newer lines first
        except IndexError:
            app.logger.warning('indi-allsky log empty')
            log_lines = list()


        if len(log_lines) == 0:
            log_lines.append('[indi-allsky log empty]')
        elif filter_str:
            filter_regex = re.compile(filter_str, re.IGNORECASE)

            filtered_lines = list()
            for line in log_lines:
                ### this is probably insecure
                if not re.search(filter_regex, line):
                    continue

                filtered_lines.append(line)

            # replace original
            log_lines = filtered_lines

            if len(log_lines) == 0:
                log_lines.append('[No matching lines]')


        json_data['log'] = ''.join(log_lines)

        return jsonify(json_data)


class LogDownloadView(BaseView):
    decorators = [login_required]
    methods = ['GET']


    def dispatch_request(self):
        import gzip

        log_file_p = Path('/var/log/indi-allsky/indi-allsky.log')
        line_size = 150  # assuming lines have an average length

        lines = int(request.args.get('lines', 20000))


        if not log_file_p.exists():
            # this can happen in docker
            return 'Log file does not exist'


        read_bytes = lines * line_size


        log_file_size = log_file_p.stat().st_size
        if log_file_size == 0:
            return 'Log file is empty'
        elif log_file_size < read_bytes:
            # just read the whole file
            #app.logger.info('Returning %d bytes of log data', log_file_size)
            log_file_seek = 0
        else:
            #app.logger.info('Returning %d bytes of log data', read_bytes)
            log_file_seek = log_file_size - read_bytes


        try:
            with io.open(log_file_p, 'rb') as log_file_f:
                log_file_f.seek(log_file_seek)
                log_data = log_file_f.read()
        except PermissionError as e:
            return 'PermissionError: {0:s}'.format(str(e))


        log_buffer = io.BytesIO(gzip.compress(log_data))


        data = {
            'ts'    : datetime.now(),
        }


        download_name = 'indi-allsky_log_{ts:%Y%m%d_%H%M%S}.txt.gz'.format(**data)

        return send_file(log_buffer, mimetype='application/octet-stream', download_name=download_name, as_attachment=True)


class LogWebappDownloadView(BaseView):
    decorators = [login_required]
    methods = ['GET']


    def dispatch_request(self):
        import gzip

        log_file_p = Path('/var/log/indi-allsky/webapp-indi-allsky.log')
        line_size = 150  # assuming lines have an average length

        lines = int(request.args.get('lines', 5000))


        if not log_file_p.exists():
            # this can happen in docker
            return 'Log file does not exist'


        read_bytes = lines * line_size


        log_file_size = log_file_p.stat().st_size
        if log_file_size == 0:
            return 'Log file is empty'
        elif log_file_size < read_bytes:
            # just read the whole file
            #app.logger.info('Returning %d bytes of log data', log_file_size)
            log_file_seek = 0
        else:
            #app.logger.info('Returning %d bytes of log data', read_bytes)
            log_file_seek = log_file_size - read_bytes


        try:
            with io.open(log_file_p, 'rb') as log_file_f:
                log_file_f.seek(log_file_seek)
                log_data = log_file_f.read()
        except PermissionError as e:
            return 'PermissionError: {0:s}'.format(str(e))


        log_buffer = io.BytesIO(gzip.compress(log_data))


        data = {
            'ts'    : datetime.now(),
        }


        download_name = 'indi-allsky_webapp_log_{ts:%Y%m%d_%H%M%S}.txt.gz'.format(**data)

        return send_file(log_buffer, mimetype='application/octet-stream', download_name=download_name, as_attachment=True)


class LogSyslogDownloadView(BaseView):
    decorators = [login_required]
    methods = ['GET']


    def dispatch_request(self):
        import gzip

        log_file_p = Path('/var/log/syslog')
        line_size = 150  # assuming lines have an average length

        lines = int(request.args.get('lines', 20000))


        if not log_file_p.exists():
            # this can happen in docker
            return 'Log file does not exist'


        read_bytes = lines * line_size


        log_file_size = log_file_p.stat().st_size
        if log_file_size == 0:
            return 'Log file is empty'
        elif log_file_size < read_bytes:
            # just read the whole file
            #app.logger.info('Returning %d bytes of log data', log_file_size)
            log_file_seek = 0
        else:
            #app.logger.info('Returning %d bytes of log data', read_bytes)
            log_file_seek = log_file_size - read_bytes


        try:
            with io.open(log_file_p, 'rb') as log_file_f:
                log_file_f.seek(log_file_seek)
                log_data = log_file_f.read()
        except PermissionError as e:
            return 'PermissionError: {0:s}'.format(str(e))


        log_buffer = io.BytesIO(gzip.compress(log_data))


        data = {
            'ts'    : datetime.now(),
        }


        download_name = 'indi-allsky_syslog_log_{ts:%Y%m%d_%H%M%S}.txt.gz'.format(**data)

        return send_file(log_buffer, mimetype='application/octet-stream', download_name=download_name, as_attachment=True)


class LogKernDownloadView(BaseView):
    decorators = [login_required]
    methods = ['GET']


    def dispatch_request(self):
        import gzip

        log_file_p = Path('/var/log/kern.log')
        line_size = 150  # assuming lines have an average length

        lines = int(request.args.get('lines', 20000))


        if not log_file_p.exists():
            # this can happen in docker
            return 'Log file does not exist'


        read_bytes = lines * line_size


        log_file_size = log_file_p.stat().st_size
        if log_file_size == 0:
            return 'Log file is empty'
        elif log_file_size < read_bytes:
            # just read the whole file
            #app.logger.info('Returning %d bytes of log data', log_file_size)
            log_file_seek = 0
        else:
            #app.logger.info('Returning %d bytes of log data', read_bytes)
            log_file_seek = log_file_size - read_bytes


        try:
            with io.open(log_file_p, 'rb') as log_file_f:
                log_file_f.seek(log_file_seek)
                log_data = log_file_f.read()
        except PermissionError as e:
            return 'PermissionError: {0:s}'.format(str(e))


        log_buffer = io.BytesIO(gzip.compress(log_data))


        data = {
            'ts'    : datetime.now(),
        }


        download_name = 'indi-allsky_kern_log_{ts:%Y%m%d_%H%M%S}.txt.gz'.format(**data)

        return send_file(log_buffer, mimetype='application/octet-stream', download_name=download_name, as_attachment=True)


class SupportInfoView(TemplateView):
    page_title = 'Support Info'
    decorators = [login_required]

    def get_context(self):
        context = super(SupportInfoView, self).get_context()
        return context


class JsonSupportInfoView(JsonView):
    decorators = [login_required]

    def __init__(self, **kwargs):
        super(JsonSupportInfoView, self).__init__(**kwargs)


    def dispatch_request(self):
        import subprocess

        cmd = [
            str(Path(__file__).parent.parent.parent.absolute().joinpath('misc', 'support_info.sh')),
        ]


        json_data = dict()

        try:
            app.logger.info('Running: %s', ' '.join(cmd))
            support_subproc = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                check=True
            )

            json_data['support_info'] = (support_subproc.stdout).decode('utf-8', errors='replace')
        except subprocess.CalledProcessError as e:
            app.logger.error('Support info generate failed: %s', e.stdout)
            return jsonify({}), 400


        return jsonify(json_data)


class NotificationsView(TemplateView):
    page_title = 'Notifications'
    decorators = [login_required]

    def get_context(self):
        context = super(NotificationsView, self).get_context()

        notices = IndiAllSkyDbNotificationTable.query\
            .order_by(IndiAllSkyDbNotificationTable.createDate.desc())\
            .limit(50)


        notice_list = list()
        for notice in notices:
            n = {
                'id'            : notice.id,
                'createDate'    : notice.createDate,
                'expireDate'    : notice.expireDate,
                'category'      : notice.category.value,
                'ack'           : notice.ack,
                'notification'  : notice.notification,
            }

            notice_list.append(n)

        context['notice_list'] = notice_list

        return context


class AjaxNotificationView(BaseView):
    methods = ['GET', 'POST']
    decorators = []  # manually handle if user is logged in


    def __init__(self, **kwargs):
        super(AjaxNotificationView, self).__init__(**kwargs)


    def dispatch_request(self):
        if not current_user.is_authenticated:
            no_data = {
                'id' : 0,
            }
            return jsonify(no_data)


        if request.method == 'POST':
            return self.post()
        elif request.method == 'GET':
            return self.get()
        else:
            return jsonify({}), 400


    def get(self, camera_id=None):
        if not camera_id:
            camera_id = int(request.args['camera_id'])

        self.cameraSetup(camera_id=camera_id)

        # return a single result, newest first
        now = self.camera_now

        # this MUST ALWAYS return the newest result
        notice = IndiAllSkyDbNotificationTable.query\
            .filter(
                and_(
                    IndiAllSkyDbNotificationTable.ack == sa_false(),
                    IndiAllSkyDbNotificationTable.expireDate > now,
                )
            )\
            .order_by(IndiAllSkyDbNotificationTable.createDate.desc())\
            .first()


        if not notice:
            no_data = {
                'id' : 0,
            }
            return jsonify(no_data)


        data = {
            'id'            : notice.id,
            'createDate'    : notice.createDate.strftime('%Y-%m-%d %H:%M:%S'),
            'category'      : notice.category.value,
            'notification'  : notice.notification,
        }

        return jsonify(data)


    def post(self):
        camera_id = int(request.json['camera_id'])
        ack_id = int(request.json['ack_id'])

        try:
            notice = IndiAllSkyDbNotificationTable.query\
                .filter(IndiAllSkyDbNotificationTable.id == ack_id)\
                .one()

            notice.setAck()
        except NoResultFound:
            pass


        # return next notification
        return self.get(camera_id=camera_id)


class UserInfoView(TemplateView):
    page_title = 'User Info'
    decorators = [login_required]

    def get_context(self):
        context = super(UserInfoView, self).get_context()

        form_data = {
            'USERNAME' : current_user.username,
            'NAME'     : current_user.name,
            'EMAIL'    : current_user.email,
            'ADMIN'    : current_user.admin,
        }

        context['form_userinfo'] = IndiAllskyUserInfoForm(data=form_data)

        return context


class AjaxUserInfoView(BaseView):
    methods = ['POST']
    decorators = [login_required]


    def __init__(self, **kwargs):
        super(AjaxUserInfoView, self).__init__(**kwargs)


    def dispatch_request(self):
        if request.method == 'POST':
            return self.post()
        else:
            return jsonify({}), 400


    def post(self):
        form_userinfo = IndiAllskyUserInfoForm(data=request.json)


        if not form_userinfo.validate(current_user):
            form_errors = form_userinfo.errors  # this must be a property
            form_errors['form_global'] = ['Please fix the errors above']
            return jsonify(form_errors), 400


        # check current password (again)
        current_password = str(request.json['CURRENT_PASSWORD'])
        if not argon2.verify(current_password, current_user.password):
            message = {
                'CURRENT_PASSWORD' : ['Current password is not valid'],
            }
            return jsonify(message), 400


        new_name = str(request.json['NAME'])
        new_password = str(request.json['NEW_PASSWORD'])
        # email is read only
        # admin is read only


        current_user.name = new_name


        if new_password:
            # do not update password if not defined
            hashed_password = argon2.hash(new_password)
            current_user.password = hashed_password
            current_user.passwordDate = datetime.now()


        db.session.commit()


        message = {
            'success-message' : 'User info updated',
        }
        return jsonify(message)


class UsersView(TemplateView):
    page_title = 'Users'
    decorators = [login_required]

    def get_context(self):
        context = super(UsersView, self).get_context()

        user_list = IndiAllSkyDbUserTable.query\
            .order_by(IndiAllSkyDbUserTable.createDate.asc())

        context['user_list'] = user_list

        return context


class ConfigListView(TemplateView):
    page_title = 'Config History'
    decorators = [login_required]

    def get_context(self):
        context = super(ConfigListView, self).get_context()

        config_list = IndiAllSkyDbConfigTable.query\
            .add_columns(
                IndiAllSkyDbConfigTable.id,
                IndiAllSkyDbConfigTable.createDate,
                IndiAllSkyDbConfigTable.level,
                IndiAllSkyDbConfigTable.note,
                IndiAllSkyDbConfigTable.encrypted,
                IndiAllSkyDbUserTable.username,
            )\
            .join(IndiAllSkyDbUserTable)\
            .order_by(IndiAllSkyDbConfigTable.createDate.desc())\
            .limit(25)

        context['config_list'] = config_list

        return context


class ConfigDownloadView(BaseView):
    decorators = [login_required]
    methods = ['GET']


    redact_dict = {
        'OWNER' : 'REDACTED',
        'FILETRANSFER' : {
            'PASSWORD' : 'REDACTED',
            'PASSWORD_E' : '',
        },
        'S3UPLOAD' : {
            'SECRET_KEY' : 'REDACTED',
            'SECRET_KEY_E' : '',
        },
        'MQTTPUBLISH' : {
            'PASSWORD' : 'REDACTED',
            'PASSWORD_E' : '',
        },
        'SYNCAPI' : {
            'APIKEY' : 'REDACTED',
            'APIKEY_E' : '',
        },
        'PYCURL_CAMERA' : {
            'PASSWORD' : 'REDACTED',
            'PASSWORD_E' : '',
        },
        'TEMP_SENSOR' : {
            'OPENWEATHERMAP_APIKEY' : 'REDACTED',
            'OPENWEATHERMAP_APIKEY_E' : '',
            'WUNDERGROUND_APIKEY' : 'REDACTED',
            'WUNDERGROUND_APIKEY_E' : '',
            'ASTROSPHERIC_APIKEY' : 'REDACTED',
            'ASTROSPHERIC_APIKEY_E' : '',
            'AMBIENTWEATHER_APIKEY' : 'REDACTED',
            'AMBIENTWEATHER_APIKEY_E' : '',
            'AMBIENTWEATHER_APPLICATIONKEY' : 'REDACTED',
            'AMBIENTWEATHER_APPLICATIONKEY_E' : '',
            'AMBIENTWEATHER_MACADDRESS' : 'REDACTED',
            'AMBIENTWEATHER_MACADDRESS_E' : '',
            'ECOWITT_APIKEY' : 'REDACTED',
            'ECOWITT_APIKEY_E' : '',
            'ECOWITT_APPLICATIONKEY' : 'REDACTED',
            'ECOWITT_APPLICATIONKEY_E' : '',
            'ECOWITT_MACADDRESS' : 'REDACTED',
            'ECOWITT_MACADDRESS_E' : '',
            'MQTT_PASSWORD' : 'REDACTED',
            'MQTT_PASSWORD_E' : '',
        },
        'DEVICE' : {
            'MQTT_PASSWORD' : 'REDACTED',
            'MQTT_PASSWORD_E' : '',
        },
        'LIBCAMERA' : {
            'MQTT_PASSWORD' : 'REDACTED',
            'MQTT_PASSWORD_E' : '',
        },
        'ADSB' : {
            'PASSWORD' : 'REDACTED',
            'PASSWORD_E' : '',
        },
        'IMAGE_OVERLAY' : {
            'A_PASSWORD' : 'REDACTED',
            'A_PASSWORD_E' : '',
        },
    }


    def dispatch_request(self):
        config_id = int(request.args.get('id', -1))
        redact = bool(request.args.get('redact', 0))

        # not catching NoResultFound
        config_entry = IndiAllSkyDbConfigTable.query\
            .filter(IndiAllSkyDbConfigTable.id == config_id)\
            .one()


        config = dict(config_entry.data)


        if redact:
            app.logger.warning('Redacting sensitive info from config download')
            config = self.dict_merge(config, self.redact_dict)

            # reduce precision of lat/long
            config['LOCATION_LATITUDE'] = float(round(config['LOCATION_LATITUDE']))
            config['LOCATION_LONGITUDE'] = float(round(config['LOCATION_LONGITUDE']))


        config_str = json.dumps(config, indent=4, ensure_ascii=False)
        config_buffer = io.BytesIO(config_str.encode())


        data = {
            'id'    : config_entry.id,
            'ts'    : datetime.now(),
            'level' : config_entry.level.replace('.', '-'),
        }

        download_name = 'indi-allsky_config_id-{id:d}_level-{level:s}_{ts:%Y%m%d_%H%M%S}.json'.format(**data)

        return send_file(config_buffer, mimetype='application/octet-stream', download_name=download_name, as_attachment=True)


    def dict_merge(self, a_dict, b_dict, path=[]):
        for k in b_dict.keys():
            if k in a_dict.keys():
                if isinstance(a_dict[k], (str, int, float, bool)) and isinstance(b_dict[k], (str, int, float, bool)):
                    a_dict[k] = b_dict[k]
                elif isinstance(a_dict[k], dict) and isinstance(b_dict[k], dict):
                    self.dict_merge(a_dict[k], b_dict[k], path + [str(k)])  # recursion
                else:
                    raise Exception('Dictionary conflict at ' + '.'.join(path + [str(k)]))
            else:
                a_dict[k] = b_dict[k]

        return a_dict


class ConfigRestoreView(TemplateView):
    page_title = 'Config Restore'
    decorators = [login_required]

    def get_context(self):
        context = super(ConfigRestoreView, self).get_context()

        context['camera_id'] = self.camera.id

        context['form_config_restore'] = IndiAllskyConfigRestoreForm(indi_allsky_config=self.indi_allsky_config)

        return context


class AjaxConfigRestoreView(BaseView):
    decorators = [login_required]
    methods = ['POST']


    def dispatch_request(self):
        if not current_user.is_admin:
            return jsonify({}), 400

        form_config_restore = IndiAllskyConfigRestoreForm(data=request.form)

        if not form_config_restore.validate():
            form_errors = form_config_restore.errors  # this must be a property
            return jsonify(form_errors), 400


        config_form_file = request.files['CONFIG_UPLOAD']
        reset_keys = request.form.get('RESET_KEYS')
        flush_configs = request.form.get('FLUSH_CONFIGS')


        f_tmp_config = tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.json')
        f_tmp_config.close()

        tmp_config_p = Path(f_tmp_config.name)

        config_form_file.save(str(tmp_config_p))


        file_size = tmp_config_p.stat().st_size
        if file_size == 0:
            error_data = {
                'form_global' : ['Please fix the errors above'],
                'CONFIG_UPLOAD' : ['File is empty'],
            }
            tmp_config_p.unlink()  # cleanup
            return jsonify(error_data), 400

        if file_size > 100000:
            error_data = {
                'form_global' : ['Please fix the errors above'],
                'CONFIG_UPLOAD' : ['File too large'],
            }
            tmp_config_p.unlink()  # cleanup
            return jsonify(error_data), 400


        try:
            with io.open(str(tmp_config_p), 'rb') as config_f:
                config_dict = json.load(config_f, object_pairs_hook=OrderedDict)
        except ValueError:
            error_data = {
                'form_global' : ['Please fix the errors above'],
                'CONFIG_UPLOAD' : ['Invalid JSON'],
            }
            return jsonify(error_data), 400
        finally:
            tmp_config_p.unlink()  # cleanup


        # basic config validation
        if not isinstance(config_dict.get('INDI_SERVER'), str) or not isinstance(config_dict.get('CCD_CONFIG'), dict) or not isinstance(config_dict.get('INDI_CONFIG_DEFAULTS'), dict):
            error_data = {
                'form_global' : ['Please fix the errors above'],
                'CONFIG_UPLOAD' : ['Not a valid indi-allsky config'],
            }
            return jsonify(error_data), 400


        # save new config
        if not app.config['LOGIN_DISABLED']:
            username = current_user.username
        else:
            username = 'system'


        try:
            # replace config
            self._indi_allsky_config_obj.config = config_dict
            self._indi_allsky_config_obj.save(username, 'Manual config restore from upload')
        except ConfigSaveException as e:
            error_data = {
                'form_global' : ['Please fix the errors above'],
                'CONFIG_UPLOAD' : [str(e)],
            }
            return jsonify(error_data), 400


        app.logger.info('Restored config from upload')


        if flush_configs:
            flush_entries = IndiAllSkyDbConfigTable.query\
                .filter(IndiAllSkyDbConfigTable.id != self._indi_allsky_config_obj.config_id)

            flush_entries.delete()
            db.session.commit()

            app.logger.warning('Config entries flushed')


        if reset_keys:
            import shutil
            import secrets
            from cryptography.fernet import Fernet


            flask_config_p = Path('/etc/indi-allsky/flask.json')


            with io.open(str(flask_config_p), 'rb') as flask_config_f:
                flask_config = json.load(flask_config_f, object_pairs_hook=OrderedDict)


            new_flask_secret_key = secrets.token_hex()
            new_flask_password_key = Fernet.generate_key().decode()


            flask_config['SECRET_KEY'] = new_flask_secret_key
            flask_config['PASSWORD_KEY'] = new_flask_password_key


            with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json', encoding='utf-8') as f_tmp_config:
                json.dump(
                    flask_config,
                    f_tmp_config,
                    indent=2,  # matches jq output
                    ensure_ascii=False,
                )

                tmp_config_p = Path(f_tmp_config.name)


            shutil.copy2(str(tmp_config_p), str(flask_config_p))
            tmp_config_p.unlink()

            flask_config_p.chmod(0o660)

            app.logger.warning('Reset security keys')


        message = {
            'success-message' : 'Restored Config',
        }
        return jsonify(message)


class AjaxSelectCameraView(BaseView):
    methods = ['POST']


    def __init__(self, **kwargs):
        super(AjaxSelectCameraView, self).__init__(**kwargs)


    def dispatch_request(self):
        if request.method == 'POST':
            return self.post()
        else:
            return jsonify({}), 400


    def post(self):
        camera_id = int(request.json['camera_id'])

        try:
            camera = IndiAllSkyDbCameraTable.query\
                .filter(IndiAllSkyDbCameraTable.id == camera_id)\
                .one()
        except NoResultFound:
            return jsonify({}), 400


        session['camera_id'] = camera.id


        # return next notification
        return jsonify({})


class CameraLensView(TemplateView):
    page_title = 'Camera/Lens Info'


    def get_context(self):
        context = super(CameraLensView, self).get_context()

        camera = IndiAllSkyDbCameraTable.query\
            .filter(IndiAllSkyDbCameraTable.id == self.camera.id)\
            .one()


        context['camera'] = camera

        if self.indi_allsky_config.get('PRIVACY_MODE'):
            context['owner'] = 'Private'
        else:
            context['owner'] = camera.owner


        context['camera_cfa'] = constants.CFA_MAP_STR[camera.cfa]
        context['lensAperture'] = camera.lensFocalLength / camera.lensFocalRatio


        camera_width_mm = camera.width * camera.pixelSize / 1000.0
        camera_height_mm = camera.height * camera.pixelSize / 1000.0
        camera_diagonal_mm = math.hypot(camera_width_mm, camera_height_mm)

        context['camera_width_mm'] = camera_width_mm
        context['camera_height_mm'] = camera_height_mm
        context['camera_diagonal_mm'] = camera_diagonal_mm


        arcsec_pixel = camera.pixelSize / camera.lensFocalLength * 206.2648
        context['arcsec_pixel'] = arcsec_pixel
        context['dms_pixel'] = self.decdeg2dms(arcsec_pixel / 3600.0)
        context['arcsec_um'] = arcsec_pixel / camera.pixelSize
        context['deg2_px'] = (arcsec_pixel / 3600) ** 2


        image_circle_diameter = int(camera.lensImageCircle)  # might be null
        context['image_circle_diameter'] = image_circle_diameter
        context['image_circle_diameter_mm'] = image_circle_diameter * camera.pixelSize / 1000.0


        # since the arcsec/px increases near the edges of the image, this factor tries to account for that
        arcsec_pix_factor = 1.2

        if image_circle_diameter <= camera.width:
            arcsec_fov_width = image_circle_diameter * arcsec_pixel * arcsec_pix_factor
        else:
            arcsec_fov_width = camera.width * arcsec_pixel * arcsec_pix_factor

        if image_circle_diameter <= camera.height:
            arcsec_fov_height = image_circle_diameter * arcsec_pixel * arcsec_pix_factor
        else:
            arcsec_fov_height = camera.height * arcsec_pixel * arcsec_pix_factor

        camera_diagonal = math.hypot(camera.width, camera.height)  # this cannot be used to calculate distance
        if image_circle_diameter <= camera_diagonal:
            arcsec_fov_diagonal = image_circle_diameter * arcsec_pixel * arcsec_pix_factor
        else:
            arcsec_fov_diagonal = camera_diagonal * arcsec_pixel * arcsec_pix_factor


        #context['arcsec_fov_width'] = arcsec_fov_width
        #context['arcsec_fov_height'] = arcsec_fov_height

        context['deg_fov_width'] = arcsec_fov_width / 3600
        context['deg_fov_height'] = arcsec_fov_height / 3600
        context['deg_fov_diagonal'] = arcsec_fov_diagonal / 3600

        return context


    def decdeg2dms(self, dd):
        is_positive = dd >= 0
        dd = abs(dd)
        minutes, seconds = divmod(dd * 3600, 60)
        degrees, minutes = divmod(minutes, 60)
        degrees = degrees if is_positive else -degrees
        return degrees, minutes, seconds


class AjaxImageExcludeView(BaseView):
    methods = ['POST']
    decorators = [login_required]


    def __init__(self, **kwargs):
        super(AjaxImageExcludeView, self).__init__(**kwargs)


    def dispatch_request(self):
        if not current_user.is_admin:
            return jsonify({}), 400

        form_image_exclude = IndiAllskyImageExcludeForm(data=request.json)

        if not form_image_exclude.validate():
            form_errors = form_image_exclude.errors  # this must be a property
            return jsonify(form_errors), 400


        camera_id = int(request.json['CAMERA_ID'])
        image_id = int(request.json['EXCLUDE_IMAGE_ID'])
        exclude = bool(request.json['EXCLUDE_EXCLUDE'])


        try:
            image = IndiAllSkyDbImageTable.query\
                .join(IndiAllSkyDbImageTable.camera)\
                .filter(
                    and_(
                        IndiAllSkyDbImageTable.id == image_id,
                        IndiAllSkyDbCameraTable.id == camera_id,
                    )
                )\
                .one()
        except NoResultFound:
            app.logger.error('Image not found')
            return jsonify({}), 400


        image.exclude = exclude
        db.session.commit()

        data = {
            'exclude' : exclude,
        }

        return jsonify(data)


class AjaxUploadYoutubeView(BaseView):
    methods = ['POST']
    decorators = [login_required]


    def __init__(self, **kwargs):
        super(AjaxUploadYoutubeView, self).__init__(**kwargs)


    def dispatch_request(self):
        camera_id = int(request.json['CAMERA_ID'])
        video_id = int(request.json['VIDEO_ID'])
        asset_type = int(request.json['ASSET_TYPE'])


        if asset_type == constants.VIDEO:
            table = IndiAllSkyDbVideoTable
            asset_label = 'Timelapse'
        elif asset_type == constants.MINI_VIDEO:
            table = IndiAllSkyDbMiniVideoTable
            asset_label = 'Mini Timelapse'
        elif asset_type == constants.STARTRAIL_VIDEO:
            table = IndiAllSkyDbStarTrailsVideoTable
            asset_label = 'Star Trails Timelapse'
        elif asset_type == constants.PANORAMA_VIDEO:
            table = IndiAllSkyDbPanoramaVideoTable
            asset_label = 'Panorama Timelapse'
        else:
            app.logger.error('Unknown video type: %d', video_id)
            return jsonify(), 400


        try:
            video_entry = table.query\
                .join(table.camera)\
                .filter(
                    and_(
                        table.id == video_id,
                        IndiAllSkyDbCameraTable.id == camera_id,
                    )
                )\
                .one()
        except NoResultFound:
            app.logger.error('Video not found')
            return jsonify({}), 400


        metadata = {
            'dayDate' : video_entry.dayDate.strftime('%Y%m%d'),
            'night'   : video_entry.night,
            'asset_label' : asset_label,
        }


        jobdata = {
            'action'      : constants.TRANSFER_YOUTUBE,
            'model'       : video_entry.__class__.__name__,
            'id'          : video_entry.id,
            'metadata'    : metadata,
        }


        upload_task = IndiAllSkyDbTaskQueueTable(
            queue=TaskQueueQueue.UPLOAD,
            state=TaskQueueState.MANUAL,
            priority=100,
            data=jobdata,
        )

        db.session.add(upload_task)
        db.session.commit()

        message = {
            'success-message' : 'Upload task submitted',
        }

        return jsonify(message)


class CameraSimulatorView(TemplateView):
    page_title = 'Camera Simulator'

    def get_context(self):
        context = super(CameraSimulatorView, self).get_context()

        lens = str(request.args.get('lens', 'zwo_f1.2_2.5mm_1-2'))
        sensor = str(request.args.get('sensor', 'imx477'))
        offset_x = int(request.args.get('offset_x', 0))
        offset_y = int(request.args.get('offset_y', 0))

        form_data = {
            'LENS_SELECT'   : lens,
            'SENSOR_SELECT' : sensor,
            'OFFSET_X'      : offset_x,
            'OFFSET_Y'      : offset_y,
        }

        context['form_camera_simulator'] = IndiAllskyCameraSimulatorForm(data=form_data)

        return context


class TimelapseImageView(TemplateView):
    model = IndiAllSkyDbImageTable
    page_title = 'Timelapse Image'
    file_view = 'indi_allsky.timelapse_image_view'
    decorators = [login_optional_media]


    def get_context(self):
        context = super(TimelapseImageView, self).get_context()

        context['file_view'] = self.file_view

        image_id = int(request.args.get('id', -1))

        if image_id == -1:
            latest_image = self.model.query\
                .order_by(
                    self.model.dayDate.desc(),
                    self.model.createDate.desc(),
                )\
                .first()

            if latest_image:
                image_id = latest_image.id


        context['image_id'] = image_id


        #createDate = datetime.fromtimestamp(timestamp)
        #app.logger.info('Timestamp date: %s', createDate)


        image_q = self.model.query\
            .filter(self.model.id == image_id)


        local = True  # default to local assets
        if self.web_nonlocal_images:
            if self.web_local_images_admin and self.verify_admin_network():
                pass
            else:
                local = False

                # Do not serve local assets
                image_q = image_q\
                    .filter(
                        or_(
                            self.model.remote_url != sa_null(),
                            self.model.s3_key != sa_null(),
                        )
                    )

        #app.logger.info('SQL: %s', str(image_q))

        try:
            image = image_q.one()
        except NoResultFound:
            app.logger.error('Image not found')
            context['timeofday'] = ''
            context['createDate_full'] = 'Image not found'
            context['image_url'] = ''
            return context


        if image.night:
            context['timeofday'] = 'Night'
        else:
            context['timeofday'] = 'Day'

        context['createDate_full'] = image.dayDate.strftime('%B %d, %Y - %H:%M:%S')
        context['image_url'] = image.getUrl(s3_prefix=self.s3_prefix, local=local)


        return context


class PanoramaImageView(TimelapseImageView):
    model = IndiAllSkyDbPanoramaImageTable
    page_title = 'Panorama Image'
    file_view = 'indi_allsky.panorama_image_view'


class KeogramImageView(TimelapseImageView):
    model = IndiAllSkyDbKeogramTable
    page_title = 'Keogram'
    file_view = 'indi_allsky.keogram_image_view'


class StartrailImageView(TimelapseImageView):
    model = IndiAllSkyDbStarTrailsTable
    page_title = 'Startrail Image'
    file_view = 'indi_allsky.startrail_image_view'


class RawImageView(TimelapseImageView):
    model = IndiAllSkyDbRawImageTable
    page_title = 'RAW Image'
    file_view = 'indi_allsky.raw_image_view'


class TimelapseVideoView(TemplateView):
    model = IndiAllSkyDbVideoTable
    page_title = 'Timelapse Video'
    file_view = 'indi_allsky.timelapse_video_view'
    decorators = [login_optional_media]


    def get_context(self):
        context = super(TimelapseVideoView, self).get_context()

        context['file_view'] = self.file_view

        video_id = int(request.args.get('id', -1))

        if video_id == -1:
            latest_video = self.model.query\
                .order_by(
                    self.model.dayDate.desc(),
                    self.model.createDate.desc(),
                )\
                .first()

            if latest_video:
                video_id = latest_video.id


        context['video_id'] = video_id


        video_q = self.model.query\
            .filter(self.model.id == video_id)


        local = True  # default to local assets
        if self.web_nonlocal_images:
            if self.web_local_images_admin and self.verify_admin_network():
                pass
            else:
                local = False

                # Do not serve local assets
                video_q = video_q\
                    .filter(
                        or_(
                            self.model.remote_url != sa_null(),
                            self.model.s3_key != sa_null(),
                        )
                    )

        try:
            video = video_q.one()
        except NoResultFound:
            app.logger.error('Video not found')
            context['timeofday'] = ''
            context['dayDate_full'] = 'Video not found'
            context['video_url'] = ''
            return context


        if video.night:
            context['timeofday'] = 'Night'
        else:
            context['timeofday'] = 'Day'

        context['dayDate_full'] = video.dayDate.strftime('%B %d, %Y')
        context['video_url'] = video.getUrl(s3_prefix=self.s3_prefix, local=local)


        return context


class MiniTimelapseVideoView(TimelapseVideoView):
    model = IndiAllSkyDbMiniVideoTable
    page_title = 'Mini Timelapse'
    file_view = 'indi_allsky.mini_timelapse_video_view'


class StartrailVideoView(TimelapseVideoView):
    model = IndiAllSkyDbStarTrailsVideoTable
    page_title = 'Startrail Video'
    file_view = 'indi_allsky.startrail_video_view'


class PanoramaVideoView(TimelapseVideoView):
    model = IndiAllSkyDbPanoramaVideoTable
    page_title = 'Panorama Video'
    file_view = 'indi_allsky.panorama_video_view'


class MiniTimelapseGeneratorView(TemplateView):
    decorators = [login_required]

    page_title = 'Mini Timelapse'
    image_loop_view = 'indi_allsky.js_image_loop_view'

    def get_context(self):
        context = super(MiniTimelapseGeneratorView, self).get_context()

        image_id = int(request.args.get('image_id', 0))

        if image_id:
            image_entry = IndiAllSkyDbImageTable.query\
                .join(IndiAllSkyDbImageTable.camera)\
                .filter(IndiAllSkyDbCameraTable.id == self.camera.id)\
                .filter(IndiAllSkyDbImageTable.id == image_id)\
                .one()
        else:
            # load last image
            image_entry = IndiAllSkyDbImageTable.query\
                .join(IndiAllSkyDbImageTable.camera)\
                .filter(IndiAllSkyDbCameraTable.id == self.camera.id)\
                .order_by(IndiAllSkyDbImageTable.createDate.desc())\
                .first()


        context['image_loop_view'] = self.image_loop_view

        context['timestamp'] = int(image_entry.createDate.timestamp())


        form_data = {
            'CAMERA_ID'             : self.camera.id,
            'IMAGE_ID'              : image_id,
            'PRE_SECONDS_SELECT'    : '240',
            'POST_SECONDS_SELECT'   : '120',
            'FRAMERATE_SELECT'      : '10',
        }

        context['form_mini_timelapse'] = IndiAllskyMiniTimelapseForm(data=form_data)

        return context


class AjaxMiniTimelapseGeneratorView(BaseView):
    methods = ['POST']
    decorators = [login_required]


    def __init__(self, **kwargs):
        super(AjaxMiniTimelapseGeneratorView, self).__init__(**kwargs)


    def dispatch_request(self):
        if not current_user.is_admin:
            json_data = {
                'failure-message' : 'User does not have permission to generate content',
            }
            return jsonify(json_data), 400


        image_id = int(request.json['IMAGE_ID'])
        camera_id = int(request.json['CAMERA_ID'])
        pre_seconds = int(request.json['PRE_SECONDS'])
        post_seconds = int(request.json['POST_SECONDS'])
        framerate = float(request.json['FRAMERATE'])
        note = str(request.json['NOTE'])


        # sanity check
        IndiAllSkyDbImageTable.query\
            .join(IndiAllSkyDbImageTable.camera)\
            .filter(IndiAllSkyDbCameraTable.id == camera_id)\
            .filter(IndiAllSkyDbImageTable.id == image_id)\
            .one()


        jobdata = {
            'action' : 'generateMiniVideo',
            'kwargs' : {
                'image_id'      : image_id,
                'camera_id'     : camera_id,
                'pre_seconds'   : pre_seconds,
                'post_seconds'  : post_seconds,
                'framerate'     : framerate,
                'note'          : note,
            },
        }


        task_mini_video = IndiAllSkyDbTaskQueueTable(
            queue=TaskQueueQueue.VIDEO,
            state=TaskQueueState.MANUAL,
            priority=100,
            data=jobdata,
        )

        db.session.add(task_mini_video)
        db.session.commit()

        message = {
            'success-message' : 'Job Submitted - Check the Mini Timelapses view in a few minutes',
        }

        return jsonify(message)


class FileSpaceUsageView(TemplateView):
    decorators = [login_required]

    page_title = 'File Space Usage'

    def get_context(self):
        context = super(FileSpaceUsageView, self).get_context()


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
            .join(IndiAllSkyDbThumbnailTable)\
            .filter(IndiAllSkyDbCameraTable.id == camera_id)\
            .filter(IndiAllSkyDbThumbnailTable.uuid == table.thumbnail_uuid)\
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


class ModernAdminCameraInfoView(ModernAdminContextMixin, CameraLensView):
    page_title = 'Modern Admin Camera Info'
    modern_admin_active_endpoint = 'indi_allsky.modern_admin_cameras_view'


class ModernAdminImageLagView(ModernAdminContextMixin, ImageLagView):
    page_title = 'Modern Admin Image Lag'
    modern_admin_active_endpoint = 'indi_allsky.modern_admin_cameras_view'


class ModernAdminAduHistoryView(ModernAdminContextMixin, RollingAduView):
    page_title = 'Modern Admin ADU History'
    modern_admin_active_endpoint = 'indi_allsky.modern_admin_cameras_view'


class ModernAdminFileSpaceUsageView(ModernAdminContextMixin, FileSpaceUsageView):
    page_title = 'Modern Admin File Space Usage'
    modern_admin_active_endpoint = 'indi_allsky.modern_admin_storage_view'


class ModernAdminSqmView(ModernAdminContextMixin, SqmView):
    page_title = 'Modern Admin SQM'
    modern_admin_active_endpoint = 'indi_allsky.modern_admin_observatory_view'

    def get_context(self):
        context = super(ModernAdminSqmView, self).get_context()
        image_data = self.get_image_data()
        camera_now_minus_30m = self.camera_now - timedelta(minutes=30)

        sqm_summary = IndiAllSkyDbImageTable.query\
            .with_entities(
                func.max(IndiAllSkyDbImageTable.sqm).label('sqm_max'),
                func.min(IndiAllSkyDbImageTable.sqm).label('sqm_min'),
                func.avg(IndiAllSkyDbImageTable.sqm).label('sqm_avg'),
                func.max(IndiAllSkyDbImageTable.stars).label('stars_max'),
                func.min(IndiAllSkyDbImageTable.stars).label('stars_min'),
                func.avg(IndiAllSkyDbImageTable.stars).label('stars_avg'),
            )\
            .join(IndiAllSkyDbImageTable.camera)\
            .filter(IndiAllSkyDbCameraTable.id == self.camera.id)\
            .filter(IndiAllSkyDbImageTable.createDate > camera_now_minus_30m)\
            .first()

        context['modern_admin_sqm'] = image_data.get('sqm', 0.0)
        context['modern_admin_stars'] = image_data.get('stars', 0)
        context['modern_admin_moon_phase'] = image_data.get('moon_phase', 0.0)
        context['modern_admin_sqm_summary'] = sqm_summary

        return context


class ModernAdminChartsView(ModernAdminContextMixin, ChartView):
    page_title = 'Modern Admin Charts'
    modern_admin_active_endpoint = 'indi_allsky.modern_admin_observatory_view'


class ModernAdminSensorPanelView(ModernAdminContextMixin, SensorPanelView):
    page_title = 'Modern Admin Sensor Panel'
    modern_admin_active_endpoint = 'indi_allsky.modern_admin_observatory_view'


class ModernAdminSystemInfoView(ModernAdminContextMixin, SystemInfoView):
    page_title = 'Modern Admin System Info'
    modern_admin_active_endpoint = 'indi_allsky.modern_admin_system_view'


class ModernAdminSupportInfoView(ModernAdminContextMixin, SupportInfoView):
    page_title = 'Modern Admin Support Info'
    modern_admin_active_endpoint = 'indi_allsky.modern_admin_system_view'


class ModernAdminLoopView(ModernAdminContextMixin, ImageLoopImgView):
    page_title = 'Modern Admin Loop'
    modern_admin_active_endpoint = 'indi_allsky.modern_admin_view'


class ModernAdminRealtimeKeogramView(ModernAdminContextMixin, RealtimeKeogramView):
    page_title = 'Modern Admin Realtime Keogram'
    modern_admin_active_endpoint = 'indi_allsky.modern_admin_observatory_view'

    def get_context(self):
        context = super(ModernAdminRealtimeKeogramView, self).get_context()
        keogram_uri = context.get('keogram_uri')
        if keogram_uri:
            context['keogram_uri'] = ModernAdminMediaListView.normalize_media_url(self, keogram_uri)

        return context


class ModernAdminLongTermKeogramView(ModernAdminContextMixin, TemplateView):
    page_title = 'Modern Admin Long Term Keogram'
    modern_admin_active_endpoint = 'indi_allsky.modern_admin_observatory_view'

    def get_context(self):
        context = super(ModernAdminLongTermKeogramView, self).get_context()
        context['keogram_age'] = ''
        context['keogram_uri'] = ''

        longterm_keogram_image_p = Path(app.config['INDI_ALLSKY_IMAGE_FOLDER']).joinpath(
            'ccd_{0:s}'.format(self.camera.uuid),
            'longterm_keogram.jpg',
        )
        if longterm_keogram_image_p.is_file():
            image_age_s = time.time() - longterm_keogram_image_p.stat().st_mtime
            image_age_days = int(image_age_s / 86400)
            image_age_hours = int((image_age_s % 86400) / 3600)
            image_age_minutes = int(((image_age_s % 86400) % 3600) / 60)

            context['keogram_age'] = 'Generated {0:d} days, {1:d} hours, {2:d} minutes ago'.format(
                image_age_days,
                image_age_hours,
                image_age_minutes,
            )
            context['keogram_uri'] = str(Path('images').joinpath('ccd_{0:s}'.format(self.camera.uuid), 'longterm_keogram.jpg'))

        keogram_uri = context.get('keogram_uri')
        if keogram_uri:
            context['keogram_uri'] = ModernAdminMediaListView.normalize_media_url(self, keogram_uri)

        try:
            context['modern_admin_longterm_rows'] = IndiAllSkyDbLongTermKeogramTable.query\
                .join(IndiAllSkyDbLongTermKeogramTable.camera)\
                .filter(IndiAllSkyDbCameraTable.id == self.camera.id)\
                .order_by(IndiAllSkyDbLongTermKeogramTable.ts.desc())\
                .limit(8)\
                .all()
        except Exception as e:
            app.logger.error('Error loading modern admin long term keogram rows: %s', str(e))
            context['modern_admin_longterm_rows'] = list()

        return context


class ModernAdminDarkLibraryView(ModernAdminContextMixin, TemplateView):
    page_title = 'Modern Admin Dark Library'
    modern_admin_active_endpoint = 'indi_allsky.modern_admin_cameras_view'

    def get_context(self):
        context = super(ModernAdminDarkLibraryView, self).get_context()

        context['darkframe_list'] = self.serialize_calibration_rows(
            IndiAllSkyDbDarkFrameTable,
            order_model=IndiAllSkyDbDarkFrameTable,
        )
        context['bpm_list'] = self.serialize_calibration_rows(
            IndiAllSkyDbBadPixelMapTable,
            order_model=IndiAllSkyDbBadPixelMapTable,
        )

        return context


    def serialize_calibration_rows(self, model, order_model):
        try:
            rows = model.query\
                .join(model.camera)\
                .filter(IndiAllSkyDbCameraTable.id == self.camera.id)\
                .order_by(
                    IndiAllSkyDbCameraTable.id.desc(),
                    order_model.gain.asc(),
                    order_model.exposure.asc(),
                )\
                .all()
        except Exception as e:
            app.logger.error('Error loading modern admin calibration rows: %s', str(e))
            return list()

        row_list = list()
        for row in rows:
            try:
                file_size = row.getFilesystemPath().stat().st_size
            except Exception:
                file_size = 0

            try:
                row_url = ModernAdminMediaListView.normalize_media_url(self, row.getUrl())
            except Exception as e:
                app.logger.error('Error determining modern admin calibration URL: %s', str(e))
                row_url = None

            row_list.append({
                'id'         : row.id,
                'createDate' : row.createDate,
                'active'     : row.active,
                'resolution' : '{0:d}x{1:d}'.format(row.width, row.height) if row.width and row.height else 'Unknown',
                'bitdepth'   : row.bitdepth,
                'gain'       : row.gain,
                'exposure'   : row.exposure,
                'binmode'    : row.binmode,
                'temp'       : row.temp,
                'adu'        : row.adu,
                'hot_pixels' : row.data.get('hot_pixels', -1) if row.data else -1,
                'method'     : row.data.get('method', '') if row.data else '',
                'url'        : row_url,
                'size_mb'    : file_size / 1024 / 1024,
            })

        return row_list


class ModernAdminAstroPanelView(ModernAdminContextMixin, TemplateView):
    page_title = 'Modern Admin Astropanel'
    modern_admin_active_endpoint = 'indi_allsky.modern_admin_observatory_view'


class ModernAdminVirtualSkyView(ModernAdminContextMixin, VirtualSkyView):
    page_title = 'Modern Admin VirtualSky'
    modern_admin_active_endpoint = 'indi_allsky.modern_admin_observatory_view'


class ModernAdminLogView(ModernAdminContextMixin, LogView):
    page_title = 'Modern Admin Log'
    modern_admin_active_endpoint = 'indi_allsky.modern_admin_system_view'


class ModernAdminMaskView(ModernAdminContextMixin, MaskView):
    page_title = 'Modern Admin Mask Base'
    modern_admin_active_endpoint = 'indi_allsky.modern_admin_cameras_view'

    def get_context(self):
        context = super(ModernAdminMaskView, self).get_context()
        mask_image_uri = context.get('mask_image_uri')
        if mask_image_uri:
            context['mask_image_uri'] = ModernAdminMediaListView.normalize_media_url(self, mask_image_uri)

        return context


class ModernAdminMediaListView(ModernAdminContextMixin, TemplateView):
    page_title = 'Modern Admin Media'
    modern_admin_section = 'Media'
    modern_admin_description = 'Recent media captured by this camera.'
    modern_admin_media_kind = 'image'
    modern_admin_media_layout = 'grid'
    modern_admin_media_model = None
    modern_admin_media_limit = 24

    def get_context(self):
        context = super(ModernAdminMediaListView, self).get_context()

        media_entries = self.get_media_entries()
        media_items = list()

        for media_entry in media_entries:
            try:
                media_items.append(self.serialize_media_entry(media_entry))
            except Exception as e:
                app.logger.error('Error serializing modern admin media entry %s: %s', getattr(media_entry, 'id', 'unknown'), str(e))

        context['modern_admin_section'] = self.modern_admin_section
        context['modern_admin_description'] = self.modern_admin_description
        context['modern_admin_media_kind'] = self.modern_admin_media_kind
        context['modern_admin_media_layout'] = self.modern_admin_media_layout
        context['modern_admin_media_items'] = media_items
        context['modern_admin_featured_media'] = media_items[0] if media_items else None

        return context


    def get_media_entries(self):
        if not self.modern_admin_media_model:
            return list()

        if not getattr(self, 'camera', None):
            return list()

        # Read-only media inventory; reuses the existing DB models behind classic viewers.
        try:
            return self.modern_admin_media_model.query\
                .join(self.modern_admin_media_model.camera)\
                .filter(IndiAllSkyDbCameraTable.id == self.camera.id)\
                .order_by(self.modern_admin_media_model.createDate.desc())\
                .limit(self.modern_admin_media_limit)\
                .all()
        except Exception as e:
            app.logger.error('Error querying modern admin media entries: %s', str(e))
            return list()


    def serialize_media_entry(self, media_entry):
        create_date = getattr(media_entry, 'createDate', None)
        day_date = getattr(media_entry, 'dayDate', None)
        file_size = getattr(media_entry, 'fileSize', None)
        width = getattr(media_entry, 'width', None)
        height = getattr(media_entry, 'height', None)
        frames = getattr(media_entry, 'frames', None)

        return {
            'id'          : media_entry.id,
            'camera_id'   : getattr(media_entry, 'camera_id', None),
            'title'       : self.format_media_title(media_entry),
            'url'         : self.get_media_url(media_entry),
            'preview_url' : self.get_media_preview_url(media_entry),
            'filename'    : Path(media_entry.filename).name,
            'created'     : create_date.strftime('%Y-%m-%d %H:%M:%S') if create_date else 'Unknown date',
            'day_date'    : day_date.strftime('%Y-%m-%d') if day_date else 'Unknown day',
            'age'         : self.format_media_age(create_date) if create_date else 'Unknown age',
            'timeofday'   : self.format_media_timeofday(media_entry),
            'size'        : self.format_media_size(file_size) if file_size else 'Unknown size',
            'dimensions'  : '{0:d} x {1:d}'.format(width, height) if width and height else 'Unknown dimensions',
            'frames'      : '{0:d} frames'.format(frames) if frames else None,
            'success'     : getattr(media_entry, 'success', None),
        }


    def get_media_url(self, media_entry):
        local = True
        if self.web_nonlocal_images:
            if self.web_local_images_admin and self.verify_admin_network():
                pass
            else:
                local = False
                if not media_entry.remote_url and not media_entry.s3_key:
                    return None

        try:
            return self.normalize_media_url(media_entry.getUrl(s3_prefix=self.s3_prefix, local=local))
        except Exception as e:
            app.logger.error('Error determining modern admin media URL: %s', str(e))
            return None


    def get_media_preview_url(self, media_entry):
        return self.get_media_url(media_entry)


    def normalize_media_url(self, media_url):
        if not media_url:
            return None

        media_url_str = str(media_url)
        if media_url_str.startswith(('http://', 'https://', '/')):
            return media_url_str

        media_url_p = Path(media_url_str)
        if media_url_p.parts and media_url_p.parts[0] == 'images':
            return url_for('indi_allsky.images_folder', path=str(Path(*media_url_p.parts[1:])))

        return media_url_str


    def format_media_title(self, media_entry):
        create_date = getattr(media_entry, 'createDate', None)
        if create_date:
            return create_date.strftime('%b %d, %H:%M')

        day_date = getattr(media_entry, 'dayDate', None)
        if day_date:
            return day_date.strftime('%Y-%m-%d')

        return Path(media_entry.filename).name


    def format_media_timeofday(self, media_entry):
        if not hasattr(media_entry, 'night'):
            return 'Captured'

        if media_entry.night:
            return 'Night'

        return 'Day'


    def format_media_age(self, create_date):
        age_s = max(0, int((self.camera_now - create_date).total_seconds()))

        if age_s < 60:
            return '{0:d}s ago'.format(age_s)
        elif age_s < 3600:
            return '{0:d}m ago'.format(int(age_s / 60))

        return '{0:d}h ago'.format(int(age_s / 3600))


    def format_media_size(self, size_b):
        size = float(size_b)
        for unit in ('B', 'KB', 'MB', 'GB'):
            if size < 1024.0:
                return '{0:0.1f} {1:s}'.format(size, unit)
            size /= 1024.0

        return '{0:0.1f} TB'.format(size)


class ModernAdminMediaGalleryView(ModernAdminMediaListView):
    page_title = 'Modern Admin Gallery'
    modern_admin_section = 'Gallery'
    modern_admin_description = 'Scrollable image archive from all cameras.'
    modern_admin_media_model = IndiAllSkyDbImageTable
    modern_admin_media_kind = 'image'
    modern_admin_media_layout = 'gallery'
    modern_admin_media_limit = 72

    def get_context(self):
        context = super(ModernAdminMediaGalleryView, self).get_context()
        camera_filters = self.get_gallery_camera_filters()
        selected_filter = self.get_selected_gallery_camera_filter(camera_filters)
        context['modern_admin_gallery_page_url'] = url_for('indi_allsky.modern_admin_media_gallery_page_view')
        context['modern_admin_gallery_limit'] = self.modern_admin_media_limit
        context['modern_admin_gallery_next_cursor'] = context['modern_admin_media_items'][-1]['id'] if context['modern_admin_media_items'] else None
        context['modern_admin_gallery_has_more'] = len(context['modern_admin_media_items']) == self.modern_admin_media_limit
        context['modern_admin_gallery_camera_filters'] = camera_filters
        context['modern_admin_gallery_selected_filter'] = selected_filter

        return context


    def get_media_entries(self):
        selected_filter = self.get_selected_gallery_camera_filter()
        return self.get_media_entries_page(
            limit=self.modern_admin_media_limit,
            camera_id=selected_filter.get('camera_id'),
        )


    def get_media_entries_page(self, limit=72, before_id=None, camera_id=None):
        query = self.modern_admin_media_model.query\
            .join(self.modern_admin_media_model.camera)

        if camera_id is not None:
            query = query.filter(IndiAllSkyDbCameraTable.id == camera_id)

        if before_id:
            cursor_entry = self.modern_admin_media_model.query\
                .filter(self.modern_admin_media_model.id == before_id)\
                .first()

            if not cursor_entry:
                return list()

            query = query.filter(or_(
                self.modern_admin_media_model.createDate < cursor_entry.createDate,
                and_(
                    self.modern_admin_media_model.createDate == cursor_entry.createDate,
                    self.modern_admin_media_model.id < cursor_entry.id,
                ),
            ))

        return query\
            .order_by(self.modern_admin_media_model.createDate.desc())\
            .order_by(self.modern_admin_media_model.id.desc())\
            .limit(limit + 1)\
            .all()


    def get_gallery_camera_filters(self):
        filters = [{
            'label'      : 'All Cameras',
            'profile_id' : '',
            'camera_id'  : None,
            'active'     : False,
        }]

        camera_rows = self.get_gallery_filter_camera_rows()
        profile_configs = self.get_gallery_filter_profiles()
        used_camera_ids = set()

        for profile_index, profile_config in enumerate(profile_configs):
            camera_id = self.get_gallery_profile_camera_id(profile_config, camera_rows, profile_index)
            if camera_id is None or camera_id in used_camera_ids:
                continue

            profile_id = str(profile_config.get('profile_id') or profile_config.get('id') or 'profile-{0:d}'.format(profile_index + 1))
            filters.append({
                'label'      : self.get_gallery_profile_label(profile_config, camera_id),
                'profile_id' : profile_id,
                'camera_id'  : camera_id,
                'active'     : False,
            })
            used_camera_ids.add(camera_id)

        if len(filters) == 1:
            for camera in camera_rows:
                filters.append({
                    'label'      : str(camera.friendlyName or camera.name or 'Camera {0:d}'.format(camera.id)),
                    'profile_id' : '',
                    'camera_id'  : camera.id,
                    'active'     : False,
                })

        return filters


    def get_selected_gallery_camera_filter(self, camera_filters=None):
        if camera_filters is None:
            camera_filters = self.get_gallery_camera_filters()

        selected_profile_id = str(request.args.get('profile_id', '') or '')
        selected_camera_id = request.args.get('camera_id', type=int)

        selected_filter = camera_filters[0]
        if selected_profile_id:
            for camera_filter in camera_filters:
                if camera_filter.get('profile_id') == selected_profile_id:
                    selected_filter = camera_filter
                    break
        elif selected_camera_id:
            for camera_filter in camera_filters:
                if camera_filter.get('camera_id') == selected_camera_id:
                    selected_filter = camera_filter
                    break
            else:
                selected_filter = {
                    'label'      : 'Camera {0:d}'.format(selected_camera_id),
                    'profile_id' : '',
                    'camera_id'  : selected_camera_id,
                    'active'     : False,
                }
                camera_filters.append(selected_filter)

        for camera_filter in camera_filters:
            camera_filter['active'] = camera_filter is selected_filter

        return selected_filter


    def get_gallery_filter_profiles(self):
        multi_camera_config = self.indi_allsky_config.get('MULTI_CAMERA') or {}
        profile_configs = multi_camera_config.get('profiles') or []
        if not isinstance(profile_configs, list):
            return list()

        return [
            profile_config
            for profile_config in profile_configs
            if isinstance(profile_config, dict)
        ]


    def get_gallery_filter_camera_rows(self):
        try:
            return IndiAllSkyDbCameraTable.query\
                .filter(IndiAllSkyDbCameraTable.hidden == False)\
                .order_by(IndiAllSkyDbCameraTable.id.asc())\
                .all()
        except Exception as e:
            app.logger.error('Error reading modern admin gallery camera filters: %s', str(e))
            return list()


    def get_gallery_profile_camera_id(self, profile_config, camera_rows, profile_index):
        for key in ('db_camera_id', 'camera_db_id', 'camera_id'):
            if key not in profile_config:
                continue

            try:
                return int(profile_config[key])
            except (TypeError, ValueError):
                continue

        matched_camera = self.get_gallery_profile_camera_match(profile_config, camera_rows)
        if matched_camera:
            return matched_camera.id

        if profile_index < len(camera_rows):
            return camera_rows[profile_index].id

        return None


    def get_gallery_profile_camera_match(self, profile_config, camera_rows):
        profile_terms = set()
        for key in ('profile_id', 'id', 'label', 'camera_name', 'camera_interface', 'indi_camera_name'):
            value = profile_config.get(key)
            if value:
                profile_terms.add(str(value).strip().lower())

        nested_indi = profile_config.get('indi') or {}
        if isinstance(nested_indi, dict):
            value = nested_indi.get('camera_name')
            if value:
                profile_terms.add(str(value).strip().lower())

        if not profile_terms:
            return None

        for camera in camera_rows:
            camera_terms = (
                camera.friendlyName,
                camera.name,
                camera.name_alt1,
                camera.name_alt2,
                camera.driver,
            )
            normalized_camera_terms = [
                str(term).strip().lower()
                for term in camera_terms
                if term
            ]

            for profile_term in profile_terms:
                for camera_term in normalized_camera_terms:
                    if profile_term == camera_term or profile_term in camera_term or camera_term in profile_term:
                        return camera

        return None


    def get_gallery_profile_label(self, profile_config, camera_id):
        label = profile_config.get('label') or profile_config.get('camera_name')
        if label:
            return str(label)

        label = profile_config.get('profile_id') \
            or profile_config.get('id') \
            or profile_config.get('camera_interface') \
            or 'Camera {0:d}'.format(camera_id)

        return self.format_gallery_filter_label(label)


    def format_gallery_filter_label(self, label):
        label_str = str(label)
        parts = [
            part
            for part in re.split(r'[-_\s]+', label_str)
            if part
        ]
        if not parts:
            return label_str

        formatted_parts = list()
        for part in parts:
            part_lower = part.lower()
            if part_lower.startswith(('imx', 'asi')) and any(character.isdigit() for character in part_lower):
                formatted_parts.append(part.upper())
            else:
                formatted_parts.append(part.capitalize())

        return ' '.join(formatted_parts)


    def get_media_preview_url(self, media_entry):
        if not media_entry.thumbnail_uuid:
            return self.get_media_url(media_entry)

        try:
            thumbnail_entry = IndiAllSkyDbThumbnailTable.query\
                .filter(IndiAllSkyDbThumbnailTable.uuid == media_entry.thumbnail_uuid)\
                .one()
        except NoResultFound:
            return self.get_media_url(media_entry)

        local = True
        if self.web_nonlocal_images:
            if self.web_local_images_admin and self.verify_admin_network():
                pass
            else:
                local = False
                if not thumbnail_entry.remote_url and not thumbnail_entry.s3_key:
                    return self.get_media_url(media_entry)

        try:
            return self.normalize_media_url(thumbnail_entry.getUrl(s3_prefix=self.s3_prefix, local=local))
        except Exception as e:
            app.logger.error('Error determining modern admin thumbnail URL: %s', str(e))
            return self.get_media_url(media_entry)


class ModernAdminMediaGalleryPageView(ModernAdminMediaGalleryView):
    methods = ['GET']

    def dispatch_request(self):
        limit = request.args.get('limit', self.modern_admin_media_limit, type=int)
        before_id = request.args.get('before_id', type=int)
        camera_id = self.get_gallery_page_camera_id()

        if limit <= 0:
            limit = self.modern_admin_media_limit
        elif limit > 144:
            limit = 144

        try:
            media_entries = self.get_media_entries_page(limit=limit, before_id=before_id, camera_id=camera_id)
        except Exception as e:
            app.logger.error('Error querying modern admin gallery page: %s', str(e))
            return jsonify({
                'images'      : list(),
                'has_more'    : False,
                'next_cursor' : None,
            }), 500

        has_more = len(media_entries) > limit
        media_entries = media_entries[:limit]

        images = list()
        for media_entry in media_entries:
            try:
                images.append(self.serialize_media_entry(media_entry))
            except Exception as e:
                app.logger.error('Error serializing modern admin gallery page entry %s: %s', getattr(media_entry, 'id', 'unknown'), str(e))

        return jsonify({
            'images'      : images,
            'has_more'    : has_more,
            'next_cursor' : images[-1]['id'] if has_more and images else None,
        })


    def get_gallery_page_camera_id(self):
        selected_profile_id = str(request.args.get('profile_id', '') or '')
        if selected_profile_id:
            for camera_filter in self.get_gallery_camera_filters():
                if camera_filter.get('profile_id') == selected_profile_id:
                    return camera_filter.get('camera_id')

            return None

        return request.args.get('camera_id', type=int)


class ModernAdminMediaImagesView(ModernAdminMediaListView):
    page_title = 'Modern Admin Images'
    modern_admin_section = 'Images'
    modern_admin_description = 'Latest individual image captures.'
    modern_admin_media_model = IndiAllSkyDbImageTable
    modern_admin_media_kind = 'image'
    modern_admin_media_layout = 'viewer'


class ModernAdminMediaTimelapsesView(ModernAdminMediaListView):
    page_title = 'Modern Admin Timelapses'
    modern_admin_section = 'Timelapses'
    modern_admin_description = 'Recent generated timelapse videos.'
    modern_admin_media_model = IndiAllSkyDbVideoTable
    modern_admin_media_kind = 'video'


class ModernAdminMediaMiniTimelapsesView(ModernAdminMediaListView):
    page_title = 'Modern Admin Mini-Timelapses'
    modern_admin_section = 'Mini-Timelapses'
    modern_admin_description = 'Recent short capture-window timelapses.'
    modern_admin_media_model = IndiAllSkyDbMiniVideoTable
    modern_admin_media_kind = 'video'


class ModernAdminMediaPanoramaView(ModernAdminMediaListView):
    page_title = 'Modern Admin Panorama'
    modern_admin_section = 'Panorama'
    modern_admin_description = 'Recent panorama image captures.'
    modern_admin_media_model = IndiAllSkyDbPanoramaImageTable
    modern_admin_media_kind = 'image'
    modern_admin_media_layout = 'viewer'


class ModernAdminMediaPanoramaLoopView(ModernAdminMediaListView):
    page_title = 'Modern Admin Panorama Loop'
    modern_admin_section = 'Panorama Loop'
    modern_admin_description = 'Recent panorama frames available for loop review.'
    modern_admin_media_model = IndiAllSkyDbPanoramaImageTable
    modern_admin_media_kind = 'image'
    modern_admin_media_layout = 'loop'


class ModernAdminMediaFitsView(ModernAdminMediaListView):
    page_title = 'Modern Admin FITS Viewer'
    modern_admin_section = 'FITS Viewer'
    modern_admin_description = 'Recent saved FITS image files.'
    modern_admin_media_model = IndiAllSkyDbFitsImageTable
    modern_admin_media_kind = 'fits'
    modern_admin_media_layout = 'viewer'

    def get_media_preview_url(self, media_entry):
        return url_for('indi_allsky.fits2jpeg_view', id=media_entry.id)


class LongTermKeogramView(TemplateView):
    page_title = 'Long Term Keogram'


    def get_context(self):
        context = super(LongTermKeogramView, self).get_context()

        data = {
            'CAMERA_ID' : self.camera.id
        }

        context['form_longterm_keogram'] = IndiAllskyLongTermKeogramForm(data=data)


        # Load cached longterm keogram if it exists
        longterm_keogram_image_p = Path(app.config['INDI_ALLSKY_IMAGE_FOLDER']).joinpath('ccd_{0:s}'.format(self.camera.uuid), 'longterm_keogram.jpg')
        if longterm_keogram_image_p.is_file():
            image_age_s = time.time() - longterm_keogram_image_p.stat().st_mtime

            image_age_days = int(image_age_s / 86400)
            image_age_hours = int((image_age_s % 86400) / 3600)
            image_age_minutes = int(((image_age_s % 86400) % 3600 ) / 60)

            context['keogram_age'] = 'Generated {0:d} days, {1:d} hours, {2:d} minutes ago'.format(image_age_days, image_age_hours, image_age_minutes)
            context['keogram_uri'] = str(Path('images').joinpath('ccd_{0:s}'.format(self.camera.uuid), 'longterm_keogram.jpg'))
        else:
            context['keogram_age'] = ''
            context['keogram_uri'] = ''


        return context


class JsonLongTermKeogramView(JsonView):
    methods = ['POST']
    decorators = [login_required]


    def dispatch_request(self):
        import cv2
        from PIL import Image

        form_longterm_keogram = IndiAllskyLongTermKeogramForm(data=request.json)

        if not form_longterm_keogram.validate():
            form_errors = form_longterm_keogram.errors  # this must be a property
            return jsonify(form_errors), 400


        camera_id = int(request.json['CAMERA_ID'])
        end = str(request.json['END_SELECT'])
        query_days = int(request.json['DAYS_SELECT'])
        period_pixels = int(request.json['PIXELS_SELECT'])
        alignment_seconds = int(request.json['ALIGNMENT_SELECT'])
        offset_seconds = int(request.json['OFFSET_SELECT'])
        reverse = bool(request.json['REVERSE'])
        label = bool(request.json['LABEL'])


        if query_days > 2000:
            # sanity check (more than 5 years)
            json_data = {
                'failure-message' : 'Try again',
            }
            return jsonify(json_data), 400


        if alignment_seconds < 5:
            # sanity check
            json_data = {
                'failure-message' : 'Try again',
            }
            return jsonify(json_data), 400

        if offset_seconds > 43200:
            # sanity check
            json_data = {
                'failure-message' : 'Try again',
            }
            return jsonify(json_data), 400


        self.cameraSetup(camera_id=camera_id)


        keogram_start = time.time()

        if end == 'today':
            tomorrow = datetime.now() + timedelta(hours=24)  # need to start noon tomorrow
            query_end_date = datetime.strptime(tomorrow.strftime('%Y%m%d_120000'), '%Y%m%d_%H%M%S')
            query_start_date = query_end_date - timedelta(days=query_days)
        elif end == 'thisyear':
            thisyear = datetime.now().year
            query_end_date = datetime.strptime('{0:d}1231_120000'.format(thisyear), '%Y%m%d_%H%M%S')
            query_start_date = query_end_date - timedelta(days=query_days)
        elif end == 'lastyear':
            lastyear = datetime.now().year - 1
            query_end_date = datetime.strptime('{0:d}1231_120000'.format(lastyear), '%Y%m%d_%H%M%S')
            query_start_date = query_end_date - timedelta(days=query_days)
        else:
            json_data = {
                'failure-message' : 'Invalid end selection',
            }
            return jsonify(json_data), 400


        from ..longTermKeogram import LongTermKeogramGenerator
        ltg_gen = LongTermKeogramGenerator(self.indi_allsky_config)
        ltg_gen.camera_id = self.camera.id
        ltg_gen.days = query_days
        ltg_gen.alignment_seconds = alignment_seconds
        ltg_gen.offset_seconds = offset_seconds
        ltg_gen.period_pixels = period_pixels
        ltg_gen.reverse = reverse
        ltg_gen.label = label

        keogram_data = ltg_gen.generate(query_start_date, query_end_date)


        jpg_compress_level = self.indi_allsky_config.get('IMAGE_FILE_COMPRESSION', {}).get('jpg', 95)
        #png_compress_level = self.indi_allsky_config.get('IMAGE_FILE_COMPRESSION', {}).get('png', 5)


        ### OpenCV
        #_, image_a = cv2.imencode('.png', keogram_data, [cv2.IMWRITE_PNG_COMPRESSION, png_compress_level])
        #image_buffer = io.BytesIO(image_a.tobytes())


        json_data = {
            'failure-message' : '',
        }


        ### pillow
        image_buffer = io.BytesIO()
        img = Image.fromarray(cv2.cvtColor(keogram_data, cv2.COLOR_BGR2RGB))
        img.save(image_buffer, format='JPEG', compress_level=jpg_compress_level)


        # Save longterm keogram so it can be cached and loaded later
        # It may take longer than 180 seconds to generate the keogram and the browser will stop
        #  waiting for the image and drop the connection.  The flask process will usually continue
        #  and should save the image to the filesystem
        longterm_keogram_image_p = Path(app.config['INDI_ALLSKY_IMAGE_FOLDER']).joinpath('ccd_{0:s}'.format(self.camera.uuid), 'longterm_keogram.jpg')

        try:
            with io.open(str(longterm_keogram_image_p), 'wb') as lt_image_f:
                app.logger.info('Writing keogram: %s', longterm_keogram_image_p)
                lt_image_f.write(image_buffer.getbuffer())
        except (PermissionError, FileNotFoundError) as e:
            app.logger.error('Creating keogram failed: %s', str(e))
            json_data['failure-message'] = 'Exception: {0:s}'.format(str(e))


        json_image_b64 = base64.b64encode(image_buffer.getvalue())


        keogram_elapsed_s = time.time() - keogram_start
        app.logger.warning('Long Term Keogram in %0.4f s', keogram_elapsed_s)


        json_data['image_b64'] = json_image_b64.decode('utf-8'),
        json_data['processing_time'] = round(keogram_elapsed_s, 3)
        json_data['success-message'] = ''


        return jsonify(json_data)


class NetworkManagerView(TemplateView):
    decorators = [login_required]
    page_title = 'Network'

    def get_context(self):
        context = super(NetworkManagerView, self).get_context()

        try:
            context['hostname'] = socket.gethostname().split('.')[0]
        except IndexError:
            context['hostname'] = 'UNKNOWN'


        try:
            # detect if network manager is available
            bus = dbus.SystemBus()
            bus.get_object(
                "org.freedesktop.NetworkManager",
                "/org/freedesktop/NetworkManager")
            nm_installed = True
        except dbus.exceptions.DBusException as e:
            app.logger.error('D-Bus Exception: %s', str(e))
            nm_installed = False


        context['nm_installed'] = nm_installed

        context['form_connections'] = IndiAllskyNetworkManagerForm()

        return context


class AjaxNetworkManagerView(BaseView):
    methods = ['POST']
    decorators = [login_required]


    nm_conn_states = {
        'Unknown'      : 0,
        'Activating'   : 1,
        'Active'       : 2,
        'Deactivating' : 3,
        'Not Active'   : 4,
    }


    def dispatch_request(self):
        if not current_user.is_admin:
            json_data = {
                'failure-message' : 'User does not have permission to access this resource',
            }
            return jsonify(json_data), 400


        command = str(request.json['COMMAND'])


        if command == 'deactivate':
            connection_uuid = str(request.json['CONNECTION'])
            return self.deactivateConnection(connection_uuid)

        elif command == 'delete':
            connection_uuid = str(request.json['CONNECTION'])
            return self.deleteConnection(connection_uuid)

        elif command == 'activate':
            connection_uuid = str(request.json['CONNECTION'])
            return self.activateConnection(connection_uuid)

        elif command == 'autostart':
            connection_uuid = str(request.json['CONNECTION'])
            return self.setAutostartConnection(connection_uuid, auto_connect=True)

        elif command == 'noautostart':
            connection_uuid = str(request.json['CONNECTION'])
            return self.setAutostartConnection(connection_uuid, auto_connect=False)

        elif command == 'incpriority':
            connection_uuid = str(request.json['CONNECTION'])
            return self.incrementConnectionPriority(connection_uuid)

        elif command == 'decpriority':
            connection_uuid = str(request.json['CONNECTION'])
            return self.decrementConnectionPriority(connection_uuid)

        elif command == 'powersavedisable':
            connection_uuid = str(request.json['CONNECTION'])
            return self.setPowersave(connection_uuid, powersave=False)

        elif command == 'powersaveenable':
            connection_uuid = str(request.json['CONNECTION'])
            return self.setPowersave(connection_uuid, powersave=True)

        elif command == 'scanap':
            interface = str(request.json['INTERFACE'])

            if not interface:
                return jsonify({
                    'failure-message' : 'No interface selected',
                }), 400

            return self.scanAPs(interface)

        elif command == 'connectap':
            interface = str(request.json['INTERFACE'])
            ap_path = str(request.json['AP_PATH'])
            psk = str(request.json['PSK'])
            priority = int(request.json['PRIORITY'])
            retries = int(request.json['RETRIES'])

            if not ap_path:
                return jsonify({
                    'failure-message' : 'No AP selected',
                }), 400

            return self.connectAP(interface, ap_path, psk, priority, retries)

        elif command == 'createhotspot':
            interface = str(request.json['INTERFACE'])
            ssid = str(request.json['SSID'])
            band = str(request.json['BAND'])
            psk = str(request.json['PSK'])
            nosecurity = bool(request.json['NOSECURITY'])

            if not interface:
                return jsonify({
                    'failure-message' : 'No interface selected',
                }), 400

            if not ssid:
                return jsonify({
                    'failure-message' : 'No SSID data',
                }), 400

            if band not in ('bg', 'a'):
                return jsonify({
                    'failure-message' : 'Invalid band selection',
                }), 400

            if nosecurity:
                # no encryption
                pass
            elif len(psk) < 8:
                return jsonify({
                    'failure-message' : 'PSK must be 8+ characters',
                }), 400


            return self.createHotspot(interface, ssid, band, psk, nosecurity=nosecurity)
        else:
            json_data = {
                'failure-message' : 'Unknown command',
            }
            return jsonify(json_data), 400


    def activateConnection(self, connection_uuid):
        bus = dbus.SystemBus()


        try:
            nm_settings = bus.get_object(
                "org.freedesktop.NetworkManager",
                "/org/freedesktop/NetworkManager/Settings")
        except dbus.exceptions.DBusException as e:
            app.logger.error('D-Bus Exception: %s', str(e))
            return jsonify({
                'failure-message' : 'D-Bus Exception: {0:s}'.format(str(e)),
            }), 400


        try:
            settings_path = self.getSettingsPath(bus, nm_settings, connection_uuid)
        except NotFound:
            app.logger.error('Connection settings not found')
            return jsonify({
                'failure-message' : 'Connection settings not found',
            }), 400


        settings = dbus.Interface(
            bus.get_object("org.freedesktop.NetworkManager", settings_path),
            "org.freedesktop.NetworkManager.Settings.Connection")


        settings_connection = dbus.Interface(
            settings,
            "org.freedesktop.NetworkManager.Settings.Connection")


        settings_dict = settings_connection.GetSettings()
        if settings_dict['connection']['type'] not in ('802-11-wireless', '802-3-ethernet'):
            return jsonify({
                'failure-message' : 'Only Ethernet and Wireless connections can be managed',
            }), 400


        nm = bus.get_object(
            "org.freedesktop.NetworkManager",
            "/org/freedesktop/NetworkManager")

        manager = dbus.Interface(
            nm,
            "org.freedesktop.NetworkManager")


        try:
            #device_path = nm_interface.GetDeviceByIpIface("xxx")
            connection_path = manager.ActivateConnection(settings_path, '/', '/')
        except dbus.exceptions.DBusException as e:
            app.logger.error('D-Bus Exception: %s', str(e))
            return jsonify({
                'failure-message' : 'D-Bus Exception: {0:s}'.format(str(e)),
            }), 400


        connection_props = dbus.Interface(
            bus.get_object("org.freedesktop.NetworkManager", connection_path),
            "org.freedesktop.DBus.Properties"
        )


        # Wait until connection is established. This may take a few seconds.
        app.logger.info("Waiting for connection")


        state = None
        for _ in range(30):
            time.sleep(1.0)
            # Loop until desired state is detected.
            try:
                state = connection_props.Get(
                    "org.freedesktop.NetworkManager.Connection.Active",
                    "State")
                #app.logger.info('Connection state: %d', int(state))
            except dbus.exceptions.DBusException as e:
                app.logger.error('D-Bus Exception: %s', str(e))

            if int(state) == self.nm_conn_states['Active']:
                app.logger.warning("Connection established!")
                break
        else:
            app.logger.error('Connection failed to activate')
            return jsonify({
                'failure-message' : 'Connection failed to activate',
            }), 400


        return jsonify({
            'success-message' : 'Connection Activated',
        })


    def deactivateConnection(self, connection_uuid):
        bus = dbus.SystemBus()


        try:
            nm_settings = bus.get_object(
                "org.freedesktop.NetworkManager",
                "/org/freedesktop/NetworkManager/Settings")
        except dbus.exceptions.DBusException as e:
            app.logger.error('D-Bus Exception: %s', str(e))
            return jsonify({
                'failure-message' : 'D-Bus Exception: {0:s}'.format(str(e)),
            }), 400


        try:
            settings_path = self.getSettingsPath(bus, nm_settings, connection_uuid)
        except NotFound:
            app.logger.error('Connection settings not found')
            return jsonify({
                'failure-message' : 'Connection settings not found',
            }), 400


        nm = bus.get_object(
            "org.freedesktop.NetworkManager",
            "/org/freedesktop/NetworkManager")


        try:
            conn_path = self.getActiveConnection(bus, nm, connection_uuid)
        except NotFound:
            app.logger.error('Active connection not found')
            return jsonify({
                'failure-message' : 'Active connection not found',
            }), 400


        settings = dbus.Interface(
            bus.get_object("org.freedesktop.NetworkManager", settings_path),
            "org.freedesktop.NetworkManager.Settings.Connection")


        settings_connection = dbus.Interface(
            settings,
            "org.freedesktop.NetworkManager.Settings.Connection")


        settings_dict = settings_connection.GetSettings()
        if settings_dict['connection']['type'] not in ('802-11-wireless', '802-3-ethernet'):
            return jsonify({
                'failure-message' : 'Only Ethernet and Wireless connections can be managed',
            }), 400



        manager = dbus.Interface(
            nm,
            "org.freedesktop.NetworkManager")


        try:
            manager.DeactivateConnection(conn_path)
        except dbus.exceptions.DBusException as e:
            app.logger.error('D-Bus Exception: %s', str(e))
            return jsonify({
                'failure-message' : 'Failed to deactivate connection: {0:s}'.format(str(e)),
            }), 400


        time.sleep(2.0)  # give some time for system to register

        return jsonify({
            'success-message' : 'Connection deactivated',
        })


    def deleteConnection(self, connection_uuid):
        bus = dbus.SystemBus()


        try:
            nm_settings = bus.get_object(
                "org.freedesktop.NetworkManager",
                "/org/freedesktop/NetworkManager/Settings")
        except dbus.exceptions.DBusException as e:
            app.logger.error('D-Bus Exception: %s', str(e))
            return jsonify({
                'failure-message' : 'D-Bus Exception: {0:s}'.format(str(e)),
            }), 400


        try:
            settings_path = self.getSettingsPath(bus, nm_settings, connection_uuid)
        except NotFound:
            app.logger.error('Connection settings not found')
            return jsonify({
                'failure-message' : 'Connection settings not found',
            }), 400


        settings = dbus.Interface(
            bus.get_object("org.freedesktop.NetworkManager", settings_path),
            "org.freedesktop.NetworkManager.Settings.Connection")


        nm = bus.get_object(
            "org.freedesktop.NetworkManager",
            "/org/freedesktop/NetworkManager")


        try:
            self.getActiveConnection(bus, nm, connection_uuid)
            return jsonify({
                'failure-message' : 'Cannot delete active connections',
            }), 400
        except NotFound:
            pass


        settings_connection = dbus.Interface(
            settings,
            "org.freedesktop.NetworkManager.Settings.Connection")


        settings_dict = settings_connection.GetSettings()
        if settings_dict['connection']['type'] not in ('802-11-wireless', '802-3-ethernet'):
            return jsonify({
                'failure-message' : 'Only Ethernet and Wireless connections can be managed',
            }), 400


        settings.Delete()


        time.sleep(2.0)  # give some time for system to register

        return jsonify({
            'success-message' : 'Connection deleted',
        })


    def setAutostartConnection(self, connection_uuid, auto_connect=True):
        bus = dbus.SystemBus()


        try:
            nm_settings = bus.get_object(
                "org.freedesktop.NetworkManager",
                "/org/freedesktop/NetworkManager/Settings")
        except dbus.exceptions.DBusException as e:
            app.logger.error('D-Bus Exception: %s', str(e))
            return jsonify({
                'failure-message' : 'D-Bus Exception: {0:s}'.format(str(e)),
            }), 400


        try:
            settings_path = self.getSettingsPath(bus, nm_settings, connection_uuid)
        except NotFound:
            app.logger.error('Connection settings not found')
            return jsonify({
                'failure-message' : 'Connection settings not found',
            }), 400


        settings = dbus.Interface(
            bus.get_object("org.freedesktop.NetworkManager", settings_path),
            "org.freedesktop.NetworkManager.Settings.Connection")


        settings_connection = dbus.Interface(
            settings,
            "org.freedesktop.NetworkManager.Settings.Connection")


        settings_dict = settings_connection.GetSettings()

        ### Here is the magic
        settings_dict['connection']['autoconnect'] = auto_connect


        try:
            settings_connection.Update(settings_dict)
        except dbus.exceptions.DBusException as e:
            app.logger.error('D-Bus Exception: %s', str(e))
            return jsonify({
                'failure-message' : 'Configure Failed: {0:s}'.format(str(e)),
            }), 400


        time.sleep(2.0)  # give some time for system to register

        return jsonify({
            'success-message' : 'Configure Successful',
        })


    def incrementConnectionPriority(self, connection_uuid, increment=10):
        bus = dbus.SystemBus()


        try:
            nm_settings = bus.get_object(
                "org.freedesktop.NetworkManager",
                "/org/freedesktop/NetworkManager/Settings")
        except dbus.exceptions.DBusException as e:
            app.logger.error('D-Bus Exception: %s', str(e))
            return jsonify({
                'failure-message' : 'D-Bus Exception: {0:s}'.format(str(e)),
            }), 400


        try:
            settings_path = self.getSettingsPath(bus, nm_settings, connection_uuid)
        except NotFound:
            app.logger.error('Connection settings not found')
            return jsonify({
                'failure-message' : 'Connection settings not found',
            }), 400


        settings = dbus.Interface(
            bus.get_object("org.freedesktop.NetworkManager", settings_path),
            "org.freedesktop.NetworkManager.Settings.Connection")


        settings_connection = dbus.Interface(
            settings,
            "org.freedesktop.NetworkManager.Settings.Connection")


        settings_dict = settings_connection.GetSettings()


        ### Here is the magic
        try:
            current_priority = int(settings_dict['connection']['autoconnect-priority'])
        except TypeError:
            current_priority = 0
        except ValueError:
            current_priority = 0
        except KeyError:
            current_priority = 0


        new_priority = current_priority + increment
        settings_dict['connection']['autoconnect-priority'] = new_priority


        try:
            settings_connection.Update(settings_dict)
        except dbus.exceptions.DBusException as e:
            app.logger.error('D-Bus Exception: %s', str(e))
            return jsonify({
                'failure-message' : 'Configure Failed: {0:s}'.format(str(e)),
            }), 400


        time.sleep(2.0)  # give some time for system to register

        return jsonify({
            'success-message' : 'Priority Updated',
        })


    def decrementConnectionPriority(self, connection_uuid, increment=-10):
        return self.incrementConnectionPriority(connection_uuid, increment=increment)


    def setPowersave(self, connection_uuid, powersave=False):
        bus = dbus.SystemBus()


        try:
            nm_settings = bus.get_object(
                "org.freedesktop.NetworkManager",
                "/org/freedesktop/NetworkManager/Settings")
        except dbus.exceptions.DBusException as e:
            app.logger.error('D-Bus Exception: %s', str(e))
            return jsonify({
                'failure-message' : 'D-Bus Exception: {0:s}'.format(str(e)),
            }), 400


        try:
            settings_path = self.getSettingsPath(bus, nm_settings, connection_uuid)
        except NotFound:
            app.logger.error('Connection settings not found')
            return jsonify({
                'failure-message' : 'Connection settings not found',
            }), 400


        settings = dbus.Interface(
            bus.get_object("org.freedesktop.NetworkManager", settings_path),
            "org.freedesktop.NetworkManager.Settings.Connection")


        settings_connection = dbus.Interface(
            settings,
            "org.freedesktop.NetworkManager.Settings.Connection")


        settings_dict = settings_connection.GetSettings()


        if settings_dict['connection']['type'] != '802-11-wireless':
            return jsonify({
                'failure-message' : 'Powersave only valid for wifi connections',
            }), 400


        if powersave:
            nm_powersave = 3  # enabled
        else:
            nm_powersave = 2  # disabled

        settings_dict['802-11-wireless']['powersave'] = nm_powersave


        try:
            settings_connection.Update(settings_dict)
        except dbus.exceptions.DBusException as e:
            app.logger.error('D-Bus Exception: %s', str(e))
            return jsonify({
                'failure-message' : 'Configure Failed: {0:s}'.format(str(e)),
            }), 400


        time.sleep(2.0)  # give some time for system to register

        return jsonify({
            'success-message' : 'Configure Successful',
        })


    def getSettingsPath(self, bus, nm_settings, connection_uuid):
        settingspath_list = nm_settings.Get(
            "org.freedesktop.NetworkManager.Settings",
            "Connections",
            dbus_interface=dbus.PROPERTIES_IFACE)


        for settings_path in settingspath_list:
            settings = bus.get_object(
                "org.freedesktop.NetworkManager",
                settings_path)


            settings_connection = dbus.Interface(
                settings,
                "org.freedesktop.NetworkManager.Settings.Connection")

            settings_dict = settings_connection.GetSettings()
            #app.logger.info('Settings: %s', settings_dict)

            settings_uuid = str(settings_dict['connection']['uuid'])


            if settings_uuid == connection_uuid:
                return settings_path
        else:
            raise NotFound('Connection settings not found')


    def getActiveConnection(self, bus, nm, connection_uuid):
        # get active connections
        connpath_list = nm.Get(
            "org.freedesktop.NetworkManager",
            "ActiveConnections",
            dbus_interface=dbus.PROPERTIES_IFACE)


        for conn_path in connpath_list:
            conn = bus.get_object(
                "org.freedesktop.NetworkManager",
                conn_path)


            conn_uuid = conn.Get(
                "org.freedesktop.NetworkManager.Connection.Active",
                "Uuid",
                dbus_interface=dbus.PROPERTIES_IFACE)


            if str(conn_uuid) == connection_uuid:
                return conn_path

        else:
            raise NotFound('Connection settings not found')


    def scanAPs(self, interface_name):
        bus = dbus.SystemBus()

        try:
            manager_bus_object = bus.get_object(
                "org.freedesktop.NetworkManager",
                "/org/freedesktop/NetworkManager")
        except dbus.exceptions.DBusException as e:
            app.logger.error('D-Bus Exception: %s', str(e))
            return jsonify({
                'failure-message' : 'D-Bus Exception: {0:s}'.format(str(e)),
            }), 400


        manager = dbus.Interface(
            manager_bus_object,
            "org.freedesktop.NetworkManager")

        manager_props = dbus.Interface(
            manager_bus_object,
            "org.freedesktop.DBus.Properties")


        # Enable Wireless. If Wireless is already enabled, this does nothing.
        wifi_enabled = manager_props.Get(
            "org.freedesktop.NetworkManager",
            "WirelessEnabled")

        if not wifi_enabled:
            app.logger.warning('Enabling WiFi')
            manager_props.Set(
                "org.freedesktop.NetworkManager",
                "WirelessEnabled",
                True)

            # Give the WiFi adapter some time to scan for APs. This is absolutely
            # the wrong way to do it, and the program should listen for
            # AccessPointAdded() signals, but it will do.
            time.sleep(10)


        device_path = manager.GetDeviceByIpIface(interface_name)
        device = dbus.Interface(
            bus.get_object("org.freedesktop.NetworkManager", device_path),
            "org.freedesktop.NetworkManager.Device.Wireless"
        )


        try:
            device.RequestScan(dbus.Dictionary({}, signature='sv'))
        except dbus.exceptions.DBusException as e:
            app.logger.error('D-Bus Exception: %s', str(e))
            return jsonify({
                'failure-message' : 'RequestScan Failed: {0:s}'.format(str(e)),
            }), 400


        time.sleep(10.0)


        try:
            accesspoints_paths_list = device.GetAccessPoints()
        except dbus.exceptions.DBusException as e:
            app.logger.error('D-Bus Exception: %s', str(e))
            return jsonify({
                'failure-message' : 'Scan APs Failed: {0:s}'.format(str(e)),
            }), 400


        ap_list = list()
        for ap_path in accesspoints_paths_list:
            ap_props = dbus.Interface(
                bus.get_object("org.freedesktop.NetworkManager", ap_path),
                "org.freedesktop.DBus.Properties"
            )

            ap_ssid = ap_props.Get(
                "org.freedesktop.NetworkManager.AccessPoint",
                "Ssid")

            ap_strength = ap_props.Get(
                "org.freedesktop.NetworkManager.AccessPoint",
                "Strength")

            ap_frequency = ap_props.Get(
                "org.freedesktop.NetworkManager.AccessPoint",
                "Frequency")

            ap_hwaddress = ap_props.Get(
                "org.freedesktop.NetworkManager.AccessPoint",
                "HwAddress")


            str_ap_ssid = "".join(chr(i) for i in ap_ssid)
            app.logger.info("Found SSID: %s", str_ap_ssid)


            ap_frequency_int = int(ap_frequency)

            if ap_frequency_int > 5999:
                ap_frequency_str = '6 GHz'
            elif ap_frequency_int > 3000:
                ap_frequency_str = '5 GHz'
            else:
                ap_frequency_str = '2.4 GHz'


            ap_list.append({
                'path' : str(ap_path),
                'ssid' : str_ap_ssid,
                'ap_hwaddress' : ap_hwaddress,
                'desc' : '{0:s} [{1:s}] - {2:s} - {3:d}%'.format(str_ap_ssid, ap_hwaddress, ap_frequency_str, int.from_bytes(str(ap_strength).encode())),
                'strength' : int.from_bytes(str(ap_strength).encode()),  # need to sort on this key
                'frequency' : ap_frequency_int,
            })


        ap_list_sorted = sorted(ap_list, key=lambda x: (x['strength'], x['ap_hwaddress']), reverse=True)


        time.sleep(2.0)  # give some time for system to register

        return jsonify({
            'success-message' : 'Scan Successful',
            'data' : ap_list_sorted,
        })


    def connectAP(self, interface_name, ap_path, psk, priority, retries):
        bus = dbus.SystemBus()

        manager_bus_object = bus.get_object(
            "org.freedesktop.NetworkManager",
            "/org/freedesktop/NetworkManager")

        manager = dbus.Interface(
            manager_bus_object,
            "org.freedesktop.NetworkManager")


        device_path = manager.GetDeviceByIpIface(interface_name)


        connection_params = {
            'connection' : {
                'type' : '802-11-wireless',
                'autoconnect' : True,
                'autoconnect-priority' : priority,
                'autoconnect-retries' : retries,
            },
            '802-11-wireless': {
                'security': '802-11-wireless-security',
                'powersave': 2,  # disable power saving
            },
            '802-11-wireless-security': {
                'key-mgmt': 'wpa-psk',
                'psk': psk,
            },
        }


        try:
            # Establish the connection.
            settings_path, connection_path = manager.AddAndActivateConnection(connection_params, device_path, ap_path)
            #app.logger.info("settings_path = %s", settings_path)
            #app.logger.info("connection_path = %s", connection_path)
        except dbus.exceptions.DBusException as e:
            app.logger.error('D-Bus Exception: %s', str(e))
            return jsonify({
                'failure-message' : 'Connect AP Failed: {0:s}'.format(str(e)),
            }), 400


        connection_props = dbus.Interface(
            bus.get_object("org.freedesktop.NetworkManager", connection_path),
            "org.freedesktop.DBus.Properties"
        )


        # Wait until connection is established. This may take a few seconds.
        app.logger.info("Waiting for wireless connection")


        state = None
        for _ in range(30):
            time.sleep(1.0)
            # Loop until desired state is detected.
            #
            # A timeout should be implemented here, otherwise the program will
            # get stuck if connection fails.
            #
            # IF PASSWORD IS BAD, NETWORK MANAGER WILL DISPLAY A QUERY DIALOG!
            #
            # Also, if connection is disconnected at this point, the Get()
            # method will raise an org.freedesktop.DBus.Error.UnknownMethod
            # exception. This should also be anticipated.
            try:
                state = connection_props.Get(
                    "org.freedesktop.NetworkManager.Connection.Active",
                    "State")
                #app.logger.info('Connection state: %d', int(state))
            except dbus.exceptions.DBusException as e:
                app.logger.error('D-Bus Exception: %s (psk may be incorrect)', str(e))


                ### remove the connection
                #manager.DeactivateConnection(connection_path)
                settings = dbus.Interface(
                    bus.get_object("org.freedesktop.NetworkManager", settings_path),
                    "org.freedesktop.NetworkManager.Settings.Connection")

                settings.Delete()


                return jsonify({
                    'failure-message' : 'Connect AP Failed: {0:s} (PSK may be incorrect)'.format(str(e)),
                }), 400


            if int(state) == self.nm_conn_states['Active']:
                app.logger.warning("Wireless connection established!")
                break
        else:
            app.logger.error('Wireless connection failed')
            return jsonify({
                'failure-message' : 'Connect AP Failed: Wireless connection failed',
            }), 400


        return jsonify({
            'success-message' : 'Connection Successful',
        })


    def createHotspot(self, interface_name, ssid, band, psk, nosecurity=False):
        bus = dbus.SystemBus()

        try:
            nm = bus.get_object(
                "org.freedesktop.NetworkManager",
                "/org/freedesktop/NetworkManager")
        except dbus.exceptions.DBusException as e:
            app.logger.error('D-Bus Exception: %s', str(e))
            return jsonify({
                'failure-message' : 'Connect AP Failed: {0:s}'.format(str(e)),
            }), 400


        manager = dbus.Interface(
            nm,
            "org.freedesktop.NetworkManager")


        nm_settings = bus.get_object(
            "org.freedesktop.NetworkManager",
            "/org/freedesktop/NetworkManager/Settings")

        settings_manager = dbus.Interface(
            nm_settings,
            "org.freedesktop.NetworkManager.Settings")


        # ensure device exists
        manager.GetDeviceByIpIface(interface_name)


        connection_params = {
            'connection' : {
                'type' : '802-11-wireless',
                'autoconnect' : True,
                'autoconnect-priority' : -90,
                'id' : ssid,
                'interface-name' : interface_name,
            },
            '802-11-wireless': {
                'mode' : 'ap',
                'ssid' : dbus.ByteArray(ssid.encode('utf-8')),
                'powersave': 2,  # disable power saving
                'band' : band,
            },
            'ipv4' : {
                # DNS not allowed for shared
                'method' : 'shared',
                'addresses' : [
                    [
                        dbus.UInt32(self.ip2int('10.42.0.1')),
                        dbus.UInt32(24),
                        dbus.UInt32(self.ip2int('0.0.0.0')),
                    ],
                ],
            },
            'ipv6' : {
                'method' : 'link-local',
            },
        }


        if not nosecurity:
            connection_params['802-11-wireless']['security'] = '802-11-wireless-security'
            connection_params['802-11-wireless-security'] = {
                'key-mgmt': 'wpa-psk',
                'psk': psk,
                'proto' : ['rsn'],
                'group' : ['ccmp'],
                'pairwise' : ['ccmp'],
            }


        try:
            # Create the connection.
            settings_manager.AddConnection(connection_params)
        except dbus.exceptions.DBusException as e:
            app.logger.error('D-Bus Exception: %s', str(e))
            return jsonify({
                'failure-message' : 'D-Bus Exception: {0:s}'.format(str(e)),
            }), 400


        time.sleep(2.0)  # give some time for system to register

        return jsonify({
            'success-message' : 'Hotspot Created',
        })


    def ip2int(self, ip_str):
        import struct
        return struct.unpack('=I', socket.inet_aton(ip_str))[0]


class DriveManagerView(TemplateView):
    decorators = [login_required]
    page_title = 'Drives'

    def get_context(self):
        context = super(DriveManagerView, self).get_context()


        try:
            # detect if udisks2 is available
            bus = dbus.SystemBus()
            bus.get_object(
                "org.freedesktop.UDisks2",
                "/org/freedesktop/UDisks2")
            udisks2_installed = True
        except dbus.exceptions.DBusException as e:
            app.logger.error('D-Bus Exception: %s', str(e))
            udisks2_installed = False


        context['udisks2_installed'] = udisks2_installed

        context['form_drives'] = IndiAllskyDriveManagerForm()

        return context


class AjaxDriveManagerView(BaseView):
    methods = ['POST']
    decorators = [login_required]


    protected_filesystems = (
        '/',
        '/boot',
        '/boot/firmware',
        '/boot/efi',
        '/var',
        '/home',
        '/tmp',
        '/var/tmp',
        '/run',
        '/dev',
        '/dev/shm',
    )


    def __init__(self, **kwargs):
        super(AjaxDriveManagerView, self).__init__(**kwargs)


    def dispatch_request(self):
        if not current_user.is_admin:
            json_data = {
                'failure-message' : 'User does not have permission to access this resource',
            }
            return jsonify(json_data), 400


        command = str(request.json['COMMAND'])


        if command == 'getmetadata':
            query_drive_id = str(request.json['DRIVE_ID'])
            return self.getMetadata(query_drive_id)
        if command == 'poweroff':
            query_drive_id = str(request.json['DRIVE_ID'])
            return self.powerOffDrive(query_drive_id)
        if command == 'unmount':
            query_device_id = str(request.json['DEVICE_ID'])
            return self.unmountDevice(query_device_id)
        if command == 'mount':
            query_device_id = str(request.json['DEVICE_ID'])
            return self.mountDevice(query_device_id)
        else:
            json_data = {
                'failure-message' : 'Unknown command',
            }
            return jsonify(json_data), 400


    def getMetadata(self, query_drive_id):
        bus = dbus.SystemBus()


        nm_udisks2 = bus.get_object(
            "org.freedesktop.UDisks2",
            "/org/freedesktop/UDisks2")

        iface = dbus.Interface(
            nm_udisks2,
            'org.freedesktop.DBus.ObjectManager')


        object_paths = iface.GetManagedObjects()

        for object_path in object_paths:
            if not object_path.startswith('/org/freedesktop/UDisks2/drives/'):
                continue


            settings = bus.get_object(
                "org.freedesktop.UDisks2",
                object_path)

            settings_connection = dbus.Interface(
                settings,
                dbus_interface='org.freedesktop.DBus.Properties')

            settings_dict = settings_connection.GetAll('org.freedesktop.UDisks2.Drive')


            drive_id = str(settings_dict['Id'])
            if query_drive_id != drive_id:
                continue


            TimeDetected = int(settings_dict['TimeDetected'])
            drive_TimeDetected = datetime.fromtimestamp(TimeDetected / 1000 / 1000)

            TimeMediaDetected = int(settings_dict['TimeMediaDetected'])
            if TimeMediaDetected:
                drive_TimeMediaDetected = datetime.fromtimestamp(TimeMediaDetected / 1000 / 1000)
            else:
                drive_TimeMediaDetected = ''


            drive_data = [
                [0, 'Id', drive_id],
                [1, 'Vendor', str(settings_dict['Vendor'])],
                [2, 'Model', str(settings_dict['Model'])],
                [3, 'Size', '{0:0.1f} GB'.format(float(settings_dict['Size']) / 1024 / 1024 / 1024)],
                [4, 'ConnectionBus', str(settings_dict['ConnectionBus'])],
                [5, 'Serial', str(settings_dict['Serial'])],
                [6, 'Media', str(settings_dict['Media'])],
                [7, 'MediaCompatibility', ', '.join(str(x) for x in settings_dict['MediaCompatibility'])],
                [8, 'CanPowerOff', bool(settings_dict['CanPowerOff'])],
                [9, 'Removable', bool(settings_dict['Removable'])],
                [10, 'Ejectable', bool(settings_dict['Ejectable'])],
                [11, 'TimeDetected', drive_TimeDetected],
                [12, 'TimeMediaDetected', drive_TimeMediaDetected],
            ]


            return_data = {
                'success-message' : '',
                'drive_data' : drive_data,
            }

            return jsonify(return_data)


        # fail if drive not found
        return jsonify({'failure-message' : 'Drive not found'}), 400


    def powerOffDrive(self, query_drive_id):
        bus = dbus.SystemBus()


        nm_udisks2 = bus.get_object(
            "org.freedesktop.UDisks2",
            "/org/freedesktop/UDisks2")

        iface = dbus.Interface(
            nm_udisks2,
            'org.freedesktop.DBus.ObjectManager')


        object_paths = iface.GetManagedObjects()

        for object_path in object_paths:
            if not object_path.startswith('/org/freedesktop/UDisks2/drives/'):
                continue


            settings = bus.get_object(
                "org.freedesktop.UDisks2",
                object_path)

            settings_connection = dbus.Interface(
                settings,
                dbus_interface='org.freedesktop.DBus.Properties')



            settings_dict = settings_connection.GetAll('org.freedesktop.UDisks2.Drive')


            drive_id = str(settings_dict['Id'])
            if query_drive_id != drive_id:
                continue


            CanPowerOff = bool(settings_dict['CanPowerOff'])
            if not CanPowerOff:
                return jsonify({'failure-message' : 'Drive cannot be powered off'}), 400



            drive_interface = dbus.Interface(
                bus.get_object('org.freedesktop.UDisks2', object_path),
                'org.freedesktop.UDisks2.Drive')


            try:
                drive_interface.PowerOff({})
            except dbus.exceptions.DBusException as e:
                app.logger.error('D-Bus Exception: %s', str(e))
                return jsonify({'failure-message' : str(e)}), 400


            return_data = {
                'success-message' : 'Power Off Successful'
            }
            return jsonify(return_data)


        # fail if drive not found
        return jsonify({'failure-message' : 'Drive not found'}), 400


    def unmountDevice(self, query_device_id):
        bus = dbus.SystemBus()


        nm_udisks2 = bus.get_object(
            "org.freedesktop.UDisks2",
            "/org/freedesktop/UDisks2")

        iface = dbus.Interface(
            nm_udisks2,
            'org.freedesktop.DBus.ObjectManager')


        objects = iface.GetManagedObjects()

        for object_path, object_info in objects.items():
            if not object_path.startswith('/org/freedesktop/UDisks2/block_devices/'):
                continue


            settings = bus.get_object(
                "org.freedesktop.UDisks2",
                object_path)

            settings_connection = dbus.Interface(
                settings,
                dbus_interface='org.freedesktop.DBus.Properties')



            settings_dict = settings_connection.GetAll('org.freedesktop.UDisks2.Block')


            device_id = str(settings_dict['Id'])
            if query_device_id != device_id:
                continue


            if len(object_info['org.freedesktop.UDisks2.Filesystem']['MountPoints']) == 0:
                return jsonify({'failure-message' : 'Filesystem not mounted'}), 400


            MountPoints0 = "".join(chr(i) for i in object_info['org.freedesktop.UDisks2.Filesystem']['MountPoints'][0][:-1])  # trim null char


            app.logger.info('Unmount %s', MountPoints0)
            if MountPoints0 in self.protected_filesystems:
                return jsonify({'failure-message' : 'Not allowed to unmount protected filesystem: {0:s}'.format(MountPoints0)}), 400


            fs_interface = dbus.Interface(
                settings,
                dbus_interface='org.freedesktop.UDisks2.Filesystem')


            try:
                fs_interface.Unmount({})
            except dbus.exceptions.DBusException as e:
                app.logger.error('D-Bus Exception: %s', str(e))
                return jsonify({'failure-message' : str(e)}), 400


            return_data = {
                'success-message' : 'Unmount Successful'
            }
            return jsonify(return_data)


        # fail if drive not found
        return jsonify({'failure-message' : 'Device not found'}), 400


    def mountDevice(self, query_device_id):
        bus = dbus.SystemBus()


        nm_udisks2 = bus.get_object(
            "org.freedesktop.UDisks2",
            "/org/freedesktop/UDisks2")

        iface = dbus.Interface(
            nm_udisks2,
            'org.freedesktop.DBus.ObjectManager')


        objects = iface.GetManagedObjects()

        for object_path, object_info in objects.items():
            if not object_path.startswith('/org/freedesktop/UDisks2/block_devices/'):
                continue


            settings = bus.get_object(
                "org.freedesktop.UDisks2",
                object_path)

            settings_connection = dbus.Interface(
                settings,
                dbus_interface='org.freedesktop.DBus.Properties')



            settings_dict = settings_connection.GetAll('org.freedesktop.UDisks2.Block')


            device_id = str(settings_dict['Id'])
            if query_device_id != device_id:
                continue


            if len(object_info['org.freedesktop.UDisks2.Filesystem']['MountPoints']) > 1:
                return jsonify({'failure-message' : 'Filesystem already mounted'}), 400


            fs_interface = dbus.Interface(
                settings,
                dbus_interface='org.freedesktop.UDisks2.Filesystem')


            try:
                fs_interface.Mount({})
            except dbus.exceptions.DBusException as e:
                app.logger.error('D-Bus Exception: %s', str(e))
                return jsonify({'failure-message' : str(e)}), 400


            return_data = {
                'success-message' : 'Mount Successful'
            }
            return jsonify(return_data)


        # fail if drive not found
        return jsonify({'failure-message' : 'Device not found'}), 400


class ImageCircleHelperView(TemplateView):
    decorators = [login_required]

    page_title = 'Image Circle Helper'
    model = IndiAllSkyDbImageTable


    def get_context(self):
        context = super(ImageCircleHelperView, self).get_context()


        form_data = {
            'IMAGE_CIRCLE_DIAMETER' : self.camera.lensImageCircle,
            'OFFSET_X' : self.indi_allsky_config.get('LENS_OFFSET_X', 0),
            'OFFSET_Y' : self.indi_allsky_config.get('LENS_OFFSET_Y', 0),
            'KEOGRAM_ANGLE' : self.indi_allsky_config.get('KEOGRAM_ANGLE', 90.0),
        }

        context['form_imagecircle'] = IndiAllskyImageCircleHelperForm(data=form_data)


        # limit time period for performance
        camera_now_minus_10days = self.camera_now - timedelta(days=10)

        latest_image_q = self.model.query\
            .join(self.model.camera)\
            .filter(IndiAllSkyDbCameraTable.id == self.camera.id)\
            .filter(self.model.createDate > camera_now_minus_10days)\


        local = True  # default to local assets
        if self.web_nonlocal_images:
            if self.web_local_images_admin and self.verify_admin_network():
                pass
            else:
                local = False

                # Do not serve local assets
                latest_image_q = latest_image_q\
                    .filter(
                        or_(
                            self.model.remote_url != sa_null(),
                            self.model.s3_key != sa_null(),
                        )
                    )


        latest_image = latest_image_q\
            .order_by(self.model.createDate.desc())\
            .first()


        if latest_image:
            context['latest_image_url'] = latest_image.getUrl(s3_prefix=self.s3_prefix, local=local)


        return context


class ModernAdminSafeControlsMixin(ModernAdminContextMixin):
    page_title = 'Modern Admin'
    modern_admin_active_endpoint = 'indi_allsky.modern_admin_system_view'

    secret_field_tokens = ('PASSWORD', 'PSK', 'SECRET', 'TOKEN', 'KEY')

    def get_context(self):
        context = super(ModernAdminSafeControlsMixin, self).get_context()
        context.setdefault('modern_admin_safe_title', self.page_title.replace('Modern Admin ', ''))
        context.setdefault('modern_admin_safe_note', 'Controls are shown in safe mode. Operational actions remain disabled in Modern Admin.')
        context.setdefault('modern_admin_safe_sections', tuple())
        context.setdefault('modern_admin_safe_actions', tuple())
        context.setdefault('modern_admin_safe_tables', tuple())
        return context


    def field_value(self, field):
        field_name = getattr(field, 'name', '').upper()
        if any(token in field_name for token in self.secret_field_tokens):
            return 'Configured' if field.data else 'Not configured'

        if isinstance(field.data, bool):
            return 'Enabled' if field.data else 'Disabled'
        elif field.data in (None, ''):
            return 'Not configured'

        return str(field.data)


    def field_rows(self, form, field_names):
        rows = list()
        for field_name in field_names:
            field = getattr(form, field_name, None)
            if not field:
                continue

            rows.append({
                'label' : str(field.label.text),
                'value' : self.field_value(field),
            })

        return rows


    def disabled_action(self, label, reason='Disabled in Modern Admin safe mode.'):
        return {
            'label'  : label,
            'reason' : reason,
        }


class ModernAdminCameraSimulatorView(ModernAdminSafeControlsMixin, CameraSimulatorView):
    page_title = 'Modern Admin Camera Simulator'
    modern_admin_active_endpoint = 'indi_allsky.modern_admin_cameras_view'

    def get_context(self):
        context = super(ModernAdminCameraSimulatorView, self).get_context()
        form = context['form_camera_simulator']

        context['modern_admin_safe_title'] = 'Camera Simulator'
        context['modern_admin_safe_note'] = 'Camera and lens inputs mirror the classic simulator. The modern page keeps the simulator read-only until the interactive canvas is ported safely.'
        context['modern_admin_safe_sections'] = (
            {
                'title' : 'Simulator inputs',
                'rows'  : self.field_rows(form, ('LENS_SELECT', 'SENSOR_SELECT', 'OFFSET_X', 'OFFSET_Y')),
            },
        )
        context['modern_admin_safe_actions'] = (
            self.disabled_action('Run simulator', 'The classic simulator is client-side and interactive; Modern Admin shows the selected inputs without applying calculations yet.'),
        )
        return context


class ModernAdminGenerateView(ModernAdminSafeControlsMixin, TimelapseGeneratorView):
    page_title = 'Modern Admin Generate'
    modern_admin_active_endpoint = 'indi_allsky.modern_admin_storage_view'

    def get_context(self):
        context = super(ModernAdminGenerateView, self).get_context()
        form = context['form_timelapsegen']

        context['modern_admin_safe_title'] = 'Generate'
        context['modern_admin_safe_note'] = 'Recent generation tasks are real. Creating new media tasks is disabled in Modern Admin safe mode.'
        context['modern_admin_safe_sections'] = (
            {
                'title' : 'Generation request',
                'rows'  : self.field_rows(form, ('ACTION_SELECT', 'DAY_SELECT')),
            },
        )
        context['modern_admin_safe_actions'] = (
            self.disabled_action('Generate', 'This queues processing jobs and remains disabled in Modern Admin.'),
        )
        context['modern_admin_safe_tables'] = (
            {
                'title'   : 'Recent tasks',
                'headers' : ('ID', 'Date', 'Queue', 'Action', 'State', 'Result'),
                'rows'    : [
                    (
                        task['id'],
                        task['createDate'].strftime('%Y-%m-%d %H:%M:%S'),
                        task['queue'],
                        task['action'],
                        task['state'],
                        task['result'] or '',
                    )
                    for task in context.get('task_list', tuple())
                ],
            },
        )
        return context


class ModernAdminFocusView(ModernAdminSafeControlsMixin, FocusView):
    page_title = 'Modern Admin Focus'
    modern_admin_active_endpoint = 'indi_allsky.modern_admin_cameras_view'

    def get_context(self):
        context = super(ModernAdminFocusView, self).get_context()

        context['modern_admin_safe_title'] = 'Focus'
        context['modern_admin_safe_note'] = 'The focus monitor uses the existing read-only focus image endpoint. Focuser movement controls remain disabled.'
        context['modern_admin_focus_monitor'] = True
        context['modern_admin_safe_sections'] = (
            {
                'title' : 'Focus status',
                'rows'  : (
                    {'label' : 'Focus mode', 'value' : 'Enabled' if self.indi_allsky_config.get('FOCUS_MODE', False) else 'Disabled'},
                    {'label' : 'Focuser device', 'value' : 'Configured' if context.get('focuser_device') else 'Not configured'},
                    {'label' : 'Refresh interval', 'value' : 'Manual preview load'},
                ),
            },
        )
        context['modern_admin_safe_actions'] = (
            self.disabled_action('Move counter-clockwise', 'Moves hardware and remains disabled in Modern Admin.'),
            self.disabled_action('Move clockwise', 'Moves hardware and remains disabled in Modern Admin.'),
        )
        return context


class ModernAdminImageProcessingView(ModernAdminSafeControlsMixin, ImageProcessingView):
    page_title = 'Modern Admin Process FITS'
    modern_admin_active_endpoint = 'indi_allsky.modern_admin_storage_view'

    def get_context(self):
        context = super(ModernAdminImageProcessingView, self).get_context()
        form = context['form_image_processing']

        context['modern_admin_safe_title'] = 'Process FITS'
        context['modern_admin_safe_note'] = 'The selected FITS frame and processing parameters are real. Processing preview generation remains disabled in Modern Admin safe mode.'
        context['modern_admin_safe_sections'] = (
            {
                'title' : 'Selected frame',
                'rows'  : self.field_rows(form, ('FRAME_TYPE', 'FITS_ID', 'CCD_BIT_DEPTH')),
            },
            {
                'title' : 'Core processing',
                'rows'  : self.field_rows(form, (
                    'NIGHT_CONTRAST_ENHANCE',
                    'CONTRAST_ENHANCE_16BIT',
                    'IMAGE_STRETCH__CLASSNAME',
                    'IMAGE_DENOISE',
                    'IMAGE_STACK_METHOD',
                    'IMAGE_STACK_COUNT',
                )),
            },
            {
                'title' : 'Lens geometry',
                'rows'  : self.field_rows(form, ('LENS_IMAGE_CIRCLE', 'LENS_OFFSET_X', 'LENS_OFFSET_Y', 'LENS_AZIMUTH')),
            },
        )
        context['modern_admin_safe_actions'] = (
            self.disabled_action('Process preview', 'This calls the FITS processing endpoint and remains disabled in Modern Admin.'),
        )
        return context


class ModernAdminImageCircleHelperView(ModernAdminSafeControlsMixin, ImageCircleHelperView):
    page_title = 'Modern Admin Image Circle Helper'
    modern_admin_active_endpoint = 'indi_allsky.modern_admin_cameras_view'

    def get_context(self):
        context = super(ModernAdminImageCircleHelperView, self).get_context()
        form = context['form_imagecircle']
        latest_image_url = context.get('latest_image_url')
        if latest_image_url:
            context['latest_image_url'] = ModernAdminMediaListView.normalize_media_url(self, latest_image_url)

        context['modern_admin_safe_title'] = 'Image Circle Helper'
        context['modern_admin_safe_note'] = 'Latest image and circle parameters come from the classic helper. Modern Admin keeps this as a read-only reference view.'
        context['modern_admin_preview_url'] = context.get('latest_image_url')
        context['modern_admin_safe_sections'] = (
            {
                'title' : 'Circle parameters',
                'rows'  : self.field_rows(form, ('IMAGE_CIRCLE_DIAMETER', 'OFFSET_X', 'OFFSET_Y', 'KEOGRAM_ANGLE')),
            },
        )
        context['modern_admin_safe_actions'] = (
            self.disabled_action('Apply helper values', 'Saving camera geometry is a configuration action and remains disabled in Modern Admin.'),
        )
        return context


class ModernAdminConfigView(ModernAdminSafeControlsMixin, ConfigView):
    page_title = 'Modern Admin Config'
    modern_admin_active_endpoint = 'indi_allsky.modern_admin_system_view'

    def get_context(self):
        context = super(ModernAdminConfigView, self).get_context()
        form = context['form_config']

        context['modern_admin_safe_title'] = 'Config'
        context['modern_admin_safe_note'] = 'Configuration values are loaded from the existing classic config form. Saving configuration remains disabled in Modern Admin.'
        context['modern_admin_safe_sections'] = (
            {
                'title' : 'Camera',
                'rows'  : self.field_rows(form, (
                    'CAMERA_INTERFACE',
                    'INDI_SERVER',
                    'INDI_PORT',
                    'INDI_CAMERA_NAME',
                    'LENS_NAME',
                    'LENS_FOCAL_LENGTH',
                    'LENS_FOCAL_RATIO',
                )),
            },
            {
                'title' : 'Exposure',
                'rows'  : self.field_rows(form, (
                    'CCD_EXPOSURE_MAX',
                    'CCD_EXPOSURE_DEF',
                    'CCD_EXPOSURE_MIN',
                    'EXPOSURE_PERIOD',
                    'CCD_BIT_DEPTH',
                    'FOCUS_MODE',
                )),
            },
            {
                'title' : 'System controls',
                'rows'  : (
                    {'label' : 'Config ID', 'value' : context.get('config_id')},
                    {'label' : 'Timezone validation', 'value' : 'Warning' if context.get('longitude_validation_message') else 'OK'},
                    {'label' : 'Dew heater status', 'value' : context.get('dh_status_str')},
                    {'label' : 'Fan status', 'value' : context.get('fan_status_str')},
                ),
            },
        )
        context['modern_admin_safe_actions'] = (
            self.disabled_action('Save config', 'Writes configuration and may reload services; disabled in Modern Admin.'),
            self.disabled_action('Restore config', 'Restores configuration state; disabled in Modern Admin.'),
        )
        return context


class ModernAdminSettingsInventoryView(ModernAdminContextMixin, ConfigView):
    page_title = 'Modern Admin Settings'
    modern_admin_active_endpoint = 'indi_allsky.modern_admin_settings_view'

    SETTINGS_GROUP_ORDER = (
        'Camera / Capture',
        'Multi-camera / Profile',
        'Exposure / Gain / Binning',
        'Processing / Calibration',
        'Overlay / Labels / Lens',
        'Output / Storage',
        'Timelapse / Keogram / Startrail',
        'Upload / Publishing',
        'Devices / GPIO / Sensors',
        'Web / Admin / System',
        'Advanced / Other',
    )
    SETTINGS_DEFAULT_OPEN_GROUPS = (
        'Camera / Capture',
        'Multi-camera / Profile',
    )
    SETTINGS_SECRET_TOKENS = (
        'PASSWORD',
        'TOKEN',
        'SECRET',
        'PRIVATE_KEY',
        'APIKEY',
        'API_KEY',
        'ACCESS_KEY',
        'CLIENT_SECRET',
        'WEBHOOK',
        'PSK',
    )

    def get_context(self):
        context = super(ModernAdminSettingsInventoryView, self).get_context()
        form = context['form_config']
        settings_groups = self.get_settings_inventory_groups(form)

        context['modern_admin_settings_groups'] = settings_groups
        context['modern_admin_settings_field_count'] = sum([group['count'] for group in settings_groups])
        context['modern_admin_settings_form_field_count'] = len([field for field in form])
        context['modern_admin_settings_profile_count'] = self.get_multi_camera_profile_count()
        context['modern_admin_settings_group_counts'] = [(group['title'], group['count']) for group in settings_groups]

        return context


    def get_settings_inventory_groups(self, form):
        grouped_fields = OrderedDict()
        for group_title in self.SETTINGS_GROUP_ORDER:
            grouped_fields[group_title] = list()

        for field in form:
            field_name = getattr(field, 'name', '')
            if not field_name:
                continue

            group_title = self.estimate_settings_group(field_name)
            grouped_fields[group_title].append(self.get_settings_field_metadata(field_name, field))

        for profile_field in self.get_multi_camera_profile_fields():
            grouped_fields['Multi-camera / Profile'].append(profile_field)

        settings_groups = list()
        for group_title, fields in grouped_fields.items():
            if not fields:
                continue

            group_key = re.sub(r'[^a-z0-9]+', '-', group_title.lower()).strip('-')
            settings_groups.append({
                'title'        : group_title,
                'key'          : group_key,
                'fields'       : fields,
                'count'        : len(fields),
                'default_open' : group_title in self.SETTINGS_DEFAULT_OPEN_GROUPS,
            })

        return settings_groups


    def get_settings_field_metadata(self, field_name, field):
        field_type = field.__class__.__name__
        risk = self.estimate_settings_risk(field_name, field)

        return {
            'label'            : str(field.label.text),
            'name'             : field_name,
            'config_key'       : self.form_field_to_config_key(field_name),
            'current_value'    : self.format_settings_value(field_name, field, risk),
            'field_type'       : field_type,
            'validators'       : self.describe_field_validators(field),
            'group'            : self.estimate_settings_group(field_name),
            'scope'            : self.estimate_settings_scope(field_name),
            'risk'             : risk,
            'restart_required' : self.estimate_settings_restart(field_name),
            'search_text'      : self.get_settings_search_text(field_name, field, risk),
        }


    def get_multi_camera_profile_count(self):
        try:
            profiles = self.indi_allsky_config.get('MULTI_CAMERA', {}).get('profiles', [])
        except AttributeError:
            return 0

        if isinstance(profiles, list):
            return len(profiles)

        return 0


    def get_multi_camera_profile_fields(self):
        try:
            profiles = self.indi_allsky_config.get('MULTI_CAMERA', {}).get('profiles', [])
        except AttributeError:
            return tuple()

        if not isinstance(profiles, list):
            return tuple()

        profile_fields = list()
        for profile_index, profile in enumerate(profiles, start=1):
            if not isinstance(profile, dict):
                continue

            profile_id = profile.get('profile_id') or profile.get('id') or 'profile-{0:d}'.format(profile_index)
            profile_name = 'MULTI_CAMERA.profiles[{0:d}]'.format(profile_index - 1)
            profile_value = self.format_structured_settings_value(profile)
            search_text = ' '.join([
                'Multi-camera profile',
                profile_name,
                str(profile_id),
                profile_value,
            ])

            profile_fields.append({
                'label'            : 'Multi-camera profile {0:s}'.format(str(profile_id)),
                'name'             : profile_name,
                'config_key'       : profile_name,
                'current_value'    : profile_value,
                'field_type'       : 'ConfigProfile',
                'validators'       : 'Configured profile entry',
                'group'            : 'Multi-camera / Profile',
                'scope'            : 'profile',
                'risk'             : 'medium',
                'restart_required' : 'restart',
                'search_text'      : search_text.lower(),
            })

        return tuple(profile_fields)


    def form_field_to_config_key(self, field_name):
        return field_name.replace('__', '.')


    def describe_field_validators(self, field):
        validators = list()
        for validator in getattr(field, 'validators', tuple()):
            validator_name = getattr(validator, '__name__', validator.__class__.__name__)
            validator_parts = list()
            for attr_name in ('min', 'max', 'length', 'equal_to'):
                if not hasattr(validator, attr_name):
                    continue

                validator_parts.append('{0:s}={1!s}'.format(attr_name, getattr(validator, attr_name)))

            if validator_parts:
                validators.append('{0:s} ({1:s})'.format(validator_name, ', '.join(validator_parts)))
            else:
                validators.append(validator_name)

        if validators:
            return ', '.join(validators)

        choices = getattr(field, 'choices', None)
        if choices:
            return '{0:d} choices'.format(len(choices))

        return 'None declared'


    def format_settings_value(self, field_name, field, risk):
        if risk == 'secret':
            if field.data in (None, ''):
                return 'Not configured'

            return 'Configured (masked)'

        data = field.data
        if data is True:
            return 'Enabled'
        elif data is False:
            return 'Disabled'
        elif data in (None, ''):
            return 'Not configured'

        return self.format_structured_settings_value(data)


    def format_structured_settings_value(self, value):
        if isinstance(value, (dict, list, tuple)):
            try:
                return json.dumps(value, sort_keys=True, default=str)
            except TypeError:
                return str(value)

        return str(value)


    def get_settings_search_text(self, field_name, field, risk):
        search_parts = (
            str(field.label.text),
            field_name,
            self.form_field_to_config_key(field_name),
            field.__class__.__name__,
            self.describe_field_validators(field),
            self.estimate_settings_group(field_name),
            self.estimate_settings_scope(field_name),
            risk,
            self.estimate_settings_restart(field_name),
            self.format_settings_value(field_name, field, risk),
        )
        return ' '.join(search_parts).lower()


    def estimate_settings_group(self, field_name):
        field_name_upper = field_name.upper()

        if field_name_upper.startswith('MULTI_CAMERA'):
            return 'Multi-camera / Profile'
        elif any(token in field_name_upper for token in (
            'CCD_CONFIG',
            'CCD_EXPOSURE',
            'EXPOSURE_PERIOD',
            'GAIN',
            'BINNING',
            'COOLING',
            'CCD_TEMP',
            'TARGET_TEMP',
        )):
            return 'Exposure / Gain / Binning'
        elif any(token in field_name_upper for token in (
            'CAMERA_INTERFACE',
            'INDI_',
            'LIBCAMERA',
            'PYCURL_CAMERA',
            'GPHOTO',
            'FOCUS',
            'CFA_PATTERN',
            'DAYTIME',
            'CAPTURE_PAUSE',
            'GPS_ENABLE',
        )):
            return 'Camera / Capture'
        elif any(token in field_name_upper for token in (
            'IMAGE_STRETCH',
            'IMAGE_DENOISE',
            'IMAGE_CALIBRATE',
            'IMAGE_STACK',
            'IMAGE_ALIGN',
            'SCNR',
            'WBR',
            'WBG',
            'WBB',
            'AUTO_WB',
            'SATURATION',
            'GAMMA',
            'SHARPEN',
            'BILATERAL',
            'CONTRAST',
            'CLAHE',
            'DETECT',
            'ADU',
            'SQM',
            'CAMERA_SQM',
            'TARGET_ADU',
        )):
            return 'Processing / Calibration'
        elif any(token in field_name_upper for token in (
            'LENS',
            'LOGO',
            'IMAGE_LABEL',
            'IMAGE_ROTATE',
            'IMAGE_FLIP',
            'IMAGE_COLORMAP',
            'IMAGE_CIRCLE',
            'IMAGE_CROP',
            'FISH2PANO',
            'TEXT_PROPERTIES',
            'MOON_OVERLAY',
            'LIGHTGRAPH_OVERLAY',
            'CARDINAL_DIRS',
            'ORB_PROPERTIES',
            'IMAGE_BORDER',
        )):
            return 'Overlay / Labels / Lens'
        elif any(token in field_name_upper for token in (
            'IMAGE_FILE',
            'IMAGE_SAVE',
            'IMAGE_EXPORT',
            'IMAGE_FOLDER',
            'FITS',
            'RAW',
            'CIRCULAR_DISPLAY',
            'TIMELAPSE_EXPIRE',
        )):
            return 'Output / Storage'
        elif any(token in field_name_upper for token in (
            'TIMELAPSE',
            'FFMPEG',
            'KEOGRAM',
            'LONGTERM_KEOGRAM',
            'STARTRAIL',
            'REALTIME_KEOGRAM',
            'PANORAMA',
        )):
            return 'Timelapse / Keogram / Startrail'
        elif any(token in field_name_upper for token in (
            'UPLOAD',
            'FILETRANSFER',
            'S3',
            'AZURE',
            'GCS',
            'MQTT',
            'YOUTUBE',
            'SYNCAPI',
        )):
            return 'Upload / Publishing'
        elif any(token in field_name_upper for token in (
            'TEMP_SENSOR',
            'DEW_HEATER',
            'FAN',
            'GENERIC_GPIO',
            'MANUAL_GPIO',
            'FOCUSER',
            'DEVICE',
            'ADSB',
            'SATELLITE',
            'CHARTS',
        )):
            return 'Devices / GPIO / Sensors'
        elif any(token in field_name_upper for token in (
            'WEBSITE',
            'WEB_',
            'OWNER',
            'LOCATION',
            'TEMP_DISPLAY',
            'PRESSURE_DISPLAY',
            'WINDSPEED_DISPLAY',
            'HEALTHCHECK',
            'ADMIN_NETWORKS',
            'LOGIN',
            'ENCRYPT_PASSWORDS',
            'RELOAD_ON_SAVE',
            'CONFIG_NOTE',
            'NIGHT_',
            'TIMEZONE',
            'LATITUDE',
            'LONGITUDE',
        )):
            return 'Web / Admin / System'

        return 'Advanced / Other'


    def estimate_settings_scope(self, field_name):
        field_name_upper = field_name.upper()
        if field_name_upper.startswith('MULTI_CAMERA') or 'PROFILE' in field_name_upper:
            return 'profile'
        elif any(token in field_name_upper for token in (
            'CAMERA',
            'CCD_',
            'INDI_',
            'LIBCAMERA',
            'GPHOTO',
            'PYCURL_CAMERA',
            'LENS',
            'FOCUS',
            'GAIN',
            'BINNING',
            'EXPOSURE',
            'CFA_PATTERN',
        )):
            return 'camera'
        elif any(token in field_name_upper for token in (
            'UPLOAD',
            'FILETRANSFER',
            'S3',
            'AZURE',
            'GCS',
            'MQTT',
            'YOUTUBE',
            'WEBSITE',
            'OWNER',
            'LOCATION',
            'TIMEZONE',
            'LATITUDE',
            'LONGITUDE',
        )):
            return 'global'
        elif any(token in field_name_upper for token in ('GPIO', 'DEVICE', 'FOCUSER', 'SENSOR')):
            return 'advanced'

        return 'unknown'


    def estimate_settings_risk(self, field_name, field):
        field_name_upper = field_name.upper()
        field_type = field.__class__.__name__
        if field_type == 'PasswordField' or any(token in field_name_upper for token in self.SETTINGS_SECRET_TOKENS):
            return 'secret'
        elif any(token in field_name_upper for token in (
            'DELETE',
            'REMOVE',
            'PURGE',
            'POWER',
            'REBOOT',
            'SHUTDOWN',
            'FORMAT',
        )):
            return 'destructive'
        elif any(token in field_name_upper for token in (
            'GPIO',
            'RELAY',
            'DEW_HEATER',
            'FAN',
            'FOCUSER',
            'INDI_PORT',
            'INDI_SERVER',
            'NETWORK',
            'ENCRYPT_PASSWORDS',
            'RELOAD_ON_SAVE',
        )):
            return 'high'
        elif any(token in field_name_upper for token in (
            'UPLOAD',
            'FILETRANSFER',
            'S3',
            'AZURE',
            'GCS',
            'MQTT',
            'YOUTUBE',
            'TIMELAPSE',
            'KEOGRAM',
            'STARTRAIL',
            'PANORAMA',
            'FITS',
            'RAW',
            'CALIBRATE',
        )):
            return 'medium'

        return 'safe'


    def estimate_settings_restart(self, field_name):
        field_name_upper = field_name.upper()
        if any(token in field_name_upper for token in (
            'CAMERA_INTERFACE',
            'INDI_',
            'LIBCAMERA',
            'GPHOTO',
            'PYCURL_CAMERA',
            'MULTI_CAMERA',
            'CCD_CONFIG',
            'GPS_ENABLE',
            'TEMP_SENSOR',
            'GPIO',
            'DEVICE',
            'FOCUSER',
            'ENCRYPT_PASSWORDS',
            'TIMEZONE',
        )):
            return 'restart'
        elif any(token in field_name_upper for token in (
            'UPLOAD',
            'FILETRANSFER',
            'S3',
            'AZURE',
            'GCS',
            'MQTT',
            'YOUTUBE',
            'WEBSITE',
            'OWNER',
            'LOCATION',
            'LOGIN',
            'ADMIN_NETWORKS',
            'HEALTHCHECK',
        )):
            return 'reload'

        return 'unknown'


class ModernAdminCameraSettingsView(ModernAdminSettingsInventoryView):
    page_title = 'Modern Admin Camera Settings'
    modern_admin_active_endpoint = 'indi_allsky.modern_admin_settings_view'
    methods = ['GET', 'POST']

    CAMERA_SETTINGS_FIELD_LABELS = {
        'profile_id' : 'Profile ID',
        'profile_label' : 'Profile Label',
        'profile_enabled' : 'Profile Enabled',
        'profile_primary' : 'Primary Profile',
        'db_camera_id' : 'DB Camera ID',
        'db_camera_name' : 'DB Camera Name',
        'db_camera_driver' : 'DB Camera Driver',
        'db_camera_status' : 'DB Camera Status',
        'PROCESSING_MODE' : 'Processing Mode',
        'CAMERA_INTERFACE' : 'Camera Interface',
        'INDI_SERVER' : 'INDI Server',
        'INDI_PORT' : 'INDI Port',
        'INDI_CAMERA_NAME' : 'INDI Camera Name',
        'LIBCAMERA.CAMERA_ID' : 'libcamera Camera ID',
        'LIBCAMERA.IMAGE_FILE_TYPE' : 'libcamera Image Type',
        'LIBCAMERA.EXTRA_OPTIONS' : 'libcamera Extra Options',
        'EXPOSURE_PERIOD' : 'Exposure Period',
        'EXPOSURE_PERIOD_DAY' : 'Day Exposure Period',
        'CCD_EXPOSURE_MIN' : 'Minimum Exposure',
        'CCD_EXPOSURE_MIN_DAY' : 'Day Minimum Exposure',
        'CCD_EXPOSURE_DEF' : 'Default Exposure',
        'CCD_EXPOSURE_MAX' : 'Maximum Exposure',
        'CCD_EXPOSURE_TIMEOUT' : 'Exposure Timeout',
        'CCD_CONFIG.NIGHT.GAIN' : 'Night Gain',
        'CCD_CONFIG.NIGHT.BINNING' : 'Night Binning',
        'CCD_CONFIG.MOONMODE.GAIN' : 'Moon Mode Gain',
        'CCD_CONFIG.MOONMODE.BINNING' : 'Moon Mode Binning',
        'CCD_CONFIG.DAY.GAIN' : 'Day Gain',
        'CCD_CONFIG.DAY.BINNING' : 'Day Binning',
        'DAYTIME_CAPTURE' : 'Daytime Capture',
        'DAYTIME_CAPTURE_SAVE' : 'Save Daytime Images',
        'TARGET_ADU' : 'Night Target ADU',
        'TARGET_ADU_DAY' : 'Day Target ADU',
        'CCD_BIT_DEPTH' : 'Bit Depth',
        'CFA_PATTERN' : 'CFA Pattern',
        'USE_NIGHT_COLOR' : 'Use Night Color',
        'AUTO_WB' : 'Auto White Balance',
        'AUTO_WB_DAY' : 'Day Auto White Balance',
        'NIGHT_GRAYSCALE' : 'Night Grayscale',
        'DAYTIME_GRAYSCALE' : 'Daytime Grayscale',
        'CCD_COOLING' : 'Cooling',
        'CCD_TEMP' : 'Target Temperature',
        'LENS_NAME' : 'Lens Name',
        'LENS_FOCAL_LENGTH' : 'Focal Length',
        'LENS_FOCAL_RATIO' : 'Focal Ratio',
        'LENS_IMAGE_CIRCLE' : 'Lens Image Circle',
        'LENS_OFFSET_X' : 'Lens Offset X',
        'LENS_OFFSET_Y' : 'Lens Offset Y',
        'LENS_ALTITUDE' : 'Lens Altitude',
        'LENS_AZIMUTH' : 'Lens Azimuth',
        'IMAGE_ROTATE' : 'Image Rotate',
        'IMAGE_ROTATE_ANGLE' : 'Image Rotate Angle',
        'IMAGE_FLIP_V' : 'Flip Vertical',
        'IMAGE_FLIP_H' : 'Flip Horizontal',
        'IMAGE_SCALE' : 'Image Scale',
        'IMAGE_CALIBRATE_DARK' : 'Dark Calibration',
        'IMAGE_CALIBRATE_BPM' : 'Bad Pixel Map Calibration',
        'IMAGE_CALIBRATE_FIX_HOLES' : 'Fix Calibration Holes',
        'IMAGE_CALIBRATE_HOLE_THOLD' : 'Calibration Hole Threshold',
        'IMAGE_CALIBRATE_MANUAL_OFFSET' : 'Calibration Manual Offset',
        'IMAGE_CIRCLE_MASK.ENABLE' : 'Image Circle Mask',
        'IMAGE_CIRCLE_MASK.DIAMETER' : 'Mask Diameter',
        'IMAGE_CIRCLE_MASK.OFFSET_X' : 'Mask Offset X',
        'IMAGE_CIRCLE_MASK.OFFSET_Y' : 'Mask Offset Y',
        'IMAGE_CIRCLE_MASK.BLUR' : 'Mask Blur',
        'IMAGE_CIRCLE_MASK.OPACITY' : 'Mask Opacity',
        'IMAGE_CIRCLE_MASK.OUTLINE' : 'Mask Outline',
        'IMAGE_CROP_ROI' : 'Image Crop ROI',
        'IMAGE_CROP_IMAGE_CIRCLE' : 'Crop to Image Circle',
        'ADU_ROI' : 'ADU ROI',
        'SQM_ROI' : 'SQM ROI',
        'INDI_CONFIG_DEFAULTS' : 'INDI Default Config',
        'INDI_CONFIG_DAY' : 'INDI Day Config',
        'LIBCAMERA.AWB' : 'libcamera AWB',
        'LIBCAMERA.AWB_DAY' : 'libcamera Day AWB',
        'LIBCAMERA.AWB_ENABLE' : 'libcamera AWB Enable',
        'LIBCAMERA.AWB_MODE' : 'libcamera AWB Mode',
        'LIBCAMERA.AWB_RED_GAIN' : 'libcamera AWB Red Gain',
        'LIBCAMERA.AWB_BLUE_GAIN' : 'libcamera AWB Blue Gain',
        'LIBCAMERA.IMMEDIATE' : 'libcamera Immediate',
        'LIBCAMERA.IMMEDIATE_DAY' : 'libcamera Day Immediate',
    }

    CAMERA_SETTINGS_PROFILE_ALIASES = {
        'PROCESSING_MODE' : ('processing_mode',),
        'CAMERA_INTERFACE' : ('camera_interface', 'interface', 'driver'),
        'INDI_SERVER' : ('indi_server', ('indi', 'server')),
        'INDI_PORT' : ('indi_port', ('indi', 'port')),
        'INDI_CAMERA_NAME' : ('indi_camera_name', 'camera_name', ('indi', 'camera_name')),
        'LIBCAMERA.CAMERA_ID' : ('libcamera_camera_id', 'libcamera_id', 'camera_id_hint', ('libcamera', 'camera_id'), ('libcamera', 'CAMERA_ID')),
        'LIBCAMERA.IMAGE_FILE_TYPE' : ('libcamera_image_file_type', ('libcamera', 'IMAGE_FILE_TYPE'), ('libcamera', 'image_file_type')),
        'LIBCAMERA.EXTRA_OPTIONS' : ('libcamera_extra_options', ('libcamera', 'EXTRA_OPTIONS'), ('libcamera', 'extra_options')),
        'CCD_CONFIG.NIGHT.GAIN' : ('gain_night', ('ccd_config', 'NIGHT', 'GAIN')),
        'CCD_CONFIG.NIGHT.BINNING' : ('binning_night', ('ccd_config', 'NIGHT', 'BINNING')),
        'CCD_CONFIG.MOONMODE.GAIN' : ('gain_moonmode', ('ccd_config', 'MOONMODE', 'GAIN')),
        'CCD_CONFIG.MOONMODE.BINNING' : ('binning_moonmode', ('ccd_config', 'MOONMODE', 'BINNING')),
        'CCD_CONFIG.DAY.GAIN' : ('gain_day', ('ccd_config', 'DAY', 'GAIN')),
        'CCD_CONFIG.DAY.BINNING' : ('binning_day', ('ccd_config', 'DAY', 'BINNING')),
        'EXPOSURE_PERIOD' : ('exposure_period',),
        'EXPOSURE_PERIOD_DAY' : ('exposure_period_day',),
        'CCD_EXPOSURE_MIN' : ('exposure_min',),
        'CCD_EXPOSURE_MIN_DAY' : ('exposure_min_day',),
        'CCD_EXPOSURE_DEF' : ('exposure_default',),
        'CCD_EXPOSURE_MAX' : ('exposure_max',),
        'CCD_EXPOSURE_TIMEOUT' : ('exposure_timeout',),
        'CCD_COOLING' : ('cooling_enabled',),
        'CCD_TEMP' : ('target_temperature',),
        'DAYTIME_CAPTURE' : ('daytime_capture',),
        'DAYTIME_CAPTURE_SAVE' : ('daytime_capture_save',),
        'CCD_BIT_DEPTH' : ('ccd_bit_depth',),
        'CFA_PATTERN' : ('cfa_pattern',),
        'LIBCAMERA.AWB' : ('libcamera_awb', ('libcamera', 'AWB'), ('libcamera', 'awb')),
        'LIBCAMERA.AWB_DAY' : ('libcamera_awb_day', ('libcamera', 'AWB_DAY'), ('libcamera', 'awb_day')),
        'LIBCAMERA.AWB_ENABLE' : ('libcamera_awb_enable', ('libcamera', 'AWB_ENABLE'), ('libcamera', 'awb_enable')),
        'LIBCAMERA.AWB_MODE' : ('libcamera_awb_mode', ('libcamera', 'AWB_MODE'), ('libcamera', 'awb_mode')),
        'LIBCAMERA.AWB_RED_GAIN' : ('libcamera_awb_red_gain', ('libcamera', 'AWB_RED_GAIN'), ('libcamera', 'awb_red_gain')),
        'LIBCAMERA.AWB_BLUE_GAIN' : ('libcamera_awb_blue_gain', ('libcamera', 'AWB_BLUE_GAIN'), ('libcamera', 'awb_blue_gain')),
        'LIBCAMERA.IMMEDIATE' : ('libcamera_immediate', ('libcamera', 'IMMEDIATE'), ('libcamera', 'immediate')),
        'LIBCAMERA.IMMEDIATE_DAY' : ('libcamera_immediate_day', ('libcamera', 'IMMEDIATE_DAY'), ('libcamera', 'immediate_day')),
        'LENS_NAME' : ('lens_name', ('lens', 'name')),
        'LENS_FOCAL_LENGTH' : ('lens_focal_length', ('lens', 'focal_length')),
        'LENS_FOCAL_RATIO' : ('lens_focal_ratio', ('lens', 'focal_ratio')),
        'LENS_IMAGE_CIRCLE' : ('lens_image_circle', ('lens', 'image_circle')),
        'LENS_OFFSET_X' : ('lens_offset_x', ('lens', 'offset_x')),
        'LENS_OFFSET_Y' : ('lens_offset_y', ('lens', 'offset_y')),
        'LENS_ALTITUDE' : ('lens_altitude', ('lens', 'altitude')),
        'LENS_AZIMUTH' : ('lens_azimuth', ('lens', 'azimuth')),
        'IMAGE_ROTATE' : ('image_rotate', ('image', 'rotate')),
        'IMAGE_ROTATE_ANGLE' : ('image_rotate_angle', ('image', 'rotate_angle')),
        'IMAGE_FLIP_V' : ('image_flip_v', ('image', 'flip_v')),
        'IMAGE_FLIP_H' : ('image_flip_h', ('image', 'flip_h')),
        'IMAGE_CIRCLE_MASK.ENABLE' : ('image_circle_mask_enable', ('image_circle_mask', 'enable')),
        'IMAGE_CIRCLE_MASK.DIAMETER' : ('image_circle_mask_diameter', ('image_circle_mask', 'diameter')),
        'IMAGE_CIRCLE_MASK.OFFSET_X' : ('image_circle_mask_offset_x', ('image_circle_mask', 'offset_x')),
        'IMAGE_CIRCLE_MASK.OFFSET_Y' : ('image_circle_mask_offset_y', ('image_circle_mask', 'offset_y')),
        'IMAGE_CIRCLE_MASK.BLUR' : ('image_circle_mask_blur', ('image_circle_mask', 'blur')),
        'IMAGE_CIRCLE_MASK.OPACITY' : ('image_circle_mask_opacity', ('image_circle_mask', 'opacity')),
        'IMAGE_CIRCLE_MASK.OUTLINE' : ('image_circle_mask_outline', ('image_circle_mask', 'outline')),
        'IMAGE_CROP_ROI' : ('image_crop_roi', ('image', 'crop_roi')),
        'IMAGE_CROP_IMAGE_CIRCLE' : ('image_crop_image_circle', ('image', 'crop_image_circle')),
        'ADU_ROI' : ('adu_roi',),
        'SQM_ROI' : ('sqm_roi',),
    }

    CAMERA_SETTINGS_SECTIONS = (
        {
            'title' : 'Profile',
            'default_open' : True,
            'fields' : (
                'profile_id',
                'profile_label',
                'profile_enabled',
                'profile_primary',
                'db_camera_id',
                'db_camera_name',
                'db_camera_driver',
                'db_camera_status',
            ),
        },
        {
            'title' : 'Driver / Connection',
            'default_open' : True,
            'fields' : (
                'CAMERA_INTERFACE',
                'INDI_SERVER',
                'INDI_PORT',
                'INDI_CAMERA_NAME',
                'LIBCAMERA.CAMERA_ID',
                'LIBCAMERA.IMAGE_FILE_TYPE',
                'LIBCAMERA.AWB_MODE',
                'LIBCAMERA.AWB_RED_GAIN',
                'LIBCAMERA.AWB_BLUE_GAIN',
                'LIBCAMERA.EXTRA_OPTIONS',
            ),
        },
        {
            'title' : 'Capture',
            'default_open' : True,
            'fields' : (
                'EXPOSURE_PERIOD',
                'EXPOSURE_PERIOD_DAY',
                'CCD_EXPOSURE_MIN',
                'CCD_EXPOSURE_MIN_DAY',
                'CCD_EXPOSURE_DEF',
                'CCD_EXPOSURE_MAX',
                'CCD_EXPOSURE_TIMEOUT',
                'CCD_CONFIG.NIGHT.GAIN',
                'CCD_CONFIG.NIGHT.BINNING',
                'CCD_CONFIG.MOONMODE.GAIN',
                'CCD_CONFIG.MOONMODE.BINNING',
                'CCD_CONFIG.DAY.GAIN',
                'CCD_CONFIG.DAY.BINNING',
                'DAYTIME_CAPTURE',
                'DAYTIME_CAPTURE_SAVE',
                'TARGET_ADU',
                'TARGET_ADU_DAY',
            ),
        },
        {
            'title' : 'Lens & Optics',
            'default_open' : False,
            'fields' : (
                'LENS_NAME',
                'LENS_FOCAL_LENGTH',
                'LENS_FOCAL_RATIO',
                'LENS_IMAGE_CIRCLE',
                'LENS_OFFSET_X',
                'LENS_OFFSET_Y',
                'LENS_ALTITUDE',
                'LENS_AZIMUTH',
                'IMAGE_ROTATE',
                'IMAGE_ROTATE_ANGLE',
                'IMAGE_FLIP_V',
                'IMAGE_FLIP_H',
                'IMAGE_CIRCLE_MASK.ENABLE',
                'IMAGE_CIRCLE_MASK.DIAMETER',
                'IMAGE_CIRCLE_MASK.OFFSET_X',
                'IMAGE_CIRCLE_MASK.OFFSET_Y',
                'IMAGE_CIRCLE_MASK.BLUR',
                'IMAGE_CIRCLE_MASK.OPACITY',
                'IMAGE_CIRCLE_MASK.OUTLINE',
                'IMAGE_CROP_ROI',
                'IMAGE_CROP_IMAGE_CIRCLE',
                'ADU_ROI',
                'SQM_ROI',
            ),
        },
        {
            'title' : 'Processing',
            'default_open' : False,
            'fields' : (
                'CCD_BIT_DEPTH',
                'CFA_PATTERN',
                'USE_NIGHT_COLOR',
                'AUTO_WB',
                'AUTO_WB_DAY',
                'NIGHT_GRAYSCALE',
                'DAYTIME_GRAYSCALE',
                'CCD_COOLING',
                'CCD_TEMP',
                'IMAGE_CALIBRATE_DARK',
                'IMAGE_CALIBRATE_BPM',
                'IMAGE_CALIBRATE_FIX_HOLES',
                'IMAGE_CALIBRATE_HOLE_THOLD',
                'IMAGE_CALIBRATE_MANUAL_OFFSET',
            ),
        },
        {
            'title' : 'Hybrid Controller',
            'default_open' : True,
            'fields' : (
                'PROCESSING_MODE',
            ),
        },
        {
            'title' : 'Advanced',
            'default_open' : False,
            'fields' : (
                'INDI_CONFIG_DEFAULTS',
                'INDI_CONFIG_DAY',
                'LIBCAMERA.AWB',
                'LIBCAMERA.AWB_DAY',
                'LIBCAMERA.AWB_ENABLE',
                'LIBCAMERA.IMMEDIATE',
                'LIBCAMERA.IMMEDIATE_DAY',
            ),
        },
    )

    CAMERA_SETTINGS_PROFILE_FIELDS = {
        'profile_id',
        'profile_label',
        'profile_enabled',
        'profile_primary',
    }
    CAMERA_SETTINGS_DB_FIELDS = {
        'db_camera_id',
        'db_camera_name',
        'db_camera_driver',
        'db_camera_status',
    }
    CAMERA_SETTINGS_DRIVER_EDIT_FIELD_ORDER = (
        'profile_id',
        'enabled',
        'primary',
        'camera_interface',
        'indi_server',
        'indi_port',
        'indi_camera_name',
        'libcamera_camera_id',
        'libcamera_image_file_type',
        'libcamera_awb_mode',
        'libcamera_awb_red_gain',
        'libcamera_awb_blue_gain',
        'libcamera_extra_options',
    )
    CAMERA_SETTINGS_DRIVER_OPTIONAL_PROFILE_FIELDS = {
        'libcamera_image_file_type',
        'libcamera_extra_options',
    }
    CAMERA_SETTINGS_DRIVER_TRANSIENT_PROFILE_KEYS = (
        'indi_server',
        'indi_port',
        'indi_camera_name',
        'libcamera_camera_id',
        'libcamera_image_file_type',
        'libcamera_awb_mode',
        'libcamera_awb_red_gain',
        'libcamera_awb_blue_gain',
        'libcamera_extra_options',
    )
    CAMERA_SETTINGS_DRIVER_FIELD_LABELS = {
        'profile_id'                 : 'Profile ID',
        'enabled'                    : 'Enabled',
        'primary'                    : 'Primary',
        'camera_interface'           : 'Camera Interface',
        'indi_server'                : 'INDI Server',
        'indi_port'                  : 'INDI Port',
        'indi_camera_name'           : 'INDI Camera Name',
        'libcamera_camera_id'        : 'libcamera Camera ID',
        'libcamera_image_file_type'  : 'libcamera Image Type',
        'libcamera_awb_mode'         : 'libcamera AWB Mode',
        'libcamera_awb_red_gain'     : 'libcamera AWB Red Gain',
        'libcamera_awb_blue_gain'    : 'libcamera AWB Blue Gain',
        'libcamera_extra_options'    : 'libcamera Extra Options',
    }
    CAMERA_SETTINGS_LIBCAMERA_AWB_MODES = (
        'auto',
        'fixed',
        'daylight',
        'cloudy',
        'tungsten',
        'fluorescent',
        'indoor',
    )
    CAMERA_SETTINGS_PROCESSING_MODES = (
        'classic',
        'hybrid',
    )
    CAMERA_SETTINGS_LENS_EDIT_FIELD_ORDER = (
        'lens_name',
        'lens_focal_length',
        'lens_focal_ratio',
        'lens_image_circle',
        'lens_offset_x',
        'lens_offset_y',
        'lens_altitude',
        'lens_azimuth',
        'image_rotate',
        'image_rotate_angle',
        'image_flip_v',
        'image_flip_h',
        'image_circle_mask_enable',
        'image_circle_mask_diameter',
        'image_circle_mask_offset_x',
        'image_circle_mask_offset_y',
        'image_circle_mask_blur',
        'image_circle_mask_opacity',
        'image_circle_mask_outline',
        'image_crop_roi',
        'image_crop_image_circle',
        'adu_roi',
        'sqm_roi',
    )
    CAMERA_SETTINGS_LENS_FIELD_CONFIG_KEYS = {
        'lens_name'                 : 'LENS_NAME',
        'lens_focal_length'         : 'LENS_FOCAL_LENGTH',
        'lens_focal_ratio'          : 'LENS_FOCAL_RATIO',
        'lens_image_circle'         : 'LENS_IMAGE_CIRCLE',
        'lens_offset_x'             : 'LENS_OFFSET_X',
        'lens_offset_y'             : 'LENS_OFFSET_Y',
        'lens_altitude'             : 'LENS_ALTITUDE',
        'lens_azimuth'              : 'LENS_AZIMUTH',
        'image_rotate'              : 'IMAGE_ROTATE',
        'image_rotate_angle'        : 'IMAGE_ROTATE_ANGLE',
        'image_flip_v'              : 'IMAGE_FLIP_V',
        'image_flip_h'              : 'IMAGE_FLIP_H',
        'image_circle_mask_enable'  : 'IMAGE_CIRCLE_MASK.ENABLE',
        'image_circle_mask_diameter': 'IMAGE_CIRCLE_MASK.DIAMETER',
        'image_circle_mask_offset_x': 'IMAGE_CIRCLE_MASK.OFFSET_X',
        'image_circle_mask_offset_y': 'IMAGE_CIRCLE_MASK.OFFSET_Y',
        'image_circle_mask_blur'    : 'IMAGE_CIRCLE_MASK.BLUR',
        'image_circle_mask_opacity' : 'IMAGE_CIRCLE_MASK.OPACITY',
        'image_circle_mask_outline' : 'IMAGE_CIRCLE_MASK.OUTLINE',
        'image_crop_roi'            : 'IMAGE_CROP_ROI',
        'image_crop_image_circle'   : 'IMAGE_CROP_IMAGE_CIRCLE',
        'adu_roi'                   : 'ADU_ROI',
        'sqm_roi'                   : 'SQM_ROI',
    }
    CAMERA_SETTINGS_LENS_FIELD_LABELS = {
        'lens_name'                 : 'Lens Name',
        'lens_focal_length'         : 'Focal Length',
        'lens_focal_ratio'          : 'Focal Ratio',
        'lens_image_circle'         : 'Image Circle Diameter',
        'lens_offset_x'             : 'Image Circle Offset X',
        'lens_offset_y'             : 'Image Circle Offset Y',
        'lens_altitude'             : 'Lens Altitude',
        'lens_azimuth'              : 'Lens Azimuth',
        'image_rotate'              : 'Image Rotate',
        'image_rotate_angle'        : 'Image Rotate Angle',
        'image_flip_v'              : 'Flip Vertical',
        'image_flip_h'              : 'Flip Horizontal',
        'image_circle_mask_enable'  : 'Image Circle Mask',
        'image_circle_mask_diameter': 'Mask Diameter',
        'image_circle_mask_offset_x': 'Mask Offset X',
        'image_circle_mask_offset_y': 'Mask Offset Y',
        'image_circle_mask_blur'    : 'Mask Blur',
        'image_circle_mask_opacity' : 'Mask Opacity',
        'image_circle_mask_outline' : 'Mask Outline',
        'image_crop_roi'            : 'Image Crop ROI',
        'image_crop_image_circle'   : 'Crop to Image Circle',
        'adu_roi'                   : 'ADU ROI',
        'sqm_roi'                   : 'SQM ROI',
    }
    CAMERA_SETTINGS_LENS_FIELD_TYPES = {
        'lens_name'                 : 'text',
        'lens_focal_length'         : 'float',
        'lens_focal_ratio'          : 'float',
        'lens_image_circle'         : 'integer',
        'lens_offset_x'             : 'integer',
        'lens_offset_y'             : 'integer',
        'lens_altitude'             : 'float',
        'lens_azimuth'              : 'float',
        'image_rotate'              : 'select',
        'image_rotate_angle'        : 'integer',
        'image_flip_v'              : 'boolean_select',
        'image_flip_h'              : 'boolean_select',
        'image_circle_mask_enable'  : 'boolean_select',
        'image_circle_mask_diameter': 'integer',
        'image_circle_mask_offset_x': 'integer',
        'image_circle_mask_offset_y': 'integer',
        'image_circle_mask_blur'    : 'integer',
        'image_circle_mask_opacity' : 'integer',
        'image_circle_mask_outline' : 'boolean_select',
        'image_crop_roi'            : 'csv_integer_list',
        'image_crop_image_circle'   : 'boolean_select',
        'adu_roi'                   : 'csv_integer_list',
        'sqm_roi'                   : 'csv_integer_list',
    }
    CAMERA_SETTINGS_LENS_NON_NEGATIVE_FIELDS = {
        'lens_focal_length',
        'lens_focal_ratio',
        'lens_image_circle',
        'lens_altitude',
        'lens_azimuth',
        'image_circle_mask_diameter',
        'image_circle_mask_blur',
        'image_circle_mask_opacity',
    }
    CAMERA_SETTINGS_LENS_CHECKBOX_FIELDS = {
        'image_flip_v',
        'image_flip_h',
        'image_circle_mask_enable',
        'image_circle_mask_outline',
        'image_crop_image_circle',
    }
    CAMERA_SETTINGS_LENS_ROTATE_CHOICES = (
        '',
        'ROTATE_90_CLOCKWISE',
        'ROTATE_90_COUNTERCLOCKWISE',
        'ROTATE_180',
    )

    def get_context(self):
        context = ModernAdminContextMixin.get_context(self)
        profiles = self.get_camera_settings_profiles()
        selected_profile = self.get_selected_camera_settings_profile(profiles)
        camera_map = self.get_camera_settings_camera_map(profiles)
        selected_camera = self.get_camera_settings_profile_camera(selected_profile, camera_map)

        context['modern_admin_camera_settings_error'] = None
        context['modern_admin_camera_settings_success'] = None
        context['modern_admin_camera_settings_errors'] = {}

        if request.method == 'POST':
            modern_admin_action = request.form.get('modern_admin_action', 'driver_connection')
            if modern_admin_action == 'hybrid_controller':
                context.update(self.save_camera_settings_hybrid_profile())
            elif modern_admin_action == 'lens_optics':
                context.update(self.save_camera_settings_lens_profile())
            else:
                context.update(self.save_camera_settings_driver_profile())
            profiles = self.get_camera_settings_profiles()
            selected_profile = self.get_selected_camera_settings_profile(profiles)
            camera_map = self.get_camera_settings_camera_map(profiles)
            selected_camera = self.get_camera_settings_profile_camera(selected_profile, camera_map)

        context['modern_admin_camera_settings_profiles'] = profiles
        context['modern_admin_camera_settings_profile'] = selected_profile
        context['modern_admin_camera_settings_camera'] = selected_camera
        context['modern_admin_camera_settings_sections'] = self.get_camera_settings_sections(selected_profile, selected_camera)
        context['modern_admin_camera_settings_profile_count'] = len(profiles)
        context['modern_admin_camera_settings_uses_multi_camera'] = bool(selected_profile.get('from_multi_camera'))
        if 'modern_admin_camera_settings_driver_form' not in context:
            context['modern_admin_camera_settings_driver_form'] = self.get_camera_settings_driver_form(selected_profile)
        if 'modern_admin_camera_settings_lens_form' not in context:
            context['modern_admin_camera_settings_lens_form'] = self.get_camera_settings_lens_form(selected_profile)
        if 'modern_admin_camera_settings_hybrid_form' not in context:
            context['modern_admin_camera_settings_hybrid_form'] = self.get_camera_settings_hybrid_form(selected_profile)

        return context


    def get_camera_settings_profiles(self):
        try:
            profiles = self.indi_allsky_config.get('MULTI_CAMERA', {}).get('profiles', [])
        except AttributeError:
            profiles = []

        normalized_profiles = list()
        if isinstance(profiles, list):
            for profile_index, profile in enumerate(profiles, start=1):
                if not isinstance(profile, dict):
                    continue

                profile_id = str(profile.get('profile_id') or profile.get('id') or 'profile-{0:d}'.format(profile_index))
                profile_label = str(profile.get('label') or profile.get('camera_name') or profile_id)
                profile_copy = dict(profile)
                profile_copy.update({
                    '_profile_index'     : profile_index,
                    'profile_id'         : profile_id,
                    '_profile_label'     : profile_label,
                    'from_multi_camera'  : True,
                    '_selector_label'    : profile_label,
                    '_selector_subtitle' : profile_id,
                })
                normalized_profiles.append(profile_copy)

        if normalized_profiles:
            return tuple(normalized_profiles)

        camera_name = 'Current config'
        if getattr(self, 'camera', None):
            camera_name = str(self.camera.friendlyName or self.camera.name or 'Current camera')

        return ({
            '_profile_index'     : 1,
            'profile_id'         : 'current-config',
            '_profile_label'     : camera_name,
            'enabled'            : True,
            'primary'            : True,
            'from_multi_camera'  : False,
            '_selector_label'    : camera_name,
            '_selector_subtitle' : 'active camera / current config',
            '_fallback_camera_id': getattr(getattr(self, 'camera', None), 'id', None),
        },)


    def get_selected_camera_settings_profile(self, profiles):
        if not profiles:
            return {}

        selected_profile_id = request.args.get('profile_id', '')
        for profile in profiles:
            if str(profile.get('profile_id')) == selected_profile_id:
                return profile

        return profiles[0]


    def get_selected_camera_settings_profile_for_save(self, profiles):
        if not profiles:
            return None

        selected_profile_id = request.args.get('profile_id', '')
        if not selected_profile_id:
            return None

        for profile in profiles:
            if str(profile.get('profile_id')) == selected_profile_id:
                return profile

        return None


    def get_camera_settings_camera_map(self, profiles):
        camera_ids = set()
        for profile in profiles:
            camera_id = self.get_camera_settings_profile_camera_id(profile)
            if camera_id:
                camera_ids.add(camera_id)

        if getattr(self, 'camera', None):
            camera_ids.add(self.camera.id)

        if not camera_ids:
            return {}

        try:
            camera_rows = IndiAllSkyDbCameraTable.query\
                .filter(IndiAllSkyDbCameraTable.id.in_(camera_ids))\
                .all()
        except Exception as e:
            app.logger.error('Error reading camera settings DB camera rows: %s', str(e))
            return {}

        return {
            camera.id : camera
            for camera in camera_rows
        }


    def get_camera_settings_profile_camera_id(self, profile):
        for key in ('db_camera_id', 'camera_db_id', 'camera_id'):
            if key not in profile:
                continue

            try:
                return int(profile[key])
            except (TypeError, ValueError):
                continue

        fallback_camera_id = profile.get('_fallback_camera_id')
        if fallback_camera_id:
            try:
                return int(fallback_camera_id)
            except (TypeError, ValueError):
                return None

        return None


    def get_camera_settings_profile_camera(self, profile, camera_map):
        camera_id = self.get_camera_settings_profile_camera_id(profile)
        if camera_id and camera_id in camera_map:
            return camera_map[camera_id]

        if profile.get('from_multi_camera'):
            return None

        return getattr(self, 'camera', None)


    def get_camera_settings_sections(self, profile, db_camera):
        sections = list()
        for section in self.CAMERA_SETTINGS_SECTIONS:
            rows = list()
            for config_key in section['fields']:
                rows.append(self.get_camera_settings_row(config_key, profile, db_camera))

            sections.append({
                'title'        : section['title'],
                'key'          : re.sub(r'[^a-z0-9]+', '-', section['title'].lower()).strip('-'),
                'fields'       : rows,
                'count'        : len(rows),
                'default_open' : bool(section.get('default_open')),
            })

        return sections


    def get_camera_settings_row(self, config_key, profile, db_camera):
        value, source = self.get_camera_settings_effective_value(config_key, profile, db_camera)
        display_value = self.format_camera_settings_value(config_key, value, source)
        search_text = ' '.join((
            self.CAMERA_SETTINGS_FIELD_LABELS.get(config_key, config_key),
            config_key,
            display_value,
            source,
            self.estimate_camera_settings_scope(config_key),
            self.estimate_camera_settings_restart(config_key),
        )).lower()

        return {
            'label'            : self.CAMERA_SETTINGS_FIELD_LABELS.get(config_key, config_key.replace('_', ' ').title()),
            'config_key'       : config_key,
            'current_value'    : display_value,
            'source'           : source,
            'source_class'     : re.sub(r'[^a-z0-9]+', '-', source.lower()).strip('-'),
            'scope'            : self.estimate_camera_settings_scope(config_key),
            'restart_required' : self.estimate_camera_settings_restart(config_key),
            'search_text'      : search_text,
        }


    def get_camera_settings_effective_value(self, config_key, profile, db_camera):
        if config_key in self.CAMERA_SETTINGS_PROFILE_FIELDS:
            return self.get_camera_settings_profile_field_value(config_key, profile), 'derived'

        if config_key in self.CAMERA_SETTINGS_DB_FIELDS:
            return self.get_camera_settings_db_field_value(config_key, db_camera, profile), 'db camera' if db_camera else 'missing'

        found, value = self.get_camera_settings_profile_override(profile, config_key)
        if found:
            return value, 'profile override'

        if config_key == 'PROCESSING_MODE':
            return 'classic', 'derived'

        found, value = self.get_camera_settings_config_value(config_key)
        if found:
            return value, 'global config'

        return None, 'missing'


    def get_camera_settings_profile_field_value(self, config_key, profile):
        if config_key == 'profile_id':
            return profile.get('profile_id')
        elif config_key == 'profile_label':
            return profile.get('_profile_label') or profile.get('label') or profile.get('camera_name')
        elif config_key == 'profile_enabled':
            return bool(profile.get('enabled', True))
        elif config_key == 'profile_primary':
            return bool(profile.get('primary', False))

        return None


    def get_camera_settings_db_field_value(self, config_key, db_camera, profile):
        if not db_camera:
            if config_key == 'db_camera_id':
                return self.get_camera_settings_profile_camera_id(profile)

            return None

        if config_key == 'db_camera_id':
            return db_camera.id
        elif config_key == 'db_camera_name':
            return db_camera.friendlyName or db_camera.name
        elif config_key == 'db_camera_driver':
            return db_camera.driver
        elif config_key == 'db_camera_status':
            if getattr(getattr(self, 'camera', None), 'id', None) == db_camera.id:
                return 'Active'

            return 'Configured'

        return None


    def get_camera_settings_profile_override(self, profile, config_key):
        candidates = [config_key, config_key.replace('.', '__')]
        candidates.extend(self.CAMERA_SETTINGS_PROFILE_ALIASES.get(config_key, tuple()))

        for candidate in candidates:
            found, value = self.get_camera_settings_nested_value(profile, candidate)
            if found:
                return True, value

        return False, None


    def get_camera_settings_config_value(self, config_key):
        return self.get_camera_settings_nested_value(self.indi_allsky_config, config_key)


    def get_camera_settings_nested_value(self, data, path):
        if not isinstance(data, dict):
            return False, None

        if isinstance(path, str):
            if path in data:
                return True, data[path]

            path_parts = path.replace('__', '.').split('.')
        else:
            path_parts = list(path)

        current = data
        for path_part in path_parts:
            if not isinstance(current, dict):
                return False, None

            candidate_keys = (
                path_part,
                str(path_part).upper(),
                str(path_part).lower(),
            )
            found_key = None
            for candidate_key in candidate_keys:
                if candidate_key in current:
                    found_key = candidate_key
                    break

            if found_key is None:
                return False, None

            current = current[found_key]

        return True, current


    def get_camera_settings_hybrid_form(self, profile, submitted_data=None, errors=None):
        submitted_data = submitted_data or {}
        errors = errors or {}
        processing_mode = str(submitted_data.get('processing_mode', self.get_camera_settings_processing_mode(profile)) or 'classic').lower()

        return {
            'enabled'         : bool(profile.get('from_multi_camera')),
            'processing_mode' : processing_mode,
            'choices'         : self.get_camera_settings_processing_mode_choices(processing_mode),
            'errors'          : errors.get('processing_mode', []),
            'readonly'        : not profile.get('from_multi_camera'),
        }


    def get_camera_settings_processing_mode(self, profile):
        found, value = self.get_camera_settings_profile_override(profile, 'PROCESSING_MODE')
        if found:
            processing_mode = str(value or 'classic').strip().lower()
            if processing_mode in self.CAMERA_SETTINGS_PROCESSING_MODES:
                return processing_mode

        return 'classic'


    def get_camera_settings_processing_mode_choices(self, value):
        labels = {
            'classic' : 'Classic',
            'hybrid'  : 'Hybrid',
        }
        return tuple({
            'value'    : processing_mode,
            'label'    : labels[processing_mode],
            'selected' : processing_mode == value,
        } for processing_mode in self.CAMERA_SETTINGS_PROCESSING_MODES)


    def save_camera_settings_hybrid_profile(self):
        result = {
            'modern_admin_camera_settings_error'   : None,
            'modern_admin_camera_settings_success' : None,
            'modern_admin_camera_settings_errors'  : {},
        }

        if not app.config['LOGIN_DISABLED'] and not current_user.is_admin:
            result['modern_admin_camera_settings_error'] = 'Only an admin user can change camera profile settings.'
            return result

        profiles = self.get_camera_settings_profiles()
        selected_profile = self.get_selected_camera_settings_profile_for_save(profiles)
        if not selected_profile:
            result['modern_admin_camera_settings_error'] = 'Select a valid multi-camera profile before saving. No config was saved.'
            return result

        if not selected_profile.get('from_multi_camera'):
            result['modern_admin_camera_settings_error'] = 'The current global camera fallback is read-only. Select a MULTI_CAMERA profile before saving.'
            return result

        submitted_data, validation_errors = self.get_camera_settings_hybrid_submitted_data()
        if validation_errors:
            result['modern_admin_camera_settings_error'] = 'Please fix the Hybrid Controller settings below. No config was saved.'
            result['modern_admin_camera_settings_errors'] = validation_errors
            result['modern_admin_camera_settings_hybrid_form'] = self.get_camera_settings_hybrid_form(selected_profile, submitted_data, validation_errors)
            return result

        try:
            new_config = json.loads(json.dumps(self.indi_allsky_config), object_pairs_hook=OrderedDict)
            updated_profile_id = self.apply_camera_settings_hybrid_profile_to_config(
                new_config,
                selected_profile.get('profile_id'),
                selected_profile.get('_profile_index'),
                submitted_data,
            )

            if not app.config['LOGIN_DISABLED']:
                username = current_user.username
            else:
                username = 'system'

            from ..config import IndiAllSkyConfig

            config_obj = IndiAllSkyConfig()
            config_obj.config = new_config
            config_obj.save(username, 'Modern Admin Camera Hybrid Controller update for {0:s}'.format(updated_profile_id))
            self.indi_allsky_config = new_config
            app.logger.info('Saved Modern Admin Camera Hybrid Controller config update for profile %s', updated_profile_id)
            result['modern_admin_camera_settings_success'] = 'Hybrid Controller saved for profile {0:s}. Restart indi-allsky for the running capture service to use the new mode.'.format(updated_profile_id)
        except ConfigSaveException as e:
            db.session.rollback()
            result['modern_admin_camera_settings_error'] = str(e)
        except Exception as e:
            db.session.rollback()
            app.logger.error('Error saving Modern Admin Camera Hybrid Controller: %s', str(e))
            result['modern_admin_camera_settings_error'] = 'Unable to save Hybrid Controller: {0:s}'.format(str(e))

        return result


    def get_camera_settings_hybrid_submitted_data(self):
        submitted_data = {}
        validation_errors = dict()

        processing_mode = request.form.get('processing_mode', 'classic').strip().lower() or 'classic'
        submitted_data['processing_mode'] = processing_mode
        if processing_mode not in self.CAMERA_SETTINGS_PROCESSING_MODES:
            validation_errors.setdefault('processing_mode', []).append('Select Classic or Hybrid.')

        return submitted_data, validation_errors


    def apply_camera_settings_hybrid_profile_to_config(self, config, profile_id, profile_index, submitted_data):
        multi_camera_config = config.get('MULTI_CAMERA')
        if not isinstance(multi_camera_config, dict):
            raise ValueError('MULTI_CAMERA config is missing or invalid.')

        profiles = multi_camera_config.get('profiles')
        if not isinstance(profiles, list):
            raise ValueError('MULTI_CAMERA.profiles is missing or invalid.')

        profile_offset = int(profile_index) - 1
        if profile_offset < 0 or profile_offset >= len(profiles):
            raise ValueError('Selected profile no longer exists.')

        profile = profiles[profile_offset]
        if not isinstance(profile, dict):
            raise ValueError('Selected profile is not editable.')

        if str(profile.get('profile_id') or profile.get('id') or 'profile-{0:d}'.format(profile_index)) != str(profile_id):
            raise ValueError('Selected profile changed before save. Reload and try again.')

        profile['processing_mode'] = submitted_data['processing_mode']
        return str(profile_id)


    def get_camera_settings_driver_form(self, profile, submitted_data=None, errors=None):
        submitted_data = submitted_data or {}
        errors = errors or {}
        fields = list()
        camera_interface = submitted_data.get('camera_interface', self.get_camera_settings_driver_field_value(profile, 'camera_interface'))
        driver_type = self.get_camera_settings_driver_type(camera_interface)
        libcamera_awb_mode = str(submitted_data.get('libcamera_awb_mode', self.get_camera_settings_driver_field_value(profile, 'libcamera_awb_mode')) or 'auto').lower()

        for field_name in self.CAMERA_SETTINGS_DRIVER_EDIT_FIELD_ORDER:
            if field_name in self.CAMERA_SETTINGS_DRIVER_OPTIONAL_PROFILE_FIELDS and not self.profile_has_camera_settings_driver_field(profile, field_name):
                continue

            value = submitted_data.get(field_name, self.get_camera_settings_driver_field_value(profile, field_name))
            field_type = self.get_camera_settings_driver_field_type(field_name)
            field_role = self.get_camera_settings_driver_field_role(field_name)
            field_required = self.is_camera_settings_driver_field_required(field_name, driver_type)
            if driver_type == 'libcamera' and libcamera_awb_mode == 'fixed' and field_name in ('libcamera_awb_red_gain', 'libcamera_awb_blue_gain'):
                field_required = True
            field_disabled = not self.is_camera_settings_driver_field_relevant(field_name, driver_type)
            fields.append({
                'name'        : field_name,
                'label'       : self.CAMERA_SETTINGS_DRIVER_FIELD_LABELS[field_name],
                'value'       : value,
                'display'     : self.format_structured_settings_value(value) if value not in (None, '') else 'Not configured',
                'input_type'  : field_type,
                'readonly'    : field_name == 'profile_id' or not profile.get('from_multi_camera'),
                'disabled'    : field_disabled,
                'required'    : field_required,
                'role'        : field_role,
                'errors'      : errors.get(field_name, []),
                'choices'     : self.get_camera_settings_driver_field_choices(field_name, value),
                'step'        : self.get_camera_settings_driver_field_step(field_name),
                'min'         : self.get_camera_settings_driver_field_min(field_name),
                'help'        : self.get_camera_settings_driver_field_help(field_name),
            })

        return {
            'enabled' : bool(profile.get('from_multi_camera')),
            'fields'  : fields,
        }


    def get_camera_settings_driver_type(self, camera_interface):
        camera_interface = str(camera_interface or '')
        if camera_interface.startswith('libcamera'):
            return 'libcamera'
        elif camera_interface == 'indi':
            return 'indi'

        return 'other'


    def get_camera_settings_driver_field_role(self, field_name):
        if field_name in ('indi_server', 'indi_port', 'indi_camera_name'):
            return 'indi'
        elif field_name in (
            'libcamera_camera_id',
            'libcamera_image_file_type',
            'libcamera_awb_mode',
            'libcamera_awb_red_gain',
            'libcamera_awb_blue_gain',
            'libcamera_extra_options',
        ):
            return 'libcamera'

        return 'common'


    def is_camera_settings_driver_field_relevant(self, field_name, driver_type):
        field_role = self.get_camera_settings_driver_field_role(field_name)
        return field_role == 'common' or field_role == driver_type


    def is_camera_settings_driver_field_required(self, field_name, driver_type):
        if driver_type == 'indi':
            return field_name in ('camera_interface', 'indi_server', 'indi_port', 'indi_camera_name')
        elif driver_type == 'libcamera':
            return field_name in ('camera_interface', 'libcamera_camera_id')

        return field_name == 'camera_interface'


    def get_camera_settings_driver_field_type(self, field_name):
        if field_name in ('enabled', 'primary'):
            return 'checkbox'
        elif field_name in ('camera_interface', 'libcamera_awb_mode'):
            return 'select'
        elif field_name in ('indi_port', 'libcamera_camera_id', 'libcamera_awb_red_gain', 'libcamera_awb_blue_gain'):
            return 'number'

        return 'text'


    def get_camera_settings_driver_field_step(self, field_name):
        if field_name in ('libcamera_awb_red_gain', 'libcamera_awb_blue_gain'):
            return '0.01'

        return '1'


    def get_camera_settings_driver_field_min(self, field_name):
        if field_name == 'indi_port':
            return '1'
        elif field_name in ('libcamera_awb_red_gain', 'libcamera_awb_blue_gain'):
            return '0.01'

        return '0'


    def get_camera_settings_driver_field_help(self, field_name):
        if field_name == 'libcamera_awb_mode':
            return 'Use fixed to emit --awbgains instead of --awb. Auto preserves current behavior.'
        elif field_name in ('libcamera_awb_red_gain', 'libcamera_awb_blue_gain'):
            return 'Required only when libcamera AWB Mode is fixed.'

        return ''


    def get_camera_settings_driver_field_choices(self, field_name, value):
        if field_name == 'libcamera_awb_mode':
            value = str(value or 'auto')
            return tuple({
                'value'    : awb_mode,
                'label'    : awb_mode,
                'selected' : awb_mode == value,
            } for awb_mode in self.CAMERA_SETTINGS_LIBCAMERA_AWB_MODES)

        if field_name != 'camera_interface':
            return tuple()

        choices = list()
        value_seen = False
        for interface in get_modern_admin_supported_camera_interfaces():
            choice_value = str(interface['value'])
            if choice_value == str(value):
                value_seen = True

            choices.append({
                'value'    : choice_value,
                'label'    : str(interface['label']),
                'selected' : choice_value == str(value),
            })

        if value not in (None, '') and not value_seen:
            choices.insert(0, {
                'value'    : str(value),
                'label'    : '{0:s} (current profile value)'.format(str(value)),
                'selected' : True,
            })

        return tuple(choices)


    def profile_has_camera_settings_driver_field(self, profile, field_name):
        if field_name == 'libcamera_image_file_type':
            return self.get_camera_settings_profile_override(profile, 'LIBCAMERA.IMAGE_FILE_TYPE')[0]
        elif field_name == 'libcamera_extra_options':
            return self.get_camera_settings_profile_override(profile, 'LIBCAMERA.EXTRA_OPTIONS')[0]

        return True


    def get_camera_settings_driver_field_value(self, profile, field_name):
        if field_name == 'profile_id':
            return profile.get('profile_id', '')
        elif field_name == 'enabled':
            return bool(profile.get('enabled', True))
        elif field_name == 'primary':
            return bool(profile.get('primary', False))

        field_config_map = {
            'camera_interface'          : 'CAMERA_INTERFACE',
            'indi_server'               : 'INDI_SERVER',
            'indi_port'                 : 'INDI_PORT',
            'indi_camera_name'          : 'INDI_CAMERA_NAME',
            'libcamera_camera_id'       : 'LIBCAMERA.CAMERA_ID',
            'libcamera_image_file_type' : 'LIBCAMERA.IMAGE_FILE_TYPE',
            'libcamera_awb_mode'        : 'LIBCAMERA.AWB_MODE',
            'libcamera_awb_red_gain'    : 'LIBCAMERA.AWB_RED_GAIN',
            'libcamera_awb_blue_gain'   : 'LIBCAMERA.AWB_BLUE_GAIN',
            'libcamera_extra_options'   : 'LIBCAMERA.EXTRA_OPTIONS',
        }
        found, value = self.get_camera_settings_profile_override(profile, field_config_map[field_name])
        if found:
            return value

        if field_name == 'libcamera_awb_mode':
            return 'auto'
        elif field_name in ('libcamera_awb_red_gain', 'libcamera_awb_blue_gain'):
            return '1.0'

        return ''


    def save_camera_settings_driver_profile(self):
        result = {
            'modern_admin_camera_settings_error'   : None,
            'modern_admin_camera_settings_success' : None,
            'modern_admin_camera_settings_errors'  : {},
        }

        if not app.config['LOGIN_DISABLED'] and not current_user.is_admin:
            result['modern_admin_camera_settings_error'] = 'Only an admin user can change camera profile settings.'
            return result

        profiles = self.get_camera_settings_profiles()
        selected_profile = self.get_selected_camera_settings_profile_for_save(profiles)
        if not selected_profile:
            result['modern_admin_camera_settings_error'] = 'Select a valid multi-camera profile before saving. No config was saved.'
            return result

        if not selected_profile.get('from_multi_camera'):
            result['modern_admin_camera_settings_error'] = 'The current global camera fallback is read-only. Select a MULTI_CAMERA profile before saving.'
            return result

        submitted_data, validation_errors = self.get_camera_settings_driver_submitted_data(selected_profile)
        if validation_errors:
            result['modern_admin_camera_settings_error'] = 'Please fix the Driver / Connection settings below. No config was saved.'
            result['modern_admin_camera_settings_errors'] = validation_errors
            result['modern_admin_camera_settings_driver_form'] = self.get_camera_settings_driver_form(selected_profile, submitted_data, validation_errors)
            return result

        try:
            new_config = json.loads(json.dumps(self.indi_allsky_config), object_pairs_hook=OrderedDict)
            updated_profile_id = self.apply_camera_settings_driver_profile_to_config(
                new_config,
                selected_profile.get('profile_id'),
                selected_profile.get('_profile_index'),
                submitted_data,
            )

            if not app.config['LOGIN_DISABLED']:
                username = current_user.username
            else:
                username = 'system'

            from ..config import IndiAllSkyConfig

            config_obj = IndiAllSkyConfig()
            config_obj.config = new_config
            config_obj.save(username, 'Modern Admin Camera Driver / Connection update for {0:s}'.format(updated_profile_id))
            self.indi_allsky_config = new_config
            app.logger.info('Saved Modern Admin Camera Driver / Connection config update for profile %s', updated_profile_id)
            result['modern_admin_camera_settings_success'] = 'Driver / Connection saved for profile {0:s}. Restart indi-allsky for the running capture service to use the new values.'.format(updated_profile_id)
        except ConfigSaveException as e:
            db.session.rollback()
            result['modern_admin_camera_settings_error'] = str(e)
        except Exception as e:
            db.session.rollback()
            app.logger.error('Error saving Modern Admin Camera Driver / Connection: %s', str(e))
            result['modern_admin_camera_settings_error'] = 'Unable to save Driver / Connection: {0:s}'.format(str(e))

        return result


    def get_camera_settings_driver_submitted_data(self, profile):
        submitted_data = {
            'profile_id' : profile.get('profile_id', ''),
            'enabled'    : 'enabled' in request.form,
            'primary'    : 'primary' in request.form,
        }
        validation_errors = dict()

        supported_interfaces = {interface['value'] for interface in get_modern_admin_supported_camera_interfaces()}
        current_interface = self.get_camera_settings_driver_field_value(profile, 'camera_interface')
        if current_interface not in (None, ''):
            supported_interfaces.add(str(current_interface))

        camera_interface = request.form.get('camera_interface', '').strip()
        if not camera_interface:
            validation_errors.setdefault('camera_interface', []).append('Camera interface is required.')
        elif camera_interface not in supported_interfaces:
            validation_errors.setdefault('camera_interface', []).append('Select a supported camera interface.')
        submitted_data['camera_interface'] = camera_interface
        driver_type = self.get_camera_settings_driver_type(camera_interface)

        if driver_type == 'indi':
            for field_name in ('indi_server', 'indi_camera_name'):
                value = request.form.get(field_name, '').strip()
                submitted_data[field_name] = value
                if not value:
                    validation_errors.setdefault(field_name, []).append('{0:s} is required for INDI profiles.'.format(self.CAMERA_SETTINGS_DRIVER_FIELD_LABELS[field_name]))

            indi_port_raw = request.form.get('indi_port', '').strip()
            if not indi_port_raw:
                submitted_data['indi_port'] = indi_port_raw
                validation_errors.setdefault('indi_port', []).append('INDI Port is required only for INDI profiles.')
            else:
                try:
                    indi_port = int(indi_port_raw)
                    if indi_port < 1 or indi_port > 65535:
                        raise ValueError()
                    submitted_data['indi_port'] = indi_port
                except ValueError:
                    submitted_data['indi_port'] = indi_port_raw
                    validation_errors.setdefault('indi_port', []).append('INDI Port must be a number from 1 to 65535.')
        elif driver_type == 'libcamera':
            libcamera_camera_id_raw = request.form.get('libcamera_camera_id', '').strip()
            if not libcamera_camera_id_raw:
                submitted_data['libcamera_camera_id'] = libcamera_camera_id_raw
                validation_errors.setdefault('libcamera_camera_id', []).append('libcamera Camera ID is required for libcamera profiles.')
            else:
                try:
                    libcamera_camera_id = int(libcamera_camera_id_raw)
                    if libcamera_camera_id < 0:
                        raise ValueError()
                    submitted_data['libcamera_camera_id'] = libcamera_camera_id
                except ValueError:
                    submitted_data['libcamera_camera_id'] = libcamera_camera_id_raw
                    validation_errors.setdefault('libcamera_camera_id', []).append('libcamera Camera ID must be a number greater than or equal to 0.')

            libcamera_awb_mode = request.form.get('libcamera_awb_mode', 'auto').strip().lower() or 'auto'
            submitted_data['libcamera_awb_mode'] = libcamera_awb_mode
            if libcamera_awb_mode not in self.CAMERA_SETTINGS_LIBCAMERA_AWB_MODES:
                validation_errors.setdefault('libcamera_awb_mode', []).append('Select a supported libcamera AWB mode.')

            for field_name in ('libcamera_awb_red_gain', 'libcamera_awb_blue_gain'):
                gain_raw = request.form.get(field_name, '').strip()
                if not gain_raw:
                    submitted_data[field_name] = gain_raw
                    if libcamera_awb_mode == 'fixed':
                        validation_errors.setdefault(field_name, []).append('{0:s} is required when libcamera AWB Mode is fixed.'.format(self.CAMERA_SETTINGS_DRIVER_FIELD_LABELS[field_name]))
                    continue

                try:
                    gain_value = float(gain_raw)
                    if gain_value <= 0:
                        raise ValueError()
                    submitted_data[field_name] = gain_value
                except ValueError:
                    submitted_data[field_name] = gain_raw
                    validation_errors.setdefault(field_name, []).append('{0:s} must be a number greater than 0.'.format(self.CAMERA_SETTINGS_DRIVER_FIELD_LABELS[field_name]))

            for field_name in self.CAMERA_SETTINGS_DRIVER_OPTIONAL_PROFILE_FIELDS:
                if not self.profile_has_camera_settings_driver_field(profile, field_name):
                    continue

                submitted_data[field_name] = request.form.get(field_name, '').strip()

        return submitted_data, validation_errors


    def apply_camera_settings_driver_profile_to_config(self, config, profile_id, profile_index, submitted_data):
        multi_camera_config = config.get('MULTI_CAMERA')
        if not isinstance(multi_camera_config, dict):
            raise ValueError('MULTI_CAMERA config is missing or invalid.')

        profiles = multi_camera_config.get('profiles')
        if not isinstance(profiles, list):
            raise ValueError('MULTI_CAMERA.profiles is missing or invalid.')

        profile_offset = int(profile_index) - 1
        if profile_offset < 0 or profile_offset >= len(profiles):
            raise ValueError('Selected profile no longer exists.')

        profile = profiles[profile_offset]
        if not isinstance(profile, dict):
            raise ValueError('Selected profile is not editable.')

        if str(profile.get('profile_id') or profile.get('id') or 'profile-{0:d}'.format(profile_index)) != str(profile_id):
            raise ValueError('Selected profile changed before save. Reload and try again.')

        if submitted_data['primary']:
            for existing_profile in profiles:
                if isinstance(existing_profile, dict):
                    existing_profile['primary'] = False

        profile['enabled'] = bool(submitted_data['enabled'])
        profile['primary'] = bool(submitted_data['primary'])
        profile['camera_interface'] = submitted_data['camera_interface']
        self.cleanup_camera_settings_driver_transient_keys(profile)
        driver_type = self.get_camera_settings_driver_type(submitted_data['camera_interface'])

        if driver_type == 'indi':
            indi_config = profile.get('indi')
            if not isinstance(indi_config, dict):
                indi_config = OrderedDict()
                profile['indi'] = indi_config

            indi_config['server'] = submitted_data['indi_server']
            indi_config['port'] = int(submitted_data['indi_port'])
            indi_config['camera_name'] = submitted_data['indi_camera_name']
        elif driver_type == 'libcamera':
            libcamera_config = profile.get('libcamera')
            if not isinstance(libcamera_config, dict):
                libcamera_config = OrderedDict()
                profile['libcamera'] = libcamera_config

            libcamera_config['camera_id'] = int(submitted_data['libcamera_camera_id'])
            libcamera_config['awb_mode'] = submitted_data['libcamera_awb_mode']
            if submitted_data.get('libcamera_awb_red_gain') not in (None, ''):
                libcamera_config['awb_red_gain'] = float(submitted_data['libcamera_awb_red_gain'])
            else:
                libcamera_config.pop('awb_red_gain', None)

            if submitted_data.get('libcamera_awb_blue_gain') not in (None, ''):
                libcamera_config['awb_blue_gain'] = float(submitted_data['libcamera_awb_blue_gain'])
            else:
                libcamera_config.pop('awb_blue_gain', None)

            if 'libcamera_image_file_type' in submitted_data:
                libcamera_config['IMAGE_FILE_TYPE'] = submitted_data['libcamera_image_file_type']
            if 'libcamera_extra_options' in submitted_data:
                libcamera_config['EXTRA_OPTIONS'] = submitted_data['libcamera_extra_options']

        return str(profile_id)


    def cleanup_camera_settings_driver_transient_keys(self, profile):
        for key in self.CAMERA_SETTINGS_DRIVER_TRANSIENT_PROFILE_KEYS:
            profile.pop(key, None)


    def get_camera_settings_lens_form(self, profile, submitted_data=None, errors=None):
        submitted_data = submitted_data or {}
        errors = errors or {}
        fields = list()
        for field_name in self.CAMERA_SETTINGS_LENS_EDIT_FIELD_ORDER:
            value = submitted_data.get(field_name, self.get_camera_settings_lens_field_value(profile, field_name))
            field_type = self.CAMERA_SETTINGS_LENS_FIELD_TYPES[field_name]
            input_type = 'number' if field_type in ('integer', 'float') else 'text'
            if field_type in ('select', 'boolean_select'):
                input_type = 'select'

            fields.append({
                'name'       : field_name,
                'label'      : self.CAMERA_SETTINGS_LENS_FIELD_LABELS[field_name],
                'config_key' : self.CAMERA_SETTINGS_LENS_FIELD_CONFIG_KEYS[field_name],
                'value'      : self.format_camera_settings_lens_form_value(value, field_type),
                'checked'    : bool(value),
                'input_type' : input_type,
                'field_type' : field_type,
                'readonly'   : not profile.get('from_multi_camera'),
                'errors'     : errors.get(field_name, []),
                'choices'    : self.get_camera_settings_lens_field_choices(field_name, value),
            })

        return {
            'enabled' : bool(profile.get('from_multi_camera')),
            'fields'  : fields,
        }


    def get_camera_settings_lens_field_value(self, profile, field_name):
        config_key = self.CAMERA_SETTINGS_LENS_FIELD_CONFIG_KEYS[field_name]
        found, value = self.get_camera_settings_profile_override(profile, config_key)
        if found:
            return value

        return ''


    def format_camera_settings_lens_form_value(self, value, field_type):
        if value in (None, ''):
            return ''
        elif field_type == 'csv_integer_list' and isinstance(value, (list, tuple)):
            return ', '.join(str(item) for item in value)

        return self.format_structured_settings_value(value)


    def get_camera_settings_lens_field_choices(self, field_name, value):
        if self.CAMERA_SETTINGS_LENS_FIELD_TYPES[field_name] == 'boolean_select':
            value_str = ''
            if value is True:
                value_str = '1'
            elif value is False:
                value_str = '0'

            return ({
                'value'    : '',
                'label'    : 'Use global',
                'selected' : value in (None, ''),
            }, {
                'value'    : '1',
                'label'    : 'Enabled',
                'selected' : value_str == '1',
            }, {
                'value'    : '0',
                'label'    : 'Disabled',
                'selected' : value_str == '0',
            })

        if field_name != 'image_rotate':
            return tuple()

        choices = list()
        for choice_value in self.CAMERA_SETTINGS_LENS_ROTATE_CHOICES:
            label = choice_value or 'No rotation'
            choices.append({
                'value'    : choice_value,
                'label'    : label,
                'selected' : str(value or '') == choice_value,
            })

        value_str = str(value or '')
        if value_str and value_str not in self.CAMERA_SETTINGS_LENS_ROTATE_CHOICES:
            choices.insert(0, {
                'value'    : value_str,
                'label'    : '{0:s} (current profile value)'.format(value_str),
                'selected' : True,
            })

        return tuple(choices)


    def save_camera_settings_lens_profile(self):
        result = {
            'modern_admin_camera_settings_error'   : None,
            'modern_admin_camera_settings_success' : None,
            'modern_admin_camera_settings_errors'  : {},
        }

        if not app.config['LOGIN_DISABLED'] and not current_user.is_admin:
            result['modern_admin_camera_settings_error'] = 'Only an admin user can change camera profile settings.'
            return result

        profiles = self.get_camera_settings_profiles()
        selected_profile = self.get_selected_camera_settings_profile_for_save(profiles)
        if not selected_profile:
            result['modern_admin_camera_settings_error'] = 'Select a valid multi-camera profile before saving. No config was saved.'
            return result

        if not selected_profile.get('from_multi_camera'):
            result['modern_admin_camera_settings_error'] = 'The current global camera fallback is read-only. Select a MULTI_CAMERA profile before saving.'
            return result

        submitted_data, validation_errors = self.get_camera_settings_lens_submitted_data()
        if validation_errors:
            result['modern_admin_camera_settings_error'] = 'Please fix the Lens & Optics settings below. No config was saved.'
            result['modern_admin_camera_settings_errors'] = validation_errors
            result['modern_admin_camera_settings_lens_form'] = self.get_camera_settings_lens_form(selected_profile, submitted_data, validation_errors)
            return result

        try:
            new_config = json.loads(json.dumps(self.indi_allsky_config), object_pairs_hook=OrderedDict)
            updated_profile_id = self.apply_camera_settings_lens_profile_to_config(
                new_config,
                selected_profile.get('profile_id'),
                selected_profile.get('_profile_index'),
                submitted_data,
            )

            if not app.config['LOGIN_DISABLED']:
                username = current_user.username
            else:
                username = 'system'

            from ..config import IndiAllSkyConfig

            config_obj = IndiAllSkyConfig()
            config_obj.config = new_config
            config_obj.save(username, 'Modern Admin Camera Lens / Optics update for {0:s}'.format(updated_profile_id))
            self.indi_allsky_config = new_config
            app.logger.info('Saved Modern Admin Camera Lens / Optics config update for profile %s', updated_profile_id)
            result['modern_admin_camera_settings_success'] = 'Lens & Optics saved for profile {0:s}. Restart or reload indi-allsky for running services to use the new values.'.format(updated_profile_id)
        except ConfigSaveException as e:
            db.session.rollback()
            result['modern_admin_camera_settings_error'] = str(e)
        except Exception as e:
            db.session.rollback()
            app.logger.error('Error saving Modern Admin Camera Lens / Optics: %s', str(e))
            result['modern_admin_camera_settings_error'] = 'Unable to save Lens & Optics: {0:s}'.format(str(e))

        return result


    def get_camera_settings_lens_submitted_data(self):
        submitted_data = dict()
        validation_errors = dict()

        for field_name in self.CAMERA_SETTINGS_LENS_EDIT_FIELD_ORDER:
            field_type = self.CAMERA_SETTINGS_LENS_FIELD_TYPES[field_name]
            raw_value = request.form.get(field_name, '').strip()
            if raw_value == '':
                submitted_data[field_name] = {
                    'delete' : True,
                    'value'  : None,
                }
                continue

            try:
                value = self.parse_camera_settings_lens_field_value(field_name, field_type, raw_value)
                submitted_data[field_name] = {
                    'delete' : False,
                    'value'  : value,
                }
            except ValueError as e:
                submitted_data[field_name] = {
                    'delete' : False,
                    'value'  : raw_value,
                }
                validation_errors.setdefault(field_name, []).append(str(e))

        return submitted_data, validation_errors


    def parse_camera_settings_lens_field_value(self, field_name, field_type, raw_value):
        if field_type == 'integer':
            try:
                value = int(raw_value)
            except ValueError:
                raise ValueError('{0:s} must be a whole number.'.format(self.CAMERA_SETTINGS_LENS_FIELD_LABELS[field_name]))
        elif field_type == 'float':
            try:
                value = float(raw_value)
            except ValueError:
                raise ValueError('{0:s} must be a number.'.format(self.CAMERA_SETTINGS_LENS_FIELD_LABELS[field_name]))
        elif field_type == 'csv_integer_list':
            value = self.parse_camera_settings_integer_list(raw_value, field_name)
        elif field_type == 'boolean_select':
            if raw_value == '1':
                value = True
            elif raw_value == '0':
                value = False
            else:
                raise ValueError('{0:s} must be Enabled, Disabled, or Use global.'.format(self.CAMERA_SETTINGS_LENS_FIELD_LABELS[field_name]))
        elif field_type == 'select':
            value = raw_value
            if field_name == 'image_rotate' and value not in self.CAMERA_SETTINGS_LENS_ROTATE_CHOICES:
                raise ValueError('Select a supported image rotation.')
        else:
            return raw_value

        if field_name in self.CAMERA_SETTINGS_LENS_NON_NEGATIVE_FIELDS and value < 0:
            raise ValueError('{0:s} must be greater than or equal to 0.'.format(self.CAMERA_SETTINGS_LENS_FIELD_LABELS[field_name]))

        return value


    def parse_camera_settings_integer_list(self, raw_value, field_name):
        try:
            values = [
                int(part.strip())
                for part in raw_value.split(',')
                if part.strip() != ''
            ]
        except ValueError:
            raise ValueError('{0:s} must be a comma-separated list of whole numbers.'.format(self.CAMERA_SETTINGS_LENS_FIELD_LABELS[field_name]))

        if len(values) not in (0, 4):
            raise ValueError('{0:s} must be empty or contain four comma-separated numbers.'.format(self.CAMERA_SETTINGS_LENS_FIELD_LABELS[field_name]))

        return values


    def apply_camera_settings_lens_profile_to_config(self, config, profile_id, profile_index, submitted_data):
        multi_camera_config = config.get('MULTI_CAMERA')
        if not isinstance(multi_camera_config, dict):
            raise ValueError('MULTI_CAMERA config is missing or invalid.')

        profiles = multi_camera_config.get('profiles')
        if not isinstance(profiles, list):
            raise ValueError('MULTI_CAMERA.profiles is missing or invalid.')

        profile_offset = int(profile_index) - 1
        if profile_offset < 0 or profile_offset >= len(profiles):
            raise ValueError('Selected profile no longer exists.')

        profile = profiles[profile_offset]
        if not isinstance(profile, dict):
            raise ValueError('Selected profile is not editable.')

        if str(profile.get('profile_id') or profile.get('id') or 'profile-{0:d}'.format(profile_index)) != str(profile_id):
            raise ValueError('Selected profile changed before save. Reload and try again.')

        for field_name, field_data in submitted_data.items():
            path = self.get_camera_settings_lens_profile_path(field_name)
            self.delete_camera_settings_lens_override_aliases(profile, field_name)
            if field_data['delete']:
                pass
            else:
                self.set_camera_settings_profile_path(profile, path, field_data['value'])

        self.cleanup_empty_camera_settings_profile_blocks(profile, ('lens', 'image', 'image_circle_mask'))
        return str(profile_id)


    def get_camera_settings_lens_profile_path(self, field_name):
        profile_paths = {
            'lens_name'                 : ('lens', 'name'),
            'lens_focal_length'         : ('lens', 'focal_length'),
            'lens_focal_ratio'          : ('lens', 'focal_ratio'),
            'lens_image_circle'         : ('lens', 'image_circle'),
            'lens_offset_x'             : ('lens', 'offset_x'),
            'lens_offset_y'             : ('lens', 'offset_y'),
            'lens_altitude'             : ('lens', 'altitude'),
            'lens_azimuth'              : ('lens', 'azimuth'),
            'image_rotate'              : ('image', 'rotate'),
            'image_rotate_angle'        : ('image', 'rotate_angle'),
            'image_flip_v'              : ('image', 'flip_v'),
            'image_flip_h'              : ('image', 'flip_h'),
            'image_circle_mask_enable'  : ('image_circle_mask', 'enable'),
            'image_circle_mask_diameter': ('image_circle_mask', 'diameter'),
            'image_circle_mask_offset_x': ('image_circle_mask', 'offset_x'),
            'image_circle_mask_offset_y': ('image_circle_mask', 'offset_y'),
            'image_circle_mask_blur'    : ('image_circle_mask', 'blur'),
            'image_circle_mask_opacity' : ('image_circle_mask', 'opacity'),
            'image_circle_mask_outline' : ('image_circle_mask', 'outline'),
            'image_crop_roi'            : ('image', 'crop_roi'),
            'image_crop_image_circle'   : ('image', 'crop_image_circle'),
            'adu_roi'                   : ('adu_roi',),
            'sqm_roi'                   : ('sqm_roi',),
        }
        return profile_paths[field_name]


    def delete_camera_settings_lens_override_aliases(self, profile, field_name):
        config_key = self.CAMERA_SETTINGS_LENS_FIELD_CONFIG_KEYS[field_name]
        candidates = [config_key, config_key.replace('.', '__')]
        candidates.extend(self.CAMERA_SETTINGS_PROFILE_ALIASES.get(config_key, tuple()))
        candidates.append(self.get_camera_settings_lens_profile_path(field_name))

        for candidate in candidates:
            if isinstance(candidate, str):
                self.delete_camera_settings_profile_path(profile, tuple(candidate.replace('__', '.').split('.')))
            else:
                self.delete_camera_settings_profile_path(profile, tuple(candidate))


    def set_camera_settings_profile_path(self, profile, path, value):
        current = profile
        for path_part in path[:-1]:
            nested_value = current.get(path_part)
            if not isinstance(nested_value, dict):
                nested_value = OrderedDict()
                current[path_part] = nested_value
            current = nested_value

        current[path[-1]] = value


    def delete_camera_settings_profile_path(self, profile, path):
        current = profile
        for path_part in path[:-1]:
            current = current.get(path_part)
            if not isinstance(current, dict):
                return

        current.pop(path[-1], None)


    def cleanup_empty_camera_settings_profile_blocks(self, profile, block_names):
        for block_name in block_names:
            if isinstance(profile.get(block_name), dict) and not profile[block_name]:
                profile.pop(block_name, None)


    def format_camera_settings_value(self, config_key, value, source):
        if source == 'missing' or value in (None, ''):
            return 'Not configured'
        elif value is True:
            return 'Enabled'
        elif value is False:
            return 'Disabled'

        if any(token in config_key.upper() for token in self.SETTINGS_SECRET_TOKENS):
            return 'Configured (masked)'

        return self.format_structured_settings_value(self.redact_camera_settings_value(value))


    def redact_camera_settings_value(self, value):
        if isinstance(value, dict):
            redacted_value = dict()
            for key, nested_value in value.items():
                if any(token in str(key).upper() for token in self.SETTINGS_SECRET_TOKENS):
                    redacted_value[key] = 'Configured (masked)'
                else:
                    redacted_value[key] = self.redact_camera_settings_value(nested_value)

            return redacted_value

        if isinstance(value, (list, tuple)):
            return [
                self.redact_camera_settings_value(nested_value)
                for nested_value in value
            ]

        return value


    def estimate_camera_settings_scope(self, config_key):
        if config_key in self.CAMERA_SETTINGS_PROFILE_FIELDS:
            return 'profile'
        elif config_key in self.CAMERA_SETTINGS_DB_FIELDS:
            return 'camera'
        elif config_key in (
            'PROCESSING_MODE',
            'CAMERA_INTERFACE',
            'INDI_SERVER',
            'INDI_PORT',
            'INDI_CAMERA_NAME',
            'LIBCAMERA.CAMERA_ID',
            'LIBCAMERA.IMAGE_FILE_TYPE',
            'LIBCAMERA.EXTRA_OPTIONS',
            'EXPOSURE_PERIOD',
            'EXPOSURE_PERIOD_DAY',
            'CCD_EXPOSURE_MIN',
            'CCD_EXPOSURE_MIN_DAY',
            'CCD_EXPOSURE_DEF',
            'CCD_EXPOSURE_MAX',
            'CCD_EXPOSURE_TIMEOUT',
            'CCD_CONFIG.NIGHT.GAIN',
            'CCD_CONFIG.NIGHT.BINNING',
            'CCD_CONFIG.MOONMODE.GAIN',
            'CCD_CONFIG.MOONMODE.BINNING',
            'CCD_CONFIG.DAY.GAIN',
            'CCD_CONFIG.DAY.BINNING',
            'DAYTIME_CAPTURE',
            'DAYTIME_CAPTURE_SAVE',
            'TARGET_ADU',
            'TARGET_ADU_DAY',
            'CCD_BIT_DEPTH',
            'CFA_PATTERN',
            'USE_NIGHT_COLOR',
            'AUTO_WB',
            'AUTO_WB_DAY',
            'NIGHT_GRAYSCALE',
            'DAYTIME_GRAYSCALE',
            'CCD_COOLING',
            'CCD_TEMP',
            'LENS_NAME',
            'LENS_FOCAL_LENGTH',
            'LENS_FOCAL_RATIO',
            'LENS_IMAGE_CIRCLE',
            'LENS_OFFSET_X',
            'LENS_OFFSET_Y',
            'LENS_ALTITUDE',
            'LENS_AZIMUTH',
            'IMAGE_ROTATE',
            'IMAGE_ROTATE_ANGLE',
            'IMAGE_FLIP_V',
            'IMAGE_FLIP_H',
            'IMAGE_SCALE',
            'IMAGE_CALIBRATE_DARK',
            'IMAGE_CALIBRATE_BPM',
            'IMAGE_CALIBRATE_FIX_HOLES',
            'IMAGE_CALIBRATE_HOLE_THOLD',
            'IMAGE_CALIBRATE_MANUAL_OFFSET',
            'IMAGE_CIRCLE_MASK.ENABLE',
            'IMAGE_CIRCLE_MASK.DIAMETER',
            'IMAGE_CIRCLE_MASK.OFFSET_X',
            'IMAGE_CIRCLE_MASK.OFFSET_Y',
            'IMAGE_CIRCLE_MASK.BLUR',
            'IMAGE_CIRCLE_MASK.OPACITY',
            'IMAGE_CIRCLE_MASK.OUTLINE',
            'IMAGE_CROP_ROI',
            'IMAGE_CROP_IMAGE_CIRCLE',
            'ADU_ROI',
            'SQM_ROI',
            'INDI_CONFIG_DEFAULTS',
            'INDI_CONFIG_DAY',
            'LIBCAMERA.AWB',
            'LIBCAMERA.AWB_DAY',
            'LIBCAMERA.AWB_ENABLE',
            'LIBCAMERA.IMMEDIATE',
            'LIBCAMERA.IMMEDIATE_DAY',
        ):
            return 'profile'

        return self.estimate_settings_scope(config_key)


    def estimate_camera_settings_restart(self, config_key):
        if config_key in self.CAMERA_SETTINGS_PROFILE_FIELDS or config_key in self.CAMERA_SETTINGS_DB_FIELDS:
            return 'no'
        elif config_key == 'PROCESSING_MODE':
            return 'restart'
        elif any(token in config_key.upper() for token in (
            'CAMERA_INTERFACE',
            'INDI_',
            'LIBCAMERA',
            'CCD_CONFIG',
            'CCD_EXPOSURE',
            'CCD_COOLING',
            'CCD_TEMP',
            'CFA_PATTERN',
        )):
            return 'restart'
        elif any(token in config_key.upper() for token in (
            'LENS',
            'IMAGE_CIRCLE',
            'IMAGE_CROP',
            'ADU_ROI',
            'SQM_ROI',
            'CALIBRATE',
            'ROTATE',
            'FLIP',
            'SCALE',
        )):
            return 'reload'

        return 'unknown'


class ModernAdminCaptureSettingsView(ModernAdminSettingsInventoryView):
    page_title = 'Modern Admin Capture Settings'
    modern_admin_active_endpoint = 'indi_allsky.modern_admin_settings_view'
    methods = ['GET', 'POST']

    CAPTURE_SETTINGS_SECTIONS = (
        {
            'title' : 'Exposure Period',
            'default_open' : True,
            'note'  : 'Cadence and exposure limits. Changes are saved to config only; capture is not restarted automatically.',
            'fields' : (
                'EXPOSURE_PERIOD',
                'EXPOSURE_PERIOD_DAY',
            ),
        },
        {
            'title' : 'Exposure Limits',
            'default_open' : True,
            'note'  : 'Minimum, default, maximum, and timeout values used by the exposure loop.',
            'fields' : (
                'CCD_EXPOSURE_MIN',
                'CCD_EXPOSURE_MIN_DAY',
                'CCD_EXPOSURE_DEF',
                'CCD_EXPOSURE_MAX',
                'CCD_EXPOSURE_TIMEOUT',
            ),
        },
        {
            'title' : 'Night Mode',
            'default_open' : False,
            'note'  : 'Night capture gain and binning.',
            'fields' : (
                'CCD_CONFIG__NIGHT__GAIN',
                'CCD_CONFIG__NIGHT__BINNING',
            ),
        },
        {
            'title' : 'Moon Mode',
            'default_open' : False,
            'note'  : 'Moon mode gain and binning.',
            'fields' : (
                'CCD_CONFIG__MOONMODE__GAIN',
                'CCD_CONFIG__MOONMODE__BINNING',
            ),
        },
        {
            'title' : 'Day Mode',
            'default_open' : False,
            'note'  : 'Daytime gain, binning, and auto-gain behavior.',
            'fields' : (
                'CCD_CONFIG__DAY__GAIN',
                'CCD_CONFIG__DAY__BINNING',
                'CCD_CONFIG__AUTO_GAIN_ENABLE',
                'CCD_CONFIG__AUTO_GAIN_LEVELS',
            ),
        },
        {
            'title' : 'ADU Control',
            'default_open' : False,
            'note'  : 'Target ADU values used by the exposure control loop.',
            'fields' : (
                'TARGET_ADU',
                'TARGET_ADU_DAY',
                'TARGET_ADU_DEV',
                'TARGET_ADU_DEV_DAY',
            ),
        },
        {
            'title' : 'Daytime Capture',
            'default_open' : False,
            'note'  : 'Daytime capture and image saving flags. Night image saving is implicit in the active capture flow and has no matching Classic field in this subset.',
            'fields' : (
                'DAYTIME_CAPTURE',
                'DAYTIME_CAPTURE_SAVE',
            ),
        },
    )
    CAPTURE_SETTINGS_FIELD_NAMES = tuple([
        field_name
        for section in CAPTURE_SETTINGS_SECTIONS
        for field_name in section['fields']
    ])

    def get_context(self):
        context = super(ModernAdminCaptureSettingsView, self).get_context()
        form = context['form_config']

        context['modern_admin_capture_settings_error'] = None
        context['modern_admin_capture_settings_success'] = None
        context['modern_admin_capture_settings_errors'] = {}

        if request.method == 'POST':
            context.update(self.save_capture_settings(form))
            form = context['modern_admin_capture_settings_form']

        context['modern_admin_capture_settings_sections'] = self.get_capture_settings_sections(form)
        context['modern_admin_capture_settings_field_names'] = self.CAPTURE_SETTINGS_FIELD_NAMES
        context['modern_admin_capture_settings_config_keys'] = [
            self.form_field_to_config_key(field_name)
            for field_name in self.CAPTURE_SETTINGS_FIELD_NAMES
        ]

        return context


    def get_capture_settings_sections(self, form):
        sections = list()
        for section in self.CAPTURE_SETTINGS_SECTIONS:
            rows = list()
            for field_name in section['fields']:
                field = getattr(form, field_name, None)
                if not field:
                    continue

                rows.append(self.get_capture_settings_field_metadata(field_name, field))

            sections.append({
                'title'        : section['title'],
                'key'          : re.sub(r'[^a-z0-9]+', '-', section['title'].lower()).strip('-'),
                'note'         : section['note'],
                'fields'       : rows,
                'default_open' : bool(section.get('default_open')),
            })

        return sections


    def get_capture_settings_field_metadata(self, field_name, field):
        field_type = field.__class__.__name__
        field_data = field.data
        input_type = 'text'
        step = None
        choices = tuple()

        if field_type == 'BooleanField':
            input_type = 'checkbox'
        elif field_type == 'IntegerField':
            input_type = 'number'
            step = '1'
        elif field_type == 'FloatField':
            input_type = 'number'
            step = '0.000001'
        elif field_type == 'SelectField':
            input_type = 'select'
            choices = tuple([
                {
                    'value'    : str(choice_value),
                    'label'    : str(choice_label),
                    'selected' : str(choice_value) == str(field_data),
                }
                for choice_value, choice_label in getattr(field, 'choices', tuple())
            ])

        return {
            'label'       : str(field.label.text),
            'name'        : field_name,
            'config_key'  : self.form_field_to_config_key(field_name),
            'value'       : field_data,
            'display'     : self.format_settings_value(field_name, field, self.estimate_settings_risk(field_name, field)),
            'input_type'  : input_type,
            'field_type'  : field_type,
            'step'        : step,
            'choices'     : choices,
            'validators'  : self.describe_field_validators(field),
            'scope'       : self.estimate_settings_scope(field_name),
        }


    def save_capture_settings(self, current_form):
        result = {
            'modern_admin_capture_settings_error'   : None,
            'modern_admin_capture_settings_success' : None,
            'modern_admin_capture_settings_errors'  : {},
            'modern_admin_capture_settings_form'    : current_form,
        }

        if not app.config['LOGIN_DISABLED'] and not current_user.is_admin:
            result['modern_admin_capture_settings_error'] = 'Only an admin user can change capture settings.'
            return result

        full_data = {
            field.name : field.data
            for field in current_form
        }

        submitted_data, parse_errors = self.get_capture_settings_submitted_data(current_form)
        full_data.update(submitted_data)

        form_config = IndiAllskyConfigForm(data=full_data)
        validation_errors = self.validate_capture_settings_form(form_config)
        validation_errors.update(parse_errors)

        result['modern_admin_capture_settings_form'] = form_config
        if validation_errors:
            result['modern_admin_capture_settings_error'] = 'Please fix the capture settings below. No config was saved.'
            result['modern_admin_capture_settings_errors'] = validation_errors
            return result

        try:
            new_config = json.loads(json.dumps(self.indi_allsky_config), object_pairs_hook=OrderedDict)
            self.apply_capture_settings_to_config(new_config, form_config)

            if not app.config['LOGIN_DISABLED']:
                username = current_user.username
            else:
                username = 'system'

            from ..config import IndiAllSkyConfig

            config_obj = IndiAllSkyConfig()
            config_obj.config = new_config
            config_obj.save(username, 'Modern Admin Capture Basics update')
            app.logger.info('Saved Modern Admin Capture Basics config update')
            result['modern_admin_capture_settings_success'] = 'Capture Basics saved. Restart or reload indi-allsky for the running capture service to use the new values.'
        except ConfigSaveException as e:
            db.session.rollback()
            result['modern_admin_capture_settings_error'] = str(e)
        except Exception as e:
            db.session.rollback()
            app.logger.error('Error saving Modern Admin Capture Basics: %s', str(e))
            result['modern_admin_capture_settings_error'] = 'Unable to save Capture Basics: {0:s}'.format(str(e))

        return result


    def get_capture_settings_submitted_data(self, form):
        submitted_data = dict()
        parse_errors = dict()

        for field_name in self.CAPTURE_SETTINGS_FIELD_NAMES:
            field = getattr(form, field_name)
            field_type = field.__class__.__name__

            if field_type == 'BooleanField':
                submitted_data[field_name] = field_name in request.form
                continue

            raw_value = request.form.get(field_name)
            if raw_value is None:
                parse_errors.setdefault(field_name, []).append('Missing value.')
                continue

            raw_value = raw_value.strip()
            try:
                if field_type == 'IntegerField':
                    submitted_data[field_name] = int(raw_value)
                elif field_type == 'FloatField':
                    submitted_data[field_name] = float(raw_value)
                else:
                    submitted_data[field_name] = raw_value
            except ValueError:
                parse_errors.setdefault(field_name, []).append('Invalid number.')

        return submitted_data, parse_errors


    def validate_capture_settings_form(self, form_config):
        validation_errors = dict()

        for field_name in self.CAPTURE_SETTINGS_FIELD_NAMES:
            field = getattr(form_config, field_name)
            field.errors = list()
            if not field.validate(form_config):
                validation_errors[field_name] = list(field.errors)

        if (
            isinstance(form_config.CCD_EXPOSURE_DEF.data, (int, float)) and
            isinstance(form_config.CCD_EXPOSURE_MAX.data, (int, float)) and
            form_config.CCD_EXPOSURE_DEF.data > form_config.CCD_EXPOSURE_MAX.data
        ):
            validation_errors.setdefault('CCD_EXPOSURE_DEF', []).append('Default exposure cannot be greater than max exposure')
            validation_errors.setdefault('CCD_EXPOSURE_MAX', []).append('Max exposure is less than default exposure')

        if (
            isinstance(form_config.CCD_EXPOSURE_MIN.data, (int, float)) and
            isinstance(form_config.CCD_EXPOSURE_MAX.data, (int, float)) and
            form_config.CCD_EXPOSURE_MIN.data > form_config.CCD_EXPOSURE_MAX.data
        ):
            validation_errors.setdefault('CCD_EXPOSURE_MIN', []).append('Minimum exposure cannot be greater than max exposure')
            validation_errors.setdefault('CCD_EXPOSURE_MAX', []).append('Max exposure is less than minimum exposure')

        return validation_errors


    def apply_capture_settings_to_config(self, config, form_config):
        config.setdefault('CCD_CONFIG', OrderedDict())
        config['CCD_CONFIG'].setdefault('NIGHT', OrderedDict())
        config['CCD_CONFIG'].setdefault('MOONMODE', OrderedDict())
        config['CCD_CONFIG'].setdefault('DAY', OrderedDict())

        config['CCD_CONFIG']['NIGHT']['GAIN'] = float(round(float(form_config.CCD_CONFIG__NIGHT__GAIN.data), 2))
        config['CCD_CONFIG']['NIGHT']['BINNING'] = int(form_config.CCD_CONFIG__NIGHT__BINNING.data)
        config['CCD_CONFIG']['MOONMODE']['GAIN'] = float(round(float(form_config.CCD_CONFIG__MOONMODE__GAIN.data), 2))
        config['CCD_CONFIG']['MOONMODE']['BINNING'] = int(form_config.CCD_CONFIG__MOONMODE__BINNING.data)
        config['CCD_CONFIG']['DAY']['GAIN'] = float(round(float(form_config.CCD_CONFIG__DAY__GAIN.data), 2))
        config['CCD_CONFIG']['DAY']['BINNING'] = int(form_config.CCD_CONFIG__DAY__BINNING.data)
        config['CCD_CONFIG']['AUTO_GAIN_ENABLE'] = bool(form_config.CCD_CONFIG__AUTO_GAIN_ENABLE.data)
        config['CCD_CONFIG']['AUTO_GAIN_LEVELS'] = int(form_config.CCD_CONFIG__AUTO_GAIN_LEVELS.data)

        config['CCD_EXPOSURE_MAX'] = float(round(float(form_config.CCD_EXPOSURE_MAX.data), 6))
        config['CCD_EXPOSURE_DEF'] = float(round(float(form_config.CCD_EXPOSURE_DEF.data), 6))
        config['CCD_EXPOSURE_MIN'] = float(round(float(form_config.CCD_EXPOSURE_MIN.data), 6))
        config['CCD_EXPOSURE_MIN_DAY'] = float(round(float(form_config.CCD_EXPOSURE_MIN_DAY.data), 6))
        config['CCD_EXPOSURE_TIMEOUT'] = int(form_config.CCD_EXPOSURE_TIMEOUT.data)
        config['EXPOSURE_PERIOD'] = float(form_config.EXPOSURE_PERIOD.data)
        config['EXPOSURE_PERIOD_DAY'] = float(form_config.EXPOSURE_PERIOD_DAY.data)

        config['DAYTIME_CAPTURE'] = bool(form_config.DAYTIME_CAPTURE.data)
        config['DAYTIME_CAPTURE_SAVE'] = bool(form_config.DAYTIME_CAPTURE_SAVE.data)

        config['TARGET_ADU'] = int(form_config.TARGET_ADU.data)
        config['TARGET_ADU_DAY'] = int(form_config.TARGET_ADU_DAY.data)
        config['TARGET_ADU_DEV'] = int(form_config.TARGET_ADU_DEV.data)
        config['TARGET_ADU_DEV_DAY'] = int(form_config.TARGET_ADU_DEV_DAY.data)


class ModernAdminNetworkView(ModernAdminSafeControlsMixin, NetworkManagerView):
    page_title = 'Modern Admin Network'
    modern_admin_active_endpoint = 'indi_allsky.modern_admin_system_view'

    def get_context(self):
        context = super(ModernAdminNetworkView, self).get_context()
        form = context['form_connections']

        context['modern_admin_safe_title'] = 'Network'
        context['modern_admin_safe_note'] = 'Network Manager status and available selectors are real. Connection changes remain disabled in Modern Admin.'
        context['modern_admin_safe_sections'] = (
            {
                'title' : 'Host',
                'rows'  : (
                    {'label' : 'Hostname', 'value' : context.get('hostname')},
                    {'label' : 'Network Manager', 'value' : 'Available' if context.get('nm_installed') else 'Unavailable'},
                ),
            },
            {
                'title' : 'Connections',
                'rows'  : self.field_rows(form, ('CONNECTIONS_SELECT', 'WIFI_DEVICES_SELECT', 'SSID_SELECT', 'HOTSPOT_DEVICES_SELECT', 'HOTSPOT_SSID')),
            },
        )
        context['modern_admin_safe_actions'] = (
            self.disabled_action('Activate connection', 'May interrupt remote access; disabled in Modern Admin.'),
            self.disabled_action('Deactivate connection', 'May disconnect the web session; disabled in Modern Admin.'),
            self.disabled_action('Delete connection', 'Destructive network action; disabled in Modern Admin.'),
            self.disabled_action('Create hotspot', 'Changes network state; disabled in Modern Admin.'),
        )
        return context


class ModernAdminDriveManagerView(ModernAdminSafeControlsMixin, DriveManagerView):
    page_title = 'Modern Admin Drives'
    modern_admin_active_endpoint = 'indi_allsky.modern_admin_storage_view'

    def get_context(self):
        context = super(ModernAdminDriveManagerView, self).get_context()
        form = context['form_drives']

        context['modern_admin_safe_title'] = 'Drives'
        context['modern_admin_safe_note'] = 'Drive and mount selectors come from the existing drive manager. Mount, unmount, and power-off remain disabled in Modern Admin.'
        context['modern_admin_safe_sections'] = (
            {
                'title' : 'Drive manager',
                'rows'  : (
                    {'label' : 'UDisks2', 'value' : 'Available' if context.get('udisks2_installed') else 'Unavailable'},
                ),
            },
            {
                'title' : 'Available devices',
                'rows'  : self.field_rows(form, ('DRIVES_SELECT', 'DEVICES_SELECT')),
            },
        )
        context['modern_admin_safe_actions'] = (
            self.disabled_action('Power off drive', 'Can disconnect storage; disabled in Modern Admin.'),
            self.disabled_action('Mount device', 'Changes system mount state; disabled in Modern Admin.'),
            self.disabled_action('Unmount device', 'Can interrupt media storage; disabled in Modern Admin.'),
        )
        return context


class ModernAdminManualGpioView(ModernAdminSafeControlsMixin, ManualGpioView):
    page_title = 'Modern Admin GPIO Control'
    modern_admin_active_endpoint = 'indi_allsky.modern_admin_system_view'

    def get_context(self):
        context = super(ModernAdminManualGpioView, self).get_context()

        pin_rows = list()
        for index, pin_name in enumerate(context.get('pin_names', tuple())):
            pin_state = context.get('pin_states', [-1, -1, -1])[index]
            if pin_state == -1:
                state_label = 'Unavailable'
            elif pin_state:
                state_label = 'On'
            else:
                state_label = 'Off'

            pin_rows.append({'label' : 'Pin {0:s}'.format(pin_name), 'value' : state_label})

        context['modern_admin_safe_title'] = 'GPIO Control'
        context['modern_admin_safe_note'] = 'GPIO class and pin states are read from the existing manual GPIO view. Toggling pins remains disabled in Modern Admin.'
        context['modern_admin_safe_sections'] = (
            {
                'title' : 'GPIO interface',
                'rows'  : (
                    {'label' : 'GPIO class', 'value' : context.get('gpio_class') or 'Not configured'},
                ),
            },
            {
                'title' : 'Pins',
                'rows'  : pin_rows,
            },
        )
        context['modern_admin_safe_actions'] = (
            self.disabled_action('Toggle pin 1', 'Manual GPIO control can affect hardware and remains disabled in Modern Admin.'),
            self.disabled_action('Toggle pin 2', 'Manual GPIO control can affect hardware and remains disabled in Modern Admin.'),
            self.disabled_action('Toggle pin 3', 'Manual GPIO control can affect hardware and remains disabled in Modern Admin.'),
        )
        return context


class AstroPanelView(TemplateView):
    page_title = 'astropanel'

    def get_context(self):
        context = super(AstroPanelView, self).get_context()
        return context


class AjaxAstroPanelView(BaseView):
    """
    Copyright(c) 2019 Radek Kaczorek  <rkaczorek AT gmail DOT com>

    Ported from https://github.com/rkaczorek/astropanel.git
    """

    methods = ['GET', 'POST']


    def dispatch_request(self):
        camera_id = int(request.args['camera_id'])

        if request.method == 'GET':
            return self.get(camera_id)
        else:
            return jsonify({}), 400


    def get(self, camera_id):
        camera = IndiAllSkyDbCameraTable.query\
            .filter(IndiAllSkyDbCameraTable.id == camera_id)\
            .one()


        satellites_visual = IndiAllSkyDbTleDataTable.query\
            .filter(IndiAllSkyDbTleDataTable.group == constants.SATELLITE_VISUAL)\
            .order_by(IndiAllSkyDbTleDataTable.title)\


        # init observer
        obs = ephem.Observer()

        # set geo position
        obs.lat = math.radians(camera.latitude)
        obs.lon = math.radians(camera.longitude)
        obs.elevation = camera.elevation

        # disable atmospheric refraction calcs
        obs.pressure = 0

        # update time
        utcnow = datetime.now(tz=timezone.utc)

        obs.date = utcnow

        sun = ephem.Sun()
        mercury = ephem.Mercury()
        venus = ephem.Venus()
        moon = ephem.Moon()
        mars = ephem.Mars()
        jupiter = ephem.Jupiter()
        saturn = ephem.Saturn()
        uranus = ephem.Uranus()
        neptune = ephem.Neptune()

        polaris_data = self.astropanel_get_polaris_data(obs)

        sun_position = self.astropanel_get_body_positions(obs, sun)
        sun_twilights = self.astropanel_get_sun_twilights(obs, sun)
        mercury_position = self.astropanel_get_body_positions(obs, mercury)
        venus_position = self.astropanel_get_body_positions(obs, venus)
        moon_position = self.astropanel_get_body_positions(obs, moon)
        mars_position = self.astropanel_get_body_positions(obs, mars)
        jupiter_position = self.astropanel_get_body_positions(obs, jupiter)
        saturn_position = self.astropanel_get_body_positions(obs, saturn)
        uranus_position = self.astropanel_get_body_positions(obs, uranus)
        neptune_position = self.astropanel_get_body_positions(obs, neptune)


        obs.date = utcnow
        sun.compute(obs)
        mercury.compute(obs)
        venus.compute(obs)
        moon.compute(obs)
        mars.compute(obs)
        jupiter.compute(obs)
        saturn.compute(obs)
        uranus.compute(obs)
        neptune.compute(obs)


        satellite_list = list()
        for sat_entry in satellites_visual:
            try:
                sat = ephem.readtle(sat_entry.title, sat_entry.line1, sat_entry.line2)
            except ValueError as e:
                app.logger.error('Satellite TLE data error: %s', str(e))
                continue

            sat.compute(obs)

            try:
                # all next_pass() values can be None
                next_pass = obs.next_pass(sat)
            except ValueError as e:
                app.logger.error('Next pass error: %s', str(e))
                continue


            sat_data = {
                'name'      : str(sat_entry.title).upper(),
                'az'        : round(math.degrees(sat.az), 2),
                'alt'       : round(math.degrees(sat.alt), 2),
                'elevation' : int(sat.elevation / 1000),
                'eclipsed'  : sat.eclipsed,
            }


            if not isinstance(next_pass[0], type(None)) and not isinstance(next_pass[4], type(None)):
                sat_data['rise'] = '{0:%Y-%m-%d %H:%M:%S}'.format(ephem.localtime(next_pass[0])),
                sat_data['duration'] = '{0:d}'.format((ephem.localtime(next_pass[4]) - ephem.localtime(next_pass[0])).seconds),
            else:
                sat_data['rise'] = 'None'
                sat_data['duration'] = 'None'


            if not isinstance(next_pass[2], type(None)):
                sat_data['transit'] = '{0:%Y-%m-%d %H:%M:%S}'.format(ephem.localtime(next_pass[2])),
            else:
                sat_data['transit'] = 'None'

            if not isinstance(next_pass[4], type(None)):
                sat_data['set'] = '{0:%Y-%m-%d %H:%M:%S}'.format(ephem.localtime(next_pass[4])),
            else:
                sat_data['set'] = 'None'


            satellite_list.append(sat_data)


        # sort by altitude
        satellite_list = sorted(satellite_list, key=lambda x: x['alt'], reverse=True)


        data = {
            'latitude'              : round(obs.lat, 2),
            'longitude'             : round(obs.lon, 2),
            'elevation'             : int(obs.elevation),
            'polaris_hour_angle'    : round(polaris_data[0], 5),
            'polaris_next_transit'  : '{0:s}'.format(polaris_data[1]),
            'polaris_alt'           : round(math.degrees(polaris_data[2]), 2),
            'moon_phase'            : self.astropanel_get_moon_phase(obs),
            'moon_light'            : int(moon.phase),
            'moon_rise'             : '{0:s}'.format(moon_position[0]),
            'moon_transit'          : '{0:s}'.format(moon_position[1]),
            'moon_set'              : '{0:s}'.format(moon_position[2]),
            'moon_az'               : round(math.degrees(moon.az), 2),
            'moon_alt'              : round(math.degrees(moon.alt), 2),
            'moon_ra'               : '{0:s}'.format(str(moon.ra)),
            'moon_dec'              : '{0:s}'.format(str(moon.dec)),
            'moon_new'              : '{0:%Y-%m-%d %H:%M:%S}'.format(ephem.localtime(ephem.next_new_moon(utcnow))),
            'moon_full'             : '{0:%Y-%m-%d %H:%M:%S}'.format(ephem.localtime(ephem.next_full_moon(utcnow))),
            'sun_at_start'          : sun_twilights[2][0],
            'sun_ct_start'          : sun_twilights[0][0],
            'sun_rise'              : '{0:s}'.format(sun_position[0]),
            'sun_transit'           : '{0:s}'.format(sun_position[1]),
            'sun_set'               : '{0:s}'.format(sun_position[2]),
            'sun_ct_end'            : sun_twilights[0][1],
            'sun_at_end'            : sun_twilights[2][1],
            'sun_az'                : round(math.degrees(sun.az), 2),
            'sun_alt'               : round(math.degrees(sun.alt), 2),
            'sun_ra'                : '{0:s}'.format(str(sun.ra)),
            'sun_dec'               : '{0:s}'.format(str(sun.dec)),
            'sun_equinox'           : '{0:%Y-%m-%d %H:%M:%S}'.format(ephem.localtime(ephem.next_equinox(utcnow))),
            'sun_solstice'          : '{0:%Y-%m-%d %H:%M:%S}'.format(ephem.localtime(ephem.next_solstice(utcnow))),
            'mercury_rise'          : '{0:s}'.format(mercury_position[0]),
            'mercury_transit'       : '{0:s}'.format(mercury_position[1]),
            'mercury_set'           : '{0:s}'.format(mercury_position[2]),
            'mercury_az'            : round(math.degrees(mercury.az), 2),
            'mercury_alt'           : round(math.degrees(mercury.alt), 2),
            'venus_rise'            : '{0:s}'.format(venus_position[0]),
            'venus_transit'         : '{0:s}'.format(venus_position[1]),
            'venus_set'             : '{0:s}'.format(venus_position[2]),
            'venus_az'              : round(math.degrees(venus.az), 2),
            'venus_alt'             : round(math.degrees(venus.alt), 2),
            'mars_rise'             : '{0:s}'.format(mars_position[0]),
            'mars_transit'          : '{0:s}'.format(mars_position[1]),
            'mars_set'              : '{0:s}'.format(mars_position[2]),
            'mars_az'               : round(math.degrees(mars.az), 2),
            'mars_alt'              : round(math.degrees(mars.alt), 2),
            'jupiter_rise'          : '{0:s}'.format(jupiter_position[0]),
            'jupiter_transit'       : '{0:s}'.format(jupiter_position[1]),
            'jupiter_set'           : '{0:s}'.format(jupiter_position[2]),
            'jupiter_az'            : round(math.degrees(jupiter.az), 2),
            'jupiter_alt'           : round(math.degrees(jupiter.alt), 2),
            'saturn_rise'           : '{0:s}'.format(saturn_position[0]),
            'saturn_transit'        : '{0:s}'.format(saturn_position[1]),
            'saturn_set'            : '{0:s}'.format(saturn_position[2]),
            'saturn_az'             : round(math.degrees(saturn.az), 2),
            'saturn_alt'            : round(math.degrees(saturn.alt), 2),
            'uranus_rise'           : '{0:s}'.format(uranus_position[0]),
            'uranus_transit'        : '{0:s}'.format(uranus_position[1]),
            'uranus_set'            : '{0:s}'.format(uranus_position[2]),
            'uranus_az'             : round(math.degrees(uranus.az), 2),
            'uranus_alt'            : round(math.degrees(uranus.alt), 2),
            'neptune_rise'          : '{0:s}'.format(neptune_position[0]),
            'neptune_transit'       : '{0:s}'.format(neptune_position[1]),
            'neptune_set'           : '{0:s}'.format(neptune_position[2]),
            'neptune_az'            : round(math.degrees(neptune.az), 2),
            'neptune_alt'           : round(math.degrees(neptune.alt), 2),
            'satellite_list'        : satellite_list,
        }

        return jsonify(data)


    def astropanel_get_moon_phase(self, obs):
        target_date_utc = obs.date
        target_date_local = ephem.localtime(target_date_utc).date()
        next_full = ephem.localtime(ephem.next_full_moon(target_date_utc)).date()
        next_new = ephem.localtime(ephem.next_new_moon(target_date_utc)).date()
        next_last_quarter = ephem.localtime(ephem.next_last_quarter_moon(target_date_utc)).date()
        next_first_quarter = ephem.localtime(ephem.next_first_quarter_moon(target_date_utc)).date()
        previous_full = ephem.localtime(ephem.previous_full_moon(target_date_utc)).date()
        previous_new = ephem.localtime(ephem.previous_new_moon(target_date_utc)).date()
        previous_last_quarter = ephem.localtime(ephem.previous_last_quarter_moon(target_date_utc)).date()
        previous_first_quarter = ephem.localtime(ephem.previous_first_quarter_moon(target_date_utc)).date()

        if target_date_local in (next_full, previous_full):
            return 'Full'
        elif target_date_local in (next_new, previous_new):
            return 'New'
        elif target_date_local in (next_first_quarter, previous_first_quarter):
            return 'First Quarter'
        elif target_date_local in (next_last_quarter, previous_last_quarter):
            return 'Last Quarter'
        elif previous_new < next_first_quarter < next_full < next_last_quarter < next_new:
            return 'Waxing Crescent'
        elif previous_first_quarter < next_full < next_last_quarter < next_new < next_first_quarter:
            return 'Waxing Gibbous'
        elif previous_full < next_last_quarter < next_new < next_first_quarter < next_full:
            return 'Waning Gibbous'
        elif previous_last_quarter < next_new < next_first_quarter < next_full < next_last_quarter:
            return 'Waning Crescent'


    def astropanel_get_body_positions(self, obs, body):
        utcnow = datetime.now(tz=timezone.utc)

        obs.date = utcnow
        body.compute(obs)


        positions = []

        # test for always below horizon or always above horizon
        try:
            if ephem.localtime(obs.previous_rising(body)).date() == ephem.localtime(obs.date).date() and obs.previous_rising(body) < obs.previous_transit(body) < obs.previous_setting(body) < obs.date:
                positions.append(obs.previous_rising(body))
                positions.append(obs.previous_transit(body))
                positions.append(obs.previous_setting(body))
            elif ephem.localtime(obs.previous_rising(body)).date() == ephem.localtime(obs.date).date() and obs.previous_rising(body) < obs.previous_transit(body) < obs.date < obs.next_setting(body):
                positions.append(obs.previous_rising(body))
                positions.append(obs.previous_transit(body))
                positions.append(obs.next_setting(body))
            elif ephem.localtime(obs.previous_rising(body)).date() == ephem.localtime(obs.date).date() and obs.previous_rising(body) < obs.date < obs.next_transit(body) < obs.next_setting(body):
                positions.append(obs.previous_rising(body))
                positions.append(obs.next_transit(body))
                positions.append(obs.next_setting(body))
            elif ephem.localtime(obs.previous_rising(body)).date() == ephem.localtime(obs.date).date() and obs.date < obs.next_rising(body) < obs.next_transit(body) < obs.next_setting(body):
                positions.append(obs.next_rising(body))
                positions.append(obs.next_transit(body))
                positions.append(obs.next_setting(body))
            else:
                positions.append(obs.next_rising(body))
                positions.append(obs.next_transit(body))
                positions.append(obs.next_setting(body))
        except (ephem.NeverUpError, ephem.AlwaysUpError):
            try:
                if ephem.localtime(obs.previous_transit(body)).date() == ephem.localtime(obs.date).date() and obs.previous_transit(body) < obs.date:
                    positions.append('-')
                    positions.append(obs.previous_transit(body))
                    positions.append('-')
                elif ephem.localtime(obs.previous_transit(body)).date() == ephem.localtime(obs.date).date() and obs.next_transit(body) > obs.date:
                    positions.append('-')
                    positions.append(obs.next_transit(body))
                    positions.append('-')
                else:
                    positions.append('-')
                    positions.append('-')
                    positions.append('-')
            except (ephem.NeverUpError, ephem.AlwaysUpError):
                positions.append('-')
                positions.append('-')
                positions.append('-')

        if positions[0] != '-':
            positions[0] = ephem.localtime(positions[0]).strftime("%H:%M:%S")
        if positions[1] != '-':
            positions[1] = ephem.localtime(positions[1]).strftime("%H:%M:%S")
        if positions[2] != '-':
            positions[2] = ephem.localtime(positions[2]).strftime("%H:%M:%S")

        return positions


    def astropanel_get_sun_twilights(self, obs, sun):
        results = []

        """
        An observer at the North Pole would see the Sun circle the sky at 23.5° above the horizon all day.
        An observer at 90° – 23.5° = 66.5° would see the Sun spend the whole day on the horizon, making a circle along its circumference.
        An observer would have to be at 90° – 23.5° – 18° = 48.5° latitude or even further south in order for the Sun to dip low enough for them to observe the level of darkness defined as astronomical twilight.

        civil twilight = -6
        nautical twilight = -12
        astronomical twilight = -18

        get_sun_twilights(home)[0][0]    -	civil twilight end
        get_sun_twilights(home)[0][1]    -	civil twilight start

        get_sun_twilights(home)[1][0]    -	nautical twilight end
        get_sun_twilights(home)[1][1]    -	nautical twilight start

        get_sun_twilights(home)[2][0]    -	astronomical twilight end
        get_sun_twilights(home)[2][1]    -	astronomical twilight start
        """

        # remember entry observer horizon
        obs_horizon = obs.horizon

        # Twilights, their horizons and whether to use the centre of the Sun or not
        twilights = [('-6', True), ('-12', True), ('-18', True)]

        for twi in twilights:
            obs.horizon = twi[0]
            try:
                rising_setting = self.astropanel_get_body_positions(obs, sun)
                results.append((rising_setting[0], rising_setting[2]))
            except ephem.AlwaysUpError:
                results.append(('n/a', 'n/a'))

        # reset observer horizon to entry
        obs.horizon = obs_horizon

        return results


    def astropanel_get_polaris_data(self, obs):
        polaris_data = []

        """
        lst = 100.46 + 0.985647 * d + lon + 15 * ut [based on http://www.stargazing.net/kepler/altaz.html]
        d - the days from J2000 (1200 hrs UT on Jan 1st 2000 AD), including the fraction of a day
        lon - your longitude in decimal degrees, East positive
        ut - the universal time in decimal hours
        """

        j2000 = ephem.Date('2000/01/01 12:00:00')
        d = obs.date - j2000

        lon = math.degrees(obs.lon)

        ut_hms = obs.date.datetime().strftime("%H:%M:%S").split(':')
        ut = float(ut_hms[0]) + (float(ut_hms[1]) / 60) + (float(ut_hms[2]) / 3600)


        lst = 100.46 + 0.985647 * d + lon + 15 * ut
        lst = lst - int(lst / 360) * 360

        polaris = ephem.readdb("Polaris,f|M|F7,2:31:48.704,89:15:50.72,2.02,2000")
        polaris.compute()
        polaris_ra_deg = math.degrees(polaris.ra)

        # Polaris Hour Angle = LST - RA Polaris [expressed in degrees or 15*(h+m/60+s/3600)]
        pha = lst - polaris_ra_deg

        # normalize
        if pha < 0:
            pha += 360
        elif pha > 360:
            pha -= 360

        # append polaris hour angle
        polaris_data.append(pha)

        # append polaris next transit
        try:
            polaris_data.append(ephem.localtime(obs.next_transit(polaris)).strftime("%H:%M:%S"))
        except (ephem.NeverUpError, ephem.AlwaysUpError):
            polaris_data.append('-')

        # append polaris alt
        polaris_data.append(polaris.alt)

        return polaris_data



# images are normally served directly by the web server, this is a backup method
@bp_allsky.route('/images/<path:path>')  # noqa: E302
def images_folder(path):
    app.logger.warning('Serving image file: %s', path)
    return send_from_directory(app.config['INDI_ALLSKY_IMAGE_FOLDER'], path)


bp_allsky.add_url_rule('/ajax/status_update', view_func=AjaxStatusUpdateView.as_view('ajax_status_update_view'))

bp_allsky.add_url_rule('/js/sensor_panel', view_func=JsonSensorPanelView.as_view('js_sensor_panel_view'))
bp_allsky.add_url_rule('/sensor_panel', view_func=SensorPanelView.as_view('sensor_panel_view', template_name='sensor_panel.html'))

bp_allsky.add_url_rule('/', view_func=IndexImgView.as_view('index_view', template_name='index_img.html'))
bp_allsky.add_url_rule('/index_canvas', view_func=IndexCanvasView.as_view('index_canvas_view', template_name='index_canvas.html'))
bp_allsky.add_url_rule('/index_img', view_func=IndexImgView.as_view('index_img_view', template_name='index_img.html'))
bp_allsky.add_url_rule('/js/latest', view_func=JsonLatestImageView.as_view('js_latest_image_view'))
bp_allsky.add_url_rule('/panorama', view_func=LatestPanoramaImgView.as_view('latest_panorama_view', template_name='index_img.html'))
bp_allsky.add_url_rule('/panorama_canvas', view_func=LatestPanoramaCanvasView.as_view('latest_panorama_canvas_view', template_name='index_canvas.html'))
bp_allsky.add_url_rule('/panorama_img', view_func=LatestPanoramaImgView.as_view('latest_panorama_img_view', template_name='index_img.html'))
bp_allsky.add_url_rule('/js/latest_panorama', view_func=JsonLatestPanoramaView.as_view('js_latest_panorama_view'))
bp_allsky.add_url_rule('/raw', view_func=LatestRawImageImgView.as_view('latest_rawimage_view', template_name='index_img.html'))
bp_allsky.add_url_rule('/raw_canvas', view_func=LatestRawImageCanvasView.as_view('latest_rawimage_canvas_view', template_name='index_canvas.html'))
bp_allsky.add_url_rule('/raw_img', view_func=LatestRawImageImgView.as_view('latest_rawimage_img_view', template_name='index_img.html'))
bp_allsky.add_url_rule('/js/latest_rawimage', view_func=JsonLatestRawImageView.as_view('js_latest_rawimage_view'))
bp_allsky.add_url_rule('/realtime_keogram', view_func=RealtimeKeogramView.as_view('realtime_keogram_view', template_name='realtime_keogram.html'))

bp_allsky.add_url_rule('/loop', view_func=ImageLoopImgView.as_view('image_loop_view', template_name='loop_img.html'))
bp_allsky.add_url_rule('/loop_canvas', view_func=ImageLoopCanvasView.as_view('image_loop_canvas_view', template_name='loop_canvas.html'))
bp_allsky.add_url_rule('/loop_img', view_func=ImageLoopImgView.as_view('image_loop_img_view', template_name='loop_img.html'))
bp_allsky.add_url_rule('/js/loop', view_func=JsonImageLoopView.as_view('js_image_loop_view'))
bp_allsky.add_url_rule('/looppanorama', view_func=PanoramaLoopImgView.as_view('panorama_loop_view', template_name='loop_img.html'))
bp_allsky.add_url_rule('/looppanorama_canvas', view_func=PanoramaLoopCanvasView.as_view('panorama_loop_canvas_view', template_name='loop_canvas.html'))
bp_allsky.add_url_rule('/looppanorama_img', view_func=PanoramaLoopImgView.as_view('panorama_loop_img_view', template_name='loop_img.html'))
bp_allsky.add_url_rule('/js/looppanorama', view_func=JsonPanoramaLoopView.as_view('js_panorama_loop_view'))
bp_allsky.add_url_rule('/loopraw', view_func=RawImageLoopImgView.as_view('rawimage_loop_view', template_name='loop_img.html'))
bp_allsky.add_url_rule('/loopraw_canvas', view_func=RawImageLoopCanvasView.as_view('rawimage_loop_canvas_view', template_name='loop_canvas.html'))
bp_allsky.add_url_rule('/loopraw_img', view_func=RawImageLoopImgView.as_view('rawimage_loop_img_view', template_name='loop_img.html'))
bp_allsky.add_url_rule('/js/loopraw', view_func=JsonRawImageLoopView.as_view('js_rawimage_loop_view'))

bp_allsky.add_url_rule('/sqm', view_func=SqmView.as_view('sqm_view', template_name='sqm.html'))

bp_allsky.add_url_rule('/charts', view_func=ChartView.as_view('chart_view', template_name='chart.html'))
bp_allsky.add_url_rule('/js/charts', view_func=JsonChartView.as_view('js_chart_view'))

bp_allsky.add_url_rule('/imageviewer', view_func=ImageViewerView.as_view('imageviewer_view', template_name='imageviewer.html'))
bp_allsky.add_url_rule('/ajax/imageviewer', view_func=AjaxImageViewerView.as_view('ajax_imageviewer_view'))
bp_allsky.add_url_rule('/ajax/exclude', view_func=AjaxImageExcludeView.as_view('ajax_image_exclude_view'))

bp_allsky.add_url_rule('/fitsimageviewer', view_func=FitsImageViewerView.as_view('fitsimageviewer_view', template_name='fitsimageviewer.html'))
bp_allsky.add_url_rule('/ajax/fitsimageviewer', view_func=AjaxFitsImageViewerView.as_view('ajax_fitsimageviewer_view'))
bp_allsky.add_url_rule('/fits2jpeg', view_func=Fits2JpegView.as_view('fits2jpeg_view'))

bp_allsky.add_url_rule('/gallery', view_func=GalleryViewerView.as_view('gallery_view', template_name='gallery.html'))
bp_allsky.add_url_rule('/ajax/gallery', view_func=AjaxGalleryViewerView.as_view('ajax_gallery_view'))

bp_allsky.add_url_rule('/videoviewer', view_func=VideoViewerView.as_view('videoviewer_view', template_name='videoviewer.html'))
bp_allsky.add_url_rule('/ajax/videoviewer', view_func=AjaxVideoViewerView.as_view('ajax_videoviewer_view'))

bp_allsky.add_url_rule('/minivideoviewer', view_func=MiniVideoViewerView.as_view('mini_videoviewer_view', template_name='minivideoviewer.html'))
bp_allsky.add_url_rule('/ajax/minivideoviewer', view_func=AjaxMiniVideoViewerView.as_view('ajax_mini_videoviewer_view'))

bp_allsky.add_url_rule('/modern-admin/media/gallery', view_func=ModernAdminMediaGalleryView.as_view('modern_admin_media_gallery_view', template_name='modern_admin/media_list.html'))
bp_allsky.add_url_rule('/modern-admin/media/gallery/page', view_func=ModernAdminMediaGalleryPageView.as_view('modern_admin_media_gallery_page_view', template_name='modern_admin/media_list.html'))
bp_allsky.add_url_rule('/modern-admin/media/images', view_func=ModernAdminMediaImagesView.as_view('modern_admin_media_images_view', template_name='modern_admin/media_list.html'))
bp_allsky.add_url_rule('/modern-admin/media/timelapses', view_func=ModernAdminMediaTimelapsesView.as_view('modern_admin_media_timelapses_view', template_name='modern_admin/media_list.html'))
bp_allsky.add_url_rule('/modern-admin/media/mini-timelapses', view_func=ModernAdminMediaMiniTimelapsesView.as_view('modern_admin_media_mini_timelapses_view', template_name='modern_admin/media_list.html'))
bp_allsky.add_url_rule('/modern-admin/media/panorama', view_func=ModernAdminMediaPanoramaView.as_view('modern_admin_media_panorama_view', template_name='modern_admin/media_list.html'))
bp_allsky.add_url_rule('/modern-admin/media/panorama-loop', view_func=ModernAdminMediaPanoramaLoopView.as_view('modern_admin_media_panorama_loop_view', template_name='modern_admin/media_list.html'))
bp_allsky.add_url_rule('/modern-admin/media/fits', view_func=ModernAdminMediaFitsView.as_view('modern_admin_media_fits_view', template_name='modern_admin/media_list.html'))

bp_allsky.add_url_rule('/view_image', view_func=TimelapseImageView.as_view('timelapse_image_view', template_name='view_image.html'))
bp_allsky.add_url_rule('/view_panorama', view_func=PanoramaImageView.as_view('panorama_image_view', template_name='view_image.html'))
bp_allsky.add_url_rule('/view_startrail', view_func=StartrailImageView.as_view('startrail_image_view', template_name='view_image.html'))
bp_allsky.add_url_rule('/view_keogram', view_func=KeogramImageView.as_view('keogram_image_view', template_name='view_image.html'))
bp_allsky.add_url_rule('/view_raw', view_func=RawImageView.as_view('raw_image_view', template_name='view_image.html'))

bp_allsky.add_url_rule('/watch_timelapse', view_func=TimelapseVideoView.as_view('timelapse_video_view', template_name='watch_video.html'))
bp_allsky.add_url_rule('/watch_mini_timelapse', view_func=MiniTimelapseVideoView.as_view('mini_timelapse_video_view', template_name='watch_video.html'))
bp_allsky.add_url_rule('/watch_startrail', view_func=StartrailVideoView.as_view('startrail_video_view', template_name='watch_video.html'))
bp_allsky.add_url_rule('/watch_panorama', view_func=PanoramaVideoView.as_view('panorama_video_view', template_name='watch_video.html'))

bp_allsky.add_url_rule('/generate', view_func=TimelapseGeneratorView.as_view('generate_view', template_name='generate.html'))
bp_allsky.add_url_rule('/ajax/generate', view_func=AjaxTimelapseGeneratorView.as_view('ajax_generate_view'))

bp_allsky.add_url_rule('/minigenerate', view_func=MiniTimelapseGeneratorView.as_view('mini_generate_view', template_name='mini_generate.html'))
bp_allsky.add_url_rule('/ajax/minigenerate', view_func=AjaxMiniTimelapseGeneratorView.as_view('ajax_mini_generate_view'))

bp_allsky.add_url_rule('/config', view_func=ConfigView.as_view('config_view', template_name='config.html'))
bp_allsky.add_url_rule('/ajax/config', view_func=AjaxConfigView.as_view('ajax_config_view'))
bp_allsky.add_url_rule('/config/list', view_func=ConfigListView.as_view('config_list_view', template_name='config_list.html'))
bp_allsky.add_url_rule('/config/download', view_func=ConfigDownloadView.as_view('config_download_view'))
bp_allsky.add_url_rule('/config/restore', view_func=ConfigRestoreView.as_view('config_restore_view', template_name='config_restore.html'))
bp_allsky.add_url_rule('/ajax/config/restore', view_func=AjaxConfigRestoreView.as_view('ajax_config_restore_view'))

bp_allsky.add_url_rule('/modern-admin', view_func=ModernAdminView.as_view('modern_admin_view', template_name='modern_admin/index.html'))
bp_allsky.add_url_rule('/modern-admin/capture/service', view_func=ModernAdminCaptureServiceActionView.as_view('modern_admin_capture_service_action_view'))
bp_allsky.add_url_rule('/modern-admin/cameras', view_func=ModernAdminCamerasView.as_view('modern_admin_cameras_view', template_name='modern_admin/cameras.html'))
bp_allsky.add_url_rule('/modern-admin/cameras/add', view_func=ModernAdminCameraAddView.as_view('modern_admin_camera_add_view', template_name='modern_admin/camera_add.html'))
bp_allsky.add_url_rule('/modern-admin/cameras/detect-indi', view_func=ModernAdminIndiCameraDetectView.as_view('modern_admin_camera_detect_indi_view'))
bp_allsky.add_url_rule('/modern-admin/cameras/start-indi', view_func=ModernAdminIndiServerStartView.as_view('modern_admin_start_indi_view'))
bp_allsky.add_url_rule('/modern-admin/cameras/info', view_func=ModernAdminCameraInfoView.as_view('modern_admin_camera_info_view', template_name='modern_admin/camera_info.html'))
bp_allsky.add_url_rule('/modern-admin/cameras/image-lag', view_func=ModernAdminImageLagView.as_view('modern_admin_image_lag_view', template_name='modern_admin/image_lag.html'))
bp_allsky.add_url_rule('/modern-admin/cameras/adu-history', view_func=ModernAdminAduHistoryView.as_view('modern_admin_adu_history_view', template_name='modern_admin/adu_history.html'))
bp_allsky.add_url_rule('/modern-admin/storage', view_func=ModernAdminStorageView.as_view('modern_admin_storage_view', template_name='modern_admin/storage.html'))
bp_allsky.add_url_rule('/modern-admin/storage/file-space-usage', view_func=ModernAdminFileSpaceUsageView.as_view('modern_admin_file_space_usage_view', template_name='modern_admin/file_space_usage.html'))
bp_allsky.add_url_rule('/modern-admin/uploads', view_func=ModernAdminUploadsView.as_view('modern_admin_uploads_view', template_name='modern_admin/uploads.html'))
bp_allsky.add_url_rule('/modern-admin/observatory', view_func=ModernAdminObservatoryView.as_view('modern_admin_observatory_view', template_name='modern_admin/observatory.html'))
bp_allsky.add_url_rule('/modern-admin/observatory/sqm', view_func=ModernAdminSqmView.as_view('modern_admin_sqm_view', template_name='modern_admin/observatory_status.html'))
bp_allsky.add_url_rule('/modern-admin/observatory/charts', view_func=ModernAdminChartsView.as_view('modern_admin_charts_view', template_name='modern_admin/charts.html'))
bp_allsky.add_url_rule('/modern-admin/observatory/sensor-panel', view_func=ModernAdminSensorPanelView.as_view('modern_admin_sensor_panel_view', template_name='modern_admin/sensor_panel.html'))
bp_allsky.add_url_rule('/modern-admin/observatory/astropanel', view_func=ModernAdminAstroPanelView.as_view('modern_admin_astropanel_view', template_name='modern_admin/astropanel.html'))
bp_allsky.add_url_rule('/modern-admin/observatory/virtualsky', view_func=ModernAdminVirtualSkyView.as_view('modern_admin_virtualsky_view', template_name='modern_admin/virtualsky.html'))
bp_allsky.add_url_rule('/modern-admin/observatory/realtime-keogram', view_func=ModernAdminRealtimeKeogramView.as_view('modern_admin_realtime_keogram_view', template_name='modern_admin/realtime_keogram.html'))
bp_allsky.add_url_rule('/modern-admin/observatory/long-term-keogram', view_func=ModernAdminLongTermKeogramView.as_view('modern_admin_longterm_keogram_view', template_name='modern_admin/longterm_keogram.html'))
bp_allsky.add_url_rule('/modern-admin/system', view_func=ModernAdminSystemView.as_view('modern_admin_system_view', template_name='modern_admin/system.html'))
bp_allsky.add_url_rule('/modern-admin/system/info', view_func=ModernAdminSystemInfoView.as_view('modern_admin_system_info_view', template_name='modern_admin/system_info.html'))
bp_allsky.add_url_rule('/modern-admin/system/support', view_func=ModernAdminSupportInfoView.as_view('modern_admin_support_info_view', template_name='modern_admin/support_info.html'))
bp_allsky.add_url_rule('/modern-admin/system/log', view_func=ModernAdminLogView.as_view('modern_admin_log_view', template_name='modern_admin/log.html'))
bp_allsky.add_url_rule('/modern-admin/cameras/dark-library', view_func=ModernAdminDarkLibraryView.as_view('modern_admin_dark_library_view', template_name='modern_admin/dark_library.html'))
bp_allsky.add_url_rule('/modern-admin/cameras/mask-base', view_func=ModernAdminMaskView.as_view('modern_admin_mask_view', template_name='modern_admin/mask.html'))
bp_allsky.add_url_rule('/modern-admin/tools/camera-simulator', view_func=ModernAdminCameraSimulatorView.as_view('modern_admin_camera_simulator_view', template_name='modern_admin/safe_controls.html'))
bp_allsky.add_url_rule('/modern-admin/tools/generate', view_func=ModernAdminGenerateView.as_view('modern_admin_generate_view', template_name='modern_admin/safe_controls.html'))
bp_allsky.add_url_rule('/modern-admin/tools/focus', view_func=ModernAdminFocusView.as_view('modern_admin_focus_view', template_name='modern_admin/safe_controls.html'))
bp_allsky.add_url_rule('/modern-admin/tools/process-fits', view_func=ModernAdminImageProcessingView.as_view('modern_admin_image_processing_view', template_name='modern_admin/safe_controls.html'))
bp_allsky.add_url_rule('/modern-admin/tools/image-circle-helper', view_func=ModernAdminImageCircleHelperView.as_view('modern_admin_image_circle_helper_view', template_name='modern_admin/safe_controls.html'))
bp_allsky.add_url_rule('/modern-admin/settings', view_func=ModernAdminSettingsInventoryView.as_view('modern_admin_settings_view', template_name='modern_admin/settings_inventory.html'))
bp_allsky.add_url_rule('/modern-admin/settings/capture', view_func=ModernAdminCaptureSettingsView.as_view('modern_admin_capture_settings_view', template_name='modern_admin/settings_capture.html'))
bp_allsky.add_url_rule('/modern-admin/settings/cameras', view_func=ModernAdminCameraSettingsView.as_view('modern_admin_camera_settings_view', template_name='modern_admin/settings_cameras.html'))
bp_allsky.add_url_rule('/modern-admin/system/config', view_func=ModernAdminConfigView.as_view('modern_admin_config_view', template_name='modern_admin/safe_controls.html'))
bp_allsky.add_url_rule('/modern-admin/system/network', view_func=ModernAdminNetworkView.as_view('modern_admin_network_view', template_name='modern_admin/safe_controls.html'))
bp_allsky.add_url_rule('/modern-admin/storage/drives', view_func=ModernAdminDriveManagerView.as_view('modern_admin_drive_manager_view', template_name='modern_admin/safe_controls.html'))
bp_allsky.add_url_rule('/modern-admin/system/gpio-control', view_func=ModernAdminManualGpioView.as_view('modern_admin_manual_gpio_view', template_name='modern_admin/safe_controls.html'))
bp_allsky.add_url_rule('/modern-admin/loop', view_func=ModernAdminLoopView.as_view('modern_admin_loop_view', template_name='modern_admin/loop.html'))
bp_allsky.add_url_rule('/modern-admin/updates', view_func=ModernAdminUpdatesView.as_view('modern_admin_updates_view', template_name='modern_admin/updates.html'))
bp_allsky.add_url_rule('/modern-admin/classic/<classic_page>', view_func=ModernAdminClassicPlaceholderView.as_view('modern_admin_classic_placeholder_view', template_name='modern_admin/placeholder.html'))
bp_allsky.add_url_rule('/modern-admin/mode/<mode>', view_func=ModernAdminModeView.as_view('modern_admin_mode_view'))
bp_allsky.add_url_rule('/system', view_func=SystemInfoView.as_view('system_view', template_name='system.html'))
bp_allsky.add_url_rule('/ajax/system', view_func=AjaxSystemInfoView.as_view('ajax_system_view'))
bp_allsky.add_url_rule('/ajax/settime', view_func=AjaxSetTimeView.as_view('ajax_settime_view'))
bp_allsky.add_url_rule('/ajax/settimezone', view_func=AjaxSetTimezoneView.as_view('ajax_settimezone_view'))
bp_allsky.add_url_rule('/ajax/indiserver', view_func=AjaxIndiServerChangeView.as_view('ajax_indiserver_change_view'))

bp_allsky.add_url_rule('/focus', view_func=FocusView.as_view('focus_view', template_name='focus.html'))
bp_allsky.add_url_rule('/js/focus', view_func=JsonFocusView.as_view('js_focus_view'))
bp_allsky.add_url_rule('/ajax/focuscontroller', view_func=AjaxFocusControllerView.as_view('focus_controller_view'))

bp_allsky.add_url_rule('/manual_gpio', view_func=ManualGpioView.as_view('manual_gpio_view', template_name='manual_gpio.html'))
bp_allsky.add_url_rule('/ajax/manual_gpio', view_func=AjaxManualGpioView.as_view('ajax_manual_gpio_view'))

bp_allsky.add_url_rule('/log', view_func=LogView.as_view('log_view', template_name='log.html'))
bp_allsky.add_url_rule('/js/log', view_func=JsonLogView.as_view('js_log_view'))
bp_allsky.add_url_rule('/log/download', view_func=LogDownloadView.as_view('log_download_view'))
bp_allsky.add_url_rule('/log/webapp_download', view_func=LogWebappDownloadView.as_view('log_webapp_download_view'))
bp_allsky.add_url_rule('/log/syslog_download', view_func=LogSyslogDownloadView.as_view('log_syslog_download_view'))
bp_allsky.add_url_rule('/log/kern_download', view_func=LogKernDownloadView.as_view('log_kern_download_view'))

bp_allsky.add_url_rule('/support', view_func=SupportInfoView.as_view('support_info_view', template_name='support_info.html'))
bp_allsky.add_url_rule('/js/support', view_func=JsonSupportInfoView.as_view('js_support_info_view'))

bp_allsky.add_url_rule('/user', view_func=UserInfoView.as_view('user_view', template_name='user.html'))
bp_allsky.add_url_rule('/ajax/user', view_func=AjaxUserInfoView.as_view('ajax_user_view'))

bp_allsky.add_url_rule('/astropanel', view_func=AstroPanelView.as_view('astropanel_view', template_name='astropanel.html'))
bp_allsky.add_url_rule('/ajax/astropanel', view_func=AjaxAstroPanelView.as_view('ajax_astropanel_view'))

bp_allsky.add_url_rule('/processing', view_func=ImageProcessingView.as_view('image_processing_view', template_name='imageprocessing.html'))
bp_allsky.add_url_rule('/js/processing', view_func=JsonImageProcessingView.as_view('js_image_processing_view'))

bp_allsky.add_url_rule('/longtermkeogram', view_func=LongTermKeogramView.as_view('longterm_keogram_view', template_name='longterm_keogram.html'))
bp_allsky.add_url_rule('/js/longtermkeogram', view_func=JsonLongTermKeogramView.as_view('js_longterm_keogram_view'))

bp_allsky.add_url_rule('/camera', view_func=CameraLensView.as_view('camera_lens_view', template_name='cameraLens.html'))
bp_allsky.add_url_rule('/lag', view_func=ImageLagView.as_view('image_lag_view', template_name='lag.html'))
bp_allsky.add_url_rule('/adu', view_func=RollingAduView.as_view('rolling_adu_view', template_name='adu.html'))
bp_allsky.add_url_rule('/darks', view_func=DarkFramesView.as_view('darks_view', template_name='darks.html'))
bp_allsky.add_url_rule('/mask', view_func=MaskView.as_view('mask_view', template_name='mask.html'))
bp_allsky.add_url_rule('/camerasimulator', view_func=CameraSimulatorView.as_view('camera_simulator_view', template_name='camera_simulator.html'))
bp_allsky.add_url_rule('/imagecirclehelper', view_func=ImageCircleHelperView.as_view('image_circle_helper_view', template_name='imagecirclehelper.html'))
bp_allsky.add_url_rule('/filespaceusage', view_func=FileSpaceUsageView.as_view('filespaceusage_view', template_name='filespaceusage.html'))

bp_allsky.add_url_rule('/public', view_func=PublicIndexView.as_view('public_index_view'))  # redirect

bp_allsky.add_url_rule('/network', view_func=NetworkManagerView.as_view('network_manager_view', template_name='network.html'))
bp_allsky.add_url_rule('/ajax/network', view_func=AjaxNetworkManagerView.as_view('ajax_network_manager_view'))

bp_allsky.add_url_rule('/drives', view_func=DriveManagerView.as_view('drive_manager_view', template_name='drive_manager.html'))
bp_allsky.add_url_rule('/ajax/drives', view_func=AjaxDriveManagerView.as_view('ajax_drive_manager_view'))

bp_allsky.add_url_rule('/virtualsky', view_func=VirtualSkyView.as_view('virtualsky_view', template_name='virtualsky.html'))

bp_allsky.add_url_rule('/ajax/notification', view_func=AjaxNotificationView.as_view('ajax_notification_view'))
bp_allsky.add_url_rule('/ajax/selectcamera', view_func=AjaxSelectCameraView.as_view('ajax_select_camera_view'))
bp_allsky.add_url_rule('/ajax/uploadyoutube', view_func=AjaxUploadYoutubeView.as_view('ajax_upload_youtube_view'))

# youtube
bp_allsky.add_url_rule('/youtube/authorize', view_func=YoutubeAuthorizeView.as_view('youtube_authorize_view'))
bp_allsky.add_url_rule('/youtube/oauth2callback', view_func=YoutubeCallbackView.as_view('youtube_oauth2callback_view'))
bp_allsky.add_url_rule('/youtube/oauth2refresh', view_func=YoutubeRefreshAuthView.as_view('youtube_oauth2refresh_view'))
bp_allsky.add_url_rule('/youtube/oauth2revoke', view_func=YoutubeRevokeAuthView.as_view('youtube_oauth2revoke_view'))

# redirects
bp_allsky.add_url_rule('/latestimage', view_func=LatestImageRedirect.as_view('latest_image_redirect_view'))
bp_allsky.add_url_rule('/latestkeogram', view_func=LatestKeogramRedirect.as_view('latest_keogram_redirect_view'))
bp_allsky.add_url_rule('/lateststartrail', view_func=LatestStartrailRedirect.as_view('latest_startrail_redirect_view'))
bp_allsky.add_url_rule('/latestpanorama', view_func=LatestPanoramaImageRedirect.as_view('latest_panorama_image_redirect_view'))
bp_allsky.add_url_rule('/latestraw', view_func=LatestRawImageRedirect.as_view('latest_raw_image_redirect_view'))
bp_allsky.add_url_rule('/latestthumbnail', view_func=LatestThumbnailRedirect.as_view('latest_thumbnail_redirect_view'))
bp_allsky.add_url_rule('/latesttimelapse', view_func=LatestTimelapseVideoRedirect.as_view('latest_timelapse_video_redirect_view'))
bp_allsky.add_url_rule('/lateststartrailvideo', view_func=LatestStartrailVideoRedirect.as_view('latest_startrail_video_redirect_view'))
bp_allsky.add_url_rule('/latestpanoramavideo', view_func=LatestPanoramaVideoRedirect.as_view('latest_panorama_video_redirect_view'))

bp_allsky.add_url_rule('/latestimageview', view_func=LatestImageViewRedirect.as_view('latest_image_view_redirect_view'))
bp_allsky.add_url_rule('/latestkeogramview', view_func=LatestKeogramViewRedirect.as_view('latest_keogram_view_redirect_view'))
bp_allsky.add_url_rule('/lateststartrailview', view_func=LatestStartrailViewRedirect.as_view('latest_startrail_view_redirect_view'))
bp_allsky.add_url_rule('/latestpanoramaview', view_func=LatestPanoramaImageViewRedirect.as_view('latest_panorama_image_view_redirect_view'))
bp_allsky.add_url_rule('/latestrawview', view_func=LatestRawImageViewRedirect.as_view('latest_raw_image_view_redirect_view'))
bp_allsky.add_url_rule('/latesttimelapsewatch', view_func=LatestTimelapseVideoWatchRedirect.as_view('latest_timelapse_video_watch_redirect_view'))
bp_allsky.add_url_rule('/lateststartrailvideowatch', view_func=LatestStartrailVideoWatchRedirect.as_view('latest_startrail_video_watch_redirect_view'))
bp_allsky.add_url_rule('/latestpanoramavideowatch', view_func=LatestPanoramaVideoWatchRedirect.as_view('latest_panorama_video_watch_redirect_view'))

# hidden
bp_allsky.add_url_rule('/cameras', view_func=CamerasView.as_view('cameras_view', template_name='cameras.html'))
bp_allsky.add_url_rule('/tasks', view_func=TaskQueueView.as_view('taskqueue_view', template_name='taskqueue.html'))
bp_allsky.add_url_rule('/notifications', view_func=NotificationsView.as_view('notifications_view', template_name='notifications.html'))
bp_allsky.add_url_rule('/users', view_func=UsersView.as_view('users_view', template_name='users.html'))
