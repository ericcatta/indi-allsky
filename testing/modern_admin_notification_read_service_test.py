#!/usr/bin/env python3

import sys
from datetime import datetime
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from indi_allsky.modern_admin_notifications import ModernAdminNotificationReadService
from indi_allsky.modern_admin_notifications import NOTIFICATION_ACKNOWLEDGE_ACTION_ID
from indi_allsky.modern_admin_notifications import NOTIFICATION_ACKNOWLEDGE_FEATURE
from indi_allsky.modern_admin_notifications import NOTIFICATION_ACKNOWLEDGE_LABEL
from indi_allsky.modern_admin_notifications import NOTIFICATION_ACKNOWLEDGE_RISK_LEVEL
from indi_allsky.modern_admin_notifications import NotificationAcknowledgeService


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


class FakeAcknowledgeNotice:
    def __init__(self, notice_id=1, ack=False):
        self.id = notice_id
        self.ack = ack
        self.set_ack_calls = 0

    def setAck(self):
        self.set_ack_calls += 1
        self.ack = True


class FakeAcknowledgeRepository:
    def __init__(self, notices=None, error=None):
        self.notices = notices or {}
        self.error = error
        self.lookup_calls = []

    def lookup(self, notification_id):
        self.lookup_calls.append(notification_id)
        if self.error is not None:
            raise self.error
        return self.notices.get(notification_id)


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


def test_notification_acknowledge_service_is_domain_owned():
    import inspect
    import indi_allsky.modern_admin_notifications as notification_module
    import indi_allsky.modern_safe_action as safe_action_module

    notification_source = inspect.getsource(notification_module)
    safe_action_source = inspect.getsource(safe_action_module)

    assert 'class NotificationAcknowledgeService' in notification_source
    assert 'class NotificationAcknowledgeDbAdapter' in notification_source
    assert 'class NotificationAcknowledgeRepositoryError' in notification_source
    assert 'class NotificationAcknowledgeSafeAction' in safe_action_source
    assert 'class NotificationAcknowledgeService' not in safe_action_source
    assert safe_action_module.NotificationAcknowledgeService is notification_module.NotificationAcknowledgeService


def test_notification_acknowledge_action_policy_is_domain_owned():
    import indi_allsky.modern_safe_action as safe_action_module

    action = safe_action_module.NotificationAcknowledgeSafeAction(permission_check=lambda actor: True)
    service = NotificationAcknowledgeService(lambda notification_id: None)

    assert action.action_id == NOTIFICATION_ACKNOWLEDGE_ACTION_ID
    assert action.label == NOTIFICATION_ACKNOWLEDGE_LABEL
    assert action.feature == NOTIFICATION_ACKNOWLEDGE_FEATURE
    assert action.risk_level == NOTIFICATION_ACKNOWLEDGE_RISK_LEVEL
    assert service.action_id == NOTIFICATION_ACKNOWLEDGE_ACTION_ID
    assert service.feature == NOTIFICATION_ACKNOWLEDGE_FEATURE
    assert service.risk_level == NOTIFICATION_ACKNOWLEDGE_RISK_LEVEL


def test_notification_acknowledge_service_preserves_acknowledge_behavior():
    notice = FakeAcknowledgeNotice(7)
    repo = FakeAcknowledgeRepository({7: notice})
    service = NotificationAcknowledgeService(repo.lookup)

    result = service.acknowledge(notification_id=7)

    assert result.status == 'acknowledged'
    assert result.allowed is True
    assert result.details == {'notification_id': 7}
    assert notice.ack is True
    assert notice.set_ack_calls == 1
    assert repo.lookup_calls == [7]


def test_notification_acknowledge_service_preserves_audit_redaction():
    notice = FakeAcknowledgeNotice(8)
    repo = FakeAcknowledgeRepository({8: notice})
    service = NotificationAcknowledgeService(repo.lookup)

    _result, audit_record, _audit_write = service.acknowledge_with_audit(
        notification_id=8,
        payload={
            'notification_id': 8,
            'api_token': 'do-not-leak',
        },
        dry_run=False,
    )
    data = audit_record.to_dict()

    assert data['status'] == 'acknowledged'
    assert data['payload_summary']['api_token'] == '[REDACTED]'
    assert 'do-not-leak' not in str(data)


def run_tests():
    test_notification_rows_preserve_context_shape()
    test_notification_detail_preserves_filter_behavior()
    test_notification_list_context_preserves_context_keys()
    test_notification_detail_context_preserves_context_key()
    test_notification_read_service_has_no_flask_or_db_dependency()
    test_notification_acknowledge_service_is_domain_owned()
    test_notification_acknowledge_action_policy_is_domain_owned()
    test_notification_acknowledge_service_preserves_acknowledge_behavior()
    test_notification_acknowledge_service_preserves_audit_redaction()
    print('Modern admin notification read service checks passed')


if __name__ == '__main__':
    run_tests()
