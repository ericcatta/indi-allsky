#!/usr/bin/env python3

import json
import sys
from tempfile import TemporaryDirectory
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from indi_allsky.modern_safe_action import ModernAdminSafeAction
from indi_allsky.modern_safe_action import ModernAdminSafeActionAuditLog
from indi_allsky.modern_safe_action import ModernAdminSafeActionPlaceholder
from indi_allsky.modern_safe_action import ModernAdminSafeActionAuditRecord
from indi_allsky.modern_safe_action import ModernAdminSafeActionRegistry
from indi_allsky.modern_safe_action import ModernAdminSafeActionResult
from indi_allsky.modern_safe_action import ModernAdminSafeActionRunner
from indi_allsky.modern_safe_action import NotificationAcknowledgeSafeAction
from indi_allsky.modern_safe_action import NotificationAcknowledgeService
from indi_allsky.modern_safe_action import build_default_modern_safe_action_registry
from indi_allsky.modern_safe_action import build_notification_acknowledge_dry_run_registry
from indi_allsky.modern_safe_action import run_modern_safe_action_dry_run


SAFE_ACTION_DRY_RUN_ROUTE = '/modern-admin/safe-action/dry-run'


class Actor:
    username = 'safe-admin'


class FakeNotification:
    def __init__(self, notification_id, ack=False):
        self.id = notification_id
        self.ack = ack
        self.set_ack_calls = 0


    def setAck(self):
        self.set_ack_calls += 1
        self.ack = True


class FailingSetAckNotification(FakeNotification):
    def setAck(self):
        self.set_ack_calls += 1
        raise RuntimeError('fake setAck failure')


class FakeNotificationRepository:
    def __init__(self, notifications=None, error=None):
        self.notifications = notifications or {}
        self.error = error
        self.lookup_calls = []


    def lookup(self, notification_id):
        self.lookup_calls.append(notification_id)
        if self.error:
            raise self.error

        return self.notifications.get(notification_id)


class FakeAuditLog:
    def __init__(self):
        self.records = []


    def append(self, audit_record):
        self.records.append(audit_record.to_dict())
        return {
            'written': True,
            'path': 'fake-audit.jsonl',
            'bytes': len(json.dumps(self.records[-1])),
        }


class AdminActor:
    username = 'admin'
    is_admin = True


class NonAdminActor:
    username = 'operator'
    is_admin = False
    password = 'do-not-render'


class ExampleAction(ModernAdminSafeAction):
    action_id = 'test.example_action'
    label = 'Example Action'
    feature = 'Testing'
    risk_level = 'low'

    def __init__(self, permission_check=None):
        super().__init__(permission_check=permission_check)
        self.executed = False


class ExecutingAction(ExampleAction):
    def execute(self, actor=None, payload=None):
        self.executed = True
        return self.result(
            status='executed',
            message='Executed',
            dry_run=False,
            allowed=True,
            audit_message=self.audit_message(actor, payload or {}, 'executed'),
        )


def test_default_action_does_not_execute():
    action = ExampleAction(permission_check=lambda actor: True)
    result = action.run(actor=Actor(), dry_run=False)

    assert result.status == 'not_implemented'
    assert result.allowed is False
    assert action.executed is False


def test_dry_run_does_not_mutate():
    action = ExecutingAction(permission_check=lambda actor: True)
    result = action.run(actor=Actor(), dry_run=True)

    assert result.status == 'dry_run'
    assert result.allowed is True
    assert result.dry_run is True
    assert action.executed is False


def test_action_without_permission_fails():
    action = ExecutingAction(permission_check=lambda actor: False)
    result = action.run(actor=Actor(), dry_run=False)

    assert result.status == 'permission_denied'
    assert result.allowed is False
    assert action.executed is False


def test_result_is_structured():
    result = ModernAdminSafeActionResult(
        action_id='test.action',
        feature='Testing',
        risk_level='low',
        status='dry_run',
        message='Dry run',
    )
    data = result.to_dict()

    assert data['action_id'] == 'test.action'
    assert data['feature'] == 'Testing'
    assert data['risk_level'] == 'low'
    assert data['status'] == 'dry_run'
    assert data['dry_run'] is True


def test_audit_message_redacts_secret_payload():
    action = ExampleAction(permission_check=lambda actor: True)
    result = action.run(
        actor=Actor(),
        payload={
            'camera_id': 1,
            'api_token': 'secret-value',
            'nested': {
                'password': 'do-not-show',
            },
        },
        dry_run=True,
    )

    assert 'secret-value' not in result.audit_message
    assert 'do-not-show' not in result.audit_message
    assert '[REDACTED]' in result.audit_message
    assert result.action_id == 'test.example_action'
    assert result.feature == 'Testing'
    assert result.risk_level == 'low'


def test_registry_empty():
    registry = ModernAdminSafeActionRegistry()

    assert registry.list_actions() == []
    assert registry.to_dict() == []


def test_registry_register_and_lookup():
    registry = ModernAdminSafeActionRegistry()
    action = ExampleAction(permission_check=lambda actor: True)
    registry.register(action)

    assert registry.get('test.example_action') is action
    assert registry.find('test.example_action') is action


def test_registry_duplicate_action_id_fails():
    registry = ModernAdminSafeActionRegistry()
    registry.register(ExampleAction())

    try:
        registry.register(ExampleAction())
    except ValueError as e:
        assert 'Duplicate safe action id' in str(e)
    else:
        raise AssertionError('Duplicate action id did not fail')


def test_registry_missing_action_returns_structured_error():
    registry = ModernAdminSafeActionRegistry()
    result = registry.find('missing.action')

    assert isinstance(result, ModernAdminSafeActionResult)
    assert result.action_id == 'missing.action'
    assert result.status == 'not_found'
    assert result.allowed is False


def test_registry_filters_by_feature_and_risk():
    registry = ModernAdminSafeActionRegistry()
    registry.register(ModernAdminSafeActionPlaceholder(
        action_id='feature.low',
        label='Low Risk',
        feature='Feature A',
        risk_level='low',
    ))
    registry.register(ModernAdminSafeActionPlaceholder(
        action_id='feature.high',
        label='High Risk',
        feature='Feature B',
        risk_level='high',
    ))

    assert [action.action_id for action in registry.list_actions(feature='Feature A')] == ['feature.low']
    assert [action.action_id for action in registry.list_actions(risk_level='high')] == ['feature.high']


def test_default_placeholder_actions_do_not_execute():
    registry = build_default_modern_safe_action_registry()
    action_ids = [action.action_id for action in registry.list_actions()]

    assert 'notification.acknowledge' in action_ids
    assert 'image.exclude' in action_ids
    assert 'youtube.oauth_status_refresh' in action_ids
    assert 'focus.move' in action_ids

    for action in registry.list_actions():
        denied = action.run(actor=Actor(), dry_run=False)
        assert denied.status == 'permission_denied'
        assert denied.allowed is False


def test_placeholder_dry_run_is_safe_when_permission_allows():
    action = ModernAdminSafeActionPlaceholder(
        action_id='placeholder.test',
        label='Placeholder',
        feature='Testing',
        risk_level='medium',
        permission_check=lambda actor: True,
    )

    dry_run = action.run(actor=Actor(), dry_run=True)
    execute = action.run(actor=Actor(), dry_run=False)

    assert dry_run.status == 'dry_run'
    assert dry_run.allowed is True
    assert execute.status == 'not_implemented'
    assert execute.allowed is False


def test_notification_acknowledge_permission_denied():
    action = NotificationAcknowledgeSafeAction(permission_check=lambda actor: False)
    result = action.run(actor=Actor(), payload={'notification_id': 1}, dry_run=False)

    assert result.status == 'permission_denied'
    assert result.allowed is False


def test_notification_acknowledge_missing_notification_id():
    action = NotificationAcknowledgeSafeAction(permission_check=lambda actor: True)
    result = action.run(actor=Actor(), payload={}, dry_run=True)

    assert result.status == 'validation_failed'
    assert 'notification_id is required' in result.message


def test_notification_acknowledge_invalid_notification_id():
    action = NotificationAcknowledgeSafeAction(permission_check=lambda actor: True)
    result = action.run(actor=Actor(), payload={'notification_id': 0}, dry_run=True)

    assert result.status == 'validation_failed'
    assert 'positive integer' in result.message


def test_notification_acknowledge_missing_lookup_result():
    action = NotificationAcknowledgeSafeAction(
        permission_check=lambda actor: True,
        notification_lookup=lambda notification_id: None,
    )
    result = action.run(actor=Actor(), payload={'notification_id': 99}, dry_run=True)

    assert result.status == 'validation_failed'
    assert 'does not exist' in result.message


def test_notification_acknowledge_dry_run_does_not_call_callback():
    calls = []
    action = NotificationAcknowledgeSafeAction(
        permission_check=lambda actor: True,
        notification_lookup=lambda notification_id: FakeNotification(notification_id),
        acknowledge_callback=lambda **kwargs: calls.append(kwargs),
    )

    result = action.run(actor=Actor(), payload={'notification_id': 1}, dry_run=True)

    assert result.status == 'dry_run'
    assert result.allowed is True
    assert calls == []


def test_notification_acknowledge_without_callback_is_not_implemented():
    action = NotificationAcknowledgeSafeAction(
        permission_check=lambda actor: True,
        notification_lookup=lambda notification_id: FakeNotification(notification_id),
    )

    result = action.run(actor=Actor(), payload={'notification_id': 1}, dry_run=False)

    assert result.status == 'not_implemented'
    assert result.allowed is False


def test_notification_acknowledge_with_callback_returns_success():
    calls = []

    def fake_acknowledge(**kwargs):
        calls.append(kwargs)
        kwargs['notification'].ack = True
        return {'details': {'source': 'fake_callback'}}

    action = NotificationAcknowledgeSafeAction(
        permission_check=lambda actor: True,
        notification_lookup=lambda notification_id: FakeNotification(notification_id),
        acknowledge_callback=fake_acknowledge,
    )

    result = action.run(actor=Actor(), payload={'notification_id': 7}, dry_run=False)

    assert result.status == 'acknowledged'
    assert result.allowed is True
    assert result.details['notification_id'] == 7
    assert result.details['source'] == 'fake_callback'
    assert len(calls) == 1


def test_notification_acknowledge_already_acked_is_idempotent():
    calls = []
    action = NotificationAcknowledgeSafeAction(
        permission_check=lambda actor: True,
        notification_lookup=lambda notification_id: FakeNotification(notification_id, ack=True),
        acknowledge_callback=lambda **kwargs: calls.append(kwargs),
    )

    result = action.run(actor=Actor(), payload={'notification_id': 5}, dry_run=False)

    assert result.status == 'already_acknowledged'
    assert result.allowed is True
    assert result.details['idempotent'] is True
    assert calls == []


def test_notification_acknowledge_audit_redacts_sensitive_payload():
    action = NotificationAcknowledgeSafeAction(
        permission_check=lambda actor: True,
        notification_lookup=lambda notification_id: FakeNotification(notification_id),
    )

    result = action.run(
        actor=Actor(),
        payload={
            'notification_id': 1,
            'refresh_token': 'do-not-render',
        },
        dry_run=True,
    )

    assert 'do-not-render' not in result.audit_message
    assert '[REDACTED]' in result.audit_message


def test_notification_acknowledge_service_invalid_id():
    repo = FakeNotificationRepository()
    service = NotificationAcknowledgeService(repo.lookup)

    result = service.acknowledge(notification_id=0)

    assert result.status == 'invalid_id'
    assert result.allowed is False
    assert repo.lookup_calls == []


def test_notification_acknowledge_service_missing_notification():
    repo = FakeNotificationRepository()
    service = NotificationAcknowledgeService(repo.lookup)

    result = service.acknowledge(notification_id=99)

    assert result.status == 'not_found'
    assert result.allowed is False
    assert repo.lookup_calls == [99]


def test_notification_acknowledge_service_already_acked_is_noop():
    notification = FakeNotification(5, ack=True)
    repo = FakeNotificationRepository({5: notification})
    service = NotificationAcknowledgeService(repo.lookup)

    result = service.acknowledge(notification_id=5)

    assert result.status == 'already_acked'
    assert result.allowed is True
    assert result.details['idempotent'] is True
    assert notification.set_ack_calls == 0


def test_notification_acknowledge_service_calls_set_ack_when_explicitly_executed():
    notification = FakeNotification(6, ack=False)
    repo = FakeNotificationRepository({6: notification})
    service = NotificationAcknowledgeService(repo.lookup)

    result = service.acknowledge(notification_id=6)

    assert result.status == 'acknowledged'
    assert result.allowed is True
    assert notification.ack is True
    assert notification.set_ack_calls == 1


def test_notification_acknowledge_service_repository_error_is_structured():
    repo = FakeNotificationRepository(error=RuntimeError('repository down api_token=secret'))
    service = NotificationAcknowledgeService(repo.lookup)

    result = service.acknowledge(notification_id=7)

    assert result.status == 'repository_error'
    assert result.allowed is False
    assert result.details['notification_id'] == 7
    assert result.details['error_type'] == 'RuntimeError'
    assert 'secret' not in str(result.to_dict())


def test_notification_acknowledge_service_set_ack_error_is_structured():
    notification = FailingSetAckNotification(8)
    repo = FakeNotificationRepository({8: notification})
    service = NotificationAcknowledgeService(repo.lookup)

    result = service.acknowledge(notification_id=8)

    assert result.status == 'acknowledge_failed'
    assert result.allowed is False
    assert result.details['error_type'] == 'RuntimeError'
    assert notification.set_ack_calls == 1


def test_notification_acknowledge_safe_action_uses_service_only_on_execute():
    notification = FakeNotification(9, ack=False)
    repo = FakeNotificationRepository({9: notification})
    service = NotificationAcknowledgeService(repo.lookup)
    action = NotificationAcknowledgeSafeAction(
        permission_check=lambda actor: True,
        acknowledge_service=service,
    )

    dry_run = action.run(actor=Actor(), payload={'notification_id': 9}, dry_run=True)
    assert dry_run.status == 'dry_run'
    assert notification.set_ack_calls == 0

    execute = action.run(actor=Actor(), payload={'notification_id': 9}, dry_run=False)
    assert execute.status == 'acknowledged'
    assert notification.set_ack_calls == 1


def test_notification_acknowledge_service_audit_record_is_redacted():
    notification = FakeNotification(10)
    repo = FakeNotificationRepository({10: notification})
    service = NotificationAcknowledgeService(repo.lookup)
    runner = build_notification_runner(
        lookup=service.lookup_notification,
        callback=service.acknowledge_callback,
    )

    _result, audit_record = runner.run_with_audit(
        action_id='notification.acknowledge',
        actor=Actor(),
        payload={
            'notification_id': 10,
            'api_token': 'service-secret',
        },
        dry_run=False,
    )
    data = audit_record.to_dict()

    assert data['status'] == 'acknowledged'
    assert 'service-secret' not in str(data)
    assert data['payload_summary']['api_token'] == '[REDACTED]'


def test_notification_acknowledge_service_has_no_flask_request_dependency():
    notification = FakeNotification(11)
    repo = FakeNotificationRepository({11: notification})
    service = NotificationAcknowledgeService(repo.lookup)

    result = service.acknowledge(notification_id=11, actor=Actor())

    assert result.status == 'acknowledged'
    assert notification.ack is True


def test_notification_acknowledge_service_with_audit_success():
    notification = FakeNotification(12)
    repo = FakeNotificationRepository({12: notification})
    audit_log = FakeAuditLog()
    service = NotificationAcknowledgeService(repo.lookup)

    result, audit_record, audit_write = service.acknowledge_with_audit(
        notification_id=12,
        actor=Actor(),
        payload={'notification_id': 12},
        audit_log=audit_log,
        dry_run=False,
    )

    assert result.status == 'acknowledged'
    assert audit_record.status == 'acknowledged'
    assert audit_write['written'] is True
    assert len(audit_log.records) == 1
    assert notification.set_ack_calls == 1


def test_notification_acknowledge_service_with_audit_failure():
    notification = FailingSetAckNotification(13)
    repo = FakeNotificationRepository({13: notification})
    audit_log = FakeAuditLog()
    service = NotificationAcknowledgeService(repo.lookup)

    result, audit_record, audit_write = service.acknowledge_with_audit(
        notification_id=13,
        actor=Actor(),
        payload={'notification_id': 13},
        audit_log=audit_log,
        dry_run=False,
    )

    assert result.status == 'acknowledge_failed'
    assert audit_record.status == 'acknowledge_failed'
    assert audit_record.allowed is False
    assert audit_write['written'] is True
    assert len(audit_log.records) == 1


def test_notification_acknowledge_service_with_audit_redacts_fake_log_record():
    notification = FakeNotification(14)
    repo = FakeNotificationRepository({14: notification})
    audit_log = FakeAuditLog()
    service = NotificationAcknowledgeService(repo.lookup)

    _result, _audit_record, _audit_write = service.acknowledge_with_audit(
        notification_id=14,
        actor=Actor(),
        payload={
            'notification_id': 14,
            'refresh_token': 'log-secret',
        },
        audit_log=audit_log,
        dry_run=False,
    )

    assert 'log-secret' not in str(audit_log.records)
    assert audit_log.records[0]['payload_summary']['refresh_token'] == '[REDACTED]'


def test_notification_acknowledge_service_dry_run_with_audit_does_not_set_ack():
    notification = FakeNotification(15)
    repo = FakeNotificationRepository({15: notification})
    audit_log = FakeAuditLog()
    service = NotificationAcknowledgeService(repo.lookup)

    result, audit_record, audit_write = service.acknowledge_with_audit(
        notification_id=15,
        actor=Actor(),
        payload={'notification_id': 15},
        audit_log=audit_log,
        dry_run=True,
    )

    assert result.status == 'dry_run'
    assert result.dry_run is True
    assert audit_record.status == 'dry_run'
    assert audit_write['written'] is True
    assert notification.set_ack_calls == 0


def build_notification_runner(permission_check=None, lookup=None, callback=None):
    registry = ModernAdminSafeActionRegistry()
    registry.register(NotificationAcknowledgeSafeAction(
        permission_check=permission_check or (lambda actor: True),
        notification_lookup=lookup,
        acknowledge_callback=callback,
    ))
    return ModernAdminSafeActionRunner(registry)


def test_runner_missing_action_id():
    runner = ModernAdminSafeActionRunner(ModernAdminSafeActionRegistry())
    result = runner.run(action_id='', actor=Actor(), payload={}, dry_run=True)

    assert result.status == 'missing_action_id'
    assert result.allowed is False


def test_runner_unknown_action_id():
    runner = ModernAdminSafeActionRunner(ModernAdminSafeActionRegistry())
    result = runner.run(action_id='missing.action', actor=Actor(), payload={}, dry_run=True)

    assert result.status == 'not_found'
    assert result.allowed is False


def test_runner_permission_denied_does_not_execute():
    calls = []
    runner = build_notification_runner(
        permission_check=lambda actor: False,
        lookup=lambda notification_id: FakeNotification(notification_id),
        callback=lambda **kwargs: calls.append(kwargs),
    )

    result = runner.run(
        action_id='notification.acknowledge',
        actor=Actor(),
        payload={'notification_id': 1},
        dry_run=False,
    )

    assert result.status == 'permission_denied'
    assert result.allowed is False
    assert calls == []


def test_runner_validation_failure_does_not_execute():
    calls = []
    runner = build_notification_runner(
        lookup=lambda notification_id: None,
        callback=lambda **kwargs: calls.append(kwargs),
    )

    result = runner.run(
        action_id='notification.acknowledge',
        actor=Actor(),
        payload={'notification_id': 42},
        dry_run=False,
    )

    assert result.status == 'validation_failed'
    assert result.allowed is False
    assert calls == []


def test_runner_dry_run_success_without_execute_callback():
    runner = build_notification_runner(
        lookup=lambda notification_id: FakeNotification(notification_id),
    )

    result = runner.run(
        action_id='notification.acknowledge',
        actor=Actor(),
        payload={'notification_id': 2},
        dry_run=True,
    )

    assert result.status == 'dry_run'
    assert result.allowed is True


def test_runner_execute_success_with_fake_callback():
    calls = []

    def fake_acknowledge(**kwargs):
        calls.append(kwargs)
        return {'details': {'runner': 'safe'}}

    runner = build_notification_runner(
        lookup=lambda notification_id: FakeNotification(notification_id),
        callback=fake_acknowledge,
    )

    result = runner.run(
        action_id='notification.acknowledge',
        actor=Actor(),
        payload={'notification_id': 3},
        dry_run=False,
    )

    assert result.status == 'acknowledged'
    assert result.allowed is True
    assert result.details['notification_id'] == 3
    assert result.details['runner'] == 'safe'
    assert len(calls) == 1


def test_runner_execute_failure_structured():
    def fake_failure(**kwargs):
        action = NotificationAcknowledgeSafeAction(permission_check=lambda actor: True)
        return action.result(
            status='execute_failed',
            message='Fake failure',
            dry_run=False,
            allowed=False,
            audit_message=action.audit_message(kwargs.get('actor'), kwargs.get('payload', {}), 'execute_failed'),
            details={'notification_id': kwargs['notification_id']},
        )

    runner = build_notification_runner(
        lookup=lambda notification_id: FakeNotification(notification_id),
        callback=fake_failure,
    )

    result = runner.run(
        action_id='notification.acknowledge',
        actor=Actor(),
        payload={'notification_id': 4},
        dry_run=False,
    )

    assert result.status == 'execute_failed'
    assert result.allowed is False
    assert result.details['notification_id'] == 4


def test_runner_audit_redaction():
    runner = build_notification_runner(
        lookup=lambda notification_id: FakeNotification(notification_id),
    )

    result = runner.run(
        action_id='notification.acknowledge',
        actor=Actor(),
        payload={
            'notification_id': 5,
            'client_secret': 'do-not-log',
        },
        dry_run=True,
    )

    assert 'do-not-log' not in result.audit_message
    assert '[REDACTED]' in result.audit_message


def test_runner_has_no_flask_request_dependency():
    runner = build_notification_runner(
        lookup=lambda notification_id: FakeNotification(notification_id),
    )

    result = runner.run(
        action_id='notification.acknowledge',
        actor=Actor(),
        payload={'notification_id': 6},
        dry_run=True,
    )

    assert result.status == 'dry_run'
    assert result.allowed is True


def test_notification_acknowledge_dry_run_registry_has_no_execute_callback():
    registry = build_notification_acknowledge_dry_run_registry(
        permission_check=lambda actor: True,
    )
    runner = ModernAdminSafeActionRunner(registry)

    dry_run = runner.run(
        action_id='notification.acknowledge',
        actor=Actor(),
        payload={'notification_id': 8},
        dry_run=True,
    )
    execute = runner.run(
        action_id='notification.acknowledge',
        actor=Actor(),
        payload={'notification_id': 8},
        dry_run=False,
    )

    assert dry_run.status == 'dry_run'
    assert dry_run.allowed is True
    assert execute.status == 'not_implemented'
    assert execute.allowed is False


def test_dry_run_helper_missing_action_id():
    result = run_modern_safe_action_dry_run(
        action_id=None,
        actor=Actor(),
        payload={},
        permission_check=lambda actor: True,
    )

    assert result.status == 'missing_action_id'
    assert result.allowed is False


def test_dry_run_helper_unknown_action_id():
    result = run_modern_safe_action_dry_run(
        action_id='unknown.action',
        actor=Actor(),
        payload={},
        permission_check=lambda actor: True,
    )

    assert result.status == 'not_found'
    assert result.allowed is False


def test_dry_run_helper_notification_acknowledge_success():
    result = run_modern_safe_action_dry_run(
        action_id='notification.acknowledge',
        actor=Actor(),
        payload={'notification_id': 9},
        permission_check=lambda actor: True,
    )

    assert result.status == 'dry_run'
    assert result.allowed is True


def test_dry_run_helper_permission_denied():
    result = run_modern_safe_action_dry_run(
        action_id='notification.acknowledge',
        actor=Actor(),
        payload={'notification_id': 9},
        permission_check=lambda actor: False,
    )

    assert result.status == 'permission_denied'
    assert result.allowed is False


def test_dry_run_helper_redacts_secret_payload():
    result = run_modern_safe_action_dry_run(
        action_id='notification.acknowledge',
        actor=Actor(),
        payload={
            'notification_id': 9,
            'api_token': 'do-not-return',
        },
        permission_check=lambda actor: True,
    )

    assert 'do-not-return' not in result.audit_message
    assert '[REDACTED]' in result.audit_message


def get_safe_action_dry_run_view_source():
    source = (Path(__file__).resolve().parents[1] / 'indi_allsky' / 'flask' / 'views.py').read_text()
    class_start = source.index('class ModernAdminSafeActionDryRunView')
    class_end = source.index('class ModernAdminCaptureServiceActionView')
    return source[class_start:class_end], source


def test_safe_action_dry_run_route_exists_and_is_post_only_static():
    view_source, full_source = get_safe_action_dry_run_view_source()

    assert "methods = ['POST']" in view_source
    assert "bp_allsky.add_url_rule('/modern-admin/safe-action/dry-run'" in full_source
    assert "methods=['POST']" in full_source


def test_safe_action_dry_run_view_has_no_legacy_ack_path_static():
    view_source, _full_source = get_safe_action_dry_run_view_source()

    assert '/ajax/notification' not in view_source
    assert 'setAck(' not in view_source
    assert 'db.session' not in view_source
    assert 'commit(' not in view_source


def test_safe_action_dry_run_helper_response_shape():
    result = run_modern_safe_action_dry_run(
        action_id='notification.acknowledge',
        actor=AdminActor(),
        payload={'notification_id': 1},
        permission_check=lambda actor: bool(getattr(actor, 'is_admin', False)),
    )
    data = result.to_dict()

    assert data['action_id'] == 'notification.acknowledge'
    assert data['status'] == 'dry_run'
    assert data['dry_run'] is True
    assert data['allowed'] is True


def test_safe_action_dry_run_helper_permission_denied_response_shape():
    result = run_modern_safe_action_dry_run(
        action_id='notification.acknowledge',
        actor=NonAdminActor(),
        payload={'notification_id': 1},
        permission_check=lambda actor: bool(getattr(actor, 'is_admin', False)),
    )
    data = result.to_dict()

    assert data['status'] == 'permission_denied'
    assert data['allowed'] is False


def test_safe_action_dry_run_helper_forces_dry_run_true():
    result = run_modern_safe_action_dry_run(
        action_id='notification.acknowledge',
        actor=AdminActor(),
        payload={
            'notification_id': 1,
            'dry_run': False,
        },
        permission_check=lambda actor: True,
    )

    assert result.status == 'dry_run'
    assert result.dry_run is True


def test_safe_action_dry_run_helper_response_redacts_sensitive_payload():
    result = run_modern_safe_action_dry_run(
        action_id='notification.acknowledge',
        actor=AdminActor(),
        payload={
            'notification_id': 1,
            'refresh_token': 'never-render',
        },
        permission_check=lambda actor: True,
    )
    data = result.to_dict()

    assert 'never-render' not in str(data)
    assert '[REDACTED]' in data['audit_message']


def test_audit_record_generated_for_dry_run_success():
    runner = build_notification_runner(
        lookup=lambda notification_id: FakeNotification(notification_id),
    )
    result, audit_record = runner.run_with_audit(
        action_id='notification.acknowledge',
        actor=Actor(),
        payload={'notification_id': 10},
        dry_run=True,
    )

    assert result.status == 'dry_run'
    assert audit_record.action_id == 'notification.acknowledge'
    assert audit_record.status == 'dry_run'
    assert audit_record.dry_run is True
    assert audit_record.allowed is True
    assert audit_record.payload_summary['notification_id'] == 10


def test_audit_record_generated_for_permission_denied():
    runner = build_notification_runner(
        permission_check=lambda actor: False,
        lookup=lambda notification_id: FakeNotification(notification_id),
    )
    result, audit_record = runner.run_with_audit(
        action_id='notification.acknowledge',
        actor=Actor(),
        payload={'notification_id': 10},
        dry_run=False,
    )

    assert result.status == 'permission_denied'
    assert audit_record.status == 'permission_denied'
    assert audit_record.allowed is False
    assert audit_record.reason == 'Permission denied'


def test_audit_record_generated_for_validation_failure():
    runner = build_notification_runner(
        lookup=lambda notification_id: None,
    )
    result, audit_record = runner.run_with_audit(
        action_id='notification.acknowledge',
        actor=Actor(),
        payload={'notification_id': 10},
        dry_run=False,
    )

    assert result.status == 'validation_failed'
    assert audit_record.status == 'validation_failed'
    assert audit_record.allowed is False
    assert 'does not exist' in audit_record.reason


def test_audit_record_redacts_sensitive_payload():
    runner = build_notification_runner(
        lookup=lambda notification_id: FakeNotification(notification_id),
    )
    _result, audit_record = runner.run_with_audit(
        action_id='notification.acknowledge',
        actor=Actor(),
        payload={
            'notification_id': 10,
            'api_token': 'payload-secret',
        },
        dry_run=True,
    )
    data = audit_record.to_dict()

    assert 'payload-secret' not in str(data)
    assert data['payload_summary']['api_token'] == '[REDACTED]'


def test_audit_record_redacts_sensitive_result_details():
    result = ModernAdminSafeActionResult(
        action_id='test.result',
        feature='Testing',
        risk_level='high',
        status='execute_failed',
        message='Failed',
        details={
            'refresh_token': 'result-secret',
            'safe': 'visible',
        },
    )
    audit_record = ModernAdminSafeActionAuditRecord.from_result(
        result,
        actor=Actor(),
        payload={},
    )
    data = audit_record.to_dict()

    assert 'result-secret' not in str(data)
    assert data['result_summary']['details']['refresh_token'] == '[REDACTED]'
    assert data['result_summary']['details']['safe'] == 'visible'


def test_audit_record_actor_is_safe_label_only():
    runner = build_notification_runner(
        lookup=lambda notification_id: FakeNotification(notification_id),
    )
    _result, audit_record = runner.run_with_audit(
        action_id='notification.acknowledge',
        actor=NonAdminActor(),
        payload={'notification_id': 10},
        dry_run=True,
    )

    assert audit_record.actor == 'operator'
    assert 'do-not-render' not in str(audit_record.to_dict())


def test_audit_record_to_dict_is_json_safe():
    runner = build_notification_runner(
        lookup=lambda notification_id: FakeNotification(notification_id),
    )
    _result, audit_record = runner.run_with_audit(
        action_id='notification.acknowledge',
        actor=Actor(),
        payload={'notification_id': 10},
        dry_run=True,
    )

    json.dumps(audit_record.to_dict())


def test_audit_record_has_no_flask_request_dependency():
    runner = build_notification_runner(
        lookup=lambda notification_id: FakeNotification(notification_id),
    )
    _result, audit_record = runner.run_with_audit(
        action_id='notification.acknowledge',
        actor=Actor(),
        payload={'notification_id': 10},
        dry_run=True,
    )

    assert audit_record.status == 'dry_run'


def build_sample_audit_record(created_at='2026-06-27T10:00:00Z'):
    return ModernAdminSafeActionAuditRecord(
        action_id='notification.acknowledge',
        feature='Notifications',
        actor='operator',
        dry_run=True,
        allowed=True,
        status='dry_run',
        risk_level='medium',
        payload_summary={
            'notification_id': 1,
            'api_token': 'payload-secret',
        },
        result_summary={
            'status': 'dry_run',
            'details': {
                'refresh_token': 'result-secret',
            },
        },
        reason='Dry run only',
        created_at=created_at,
    )


def test_audit_log_writes_one_record():
    with TemporaryDirectory() as tmpdir:
        audit_log = ModernAdminSafeActionAuditLog(tmpdir)
        result = audit_log.append(build_sample_audit_record())
        path = Path(result['path'])

        assert result['written'] is True
        assert path.exists()
        lines = path.read_text().splitlines()
        assert len(lines) == 1
        data = json.loads(lines[0])
        assert data['action_id'] == 'notification.acknowledge'
        assert data['status'] == 'dry_run'


def test_audit_log_appends_multiple_records():
    with TemporaryDirectory() as tmpdir:
        audit_log = ModernAdminSafeActionAuditLog(tmpdir)
        audit_log.append(build_sample_audit_record())
        audit_log.append(build_sample_audit_record())

        path = Path(tmpdir) / '2026-06-27.jsonl'
        assert len(path.read_text().splitlines()) == 2


def test_audit_log_creates_directory():
    with TemporaryDirectory() as tmpdir:
        audit_dir = Path(tmpdir) / 'nested' / 'audit'
        audit_log = ModernAdminSafeActionAuditLog(audit_dir)
        audit_log.append(build_sample_audit_record())

        assert audit_dir.exists()
        assert (audit_dir / '2026-06-27.jsonl').exists()


def test_audit_log_redacts_sensitive_fields():
    with TemporaryDirectory() as tmpdir:
        audit_log = ModernAdminSafeActionAuditLog(tmpdir)
        result = audit_log.append(build_sample_audit_record())
        contents = Path(result['path']).read_text()

        assert 'payload-secret' not in contents
        assert 'result-secret' not in contents
        assert '[REDACTED]' in contents


def test_audit_log_retention_limits_files():
    with TemporaryDirectory() as tmpdir:
        audit_log = ModernAdminSafeActionAuditLog(tmpdir, max_files=2)
        audit_log.append(build_sample_audit_record(created_at='2026-06-25T10:00:00Z'))
        audit_log.append(build_sample_audit_record(created_at='2026-06-26T10:00:00Z'))
        audit_log.append(build_sample_audit_record(created_at='2026-06-27T10:00:00Z'))

        files = sorted(path.name for path in Path(tmpdir).glob('*.jsonl'))
        assert files == ['2026-06-26.jsonl', '2026-06-27.jsonl']


def test_audit_log_record_size_limit():
    with TemporaryDirectory() as tmpdir:
        audit_log = ModernAdminSafeActionAuditLog(tmpdir, max_record_bytes=64)

        try:
            audit_log.append(build_sample_audit_record())
        except ValueError as e:
            assert 'max_record_bytes' in str(e)
        else:
            raise AssertionError('Oversized audit record did not fail')


if __name__ == '__main__':
    test_default_action_does_not_execute()
    test_dry_run_does_not_mutate()
    test_action_without_permission_fails()
    test_result_is_structured()
    test_audit_message_redacts_secret_payload()
    test_registry_empty()
    test_registry_register_and_lookup()
    test_registry_duplicate_action_id_fails()
    test_registry_missing_action_returns_structured_error()
    test_registry_filters_by_feature_and_risk()
    test_default_placeholder_actions_do_not_execute()
    test_placeholder_dry_run_is_safe_when_permission_allows()
    test_notification_acknowledge_permission_denied()
    test_notification_acknowledge_missing_notification_id()
    test_notification_acknowledge_invalid_notification_id()
    test_notification_acknowledge_missing_lookup_result()
    test_notification_acknowledge_dry_run_does_not_call_callback()
    test_notification_acknowledge_without_callback_is_not_implemented()
    test_notification_acknowledge_with_callback_returns_success()
    test_notification_acknowledge_already_acked_is_idempotent()
    test_notification_acknowledge_audit_redacts_sensitive_payload()
    test_notification_acknowledge_service_invalid_id()
    test_notification_acknowledge_service_missing_notification()
    test_notification_acknowledge_service_already_acked_is_noop()
    test_notification_acknowledge_service_calls_set_ack_when_explicitly_executed()
    test_notification_acknowledge_service_repository_error_is_structured()
    test_notification_acknowledge_service_set_ack_error_is_structured()
    test_notification_acknowledge_safe_action_uses_service_only_on_execute()
    test_notification_acknowledge_service_audit_record_is_redacted()
    test_notification_acknowledge_service_has_no_flask_request_dependency()
    test_notification_acknowledge_service_with_audit_success()
    test_notification_acknowledge_service_with_audit_failure()
    test_notification_acknowledge_service_with_audit_redacts_fake_log_record()
    test_notification_acknowledge_service_dry_run_with_audit_does_not_set_ack()
    test_runner_missing_action_id()
    test_runner_unknown_action_id()
    test_runner_permission_denied_does_not_execute()
    test_runner_validation_failure_does_not_execute()
    test_runner_dry_run_success_without_execute_callback()
    test_runner_execute_success_with_fake_callback()
    test_runner_execute_failure_structured()
    test_runner_audit_redaction()
    test_runner_has_no_flask_request_dependency()
    test_notification_acknowledge_dry_run_registry_has_no_execute_callback()
    test_dry_run_helper_missing_action_id()
    test_dry_run_helper_unknown_action_id()
    test_dry_run_helper_notification_acknowledge_success()
    test_dry_run_helper_permission_denied()
    test_dry_run_helper_redacts_secret_payload()
    test_safe_action_dry_run_route_exists_and_is_post_only_static()
    test_safe_action_dry_run_view_has_no_legacy_ack_path_static()
    test_safe_action_dry_run_helper_response_shape()
    test_safe_action_dry_run_helper_permission_denied_response_shape()
    test_safe_action_dry_run_helper_forces_dry_run_true()
    test_safe_action_dry_run_helper_response_redacts_sensitive_payload()
    test_audit_record_generated_for_dry_run_success()
    test_audit_record_generated_for_permission_denied()
    test_audit_record_generated_for_validation_failure()
    test_audit_record_redacts_sensitive_payload()
    test_audit_record_redacts_sensitive_result_details()
    test_audit_record_actor_is_safe_label_only()
    test_audit_record_to_dict_is_json_safe()
    test_audit_record_has_no_flask_request_dependency()
    test_audit_log_writes_one_record()
    test_audit_log_appends_multiple_records()
    test_audit_log_creates_directory()
    test_audit_log_redacts_sensitive_fields()
    test_audit_log_retention_limits_files()
    test_audit_log_record_size_limit()
    print('Modern safe action tests passed')
