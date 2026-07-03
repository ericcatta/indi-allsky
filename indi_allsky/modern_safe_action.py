import json
import re
from dataclasses import dataclass
from dataclasses import field
from datetime import date
from datetime import datetime
from pathlib import Path
from typing import Any
from typing import Callable

from .modern_admin_notifications import NOTIFICATION_ACKNOWLEDGE_ACTION_ID
from .modern_admin_notifications import NOTIFICATION_ACKNOWLEDGE_FEATURE
from .modern_admin_notifications import NOTIFICATION_ACKNOWLEDGE_LABEL
from .modern_admin_notifications import NOTIFICATION_ACKNOWLEDGE_RISK_LEVEL
from .modern_admin_notifications import NotificationAcknowledgeDbAdapter
from .modern_admin_notifications import NotificationAcknowledgeRepositoryError
from .modern_admin_notifications import NotificationAcknowledgeService


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
class ModernAdminSafeActionContract:
    action_id: str
    label: str
    feature: str
    risk_level: str
    required_permission: str = 'admin'

    def to_dict(self):
        return {
            'action_id'           : self.action_id,
            'label'               : self.label,
            'feature'             : self.feature,
            'risk_level'          : self.risk_level,
            'required_permission' : self.required_permission,
        }


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


@dataclass(frozen=True)
class ModernAdminSafeActionAuditRecord:
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
    def from_result(cls, result, actor=None, payload=None, sanitizer=None):
        sanitizer = sanitizer or ModernAdminSafeAction()
        result_summary = {
            'status'  : result.status,
            'message' : result.message,
            'details' : result.details,
        }

        return cls(
            action_id=result.action_id,
            feature=result.feature,
            actor=sanitizer.actor_label(actor),
            dry_run=result.dry_run,
            allowed=result.allowed,
            status=result.status,
            risk_level=result.risk_level,
            payload_summary=sanitizer.sanitize_payload(payload or {}),
            result_summary=sanitizer.sanitize_payload(result_summary),
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


class ModernAdminSafeActionAuditLog:
    """Append-only JSONL persistence for safe-action audit records.

    The log is intentionally lightweight and explicit-call only. It does not
    hook into Flask, logging, DB sessions, or action execution by itself.
    """

    def __init__(self, base_dir, max_files=30, max_record_bytes=16384):
        self.base_dir = Path(base_dir)
        self.max_files = max_files
        self.max_record_bytes = max_record_bytes


    def append(self, audit_record):
        data = self.record_to_dict(audit_record)
        path = self.path_for_record(data)
        serialized = json.dumps(data, sort_keys=True, separators=(',', ':'))

        if self.max_record_bytes and len(serialized.encode('utf-8')) > self.max_record_bytes:
            raise ValueError('Safe action audit record exceeds max_record_bytes')

        self.base_dir.mkdir(parents=True, exist_ok=True)
        with path.open('a', encoding='utf-8') as audit_file:
            audit_file.write(serialized + '\n')

        self.enforce_retention()

        return {
            'path'   : str(path),
            'bytes'  : len(serialized.encode('utf-8')),
            'written': True,
        }


    def record_to_dict(self, audit_record):
        if hasattr(audit_record, 'to_dict'):
            data = audit_record.to_dict()
        else:
            data = dict(audit_record)

        sanitizer = ModernAdminSafeAction()
        return sanitizer.sanitize_payload(data)


    def path_for_record(self, record_data):
        date_label = self.date_label(record_data.get('created_at'))
        return self.base_dir / '{0:s}.jsonl'.format(date_label)


    def date_label(self, created_at):
        if isinstance(created_at, str) and len(created_at) >= 10:
            candidate = created_at[:10]
            try:
                datetime.strptime(candidate, '%Y-%m-%d')
                return candidate
            except ValueError:
                pass

        return datetime.utcnow().strftime('%Y-%m-%d')


    def enforce_retention(self):
        if not self.max_files or self.max_files < 1:
            return

        files = sorted(self.base_dir.glob('*.jsonl'))
        stale_files = files[:-self.max_files]
        for stale_file in stale_files:
            stale_file.unlink()


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


    @classmethod
    def action_contract(cls):
        return ModernAdminSafeActionContract(
            action_id=cls.action_id,
            label=cls.label,
            feature=cls.feature,
            risk_level=cls.risk_level,
            required_permission=cls.required_permission,
        )


    @property
    def contract(self):
        return ModernAdminSafeActionContract(
            action_id=self.action_id,
            label=self.label,
            feature=self.feature,
            risk_level=self.risk_level,
            required_permission=self.required_permission,
        )


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
    action_id = NOTIFICATION_ACKNOWLEDGE_ACTION_ID
    label = NOTIFICATION_ACKNOWLEDGE_LABEL
    feature = NOTIFICATION_ACKNOWLEDGE_FEATURE
    risk_level = NOTIFICATION_ACKNOWLEDGE_RISK_LEVEL

    def __init__(self, permission_check=None, notification_lookup=None, acknowledge_callback=None, acknowledge_service=None):
        super().__init__(permission_check=permission_check)
        if acknowledge_service is not None:
            notification_lookup = acknowledge_service.lookup_notification
            acknowledge_callback = acknowledge_service.acknowledge_callback

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

        try:
            notification = self.notification_lookup(notification_id)
        except Exception:
            return 'notification lookup failed'

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

        if self.is_action_result(callback_result):
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


    def is_action_result(self, value):
        return all(
            hasattr(value, attr)
            for attr in (
                'action_id',
                'feature',
                'risk_level',
                'status',
                'message',
                'dry_run',
                'allowed',
                'details',
            )
        )


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


class ImageExcludeRepositoryError(RuntimeError):
    """Sanitized repository error for image exclude lookup."""


class ImageExcludeDbAdapter:
    """DB adapter between image models and the exclude service.

    The adapter performs lookup only. It does not change exclude state, commit,
    depend on Flask request context, or expose raw repository exception
    messages.
    """

    def __init__(self, image_model=None, query=None, no_result_exceptions=None):
        self.image_model = image_model
        self.query = query
        self.no_result_exceptions = tuple(no_result_exceptions or ())


    def lookup(self, image_id, camera_id):
        try:
            query = self.query_for_lookup()

            if hasattr(query, 'filter_by'):
                return query.filter_by(id=image_id, camera_id=camera_id).one()

            if self.image_model is None:
                raise ImageExcludeRepositoryError('image_model is required')

            return query.filter(
                self.image_model.id == image_id,
                self.image_model.camera_id == camera_id,
            ).one()
        except Exception as e:
            if self.is_no_result(e):
                return None

            raise ImageExcludeRepositoryError(type(e).__name__) from e


    def query_for_lookup(self):
        if self.query is not None:
            return self.query

        if self.image_model is None:
            raise ImageExcludeRepositoryError('image_model is required')

        return self.image_model.query


    def is_no_result(self, error):
        if self.no_result_exceptions and isinstance(error, self.no_result_exceptions):
            return True

        return type(error).__name__ == 'NoResultFound'


class ImageExcludeService:
    """Service boundary for image exclude/unexclude operations.

    The service is not exposed to Flask or the UI. It can change exclude state
    only through an explicit injected apply callback.
    """

    action_id = 'image.exclude'
    feature = 'Image Viewer'
    risk_level = 'medium'

    def __init__(self, image_lookup, apply_callback=None):
        self.image_lookup = image_lookup
        self.apply_callback = apply_callback


    def validate_positive_int(self, value, field_name):
        if value is None or isinstance(value, bool):
            return None, '{0:s} is required'.format(field_name)

        try:
            value_i = int(value)
        except (TypeError, ValueError):
            return None, '{0:s} must be a positive integer'.format(field_name)

        if value_i < 1:
            return None, '{0:s} must be a positive integer'.format(field_name)

        return value_i, None


    def validate_exclude(self, exclude):
        if not isinstance(exclude, bool):
            return None, 'exclude must be a boolean'

        return exclude, None


    def set_exclude(self, image_id, camera_id, exclude, image=None, actor=None, payload=None, dry_run=False):
        payload = payload or {}
        image_id_i, image_error = self.validate_positive_int(image_id, 'image_id')
        if image_error:
            return self.result(
                status='invalid_id',
                message=image_error,
                dry_run=dry_run,
                allowed=False,
                details={'image_id': image_id},
            )

        camera_id_i, camera_error = self.validate_positive_int(camera_id, 'camera_id')
        if camera_error:
            return self.result(
                status='invalid_camera_id',
                message=camera_error,
                dry_run=dry_run,
                allowed=False,
                details={
                    'image_id': image_id_i,
                    'camera_id': camera_id,
                },
            )

        exclude_b, exclude_error = self.validate_exclude(exclude)
        if exclude_error:
            return self.result(
                status='invalid_exclude',
                message=exclude_error,
                dry_run=dry_run,
                allowed=False,
                details={
                    'image_id': image_id_i,
                    'camera_id': camera_id_i,
                },
            )

        try:
            if image is None:
                image = self.image_lookup(image_id_i, camera_id_i)
        except Exception as e:
            return self.result(
                status='repository_error',
                message='Image lookup failed',
                dry_run=dry_run,
                allowed=False,
                details={
                    'image_id': image_id_i,
                    'camera_id': camera_id_i,
                    'error_type': type(e).__name__,
                },
            )

        if image is None:
            return self.result(
                status='not_found',
                message='Image does not exist',
                dry_run=dry_run,
                allowed=False,
                details={
                    'image_id': image_id_i,
                    'camera_id': camera_id_i,
                },
            )

        if bool(getattr(image, 'exclude', False)) is exclude_b:
            return self.result(
                status='already_set',
                message='Image exclude state is already set',
                dry_run=dry_run,
                allowed=True,
                details={
                    'image_id': image_id_i,
                    'camera_id': camera_id_i,
                    'exclude': exclude_b,
                    'idempotent': True,
                },
            )

        if dry_run:
            return self.result(
                status='dry_run',
                message='Dry run only; no image exclude state changed',
                dry_run=True,
                allowed=True,
                details={
                    'image_id': image_id_i,
                    'camera_id': camera_id_i,
                    'exclude': exclude_b,
                },
            )

        if self.apply_callback is None:
            return self.result(
                status='not_implemented',
                message='Image exclude apply callback is not configured',
                dry_run=False,
                allowed=False,
                details={
                    'image_id': image_id_i,
                    'camera_id': camera_id_i,
                    'exclude': exclude_b,
                },
            )

        try:
            callback_result = self.apply_callback(
                image_id=image_id_i,
                camera_id=camera_id_i,
                image=image,
                exclude=exclude_b,
                actor=actor,
                payload=payload,
            )
        except Exception as e:
            return self.result(
                status='update_failed',
                message='Image exclude update failed',
                dry_run=False,
                allowed=False,
                details={
                    'image_id': image_id_i,
                    'camera_id': camera_id_i,
                    'exclude': exclude_b,
                    'error_type': type(e).__name__,
                },
            )

        callback_details = {}
        if isinstance(callback_result, dict):
            callback_details = dict(callback_result.get('details', callback_result))

        return self.result(
            status='excluded' if exclude_b else 'unexcluded',
            message='Image excluded' if exclude_b else 'Image unexcluded',
            dry_run=False,
            allowed=True,
            details={
                'image_id': image_id_i,
                'camera_id': camera_id_i,
                'exclude': exclude_b,
                **callback_details,
            },
        )


    def set_exclude_with_audit(self, image_id, camera_id, exclude, actor=None, payload=None, audit_log=None, dry_run=False):
        payload = dict(payload or {})
        payload.setdefault('image_id', image_id)
        payload.setdefault('camera_id', camera_id)
        payload.setdefault('exclude', exclude)

        result = self.set_exclude(
            image_id=image_id,
            camera_id=camera_id,
            exclude=exclude,
            actor=actor,
            payload=payload,
            dry_run=dry_run,
        )

        audit_record = ModernAdminSafeActionAuditRecord.from_result(
            result,
            actor=actor,
            payload=payload,
        )
        audit_write = None
        if audit_log is not None:
            audit_write = audit_log.append(audit_record)

        return result, audit_record, audit_write


    def result(self, status, message, dry_run=False, allowed=False, details=None):
        return ModernAdminSafeActionResult(
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


class ImageExcludeSafeAction(ModernAdminSafeAction):
    action_id = 'image.exclude'
    label = 'Exclude Image'
    feature = 'Image Viewer'
    risk_level = 'medium'
    target_exclude = True

    def __init__(self, permission_check=None, image_lookup=None, apply_callback=None, image_service=None):
        super().__init__(permission_check=permission_check)
        if image_service is not None:
            image_lookup = image_service.image_lookup
            apply_callback = image_service.apply_callback

        self.image_lookup = image_lookup
        self.apply_callback = apply_callback


    def validate(self, payload):
        image_id = self.image_id_from_payload(payload)
        if image_id is None:
            return 'image_id is required'

        if image_id < 1:
            return 'image_id must be a positive integer'

        camera_id = self.camera_id_from_payload(payload)
        if camera_id is None:
            return 'camera_id is required'

        if camera_id < 1:
            return 'camera_id must be a positive integer'

        if self.image_lookup is None:
            return True

        try:
            image = self.image_lookup(image_id, camera_id)
        except Exception:
            return 'image lookup failed'

        if image is None:
            return 'image does not exist'

        return True


    def execute(self, actor=None, payload=None):
        payload = payload or {}
        image_id = self.image_id_from_payload(payload)
        camera_id = self.camera_id_from_payload(payload)
        service = ImageExcludeService(
            self.image_lookup or (lambda image_id, camera_id: None),
            apply_callback=self.apply_callback,
        )

        result = service.set_exclude(
            image_id=image_id,
            camera_id=camera_id,
            exclude=self.target_exclude,
            actor=actor,
            payload=payload,
            dry_run=False,
        )

        return result


    def image_id_from_payload(self, payload):
        payload = payload or {}

        if 'image_id' in payload:
            value = payload.get('image_id')
        else:
            value = payload.get('EXCLUDE_IMAGE_ID')

        if value is None or isinstance(value, bool):
            return None

        try:
            return int(value)
        except (TypeError, ValueError):
            return None


    def camera_id_from_payload(self, payload):
        payload = payload or {}

        if 'camera_id' in payload:
            value = payload.get('camera_id')
        else:
            value = payload.get('CAMERA_ID')

        if value is None or isinstance(value, bool):
            return None

        try:
            return int(value)
        except (TypeError, ValueError):
            return None


class ImageUnexcludeSafeAction(ImageExcludeSafeAction):
    action_id = 'image.unexclude'
    label = 'Unexclude Image'
    target_exclude = False


class LogDownloadPolicy:
    """Allowlist and redaction policy for future log downloads.

    This policy does not read, stream, or download files. It only validates
    symbolic log names and metadata from an injected stat provider.
    """

    DEFAULT_LOGS = {
        'capture': {
            'label': 'Capture Log',
            'path': '/var/log/indi-allsky/indi-allsky.log',
            'download_name': 'indi-allsky_log.txt.gz',
        },
        'webapp': {
            'label': 'Webapp Log',
            'path': '/var/log/indi-allsky/webapp-indi-allsky.log',
            'download_name': 'indi-allsky_webapp_log.txt.gz',
        },
        'syslog': {
            'label': 'OS System Log',
            'path': '/var/log/syslog',
            'download_name': 'indi-allsky_syslog_log.txt.gz',
        },
        'kernel': {
            'label': 'Kernel Log',
            'path': '/var/log/kern.log',
            'download_name': 'indi-allsky_kern_log.txt.gz',
        },
    }

    SECRET_VALUE_RE = re.compile(
        r'(?i)\b(api[_-]?key|password|refresh[_-]?token|secret|token|credential)\b\s*[:=]\s*([^\s,;]+)'
    )

    def __init__(self, allowed_logs=None, max_bytes=5 * 1024 * 1024):
        self.allowed_logs = dict(allowed_logs or self.DEFAULT_LOGS)
        self.max_bytes = max_bytes


    def normalize_log_name(self, log_name):
        if log_name is None or isinstance(log_name, bool):
            return None

        try:
            log_name_s = str(log_name).strip().lower()
        except (TypeError, ValueError):
            return None

        if not re.match(r'^[a-z0-9_-]+$', log_name_s):
            return None

        return log_name_s


    def resolve(self, log_name):
        log_name_s = self.normalize_log_name(log_name)
        if not log_name_s:
            return None, 'invalid_log_name'

        log_info = self.allowed_logs.get(log_name_s)
        if log_info is None:
            return None, 'not_allowlisted'

        path = Path(str(log_info.get('path', '')))
        if self.path_is_unsafe(path):
            return None, 'unsafe_path'

        resolved = dict(log_info)
        resolved['log_name'] = log_name_s
        resolved['basename'] = path.name
        return resolved, None


    def path_is_unsafe(self, path):
        if not path.is_absolute():
            return True

        path_parts = path.parts
        if '..' in path_parts:
            return True

        for allowed_info in self.allowed_logs.values():
            allowed_path = Path(str(allowed_info.get('path', '')))
            if path == allowed_path:
                return False

        return True


    def inspect_metadata(self, log_info, stat_provider=None):
        metadata = {
            'log_name': log_info.get('log_name'),
            'label': log_info.get('label'),
            'basename': log_info.get('basename'),
            'download_name': log_info.get('download_name'),
            'redaction_required': True,
            'size_bytes': None,
            'max_bytes': self.max_bytes,
            'too_large': False,
        }

        if stat_provider is None:
            return metadata

        stat_data = stat_provider(log_info)
        if stat_data is None:
            return metadata

        stat_data = dict(stat_data)
        size_bytes = stat_data.get('size_bytes')
        if size_bytes is not None:
            try:
                size_bytes = int(size_bytes)
            except (TypeError, ValueError):
                size_bytes = None

        metadata['size_bytes'] = size_bytes
        if size_bytes is not None:
            metadata['too_large'] = bool(self.max_bytes and size_bytes > self.max_bytes)

        return metadata


    def redact_text(self, text):
        text_s = str(text)
        text_s = self.SECRET_VALUE_RE.sub(lambda match: '{0:s}=[REDACTED]'.format(match.group(1)), text_s)

        for token in SECRET_TOKENS:
            text_s = re.sub(
                r'(?i)({0:s})\s*[:=]\s*([^\s,;]+)'.format(re.escape(token)),
                r'\1=[REDACTED]',
                text_s,
            )

        return text_s


class LogDownloadService:
    """Service-only foundation for future log download actions.

    The service performs no file reads, no streaming, and no downloads. Metadata
    inspection uses an injected provider so tests can remain filesystem-free.
    """

    action_id = 'log.download'
    feature = 'Logs'
    risk_level = 'high'

    def __init__(self, policy=None, stat_provider=None):
        self.policy = policy or LogDownloadPolicy()
        self.stat_provider = stat_provider


    def inspect(self, log_name, actor=None, payload=None, dry_run=True):
        payload = payload or {}
        log_info, error = self.policy.resolve(log_name)
        if error:
            return self.result(
                status=error,
                message='Log is not available for safe download',
                dry_run=True,
                allowed=False,
                details={'log_name': log_name},
            )

        try:
            metadata = self.policy.inspect_metadata(log_info, stat_provider=self.stat_provider)
        except Exception as e:
            return self.result(
                status='metadata_error',
                message='Log metadata lookup failed',
                dry_run=True,
                allowed=False,
                details={
                    'log_name': log_info.get('log_name'),
                    'error_type': type(e).__name__,
                },
            )

        if metadata.get('too_large'):
            return self.result(
                status='too_large',
                message='Log exceeds safe download size limit',
                dry_run=True,
                allowed=False,
                details=metadata,
            )

        if not dry_run:
            return self.result(
                status='not_implemented',
                message='Real log download is not implemented in Modern Safe Actions',
                dry_run=False,
                allowed=False,
                details=metadata,
            )

        return self.result(
            status='dry_run',
            message='Dry run only; no log file read or streamed',
            dry_run=True,
            allowed=True,
            details=metadata,
        )


    def inspect_with_audit(self, log_name, actor=None, payload=None, audit_log=None, dry_run=True):
        payload = dict(payload or {})
        payload.setdefault('log_name', log_name)

        result = self.inspect(
            log_name=log_name,
            actor=actor,
            payload=payload,
            dry_run=dry_run,
        )
        audit_record = ModernAdminSafeActionAuditRecord.from_result(
            result,
            actor=actor,
            payload=payload,
        )
        audit_write = None
        if audit_log is not None:
            audit_write = audit_log.append(audit_record)

        return result, audit_record, audit_write


    def result(self, status, message, dry_run=True, allowed=False, details=None):
        return ModernAdminSafeActionResult(
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


class LogDownloadSafeAction(ModernAdminSafeAction):
    action_id = 'log.download'
    label = 'Download Log'
    feature = 'Logs'
    risk_level = 'high'

    def __init__(self, permission_check=None, log_service=None):
        super().__init__(permission_check=permission_check)
        self.log_service = log_service or LogDownloadService()


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

        result = self.log_service.inspect(
            log_name=self.log_name_from_payload(payload),
            actor=actor,
            payload=payload,
            dry_run=dry_run,
        )

        return result


    def validate(self, payload):
        log_name = self.log_name_from_payload(payload)
        if log_name is None:
            return 'log_name is required'

        _, error = self.log_service.policy.resolve(log_name)
        if error:
            return 'log_name is not allowlisted'

        return True


    def execute(self, actor=None, payload=None):
        payload = payload or {}
        return self.log_service.inspect(
            log_name=self.log_name_from_payload(payload),
            actor=actor,
            payload=payload,
            dry_run=False,
        )


    def log_name_from_payload(self, payload):
        payload = payload or {}

        if 'log_name' in payload:
            value = payload.get('log_name')
        else:
            value = payload.get('log')

        return self.log_service.policy.normalize_log_name(value)


class ModernAdminCaptureServiceCommandBoundary:
    """Hybrid-owned command boundary for capture service controls.

    The boundary owns request intent normalization and command allowlisting.
    The injected effect adapter remains responsible for the actual service
    command, preserving existing runtime behavior.
    """

    action_id = 'capture.service_control'
    feature = 'Capture Service'
    risk_level = 'critical'

    DEFAULT_COMMANDS = {
        'start'   : 'started',
        'stop'    : 'stopped',
        'restart' : 'restarted',
    }

    def __init__(self, effect_adapter=None, valid_commands=None):
        self.effect_adapter = effect_adapter
        self.valid_commands = dict(valid_commands or self.DEFAULT_COMMANDS)


    def normalize_command(self, value):
        if isinstance(value, dict) or hasattr(value, 'get'):
            value = value.get('command')

        if value is None or isinstance(value, bool):
            return ''

        return str(value).strip().lower()


    def run(self, command=None, actor=None, payload=None):
        payload = payload or {}
        command = self.normalize_command(command if command is not None else payload)

        if command not in self.valid_commands:
            return ModernAdminSafeActionResult(
                action_id=self.action_id,
                feature=self.feature,
                risk_level=self.risk_level,
                status='validation_failed',
                message='Invalid capture command.',
                dry_run=False,
                allowed=False,
                details={
                    'command': command,
                },
            )

        if self.effect_adapter is None:
            return ModernAdminSafeActionResult(
                action_id=self.action_id,
                feature=self.feature,
                risk_level=self.risk_level,
                status='not_implemented',
                message='Capture service command adapter is not configured.',
                dry_run=False,
                allowed=False,
                details={
                    'command': command,
                },
            )

        effect_result = self.effect_adapter(command)

        return ModernAdminSafeActionResult(
            action_id=self.action_id,
            feature=self.feature,
            risk_level=self.risk_level,
            status='executed',
            message='Capture service command executed.',
            dry_run=False,
            allowed=True,
            details={
                'command'       : command,
                'past_tense'    : self.valid_commands[command],
                'service_result': effect_result,
            },
        )


class ModernAdminGeneratedOutputActionPlanner:
    """Hybrid-owned planning boundary for generated-output actions.

    The planner does not enqueue tasks, write to the database, generate media,
    or touch the filesystem. It only normalizes a supported action intent into
    the same job payload shape used by the existing effect adapter.
    """

    action_id = 'generated_output.plan'
    feature = 'Generated Output'
    risk_level = 'high'

    DEFAULT_ACTIONS = {
        'generate_video': {
            'job_action': 'generateVideo',
            'queue'     : 'VIDEO',
            'state'     : 'MANUAL',
            'priority'  : 100,
        },
        'generate_k_st': {
            'job_action': 'generateKeogramStarTrails',
            'queue'     : 'VIDEO',
            'state'     : 'MANUAL',
            'priority'  : 100,
        },
        'generate_panorama_video': {
            'job_action'         : 'generatePanoramaVideo',
            'queue'              : 'VIDEO',
            'state'              : 'MANUAL',
            'priority'           : 100,
            'requires_fish2pano' : True,
            'disabled_message'   : 'Panoramas disabled',
        },
    }

    def __init__(self, supported_actions=None):
        self.supported_actions = dict(supported_actions or self.DEFAULT_ACTIONS)


    def normalize_action(self, value):
        if value is None or isinstance(value, bool):
            return ''

        return str(value).strip().lower()


    def normalize_camera_id(self, value):
        if value is None or isinstance(value, bool):
            return None

        try:
            camera_id = int(value)
        except (TypeError, ValueError):
            return None

        if camera_id < 1:
            return None

        return camera_id


    def normalize_day_date(self, value):
        if isinstance(value, datetime):
            return value.date()

        if isinstance(value, date):
            return value

        if value is None or isinstance(value, bool):
            return None

        try:
            return datetime.strptime(str(value).strip(), '%Y-%m-%d').date()
        except (TypeError, ValueError):
            return None


    def normalize_night(self, value):
        if isinstance(value, bool):
            return value

        if value is None:
            return None

        value_s = str(value).strip().lower()
        if value_s in ('night', 'true', '1', 'yes'):
            return True

        if value_s in ('day', 'false', '0', 'no'):
            return False

        return None


    def fish2pano_enabled(self, config):
        if config is None:
            return False

        fish2pano_config = config.get('FISH2PANO', {}) if hasattr(config, 'get') else {}
        if not hasattr(fish2pano_config, 'get'):
            return False

        return bool(fish2pano_config.get('ENABLE'))


    def plan(self, action=None, camera_id=None, day_date=None, night=None, payload=None, config=None):
        payload = payload or {}
        action_name = self.normalize_action(action if action is not None else payload.get('action', payload.get('ACTION_SELECT')))
        camera_id = self.normalize_camera_id(camera_id if camera_id is not None else payload.get('camera_id', payload.get('CAMERA_ID')))
        day_date = self.normalize_day_date(day_date if day_date is not None else payload.get('day_date', payload.get('DAY_DATE')))
        night = self.normalize_night(night if night is not None else payload.get('night', payload.get('NIGHT')))

        if action_name not in self.supported_actions:
            return self.result(
                status='validation_failed',
                message='Unsupported generated output action.',
                allowed=False,
                details={
                    'action': action_name,
                },
            )

        if camera_id is None:
            return self.result(
                status='validation_failed',
                message='camera_id is required.',
                allowed=False,
                details={
                    'action': action_name,
                },
            )

        if day_date is None:
            return self.result(
                status='validation_failed',
                message='day_date is required.',
                allowed=False,
                details={
                    'action'   : action_name,
                    'camera_id': camera_id,
                },
            )

        if night is None:
            return self.result(
                status='validation_failed',
                message='night is required.',
                allowed=False,
                details={
                    'action'   : action_name,
                    'camera_id': camera_id,
                },
            )

        action_config = self.supported_actions[action_name]
        if action_config.get('requires_fish2pano') and not self.fish2pano_enabled(config):
            return self.result(
                status='unavailable',
                message=action_config.get('disabled_message', 'Generated output action unavailable.'),
                allowed=False,
                details={
                    'action'    : action_name,
                    'camera_id' : camera_id,
                    'day_date'  : day_date.isoformat(),
                    'night'     : night,
                },
            )

        timespec = day_date.strftime('%Y%m%d')
        jobdata = {
            'action' : action_config['job_action'],
            'kwargs' : {
                'timespec'  : timespec,
                'night'     : night,
                'camera_id' : camera_id,
            },
        }

        return self.result(
            status='planned',
            message='Generated output action planned.',
            allowed=True,
            details={
                'action'    : action_name,
                'camera_id' : camera_id,
                'day_date'  : day_date.isoformat(),
                'timespec'  : timespec,
                'night'     : night,
                'jobdata'   : jobdata,
                'queue'     : action_config['queue'],
                'state'     : action_config['state'],
                'priority'  : action_config['priority'],
            },
        )


    def result(self, status, message, allowed=False, details=None):
        return ModernAdminSafeActionResult(
            action_id=self.action_id,
            feature=self.feature,
            risk_level=self.risk_level,
            status=status,
            message=message,
            dry_run=True,
            allowed=allowed,
            details=details or {},
        )


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


    def run_with_audit(self, action_id=None, payload=None, actor=None, dry_run=True):
        payload = payload or {}
        result = self.run(
            action_id=action_id,
            payload=payload,
            actor=actor,
            dry_run=dry_run,
        )
        audit_record = ModernAdminSafeActionAuditRecord.from_result(
            result,
            actor=actor,
            payload=payload,
        )

        return result, audit_record


def allow_no_one(actor):
    return False


def build_notification_acknowledge_dry_run_registry(permission_check):
    registry = ModernAdminSafeActionRegistry()
    registry.register(NotificationAcknowledgeSafeAction(
        permission_check=permission_check,
    ))
    return registry


def run_modern_safe_action_dry_run(action_id=None, payload=None, actor=None, permission_check=None):
    registry = build_notification_acknowledge_dry_run_registry(
        permission_check=permission_check or allow_no_one,
    )
    runner = ModernAdminSafeActionRunner(registry)
    return runner.run(
        action_id=action_id,
        payload=payload or {},
        actor=actor,
        dry_run=True,
    )


def build_default_modern_safe_action_registry():
    registry = ModernAdminSafeActionRegistry()

    registry.register(NotificationAcknowledgeSafeAction(
        permission_check=allow_no_one,
    ))
    registry.register(ImageExcludeSafeAction(
        permission_check=allow_no_one,
    ))
    registry.register(ImageUnexcludeSafeAction(
        permission_check=allow_no_one,
    ))
    registry.register(LogDownloadSafeAction(
        permission_check=allow_no_one,
    ))

    for action_id, label, feature, risk_level in (
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
