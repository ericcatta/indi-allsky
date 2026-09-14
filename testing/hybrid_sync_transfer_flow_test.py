#!/usr/bin/env python3
"""Actual Sync video transfer effects, isolation and temporary-file cleanup."""
import hashlib
import hmac
import io
import json
import tempfile
import time
from pathlib import Path
from unittest.mock import patch
from hybrid_runtime_fixture import isolated_app


def run():
    with isolated_app(multi_camera=True) as app:
        from indi_allsky.flask import db
        from indi_allsky.flask.models import IndiAllSkyDbUserTable, IndiAllSkyDbVideoTable
        from indi_allsky.flask.syncapi_views import SyncApiBaseView, SyncApiVideoView
        key = 'dedicated-transfer-fixture-key'
        with app.app_context():
            db.session.get(IndiAllSkyDbUserTable, 1).setApiKey(key, app.config['PASSWORD_KEY'])
        root = Path(app.config['INDI_ALLSKY_IMAGE_FOLDER'])
        scratch = root / 'upload-temporary'; scratch.mkdir()
        original = tempfile.NamedTemporaryFile
        client = app.test_client()
        payload = b'dedicated transfer bytes; codec decoding is tested elsewhere'

        def temporary(*args, **kwargs):
            return original(*args, **{**kwargs, 'dir': scratch})

        def request(method, cid, media=payload, **extra):
            metadata = {'camera_uuid': 'test-camera-' + str(cid), 'utc_offset': 0,
                        'createDate': 1800000000, 'dayDate': '20270115', 'night': True,
                        'success': True, 'frames': 20, 'file_size': len(media), **extra}
            raw = json.dumps(metadata).encode()
            signature = hmac.new(key.encode(), str(int(time.time() // SyncApiBaseView.time_skew)).encode() + raw, hashlib.sha3_512).hexdigest()
            data = {'metadata': (io.BytesIO(raw), 'metadata.json')}
            if method in ('POST', 'PUT'):
                data['media'] = (io.BytesIO(media), 'test.mp4')
            return client.open('/indi-allsky/sync/v1/video', method=method, data=data,
                               headers={'Authorization': 'Bearer test-user-1:' + signature})

        def rows():
            with app.app_context():
                return [(r.id, r.camera_id, r.filename, Path(r.filename).read_bytes())
                        for r in IndiAllSkyDbVideoTable.query.order_by(IndiAllSkyDbVideoTable.camera_id)]

        with patch('indi_allsky.flask.syncapi_views.tempfile.NamedTemporaryFile', side_effect=temporary):
            for cid in (1, 2):
                result = request('POST', cid)
                assert result.status_code == 200, result.text
                assert not list(scratch.iterdir())
            initial = rows()
            assert len(initial) == 2 and [r[1] for r in initial] == [1, 2]
            assert all(r[3] == payload and ('ccd_test-camera-' + str(r[1])) in r[2] for r in initial)
            for extra, expected in (({}, 'file_exists'), ({'camera_uuid': 'missing'}, 'camera not found'),
                                    ({'file_size': 1}, 'authentication failed')):
                result = request('POST', 1, **extra)
                assert result.status_code == 400 and result.json == {'error': expected}
                assert rows() == initial
                assert not list(scratch.iterdir()), ('temporary upload leaked', expected)
            # PUT replaces only the selected camera's output.
            result = request('PUT', 1, media=b'replacement fixture bytes', createDate=1800000030)
            assert result.status_code == 200
            changed = rows()
            assert changed[0][3] == b'replacement fixture bytes' and changed[1] == initial[1]
            assert not Path(initial[0][2]).exists() and not list(scratch.iterdir())
            result = request('DELETE', 2, id=changed[0][0])
            assert result.status_code == 400 and result.json == {'error': 'file_missing'}
            assert rows() == changed
            for row in changed:
                assert request('DELETE', row[1], id=row[0]).status_code == 200
                assert not Path(row[2]).exists()
            assert rows() == []
            # Failed processing and interrupted file writes must also release scratch space.
            with patch.object(SyncApiVideoView, 'processPost', side_effect=OSError('fixture processing failure')):
                try:
                    request('POST', 1)
                except OSError:
                    pass
                else:
                    raise AssertionError('Expected processing exception')
                assert not list(scratch.iterdir())
            from werkzeug.datastructures import FileStorage
            with patch.object(FileStorage, 'save', side_effect=OSError('fixture write failure')):
                try:
                    request('POST', 1)
                except OSError:
                    pass
                else:
                    raise AssertionError('Expected file-write exception')
                assert not list(scratch.iterdir())
        print('Sync transfers: actual POST/PUT/DELETE bytes and rows, two-camera isolation, rejected uploads and exception cleanup: PASS')


if __name__ == '__main__':
    run()
