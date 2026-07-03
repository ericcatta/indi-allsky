from datetime import datetime
from datetime import timezone


class ModernAdminServiceStatusProvider:
    """Hybrid-owned read boundary for Modern/Admin service status."""

    def __init__(self, status_adapter=None):
        self.status_adapter = status_adapter


    def get_service_status(self, service_name='indi-allsky.service'):
        if not self.status_adapter:
            return self.unknown_status(service_name, 'No service status adapter configured')

        try:
            adapter_result = self.status_adapter(service_name)
        except Exception as e:
            return self.unknown_status(service_name, str(e))

        return self.status_from_adapter_result(adapter_result)


    def status_from_adapter_result(self, adapter_result):
        output = self.adapter_output(adapter_result)
        state = self.state_from_output(output)
        running = state == 'active'

        if running:
            label = '● Running'
            tone = 'good'
            toggle_command = 'stop'
            toggle_label = 'Stop Capture'
        elif state == 'failed':
            label = '● Failed'
            tone = 'danger'
            toggle_command = 'start'
            toggle_label = 'Start Capture'
        else:
            label = '○ Stopped'
            tone = 'muted'
            toggle_command = 'start'
            toggle_label = 'Start Capture'

        return {
            'state'          : state,
            'running'        : running,
            'label'          : label,
            'tone'           : tone,
            'toggle_command' : toggle_command,
            'toggle_label'   : toggle_label,
            'output'         : output,
        }


    def unknown_status(self, service_name, output=''):
        return {
            'state'          : 'unknown',
            'running'        : False,
            'label'          : '? Unknown',
            'tone'           : 'muted',
            'toggle_command' : 'start',
            'toggle_label'   : 'Start Capture',
            'output'         : str(output or ''),
        }


    def adapter_output(self, adapter_result):
        if adapter_result is None:
            return ''

        if isinstance(adapter_result, dict):
            return str(adapter_result.get('output') or '').strip()

        return str(adapter_result).strip()


    def state_from_output(self, output):
        return (output or '').strip().split('\n')[0].strip().lower() or 'unknown'


class ModernAdminCameraRuntimeMetadataProvider:
    """Hybrid-owned camera runtime summary for Modern/Admin shell metadata."""

    def get_runtime_status(
        self,
        multi_camera_enabled=False,
        profile_configs=None,
        recent_camera_ids=None,
        recent_camera_labels=None,
        current_camera=None,
    ):
        profile_configs = profile_configs or []
        enabled_profiles = [p for p in profile_configs if p.get('enabled', False)]
        recent_camera_ids = [camera_id for camera_id in (recent_camera_ids or []) if camera_id]
        recent_camera_labels = [str(label) for label in (recent_camera_labels or []) if label]

        if multi_camera_enabled:
            if len(recent_camera_ids) >= 2:
                label = 'Runtime: Multi-camera active'
                detail = self.format_camera_list(recent_camera_labels)
                if detail:
                    label = '{0:s} · {1:s}'.format(label, detail)

                return {
                    'label' : label,
                    'tone'  : 'good',
                }

            if len(recent_camera_ids) == 1:
                label = 'Runtime: Restart required or only one camera active'
                detail = self.format_camera_list(recent_camera_labels)
                if detail:
                    label = '{0:s} · {1:s}'.format(label, detail)

                return {
                    'label' : label,
                    'tone'  : 'warn',
                }

            profile_labels = self.profile_labels(enabled_profiles)
            label = 'Config: Multi-camera enabled · Restart may be required'
            detail = self.format_camera_list(profile_labels)
            if detail:
                label = '{0:s} · {1:s}'.format(label, detail)

            return {
                'label' : label,
                'tone'  : 'warn',
            }

        if len(recent_camera_ids) >= 2:
            label = 'Runtime: Multi-camera still active · Config disabled, restart may be required'
            detail = self.format_camera_list(recent_camera_labels)
            if detail:
                label = '{0:s} · {1:s}'.format(label, detail)

            return {
                'label' : label,
                'tone'  : 'warn',
            }

        if recent_camera_labels:
            label = 'Capture: Single camera · {0:s}'.format(recent_camera_labels[0])
        elif current_camera is not None:
            label = 'Capture: Single camera · {0:s}'.format(self.camera_label(current_camera))
        else:
            label = 'Capture: Single camera'

        return {
            'label' : label,
            'tone'  : 'muted',
        }


    def camera_label(self, camera):
        return str(
            getattr(camera, 'friendlyName', None)
            or getattr(camera, 'name', None)
            or getattr(camera, 'driver', None)
            or 'Unknown camera'
        )


    def profile_labels(self, enabled_profiles):
        profile_labels = list()
        for profile_config in enabled_profiles:
            label = profile_config.get('label') \
                or profile_config.get('camera_name') \
                or profile_config.get('profile_id') \
                or profile_config.get('camera_interface')
            if label:
                profile_labels.append(str(label))

        return profile_labels


    def format_camera_list(self, camera_labels):
        camera_labels = [str(label) for label in (camera_labels or []) if label]
        if not camera_labels:
            return ''

        if len(camera_labels) <= 2:
            return ' + '.join(camera_labels)

        return '{0:s} + {1:d} more'.format(' + '.join(camera_labels[:2]), len(camera_labels) - 2)


class ModernAdminWatchdogStatusSummaryProvider:
    """Hybrid-owned capture/watchdog summary shaping for Modern/Admin runtime."""

    STATE_RUNNING = 'running'
    STATE_IDLE = 'idle'
    STATE_PAUSED = 'paused'
    STATE_ERROR = 'error'
    STATE_UNKNOWN = 'unknown'

    ALLOWED_STATES = frozenset((
        STATE_RUNNING,
        STATE_IDLE,
        STATE_PAUSED,
        STATE_ERROR,
        STATE_UNKNOWN,
    ))

    def get_current_capture_metadata(
        self,
        status_code=None,
        status_map=None,
        watchdog_age_seconds=None,
        local_camera=True,
        focus_mode=False,
        capture_pause=False,
        daytime_capture=True,
        daytime_capture_save=True,
        camera_label='Camera not evaluated yet',
    ):
        raw_state = dict(status_map or {}).get(status_code, self.STATE_UNKNOWN)
        capture_state = self.resolve_capture_state(
            raw_state=raw_state,
            capture_pause=capture_pause,
            local_camera=local_camera,
            focus_mode=focus_mode,
        )

        return {
            'capture_state': capture_state,
            'is_acquiring': capture_state == self.STATE_RUNNING,
            'camera_label': str(camera_label or 'Camera not evaluated yet'),
            'policy_label': self.policy_label(
                capture_pause=capture_pause,
                local_camera=local_camera,
                focus_mode=focus_mode,
                daytime_capture=daytime_capture,
                daytime_capture_save=daytime_capture_save,
            ),
            'source_status': self.source_status(watchdog_age_seconds),
            'watchdog_age_seconds': watchdog_age_seconds,
        }


    def resolve_capture_state(self, raw_state, capture_pause=False, local_camera=True, focus_mode=False):
        if capture_pause:
            return self.STATE_PAUSED

        if not local_camera:
            return self.STATE_UNKNOWN

        if focus_mode:
            return self.STATE_IDLE

        if raw_state in self.ALLOWED_STATES:
            return raw_state

        return self.STATE_UNKNOWN


    def policy_label(
        self,
        capture_pause=False,
        local_camera=True,
        focus_mode=False,
        daytime_capture=True,
        daytime_capture_save=True,
    ):
        if capture_pause:
            return 'Capture intentionally paused.'

        if not local_camera:
            return 'Remote camera mode; local capture state is not authoritative.'

        if focus_mode:
            return 'Focus mode active; normal capture status is not evaluated.'

        if not daytime_capture:
            return 'Daytime capture disabled by camera policy.'

        if daytime_capture and not daytime_capture_save:
            return 'Daytime capture enabled, but daytime frame saving is disabled.'

        return 'Capture policy allows normal acquisition.'


    def source_status(self, watchdog_age_seconds):
        if watchdog_age_seconds is None:
            return 'Persisted capture status read; watchdog age not evaluated.'

        if not isinstance(watchdog_age_seconds, (int, float)):
            return 'Persisted capture status read; watchdog age unavailable.'

        if watchdog_age_seconds > 600:
            return 'Persisted capture watchdog is stale.'

        return 'Persisted capture status and watchdog are available.'


class ModernAdminCurrentCaptureMetadataRepository:
    """Adapter exposing provider metadata through the Product repository contract."""

    def __init__(self, metadata=None):
        self.metadata = dict(metadata or {})


    def get_current_capture_metadata(self):
        return dict(self.metadata)


class ModernAdminCaptureHealthSummaryProvider:
    """Hybrid-owned per-camera/profile capture health summary shaping."""

    DEFAULT_EXPECTED_INTERVAL_SECONDS = 45
    DEFAULT_EXPOSURE_TIMEOUT_SECONDS = 330
    MIN_STALE_AFTER_SECONDS = 60

    def get_capture_health_summary(
        self,
        profile_configs=None,
        latest_frames=None,
        current_camera=None,
        now=None,
        default_expected_interval_seconds=DEFAULT_EXPECTED_INTERVAL_SECONDS,
        default_exposure_timeout_seconds=DEFAULT_EXPOSURE_TIMEOUT_SECONDS,
    ):
        now = self.normalize_now(now)
        latest_frame_map = self.latest_frame_map(latest_frames)
        targets = self.capture_targets(
            profile_configs=profile_configs,
            current_camera=current_camera,
            default_expected_interval_seconds=default_expected_interval_seconds,
            default_exposure_timeout_seconds=default_exposure_timeout_seconds,
        )

        camera_health = [
            self.target_health(target, latest_frame_map.get(target['camera_id']), now)
            for target in targets
        ]

        return {
            'status'        : self.summary_status(camera_health),
            'tone'          : self.summary_tone(camera_health),
            'camera_health' : camera_health,
            'source_status' : self.source_status(camera_health),
        }


    def capture_targets(
        self,
        profile_configs=None,
        current_camera=None,
        default_expected_interval_seconds=DEFAULT_EXPECTED_INTERVAL_SECONDS,
        default_exposure_timeout_seconds=DEFAULT_EXPOSURE_TIMEOUT_SECONDS,
    ):
        targets = list()
        for profile_config in profile_configs or []:
            if not profile_config.get('enabled', False):
                continue

            camera_id = self.normalize_camera_id(
                profile_config.get('camera_id')
                or profile_config.get('camera_db_id')
                or profile_config.get('db_camera_id')
            )
            profile_id = self.safe_text(profile_config.get('profile_id') or profile_config.get('id'))
            label = self.safe_text(
                profile_config.get('label')
                or profile_config.get('camera_name')
                or profile_config.get('name')
                or profile_id
                or camera_id
                or 'Camera not evaluated yet'
            )
            expected_interval = self.positive_float(
                profile_config.get('expected_interval_seconds')
                or profile_config.get('capture_interval')
                or profile_config.get('exposure_period')
                or self.nested_value(profile_config, ('exposure', 'period')),
                default_expected_interval_seconds,
            )
            exposure_timeout = self.positive_float(
                profile_config.get('exposure_timeout')
                or self.nested_value(profile_config, ('exposure', 'timeout')),
                default_exposure_timeout_seconds,
            )
            stale_after = self.positive_float(
                profile_config.get('stale_after_seconds'),
                max(expected_interval * 3, self.MIN_STALE_AFTER_SECONDS),
            )

            targets.append({
                'profile_id'                : profile_id,
                'camera_id'                 : camera_id,
                'label'                     : label,
                'expected_interval_seconds' : expected_interval,
                'exposure_timeout_seconds'  : exposure_timeout,
                'stale_after_seconds'       : stale_after,
            })

        if targets:
            return targets

        camera_id = self.normalize_camera_id(getattr(current_camera, 'id', None))
        if current_camera is None and not camera_id:
            return []

        return [{
            'profile_id'                : '',
            'camera_id'                 : camera_id,
            'label'                     : ModernAdminCameraRuntimeMetadataProvider().camera_label(current_camera),
            'expected_interval_seconds' : self.positive_float(None, default_expected_interval_seconds),
            'exposure_timeout_seconds'  : self.positive_float(None, default_exposure_timeout_seconds),
            'stale_after_seconds'       : max(self.positive_float(None, default_expected_interval_seconds) * 3, self.MIN_STALE_AFTER_SECONDS),
        }]


    def target_health(self, target, latest_frame, now):
        timestamp = self.frame_timestamp(latest_frame)
        age_seconds = self.age_seconds(timestamp, now)
        status = self.health_status(age_seconds, target['stale_after_seconds'], latest_frame)

        return {
            'profile_id'                : target['profile_id'],
            'camera_id'                 : target['camera_id'],
            'label'                     : target['label'],
            'status'                    : status,
            'tone'                      : self.health_tone(status),
            'status_label'              : self.health_label(status, age_seconds),
            'latest_frame_timestamp'    : self.format_timestamp(timestamp),
            'latest_frame_age_seconds'  : age_seconds,
            'expected_interval_seconds' : target['expected_interval_seconds'],
            'stale_after_seconds'       : target['stale_after_seconds'],
            'exposure_timeout_seconds'  : target['exposure_timeout_seconds'],
        }


    def health_status(self, age_seconds, stale_after_seconds, latest_frame):
        if latest_frame and bool(latest_frame.get('busy', False)):
            return 'busy'

        if age_seconds is None:
            return 'missing'

        if age_seconds > stale_after_seconds:
            return 'stale'

        return 'ok'


    def health_tone(self, status):
        return {
            'ok'      : 'good',
            'busy'    : 'warn',
            'stale'   : 'warn',
            'missing' : 'muted',
        }.get(status, 'muted')


    def health_label(self, status, age_seconds):
        if status == 'ok':
            return 'Latest frame is fresh.'
        if status == 'busy':
            return 'Capture is busy.'
        if status == 'stale':
            return 'Latest frame is stale.'
        if status == 'missing':
            return 'No latest frame metadata.'
        return 'Capture health not evaluated.'


    def summary_status(self, camera_health):
        statuses = [item['status'] for item in camera_health]
        if not statuses:
            return 'unknown'
        if len(set(statuses)) == 1:
            return statuses[0]
        if all(status == 'ok' for status in statuses):
            return 'ok'
        if any(status in ('stale', 'busy') for status in statuses):
            return 'mixed'
        return 'mixed'


    def summary_tone(self, camera_health):
        status = self.summary_status(camera_health)
        return {
            'ok'      : 'good',
            'stale'   : 'warn',
            'busy'    : 'warn',
            'mixed'   : 'warn',
            'missing' : 'muted',
            'unknown' : 'muted',
        }.get(status, 'muted')


    def source_status(self, camera_health):
        if not camera_health:
            return 'No camera/profile metadata available.'
        return 'Capture health is based on latest frame metadata only.'


    def latest_frame_map(self, latest_frames):
        frame_map = dict()
        for frame in latest_frames or []:
            camera_id = self.normalize_camera_id(frame.get('camera_id'))
            if camera_id:
                frame_map[camera_id] = dict(frame)
        return frame_map


    def frame_timestamp(self, latest_frame):
        if not latest_frame:
            return None

        timestamp = latest_frame.get('timestamp') or latest_frame.get('createDate')
        if isinstance(timestamp, datetime):
            return timestamp

        return None


    def age_seconds(self, timestamp, now):
        if timestamp is None:
            return None

        if timestamp.tzinfo is not None and now.tzinfo is None:
            timestamp = timestamp.astimezone(timezone.utc).replace(tzinfo=None)
        if timestamp.tzinfo is None and now.tzinfo is not None:
            now = now.astimezone(timezone.utc).replace(tzinfo=None)

        return max(0, int((now - timestamp).total_seconds()))


    def format_timestamp(self, timestamp):
        if timestamp is None:
            return None
        return timestamp.isoformat()


    def normalize_now(self, now):
        if isinstance(now, datetime):
            return now
        return datetime.now()


    def normalize_camera_id(self, camera_id):
        if camera_id is None:
            return ''
        return str(camera_id).strip()


    def safe_text(self, value):
        if value is None:
            return ''
        return str(value)


    def positive_float(self, value, default):
        try:
            value = float(value)
        except (TypeError, ValueError):
            value = float(default)

        if value <= 0:
            return float(default)

        return value


    def nested_value(self, mapping, keys):
        value = mapping
        for key in keys:
            if not isinstance(value, dict):
                return None
            value = value.get(key)
        return value


class ModernAdminLocationMetadataProvider:
    """Hybrid-owned read boundary for observatory/GPS location metadata."""

    def get_location_metadata(self, camera=None, config=None):
        config = config if isinstance(config, dict) else {}
        camera_latitude = self.number_or_none(getattr(camera, 'latitude', None))
        camera_longitude = self.number_or_none(getattr(camera, 'longitude', None))
        camera_elevation = self.number_or_none(getattr(camera, 'elevation', None))
        camera_has_location = camera_latitude is not None and camera_longitude is not None

        latitude = self.first_number(
            camera_latitude,
            config.get('LOCATION_LATITUDE'),
        )
        longitude = self.first_number(
            camera_longitude,
            config.get('LOCATION_LONGITUDE'),
        )
        elevation = self.first_number(
            camera_elevation,
            config.get('LOCATION_ELEVATION'),
        )
        gps_enabled = bool(config.get('GPS_ENABLE', False))

        status = 'available' if latitude is not None and longitude is not None else 'unknown'

        return {
            'status'          : status,
            'tone'            : 'good' if status == 'available' else 'muted',
            'source'          : 'camera_metadata' if camera_has_location else 'config',
            'location_name'   : self.safe_text(config.get('LOCATION_NAME')),
            'latitude'        : latitude,
            'longitude'       : longitude,
            'elevation'       : elevation,
            'gps_enabled'     : gps_enabled,
            'gps_status_label': 'GPS enabled' if gps_enabled else 'GPS disabled',
            'status_label'    : self.status_label(status, gps_enabled),
        }


    def status_label(self, status, gps_enabled):
        if status == 'available':
            if gps_enabled:
                return 'Location metadata available; GPS may update it.'
            return 'Location metadata available from saved configuration.'

        if gps_enabled:
            return 'GPS enabled, but location metadata is unavailable.'

        return 'Location metadata unavailable.'


    def first_number(self, *values):
        for value in values:
            number = self.number_or_none(value)
            if number is not None:
                return number
        return None


    def number_or_none(self, value):
        if value is None:
            return None

        try:
            return float(value)
        except (TypeError, ValueError):
            return None


    def safe_text(self, value):
        if value is None:
            return ''
        return str(value)
