#!/usr/bin/env python3
"""Diagnostic table parity and storage accounting with synthetic records."""
from datetime import datetime, timedelta
import json
import re
from flask import template_rendered
from hybrid_runtime_fixture import isolated_app, login_client
from hybrid_generation_fixture import seed_generation


def run():
    with isolated_app(multi_camera=True) as app:
        seed_generation(app)
        from indi_allsky.flask import db
        from indi_allsky.flask.models import IndiAllSkyDbImageTable, IndiAllSkyDbThumbnailTable, IndiAllSkyDbConfigTable, IndiAllSkyDbCameraTable
        contexts = []
        def rendered(sender, template, context, **extra):
            contexts.append(context)
        template_rendered.connect(rendered, app)
        with app.app_context():
            for cid in (1, 2):
                db.session.get(IndiAllSkyDbCameraTable, cid).utc_offset = datetime.now().astimezone().utcoffset().total_seconds()
                image = db.session.get(IndiAllSkyDbImageTable, cid)
                image.createDate = datetime.now() - timedelta(seconds=30)
                image.fileSize = cid * 1000
                image.exp_elapsed = None if cid == 1 else 4.4
                image.process_elapsed = None if cid == 1 else 2.2
            db.session.add(IndiAllSkyDbThumbnailTable(uuid='diagnostic-thumb', filename='synthetic-thumb.jpg',
                camera_id=2, width=64, height=48, fileSize=55))
            db.session.get(IndiAllSkyDbImageTable, 2).thumbnail_uuid = 'diagnostic-thumb'
            db.session.commit()
        paths = ['/cameras/image-lag', '/storage/file-space-usage', '/cameras/info',
                 '/cameras/adu-history', '/observatory/virtualsky', '/system/info',
                 '/observatory/charts', '/observatory/sensor-panel', '/observatory/sqm']
        for uid in (1, 2):
            client = login_client(app, uid)
            for suffix in paths:
                path = '/indi-allsky/modern-admin' + suffix
                for cid in (1, 2):
                    page = client.get(path + '?camera_id=' + str(cid))
                    assert page.status_code == 200, (path, page.status_code, page.text[:200])
                    assert int(contexts[-1]['camera_id']) == cid, path
                    if suffix.endswith('image-lag'):
                        body = page.text.split('<tbody>')[1].split('</tbody>')[0]
                        assert ('4.40' in body) == (cid == 2)
                        if cid == 1:
                            assert body.count('—') == 4, body
                    if suffix.endswith('file-space-usage'):
                        days = contexts[-1]['days_fileSize_dict']
                        groups = [group for day in days.values() for group in day.values()]
                        assert sum(group['Images']['count'] for group in groups) == 1
                        assert sum(group['Images']['fileSize'] for group in groups) == cid * 1000
                        assert sum(group['Thumbnails']['fileSize'] for group in groups) == (55 if cid == 2 else 0)
                        assert sum(group['tod_fileSize'] for group in groups) == (2055 if cid == 2 else 1000)
                        for label in ('Panorama Timelapses', 'Star Trail Timelapses', 'Thumbnails'):
                            assert '<th>' + label + '</th>' in page.text
                    if suffix in ('/cameras/image-lag', '/storage/file-space-usage'):
                        cfg = json.loads(re.search(r'id="hybrid-operations-table-config" type="application/json">(.*?)</script>',page.text,re.S)[1])
                        assert cfg['exportColumns'] == list(range(6 if suffix.endswith('image-lag') else 11))
                        assert cfg['filters'][0]['text'] is True
                if suffix in ('/observatory/charts', '/observatory/sensor-panel', '/observatory/sqm'):
                    selected = client.get(path + '?camera_id=1&timestamp=1700000000&all=1')
                    nav = re.search(r'<nav[^>]+aria-label="Observatory camera">(.*?)</nav>', selected.text, re.S)[1]
                    assert nav.count('aria-current="page"') == 1
                    assert nav.count('timestamp=1700000000') == 2 and nav.count('all=1') == 2
                    assert 'profile_id=test-profile-1' in nav and 'profile_id=test-profile-2' in nav
                assert client.get(path + '?profile_id=test-profile-1').status_code == 200
                assert int(contexts[-1]['camera_id']) == 1
                for query in ('camera_id=bad', 'camera_id=1&profile_id=test-profile-2', 'profile_id=missing'):
                    assert client.get(path + '?' + query).status_code == 400, (path, query)
            history = client.get('/indi-allsky/modern-admin/config-history')
            assert history.status_code == 200
            cfg = json.loads(re.search(r'id="hybrid-operations-table-config" type="application/json">(.*?)</script>',history.text,re.S)[1])
            assert cfg['exportColumns'] == list(range(9))
            assert [item['id'] for item in cfg['filters']] == ['modern-config-history-search','modern-config-history-level','modern-config-history-encrypted']
        for offset in (-14400, 14400):
            with app.app_context():
                camera = db.session.get(IndiAllSkyDbCameraTable, 1)
                camera.utc_offset = datetime.now().astimezone().utcoffset().total_seconds() + offset
                db.session.get(IndiAllSkyDbImageTable, 1).createDate = datetime.now() + timedelta(seconds=offset-30)
                db.session.commit()
            page = client.get('/indi-allsky/modern-admin/cameras/image-lag?camera_id=1')
            assert page.status_code == 200 and 'tr data-search' in page.text, 'Recent camera-local frame missing at offset ' + str(offset)
        with app.app_context():
            assert db.session.query(IndiAllSkyDbConfigTable).count() == 1
            assert db.session.query(IndiAllSkyDbImageTable).count() == 2
        print('Diagnostic tables: nine camera-scoped views, nullable timing, all storage categories, thumbnail-free accounting and table controls: PASS')


if __name__ == '__main__':
    run()
