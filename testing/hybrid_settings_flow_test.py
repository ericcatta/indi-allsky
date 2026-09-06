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
        downloaded = client.get('/indi-allsky/config/download?id='+str(saved_id))
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
        print('Hybrid full Settings save/download/restore with real isolated persistence: PASS')

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--runtime-config', default='/etc/indi-allsky/flask.json')
    run(parser.parse_args().runtime_config)
