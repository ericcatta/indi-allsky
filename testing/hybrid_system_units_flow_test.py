#!/usr/bin/env python3
"""System controls retain authorization, exact unit effects and timer semantics."""
import ast
import re
from pathlib import Path
from unittest.mock import patch
from hybrid_runtime_fixture import isolated_app, login_client


def run():
    with isolated_app() as app:
        from indi_allsky.flask.views import AjaxSystemInfoView
        from indi_allsky.modern_admin_system_units import ModernAdminSystemUnits
        assert not app.config['HYBRID_ENABLE_CLASSIC_UI']
        admin, ordinary = login_client(app, 1), login_client(app, 2)
        def headers(client):
            page = client.get('/indi-allsky/modern-admin/account')
            return {'X-CSRFToken': re.search(r'name="csrf_token"[^>]*value="([^"]+)"', page.text)[1]}
        auth, denied = headers(admin), headers(ordinary)
        endpoint = '/indi-allsky/ajax/system'
        methods = {'start': 'startSystemdUnit', 'stop': 'stopSystemdUnit',
                   'enable': 'enableSystemdUnit', 'disable': 'disableSystemdUnit'}
        for key, label, _, commands in ModernAdminSystemUnits.specs:
            for command in commands:
                payload = dict(CAMERA_ID=1, SERVICE_HIDDEN=app.config[key], COMMAND_HIDDEN=command)
                with patch.object(AjaxSystemInfoView, methods[command], return_value='job/1') as effect:
                    assert admin.post(endpoint, json=payload).status_code == 400
                    assert ordinary.post(endpoint, json=payload, headers=denied).status_code == 400
                    assert app.test_client().post(endpoint, json=payload).status_code in (302, 400)
                    effect.assert_not_called()
                    response = admin.post(endpoint, json=payload, headers=auth)
                    assert response.status_code == 200, response.text
                    assert response.json == {'success-message': 'Job submitted'}
                    effect.assert_called_once_with(app.config[key])
                    effect.reset_mock()
                    for invalid in ('restart', 'invalid', *set(methods).difference(commands)):
                        response = admin.post(endpoint, json=dict(payload, COMMAND_HIDDEN=invalid), headers=auth)
                        assert response.status_code == 400, response.text
                    effect.assert_not_called()
                    effect.side_effect = RuntimeError('private details')
                    response = admin.post(endpoint, json=payload, headers=auth)
                    assert response.status_code == 503 and 'private details' not in response.text
        policy = ModernAdminSystemUnits(app.config)
        assert policy.run('arbitrary.service', 'start', authorized=True, effects={})[1] == 400
        assert policy.run(app.config['INDISERVER_SERVICE_NAME'], 'start', authorized=False, effects={})[1] == 400
        for client, writable in ((admin, True), (ordinary, False)):
            response = client.get('/indi-allsky/modern-admin/system/info?camera_id=1&profile_id=imx708-wide')
            assert response.status_code == 200, response.text
            controls = response.text.split('id="system-units"', 1)[1].split('<details>', 1)[0]
            assert controls.count('class="system-unit-form"') == 4
            assert ('<fieldset disabled>' in controls) != writable
            assert 'Refresh service state' in response.text and 'device-wide change' in controls
        # Execute the actual shared timer methods against a recording D-Bus fake:
        # enable/disable must reload definitions, never start or stop a timer.
        tree = ast.parse((Path(__file__).resolve().parents[1] / 'indi_allsky/flask/base_views.py').read_text())
        cls = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == 'BaseView')
        class Bus:
            def get_object(self, *args): return self
        class Dbus:
            SessionBus = Bus
            @staticmethod
            def Interface(*args): return manager
        class Manager:
            def __getattr__(self, name):
                def call(*args): calls.append((name, args)); return 'receipt'
                return call
        manager = Manager()
        for method, expected in [('enableSystemdUnit', [('EnableUnitFiles', (['test.timer'], False, True)), ('Reload', ())]),
                                 ('disableSystemdUnit', [('DisableUnitFiles', (['test.timer'], False)), ('Reload', ())])]:
            node = next(n for n in cls.body if isinstance(n, ast.FunctionDef) and n.name == method)
            namespace = {'dbus': Dbus}; calls = []
            exec(compile(ast.Module(body=[node], type_ignores=[]), '<shared timer>', 'exec'), namespace)
            assert namespace[method](None, 'test.timer') == 'receipt'
            assert calls == expected
        print('System units: Classic disabled, roles/CSRF, seven actions, exact units, invalid commands, failed effects, UI and shared timer semantics: PASS')

if __name__ == '__main__': run()
