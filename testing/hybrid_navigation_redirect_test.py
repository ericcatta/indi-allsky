#!/usr/bin/env python3
"""All Classic UI entrances remain resolvable with Classic import forbidden."""
import ast
from pathlib import Path
from urllib.parse import parse_qsl, urlsplit
from unittest.mock import patch
from hybrid_runtime_fixture import isolated_app, login_client


def run():
    with isolated_app(multi_camera=True) as app:
        from flask import url_for
        from indi_allsky.flask.navigation_redirects import NAVIGATION_GROUPS
        source = ast.parse((Path(__file__).resolve().parents[1]/'indi_allsky/flask/classic_views.py').read_text())
        legacy = {node.args[0].value for node in ast.walk(source)
                  if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
                  and node.func.attr == 'add_url_rule'}
        paths = [path for group in NAVIGATION_GROUPS.values() for path in group]
        assert len(paths) == len(set(paths)) == 56 and set(paths) == legacy
        query = 'camera_id=2&profile_id=test-profile-2&timestamp=1700000000&tag=a&tag=b&_external=1&_scheme=https&next=https%3A%2F%2Fexample.invalid'
        for client in (login_client(app, 1), login_client(app, 2), app.test_client()):
            for target, group in NAVIGATION_GROUPS.items():
                with app.test_request_context():
                    expected = url_for('indi_allsky.' + target)
                for path in group:
                    with patch.object(app.jinja_env, 'get_template', side_effect=AssertionError('Navigation redirect rendered a template')):
                        response = client.get('/indi-allsky' + path + '?' + query)
                        head = client.head('/indi-allsky' + path + '?' + query)
                    assert response.status_code == head.status_code == 302, (path, response.status_code)
                    location = urlsplit(response.location)
                    assert location.path == expected and not location.netloc and not location.scheme
                    assert parse_qsl(location.query) == parse_qsl(query)
                    assert head.location == response.location and not head.data
        client = login_client(app, 1)
        for path in ('/user', '/config', '/users', '/loopraw'):
            response = client.get('/indi-allsky' + path + '?camera_id=2&profile_id=test-profile-2', follow_redirects=True)
            assert response.status_code == 200, path
            assert response.request.args['camera_id'] == '2'
            assert response.request.args['profile_id'] == 'test-profile-2'
        anonymous = app.test_client().get('/indi-allsky/user', follow_redirects=True)
        assert '/login' in anonymous.request.path
        assert client.post('/indi-allsky/config').status_code in (400, 405)
        rules = {rule.rule: rule.endpoint for rule in app.url_map.iter_rules()}
        for path in ('/indi-allsky/js/loopraw', '/indi-allsky/ajax/config', '/indi-allsky/latestimage', '/indi-allsky/config/download'):
            assert path in rules and 'hybrid_navigation_' not in rules[path]
        assert client.get('/indi-allsky/no-such-legacy-page').status_code == 404
    print('56 navigation aliases, three roles, GET/HEAD, scope/query preservation, final page auth, and independent public APIs PASS')


if __name__ == '__main__':
    run()
