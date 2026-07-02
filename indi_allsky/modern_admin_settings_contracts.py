class ModernAdminNotificationsSettingsContract:
    CONFIG_SECTIONS = (
        {
            'label'       : 'Notification categories',
            'description' : 'Classification metadata used to group notification rows in Classic and Modern notification views.',
            'keys'        : (
                {
                    'key'     : 'category',
                    'source'  : 'IndiAllSkyDbNotificationTable / notification views',
                    'notes'   : 'Notification category shown by Classic and Modern notification surfaces.',
                },
                {
                    'key'     : 'item',
                    'source'  : 'IndiAllSkyDbNotificationTable / notification views',
                    'notes'   : 'Optional item/scope metadata used by Modern filters and detail views.',
                },
            ),
        },
        {
            'label'       : 'Delivery / visibility',
            'description' : 'Read-only notification text and display metadata surfaced to operators.',
            'keys'        : (
                {
                    'key'     : 'notification',
                    'source'  : 'IndiAllSkyDbNotificationTable / notification views',
                    'notes'   : 'Notification message text displayed by list and detail pages.',
                },
                {
                    'key'     : 'createDate',
                    'source'  : 'IndiAllSkyDbNotificationTable / notification views',
                    'notes'   : 'Creation timestamp used for ordering and detail context.',
                },
            ),
        },
        {
            'label'       : 'Acknowledge behavior',
            'description' : 'Acknowledgement metadata and future Safe Action boundary. This page does not acknowledge anything.',
            'keys'        : (
                {
                    'key'     : 'ack',
                    'source'  : 'IndiAllSkyDbNotificationTable / notification views',
                    'notes'   : 'Acknowledgement state shown read-only in Modern views.',
                },
                {
                    'key'     : 'notification.acknowledge',
                    'source'  : 'Modern Safe Action registry/service boundary',
                    'notes'   : 'Service-ready action remains blocked from UI execute pending auth/session/CSRF tests.',
                },
            ),
        },
        {
            'label'       : 'Retention / expiry',
            'description' : 'Notification expiry metadata used to determine visible/current notification records.',
            'keys'        : (
                {
                    'key'     : 'expireDate',
                    'source'  : 'IndiAllSkyDbNotificationTable / notification views',
                    'notes'   : 'Expiry timestamp shown read-only and used by legacy AJAX notification lookup.',
                },
            ),
        },
    )

    PROPOSED_LAYOUT = (
        {
            'label'          : 'Notification categories',
            'purpose'        : 'Group operator messages by category and item before exposing future controls.',
            'source_keys'    : ('category', 'item'),
            'proposed_level' : 'Future Basic / Notifications',
        },
        {
            'label'          : 'Delivery / visibility',
            'purpose'        : 'Separate what operators can see from how notifications are delivered or produced.',
            'source_keys'    : ('notification', 'createDate'),
            'proposed_level' : 'Future Basic / Notifications',
        },
        {
            'label'          : 'Acknowledge behavior',
            'purpose'        : 'Keep acknowledgement state visible while execute remains behind Safe Actions and auth/session/CSRF tests.',
            'source_keys'    : ('ack', 'notification.acknowledge'),
            'proposed_level' : 'Future Advanced / Safe Actions',
        },
        {
            'label'          : 'Retention / expiry',
            'purpose'        : 'Make expiry semantics understandable before any retention or cleanup controls exist.',
            'source_keys'    : ('expireDate',),
            'proposed_level' : 'Future Advanced / Notifications',
        },
    )

    OVERVIEW_CARDS = (
        {
            'label'                      : 'Notification categories',
            'purpose'                    : 'Summarize how notifications are grouped for operators and future settings.',
            'related_fields'             : ('category', 'item'),
            'future_editable_actionable' : 'no from this page',
            'safety_note'                : 'Category metadata is shown as schema evidence only; no rows are loaded here.',
        },
        {
            'label'                      : 'Notification items',
            'purpose'                    : 'Show that notification scope/item values exist without exposing live notification data.',
            'related_fields'             : ('item', 'notification', 'createDate'),
            'future_editable_actionable' : 'no from this page',
            'safety_note'                : 'This page does not query notification rows or expose runtime notification payloads.',
        },
        {
            'label'                      : 'Acknowledge state',
            'purpose'                    : 'Keep acknowledgement visible as a future Safe Action boundary, not as an editor control.',
            'related_fields'             : ('ack', 'notification.acknowledge', 'Modern Safe Action registry/service boundary'),
            'future_editable_actionable' : 'blocked until auth/session/CSRF tests',
            'safety_note'                : 'No acknowledge action is exposed; execute/UI remain blocked.',
        },
        {
            'label'                      : 'Expiry / retention',
            'purpose'                    : 'Document expiry semantics before any retention or cleanup controls exist.',
            'related_fields'             : ('expireDate', 'createDate'),
            'future_editable_actionable' : 'blocked until retention policy exists',
            'safety_note'                : 'This page does not delete, expire, or mutate notification records.',
        },
        {
            'label'                      : 'Delivery / visibility',
            'purpose'                    : 'Separate what operators can see from how notifications are produced or delivered.',
            'related_fields'             : ('notification', 'category', 'Modern /modern-admin/notifications'),
            'future_editable_actionable' : 'yes after delivery policy exists',
            'safety_note'                : 'Delivery behavior and visibility controls are not changed from this page.',
        },
        {
            'label'                      : 'Future notification actions',
            'purpose'                    : 'Reserve product space for future acknowledge/delete controls once Safe Actions are ready.',
            'related_fields'             : ('notification.acknowledge', 'notification.delete', 'audit log', 'permission policy'),
            'future_editable_actionable' : 'blocked',
            'safety_note'                : 'No buttons, forms, AJAX calls, or mutative endpoints are exposed here.',
        },
    )


    def build_context(self, settings_groups):
        return {
            'modern_admin_notifications_settings_group'  : self.find_settings_group(settings_groups, 'notifications'),
            'modern_admin_notifications_overview_cards'  : self.get_overview_cards(),
            'modern_admin_notifications_config_sections' : self.get_config_sections(),
            'modern_admin_notifications_proposed_layout' : self.get_proposed_layout(),
        }


    def find_settings_group(self, settings_groups, group_id):
        for group in settings_groups or tuple():
            if group.get('group_id') == group_id:
                return group

        return None


    def get_overview_cards(self):
        return tuple(
            {
                'label'                      : self.safe_text(row.get('label')),
                'purpose'                    : self.safe_text(row.get('purpose')),
                'related_fields'             : tuple(self.safe_text(field) for field in row.get('related_fields', tuple())),
                'current_status'             : 'not evaluated here',
                'future_editable_actionable' : self.safe_text(row.get('future_editable_actionable')),
                'safety_note'                : self.safe_text(row.get('safety_note')),
            }
            for row in self.OVERVIEW_CARDS
        )


    def get_config_sections(self):
        return tuple(
            {
                'label'       : self.safe_text(section.get('label')),
                'description' : self.safe_text(section.get('description')),
                'key_count'   : len(section.get('keys') or tuple()),
                'keys'        : tuple(
                    {
                        'key'    : self.safe_text(row.get('key')),
                        'source' : self.safe_text(row.get('source')),
                        'notes'  : self.safe_text(row.get('notes')),
                    }
                    for row in section.get('keys', tuple())
                ),
            }
            for section in self.CONFIG_SECTIONS
        )


    def get_proposed_layout(self):
        return tuple(
            {
                'label'          : self.safe_text(row.get('label')),
                'purpose'        : self.safe_text(row.get('purpose')),
                'source_keys'    : tuple(self.safe_text(key) for key in row.get('source_keys', tuple())),
                'proposed_level' : self.safe_text(row.get('proposed_level')),
                'note'           : 'read-only proposal',
            }
            for row in self.PROPOSED_LAYOUT
        )


    def safe_text(self, value):
        if value is None:
            return ''

        return str(value)
