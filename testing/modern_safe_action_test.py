#!/usr/bin/env python3

import json
import sys
import subprocess
from tempfile import TemporaryDirectory
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from indi_allsky.modern_safe_action import ModernAdminSafeAction
from indi_allsky.modern_safe_action import ModernAdminSafeActionAuditLog
from indi_allsky.modern_safe_action import ModernAdminSafeActionPlaceholder
from indi_allsky.modern_safe_action import ModernAdminSafeActionAuditRecord
from indi_allsky.modern_safe_action import ModernAdminSafeActionContract
from indi_allsky.modern_safe_action import ModernAdminSafeActionRegistry
from indi_allsky.modern_safe_action import ModernAdminSafeActionResult
from indi_allsky.modern_safe_action import ModernAdminSafeActionRunner
from indi_allsky.modern_safe_action import ImageExcludeDbAdapter
from indi_allsky.modern_safe_action import ImageExcludeRepositoryError
from indi_allsky.modern_safe_action import ImageExcludeSafeAction
from indi_allsky.modern_safe_action import ImageExcludeService
from indi_allsky.modern_safe_action import ImageUnexcludeSafeAction
from indi_allsky.modern_safe_action import LogDownloadPolicy
from indi_allsky.modern_safe_action import LogDownloadSafeAction
from indi_allsky.modern_safe_action import LogDownloadService
from indi_allsky.modern_safe_action import ModernAdminAbortExposureActionPlanner
from indi_allsky.modern_safe_action import ModernAdminCaptureServiceCommandBoundary
from indi_allsky.modern_safe_action import ModernAdminGeneratedOutputActionPlanner
from indi_allsky.modern_safe_action import ModernAdminMaintenanceActionPlanner
from indi_allsky.modern_safe_action import ModernAdminSystemPowerCommandBoundary
from indi_allsky.modern_safe_action import NotificationAcknowledgeDbAdapter
from indi_allsky.modern_safe_action import NotificationAcknowledgeRepositoryError
from indi_allsky.modern_safe_action import NotificationAcknowledgeSafeAction
from indi_allsky.modern_safe_action import NotificationAcknowledgeService
from indi_allsky.modern_safe_action import build_default_modern_safe_action_registry
from indi_allsky.modern_safe_action import build_notification_acknowledge_dry_run_registry
from indi_allsky.modern_safe_action import run_modern_safe_action_dry_run
from indi_allsky.modern_admin_runtime_effects import ModernAdminServiceControlEffectAdapter
from indi_allsky.modern_admin_runtime_effects import ModernAdminSystemPowerEffectAdapter
from indi_allsky.modern_admin_runtime_effects import ModernAdminTaskEnqueueEffectAdapter


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


class FakeImage:
    def __init__(self, image_id, camera_id=1, exclude=False):
        self.id = image_id
        self.camera_id = camera_id
        self.exclude = exclude


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


class FakeNoResultFound(Exception):
    pass


class FakeQuery:
    def __init__(self, notification=None, image=None, error=None):
        self.notification = notification
        self.image = image
        self.error = error
        self.filter_by_calls = []
        self.one_calls = 0


    def filter_by(self, **kwargs):
        self.filter_by_calls.append(kwargs)
        return self


    def one(self):
        self.one_calls += 1
        if self.error:
            raise self.error

        if self.image is not None:
            return self.image

        return self.notification


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


def test_safe_action_contract_shape_is_stable():
    contract = ModernAdminSafeActionContract(
        action_id='test.contract',
        label='Test Contract',
        feature='Testing',
        risk_level='medium',
        required_permission='admin',
    )

    assert contract.to_dict() == {
        'action_id'           : 'test.contract',
        'label'               : 'Test Contract',
        'feature'             : 'Testing',
        'risk_level'          : 'medium',
        'required_permission' : 'admin',
    }


def test_safe_action_contract_uses_class_metadata():
    contract = ExampleAction.action_contract()

    assert contract.to_dict() == {
        'action_id'           : 'test.example_action',
        'label'               : 'Example Action',
        'feature'             : 'Testing',
        'risk_level'          : 'low',
        'required_permission' : 'admin',
    }


def test_placeholder_contract_uses_instance_metadata():
    action = ModernAdminSafeActionPlaceholder(
        action_id='placeholder.contract',
        label='Placeholder Contract',
        feature='Placeholder',
        risk_level='high',
        permission_check=lambda actor: True,
    )

    assert action.contract.to_dict() == {
        'action_id'           : 'placeholder.contract',
        'label'               : 'Placeholder Contract',
        'feature'             : 'Placeholder',
        'risk_level'          : 'high',
        'required_permission' : 'admin',
    }


def test_notification_acknowledge_contract_uses_domain_metadata():
    action = NotificationAcknowledgeSafeAction(permission_check=lambda actor: True)

    assert action.contract.to_dict() == {
        'action_id'           : 'notification.acknowledge',
        'label'               : 'Acknowledge Notification',
        'feature'             : 'Notifications',
        'risk_level'          : 'medium',
        'required_permission' : 'admin',
    }


def test_safe_action_contract_does_not_change_result_shape():
    action = ExampleAction(permission_check=lambda actor: True)
    result = action.run(actor=Actor(), payload={}, dry_run=True).to_dict()

    assert list(result.keys()) == [
        'action_id',
        'feature',
        'risk_level',
        'status',
        'message',
        'dry_run',
        'allowed',
        'audit_message',
        'details',
        'created_at',
    ]


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


def test_registry_output_shape_remains_backward_compatible():
    registry = ModernAdminSafeActionRegistry()
    registry.register(ExampleAction(permission_check=lambda actor: True))

    assert registry.to_dict() == [
        {
            'action_id'  : 'test.example_action',
            'label'      : 'Example Action',
            'feature'    : 'Testing',
            'risk_level' : 'low',
        },
    ]


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


def test_notification_acknowledge_db_adapter_lookup_success():
    notification = FakeNotification(21)
    query = FakeQuery(notification=notification)
    adapter = NotificationAcknowledgeDbAdapter(
        query=query,
        no_result_exceptions=(FakeNoResultFound,),
    )

    result = adapter.lookup(21)

    assert result is notification
    assert query.filter_by_calls == [{'id': 21}]
    assert query.one_calls == 1


def test_notification_acknowledge_db_adapter_not_found():
    query = FakeQuery(error=FakeNoResultFound())
    adapter = NotificationAcknowledgeDbAdapter(
        query=query,
        no_result_exceptions=(FakeNoResultFound,),
    )

    result = adapter.lookup(22)

    assert result is None
    assert query.filter_by_calls == [{'id': 22}]


def test_notification_acknowledge_db_adapter_query_exception_is_sanitized():
    query = FakeQuery(error=RuntimeError('database exploded api_token=secret'))
    adapter = NotificationAcknowledgeDbAdapter(query=query)

    try:
        adapter.lookup(23)
    except NotificationAcknowledgeRepositoryError as e:
        assert str(e) == 'RuntimeError'
        assert 'secret' not in str(e)
    else:
        raise AssertionError('Repository exception was not raised')


def test_notification_acknowledge_db_adapter_lookup_does_not_ack():
    notification = FakeNotification(24)
    query = FakeQuery(notification=notification)
    adapter = NotificationAcknowledgeDbAdapter(query=query)

    result = adapter.lookup(24)

    assert result is notification
    assert notification.set_ack_calls == 0
    assert notification.ack is False


def test_notification_acknowledge_service_with_db_adapter_already_acked():
    notification = FakeNotification(25, ack=True)
    adapter = NotificationAcknowledgeDbAdapter(query=FakeQuery(notification=notification))
    service = NotificationAcknowledgeService(adapter.lookup)

    result = service.acknowledge(notification_id=25)

    assert result.status == 'already_acked'
    assert result.allowed is True
    assert notification.set_ack_calls == 0


def test_notification_acknowledge_service_with_db_adapter_not_acked():
    notification = FakeNotification(26, ack=False)
    adapter = NotificationAcknowledgeDbAdapter(query=FakeQuery(notification=notification))
    service = NotificationAcknowledgeService(adapter.lookup)

    result = service.acknowledge(notification_id=26)

    assert result.status == 'acknowledged'
    assert result.allowed is True
    assert notification.ack is True
    assert notification.set_ack_calls == 1


def test_notification_acknowledge_service_with_db_adapter_set_ack_error():
    notification = FailingSetAckNotification(27)
    adapter = NotificationAcknowledgeDbAdapter(query=FakeQuery(notification=notification))
    service = NotificationAcknowledgeService(adapter.lookup)

    result = service.acknowledge(notification_id=27)

    assert result.status == 'acknowledge_failed'
    assert result.allowed is False
    assert result.details['error_type'] == 'RuntimeError'


def test_notification_acknowledge_service_with_db_adapter_repository_error_redacted():
    query = FakeQuery(error=RuntimeError('database exploded refresh_token=secret'))
    adapter = NotificationAcknowledgeDbAdapter(query=query)
    service = NotificationAcknowledgeService(adapter.lookup)

    result = service.acknowledge(notification_id=28)

    assert result.status == 'repository_error'
    assert result.allowed is False
    assert result.details['error_type'] == 'NotificationAcknowledgeRepositoryError'
    assert 'secret' not in str(result.to_dict())


def test_image_exclude_db_adapter_lookup_success():
    image = FakeImage(101, camera_id=3)
    query = FakeQuery(image=image)
    adapter = ImageExcludeDbAdapter(
        query=query,
        no_result_exceptions=(FakeNoResultFound,),
    )

    result = adapter.lookup(101, 3)

    assert result is image
    assert query.filter_by_calls == [{'id': 101, 'camera_id': 3}]
    assert query.one_calls == 1


def test_image_exclude_db_adapter_not_found():
    query = FakeQuery(error=FakeNoResultFound())
    adapter = ImageExcludeDbAdapter(
        query=query,
        no_result_exceptions=(FakeNoResultFound,),
    )

    result = adapter.lookup(102, 3)

    assert result is None
    assert query.filter_by_calls == [{'id': 102, 'camera_id': 3}]


def test_image_exclude_db_adapter_query_exception_is_sanitized():
    query = FakeQuery(error=RuntimeError('database exploded api_key=secret'))
    adapter = ImageExcludeDbAdapter(query=query)

    try:
        adapter.lookup(103, 3)
    except ImageExcludeRepositoryError as e:
        assert str(e) == 'RuntimeError'
        assert 'secret' not in str(e)
    else:
        raise AssertionError('Repository exception was not raised')


def test_image_exclude_db_adapter_lookup_does_not_mutate():
    image = FakeImage(104, camera_id=3, exclude=False)
    adapter = ImageExcludeDbAdapter(query=FakeQuery(image=image))

    result = adapter.lookup(104, 3)

    assert result is image
    assert image.exclude is False


def test_image_exclude_service_invalid_ids():
    calls = []
    service = ImageExcludeService(lambda image_id, camera_id: calls.append((image_id, camera_id)))

    result = service.set_exclude(image_id=0, camera_id=3, exclude=True)

    assert result.status == 'invalid_id'
    assert result.allowed is False
    assert calls == []

    result = service.set_exclude(image_id=1, camera_id=0, exclude=True)

    assert result.status == 'invalid_camera_id'
    assert result.allowed is False
    assert calls == []


def test_image_exclude_service_invalid_exclude_value():
    calls = []
    service = ImageExcludeService(lambda image_id, camera_id: calls.append((image_id, camera_id)))

    result = service.set_exclude(image_id=1, camera_id=3, exclude='true')

    assert result.status == 'invalid_exclude'
    assert result.allowed is False
    assert calls == []


def test_image_exclude_service_missing_image():
    service = ImageExcludeService(lambda image_id, camera_id: None)

    result = service.set_exclude(image_id=105, camera_id=3, exclude=True)

    assert result.status == 'not_found'
    assert result.allowed is False


def test_image_exclude_service_repository_error_redacted():
    def lookup(image_id, camera_id):
        raise RuntimeError('lookup failed refresh_token=secret')

    service = ImageExcludeService(lookup)

    result = service.set_exclude(image_id=106, camera_id=3, exclude=True)

    assert result.status == 'repository_error'
    assert result.allowed is False
    assert result.details['error_type'] == 'RuntimeError'
    assert 'secret' not in str(result.to_dict())


def test_image_exclude_service_already_set_is_noop():
    image = FakeImage(107, camera_id=3, exclude=True)
    calls = []
    service = ImageExcludeService(
        lambda image_id, camera_id: image,
        apply_callback=lambda **kwargs: calls.append(kwargs),
    )

    result = service.set_exclude(image_id=107, camera_id=3, exclude=True)

    assert result.status == 'already_set'
    assert result.allowed is True
    assert result.details['idempotent'] is True
    assert calls == []


def test_image_exclude_service_dry_run_does_not_apply():
    image = FakeImage(108, camera_id=3, exclude=False)
    calls = []
    service = ImageExcludeService(
        lambda image_id, camera_id: image,
        apply_callback=lambda **kwargs: calls.append(kwargs),
    )

    result = service.set_exclude(image_id=108, camera_id=3, exclude=True, dry_run=True)

    assert result.status == 'dry_run'
    assert result.allowed is True
    assert image.exclude is False
    assert calls == []


def test_image_exclude_service_without_apply_callback_is_not_implemented():
    image = FakeImage(109, camera_id=3, exclude=False)
    service = ImageExcludeService(lambda image_id, camera_id: image)

    result = service.set_exclude(image_id=109, camera_id=3, exclude=True)

    assert result.status == 'not_implemented'
    assert result.allowed is False
    assert image.exclude is False


def test_image_exclude_service_with_fake_apply_excludes_image():
    image = FakeImage(110, camera_id=3, exclude=False)
    calls = []

    def apply(**kwargs):
        calls.append(kwargs)
        kwargs['image'].exclude = kwargs['exclude']
        return {'details': {'source': 'fake_apply'}}

    service = ImageExcludeService(
        lambda image_id, camera_id: image,
        apply_callback=apply,
    )

    result = service.set_exclude(image_id=110, camera_id=3, exclude=True)

    assert result.status == 'excluded'
    assert result.allowed is True
    assert image.exclude is True
    assert len(calls) == 1
    assert result.details['source'] == 'fake_apply'


def test_image_exclude_service_with_fake_apply_unexcludes_image():
    image = FakeImage(111, camera_id=3, exclude=True)

    def apply(**kwargs):
        kwargs['image'].exclude = kwargs['exclude']

    service = ImageExcludeService(
        lambda image_id, camera_id: image,
        apply_callback=apply,
    )

    result = service.set_exclude(image_id=111, camera_id=3, exclude=False)

    assert result.status == 'unexcluded'
    assert result.allowed is True
    assert image.exclude is False


def test_image_exclude_service_apply_error_is_structured():
    image = FakeImage(112, camera_id=3, exclude=False)

    def apply(**kwargs):
        raise RuntimeError('commit failed token=secret')

    service = ImageExcludeService(
        lambda image_id, camera_id: image,
        apply_callback=apply,
    )

    result = service.set_exclude(image_id=112, camera_id=3, exclude=True)

    assert result.status == 'update_failed'
    assert result.allowed is False
    assert result.details['error_type'] == 'RuntimeError'
    assert 'secret' not in str(result.to_dict())


def test_image_exclude_service_audit_redacts_payload():
    image = FakeImage(113, camera_id=3, exclude=False)
    audit_log = FakeAuditLog()

    def apply(**kwargs):
        kwargs['image'].exclude = kwargs['exclude']

    service = ImageExcludeService(
        lambda image_id, camera_id: image,
        apply_callback=apply,
    )

    result, audit_record, audit_write = service.set_exclude_with_audit(
        image_id=113,
        camera_id=3,
        exclude=True,
        payload={'image_id': 113, 'api_key': 'secret'},
        audit_log=audit_log,
    )

    assert result.status == 'excluded'
    assert audit_write['written'] is True
    assert audit_record.status == 'excluded'
    assert 'secret' not in str(audit_record.to_dict())
    assert 'secret' not in str(audit_log.records)


def test_image_exclude_safe_action_dry_run_uses_no_apply_callback():
    image = FakeImage(114, camera_id=3, exclude=False)
    calls = []
    action = ImageExcludeSafeAction(
        permission_check=lambda actor: True,
        image_lookup=lambda image_id, camera_id: image,
        apply_callback=lambda **kwargs: calls.append(kwargs),
    )

    result = action.run(
        actor=Actor(),
        payload={'image_id': 114, 'camera_id': 3},
        dry_run=True,
    )

    assert result.status == 'dry_run'
    assert result.allowed is True
    assert image.exclude is False
    assert calls == []


def test_image_exclude_safe_action_execute_with_fake_callback():
    image = FakeImage(115, camera_id=3, exclude=False)

    def apply(**kwargs):
        kwargs['image'].exclude = kwargs['exclude']

    action = ImageExcludeSafeAction(
        permission_check=lambda actor: True,
        image_lookup=lambda image_id, camera_id: image,
        apply_callback=apply,
    )

    result = action.run(
        actor=Actor(),
        payload={'image_id': 115, 'camera_id': 3},
        dry_run=False,
    )

    assert result.status == 'excluded'
    assert result.allowed is True
    assert image.exclude is True


def test_image_unexclude_safe_action_execute_with_fake_callback():
    image = FakeImage(116, camera_id=3, exclude=True)

    def apply(**kwargs):
        kwargs['image'].exclude = kwargs['exclude']

    action = ImageUnexcludeSafeAction(
        permission_check=lambda actor: True,
        image_lookup=lambda image_id, camera_id: image,
        apply_callback=apply,
    )

    result = action.run(
        actor=Actor(),
        payload={'image_id': 116, 'camera_id': 3},
        dry_run=False,
    )

    assert result.status == 'unexcluded'
    assert result.allowed is True
    assert image.exclude is False


def test_log_download_policy_valid_log_name():
    policy = LogDownloadPolicy()

    log_info, error = policy.resolve('capture')

    assert error is None
    assert log_info['log_name'] == 'capture'
    assert log_info['basename'] == 'indi-allsky.log'


def test_log_download_policy_rejects_unknown_log_name():
    policy = LogDownloadPolicy()

    log_info, error = policy.resolve('unknown')

    assert log_info is None
    assert error == 'not_allowlisted'


def test_log_download_policy_rejects_path_traversal_log_name():
    policy = LogDownloadPolicy()

    log_info, error = policy.resolve('../syslog')

    assert log_info is None
    assert error == 'invalid_log_name'


def test_log_download_policy_rejects_relative_allowlist_path():
    policy = LogDownloadPolicy(allowed_logs={
        'bad': {
            'label': 'Bad Log',
            'path': '../bad.log',
            'download_name': 'bad.log.gz',
        },
    })

    log_info, error = policy.resolve('bad')

    assert log_info is None
    assert error == 'unsafe_path'


def test_log_download_policy_rejects_absolute_path_not_in_allowlist():
    policy = LogDownloadPolicy()

    assert policy.path_is_unsafe(Path('/etc/passwd')) is True


def test_log_download_service_valid_dry_run_uses_fake_stat_provider():
    calls = []

    def stat_provider(log_info):
        calls.append(log_info['log_name'])
        return {'size_bytes': 1234}

    service = LogDownloadService(stat_provider=stat_provider)

    result = service.inspect('capture', dry_run=True)

    assert result.status == 'dry_run'
    assert result.allowed is True
    assert result.details['size_bytes'] == 1234
    assert result.details['basename'] == 'indi-allsky.log'
    assert result.details['redaction_required'] is True
    assert calls == ['capture']


def test_log_download_service_rejects_too_large_file_metadata():
    service = LogDownloadService(
        policy=LogDownloadPolicy(max_bytes=100),
        stat_provider=lambda log_info: {'size_bytes': 101},
    )

    result = service.inspect('capture', dry_run=True)

    assert result.status == 'too_large'
    assert result.allowed is False
    assert result.details['too_large'] is True


def test_log_download_service_metadata_error_is_structured_and_redacted():
    def stat_provider(log_info):
        raise RuntimeError('stat failed token=secret')

    service = LogDownloadService(stat_provider=stat_provider)

    result = service.inspect('capture', dry_run=True)

    assert result.status == 'metadata_error'
    assert result.allowed is False
    assert result.details['error_type'] == 'RuntimeError'
    assert 'secret' not in str(result.to_dict())


def test_log_download_service_non_dry_run_is_not_implemented():
    service = LogDownloadService(stat_provider=lambda log_info: {'size_bytes': 1})

    result = service.inspect('capture', dry_run=False)

    assert result.status == 'not_implemented'
    assert result.allowed is False
    assert result.dry_run is False


def test_log_download_redacts_secret_values():
    policy = LogDownloadPolicy()

    redacted = policy.redact_text('api_key=abc password:super refresh_token=zzz ordinary=value')

    assert 'abc' not in redacted
    assert 'super' not in redacted
    assert 'zzz' not in redacted
    assert '[REDACTED]' in redacted


def test_log_download_service_audit_records_success_and_failure():
    audit_log = FakeAuditLog()
    service = LogDownloadService(stat_provider=lambda log_info: {'size_bytes': 10})

    result, audit_record, audit_write = service.inspect_with_audit(
        'capture',
        payload={'log_name': 'capture', 'token': 'secret'},
        audit_log=audit_log,
    )

    assert result.status == 'dry_run'
    assert audit_record.status == 'dry_run'
    assert audit_write['written'] is True
    assert 'secret' not in str(audit_record.to_dict())
    assert 'secret' not in str(audit_log.records)

    result, audit_record, audit_write = service.inspect_with_audit(
        'unknown',
        audit_log=audit_log,
    )

    assert result.status == 'not_allowlisted'
    assert audit_record.status == 'not_allowlisted'
    assert audit_write['written'] is True


def test_log_download_safe_action_dry_run_does_not_stream_file():
    calls = []

    def stat_provider(log_info):
        calls.append(log_info['log_name'])
        return {'size_bytes': 11}

    action = LogDownloadSafeAction(
        permission_check=lambda actor: True,
        log_service=LogDownloadService(stat_provider=stat_provider),
    )

    result = action.run(
        actor=Actor(),
        payload={'log_name': 'capture'},
        dry_run=True,
    )

    assert result.status == 'dry_run'
    assert result.allowed is True
    assert calls == ['capture']


def test_log_download_safe_action_execute_is_not_implemented():
    action = LogDownloadSafeAction(
        permission_check=lambda actor: True,
        log_service=LogDownloadService(stat_provider=lambda log_info: {'size_bytes': 11}),
    )

    result = action.run(
        actor=Actor(),
        payload={'log_name': 'capture'},
        dry_run=False,
    )

    assert result.status == 'not_implemented'
    assert result.allowed is False


def test_log_download_has_no_flask_request_dependency():
    service = LogDownloadService(stat_provider=lambda log_info: {'size_bytes': 1})

    result = service.inspect('capture')

    assert result.status == 'dry_run'
    assert result.allowed is True


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


def test_capture_service_command_boundary_normalizes_command_intent():
    boundary = ModernAdminCaptureServiceCommandBoundary(effect_adapter=lambda command: {'returncode': 0, 'output': ''})

    assert boundary.normalize_command({'command': ' Restart '}) == 'restart'
    assert boundary.normalize_command({'command': 'STOP'}) == 'stop'
    assert boundary.normalize_command({'command': None}) == ''
    assert boundary.normalize_command({'command': True}) == ''


def test_capture_service_command_boundary_rejects_invalid_without_adapter_call():
    calls = []
    boundary = ModernAdminCaptureServiceCommandBoundary(effect_adapter=lambda command: calls.append(command))

    result = boundary.run(payload={'command': 'rm -rf'})

    assert result.status == 'validation_failed'
    assert result.allowed is False
    assert result.details['command'] == 'rm -rf'
    assert calls == []


def test_capture_service_command_boundary_delegates_valid_command_only():
    calls = []

    def fake_effect(command):
        calls.append(command)
        return {
            'returncode': 0,
            'output': '',
        }

    boundary = ModernAdminCaptureServiceCommandBoundary(effect_adapter=fake_effect)
    result = boundary.run(payload={'command': ' restart '})

    assert result.status == 'executed'
    assert result.allowed is True
    assert result.details['command'] == 'restart'
    assert result.details['past_tense'] == 'restarted'
    assert result.details['service_result'] == {'returncode': 0, 'output': ''}
    assert calls == ['restart']


def test_capture_service_command_boundary_requires_effect_adapter():
    boundary = ModernAdminCaptureServiceCommandBoundary()
    result = boundary.run(payload={'command': 'start'})

    assert result.status == 'not_implemented'
    assert result.allowed is False
    assert result.details['command'] == 'start'


def test_service_control_effect_adapter_preserves_systemctl_command_shape():
    calls = []

    class FakeResult:
        returncode = 0
        stdout = ' done \n'

    def fake_run(*args, **kwargs):
        calls.append((args, kwargs))
        return FakeResult()

    adapter = ModernAdminServiceControlEffectAdapter(
        service_name='indi-allsky.service',
        subprocess_run=fake_run,
        timeout=20,
    )

    result = adapter.execute('restart')

    assert result == {
        'returncode': 0,
        'output': 'done',
    }
    assert calls == [(
        (['systemctl', '--user', 'restart', 'indi-allsky.service'],),
        {
            'stdout': subprocess.PIPE,
            'stderr': subprocess.STDOUT,
            'text': True,
            'timeout': 20,
            'check': False,
        },
    )]


def test_service_control_effect_adapter_maps_timeout_to_timeout_error():
    def fake_run(*args, **kwargs):
        raise subprocess.TimeoutExpired(cmd=args[0], timeout=kwargs['timeout'])

    adapter = ModernAdminServiceControlEffectAdapter(
        service_name='indi-allsky.service',
        subprocess_run=fake_run,
    )

    try:
        adapter.execute('restart')
    except TimeoutError:
        pass
    else:
        raise AssertionError('Expected TimeoutError')


def test_abort_exposure_action_planner_creates_profile_plan():
    planner = ModernAdminAbortExposureActionPlanner(
        profile_configs=[
            {
                'profile_id': 'asi678mc',
                'enabled': True,
                'camera_id': 2,
                'camera_interface': 'indi',
                'label': 'ASI678MC',
            },
            {
                'profile_id': 'disabled',
                'enabled': False,
                'camera_id': 3,
                'camera_interface': 'indi',
            },
        ],
    )

    result = planner.plan(payload={'profile_id': 'asi678mc', 'camera_id': '2'})

    assert result.status == 'planned'
    assert result.allowed is True
    assert result.details['profile_id'] == 'asi678mc'
    assert result.details['camera_id'] == 2
    assert result.details['camera_interface'] == 'indi'
    assert result.details['priority'] == 10
    assert result.details['jobdata'] == {
        'action': 'abortExposure',
        'profile_id': 'asi678mc',
        'camera_id': 2,
    }


def test_abort_exposure_action_planner_rejects_invalid_profile():
    planner = ModernAdminAbortExposureActionPlanner(
        profile_configs=[
            {
                'profile_id': 'imx708-wide',
                'enabled': True,
                'camera_id': 1,
                'camera_interface': 'libcamera',
            },
        ],
    )

    result = planner.plan(payload={'profile_id': 'missing'})

    assert result.status == 'validation_failed'
    assert result.allowed is False
    assert result.message == 'Unsupported capture profile.'
    assert result.details == {'profile_id': 'missing'}


def test_abort_exposure_action_planner_rejects_unsupported_camera_interface():
    planner = ModernAdminAbortExposureActionPlanner(
        profile_configs=[
            {
                'profile_id': 'network-camera',
                'enabled': True,
                'camera_id': 4,
                'camera_interface': 'pycurl',
            },
        ],
    )

    result = planner.plan(payload={'profile_id': 'network-camera'})

    assert result.status == 'validation_failed'
    assert result.allowed is False
    assert result.message == 'Unsupported capture profile.'


def test_abort_exposure_action_planner_accepts_libcamera_backend_family():
    planner = ModernAdminAbortExposureActionPlanner(
        profile_configs=[
            {
                'profile_id': 'imx708-wide',
                'enabled': True,
                'camera_id': 1,
                'camera_interface': 'libcamera_imx708',
            },
        ],
    )

    result = planner.plan(payload={'profile_id': 'imx708-wide'})

    assert result.status == 'planned'
    assert result.allowed is True
    assert result.details['profile_id'] == 'imx708-wide'
    assert result.details['camera_id'] == 1
    assert result.details['camera_interface'] == 'libcamera_imx708'


def test_abort_exposure_action_planner_rejects_camera_profile_mismatch():
    planner = ModernAdminAbortExposureActionPlanner(
        profile_configs=[
            {
                'profile_id': 'asi678mc',
                'enabled': True,
                'camera_id': 2,
                'camera_interface': 'indi',
            },
        ],
    )

    result = planner.plan(payload={'profile_id': 'asi678mc', 'camera_id': 9})

    assert result.status == 'validation_failed'
    assert result.allowed is False
    assert result.message == 'camera_id does not match capture profile.'


def test_abort_exposure_action_planner_supports_single_camera_fallback():
    planner = ModernAdminAbortExposureActionPlanner(current_camera_id=8)

    result = planner.plan(payload={})

    assert result.status == 'planned'
    assert result.allowed is True
    assert result.details['profile_id'] == ''
    assert result.details['camera_id'] == 8
    assert result.details['jobdata'] == {
        'action': 'abortExposure',
        'profile_id': '',
        'camera_id': 8,
    }


def test_system_power_command_boundary_normalizes_reboot_intent():
    boundary = ModernAdminSystemPowerCommandBoundary(effect_adapter=lambda command: 'ok')

    assert boundary.normalize_command({'COMMAND_HIDDEN': ' Reboot '}) == 'reboot'
    assert boundary.normalize_command({'command': 'REBOOT'}) == 'reboot'
    assert boundary.normalize_command({'command': None}) == ''
    assert boundary.normalize_command({'command': False}) == ''


def test_system_power_command_boundary_rejects_unsupported_command_without_adapter_call():
    calls = []
    boundary = ModernAdminSystemPowerCommandBoundary(effect_adapter=lambda command: calls.append(command))

    result = boundary.run(payload={'COMMAND_HIDDEN': 'poweroff'})

    assert result.status == 'validation_failed'
    assert result.allowed is False
    assert result.details['command'] == 'poweroff'
    assert calls == []


def test_system_power_command_boundary_delegates_reboot_only():
    calls = []

    def fake_effect(command):
        calls.append(command)
        return 'reboot-submitted'

    boundary = ModernAdminSystemPowerCommandBoundary(effect_adapter=fake_effect)
    result = boundary.run(payload={'COMMAND_HIDDEN': ' reboot '})

    assert result.status == 'executed'
    assert result.allowed is True
    assert result.details['command'] == 'reboot'
    assert result.details['past_tense'] == 'restarted'
    assert result.details['service_result'] == 'reboot-submitted'
    assert calls == ['reboot']


def test_system_power_command_boundary_requires_effect_adapter():
    boundary = ModernAdminSystemPowerCommandBoundary()
    result = boundary.run(payload={'COMMAND_HIDDEN': 'reboot'})

    assert result.status == 'not_implemented'
    assert result.allowed is False
    assert result.details['command'] == 'reboot'


def test_system_power_effect_adapter_delegates_reboot_only():
    calls = []

    def fake_reboot():
        calls.append('reboot')
        return 'dbus-reboot-result'

    adapter = ModernAdminSystemPowerEffectAdapter(reboot_effect=fake_reboot)

    assert adapter.execute('reboot') == 'dbus-reboot-result'
    assert calls == ['reboot']


def test_system_power_effect_adapter_rejects_unsupported_command():
    adapter = ModernAdminSystemPowerEffectAdapter(reboot_effect=lambda: 'unexpected')

    try:
        adapter.execute('poweroff')
    except ValueError as e:
        assert str(e) == 'Unhandled system power command'
    else:
        raise AssertionError('Expected ValueError')


def test_generated_output_action_planner_creates_generate_video_plan():
    planner = ModernAdminGeneratedOutputActionPlanner()

    result = planner.plan(
        action=' generate_video ',
        camera_id='7',
        day_date='2026-07-02',
        night='night',
    )

    assert result.status == 'planned'
    assert result.allowed is True
    assert result.dry_run is True
    assert result.details['action'] == 'generate_video'
    assert result.details['camera_id'] == 7
    assert result.details['timespec'] == '20260702'
    assert result.details['night'] is True
    assert result.details['priority'] == 100
    assert result.details['jobdata'] == {
        'action': 'generateVideo',
        'kwargs': {
            'timespec': '20260702',
            'night': True,
            'camera_id': 7,
        },
    }


def test_generated_output_action_planner_creates_generate_k_st_plan():
    planner = ModernAdminGeneratedOutputActionPlanner()

    result = planner.plan(
        action='generate_k_st',
        camera_id=9,
        day_date='2026-07-02',
        night='day',
    )

    assert result.status == 'planned'
    assert result.allowed is True
    assert result.details['action'] == 'generate_k_st'
    assert result.details['camera_id'] == 9
    assert result.details['timespec'] == '20260702'
    assert result.details['night'] is False
    assert result.details['priority'] == 100
    assert result.details['jobdata'] == {
        'action': 'generateKeogramStarTrails',
        'kwargs': {
            'timespec': '20260702',
            'night': False,
            'camera_id': 9,
        },
    }


def test_generated_output_action_planner_creates_generate_panorama_plan_when_enabled():
    planner = ModernAdminGeneratedOutputActionPlanner()

    result = planner.plan(
        action='generate_panorama_video',
        camera_id=11,
        day_date='2026-07-02',
        night=True,
        config={'FISH2PANO': {'ENABLE': True}},
    )

    assert result.status == 'planned'
    assert result.allowed is True
    assert result.details['action'] == 'generate_panorama_video'
    assert result.details['camera_id'] == 11
    assert result.details['timespec'] == '20260702'
    assert result.details['night'] is True
    assert result.details['priority'] == 100
    assert result.details['jobdata'] == {
        'action': 'generatePanoramaVideo',
        'kwargs': {
            'timespec': '20260702',
            'night': True,
            'camera_id': 11,
        },
    }


def test_generated_output_action_planner_rejects_generate_panorama_when_disabled():
    planner = ModernAdminGeneratedOutputActionPlanner()

    result = planner.plan(
        action='generate_panorama_video',
        camera_id=11,
        day_date='2026-07-02',
        night=False,
        config={'FISH2PANO': {'ENABLE': False}},
    )

    assert result.status == 'unavailable'
    assert result.allowed is False
    assert result.message == 'Panoramas disabled'
    assert result.details == {
        'action': 'generate_panorama_video',
        'camera_id': 11,
        'day_date': '2026-07-02',
        'night': False,
    }


def test_generated_output_action_planner_rejects_unsupported_action():
    planner = ModernAdminGeneratedOutputActionPlanner()

    result = planner.plan(
        action='delete_video',
        camera_id=7,
        day_date='2026-07-02',
        night=False,
    )

    assert result.status == 'validation_failed'
    assert result.allowed is False
    assert result.details['action'] == 'delete_video'


def test_generated_output_action_planner_rejects_invalid_target():
    planner = ModernAdminGeneratedOutputActionPlanner()

    result = planner.plan(
        action='generate_video',
        camera_id='not-a-camera',
        day_date='2026-07-02',
        night=False,
    )

    assert result.status == 'validation_failed'
    assert result.allowed is False
    assert result.message == 'camera_id is required.'


def test_generated_output_action_planner_has_no_effect_adapter():
    planner = ModernAdminGeneratedOutputActionPlanner()

    assert not hasattr(planner, 'effect_adapter')


def test_task_enqueue_effect_adapter_materializes_plan_without_changing_payload():
    class FakeTask:
        next_id = 40

        def __init__(self, queue=None, state=None, priority=None, data=None):
            FakeTask.next_id += 1
            self.id = FakeTask.next_id
            self.queue = queue
            self.state = state
            self.priority = priority
            self.data = data

    class FakeSession:
        def __init__(self):
            self.added = []
            self.commits = 0

        def add(self, task):
            self.added.append(task)

        def commit(self):
            self.commits += 1

    session = FakeSession()
    jobdata = {
        'action': 'generateVideo',
        'kwargs': {
            'timespec': '20260702',
            'night': True,
            'camera_id': 7,
        },
    }
    adapter = ModernAdminTaskEnqueueEffectAdapter(
        task_model=FakeTask,
        db_session=session,
        queue_enum={'VIDEO': 'video-enum'},
        state_enum={'MANUAL': 'manual-enum'},
    )

    result = adapter.enqueue_from_plan({
        'queue': 'VIDEO',
        'state': 'MANUAL',
        'priority': 100,
        'jobdata': jobdata,
    })

    assert session.commits == 1
    assert session.added == [result.task]
    assert result.task_id == 41
    assert result.queue == 'video-enum'
    assert result.state == 'manual-enum'
    assert result.priority == 100
    assert result.jobdata is jobdata
    assert result.task.data is jobdata


def test_maintenance_action_planner_creates_backup_db_plan():
    planner = ModernAdminMaintenanceActionPlanner()

    result = planner.plan(action=' backup_db ')

    assert result.status == 'planned'
    assert result.allowed is True
    assert result.dry_run is True
    assert result.details == {
        'action': 'backup_db',
        'jobdata': {
            'action': 'backupDatabase',
            'kwargs': {},
        },
        'queue': 'VIDEO',
        'state': 'MANUAL',
        'priority': 100,
        'success_message': 'Submitted backup task',
    }


def test_maintenance_action_planner_rejects_unsupported_action():
    planner = ModernAdminMaintenanceActionPlanner()

    result = planner.plan(action='flush_images')

    assert result.status == 'validation_failed'
    assert result.allowed is False
    assert result.details == {
        'action': 'flush_images',
    }


def test_maintenance_action_planner_has_no_effect_adapter():
    planner = ModernAdminMaintenanceActionPlanner()

    assert not hasattr(planner, 'effect_adapter')


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


def get_capture_service_action_view_source():
    source = (Path(__file__).resolve().parents[1] / 'indi_allsky' / 'flask' / 'views.py').read_text()
    class_start = source.index('class ModernAdminCaptureServiceActionView')
    class_end = source.index('class SystemInfoView')
    return source[class_start:class_end], source


def get_ajax_timelapse_generator_view_source():
    source = (Path(__file__).resolve().parents[1] / 'indi_allsky' / 'flask' / 'views.py').read_text()
    class_start = source.index('class AjaxTimelapseGeneratorView')
    class_end = source.index('class MiniTimelapseGeneratorView')
    return source[class_start:class_end], source


def get_ajax_system_view_source():
    source = (Path(__file__).resolve().parents[1] / 'indi_allsky' / 'flask' / 'views.py').read_text()
    class_start = source.index('class AjaxSystemInfoView')
    class_end = source.index('class ConfigDownloadView')
    return source[class_start:class_end], source


def get_base_template_source():
    return (Path(__file__).resolve().parents[1] / 'indi_allsky' / 'flask' / 'templates' / 'base.html').read_text()


def get_hybrid_product_css_source():
    return (Path(__file__).resolve().parents[1] / 'indi_allsky' / 'flask' / 'static' / 'modern_admin' / 'hybrid-product-ui.css').read_text()


def get_hybrid_product_template_sources():
    template_root = Path(__file__).resolve().parents[1] / 'indi_allsky' / 'flask' / 'templates'
    sources = []
    for path in sorted(template_root.rglob('*.html')):
        source = path.read_text()
        if 'hybrid-product-ui.css' in source:
            sources.append(source)
    return '\n'.join(sources)


def get_allsky_source():
    return (Path(__file__).resolve().parents[1] / 'indi_allsky' / 'allsky.py').read_text()


def get_capture_worker_source():
    return (Path(__file__).resolve().parents[1] / 'indi_allsky' / 'capture.py').read_text()


def get_flask_init_source():
    return (Path(__file__).resolve().parents[1] / 'indi_allsky' / 'flask' / '__init__.py').read_text()


def test_safe_action_dry_run_route_exists_and_is_post_only_static():
    view_source, full_source = get_safe_action_dry_run_view_source()

    assert "methods = ['POST']" in view_source
    assert "bp_allsky.add_url_rule('/modern-admin/safe-action/dry-run'" in full_source
    assert "methods=['POST']" in full_source


def test_safe_action_dry_run_route_requires_login_static():
    view_source, _full_source = get_safe_action_dry_run_view_source()

    assert 'decorators = [login_required]' in view_source


def test_safe_action_dry_run_route_is_not_csrf_exempt_static():
    init_source = get_flask_init_source()

    assert 'csrf.init_app(app)' in init_source
    assert 'csrf.exempt(bp_syncapi_allsky)' in init_source
    assert 'csrf.exempt(bp_actionapi_allsky)' in init_source
    assert 'csrf.exempt(bp_allsky)' not in init_source


def test_safe_action_dry_run_view_permission_policy_static():
    view_source, _full_source = get_safe_action_dry_run_view_source()

    assert 'def has_safe_action_permission' in view_source
    assert "app.config.get('LOGIN_DISABLED')" in view_source
    assert "getattr(actor, 'is_admin', False)" in view_source


def test_safe_action_dry_run_view_status_mapping_static():
    view_source, _full_source = get_safe_action_dry_run_view_source()

    assert "result.status == 'permission_denied'" in view_source
    assert 'return 403' in view_source
    assert "'missing_action_id'" in view_source
    assert "'not_found'" in view_source
    assert "'validation_failed'" in view_source
    assert 'return 400' in view_source


def test_safe_action_dry_run_view_has_no_legacy_ack_path_static():
    view_source, _full_source = get_safe_action_dry_run_view_source()

    assert '/ajax/notification' not in view_source
    assert 'setAck(' not in view_source
    assert 'db.session' not in view_source
    assert 'commit(' not in view_source


def test_capture_service_action_view_uses_hybrid_boundary_static():
    view_source, _full_source = get_capture_service_action_view_source()

    assert 'ModernAdminCaptureServiceCommandBoundary' in view_source
    assert 'ModernAdminServiceControlEffectAdapter' in view_source
    assert 'get_capture_service_command_boundary' in view_source
    assert 'effect_adapter=self.run_capture_service_command' in view_source
    assert ".execute(command)" in view_source
    assert 'command not in self.valid_commands' not in view_source


def test_abort_exposure_action_view_uses_hybrid_planner_static():
    view_source, full_source = get_capture_service_action_view_source()
    class_start = view_source.index('class ModernAdminAbortExposureActionView')
    class_source = view_source[class_start:]

    assert 'ModernAdminAbortExposureActionPlanner' in class_source
    assert 'ModernAdminTaskEnqueueEffectAdapter' in class_source
    assert '.enqueue_from_plan(plan.details)' in class_source
    assert "'task-id'        : enqueue_result.task_id" in class_source
    assert 'abortCcdExposure(' not in class_source
    assert "bp_allsky.add_url_rule('/modern-admin/capture/abort-exposure'" in full_source


def test_ajax_generate_video_uses_hybrid_planner_static():
    view_source, _full_source = get_ajax_timelapse_generator_view_source()
    branch_start = view_source.index("elif action == 'generate_video':")
    branch_end = view_source.index("elif action == 'generate_panorama_video':")
    branch = view_source[branch_start:branch_end]

    assert 'ModernAdminGeneratedOutputActionPlanner().plan' in branch
    assert 'ModernAdminTaskEnqueueEffectAdapter' in branch
    assert '.enqueue_from_plan(plan.details)' in branch


def test_ajax_generate_k_st_uses_hybrid_planner_static():
    view_source, _full_source = get_ajax_timelapse_generator_view_source()
    branch_start = view_source.index("elif action == 'generate_k_st':")
    branch_end = view_source.index("elif action == 'upload_endofnight':")
    branch = view_source[branch_start:branch_end]

    assert 'ModernAdminGeneratedOutputActionPlanner().plan' in branch
    assert 'ModernAdminTaskEnqueueEffectAdapter' in branch
    assert '.enqueue_from_plan(plan.details)' in branch


def test_ajax_generate_panorama_video_uses_hybrid_planner_static():
    view_source, _full_source = get_ajax_timelapse_generator_view_source()
    branch_start = view_source.index("elif action == 'generate_panorama_video':")
    branch_end = view_source.index("elif action == 'generate_k_st':")
    branch = view_source[branch_start:branch_end]

    assert 'ModernAdminGeneratedOutputActionPlanner().plan' in branch
    assert 'config=self.indi_allsky_config' in branch
    assert "if plan.status == 'unavailable':" in branch
    assert "'success-message' : plan.message" in branch
    assert 'ModernAdminTaskEnqueueEffectAdapter' in branch
    assert '.enqueue_from_plan(plan.details)' in branch


def test_ajax_system_backup_db_uses_hybrid_maintenance_planner_static():
    view_source, _full_source = get_ajax_system_view_source()
    branch_start = view_source.index("elif command == 'backup_db':")
    branch_end = view_source.index("elif command == 'expire_data':")
    branch = view_source[branch_start:branch_end]

    assert 'ModernAdminMaintenanceActionPlanner().plan' in branch
    assert 'ModernAdminTaskEnqueueEffectAdapter' in branch
    assert '.enqueue_from_plan(plan.details)' in branch
    assert "message_list = [plan.details['success_message']]" in branch


def test_ajax_system_reboot_uses_hybrid_power_boundary_static():
    view_source, _full_source = get_ajax_system_view_source()
    branch_start = view_source.index("if command == 'reboot':")
    branch_end = view_source.index("elif command == 'poweroff':")
    branch = view_source[branch_start:branch_end]

    assert 'ModernAdminSystemPowerCommandBoundary' in branch
    assert 'effect_adapter=self.run_system_power_command' in branch
    assert 'ModernAdminSystemPowerEffectAdapter' in view_source
    assert "r = action_result.details['service_result']" in branch


def test_hybrid_shell_exposes_recovery_controls_static():
    source = get_base_template_source()

    assert 'data-hybrid-capture-command="start"' in source
    assert 'data-hybrid-capture-command="stop"' in source
    assert 'data-hybrid-capture-command="restart"' in source
    assert 'data-hybrid-abort-exposure' in source
    assert 'data-hybrid-abort-profile="{{ target.profile_id }}"' in source
    assert 'fetch(abortExposureActionUrl' in source
    assert 'data-hybrid-system-command="reboot"' in source
    assert 'data-hybrid-system-command="poweroff"' not in source
    assert 'fetch(captureActionUrl' in source
    assert 'fetch(quickActionUrl' in source


def test_hybrid_runtime_buttons_reset_native_browser_appearance_static():
    source = get_hybrid_product_css_source()
    button_block_start = source.index('.hybrid-runtime-button {')
    button_block_end = source.index('.hybrid-runtime-button:hover', button_block_start)
    button_block = source[button_block_start:button_block_end]
    shared_block_start = source.index('.hybrid-runtime-status,')
    shared_block_end = source.index('.hybrid-runtime-status {', shared_block_start)
    shared_block = source[shared_block_start:shared_block_end]

    assert 'appearance: none;' in button_block
    assert '-webkit-appearance: none;' in button_block
    assert 'font: inherit;' in shared_block
    assert 'border-radius: 999px;' in shared_block
    assert 'box-sizing: border-box;' in shared_block
    assert '.hybrid-runtime-button:disabled' in source
    assert '.hybrid-app-topbar .hybrid-runtime-actions .hybrid-runtime-button:disabled' in source
    assert 'opacity: 1;' in source


def test_hybrid_product_css_cache_key_is_bumped_static():
    source = get_hybrid_product_template_sources()

    assert 'hybrid-product-ui-shell-004' in source
    assert 'hybrid-product-ui-shell-001' not in source


def test_abort_exposure_main_task_routes_to_capture_worker_queue_static():
    source = get_allsky_source()
    branch_start = source.index("elif action == 'abortExposure':")
    branch_end = source.index("elif action == 'setlocation':", branch_start)
    branch = source[branch_start:branch_end]

    assert "task.data.get('profile_id')" in branch
    assert 'self.capture_worker_map.get(str(profile_id))' in branch
    assert "'abort_exposure': True" in branch
    assert "task.setFailed('Missing profile_id')" in branch
    assert "task.setFailed('Unknown profile_id')" in branch
    assert "task.setSuccess('Abort exposure queued" in branch


def test_capture_worker_abort_exposure_queue_command_uses_camera_adapter_static():
    source = get_capture_worker_source()
    branch_start = source.index("elif c_dict.get('abort_exposure'):")
    branch_end = source.index('else:', branch_start)
    branch = source[branch_start:branch_end]

    assert 'self.indiclient.abortCcdExposure()' in branch
    assert 'waiting_for_frame = False' in branch
    assert 'waiting_for_sqm_frame = False' in branch


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


def test_safe_action_dry_run_helper_missing_action_id_response_shape():
    result = run_modern_safe_action_dry_run(
        action_id=None,
        actor=AdminActor(),
        payload={'notification_id': 1},
        permission_check=lambda actor: bool(getattr(actor, 'is_admin', False)),
    )
    data = result.to_dict()

    assert data['status'] == 'missing_action_id'
    assert data['allowed'] is False
    assert data['dry_run'] is True


def test_safe_action_dry_run_helper_unknown_action_response_shape():
    result = run_modern_safe_action_dry_run(
        action_id='unknown.action',
        actor=AdminActor(),
        payload={'notification_id': 1},
        permission_check=lambda actor: bool(getattr(actor, 'is_admin', False)),
    )
    data = result.to_dict()

    assert data['status'] == 'not_found'
    assert data['allowed'] is False
    assert data['dry_run'] is True


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
    test_safe_action_contract_shape_is_stable()
    test_safe_action_contract_uses_class_metadata()
    test_placeholder_contract_uses_instance_metadata()
    test_notification_acknowledge_contract_uses_domain_metadata()
    test_safe_action_contract_does_not_change_result_shape()
    test_audit_message_redacts_secret_payload()
    test_registry_empty()
    test_registry_register_and_lookup()
    test_registry_output_shape_remains_backward_compatible()
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
    test_notification_acknowledge_db_adapter_lookup_success()
    test_notification_acknowledge_db_adapter_not_found()
    test_notification_acknowledge_db_adapter_query_exception_is_sanitized()
    test_notification_acknowledge_db_adapter_lookup_does_not_ack()
    test_notification_acknowledge_service_with_db_adapter_already_acked()
    test_notification_acknowledge_service_with_db_adapter_not_acked()
    test_notification_acknowledge_service_with_db_adapter_set_ack_error()
    test_notification_acknowledge_service_with_db_adapter_repository_error_redacted()
    test_image_exclude_db_adapter_lookup_success()
    test_image_exclude_db_adapter_not_found()
    test_image_exclude_db_adapter_query_exception_is_sanitized()
    test_image_exclude_db_adapter_lookup_does_not_mutate()
    test_image_exclude_service_invalid_ids()
    test_image_exclude_service_invalid_exclude_value()
    test_image_exclude_service_missing_image()
    test_image_exclude_service_repository_error_redacted()
    test_image_exclude_service_already_set_is_noop()
    test_image_exclude_service_dry_run_does_not_apply()
    test_image_exclude_service_without_apply_callback_is_not_implemented()
    test_image_exclude_service_with_fake_apply_excludes_image()
    test_image_exclude_service_with_fake_apply_unexcludes_image()
    test_image_exclude_service_apply_error_is_structured()
    test_image_exclude_service_audit_redacts_payload()
    test_image_exclude_safe_action_dry_run_uses_no_apply_callback()
    test_image_exclude_safe_action_execute_with_fake_callback()
    test_image_unexclude_safe_action_execute_with_fake_callback()
    test_log_download_policy_valid_log_name()
    test_log_download_policy_rejects_unknown_log_name()
    test_log_download_policy_rejects_path_traversal_log_name()
    test_log_download_policy_rejects_relative_allowlist_path()
    test_log_download_policy_rejects_absolute_path_not_in_allowlist()
    test_log_download_service_valid_dry_run_uses_fake_stat_provider()
    test_log_download_service_rejects_too_large_file_metadata()
    test_log_download_service_metadata_error_is_structured_and_redacted()
    test_log_download_service_non_dry_run_is_not_implemented()
    test_log_download_redacts_secret_values()
    test_log_download_service_audit_records_success_and_failure()
    test_log_download_safe_action_dry_run_does_not_stream_file()
    test_log_download_safe_action_execute_is_not_implemented()
    test_log_download_has_no_flask_request_dependency()
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
    test_capture_service_command_boundary_normalizes_command_intent()
    test_capture_service_command_boundary_rejects_invalid_without_adapter_call()
    test_capture_service_command_boundary_delegates_valid_command_only()
    test_capture_service_command_boundary_requires_effect_adapter()
    test_service_control_effect_adapter_preserves_systemctl_command_shape()
    test_service_control_effect_adapter_maps_timeout_to_timeout_error()
    test_system_power_effect_adapter_delegates_reboot_only()
    test_system_power_effect_adapter_rejects_unsupported_command()
    test_abort_exposure_action_planner_creates_profile_plan()
    test_abort_exposure_action_planner_rejects_invalid_profile()
    test_abort_exposure_action_planner_rejects_unsupported_camera_interface()
    test_abort_exposure_action_planner_accepts_libcamera_backend_family()
    test_abort_exposure_action_planner_rejects_camera_profile_mismatch()
    test_abort_exposure_action_planner_supports_single_camera_fallback()
    test_generated_output_action_planner_creates_generate_video_plan()
    test_generated_output_action_planner_creates_generate_k_st_plan()
    test_generated_output_action_planner_creates_generate_panorama_plan_when_enabled()
    test_generated_output_action_planner_rejects_generate_panorama_when_disabled()
    test_generated_output_action_planner_rejects_unsupported_action()
    test_generated_output_action_planner_rejects_invalid_target()
    test_generated_output_action_planner_has_no_effect_adapter()
    test_task_enqueue_effect_adapter_materializes_plan_without_changing_payload()
    test_maintenance_action_planner_creates_backup_db_plan()
    test_maintenance_action_planner_rejects_unsupported_action()
    test_maintenance_action_planner_has_no_effect_adapter()
    test_notification_acknowledge_dry_run_registry_has_no_execute_callback()
    test_dry_run_helper_missing_action_id()
    test_dry_run_helper_unknown_action_id()
    test_dry_run_helper_notification_acknowledge_success()
    test_dry_run_helper_permission_denied()
    test_dry_run_helper_redacts_secret_payload()
    test_safe_action_dry_run_route_exists_and_is_post_only_static()
    test_safe_action_dry_run_route_requires_login_static()
    test_safe_action_dry_run_route_is_not_csrf_exempt_static()
    test_safe_action_dry_run_view_permission_policy_static()
    test_safe_action_dry_run_view_status_mapping_static()
    test_safe_action_dry_run_view_has_no_legacy_ack_path_static()
    test_capture_service_action_view_uses_hybrid_boundary_static()
    test_abort_exposure_action_view_uses_hybrid_planner_static()
    test_ajax_generate_video_uses_hybrid_planner_static()
    test_ajax_generate_k_st_uses_hybrid_planner_static()
    test_ajax_generate_panorama_video_uses_hybrid_planner_static()
    test_ajax_system_backup_db_uses_hybrid_maintenance_planner_static()
    test_ajax_system_reboot_uses_hybrid_power_boundary_static()
    test_hybrid_shell_exposes_recovery_controls_static()
    test_hybrid_runtime_buttons_reset_native_browser_appearance_static()
    test_hybrid_product_css_cache_key_is_bumped_static()
    test_abort_exposure_main_task_routes_to_capture_worker_queue_static()
    test_capture_worker_abort_exposure_queue_command_uses_camera_adapter_static()
    test_safe_action_dry_run_helper_response_shape()
    test_safe_action_dry_run_helper_missing_action_id_response_shape()
    test_safe_action_dry_run_helper_unknown_action_response_shape()
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
