"""Hybrid upgrade service observation and serialized command submission."""
from contextlib import contextmanager
from datetime import datetime
import fcntl
import os
import tempfile

import psutil
from .modern_safe_action import ModernAdminUpgradeCommandBoundary


@contextmanager
def upgrade_lock():
    path = os.path.join(tempfile.gettempdir(), 'indi-allsky-upgrade-{0}.lock'.format(os.getuid()))
    fd = os.open(path, os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
    try:
        if os.fstat(fd).st_uid != os.getuid():
            raise OSError('Upgrade lock owner mismatch')
        os.fchmod(fd, 0o600)
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        yield
    finally:
        os.close(fd)


class UpgradeRuntime:
    def __init__(self, unit):
        self.unit = unit

    def manager(self):
        import dbus
        bus = dbus.SessionBus()
        manager = dbus.Interface(bus.get_object('org.freedesktop.systemd1', '/org/freedesktop/systemd1'),
                                 'org.freedesktop.systemd1.Manager')
        return bus, manager

    def properties(self):
        import dbus
        bus, manager = self.manager()
        path = manager.LoadUnit(self.unit, timeout=5)
        interface = dbus.Interface(bus.get_object('org.freedesktop.systemd1', path), 'org.freedesktop.DBus.Properties')
        values = dict(interface.GetAll('org.freedesktop.systemd1.Unit', timeout=5))
        values.update(interface.GetAll('org.freedesktop.systemd1.Service', timeout=5))
        return values

    def snapshot(self):
        props = self.properties()
        state, substate = str(props.get('ActiveState', '')), str(props.get('SubState', ''))
        started, finished = int(props.get('ExecMainStartTimestamp', 0)), int(props.get('ExecMainExitTimestamp', 0))
        result = str(props.get('Result', ''))
        job = props.get('Job', (0, '/'))
        if props.get('LoadState') != 'loaded':
            status = 'unavailable'
        elif int(job[0]) or state in ('activating', 'deactivating', 'reloading') or substate in ('running', 'start', 'start-pre', 'start-post'):
            status = 'running'
        elif state == 'failed' or (started and result and result != 'success'):
            status = 'failed'
        elif started and finished >= started and result == 'success' and int(props.get('ExecMainStatus', -1)) == 0:
            status = 'completed'
        elif state == 'inactive' and not started:
            status = 'idle'
        else:
            status = 'unknown'
        def timestamp(value):
            return datetime.fromtimestamp(value / 1000000).astimezone().isoformat() if value else None
        return {'status': status, 'unit': self.unit, 'active_state': state, 'substate': substate,
                'result': result, 'exit_status': int(props.get('ExecMainStatus', 0)),
                'started': timestamp(started), 'finished': timestamp(finished),
                'token': str(started) + ':' + str(finished) + ':' + result,
                'can_start': status in ('idle', 'completed', 'failed')}

    def submit(self, payload, *, authorized=False):
        if not authorized:
            return {'message': 'Administrator access is required.'}, 403
        if not isinstance(payload, dict) or payload.get('backup_confirmed') is not True or payload.get('maintenance_confirmed') is not True:
            return {'message': 'Confirm a verified backup and the capture interruption before upgrading.'}, 400
        try:
            with upgrade_lock():
                current = self.snapshot()
                if not current['can_start']:
                    return {'message': 'Upgrade is running or its service state is unavailable. Refresh status.'}, 409
                if payload.get('observed_token') != current['token']:
                    return {'message': 'Upgrade state changed. Refresh and confirm again.'}, 409
                def effect():
                    _, manager = self.manager()
                    # Restart an exited oneshot; Start alone would be a no-op.
                    method = manager.RestartUnit if current['status'] == 'completed' else manager.StartUnit
                    return str(method(self.unit, 'fail', timeout=10))
                action = ModernAdminUpgradeCommandBoundary(psutil.disk_usage, effect).run('start', authorized=True)
                if not action.allowed:
                    code = 503 if action.status in ('provider_unavailable', 'effect_failed') else 400
                    return {'message': action.message}, code
                return {'message': 'Upgrade job submitted. Refresh status to verify progress and completion.',
                        'job': action.details['service_result']}, 202
        except BlockingIOError:
            return {'message': 'Another upgrade request is being processed. Refresh status.'}, 409
