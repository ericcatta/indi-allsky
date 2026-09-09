#!/usr/bin/env python3
"""Former preview URLs lead to actual editors without changing scope or data."""
from urllib.parse import urlsplit, parse_qs
from html import unescape
import re
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
        print('Camera Settings entries: actual editors, both roles/profiles, fixed anchors, auth and no mutation: PASS')


if __name__ == '__main__':
    run()
