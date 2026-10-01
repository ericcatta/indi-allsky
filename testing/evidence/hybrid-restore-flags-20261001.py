#!/usr/bin/env python3
"""Bounded HTTP acceptance of restore flags on disposable state only.

Never rotates production keys or deletes production history. Native browser
confirmation and post-reload login are separate acceptance cases.
"""
from copy import deepcopy
import io
import json
import os
from pathlib import Path
import subprocess
import sys
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from hybrid_runtime_fixture import isolated_app, login_client
from hybrid_settings_flow_test import payload_from_page


def run(flush, reset):
    with isolated_app(multi_camera=True) as app:
        from cryptography.fernet import Fernet
        from indi_allsky.flask import db
        from indi_allsky.flask.models import IndiAllSkyDbConfigTable as Config, IndiAllSkyDbTaskQueueTable as Task
        private_config = Path(os.environ['INDI_ALLSKY_FLASK_CONFIG'])
        assert private_config.parent == Path(app.config['INDI_ALLSKY_IMAGE_FOLDER'])
        assert private_config != Path('/etc/indi-allsky/flask.json')
        before_keys = json.loads(private_config.read_text())
        with app.app_context():
            original = deepcopy(db.session.get(Config, 1).data)
            assert original['ENCRYPT_PASSWORDS'] is False
        client = login_client(app, 1)
        _, token = payload_from_page(client.get('/indi-allsky/modern-admin/settings/full').text)
        def isolated_path(value, *parts):
            if str(value) == '/etc/indi-allsky/flask.json' and not parts:
                return private_config
            return Path(value, *parts)
        with patch('indi_allsky.flask.views.Path', side_effect=isolated_path):
            response = client.post('/indi-allsky/ajax/config/restore', headers={'X-CSRFToken': token}, data={
                'csrf_token': token, 'CONFIG_UPLOAD': (io.BytesIO(json.dumps(original).encode()), 'fixture.json'),
                'FLUSH_CONFIGS': 'true' if flush else '', 'RESET_KEYS': 'true' if reset else '',
            })
        assert response.status_code == 200, response.json
        assert response.json['success-message'] == 'Restored Config'
        with app.app_context():
            rows = Config.query.order_by(Config.id).all()
            assert len(rows) == (1 if flush else 2)
            assert rows[-1].id == 2
            assert rows[-1].data['MULTI_CAMERA'] == original['MULTI_CAMERA']
            assert rows[-1].data['OWNER'] == original['OWNER']
            assert Task.query.count() == 0
        after_keys = json.loads(private_config.read_text())
        other = lambda value: {k:v for k,v in value.items() if k not in ('SECRET_KEY', 'PASSWORD_KEY')}
        assert other(after_keys) == other(before_keys)
        for key in ('SECRET_KEY', 'PASSWORD_KEY'):
            assert (after_keys[key] != before_keys[key]) == reset
        if reset:
            f = Fernet(after_keys['PASSWORD_KEY'].encode())
            assert f.decrypt(f.encrypt(b'synthetic-only')) == b'synthetic-only'
            assert private_config.stat().st_mode & 0o777 == 0o660
        print(json.dumps({'flush': flush, 'reset': reset, 'status':'passed', 'history_rows':1 if flush else 2,
                          'profiles_preserved':True, 'keys_changed':reset, 'effects_queued':0}))


if __name__ == '__main__':
    if len(sys.argv) == 3:
        run(sys.argv[1] == '1', sys.argv[2] == '1')
    else:
        for flush in (0, 1):
            for reset in (0, 1):
                subprocess.run([sys.executable, __file__, str(flush), str(reset)], check=True)
