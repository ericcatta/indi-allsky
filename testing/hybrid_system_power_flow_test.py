#!/usr/bin/env python3
"""Shutdown network policy and login1 effects without touching real hardware."""
import re
from unittest.mock import patch
from hybrid_runtime_fixture import isolated_app, login_client


def run():
    with isolated_app() as app:
        from indi_allsky.flask.views import AjaxSystemInfoView, ModernAdminSystemInfoView
        from indi_allsky.modern_safe_action import ModernAdminPowerOffCommandBoundary
        from indi_allsky.modern_admin_runtime_effects import ModernAdminLogin1PowerEffects
        assert not app.config['HYBRID_ENABLE_CLASSIC_UI']
        admin, ordinary, anonymous = login_client(app, 1), login_client(app, 2), app.test_client()
        def headers(client, page='/indi-allsky/modern-admin/account'):
            return {'X-CSRFToken': re.search(r'name="csrf_token"[^>]*value="([^"]+)"', client.get(page).text)[1]}
        auth, denied, anon = headers(admin), headers(ordinary), headers(anonymous, '/indi-allsky/login')
        payload = dict(CAMERA_ID=1, SERVICE_HIDDEN='system', COMMAND_HIDDEN='poweroff')
        endpoint = '/indi-allsky/ajax/system'
        with patch.object(AjaxSystemInfoView, 'poweroffSystemd', return_value='receipt') as effect, \
             patch.object(AjaxSystemInfoView, 'verify_admin_network', return_value=False) as network:
            assert admin.post(endpoint, json=payload).status_code == 400
            assert ordinary.post(endpoint, json=payload, headers=denied).status_code == 400
            assert anonymous.post(endpoint, json=payload, headers=anon).status_code == 302
            effect.assert_not_called(); network.assert_not_called()
            response = admin.post(endpoint, json=payload, headers=auth)
            assert response.status_code == 400 and 'admin network' in response.text
            effect.assert_not_called()
            network.return_value = True
            for camera_id in (1, 2):
                response = admin.post(endpoint, json=dict(payload, CAMERA_ID=camera_id), headers=auth)
                assert response.status_code == 200 and response.json == {'success-message':'Job submitted'}
            assert effect.call_count == 2
            effect.side_effect = RuntimeError('private login1 details')
            response = admin.post(endpoint, json=payload, headers=auth)
            assert response.status_code == 503 and 'private login1' not in response.text
        calls = []
        boundary = ModernAdminPowerOffCommandBoundary(effect_adapter=lambda command: calls.append(command))
        for authorized, network in ((False, False), (False, True), (True, False)):
            assert not boundary.run('poweroff', authorized=authorized, admin_network=network).allowed
        assert not boundary.run('reboot', authorized=True, admin_network=True).allowed
        assert not calls
        assert boundary.run('poweroff', authorized=True, admin_network=True).allowed
        assert calls == ['poweroff']
        for client, role in ((admin, True), (ordinary, False)):
            for allowed_network in (True, False):
                with patch.object(ModernAdminSystemInfoView, 'verify_admin_network', return_value=allowed_network):
                    response = client.get('/indi-allsky/modern-admin/system/info')
                    assert response.status_code == 200
                    form = response.text.split('class="system-poweroff-form"', 1)[1].split('</form>', 1)[0]
                    assert ('<fieldset disabled>' in form) == (not (role and allowed_network))
                    assert 'value="poweroff"' in form and 'turn this device on again' in form
        calls = []
        class Manager:
            def Reboot(self, interactive): calls.append(('Reboot', interactive)); return 'reboot-receipt'
            def PowerOff(self, interactive): calls.append(('PowerOff', interactive)); return 'shutdown-receipt'
        class Bus:
            def get_object(self, service, path):
                assert (service, path) == ('org.freedesktop.login1', '/org/freedesktop/login1')
                return 'object'
        class Dbus:
            SystemBus = Bus
            @staticmethod
            def Interface(obj, interface):
                assert (obj, interface) == ('object', 'org.freedesktop.login1.Manager')
                return Manager()
        effects = ModernAdminLogin1PowerEffects(Dbus)
        assert effects.reboot() == 'reboot-receipt'
        assert effects.poweroff() == 'shutdown-receipt'
        assert calls == [('Reboot', False), ('PowerOff', False)]
        print('Power controls: Classic disabled, admin/ordinary/anonymous, CSRF, admin network, both camera contexts, unknown effects, UI gates and exact login1 calls: PASS')

if __name__ == '__main__': run()
