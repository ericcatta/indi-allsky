"""Hybrid mini-timelapse request validation, preview and queue adapter."""
import math
from datetime import timedelta
from flask import current_app, jsonify, request, url_for
from flask_login import login_required, current_user
from sqlalchemy.exc import SQLAlchemyError
from . import db
from .base_views import BaseView
from .models import IndiAllSkyDbImageTable, IndiAllSkyDbTaskQueueTable, TaskQueueQueue, TaskQueueState
from .source_media_views import local_source_allowed
from ..modern_admin_media_runtime import ModernAdminMediaUrlNormalizer


def mini_parameters(payload):
    if not isinstance(payload, dict):
        raise ValueError('Expected a JSON object.')
    try:
        values = {key: int(payload[key]) for key in ('CAMERA_ID', 'IMAGE_ID', 'PRE_SECONDS', 'POST_SECONDS')}
        values['FRAMERATE'] = float(payload['FRAMERATE'])
    except (KeyError, TypeError, ValueError, OverflowError):
        raise ValueError('Choose an image, time interval and valid frame rate.') from None
    if values['CAMERA_ID'] <= 0 or values['IMAGE_ID'] <= 0:
        raise ValueError('Choose an available camera and image.')
    if any(not 0 <= values[key] <= 43200 for key in ('PRE_SECONDS', 'POST_SECONDS')):
        raise ValueError('Each side of the interval must be between 0 and 12 hours.')
    if not math.isfinite(values['FRAMERATE']) or not .25 <= values['FRAMERATE'] <= 25:
        raise ValueError('Frame rate must be between 0.25 and 25 FPS.')
    values['NOTE'] = str(payload.get('NOTE', ''))
    if len(values['NOTE']) > 255:
        raise ValueError('Description must contain at most 255 characters.')
    return values


def mini_image(values):
    return IndiAllSkyDbImageTable.query.filter_by(
        id=values['IMAGE_ID'], camera_id=values['CAMERA_ID']).first_or_404()


def queue_mini_generation():
    # Preserve the existing API's administrator requirement and response key.
    if not current_user.is_admin:
        return jsonify({'failure-message': 'User does not have permission to generate content'}), 400
    try:
        values = mini_parameters(request.get_json(silent=True))
    except ValueError as error:
        return jsonify({'failure-message': str(error)}), 400
    mini_image(values)
    task = IndiAllSkyDbTaskQueueTable(queue=TaskQueueQueue.VIDEO, state=TaskQueueState.MANUAL,
        priority=100, data={'action': 'generateMiniVideo', 'kwargs': {
            key.lower(): values[key] for key in ('IMAGE_ID', 'CAMERA_ID', 'PRE_SECONDS', 'POST_SECONDS', 'FRAMERATE', 'NOTE')}})
    try:
        db.session.add(task)
        db.session.commit()
    except SQLAlchemyError:
        db.session.rollback()
        current_app.logger.exception('Unable to queue mini timelapse')
        return jsonify({'failure-message': 'The queue result could not be confirmed. Check tasks before retrying.'}), 500
    return jsonify({'success-message': 'Job submitted. Check the task result before looking for the output.',
        'task_id': task.id, 'task_url': url_for('indi_allsky.modern_admin_task_detail_view',
                                             task_id=task.id, camera_id=values['CAMERA_ID'])})


class ModernAdminMiniPreviewView(BaseView):
    methods = ['GET']
    decorators = [login_required]

    def dispatch_request(self):
        try:
            values = mini_parameters(request.args.to_dict())
        except ValueError as error:
            return jsonify({'error': str(error)}), 400
        target = mini_image(values)
        start = target.createDate - timedelta(seconds=values['PRE_SECONDS'])
        end = target.createDate + timedelta(seconds=values['POST_SECONDS'])
        # Same inclusive boundaries and excluded-image rule as generateMiniVideo.
        query = IndiAllSkyDbImageTable.query.filter(
            IndiAllSkyDbImageTable.camera_id == target.camera_id,
            IndiAllSkyDbImageTable.createDate >= start, IndiAllSkyDbImageTable.createDate <= end,
            IndiAllSkyDbImageTable.exclude.is_(False))
        count = query.count()
        normalizer = ModernAdminMediaUrlNormalizer(
            images_folder_url_builder=lambda path: url_for('indi_allsky.images_folder', path=path))
        local = local_source_allowed(target.camera, self.verify_admin_network)
        images = []
        for entry in query.order_by(IndiAllSkyDbImageTable.createDate, IndiAllSkyDbImageTable.id).limit(1000):
            if not local and not entry.remote_url and not entry.s3_key:
                continue
            try:
                media_url = normalizer.normalize_media_url(entry.getUrl(s3_prefix=target.camera.s3_prefix, local=local))
            except (ValueError, OSError):
                continue
            images.append({'id': entry.id, 'url': media_url, 'created': entry.createDate.isoformat(' ')})
        return jsonify({'image_id': target.id, 'camera_id': target.camera_id, 'start': start.isoformat(' '),
            'end': end.isoformat(' '), 'count': count, 'seconds': count / values['FRAMERATE'],
            'images': images, 'limited': count > 1000})
