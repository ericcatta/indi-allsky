"""Shared NetworkManager effects, independent of Classic and Flask view classes."""
import logging
import socket
import time
import dbus
from werkzeug.exceptions import NotFound

logger = logging.getLogger('indi_allsky')


class NetworkManagerEffects:
    nm_conn_states = {'Unknown': 0, 'Activating': 1, 'Active': 2, 'Deactivating': 3, 'Not Active': 4}

    def activateConnection(self, connection_uuid):
        bus = dbus.SystemBus()
        try:
            nm_settings = bus.get_object('org.freedesktop.NetworkManager', '/org/freedesktop/NetworkManager/Settings')
        except dbus.exceptions.DBusException as e:
            logger.error('D-Bus Exception: %s', str(e))
            return ({'failure-message': 'D-Bus Exception: {0:s}'.format(str(e))}, 400)
        try:
            settings_path = self.getSettingsPath(bus, nm_settings, connection_uuid)
        except NotFound:
            logger.error('Connection settings not found')
            return ({'failure-message': 'Connection settings not found'}, 400)
        settings = dbus.Interface(bus.get_object('org.freedesktop.NetworkManager', settings_path), 'org.freedesktop.NetworkManager.Settings.Connection')
        settings_connection = dbus.Interface(settings, 'org.freedesktop.NetworkManager.Settings.Connection')
        settings_dict = settings_connection.GetSettings()
        if settings_dict['connection']['type'] not in ('802-11-wireless', '802-3-ethernet'):
            return ({'failure-message': 'Only Ethernet and Wireless connections can be managed'}, 400)
        nm = bus.get_object('org.freedesktop.NetworkManager', '/org/freedesktop/NetworkManager')
        manager = dbus.Interface(nm, 'org.freedesktop.NetworkManager')
        try:
            connection_path = manager.ActivateConnection(settings_path, '/', '/')
        except dbus.exceptions.DBusException as e:
            logger.error('D-Bus Exception: %s', str(e))
            return ({'failure-message': 'D-Bus Exception: {0:s}'.format(str(e))}, 400)
        connection_props = dbus.Interface(bus.get_object('org.freedesktop.NetworkManager', connection_path), 'org.freedesktop.DBus.Properties')
        logger.info('Waiting for connection')
        state = None
        for _ in range(30):
            time.sleep(1.0)
            try:
                state = connection_props.Get('org.freedesktop.NetworkManager.Connection.Active', 'State')
            except dbus.exceptions.DBusException as e:
                logger.error('D-Bus Exception: %s', str(e))
                continue
            if int(state) == self.nm_conn_states['Active']:
                logger.warning('Connection established!')
                break
        else:
            logger.error('Connection failed to activate')
            return ({'failure-message': 'Connection failed to activate'}, 400)
        return {'success-message': 'Connection Activated'}

    def deactivateConnection(self, connection_uuid):
        bus = dbus.SystemBus()
        try:
            nm_settings = bus.get_object('org.freedesktop.NetworkManager', '/org/freedesktop/NetworkManager/Settings')
        except dbus.exceptions.DBusException as e:
            logger.error('D-Bus Exception: %s', str(e))
            return ({'failure-message': 'D-Bus Exception: {0:s}'.format(str(e))}, 400)
        try:
            settings_path = self.getSettingsPath(bus, nm_settings, connection_uuid)
        except NotFound:
            logger.error('Connection settings not found')
            return ({'failure-message': 'Connection settings not found'}, 400)
        nm = bus.get_object('org.freedesktop.NetworkManager', '/org/freedesktop/NetworkManager')
        try:
            conn_path = self.getActiveConnection(bus, nm, connection_uuid)
        except NotFound:
            logger.error('Active connection not found')
            return ({'failure-message': 'Active connection not found'}, 400)
        settings = dbus.Interface(bus.get_object('org.freedesktop.NetworkManager', settings_path), 'org.freedesktop.NetworkManager.Settings.Connection')
        settings_connection = dbus.Interface(settings, 'org.freedesktop.NetworkManager.Settings.Connection')
        settings_dict = settings_connection.GetSettings()
        if settings_dict['connection']['type'] not in ('802-11-wireless', '802-3-ethernet'):
            return ({'failure-message': 'Only Ethernet and Wireless connections can be managed'}, 400)
        manager = dbus.Interface(nm, 'org.freedesktop.NetworkManager')
        try:
            manager.DeactivateConnection(conn_path)
        except dbus.exceptions.DBusException as e:
            logger.error('D-Bus Exception: %s', str(e))
            return ({'failure-message': 'Failed to deactivate connection: {0:s}'.format(str(e))}, 400)
        time.sleep(2.0)
        return {'success-message': 'Connection deactivated'}

    def deleteConnection(self, connection_uuid):
        bus = dbus.SystemBus()
        try:
            nm_settings = bus.get_object('org.freedesktop.NetworkManager', '/org/freedesktop/NetworkManager/Settings')
        except dbus.exceptions.DBusException as e:
            logger.error('D-Bus Exception: %s', str(e))
            return ({'failure-message': 'D-Bus Exception: {0:s}'.format(str(e))}, 400)
        try:
            settings_path = self.getSettingsPath(bus, nm_settings, connection_uuid)
        except NotFound:
            logger.error('Connection settings not found')
            return ({'failure-message': 'Connection settings not found'}, 400)
        settings = dbus.Interface(bus.get_object('org.freedesktop.NetworkManager', settings_path), 'org.freedesktop.NetworkManager.Settings.Connection')
        nm = bus.get_object('org.freedesktop.NetworkManager', '/org/freedesktop/NetworkManager')
        try:
            self.getActiveConnection(bus, nm, connection_uuid)
            return ({'failure-message': 'Cannot delete active connections'}, 400)
        except NotFound:
            pass
        settings_connection = dbus.Interface(settings, 'org.freedesktop.NetworkManager.Settings.Connection')
        settings_dict = settings_connection.GetSettings()
        if settings_dict['connection']['type'] not in ('802-11-wireless', '802-3-ethernet'):
            return ({'failure-message': 'Only Ethernet and Wireless connections can be managed'}, 400)
        settings.Delete()
        time.sleep(2.0)
        return {'success-message': 'Connection deleted'}

    def setAutostartConnection(self, connection_uuid, auto_connect=True):
        bus = dbus.SystemBus()
        try:
            nm_settings = bus.get_object('org.freedesktop.NetworkManager', '/org/freedesktop/NetworkManager/Settings')
        except dbus.exceptions.DBusException as e:
            logger.error('D-Bus Exception: %s', str(e))
            return ({'failure-message': 'D-Bus Exception: {0:s}'.format(str(e))}, 400)
        try:
            settings_path = self.getSettingsPath(bus, nm_settings, connection_uuid)
        except NotFound:
            logger.error('Connection settings not found')
            return ({'failure-message': 'Connection settings not found'}, 400)
        settings = dbus.Interface(bus.get_object('org.freedesktop.NetworkManager', settings_path), 'org.freedesktop.NetworkManager.Settings.Connection')
        settings_connection = dbus.Interface(settings, 'org.freedesktop.NetworkManager.Settings.Connection')
        settings_dict = settings_connection.GetSettings()
        settings_dict['connection']['autoconnect'] = auto_connect
        try:
            settings_connection.Update(settings_dict)
        except dbus.exceptions.DBusException as e:
            logger.error('D-Bus Exception: %s', str(e))
            return ({'failure-message': 'Configure Failed: {0:s}'.format(str(e))}, 400)
        time.sleep(2.0)
        return {'success-message': 'Configure Successful'}

    def incrementConnectionPriority(self, connection_uuid, increment=10):
        bus = dbus.SystemBus()
        try:
            nm_settings = bus.get_object('org.freedesktop.NetworkManager', '/org/freedesktop/NetworkManager/Settings')
        except dbus.exceptions.DBusException as e:
            logger.error('D-Bus Exception: %s', str(e))
            return ({'failure-message': 'D-Bus Exception: {0:s}'.format(str(e))}, 400)
        try:
            settings_path = self.getSettingsPath(bus, nm_settings, connection_uuid)
        except NotFound:
            logger.error('Connection settings not found')
            return ({'failure-message': 'Connection settings not found'}, 400)
        settings = dbus.Interface(bus.get_object('org.freedesktop.NetworkManager', settings_path), 'org.freedesktop.NetworkManager.Settings.Connection')
        settings_connection = dbus.Interface(settings, 'org.freedesktop.NetworkManager.Settings.Connection')
        settings_dict = settings_connection.GetSettings()
        try:
            current_priority = int(settings_dict['connection']['autoconnect-priority'])
        except TypeError:
            current_priority = 0
        except ValueError:
            current_priority = 0
        except KeyError:
            current_priority = 0
        new_priority = current_priority + increment
        settings_dict['connection']['autoconnect-priority'] = new_priority
        try:
            settings_connection.Update(settings_dict)
        except dbus.exceptions.DBusException as e:
            logger.error('D-Bus Exception: %s', str(e))
            return ({'failure-message': 'Configure Failed: {0:s}'.format(str(e))}, 400)
        time.sleep(2.0)
        return {'success-message': 'Priority Updated'}

    def decrementConnectionPriority(self, connection_uuid, increment=-10):
        return self.incrementConnectionPriority(connection_uuid, increment=increment)

    def setPowersave(self, connection_uuid, powersave=False):
        bus = dbus.SystemBus()
        try:
            nm_settings = bus.get_object('org.freedesktop.NetworkManager', '/org/freedesktop/NetworkManager/Settings')
        except dbus.exceptions.DBusException as e:
            logger.error('D-Bus Exception: %s', str(e))
            return ({'failure-message': 'D-Bus Exception: {0:s}'.format(str(e))}, 400)
        try:
            settings_path = self.getSettingsPath(bus, nm_settings, connection_uuid)
        except NotFound:
            logger.error('Connection settings not found')
            return ({'failure-message': 'Connection settings not found'}, 400)
        settings = dbus.Interface(bus.get_object('org.freedesktop.NetworkManager', settings_path), 'org.freedesktop.NetworkManager.Settings.Connection')
        settings_connection = dbus.Interface(settings, 'org.freedesktop.NetworkManager.Settings.Connection')
        settings_dict = settings_connection.GetSettings()
        if settings_dict['connection']['type'] != '802-11-wireless':
            return ({'failure-message': 'Powersave only valid for wifi connections'}, 400)
        if powersave:
            nm_powersave = 3
        else:
            nm_powersave = 2
        settings_dict['802-11-wireless']['powersave'] = nm_powersave
        try:
            settings_connection.Update(settings_dict)
        except dbus.exceptions.DBusException as e:
            logger.error('D-Bus Exception: %s', str(e))
            return ({'failure-message': 'Configure Failed: {0:s}'.format(str(e))}, 400)
        time.sleep(2.0)
        return {'success-message': 'Configure Successful'}

    def getSettingsPath(self, bus, nm_settings, connection_uuid):
        settingspath_list = nm_settings.Get('org.freedesktop.NetworkManager.Settings', 'Connections', dbus_interface=dbus.PROPERTIES_IFACE)
        for settings_path in settingspath_list:
            settings = bus.get_object('org.freedesktop.NetworkManager', settings_path)
            settings_connection = dbus.Interface(settings, 'org.freedesktop.NetworkManager.Settings.Connection')
            settings_dict = settings_connection.GetSettings()
            settings_uuid = str(settings_dict['connection']['uuid'])
            if settings_uuid == connection_uuid:
                return settings_path
        else:
            raise NotFound('Connection settings not found')

    def getActiveConnection(self, bus, nm, connection_uuid):
        connpath_list = nm.Get('org.freedesktop.NetworkManager', 'ActiveConnections', dbus_interface=dbus.PROPERTIES_IFACE)
        for conn_path in connpath_list:
            conn = bus.get_object('org.freedesktop.NetworkManager', conn_path)
            conn_uuid = conn.Get('org.freedesktop.NetworkManager.Connection.Active', 'Uuid', dbus_interface=dbus.PROPERTIES_IFACE)
            if str(conn_uuid) == connection_uuid:
                return conn_path
        else:
            raise NotFound('Connection settings not found')

    def scanAPs(self, interface_name):
        bus = dbus.SystemBus()
        try:
            manager_bus_object = bus.get_object('org.freedesktop.NetworkManager', '/org/freedesktop/NetworkManager')
        except dbus.exceptions.DBusException as e:
            logger.error('D-Bus Exception: %s', str(e))
            return ({'failure-message': 'D-Bus Exception: {0:s}'.format(str(e))}, 400)
        manager = dbus.Interface(manager_bus_object, 'org.freedesktop.NetworkManager')
        manager_props = dbus.Interface(manager_bus_object, 'org.freedesktop.DBus.Properties')
        wifi_enabled = manager_props.Get('org.freedesktop.NetworkManager', 'WirelessEnabled')
        if not wifi_enabled:
            logger.warning('Enabling WiFi')
            manager_props.Set('org.freedesktop.NetworkManager', 'WirelessEnabled', True)
            time.sleep(10)
        device_path = manager.GetDeviceByIpIface(interface_name)
        device = dbus.Interface(bus.get_object('org.freedesktop.NetworkManager', device_path), 'org.freedesktop.NetworkManager.Device.Wireless')
        try:
            device.RequestScan(dbus.Dictionary({}, signature='sv'))
        except dbus.exceptions.DBusException as e:
            logger.error('D-Bus Exception: %s', str(e))
            return ({'failure-message': 'RequestScan Failed: {0:s}'.format(str(e))}, 400)
        time.sleep(10.0)
        try:
            accesspoints_paths_list = device.GetAccessPoints()
        except dbus.exceptions.DBusException as e:
            logger.error('D-Bus Exception: %s', str(e))
            return ({'failure-message': 'Scan APs Failed: {0:s}'.format(str(e))}, 400)
        ap_list = list()
        for ap_path in accesspoints_paths_list:
            ap_props = dbus.Interface(bus.get_object('org.freedesktop.NetworkManager', ap_path), 'org.freedesktop.DBus.Properties')
            ap_ssid = ap_props.Get('org.freedesktop.NetworkManager.AccessPoint', 'Ssid')
            ap_strength = ap_props.Get('org.freedesktop.NetworkManager.AccessPoint', 'Strength')
            ap_frequency = ap_props.Get('org.freedesktop.NetworkManager.AccessPoint', 'Frequency')
            ap_hwaddress = ap_props.Get('org.freedesktop.NetworkManager.AccessPoint', 'HwAddress')
            str_ap_ssid = ''.join((chr(i) for i in ap_ssid))
            logger.info('Found SSID: %s', str_ap_ssid)
            ap_frequency_int = int(ap_frequency)
            if ap_frequency_int > 5999:
                ap_frequency_str = '6 GHz'
            elif ap_frequency_int > 3000:
                ap_frequency_str = '5 GHz'
            else:
                ap_frequency_str = '2.4 GHz'
            ap_list.append({'path': str(ap_path), 'ssid': str_ap_ssid, 'ap_hwaddress': ap_hwaddress, 'desc': '{0:s} [{1:s}] - {2:s} - {3:d}%'.format(str_ap_ssid, ap_hwaddress, ap_frequency_str, int.from_bytes(str(ap_strength).encode())), 'strength': int.from_bytes(str(ap_strength).encode()), 'frequency': ap_frequency_int})
        ap_list_sorted = sorted(ap_list, key=lambda x: (x['strength'], x['ap_hwaddress']), reverse=True)
        time.sleep(2.0)
        return {'success-message': 'Scan Successful', 'data': ap_list_sorted}

    def connectAP(self, interface_name, ap_path, psk, priority, retries):
        bus = dbus.SystemBus()
        manager_bus_object = bus.get_object('org.freedesktop.NetworkManager', '/org/freedesktop/NetworkManager')
        manager = dbus.Interface(manager_bus_object, 'org.freedesktop.NetworkManager')
        device_path = manager.GetDeviceByIpIface(interface_name)
        connection_params = {'connection': {'type': '802-11-wireless', 'autoconnect': True, 'autoconnect-priority': priority, 'autoconnect-retries': retries}, '802-11-wireless': {'security': '802-11-wireless-security', 'powersave': 2}, '802-11-wireless-security': {'key-mgmt': 'wpa-psk', 'psk': psk}}
        try:
            settings_path, connection_path = manager.AddAndActivateConnection(connection_params, device_path, ap_path)
        except dbus.exceptions.DBusException as e:
            logger.error('D-Bus Exception: %s', str(e))
            return ({'failure-message': 'Connect AP Failed: {0:s}'.format(str(e))}, 400)
        connection_props = dbus.Interface(bus.get_object('org.freedesktop.NetworkManager', connection_path), 'org.freedesktop.DBus.Properties')
        logger.info('Waiting for wireless connection')
        state = None
        for _ in range(30):
            time.sleep(1.0)
            try:
                state = connection_props.Get('org.freedesktop.NetworkManager.Connection.Active', 'State')
            except dbus.exceptions.DBusException as e:
                logger.error('D-Bus Exception: %s (psk may be incorrect)', str(e))
                settings = dbus.Interface(bus.get_object('org.freedesktop.NetworkManager', settings_path), 'org.freedesktop.NetworkManager.Settings.Connection')
                settings.Delete()
                return ({'failure-message': 'Connect AP Failed: {0:s} (PSK may be incorrect)'.format(str(e))}, 400)
            if int(state) == self.nm_conn_states['Active']:
                logger.warning('Wireless connection established!')
                break
        else:
            logger.error('Wireless connection failed')
            return ({'failure-message': 'Connect AP Failed: Wireless connection failed'}, 400)
        return {'success-message': 'Connection Successful'}

    def createHotspot(self, interface_name, ssid, band, psk, nosecurity=False):
        bus = dbus.SystemBus()
        try:
            nm = bus.get_object('org.freedesktop.NetworkManager', '/org/freedesktop/NetworkManager')
        except dbus.exceptions.DBusException as e:
            logger.error('D-Bus Exception: %s', str(e))
            return ({'failure-message': 'Connect AP Failed: {0:s}'.format(str(e))}, 400)
        manager = dbus.Interface(nm, 'org.freedesktop.NetworkManager')
        nm_settings = bus.get_object('org.freedesktop.NetworkManager', '/org/freedesktop/NetworkManager/Settings')
        settings_manager = dbus.Interface(nm_settings, 'org.freedesktop.NetworkManager.Settings')
        manager.GetDeviceByIpIface(interface_name)
        connection_params = {'connection': {'type': '802-11-wireless', 'autoconnect': True, 'autoconnect-priority': -90, 'id': ssid, 'interface-name': interface_name}, '802-11-wireless': {'mode': 'ap', 'ssid': dbus.ByteArray(ssid.encode('utf-8')), 'powersave': 2, 'band': band}, 'ipv4': {'method': 'shared', 'addresses': [[dbus.UInt32(self.ip2int('10.42.0.1')), dbus.UInt32(24), dbus.UInt32(self.ip2int('0.0.0.0'))]]}, 'ipv6': {'method': 'link-local'}}
        if not nosecurity:
            connection_params['802-11-wireless']['security'] = '802-11-wireless-security'
            connection_params['802-11-wireless-security'] = {'key-mgmt': 'wpa-psk', 'psk': psk, 'proto': ['rsn'], 'group': ['ccmp'], 'pairwise': ['ccmp']}
        try:
            settings_manager.AddConnection(connection_params)
        except dbus.exceptions.DBusException as e:
            logger.error('D-Bus Exception: %s', str(e))
            return ({'failure-message': 'D-Bus Exception: {0:s}'.format(str(e))}, 400)
        time.sleep(2.0)
        return {'success-message': 'Hotspot Created'}

    def ip2int(self, ip_str):
        import struct
        return struct.unpack('=I', socket.inet_aton(ip_str))[0]
