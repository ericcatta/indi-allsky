#!/usr/bin/env python3
"""Execute the actual coordinator method with real Flask tasks and a local queue."""
import ast
import logging
from pathlib import Path
from queue import Queue as LocalQueue
from types import SimpleNamespace
from hybrid_runtime_fixture import isolated_app


def run():
    with isolated_app(multi_camera=True) as app:
        from indi_allsky.flask import db
        from indi_allsky.flask.models import IndiAllSkyDbTaskQueueTable as Task, TaskQueueState as State, TaskQueueQueue as Queue
        from indi_allsky.flask.models import IndiAllSkyDbCameraTable as Camera
        from indi_allsky.hybrid_video_task_policy import multicamera_rejection, video_task_profile_id
        assert video_task_profile_id({}, None, 'primary') == 'primary'
        assert video_task_profile_id({}, 2, 'primary') == 'default'
        assert video_task_profile_id({'MULTI_CAMERA':None}, 2, 'primary') == 'default'
        for key in ('db_camera_id','camera_db_id','camera_id'):
            config={'MULTI_CAMERA':{'profiles':[{'profile_id':'second',key:'2'}]}}
            assert video_task_profile_id(config, 2, 'primary') == 'second'
            config['MULTI_CAMERA']['profiles'].append({'profile_id':'ambiguous',key:2})
            assert video_task_profile_id(config, 2, 'primary') == 'default'
        unbound={'MULTI_CAMERA':{'profiles':[
            {'profile_id':'rpi','camera_interface':'libcamera_imx708'},
            {'profile_id':'zwo','indi':{'camera_name':'ZWO CCD ASI678MC'}}]}}
        assert video_task_profile_id(unbound,1,'first',camera_name='libcamera_imx708')=='rpi'
        assert video_task_profile_id(unbound,2,'first',camera_name='ZWO CCD ASI678MC')=='zwo'
        assert video_task_profile_id(unbound,2,'first',camera_name='ZWO')=='default'
        unbound['MULTI_CAMERA']['profiles'].append({'profile_id':'duplicate','indi_camera_name':'ZWO CCD ASI678MC'})
        assert video_task_profile_id(unbound,2,'first',camera_name='ZWO CCD ASI678MC')=='default'
        unbound['MULTI_CAMERA']['profiles'][1]['db_camera_id']=3
        assert video_task_profile_id(unbound,2,'first',camera_name='ZWO CCD ASI678MC')=='duplicate'
        source=Path(__file__).resolve().parents[1]/'indi_allsky/allsky.py'
        tree=ast.parse(source.read_text())
        method=next(node for node in ast.walk(tree) if isinstance(node,ast.FunctionDef) and node.name=='_queue_video_task')
        namespace={'db':db,'IndiAllSkyDbCameraTable':Camera,'logger':logging.getLogger('dispatch-test'),'multicamera_rejection':multicamera_rejection,'video_task_profile_id':video_task_profile_id}
        exec(compile(ast.fix_missing_locations(ast.Module(body=[method],type_ignores=[])),str(source),'exec'),namespace)
        queue=LocalQueue()
        coordinator=SimpleNamespace(config={'MULTI_CAMERA':{'profiles':[{'profile_id':'test-profile-'+str(cid),'db_camera_id':cid} for cid in (1,2)]}},multi_camera_capture_enable=True,capture_profiles=[SimpleNamespace(profile_id='test-profile-1')],video_q=queue)
        cases=[(action,cid,True) for action in ('generateVideo','generateMiniVideo','generateKeogramStarTrails','generatePanoramaVideo','updateAuroraData','updateSmokeData','uploadAllskyEndOfNight','expireData') for cid in (1,2)]
        cases += [(action,None,True) for action in ('backupDatabase','updateSatelliteTleData','systemHealthCheck')]
        cases += [(action,None,False) for action in ('generateVideo','generateMiniVideo','updateAuroraData','updateSmokeData','uploadAllskyEndOfNight','expireData')]
        cases += [(action,2,False) for action in ('unknown',)]
        with app.app_context():
            for action,cid,allowed in cases:
                kwargs={'camera_id':cid} if cid else {}
                original={'action':action,'kwargs':kwargs}
                task=Task(queue=Queue.VIDEO,state=State.QUEUED,data=original)
                db.session.add(task);db.session.commit()
                namespace['_queue_video_task'](coordinator,task)
                db.session.refresh(task)
                assert task.data==original
                if allowed:
                    payload=queue.get_nowait()
                    assert payload=={'task_id':task.id,'profile_id':'test-profile-'+str(cid or 1),**({'camera_id':cid} if cid else {})}
                    assert task.state==State.QUEUED and task.result is None
                else:
                    assert queue.empty() and task.state==State.EXPIRED and task.result
            coordinator.config={'MULTI_CAMERA':{'profiles':[{'profile_id':'named-'+str(cid),'indi':{'camera_name':'Test Camera '+str(cid)}} for cid in (1,2)]}}
            for cid in (1,2):
                task=Task(queue=Queue.VIDEO,state=State.QUEUED,data={'action':'generateMiniVideo','kwargs':{'camera_id':cid}})
                db.session.add(task);db.session.commit();namespace['_queue_video_task'](coordinator,task)
                assert queue.get_nowait()['profile_id']=='named-'+str(cid)
            db.session.get(Camera,2).local=False;db.session.commit()
            namespace['_queue_video_task'](coordinator,task)
            assert queue.get_nowait()['profile_id']=='default'
            coordinator.multi_camera_capture_enable=False
            task=Task(queue=Queue.VIDEO,state=State.QUEUED,data={'action':'expireData','kwargs':{}})
            db.session.add(task);db.session.commit();namespace['_queue_video_task'](coordinator,task)
            assert queue.get_nowait()['task_id']==task.id and task.state==State.QUEUED
        print('Actual coordinator: 19 supported camera/global dispatch cases, missing-camera and unsupported rejection, persisted reasons, unchanged single-camera dispatch: PASS')


if __name__=='__main__':run()
