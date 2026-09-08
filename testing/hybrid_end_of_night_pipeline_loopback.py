#!/usr/bin/env python3
"""Actual Hybrid request -> coordinator -> VideoWorker -> FileUploader -> SFTP.

Disposable SQLite and loopback SFTP destinations only. The actual worker
methods run synchronously, without production threads, queues or media.
The installed SSH host key is pinned; the password is prompted and never saved.
"""
import argparse
from copy import deepcopy
from datetime import date
import hashlib
import base64
import getpass
import tempfile
import json
from pathlib import Path
from queue import Queue
import re
from types import SimpleNamespace
from unittest.mock import patch
from hybrid_runtime_fixture import isolated_app, login_client
from hybrid_generation_fixture import seed_generation


def run(runtime_config, evidence=None):
    import paramiko
    password=getpass.getpass('Password for isolated loopback SFTP: ')
    key_parts=Path('/etc/ssh/ssh_host_ed25519_key.pub').read_text().split()
    key=paramiko.Ed25519Key(data=base64.b64decode(key_parts[1]))
    actual_client=paramiko.SSHClient
    def trusted_client():
        client=actual_client()
        client.get_host_keys().add('127.0.0.1',key.get_name(),key)
        return client
    results=[]
    with isolated_app(runtime_config, multi_camera=True) as app:
        app.config['ADMIN_NETWORKS']=['127.0.0.0/8']
        seed_generation(app)
        from indi_allsky.flask import db
        from indi_allsky.flask.models import IndiAllSkyDbConfigTable as Config, IndiAllSkyDbTaskQueueTable as Task
        from indi_allsky.flask.models import TaskQueueState as State
        # Real worker modules bind their application to this isolated database.
        with patch('indi_allsky.flask.create_app', return_value=app):
            from indi_allsky.allsky import IndiAllSky
            from indi_allsky.video import VideoWorker
            from indi_allsky.uploader import FileUploader
        with app.app_context():
            config=deepcopy(db.session.get(Config,1).data)
            config['FILETRANSFER']={'UPLOAD_ENDOFNIGHT':True,'REMOTE_ENDOFNIGHT_FOLDER':'pending/{camera_uuid}',
                'HOST':'127.0.0.1','USERNAME':getpass.getuser(),'PASSWORD':'',
                'CERT_BYPASS':False,'CLASSNAME':'paramiko_sftp','PORT':22}
            row=db.session.get(Config,1);row.data=config;db.session.commit()
        coordinator=IndiAllSky.__new__(IndiAllSky)
        coordinator.config=config;coordinator.multi_camera_capture_enable=True
        coordinator.capture_profiles=[SimpleNamespace(profile_id='test-profile-'+str(cid)) for cid in (1,2)]
        coordinator.video_q=Queue()
        uploads=Queue()
        worker=VideoWorker(99,config,Queue(),coordinator.video_q,uploads,[1,0],[1])
        admin=login_client(app,1);reader=login_client(app,2)
        root=Path(app.config['INDI_ALLSKY_IMAGE_FOLDER']).resolve()
        uploader=FileUploader(99,deepcopy(config),Queue(),uploads)
        uploader.config['FILETRANSFER']['PASSWORD']=password
        temp_file=tempfile.NamedTemporaryFile
        sentinel=root/'unrelated.txt';sentinel.write_text('untouched disposable sentinel')
        for cid in (1,2):
            for succeeds in (True,False):
                destination=root/f'destination-{cid}-{succeeds}'
                destination.mkdir()
                if not succeeds:destination.chmod(0o500)
                worker.config['FILETRANSFER']['REMOTE_ENDOFNIGHT_FOLDER']=str(destination/'{camera_uuid}')
                page=admin.get('/indi-allsky/modern-admin/tools/generate?camera_id='+str(cid))
                assert page.status_code==200
                token=re.search(r'name="csrf_token"[^>]*value="([^"]+)"',page.text)[1]
                response=admin.post('/indi-allsky/ajax/generate',json={'CAMERA_ID':str(cid),'ACTION_SELECT':'upload_endofnight','DAY_SELECT':str(date.today())+'_night'},headers={'X-CSRFToken':token})
                assert response.status_code==200,response.text
                try:
                    with app.app_context():
                        parent=Task.query.order_by(Task.id.desc()).first();parent_id=parent.id
                        assert parent.state==State.MANUAL
                        coordinator._queueManualTasks();db.session.refresh(parent)
                        assert parent.state==State.QUEUED,(parent.state,parent.result)
                        message=coordinator.video_q.get_nowait()
                        assert message['camera_id']==cid and message['profile_id']==f'test-profile-{cid}'
                        with patch.object(tempfile,'NamedTemporaryFile',side_effect=lambda **kw:temp_file(dir=root,**kw)):
                            worker.processTask(message)
                        db.session.refresh(parent)
                        assert parent.state==State.SUCCESS,parent.result
                        child_message=uploads.get_nowait()
                        receipt=parent.data['end_of_night_upload']
                        assert child_message['task_id']==receipt['task_id']
                        assert child_message['camera_id']==cid and child_message['profile_id']==f'test-profile-{cid}'
                        child=db.session.get(Task,child_message['task_id']);child_id=child.id
                        source=Path(child.data['local_file']);content=source.read_bytes()
                        payload=json.loads(content)
                        assert set(payload)=={'sunrise','sunset','streamDaytime'}
                        remote=Path(child.data['remote_file'])
                        assert remote==destination/f'test-camera-{cid}'/'data.json'
                        with patch('paramiko.SSHClient',side_effect=trusted_client):
                            uploader.processUpload(child_message)
                        db.session.refresh(child)
                        expected=State.SUCCESS if succeeds else State.FAILED
                        assert child.state==expected,(child.state,child.result)
                        assert remote.is_file()==succeeds
                        if succeeds:assert remote.read_bytes()==content
                        assert not source.exists()  # Existing remove_local=True cleanup semantics.
                        assert uploads.empty() and coordinator.video_q.empty()
                        assert sentinel.read_text()=='untouched disposable sentinel'
                        # A terminal delivery cannot issue a second network transfer.
                        with patch('paramiko.SSHClient',side_effect=AssertionError('Duplicate transfer')):
                            uploader.processUpload(child_message)
                        assert child.state==expected
                    for client in (admin,reader):
                        page=client.get('/indi-allsky/modern-admin/tasks/'+str(parent_id))
                        assert page.status_code==200 and f'Inspect upload task {child_id}' in page.text
                        page=client.get('/indi-allsky/modern-admin/tasks/'+str(child_id))
                        assert page.status_code==200 and expected.name in page.text and f'test-profile-{cid}' in page.text
                    results.append({'camera_id':cid,'profile_id':message['profile_id'],'parent_task':parent_id,'upload_task':child_id,'upload_state':expected.name,'delivered':succeeds,'host_key_verified':True,'destination_scope':'temporary loopback folder','bytes':len(content) if succeeds else 0,'payload_sha256':hashlib.sha256(content).hexdigest(),'duplicate_transfer_blocked':True})
                finally:
                    destination.chmod(0o700)
        uploader.config['FILETRANSFER']['PASSWORD']=None;password=None
    report={'scope':'Actual Hybrid requests, coordinator, video/upload workers and loopback SFTP on disposable fixtures with Classic disabled; not production daemon or external endpoint acceptance','results':results}
    if evidence:Path(evidence).write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--runtime-config',default='/etc/indi-allsky/flask.json')
    parser.add_argument('--evidence')
    args=parser.parse_args();run(args.runtime_config,args.evidence)
