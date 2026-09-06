#!/usr/bin/env python3
"""Runtime recovery context on native Hybrid pages, with Classic forbidden."""
import argparse
from html.parser import HTMLParser
from unittest.mock import patch
from hybrid_runtime_fixture import isolated_app, login_client


class Controls(HTMLParser):
    def __init__(self, text):
        super().__init__()
        self.controls = []
        self.feed(text)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'button' and any(key in attrs for key in (
            'data-hybrid-capture-command', 'data-hybrid-abort-exposure',
            'data-hybrid-system-command',
        )):
            self.controls.append(attrs)


def run(runtime_config):
    with isolated_app(runtime_config, multi_camera=True) as app:
        from indi_allsky.flask import views
        pages = ('now', 'media/archive', 'tasks', 'notifications', 'account',
                 'tools/process-fits', 'tools/image-circle-helper',
                 'tools/camera-simulator')
        status = {'label': 'Capture: Running', 'tone': 'good', 'active': True}
        for uid in (1, 2):
            client = login_client(app, uid)
            for page in pages:
                with patch.object(views, 'get_modern_admin_capture_service_status', return_value=status) as provider:
                    response = client.get('/indi-allsky/modern-admin/' + page)
                assert response.status_code == 200, (page, response.status_code)
                provider.assert_called_once_with()
                assert 'Capture: Running' in response.text, page
                controls = Controls(response.text).controls
                assert len(controls) == 6, (page, controls)
                assert all(('disabled' in c) == (uid != 1) for c in controls), (uid, page)
                assert {c['data-hybrid-abort-profile'] for c in controls if 'data-hybrid-abort-profile' in c} == {'test-profile-1', 'test-profile-2'}
                assert {c['data-hybrid-abort-camera'] for c in controls if 'data-hybrid-abort-camera' in c} == {'1', '2'}
                if uid != 1:
                    assert 'Administrator access is required for recovery controls.' in response.text
                    assert all(c.get('aria-describedby') == 'hybrid-runtime-permission' for c in controls)
        with patch.object(views, 'get_modern_admin_capture_service_status', return_value={'label': 'Capture: Unknown', 'tone': 'muted'}):
            response = login_client(app, 1).get('/indi-allsky/modern-admin/media/archive')
            assert 'Capture: Unknown' in response.text
            assert not any('disabled' in c for c in Controls(response.text).controls)
        assert app.test_client().get('/indi-allsky/modern-admin/media/archive').status_code == 302
        print('Hybrid runtime shell: eight pages, both roles, provider states and profile/camera recovery targets: PASS')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--runtime-config', default='/etc/indi-allsky/flask.json')
    run(parser.parse_args().runtime_config)
