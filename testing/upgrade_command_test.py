#!/usr/bin/env python3
"""Upgrade must test free space, not capacity, and fail closed before effects."""
from pathlib import Path
import sys
from types import SimpleNamespace
from unittest.mock import Mock
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from indi_allsky.modern_safe_action import ModernAdminUpgradeCommandBoundary as Boundary


def run():
    minimum=Boundary.MIN_FREE_BYTES
    for authorized,command in ((False,'start'),(1,'start'),(True,'restart'),(True,None)):
        disk=Mock();effect=Mock()
        result=Boundary(disk,effect).run(command,authorized=authorized)
        assert not result.allowed
        disk.assert_not_called();effect.assert_not_called()
    for mount in ('/','/var'):
        for free in (0,minimum-1,None,-1,True,'9999999999',float('nan'),float('inf')):
            disk=Mock(side_effect=lambda path:SimpleNamespace(total=200*minimum,free=free if path==mount else minimum))
            effect=Mock()
            result=Boundary(disk,effect).run('start',authorized=True)
            assert not result.allowed,(mount,free,result)
            assert mount in result.message
            effect.assert_not_called()
        for failure in (PermissionError('private path'),OSError('device error')):
            def usage(path):
                if path==mount:raise failure
                return SimpleNamespace(free=minimum)
            effect=Mock();result=Boundary(usage,effect).run('start',authorized=True)
            assert result.status=='provider_unavailable' and 'private' not in result.message
            effect.assert_not_called()
    disk=Mock(return_value=SimpleNamespace(total=200*minimum,free=minimum))
    effect=Mock(return_value='/org/freedesktop/systemd1/job/42')
    result=Boundary(disk,effect).run('start',authorized=True)
    assert result.allowed and result.status=='submitted'
    assert [call.args for call in disk.call_args_list]==[('/',),('/var',)]
    effect.assert_called_once_with()
    assert result.details['free_bytes']=={'/':minimum,'/var':minimum}
    effect=Mock(side_effect=RuntimeError('private bus details'))
    result=Boundary(disk,effect).run('start',authorized=True)
    assert result.status=='effect_failed' and not result.allowed and 'private' not in result.message
    print('Upgrade preconditions: free bytes, exact threshold, root/var, read failures, permissions, commands and single effect: PASS')

if __name__=='__main__':run()
