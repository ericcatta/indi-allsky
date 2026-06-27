#!/usr/bin/env python3

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from indi_allsky.modern_safe_action import ModernAdminSafeAction
from indi_allsky.modern_safe_action import ModernAdminSafeActionResult


class Actor:
    username = 'safe-admin'


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


if __name__ == '__main__':
    test_default_action_does_not_execute()
    test_dry_run_does_not_mutate()
    test_action_without_permission_fails()
    test_result_is_structured()
    test_audit_message_redacts_secret_payload()
    print('Modern safe action tests passed')
