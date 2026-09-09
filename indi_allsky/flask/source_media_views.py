"""Hybrid original media downloads, independent of UI compatibility routes."""
import io
import time
from datetime import datetime
from sqlalchemy.orm.exc import NoResultFound
from ..processing import ImageProcessor
from ..modern_admin_media_runtime import ModernAdminMediaAccessAdapter, ModernAdminMediaUrlNormalizer
from pathlib import Path
from urllib.parse import urlsplit
from flask import abort, current_app as app, redirect, send_file, request, Response
from flask_login import login_required
from .base_views import BaseView
from .models import (IndiAllSkyDbFitsImageTable, IndiAllSkyDbRawImageTable,
    IndiAllSkyDbImageTable, IndiAllSkyDbVideoTable, IndiAllSkyDbMiniVideoTable,
    IndiAllSkyDbKeogramTable, IndiAllSkyDbStarTrailsTable, IndiAllSkyDbStarTrailsVideoTable,
    IndiAllSkyDbPanoramaImageTable, IndiAllSkyDbPanoramaVideoTable,
    IndiAllSkyDbDarkFrameTable, IndiAllSkyDbBadPixelMapTable)

MEDIA_DOWNLOAD_MODELS = {
    'dark': IndiAllSkyDbDarkFrameTable, 'bpm': IndiAllSkyDbBadPixelMapTable,
    'fits': IndiAllSkyDbFitsImageTable, 'raw': IndiAllSkyDbRawImageTable,
    'image': IndiAllSkyDbImageTable, 'video': IndiAllSkyDbVideoTable,
    'mini-video': IndiAllSkyDbMiniVideoTable, 'keogram': IndiAllSkyDbKeogramTable,
    'startrail': IndiAllSkyDbStarTrailsTable, 'startrail-video': IndiAllSkyDbStarTrailsVideoTable,
    'panorama': IndiAllSkyDbPanoramaImageTable, 'panorama-video': IndiAllSkyDbPanoramaVideoTable,
}


def local_source_allowed(camera, verify_admin_network):
    return not camera.web_nonlocal_images or (
        camera.web_local_images_admin and verify_admin_network())


def source_file_path(entry, config):
    """Resolve only a database record inside configured media roots, including RAW export."""
    path = Path(entry.getFilesystemPath()).resolve()
    roots = [app.config['INDI_ALLSKY_IMAGE_FOLDER'], config.get('IMAGE_FOLDER'),
             config.get('IMAGE_EXPORT_FOLDER')]
    if not any(path.is_relative_to(Path(root).resolve()) for root in roots if root):
        abort(404, description='The original file is outside the configured media folders.')
    if not path.is_file():
        abort(404, description='The original file is no longer available locally.')
    return path


class ModernAdminSourceDownloadView(BaseView):
    methods = ['GET']
    decorators = [login_required]

    def dispatch_request(self, kind, camera_id, media_id):
        model = MEDIA_DOWNLOAD_MODELS.get(kind)
        if model is None:
            abort(404)
        entry = model.query.filter_by(id=media_id, camera_id=camera_id).first_or_404()
        # Policy belongs to the record's camera, regardless of current UI selection.
        if not local_source_allowed(entry.camera, self.verify_admin_network):
            if not entry.remote_url and not entry.s3_key:
                abort(404, description='No remote original is available for this camera.')
            target = str(entry.getUrl(s3_prefix=entry.camera.s3_prefix, local=False))
            try:
                parts = urlsplit(target)
            except ValueError:
                abort(404, description='The remote original URL is invalid.')
            if parts.scheme not in ('https', 'http') or not parts.netloc:
                abort(404, description='The remote original URL is unavailable.')
            return redirect(target)
        try:
            path = source_file_path(entry, self.indi_allsky_config)
            response = send_file(path, mimetype='application/octet-stream', as_attachment=True,
                                 download_name=path.name, conditional=True, max_age=0)
            response.cache_control.private = True
            return response
        except FileNotFoundError:
            abort(404, description='The original file was removed before the download started.')
        except PermissionError:
            abort(403, description='The original file cannot be read by the web service.')


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

        try:
            fits_id = int(request.args['id'])
        except (KeyError, ValueError):
            abort(400, description='A valid FITS identifier is required.')


        table = IndiAllSkyDbFitsImageTable

        try:
            fits_entry = table.query\
                .filter(table.id == fits_id)\
                .one()
        except NoResultFound:
            return 'FITS not found', 404


        self.cameraSetup(camera_id=fits_entry.camera_id)


        media_access_adapter = self.get_media_access_adapter()
        if not local_source_allowed(fits_entry.camera, self.verify_admin_network):
            abort(403, description='Local FITS previews are unavailable under this camera storage policy.')
        filename_p = source_file_path(fits_entry, self.indi_allsky_config)


        p_config = self.indi_allsky_config.copy()


        try:
            fits_metadata = media_access_adapter.read_fits_preview_metadata(filename_p, fits.open)
        except FileNotFoundError:
            abort(404, description='The FITS file is no longer available locally.')
        except PermissionError:
            abort(403, description='The FITS file cannot be read by the web service.')
        except (OSError, ValueError, TypeError, IndexError):
            abort(422, description='The FITS header cannot be read. Download the original to inspect it.')

        exposure = fits_metadata['exposure']
        gain = fits_metadata['gain']
        gain_av = Array('f', [gain])
        position_av = Array('f', [self.camera.latitude, self.camera.longitude, self.camera.elevation])
        binning = fits_metadata['binning']
        binning_av = Array('i', [binning])
        sensors_temp_av = Array('f', [fits_metadata['sensor_temp']])
        sensors_user_av = Array('f', [fits_metadata['sensor_temp'], 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0])
        night_av = Array('i', [1, 0])  # using night values for processing
        astro_av = Array('f', [0.0, 0.0, 0.0])

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
        image_date = datetime.fromtimestamp(media_access_adapter.resolve_file_mtime(filename_p))


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


    def get_media_access_adapter(self):
        return ModernAdminMediaAccessAdapter(
            url_normalizer=ModernAdminMediaUrlNormalizer(),
            s3_prefix=self.s3_prefix,
            logger=app.logger,
            error_message='Error resolving FITS preview media path: %s',
        )
