#!/usr/bin/env python3
"""Exercise real authenticated HTTP flows without Classic or production effects."""
import argparse
from html.parser import HTMLParser
from hybrid_runtime_fixture import isolated_app, PASSWORD

class FormFields(HTMLParser):
    def __init__(self, html):
        super().__init__()
        self.fields = {}
        self.feed(html)
    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'input' and attrs.get('name'):
            self.fields[attrs['name']] = attrs.get('value', '')

def run(runtime_config):
    with isolated_app(runtime_config) as app:
        client = app.test_client()
        login = client.get('/indi-allsky/login')
        assert login.status_code == 200
        token = FormFields(login.text).fields['csrf_token']
        response = client.post('/indi-allsky/login', headers={'X-CSRFToken': token}, json={
            'USERNAME': 'test-user-1', 'PASSWORD': PASSWORD, 'NEXT': '', 'csrf_token': token})
        assert response.status_code == 200, response.status_code
        assert response.json['redirect'] == '/indi-allsky/modern-admin/now'
        assert client.get('/indi-allsky/login').location == '/indi-allsky/modern-admin/now'
        for route in ('now', 'config-history', 'config-restore', 'settings/full', 'account', 'users', 'users/1'):
            response = client.get('/indi-allsky/modern-admin/'+route)
            assert response.status_code == 200, (route, response.status_code)
        for group in ('acquisition-save', 'analytics', 'auto-exposure-gain', 'camera-connection',
                      'camera-profile', 'exposure-gain', 'fits-source', 'hybrid-awb', 'notifications', 'storage'):
            response = client.get('/indi-allsky/modern-admin/settings/'+group)
            assert response.status_code == 200, (group, response.status_code)
        duplicate = client.get('/indi-allsky/modern-admin/system/config?camera_id=2&profile_id=test-profile')
        assert duplicate.status_code == 302
        assert duplicate.location == '/indi-allsky/modern-admin/settings/full?camera_id=2&profile_id=test-profile'
        account = client.get('/indi-allsky/modern-admin/account')
        assert 'hybrid-account-form' in account.text
        token = FormFields(account.text).fields['csrf_token']
        payload = {'NAME': 'Updated Tester', 'CURRENT_PASSWORD': PASSWORD,
                   'NEW_PASSWORD': '', 'NEW_PASSWORD2': ''}
        headers = {'X-CSRFToken': token}
        assert client.post('/indi-allsky/ajax/user', json=payload).status_code == 400
        bad = dict(payload, CURRENT_PASSWORD='incorrect')
        assert client.post('/indi-allsky/ajax/user', json=bad, headers=headers).status_code == 400
        from indi_allsky.flask import db
        from indi_allsky.flask.models import IndiAllSkyDbUserTable
        from passlib.hash import argon2
        with app.app_context():
            assert db.session.get(IndiAllSkyDbUserTable, 1).name == 'Test User'
        assert client.post('/indi-allsky/ajax/user', json=payload, headers=headers).status_code == 200
        with app.app_context():
            assert db.session.get(IndiAllSkyDbUserTable, 1).name == 'Updated Tester'
            assert argon2.verify(PASSWORD, db.session.get(IndiAllSkyDbUserTable, 1).password)
        changed = dict(payload, NEW_PASSWORD='Updated-Hybrid-Password!', NEW_PASSWORD2='mismatch')
        assert client.post('/indi-allsky/ajax/user', json=changed, headers=headers).status_code == 400
        changed['NEW_PASSWORD2'] = changed['NEW_PASSWORD']
        assert client.post('/indi-allsky/ajax/user', json=changed, headers=headers).status_code == 200
        assert client.get('/indi-allsky/logout').location == '/indi-allsky/modern-admin/now'
        assert client.get('/indi-allsky/modern-admin/account').status_code == 302
        login = client.get('/indi-allsky/login')
        token = FormFields(login.text).fields['csrf_token']
        headers = {'X-CSRFToken': token}
        login_payload = {'USERNAME': 'test-user-1', 'PASSWORD': PASSWORD, 'NEXT': ''}
        assert client.post('/indi-allsky/login', json=login_payload, headers=headers).status_code == 400
        login_payload['PASSWORD'] = changed['NEW_PASSWORD']
        assert client.post('/indi-allsky/login', json=login_payload, headers=headers).status_code == 200
        client.get('/indi-allsky/logout')
        login = client.get('/indi-allsky/login')
        token = FormFields(login.text).fields['csrf_token']
        headers = {'X-CSRFToken': token}
        login_payload.update(USERNAME='test-user-2', PASSWORD=PASSWORD)
        assert client.post('/indi-allsky/login', json=login_payload, headers=headers).status_code == 200
        account = client.get('/indi-allsky/modern-admin/account')
        assert account.status_code == 200 and 'hybrid-account-form' in account.text
        ordinary = dict(payload, ADMIN=True, USERNAME='test-user-1', EMAIL='changed@example.invalid')
        assert client.post('/indi-allsky/ajax/user', json=ordinary, headers=headers).status_code == 200
        with app.app_context():
            user = db.session.get(IndiAllSkyDbUserTable, 2)
            assert user.name == 'Updated Tester'
            assert user.admin is False and user.username == 'test-user-2' and user.email == 'test@example.invalid'
        client.get('/indi-allsky/logout')
        assert client.post('/indi-allsky/ajax/user', json=ordinary, headers=headers).status_code == 302
        print('Hybrid login, account save/password change, role isolation, CSRF and logout: PASS')

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--runtime-config', default='/etc/indi-allsky/flask.json')
    run(parser.parse_args().runtime_config)
