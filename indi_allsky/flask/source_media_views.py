"""Hybrid original media downloads, independent of UI compatibility routes."""
from pathlib import Path
from urllib.parse import urlsplit
from flask import abort, current_app as app, redirect, send_file
from flask_login import login_required
from .base_views import BaseView
from .models import (IndiAllSkyDbFitsImageTable, IndiAllSkyDbRawImageTable,
    IndiAllSkyDbImageTable, IndiAllSkyDbVideoTable, IndiAllSkyDbMiniVideoTable,
    IndiAllSkyDbKeogramTable, IndiAllSkyDbStarTrailsTable, IndiAllSkyDbStarTrailsVideoTable,
    IndiAllSkyDbPanoramaImageTable, IndiAllSkyDbPanoramaVideoTable)

MEDIA_DOWNLOAD_MODELS = {
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
