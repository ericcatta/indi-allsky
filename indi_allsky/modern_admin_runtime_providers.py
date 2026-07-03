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
