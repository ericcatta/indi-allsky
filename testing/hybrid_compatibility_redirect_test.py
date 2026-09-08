#!/usr/bin/env python3
"""Compatibility ingress keeps scope and filters without rendering placeholders."""
from urllib.parse import parse_qsl, urlsplit
from hybrid_runtime_fixture import isolated_app, login_client


def run():
    with isolated_app(multi_camera=True) as app:
        from flask import url_for
        from indi_allsky.flask.views import ModernAdminCompatibilityRedirectView
        routes = ModernAdminCompatibilityRedirectView.modern_page_redirect_map
        from pathlib import Path
        from unittest.mock import patch
        root = Path(__file__).resolve().parents[1]
        assert not (root / 'indi_allsky/flask/templates/modern_admin/placeholder.html').exists()
        source = (root / 'indi_allsky/flask/views.py').read_text()
        assert 'class ModernAdminPlaceholderView(' not in source
        assert 'classic_page_map =' not in source
        assert set(routes) == {
            'gallery', 'images', 'timelapses', 'mini-timelapses', 'panorama',
            'panorama-loop', 'fits-viewer', 'loop', 'realtime-keogram',
            'long-term-keogram', 'dark-library', 'virtualsky', 'astropanel',
            'log', 'mask-base', 'camera-simulator', 'generate', 'focus',
            'process-fits', 'image-circle-helper', 'config', 'network', 'drives', 'gpio-control'}
        query = 'camera_id=2&profile_id=test-profile-2&filter=sky+%2B+moon&tag=a&tag=b&_external=1&_scheme=https'
        for uid in (1, 2):
            client = login_client(app, uid)
            for slug, endpoint in routes.items():
                with app.test_request_context():
                    expected = url_for(endpoint)
                for suffix in ('', '?' + query):
                    with patch.object(app.jinja_env, 'get_template', side_effect=AssertionError('Redirect tried to load a template')):
                        response = client.get('/indi-allsky/modern-admin/classic/' + slug + suffix)
                    assert response.status_code == 302, (uid, slug, response.status_code)
                    destination = urlsplit(response.headers['Location'])
                    assert not destination.netloc and not destination.scheme
                    assert destination.path == expected
                    assert parse_qsl(destination.query) == (parse_qsl(query) if suffix else [])
            unknown = client.get('/indi-allsky/modern-admin/classic/no-such-feature')
            assert unknown.status_code == 404 and 'coming later' not in unknown.text
            # Complete a representative read-only redirect through its target.
            log = client.get('/indi-allsky/modern-admin/classic/log?camera_id=2&profile_id=test-profile-2', follow_redirects=True)
            assert log.status_code == 200 and 'Application log' in log.text
            assert log.request.args['camera_id'] == '2' and log.request.args['profile_id'] == 'test-profile-2'
        # Bookmarked shell switches must remain usable without Classic routes.
        for uid in (1, 2):
            client = login_client(app, uid)
            for mode, endpoint in [('classic', 'modern_admin_full_settings_view'),
                                   ('modern', 'modern_admin_now_view')]:
                response = client.get('/indi-allsky/modern-admin/mode/' + mode + '?' + query)
                assert response.status_code == 302
                destination = urlsplit(response.location)
                with app.test_request_context():
                    assert destination.path == url_for('indi_allsky.' + endpoint)
                assert not destination.netloc and not destination.scheme
                assert parse_qsl(destination.query) == parse_qsl(query)
                with client.session_transaction() as session:
                    assert session['admin_mode'] == 'modern'
                final = client.get(response.location)
                assert final.status_code == 200
                assert final.request.args['camera_id'] == '2'
                assert final.request.args['profile_id'] == 'test-profile-2'
                assert final.request.args.getlist('tag') == ['a', 'b']
        anonymous_mode = app.test_client().get('/indi-allsky/modern-admin/mode/classic')
        assert anonymous_mode.status_code == 302 and '/login' in anonymous_mode.location
        anonymous = app.test_client().get('/indi-allsky/modern-admin/classic/log')
        assert anonymous.status_code == 302 and '/login' in anonymous.headers['Location']
        print('24 redirect aliases, both roles, repeated filters, camera/profile, local destinations, missing aliases and real target rendering: PASS')


if __name__ == '__main__':
    run()
