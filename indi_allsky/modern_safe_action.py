from dataclasses import dataclass
from dataclasses import field
from datetime import datetime
from typing import Any
from typing import Callable


SECRET_TOKENS = (
    'apikey',
    'api_key',
    'credential',
    'password',
    'private_key',
    'refresh_token',
    'secret',
    'token',
)


@dataclass(frozen=True)
class ModernAdminSafeActionResult:
    action_id: str
    feature: str
    risk_level: str
    status: str
    message: str
    dry_run: bool = True
    allowed: bool = False
    audit_message: str = ''
    details: dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.utcnow().replace(microsecond=0).isoformat() + 'Z')

    def to_dict(self):
        return {
            'action_id'     : self.action_id,
            'feature'       : self.feature,
            'risk_level'    : self.risk_level,
            'status'        : self.status,
            'message'       : self.message,
            'dry_run'       : self.dry_run,
            'allowed'       : self.allowed,
            'audit_message' : self.audit_message,
            'details'       : dict(self.details),
            'created_at'    : self.created_at,
        }


class ModernAdminSafeAction:
    """Contract-only base for future Modern Admin actions.

    This class intentionally implements no real mutation. Subclasses must
    override validate() and execute() before an action can do useful work.
    """

    action_id = 'modern_admin_safe_action.unimplemented'
    label = 'Unimplemented Modern Admin Safe Action'
    feature = 'unknown'
    risk_level = 'high'
    required_permission = 'admin'

    def __init__(self, permission_check: Callable[[Any], bool] | None = None):
        self.permission_check = permission_check


    def run(self, actor=None, payload=None, dry_run=True):
        payload = payload or {}

        if not self.has_permission(actor):
            return self.result(
                status='permission_denied',
                message='Permission denied',
                dry_run=dry_run,
                allowed=False,
                audit_message=self.audit_message(actor, payload, 'permission_denied'),
            )

        validation_result = self.validate(payload)
        if validation_result is not True:
            return self.result(
                status='validation_failed',
                message=str(validation_result or 'Validation failed'),
                dry_run=dry_run,
                allowed=False,
                audit_message=self.audit_message(actor, payload, 'validation_failed'),
            )

        if dry_run:
            return self.result(
                status='dry_run',
                message='Dry run only; no action executed',
                dry_run=True,
                allowed=True,
                audit_message=self.audit_message(actor, payload, 'dry_run'),
            )

        return self.execute(actor=actor, payload=payload)


    def has_permission(self, actor):
        if self.permission_check is None:
            return False

        return bool(self.permission_check(actor))


    def validate(self, payload):
        return True


    def execute(self, actor=None, payload=None):
        return self.result(
            status='not_implemented',
            message='Action execution is not implemented',
            dry_run=False,
            allowed=False,
            audit_message=self.audit_message(actor, payload or {}, 'not_implemented'),
        )


    def result(self, status, message, dry_run=True, allowed=False, audit_message='', details=None):
        return ModernAdminSafeActionResult(
            action_id=self.action_id,
            feature=self.feature,
            risk_level=self.risk_level,
            status=status,
            message=message,
            dry_run=dry_run,
            allowed=allowed,
            audit_message=self.sanitize_audit_message(audit_message),
            details=details or {},
        )


    def audit_message(self, actor, payload, outcome):
        actor_label = self.actor_label(actor)
        safe_payload = self.sanitize_payload(payload)
        return '{0:s} action={1:s} feature={2:s} actor={3:s} payload={4!r}'.format(
            outcome,
            self.action_id,
            self.feature,
            actor_label,
            safe_payload,
        )


    def actor_label(self, actor):
        if actor is None:
            return 'unknown'

        for attr in ('username', 'id'):
            value = getattr(actor, attr, None)
            if value is not None:
                return str(value)

        return str(actor)


    def sanitize_payload(self, value):
        if isinstance(value, dict):
            sanitized = {}
            for key, item in value.items():
                key_s = str(key)
                if self.is_secret_key(key_s):
                    sanitized[key_s] = '[REDACTED]'
                else:
                    sanitized[key_s] = self.sanitize_payload(item)
            return sanitized

        if isinstance(value, list):
            return [self.sanitize_payload(item) for item in value]

        return value


    def sanitize_audit_message(self, message):
        sanitized = str(message)
        for token in SECRET_TOKENS:
            sanitized = sanitized.replace(token, '[REDACTED]')
            sanitized = sanitized.replace(token.upper(), '[REDACTED]')
        return sanitized


    def is_secret_key(self, key):
        key_l = key.lower()
        return any(token in key_l for token in SECRET_TOKENS)


class ModernAdminSafeActionPlaceholder(ModernAdminSafeAction):
    def __init__(self, action_id, label, feature, risk_level, permission_check=None):
        super().__init__(permission_check=permission_check)
        self.action_id = action_id
        self.label = label
        self.feature = feature
        self.risk_level = risk_level


class NotificationAcknowledgeSafeAction(ModernAdminSafeAction):
    action_id = 'notification.acknowledge'
    label = 'Acknowledge Notification'
    feature = 'Notifications'
    risk_level = 'medium'

    def __init__(self, permission_check=None, notification_lookup=None, acknowledge_callback=None):
        super().__init__(permission_check=permission_check)
        self.notification_lookup = notification_lookup
        self.acknowledge_callback = acknowledge_callback


    def validate(self, payload):
        notification_id = self.notification_id_from_payload(payload)
        if notification_id is None:
            return 'notification_id is required'

        if notification_id < 1:
            return 'notification_id must be a positive integer'

        if self.notification_lookup is None:
            return True

        notification = self.notification_lookup(notification_id)
        if notification is None:
            return 'notification does not exist'

        return True


    def execute(self, actor=None, payload=None):
        payload = payload or {}
        notification_id = self.notification_id_from_payload(payload)
        notification = self.lookup_notification(notification_id)

        if notification is not None and bool(getattr(notification, 'ack', False)):
            return self.result(
                status='already_acknowledged',
                message='Notification is already acknowledged',
                dry_run=False,
                allowed=True,
                audit_message=self.audit_message(actor, payload, 'already_acknowledged'),
                details={
                    'notification_id': notification_id,
                    'idempotent': True,
                },
            )

        if self.acknowledge_callback is None:
            return super().execute(actor=actor, payload=payload)

        callback_result = self.acknowledge_callback(
            notification_id=notification_id,
            notification=notification,
            actor=actor,
            payload=payload,
        )

        if isinstance(callback_result, ModernAdminSafeActionResult):
            return callback_result

        callback_details = {}
        if isinstance(callback_result, dict):
            callback_details = dict(callback_result.get('details', callback_result))

        return self.result(
            status='acknowledged',
            message='Notification acknowledged',
            dry_run=False,
            allowed=True,
            audit_message=self.audit_message(actor, payload, 'acknowledged'),
            details={
                'notification_id': notification_id,
                **callback_details,
            },
        )


    def lookup_notification(self, notification_id):
        if self.notification_lookup is None:
            return None

        return self.notification_lookup(notification_id)


    def notification_id_from_payload(self, payload):
        payload = payload or {}

        if 'notification_id' in payload:
            value = payload.get('notification_id')
        else:
            value = payload.get('ack_id')

        if value is None or isinstance(value, bool):
            return None

        try:
            return int(value)
        except (TypeError, ValueError):
            return None


class ModernAdminSafeActionRegistry:
    def __init__(self):
        self._actions = {}


    def register(self, action):
        if action.action_id in self._actions:
            raise ValueError('Duplicate safe action id: {0:s}'.format(action.action_id))

        self._actions[action.action_id] = action
        return action


    def get(self, action_id):
        return self._actions[action_id]


    def find(self, action_id):
        action = self._actions.get(action_id)
        if action:
            return action

        return ModernAdminSafeActionResult(
            action_id=str(action_id),
            feature='unknown',
            risk_level='unknown',
            status='not_found',
            message='Safe action is not registered',
            dry_run=True,
            allowed=False,
        )


    def list_actions(self, feature=None, risk_level=None):
        actions = list(self._actions.values())

        if feature is not None:
            actions = [action for action in actions if action.feature == feature]

        if risk_level is not None:
            actions = [action for action in actions if action.risk_level == risk_level]

        return sorted(actions, key=lambda action: action.action_id)


    def to_dict(self):
        return [
            {
                'action_id'  : action.action_id,
                'label'      : action.label,
                'feature'    : action.feature,
                'risk_level' : action.risk_level,
            }
            for action in self.list_actions()
        ]


class ModernAdminSafeActionRunner:
    """Small invocation helper for tests and future Flask wrappers.

    The runner intentionally has no Flask dependency and exposes no route. It
    only resolves an action from a registry and returns a structured result.
    """

    def __init__(self, registry):
        self.registry = registry


    def run(self, action_id=None, payload=None, actor=None, dry_run=True):
        if not action_id:
            return ModernAdminSafeActionResult(
                action_id='',
                feature='unknown',
                risk_level='unknown',
                status='missing_action_id',
                message='Safe action id is required',
                dry_run=True,
                allowed=False,
            )

        action = self.registry.find(action_id)
        if isinstance(action, ModernAdminSafeActionResult):
            return action

        return action.run(actor=actor, payload=payload or {}, dry_run=dry_run)


def allow_no_one(actor):
    return False


def build_default_modern_safe_action_registry():
    registry = ModernAdminSafeActionRegistry()

    registry.register(NotificationAcknowledgeSafeAction(
        permission_check=allow_no_one,
    ))

    for action_id, label, feature, risk_level in (
        ('image.exclude', 'Exclude Image', 'Image Viewer', 'medium'),
        ('image.unexclude', 'Unexclude Image', 'Image Viewer', 'medium'),
        ('log.download', 'Download Log', 'Logs', 'high'),
        ('task.retry', 'Retry Task', 'Task Queue', 'high'),
        ('task.cancel', 'Cancel Task', 'Task Queue', 'high'),
        ('config.restore_preview', 'Preview Config Restore', 'Config Restore', 'critical'),
        ('youtube.oauth_status_refresh', 'Refresh YouTube OAuth Status', 'YouTube / OAuth', 'critical'),
        ('focus.move', 'Move Focuser', 'Focus', 'critical'),
    ):
        registry.register(ModernAdminSafeActionPlaceholder(
            action_id=action_id,
            label=label,
            feature=feature,
            risk_level=risk_level,
            permission_check=allow_no_one,
        ))

    return registry
