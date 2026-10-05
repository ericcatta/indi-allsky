#!/usr/bin/env python3
"""Actual video execution boundary keeps failures terminal and allows the next job."""
import ast
import logging
import sqlite3
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
from hybrid_runtime_fixture import isolated_app


def run():
    with isolated_app(multi_camera=True, file_database=True) as app:
        from sqlalchemy.orm.exc import NoResultFound
        from indi_allsky.flask import db
        from indi_allsky.flask.models import IndiAllSkyDbTaskQueueTable as Task, TaskQueueState as State, TaskQueueQueue as Queue, IndiAllSkyDbCameraTable as Camera
        tree=ast.parse((Path(__file__).resolve().parents[1]/'indi_allsky/video.py').read_text())
        method=next(node for node in ast.walk(tree) if isinstance(node,ast.FunctionDef) and node.name=='processTask')
        namespace={'__package__':'indi_allsky','IndiAllSkyDbTaskQueueTable':Task,'TaskQueueState':State,'TaskQueueQueue':Queue,'NoResultFound':NoResultFound,'db':db,'logger':logging.getLogger('video-test')}
        exec(compile(ast.fix_missing_locations(ast.Module(body=[method],type_ignores=[])),'actual-video-method','exec'),namespace)
        worker=SimpleNamespace(config={},image_dir=Path(app.config['INDI_ALLSKY_IMAGE_FOLDER']),_validate_profile_id=lambda payload:payload['profile_id'],_set_queue_context=lambda *args,**kwargs:None)
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
            from indi_allsky.archive_volume import ArchiveUnavailable
            worker.config={'ARCHIVE_VOLUME':{'ROOT':str(worker.image_dir),'UUID':'missing'}}
            task=Task(queue=Queue.VIDEO,state=State.QUEUED,data={'action':'succeed'})
            db.session.add(task); db.session.commit()
            with patch('indi_allsky.archive_volume.verify_archive',side_effect=ArchiveUnavailable('missing disk')):
                namespace['processTask'](worker,{'task_id':task.id,'profile_id':'test-profile-2'})
            assert task.state==State.FAILED and task.result
            worker.config={}
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

            # Actual competing SQLite writer during effect failure. The failure
            # status must recover without replaying the effect or killing this
            # worker's ability to execute the next queue message.
            writer = sqlite3.connect(db.engine.url.database, timeout=0)
            calls = []
            def fail_locked(task, **kwargs):
                calls.append(task.id)
                writer.execute('BEGIN IMMEDIATE')
                writer.execute('UPDATE camera SET name=name WHERE id=1')
                raise RuntimeError('Effect failed while another writer is active')
            worker.fail_locked = fail_locked
            task = Task(queue=Queue.VIDEO, state=State.QUEUED, data={'action': 'fail_locked'})
            db.session.add(task); db.session.commit()
            task_id = task.id
            db.session.execute(db.text('PRAGMA busy_timeout=0'))
            with patch('indi_allsky.task_failure.time.sleep', side_effect=lambda delay: writer.commit()) as sleep:
                namespace['processTask'](worker, {'task_id': task_id, 'profile_id': 'test-profile-2'})
                assert sleep.call_count == 1
            assert calls == [task_id] and task.state == State.FAILED
            assert 'RuntimeError' in task.result
            writer.close()
            next_task = Task(queue=Queue.VIDEO, state=State.QUEUED, data={'action': 'succeed'})
            db.session.add(next_task); db.session.commit()
            namespace['processTask'](worker, {'task_id': next_task.id, 'profile_id': 'test-profile-2'})
            assert next_task.state == State.SUCCESS

            from indi_allsky.task_failure import record_video_failure
            from indi_allsky.flask import models
            # A terminal result or a different queue is never overwritten.
            assert not record_video_failure(db.session, models, next_task.id, 'must not replace success')
            assert next_task.state == State.SUCCESS and next_task.result == 'Effect complete'
            other = Task(queue=Queue.UPLOAD, state=State.RUNNING, data={})
            db.session.add(other); db.session.commit()
            assert not record_video_failure(db.session, models, other.id, 'wrong queue')
            assert other.state == State.RUNNING
            assert not record_video_failure(db.session, models, -1, 'missing row')

            # Bounded retry, with unrelated database/backend errors propagated.
            from sqlalchemy.exc import OperationalError
            busy = sqlite3.OperationalError('database is locked')
            busy.sqlite_errorcode = sqlite3.SQLITE_BUSY
            for original_error, attempts in ((busy, 3), (sqlite3.OperationalError('no such table'), 1),
                                              (RuntimeError('backend unavailable'), 1)):
                error = OperationalError('UPDATE', {}, original_error)
                with patch.object(db.session, 'query', side_effect=error) as query, \
                        patch('indi_allsky.task_failure.time.sleep') as sleep:
                    try:
                        record_video_failure(db.session, models, task_id, 'failure')
                    except OperationalError as caught:
                        assert caught is error
                    else:
                        raise AssertionError('Failure write error hidden')
                    assert query.call_count == attempts and sleep.call_count == attempts - 1
        print('Video execution: effect exceptions roll back and mark FAILED, unknown actions terminal, next valid task succeeds: PASS')


if __name__=='__main__':run()
