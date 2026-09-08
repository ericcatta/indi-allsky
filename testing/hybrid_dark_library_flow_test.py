#!/usr/bin/env python3
"""Calibration library to real FITS processing/download, without Classic."""
import base64
from copy import deepcopy
import hashlib
from html.parser import HTMLParser
import io
import json
from pathlib import Path
import re
from shutil import copyfile
from urllib.parse import parse_qs, urlsplit
from unittest.mock import patch
from zipfile import ZipFile
from hybrid_runtime_fixture import isolated_app, login_client
from hybrid_source_media_fixture import seed_source_media
from hybrid_fits_processing_flow_test import payload_from_page


class Library(HTMLParser):
    def __init__(self, text):
        super().__init__()
        self.links = {'process': [], 'download': []}
        self.rows = []
        self.feed(text)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'tr' and 'data-calibration-row' in attrs:
            self.rows.append(attrs)
        for kind in self.links:
            if tag == 'a' and 'data-calibration-' + kind in attrs:
                self.links[kind].append(attrs['href'])


def run():
    from PIL import Image
    with isolated_app(multi_camera=True) as app:
        seed_source_media(app)
        from indi_allsky.flask import db
        from indi_allsky.flask.models import (IndiAllSkyDbDarkFrameTable as Dark,
            IndiAllSkyDbBadPixelMapTable as Bpm, IndiAllSkyDbCameraTable as Camera,
            IndiAllSkyDbConfigTable as Config, IndiAllSkyDbTaskQueueTable as Task)
        with app.app_context():
            root = Path(app.config['INDI_ALLSKY_IMAGE_FOLDER'])
            original_config = deepcopy(db.session.get(Config, 1).data)
            for cid in (1, 2):
                source = root / ('ccd_test-camera-' + str(cid)) / ('source-camera-' + str(cid) + '.fit')
                for kind, model in (('dark', Dark), ('bpm', Bpm)):
                    target = source.parent / (kind + '.fit')
                    copyfile(source, target)
                    db.session.add(model(id=cid, camera_id=cid, filename=str(target),
                        bitdepth=16, exposure=1, gain=10, binmode=1, width=64, height=48,
                        temp=None, adu=None, active=kind == 'dark',
                        data={'method': 'camera-' + str(cid), 'hot_pixels': None if cid == 2 else 3 * cid}))
            db.session.commit()
            hashes = {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in root.rglob('*') if p.is_file()}
        page = '/indi-allsky/modern-admin/cameras/dark-library'
        results = []
        for uid in (1, 2):
            client = login_client(app, uid)
            for cid in (1, 2):
                response = client.get(page, query_string={'camera_id': cid, 'profile_id': 'test-profile-' + str(cid)})
                assert response.status_code == 200
                assert 'intentionally omitted' not in response.text and 'Unknown' in response.text
                parsed = Library(response.text)
                assert len(parsed.rows) == 2 and len(parsed.links['process']) == len(parsed.links['download']) == 2
                assert {r['data-kind'] for r in parsed.rows} == {'dark', 'bpm'}
                assert all('camera-' + str(cid) in r['data-search'] for r in parsed.rows)
                for url in parsed.links['process']:
                    query = parse_qs(urlsplit(url).query)
                    assert query['camera_id'] == query['id'] == [str(cid)]
                    process = client.get(url)
                    assert process.status_code == 200
                    payload, headers = payload_from_page(app, process.text)
                    assert payload['CAMERA_ID'] == payload['FITS_ID'] == str(cid)
                    assert payload['FRAME_TYPE'] == query['type'][0]
                    payload.update(DISABLE_PROCESSING=True, IMAGE_STACK_COUNT='1', OUTPUT_IMAGE_TYPE='png')
                    generated = client.post('/indi-allsky/js/processing', json=payload, headers=headers)
                    assert generated.status_code == 200, generated.json
                    pixels = base64.b64decode(generated.json['image_b64'])
                    with Image.open(io.BytesIO(pixels)) as image:
                        image.load()
                        assert image.size == (64, 48)
                    assert client.post('/indi-allsky/js/processing', json=payload).status_code == 400
                    results.append({'user_id': uid, 'camera_id': cid, 'kind': query['type'][0],
                                    'processed_bytes': len(pixels), 'sha256': hashlib.sha256(pixels).hexdigest()})
                for url in parsed.links['download']:
                    download = client.get(url)
                    assert download.status_code == 200 and 'attachment' in download.headers['Content-Disposition']
                    kind = 'dark' if '/dark/' in url else 'bpm'
                    assert download.data == (root / ('ccd_test-camera-' + str(cid)) / (kind + '.fit')).read_bytes()
                    assert client.get(url.replace('/' + str(cid) + '/' + str(cid) + '/', '/' + str(3-cid) + '/' + str(cid) + '/')).status_code == 404
                settings = json.loads(re.search(r'id="hybrid-operations-table-config">(.*?)</script>', response.text, re.S)[1])
                assert settings['table'] == 'calibration-table' and len(settings['filters']) == 3
                for fmt in ('csv', 'xlsx'):
                    export = client.post(settings['exportUrl'], data={'csrf_token': settings['csrfToken'], 'format': fmt,
                        'table': json.dumps({'header': ['Type', 'Method'], 'body': [['Dark frame', 'camera-' + str(cid)]]})})
                    assert export.status_code == 200, export.text[:200]
                    if fmt == 'csv':
                        assert 'camera-' + str(cid) in export.text
                    else:
                        with ZipFile(io.BytesIO(export.data)) as archive:
                            assert any(('camera-' + str(cid)).encode() in archive.read(n) for n in archive.namelist() if n.endswith('.xml'))
        client = login_client(app, 1)
        with patch('indi_allsky.flask.views.IndiAllSkyDbDarkFrameTable') as broken_model:
            broken_model.query.join.side_effect = RuntimeError('synthetic provider failure')
            failure_page = client.get(page + '?camera_id=1')
            assert failure_page.status_code == 200 and 'Unable to load dark frames' in failure_page.text
            assert 'synthetic provider failure' not in failure_page.text
            assert len(Library(failure_page.text).rows) == 1
        assert app.test_client().get(page).status_code == 302
        for query, status in (('camera_id=bad',400), ('camera_id=999',404),
                              ('camera_id=1&profile_id=test-profile-2',400), ('profile_id=missing',400)):
            assert client.get(page + '?' + query).status_code == status
        assert len(Library(client.get(page + '?profile_id=test-profile-2').text).rows) == 2
        for kind in ('dark', 'bpm'):
            url = '/indi-allsky/modern-admin/media/' + kind + '/1/1/download'
            assert app.test_client().get(url).status_code == 302
        with app.app_context():
            assert db.session.get(Config, 1).data == original_config and Task.query.count() == 0
            assert hashes == {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in root.rglob('*') if p.is_file()}
            missing = root / 'ccd_test-camera-1/dark.fit'
            saved = missing.read_bytes()
            missing.unlink()
        missing_page = client.get(page + '?camera_id=1')
        assert 'File unavailable' in missing_page.text and len(Library(missing_page.text).links['process']) == 1
        assert client.get('/indi-allsky/modern-admin/media/dark/1/1/download').status_code == 404
        missing.write_bytes(saved)
        with app.app_context():
            camera = db.session.get(Camera, 2)
            camera.web_nonlocal_images = True
            camera.web_local_images_admin = False
            db.session.commit()
        restricted = client.get(page + '?camera_id=2')
        assert 'Local access restricted' in restricted.text and not Library(restricted.text).links['process']
        assert client.get('/indi-allsky/modern-admin/media/dark/2/2/download').status_code == 404
        with app.app_context():
            Dark.query.filter_by(camera_id=1).delete()
            Bpm.query.filter_by(camera_id=1).delete()
            db.session.commit()
        assert 'No calibration records' in client.get(page + '?camera_id=1').text
        print(json.dumps({'scope': 'Classic-disabled isolated SQLite and synthetic FITS; no live calibration changes',
                          'processing': results, 'downloads': 'byte-identical originals for both roles/cameras/types',
                          'exports': 'CSV and XLSX decoded', 'missing_restricted_empty': 'explicit states',
                          'source_config_task_mutations': 'none'}, indent=2))


if __name__ == '__main__':
    run()
