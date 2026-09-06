#!/usr/bin/env python3
"""Native GPIO must not configure pins on GET; explicit output commands only."""
import argparse
import re
import sys
from types import SimpleNamespace
from unittest.mock import Mock, patch
from hybrid_runtime_fixture import isolated_app, login_client


def run(runtime_config):
    with isolated_app(runtime_config) as app:
        from indi_allsky.flask import db
        from indi_allsky.flask.models import IndiAllSkyDbConfigTable
        from indi_allsky.devices.exceptions import DeviceControlException
        with app.app_context():
            row=db.session.get(IndiAllSkyDbConfigTable,1)
            row.data=dict(row.data,MANUAL_GPIO={'A_CLASSNAME':'rpigpio_gpio_rpigpio','A_PIN_1':'12','A_PIN_2':'13','A_PIN_3':'14'})
            db.session.commit()
        gpio=Mock(BCM=11,OUT=0,IN=1)
        gpio.getmode.return_value=11
        gpio.gpio_function.side_effect=lambda pin:0 if pin in (12,13) else 1
        gpio.input.side_effect=lambda pin:pin==12
        page='/indi-allsky/modern-admin/system/gpio-control'
        endpoint='/indi-allsky/ajax/manual_gpio'
        with patch.dict(sys.modules,{'RPi':SimpleNamespace(GPIO=gpio),'RPi.GPIO':gpio}), patch('indi_allsky.devices.generic.rpigpio_gpio_rpigpio') as factory:
            for uid in (1,2):
                client=login_client(app,uid)
                response=client.get(page)
                assert response.status_code==200
                assert 'Observed state: On' in response.text and 'Observed state: Off' in response.text
                assert 'Unknown / not configured as an output' in response.text
                if uid==2: assert 'Administrator access' in response.text
            factory.assert_not_called();gpio.setup.assert_not_called();gpio.output.assert_not_called();gpio.cleanup.assert_not_called()
            admin=login_client(app,1)
            token=re.search(r'name="csrf_token"[^>]*value="([^"]+)"',admin.get('/indi-allsky/modern-admin/account').text)[1]
            headers={'X-CSRFToken':token}
            for payload in ([],{},None,{'PIN_ID':4,'NEW_PIN_STATE':1},{'PIN_ID':True,'NEW_PIN_STATE':1},{'PIN_ID':1,'NEW_PIN_STATE':'false'},{'PIN_ID':1,'NEW_PIN_STATE':2}):
                response=admin.post(endpoint,json=payload,headers=headers)
                assert response.status_code==400 and response.json['failure-message'],(payload,response.text)
            factory.assert_not_called()
            device=SimpleNamespace(state=None);factory.return_value=device
            with patch('indi_allsky.flask.views.time.sleep'):
                response=admin.post(endpoint,json={'PIN_ID':2,'NEW_PIN_STATE':0},headers=headers)
            assert response.status_code==200 and response.json['pin_name']=='13' and response.json['pin_state'] is False
            assert factory.call_args.kwargs=={'pin_1_name':'13'}
            factory.reset_mock()
            assert admin.post(endpoint,json={'PIN_ID':1,'NEW_PIN_STATE':1}).status_code==400
            ordinary_token=re.search(r'name="csrf_token"[^>]*value="([^"]+)"',client.get('/indi-allsky/modern-admin/account').text)[1]
            assert client.post(endpoint,json={'PIN_ID':1,'NEW_PIN_STATE':1},headers={'X-CSRFToken':ordinary_token}).status_code==400
            factory.assert_not_called()
            factory.side_effect=DeviceControlException('private driver error')
            response=admin.post(endpoint,json={'PIN_ID':1,'NEW_PIN_STATE':1},headers=headers)
            assert response.status_code==503 and 'private driver error' not in response.text
            gpio.input.side_effect=RuntimeError('private read error')
            response=admin.get(page)
            assert 'GPIO state could not be read' in response.text and 'private read error' not in response.text
        assert app.test_client().get(page).status_code==302
        print('Native GPIO: read-only GET, actual read adapter, roles/CSRF, strict commands, configured pin mapping and failures: PASS')

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--runtime-config',default='/etc/indi-allsky/flask.json')
    run(parser.parse_args().runtime_config)
