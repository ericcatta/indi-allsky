class ModernAdminSettingsContractBase:
    def find_settings_group(self, settings_groups, group_id):
        for group in settings_groups or tuple():
            if group.get('group_id') == group_id:
                return group

        return None


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


class ModernAdminStorageSettingsContract(ModernAdminSettingsContractBase):
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

class ModernAdminCameraProfileSettingsContract(ModernAdminSettingsContractBase):
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


class ModernAdminCameraConnectionSettingsContract(ModernAdminSettingsContractBase):
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


class ModernAdminExposureGainSettingsContract(ModernAdminSettingsContractBase):
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


class ModernAdminAutoExposureGainSettingsContract(ModernAdminSettingsContractBase):
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


class ModernAdminHybridAwbSettingsContract(ModernAdminSettingsContractBase):
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


class ModernAdminAcquisitionSaveSettingsContract(ModernAdminSettingsContractBase):
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


class ModernAdminFitsSourceSettingsContract(ModernAdminSettingsContractBase):
    CONFIG_SECTIONS = (
        {
            'label'       : 'FITS persistence',
            'description' : 'FITS source persistence settings discovered from Classic config and Modern FITS metadata surfaces.',
            'keys'        : (
                {
                    'key'     : 'IMAGE_SAVE_FITS',
                    'source'  : 'Classic config form / Modern FITS metadata pages',
                    'notes'   : 'Primary FITS persistence gate; this preview does not create FITS files.',
                },
                {
                    'key'     : 'IMAGE_SAVE_FITS_COMPRESSED',
                    'source'  : 'Classic config form',
                    'notes'   : 'Compression metadata for persisted FITS records.',
                },
                {
                    'key'     : 'IMAGE_SAVE_FITS_PERIOD',
                    'source'  : 'Classic config form',
                    'notes'   : 'Periodic FITS save interval metadata.',
                },
                {
                    'key'     : 'IMAGE_SAVE_FITS_PRE_DARK',
                    'source'  : 'Classic config form',
                    'notes'   : 'Pre-dark FITS source behavior metadata.',
                },
            ),
        },
        {
            'label'       : 'RAW / source persistence',
            'description' : 'RAW/source export settings that must remain separate from display-image output settings.',
            'keys'        : (
                {
                    'key'     : 'IMAGE_EXPORT_RAW',
                    'source'  : 'Classic config form / Modern RAW metadata pages',
                    'notes'   : 'RAW/source export behavior; no filesystem access is performed here.',
                },
                {
                    'key'     : 'FILETRANSFER__UPLOAD_RAW',
                    'source'  : 'Classic upload config form',
                    'notes'   : 'Remote upload flag for RAW/source products; no remote action is triggered here.',
                },
                {
                    'key'     : 'FILETRANSFER__UPLOAD_FITS / S3UPLOAD__UPLOAD_FITS',
                    'source'  : 'Classic upload config form',
                    'notes'   : 'Remote upload flags for FITS products; shown as static evidence only.',
                },
            ),
        },
        {
            'label'       : 'FITS headers / metadata',
            'description' : 'Static FITS header and image metadata fields that connect source files to scientific context.',
            'keys'        : (
                {
                    'key'     : 'FITSHEADERS__*_KEY / FITSHEADERS__*_VAL',
                    'source'  : 'Classic config form',
                    'notes'   : 'Optional FITS header metadata rows.',
                },
                {
                    'key'     : 'CCD_BIT_DEPTH',
                    'source'  : 'Classic config form / Modern camera settings',
                    'notes'   : 'Source bit-depth metadata used by FITS processing contexts.',
                },
                {
                    'key'     : 'IndiAllSkyDbFitsImageTable metadata',
                    'source'  : 'Modern FITS inspection/detail pages',
                    'notes'   : 'Existing DB metadata surfaced read-only by Modern FITS pages.',
                },
            ),
        },
        {
            'label'       : 'Retention and storage impact',
            'description' : 'Retention and storage placement settings that affect source-data footprint on Raspberry Pi storage.',
            'keys'        : (
                {
                    'key'     : 'IMAGE_FITS_EXPIRE_DAYS',
                    'source'  : 'Classic config form / Storage settings preview',
                    'notes'   : 'FITS retention period metadata.',
                },
                {
                    'key'     : 'IMAGE_RAW_EXPIRE_DAYS',
                    'source'  : 'Classic config form / Storage settings preview',
                    'notes'   : 'RAW/source retention period metadata.',
                },
                {
                    'key'     : 'IMAGE_FOLDER / IMAGE_EXPORT_FOLDER',
                    'source'  : 'Classic config form / Storage settings preview',
                    'notes'   : 'Storage roots shown as key names only; no path is read or scanned here.',
                },
            ),
        },
        {
            'label'       : 'Viewer / file access safety notes',
            'description' : 'Boundaries for future source-file viewers and file access actions.',
            'keys'        : (
                {
                    'key'     : 'Classic conversion route',
                    'source'  : 'Classic FITS viewer',
                    'notes'   : 'Classic conversion route exists; this settings preview never calls it.',
                },
                {
                    'key'     : 'Modern FITS inspection/detail',
                    'source'  : 'Modern read-only metadata pages',
                    'notes'   : 'Safe metadata inspection already exists separately from source-file actions.',
                },
                {
                    'key'     : 'path allowlist / basename-only UI',
                    'source'  : 'Safe Actions and file policy',
                    'notes'   : 'Future file actions require explicit policy before exposure.',
                },
            ),
        },
    )

    PROPOSED_LAYOUT = (
        {
            'label'          : 'FITS persistence',
            'purpose'        : 'Make FITS save mode, compression, period, and pre-dark semantics explicit without creating files.',
            'source_keys'    : ('IMAGE_SAVE_FITS', 'IMAGE_SAVE_FITS_COMPRESSED', 'IMAGE_SAVE_FITS_PERIOD', 'IMAGE_SAVE_FITS_PRE_DARK'),
            'proposed_level' : 'Future Advanced / Scientific Source',
        },
        {
            'label'          : 'RAW/source persistence',
            'purpose'        : 'Keep RAW/source export behavior separate from display-image save formats and remote upload actions.',
            'source_keys'    : ('IMAGE_EXPORT_RAW', 'FILETRANSFER__UPLOAD_RAW', 'FILETRANSFER__UPLOAD_FITS'),
            'proposed_level' : 'Future Advanced / Scientific Source',
        },
        {
            'label'          : 'FITS headers / metadata',
            'purpose'        : 'Group source metadata and FITS headers as scientific context instead of generic config rows.',
            'source_keys'    : ('FITSHEADERS__*', 'CCD_BIT_DEPTH', 'IndiAllSkyDbFitsImageTable'),
            'proposed_level' : 'Future Advanced / Metadata',
        },
        {
            'label'          : 'Retention and storage impact',
            'purpose'        : 'Show source-data storage cost and retention constraints with RPi5-first limits.',
            'source_keys'    : ('IMAGE_FITS_EXPIRE_DAYS', 'IMAGE_RAW_EXPIRE_DAYS', 'IMAGE_FOLDER', 'IMAGE_EXPORT_FOLDER'),
            'proposed_level' : 'Future Advanced / Storage',
        },
        {
            'label'          : 'Scientific Source Layer relationship',
            'purpose'        : 'Preserve source-first semantics so final UI does not reduce explainability or scientific traceability.',
            'source_keys'    : ('ScientificFrame', 'ScientificFrameProvider', 'FITS metadata'),
            'proposed_level' : 'Future Advanced / Scientific Source',
        },
        {
            'label'          : 'Viewer / file access safety notes',
            'purpose'        : 'Keep conversion, preview, and file-access actions outside this read-only settings preview.',
            'source_keys'    : ('Classic FITS viewer', 'Modern FITS metadata inspection', 'Safe file policy'),
            'proposed_level' : 'Future Developer / Safety',
        },
    )

    OVERVIEW_CARDS = (
        {
            'label'           : 'FITS persistence',
            'purpose'         : 'Summarize FITS save policy as scientific source persistence, not ordinary display output.',
            'related_fields'  : ('IMAGE_SAVE_FITS', 'IMAGE_SAVE_FITS_COMPRESSED', 'IMAGE_SAVE_FITS_PERIOD', 'IMAGE_SAVE_FITS_PRE_DARK'),
            'future_editable' : 'blocked until Scientific Source policy is preserved',
            'safety_note'     : 'This page does not create, inspect, convert, or download FITS files.',
        },
        {
            'label'           : 'RAW/source persistence',
            'purpose'         : 'Keep RAW/source export behavior separate from display-image save formats.',
            'related_fields'  : ('IMAGE_EXPORT_RAW', 'FILETRANSFER__UPLOAD_RAW', 'FILETRANSFER__UPLOAD_FITS / S3UPLOAD__UPLOAD_FITS'),
            'future_editable' : 'blocked until source export policy exists',
            'safety_note'     : 'This page does not read source files or trigger remote upload/export behavior.',
        },
        {
            'label'           : 'FITS headers',
            'purpose'         : 'Show FITS header metadata as scientific context rather than generic raw config rows.',
            'related_fields'  : ('FITSHEADERS__*_KEY / FITSHEADERS__*_VAL', 'CCD_BIT_DEPTH', 'IndiAllSkyDbFitsImageTable metadata'),
            'future_editable' : 'yes after metadata validation policy',
            'safety_note'     : 'Header edits must preserve metadata quality and avoid leaking sensitive values.',
        },
        {
            'label'           : 'Upload/export source files',
            'purpose'         : 'Document source-file upload/export flags without running network or filesystem actions.',
            'related_fields'  : ('FILETRANSFER__UPLOAD_RAW', 'FILETRANSFER__UPLOAD_FITS', 'S3UPLOAD__UPLOAD_FITS', 'IMAGE_EXPORT_RAW'),
            'future_editable' : 'blocked until upload/source action policy exists',
            'safety_note'     : 'Remote operations, credential use, and source export actions remain out of scope here.',
        },
        {
            'label'           : 'Retention and storage impact',
            'purpose'         : 'Make source-data footprint visible with Raspberry Pi storage constraints in mind.',
            'related_fields'  : ('IMAGE_FITS_EXPIRE_DAYS', 'IMAGE_RAW_EXPIRE_DAYS', 'IMAGE_FOLDER / IMAGE_EXPORT_FOLDER'),
            'future_editable' : 'yes after retention/storage policy',
            'safety_note'     : 'This page does not scan folders, estimate disk usage, or delete expired files.',
        },
        {
            'label'           : 'Viewer/download safety boundary',
            'purpose'         : 'Keep preview, conversion, and download actions separated from this read-only settings product page.',
            'related_fields'  : ('Classic conversion route', 'Modern FITS inspection/detail', 'path allowlist / basename-only UI'),
            'future_editable' : 'no from this page',
            'safety_note'     : 'No fits2jpeg, file streaming, arbitrary path access, or download link is exposed here.',
        },
    )


    def build_context(self, settings_groups):
        return {
            'modern_admin_fits_source_settings_group'  : self.find_settings_group(settings_groups, 'fits_source_files'),
            'modern_admin_fits_source_overview_cards'  : self.get_overview_cards(),
            'modern_admin_fits_source_config_sections' : self.get_config_sections(),
            'modern_admin_fits_source_proposed_layout' : self.get_proposed_layout(),
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


class ModernAdminAnalyticsSettingsContract(ModernAdminSettingsContractBase):
    CONFIG_SECTIONS = (
        {
            'label'       : 'Charts / Custom Slots',
            'description' : 'Controls which metrics are selected for Classic chart custom slots and their optional display floors.',
            'keys'        : (
                {
                    'key'     : 'CHARTS__CUSTOM_SLOT_*',
                    'source'  : 'Classic config form',
                    'notes'   : 'Custom chart slot metric selectors shown by the Classic config surface.',
                },
                {
                    'key'     : 'CHARTS__CUSTOM_SLOT_*_MIN',
                    'source'  : 'Classic config form',
                    'notes'   : 'Optional minimum bounds for custom chart slots.',
                },
            ),
        },
        {
            'label'       : 'ADU Analytics',
            'description' : 'Defines the brightness sampling area used by operational ADU summaries and related status views.',
            'keys'        : (
                {
                    'key'     : 'ADU_ROI_*',
                    'source'  : 'Classic config form',
                    'notes'   : 'ADU region metadata used by operational brightness analytics.',
                },
                {
                    'key'     : 'ADU_FOV_DIV',
                    'source'  : 'Classic config form',
                    'notes'   : 'Fallback ADU field-of-view division when no ROI is configured.',
                },
            ),
        },
        {
            'label'       : 'SQM Analytics',
            'description' : 'Groups sky quality sampling metadata and camera-SQM sensor settings used by analytics/status surfaces.',
            'keys'        : (
                {
                    'key'     : 'SQM_ROI_*',
                    'source'  : 'Classic config form',
                    'notes'   : 'SQM/star region metadata used by brightness and sky quality summaries.',
                },
                {
                    'key'     : 'SQM_FOV_DIV',
                    'source'  : 'Classic config form',
                    'notes'   : 'Fallback SQM/star field-of-view division when no ROI is configured.',
                },
                {
                    'key'     : 'CAMERA_SQM__*',
                    'source'  : 'Classic config form',
                    'notes'   : 'Camera SQM sensor settings that feed analytics/status surfaces.',
                },
            ),
        },
    )

    PROPOSED_LAYOUT = (
        {
            'label'          : 'Sky brightness / SQM',
            'purpose'        : 'Group sky-quality sampling controls and camera-SQM sensor context in one analytics-oriented area.',
            'source_keys'    : ('SQM_ROI_*', 'SQM_FOV_DIV', 'CAMERA_SQM__*'),
            'proposed_level' : 'Future Advanced / Analytics',
        },
        {
            'label'          : 'Image signal / ADU',
            'purpose'        : 'Keep image brightness sampling controls close to analytics and signal-health reporting.',
            'source_keys'    : ('ADU_ROI_*', 'ADU_FOV_DIV'),
            'proposed_level' : 'Future Advanced / Analytics',
        },
        {
            'label'          : 'Charts / Custom slots',
            'purpose'        : 'Treat custom chart slots as chart composition controls, separate from daily operational settings.',
            'source_keys'    : ('CHARTS__CUSTOM_SLOT_*', 'CHARTS__CUSTOM_SLOT_*_MIN'),
            'proposed_level' : 'Future Developer / Advanced depending on use',
        },
    )

    OVERVIEW_CARDS = (
        {
            'label'           : 'Sky brightness / SQM',
            'purpose'         : 'Describe sky-brightness sampling and sky quality context without computing live SQM values.',
            'related_keys'    : ('SQM_ROI_*', 'SQM_FOV_DIV'),
            'future_editable' : 'yes',
            'safety_note'     : 'Future editing needs validation and clear ROI preview; this page does not run analytics.',
        },
        {
            'label'           : 'Image signal / ADU',
            'purpose'         : 'Describe image-signal sampling used by ADU summaries and quality context.',
            'related_keys'    : ('ADU_ROI_*', 'ADU_FOV_DIV'),
            'future_editable' : 'yes',
            'safety_note'     : 'ROI changes affect analytics interpretation and should stay explainable.',
        },
        {
            'label'           : 'Chart slots',
            'purpose'         : 'Group custom chart slot choices separately from operational measurement definitions.',
            'related_keys'    : ('CHARTS__CUSTOM_SLOT_*', 'CHARTS__CUSTOM_SLOT_*_MIN'),
            'future_editable' : 'yes',
            'safety_note'     : 'Chart composition can become editable after value validation; no chart data is queried here.',
        },
        {
            'label'           : 'ROI / FOV definitions',
            'purpose'         : 'Keep region-of-interest and field-of-view concepts visible as shared analytics geometry.',
            'related_keys'    : ('ADU_ROI_*', 'SQM_ROI_*', 'ADU_FOV_DIV', 'SQM_FOV_DIV'),
            'future_editable' : 'blocked',
            'safety_note'     : 'Final editing needs a visual geometry workflow and camera/profile ownership review.',
        },
        {
            'label'           : 'Camera SQM integration',
            'purpose'         : 'Describe camera-SQM settings as an analytics input without polling sensors or reading config.',
            'related_keys'    : ('CAMERA_SQM__*',),
            'future_editable' : 'blocked',
            'safety_note'     : 'Sensor/provider ownership must be verified before active editing.',
        },
        {
            'label'           : 'Future analytics dashboard',
            'purpose'         : 'Show where analytics configuration should connect to future dashboard/report surfaces.',
            'related_keys'    : ('CHARTS__CUSTOM_SLOT_*', 'ADU_*', 'SQM_*', 'CAMERA_SQM__*'),
            'future_editable' : 'no',
            'safety_note'     : 'Dashboards consume analytics outputs; this settings page does not query or calculate them.',
        },
    )


    def build_context(self, settings_groups):
        return {
            'modern_admin_analytics_settings_group'  : self.find_settings_group(settings_groups, 'analytics'),
            'modern_admin_analytics_overview_cards'  : self.get_overview_cards(),
            'modern_admin_analytics_config_sections' : self.get_config_sections(),
            'modern_admin_analytics_proposed_layout' : self.get_proposed_layout(),
        }


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


class ModernAdminEnvironmentalAwarenessSettingsContract(ModernAdminSettingsContractBase):
    CONFIG_SECTIONS = (
        {
            'label'       : 'Environmental status display',
            'description' : 'Controls where environmental context appears in operator status text and image labels without evaluating live conditions here.',
            'keys'        : (
                {
                    'key'     : 'WEB_STATUS_TEMPLATE',
                    'source'  : 'Classic config defaults / config form',
                    'notes'   : 'Status template can display smoke, aurora, Kp-index, sun, and moon context.',
                },
                {
                    'key'     : 'IMAGE_LABEL_TEMPLATE',
                    'source'  : 'Classic config defaults / config form',
                    'notes'   : 'Image label template can display environmental and sky-context metadata on rendered output.',
                },
            ),
        },
        {
            'label'       : 'Weather / sensor providers',
            'description' : 'Groups external weather provider and station configuration metadata without connecting to network services.',
            'keys'        : (
                {
                    'key'     : 'TEMP_SENSOR__OPENWEATHERMAP_*',
                    'source'  : 'Classic config form / config storage',
                    'notes'   : 'OpenWeatherMap provider metadata; credentials must remain hidden from normal product views.',
                },
                {
                    'key'     : 'TEMP_SENSOR__AMBIENTWEATHER_*',
                    'source'  : 'Classic config form / config storage',
                    'notes'   : 'Ambient Weather provider metadata, including credential and station identity fields.',
                },
                {
                    'key'     : 'TEMP_SENSOR__WEATHERUNDERGROUND_*',
                    'source'  : 'Classic config form / config storage',
                    'notes'   : 'Weather Underground provider metadata when present in Classic configuration.',
                },
            ),
        },
        {
            'label'       : 'Space weather / atmospheric context',
            'description' : 'Documents environmental concepts used by status surfaces without calculating aurora, smoke, or cloud state here.',
            'keys'        : (
                {
                    'key'     : 'smoke_rating / smoke_rating_status',
                    'source'  : 'status data / label templates',
                    'notes'   : 'Smoke context displayed by status and image label templates.',
                },
                {
                    'key'     : 'aurora_* / kpindex_*',
                    'source'  : 'status data / label templates',
                    'notes'   : 'Aurora and space-weather context displayed by status and image label templates.',
                },
                {
                    'key'     : 'sky_condition / cloud_condition / sky_trend',
                    'source'  : 'Modern analytics/status summaries',
                    'notes'   : 'Cloud and sky condition summaries consumed by dashboard/status surfaces.',
                },
            ),
        },
    )

    PROPOSED_LAYOUT = (
        {
            'label'          : 'Status display',
            'purpose'        : 'Keep environmental display templates separate from provider credentials and runtime sensor behavior.',
            'source_keys'    : ('WEB_STATUS_TEMPLATE', 'IMAGE_LABEL_TEMPLATE'),
            'proposed_level' : 'Future Advanced / Environmental Awareness',
        },
        {
            'label'          : 'Weather providers',
            'purpose'        : 'Describe provider configuration ownership without exposing or validating credentials.',
            'source_keys'    : ('TEMP_SENSOR__OPENWEATHERMAP_*', 'TEMP_SENSOR__AMBIENTWEATHER_*', 'TEMP_SENSOR__WEATHERUNDERGROUND_*'),
            'proposed_level' : 'Future Advanced / Environmental Awareness',
        },
        {
            'label'          : 'Environmental evidence',
            'purpose'        : 'Separate environmental facts consumed by Product UI from the providers that generate them.',
            'source_keys'    : ('smoke_rating', 'aurora_*', 'kpindex_*', 'sky_condition', 'cloud_condition'),
            'proposed_level' : 'Future Advanced / Observatory Context',
        },
    )

    OVERVIEW_CARDS = (
        {
            'label'           : 'Display templates',
            'purpose'         : 'Show that environmental context can appear in status text and rendered labels.',
            'related_keys'    : ('WEB_STATUS_TEMPLATE', 'IMAGE_LABEL_TEMPLATE'),
            'future_editable' : 'blocked',
            'safety_note'     : 'Template editing can affect rendered output and should remain outside this contract-only slice.',
        },
        {
            'label'           : 'Weather provider metadata',
            'purpose'         : 'Clarify provider ownership without reading network state or exposing credentials.',
            'related_keys'    : ('TEMP_SENSOR__OPENWEATHERMAP_*', 'TEMP_SENSOR__AMBIENTWEATHER_*', 'TEMP_SENSOR__WEATHERUNDERGROUND_*'),
            'future_editable' : 'blocked',
            'safety_note'     : 'Credentials and provider validation remain Classic fallback until a redaction/write policy exists.',
        },
        {
            'label'           : 'Atmospheric context',
            'purpose'         : 'Keep smoke, cloud, and sky-condition concepts visible as product context.',
            'related_keys'    : ('smoke_rating', 'cloud_condition', 'sky_condition', 'sky_trend'),
            'future_editable' : 'no',
            'safety_note'     : 'This contract does not calculate or refresh environmental observations.',
        },
        {
            'label'           : 'Space-weather context',
            'purpose'         : 'Separate aurora/Kp concepts from future detector or ranking features.',
            'related_keys'    : ('aurora_*', 'kpindex_*'),
            'future_editable' : 'no',
            'safety_note'     : 'This contract does not call external space-weather providers.',
        },
        {
            'label'           : 'Future Observatory connection',
            'purpose'         : 'Prepare environmental awareness for future Observatory context without making it a live health check.',
            'related_keys'    : ('Observatory context', 'status summaries', 'environmental metadata'),
            'future_editable' : 'blocked',
            'safety_note'     : 'Live polling, provider checks, and sensor ownership need dedicated review before UI exposure.',
        },
    )


    def build_context(self, settings_groups):
        return {
            'modern_admin_environmental_awareness_settings_group'  : self.find_settings_group(settings_groups, 'environmental_awareness'),
            'modern_admin_environmental_awareness_overview_cards'  : self.get_overview_cards(),
            'modern_admin_environmental_awareness_config_sections' : self.get_config_sections(),
            'modern_admin_environmental_awareness_proposed_layout' : self.get_proposed_layout(),
        }


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


class ModernAdminMiniTimelapseSettingsContract(ModernAdminSettingsContractBase):
    CONFIG_SECTIONS = (
        {
            'label'       : 'Manual mini-timelapse job',
            'description' : 'Describes the operator-selected window and playback metadata used when a mini timelapse job is prepared manually.',
            'keys'        : (
                {
                    'key'     : 'CAMERA_ID',
                    'source'  : 'Mini timelapse generator form',
                    'notes'   : 'Camera scope for the generated mini-timelapse job.',
                },
                {
                    'key'     : 'IMAGE_ID',
                    'source'  : 'Mini timelapse generator form',
                    'notes'   : 'Anchor frame used to build the pre/post window.',
                },
                {
                    'key'     : 'PRE_SECONDS_SELECT / POST_SECONDS_SELECT',
                    'source'  : 'Mini timelapse generator form',
                    'notes'   : 'Operator-selected time window around the anchor frame.',
                },
                {
                    'key'     : 'FRAMERATE_SELECT',
                    'source'  : 'Mini timelapse generator form',
                    'notes'   : 'Playback speed selected for the generated clip.',
                },
                {
                    'key'     : 'NOTE',
                    'source'  : 'Mini timelapse generator form',
                    'notes'   : 'Operator description stored with the generation job.',
                },
            ),
        },
        {
            'label'       : 'Generation task boundary',
            'description' : 'Documents the task/action metadata boundary without creating, retrying, or mutating generation jobs.',
            'keys'        : (
                {
                    'key'     : 'generateMiniVideo',
                    'source'  : 'Task queue job action',
                    'notes'   : 'Task action used by the existing generator endpoint; this contract does not execute it.',
                },
                {
                    'key'     : 'TaskQueueQueue.VIDEO / TaskQueueState.MANUAL',
                    'source'  : 'Task queue metadata',
                    'notes'   : 'Queue/state metadata for generated mini-timelapse jobs.',
                },
                {
                    'key'     : 'pre_seconds / post_seconds / framerate / note',
                    'source'  : 'Task queue job payload',
                    'notes'   : 'Payload fields forwarded to generation; no validation or execution is performed here.',
                },
            ),
        },
        {
            'label'       : 'Upload / remote naming',
            'description' : 'Groups upload and remote destination metadata for generated mini timelapse outputs without transferring media.',
            'keys'        : (
                {
                    'key'     : 'FILETRANSFER__REMOTE_MINI_VIDEO_NAME',
                    'source'  : 'Classic config form / config defaults',
                    'notes'   : 'Remote filename template for mini-timelapse uploads.',
                },
                {
                    'key'     : 'FILETRANSFER__REMOTE_MINI_VIDEO_FOLDER',
                    'source'  : 'Classic config form / config defaults',
                    'notes'   : 'Remote folder template for mini-timelapse uploads.',
                },
                {
                    'key'     : 'FILETRANSFER__UPLOAD_MINI_VIDEO',
                    'source'  : 'Classic config form / config defaults',
                    'notes'   : 'File-transfer enablement flag for mini-timelapse outputs.',
                },
                {
                    'key'     : 'YOUTUBE__UPLOAD_MINI_VIDEO',
                    'source'  : 'Classic config form / config defaults',
                    'notes'   : 'YouTube upload enablement flag for mini-timelapse outputs.',
                },
            ),
        },
        {
            'label'       : 'Read-only media metadata',
            'description' : 'Connects settings ownership to existing Hybrid mini-timelapse metadata views without browsing or opening media files.',
            'keys'        : (
                {
                    'key'     : 'ModernAdminMiniTimelapseMetadataService',
                    'source'  : 'Hybrid media metadata service',
                    'notes'   : 'Read-only metadata listing already owned by Hybrid; media preview/download behavior is outside this contract.',
                },
                {
                    'key'     : 'IndiAllSkyDbMiniVideoTable',
                    'source'  : 'Generated media metadata table',
                    'notes'   : 'DB metadata source for mini-timelapse rows; this contract does not query it.',
                },
            ),
        },
    )

    PROPOSED_LAYOUT = (
        {
            'label'          : 'Mini-timelapse job',
            'purpose'        : 'Keep the selected camera, anchor image, time window, speed, and note visible as product concepts.',
            'source_keys'    : ('CAMERA_ID', 'IMAGE_ID', 'PRE_SECONDS_SELECT', 'POST_SECONDS_SELECT', 'FRAMERATE_SELECT', 'NOTE'),
            'proposed_level' : 'Future Advanced / Mini Timelapse',
        },
        {
            'label'          : 'Generation boundary',
            'purpose'        : 'Separate generation job metadata from task execution, retry, and queue mutation.',
            'source_keys'    : ('generateMiniVideo', 'TaskQueueQueue.VIDEO', 'TaskQueueState.MANUAL'),
            'proposed_level' : 'Future Developer / Safe Actions',
        },
        {
            'label'          : 'Delivery settings',
            'purpose'        : 'Keep mini-timelapse upload flags and remote naming separate from generation and metadata listing.',
            'source_keys'    : ('FILETRANSFER__REMOTE_MINI_VIDEO_*', 'FILETRANSFER__UPLOAD_MINI_VIDEO', 'YOUTUBE__UPLOAD_MINI_VIDEO'),
            'proposed_level' : 'Future Advanced / Uploads',
        },
        {
            'label'          : 'Metadata listing',
            'purpose'        : 'Use Hybrid-owned metadata services for read-only status while keeping media open/download behavior separate.',
            'source_keys'    : ('ModernAdminMiniTimelapseMetadataService', 'IndiAllSkyDbMiniVideoTable'),
            'proposed_level' : 'Future Advanced / Media Metadata',
        },
    )

    OVERVIEW_CARDS = (
        {
            'label'           : 'Manual job metadata',
            'purpose'         : 'Describe the operator-selected scope for a mini-timelapse without submitting a job.',
            'related_keys'    : ('CAMERA_ID', 'IMAGE_ID', 'PRE_SECONDS_SELECT', 'POST_SECONDS_SELECT', 'FRAMERATE_SELECT', 'NOTE'),
            'future_editable' : 'blocked',
            'safety_note'     : 'Generation remains a mutating task action and is not exposed by this contract.',
        },
        {
            'label'           : 'Generation task',
            'purpose'         : 'Make the task boundary explicit before any future Safe Action ownership work.',
            'related_keys'    : ('generateMiniVideo', 'TaskQueueQueue.VIDEO', 'TaskQueueState.MANUAL'),
            'future_editable' : 'no from settings',
            'safety_note'     : 'No queue insert, retry, purge, or generation behavior is changed.',
        },
        {
            'label'           : 'Upload flags',
            'purpose'         : 'Document file-transfer and YouTube flags that affect mini-timelapse delivery.',
            'related_keys'    : ('FILETRANSFER__UPLOAD_MINI_VIDEO', 'YOUTUBE__UPLOAD_MINI_VIDEO'),
            'future_editable' : 'blocked',
            'safety_note'     : 'Upload credentials, remote paths, and external delivery remain outside this slice.',
        },
        {
            'label'           : 'Remote naming',
            'purpose'         : 'Keep remote filename/folder templates visible as delivery metadata, not filesystem behavior.',
            'related_keys'    : ('FILETRANSFER__REMOTE_MINI_VIDEO_NAME', 'FILETRANSFER__REMOTE_MINI_VIDEO_FOLDER'),
            'future_editable' : 'blocked',
            'safety_note'     : 'No remote path validation, upload, or filesystem access is performed here.',
        },
        {
            'label'           : 'Hybrid metadata ownership',
            'purpose'         : 'Connect settings ownership to the existing read-only Hybrid mini-timelapse metadata service.',
            'related_keys'    : ('ModernAdminMiniTimelapseMetadataService', 'IndiAllSkyDbMiniVideoTable'),
            'future_editable' : 'no',
            'safety_note'     : 'Preview, download, watch routes, and media browsing behavior remain unchanged.',
        },
    )


    def build_context(self, settings_groups):
        return {
            'modern_admin_mini_timelapse_settings_group'  : self.find_settings_group(settings_groups, 'mini_timelapse'),
            'modern_admin_mini_timelapse_overview_cards'  : self.get_overview_cards(),
            'modern_admin_mini_timelapse_config_sections' : self.get_config_sections(),
            'modern_admin_mini_timelapse_proposed_layout' : self.get_proposed_layout(),
        }


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


class ModernAdminNotificationsSettingsContract(ModernAdminSettingsContractBase):
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
