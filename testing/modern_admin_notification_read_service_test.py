#!/usr/bin/env python3

import sys
from datetime import datetime
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from indi_allsky.modern_admin_notifications import ModernAdminNotificationReadService


class FakeCategory:
    value = 'System'


class FakeField:
    def __eq__(self, value):
        return ('eq', value)


class FakeNotice:
    def __init__(self, notice_id=1, ack=False, category=None):
        self.id = notice_id
        self.category = category
        self.item = ''
        self.createDate = datetime(2026, 1, 2, 3, 4, 5)
        self.expireDate = datetime(2026, 1, 3, 4, 5, 6)
        self.ack = ack
        self.notification = 'Test notification'


class FakeQuery:
    def __init__(self, notices):
        self.notices = notices
        self.order_by_calls = list()
        self.limit_calls = list()
        self.filter_calls = list()

    def order_by(self, expression):
        self.order_by_calls.append(expression)
        return self

    def limit(self, limit):
        self.limit_calls.append(limit)
        return self

    def filter(self, expression):
        self.filter_calls.append(expression)
        return self

    def all(self):
        return self.notices

    def one(self):
        return self.notices[0]


def test_notification_rows_preserve_context_shape():
    query = FakeQuery([FakeNotice(category=FakeCategory()), FakeNotice(notice_id=2, ack=True)])
    service = ModernAdminNotificationReadService(
        query=query,
        order_by_expression='created-desc',
        id_field=FakeField(),
    )

    notices = service.list_notifications(limit=100)
    rows = service.build_notification_rows(notices)

    assert query.order_by_calls == ['created-desc']
    assert query.limit_calls == [100]
    assert rows[0] == {
        'id'          : 1,
        'category'    : 'System',
        'item'        : 'Not set',
        'created'     : '2026-01-02 03:04:05',
        'expires'     : '2026-01-03 04:05:06',
        'ack'         : 'No',
        'ack_tone'    : 'modern-admin-status-warning',
        'notification': 'Test notification',
    }
    assert rows[1]['ack'] == 'Yes'
    assert rows[1]['ack_tone'] == 'modern-admin-status-muted'


def test_notification_detail_preserves_filter_behavior():
    query = FakeQuery([FakeNotice(notice_id=42, category=None)])
    service = ModernAdminNotificationReadService(query=query, id_field=FakeField())

    notice = service.get_notification(42)
    row = service.build_notification_detail(notice)

    assert query.filter_calls == [('eq', 42)]
    assert row['id'] == 42
    assert row['category'] == 'Unknown'


def test_notification_list_context_preserves_context_keys():
    service = ModernAdminNotificationReadService(query=FakeQuery([]))
    rows = [
        {
            'id'      : 1,
            'category': 'System',
            'item'    : 'Camera',
            'ack'     : 'No',
        },
        {
            'id'      : 2,
            'category': 'System',
            'item'    : 'Storage',
            'ack'     : 'Yes',
        },
    ]

    context = service.build_notification_list_context(rows)

    assert context == {
        'modern_admin_notification_rows'          : rows,
        'modern_admin_notification_count'         : 2,
        'modern_admin_notification_unacked_count' : 1,
        'modern_admin_notification_categories'    : ['System'],
        'modern_admin_notification_items'         : ['Camera', 'Storage'],
    }


def test_notification_detail_context_preserves_context_key():
    service = ModernAdminNotificationReadService(query=FakeQuery([]))
    detail = {'id': 42}

    context = service.build_notification_detail_context(detail)

    assert context == {
        'modern_admin_notification_detail': detail,
    }


def test_notification_read_service_has_no_flask_or_db_dependency():
    import inspect
    import indi_allsky.modern_admin_notifications as module

    source = inspect.getsource(module)

    assert 'flask' not in source.lower()
    assert 'db.session' not in source
    assert 'request' not in source
    assert 'open(' not in source


def run_tests():
    test_notification_rows_preserve_context_shape()
    test_notification_detail_preserves_filter_behavior()
    test_notification_list_context_preserves_context_keys()
    test_notification_detail_context_preserves_context_key()
    test_notification_read_service_has_no_flask_or_db_dependency()
    print('Modern admin notification read service checks passed')


if __name__ == '__main__':
    run_tests()
