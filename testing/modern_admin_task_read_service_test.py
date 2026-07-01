#!/usr/bin/env python3

import sys
from datetime import datetime
from datetime import timedelta
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from indi_allsky.modern_admin_tasks import ModernAdminTaskReadService


class FakeEnum:
    def __init__(self, name, value):
        self.name = name
        self.value = value


class FakeField:
    def __eq__(self, value):
        return ('eq', value)


class FakeTask:
    def __init__(self, task_id=1, data=None, state=None, queue=None, create_date=None):
        self.id = task_id
        self.createDate = create_date or datetime(2026, 1, 2, 3, 4, 5)
        self.updateDate = datetime(2026, 1, 2, 4, 5, 6)
        self.queue = queue or FakeEnum('VIDEO', 'video')
        self.state = state or FakeEnum('SUCCESS', 'success')
        self.priority = 100
        self.data = data if data is not None else {'action': 'generate', 'camera_id': 7}
        self.result = 'Task completed'


class FakeQuery:
    def __init__(self, tasks):
        self.tasks = tasks
        self.filter_calls = list()
        self.order_by_calls = list()

    def filter(self, expression):
        self.filter_calls.append(expression)
        return self

    def order_by(self, expression):
        self.order_by_calls.append(expression)
        return self

    def __iter__(self):
        return iter(self.tasks)

    def one(self):
        return self.tasks[0]


def build_service(query=None, now=None):
    return ModernAdminTaskReadService(
        query=query or FakeQuery([FakeTask()]),
        now=now or datetime(2026, 1, 2, 5, 4, 5),
        filter_expression='recent-visible-tasks',
        order_by_expression='created-desc',
        id_field=FakeField(),
    )


def test_task_list_preserves_classic_task_entry_shape():
    query = FakeQuery([
        FakeTask(data={'kwargs': {'action': 'timelapse', 'profile_id': 3}, 'message': 'Queued'}),
    ])
    service = build_service(query=query)

    tasks = service.list_tasks()

    assert query.filter_calls == ['recent-visible-tasks']
    assert query.order_by_calls == ['created-desc']
    assert tasks == [{
        'id'         : 1,
        'createDate' : datetime(2026, 1, 2, 3, 4, 5),
        'updateDate' : datetime(2026, 1, 2, 4, 5, 6),
        'queue'      : 'VIDEO',
        'state'      : 'SUCCESS',
        'action'     : 'timelapse',
        'camera_id'  : '',
        'profile_id' : 3,
        'message'    : 'Queued',
        'result'     : 'Task completed',
    }]


def test_queue_rows_preserve_modern_context_shape():
    service = build_service(now=datetime(2026, 1, 2, 5, 4, 5))
    task_list = [
        service.build_task_entry(FakeTask(state=FakeEnum('RUNNING', 'running'))),
    ]

    rows = service.build_queue_rows(
        task_list,
        details_url_builder=lambda task_id: '/modern-admin/tasks/{0:d}'.format(task_id),
        display_limit=200,
    )

    assert rows == [{
        'id'         : 1,
        'details_url': '/modern-admin/tasks/1',
        'created'    : '2026-01-02 03:04:05',
        'age'        : '2h ago',
        'updated'    : '2026-01-02 04:05:06',
        'queue'      : 'VIDEO',
        'action'     : 'generate',
        'state'      : 'RUNNING',
        'state_tone' : 'modern-admin-status-neutral',
        'camera_id'  : 7,
        'profile_id' : 'Any',
        'message'    : 'Task completed',
    }]


def test_task_detail_redacts_sensitive_payload():
    service = build_service()
    task = FakeTask(data={
        'action': 'upload',
        'password': 'secret',
        'kwargs': {
            'api_key': 'key',
            'message': 'Ready',
        },
    })

    detail = service.build_task_detail(task)

    assert detail['action'] == 'upload'
    assert detail['message'] == 'Ready'
    assert '"password": "<redacted>"' in detail['payload_text']
    assert '"api_key": "<redacted>"' in detail['payload_text']
    assert detail['has_payload'] is True


def test_task_detail_query_uses_id_filter():
    query = FakeQuery([FakeTask(task_id=42)])
    service = build_service(query=query)

    task = service.get_task(42)

    assert query.filter_calls == [('eq', 42)]
    assert task.id == 42


def test_recent_task_count_matches_previous_boundary_behavior():
    service = build_service(now=datetime(2026, 1, 2, 5, 4, 5))

    count = service.get_recent_task_count([
        {'createDate': datetime(2026, 1, 2, 4, 30, 0)},
        {'createDate': datetime(2026, 1, 2, 1, 30, 0)},
        {'createDate': None},
    ])

    assert count == 1


def test_task_read_service_has_no_flask_or_db_dependency():
    import inspect
    import indi_allsky.modern_admin_tasks as module

    source = inspect.getsource(module)

    assert 'flask' not in source.lower()
    assert 'db.session' not in source
    assert 'request' not in source
    assert 'open(' not in source


def run_tests():
    test_task_list_preserves_classic_task_entry_shape()
    test_queue_rows_preserve_modern_context_shape()
    test_task_detail_redacts_sensitive_payload()
    test_task_detail_query_uses_id_filter()
    test_recent_task_count_matches_previous_boundary_behavior()
    test_task_read_service_has_no_flask_or_db_dependency()
    print('Modern admin task read service checks passed')


if __name__ == '__main__':
    run_tests()
