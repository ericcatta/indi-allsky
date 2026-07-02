from dataclasses import dataclass
from dataclasses import field
from datetime import datetime
from typing import Any


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

NOTIFICATION_ACKNOWLEDGE_ACTION_ID = 'notification.acknowledge'
NOTIFICATION_ACKNOWLEDGE_LABEL = 'Acknowledge Notification'
NOTIFICATION_ACKNOWLEDGE_FEATURE = 'Notifications'
NOTIFICATION_ACKNOWLEDGE_RISK_LEVEL = 'medium'


@dataclass(frozen=True)
class NotificationAcknowledgeResult:
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


@dataclass(frozen=True)
class NotificationAcknowledgeAuditRecord:
    action_id: str
    feature: str
    actor: str
    dry_run: bool
    allowed: bool
    status: str
    risk_level: str
    payload_summary: dict[str, Any] = field(default_factory=dict)
    result_summary: dict[str, Any] = field(default_factory=dict)
    reason: str = ''
    created_at: str = field(default_factory=lambda: datetime.utcnow().replace(microsecond=0).isoformat() + 'Z')


    @classmethod
    def from_result(cls, result, actor=None, payload=None):
        result_summary = {
            'status'  : result.status,
            'message' : result.message,
            'details' : result.details,
        }

        return cls(
            action_id=result.action_id,
            feature=result.feature,
            actor=actor_label(actor),
            dry_run=result.dry_run,
            allowed=result.allowed,
            status=result.status,
            risk_level=result.risk_level,
            payload_summary=sanitize_payload(payload or {}),
            result_summary=sanitize_payload(result_summary),
            reason=result.message,
            created_at=result.created_at,
        )


    def to_dict(self):
        return {
            'action_id'      : self.action_id,
            'feature'        : self.feature,
            'actor'          : self.actor,
            'dry_run'        : self.dry_run,
            'allowed'        : self.allowed,
            'status'         : self.status,
            'risk_level'     : self.risk_level,
            'payload_summary': dict(self.payload_summary),
            'result_summary' : dict(self.result_summary),
            'reason'         : self.reason,
            'created_at'     : self.created_at,
        }


def actor_label(actor):
    if actor is None:
        return 'unknown'

    for attr in ('username', 'id'):
        value = getattr(actor, attr, None)
        if value is not None:
            return str(value)

    return str(actor)


def sanitize_payload(value):
    if isinstance(value, dict):
        sanitized = {}
        for key, item in value.items():
            key_s = str(key)
            if is_secret_key(key_s):
                sanitized[key_s] = '[REDACTED]'
            else:
                sanitized[key_s] = sanitize_payload(item)
        return sanitized

    if isinstance(value, list):
        return [sanitize_payload(item) for item in value]

    return value


def is_secret_key(key):
    key_l = key.lower()
    return any(token in key_l for token in SECRET_TOKENS)


class NotificationAcknowledgeRepositoryError(RuntimeError):
    """Sanitized repository error for notification acknowledge lookup."""


class NotificationAcknowledgeDbAdapter:
    """DB adapter between notification models and the acknowledge service.

    The adapter performs lookup only. It does not call setAck(), commit, mutate
    database state, depend on web context, or expose raw repository
    exception messages.
    """

    def __init__(self, notification_model=None, query=None, no_result_exceptions=None):
        self.notification_model = notification_model
        self.query = query
        self.no_result_exceptions = tuple(no_result_exceptions or ())


    def lookup(self, notification_id):
        try:
            query = self.query_for_lookup()

            if hasattr(query, 'filter_by'):
                return query.filter_by(id=notification_id).one()

            if self.notification_model is None:
                raise NotificationAcknowledgeRepositoryError('notification_model is required')

            return query.filter(self.notification_model.id == notification_id).one()
        except Exception as e:
            if self.is_no_result(e):
                return None

            raise NotificationAcknowledgeRepositoryError(type(e).__name__) from e


    def query_for_lookup(self):
        if self.query is not None:
            return self.query

        if self.notification_model is None:
            raise NotificationAcknowledgeRepositoryError('notification_model is required')

        return self.notification_model.query


    def is_no_result(self, error):
        if self.no_result_exceptions and isinstance(error, self.no_result_exceptions):
            return True

        return type(error).__name__ == 'NoResultFound'


class NotificationAcknowledgeService:
    """Hybrid-owned service boundary for notification acknowledge operations."""

    action_id = NOTIFICATION_ACKNOWLEDGE_ACTION_ID
    feature = NOTIFICATION_ACKNOWLEDGE_FEATURE
    risk_level = NOTIFICATION_ACKNOWLEDGE_RISK_LEVEL

    def __init__(self, notification_lookup):
        self.notification_lookup = notification_lookup


    def validate_notification_id(self, notification_id):
        if notification_id is None or isinstance(notification_id, bool):
            return None, 'notification_id is required'

        try:
            notification_id_i = int(notification_id)
        except (TypeError, ValueError):
            return None, 'notification_id must be a positive integer'

        if notification_id_i < 1:
            return None, 'notification_id must be a positive integer'

        return notification_id_i, None


    def lookup_notification(self, notification_id):
        notification_id_i, error = self.validate_notification_id(notification_id)
        if error:
            return None

        return self.notification_lookup(notification_id_i)


    def acknowledge(self, notification_id, notification=None, actor=None, payload=None):
        payload = payload or {}
        notification_id_i, error = self.validate_notification_id(notification_id)
        if error:
            return self.result(
                status='invalid_id',
                message=error,
                dry_run=False,
                allowed=False,
                details={'notification_id': notification_id},
            )

        try:
            if notification is None:
                notification = self.notification_lookup(notification_id_i)
        except Exception as e:
            return self.result(
                status='repository_error',
                message='Notification lookup failed',
                dry_run=False,
                allowed=False,
                details={
                    'notification_id': notification_id_i,
                    'error_type': type(e).__name__,
                },
            )

        if notification is None:
            return self.result(
                status='not_found',
                message='Notification does not exist',
                dry_run=False,
                allowed=False,
                details={'notification_id': notification_id_i},
            )

        if bool(getattr(notification, 'ack', False)):
            return self.result(
                status='already_acked',
                message='Notification is already acknowledged',
                dry_run=False,
                allowed=True,
                details={
                    'notification_id': notification_id_i,
                    'idempotent': True,
                },
            )

        try:
            notification.setAck()
        except Exception as e:
            return self.result(
                status='acknowledge_failed',
                message='Notification acknowledge failed',
                dry_run=False,
                allowed=False,
                details={
                    'notification_id': notification_id_i,
                    'error_type': type(e).__name__,
                },
            )

        return self.result(
            status='acknowledged',
            message='Notification acknowledged',
            dry_run=False,
            allowed=True,
            details={'notification_id': notification_id_i},
        )


    def acknowledge_with_audit(self, notification_id, actor=None, payload=None, audit_log=None, dry_run=False):
        payload = dict(payload or {})
        payload.setdefault('notification_id', notification_id)

        if dry_run:
            result = self.dry_run(notification_id)
        else:
            result = self.acknowledge(
                notification_id=notification_id,
                actor=actor,
                payload=payload,
            )

        audit_record = NotificationAcknowledgeAuditRecord.from_result(
            result,
            actor=actor,
            payload=payload,
        )
        audit_write = None
        if audit_log is not None:
            audit_write = audit_log.append(audit_record)

        return result, audit_record, audit_write


    def dry_run(self, notification_id):
        notification_id_i, error = self.validate_notification_id(notification_id)
        if error:
            return self.result(
                status='invalid_id',
                message=error,
                dry_run=True,
                allowed=False,
                details={'notification_id': notification_id},
            )

        try:
            notification = self.notification_lookup(notification_id_i)
        except Exception as e:
            return self.result(
                status='repository_error',
                message='Notification lookup failed',
                dry_run=True,
                allowed=False,
                details={
                    'notification_id': notification_id_i,
                    'error_type': type(e).__name__,
                },
            )

        if notification is None:
            return self.result(
                status='not_found',
                message='Notification does not exist',
                dry_run=True,
                allowed=False,
                details={'notification_id': notification_id_i},
            )

        if bool(getattr(notification, 'ack', False)):
            return self.result(
                status='already_acked',
                message='Notification is already acknowledged',
                dry_run=True,
                allowed=True,
                details={
                    'notification_id': notification_id_i,
                    'idempotent': True,
                },
            )

        return self.result(
            status='dry_run',
            message='Dry run only; no action executed',
            dry_run=True,
            allowed=True,
            details={'notification_id': notification_id_i},
        )


    def acknowledge_callback(self, notification_id, notification=None, actor=None, payload=None):
        return self.acknowledge(
            notification_id=notification_id,
            notification=notification,
            actor=actor,
            payload=payload or {},
        )


    def result(self, status, message, dry_run=False, allowed=False, details=None):
        return NotificationAcknowledgeResult(
            action_id=self.action_id,
            feature=self.feature,
            risk_level=self.risk_level,
            status=status,
            message=message,
            dry_run=dry_run,
            allowed=allowed,
            audit_message='service action={0:s} status={1:s}'.format(self.action_id, status),
            details=details or {},
        )


class ModernAdminNotificationReadService:
    def __init__(self, query, order_by_expression=None, id_field=None):
        self.query = query
        self.order_by_expression = order_by_expression
        self.id_field = id_field


    def list_notifications(self, limit=100):
        query = self.query
        if self.order_by_expression is not None:
            query = query.order_by(self.order_by_expression)
        if limit is not None:
            query = query.limit(limit)

        return query.all()


    def get_notification(self, notification_id):
        query = self.query
        if self.id_field is not None:
            query = query.filter(self.id_field == notification_id)

        return query.one()


    def build_notification_rows(self, notices):
        return [
            self.build_notification_row(notice)
            for notice in notices
        ]


    def build_notification_detail(self, notice):
        return self.build_notification_row(notice)


    def build_notification_list_context(self, notification_rows):
        return {
            'modern_admin_notification_rows'          : notification_rows,
            'modern_admin_notification_count'         : len(notification_rows),
            'modern_admin_notification_unacked_count' : len([
                row for row in notification_rows if row['ack'] == 'No'
            ]),
            'modern_admin_notification_categories'    : sorted({row['category'] for row in notification_rows}),
            'modern_admin_notification_items'         : sorted({row['item'] for row in notification_rows}),
        }


    def build_notification_detail_context(self, notification_detail):
        return {
            'modern_admin_notification_detail': notification_detail,
        }


    def build_notification_row(self, notice):
        is_ack = bool(getattr(notice, 'ack', False))

        return {
            'id'          : getattr(notice, 'id', None),
            'category'    : self.format_notification_category(getattr(notice, 'category', None)),
            'item'        : getattr(notice, 'item', None) or 'Not set',
            'created'     : self.format_notification_datetime(getattr(notice, 'createDate', None)),
            'expires'     : self.format_notification_datetime(getattr(notice, 'expireDate', None)),
            'ack'         : 'Yes' if is_ack else 'No',
            'ack_tone'    : 'modern-admin-status-muted' if is_ack else 'modern-admin-status-warning',
            'notification': getattr(notice, 'notification', None),
        }


    def format_notification_datetime(self, value, default='Unknown'):
        if not value:
            return default
        if hasattr(value, 'strftime'):
            return value.strftime('%Y-%m-%d %H:%M:%S')
        return str(value)


    def format_notification_category(self, value):
        if value:
            return getattr(value, 'value', value)
        return 'Unknown'
