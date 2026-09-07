#!/usr/bin/env python3
"""Login return destinations retain local scope and reject browser URL ambiguity."""
from hybrid_runtime_fixture import isolated_app, PASSWORD
from hybrid_account_input_test import csrf


def run():
    with isolated_app(multi_camera=True) as app:
        client = app.test_client()
        token = csrf(client, '/indi-allsky/login')
        fallback = '/indi-allsky/modern-admin/now'
        rejected = [
            '', 'https://external.invalid/path', '//external.invalid/path',
            '///external.invalid/path', '/\\external.invalid/path',
            'javascript:alert(1)', 'data:text/html,test', 'http:///external.invalid',
            '/\t/external.invalid', '/\n/external.invalid', '/\r/external.invalid',
            'java\tscript:alert(1)', 'java\nscript:alert(1)', 'java\rscript:alert(1)',
            '/indi-allsky/\x00now', '/indi-allsky/\x7fnow',
        ]
        accepted = [
            '/indi-allsky/modern-admin/now',
            '/indi-allsky/modern-admin/media?camera_id=2&camera_profile=test-profile-2',
            '/indi-allsky/modern-admin/settings?tag=a&tag=b#section',
        ]
        for target in rejected + accepted:
            response = client.post('/indi-allsky/login', headers={'X-CSRFToken': token}, json={
                'USERNAME': 'test-user-1', 'PASSWORD': PASSWORD, 'NEXT': target})
            assert response.status_code == 200, (repr(target), response.status_code)
            expected = target if target in accepted else fallback
            assert response.json['redirect'] == expected, (repr(target), response.json)
        print('Login redirects: external/scheme/control-character rejection and local camera/profile/query preservation: PASS')


if __name__ == '__main__':
    run()
