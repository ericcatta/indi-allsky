#!/usr/bin/env python3
"""Hybrid AWB sync respects the destination camera's real capabilities."""
from copy import deepcopy
import re
from hybrid_runtime_fixture import isolated_app, login_client


def run():
    with isolated_app(multi_camera=True) as app:
        from indi_allsky.flask import db
        from indi_allsky.flask.models import IndiAllSkyDbConfigTable as Config, IndiAllSkyDbTaskQueueTable as Task
        with app.app_context():
            row = db.session.get(Config, 1)
            config = deepcopy(row.data)
            config['MULTI_CAMERA']['profiles'][0]['camera_interface'] = 'libcamera_imx708'
            row.data = config
            db.session.commit()
        admin = login_client(app, 1)
        reader = login_client(app, 2)
        url = '/indi-allsky/modern-admin/settings/cameras?camera_id=1&profile_id=test-profile-1'

        def snapshot():
            with app.app_context():
                row = Config.query.order_by(Config.id.desc()).first()
                return row.id, deepcopy(row.data)

        def submit(client, action='hybrid_controller', mode='capture_driver', sync=True):
            page = client.get(url)
            token = re.search(r'name="csrf_token" value="([^"]+)"', page.text)[1]
            data = dict(csrf_token=token, profile_id='test-profile-1', modern_admin_action=action,
                        processing_mode='hybrid', awb_apply_mode=mode)
            if sync:
                data['modern_admin_save_sync'] = 'hybrid'
            return client.post(url, data=data)

        before = snapshot()
        rejected = submit(admin)
        assert snapshot() == before, 'Save & Sync copied unsupported capture-driver AWB to INDI'
        assert 'target camera' in rejected.text and 'No config was saved' in rejected.text
        submit(reader, mode='postprocess_rgb')
        assert snapshot() == before, 'Ordinary user changed profiles'
        assert admin.post(url, data={'modern_admin_action':'hybrid_sync'}).status_code == 400

        # Capture-side application is valid for the source when saving alone.
        submit(admin, sync=False)
        source_saved = snapshot()
        assert source_saved[0] == before[0] + 1
        assert source_saved[1]['MULTI_CAMERA']['profiles'][0]['hybrid']['awb']['apply_mode'] == 'capture_driver'
        rejected = submit(admin, action='hybrid_sync', sync=False)
        assert snapshot() == source_saved, 'Standalone sync bypassed destination validation'
        assert 'target camera' in rejected.text

        accepted = submit(admin, mode='postprocess_rgb')
        after = snapshot()
        assert 'synced to test-profile-2' in accepted.text
        assert after[0] == source_saved[0] + 1
        assert {k:v for k,v in after[1].items() if k != 'MULTI_CAMERA'} == {k:v for k,v in before[1].items() if k != 'MULTI_CAMERA'}
        for old, new in zip(before[1]['MULTI_CAMERA']['profiles'], after[1]['MULTI_CAMERA']['profiles']):
            assert {k:v for k,v in new.items() if k not in ('processing_mode','awb','hybrid')} == old
            assert new['processing_mode'] == 'hybrid'
            assert new['awb']['apply_mode'] == new['hybrid']['awb']['apply_mode'] == 'postprocess_rgb'
        # A second libcamera destination must still accept capture-side AWB.
        with app.app_context():
            row = Config.query.order_by(Config.id.desc()).first()
            compatible = deepcopy(row.data)
            compatible['MULTI_CAMERA']['profiles'][1]['camera_interface'] = 'libcamera_imx708'
            row.data = compatible
            db.session.commit()
        compatible_before = snapshot()
        accepted = submit(admin)
        compatible_after = snapshot()
        assert compatible_after[0] == compatible_before[0] + 1
        assert 'synced to test-profile-2' in accepted.text
        for profile in compatible_after[1]['MULTI_CAMERA']['profiles']:
            assert profile['hybrid']['awb']['apply_mode'] == 'capture_driver'
        with app.app_context():
            assert Task.query.count() == 0
        print('Hybrid profile sync: target capability rejection is atomic for both endpoints; supported copy preserves identities, acquisition, other domains, roles and CSRF: PASS')


if __name__ == '__main__':
    run()
