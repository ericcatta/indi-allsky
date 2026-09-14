#!/usr/bin/env python3
"""Signed public Sync reads and camera isolation with Classic forbidden."""
import hashlib
import hmac
import io
import json
from pathlib import Path
from unittest.mock import patch
from hybrid_runtime_fixture import isolated_app
from hybrid_generation_fixture import seed_generation
from hybrid_source_media_fixture import seed_source_media
from hybrid_generated_media_fixture import seed_generated_media
from hybrid_public_media_fixture import seed_public_media


def run():
    with isolated_app(multi_camera=True) as app:
        seed_generation(app); seed_source_media(app); seed_generated_media(app); seed_public_media(app)
        from indi_allsky.flask import db
        from indi_allsky.flask.models import IndiAllSkyDbUserTable, IndiAllSkyDbTaskQueueTable
        from indi_allsky.flask.syncapi_views import SyncApiBaseView
        routes = ('camera', 'image', 'video', 'minivideo', 'keogram', 'startrail',
                  'startrailvideo', 'rawimage', 'fitsimage', 'panoramaimage', 'panoramavideo', 'thumbnail')
        registered = {rule.rule.rsplit('/', 1)[-1] for rule in app.url_map.iter_rules()
                      if rule.rule.startswith('/indi-allsky/sync/v1/')}
        assert registered == set(routes)
        keys = {uid: 'dedicated-sync-key-' + str(uid) for uid in (1, 2)}
        with app.app_context():
            for uid, key in keys.items():
                db.session.get(IndiAllSkyDbUserTable, uid).setApiKey(key, app.config['PASSWORD_KEY'])
        root = Path(app.config['INDI_ALLSKY_IMAGE_FOLDER'])
        def files():
            return {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest()
                    for p in root.rglob('*') if p.is_file()}
        before = files()
        client = app.test_client()
        clock = 1800000150
        bucket = clock // SyncApiBaseView.time_skew

        def request(kind, metadata, uid=1, offset=0, header=None, signed=None):
            raw = json.dumps(metadata, sort_keys=True).encode()
            signature = hmac.new(keys[uid].encode(), str(bucket + offset).encode() + (signed if signed is not None else raw), hashlib.sha3_512).hexdigest()
            headers = {'Authorization': header if header is not None else 'Bearer test-user-' + str(uid) + ':' + signature}
            return client.get('/indi-allsky/sync/v1/' + kind, headers=headers,
                              data={'metadata': (io.BytesIO(raw), 'metadata.json')})

        with patch('indi_allsky.flask.syncapi_views.time.time', return_value=clock):
            for kind in routes:
                for uid in (1, 2):
                    for cid in (1, 2):
                        metadata = {'id': cid, 'camera_uuid': 'test-camera-' + str(cid), 'utc_offset': 0}
                        result = request(kind, metadata, uid)
                        assert result.status_code == 200 and result.json['id'] == cid, (kind, result.text)
                        if kind == 'camera':
                            assert result.json == {'id': cid}
                        else:
                            assert set(result.json) == {'id', 'url'}
                            assert 'camera-' + str(cid) in result.json['url'], result.json
                        other = {**metadata, 'id': 3-cid}
                        result = request(kind, other, uid)
                        assert result.status_code == 400 and result.json == {'error': 'camera_missing' if kind == 'camera' else 'file_missing'}
                        missing = {**metadata, 'camera_uuid': 'missing-camera'}
                        result = request(kind, missing, uid)
                        assert result.status_code == 400 and result.json == {'error': 'camera_missing' if kind == 'camera' else 'camera not found'}
                metadata = {'id': 1, 'camera_uuid': 'test-camera-1', 'utc_offset': 0}
                for header in ('', 'invalid', 'Bearer missing:invalid', 'Bearer test-user-1:invalid'):
                    result = request(kind, metadata, header=header)
                    assert result.status_code == 400 and result.json == {'error': 'authentication failed'}
                result = request(kind, metadata, signed=b'{}')
                assert result.status_code == 400 and result.json == {'error': 'authentication failed'}
            metadata = {'id': 1, 'camera_uuid': 'test-camera-1', 'utc_offset': 0}
            for offset in (-4, -3, -2, -1, 0, 1):
                assert request('camera', metadata, offset=offset).status_code == 200
            for offset in (-5, 2):
                result = request('camera', metadata, offset=offset)
                assert result.status_code == 400 and result.json == {'error': 'authentication failed'}
        assert files() == before
        with app.app_context():
            assert IndiAllSkyDbTaskQueueTable.query.count() == 0
        print('Sync API: all 12 read routes, both API users/cameras, signed metadata, skew window, missing/cross-camera records, no file/task effects without Classic: PASS')


if __name__ == '__main__':
    run()
