#!/usr/bin/env python3
"""Concurrent file-backed SQLite claims, including uncertain commit outcomes."""
import ast
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from threading import Barrier

from hybrid_runtime_fixture import isolated_app


def run():
    with isolated_app(multi_camera=True) as app:
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker
        from indi_allsky.flask.models import IndiAllSkyDbTaskQueueTable as Task, TaskQueueQueue as Queue, TaskQueueState as State
        from indi_allsky.task_claim import claim_upload_task
        root = Path(app.config['INDI_ALLSKY_IMAGE_FOLDER'])
        engine = create_engine('sqlite:///' + str(root / 'claims.sqlite'), connect_args={'timeout': 10})
        Task.__table__.create(engine)
        Session = sessionmaker(bind=engine)

        def add_task(state=State.QUEUED, queue=Queue.UPLOAD):
            with Session() as session:
                task = Task(state=state, queue=queue, data={'camera_id': 2, 'profile_id': 'test-profile-2'})
                session.add(task)
                session.commit()
                return task.id

        def read_state(task_id):
            with Session() as session:
                return session.get(Task, task_id).state

        try:
            # Deterministically reproduce the old read-then-write algorithm:
            # both readers see QUEUED before either writes RUNNING.
            task_id = add_task()
            ready = Barrier(2)

            def old_claim():
                with Session() as session:
                    task = session.query(Task).filter_by(id=task_id, state=State.QUEUED, queue=Queue.UPLOAD).one()
                    ready.wait(timeout=10)
                    task.state = State.RUNNING
                    session.commit()
                    return True

            with ThreadPoolExecutor(max_workers=2) as pool:
                attempts = [pool.submit(old_claim) for _ in range(2)]
                assert sum(f.result(timeout=15) for f in attempts) == 2

            # Independent connections race for each task. Exactly one may own it.
            for _ in range(10):
                task_id = add_task()
                ready = Barrier(2)

                def new_claim():
                    with Session() as session:
                        # Exercise a stale identity-map entry too.
                        existing = session.get(Task, task_id)
                        assert existing.state == State.QUEUED
                        ready.wait(timeout=10)
                        task = claim_upload_task(task_id, session=session)
                        if task is None:
                            return False
                        assert task.state == State.RUNNING
                        assert task.data == {'camera_id': 2, 'profile_id': 'test-profile-2'}
                        return True

                with ThreadPoolExecutor(max_workers=2) as pool:
                    attempts = [pool.submit(new_claim) for _ in range(2)]
                    assert sum(f.result(timeout=15) for f in attempts) == 1
                assert read_state(task_id) == State.RUNNING

            for state in (State.MANUAL, State.RUNNING, State.SUCCESS, State.FAILED, State.EXPIRED):
                task_id = add_task(state)
                with Session() as session:
                    assert claim_upload_task(task_id, session=session) is None
                assert read_state(task_id) == state
            for queue in (Queue.IMAGE, Queue.VIDEO, Queue.MAIN):
                task_id = add_task(queue=queue)
                with Session() as session:
                    assert claim_upload_task(task_id, session=session) is None
                assert read_state(task_id) == State.QUEUED
            with Session() as session:
                assert claim_upload_task(-1, session=session) is None

            # No caller is authorized to execute after an uncertain commit.
            for commit_reached_database in (False, True):
                task_id = add_task()
                with Session() as session:
                    class FailedCommit:
                        def __getattr__(self, name):
                            return getattr(session, name)

                        def commit(self):
                            if commit_reached_database:
                                session.commit()
                            raise RuntimeError('simulated commit acknowledgement failure')

                    try:
                        claim_upload_task(task_id, session=FailedCommit())
                    except RuntimeError as exc:
                        assert 'acknowledgement' in str(exc)
                    else:
                        raise AssertionError('Uncertain claim allowed an effect')
                assert read_state(task_id) == (State.RUNNING if commit_reached_database else State.QUEUED)

            source = (Path(__file__).resolve().parents[1] / 'indi_allsky/uploader.py').read_text()
            tree = ast.parse(source)
            method = next(n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name == 'processUpload')
            text = ast.unparse(method)
            assert 'task = claim_upload_task(task_id)' in text
            assert 'task.setRunning()' not in text
            assert text.index('task = claim_upload_task(task_id)') < text.index('client.connect(')
            assert 'if task is None:\n        logger.info' in text
            print('Old duplicate reproduced; 10 concurrent atomic claims, scopes, terminal states and uncertain commits: PASS')
        finally:
            engine.dispose()


if __name__ == '__main__':
    run()
