#!/usr/bin/env python3
"""Real files/SQLite: sacrifice day images before night and generated media."""
from datetime import datetime, timedelta
from pathlib import Path
from types import SimpleNamespace
from hybrid_runtime_fixture import isolated_app


with isolated_app(multi_camera=True) as app, app.app_context():
    from indi_allsky.flask import db, models
    from indi_allsky.storage_pressure import GIB
    from indi_allsky.storage_pressure_runtime import StoragePressureRuntime
    root = Path(app.config['INDI_ALLSKY_IMAGE_FOLDER'])
    now = datetime(2026, 10, 20, 12, 0, 0)
    Image, Fits, Video = (models.IndiAllSkyDbImageTable,
                         models.IndiAllSkyDbFitsImageTable, models.IndiAllSkyDbVideoTable)
    def asset(table, ident, days, night, camera=1):
        when = now - timedelta(days=days)
        path = root / f'{table.__tablename__}-{ident}.dat'
        path.write_bytes(b'disposable priority fixture')
        kw = dict(id=ident, filename=str(path), createDate=when,
                  dayDate=when.date(), night=night, camera_id=camera, data={})
        if table in (Image, Fits):
            kw.update(exposure=1, gain=0)
        if table is Image:
            kw['adu'] = 1
        row = table(**kw)
        db.session.add(row)
        return row, path

    day, day_path = asset(Image, 1, 2, False, 2)
    night, night_path = asset(Image, 2, 8, True)
    recent, recent_path = asset(Image, 3, .5, False)
    source, source_path = asset(Fits, 4, 3, False)
    display, display_path = asset(Image, 4, 3, False)
    display.createDate = source.createDate
    display.data = {'storage_format': 'fits', 'source_fits_id': 4}
    display_path.unlink()
    orphan, orphan_path = asset(Fits, 5, 4, False)
    day_video, day_video_path = asset(Video, 1, 7, False)
    night_video, night_video_path = asset(Video, 2, 9, True, 2)
    protected_video, protected_video_path = asset(Video, 3, 4.99, True)
    uploading_video, uploading_video_path = asset(Video, 4, 10, True)
    db.session.add(models.IndiAllSkyDbTaskQueueTable(
        queue=models.TaskQueueQueue.UPLOAD, state=models.TaskQueueState.QUEUED,
        data={'action': 'upload', 'model': Video.__name__, 'id': 4}))
    db.session.commit()
    space = [4 * GIB]
    runtime = StoragePressureRuntime(
        {'STORAGE_PRESSURE': {'KEEP_DAYS': 1}, 'TIMELAPSE_EXPIRE_DAYS': 1},
        db.session, models, root, disk_usage=lambda path: SimpleNamespace(free=space[0]))
    assert runtime.generated_keep_days == 5
    removed = []
    original_delete = runtime.delete
    def delete(candidate):
        original_delete(candidate)
        removed.append((candidate.table.__tablename__, candidate.identity))
        space[0] += GIB
    runtime.delete = delete
    result = runtime.run(now)
    assert result['status'] == 'recovered'
    assert removed == [('fitsimage', 5), ('image', 4), ('fitsimage', 4), ('image', 1)], removed
    assert not source_path.exists() and not day_path.exists() and not orphan_path.exists()
    assert night_path.exists()
    assert day_video_path.exists() and night_video_path.exists()
    assert recent_path.exists() and protected_video_path.exists() and uploading_video_path.exists()
    # With eligible photos exhausted, generated day output precedes the older
    # night output. Five complete days and pending transfers remain protected.
    space[0] = 4 * GIB
    removed.clear()
    result = runtime.run(now)
    assert removed == [('image', 2), ('video', 1), ('video', 2)], removed
    assert result['status'] == 'insufficient_old_images'
    assert not day_video_path.exists() and not night_video_path.exists()
    assert recent_path.exists() and protected_video_path.exists() and uploading_video_path.exists()

    # Exercise the exact retention boundaries and all states treated as pending
    # in one real candidate scan. Files exactly on a cutoff remain protected;
    # one microsecond older is eligible.
    def asset_at(table, ident, when, night, camera=1):
        path = root / f'boundary-{table.__tablename__}-{ident}.dat'
        path.write_bytes(b'disposable boundary fixture')
        kw = dict(id=ident, filename=str(path), createDate=when,
                  dayDate=when.date(), night=night, camera_id=camera, data={})
        if table is Image:
            kw.update(exposure=1, gain=0, adu=1)
        row = table(**kw)
        db.session.add(row)
        return row, path

    image_boundary, image_boundary_path = asset_at(Image, 10, now-timedelta(days=1), False)
    image_expired, image_expired_path = asset_at(
        Image, 11, now-timedelta(days=1, microseconds=1), False)
    tied_day, tied_day_path = asset_at(Image, 12, now-timedelta(days=2), False)
    tied_night, tied_night_path = asset_at(Image, 13, now-timedelta(days=2), True)
    video_boundary, video_boundary_path = asset_at(Video, 10, now-timedelta(days=5), True)
    video_expired, video_expired_path = asset_at(
        Video, 11, now-timedelta(days=5, microseconds=1), True)
    manual_video, manual_video_path = asset_at(Video, 12, now-timedelta(days=10), True)
    queued_video, queued_video_path = asset_at(Video, 13, now-timedelta(days=10), True)
    running_video, running_video_path = asset_at(Video, 14, now-timedelta(days=10), True)
    for state, data in (
            (models.TaskQueueState.MANUAL,
             {'action': 'upload', 'model': Video.__name__, 'id': manual_video.id}),
            (models.TaskQueueState.QUEUED,
             {'action': 'upload', 'local_file': str(queued_video_path)}),
            (models.TaskQueueState.RUNNING,
             {'action': 'upload', 'model': Video.__name__, 'id': running_video.id})):
        db.session.add(models.IndiAllSkyDbTaskQueueTable(
            queue=models.TaskQueueQueue.UPLOAD, state=state, data=data))
    db.session.commit()

    runtime = StoragePressureRuntime(
        {'STORAGE_PRESSURE': {'KEEP_DAYS': 1}, 'TIMELAPSE_EXPIRE_DAYS': 1},
        db.session, models, root,
        disk_usage=lambda path: SimpleNamespace(free=4 * GIB))
    removed.clear()
    boundary_delete = runtime.delete
    def delete_boundary(candidate):
        boundary_delete(candidate)
        removed.append((candidate.table.__tablename__, candidate.identity))
    runtime.delete = delete_boundary
    result = runtime.run(now)
    assert result['status'] == 'insufficient_old_images'
    assert removed == [
        ('image', tied_day.id),
        ('image', image_expired.id),
        ('image', tied_night.id),
        ('video', video_expired.id),
    ], removed
    assert not image_expired_path.exists() and not tied_day_path.exists()
    assert not tied_night_path.exists() and not video_expired_path.exists()
    for protected in (image_boundary_path, video_boundary_path, manual_video_path,
                      queued_video_path, running_video_path):
        assert protected.exists(), protected
    print('Storage priority: day before night, immediate FITS source reclamation, generated fallback, five-day and upload protection PASS')
