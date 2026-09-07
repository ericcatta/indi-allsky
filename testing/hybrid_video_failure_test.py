#!/usr/bin/env python3
"""Actual video execution boundary keeps failures terminal and allows the next job."""
import ast
import logging
from pathlib import Path
from types import SimpleNamespace
from hybrid_runtime_fixture import isolated_app


def run():
    with isolated_app(multi_camera=True) as app:
        from sqlalchemy.orm.exc import NoResultFound
        from indi_allsky.flask import db
        from indi_allsky.flask.models import IndiAllSkyDbTaskQueueTable as Task, TaskQueueState as State, TaskQueueQueue as Queue, IndiAllSkyDbCameraTable as Camera
        tree=ast.parse((Path(__file__).resolve().parents[1]/'indi_allsky/video.py').read_text())
        method=next(node for node in ast.walk(tree) if isinstance(node,ast.FunctionDef) and node.name=='processTask')
        namespace={'IndiAllSkyDbTaskQueueTable':Task,'TaskQueueState':State,'TaskQueueQueue':Queue,'NoResultFound':NoResultFound,'db':db,'logger':logging.getLogger('video-test')}
        exec(compile(ast.fix_missing_locations(ast.Module(body=[method],type_ignores=[])),'actual-video-method','exec'),namespace)
        worker=SimpleNamespace(_validate_profile_id=lambda payload:payload['profile_id'],_set_queue_context=lambda *args,**kwargs:None)
        def fail(task,**kwargs):
            db.session.get(Camera,2).name='must rollback'
            raise TypeError('provider returned None')
        worker.fail=fail
        worker.succeed=lambda task,**kwargs:task.setSuccess('Effect complete')
        with app.app_context():
            original=db.session.get(Camera,2).name
            for action,expected in [('fail',State.FAILED),('unknown',State.FAILED),('succeed',State.SUCCESS)]:
                task=Task(queue=Queue.VIDEO,state=State.QUEUED,data={'action':action,'kwargs':{'camera_id':2}})
                db.session.add(task);db.session.commit()
                namespace['processTask'](worker,{'task_id':task.id,'profile_id':'test-profile-2','camera_id':2})
                db.session.refresh(task)
                assert task.state==expected and task.result
                assert db.session.get(Camera,2).name==original
        print('Video execution: effect exceptions roll back and mark FAILED, unknown actions terminal, next valid task succeeds: PASS')


if __name__=='__main__':run()
