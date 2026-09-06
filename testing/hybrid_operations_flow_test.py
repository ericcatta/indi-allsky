#!/usr/bin/env python3
"""Real Hybrid task/notification HTTP flows without Classic or external effects."""
import argparse
import re
import json
import io
from zipfile import ZipFile
from unittest.mock import patch
from hybrid_runtime_fixture import isolated_app, login_client
from hybrid_operations_fixture import seed_operations


def run(runtime_config):
    with isolated_app(runtime_config, multi_camera=True) as app:
        seed_operations(app)
        from indi_allsky.flask import db
        from indi_allsky.flask.models import IndiAllSkyDbNotificationTable, IndiAllSkyDbTaskQueueTable
        for uid in (1,2):
            client = login_client(app, uid)
            for camera in (1,2):
                for route in ('tasks','tasks/205','notifications','notifications/1'):
                    response = client.get('/indi-allsky/modern-admin/'+route+'?camera_id='+str(camera))
                    assert response.status_code == 200, (route,response.status_code)
                    assert 'Open legacy' not in response.text
            tasks = client.get('/indi-allsky/modern-admin/tasks')
            assert tasks.text.count('class="modern-admin-task-row"') == 205
            assert '/modern-admin/tasks/205' in tasks.text
            detail = client.get('/indi-allsky/modern-admin/tasks/205')
            assert 'test-profile-1' in detail.text and '&lt;redacted&gt;' in detail.text
            assert 'synthetic-secret-must-be-redacted' not in detail.text
            for route in ('tasks/9999','notifications/9999'):
                assert client.get('/indi-allsky/modern-admin/'+route).status_code == 404
        # Same permission as the old modal: any authenticated user can ack a
        # system-wide notice. The URL identifies the target, not camera state.
        detail = client.get('/indi-allsky/modern-admin/notifications/1')
        token = re.search(r'name="csrf_token" value="([^"]+)"',detail.text)[1]
        url = '/indi-allsky/modern-admin/notifications/1/acknowledge'
        headers={'X-CSRFToken':token}
        assert client.get(url).status_code == 405
        assert client.post(url,json={}).status_code == 400
        assert client.post(url,json=[],headers=headers).status_code == 400
        result = client.post(url,json={},headers=headers)
        assert result.status_code == 200 and result.json['status']=='acknowledged'
        repeat = client.post(url,json={},headers=headers)
        assert repeat.status_code == 200 and repeat.json['status']=='already_acked'
        assert 'already acknowledged' in client.get('/indi-allsky/modern-admin/notifications/1').text
        with app.app_context():
            assert db.session.get(IndiAllSkyDbNotificationTable,1).ack
            assert not db.session.get(IndiAllSkyDbNotificationTable,2).ack
            assert IndiAllSkyDbTaskQueueTable.query.count() == 205
        export_url='/indi-allsky/modern-admin/operations/export'
        data={'table':json.dumps({'header':['ID','Result'],'body':[['205','Synthetic result 205']]}),'format':'csv','csrf_token':token}
        exported=client.post(export_url,data=data)
        assert exported.status_code == 200 and b'Synthetic result 205' in exported.data
        assert 'attachment' in exported.headers['Content-Disposition']
        data['format']='xlsx'
        workbook=client.post(export_url,data=data)
        assert workbook.status_code==200
        with ZipFile(io.BytesIO(workbook.data)) as archive:
            assert b'Synthetic result 205' in archive.read('xl/worksheets/sheet1.xml')
        assert client.post(export_url,data={'table':data['table'],'format':'csv'}).status_code==400
        assert client.post(export_url,data={'table':'{}','format':'csv','csrf_token':token}).status_code==400
        missing = client.post('/indi-allsky/modern-admin/notifications/9999/acknowledge',json={},headers=headers)
        assert missing.status_code == 404 and missing.json['status']=='not_found'
        with patch.object(IndiAllSkyDbNotificationTable,'setAck',side_effect=RuntimeError('private backend detail')):
            failed = client.post('/indi-allsky/modern-admin/notifications/2/acknowledge',json={},headers=headers)
        assert failed.status_code == 500 and failed.json['status']=='acknowledge_failed'
        assert 'private backend detail' not in failed.text
        with app.app_context():
            assert not db.session.get(IndiAllSkyDbNotificationTable,2).ack
        anonymous=app.test_client()
        assert anonymous.get('/indi-allsky/modern-admin/notifications').status_code == 302
        login=anonymous.get('/indi-allsky/login')
        anon_token=re.search(r'name="csrf_token"[^>]*value="([^"]+)"',login.text)[1]
        assert anonymous.post(url,json={},headers={'X-CSRFToken':anon_token}).status_code == 302
        for asset in ('notification-ack.js','operations-table.js'):
            assert client.get('/indi-allsky/static/modern_admin/'+asset).status_code == 200
        print('Hybrid task/notification listing, details, roles, acknowledgement, idempotency, CSRF and failed effects: PASS')

if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--runtime-config',default='/etc/indi-allsky/flask.json')
    run(parser.parse_args().runtime_config)
