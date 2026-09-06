#!/usr/bin/env python3
"""Network command admission with real Flask/CSRF and isolated effect adapters."""
import argparse
import re
from unittest.mock import Mock, patch
from hybrid_runtime_fixture import isolated_app, login_client


def run(runtime_config):
    with isolated_app(runtime_config) as app:
        from indi_allsky.network_commands import CONNECTION_COMMANDS
        import dbus
        endpoint='/indi-allsky/ajax/network'
        admin=login_client(app,1);ordinary=login_client(app,2)
        token=re.search(r'name="csrf_token"[^>]*value="([^"]+)"',admin.get('/indi-allsky/modern-admin/account').text)[1]
        headers={'X-CSRFToken':token}
        effects=Mock()
        methods={value[0] for value in CONNECTION_COMMANDS.values()}|{'scanAPs','connectAP','createHotspot'}
        for method in methods:getattr(effects,method).return_value={'success-message':'Test effect'}
        with patch('indi_allsky.network_manager_effects.NetworkManagerEffects',return_value=effects) as factory:
            for payload in ([],None,{}, {'COMMAND':'activate'}, {'COMMAND':'createhotspot','INTERFACE':'wlan0','SSID':'Test','BAND':'bg','PSK':'test-only-password','NOSECURITY':'false'}):
                response=admin.post(endpoint,json=payload,headers=headers)
                assert response.status_code==400 and response.json['failure-message'],response.text
            factory.assert_not_called()
            for command,(method,kwargs) in CONNECTION_COMMANDS.items():
                response=admin.post(endpoint,json={'COMMAND':command,'CONNECTION':'test-uuid'},headers=headers)
                assert response.status_code==200,response.text
                getattr(effects,method).assert_called_with('test-uuid',**kwargs)
            payload={'COMMAND':'createhotspot','INTERFACE':'wlan0','SSID':'Test','BAND':'bg','PSK':'test-only-password','NOSECURITY':False}
            assert admin.post(endpoint,json=payload,headers=headers).status_code==200
            effects.createHotspot.assert_called_once_with('wlan0','Test','bg','test-only-password',nosecurity=False)
            factory.reset_mock()
            assert admin.post(endpoint,json=payload).status_code==400
            user_token=re.search(r'name="csrf_token"[^>]*value="([^"]+)"',ordinary.get('/indi-allsky/modern-admin/account').text)[1]
            assert ordinary.post(endpoint,json=payload,headers={'X-CSRFToken':user_token}).status_code==400
            factory.assert_not_called()
            effects.createHotspot.side_effect=dbus.exceptions.DBusException('private details')
            response=admin.post(endpoint,json=payload,headers=headers)
            assert response.status_code==503 and 'private details' not in response.text
        print('Network endpoint: required inputs, hotspot security, command dispatch, roles/CSRF and provider failure: PASS')

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--runtime-config',default='/etc/indi-allsky/flask.json')
    run(parser.parse_args().runtime_config)
