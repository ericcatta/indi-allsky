#!/usr/bin/env python3
"""Actual EndOfNight preparation and linked delivery task; no network upload."""
import ast
from datetime import datetime,timedelta,timezone
import json,logging,math,tempfile
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock,patch
from hybrid_runtime_fixture import isolated_app


def run():
    with isolated_app(multi_camera=True) as app:
        import ephem
        from indi_allsky import constants
        from indi_allsky.flask import db
        from indi_allsky.flask.models import IndiAllSkyDbCameraTable,IndiAllSkyDbTaskQueueTable,TaskQueueQueue,TaskQueueState
        from hybrid_runtime_fixture import login_client
        source=(Path(__file__).resolve().parents[1]/'indi_allsky/video.py').read_text()
        method=next(n for n in ast.walk(ast.parse(source)) if isinstance(n,ast.FunctionDef) and n.name=='uploadAllskyEndOfNight')
        namespace=dict(ephem=ephem,math=math,datetime=datetime,timedelta=timedelta,timezone=timezone,
                       json=json,tempfile=tempfile,Path=Path,constants=constants,db=db,
                       IndiAllSkyDbCameraTable=IndiAllSkyDbCameraTable,IndiAllSkyDbTaskQueueTable=IndiAllSkyDbTaskQueueTable,
                       TaskQueueQueue=TaskQueueQueue,TaskQueueState=TaskQueueState,logger=logging.getLogger('test'))
        exec(compile(ast.fix_missing_locations(ast.Module(body=[method],type_ignores=[])),'video.py','exec'),namespace)
        worker=SimpleNamespace(config={'DAYTIME_CAPTURE':True,'FILETRANSFER':{'UPLOAD_ENDOFNIGHT':True,'REMOTE_ENDOFNIGHT_FOLDER':'test-destination/{camera_uuid}'}},profile_id='test-profile-2',_queue_upload_task=Mock())
        with app.app_context():
            task=IndiAllSkyDbTaskQueueTable(queue=TaskQueueQueue.VIDEO,state=TaskQueueState.QUEUED,
                   data={'action':'uploadAllskyEndOfNight','kwargs':{'camera_id':2,'night':True},'profile_id':'test-profile-2'})
            db.session.add(task);db.session.commit();parent_id=task.id
            original=tempfile.NamedTemporaryFile
            with patch.object(tempfile,'NamedTemporaryFile',side_effect=lambda **kwargs:original(dir=app.config['INDI_ALLSKY_IMAGE_FOLDER'],**kwargs)):
                namespace['uploadAllskyEndOfNight'](worker,task,camera_id=2,night=True)
            worker._queue_upload_task.assert_called_once()
            child=worker._queue_upload_task.call_args.args[0];child_id=child.id
            assert worker._queue_upload_task.call_args.kwargs=={'camera_id':2}
            assert child.data['camera_id']==2 and child.data['profile_id']=='test-profile-2'
            content=json.loads(Path(child.data['local_file']).read_text())
            assert set(content)=={'sunrise','sunset','streamDaytime'}
            assert child.data['remote_file']=='test-destination/test-camera-2/data.json'
            assert child.state==TaskQueueState.QUEUED
            db.session.expire_all();parent=db.session.get(IndiAllSkyDbTaskQueueTable,parent_id)
            assert parent.data['end_of_night_upload']['task_id']==child_id
            assert 'Queued EndOfNight upload task' in parent.result and 'delivery is not yet confirmed' in parent.result
        for uid in (1,2):
            client=login_client(app,uid)
            response=client.get('/indi-allsky/modern-admin/tasks/'+str(parent_id))
            assert response.status_code==200
            assert f'Inspect upload task {child_id}' in response.text
            response=client.get('/indi-allsky/modern-admin/tasks/'+str(child_id))
            assert response.status_code==200 and 'QUEUED' in response.text and 'test-profile-2' in response.text
        # Real PyEphem at both poles in summer/winter, not synthetic exceptions.
        with app.app_context():
            camera=db.session.get(IndiAllSkyDbCameraTable,2)
            for latitude in (-90,90):
                for month in (6,12):
                    instant=datetime(2024,month,21,12,tzinfo=timezone.utc)
                    class FixedClock:
                        @staticmethod
                        def now(tz=None):return instant
                    namespace['datetime']=FixedClock
                    camera.latitude=latitude;camera.longitude=0;db.session.commit()
                    polar_task=IndiAllSkyDbTaskQueueTable(queue=TaskQueueQueue.VIDEO,state=TaskQueueState.QUEUED,
                        data={'action':'uploadAllskyEndOfNight','kwargs':{'camera_id':2,'night':True}})
                    db.session.add(polar_task);db.session.commit()
                    worker._queue_upload_task.reset_mock()
                    with patch.object(tempfile,'NamedTemporaryFile',side_effect=lambda **kwargs:original(dir=app.config['INDI_ALLSKY_IMAGE_FOLDER'],**kwargs)):
                        namespace['uploadAllskyEndOfNight'](worker,polar_task,camera_id=2,night=True)
                    worker._queue_upload_task.assert_called_once()
                    data=json.loads(Path(worker._queue_upload_task.call_args.args[0].data['local_file']).read_text())
                    daylight=(latitude>0 and month==6) or (latitude<0 and month==12)
                    expected=instant+timedelta(days=-1 if daylight else 3650)
                    assert datetime.fromisoformat(data['sunrise'])==expected,(latitude,month,data)
                    assert datetime.fromisoformat(data['sunset'])==expected,(latitude,month,data)
        print('EndOfNight: real metadata file, scoped queued task, linked UI and four real PyEphem polar cases; no transfer executed: PASS')

if __name__=='__main__':run()
