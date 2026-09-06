"""Optional Classic frontend. Imported only when Classic UI is enabled."""

from datetime import timedelta
import time
import math
from pathlib import Path
from flask import request
from flask import current_app as app
from flask_login import login_required
from flask_login import current_user
from .misc import login_optional_media
from .models import IndiAllSkyDbCameraTable
from .models import IndiAllSkyDbImageTable
from .models import IndiAllSkyDbDarkFrameTable
from .models import IndiAllSkyDbBadPixelMapTable
from .models import IndiAllSkyDbTaskQueueTable
from .models import IndiAllSkyDbNotificationTable
from .models import IndiAllSkyDbUserTable
from .models import IndiAllSkyDbConfigTable
from .models import TaskQueueQueue
from .models import TaskQueueState
from sqlalchemy import and_
from .forms import IndiAllskyImageViewerPreload
from .forms import IndiAllskyFitsImageViewerPreload
from .forms import IndiAllskyGalleryViewerPreload
from .forms import IndiAllskyVideoViewerPreload
from .forms import IndiAllskyMiniVideoViewerPreload
from .forms import IndiAllskyLoopHistoryForm
from .forms import IndiAllskyUserInfoForm
from .forms import IndiAllskyImageExcludeForm
from .forms import IndiAllskyMiniTimelapseForm
from .forms import IndiAllskyLongTermKeogramForm
from .forms import IndiAllskyConfigRestoreForm
from .base_views import TemplateView
from .base_views import FormView
from .views import CameraLensView
from .views import CameraSimulatorView
from .views import ChartView
from .views import ConfigView
from .views import DriveManagerView
from .views import FileSpaceUsageView
from .views import FocusView
from .views import ImageCircleHelperView
from .views import ImageLagView
from .views import ImageLoopImgView
from .views import ImageProcessingView
from .views import LogView
from .views import ManualGpioView
from .views import MaskView
from .views import NetworkManagerView
from .views import RealtimeKeogramView
from .views import RollingAduView
from .views import SensorPanelView
from .views import SqmView
from .views import SupportInfoView
from .views import SystemInfoView
from .views import TimelapseGeneratorView
from .views import VirtualSkyView


class IndexCanvasView(TemplateView):
    page_title = 'Latest'
    latest_image_view = 'indi_allsky.js_latest_image_view'


    def get_context(self):
        context = super(IndexCanvasView, self).get_context()

        context['latest_image_view'] = self.latest_image_view

        refreshInterval_ms = math.ceil(self.indi_allsky_config.get('CCD_EXPOSURE_MAX', 15.0)) * 1000
        context['refreshInterval'] = refreshInterval_ms + 1000  # additional time for exposures to download

        return context


class IndexImgView(TemplateView):
    page_title = 'Latest'
    latest_image_view = 'indi_allsky.js_latest_image_view'


    def get_context(self):
        context = super(IndexImgView, self).get_context()

        context['latest_image_view'] = self.latest_image_view

        refreshInterval_ms = math.ceil(self.indi_allsky_config.get('CCD_EXPOSURE_MAX', 15.0)) * 1000
        context['refreshInterval'] = refreshInterval_ms + 1000  # additional time for exposures to download

        return context


class LatestPanoramaCanvasView(IndexCanvasView):
    page_title = 'Panorama'
    latest_image_view = 'indi_allsky.js_latest_panorama_view'


class LatestPanoramaImgView(IndexImgView):
    page_title = 'Panorama'
    latest_image_view = 'indi_allsky.js_latest_panorama_view'


class LatestRawImageCanvasView(IndexCanvasView):
    page_title = 'RAW Image'
    latest_image_view = 'indi_allsky.js_latest_rawimage_view'


class LatestRawImageImgView(IndexImgView):
    page_title = 'RAW Image'
    latest_image_view = 'indi_allsky.js_latest_rawimage_view'


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


class PanoramaLoopCanvasView(ImageLoopCanvasView):
    page_title = 'Panorama Loop'
    image_loop_view = 'indi_allsky.js_panorama_loop_view'


class PanoramaLoopImgView(ImageLoopImgView):
    page_title = 'Panorama Loop'
    image_loop_view = 'indi_allsky.js_panorama_loop_view'


class RawImageLoopCanvasView(ImageLoopCanvasView):
    page_title = 'RAW Image Loop'
    image_loop_view = 'indi_allsky.js_rawimage_loop_view'


class RawImageLoopImgView(ImageLoopImgView):
    page_title = 'RAW Image Loop'
    image_loop_view = 'indi_allsky.js_rawimage_loop_view'


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


class TaskQueueView(TemplateView):
    page_title = 'Task Queue'
    decorators = [login_required]

    def get_task_data_value(self, task_data, key, default=''):
        if not isinstance(task_data, dict):
            return default

        value = task_data.get(key)
        if value not in (None, ''):
            return value

        task_kwargs = task_data.get('kwargs')
        if isinstance(task_kwargs, dict):
            value = task_kwargs.get(key)
            if value not in (None, ''):
                return value

        return default

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
            if isinstance(task.data, dict):
                task_data = task.data
            else:
                task_data = {}

            t = {
                'id'         : task.id,
                'createDate' : task.createDate,
                'updateDate' : getattr(task, 'updateDate', None),
                'queue'      : task.queue.name,
                'state'      : task.state.name,
                'action'     : self.get_task_data_value(task_data, 'action', 'MISSING'),
                'camera_id'  : self.get_task_data_value(task_data, 'camera_id'),
                'profile_id' : self.get_task_data_value(task_data, 'profile_id'),
                'message'    : self.get_task_data_value(task_data, 'message') or self.get_task_data_value(task_data, 'error'),
                'result'     : task.result,
            }

            task_list.append(t)

        context['task_list'] = task_list

        return context


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


class ConfigRestoreView(TemplateView):
    page_title = 'Config Restore'
    decorators = [login_required]

    def get_context(self):
        context = super(ConfigRestoreView, self).get_context()

        context['camera_id'] = self.camera.id

        context['form_config_restore'] = IndiAllskyConfigRestoreForm(indi_allsky_config=self.indi_allsky_config)

        return context


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


class AstroPanelView(TemplateView):
    page_title = 'astropanel'

    def get_context(self):
        context = super(AstroPanelView, self).get_context()
        return context

def register_classic_routes(bp_allsky):
    bp_allsky.add_url_rule('/sensor_panel', view_func=SensorPanelView.as_view('sensor_panel_view', template_name='sensor_panel.html'))
    bp_allsky.add_url_rule('/', view_func=IndexImgView.as_view('index_view', template_name='index_img.html'))
    bp_allsky.add_url_rule('/index_canvas', view_func=IndexCanvasView.as_view('index_canvas_view', template_name='index_canvas.html'))
    bp_allsky.add_url_rule('/index_img', view_func=IndexImgView.as_view('index_img_view', template_name='index_img.html'))
    bp_allsky.add_url_rule('/panorama', view_func=LatestPanoramaImgView.as_view('latest_panorama_view', template_name='index_img.html'))
    bp_allsky.add_url_rule('/panorama_canvas', view_func=LatestPanoramaCanvasView.as_view('latest_panorama_canvas_view', template_name='index_canvas.html'))
    bp_allsky.add_url_rule('/panorama_img', view_func=LatestPanoramaImgView.as_view('latest_panorama_img_view', template_name='index_img.html'))
    bp_allsky.add_url_rule('/raw', view_func=LatestRawImageImgView.as_view('latest_rawimage_view', template_name='index_img.html'))
    bp_allsky.add_url_rule('/raw_canvas', view_func=LatestRawImageCanvasView.as_view('latest_rawimage_canvas_view', template_name='index_canvas.html'))
    bp_allsky.add_url_rule('/raw_img', view_func=LatestRawImageImgView.as_view('latest_rawimage_img_view', template_name='index_img.html'))
    bp_allsky.add_url_rule('/realtime_keogram', view_func=RealtimeKeogramView.as_view('realtime_keogram_view', template_name='realtime_keogram.html'))
    bp_allsky.add_url_rule('/loop', view_func=ImageLoopImgView.as_view('image_loop_view', template_name='loop_img.html'))
    bp_allsky.add_url_rule('/loop_canvas', view_func=ImageLoopCanvasView.as_view('image_loop_canvas_view', template_name='loop_canvas.html'))
    bp_allsky.add_url_rule('/loop_img', view_func=ImageLoopImgView.as_view('image_loop_img_view', template_name='loop_img.html'))
    bp_allsky.add_url_rule('/looppanorama', view_func=PanoramaLoopImgView.as_view('panorama_loop_view', template_name='loop_img.html'))
    bp_allsky.add_url_rule('/looppanorama_canvas', view_func=PanoramaLoopCanvasView.as_view('panorama_loop_canvas_view', template_name='loop_canvas.html'))
    bp_allsky.add_url_rule('/looppanorama_img', view_func=PanoramaLoopImgView.as_view('panorama_loop_img_view', template_name='loop_img.html'))
    bp_allsky.add_url_rule('/loopraw', view_func=RawImageLoopImgView.as_view('rawimage_loop_view', template_name='loop_img.html'))
    bp_allsky.add_url_rule('/loopraw_canvas', view_func=RawImageLoopCanvasView.as_view('rawimage_loop_canvas_view', template_name='loop_canvas.html'))
    bp_allsky.add_url_rule('/loopraw_img', view_func=RawImageLoopImgView.as_view('rawimage_loop_img_view', template_name='loop_img.html'))
    bp_allsky.add_url_rule('/sqm', view_func=SqmView.as_view('sqm_view', template_name='sqm.html'))
    bp_allsky.add_url_rule('/charts', view_func=ChartView.as_view('chart_view', template_name='chart.html'))
    bp_allsky.add_url_rule('/imageviewer', view_func=ImageViewerView.as_view('imageviewer_view', template_name='imageviewer.html'))
    bp_allsky.add_url_rule('/fitsimageviewer', view_func=FitsImageViewerView.as_view('fitsimageviewer_view', template_name='fitsimageviewer.html'))
    bp_allsky.add_url_rule('/gallery', view_func=GalleryViewerView.as_view('gallery_view', template_name='gallery.html'))
    bp_allsky.add_url_rule('/videoviewer', view_func=VideoViewerView.as_view('videoviewer_view', template_name='videoviewer.html'))
    bp_allsky.add_url_rule('/minivideoviewer', view_func=MiniVideoViewerView.as_view('mini_videoviewer_view', template_name='minivideoviewer.html'))
    bp_allsky.add_url_rule('/generate', view_func=TimelapseGeneratorView.as_view('generate_view', template_name='generate.html'))
    bp_allsky.add_url_rule('/minigenerate', view_func=MiniTimelapseGeneratorView.as_view('mini_generate_view', template_name='mini_generate.html'))
    bp_allsky.add_url_rule('/config', view_func=ConfigView.as_view('config_view', template_name='config.html'))
    bp_allsky.add_url_rule('/config/list', view_func=ConfigListView.as_view('config_list_view', template_name='config_list.html'))
    bp_allsky.add_url_rule('/config/restore', view_func=ConfigRestoreView.as_view('config_restore_view', template_name='config_restore.html'))
    bp_allsky.add_url_rule('/system', view_func=SystemInfoView.as_view('system_view', template_name='system.html'))
    bp_allsky.add_url_rule('/focus', view_func=FocusView.as_view('focus_view', template_name='focus.html'))
    bp_allsky.add_url_rule('/manual_gpio', view_func=ManualGpioView.as_view('manual_gpio_view', template_name='manual_gpio.html'))
    bp_allsky.add_url_rule('/log', view_func=LogView.as_view('log_view', template_name='log.html'))
    bp_allsky.add_url_rule('/support', view_func=SupportInfoView.as_view('support_info_view', template_name='support_info.html'))
    bp_allsky.add_url_rule('/user', view_func=UserInfoView.as_view('user_view', template_name='user.html'))
    bp_allsky.add_url_rule('/astropanel', view_func=AstroPanelView.as_view('astropanel_view', template_name='astropanel.html'))
    bp_allsky.add_url_rule('/processing', view_func=ImageProcessingView.as_view('image_processing_view', template_name='imageprocessing.html'))
    bp_allsky.add_url_rule('/longtermkeogram', view_func=LongTermKeogramView.as_view('longterm_keogram_view', template_name='longterm_keogram.html'))
    bp_allsky.add_url_rule('/camera', view_func=CameraLensView.as_view('camera_lens_view', template_name='cameraLens.html'))
    bp_allsky.add_url_rule('/lag', view_func=ImageLagView.as_view('image_lag_view', template_name='lag.html'))
    bp_allsky.add_url_rule('/adu', view_func=RollingAduView.as_view('rolling_adu_view', template_name='adu.html'))
    bp_allsky.add_url_rule('/darks', view_func=DarkFramesView.as_view('darks_view', template_name='darks.html'))
    bp_allsky.add_url_rule('/mask', view_func=MaskView.as_view('mask_view', template_name='mask.html'))
    bp_allsky.add_url_rule('/camerasimulator', view_func=CameraSimulatorView.as_view('camera_simulator_view', template_name='camera_simulator.html'))
    bp_allsky.add_url_rule('/imagecirclehelper', view_func=ImageCircleHelperView.as_view('image_circle_helper_view', template_name='imagecirclehelper.html'))
    bp_allsky.add_url_rule('/filespaceusage', view_func=FileSpaceUsageView.as_view('filespaceusage_view', template_name='filespaceusage.html'))
    bp_allsky.add_url_rule('/network', view_func=NetworkManagerView.as_view('network_manager_view', template_name='network.html'))
    bp_allsky.add_url_rule('/drives', view_func=DriveManagerView.as_view('drive_manager_view', template_name='drive_manager.html'))
    bp_allsky.add_url_rule('/virtualsky', view_func=VirtualSkyView.as_view('virtualsky_view', template_name='virtualsky.html'))
    bp_allsky.add_url_rule('/cameras', view_func=CamerasView.as_view('cameras_view', template_name='cameras.html'))
    bp_allsky.add_url_rule('/tasks', view_func=TaskQueueView.as_view('taskqueue_view', template_name='taskqueue.html'))
    bp_allsky.add_url_rule('/notifications', view_func=NotificationsView.as_view('notifications_view', template_name='notifications.html'))
    bp_allsky.add_url_rule('/users', view_func=UsersView.as_view('users_view', template_name='users.html'))
