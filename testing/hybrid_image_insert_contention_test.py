#!/usr/bin/env python3
"""Real SQLite writer contention for image and panorama registration."""
import argparse
from datetime import datetime
import hashlib
from pathlib import Path
import sqlite3
from unittest.mock import patch

from sqlalchemy.exc import OperationalError

from hybrid_runtime_fixture import isolated_app


def file_digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def run(runtime_config):
    with isolated_app(runtime_config, multi_camera=True, file_database=True) as app:
        with app.app_context():
            from indi_allsky.flask import db
            from indi_allsky.flask.miscDb import miscDb
            from indi_allsky.flask.models import IndiAllSkyDbImageTable as Image
            from indi_allsky.flask.models import IndiAllSkyDbPanoramaImageTable as Panorama

            root = Path(app.config['INDI_ALLSKY_IMAGE_FOLDER'])
            image_path = root / 'contention-image.jpg'
            panorama_path = root / 'contention-panorama.jpg'
            image_path.write_bytes(b'image bytes stay unchanged')
            panorama_path.write_bytes(b'panorama bytes stay unchanged')
            hashes = {image_path: file_digest(image_path), panorama_path: file_digest(panorama_path)}
            created = datetime(2026, 10, 19, 1, 2, 3)
            image_metadata = dict(
                createDate=created, dayDate='20261019', exposure=1.5,
                exp_elapsed=1.6, gain=22, binmode=1, temp=4.5, adu=31.0,
                stable=True, moonmode=False, moonphase=42.0, night=True,
                sqm=20.1, adu_roi=False, calibrated=False, stars=7,
                detections=2, process_elapsed=0.4, fileSize=image_path.stat().st_size,
                width=64, height=48, data={'scope': 'image'}, exclude=False,
            )
            panorama_metadata = dict(
                createDate=created, dayDate='20261019', exposure=1.5,
                gain=22, binmode=1, night=True,
                fileSize=panorama_path.stat().st_size, width=128, height=32,
                data={'scope': 'panorama'},
            )
            database = db.engine.url.database
            registrar = miscDb({})

            def contend(call):
                db.session.rollback()
                db.session.execute(db.text('PRAGMA busy_timeout=0'))
                writer = sqlite3.connect(database, timeout=0)
                writer.execute('BEGIN IMMEDIATE')
                writer.execute('UPDATE camera SET name=name WHERE id=1')
                delays = []

                def release(delay):
                    assert all(file_digest(path) == digest for path, digest in hashes.items())
                    writer.commit()
                    delays.append(delay)

                try:
                    with patch('indi_allsky.sqlite_transactions.time.sleep', release):
                        entry = call()
                finally:
                    writer.close()
                assert delays == [0.1]
                return entry

            image = contend(lambda: registrar.addImage(image_path, 1, image_metadata))
            panorama = contend(lambda: registrar.addPanoramaImage(
                panorama_path, 1, panorama_metadata))

            assert Image.query.filter_by(filename=str(image_path)).count() == 1
            assert Panorama.query.filter_by(filename=str(panorama_path)).count() == 1
            assert (image.camera_id, image.createDate, image.gain, image.data) == (
                1, created, 22.0, {'scope': 'image'})
            assert (panorama.camera_id, panorama.createDate, panorama.width,
                    panorama.data) == (1, created, 128, {'scope': 'panorama'})
            assert all(file_digest(path) == digest for path, digest in hashes.items())

            busy = sqlite3.OperationalError('database is locked')
            busy.sqlite_errorcode = sqlite3.SQLITE_BUSY
            blocked_image = root / 'blocked-image.jpg'
            blocked_panorama = root / 'blocked-panorama.jpg'
            for method, model, path, metadata in (
                    (registrar.addImage, Image, blocked_image, image_metadata),
                    (registrar.addPanoramaImage, Panorama, blocked_panorama, panorama_metadata)):
                with patch.object(db.session, 'commit',
                                  side_effect=OperationalError('INSERT', {}, busy)) as commit, \
                        patch('indi_allsky.sqlite_transactions.time.sleep') as sleep:
                    try:
                        method(path, 2, metadata)
                    except OperationalError:
                        pass
                    else:
                        raise AssertionError('Persistent SQLite contention was hidden')
                    assert commit.call_count == 3 and sleep.call_count == 2
                assert model.query.filter_by(filename=str(path)).count() == 0

            for original in (sqlite3.OperationalError('no such table'),
                             RuntimeError('other backend')):
                invalid = root / ('invalid-%s.jpg' % type(original).__name__)
                with patch.object(db.session, 'commit',
                                  side_effect=OperationalError('INSERT', {}, original)) as commit, \
                        patch('indi_allsky.sqlite_transactions.time.sleep') as sleep:
                    try:
                        registrar.addImage(invalid, 2, image_metadata)
                    except OperationalError:
                        pass
                    else:
                        raise AssertionError('Non-contention database error was hidden')
                    assert commit.call_count == 1 and not sleep.called
                assert Image.query.filter_by(filename=str(invalid)).count() == 0

            # Rollback after bounded failure leaves the scoped session reusable.
            recovered_path = root / 'recovered-camera2.jpg'
            recovered = registrar.addPanoramaImage(recovered_path, 2, panorama_metadata)
            assert recovered.camera_id == 2
            assert Panorama.query.filter_by(filename=str(recovered_path)).count() == 1
            assert all(file_digest(path) == digest for path, digest in hashes.items())

    print('Image inserts: real SQLite competition, one row, bounded retry, no file replay, error propagation and session recovery PASS')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--runtime-config', default='/etc/indi-allsky/flask.json')
    args = parser.parse_args()
    run(args.runtime_config)
