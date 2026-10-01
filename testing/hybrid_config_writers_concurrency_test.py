#!/usr/bin/env python3
"""Competing HTTP configuration writers must preserve a committed profile edit."""
from contextlib import ExitStack
import ast
from pathlib import Path
from copy import deepcopy
import io
import json
import multiprocessing
import re
import subprocess
import sys
from unittest.mock import patch
from hybrid_runtime_fixture import isolated_app, login_client
from hybrid_settings_flow_test import payload_from_page

CASES = ('timelapse', 'storage', 'mode', 'camera', 'full', 'restore')


def run(case):
    with isolated_app(multi_camera=True, file_database=True) as app:
        from indi_allsky.flask import db
        from indi_allsky.flask.models import IndiAllSkyDbConfigTable as Config, IndiAllSkyDbCameraTable as Camera, IndiAllSkyDbTaskQueueTable as Task
        from indi_allsky.modern_admin_settings_runtime import ModernAdminSettingsRuntimeService as Runtime, ModernAdminSettingsRestoreService as Restore
        with app.app_context():
            row = db.session.get(Config, 1)
            original = deepcopy(row.data)
            original.update(MULTI_CAMERA_CAPTURE_ENABLE=False, EXPOSURE_PERIOD_DAY=15, EXPOSURE_PERIOD=45)
            original['MULTI_CAMERA']['profiles'][0]['camera_interface'] = 'libcamera_imx708'
            row.data = original
            camera = db.session.get(Camera, 1)
            camera.name, camera.driver = 'libcamera_imx708', 'rpicam-still'
            db.session.commit()
        client = login_client(app, 1)
        with client.session_transaction() as session:
            session['camera_id'] = 2
        payload, token = payload_from_page(client.get('/indi-allsky/modern-admin/settings/full').text)
        payload.update(RELOAD_ON_SAVE=True, CONFIG_NOTE='Concurrent full settings', OWNER='Competing edit')
        ctx = multiprocessing.get_context('fork')
        barrier, first_done, results = ctx.Barrier(2), ctx.Event(), ctx.Queue()
        methods = [(Runtime, 'save_config_revision'), (Runtime, 'save_full_config'), (Restore, 'restore_config')]

        def submit(primary):
            with app.app_context():
                db.session.remove()
                db.engine.dispose()
            def gate(method):
                def wrapped(*args, **kwargs):
                    barrier.wait(timeout=20)
                    if not primary:
                        assert first_done.wait(20), 'First request did not finish'
                    return method(*args, **kwargs)
                return wrapped
            try:
                with ExitStack() as stack:
                    for cls, name in methods:
                        stack.enter_context(patch.object(cls, name, gate(getattr(cls, name))))
                    data = dict(csrf_token=token)
                    if primary:
                        response = client.post('/indi-allsky/modern-admin/settings/cameras?camera_id=1&profile_id=test-profile-1',
                            data=dict(data, profile_id='test-profile-1', modern_admin_action='hybrid_controller', processing_mode='hybrid', awb_apply_mode='postprocess_rgb'))
                    elif case == 'timelapse':
                        response = client.post('/indi-allsky/modern-admin/settings/timelapse', data=dict(data, revision='1', window='9', deflicker='on'))
                    elif case == 'storage':
                        response = client.post('/indi-allsky/modern-admin/settings/storage-protection', data=dict(data, revision='1', minimum='5', target='8', days='4', enabled='on'))
                    elif case in ('mode', 'camera'):
                        response = client.post('/indi-allsky/modern-admin/cameras', data=dict(data, modern_admin_action='multi_camera_enable' if case == 'mode' else 'switch', camera_id='1'))
                    elif case == 'full':
                        response = client.post('/indi-allsky/ajax/config', json=payload, headers={'X-CSRFToken':token})
                    else:
                        response = client.post('/indi-allsky/ajax/config/restore', data=dict(data, CONFIG_UPLOAD=(io.BytesIO(json.dumps(original).encode()), 'fixture.json'), RESET_KEYS='yes', FLUSH_CONFIGS='yes'), headers={'X-CSRFToken':token})
                results.put((primary, response.status_code, 'Configuration changed' in response.text))
            finally:
                if primary:
                    first_done.set()
        processes = [ctx.Process(target=submit, args=(primary,)) for primary in (True, False)]
        try:
            for process in processes:
                process.start()
            for process in processes:
                process.join(timeout=45)
            assert all(not p.is_alive() and p.exitcode == 0 for p in processes), case
            responses = sorted(results.get(timeout=2) for _ in processes)
            with app.app_context():
                db.session.remove()
                rows = Config.query.order_by(Config.id).all()
                assert len(rows) == 2, (case, 'stale whole-config write accepted', len(rows), responses)
                assert rows[-1].data['MULTI_CAMERA']['profiles'][0]['processing_mode'] == 'hybrid'
                assert {k:v for k,v in rows[-1].data.items() if k != 'MULTI_CAMERA'} == {k:v for k,v in original.items() if k != 'MULTI_CAMERA'}
                assert Task.query.count() == 0
            expected_status = 409 if case in ('timelapse', 'storage') else 400 if case in ('full', 'restore') else 200
            assert responses == [(False, expected_status, True), (True, 200, False)], (case, responses)
            print(case + ': committed profile retained, stale writer rejected, no effect queued: PASS')
        finally:
            for process in processes:
                if process.is_alive():
                    process.terminate()
                    process.join()


if __name__ == '__main__':
    if len(sys.argv) > 1:
        run(sys.argv[1])
    else:
        # Future HTTP writers must carry the request's revision into persistence.
        root = Path(__file__).resolve().parents[1] / 'indi_allsky' / 'flask'
        for path in root.rglob('*.py'):
            for node in ast.walk(ast.parse(path.read_text())):
                if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr in ('save_config_revision', 'save_full_config', 'restore_config'):
                    assert 'expected_config_id' in {kw.arg for kw in node.keywords}, (path.name, node.lineno)
        statuses = [subprocess.run([sys.executable, __file__, case]).returncode for case in CASES]
        assert not any(statuses), dict(zip(CASES, statuses))
