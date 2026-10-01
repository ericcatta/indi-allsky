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
        def fail_commit(task, **kwargs):
            task.queue = None  # Real NOT NULL failure leaves SQLAlchemy pending rollback.
            db.session.commit()
        worker.fail_commit = fail_commit
        worker.fail=fail
        worker.succeed=lambda task,**kwargs:task.setSuccess('Effect complete')
        with app.app_context():
            original=db.session.get(Camera,2).name
            cases = [({'action': 'fail'}, State.FAILED),
                     ({'action': 'unknown'}, State.FAILED),
                     ({'action': 'fail_commit'}, State.FAILED),
                     ({}, State.FAILED), ([], State.FAILED),
                     ({'action': 'succeed', 'kwargs': None}, State.FAILED),
                     ({'action': 'succeed', 'kwargs': []}, State.FAILED),
                     ({'action': None}, State.FAILED),
                     ({'action': 'succeed'}, State.SUCCESS)]
            for data, expected in cases:
                task=Task(queue=Queue.VIDEO,state=State.QUEUED,data=data)
                db.session.add(task);db.session.commit()
                namespace['processTask'](worker,{'task_id':task.id,'profile_id':'test-profile-2','camera_id':2})
                db.session.refresh(task)
                assert task.state==expected and task.result
                assert task.queue == Queue.VIDEO
                assert db.session.get(Camera,2).name==original
            def fail_context(*args, **kwargs):
                db.session.get(Camera, 2).name = 'must rollback context'
                raise RuntimeError('route setup failed')
            worker._set_queue_context = fail_context
            task = Task(queue=Queue.VIDEO, state=State.QUEUED, data={'action': 'succeed'})
            db.session.add(task); db.session.commit()
            namespace['processTask'](worker, {'task_id': task.id, 'profile_id': 'test-profile-2'})
            assert task.state == State.FAILED
            assert db.session.get(Camera, 2).name == original
            worker._set_queue_context = lambda *args, **kwargs: None
            next_task = Task(queue=Queue.VIDEO, state=State.QUEUED, data={'action': 'succeed'})
            db.session.add(next_task); db.session.commit()
            namespace['processTask'](worker, {'task_id': next_task.id, 'profile_id': 'test-profile-2'})
            assert next_task.state == State.SUCCESS
        print('Video execution: effect exceptions roll back and mark FAILED, unknown actions terminal, next valid task succeeds: PASS')


if __name__=='__main__':run()
