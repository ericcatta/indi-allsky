#!/usr/bin/env python3
"""Malformed authentication/account JSON never reaches credential mutation."""
import re
from unittest.mock import patch
from hybrid_runtime_fixture import isolated_app, login_client, PASSWORD


def csrf(client, route):
    page = client.get(route)
    return re.search(r'name="csrf_token"[^>]*value="([^"]+)"', page.text)[1]


def invalid_requests(client, url, token, valid):
    headers = {'X-CSRFToken': token}
    for body in ('null', '[1]', 'true', '12', '"text"', '{bad json'):
        response = client.post(url, data=body, content_type='application/json', headers=headers)
        assert response.status_code == 400 and response.is_json, (url, body, response.status_code)
        assert 'form_global' in response.json
    response = client.post(url, data='not json', content_type='text/plain', headers=headers)
    assert response.status_code == 400 and response.is_json
    for field in valid:
        payload = dict(valid); del payload[field]
        response = client.post(url, json=payload, headers=headers)
        assert response.status_code == 400 and field in response.json
        for value in (None, False, 123, ['unexpected'], {'unexpected': 'object'}):
            response = client.post(url, json={**valid, field: value}, headers=headers)
            assert response.status_code == 400 and field in response.json, (field, value)


def run():
    with isolated_app(multi_camera=True) as app:
        from passlib.hash import argon2
        from indi_allsky.flask import db
        from indi_allsky.flask.models import IndiAllSkyDbUserTable
        for uid in (1, 2):
            anonymous = app.test_client()
            token = csrf(anonymous, '/indi-allsky/login')
            login = {'USERNAME': 'test-user-' + str(uid), 'PASSWORD': PASSWORD, 'NEXT': ''}
            invalid_requests(anonymous, '/indi-allsky/login', token, login)
            with app.app_context():
                assert db.session.get(IndiAllSkyDbUserTable, uid).loginDate is None
            assert anonymous.get('/indi-allsky/modern-admin/account').status_code == 302
            client = login_client(app, uid)
            token = csrf(client, '/indi-allsky/modern-admin/account')
            payload = {'NAME': 'Updated User', 'CURRENT_PASSWORD': PASSWORD, 'NEW_PASSWORD': '', 'NEW_PASSWORD2': ''}
            with app.app_context():
                user = db.session.get(IndiAllSkyDbUserTable, uid)
                before = (user.name, user.password, user.admin, user.email)
            invalid_requests(client, '/indi-allsky/ajax/user', token, payload)
            for current in ('', 'incorrect'):
                response=client.post('/indi-allsky/ajax/user',json={**payload,'CURRENT_PASSWORD':current},headers={'X-CSRFToken':token})
                assert response.status_code==400 and 'CURRENT_PASSWORD' in response.json
            reused={**payload,'NEW_PASSWORD':PASSWORD,'NEW_PASSWORD2':PASSWORD}
            response=client.post('/indi-allsky/ajax/user',json=reused,headers={'X-CSRFToken':token})
            assert response.status_code==400 and 'NEW_PASSWORD' in response.json
            with app.app_context():
                user = db.session.get(IndiAllSkyDbUserTable, uid)
                assert (user.name, user.password, user.admin, user.email) == before
            with patch.object(argon2,'verify',wraps=argon2.verify) as verify:
                response = client.post('/indi-allsky/ajax/user', json=payload, headers={'X-CSRFToken': token})
                assert response.status_code == 200
                assert verify.call_count==1, 'A name-only save must authenticate once without redundant expensive hashes'
            with app.app_context():
                assert db.session.get(IndiAllSkyDbUserTable, uid).name == 'Updated User'
        print('Account/login input: malformed JSON, missing/wrong-type fields, both roles, no authentication or mutation, valid recovery: PASS')


if __name__ == '__main__':
    run()
