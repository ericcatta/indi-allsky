#!/usr/bin/env python3
"""Real SQLite contention during FITS registration, without rewriting a source."""
from datetime import datetime
from pathlib import Path
import hashlib
import sqlite3
from unittest.mock import patch

from sqlalchemy.exc import OperationalError
from hybrid_runtime_fixture import isolated_app
from hybrid_source_media_fixture import seed_source_media

with isolated_app(multi_camera=True, file_database=True) as app:
    seed_source_media(app)
    with app.app_context():
        from indi_allsky.flask import db
        from indi_allsky.flask.models import IndiAllSkyDbFitsImageTable as Fits
        from indi_allsky.flask.miscDb import miscDb
        root = Path(app.config['INDI_ALLSKY_IMAGE_FOLDER'])
        source = root / 'published.fit'
        source.write_bytes(db.session.get(Fits, 1).getFilesystemPath().read_bytes())
        digest = hashlib.sha256(source.read_bytes()).hexdigest()
        metadata = dict(createDate=datetime(2026, 1, 1), dayDate='20260101',
                        exposure=1.5, gain=0, binmode=1, night=True,
                        fileSize=source.stat().st_size, height=48, width=64,
                        data={'context':'preserved'})
        db.session.rollback()
        db.session.execute(db.text('PRAGMA busy_timeout=0'))
        writer = sqlite3.connect(db.engine.url.database, timeout=0)
        writer.execute('BEGIN IMMEDIATE')
        writer.execute('UPDATE camera SET name=name WHERE id=1')
        delays = []
        def release(delay):
            assert hashlib.sha256(source.read_bytes()).hexdigest() == digest
            writer.commit()
            delays.append(delay)
        with patch('indi_allsky.fits_registration.time.sleep', release):
            entry = miscDb({}).addFitsImage(source, 1, metadata)
        assert delays == [0.1]
        assert Fits.query.filter_by(filename=str(source)).count() == 1
        assert (entry.camera_id, entry.createDate, entry.exposure, entry.gain) == (1, metadata['createDate'], 1.5, 0)
        assert entry.data == metadata['data']
        assert hashlib.sha256(source.read_bytes()).hexdigest() == digest
        writer.close()

        busy = sqlite3.OperationalError('database is locked')
        busy.sqlite_errorcode = sqlite3.SQLITE_BUSY
        with patch.object(db.session, 'commit', side_effect=OperationalError('INSERT', {}, busy)) as commit, \
                patch('indi_allsky.fits_registration.time.sleep') as sleep:
            try: miscDb({}).addFitsImage(root/'blocked.fit', 2, metadata)
            except OperationalError: pass
            else: raise AssertionError('Persistent contention hidden')
            assert commit.call_count == 3 and sleep.call_count == 2
        assert Fits.query.filter_by(filename=str(root/'blocked.fit')).count() == 0
        for original in (sqlite3.OperationalError('no such table'), RuntimeError('other backend')):
            with patch.object(db.session, 'commit', side_effect=OperationalError('INSERT', {}, original)) as commit, \
                    patch('indi_allsky.fits_registration.time.sleep') as sleep:
                try: miscDb({}).addFitsImage(root/'invalid.fit', 2, metadata)
                except OperationalError: pass
                else: raise AssertionError('Non-contention error hidden')
                assert commit.call_count == 1 and not sleep.called
        assert Fits.query.filter_by(filename=str(root/'invalid.fit')).count() == 0
        # Failure leaves the session usable; the other camera remains independent.
        other = miscDb({}).addFitsImage(root/'camera2.fit', 2, metadata)
        assert other.camera_id == 2 and other.id != entry.id
        assert hashlib.sha256(source.read_bytes()).hexdigest() == digest
print('FITS registration: real writer conflict, one row, preserved source bytes/metadata, bounded retry and session recovery PASS')
