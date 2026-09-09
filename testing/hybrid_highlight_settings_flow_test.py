#!/usr/bin/env python3
"""Highlight controls persist per profile through real Flask/CSRF and SQLite."""
from copy import deepcopy
import re
from hybrid_runtime_fixture import isolated_app, login_client
from hybrid_settings_flow_test import BrowserValues


def run():
    with isolated_app(multi_camera=True) as app:
        from indi_allsky.flask import db
        from indi_allsky.flask.models import IndiAllSkyDbConfigTable as Config
        from indi_allsky.capture_profiles import derive_capture_profiles, build_profile_config
        with app.app_context():
            row = db.session.get(Config, 1)
            config = deepcopy(row.data)
            config['MULTI_CAMERA_CAPTURE_ENABLE'] = True
            row.data = config
            db.session.commit()
        admin, reader = login_client(app, 1), login_client(app, 2)
        def latest():
            return Config.query.order_by(Config.id.desc()).first()
        for cid, budget in ((1, '.5'), (2, '2')):
            url = '/indi-allsky/modern-admin/settings/cameras?profile_id=test-profile-' + str(cid)
            page = admin.get(url)
            assert page.status_code == 200
            assert 'Protect highlights (whole frame)' in page.text
            values = BrowserValues(page.text).values
            payload = {k.removeprefix('camera-capture-'): v for k, v in values.items() if k.startswith('camera-capture-')}
            payload.update(modern_admin_action='capture',
                           csrf_token=re.search(r'name="csrf_token" value="([^"]+)"', page.text)[1],
                           auto_exposure_metering_mode='highlight_protected',
                           auto_exposure_highlight_clip_percent=budget)
            with app.app_context():
                before = deepcopy(latest().data)
                revision = latest().id
            assert admin.post(url, data={k:v for k,v in payload.items() if k != 'csrf_token'}).status_code == 400
            for invalid in ('0', '-1', '11', 'nan', 'inf', 'invalid'):
                response = admin.post(url, data=dict(payload, auto_exposure_highlight_clip_percent=invalid))
                with app.app_context():
                    assert latest().id == revision, (invalid, response.status_code)
            reader_page = reader.get(url)
            reader_token = re.search(r'name="csrf_token" value="([^"]+)"', reader_page.text)[1]
            reader.post(url, data=dict(payload, csrf_token=reader_token))
            with app.app_context():
                assert latest().id == revision
            response = admin.post(url, data=payload)
            with app.app_context():
                assert latest().id > revision, response.text[-4000:]
                saved = deepcopy(latest().data)
                assert saved['MULTI_CAMERA']['profiles'][2-cid] == before['MULTI_CAMERA']['profiles'][2-cid]
                for key in ('EXPOSURE_PERIOD', 'EXPOSURE_PERIOD_DAY'):
                    assert saved.get(key) == before.get(key)
                resolved = [build_profile_config(saved,p) for p in derive_capture_profiles(saved)]
                assert resolved[cid-1]['AUTO_EXPOSURE_METERING_MODE'] == 'highlight_protected'
                assert resolved[cid-1]['AUTO_EXPOSURE_HIGHLIGHT_CLIP_PERCENT'] == float(budget)
            rendered = BrowserValues(admin.get(url).text).values
            assert rendered['camera-capture-auto_exposure_metering_mode'] == 'highlight_protected'
            assert float(rendered['camera-capture-auto_exposure_highlight_clip_percent']) == float(budget)
        print('Highlight Settings: persistence, profiles, cadence, invalid input, roles and CSRF: PASS')


if __name__ == '__main__':
    run()
