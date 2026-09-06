"""Public media compatibility handlers owned by Hybrid, without Classic UI."""
from pathlib import Path
from urllib.parse import urlsplit
from flask import abort, redirect, render_template, request, send_file, url_for
from sqlalchemy.orm.exc import NoResultFound
from . import db
from .base_views import BaseView
from .misc import login_optional_media
from .models import IndiAllSkyDbCameraTable, IndiAllSkyDbImageTable, IndiAllSkyDbThumbnailTable
from .source_media_views import MEDIA_DOWNLOAD_MODELS, local_source_allowed, source_file_path
from ..modern_admin_media_runtime import ModernAdminMediaUrlNormalizer

PUBLIC_MEDIA_MODELS = {key: model for key, model in MEDIA_DOWNLOAD_MODELS.items() if key != 'fits'}
PUBLIC_MEDIA_MODELS['thumbnail'] = IndiAllSkyDbThumbnailTable


def integer_argument(name, default):
    try:
        value = int(request.args.get(name, default))
        if not -(2**63) < value < 2**63:
            raise ValueError()
        return value
    except (ValueError, TypeError):
        abort(400, description='Invalid media '+name+'.')


def record_kind(entry):
    return next(kind for kind, model in PUBLIC_MEDIA_MODELS.items() if isinstance(entry, model))


def checked_local_path(entry, config):
    try:
        return source_file_path(entry, config)
    except PermissionError:
        abort(403, description='The media file cannot be read by the web service.')
    except OSError:
        abort(404, description='The media file is unavailable.')


def media_url(entry, config, verify_admin_network, *, public_redirect=False):
    local = (not entry.camera.web_nonlocal_images if public_redirect
             else local_source_allowed(entry.camera, verify_admin_network))
    if not local:
        if not entry.remote_url and not entry.s3_key:
            abort(404, description='No remote media URL is available for this camera.')
        try:
            target = str(entry.getUrl(s3_prefix=entry.camera.s3_prefix, local=False))
            parts = urlsplit(target)
        except (ValueError, TypeError):
            abort(404, description='The remote media URL is invalid.')
        if parts.scheme not in ('http', 'https') or not parts.netloc:
            abort(404, description='The remote media URL is unavailable.')
        return target
    checked_local_path(entry, config)
    try:
        target = entry.getUrl(local=True)
    except ValueError:
        # A configured RAW export folder can lie outside the ordinary images root.
        return url_for('indi_allsky.public_media_original_view', kind=record_kind(entry),
                       camera_id=entry.camera_id, media_id=entry.id)
    return str(target)


class PublicLatestMediaView(BaseView):
    model = IndiAllSkyDbImageTable
    sort_by_day = False
    thumbnail = False
    show_viewer = False

    def dispatch_request(self):
        camera_id = integer_argument('camera_id', 0)
        if not camera_id:
            try:
                camera_id = self.getLatestCamera().id
            except NoResultFound:
                abort(404, description='No camera is available.')
        IndiAllSkyDbCameraTable.query.filter_by(id=camera_id).first_or_404()
        night = None
        if request.args.get('night') is not None:
            night = bool(integer_argument('night', 0))
        if self.thumbnail:
            query = db.session.query(IndiAllSkyDbThumbnailTable).join(
                IndiAllSkyDbImageTable, IndiAllSkyDbImageTable.thumbnail_uuid == IndiAllSkyDbThumbnailTable.uuid).filter(
                    IndiAllSkyDbImageTable.camera_id == camera_id,
                    IndiAllSkyDbThumbnailTable.camera_id == camera_id)
            if night is not None:
                query = query.filter(IndiAllSkyDbImageTable.night.is_(night))
            query = query.order_by(IndiAllSkyDbImageTable.createDate.desc(), IndiAllSkyDbImageTable.id.desc())
        else:
            query = self.model.query.filter_by(camera_id=camera_id)
            if night is not None:
                query = query.filter(self.model.night.is_(night))
            if self.sort_by_day:
                query = query.order_by(self.model.dayDate.desc())
            query = query.order_by(self.model.createDate.desc(), self.model.id.desc())
        entry = query.first()
        if entry is None:
            abort(404, description='No media match this camera and day/night selection.')
        if self.show_viewer:
            endpoint = getattr(self, 'view_view', None) or self.watch_view
            return redirect(url_for(endpoint, id=entry.id, camera_id=entry.camera_id))
        return redirect(media_url(entry, self.indi_allsky_config, self.verify_admin_network, public_redirect=True))


class PublicMediaViewerView(BaseView):
    decorators = [login_optional_media]
    video = False

    def __init__(self, template_name, **kwargs):
        super().__init__(**kwargs)
        self.template_name = template_name

    def dispatch_request(self):
        media_id = integer_argument('id', -1)
        camera_id = integer_argument('camera_id', 0)
        query = self.model.query
        if camera_id:
            query = query.filter_by(camera_id=camera_id)
        if media_id == -1:
            entry = query.order_by(self.model.dayDate.desc(), self.model.createDate.desc(), self.model.id.desc()).first()
        else:
            entry = query.filter_by(id=media_id).first()
        if entry is None:
            abort(404, description='The requested media record is unavailable.')
        target = media_url(entry, self.indi_allsky_config, self.verify_admin_network)
        normalizer = ModernAdminMediaUrlNormalizer(
            images_folder_url_builder=lambda path: url_for('indi_allsky.images_folder', path=path))
        original = url_for('indi_allsky.public_media_original_view', kind=record_kind(entry),
                          camera_id=entry.camera_id, media_id=entry.id, download=1)
        return render_template(self.template_name, website_title=self.indi_allsky_config.get('WEBSITE', {}).get('TITLE', 'indi-allsky'),
            page_title=self.page_title, media=entry, media_kind=record_kind(entry), media_url=normalizer.normalize_media_url(target),
            original_url=original, is_video=self.video, filename=Path(entry.filename).name,
            permalink=url_for(self.file_view, id=entry.id, camera_id=entry.camera_id, _external=True))


class PublicMediaOriginalView(BaseView):
    decorators = [login_optional_media]

    def dispatch_request(self, kind, camera_id, media_id):
        model = PUBLIC_MEDIA_MODELS.get(kind)
        if model is None:
            abort(404)
        entry = model.query.filter_by(id=media_id, camera_id=camera_id).first_or_404()
        if not local_source_allowed(entry.camera, self.verify_admin_network):
            return redirect(media_url(entry, self.indi_allsky_config, self.verify_admin_network))
        path = checked_local_path(entry, self.indi_allsky_config)
        types = {'.jpg':'image/jpeg', '.jpeg':'image/jpeg', '.png':'image/png', '.webp':'image/webp',
                 '.gif':'image/gif', '.avif':'image/avif', '.mp4':'video/mp4', '.webm':'video/webm'}
        mimetype = types.get(path.suffix.lower(), 'application/octet-stream')
        try:
            response = send_file(path, mimetype=mimetype,
                as_attachment=request.args.get('download') == '1' or mimetype == 'application/octet-stream',
                download_name=path.name, conditional=True, max_age=0)
            response.cache_control.private = True
            response.headers['X-Content-Type-Options'] = 'nosniff'
            return response
        except FileNotFoundError:
            abort(404, description='The media file was removed before it could be read.')
        except PermissionError:
            abort(403, description='The media file cannot be read by the web service.')
