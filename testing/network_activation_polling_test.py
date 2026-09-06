#!/usr/bin/env python3
"""Activation tolerates transient D-Bus state-read failure and remains bounded."""
from pathlib import Path
import sys
from types import SimpleNamespace
from unittest.mock import Mock, patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))

class BusError(Exception):pass


def run():
    fake_dbus=SimpleNamespace(SystemBus=Mock(),Interface=Mock(),exceptions=SimpleNamespace(DBusException=BusError))
    with patch.dict(sys.modules,{'dbus':fake_dbus}):
        from indi_allsky.network_manager_effects import NetworkManagerEffects
    for readings,success,expected_reads in (([BusError('temporary'),2],True,2),
                                            ([BusError('temporary')]*30,False,30),
                                            ([1]*30,False,30),([2],True,1)):
        bus=Mock();bus.get_object.side_effect=lambda name,path:path
        fake_dbus.SystemBus.return_value=bus
        manager=Mock();manager.ActivateConnection.return_value='/active'
        settings=Mock();settings.GetSettings.return_value={'connection':{'type':'802-3-ethernet'}}
        properties=Mock();properties.Get.side_effect=readings
        def interface(obj,kind):
            if kind=='org.freedesktop.NetworkManager.Settings.Connection':return settings
            if kind=='org.freedesktop.NetworkManager':return manager
            if kind=='org.freedesktop.DBus.Properties':return properties
            raise AssertionError(kind)
        fake_dbus.Interface.side_effect=interface
        effects=NetworkManagerEffects()
        with patch.object(effects,'getSettingsPath',return_value='/saved'),patch('indi_allsky.network_manager_effects.time.sleep') as sleep:
            result=effects.activateConnection('test-uuid')
        assert properties.Get.call_count==expected_reads
        assert sleep.call_count==expected_reads
        manager.ActivateConnection.assert_called_once_with('/saved','/','/')
        if success:assert result=={'success-message':'Connection Activated'}
        else:assert result==({'failure-message':'Connection failed to activate'},400)
    print('Network activation: failed first read recovers, repeated failure/activating stop at 30 polls, immediate success, single activation: PASS')

if __name__=='__main__':run()
