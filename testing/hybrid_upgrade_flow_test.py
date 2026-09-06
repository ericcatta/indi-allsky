#!/usr/bin/env python3
"""Existing upgrade API keeps auth/CSRF and fails closed on insufficient space."""
import re
from types import SimpleNamespace
from unittest.mock import patch
from hybrid_runtime_fixture import isolated_app, login_client


def run():
    with isolated_app() as app:
        from indi_allsky.flask.views import AjaxSystemInfoView
        from indi_allsky.modern_safe_action import ModernAdminUpgradeCommandBoundary as Boundary
        endpoint='/indi-allsky/ajax/system'
        payload={'CAMERA_ID':1,'SERVICE_HIDDEN':app.config['UPGRADE_ALLSKY_SERVICE_NAME'],'COMMAND_HIDDEN':'start'}
        admin=login_client(app,1)
        def headers(client):
            token=re.search(r'name="csrf_token"[^>]*value="([^"]+)"',client.get('/indi-allsky/modern-admin/account').text)[1]
            return {'X-CSRFToken':token}
        auth=headers(admin)
        ordinary=login_client(app,2);ordinary_auth=headers(ordinary)
        with patch.object(AjaxSystemInfoView,'startSystemdUnit',return_value='job/42') as effect, \
             patch('indi_allsky.flask.views.psutil.disk_usage') as disk:
            assert admin.post(endpoint,json=payload).status_code==400
            assert ordinary.post(endpoint,json=payload,headers=ordinary_auth).status_code==400
            assert app.test_client().post(endpoint,json=payload).status_code in (302,400)
            effect.assert_not_called();disk.assert_not_called()
            disk.return_value=SimpleNamespace(total=10**12,free=100)
            response=admin.post(endpoint,json=payload,headers=auth)
            assert response.status_code==400,response.text
            assert 'Not enough available space' in response.json['COMMAND_HIDDEN'][0]
            effect.assert_not_called()
            disk.side_effect=PermissionError('private mount')
            response=admin.post(endpoint,json=payload,headers=auth)
            assert response.status_code==503 and 'private mount' not in response.text
            effect.assert_not_called()
            disk.side_effect=None;disk.return_value=SimpleNamespace(total=10**12,free=Boundary.MIN_FREE_BYTES)
            response=admin.post(endpoint,json=payload,headers=auth)
            assert response.status_code==200 and response.json=={'success-message':'Job submitted'},response.text
            effect.assert_called_once_with(app.config['UPGRADE_ALLSKY_SERVICE_NAME'])
            effect.reset_mock()
            for command in ('stop','restart','invalid'):
                response=admin.post(endpoint,json=dict(payload,COMMAND_HIDDEN=command),headers=auth)
                assert response.status_code==400
            effect.assert_not_called()
            effect.side_effect=RuntimeError('private service error')
            response=admin.post(endpoint,json=payload,headers=auth)
            assert response.status_code==503 and 'private service error' not in response.text
        print('Upgrade API: admin/ordinary/anonymous, CSRF, free-space rejection, unreadable disk, command allowlist, exact unit and failed effects: PASS')

if __name__=='__main__':run()
