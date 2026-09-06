#!/usr/bin/env python3
"""Focuser admission and release on success/failure without touching hardware."""
import argparse
from unittest.mock import Mock, patch
from hybrid_runtime_fixture import isolated_app, login_client


def run(runtime_config):
    with isolated_app(runtime_config) as app:
        from indi_allsky.flask.views import AjaxFocusControllerView
        from indi_allsky.devices.exceptions import DeviceControlException
        client=login_client(app,1)
        # Flask-WTF uses signed tokens from a rendered form.
        import re
        token=re.search(r'name="csrf_token"[^>]*value="([^"]+)"',client.get('/indi-allsky/modern-admin/account').text)[1]
        headers={'X-CSRFToken':token}
        route='/indi-allsky/ajax/focuscontroller'
        with patch('indi_allsky.focuser.IndiAllSkyFocuserInterface') as factory, patch.object(AjaxFocusControllerView,'verify_admin_network',return_value=True):
            for payload in ([],None,{}, {'DIRECTION':'invalid','STEP_DEGREES':24},
                            {'DIRECTION':'cw'}, {'DIRECTION':'cw','STEP_DEGREES':999}):
                assert client.post(route,json=payload,headers=headers).status_code==400,payload
            factory.assert_not_called()
            device=Mock();device.move.return_value=24;factory.return_value=device
            valid={'DIRECTION':'cw','STEP_DEGREES':24}
            response=client.post(route,json=valid,headers=headers)
            assert response.status_code==200 and response.json=={'steps':24},response.json
            device.move.assert_called_once_with('cw',24);device.deinit.assert_called_once_with()
            for error in (DeviceControlException('private'),OSError('private'),ValueError('private'),SystemError('private')):
                device.reset_mock();device.move.side_effect=error
                response=client.post(route,json=valid,headers=headers)
                assert response.status_code==400 and 'private' not in response.text
                device.deinit.assert_called_once_with()
            device.move.side_effect=None;device.deinit.side_effect=OSError('private')
            response=client.post(route,json=valid,headers=headers)
            assert response.status_code==500 and response.json['steps']==24
            assert 'Movement completed.' in response.text and 'private' not in response.text
            device.move.side_effect=DeviceControlException('private')
            response=client.post(route,json=valid,headers=headers)
            assert response.status_code==400 and len(response.json['focuser_error'])==2
            factory.reset_mock()
            assert client.post(route,json=valid).status_code==400
            with patch.object(AjaxFocusControllerView,'verify_admin_network',return_value=False):
                assert client.post(route,json=valid,headers=headers).status_code==400
            factory.assert_not_called()
            ordinary=login_client(app,2)
            ordinary_token=re.search(r'name="csrf_token"[^>]*value="([^"]+)"',ordinary.get('/indi-allsky/modern-admin/account').text)[1]
            assert ordinary.post(route,json=valid,headers={'X-CSRFToken':ordinary_token}).status_code==400
            factory.assert_not_called()
        print('Hybrid focuser: input validation, CSRF/network, success, movement/release failures and resource cleanup: PASS')

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--runtime-config',default='/etc/indi-allsky/flask.json')
    run(parser.parse_args().runtime_config)
