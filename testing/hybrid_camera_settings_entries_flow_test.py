#!/usr/bin/env python3
"""Former preview URLs lead to actual editors without changing scope or data."""
from urllib.parse import urlsplit, parse_qs
from html import unescape
import re
from copy import deepcopy
from types import SimpleNamespace
from hybrid_runtime_fixture import isolated_app, login_client
from hybrid_settings_flow_test import BrowserValues


def run():
    with isolated_app(multi_camera=True) as app:
        from indi_allsky.flask.settings_entries import CAMERA_SETTINGS_ENTRIES
        from indi_allsky.flask.models import IndiAllSkyDbConfigTable as Config
        clients = [login_client(app, 1), login_client(app, 2)]
        for client in clients:
            for cid in (1, 2):
                for path, (_, anchor) in CAMERA_SETTINGS_ENTRIES.items():
                    url = '/indi-allsky/modern-admin/settings/' + path
                    query = '?camera_id=' + str(cid) + '&profile_id=test-profile-' + str(cid)
                    response = client.get(url + query)
                    assert response.status_code == 302
                    target = urlsplit(response.location)
                    assert target.path == '/indi-allsky/modern-admin/settings/cameras'
                    assert target.fragment == anchor
                    assert parse_qs(target.query) == {'camera_id':[str(cid)], 'profile_id':['test-profile-'+str(cid)]}
                    page = client.get(response.location)
                    assert page.status_code == 200
                    assert 'Preview only' not in page.text
                    assert 'id="' + anchor + '"' in page.text
                    values = BrowserValues(page.text).values
                    assert values['camera-driver-profile_id'] == 'test-profile-' + str(cid)
                    assert 'Save Acquisition' in page.text and 'Save Driver / Connection' in page.text
                    assert client.post(url).status_code in (400,405)
                    camera_only = client.get(url + '?camera_id=' + str(cid), follow_redirects=True)
                    assert camera_only.status_code == 200
                    assert BrowserValues(camera_only.text).values['camera-driver-profile_id'] == 'test-profile-' + str(cid)
        # Round trip through the Settings index must retain the chosen profile.
        page = clients[0].get('/indi-allsky/modern-admin/settings/cameras?camera_id=2&profile_id=test-profile-2')
        back = unescape(re.search(r'href="([^"]+)"[^>]*>Back to Settings Inventory</a>', page.text)[1])
        index = clients[0].get(back)
        assert 'data-settings-editors' in index.text
        assert '<summary>Technical reference and settings inventory</summary>' in index.text
        for target in ('/settings/timelapse', '/settings/full', '/config-history', '/config-restore'):
            hrefs = [unescape(href) for href in re.findall(r'href="([^"]+)"', index.text) if target in href]
            assert hrefs, target
            for href in hrefs:
                assert clients[0].get(href, follow_redirects=True).status_code == 200, href
        links = [unescape(href) for href in re.findall(r'href="([^"]+)"', index.text)
                 if '/settings/exposure-gain' in href]
        assert links
        for href in links:
            arrived = clients[0].get(href, follow_redirects=True)
            assert BrowserValues(arrived.text).values['camera-driver-profile_id'] == 'test-profile-2'
        anonymous = app.test_client()
        response = anonymous.get('/indi-allsky/modern-admin/settings/exposure-gain', follow_redirects=True)
        assert 'USERNAME' in response.text or '/login' in response.request.path
        with app.app_context():
            assert Config.query.count() == 1
            from indi_allsky.flask import db
            config = Config.query.one()
            unbound = deepcopy(config.data)
            for profile in unbound['MULTI_CAMERA']['profiles']:
                del profile['db_camera_id']
            config.data = unbound
            db.session.commit()
        # Real deployments may identify hardware by device name, with no DB ID.
        for client in clients:
            for cid in (2, 1):
                profile_id = 'test-profile-' + str(cid)
                page = client.get('/indi-allsky/modern-admin/settings/cameras?profile_id=' + profile_id)
                assert page.status_code == 200
                assert 'Not linked' not in page.text
                back = unescape(re.search(r'href="([^"]+)"[^>]*>Back to Settings Inventory</a>', page.text)[1])
                assert parse_qs(urlsplit(back).query) == {'camera_id':[str(cid)], 'profile_id':[profile_id]}
                index = client.get(back)
                link = next(unescape(href) for href in re.findall(r'href="([^"]+)"', index.text)
                            if '/settings/exposure-gain' in href)
                assert parse_qs(urlsplit(link).query) == {'camera_id':[str(cid)], 'profile_id':[profile_id]}
                arrived = client.get(link, follow_redirects=True)
                assert BrowserValues(arrived.text).values['camera-driver-profile_id'] == profile_id
                camera_only = client.get('/indi-allsky/modern-admin/settings/cameras?camera_id=' + str(cid))
                assert BrowserValues(camera_only.text).values['camera-driver-profile_id'] == profile_id
            assert client.get('/indi-allsky/modern-admin/settings?camera_id=1&profile_id=test-profile-2').status_code == 400
            assert client.get('/indi-allsky/modern-admin/settings?camera_id=invalid').status_code == 400
        with app.app_context():
            assert Config.query.count() == 1
            assert Config.query.one().data == unbound
        from indi_allsky.flask.camera_scope import settings_profile_camera_id
        cameras = [SimpleNamespace(id=1, name='libcamera_imx708'),
                   SimpleNamespace(id=2, name='ZWO CCD ASI678MC')]
        assert settings_profile_camera_id({'camera_interface':'libcamera_imx708'}, cameras) == 1
        assert settings_profile_camera_id({'indi':{'camera_name':'ZWO CCD ASI678MC'}}, cameras) == 2
        assert settings_profile_camera_id({'indi_camera_name':'ASI678'}, cameras) is None
        assert settings_profile_camera_id({'camera_interface':'indi'}, cameras) is None
        assert settings_profile_camera_id({'camera_id':99, 'indi_camera_name':'ZWO CCD ASI678MC'}, cameras) == 99
        assert settings_profile_camera_id({'camera_interface':'libcamera_imx708'}, cameras +
                                         [SimpleNamespace(id=3,name='libcamera_imx708')]) is None
        print('Camera Settings entries: actual editors, both roles/profiles, fixed anchors, auth and no mutation: PASS')


if __name__ == '__main__':
    run()
