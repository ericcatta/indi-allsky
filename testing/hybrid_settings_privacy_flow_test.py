#!/usr/bin/env python3
"""Keep configuration credentials out of ordinary-user HTML and persistence."""
import argparse
from copy import deepcopy
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from indi_allsky.modern_admin_settings_privacy import redact_settings, MASKED
from hybrid_runtime_fixture import isolated_app, login_client
from hybrid_settings_flow_test import payload_from_page


def run(runtime_config):
    sample = {'ENCRYPT_PASSWORDS': True, 'PASSWORD': 'example-secret', 'empty_TOKEN': '',
              'nested': [{'API_KEY': 'example-key', 'gain': 17}],
              'encoded': json.dumps({'Authorization': 'example-bearer', 'enabled': False})}
    original = deepcopy(sample)
    safe = redact_settings(sample)
    assert sample == original and safe is not sample
    assert safe['ENCRYPT_PASSWORDS'] is True and safe['empty_TOKEN'] == ''
    assert safe['PASSWORD'] == MASKED and safe['nested'][0]['API_KEY'] == MASKED
    assert safe['nested'][0]['gain'] == 17
    assert json.loads(safe['encoded']) == {'Authorization': MASKED, 'enabled': False}
    with isolated_app(runtime_config, multi_camera=True) as app:
        from indi_allsky.flask import db
        from indi_allsky.flask.models import IndiAllSkyDbConfigTable
        sentinels = ('synthetic-mqtt-credential', 'synthetic-profile-credential', 'synthetic-driver-credential')
        with app.app_context():
            row = db.session.get(IndiAllSkyDbConfigTable, 1)
            stored = deepcopy(row.data)
            stored['ENCRYPT_PASSWORDS'] = False
            stored['MQTTPUBLISH']['PASSWORD'] = sentinels[0]
            stored['INDI_CONFIG_DEFAULTS']['TEXTS'] = {'SYNTHETIC': {'PASSWORD': sentinels[2]}}
            for profile in stored['MULTI_CAMERA']['profiles']:
                profile['test_extension']['PASSWORD'] = sentinels[1]
            row.data = stored
            db.session.commit()
        admin, reader = login_client(app, 1), login_client(app, 2)
        for camera in (1, 2):
            scope = f'?camera_id={camera}&profile_id=test-profile-{camera}'
            for path in ('/indi-allsky/modern-admin/settings/full',
                         '/indi-allsky/modern-admin/settings/cameras',
                         '/indi-allsky/modern-admin/settings'):
                response = reader.get(path + scope)
                assert response.status_code == 200, (path, response.status_code)
                assert not any(secret in response.text for secret in sentinels), path
                assert 'test-profile-' + str(camera) in response.text or path.endswith('/settings')
        admin_page = admin.get('/indi-allsky/modern-admin/settings/full')
        payload, _ = payload_from_page(admin_page.text)
        assert payload['MQTTPUBLISH__PASSWORD'] == sentinels[0]
        assert sentinels[2] in admin_page.text
        reader_page = reader.get('/indi-allsky/modern-admin/settings/full')
        reader_payload, token = payload_from_page(reader_page.text)
        assert reader_payload['MQTTPUBLISH__PASSWORD'] == MASKED
        denied = reader.post('/indi-allsky/ajax/config', json=reader_payload,
                             headers={'X-CSRFToken': token})
        assert denied.status_code in (400, 403)
        with app.app_context():
            assert IndiAllSkyDbConfigTable.query.count() == 1
            assert db.session.get(IndiAllSkyDbConfigTable, 1).data == stored
        # A reader request must not poison the next administrator's form/cache.
        later = admin.get('/indi-allsky/modern-admin/settings/full')
        assert sentinels[0] in later.text and sentinels[2] in later.text
        print('Settings privacy: admin values retained; ordinary HTML/form/profile/search projections redacted for both cameras; attempted save cannot overwrite secrets PASS')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--runtime-config', default='/etc/indi-allsky/flask.json')
    run(parser.parse_args().runtime_config)
