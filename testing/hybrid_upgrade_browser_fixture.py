"""Explicit synthetic upgrade service for the isolated browser server only."""
import json
from types import SimpleNamespace
from unittest.mock import patch


def install_upgrade_fixture(stack, path):
    from indi_allsky.upgrade_runtime import UpgradeRuntime

    def read():
        return json.loads(path.read_text())

    def properties():
        state = read()['state']
        if state == 'unavailable':
            raise RuntimeError('Synthetic unavailable upgrade provider')
        props = {'LoadState': 'loaded', 'ActiveState': 'inactive', 'SubState': 'dead',
                 'Job': (0, '/'), 'ExecMainStartTimestamp': 0,
                 'ExecMainExitTimestamp': 0, 'ExecMainStatus': 0, 'Result': 'success'}
        if state == 'running':
            props.update(Job=(42, '/synthetic/job/42'), ActiveState='activating')
        elif state in ('completed', 'failed'):
            props.update(ExecMainStartTimestamp=1700000000000000, ExecMainExitTimestamp=1700000001000000,
                         ActiveState='active', SubState='exited')
            if state == 'failed':
                props.update(ActiveState='failed', SubState='failed', Result='exit-code', ExecMainStatus=1)
        elif state not in ('idle', 'reject'):
            raise ValueError('Unknown synthetic upgrade state')
        return props

    def effect(method, unit, mode, timeout):
        data = read()
        if data['state'] == 'reject':
            raise RuntimeError('Synthetic service command failure')
        data.setdefault('effects', []).append({'method': method, 'unit': str(unit), 'mode': mode})
        data['state'] = 'running'
        path.write_text(json.dumps(data, indent=2) + '\n')
        return '/synthetic/job/42'

    manager = SimpleNamespace(
        StartUnit=lambda unit, mode, timeout: effect('StartUnit', unit, mode, timeout),
        RestartUnit=lambda unit, mode, timeout: effect('RestartUnit', unit, mode, timeout))
    stack.enter_context(patch.object(UpgradeRuntime, 'properties', side_effect=properties))
    stack.enter_context(patch.object(UpgradeRuntime, 'manager', return_value=(None, manager)))
