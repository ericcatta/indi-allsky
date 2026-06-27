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
