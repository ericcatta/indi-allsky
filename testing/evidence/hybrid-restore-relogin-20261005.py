#!/usr/bin/env python3
"""Disposable HTTP acceptance: key activation on reload and subsequent login.

This does not operate the pending native-browser fixture or production keys.
"""
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

with isolated_app(multi_camera=True, file_database=True) as app:
    from indi_allsky.flask.models import IndiAllSkyDbConfigTable as Config
    private = Path(os.environ['INDI_ALLSKY_FLASK_CONFIG'])
    assert private.parent == Path(app.config['INDI_ALLSKY_IMAGE_FOLDER'])
    before = json.loads(private.read_text())
    with app.app_context():
        original = Config.query.one().data
    client = login_client(app, 1)
    _, token = payload_from_page(client.get('/indi-allsky/modern-admin/settings/full').text)
    old_cookie = client.get_cookie(app.config['SESSION_COOKIE_NAME']).value
    def fixture_path(value, *parts):
        if str(value) == '/etc/indi-allsky/flask.json' and not parts:
            return private
        return Path(value, *parts)
    with patch('indi_allsky.flask.views.Path', side_effect=fixture_path):
        response = client.post('/indi-allsky/ajax/config/restore',
            headers={'X-CSRFToken': token}, data={
                'csrf_token': token,
                'CONFIG_UPLOAD': (io.BytesIO(json.dumps(original).encode()), 'synthetic.json'),
                'FLUSH_CONFIGS': 'true', 'RESET_KEYS': 'true'})
    assert response.status_code == 200 and response.json['success-message'] == 'Restored Config'
    after = json.loads(private.read_text())
    assert all(after[key] != before[key] for key in ('SECRET_KEY', 'PASSWORD_KEY'))
    assert app.config['SECRET_KEY'] == before['SECRET_KEY']
    assert client.get('/indi-allsky/modern-admin/config-history').status_code == 200
    child = r'''
import json, sys
sys.path.insert(0, sys.argv[1])
from hybrid_runtime_fixture import login_client
from indi_allsky.flask import create_app
from indi_allsky.flask.models import IndiAllSkyDbConfigTable as Config
app = create_app()
old = app.test_client()
old.set_cookie(app.config['SESSION_COOKIE_NAME'], sys.stdin.read())
response = old.get('/indi-allsky/modern-admin/config-history')
assert response.status_code == 302 and '/login' in response.headers['Location']
fresh = login_client(app, 1)
assert fresh.get('/indi-allsky/modern-admin/config-history').status_code == 200
with app.app_context():
    assert [row.id for row in Config.query.all()] == [2]
print(json.dumps({'status':'passed', 'old_session_rejected_after_reload':True,
                  'new_login_succeeds':True, 'only_restored_revision_remains':True}))
'''
    subprocess.run([sys.executable, '-c', child, str(Path(__file__).resolve().parents[1])],
                   input=old_cookie, text=True, check=True)
