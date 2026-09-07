#!/usr/bin/env python3
"""Disabled/deleted users cannot retain Hybrid access through saved sessions."""
import re
import io
import hmac
import hashlib
import time
from unittest.mock import patch
from hybrid_runtime_fixture import isolated_app, login_client, PASSWORD


def run():
    with isolated_app(multi_camera=True) as app:
        from indi_allsky.flask import db
        from indi_allsky.flask.models import IndiAllSkyDbUserTable, IndiAllSkyDbTaskQueueTable
        from indi_allsky.flask.syncapi_views import SyncApiBaseView
        from indi_allsky.flask.actionapi_views import ActionApiBaseView, PermissionDenied
        for uid in (1, 2):
            remember_client = login_client(app, uid)
            assert remember_client.get_cookie(app.config.get('REMEMBER_COOKIE_NAME', 'remember_token')) is not None
            with remember_client.session_transaction() as session:
                session.clear()
            assert remember_client.get('/indi-allsky/modern-admin/account').status_code == 200
            client = login_client(app, uid)
            page = client.get('/indi-allsky/modern-admin/account')
            token = re.search(r'name="csrf_token"[^>]*value="([^"]+)"', page.text)[1]
            assert page.status_code == 200
            api_key = 'dedicated-fixture-api-key'
            metadata = b'{}'
            with app.app_context():
                db.session.get(IndiAllSkyDbUserTable, uid).setApiKey(api_key, app.config['PASSWORD_KEY'])
                db.session.commit()
            signature = hmac.new(api_key.encode(), str(int(time.time() // SyncApiBaseView.time_skew)).encode() + metadata,
                                 hashlib.sha3_512).hexdigest()
            auth_header = {'Authorization': 'Bearer test-user-' + str(uid) + ':' + signature}
            with app.test_request_context(headers=auth_header):
                object.__new__(SyncApiBaseView).authorize(metadata)
            credentials = {'username': 'test-user-' + str(uid), 'password': PASSWORD}
            with app.test_request_context(), patch.object(ActionApiBaseView, 'verify_admin_network', return_value=True):
                try:
                    object.__new__(ActionApiBaseView).authorize(credentials)
                except PermissionDenied:
                    assert uid == 2
                else:
                    assert uid == 1
            with app.app_context():
                user = db.session.get(IndiAllSkyDbUserTable, uid)
                user.active = False
                before_name = user.name
                db.session.commit()
            for route in ('account', 'now', 'settings/full', 'tasks', 'users'):
                result = client.get('/indi-allsky/modern-admin/' + route)
                assert result.status_code == 302 and '/login' in result.location, (uid, route)
            result = client.post('/indi-allsky/ajax/user', headers={'X-CSRFToken': token}, json={
                'NAME': 'Must not save', 'CURRENT_PASSWORD': PASSWORD, 'NEW_PASSWORD': '', 'NEW_PASSWORD2': ''})
            assert result.status_code == 302
            for route in ('pause', 'unpause'):
                result = app.test_client().post('/indi-allsky/action/' + route, json=credentials)
                assert result.status_code == 400 and result.json == {'error': 'authentication failed'}
            result = app.test_client().post('/indi-allsky/sync/v1/image', headers=auth_header,
                data={'metadata': (io.BytesIO(metadata), 'metadata.json')})
            assert result.status_code == 400 and result.json == {'error': 'authentication failed'}
            with app.app_context():
                assert db.session.get(IndiAllSkyDbUserTable, uid).name == before_name
                assert IndiAllSkyDbTaskQueueTable.query.count() == 0
            assert client.get_cookie(app.config.get('REMEMBER_COOKIE_NAME', 'remember_token')) is not None
            # Clear only the session; the signed remember cookie still exists.
            with client.session_transaction() as session:
                session.clear()
            assert client.get('/indi-allsky/modern-admin/account').status_code == 302
            login = client.get('/indi-allsky/login')
            token = re.search(r'name="csrf_token"[^>]*value="([^"]+)"', login.text)[1]
            result = client.post('/indi-allsky/login', headers={'X-CSRFToken': token}, json={
                'USERNAME': 'test-user-' + str(uid), 'PASSWORD': PASSWORD, 'NEXT': ''})
            assert result.status_code == 400 and 'disabled' in result.text.lower()
            with app.app_context():
                db.session.get(IndiAllSkyDbUserTable, uid).active = True
                db.session.commit()
            assert login_client(app, uid).get('/indi-allsky/modern-admin/account').status_code == 200
        # Missing users and malformed signed-session identities must not cause 500.
        for identity in ('not-an-id', '', '99999', '9223372036854775808', '-1', 0, True, [], {}):
            with app.app_context():
                assert app.login_manager._user_callback(identity) is None
            client = app.test_client()
            with client.session_transaction() as session:
                session['_user_id'] = identity
                session['_fresh'] = True
            assert client.get('/indi-allsky/modern-admin/account').status_code == 302, identity
        client = login_client(app, 2)
        with app.app_context():
            db.session.delete(db.session.get(IndiAllSkyDbUserTable, 2))
            db.session.commit()
        assert client.get('/indi-allsky/modern-admin/account').status_code == 302
        print('Hybrid sessions: disabled admin/user, remember cookies, denied mutations, fresh login, reactivation, deleted/malformed identities: PASS')


if __name__ == '__main__':
    run()
