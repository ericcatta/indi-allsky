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
