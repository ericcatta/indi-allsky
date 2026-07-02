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


class ModernAdminAutoExposureGainSettingsContract:
    CONFIG_SECTIONS = (
        {
            'label'       : 'Target ADU',
            'description' : 'Signal targets and allowed deviation used by automatic exposure/gain controllers.',
            'keys'        : (
                {
                    'key'     : 'TARGET_ADU / target_adu',
                    'source'  : 'Classic config form / Modern camera profile fields',
                    'notes'   : 'Night target signal level for automation decisions.',
                },
                {
                    'key'     : 'TARGET_ADU_DAY / target_adu_day',
                    'source'  : 'Classic config form / Modern camera profile fields',
                    'notes'   : 'Day target signal level for automation decisions.',
                },
                {
                    'key'     : 'TARGET_ADU_DEV / target_adu_dev',
                    'source'  : 'Classic config form / Modern camera profile fields',
                    'notes'   : 'Night allowed deviation from target.',
                },
                {
                    'key'     : 'TARGET_ADU_DEV_DAY / target_adu_dev_day',
                    'source'  : 'Classic config form / Modern camera profile fields',
                    'notes'   : 'Day allowed deviation from target.',
                },
            ),
        },
        {
            'label'       : 'Auto Exposure',
            'description' : 'Enablement and metering strategy for automatic exposure decisions.',
            'keys'        : (
                {
                    'key'     : 'AUTO_EXPOSURE_ENABLED / auto_exposure_enabled',
                    'source'  : 'Modern camera profile fields',
                    'notes'   : 'Protected Auto Exposure gate. This preview does not enable or apply it.',
                },
                {
                    'key'     : 'AUTO_EXPOSURE_METERING_MODE / auto_exposure_metering_mode',
                    'source'  : 'Modern camera profile fields',
                    'notes'   : 'Per-camera metering strategy for the controller.',
                },
                {
                    'key'     : 'CCD_EXPOSURE_* / exposure_*',
                    'source'  : 'Manual Exposure settings',
                    'notes'   : 'Manual exposure boundaries that constrain automatic exposure behavior.',
                },
            ),
        },
        {
            'label'       : 'Auto Gain',
            'description' : 'Enablement and levels for automatic gain decisions.',
            'keys'        : (
                {
                    'key'     : 'CCD_CONFIG.AUTO_GAIN_ENABLE / auto_gain_enable',
                    'source'  : 'Classic config form / Modern camera profile fields',
                    'notes'   : 'Legacy/global Auto Gain gate and profile-aware equivalent.',
                },
                {
                    'key'     : 'AUTO_GAIN_DAY / auto_gain_day',
                    'source'  : 'Modern camera profile fields',
                    'notes'   : 'Day Auto Gain gate.',
                },
                {
                    'key'     : 'AUTO_GAIN_NIGHT / auto_gain_night',
                    'source'  : 'Modern camera profile fields',
                    'notes'   : 'Night Auto Gain gate.',
                },
                {
                    'key'     : 'AUTO_GAIN_MOONMODE / auto_gain_moonmode',
                    'source'  : 'Modern camera profile fields',
                    'notes'   : 'Moon mode Auto Gain gate.',
                },
                {
                    'key'     : 'AUTO_GAIN_LEVELS / auto_gain_levels',
                    'source'  : 'Classic config form / Modern camera profile fields',
                    'notes'   : 'Step/level metadata used by Auto Gain proposals.',
                },
            ),
        },
        {
            'label'       : 'Gain limits',
            'description' : 'Manual gain caps that bound automatic gain behavior.',
            'keys'        : (
                {
                    'key'     : 'GAIN_MAX_DAY / gain_max_day',
                    'source'  : 'Modern camera profile fields',
                    'notes'   : 'Maximum day gain Auto Gain may use.',
                },
                {
                    'key'     : 'GAIN_MAX_NIGHT / gain_max_night',
                    'source'  : 'Modern camera profile fields',
                    'notes'   : 'Maximum night gain Auto Gain may use.',
                },
                {
                    'key'     : 'GAIN_MAX_MOONMODE / gain_max_moonmode',
                    'source'  : 'Modern camera profile fields',
                    'notes'   : 'Maximum moon mode gain Auto Gain may use.',
                },
                {
                    'key'     : 'CCD_CONFIG.*.GAIN / gain_*',
                    'source'  : 'Manual Gain settings',
                    'notes'   : 'Manual gain values that interact with gain caps and validation.',
                },
            ),
        },
        {
            'label'       : 'Profile-specific behavior',
            'description' : 'Profile ownership and fallback boundaries that keep automation multicamera-safe.',
            'keys'        : (
                {
                    'key'     : 'profile_id',
                    'source'  : 'Modern camera profile settings',
                    'notes'   : 'Automation settings are scoped to selected profiles when multicamera is enabled.',
                },
                {
                    'key'     : 'MULTI_CAMERA.profiles',
                    'source'  : 'Settings ownership map / Modern profile resolver',
                    'notes'   : 'Profile collection that owns final automation values.',
                },
                {
                    'key'     : 'Global Capture Defaults',
                    'source'  : 'Modern /modern-admin/settings/capture',
                    'notes'   : 'Compatibility fallback only; not canonical over profile-specific automation.',
                },
            ),
        },
    )

    PROPOSED_LAYOUT = (
        {
            'label'          : 'Target ADU',
            'purpose'        : 'Show target signal and deviation controls as the common goal shared by Auto Exposure and Auto Gain.',
            'source_keys'    : ('TARGET_ADU', 'TARGET_ADU_DAY', 'TARGET_ADU_DEV', 'TARGET_ADU_DEV_DAY'),
            'proposed_level' : 'Future Basic / Automation',
        },
        {
            'label'          : 'Exposure limits',
            'purpose'        : 'Keep automatic exposure bounded by manual min/default/max/timeout values.',
            'source_keys'    : ('AUTO_EXPOSURE_*', 'CCD_EXPOSURE_*', 'exposure_*'),
            'proposed_level' : 'Future Advanced / Automation',
        },
        {
            'label'          : 'Gain limits',
            'purpose'        : 'Keep automatic gain bounded by manual gain and gain cap values.',
            'source_keys'    : ('AUTO_GAIN_*', 'GAIN_MAX_*', 'CCD_CONFIG.*.GAIN'),
            'proposed_level' : 'Future Advanced / Automation',
        },
        {
            'label'          : 'Day/night behavior',
            'purpose'        : 'Separate day, night, and moon-mode automation gates instead of flattening them into one toggle.',
            'source_keys'    : ('*_DAY', '*_NIGHT', '*_MOONMODE'),
            'proposed_level' : 'Future Basic / Camera Profile',
        },
        {
            'label'          : 'Profile-specific behavior',
            'purpose'        : 'Keep automation profile-first and multicamera-safe.',
            'source_keys'    : ('profile_id', 'MULTI_CAMERA.profiles', 'Global Capture Defaults'),
            'proposed_level' : 'Future Basic / Camera Profile',
        },
        {
            'label'          : 'Relationship to manual Exposure / Gain',
            'purpose'        : 'Make manual limits and automation gates visibly related without editing either from this preview.',
            'source_keys'    : ('Manual Exposure / Gain', 'AUTO_EXPOSURE_*', 'AUTO_GAIN_*'),
            'proposed_level' : 'Future Advanced / Automation',
        },
    )

    OVERVIEW_CARDS = (
        {
            'label'           : 'Target ADU strategy',
            'purpose'         : 'Summarize the signal target strategy shared by Auto Exposure and Auto Gain.',
            'related_fields'  : ('TARGET_ADU / target_adu', 'TARGET_ADU_DEV / target_adu_dev', 'AUTO_EXPOSURE_*', 'AUTO_GAIN_*'),
            'future_editable' : 'yes after automation validation policy',
            'safety_note'     : 'Future edits must remain profile-aware and must not apply runtime exposure/gain decisions from this page.',
        },
        {
            'label'           : 'Day/night targets',
            'purpose'         : 'Keep day and night target values visible as separate automation behaviors.',
            'related_fields'  : ('TARGET_ADU / target_adu', 'TARGET_ADU_DAY / target_adu_day', 'TARGET_ADU_DEV / target_adu_dev', 'TARGET_ADU_DEV_DAY / target_adu_dev_day'),
            'future_editable' : 'yes after day/night automation policy',
            'safety_note'     : 'Day/night target changes can affect capture quality and must be bounded by profile settings.',
        },
        {
            'label'           : 'Exposure control limits',
            'purpose'         : 'Show how Auto Exposure is bounded by manual exposure limits and metering strategy.',
            'related_fields'  : ('AUTO_EXPOSURE_ENABLED / auto_exposure_enabled', 'AUTO_EXPOSURE_METERING_MODE / auto_exposure_metering_mode', 'CCD_EXPOSURE_* / exposure_*'),
            'future_editable' : 'blocked until controller safety policy exists',
            'safety_note'     : 'This page does not enable Auto Exposure or change exposure controller state.',
        },
        {
            'label'           : 'Gain control limits',
            'purpose'         : 'Show Auto Gain enablement and gain caps as a bounded automation system.',
            'related_fields'  : ('CCD_CONFIG.AUTO_GAIN_ENABLE / auto_gain_enable', 'AUTO_GAIN_DAY / auto_gain_day', 'AUTO_GAIN_NIGHT / auto_gain_night', 'GAIN_MAX_*'),
            'future_editable' : 'blocked until controller safety policy exists',
            'safety_note'     : 'This page does not enable Auto Gain or change camera gain values.',
        },
        {
            'label'           : 'Moon mode behavior',
            'purpose'         : 'Keep moon-mode automation visible as a separate operating mode.',
            'related_fields'  : ('AUTO_GAIN_MOONMODE / auto_gain_moonmode', 'GAIN_MAX_MOONMODE / gain_max_moonmode', 'CCD_CONFIG.MOONMODE.GAIN / gain_moonmode'),
            'future_editable' : 'yes after moon-mode automation policy',
            'safety_note'     : 'Moon-mode automation must remain explicit because it affects image signal and quality.',
        },
        {
            'label'           : 'Manual override relationship',
            'purpose'         : 'Make the relationship between manual Exposure/Gain and automation controls clear without merging them.',
            'related_fields'  : ('Manual Exposure / Gain', 'CCD_EXPOSURE_*', 'CCD_CONFIG.*.GAIN', 'AUTO_EXPOSURE_*', 'AUTO_GAIN_*'),
            'future_editable' : 'blocked until override semantics exist',
            'safety_note'     : 'Manual and automatic controls should not be collapsed into one unsafe editor.',
        },
    )


    def build_context(self, settings_groups):
        groups_by_id = {
            group.get('group_id') : group
            for group in settings_groups or tuple()
        }
        auto_exposure_group = groups_by_id.get('auto_exposure')
        auto_gain_group = groups_by_id.get('auto_gain')

        return {
            'modern_admin_auto_exposure_settings_group'       : auto_exposure_group,
            'modern_admin_auto_gain_settings_group'           : auto_gain_group,
            'modern_admin_auto_exposure_gain_settings_groups' : tuple(
                group
                for group in (
                    auto_exposure_group,
                    auto_gain_group,
                )
                if group
            ),
            'modern_admin_auto_exposure_gain_overview_cards'  : self.get_overview_cards(),
            'modern_admin_auto_exposure_gain_config_sections' : self.get_config_sections(),
            'modern_admin_auto_exposure_gain_proposed_layout' : self.get_proposed_layout(),
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


class ModernAdminHybridAwbSettingsContract:
    CONFIG_SECTIONS = (
        {
            'label'       : 'Hybrid AWB mode / strategy',
            'description' : 'Modern Hybrid Controller fields that select processing mode and AWB apply behavior.',
            'keys'        : (
                {
                    'key'     : 'PROCESSING_MODE / awb.mode',
                    'source'  : 'Modern camera settings Hybrid Controller',
                    'notes'   : 'Profile-aware processing mode used by the Hybrid controller.',
                },
                {
                    'key'     : 'HYBRID.AWB.APPLY_MODE / awb.apply_mode',
                    'source'  : 'Modern camera settings Hybrid Controller',
                    'notes'   : 'Controls whether AWB is auto, capture-driver, postprocess RGB, or disabled.',
                },
            ),
        },
        {
            'label'       : 'libcamera AWB backend',
            'description' : 'Capture-side AWB controls for libcamera profiles. This page does not apply driver values.',
            'keys'        : (
                {
                    'key'     : 'LIBCAMERA.AWB / libcamera_awb',
                    'source'  : 'Classic config form / Modern camera profile fields',
                    'notes'   : 'Night libcamera AWB mode fallback/profile value.',
                },
                {
                    'key'     : 'LIBCAMERA.AWB_DAY / libcamera_awb_day',
                    'source'  : 'Classic config form / Modern camera profile fields',
                    'notes'   : 'Day libcamera AWB mode fallback/profile value.',
                },
                {
                    'key'     : 'LIBCAMERA.AWB_ENABLE / libcamera_awb_enable',
                    'source'  : 'Classic config form / Modern camera profile fields',
                    'notes'   : 'Night libcamera AWB enable gate.',
                },
                {
                    'key'     : 'LIBCAMERA.AWB_ENABLE_DAY / libcamera_awb_enable_day',
                    'source'  : 'Classic config form / Modern camera profile fields',
                    'notes'   : 'Day libcamera AWB enable gate.',
                },
                {
                    'key'     : 'LIBCAMERA.AWB_MODE / libcamera_awb_mode',
                    'source'  : 'Modern camera profile fields',
                    'notes'   : 'libcamera AWB strategy; fixed mode requires explicit gains.',
                },
                {
                    'key'     : 'LIBCAMERA.AWB_RED_GAIN / libcamera_awb_red_gain',
                    'source'  : 'Modern camera profile fields',
                    'notes'   : 'Capture-side red gain used only when supported and explicitly configured.',
                },
                {
                    'key'     : 'LIBCAMERA.AWB_BLUE_GAIN / libcamera_awb_blue_gain',
                    'source'  : 'Modern camera profile fields',
                    'notes'   : 'Capture-side blue gain used only when supported and explicitly configured.',
                },
            ),
        },
        {
            'label'       : 'Post-process RGB / legacy white balance',
            'description' : 'Postprocess RGB fields that remain separate from capture-driver AWB.',
            'keys'        : (
                {
                    'key'     : 'AUTO_WB / auto_wb',
                    'source'  : 'Classic config form / Modern camera profile fields',
                    'notes'   : 'Legacy night postprocess auto white balance gate.',
                },
                {
                    'key'     : 'AUTO_WB_DAY / auto_wb_day',
                    'source'  : 'Classic config form / Modern camera profile fields',
                    'notes'   : 'Legacy day postprocess auto white balance gate.',
                },
                {
                    'key'     : 'WBR_FACTOR* / wbr_factor*',
                    'source'  : 'Classic config form / Modern camera profile fields',
                    'notes'   : 'Manual red multipliers for night/day postprocess white balance.',
                },
                {
                    'key'     : 'WBG_FACTOR* / wbg_factor*',
                    'source'  : 'Classic config form / Modern camera profile fields',
                    'notes'   : 'Manual green multipliers for night/day postprocess white balance.',
                },
                {
                    'key'     : 'WBB_FACTOR* / wbb_factor*',
                    'source'  : 'Classic config form / Modern camera profile fields',
                    'notes'   : 'Manual blue multipliers for night/day postprocess white balance.',
                },
            ),
        },
        {
            'label'       : 'Backend constraints',
            'description' : 'Capability and fallback concepts used by the Hybrid AWB controller.',
            'keys'        : (
                {
                    'key'     : 'camera_interface',
                    'source'  : 'Modern camera settings capabilities',
                    'notes'   : 'Determines whether capture-driver AWB is supported.',
                },
                {
                    'key'     : 'capture_driver / postprocess_rgb / disabled',
                    'source'  : 'Hybrid AWB apply mode choices',
                    'notes'   : 'Apply-mode choices exposed by Modern camera settings, not executed from this preview.',
                },
            ),
        },
        {
            'label'       : 'Profile-specific color behavior',
            'description' : 'Profile ownership and image-quality relationship for camera-specific color pipelines.',
            'keys'        : (
                {
                    'key'     : 'profile_id',
                    'source'  : 'Modern camera profile settings',
                    'notes'   : 'AWB settings must remain profile-aware because sensors and color pipelines differ.',
                },
                {
                    'key'     : 'profile.awb',
                    'source'  : 'Modern camera profile config',
                    'notes'   : 'Profile-scoped AWB block used by Modern Camera Settings.',
                },
                {
                    'key'     : 'image quality / color pipeline',
                    'source'  : 'Settings ownership map',
                    'notes'   : 'Relationship to final image quality; this page is descriptive only.',
                },
            ),
        },
    )

    PROPOSED_LAYOUT = (
        {
            'label'          : 'AWB mode / strategy',
            'purpose'        : 'Show Hybrid AWB mode and apply strategy as the product concept, not as raw scattered keys.',
            'source_keys'    : ('PROCESSING_MODE', 'HYBRID.AWB.APPLY_MODE', 'profile.awb'),
            'proposed_level' : 'Future Basic / Camera Profile',
        },
        {
            'label'          : 'Day/night behavior',
            'purpose'        : 'Keep day and night color behavior visible without flattening separate profile values.',
            'source_keys'    : ('LIBCAMERA.AWB_DAY', 'AUTO_WB_DAY', 'WBR/WBG/WBB *_DAY'),
            'proposed_level' : 'Future Advanced / Hybrid AWB',
        },
        {
            'label'          : 'Camera/backend constraints',
            'purpose'        : 'Explain capture-driver and postprocess availability without probing hardware from the preview.',
            'source_keys'    : ('camera_interface', 'capture_driver', 'postprocess_rgb', 'disabled'),
            'proposed_level' : 'Future Advanced / Camera Connection',
        },
        {
            'label'          : 'Profile-specific behavior',
            'purpose'        : 'Keep AWB settings profile-first and multicamera-safe because sensors differ.',
            'source_keys'    : ('profile_id', 'profile.awb', 'MULTI_CAMERA.profiles'),
            'proposed_level' : 'Future Basic / Camera Profile',
        },
        {
            'label'          : 'Relationship to image quality',
            'purpose'        : 'Connect AWB strategy to color quality and processing without introducing image processing controls here.',
            'source_keys'    : ('AUTO_WB*', 'WBR/WBG/WBB*', 'LIBCAMERA.AWB_*'),
            'proposed_level' : 'Future Advanced / Quality',
        },
    )

    OVERVIEW_CARDS = (
        {
            'label'           : 'AWB strategy',
            'purpose'         : 'Summarize the Hybrid AWB product mode and whether color is handled at capture, postprocess, or disabled.',
            'related_fields'  : ('PROCESSING_MODE / awb.mode', 'HYBRID.AWB.APPLY_MODE / awb.apply_mode', 'profile.awb'),
            'future_editable' : 'yes after AWB validation policy',
            'safety_note'     : 'Future edits must remain profile-aware and must not apply AWB from this page.',
        },
        {
            'label'           : 'libcamera AWB controls',
            'purpose'         : 'Group capture-driver AWB enablement, mode, and fixed gains without contacting libcamera.',
            'related_fields'  : ('LIBCAMERA.AWB / libcamera_awb', 'LIBCAMERA.AWB_ENABLE / libcamera_awb_enable', 'LIBCAMERA.AWB_MODE / libcamera_awb_mode', 'LIBCAMERA.AWB_RED_GAIN / libcamera_awb_red_gain', 'LIBCAMERA.AWB_BLUE_GAIN / libcamera_awb_blue_gain'),
            'future_editable' : 'blocked until camera capability policy exists',
            'safety_note'     : 'This page does not probe hardware or apply driver AWB values.',
        },
        {
            'label'           : 'Manual RGB factors',
            'purpose'         : 'Keep postprocess RGB factors visible as a separate manual color path.',
            'related_fields'  : ('WBR_FACTOR* / wbr_factor*', 'WBG_FACTOR* / wbg_factor*', 'WBB_FACTOR* / wbb_factor*', 'AUTO_WB / auto_wb'),
            'future_editable' : 'yes after image-processing policy',
            'safety_note'     : 'Manual RGB factors can affect image quality and should remain separate from capture-driver AWB.',
        },
        {
            'label'           : 'Day/night color behavior',
            'purpose'         : 'Show day and night color settings as distinct profile behavior instead of flattening them.',
            'related_fields'  : ('LIBCAMERA.AWB_DAY / libcamera_awb_day', 'LIBCAMERA.AWB_ENABLE_DAY / libcamera_awb_enable_day', 'AUTO_WB_DAY / auto_wb_day', 'WBR/WBG/WBB *_DAY'),
            'future_editable' : 'yes after day/night AWB policy',
            'safety_note'     : 'Day/night AWB choices must not override profile-specific color behavior silently.',
        },
        {
            'label'           : 'Profile-specific AWB',
            'purpose'         : 'Make AWB ownership explicit because camera sensors and profiles may need different color pipelines.',
            'related_fields'  : ('profile_id', 'profile.awb', 'MULTI_CAMERA.profiles', 'camera_interface'),
            'future_editable' : 'blocked until profile AWB editor policy exists',
            'safety_note'     : 'Future controls must stay profile-first and multicamera-safe.',
        },
        {
            'label'           : 'Image quality relationship',
            'purpose'         : 'Connect AWB strategy to final color quality without introducing processing controls here.',
            'related_fields'  : ('image quality / color pipeline', 'AUTO_WB*', 'WBR/WBG/WBB*', 'LIBCAMERA.AWB_*'),
            'future_editable' : 'no from this page',
            'safety_note'     : 'This page does not process images, recalculate color, or change quality outputs.',
        },
    )


    def build_context(self, settings_groups):
        return {
            'modern_admin_hybrid_awb_settings_group'  : self.find_settings_group(settings_groups, 'hybrid_awb'),
            'modern_admin_hybrid_awb_overview_cards'  : self.get_overview_cards(),
            'modern_admin_hybrid_awb_config_sections' : self.get_config_sections(),
            'modern_admin_hybrid_awb_proposed_layout' : self.get_proposed_layout(),
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


class ModernAdminAcquisitionSaveSettingsContract:
    CONFIG_SECTIONS = (
        {
            'label'       : 'Capture cadence',
            'description' : 'Timing and cadence keys that shape when frames are acquired without changing capture behavior here.',
            'keys'        : (
                {
                    'key'     : 'EXPOSURE_PERIOD / exposure_period',
                    'source'  : 'Classic config form / Modern camera profile fields',
                    'notes'   : 'Night capture cadence metadata.',
                },
                {
                    'key'     : 'EXPOSURE_PERIOD_DAY / exposure_period_day',
                    'source'  : 'Classic config form / Modern camera profile fields',
                    'notes'   : 'Day capture cadence metadata.',
                },
                {
                    'key'     : 'CCD_EXPOSURE_TIMEOUT / exposure_timeout',
                    'source'  : 'Classic config form / Modern camera profile fields',
                    'notes'   : 'Capture timeout boundary; not changed from this preview.',
                },
            ),
        },
        {
            'label'       : 'Day/night acquisition behavior',
            'description' : 'Capture mode fields that differ by day, night, and moon-mode profile behavior.',
            'keys'        : (
                {
                    'key'     : 'CCD_CONFIG.*.BINNING / binning_*',
                    'source'  : 'Classic config form / Modern camera profile fields',
                    'notes'   : 'Day, night, and moon-mode binning values.',
                },
                {
                    'key'     : 'CCD_BIT_DEPTH / bit_depth',
                    'source'  : 'Classic config form / Modern camera settings',
                    'notes'   : 'Camera bit depth metadata used by capture and FITS processing.',
                },
                {
                    'key'     : 'DAYTIME_CAPTURE / night/day capture gates',
                    'source'  : 'Classic config form',
                    'notes'   : 'Acquisition mode gates remain static evidence here.',
                },
            ),
        },
        {
            'label'       : 'Save JPEG/PNG behavior',
            'description' : 'Display-image output format and compression settings used by Classic and Modern media surfaces.',
            'keys'        : (
                {
                    'key'     : 'IMAGE_FILE_TYPE',
                    'source'  : 'Classic config form',
                    'notes'   : 'Primary display image file type.',
                },
                {
                    'key'     : 'IMAGE_FILE_COMPRESSION__JPG',
                    'source'  : 'Classic config form',
                    'notes'   : 'JPEG compression quality metadata.',
                },
                {
                    'key'     : 'IMAGE_FILE_COMPRESSION__PNG',
                    'source'  : 'Classic config form',
                    'notes'   : 'PNG compression level metadata.',
                },
                {
                    'key'     : 'LIBCAMERA__IMAGE_FILE_TYPE* / PYCURL_CAMERA__IMAGE_FILE_TYPE',
                    'source'  : 'Classic config form',
                    'notes'   : 'Backend-specific display image type overrides.',
                },
            ),
        },
        {
            'label'       : 'Save RAW/FITS/source behavior',
            'description' : 'Scientific/source persistence keys. This page does not create, convert, inspect, or download files.',
            'keys'        : (
                {
                    'key'     : 'IMAGE_SAVE_FITS',
                    'source'  : 'Classic config form / Modern FITS metadata pages',
                    'notes'   : 'FITS persistence gate; protected by scientific-source guardrails.',
                },
                {
                    'key'     : 'IMAGE_SAVE_FITS_COMPRESSED',
                    'source'  : 'Classic config form',
                    'notes'   : 'FITS compression metadata.',
                },
                {
                    'key'     : 'IMAGE_SAVE_FITS_PERIOD',
                    'source'  : 'Classic config form',
                    'notes'   : 'Periodic FITS persistence interval.',
                },
                {
                    'key'     : 'IMAGE_EXPORT_RAW',
                    'source'  : 'Classic config form / Modern RAW metadata pages',
                    'notes'   : 'RAW/source export setting; no filesystem scan is performed here.',
                },
                {
                    'key'     : 'FITSHEADERS__*',
                    'source'  : 'Classic config form',
                    'notes'   : 'Static FITS header metadata candidates.',
                },
            ),
        },
        {
            'label'       : 'Retention / storage impact',
            'description' : 'Retention and storage-impact keys that connect acquisition outputs to Storage / Drives.',
            'keys'        : (
                {
                    'key'     : 'IMAGE_FOLDER',
                    'source'  : 'Classic config form',
                    'notes'   : 'Image storage root; listed as key evidence only, not read from disk.',
                },
                {
                    'key'     : 'IMAGE_RAW_EXPIRE_DAYS',
                    'source'  : 'Classic config form',
                    'notes'   : 'RAW/source retention period.',
                },
                {
                    'key'     : 'IMAGE_FITS_EXPIRE_DAYS',
                    'source'  : 'Classic config form',
                    'notes'   : 'FITS retention period.',
                },
                {
                    'key'     : 'IMAGE_SAVE_HOOK_*',
                    'source'  : 'Classic config form',
                    'notes'   : 'Pre/post save hook metadata; execution remains outside this preview.',
                },
            ),
        },
    )

    PROPOSED_LAYOUT = (
        {
            'label'          : 'Capture cadence',
            'purpose'        : 'Group exposure period and timeout concepts as profile-owned acquisition behavior.',
            'source_keys'    : ('EXPOSURE_PERIOD', 'EXPOSURE_PERIOD_DAY', 'CCD_EXPOSURE_TIMEOUT'),
            'proposed_level' : 'Future Advanced / Acquisition',
        },
        {
            'label'          : 'Day/night acquisition behavior',
            'purpose'        : 'Keep day, night, and moon-mode acquisition differences visible without changing capture state.',
            'source_keys'    : ('CCD_CONFIG.*.BINNING', 'CCD_BIT_DEPTH', 'DAYTIME_CAPTURE'),
            'proposed_level' : 'Future Advanced / Camera Profile',
        },
        {
            'label'          : 'Save JPEG/PNG behavior',
            'purpose'        : 'Separate display-image format/compression choices from scientific source persistence.',
            'source_keys'    : ('IMAGE_FILE_TYPE', 'IMAGE_FILE_COMPRESSION__JPG', 'IMAGE_FILE_COMPRESSION__PNG'),
            'proposed_level' : 'Future Advanced / Output Formats',
        },
        {
            'label'          : 'Save RAW/FITS/source behavior',
            'purpose'        : 'Treat source files as scientific/output policy, not as ordinary image display settings.',
            'source_keys'    : ('IMAGE_SAVE_FITS*', 'IMAGE_EXPORT_RAW', 'FITSHEADERS__*'),
            'proposed_level' : 'Future Advanced / Scientific Source',
        },
        {
            'label'          : 'Retention / storage impact',
            'purpose'        : 'Show storage cost and retention relationships without scanning the filesystem.',
            'source_keys'    : ('IMAGE_FOLDER', 'IMAGE_RAW_EXPIRE_DAYS', 'IMAGE_FITS_EXPIRE_DAYS', 'IMAGE_SAVE_HOOK_*'),
            'proposed_level' : 'Future Advanced / Storage',
        },
        {
            'label'          : 'Relationship to Scientific Source Layer',
            'purpose'        : 'Preserve FITS/RAW/source semantics so final UI does not degrade protected scientific work.',
            'source_keys'    : ('Scientific Source Layer', 'FITS metadata', 'RAW/source exports'),
            'proposed_level' : 'Future Advanced / Scientific Source',
        },
    )

    OVERVIEW_CARDS = (
        {
            'label'           : 'Capture cadence',
            'purpose'         : 'Summarize timing controls that shape how often frames are acquired.',
            'related_fields'  : ('EXPOSURE_PERIOD / exposure_period', 'EXPOSURE_PERIOD_DAY / exposure_period_day', 'CCD_EXPOSURE_TIMEOUT / exposure_timeout'),
            'future_editable' : 'yes after cadence validation policy',
            'safety_note'     : 'Future edits can affect capture load and should remain profile-aware.',
        },
        {
            'label'           : 'Day/night acquisition',
            'purpose'         : 'Keep day, night, and moon-mode acquisition behavior visible as separate operating contexts.',
            'related_fields'  : ('DAYTIME_CAPTURE / night/day capture gates', 'CCD_CONFIG.*.BINNING / binning_*', 'profile_id'),
            'future_editable' : 'yes after day/night capture policy',
            'safety_note'     : 'This page does not start capture, pause capture, or change acquisition behavior.',
        },
        {
            'label'           : 'Binning / bit depth',
            'purpose'         : 'Show sensor output shape settings as acquisition metadata rather than generic display options.',
            'related_fields'  : ('CCD_CONFIG.*.BINNING / binning_*', 'CCD_BIT_DEPTH / bit_depth'),
            'future_editable' : 'blocked until camera capability policy exists',
            'safety_note'     : 'Binning and bit depth may be camera/backend constrained and are not applied here.',
        },
        {
            'label'           : 'JPEG/PNG output',
            'purpose'         : 'Group display-image file type and compression choices separately from source persistence.',
            'related_fields'  : ('IMAGE_FILE_TYPE', 'IMAGE_FILE_COMPRESSION__JPG', 'IMAGE_FILE_COMPRESSION__PNG', 'LIBCAMERA__IMAGE_FILE_TYPE* / PYCURL_CAMERA__IMAGE_FILE_TYPE'),
            'future_editable' : 'yes after output-format validation',
            'safety_note'     : 'This page does not save files, rewrite images, or inspect output folders.',
        },
        {
            'label'           : 'FITS/RAW source output',
            'purpose'         : 'Keep scientific/source persistence visible as a protected output policy.',
            'related_fields'  : ('IMAGE_SAVE_FITS', 'IMAGE_SAVE_FITS_COMPRESSED', 'IMAGE_SAVE_FITS_PERIOD', 'IMAGE_EXPORT_RAW', 'FITSHEADERS__*'),
            'future_editable' : 'blocked until Scientific Source policy is preserved',
            'safety_note'     : 'This page does not create, convert, inspect, download, or delete FITS/RAW files.',
        },
        {
            'label'           : 'Hooks / post-save behavior',
            'purpose'         : 'Document pre/post-save hook settings as high-impact behavior that needs policy before editing.',
            'related_fields'  : ('IMAGE_SAVE_HOOK_*', 'IMAGE_FOLDER', 'IMAGE_RAW_EXPIRE_DAYS', 'IMAGE_FITS_EXPIRE_DAYS'),
            'future_editable' : 'blocked until hook safety policy exists',
            'safety_note'     : 'Hooks may execute external behavior and are not invoked or edited from this page.',
        },
    )


    def build_context(self, settings_groups):
        groups_by_id = {
            group.get('group_id') : group
            for group in settings_groups or tuple()
        }
        image_acquisition_group = groups_by_id.get('image_acquisition')
        image_save_formats_group = groups_by_id.get('image_save_formats')

        return {
            'modern_admin_image_acquisition_settings_group'    : image_acquisition_group,
            'modern_admin_image_save_formats_settings_group'   : image_save_formats_group,
            'modern_admin_acquisition_save_settings_groups'    : tuple(
                group
                for group in (
                    image_acquisition_group,
                    image_save_formats_group,
                )
                if group
            ),
            'modern_admin_acquisition_save_overview_cards'     : self.get_overview_cards(),
            'modern_admin_acquisition_save_config_sections'    : self.get_config_sections(),
            'modern_admin_acquisition_save_proposed_layout'    : self.get_proposed_layout(),
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
