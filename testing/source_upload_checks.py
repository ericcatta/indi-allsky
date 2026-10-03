"""Upload worker checks using the real FITS fixture supplied by replay tests."""
import ast
from copy import deepcopy
from datetime import timedelta
import io
import logging
from pathlib import Path
import time
from types import MethodType, SimpleNamespace


def check_source_upload(entry, source, root, expected):
    import numpy as np
    from PIL import Image
    from sqlalchemy.orm.exc import NoResultFound
    from indi_allsky import constants
    from indi_allsky.config import IndiAllSkyConfigBase
    from indi_allsky.flask import db, models
    from indi_allsky.source_upload import source_upload_file
    from indi_allsky.task_claim import claim_upload_task
    Task, State, Queue = models.IndiAllSkyDbTaskQueueTable, models.TaskQueueState, models.TaskQueueQueue
    original = source.read_bytes()
    filename, data = entry.filename, deepcopy(entry.data)
    metadata = {'type': constants.IMAGE, 'fileSize': 0, 'data': deepcopy(data)}
    metadata['data']['render_source'] = {'local-only': True}
    before = deepcopy(metadata)
    for extension, format_name in [('jpg','JPEG'), ('jpeg','JPEG'), ('png','PNG'),
                                   ('webp','WEBP'), ('tif','TIFF'), ('tiff','TIFF')]:
        entry.filename = str(root / ('upload-fixture.' + extension))
        with source_upload_file(entry, root, metadata) as (path, exported):
            assert path.suffix == '.' + extension
            with Image.open(path) as image:
                assert image.format == format_name
                assert image.size == (expected.shape[1], expected.shape[0])
                if extension in ('png','tif','tiff'):
                    np.testing.assert_array_equal(np.array(image), expected[:,:,::-1])
            assert exported['fileSize'] == exported['file_size'] == path.stat().st_size
            assert not any(k in exported['data'] for k in ('storage_format','source_fits_id','render_source'))
        assert not path.exists()
        assert metadata == before and entry.data == data and source.read_bytes() == original
    entry.filename = filename
    db.session.commit()
    code_path = Path(__file__).resolve().parents[1] / 'indi_allsky/uploader.py'
    methods = [n for n in ast.walk(ast.parse(code_path.read_text()))
               if isinstance(n, ast.FunctionDef) and n.name in ('processUpload','_executeUpload')]
    events, transfers, handoffs = [], [], []
    fail = [False]
    class Client:
        def __init__(self, *args, **kwargs): pass
        def connect(self, **kwargs): events.append('connect')
        def close(self): events.append('close')
        def put(self, **kwargs):
            path = kwargs['local_file']
            assert path.is_file() and path != Path(entry.filename)
            with Image.open(path) as image:
                assert image.format == 'JPEG'
            transferred = deepcopy(kwargs)
            transferred['bytes'] = path.read_bytes()
            transfers.append(transferred)
            if fail[0]: raise RuntimeError('Synthetic transfer failure')
            return {'id': 987}
    errors = SimpleNamespace(**{name: type(name, (Exception,), {}) for name in
        ('ConnectionFailure','AuthenticationFailure','CertificateValidationFailure','TransferFailure','PermissionFailure')})
    ns = dict(__name__='indi_allsky.uploader', __package__='indi_allsky',
              constants=constants, db=db, models=models, claim_upload_task=claim_upload_task,
              logger=logging.getLogger('upload-source-test'), Path=Path, time=time,
              timedelta=timedelta, NoResultFound=NoResultFound,
              filetransfer=SimpleNamespace(test_client=Client, requests_syncapi_v1=Client,
                                           paho_mqtt=Client, exceptions=errors))
    exec(compile(ast.fix_missing_locations(ast.Module(body=methods,type_ignores=[])),str(code_path),'exec'),ns)
    config = deepcopy(IndiAllSkyConfigBase().base_config)
    for section in ('FILETRANSFER','S3UPLOAD','MQTTPUBLISH'):
        config[section].update(HOST='fixture.invalid', CLASSNAME='test_client')
    worker = SimpleNamespace(config=config,image_dir=root,
        _validate_profile_id=lambda payload: 'test', _set_queue_context=lambda *a,**k: None,
        cleanup=lambda *a,**k: events.append('cleanup'),
        _syncapi=lambda item,meta: handoffs.append(deepcopy(meta)),
        _miscDb=SimpleNamespace(addNotification=lambda *a,**k: None))
    worker._executeUpload=MethodType(ns['_executeUpload'],worker)
    for action in (constants.TRANSFER_UPLOAD,constants.TRANSFER_S3,
                   constants.TRANSFER_SYNC_V1,constants.TRANSFER_MQTT):
        for failure in (False,True):
            fail[0]=failure; events.clear(); transfers.clear()
            payload=dict(action=action,model=type(entry).__name__,id=entry.id,
                         remote_file='night/display.jpg',metadata=deepcopy(metadata))
            task=Task(queue=Queue.UPLOAD,state=State.QUEUED,data=payload)
            db.session.add(task);db.session.commit()
            ns['processUpload'](worker,{'task_id':task.id})
            assert task.state == (State.FAILED if failure else State.SUCCESS), task.result
            assert 'close' in events and len(transfers)==1
            sent=transfers[0]
            assert not sent['local_file'].exists()
            if action==constants.TRANSFER_S3:
                assert sent['key']==Path(filename).relative_to(root).as_posix()
                if not failure: assert handoffs[-1]['data']=={}
            for key in ('metadata','mq_data'):
                if key in sent: assert sent[key]['data']=={}
            assert entry.data==data and task.data==payload
            previous=list(events)
            ns['processUpload'](worker,{'task_id':task.id})
            assert events==previous
            assert source.read_bytes()==original
    # Invalid references must fail before sending any bytes and release the client.
    for identity in (True, -1, 2**64, 999999):
        entry.data={**data, 'source_fits_id':identity};db.session.commit()
        events.clear();transfers.clear();fail[0]=False
        task=Task(queue=Queue.UPLOAD,state=State.QUEUED,data=dict(
            action=constants.TRANSFER_UPLOAD,model=type(entry).__name__,id=entry.id,
            remote_file='night/display.jpg',metadata=deepcopy(metadata)))
        db.session.add(task);db.session.commit()
        ns['processUpload'](worker,{'task_id':task.id})
        assert task.state==State.FAILED and not transfers and 'close' in events
    entry.data=data;db.session.commit()
    assert source.read_bytes()==original
    print('Source upload: real rendered bytes in all formats, FTP/S3/Sync/MQTT worker paths, metadata isolation, failure cleanup, duplicate claims PASS')
