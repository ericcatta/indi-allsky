class ModernAdminStorageSettingsContract:
    CONFIG_SECTIONS = (
        {
            'label'       : 'Storage health',
            'description' : 'Status and threshold metadata for local disk health without performing filesystem checks here.',
            'keys'        : (
                {
                    'key'     : 'HEALTHCHECK__DISK_USAGE',
                    'source'  : 'Classic config form',
                    'notes'   : 'Disk usage warning threshold used by health/status surfaces.',
                },
            ),
        },
        {
            'label'       : 'Local paths / data retention',
            'description' : 'Local storage roots and retention windows that affect image, RAW, FITS, and timelapse product storage.',
            'keys'        : (
                {
                    'key'     : 'VARLIB_FOLDER',
                    'source'  : 'Classic config form',
                    'notes'   : 'Project data root path; high-risk to move without migration planning.',
                },
                {
                    'key'     : 'IMAGE_FOLDER',
                    'source'  : 'Classic config form',
                    'notes'   : 'Image storage folder path.',
                },
                {
                    'key'     : 'IMAGE_EXPORT_FOLDER',
                    'source'  : 'Classic config form',
                    'notes'   : 'RAW export folder path.',
                },
                {
                    'key'     : 'IMAGE_RAW_EXPIRE_DAYS',
                    'source'  : 'Classic config form',
                    'notes'   : 'RAW image retention period.',
                },
                {
                    'key'     : 'IMAGE_FITS_EXPIRE_DAYS',
                    'source'  : 'Classic config form',
                    'notes'   : 'FITS image retention period.',
                },
                {
                    'key'     : 'TIMELAPSE_EXPIRE_DAYS',
                    'source'  : 'Classic config form',
                    'notes'   : 'Timelapse retention period.',
                },
            ),
        },
        {
            'label'       : 'External drives / mount points',
            'description' : 'Drive and mount selection concepts surfaced by Classic and Modern drive manager pages.',
            'keys'        : (
                {
                    'key'     : 'DRIVES_SELECT',
                    'source'  : 'Drive manager form',
                    'notes'   : 'Drive selector metadata; this settings page does not enumerate drives.',
                },
                {
                    'key'     : 'DEVICES_SELECT',
                    'source'  : 'Drive manager form',
                    'notes'   : 'Mount selector metadata; this settings page does not enumerate mounts.',
                },
            ),
        },
        {
            'label'       : 'Backup / maintenance notes',
            'description' : 'Remote backup folder and file transfer storage hooks that influence maintenance planning.',
            'keys'        : (
                {
                    'key'     : 'FILETRANSFER__REMOTE_DB_BACKUP_FOLDER',
                    'source'  : 'Classic config form',
                    'notes'   : 'Remote folder used for database backup publishing.',
                },
            ),
        },
    )

    PROPOSED_LAYOUT = (
        {
            'label'          : 'Storage health',
            'purpose'        : 'Show capacity warnings, thresholds, and status links without live filesystem scans.',
            'source_keys'    : ('HEALTHCHECK__DISK_USAGE',),
            'proposed_level' : 'Future Basic / Storage',
        },
        {
            'label'          : 'Local paths / data retention',
            'purpose'        : 'Group local storage roots and retention windows with clear migration warnings.',
            'source_keys'    : ('VARLIB_FOLDER', 'IMAGE_FOLDER', 'IMAGE_EXPORT_FOLDER', 'IMAGE_RAW_EXPIRE_DAYS', 'IMAGE_FITS_EXPIRE_DAYS', 'TIMELAPSE_EXPIRE_DAYS'),
            'proposed_level' : 'Future Advanced / Storage',
        },
        {
            'label'          : 'External drives / mount points',
            'purpose'        : 'Keep drive and mount concepts visible while leaving mount/unmount actions behind safe controls.',
            'source_keys'    : ('DRIVES_SELECT', 'DEVICES_SELECT'),
            'proposed_level' : 'Future Advanced / Maintenance',
        },
        {
            'label'          : 'Backup / maintenance notes',
            'purpose'        : 'Surface backup-related storage destinations separately from upload credentials and actions.',
            'source_keys'    : ('FILETRANSFER__REMOTE_DB_BACKUP_FOLDER',),
            'proposed_level' : 'Future Developer / Maintenance',
        },
    )

    OVERVIEW_CARDS = (
        {
            'label'           : 'Data folders',
            'purpose'         : 'Identify where local all-sky images and application data conceptually belong.',
            'related_keys'    : ('VARLIB_FOLDER', 'IMAGE_FOLDER'),
            'future_editable' : 'blocked',
            'safety_note'     : 'Do not edit or validate paths here; moving data folders needs migration planning.',
        },
        {
            'label'           : 'Export folders',
            'purpose'         : 'Separate exported RAW/source destinations from normal display-image storage.',
            'related_keys'    : ('IMAGE_EXPORT_FOLDER', 'IMAGE_EXPORT_RAW'),
            'future_editable' : 'blocked',
            'safety_note'     : 'No filesystem access or export action is triggered from this page.',
        },
        {
            'label'           : 'RAW/FITS retention',
            'purpose'         : 'Show source-file retention concepts that affect disk growth and scientific traceability.',
            'related_keys'    : ('IMAGE_RAW_EXPIRE_DAYS', 'IMAGE_FITS_EXPIRE_DAYS'),
            'future_editable' : 'yes',
            'safety_note'     : 'Future editing needs validation and clear source-data loss warnings.',
        },
        {
            'label'           : 'Disk usage policy',
            'purpose'         : 'Expose disk warning thresholds as policy metadata without polling disk state here.',
            'related_keys'    : ('HEALTHCHECK__DISK_USAGE',),
            'future_editable' : 'yes',
            'safety_note'     : 'RPi5-first: status pages may measure disk usage; this settings page does not.',
        },
        {
            'label'           : 'External drives',
            'purpose'         : 'Keep drive and mount point concepts visible while separating them from mount actions.',
            'related_keys'    : ('DRIVES_SELECT', 'DEVICES_SELECT'),
            'future_editable' : 'blocked',
            'safety_note'     : 'Mount/unmount and drive operations remain safe-control or Classic fallback territory.',
        },
        {
            'label'           : 'Remote backup',
            'purpose'         : 'Show backup destination concepts without remote checks or credential exposure.',
            'related_keys'    : ('FILETRANSFER__REMOTE_DB_BACKUP_FOLDER',),
            'future_editable' : 'blocked',
            'safety_note'     : 'Remote operations and credentials require separate upload/provider policy.',
        },
    )


    def build_context(self, settings_groups):
        return {
            'modern_admin_storage_settings_group'  : self.find_settings_group(settings_groups, 'storage_drives'),
            'modern_admin_storage_overview_cards'  : self.get_overview_cards(),
            'modern_admin_storage_config_sections' : self.get_config_sections(),
            'modern_admin_storage_proposed_layout' : self.get_proposed_layout(),
        }


    def find_settings_group(self, settings_groups, group_id):
        for group in settings_groups or tuple():
            if group.get('group_id') == group_id:
                return group

        return None


    def get_overview_cards(self):
        return tuple(
            {
                'label'          : self.safe_text(row.get('label')),
                'purpose'        : self.safe_text(row.get('purpose')),
                'related_keys'   : tuple(self.safe_text(key) for key in row.get('related_keys', tuple())),
                'current_status' : 'not evaluated here',
                'future_editable': self.safe_text(row.get('future_editable')),
                'safety_note'    : self.safe_text(row.get('safety_note')),
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


class ModernAdminCameraProfileSettingsContract:
    CONFIG_SECTIONS = (
        {
            'label'       : 'Profile identity',
            'description' : 'Stable profile identifiers and labels that keep settings scoped to the intended camera profile.',
            'keys'        : (
                {
                    'key'     : 'profile_id',
                    'source'  : 'Modern camera settings profile fields',
                    'notes'   : 'Protected identity field used by Modern camera settings, galleries, tasks, and metadata filters.',
                },
                {
                    'key'     : 'profile_label',
                    'source'  : 'Modern camera settings profile fields',
                    'notes'   : 'Operator-facing profile label/purpose metadata.',
                },
            ),
        },
        {
            'label'       : 'Profile state',
            'description' : 'Read-only state concepts that decide whether a profile participates in capture/runtime selection.',
            'keys'        : (
                {
                    'key'     : 'profile_enabled',
                    'source'  : 'Modern camera settings profile fields',
                    'notes'   : 'Enabled flag used to decide whether a profile can participate in multicamera capture.',
                },
                {
                    'key'     : 'profile_primary',
                    'source'  : 'Modern camera settings profile fields',
                    'notes'   : 'Primary profile marker used by profile-first runtime selection.',
                },
            ),
        },
        {
            'label'       : 'Camera relationship',
            'description' : 'Database camera metadata that links a profile to a physical/logical camera without editing it here.',
            'keys'        : (
                {
                    'key'     : 'db_camera_id',
                    'source'  : 'Modern camera settings DB fields',
                    'notes'   : 'Database camera row identifier shown for relationship clarity.',
                },
                {
                    'key'     : 'db_camera_name',
                    'source'  : 'Modern camera settings DB fields',
                    'notes'   : 'Database camera name associated with the selected profile.',
                },
                {
                    'key'     : 'db_camera_driver',
                    'source'  : 'Modern camera settings DB fields',
                    'notes'   : 'Driver/interface metadata for the associated camera.',
                },
                {
                    'key'     : 'db_camera_status',
                    'source'  : 'Modern camera settings DB fields',
                    'notes'   : 'Read-only camera status metadata surfaced by Modern camera settings.',
                },
            ),
        },
        {
            'label'       : 'Multicamera binding',
            'description' : 'Configuration concepts that preserve camera/profile separation for future settings redesign.',
            'keys'        : (
                {
                    'key'     : 'MULTI_CAMERA.profiles',
                    'source'  : 'Config ownership map / Modern profile resolver',
                    'notes'   : 'Profile collection that must stay profile-first and must not be flattened into global config.',
                },
                {
                    'key'     : 'camera_id / profile_id filters',
                    'source'  : 'Modern media/tasks/metadata views',
                    'notes'   : 'Read-only relationship metadata used across Modern pages to avoid single-camera assumptions.',
                },
            ),
        },
    )

    PROPOSED_LAYOUT = (
        {
            'label'          : 'Active camera',
            'purpose'        : 'Show the camera relationship for the active profile without editing camera binding here.',
            'source_keys'    : ('db_camera_id', 'db_camera_name', 'db_camera_driver', 'db_camera_status'),
            'proposed_level' : 'Future Basic / Camera Profile',
        },
        {
            'label'          : 'Active profile',
            'purpose'        : 'Make profile identity and enabled/primary state visible before exposing any edits.',
            'source_keys'    : ('profile_id', 'profile_enabled', 'profile_primary'),
            'proposed_level' : 'Future Basic / Camera Profile',
        },
        {
            'label'          : 'Profile label / purpose',
            'purpose'        : 'Separate operator-facing label/purpose from stable profile identifiers.',
            'source_keys'    : ('profile_label',),
            'proposed_level' : 'Future Basic / Camera Profile',
        },
        {
            'label'          : 'Profile-camera relationship',
            'purpose'        : 'Keep the camera/profile binding explicit so settings stay profile-first and multicamera-safe.',
            'source_keys'    : ('MULTI_CAMERA.profiles', 'camera_id / profile_id filters'),
            'proposed_level' : 'Future Advanced / Multicamera',
        },
        {
            'label'          : 'Multicamera notes',
            'purpose'        : 'Document constraints that prevent flattening profile-owned fields into global settings.',
            'source_keys'    : ('profile_id', 'MULTI_CAMERA.profiles'),
            'proposed_level' : 'Future Developer / Guardrails',
        },
    )

    OVERVIEW_CARDS = (
        {
            'label'           : 'Active profile',
            'purpose'         : 'Summarize which profile concept will anchor the final Basic camera settings experience.',
            'related_fields'  : ('profile_id', 'profile_enabled', 'profile_primary'),
            'future_editable' : 'blocked until profile edit contract exists',
            'safety_note'     : 'This card does not load or change the active runtime profile.',
        },
        {
            'label'           : 'Profile identity',
            'purpose'         : 'Keep stable profile identifiers separate from operator-facing labels and purpose text.',
            'related_fields'  : ('profile_id', 'profile_label'),
            'future_editable' : 'yes after profile validation policy',
            'safety_note'     : 'Identity changes must preserve existing camera/profile references and metadata filters.',
        },
        {
            'label'           : 'Profile-camera binding',
            'purpose'         : 'Make the camera relationship visible without rebinding profiles from this read-only page.',
            'related_fields'  : ('db_camera_id', 'db_camera_name', 'db_camera_driver', 'MULTI_CAMERA.profiles'),
            'future_editable' : 'blocked until multicamera binding policy exists',
            'safety_note'     : 'Binding edits can affect capture, media routing, tasks, and profile-first configuration.',
        },
        {
            'label'           : 'Multicamera role',
            'purpose'         : 'Show that profiles may participate in multicamera operation without flattening them into global settings.',
            'related_fields'  : ('profile_primary', 'profile_enabled', 'camera_id / profile_id filters'),
            'future_editable' : 'blocked until multicamera role policy exists',
            'safety_note'     : 'Future edits must stay profile-first and must not assume a single camera.',
        },
        {
            'label'           : 'Profile fallback behavior',
            'purpose'         : 'Document future fallback expectations when a profile or camera relationship is unavailable.',
            'related_fields'  : ('profile_enabled', 'db_camera_status', 'MULTI_CAMERA.profiles'),
            'future_editable' : 'no until runtime fallback contract exists',
            'safety_note'     : 'Fallback behavior touches runtime selection and should remain descriptive here.',
        },
        {
            'label'           : 'Future profile editor',
            'purpose'         : 'Reserve space for a later safe editor once validation, audit, rollback, and multicamera rules exist.',
            'related_fields'  : ('profile_id', 'profile_label', 'db_camera_id', 'MULTI_CAMERA.profiles'),
            'future_editable' : 'blocked',
            'safety_note'     : 'No profile editor is exposed from this page.',
        },
    )


    def build_context(self, settings_groups):
        return {
            'modern_admin_camera_profile_settings_group'  : self.find_settings_group(settings_groups, 'camera_profile_identity'),
            'modern_admin_camera_profile_overview_cards'  : self.get_overview_cards(),
            'modern_admin_camera_profile_config_sections' : self.get_config_sections(),
            'modern_admin_camera_profile_proposed_layout' : self.get_proposed_layout(),
        }


    def find_settings_group(self, settings_groups, group_id):
        for group in settings_groups or tuple():
            if group.get('group_id') == group_id:
                return group

        return None


    def get_overview_cards(self):
        return tuple(
            {
                'label'           : self.safe_text(row.get('label')),
                'purpose'         : self.safe_text(row.get('purpose')),
                'related_fields'  : tuple(self.safe_text(field) for field in row.get('related_fields', tuple())),
                'current_status'  : 'not evaluated here',
                'future_editable' : self.safe_text(row.get('future_editable')),
                'safety_note'     : self.safe_text(row.get('safety_note')),
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


class ModernAdminCameraConnectionSettingsContract:
    CONFIG_SECTIONS = (
        {
            'label'       : 'Camera driver / backend',
            'description' : 'Driver/backend selectors that determine how indi-allsky talks to a camera.',
            'keys'        : (
                {
                    'key'     : 'CAMERA_INTERFACE',
                    'source'  : 'Classic config form / Modern camera settings',
                    'notes'   : 'High-impact backend selector for INDI, libcamera, and supported camera interfaces.',
                },
                {
                    'key'     : 'camera_interface',
                    'source'  : 'Modern camera profile fields',
                    'notes'   : 'Profile-scoped connection backend used by Modern Camera Settings.',
                },
            ),
        },
        {
            'label'       : 'INDI connection',
            'description' : 'Connection fields for INDI-based cameras. This page does not contact INDI or test connectivity.',
            'keys'        : (
                {
                    'key'     : 'INDI_SERVER / indi_server',
                    'source'  : 'Classic config form / Modern camera settings',
                    'notes'   : 'INDI host metadata; future UI must keep it profile-aware where profiles are active.',
                },
                {
                    'key'     : 'INDI_PORT / indi_port',
                    'source'  : 'Classic config form / Modern camera settings',
                    'notes'   : 'INDI port metadata with validation in existing Modern camera settings.',
                },
                {
                    'key'     : 'INDI_CAMERA_NAME / indi_camera_name',
                    'source'  : 'Classic config form / Modern camera settings',
                    'notes'   : 'INDI device name binding for the selected camera/profile.',
                },
            ),
        },
        {
            'label'       : 'libcamera identity',
            'description' : 'libcamera identity fields that bind a profile to a local camera interface.',
            'keys'        : (
                {
                    'key'     : 'LIBCAMERA.CAMERA_ID / libcamera_camera_id',
                    'source'  : 'Classic config form / Modern camera settings',
                    'notes'   : 'libcamera device id. This preview does not enumerate cameras or run hardware detection.',
                },
                {
                    'key'     : 'LIBCAMERA.IMAGE_FILE_TYPE / libcamera_image_file_type',
                    'source'  : 'Modern camera settings',
                    'notes'   : 'Optional libcamera image type metadata tied to camera connection behavior.',
                },
            ),
        },
        {
            'label'       : 'Camera row association',
            'description' : 'Read-only database camera metadata that clarifies which camera row a profile maps to.',
            'keys'        : (
                {
                    'key'     : 'db_camera_id',
                    'source'  : 'Modern camera settings DB fields',
                    'notes'   : 'Database camera identifier surfaced for relationship clarity.',
                },
                {
                    'key'     : 'db_camera_name',
                    'source'  : 'Modern camera settings DB fields',
                    'notes'   : 'Database camera name surfaced by Modern camera settings.',
                },
                {
                    'key'     : 'db_camera_driver',
                    'source'  : 'Modern camera settings DB fields',
                    'notes'   : 'Driver metadata for the associated camera row.',
                },
                {
                    'key'     : 'db_camera_status',
                    'source'  : 'Modern camera settings DB fields',
                    'notes'   : 'Status metadata shown read-only by Modern camera settings.',
                },
            ),
        },
        {
            'label'       : 'Failure / fallback metadata',
            'description' : 'Existing fallback concepts that must remain explicit until final Modern connection UX is designed.',
            'keys'        : (
                {
                    'key'     : 'current config fallback',
                    'source'  : 'Modern camera settings / Classic config',
                    'notes'   : 'Single-camera fallback config remains compatibility infrastructure and is not edited here.',
                },
                {
                    'key'     : 'profile read-only state',
                    'source'  : 'Modern camera settings profile resolver',
                    'notes'   : 'Prevents unsafe profile edits; this preview only documents the concept.',
                },
            ),
        },
    )

    PROPOSED_LAYOUT = (
        {
            'label'          : 'Camera driver / backend',
            'purpose'        : 'Make the selected backend clear without hiding whether it is global fallback or profile-owned.',
            'source_keys'    : ('CAMERA_INTERFACE', 'camera_interface'),
            'proposed_level' : 'Future Basic / Camera Connection',
        },
        {
            'label'          : 'Connection status',
            'purpose'        : 'Show status context from existing Modern camera surfaces without doing hardware checks here.',
            'source_keys'    : ('db_camera_status', 'profile read-only state'),
            'proposed_level' : 'Future Basic / Camera Connection',
        },
        {
            'label'          : 'Device identity',
            'purpose'        : 'Group INDI and libcamera identity fields by backend so hardware binding is understandable.',
            'source_keys'    : ('INDI_CAMERA_NAME', 'LIBCAMERA.CAMERA_ID', 'db_camera_name'),
            'proposed_level' : 'Future Advanced / Camera Connection',
        },
        {
            'label'          : 'Multicamera selection',
            'purpose'        : 'Keep camera connection settings aligned with the selected profile and never flatten multicamera ownership.',
            'source_keys'    : ('camera_interface', 'db_camera_id', 'MULTI_CAMERA.profiles'),
            'proposed_level' : 'Future Advanced / Multicamera',
        },
        {
            'label'          : 'Failure / fallback notes',
            'purpose'        : 'Explain what remains compatibility fallback before any final editor or safe action exists.',
            'source_keys'    : ('current config fallback', 'profile read-only state'),
            'proposed_level' : 'Future Developer / Guardrails',
        },
    )

    OVERVIEW_CARDS = (
        {
            'label'           : 'Camera backend',
            'purpose'         : 'Summarize which camera interface family a future final UI should present first.',
            'related_fields'  : ('CAMERA_INTERFACE', 'camera_interface'),
            'future_editable' : 'yes after profile-safe validation',
            'safety_note'     : 'Changing backend can affect capture startup and must remain profile-aware.',
        },
        {
            'label'           : 'INDI connection',
            'purpose'         : 'Group INDI host, port, and device identity without opening sockets or testing hardware here.',
            'related_fields'  : ('INDI_SERVER / indi_server', 'INDI_PORT / indi_port', 'INDI_CAMERA_NAME / indi_camera_name'),
            'future_editable' : 'blocked until connection test policy exists',
            'safety_note'     : 'This card does not contact INDI or validate a live connection.',
        },
        {
            'label'           : 'libcamera identity',
            'purpose'         : 'Describe local libcamera identity fields without enumerating attached cameras.',
            'related_fields'  : ('LIBCAMERA.CAMERA_ID / libcamera_camera_id', 'LIBCAMERA.IMAGE_FILE_TYPE / libcamera_image_file_type'),
            'future_editable' : 'blocked until hardware discovery policy exists',
            'safety_note'     : 'No hardware scan or camera detection is performed by this page.',
        },
        {
            'label'           : 'Database camera identity',
            'purpose'         : 'Keep database camera row identity visible as product context without querying live rows here.',
            'related_fields'  : ('db_camera_id', 'db_camera_name', 'db_camera_driver', 'db_camera_status'),
            'future_editable' : 'no from this page',
            'safety_note'     : 'Database camera identity is shown as static design evidence only.',
        },
        {
            'label'           : 'Multicamera selection',
            'purpose'         : 'Preserve the relationship between connection settings, selected camera, and active profile.',
            'related_fields'  : ('camera_interface', 'db_camera_id', 'MULTI_CAMERA.profiles'),
            'future_editable' : 'blocked until multicamera selection policy exists',
            'safety_note'     : 'Future controls must not flatten multicamera/profile ownership into a single global setting.',
        },
        {
            'label'           : 'Failure / fallback behavior',
            'purpose'         : 'Document how final UI should explain fallback state before exposing connection edits.',
            'related_fields'  : ('current config fallback', 'profile read-only state', 'db_camera_status'),
            'future_editable' : 'blocked until fallback contract exists',
            'safety_note'     : 'Fallback behavior touches runtime capture safety and remains descriptive here.',
        },
    )


    def build_context(self, settings_groups):
        return {
            'modern_admin_camera_connection_settings_group'  : self.find_settings_group(settings_groups, 'camera_connection'),
            'modern_admin_camera_connection_overview_cards'  : self.get_overview_cards(),
            'modern_admin_camera_connection_config_sections' : self.get_config_sections(),
            'modern_admin_camera_connection_proposed_layout' : self.get_proposed_layout(),
        }


    def find_settings_group(self, settings_groups, group_id):
        for group in settings_groups or tuple():
            if group.get('group_id') == group_id:
                return group

        return None


    def get_overview_cards(self):
        return tuple(
            {
                'label'           : self.safe_text(row.get('label')),
                'purpose'         : self.safe_text(row.get('purpose')),
                'related_fields'  : tuple(self.safe_text(field) for field in row.get('related_fields', tuple())),
                'current_status'  : 'not evaluated here',
                'future_editable' : self.safe_text(row.get('future_editable')),
                'safety_note'     : self.safe_text(row.get('safety_note')),
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


class ModernAdminExposureGainSettingsContract:
    CONFIG_SECTIONS = (
        {
            'label'       : 'Manual exposure',
            'description' : 'Exposure limits, defaults, cadence, and timeout fields used by Classic fallback and Modern camera profiles.',
            'keys'        : (
                {
                    'key'     : 'CCD_EXPOSURE_MIN / exposure_min',
                    'source'  : 'Classic config form / Modern camera profile fields',
                    'notes'   : 'Night minimum exposure; profile-owned when multicamera profiles are active.',
                },
                {
                    'key'     : 'CCD_EXPOSURE_MIN_DAY / exposure_min_day',
                    'source'  : 'Classic config form / Modern camera profile fields',
                    'notes'   : 'Day minimum exposure boundary.',
                },
                {
                    'key'     : 'CCD_EXPOSURE_DEF / exposure_default',
                    'source'  : 'Classic config form / Modern camera profile fields',
                    'notes'   : 'Startup/default exposure seed; treated carefully in profile mode.',
                },
                {
                    'key'     : 'CCD_EXPOSURE_MAX / exposure_max',
                    'source'  : 'Classic config form / Modern camera profile fields',
                    'notes'   : 'Maximum exposure cap used by capture cadence and UI refresh timing.',
                },
                {
                    'key'     : 'CCD_EXPOSURE_TIMEOUT / exposure_timeout',
                    'source'  : 'Classic config form / Modern camera profile fields',
                    'notes'   : 'Camera exposure timeout metadata.',
                },
                {
                    'key'     : 'EXPOSURE_PERIOD / exposure_period',
                    'source'  : 'Classic config form / Modern camera profile fields',
                    'notes'   : 'Night capture cadence/period.',
                },
                {
                    'key'     : 'EXPOSURE_PERIOD_DAY / exposure_period_day',
                    'source'  : 'Classic config form / Modern camera profile fields',
                    'notes'   : 'Day capture cadence/period.',
                },
            ),
        },
        {
            'label'       : 'Manual gain',
            'description' : 'Day, night, and moon-mode gain values plus optional gain caps.',
            'keys'        : (
                {
                    'key'     : 'CCD_CONFIG.NIGHT.GAIN / gain_night',
                    'source'  : 'Classic config form / Modern camera profile fields',
                    'notes'   : 'Night gain profile value.',
                },
                {
                    'key'     : 'CCD_CONFIG.MOONMODE.GAIN / gain_moonmode',
                    'source'  : 'Classic config form / Modern camera profile fields',
                    'notes'   : 'Moon mode gain profile value.',
                },
                {
                    'key'     : 'CCD_CONFIG.DAY.GAIN / gain_day',
                    'source'  : 'Classic config form / Modern camera profile fields',
                    'notes'   : 'Day gain profile value.',
                },
                {
                    'key'     : 'GAIN_MAX_DAY / gain_max_day',
                    'source'  : 'Modern camera profile fields',
                    'notes'   : 'Day gain cap used by Auto Gain boundaries.',
                },
                {
                    'key'     : 'GAIN_MAX_NIGHT / gain_max_night',
                    'source'  : 'Modern camera profile fields',
                    'notes'   : 'Night gain cap used by Auto Gain boundaries.',
                },
                {
                    'key'     : 'GAIN_MAX_MOONMODE / gain_max_moonmode',
                    'source'  : 'Modern camera profile fields',
                    'notes'   : 'Moon mode gain cap used by Auto Gain boundaries.',
                },
            ),
        },
        {
            'label'       : 'Profile-specific behavior',
            'description' : 'Profile-owned fields and fallback behavior that must stay separated during redesign.',
            'keys'        : (
                {
                    'key'     : 'profile_id',
                    'source'  : 'Modern camera profile settings',
                    'notes'   : 'Exposure/gain values are scoped to selected profiles when multicamera is enabled.',
                },
                {
                    'key'     : 'MULTI_CAMERA.profiles',
                    'source'  : 'Settings ownership map / Modern profile resolver',
                    'notes'   : 'Profile collection that owns final camera-facing values.',
                },
                {
                    'key'     : 'Global Capture Defaults',
                    'source'  : 'Modern /modern-admin/settings/capture',
                    'notes'   : 'Compatibility fallback only; should not become canonical over profile values.',
                },
            ),
        },
        {
            'label'       : 'Automation relationship',
            'description' : 'Automation flags that influence exposure/gain but remain separate protected settings groups.',
            'keys'        : (
                {
                    'key'     : 'AUTO_EXPOSURE_*',
                    'source'  : 'Modern camera profile fields',
                    'notes'   : 'Auto Exposure relationship only; not edited from this preview.',
                },
                {
                    'key'     : 'AUTO_GAIN_* / CCD_CONFIG.AUTO_GAIN_*',
                    'source'  : 'Classic config form / Modern camera profile fields',
                    'notes'   : 'Auto Gain relationship only; not edited from this preview.',
                },
                {
                    'key'     : 'TARGET_ADU_*',
                    'source'  : 'Classic config form / Modern camera profile fields',
                    'notes'   : 'Auto Exposure/Auto Gain target signal relationship.',
                },
            ),
        },
    )

    PROPOSED_LAYOUT = (
        {
            'label'          : 'Manual exposure',
            'purpose'        : 'Keep min/default/max/timeout/cadence together as profile-owned camera behavior.',
            'source_keys'    : ('CCD_EXPOSURE_*', 'EXPOSURE_PERIOD*', 'exposure_*'),
            'proposed_level' : 'Future Basic / Camera Profile',
        },
        {
            'label'          : 'Manual gain',
            'purpose'        : 'Group day/night/moon gain values and caps without mixing them into sensor or SQM gain.',
            'source_keys'    : ('CCD_CONFIG.*.GAIN', 'gain_day', 'gain_night', 'gain_moonmode', 'GAIN_MAX_*'),
            'proposed_level' : 'Future Basic / Camera Profile',
        },
        {
            'label'          : 'Profile-specific behavior',
            'purpose'        : 'Make clear whether values come from the active profile or global fallback.',
            'source_keys'    : ('profile_id', 'MULTI_CAMERA.profiles', 'Global Capture Defaults'),
            'proposed_level' : 'Future Basic / Camera Profile',
        },
        {
            'label'          : 'Camera/backend constraints',
            'purpose'        : 'Leave room for backend capability warnings without probing hardware from the settings preview.',
            'source_keys'    : ('CAMERA_INTERFACE', 'db_camera_driver', 'capture capabilities'),
            'proposed_level' : 'Future Advanced / Camera Connection',
        },
        {
            'label'          : 'Relationship to Auto Exposure / Auto Gain',
            'purpose'        : 'Show automation dependencies without collapsing manual and automatic controls into one unsafe editor.',
            'source_keys'    : ('AUTO_EXPOSURE_*', 'AUTO_GAIN_*', 'TARGET_ADU_*'),
            'proposed_level' : 'Future Advanced / Automation',
        },
    )

    OVERVIEW_CARDS = (
        {
            'label'           : 'Manual exposure limits',
            'purpose'         : 'Summarize the safe boundaries that constrain manual exposure values.',
            'related_fields'  : ('CCD_EXPOSURE_MIN / exposure_min', 'CCD_EXPOSURE_DEF / exposure_default', 'CCD_EXPOSURE_MAX / exposure_max', 'CCD_EXPOSURE_TIMEOUT / exposure_timeout'),
            'future_editable' : 'yes after profile-safe validation',
            'safety_note'     : 'Future edits must respect camera/backend limits and profile ownership.',
        },
        {
            'label'           : 'Day/night exposure cadence',
            'purpose'         : 'Separate day and night cadence behavior so capture timing stays understandable.',
            'related_fields'  : ('EXPOSURE_PERIOD / exposure_period', 'EXPOSURE_PERIOD_DAY / exposure_period_day', 'CCD_EXPOSURE_MIN_DAY / exposure_min_day'),
            'future_editable' : 'yes after capture cadence validation',
            'safety_note'     : 'Cadence changes can affect capture throughput and should remain profile-aware.',
        },
        {
            'label'           : 'Manual gain profiles',
            'purpose'         : 'Group day, night, and capped gain values as profile-specific camera behavior.',
            'related_fields'  : ('CCD_CONFIG.NIGHT.GAIN / gain_night', 'CCD_CONFIG.DAY.GAIN / gain_day', 'GAIN_MAX_DAY / gain_max_day', 'GAIN_MAX_NIGHT / gain_max_night'),
            'future_editable' : 'yes after gain range validation',
            'safety_note'     : 'Gain edits must not bypass camera capability constraints or Auto Gain boundaries.',
        },
        {
            'label'           : 'Moon mode gain',
            'purpose'         : 'Keep moon-mode gain visible as a separate operating profile instead of hiding it inside night gain.',
            'related_fields'  : ('CCD_CONFIG.MOONMODE.GAIN / gain_moonmode', 'GAIN_MAX_MOONMODE / gain_max_moonmode'),
            'future_editable' : 'yes after moon-mode policy review',
            'safety_note'     : 'Moon-mode gain can affect image quality and automation behavior.',
        },
        {
            'label'           : 'Camera/backend constraints',
            'purpose'         : 'Reserve room for backend capability warnings without probing hardware from this page.',
            'related_fields'  : ('CAMERA_INTERFACE', 'db_camera_driver', 'capture capabilities'),
            'future_editable' : 'blocked until capability policy exists',
            'safety_note'     : 'This page does not check hardware, query cameras, or apply exposure/gain values.',
        },
        {
            'label'           : 'Auto exposure/gain relationship',
            'purpose'         : 'Show that manual boundaries and automation controls are related but remain separate settings groups.',
            'related_fields'  : ('AUTO_EXPOSURE_*', 'AUTO_GAIN_*', 'TARGET_ADU_*', 'CCD_EXPOSURE_*', 'GAIN_MAX_*'),
            'future_editable' : 'blocked until automation editor policy exists',
            'safety_note'     : 'Manual and automatic controls should not be collapsed into one unsafe editor.',
        },
    )


    def build_context(self, settings_groups):
        groups_by_id = {
            group.get('group_id') : group
            for group in settings_groups or tuple()
        }
        exposure_group = groups_by_id.get('exposure')
        gain_group = groups_by_id.get('gain')

        return {
            'modern_admin_exposure_settings_group'       : exposure_group,
            'modern_admin_gain_settings_group'           : gain_group,
            'modern_admin_exposure_gain_settings_groups' : tuple(
                group
                for group in (
                    exposure_group,
                    gain_group,
                )
                if group
            ),
            'modern_admin_exposure_gain_overview_cards'  : self.get_overview_cards(),
            'modern_admin_exposure_gain_config_sections' : self.get_config_sections(),
            'modern_admin_exposure_gain_proposed_layout' : self.get_proposed_layout(),
        }


    def get_overview_cards(self):
        return tuple(
            {
                'label'           : self.safe_text(row.get('label')),
                'purpose'         : self.safe_text(row.get('purpose')),
                'related_fields'  : tuple(self.safe_text(field) for field in row.get('related_fields', tuple())),
                'current_status'  : 'not evaluated here',
                'future_editable' : self.safe_text(row.get('future_editable')),
                'safety_note'     : self.safe_text(row.get('safety_note')),
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
