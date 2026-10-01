#!/usr/bin/env python3
"""Actual upload boundary with isolated DB and non-network effect adapter."""
import ast
from datetime import timedelta
import logging
from pathlib import Path
from types import MethodType, SimpleNamespace
import time
from hybrid_runtime_fixture import isolated_app


def run():
    with isolated_app(multi_camera=True) as app, app.app_context():
        from sqlalchemy.orm.exc import NoResultFound
        from indi_allsky import constants
        from indi_allsky.flask import db, models
        from indi_allsky.task_claim import claim_upload_task
        Task, State, Queue = models.IndiAllSkyDbTaskQueueTable, models.TaskQueueState, models.TaskQueueQueue
        path = Path(__file__).resolve().parents[1] / 'indi_allsky/uploader.py'
        tree = ast.parse(path.read_text())
        methods = [n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)
                   and n.name in ('processUpload', '_executeUpload')]
        events = []
        mode = ['success']
        class Client:
            def __init__(self, config, **kwargs):
                events.append(('create', kwargs))
            def connect(self, **kwargs):
                events.append(('connect', None))
                if mode[0] == 'connect':
                    raise RuntimeError('synthetic unexpected connection error')
            def put(self, **kwargs):
                events.append(('put', kwargs))
                if mode[0] == 'put':
                    raise RuntimeError('synthetic unexpected transfer error')
                return {'id': 12}
            def close(self):
                events.append(('close', None))
        errors = SimpleNamespace(**{name: type(name, (Exception,), {}) for name in
            ('ConnectionFailure', 'AuthenticationFailure', 'CertificateValidationFailure',
             'TransferFailure', 'PermissionFailure')})
        ns = dict(constants=constants, db=db, models=models, claim_upload_task=claim_upload_task,
                  logger=logging.getLogger('upload-test'), Path=Path, time=time,
                  timedelta=timedelta, NoResultFound=NoResultFound,
                  filetransfer=SimpleNamespace(test_client=Client, exceptions=errors))
        exec(compile(ast.fix_missing_locations(ast.Module(body=methods, type_ignores=[])), str(path), 'exec'), ns)
        config = {'FILETRANSFER': {'HOST':'fixture.invalid','USERNAME':'','PASSWORD':'','CLASSNAME':'test_client','PORT':0},
                  'S3UPLOAD': {'ACCESS_KEY':'','SECRET_KEY':'','REGION':'','HOST':'fixture.invalid','TLS':True,
                               'CERT_BYPASS':False,'BUCKET':'fixture','CLASSNAME':'test_client','PORT':0}}
        root = Path(app.config['INDI_ALLSKY_IMAGE_FOLDER'])
        source = root / 'upload-failure-fixture.dat'
        source.write_bytes(b'disposable isolated upload source')
        worker = SimpleNamespace(config=config, image_dir=root,
                    _validate_profile_id=lambda payload: payload.get('profile_id', 'default'),
                    _set_queue_context=lambda *a, **k: None,
                    cleanup=lambda *a, **k: events.append(('cleanup', a)),
                    _miscDb=SimpleNamespace(addNotification=lambda *a, **k: None))
        if '_executeUpload' in ns:
            worker._executeUpload = MethodType(ns['_executeUpload'], worker)
        def execute(data, expected):
            task = Task(queue=Queue.UPLOAD, state=State.QUEUED, data=data)
            db.session.add(task); db.session.commit()
            ns['processUpload'](worker, {'task_id': task.id, 'profile_id':'test-profile-2', 'camera_id':2})
            db.session.refresh(task)
            assert task.state == expected, task.result
            before = list(events)
            ns['processUpload'](worker, {'task_id': task.id})
            assert events == before, 'terminal task executed twice'
            assert source.read_bytes() == b'disposable isolated upload source'
            return task
        for invalid in ({}, [], {'action': constants.TRANSFER_UPLOAD, 'local_file': str(source)}):
            execute(invalid, State.FAILED)
        payload = {'action':constants.TRANSFER_UPLOAD, 'local_file':str(source), 'remote_file':'test.dat'}
        for failure in ('connect', 'put'):
            mode[0] = failure; events.clear()
            execute(payload, State.FAILED)
            assert ('close', None) in events, failure
        mode[0] = 'success'; events.clear()
        original_context = worker._set_queue_context
        original_name = db.session.get(models.IndiAllSkyDbCameraTable, 2).name
        def fail_context(*args, **kwargs):
            db.session.get(models.IndiAllSkyDbCameraTable, 2).name = 'must roll back'
            raise RuntimeError('synthetic context setup failure')
        worker._set_queue_context = fail_context
        execute(payload, State.FAILED)
        assert not events
        assert db.session.get(models.IndiAllSkyDbCameraTable, 2).name == original_name
        worker._set_queue_context = original_context
        execute(payload, State.SUCCESS)
        events.clear()
        task = execute({'action':constants.DELETE_S3, 's3_key':'test-only/key', 'remove_local':True}, State.SUCCESS)
        assert ('create', {'delete': True}) in events
        assert next(value for name,value in events if name == 'put')['key'] == 'test-only/key'
        assert not any(name == 'cleanup' for name, _ in events)
        assert task.result == 'Remote file deleted'
        print('Upload boundary: invalid data, unexpected connect/put errors close client, terminal task replay ignored, next job succeeds, S3 delete has no local effect PASS')


if __name__ == '__main__':
    run()
