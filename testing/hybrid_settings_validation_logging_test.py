#!/usr/bin/env python3
"""Validation diagnostics identify fields without persisting submitted secrets."""
import argparse
import json
import logging
from types import SimpleNamespace

from hybrid_runtime_fixture import isolated_app, login_client
from hybrid_settings_flow_test import payload_from_page


class Capture(logging.Handler):
    def __init__(self):
        super().__init__()
        self.messages = []

    def emit(self, record):
        if record.getMessage().startswith('Config save validation failed:'):
            self.messages.append(record.getMessage())


def run(runtime_config):
    with isolated_app(runtime_config, multi_camera=True) as app:
        from indi_allsky.flask import db
        from indi_allsky.flask.models import IndiAllSkyDbConfigTable
        from indi_allsky.flask.views import AjaxConfigView
        client = login_client(app, 1)
        page = client.get('/indi-allsky/modern-admin/settings/full')
        assert page.status_code == 200
        payload, token = payload_from_page(page.text)
        secret = 'synthetic-submitted-driver-credential'
        reflected = 'synthetic-reflected-validation-input'
        payload['INDI_CONFIG_DEFAULTS'] = json.dumps({'TEXTS': {'DRIVER': {'PASSWORD': secret}}})
        capture = Capture()
        previous = app.logger.level
        app.logger.addHandler(capture)
        app.logger.setLevel(logging.WARNING)
        try:
            response = client.post('/indi-allsky/ajax/config', json=payload,
                                   headers={'X-CSRFToken': token})
            assert response.status_code == 400
            assert response.json['INDI_CONFIG_DEFAULTS'] == ['Only PROPERTIES, TEXT, and SWITCHES attributes allowed']
            with app.app_context():
                assert IndiAllSkyDbConfigTable.query.count() == 1
                # Validators may interpolate submitted input into their message.
                # Missing-field diagnostics must not copy that text into logs.
                AjaxConfigView.log_config_validation_errors(None,
                    SimpleNamespace(errors={'missing_test_field': [reflected]}))
            assert any('INDI_CONFIG_DEFAULTS' in message and 'TextAreaField' in message
                       for message in capture.messages), capture.messages
            assert any('missing_test_field' in message for message in capture.messages)
            assert not any(secret in message or reflected in message for message in capture.messages), 'Submitted data leaked into validation logs'
            assert all('error_count=1' in message for message in capture.messages)
        finally:
            app.logger.removeHandler(capture)
            app.logger.setLevel(previous)
        print('Settings validation logs: embedded credentials and reflected error text excluded; field/type/count diagnostics and HTTP errors retained PASS')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--runtime-config', default='/etc/indi-allsky/flask.json')
    run(parser.parse_args().runtime_config)
