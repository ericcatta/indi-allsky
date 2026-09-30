#!/usr/bin/env python3
"""Non-object bodies cannot enter legacy JSON handlers or produce effects."""
from copy import deepcopy
from unittest.mock import patch
from hybrid_runtime_fixture import isolated_app, login_client
from hybrid_account_input_test import csrf

ROUTES = ('settime', 'settimezone', 'imageviewer', 'fitsimageviewer', 'gallery',
          'videoviewer', 'minivideoviewer', 'system', 'indiserver', 'notification',
          'selectcamera', 'exclude', 'uploadyoutube')


def run():
    with isolated_app(multi_camera=True) as app:
        from indi_allsky.flask import models
        with app.app_context():
            original_config = deepcopy(models.IndiAllSkyDbConfigTable.query.one().data)
        failures = []
        for uid in (1, 2):
            client = login_client(app, uid)
            headers = {'X-CSRFToken': csrf(client, '/indi-allsky/modern-admin/account')}
            with client.session_transaction() as session:
                session['camera_id'] = 2
            with patch('subprocess.Popen') as process:
                for route in ROUTES:
                    url = '/indi-allsky/ajax/' + route
                    for body in ('null', '[]', '[1]', 'true', '12', '"text"', '{bad json'):
                        try:
                            response = client.post(url, data=body, content_type='application/json', headers=headers)
                            if response.status_code != 400 or not response.is_json:
                                failures.append((uid, route, body, response.status_code))
                        except Exception as error:
                            failures.append((uid, route, body, type(error).__name__))
                    response = client.post(url, data='not json', content_type='text/plain', headers=headers)
                    assert response.status_code == 400 and response.is_json, (uid, route, response.status_code)
                    assert client.post(url, json=[1]).status_code == 400  # CSRF
                process.assert_not_called()
            with client.session_transaction() as session:
                assert session['camera_id'] == 2
        # Anonymous notification polling keeps its existing empty response.
        anonymous = app.test_client()
        token = csrf(anonymous, '/indi-allsky/login')
        response = anonymous.post('/indi-allsky/ajax/notification', json=[1], headers={'X-CSRFToken': token})
        assert response.status_code == 200 and response.json == {'id': 0}
        for route in ('settime', 'settimezone', 'fitsimageviewer', 'system', 'indiserver', 'exclude', 'uploadyoutube'):
            response = anonymous.post('/indi-allsky/ajax/' + route, json=[1], headers={'X-CSRFToken': token})
            assert response.status_code == 302 and '/login' in response.location, route
        with app.app_context():
            assert models.IndiAllSkyDbConfigTable.query.count() == 1
            assert models.IndiAllSkyDbConfigTable.query.one().data == original_config
            assert models.IndiAllSkyDbTaskQueueTable.query.count() == 0
        assert not failures, failures
    print('13 AJAX JSON contracts: two roles, malformed bodies, CSRF, unchanged camera/config/task state, anonymous compatibility: PASS')


if __name__ == '__main__':
    run()
