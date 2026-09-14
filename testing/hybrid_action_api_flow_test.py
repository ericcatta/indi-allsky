#!/usr/bin/env python3
"""Public pause/unpause contracts survive without the optional Classic frontend."""
from unittest.mock import patch
from hybrid_runtime_fixture import isolated_app, PASSWORD


def run():
    with isolated_app(multi_camera=True) as app:
        from indi_allsky.flask import db
        from indi_allsky.flask.actionapi_views import ActionApiBaseView
        from indi_allsky.flask.models import (
            IndiAllSkyDbConfigTable, IndiAllSkyDbTaskQueueTable,
            TaskQueueQueue, TaskQueueState,
        )
        client = app.test_client()
        credentials = {'username': 'test-user-1', 'password': PASSWORD}

        def tasks():
            with app.app_context():
                return [(t.queue, t.state, t.priority, t.data)
                        for t in IndiAllSkyDbTaskQueueTable.query.order_by(IndiAllSkyDbTaskQueueTable.id)]

        def paused(value):
            with app.app_context():
                config = db.session.get(IndiAllSkyDbConfigTable, 1)
                config.data = {**config.data, 'CAPTURE_PAUSE': value}
                db.session.commit()

        # Real Flask dispatch, password verification and database persistence.
        # Only network membership is controlled; no worker/service is invoked.
        with patch.object(ActionApiBaseView, 'verify_admin_network', return_value=True):
            for action, initial, expected in (('pause', False, True), ('unpause', True, False)):
                route = '/indi-allsky/action/' + action
                paused(initial)
                before = tasks()
                assert client.get(route).status_code == 405
                for invalid in ({}, {'username': 'missing', 'password': PASSWORD},
                                {**credentials, 'password': 'incorrect'}):
                    result = client.post(route, json=invalid)
                    assert result.status_code == 400 and result.json == {'error': 'authentication failed'}
                    assert tasks() == before
                result = client.post(route, json={'username': 'test-user-2', 'password': PASSWORD})
                assert result.status_code == 400 and result.json == {'error': 'permission denied'}
                assert tasks() == before
                # API credentials authenticate without a browser session or CSRF token.
                result = client.post(route, json=credentials)
                assert result.status_code == 201 and result.json == {'message': action.capitalize() + ' task created.'}
                assert tasks() == before + [(TaskQueueQueue.MAIN, TaskQueueState.MANUAL, 100,
                                             {'action': 'setpaused', 'pause': expected})]
                paused(expected)
                before = tasks()
                result = client.post(route, json=credentials)
                assert result.status_code == 200 and result.json == {'message': 'Capture is already ' + ('paused' if expected else 'unpaused')}
                assert tasks() == before
        with patch.object(ActionApiBaseView, 'verify_admin_network', return_value=False):
            before = tasks()
            for action in ('pause', 'unpause'):
                result = client.post('/indi-allsky/action/' + action, json=credentials)
                assert result.status_code == 400 and result.json == {'error': 'permission denied'}
                assert tasks() == before
        print('Action API: both public routes, credentials, admin/network authorization, actual queue payload and already-applied state without Classic: PASS')


if __name__ == '__main__':
    run()
