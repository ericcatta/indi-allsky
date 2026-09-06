#!/usr/bin/env python3
"""Real Hybrid OAuth routes/storage; Google transport is explicitly simulated."""
import argparse
import json
import re
import time
from unittest.mock import MagicMock, patch
from hybrid_runtime_fixture import isolated_app, login_client


def run(runtime_config):
    with isolated_app(runtime_config, multi_camera=True) as app:
        from indi_allsky.flask import db
        from indi_allsky.flask.models import IndiAllSkyDbConfigTable, IndiAllSkyDbStateTable
        from indi_allsky.flask.miscDb import miscDb
        from indi_allsky.flask.youtube_views import CREDENTIALS_KEY, NETWORK_TIMEOUT
        from google.oauth2.credentials import Credentials
        from google.auth.exceptions import RefreshError
        from oauthlib.oauth2 import InvalidGrantError
        from requests import Timeout
        from sqlalchemy.exc import SQLAlchemyError
        admin, user = login_client(app,1), login_client(app,2)
        base='/indi-allsky/youtube/'
        panel='/indi-allsky/modern-admin/youtube'
        def csrf(client):
            page=client.get(panel)
            assert page.status_code==200, page.text[:200]
            assert 'config_view' not in page.text and 'Legacy YouTube' not in page.text
            return re.search(r'name="csrf_token" value="([^"]+)"',page.text)[1]
        headers={'X-CSRFToken':csrf(admin)}
        with patch('indi_allsky.flask.youtube_views.oauth_modules_available',return_value=False):
            assert 'YouTube support is not installed' in admin.get(panel).text
            assert admin.post(base+'authorize',headers=headers).status_code==503
            assert admin.get(base+'oauth2callback').status_code==503
        userheaders={'X-CSRFToken':csrf(user)}
        assert 'Only administrators' in user.get(panel).text
        assert 'Not connected' in admin.get(panel).text
        for name in ('authorize','oauth2refresh','oauth2revoke'):
            assert admin.get(base+name).location.endswith(panel)
            assert admin.post(base+name).status_code==400
            assert user.get(base+name).status_code==403
            assert user.post(base+name,headers=userheaders).status_code==403
            assert app.test_client().get(base+name).status_code==302
            assert app.test_client().post(base+name,headers=headers).status_code==400
            assert admin.post(base+name,headers=headers).status_code==400
        assert admin.get(base+'oauth2callback').status_code==400
        assert user.get(base+'oauth2callback').status_code==403
        with app.app_context():
            config=db.session.get(IndiAllSkyDbConfigTable,1)
            settings=dict(config.data); settings['YOUTUBE']=dict(settings['YOUTUBE'],SECRETS_FILE='/missing-test-secrets.json')
            config.data=settings;db.session.commit()
        assert admin.post(base+'authorize',headers=headers).status_code==400
        credentials=Credentials(token='access-test',refresh_token='refresh-test',token_uri='https://oauth2.googleapis.com/token',client_id='test-client',client_secret='test-secret',scopes=['https://www.googleapis.com/auth/youtube.upload'])
        flow=MagicMock()
        flow.authorization_url.return_value=('https://accounts.google.com/test-authorize','test-state')
        flow.code_verifier='test-verifier'
        flow.credentials=credentials
        factory='google_auth_oauthlib.flow.Flow.from_client_secrets_file'
        def begin():
            response=admin.post(base+'authorize',headers=headers)
            assert response.status_code==303 and response.location=='https://accounts.google.com/test-authorize'
        def stored():
            with app.app_context():
                return json.loads(miscDb({}).getState(CREDENTIALS_KEY))
        with patch(factory,return_value=flow) as create:
            begin()
            assert flow.authorization_url.call_args.kwargs['prompt']=='consent'
            assert flow.redirect_uri=='http://localhost/indi-allsky/youtube/oauth2callback'
            response=admin.get(base+'oauth2callback?state=test-state&code=test-code')
            assert response.status_code==303 and response.location.endswith(panel),response.text
            assert flow.fetch_token.call_args.kwargs['timeout']==NETWORK_TIMEOUT
            assert stored()['refresh_token']=='refresh-test'
            with app.app_context():
                row=IndiAllSkyDbStateTable.query.filter_by(key=CREDENTIALS_KEY).one()
                assert row.encrypted and 'access-test' not in row.value and 'test-secret' not in row.value
            assert admin.get(base+'oauth2callback?state=test-state&code=test-code').status_code==400
            assert 'YouTube account connected' in admin.get(panel).text
            for invalid in ('wrong', '☀'):
                begin()
                assert admin.get(base+'oauth2callback',query_string={'state':invalid,'code':'test'}).status_code==400
            for change in ({'youtube_started_at':time.time()-601},{'youtube_user_id':'2'},{'youtube_code_verifier':None}):
                begin()
                with admin.session_transaction() as session: session.update(change)
                assert admin.get(base+'oauth2callback?state=test-state&code=test').status_code==400
            begin()
            assert admin.get(base+'oauth2callback?state=test-state&error=access_denied').status_code==303
            assert stored()['token']=='access-test'
            for failure in (InvalidGrantError(description='secret error'), Timeout('secret error')):
                begin()
                with patch.object(flow,'fetch_token',side_effect=failure):
                    failed=admin.get(base+'oauth2callback?state=test-state&code=test')
                    assert failed.status_code==502 and 'secret error' not in failed.text
                assert stored()['token']=='access-test'
            begin()
            flow.credentials=Credentials(token='replacement-test')
            assert admin.get(base+'oauth2callback?state=test-state&code=test').status_code==400
            assert stored()['token']=='access-test'
            flow.credentials=credentials
            begin()
            with patch.object(db.session,'commit',side_effect=SQLAlchemyError('secret database')):
                failed=admin.get(base+'oauth2callback?state=test-state&code=test')
                assert failed.status_code==503 and 'secret database' not in failed.text
            assert stored()['token']=='access-test'
        assert flow.oauth2session.close.called
        def refresh(instance,transport):
            transport(url='https://oauth2.googleapis.com/token',method='POST',timeout=999)
            instance.token='refreshed-test'
        with patch.object(Credentials,'refresh',autospec=True,side_effect=refresh), patch('google.auth.transport.requests.Request') as transport:
            response=admin.post(base+'oauth2refresh',headers=headers)
            assert response.status_code==303,response.text
            assert stored()['token']=='refreshed-test'
            assert transport.return_value.call_args.kwargs['timeout']==NETWORK_TIMEOUT
        with patch.object(Credentials,'refresh',side_effect=RefreshError('secret error')):
            failed=admin.post(base+'oauth2refresh',headers=headers)
            assert failed.status_code==502 and 'secret error' not in failed.text
        assert stored()['token']=='refreshed-test'
        with patch('indi_allsky.flask.youtube_views.requests.post') as post:
            post.return_value.__enter__.return_value.status_code=503
            assert admin.post(base+'oauth2revoke',headers=headers).status_code==502
            assert stored()['token']=='refreshed-test'
            assert post.call_args.kwargs=={'data':{'token':'refresh-test'},'timeout':NETWORK_TIMEOUT}
            post.return_value.__enter__.return_value.status_code=200
            assert admin.post(base+'oauth2revoke',headers=headers).status_code==303
            with app.app_context(): assert IndiAllSkyDbStateTable.query.filter_by(key=CREDENTIALS_KEY).count()==0
            assert admin.post(base+'oauth2revoke',headers=headers).status_code==400
        with app.app_context(): miscDb({}).setEncryptedState(CREDENTIALS_KEY,'not valid JSON')
        page=admin.get(panel)
        assert page.status_code==200 and 'Unreadable' in page.text
        assert admin.post(base+'oauth2refresh',headers=headers).status_code==400
        assert admin.post(base+'oauth2revoke',headers=headers).status_code==400
        assert 'test-secret' not in page.text and 'refresh-test' not in page.text
        print('Hybrid YouTube: real roles/CSRF, safe bookmarks, PKCE state/expiry/replay, encrypted persistence, refresh, revoke and transport/storage failures: PASS (Google simulated)')

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--runtime-config',default='/etc/indi-allsky/flask.json')
    run(parser.parse_args().runtime_config)
