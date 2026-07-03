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
