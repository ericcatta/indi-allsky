#!/usr/bin/env python3
"""Exercise all EndOfNight polar exception branches in the actual worker method."""
import ast,json,logging,math,tempfile,sys
from datetime import datetime,timedelta,timezone
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from indi_allsky.end_of_night import prepare_end_of_night_payload, handoff_end_of_night_upload


class NeverUpError(Exception):pass
class AlwaysUpError(Exception):pass
class Clock:
    @staticmethod
    def now(tz=None):return datetime(2024,2,29,12,tzinfo=timezone.utc)


def run():
    try:timedelta(years=10)
    except TypeError:pass
    else:raise AssertionError('Original failure did not reproduce')
    source=(Path(__file__).resolve().parents[1]/'indi_allsky/video.py').read_text()
    method=next(n for n in ast.walk(ast.parse(source)) if isinstance(n,ast.FunctionDef) and n.name=='uploadAllskyEndOfNight')
    for rising_error,setting_error in ((NeverUpError,NeverUpError),(AlwaysUpError,AlwaysUpError),(NeverUpError,AlwaysUpError),(AlwaysUpError,NeverUpError)):
        for altitude in (-.5,.5):
            with tempfile.TemporaryDirectory() as directory:
                observer=Mock()
                observer.next_rising.side_effect=rising_error()
                observer.previous_rising.side_effect=rising_error()
                observer.next_setting.side_effect=setting_error()
                camera=SimpleNamespace(id=2,latitude=90,longitude=0,elevation=0,uuid='polar-camera')
                camera_model=Mock();camera_model.id=2;camera_model.query.filter.return_value.one.return_value=camera
                task_model=Mock(side_effect=lambda **kwargs:SimpleNamespace(id=42,**kwargs))
                env={'prepare_end_of_night_payload':prepare_end_of_night_payload,'handoff_end_of_night_upload':handoff_end_of_night_upload,'IndiAllSkyDbCameraTable':camera_model,'IndiAllSkyDbTaskQueueTable':task_model,
                     'TaskQueueQueue':SimpleNamespace(UPLOAD='UPLOAD'),'TaskQueueState':SimpleNamespace(QUEUED='QUEUED'),
                     'logger':logging.getLogger('test'),'datetime':Clock,'timezone':timezone,'timedelta':timedelta,
                     'math':math,'Path':Path,'json':json,'db':Mock(),'constants':SimpleNamespace(TRANSFER_UPLOAD=1),
                     'tempfile':SimpleNamespace(NamedTemporaryFile=lambda **kwargs:tempfile.NamedTemporaryFile(dir=directory,**kwargs)),
                     'ephem':SimpleNamespace(Observer=lambda:observer,Sun=lambda:SimpleNamespace(alt=altitude,compute=lambda obs:None),NeverUpError=NeverUpError,AlwaysUpError=AlwaysUpError)}
                exec(compile(ast.fix_missing_locations(ast.Module(body=[method],type_ignores=[])),'video.py','exec'),env)
                worker=SimpleNamespace(config={'DAYTIME_CAPTURE':True,'FILETRANSFER':{'UPLOAD_ENDOFNIGHT':True,'REMOTE_ENDOFNIGHT_FOLDER':'test/{camera_uuid}'}},profile_id='polar-profile',_queue_upload_task=Mock())
                task=Mock(data={'action':'uploadAllskyEndOfNight'})
                env['uploadAllskyEndOfNight'](worker,task,night=True,camera_id=2)
                worker._queue_upload_task.assert_called_once();task.setSuccess.assert_called_once();task.setFailed.assert_not_called()
                child=worker._queue_upload_task.call_args.args[0]
                data=json.loads(Path(child.data['local_file']).read_text())
                for key,error in (('sunrise',rising_error),('sunset',setting_error)):
                    expected=Clock.now()+timedelta(days=3650 if error is NeverUpError else -1)
                    assert datetime.fromisoformat(data[key])==expected,(key,data)
                assert data['streamDaytime'] is True
    print('EndOfNight polar fallback: original TypeError reproduced; 8 rising/setting/altitude cases, leap-day clock, valid metadata and queued task: PASS')

if __name__=='__main__':run()
