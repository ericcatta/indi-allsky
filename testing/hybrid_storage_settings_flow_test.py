#!/usr/bin/env python3
"""Exercise storage protection settings with real isolated persistence and CSRF."""
import argparse
import re
from html import unescape
from urllib.parse import parse_qs, urlsplit
from hybrid_runtime_fixture import isolated_app, login_client


def run(runtime_config):
    with isolated_app(runtime_config, multi_camera=True) as app:
        from indi_allsky.flask.models import IndiAllSkyDbConfigTable as Config
        admin = login_client(app, 1)
        url = '/indi-allsky/modern-admin/settings/storage-protection'

        base_url = url
        url += '?camera_id=2&profile_id=test-profile-2'

        def assert_context(location, camera=2):
            query = parse_qs(urlsplit(unescape(location)).query)
            assert query.get('camera_id') == [str(camera)], location
            assert query.get('profile_id') == [f'test-profile-{camera}'], location

        for camera in (1, 2):
            page = admin.get(base_url + f'?camera_id={camera}&profile_id=test-profile-{camera}')
            assert page.status_code == 200
            for label in ['All settings', 'Tasks']:
                links = re.findall(r'<a href="([^"]+)">' + re.escape(label) + r'</a>', page.text)
                assert links, label
                # Footer links follow the shared navigation.
                assert_context(links[-1], camera)

        def form(client):
            page = client.get(url)
            assert page.status_code == 200, page.text[:300]
            return page, {
                name: re.search(r'name="' + name + r'" value="([^"]+)"', page.text)[1]
                for name in ('csrf_token', 'revision')}

        page, data = form(admin)
        assert re.search(r'name="enabled" checked', page.text)
        assert admin.post(url, data={'minimum': '5'}).status_code == 400
        assert app.test_client().get(url).status_code == 302
        with app.app_context():
            before = Config.query.order_by(Config.id.desc()).first().data
        data.update(minimum='5', target='4', days='3')
        assert admin.post(url, data=data).status_code == 400
        data['target'] = '8'
        response = admin.post(url, data=data)
        assert response.status_code == 303
        assert_context(response.headers['Location'])
        with app.app_context():
            saved = Config.query.order_by(Config.id.desc()).first().data
            assert saved['STORAGE_PRESSURE'] == dict(ENABLE=False, MIN_FREE_GIB=5., TARGET_FREE_GIB=8., KEEP_DAYS=3)
            assert {k:v for k,v in saved.items() if k != 'STORAGE_PRESSURE'} == {k:v for k,v in before.items() if k != 'STORAGE_PRESSURE'}
        assert admin.post(url, data=data).status_code == 409
        page, data = form(admin)
        assert not re.search(r'name="enabled" checked', page.text)
        data.update(minimum='6', target='10', days='2', enabled='on')
        response = admin.post(url, data=data)
        assert response.status_code == 303
        assert_context(response.headers['Location'])
        with app.app_context():
            saved = Config.query.order_by(Config.id.desc()).first().data
            assert saved['STORAGE_PRESSURE'] == dict(ENABLE=True, MIN_FREE_GIB=6., TARGET_FREE_GIB=10., KEEP_DAYS=2)
        reader = login_client(app, 2)
        page, data = form(reader)
        assert re.search(r'<fieldset[^>]*disabled', page.text)
        data.update(minimum='5', target='8', days='3', enabled='on')
        assert reader.post(url, data=data).status_code == 403
        print('Hybrid storage protection settings persistence: PASS')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--runtime-config', default='/etc/indi-allsky/flask.json')
    run(parser.parse_args().runtime_config)
