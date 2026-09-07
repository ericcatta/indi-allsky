#!/usr/bin/env python3
"""Camera settings describe saved processing behavior without claiming live state."""
from copy import deepcopy
from hybrid_runtime_fixture import isolated_app, login_client
from hybrid_settings_flow_test import BrowserValues


def run():
    with isolated_app(multi_camera=True) as app:
        from indi_allsky.flask import db
        from indi_allsky.flask.models import IndiAllSkyDbConfigTable, IndiAllSkyDbTaskQueueTable
        clients = [login_client(app, uid) for uid in (1, 2)]
        cases = [
            ('classic', 'auto', 'Classic white balance'),
            ('hybrid', 'auto', 'Apply via post-process RGB'),
            ('hybrid', 'disabled', 'Measurement only · corrections disabled'),
            ('hybrid', 'capture_driver', 'Corrections unavailable for this interface'),
        ]
        for mode, apply, expected in cases:
            with app.app_context():
                row = db.session.get(IndiAllSkyDbConfigTable, 1)
                config = deepcopy(row.data)
                for profile in config['MULTI_CAMERA']['profiles']:
                    profile['processing_mode'] = mode
                    profile['hybrid'] = {'awb': {'apply_mode': apply}}
                row.data = config
                db.session.commit()
            for client in clients:
                for cid in (1, 2):
                    response = client.get('/indi-allsky/modern-admin/settings/cameras', query_string={
                        'profile_id': 'test-profile-' + str(cid), 'camera_id': cid})
                    assert response.status_code == 200
                    assert expected in response.text, (mode, apply, expected)
                    assert 'Selected processing mode' in response.text
                    assert 'not confirmation of the running service state' in response.text
                    assert 'Future per-camera controller' not in response.text
                    assert 'opt-in placeholder' not in response.text
                    values = BrowserValues(response.text).values
                    assert values['camera-hybrid-processing-mode'] == mode
                    assert values['camera-hybrid-awb-apply-mode'] == apply
            with app.app_context():
                assert db.session.get(IndiAllSkyDbConfigTable, 1).data == config
                assert IndiAllSkyDbConfigTable.query.count() == 1
                assert IndiAllSkyDbTaskQueueTable.query.count() == 0
        print('Camera processing status: both roles/profiles, saved mode, enabled/disabled/unsupported AWB, unchanged config: PASS')


if __name__ == '__main__':
    run()
