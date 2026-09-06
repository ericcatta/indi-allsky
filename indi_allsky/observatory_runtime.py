"""Read-only Observatory evidence from saved records and the media filesystem."""
from datetime import datetime
import logging
import shutil

from sqlalchemy import func
from sqlalchemy.exc import SQLAlchemyError

from .flask.models import (IndiAllSkyDbCameraTable, IndiAllSkyDbImageTable,
    IndiAllSkyDbFitsImageTable, IndiAllSkyDbRawImageTable, IndiAllSkyDbTaskQueueTable)
from .modern_admin_runtime_providers import ModernAdminCaptureHealthSummaryProvider

logger = logging.getLogger(__name__)


class ObservatoryRuntime:
    def snapshot(self, config, now=None):
        now = now or datetime.now()
        result = {'observed_at': now, 'cameras': [], 'cameras_error': None,
                  'tasks': [], 'tasks_error': None, 'storage': None, 'storage_error': None}
        try:
            result['cameras'] = self.camera_records(config, now)
        except SQLAlchemyError:
            logger.exception('Observatory camera records unavailable')
            result['cameras_error'] = 'Camera records could not be read. Try refreshing or inspect system logs.'
        try:
            result['tasks'] = self.task_counts()
        except SQLAlchemyError:
            logger.exception('Observatory task records unavailable')
            result['tasks_error'] = 'Task records could not be read. Queue health is unknown.'
        try:
            usage = shutil.disk_usage(config['IMAGE_FOLDER'])
            result['storage'] = {'total': usage.total, 'used': usage.used, 'free': usage.free,
                                 'percent': round(100 * usage.used / usage.total, 1) if usage.total else None}
        except (OSError, KeyError, TypeError):
            logger.exception('Observatory media filesystem unavailable')
            result['storage_error'] = 'The configured media filesystem could not be inspected.'
        result['integrations'] = [
            {'label': 'File transfer', 'configured': bool((config.get('FILETRANSFER') or {}).get('HOST'))},
            {'label': 'S3', 'configured': bool((config.get('S3UPLOAD') or {}).get('ENABLE'))},
            {'label': 'YouTube', 'configured': bool((config.get('YOUTUBE') or {}).get('ENABLE'))},
        ]
        return result

    def camera_records(self, config, now):
        profiles = (config.get('MULTI_CAMERA') or {}).get('profiles') or []
        health_provider = ModernAdminCaptureHealthSummaryProvider()
        rows = []
        for camera in IndiAllSkyDbCameraTable.query.order_by(IndiAllSkyDbCameraTable.id).all():
            matching = [p for p in profiles if str(p.get('camera_id') or p.get('camera_db_id') or p.get('db_camera_id')) == str(camera.id)]
            latest = IndiAllSkyDbImageTable.query.filter_by(camera_id=camera.id).order_by(
                IndiAllSkyDbImageTable.createDate.desc(), IndiAllSkyDbImageTable.id.desc()).first()
            health = health_provider.get_capture_health_summary(
                profile_configs=matching, current_camera=camera, now=now,
                latest_frames=[{'camera_id': camera.id, 'timestamp': latest.createDate}] if latest else [],
                default_expected_interval_seconds=config.get('CCD_EXPOSURE_PERIOD', 45),
                default_exposure_timeout_seconds=config.get('CCD_EXPOSURE_TIMEOUT', 330))
            sources = []
            for kind, model in (('fits', IndiAllSkyDbFitsImageTable), ('raw', IndiAllSkyDbRawImageTable)):
                record = model.query.filter_by(camera_id=camera.id).order_by(model.createDate.desc(), model.id.desc()).first()
                sources.append({'kind': kind, 'latest': record.createDate if record else None})
            rows.append({'id': camera.id, 'name': camera.friendlyName or camera.name,
                         'health': health['camera_health'], 'sources': sources,
                         'image_id': latest.id if latest else None,
                         'profiles': [{'id': p.get('profile_id') or p.get('id'), 'enabled': bool(p.get('enabled'))} for p in matching]})
        return rows

    def task_counts(self):
        model = IndiAllSkyDbTaskQueueTable
        rows = model.query.with_entities(model.queue, model.state, func.count(model.id),
            func.min(model.createDate)).group_by(model.queue, model.state).order_by(model.queue, model.state).all()
        return [{'queue': queue.value, 'state': state.value, 'count': count, 'oldest': oldest}
                for queue, state, count, oldest in rows]
