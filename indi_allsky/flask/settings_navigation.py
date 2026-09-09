"""Operational destinations for the three Settings entry levels."""
SETTINGS_NAVIGATION = {
    'basic': (
        ('modern_admin_camera_settings_view', 'Camera profiles', 'Connection, exposure, gain, white balance and shared capture cadence.'),
        ('modern_admin_timelapse_settings_view', 'Timelapse', 'Brightness smoothing for generated videos.'),
        ('modern_admin_storage_settings_view', 'Storage', 'Image folders, retention and disk usage warning threshold.'),
        ('modern_admin_notifications_view', 'Notifications', 'Review and acknowledge system messages.'),
    ),
    'advanced': (
        ('modern_admin_analytics_settings_view', 'Analytics', 'Chart metrics, metering regions and sky quality camera settings.'),
        ('modern_admin_acquisition_save_settings_view', 'Acquisition and save', 'Capture output formats, compression and save hooks.'),
        ('modern_admin_fits_source_settings_view', 'FITS and source', 'Source files, headers, retention and upload options.'),
        ('modern_admin_full_settings_view', 'Full Settings', 'Search all shared configuration fields.'),
    ),
    'developer': (
        ('modern_admin_full_settings_view', 'Full Settings', 'Shared configuration, integrations and detailed processing controls.'),
        ('modern_admin_config_history_view', 'Config History', 'Inspect saved revisions and download configuration.'),
        ('modern_admin_config_restore_view', 'Restore Config', 'Validate a saved configuration before restoring it.'),
        ('modern_admin_system_info_view', 'System Info', 'Inspect system and runtime information.'),
    ),
}
