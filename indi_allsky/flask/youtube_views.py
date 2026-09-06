"""Hybrid OAuth controls; historical callback URLs remain public contracts."""
import hmac
from importlib.util import find_spec
import json
import time

import requests
from cryptography.fernet import InvalidToken
from flask import abort, current_app as app, flash, redirect, request, session, url_for
from flask_login import current_user, login_required
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm.exc import NoResultFound

from . import db
from .base_views import BaseView

SCOPES = ['https://www.googleapis.com/auth/youtube.upload']
CREDENTIALS_KEY = 'YOUTUBE_CREDENTIALS'
OAUTH_MAX_AGE = 600
NETWORK_TIMEOUT = 30


def oauth_modules_available():
    try:
        return all(find_spec(name) is not None for name in ('google_auth_oauthlib.flow', 'google.oauth2.credentials', 'oauthlib.oauth2'))
    except (ImportError, ValueError):
        return False


def require_oauth_modules():
    if not oauth_modules_available():
        abort(503, 'YouTube support is not installed. Install the optional Python modules using the project setup instructions.')


def credentials_to_dict(credentials):
    # Retain the worker's established Credentials(**payload) contract.
    return {key: getattr(credentials, key) for key in (
        'token', 'refresh_token', 'token_uri', 'client_id', 'client_secret', 'scopes')}


def load_credentials(store):
    from google.oauth2.credentials import Credentials
    try:
        payload = json.loads(store.getState(CREDENTIALS_KEY))
        if not isinstance(payload, dict):
            raise ValueError('Invalid credential container')
        return Credentials(**payload)
    except NoResultFound:
        abort(400, 'YouTube is not connected. Connect an account first.')
    except (InvalidToken, ValueError, TypeError):
        abort(400, 'Stored YouTube authorization cannot be read. Reconnect the account.')
    except SQLAlchemyError:
        db.session.rollback()
        abort(503, 'YouTube authorization storage is unavailable. Try again later.')


def authorization_status(store):
    """Expose capability, never tokens, client IDs or secret file contents."""
    try:
        payload = json.loads(store.getState(CREDENTIALS_KEY))
        if not isinstance(payload, dict) or not payload.get('token'):
            raise ValueError('Missing token')
        return {'label': 'Stored', 'stored': True, 'refreshable': bool(payload.get('refresh_token')),
                'detail': 'Authorization is stored. Google connectivity is checked when an action runs.'}
    except NoResultFound:
        return {'label': 'Not connected', 'stored': False, 'refreshable': False,
                'detail': 'Connect a Google account to authorize uploads.'}
    except (InvalidToken, ValueError, TypeError):
        return {'label': 'Unreadable', 'stored': False, 'refreshable': False,
                'detail': 'Stored authorization cannot be read. Reconnect the account.'}
    except SQLAlchemyError:
        db.session.rollback()
        return {'label': 'Unavailable', 'stored': False, 'refreshable': False,
                'detail': 'Authorization storage is unavailable. Try again later.'}


class YoutubeActionView(BaseView):
    decorators = [login_required]
    methods = ['GET', 'POST']

    def dispatch_request(self):
        if not current_user.is_authenticated or not current_user.admin:
            abort(403, 'Administrator access is required to change YouTube authorization.')
        if request.method == 'GET':
            # Old bookmarks remain safe: changes require a CSRF-protected form.
            return redirect(url_for('indi_allsky.modern_admin_youtube_view'))
        require_oauth_modules()
        try:
            return self.perform()
        except SQLAlchemyError:
            db.session.rollback()
            abort(503, 'The authorization change could not be saved. Check YouTube status before retrying.')

    def finished(self, message):
        flash(message, 'success')
        return redirect(url_for('indi_allsky.modern_admin_youtube_view'), code=303)

    def make_flow(self, **kwargs):
        from google_auth_oauthlib.flow import Flow
        config = self.indi_allsky_config.get('YOUTUBE', {})
        filename = config.get('SECRETS_FILE') if isinstance(config, dict) else None
        if not filename:
            abort(400, 'Configure the YouTube client secrets file in Full Settings first.')
        try:
            flow = Flow.from_client_secrets_file(filename, scopes=SCOPES, **kwargs)
        except (OSError, ValueError, KeyError, TypeError):
            abort(400, 'The YouTube client secrets file is missing, unreadable or invalid.')
        flow.redirect_uri = url_for('indi_allsky.youtube_oauth2callback_view', _external=True)
        return flow


class YoutubeAuthorizeView(YoutubeActionView):
    def perform(self):
        flow = self.make_flow(autogenerate_code_verifier=True)
        try:
            authorization_url, state = flow.authorization_url(
                access_type='offline', include_granted_scopes='true', prompt='consent')
        finally:
            flow.oauth2session.close()
        session['youtube_state'] = state
        session['youtube_code_verifier'] = flow.code_verifier
        session['youtube_started_at'] = time.time()
        session['youtube_user_id'] = str(current_user.get_id())
        return redirect(authorization_url, code=303)


class YoutubeCallbackView(YoutubeActionView):
    methods = ['GET']

    def dispatch_request(self):
        require_oauth_modules()
        from google.auth.exceptions import GoogleAuthError
        from oauthlib.oauth2 import OAuth2Error
        if not current_user.is_authenticated or not current_user.admin:
            abort(403, 'Administrator access is required to connect YouTube.')
        expected = session.pop('youtube_state', None)
        verifier = session.pop('youtube_code_verifier', None)
        started = session.pop('youtube_started_at', None)
        owner = session.pop('youtube_user_id', None)
        supplied = request.args.get('state', '')
        if (not isinstance(expected, str) or not expected or not verifier
                or not hmac.compare_digest(expected.encode('utf-8'), supplied.encode('utf-8'))
                or not isinstance(started, (int, float))
                or not 0 <= time.time() - started <= OAUTH_MAX_AGE
                or owner != str(current_user.get_id())):
            abort(400, 'This YouTube connection request is missing or expired. Start Connect account again.')
        if request.args.get('error'):
            flash('YouTube connection was cancelled or denied. Existing authorization was kept.', 'warning')
            return redirect(url_for('indi_allsky.modern_admin_youtube_view'), code=303)
        if not request.args.get('code'):
            abort(400, 'Google did not return an authorization code. Start Connect account again.')
        flow = self.make_flow(state=expected, code_verifier=verifier)
        try:
            flow.fetch_token(authorization_response=request.url, timeout=NETWORK_TIMEOUT)
            credentials = credentials_to_dict(flow.credentials)
            if not credentials['refresh_token']:
                abort(400, 'Google did not grant offline access. Reconnect and grant the requested access. Existing authorization was kept.')
            self._miscDb.setEncryptedState(CREDENTIALS_KEY, json.dumps(credentials))
        except (OAuth2Error, GoogleAuthError, requests.RequestException):
            abort(502, 'Google authorization failed. Existing authorization was kept. Start Connect account again.')
        except SQLAlchemyError:
            db.session.rollback()
            abort(503, 'YouTube authorization could not be saved. Start Connect account again.')
        finally:
            flow.oauth2session.close()
        return self.finished('YouTube account connected. Uploads follow the enabled categories in Settings.')


class YoutubeRefreshAuthView(YoutubeActionView):
    def perform(self):
        from google.auth.exceptions import GoogleAuthError
        from google.auth.transport.requests import Request
        credentials = load_credentials(self._miscDb)
        if not credentials.refresh_token:
            abort(400, 'This authorization has no refresh token. Reconnect the account.')
        try:
            with requests.Session() as transport:
                adapter = Request(session=transport)
                def bounded_request(*args, **kwargs):
                    kwargs['timeout'] = NETWORK_TIMEOUT
                    return adapter(*args, **kwargs)
                # Old stored credentials omit expiry. An explicit refresh must
                # therefore not depend on Credentials.expired being true.
                credentials.refresh(bounded_request)
            self._miscDb.setEncryptedState(CREDENTIALS_KEY, json.dumps(credentials_to_dict(credentials)))
        except (GoogleAuthError, requests.RequestException):
            abort(502, 'Google could not refresh authorization. Existing authorization was kept; retry or reconnect.')
        return self.finished('YouTube authorization refreshed.')


class YoutubeRevokeAuthView(YoutubeActionView):
    def perform(self):
        credentials = load_credentials(self._miscDb)
        token = credentials.refresh_token or credentials.token
        if not token:
            abort(400, 'No token is available to revoke. Reconnect the account.')
        try:
            with requests.post('https://oauth2.googleapis.com/revoke',
                               data={'token': token}, timeout=NETWORK_TIMEOUT) as response:
                if response.status_code != 200:
                    abort(502, 'Google did not confirm revocation. Stored authorization was kept; retry later.')
        except requests.RequestException:
            abort(502, 'Google revocation could not be confirmed. Stored authorization was kept; retry later.')
        self._miscDb.removeState(CREDENTIALS_KEY)
        return self.finished('YouTube authorization revoked and removed. Uploads require reconnecting an account.')
