#!/usr/bin/env python3
"""Real Settings save/download/restore through Hybrid with isolated persistence."""
import argparse
from html.parser import HTMLParser
import io
import json
import re
from hybrid_runtime_fixture import isolated_app, login_client

class BrowserValues(HTMLParser):
    def __init__(self, html):
        super().__init__()
        self.values = {}
        self.checks = {}
        self.select = None
        self.option = None
        self.textarea = None
        self.feed(html)
    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == 'input' and a.get('id'):
            self.values[a['id']] = a.get('value', '')
            self.checks[a['id']] = 'checked' in a
        elif tag == 'select':
            self.select = a.get('id')
        elif tag == 'option' and self.select:
            self.option = {'value':a.get('value'), 'text':'', 'selected':'selected' in a}
        elif tag == 'textarea':
            self.textarea = a.get('id')
            if self.textarea:
                self.values[self.textarea] = ''
    def handle_data(self, value):
        if self.textarea:
            self.values[self.textarea] += value
        if self.option is not None:
            self.option['text'] += value
    def handle_endtag(self, tag):
        if tag == 'textarea':
            self.textarea = None
        if tag == 'option' and self.select and self.option is not None:
            if self.select not in self.values or self.option['selected']:
                self.values[self.select] = self.option['value'] if self.option['value'] is not None else self.option['text']
            self.option = None
        if tag == 'select':
            self.select = None

def payload_from_page(html):
    values = BrowserValues(html)
    config = json.loads(re.search(r'<script type="application/json" id="hybrid-full-settings-config">(.*?)</script>', html, re.S)[1])
    fields = config['fieldNames']
    checks = set(config['checkboxNames'])
    payload = {name: values.checks.get(name,False) if name in checks else values.values[name]
               for name in fields if name in values.values}
    token = config['csrfToken']
    return payload, token

def run(runtime_config):
    with isolated_app(runtime_config, multi_camera=True) as app:
        client = login_client(app, 1)
        page = client.get('/indi-allsky/modern-admin/settings/full')
        assert page.status_code == 200
        payload, token = payload_from_page(page.text)
        from urllib.parse import urlsplit, parse_qs
        for slug, sample in (('storage','HEALTHCHECK__DISK_USAGE'), ('analytics','CHARTS__CUSTOM_SLOT_1'), ('acquisition-save','IMAGE_FILE_TYPE'), ('fits-source','IMAGE_SAVE_FITS')):
            entry = client.get('/indi-allsky/modern-admin/settings/' + slug + '?camera_id=2&profile_id=test-profile-2&domain=invalid')
            assert entry.status_code == 302
            target = urlsplit(entry.location)
            assert parse_qs(target.query) == {'camera_id':['2'], 'profile_id':['test-profile-2'], 'domain':[slug]}
            scoped = client.get(entry.location)
            assert scoped.status_code == 200 and 'settings-domain-only' in scoped.text
            scoped_payload, scoped_token = payload_from_page(scoped.text)
            assert scoped_payload.keys() == payload.keys(), slug
            # Flask-WTF signs a fresh timestamp; compare configuration, not the CSRF signature.
            assert {k:v for k,v in scoped_payload.items() if k != 'csrf_token'} == {k:v for k,v in payload.items() if k != 'csrf_token'}, slug
            metadata = json.loads(re.search(r'id="hybrid-full-settings-config">(.*?)</script>', scoped.text, re.S)[1])
            assert sample in metadata['focusFields'], (slug, metadata['focusFields'])
            assert set(metadata['focusFields']) <= set(metadata['fieldNames'])
        # Save the complete payload collected from a focused view, including fields outside its group.
        payload, token = scoped_payload, scoped_token
        payload.update(CONFIG_NOTE='Acceptance save', RELOAD_ON_SAVE=False, OWNER='Acceptance observer')
        headers = {'X-CSRFToken':token}
        from indi_allsky.flask import db
        from indi_allsky.flask.models import IndiAllSkyDbConfigTable, IndiAllSkyDbTaskQueueTable
        from copy import deepcopy
        with app.app_context():
            original = deepcopy(db.session.get(IndiAllSkyDbConfigTable, 1).data)
        assert client.post('/indi-allsky/ajax/config', json=payload).status_code == 400
        invalid = dict(payload, IMAGE_SCALE='invalid')
        assert client.post('/indi-allsky/ajax/config', json=invalid, headers=headers).status_code == 400
        response = client.post('/indi-allsky/ajax/config', json=payload, headers=headers)
        assert response.status_code == 200, response.json
        from indi_allsky.flask import db
        from indi_allsky.flask.models import IndiAllSkyDbConfigTable, IndiAllSkyDbTaskQueueTable
        with app.app_context():
            assert IndiAllSkyDbConfigTable.query.count() == 2
            assert IndiAllSkyDbTaskQueueTable.query.count() == 0
            saved = IndiAllSkyDbConfigTable.query.order_by(IndiAllSkyDbConfigTable.id.desc()).first()
            assert saved.note == 'Acceptance save'
            assert saved.data['OWNER'] == 'Acceptance observer'
            assert saved.data['MULTI_CAMERA'] == original['MULTI_CAMERA']
            assert db.session.get(IndiAllSkyDbConfigTable, 1).data == original
            saved_id = saved.id
        download_url = '/indi-allsky/config/download?id=' + str(saved_id)
        assert app.test_client().get(download_url).status_code == 302
        assert login_client(app, 2).get(download_url).status_code == 403
        assert login_client(app, 2).get(download_url + '&redact=1').status_code == 403
        with app.app_context():
            source_entry = db.session.get(IndiAllSkyDbConfigTable, saved_id)
            before_redaction = deepcopy(source_entry.data)
            redacted = client.get(download_url + '&redact=1')
            assert redacted.status_code == 200
            assert json.loads(redacted.data)['FILETRANSFER']['PASSWORD'] == 'REDACTED'
            assert source_entry.data == before_redaction
        downloaded = client.get(download_url)
        assert downloaded.status_code == 200
        for content in (b'', b'invalid JSON', b'{}', b' ' * 100001):
            invalid_restore = client.post('/indi-allsky/ajax/config/restore', headers=headers, data={
                'CONFIG_UPLOAD':(io.BytesIO(content),'invalid.json'), 'csrf_token':token})
            assert invalid_restore.status_code == 400
        with app.app_context():
            assert IndiAllSkyDbConfigTable.query.count() == 2
        restored = client.post('/indi-allsky/ajax/config/restore', headers=headers, data={
            'CONFIG_UPLOAD':(io.BytesIO(downloaded.data),'acceptance.json'),
            'RESET_KEYS':'', 'FLUSH_CONFIGS':'', 'csrf_token':token})
        assert restored.status_code == 200, restored.json
        with app.app_context():
            assert IndiAllSkyDbConfigTable.query.count() == 3
            latest = IndiAllSkyDbConfigTable.query.order_by(IndiAllSkyDbConfigTable.id.desc()).first()
            assert latest.data['OWNER'] == 'Acceptance observer'
            assert latest.data['MULTI_CAMERA'] == original['MULTI_CAMERA']
            assert IndiAllSkyDbTaskQueueTable.query.count() == 0
        ordinary = login_client(app, 2)
        readonly = ordinary.get('/indi-allsky/modern-admin/settings/full')
        _, ordinary_token = payload_from_page(readonly.text)
        assert re.search(r'<fieldset[^>]*disabled', readonly.text)
        assert 'administrator account is required' in readonly.text
        assert ordinary.post('/indi-allsky/ajax/config', json=payload, headers={'X-CSRFToken':ordinary_token}).status_code == 400
        assert ordinary.post('/indi-allsky/ajax/config/restore', data={
            'CONFIG_UPLOAD':(io.BytesIO(downloaded.data),'acceptance.json')},
            headers={'X-CSRFToken':ordinary_token}).status_code == 400
        with app.app_context():
            assert IndiAllSkyDbConfigTable.query.count() == 3
        snapshot_url = '/indi-allsky/modern-admin/config-restore/1/apply'
        snapshot_payload = {'CONFIRM_RESTORE':'yes', 'EXPECTED_CONFIG_ID':'3'}
        assert client.get(snapshot_url).status_code == 405
        assert client.post(snapshot_url, data=snapshot_payload).status_code == 400
        assert client.post(snapshot_url, data={'EXPECTED_CONFIG_ID':'3'}, headers=headers).status_code == 400
        assert ordinary.post(snapshot_url, data=snapshot_payload, headers={'X-CSRFToken':ordinary_token}).status_code == 403
        assert client.post(snapshot_url, data=dict(snapshot_payload, EXPECTED_CONFIG_ID='2'), headers=headers).status_code == 409
        result = client.post(snapshot_url, data=snapshot_payload, headers=headers)
        assert result.status_code == 200 and 'revision 4' in result.json['success-message'], result.json
        assert client.post(snapshot_url, data=snapshot_payload, headers=headers).status_code == 409
        with app.app_context():
            restored = db.session.get(IndiAllSkyDbConfigTable, 4)
            assert restored.data['MULTI_CAMERA'] == original['MULTI_CAMERA']
            assert restored.data['OWNER'] == original['OWNER']
            assert restored.note == 'Restored internal snapshot 1'
            assert db.session.get(IndiAllSkyDbConfigTable, 1).data == original
            assert IndiAllSkyDbTaskQueueTable.query.count() == 0
            # Encrypted internal snapshots must retain secrets without mutating history.
            from indi_allsky.modern_admin_settings_runtime import ModernAdminSettingsCredentialEncryptionService, ModernAdminSettingsCredentialDecryptionService
            encrypted_source = deepcopy(original)
            encrypted_source['ENCRYPT_PASSWORDS'] = True
            encrypted_source['FILETRANSFER']['PASSWORD'] = 'synthetic-snapshot-secret'
            encrypted, _ = ModernAdminSettingsCredentialEncryptionService(lambda: app.config['PASSWORD_KEY']).encrypt_config(encrypted_source)
            db.session.get(IndiAllSkyDbConfigTable, 1).data = encrypted
            db.session.commit()
            encrypted_before = deepcopy(encrypted)
        result = client.post(snapshot_url, data=dict(snapshot_payload, EXPECTED_CONFIG_ID='4'), headers=headers)
        assert result.status_code == 200, result.json
        with app.app_context():
            saved = deepcopy(db.session.get(IndiAllSkyDbConfigTable, 5).data)
            clear = ModernAdminSettingsCredentialDecryptionService(lambda: app.config['PASSWORD_KEY']).decrypt_config(saved)
            assert clear['FILETRANSFER']['PASSWORD'] == 'synthetic-snapshot-secret'
            assert db.session.get(IndiAllSkyDbConfigTable, 1).data == encrypted_before
            assert IndiAllSkyDbTaskQueueTable.query.count() == 0
        print('Hybrid full Settings save/download/upload restore and internal snapshot restore: PASS')

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--runtime-config', default='/etc/indi-allsky/flask.json')
    run(parser.parse_args().runtime_config)
