#!/usr/bin/env python3
"""Read methods cannot dispatch capture effects; commands require authorized POST."""
import re
from unittest.mock import patch
from hybrid_runtime_fixture import isolated_app, login_client


def run():
    with isolated_app(multi_camera=True) as app:
        from indi_allsky.flask.views import ModernAdminCaptureServiceActionView
        admin, ordinary, anonymous = login_client(app, 1), login_client(app, 2), app.test_client()
        endpoint = '/indi-allsky/modern-admin/capture/service'
        status = {'state': 'active'}
        def headers(client):
            page = client.get('/indi-allsky/modern-admin/account')
            return {'X-CSRFToken': re.search(r'name="csrf_token"[^>]*value="([^"]+)"', page.text)[1]}
        admin_headers, user_headers = headers(admin), headers(ordinary)
        with patch('indi_allsky.flask.views.get_modern_admin_capture_service_status', return_value=status), \
             patch.object(ModernAdminCaptureServiceActionView, 'run_capture_service_command', return_value={'returncode':0,'output':''}) as effect:
            for client in (admin, ordinary):
                for method in ('GET', 'HEAD'):
                    for body in ({'json':{'command':'stop'}}, {'data':{'command':'restart'}}):
                        response = client.open(endpoint, method=method, **body)
                        assert effect.call_count == 0, method + ' invoked a capture effect'
                        assert response.status_code == 200, (method, response.status_code)
                        if method == 'GET':
                            assert response.json == {'service-status':status}
                        else:
                            assert response.data == b''
            for method in ('GET','HEAD'):
                assert anonymous.open(endpoint, method=method, json={'command':'stop'}).status_code == 302
            assert admin.post(endpoint, json={'command':'stop'}).status_code == 400
            assert ordinary.post(endpoint, json={'command':'stop'}, headers=user_headers).status_code == 403
            for method in ('PUT','PATCH','DELETE'):
                assert admin.open(endpoint, method=method, json={'command':'stop'}, headers=admin_headers).status_code == 405
            assert admin.post(endpoint, json={'command':'invalid'}, headers=admin_headers).status_code == 400
            effect.assert_not_called()
            for command in ('start','stop','restart'):
                response = admin.post(endpoint, json={'command':command}, headers=admin_headers)
                assert response.status_code == 200 and 'success-message' in response.json
                assert effect.call_args.args == (command,)
            assert effect.call_count == 3
        print('Capture HTTP methods: GET/HEAD read-only; POST commands, role and CSRF checks: PASS')


if __name__ == '__main__':
    run()
