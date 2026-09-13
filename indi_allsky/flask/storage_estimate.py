"""Read-only storage forecast from recorded local media sizes and fresh frames."""
from datetime import datetime, timedelta, timezone
from pathlib import Path
import shutil
from sqlalchemy import func, or_
from . import db, models
from ..storage_pressure import GIB, StoragePressureOptions, retention_estimate

IMAGE_FAMILIES = ('Image', 'FitsImage', 'RawImage', 'PanoramaImage', 'Thumbnail')
OUTPUT_FAMILIES = ('Video', 'MiniVideo', 'Keogram', 'StarTrails', 'StarTrailsVideo', 'PanoramaVideo')


def duration_label(seconds):
    if seconds is None:
        return None
    hours = int(max(0, seconds) // 3600)
    if hours == 0:
        return 'less than 1 hour'
    return '{} days, {} hours'.format(*divmod(hours, 24))


def storage_forecast(config, config_id, root, *, now=None, disk_usage=shutil.disk_usage):
    now = now or datetime.now()
    root = Path(root).resolve()
    disk = disk_usage(root)
    result = dict(status='insufficient_data', free_gib=round(disk.free/GIB, 2),
                  total_gib=round(disk.total/GIB, 2), reason='At least one hour of fresh media is needed.')
    options = StoragePressureOptions.from_config(config)
    state = db.session.get(models.IndiAllSkyDbStateTable, 'CONFIG_ID')
    try:
        loaded_id = int(state.value) if state else None
    except ValueError:
        loaded_id = None
    loaded = db.session.get(models.IndiAllSkyDbConfigTable, loaded_id) if loaded_id else None
    current = db.session.get(models.IndiAllSkyDbConfigTable, config_id)
    # Compare persisted representations, avoiding decrypted secrets. A storage-
    # only edit must not require capture reload merely to retain the estimate.
    def capture_settings(entry):
        return {k:v for k,v in entry.data.items() if k != 'STORAGE_PRESSURE'}
    if not loaded or not current or capture_settings(loaded) != capture_settings(current):
        result['reason'] = 'Capture has not confirmed the current configuration. Reload capture before estimating these settings.'
        return result
    saved_local = loaded.createDate.replace(tzinfo=timezone.utc).astimezone().replace(tzinfo=None)
    since = max(saved_local, now-timedelta(hours=24))
    cameras = models.IndiAllSkyDbCameraTable.query.filter_by(local=True, hidden=False).all()
    if not cameras:
        result['reason'] = 'No local cameras are available.'
        return result
    image = models.IndiAllSkyDbImageTable
    starts = []
    for camera in cameras:
        earliest, latest = db.session.query(func.min(image.createDate), func.max(image.createDate)).filter(
            image.camera_id == camera.id, image.createDate >= since, image.createDate <= now).one()
        if latest is None or (now-latest).total_seconds() > 900:
            result['reason'] = 'A local camera has missing or stale frames. Resume acquisition before estimating capacity.'
            return result
        starts.append(earliest)
    since = max(since, *starts)
    seconds = (now-since).total_seconds()
    if seconds < 3600:
        return result
    ids = [camera.id for camera in cameras]
    recorded = observed = samples = unknown = 0
    for name in IMAGE_FAMILIES + OUTPUT_FAMILIES:
        table = getattr(models, 'IndiAllSkyDb'+name+'Table')
        # Historical absolute paths on other disks do not describe this volume.
        # Relative media names are resolved against the configured image root.
        local_path = or_(table.filename.startswith(str(root)+'/'),
                         ~table.filename.startswith('/'))
        scope = (table.camera_id.in_(ids), local_path)
        if name in IMAGE_FAMILIES:
            recorded += db.session.query(func.coalesce(func.sum(table.fileSize), 0)).filter(*scope).scalar()
        total, count, known = db.session.query(func.coalesce(func.sum(table.fileSize), 0),
                func.count(table.id), func.count(table.fileSize)).filter(
                    *scope, table.createDate > since, table.createDate <= now).one()
        observed += total
        samples += count
        unknown += count-known
    if unknown:
        result['reason'] = 'Some recent media have no recorded size; capacity cannot yet be estimated reliably.'
        return result
    estimate = retention_estimate(free_bytes=disk.free, stored_image_bytes=recorded,
                 observed_bytes=observed, observed_seconds=seconds, samples=samples, options=options)
    result.update(estimate)
    if estimate['status'] == 'estimated':
        result.update(reason=None, until_threshold=duration_label(estimate['seconds_to_threshold']),
                      retained_capacity=duration_label(estimate['retained_seconds']),
                      observed_period=duration_label(seconds), gib_per_day=round(observed/seconds*86400/GIB, 2),
                      retention_fits=estimate['retained_seconds'] >= options.keep_days*86400)
    return result
