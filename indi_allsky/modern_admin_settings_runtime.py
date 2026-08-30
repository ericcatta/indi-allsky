from datetime import datetime
from datetime import timezone

from .exceptions import ConfigSaveException


class ModernAdminSettingsConfigValidationService:
    """Hybrid-owned type validation for config payloads before persistence."""

    SKIP_KEYS = (
        'INDI_CONFIG_DEFAULTS',
        'INDI_CONFIG_DAY',
    )

    SKIP_NESTED_KEYS = (
        ('FILETRANSFER', 'LIBCURL_OPTIONS'),
    )

    def __init__(self, base_config, logger=None):
        self.base_config = base_config
        self.logger = logger


    def validate(self, config):
        for key in config.keys():
            if key in self.SKIP_KEYS:
                continue

            if isinstance(config[key], dict):
                self.validate_nested_config(config, key)
            else:
                self.validate_value(config, key)

        return True


    def validate_nested_config(self, config, key):
        for nested_key in config[key].keys():
            if (key, nested_key) in self.SKIP_NESTED_KEYS:
                continue

            try:
                expected_value = self.base_config[key][nested_key]
            except KeyError:
                self.log_warning(
                    'Config key not found in base config: [%s][%s]',
                    str(key),
                    str(nested_key),
                )
                continue

            value = config[key][nested_key]
            if not isinstance(value, self.valid_types(value, expected_value)):
                self.log_error(
                    'Config key has wrong type: [%s][%s] (%s vs %s)',
                    str(key),
                    str(nested_key),
                    str(type(expected_value)),
                    str(type(value)),
                )
                raise ConfigSaveException(
                    'Config key has wrong type: [{0:s}][{1:s}]'.format(
                        str(key),
                        str(nested_key),
                    ),
                )


    def validate_value(self, config, key):
        try:
            expected_value = self.base_config[key]
        except KeyError:
            self.log_warning('Config key not found in base config: [%s]', str(key))
            return

        value = config[key]
        if not isinstance(value, self.valid_types(value, expected_value)):
            self.log_error(
                'Config key has wrong type: [%s] (%s vs %s)',
                str(key),
                str(type(expected_value)),
                str(type(value)),
            )
            raise ConfigSaveException(
                'Config key has wrong type: [{0:s}]'.format(str(key)),
            )


    def valid_types(self, value, expected_value):
        if isinstance(value, int):
            return (int, float)

        return type(expected_value)


    def log_error(self, message, *args):
        if self.logger is not None:
            self.logger.error(message, *args)


    def log_warning(self, message, *args):
        if self.logger is not None:
            self.logger.warning(message, *args)


class ModernAdminConfigRevisionPersistenceAdapter:
    """Hybrid-owned persistence for an already validated config revision."""

    def __init__(self, config_model, db_session, config_level, clock=None):
        self.config_model = config_model
        self.db_session = db_session
        self.config_level = config_level
        self.clock = clock or self.utcnow


    def save_revision(self, config, user_entry, note, encrypted):
        config_entry = self.config_model(
            data=config,
            createDate=self.clock(),
            level=str(self.config_level),
            user_id=user_entry.id,
            note=str(note),
            encrypted=encrypted,
        )

        self.db_session.add(config_entry)
        self.db_session.commit()
        return config_entry


    def utcnow(self):
        return datetime.now(tz=timezone.utc).replace(tzinfo=None)


class ModernAdminSettingsRevisionRollbackService:
    """Hybrid-owned application of a confirmed config revision rollback."""

    ROLLBACK_NOTE = 'Revert to config: {revision_id:d}'

    def apply_revision(self, revision, current_config, save_adapter, username='system'):
        current_config.update(revision.data)
        return save_adapter(
            username,
            self.ROLLBACK_NOTE.format(revision_id=revision.id),
        )


class ModernAdminSettingsRuntimeService:
    """Hybrid-owned boundary for Modern settings runtime persistence.

    The service owns the Modern settings save intent. The default config adapter
    still delegates to the existing config implementation so persistence
    behavior stays unchanged.
    """

    def __init__(self, config_adapter_factory=None):
        self.config_adapter_factory = config_adapter_factory or self.default_config_adapter_factory


    def save_config_revision(self, config, username, note):
        config_adapter = self.config_adapter_factory()
        config_adapter.config = config
        return config_adapter.save(username, note)


    def save_full_config(self, config, username, note, config_adapter):
        config_adapter.config = config
        return config_adapter.save(username, note)


    def default_config_adapter_factory(self):
        from .config import IndiAllSkyConfig

        return IndiAllSkyConfig()


class ModernAdminSettingsRestoreValidationError(ValueError):
    pass


class ModernAdminSettingsRestoreService:
    """Hybrid-owned boundary for settings restore execution intent.

    The service validates the restore target and delegates persistence to the
    existing config adapter so restore behavior and storage semantics remain
    unchanged.
    """

    REQUIRED_CONFIG_KEYS = (
        'INDI_SERVER',
        'CCD_CONFIG',
        'INDI_CONFIG_DEFAULTS',
    )

    DEFAULT_RESTORE_NOTE = 'Manual config restore from upload'

    def post_restore_cleanup(self, flush_configs=None, reset_keys=None, flush_adapter=None, reset_adapter=None):
        cleanup_flags = self.normalize_post_restore_flags(
            flush_configs=flush_configs,
            reset_keys=reset_keys,
        )

        if cleanup_flags['flush_configs'] and flush_adapter is not None:
            flush_adapter()

        if cleanup_flags['reset_keys'] and reset_adapter is not None:
            reset_adapter()

        return cleanup_flags


    def normalize_post_restore_flags(self, flush_configs=None, reset_keys=None):
        return {
            'flush_configs': bool(flush_configs),
            'reset_keys': bool(reset_keys),
        }


    def restore_config(self, config, username, config_adapter, note=None):
        self.validate_restore_target(config)
        config_adapter.config = config
        return config_adapter.save(username, note or self.DEFAULT_RESTORE_NOTE)


    def validate_restore_target(self, config):
        if not isinstance(config, dict):
            raise ModernAdminSettingsRestoreValidationError('Not a valid indi-allsky config')

        if (
            not isinstance(config.get('INDI_SERVER'), str)
            or not isinstance(config.get('CCD_CONFIG'), dict)
            or not isinstance(config.get('INDI_CONFIG_DEFAULTS'), dict)
        ):
            raise ModernAdminSettingsRestoreValidationError('Not a valid indi-allsky config')

        return True


class ModernAdminSettingsReloadCommandService:
    """Hybrid-owned reload/restart intent boundary for settings saves."""

    RELOAD_ACTION = 'reload'
    SAVE_MESSAGE = 'Saved new config'
    RELOAD_MESSAGE = 'Saved new config,  Reloading indi-allsky service.'

    def execute_after_save(self, reload_requested=None, status_adapter=None, task_adapter=None):
        plan = self.build_after_save_plan(reload_requested=reload_requested)

        if plan['reload_requested']:
            if status_adapter is not None:
                status_adapter()

            if task_adapter is not None:
                task_adapter(plan['task_action'])

        return plan


    def build_after_save_plan(self, reload_requested=None):
        reload_enabled = self.normalize_reload_intent(reload_requested)
        return {
            'reload_requested': reload_enabled,
            'task_action': self.RELOAD_ACTION if reload_enabled else None,
            'success_message': self.RELOAD_MESSAGE if reload_enabled else self.SAVE_MESSAGE,
        }


    def normalize_reload_intent(self, reload_requested=None):
        return bool(reload_requested)


class ModernAdminSettingsRevisionMetadataService:
    """Hybrid-owned read model for config revision metadata.

    The DB/query object is injected by the Flask layer. This keeps restore
    execution and persistence unchanged while moving history/restore metadata
    ownership out of Modern views.
    """

    RESTORE_WARNING = 'Read-only inspection only. Actual restore flow remains in Classic UI.'
    RESTORE_DETAIL_WARNING = 'Read-only metadata inspection only. Raw config payload and restore actions are intentionally hidden.'

    def __init__(self, query, id_field=None, created_field=None):
        self.query = query
        self.id_field = id_field
        self.created_field = created_field


    def history_context(self, limit=25):
        rows = self.list_revisions(limit=limit, include_restore_state=False)
        return {
            'modern_admin_config_history_rows'             : rows,
            'modern_admin_config_history_count'            : len(rows),
            'modern_admin_config_history_display_limit'    : limit,
            'modern_admin_config_history_encrypted_count'  : len([
                row for row in rows if row['encrypted'] == 'Yes'
            ]),
            'modern_admin_config_history_levels'           : sorted({row['level'] for row in rows}),
            'modern_admin_config_history_encrypted_states' : sorted({row['encrypted'] for row in rows}),
        }


    def restore_context(self, limit=25):
        rows = self.list_revisions(limit=limit, include_restore_state=True)
        return {
            'modern_admin_config_restore_rows'             : rows,
            'modern_admin_config_restore_count'            : len(rows),
            'modern_admin_config_restore_display_limit'    : limit,
            'modern_admin_config_restore_likely_count'     : len([
                row for row in rows if row['restore_state'] == 'Likely restore candidate'
            ]),
            'modern_admin_config_restore_encrypted_count'  : len([
                row for row in rows if row['encrypted'] == 'Yes'
            ]),
            'modern_admin_config_restore_levels'           : sorted({row['level'] for row in rows}),
            'modern_admin_config_restore_states'           : sorted({row['restore_state'] for row in rows}),
            'modern_admin_config_restore_warning'          : self.RESTORE_WARNING,
        }


    def restore_detail_context(self, config_id):
        entry = self.lookup_revision(config_id)
        return {
            'modern_admin_config_restore_detail'  : self.format_revision(
                entry,
                include_restore_state=True,
            ),
            'modern_admin_config_restore_warning' : self.RESTORE_DETAIL_WARNING,
        }


    def list_revisions(self, limit=25, include_restore_state=False):
        query = self.query
        if self.created_field is not None and hasattr(query, 'order_by'):
            query = query.order_by(self.created_field.desc())

        if hasattr(query, 'limit'):
            query = query.limit(limit)

        return [
            self.format_revision(entry, include_restore_state=include_restore_state)
            for entry in query
        ]


    def lookup_revision(self, config_id):
        query = self.query
        if self.id_field is not None and hasattr(query, 'filter'):
            query = query.filter(self.id_field == config_id)

        return query.one()


    def format_revision(self, entry, include_restore_state=False):
        user_row = getattr(entry, 'user', None)
        entry_data = entry.data if isinstance(getattr(entry, 'data', None), dict) else {}
        summary, data_size = self.summarize_config_data(entry_data)

        row = {
            'id'         : entry.id,
            'created'    : self.format_datetime(getattr(entry, 'createDate', None)),
            'user'       : user_row.username if user_row else 'Deleted user',
            'user_id'    : user_row.id if user_row else 'N/A',
            'level'      : entry.level or 'Unknown',
            'encrypted'  : 'Yes' if bool(entry.encrypted) else 'No',
            'note'       : entry.note or 'No note',
            'summary'    : summary,
            'data_size'  : data_size,
        }

        if include_restore_state:
            row['restore_state'] = self.restore_state(entry_data, summary)

        return row


    def restore_state(self, data, summary):
        if data and summary != 'Non-dict payload':
            return 'Likely restore candidate'

        return 'Unavailable'


    def format_datetime(self, value, default='Unknown'):
        if not value:
            return default
        if hasattr(value, 'strftime'):
            return value.strftime('%Y-%m-%d %H:%M:%S')
        return str(value)


    def summarize_config_data(self, data):
        if not isinstance(data, dict):
            if data is None:
                return 'No config snapshot', 'N/A'
            return 'Non-dict payload', 'N/A'

        try:
            import json

            size_bytes = len(json.dumps(data, default=str).encode('utf-8'))
            size_display = '{:.1f} KB'.format(size_bytes / 1024.0)
        except (TypeError, ValueError):
            size_display = 'Unavailable'

        summary = 'Keys: {0:d}'.format(len(data))
        return summary, size_display
