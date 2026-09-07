#!/usr/bin/env python3
"""Flush failure terminates, reports committed progress, and preserves camera scope."""
from datetime import date, datetime
from pathlib import Path
from unittest.mock import patch
from hybrid_runtime_fixture import isolated_app, login_client
from hybrid_account_input_test import csrf


def run(command):
    with isolated_app(multi_camera=True) as app:
        from indi_allsky.flask import db
        from indi_allsky.flask.models import IndiAllSkyDbImageTable, IndiAllSkyDbVideoTable
        from indi_allsky.flask.views import AjaxSystemInfoView
        model = IndiAllSkyDbVideoTable if command == 'flush_timelapses' else IndiAllSkyDbImageTable
        root = Path(app.config['INDI_ALLSKY_IMAGE_FOLDER'])
        with app.app_context():
            for ident, camera in ((1, 1), (2, 2), (3, 2)):
                path = root / f'cleanup-{ident}.test'; path.write_bytes(b'dedicated cleanup fixture')
                fields = dict(id=ident, camera_id=camera, filename=str(path), dayDate=date.today(),
                              createDate=datetime.now(), night=False, data={})
                if model is IndiAllSkyDbImageTable:
                    fields.update(exposure=1, gain=1, adu=.1, width=1, height=1)
                else:
                    fields['success'] = True
                db.session.add(model(**fields))
            db.session.commit()
        admin, user = login_client(app, 1), login_client(app, 2)
        headers = {'X-CSRFToken': csrf(admin, '/indi-allsky/modern-admin/account')}
        payload = {'CAMERA_ID': 2, 'SERVICE_HIDDEN': 'system', 'COMMAND_HIDDEN': command}
        url = '/indi-allsky/ajax/system'
        assert admin.post(url, json=payload).status_code == 400
        user_headers = {'X-CSRFToken': csrf(user, '/indi-allsky/modern-admin/account')}
        assert user.post(url, json=payload, headers=user_headers).status_code == 400
        with patch.object(AjaxSystemInfoView, 'verify_admin_network', return_value=False):
            assert admin.post(url, json=payload, headers=headers).status_code == 400
        original = model.deleteAsset
        attempts = []
        def delete(entry):
            attempts.append(entry.id)
            if attempts.count(2) > 1:
                raise RuntimeError('Failure retried: would loop indefinitely')
            if entry.id == 2:
                raise PermissionError('dedicated fixture cannot be removed')
            return original(entry)
        with patch.object(model, 'deleteAsset', delete):
            response = admin.post(url, json=payload, headers=headers)
        assert response.status_code == 400, response.json
        assert response.json['deleted_count'] == 1 and response.json['failed_count'] == 1
        assert response.json['camera_id'] == 2 and 'Cleanup stopped' in response.json['form_global'][0]
        assert attempts == [2, 3], attempts
        with app.app_context():
            assert db.session.get(model, 1) and db.session.get(model, 2)
            assert db.session.get(model, 3) is None
        assert (root/'cleanup-1.test').exists() and (root/'cleanup-2.test').exists()
        assert not (root/'cleanup-3.test').exists()
        retry = admin.post(url, json=payload, headers=headers)
        assert retry.status_code == 200 and '1 ' in retry.json['success-message']
        assert (root/'cleanup-1.test').exists() and not (root/'cleanup-2.test').exists()
        assert admin.post(url, json=payload, headers=headers).json['success-message'].startswith('0 ')
    print('Four cleanup commands: CSRF/role/network denial, partial failure without retry loop, scoped files/DB, deliberate retry and empty completion: PASS')


if __name__ == '__main__':
    import subprocess
    import sys
    if len(sys.argv) == 2:
        run(sys.argv[1])
    else:
        for command in ('flush_images', 'flush_16min_images', 'flush_daytime', 'flush_timelapses'):
            subprocess.run([sys.executable, __file__, command], check=True)
