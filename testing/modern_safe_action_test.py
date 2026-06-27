#!/usr/bin/env python3

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from indi_allsky.modern_safe_action import ModernAdminSafeAction
from indi_allsky.modern_safe_action import ModernAdminSafeActionPlaceholder
from indi_allsky.modern_safe_action import ModernAdminSafeActionRegistry
from indi_allsky.modern_safe_action import ModernAdminSafeActionResult
from indi_allsky.modern_safe_action import NotificationAcknowledgeSafeAction
from indi_allsky.modern_safe_action import build_default_modern_safe_action_registry


class Actor:
    username = 'safe-admin'


class FakeNotification:
    def __init__(self, notification_id, ack=False):
        self.id = notification_id
        self.ack = ack


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
    print('Modern safe action tests passed')
