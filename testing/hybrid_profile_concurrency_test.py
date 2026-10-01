#!/usr/bin/env python3
"""Concurrent profile edits must not silently replace another committed edit."""
import multiprocessing
import re
import time
from unittest.mock import patch

from hybrid_runtime_fixture import isolated_app, login_client


def run():
    with isolated_app(multi_camera=True, file_database=True) as app:
        from indi_allsky.flask import db
        from indi_allsky.flask.models import IndiAllSkyDbConfigTable as Config
        from indi_allsky.flask.views import ModernAdminSettingsInventoryView

        client = login_client(app, 1)
        url = '/indi-allsky/modern-admin/settings/cameras'
        page = client.get(url + '?camera_id=1&profile_id=test-profile-1')
        token = re.search(r'name="csrf_token" value="([^"]+)"', page.text)[1]
        ctx = multiprocessing.get_context('fork')
        barrier, results = ctx.Barrier(2), ctx.Queue()
        save = ModernAdminSettingsInventoryView.save_settings_config_revision

        def submit(camera_id):
            with app.app_context():
                db.session.remove()
                db.engine.dispose()

            def overlapping_save(view, *args, **kwargs):
                # Both views have read and modified revision 1 before either saves.
                barrier.wait(timeout=15)
                if camera_id == 2:
                    time.sleep(1)
                return save(view, *args, **kwargs)

            with patch.object(ModernAdminSettingsInventoryView, 'save_settings_config_revision', overlapping_save):
                response = client.post(url + '?camera_id=%d&profile_id=test-profile-%d' % (camera_id, camera_id),
                    data=dict(csrf_token=token, profile_id='test-profile-%d' % camera_id,
                              modern_admin_action='hybrid_controller', processing_mode='hybrid',
                              awb_apply_mode='postprocess_rgb'))
            results.put((camera_id, response.status_code, 'Configuration changed' in response.text))

        processes = [ctx.Process(target=submit, args=(cid,)) for cid in (1, 2)]
        try:
            for process in processes:
                process.start()
            for process in processes:
                process.join(timeout=30)
            assert all(not p.is_alive() and p.exitcode == 0 for p in processes)
            responses = sorted(results.get(timeout=2) for _ in processes)
            with app.app_context():
                db.session.remove()
                rows = Config.query.order_by(Config.id).all()
                assert len(rows) == 2, ('Concurrent profile save silently accepted a stale config', len(rows), responses)
                profiles = rows[-1].data['MULTI_CAMERA']['profiles']
                assert profiles[0]['processing_mode'] == 'hybrid'
                assert profiles[1] == rows[0].data['MULTI_CAMERA']['profiles'][1]
            assert responses == [(1, 200, False), (2, 200, True)], responses
            # A new request can read the new revision and preserve both edits.
            response = client.post(url + '?camera_id=2&profile_id=test-profile-2',
                data=dict(csrf_token=token, profile_id='test-profile-2',
                          modern_admin_action='hybrid_controller', processing_mode='hybrid',
                          awb_apply_mode='postprocess_rgb'))
            assert response.status_code == 200 and 'Configuration changed' not in response.text
            with app.app_context():
                db.session.remove()
                rows = Config.query.order_by(Config.id).all()
                assert len(rows) == 3
                assert all(p['processing_mode'] == 'hybrid' for p in rows[-1].data['MULTI_CAMERA']['profiles'])
                assert {k:v for k,v in rows[-1].data.items() if k != 'MULTI_CAMERA'} == {k:v for k,v in rows[0].data.items() if k != 'MULTI_CAMERA'}
            print('Concurrent profile save: first edit retained, stale competitor rejected; fresh retry preserves both edits and global config: PASS')
        finally:
            for process in processes:
                if process.is_alive():
                    process.terminate()
                    process.join()


if __name__ == '__main__':
    run()
