#!/usr/bin/env python3
"""Real SQLite writer conflict after thumbnail unlink; bounded safe recovery."""
from datetime import datetime, timedelta
from pathlib import Path
import sqlite3
from unittest.mock import patch

from sqlalchemy.exc import OperationalError

from hybrid_runtime_fixture import isolated_app


with isolated_app(file_database=True) as app, app.app_context():
    from indi_allsky.flask import db, models
    from indi_allsky.storage_pressure_runtime import ImageCandidate, StoragePressureRuntime

    root = Path(app.config['INDI_ALLSKY_IMAGE_FOLDER'])
    Image = models.IndiAllSkyDbImageTable
    Thumbnail = models.IndiAllSkyDbThumbnailTable
    runtime = StoragePressureRuntime({}, db.session, models, root)
    when = datetime.now() - timedelta(days=8)

    def fixture(identity):
        photo, thumb = root / f'{identity}.jpg', root / f'{identity}-thumb.jpg'
        photo.write_bytes(b'expired disposable photo')
        thumb.write_bytes(b'expired disposable thumbnail')
        db.session.add(Thumbnail(id=identity, uuid=f'thumb-{identity}',
                                filename=str(thumb), camera_id=1, createDate=when))
        db.session.add(Image(id=identity, filename=str(photo), camera_id=1,
                             thumbnail_uuid=f'thumb-{identity}', createDate=when,
                             dayDate=when.date(), night=False, exposure=1, gain=0, adu=1))
        db.session.commit()
        return photo, thumb, ImageCandidate(when, Image, identity)

    # No production database or files are used. WAL enables a competing writer
    # after the cleanup transaction has read its candidate and protections.
    database = db.engine.url.database
    writer = sqlite3.connect(database, timeout=0)
    original = Thumbnail.deleteAsset
    collisions = []

    def collide(thumbnail):
        original(thumbnail)
        if not collisions:
            writer.execute('BEGIN IMMEDIATE')
            writer.execute('UPDATE camera SET name=name WHERE id=1')
            collisions.append(thumbnail.id)

    photo, thumb, candidate = fixture(1)
    db.session.execute(db.text('PRAGMA busy_timeout=0'))
    released = []
    def release(delay):
        assert photo.exists() and not thumb.exists()
        writer.commit()
        released.append(delay)
    with patch.object(Thumbnail, 'deleteAsset', collide), \
            patch('indi_allsky.storage_pressure_runtime.time.sleep', release):
        runtime.delete(candidate)
    assert collisions == [1] and released == [0.1]
    assert not photo.exists() and not thumb.exists()
    assert db.session.get(Image, 1) is None and db.session.get(Thumbnail, 1) is None

    # Pending work introduced between attempts must be honored, even though an
    # earlier attempt already removed a thumbnail before the database collision.
    photo, thumb, candidate = fixture(2)
    collisions.clear()
    def queue_upload(delay):
        writer.commit()
        db.session.add(models.IndiAllSkyDbTaskQueueTable(
            queue=models.TaskQueueQueue.UPLOAD, state=models.TaskQueueState.QUEUED,
            data={'action': 'upload', 'model': Image.__name__, 'id': 2}))
        db.session.commit()
    with patch.object(Thumbnail, 'deleteAsset', collide), \
            patch('indi_allsky.storage_pressure_runtime.time.sleep', queue_upload):
        try:
            runtime.delete(candidate)
        except RuntimeError as exc:
            assert 'queued for transfer' in str(exc)
        else:
            raise AssertionError('Retry ignored a newly queued upload')
    db.session.rollback()
    assert photo.exists() and db.session.get(Image, 2) is not None

    # A sustained lock must stop after three attempts, leaving the session usable.
    photo, thumb, candidate = fixture(3)
    busy = sqlite3.OperationalError('database is locked')
    busy.sqlite_errorcode = sqlite3.SQLITE_BUSY
    with patch.object(runtime, '_delete_once', side_effect=OperationalError('DELETE', {}, busy)) as delete, \
            patch('indi_allsky.storage_pressure_runtime.time.sleep') as sleep:
        try:
            runtime.delete(candidate)
        except OperationalError:
            pass
        else:
            raise AssertionError('Exhausted lock failure hidden')
        assert delete.call_count == 3 and sleep.call_count == 2
    assert photo.exists() and thumb.exists() and db.session.get(Image, 3) is not None

    # Non-lock SQLite errors (and non-SQLite failures) must never be retried.
    for original_error in (sqlite3.OperationalError('no such table'), RuntimeError('backend offline')):
        error = OperationalError('DELETE', {}, original_error)
        with patch.object(runtime, '_delete_once', side_effect=error) as delete, \
                patch('indi_allsky.storage_pressure_runtime.time.sleep') as sleep:
            try:
                runtime.delete(candidate)
            except OperationalError as caught:
                assert caught is error
            else:
                raise AssertionError('Non-lock failure hidden')
            assert delete.call_count == 1 and sleep.call_count == 0
    writer.close()
    print('Storage contention: real thumbnail commit collision, refreshed upload guard, bounded retry and error propagation PASS')
