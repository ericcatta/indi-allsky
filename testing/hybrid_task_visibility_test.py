#!/usr/bin/env python3
"""All persisted task queues/states remain inspectable without Classic."""
from datetime import timedelta
import re
from hybrid_runtime_fixture import isolated_app, login_client


def run():
    with isolated_app(multi_camera=True) as app:
        from sqlalchemy import func
        from indi_allsky.flask import db
        from indi_allsky.flask.models import IndiAllSkyDbTaskQueueTable, TaskQueueQueue, TaskQueueState
        from indi_allsky.flask.views import ModernAdminTaskQueueView
        with app.app_context():
            now = db.session.query(func.now()).scalar()
            rows = []
            for camera in (1, 2):
                for queue in TaskQueueQueue:
                    for state in TaskQueueState:
                        number = len(rows) + 1
                        task = IndiAllSkyDbTaskQueueTable(id=number, queue=queue, state=state,
                            createDate=now-timedelta(minutes=30), result='Recorded outcome ' + str(number),
                            data={'action': 'fixture-' + queue.name, 'camera_id': camera,
                                  'profile_id': 'test-profile-' + str(camera), 'token': 'private-fixture-token'})
                        rows.append((number, camera, queue.name, state.name))
                        db.session.add(task)
            db.session.add(IndiAllSkyDbTaskQueueTable(id=1000, queue=TaskQueueQueue.UPLOAD,
                state=TaskQueueState.FAILED, createDate=now-timedelta(days=4), data={}))
            db.session.commit()
            for offset in (-12, 12):
                view = object.__new__(ModernAdminTaskQueueView)
                view.camera_now = now + timedelta(hours=offset)
                service = view.get_task_read_service()
                tasks = service.list_tasks()
                assert len(tasks) == 48 and service.get_recent_task_count(tasks) == 48
                assert all(service.format_task_age(task['createDate']) == '30m ago' for task in tasks)
        for uid in (1, 2):
            client = login_client(app, uid)
            for camera in (1, 2):
                with client.session_transaction() as session:
                    session['camera_id'] = camera
                response = client.get('/indi-allsky/modern-admin/tasks')
                assert response.status_code == 200
                assert response.text.count('class="modern-admin-task-row"') == 48
                assert '/modern-admin/tasks/1000' not in response.text
                assert re.search(r'Recent Tasks</div>\s*<h3>48</h3>', response.text)
                for queue in TaskQueueQueue:
                    assert 'value="' + queue.name.lower() + '"' in response.text
                for state in TaskQueueState:
                    assert 'value="' + state.name.lower() + '"' in response.text
            for number, camera, queue, state in rows:
                response = client.get('/indi-allsky/modern-admin/tasks/' + str(number))
                assert response.status_code == 200
                assert queue in response.text and state in response.text
                assert 'Recorded outcome ' + str(number) in response.text
                assert 'test-profile-' + str(camera) in response.text
                assert 'private-fixture-token' not in response.text and '&lt;redacted&gt;' in response.text
        assert app.test_client().get('/indi-allsky/modern-admin/tasks').status_code == 302
        with app.app_context():
            assert IndiAllSkyDbTaskQueueTable.query.count() == 49
            assert {task.state for task in IndiAllSkyDbTaskQueueTable.query} == set(TaskQueueState)
        print('Task visibility: all four queues/six states, both roles/cameras, database clock, lookback, outcomes and redaction: PASS')


if __name__ == '__main__':
    run()
