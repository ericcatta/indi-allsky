#!/usr/bin/env python3
"""Scan through the real adapter with real D-Bus value types and no live bus."""
from pathlib import Path
import sys
from unittest.mock import Mock, patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import dbus
from indi_allsky.network_manager_effects import NetworkManagerEffects


def run():
    prefix='/org/freedesktop/NetworkManager/AccessPoint/'
    points={prefix+'1':(b'Caf\xc3\xa8',70,2412),
            prefix+'2':(b'Plain',100,5180),
            prefix+'3':(b'\xff',0,2412),
            prefix+'4':(b'',50,2412)}
    for enabled in (True,False):
        manager=Mock();manager.GetDeviceByIpIface.return_value='/device'
        properties=Mock();properties.Get.return_value=enabled
        device=Mock();device.GetAccessPoints.return_value=list(points)
        bus=Mock();bus.get_object.side_effect=lambda service,path:path
        def interface(path,kind):
            if kind=='org.freedesktop.NetworkManager':return manager
            if kind=='org.freedesktop.NetworkManager.Device.Wireless':return device
            if path in points:
                ssid,strength,frequency=points[path]
                values={'Ssid':dbus.ByteArray(ssid),'Strength':dbus.Byte(strength),
                        'Frequency':dbus.UInt32(frequency),'HwAddress':'00:00:00:00:00:'+path[-1]}
                return Mock(Get=lambda service,name:values[name])
            return properties
        with patch('dbus.SystemBus',return_value=bus),patch('dbus.Interface',side_effect=interface),patch('indi_allsky.network_manager_effects.time.sleep'):
            result=NetworkManagerEffects().scanAPs('wlan-test')
            rows=result['data']
            assert [r['path'] for r in rows]==[prefix+'2',prefix+'1',prefix+'4',prefix+'3']
            assert [r['strength'] for r in rows]==[100,70,50,0]
            assert rows[1]['ssid']=='Cafè' and 'Cafè' in rows[1]['desc']
            assert rows[2]['ssid']=='' and rows[3]['ssid']=='\ufffd'
            assert rows[0]['frequency']==5180 and '5 GHz' in rows[0]['desc']
            manager.GetDeviceByIpIface.assert_called_once_with('wlan-test')
            device.RequestScan.assert_called_once()
            if enabled:properties.Set.assert_not_called()
            else:properties.Set.assert_called_once_with('org.freedesktop.NetworkManager','WirelessEnabled',True)
            device.RequestScan.side_effect=dbus.exceptions.DBusException('scan rejected')
            device.GetAccessPoints.reset_mock()
            response=NetworkManagerEffects().scanAPs('wlan-test')
            assert response[1]==400 and 'RequestScan Failed' in response[0]['failure-message']
            device.GetAccessPoints.assert_not_called()
            device.RequestScan.side_effect=None
            device.GetAccessPoints.return_value=[]
            assert NetworkManagerEffects().scanAPs('wlan-test')['data']==[]
    print('Network scan: UTF-8/invalid/empty SSIDs, AP identity, D-Bus strengths, sort, radio enable, failed scan and empty results: PASS')


if __name__=='__main__':run()
