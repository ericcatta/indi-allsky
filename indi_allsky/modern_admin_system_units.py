"""Hybrid policy for INDI control and automatic service activation."""


class ModernAdminSystemUnits:
    specs = (
        ('INDISERVER_SERVICE_NAME', 'INDI Server', 'indiserver_service', ('start', 'stop')),
        ('INDISERVER_TIMER_NAME', 'INDI automatic start', 'indiserver_timer', ('enable', 'disable')),
        ('ALLSKY_TIMER_NAME', 'Capture automatic start', 'indi_allsky_timer', ('enable', 'disable')),
        ('GUNICORN_SERVICE_NAME', 'Web service', 'gunicorn_indi_allsky_service', ('stop',)),
    )

    def __init__(self, config):
        self.config = config

    def rows(self, context):
        return [dict(unit=self.config[key], label=label, commands=commands,
                     active=context.get(prefix + '_activestate', 'Unavailable'),
                     enabled=context.get(prefix + '_unitstate', 'Unavailable'))
                for key, label, prefix, commands in self.specs]

    def handles(self, unit):
        return any(unit == self.config[key] for key, *_ in self.specs)

    def run(self, unit, command, *, authorized, effects):
        if not authorized:
            return {'form_global': ['Administrator access is required.']}, 400
        allowed = next((commands for key, _, _, commands in self.specs
                        if unit == self.config[key]), ())
        if command not in allowed:
            return {'COMMAND_HIDDEN': ['Unhandled command']}, 400
        try:
            effects[command](unit)
        except Exception:
            # A D-Bus disconnect can occur after acceptance. Do not claim failure
            # or retry automatically; require a fresh observation of system state.
            return {'form_global': ['The service request outcome could not be confirmed. Refresh service state before retrying.']}, 503
        return {'success-message': 'Job submitted'}, 200
