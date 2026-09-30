#!/usr/bin/env python3
"""Malformed action requests fail before planning, enqueue or hardware access."""
from unittest.mock import patch
from hybrid_runtime_fixture import isolated_app, login_client
from hybrid_account_input_test import csrf


def run():
    with isolated_app(multi_camera=True) as app:
        from indi_allsky.flask import models
        admin = login_client(app, 1)
        headers = {'X-CSRFToken': csrf(admin, '/indi-allsky/modern-admin/account')}
        base = '/indi-allsky/modern-admin/'
        with patch('indi_allsky.flask.views.detect_modern_admin_usb_camera_driver') as detect, \
             patch('indi_allsky.flask.views.ModernAdminTaskEnqueueEffectAdapter') as enqueue, \
             patch('subprocess.Popen') as process, \
             patch('indi_allsky.flask.views.detect_modern_admin_libcamera_cameras') as libcamera:
            with app.app_context():
                before = models.IndiAllSkyDbTaskQueueTable.query.count()
            for route in ('safe-action/dry-run', 'capture/abort-exposure', 'cameras/start-indi', 'cameras/detect-indi'):
                for body in ('null', '[]', '[1]', 'true', '12', '"text"', '{bad json'):
                    result = admin.post(base + route, data=body, content_type='application/json', headers=headers)
                    assert result.status_code == 400 and result.is_json, (route, body, result.status_code)
                result = admin.post(base + route, data='text', content_type='text/plain', headers=headers)
                assert result.status_code == 400 and result.is_json
                assert admin.post(base + route, json={}).status_code == 400  # CSRF still enforced
            for field, values in (('indi_server', (None, True, 12, [], {})),
                                  ('indi_port', (None, [], {}, 'bad', 0, 65536)),
                                  ('driver_hint', (None, True, 12, [], {}))):
                for value in values:
                    result = admin.post(base + 'cameras/start-indi', json={field: value}, headers=headers)
                    assert result.status_code == 400 and result.is_json, (field, value)
            for value in ([1], {'bad': 1}):
                result = admin.post(base + 'safe-action/dry-run', json={'action_id': value}, headers=headers)
                assert result.status_code == 400 and result.is_json
            libcamera.assert_not_called()
            detect.assert_not_called()
            enqueue.assert_not_called()
            process.assert_not_called()
            with app.app_context():
                assert models.IndiAllSkyDbTaskQueueTable.query.count() == before
        # Valid abort requests enqueue the camera-specific command in the disposable DB.
        for camera in (1, 2):
            result = admin.post(base + 'capture/abort-exposure', headers=headers, json={
                'camera_id': camera, 'profile_id': f'test-profile-{camera}'})
            assert result.status_code == 200, result.text
            with app.app_context():
                task = models.IndiAllSkyDbTaskQueueTable.query.filter_by(id=result.json['task-id']).one()
                assert task.data == {'action': 'abortExposure', 'camera_id': camera,
                                     'profile_id': f'test-profile-{camera}'}, task.data
        result = admin.post(base + 'safe-action/dry-run', headers=headers, json={'action_id': 'unknown'})
        assert result.status_code == 400 and result.json['status'] == 'not_found'
        with patch('indi_allsky.flask.views.detect_modern_admin_usb_camera_driver', return_value={'driver': ''}), \
             patch('subprocess.Popen') as process:
            result = admin.post(base + 'cameras/start-indi', headers=headers, json={'indi_port': '7624'})
            assert result.status_code == 400 and 'No USB camera driver' in result.json['error']
            process.assert_not_called()
        ordinary = login_client(app, 2)
        user_headers = {'X-CSRFToken': csrf(ordinary, '/indi-allsky/modern-admin/account')}
        for route in ('capture/abort-exposure', 'cameras/start-indi', 'cameras/detect-indi'):
            assert ordinary.post(base + route, json=[1], headers=user_headers).status_code == 403
    print('Action HTTP validation, CSRF, role precedence and no task/hardware effects: PASS')


if __name__ == '__main__':
    run()
