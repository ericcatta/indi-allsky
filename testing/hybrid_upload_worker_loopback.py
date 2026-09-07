#!/usr/bin/env python3
"""Actual upload method, SQLite and SFTP; only disposable loopback destinations.

Does not start the worker thread or production Flask app. The four unmodified
worker methods are compiled from source inside the Classic-disabled fixture.
This verifies synchronous task execution, not queue scheduling or external hosts.
"""
import argparse
import ast
import base64
from datetime import datetime, timedelta, timezone
import getpass
import hashlib
import json
import logging
from pathlib import Path
import time
from unittest.mock import patch

from hybrid_runtime_fixture import isolated_app, login_client


def run(output):
    import paramiko
    password = getpass.getpass('Raspberry password for disposable loopback upload: ')
    key_parts = Path('/etc/ssh/ssh_host_ed25519_key.pub').read_text().split()
    key = paramiko.Ed25519Key(data=base64.b64decode(key_parts[1]))
    original_client = paramiko.SSHClient

    def trusted_client():
        client = original_client()
        client.get_host_keys().add('127.0.0.1', key.get_name(), key)
        return client

    report = {'observed_at': datetime.now(timezone.utc).isoformat(),
              'scope': 'Actual synchronous upload worker method; isolated SQLite, Classic disabled, real loopback SFTP; no queue scheduler or external destination acceptance',
              'cert_bypass': False, 'checks': []}
    with isolated_app(multi_camera=True) as app:
        from sqlalchemy.orm.exc import NoResultFound
        from indi_allsky import constants, filetransfer
        from indi_allsky.flask import db, models
        from indi_allsky.flask.miscDb import miscDb
        from indi_allsky.task_claim import claim_upload_task
        source = (Path(__file__).resolve().parents[1] / 'indi_allsky/uploader.py').read_text()
        tree = ast.parse(source)
        cls = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == 'FileUploader')
        names = {'processUpload', 'cleanup', '_validate_profile_id', '_set_queue_context'}
        methods = [n for n in cls.body if isinstance(n, ast.FunctionDef) and n.name in names]
        assert len(methods) == len(names)
        namespace = dict(claim_upload_task=claim_upload_task, Path=Path, time=time, timedelta=timedelta, constants=constants,
                         filetransfer=filetransfer, db=db, models=models,
                         NoResultFound=NoResultFound, logger=logging.getLogger('upload-acceptance'))
        exec(compile(ast.fix_missing_locations(ast.Module(body=methods, type_ignores=[])), 'uploader.py', 'exec'), namespace)
        worker = type('ActualUploadMethods', (), {name: namespace[name] for name in names})()
        worker.config = {'FILETRANSFER': {'HOST': '127.0.0.1', 'USERNAME': getpass.getuser(),
                         'PASSWORD': password, 'CERT_BYPASS': False, 'CLASSNAME': 'paramiko_sftp', 'PORT': 22}}
        worker._miscDb = miscDb(worker.config)
        root = Path(app.config['INDI_ALLSKY_IMAGE_FOLDER'])
        untouched = root / 'unrelated-media.jpg'
        untouched.write_bytes(b'unrelated disposable sentinel')
        checks = []
        with app.app_context(), patch('paramiko.SSHClient', side_effect=trusted_client):
            for camera_id in (1, 2):
                for succeeds in (True, False):
                    for remove_local in (False, True):
                        label = f'camera-{camera_id}-success-{succeeds}-remove-{remove_local}'
                        local = root / (label + '.json')
                        content = json.dumps({'camera_id': camera_id, 'profile_id': f'test-profile-{camera_id}'}).encode()
                        local.write_bytes(content)
                        destination = root / ('destination-' + label)
                        destination.mkdir()
                        if not succeeds:
                            destination.chmod(0o500)
                        remote = destination / 'data.json'
                        task = models.IndiAllSkyDbTaskQueueTable(queue=models.TaskQueueQueue.UPLOAD,
                            state=models.TaskQueueState.QUEUED, data={'action': constants.TRANSFER_UPLOAD,
                            'local_file': str(local), 'remote_file': str(remote), 'remove_local': remove_local,
                            'camera_id': camera_id, 'profile_id': f'test-profile-{camera_id}'})
                        db.session.add(task)
                        db.session.commit()
                        task_id = task.id
                        try:
                            worker.processUpload({'task_id': task_id, 'camera_id': camera_id,
                                                  'profile_id': f'test-profile-{camera_id}'})
                        finally:
                            destination.chmod(0o700)
                        db.session.expire_all()
                        task = db.session.get(models.IndiAllSkyDbTaskQueueTable, task_id)
                        expected = models.TaskQueueState.SUCCESS if succeeds else models.TaskQueueState.FAILED
                        assert task.state == expected, (label, task.state, task.result)
                        assert remote.exists() == succeeds
                        if succeeds:
                            assert remote.read_bytes() == content
                        assert local.exists() == (not remove_local)
                        assert untouched.read_bytes() == b'unrelated disposable sentinel'
                        assert worker.current_camera_id == camera_id and worker.profile_id == f'test-profile-{camera_id}'
                        assert task.data['camera_id'] == camera_id
                        # A duplicate delivery of a terminal task must not upload again.
                        if succeeds:
                            remote.unlink()
                        worker.processUpload({'task_id': task_id, 'camera_id': camera_id,
                                              'profile_id': f'test-profile-{camera_id}'})
                        assert not remote.exists()
                        checks.append((task_id, expected.name, label))
                        report['checks'].append({'case': label, 'status': 'superato', 'task_state': expected.name,
                            'source_retained': not remove_local, 'sha256': hashlib.sha256(content).hexdigest(),
                            'terminal_duplicate_ignored': True})
            assert models.IndiAllSkyDbNotificationTable.query.filter_by(item='filetransfer').count() > 0
        for user in (1, 2):
            client = login_client(app, user)
            for task_id, state, label in checks:
                response = client.get(f'/indi-allsky/modern-admin/tasks/{task_id}')
                assert response.status_code == 200 and state in response.text, (user, label)
        worker.config['FILETRANSFER']['PASSWORD'] = None
        password = None
    assert not root.exists()
    report['checks'].append({'case': 'admin/ordinary task results, failure notification and disposable cleanup', 'status': 'superato'})
    output.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    run(parser.parse_args().output)
