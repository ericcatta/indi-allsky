#!/usr/bin/env python3
"""Settings levels lead to existing controls, preserving camera/profile scope."""
from html import unescape
import re
from urllib.parse import urlsplit, parse_qs
from hybrid_runtime_fixture import isolated_app, login_client


def run():
    with isolated_app(multi_camera=True) as app:
        from indi_allsky.flask.models import IndiAllSkyDbConfigTable
        for uid in (1, 2):
            client = login_client(app, uid)
            for level in ('basic', 'advanced', 'developer'):
                query = '?camera_id=2&profile_id=test-profile-2'
                page = client.get('/indi-allsky/modern-admin/settings/' + level + query)
                assert page.status_code == 200
                assert 'Preview only' not in page.text and 'future product' not in page.text
                grid = re.search(r'data-settings-level-links>(.*?)</div>', page.text, re.S)[1]
                links = [unescape(link) for link in re.findall(r'href="([^"]+)"', grid)]
                assert len(links) == 4
                for href in links:
                    params = parse_qs(urlsplit(href).query)
                    assert params['camera_id'] == ['2'] and params['profile_id'] == ['test-profile-2']
                    destination = client.get(href, follow_redirects=True)
                    assert destination.status_code == 200, (uid, level, href, destination.status_code)
                    assert 'Preview only' not in destination.text
            ready = client.get('/indi-allsky/modern-admin/settings/ready' + query)
            assert ready.status_code == 302
            assert ready.location.endswith('/settings' + query)
            assert 'data-settings-editors' in client.get(ready.location).text
        anonymous = app.test_client().get('/indi-allsky/modern-admin/settings/basic', follow_redirects=True)
        assert '/login' in anonymous.request.path
        with app.app_context():
            assert IndiAllSkyDbConfigTable.query.count() == 1
        print('Settings levels: operational destinations, roles, scope, login and no GET mutation: PASS')


if __name__ == '__main__':
    run()
