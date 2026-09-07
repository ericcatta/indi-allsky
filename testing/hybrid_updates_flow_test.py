#!/usr/bin/env python3
"""Native upgrade page and serialized service lifecycle; effects are mocked."""
import re
from types import SimpleNamespace
from unittest.mock import Mock, patch
from hybrid_runtime_fixture import isolated_app, login_client


def run():
    with isolated_app() as app:
        from indi_allsky.upgrade_runtime import UpgradeRuntime, upgrade_lock
        from indi_allsky.modern_safe_action import ModernAdminUpgradeCommandBoundary as Boundary
        unit=app.config['UPGRADE_ALLSKY_SERVICE_NAME']
        props={'LoadState':'loaded','ActiveState':'inactive','SubState':'dead','Job':(0,'/'),
               'ExecMainStartTimestamp':0,'ExecMainExitTimestamp':0,'ExecMainStatus':0,'Result':'success'}
        page='/indi-allsky/modern-admin/updates';endpoint=page+'/start'
        with patch.object(UpgradeRuntime,'properties',return_value=props), patch.object(UpgradeRuntime,'manager') as bus:
            manager=Mock();manager.StartUnit.return_value='job/start';manager.RestartUnit.return_value='job/restart'
            bus.return_value=(None,manager)
            clients=[login_client(app,uid) for uid in (1,2)]
            for index,client in enumerate(clients):
                response=client.get(page)
                assert response.status_code==200,response.text[:500]
                assert 'Upgrade service: Idle' in response.text
                assert 'Classic Fallback' not in response.text and 'not implemented' not in response.text
                if index: assert 'Administrator access is required.' in response.text
            manager.StartUnit.assert_not_called();manager.RestartUnit.assert_not_called()
            def headers(client):
                token=re.search(r'name="csrf_token"[^>]*value="([^"]+)"',client.get('/indi-allsky/modern-admin/account').text)[1]
                return {'X-CSRFToken':token}
            auth=headers(clients[0]);ordinary_auth=headers(clients[1])
            token=UpgradeRuntime(unit).snapshot()['token']
            payload={'backup_confirmed':True,'maintenance_confirmed':True,'observed_token':token}
            admin=clients[0]
            assert admin.post(endpoint,json=payload).status_code==400
            assert clients[1].post(endpoint,json=payload,headers=ordinary_auth).status_code==403
            for bad in ({},[],None,dict(payload,backup_confirmed='true'),dict(payload,maintenance_confirmed=1)):
                assert admin.post(endpoint,json=bad,headers=auth).status_code==400
            assert admin.post(endpoint,json=dict(payload,observed_token='stale'),headers=auth).status_code==409
            with upgrade_lock():
                assert admin.post(endpoint,json=payload,headers=auth).status_code==409
            manager.StartUnit.assert_not_called()
            with patch('indi_allsky.upgrade_runtime.psutil.disk_usage',return_value=SimpleNamespace(free=Boundary.MIN_FREE_BYTES)):
                response=admin.post(endpoint,json=payload,headers=auth)
                assert response.status_code==202 and response.json['job']=='job/start',response.text
                manager.StartUnit.assert_called_once_with(unit,'fail',timeout=10)
                props.update(Job=(23,'/job/23'))
                assert admin.post(endpoint,json=payload,headers=auth).status_code==409
                assert 'Upgrade service: Running' in admin.get(page).text
                props.update(Job=(0,'/'),ActiveState='active',SubState='exited',ExecMainStartTimestamp=1000000,ExecMainExitTimestamp=2000000)
                assert 'Upgrade service: Completed' in admin.get(page).text
                assert admin.post(endpoint,json=payload,headers=auth).status_code==409
                payload['observed_token']=UpgradeRuntime(unit).snapshot()['token']
                assert admin.post(endpoint,json=payload,headers=auth).status_code==202
                manager.RestartUnit.assert_called_once_with(unit,'fail',timeout=10)
                props.update(ActiveState='failed',SubState='failed',Result='exit-code',ExecMainStatus=1)
                assert 'Upgrade service: Failed' in admin.get(page).text
                payload['observed_token']=UpgradeRuntime(unit).snapshot()['token']
                assert admin.post(endpoint,json=payload,headers=auth).status_code==202
                assert manager.StartUnit.call_count==2
            with patch.object(UpgradeRuntime,'properties',side_effect=RuntimeError('private bus details')):
                response=admin.get(page)
                assert 'Upgrade service: Unavailable' in response.text and 'private bus details' not in response.text
                assert admin.post(endpoint,json=payload,headers=auth).status_code==503
        assert app.test_client().get(page).status_code==302
        print('Updates: rendered state, auth/CSRF, strict confirmations, actual cross-request lock, stale state, queued duplicate, oneshot restart, failed retry and unavailable provider: PASS')

if __name__=='__main__':run()
