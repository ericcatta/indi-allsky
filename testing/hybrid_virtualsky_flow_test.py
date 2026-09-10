#!/usr/bin/env python3
"""Interactive VirtualSky inputs/assets render independently of Classic."""
import json
import re
from html import unescape
from urllib.parse import urlsplit, parse_qs
from hybrid_runtime_fixture import isolated_app, login_client


def run():
    with isolated_app(multi_camera=True) as app:
        from indi_allsky.flask import db
        from indi_allsky.flask.models import IndiAllSkyDbCameraTable, IndiAllSkyDbConfigTable
        with app.app_context():
            for cid in (1, 2):
                camera = db.session.get(IndiAllSkyDbCameraTable, cid)
                camera.az = 30 * cid
                camera.data = {'vs_image_circle_diameter': 400 * cid}
            db.session.commit()
        for uid in (1, 2):
            client = login_client(app, uid)
            for cid in (1, 2):
                page = client.get('/indi-allsky/modern-admin/observatory/virtualsky?camera_id=' + str(cid))
                assert page.status_code == 200, page.text[:500]
                assert 'read-only here' not in page.text
                assert 'id="virtualsky-clip" aria-hidden="true"' in page.text
                assert 'alt="Selected camera frame with sky overlay"' in page.text
                nav = re.search(r'<nav[^>]+aria-label="Observatory camera">(.*?)</nav>', page.text, re.S)[1]
                assert nav.count('aria-current="page"') == 1
                links = re.findall(r'<a[^>]+href="([^"]+)"([^>]*)>', nav)
                assert len(links) == 2
                for href, attributes in links:
                    query = parse_qs(urlsplit(unescape(href)).query)
                    target = int(query['camera_id'][0])
                    assert query['profile_id'] == ['test-profile-' + str(target)]
                    assert ('aria-current="page"' in attributes) == (target == cid)
                    destination = client.get(unescape(href))
                    target_config = json.loads(re.search(r'<script id="virtualsky-config" type="application/json">(.*?)</script>', destination.text, re.S)[1])
                    assert int(target_config['cameraId']) == target
                for control in ('AZIMUTH_ANGLE', 'LATITUDE_OFFSET', 'LONGITUDE_OFFSET', 'IMAGE_CIRCLE_DIAMETER',
                                'OFFSET_X', 'OFFSET_Y', 'MAGNITUDE', 'CONSTELLATIONS', 'CONSTELLATIONLABELS',
                                'SHOWSTARS', 'SHOWSTARLABELS', 'SHOWPLANETS', 'SHOWPLANETLABELS'):
                    assert 'name="' + control + '"' in page.text, control
                config = json.loads(re.search(r'<script id="virtualsky-config" type="application/json">(.*?)</script>', page.text, re.S)[1])
                assert int(config['cameraId']) == cid
                assert config['latitude'] == 46 and config['longitude'] == 8
                assert 'value="' + str(400 * cid) + '"' in page.text
                for asset in ('modern_admin/virtualsky.js', 'modern_admin/virtualsky.css',
                              'virtualsky/virtualsky.min.js', 'virtualsky/stuquery.min.js', 'html2canvas/html2canvas.min.js'):
                    assert client.get('/indi-allsky/static/' + asset).status_code == 200
            for query in ('camera_id=bad', 'camera_id=1&profile_id=test-profile-2', 'profile_id=missing'):
                assert client.get('/indi-allsky/modern-admin/observatory/virtualsky?' + query).status_code == 400
            profile = client.get('/indi-allsky/modern-admin/observatory/virtualsky?profile_id=test-profile-1')
            assert profile.status_code == 200 and 'value="400"' in profile.text
        assert app.test_client().get('/indi-allsky/modern-admin/observatory/virtualsky').status_code == 302
        with app.app_context():
            assert db.session.query(IndiAllSkyDbConfigTable).count() == 1
            assert db.session.get(IndiAllSkyDbCameraTable, 2).data == {'vs_image_circle_diameter': 800}
        print('VirtualSky controls, camera scope, assets, roles and unchanged configuration: PASS')


if __name__ == '__main__':
    run()
