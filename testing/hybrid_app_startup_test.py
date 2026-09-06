#!/usr/bin/env python3
"""Run with the deployed Python environment, using an isolated in-memory DB.

Each mode runs in a separate process so disabled-mode imports cannot be hidden
by Python's module cache. No request is made to production services or data.
"""

import argparse
import importlib.abc
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile


ROOT = Path(__file__).resolve().parents[1]


class ForbidClassicImport(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname == 'indi_allsky.flask.classic_views':
            raise AssertionError('Hybrid-only startup tried to import Classic')


def check_startup(config_path, classic_enabled):
    sys.path.insert(0, str(ROOT))
    if not classic_enabled:
        sys.meta_path.insert(0, ForbidClassicImport())
    config = json.loads(Path(config_path).read_text())
    config.update({
        'HYBRID_ENABLE_CLASSIC_UI': classic_enabled,
        'SQLALCHEMY_DATABASE_URI': 'sqlite://',
        'SQLALCHEMY_ENGINE_OPTIONS': {},
        'SQLALCHEMY_BINDS': {},
        'LOGIN_DISABLED': False,
        'TESTING': True,
        'WTF_CSRF_ENABLED': True,
    })
    with tempfile.TemporaryDirectory(prefix='hybrid-startup-') as directory:
        path = Path(directory) / 'flask.json'
        path.write_text(json.dumps(config))
        os.environ['INDI_ALLSKY_FLASK_CONFIG'] = str(path)
        from indi_allsky.flask import create_app
        app = create_app()
        # Repeated factories must not reuse an already-registered blueprint.
        second = create_app()
        assert app.blueprints['indi_allsky'] is not second.blueprints['indi_allsky']
        routes = {rule.endpoint: rule.rule for rule in app.url_map.iter_rules()}
        assert ('indi_allsky.flask.classic_views' in sys.modules) == classic_enabled
        assert ('indi_allsky.config_view' in routes) == classic_enabled
        assert ('indi_allsky.index_view' in routes) == classic_enabled
        for name in ('modern_admin_now_view', 'modern_admin_library_view', 'ajax_config_view',
                     'fits2jpeg_view', 'latest_image_redirect_view', 'images_folder'):
            assert 'indi_allsky.' + name in routes, name
        assert 'basename' in app.jinja_env.filters
        from flask import render_template
        with app.test_request_context('/indi-allsky/modern-admin/now'):
            shell = render_template('modern_admin/base.html')
            assert 'hybrid-app-shell' in shell
            assert 'admin-mode-switch-classic' not in shell
        client = app.test_client()
        response = client.get('/indi-allsky/static/images/favicon_32.png')
        assert response.status_code == 200
        response = client.post('/indi-allsky/modern-admin/capture/service')
        assert response.status_code == 400  # CSRF rejects before any effect.
        response = client.get('/indi-allsky/modern-admin/tasks')
        assert response.status_code == 302 and '/login' in response.location
        if not classic_enabled:
            assert client.get('/indi-allsky/config').status_code == 404
        print('Real Flask startup, static serving, auth and CSRF passed; Classic={0}'.format(classic_enabled))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--runtime-config', default='/etc/indi-allsky/flask.json')
    parser.add_argument('--mode', choices=('enabled', 'disabled'))
    args = parser.parse_args()
    if args.mode:
        check_startup(args.runtime_config, args.mode == 'enabled')
    else:
        for mode in ('disabled', 'enabled'):
            subprocess.run([
                sys.executable, __file__, '--runtime-config', args.runtime_config, '--mode', mode,
            ], check=True)
