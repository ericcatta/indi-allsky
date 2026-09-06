"""Validated NetworkManager command intent, without Flask or hardware effects."""
import re

CONNECTION_COMMANDS = {
    'activate': ('activateConnection', {}), 'deactivate': ('deactivateConnection', {}),
    'delete': ('deleteConnection', {}), 'autostart': ('setAutostartConnection', {'auto_connect': True}),
    'noautostart': ('setAutostartConnection', {'auto_connect': False}),
    'incpriority': ('incrementConnectionPriority', {}), 'decpriority': ('decrementConnectionPriority', {}),
    'powersavedisable': ('setPowersave', {'powersave': False}),
    'powersaveenable': ('setPowersave', {'powersave': True}),
}


def plan_network_command(payload):
    if not isinstance(payload, dict):
        raise ValueError('A JSON object is required.')
    command = payload.get('COMMAND')
    if not isinstance(command, str):
        raise ValueError('Choose a network command.')
    if command in CONNECTION_COMMANDS:
        connection = payload.get('CONNECTION')
        if not isinstance(connection, str) or not connection.strip():
            raise ValueError('Choose a saved connection.')
        method, kwargs = CONNECTION_COMMANDS[command]
        return method, (connection,), dict(kwargs)
    if command not in ('scanap', 'connectap', 'createhotspot'):
        raise ValueError('Unknown command')
    interface = payload.get('INTERFACE')
    if not isinstance(interface, str) or not re.fullmatch(r'[A-Za-z0-9_.:-]{1,64}', interface):
        raise ValueError('Choose a network interface.')
    if command == 'scanap':
        return 'scanAPs', (interface,), {}
    psk = payload.get('PSK')
    if not isinstance(psk, str):
        raise ValueError('Supply a Wi-Fi password.')
    if command == 'connectap':
        ap = payload.get('AP_PATH')
        if not isinstance(ap, str) or not ap.startswith('/org/freedesktop/NetworkManager/AccessPoint/'):
            raise ValueError('Choose an access point from the scan results.')
        values = []
        for name, minimum in (('PRIORITY', -(2**31)), ('RETRIES', -1)):
            value = payload.get(name)
            try:
                if isinstance(value, bool) or str(int(value)) != str(value):
                    raise ValueError()
                value = int(value)
                if not minimum <= value < 2**31:
                    raise ValueError()
            except (TypeError, ValueError, OverflowError):
                raise ValueError('Invalid '+name.lower()+'.') from None
            values.append(value)
        return 'connectAP', (interface, ap, psk, *values), {}
    ssid, band, open_network = payload.get('SSID'), payload.get('BAND'), payload.get('NOSECURITY')
    if not isinstance(ssid, str) or not 1 <= len(ssid.encode('utf-8')) <= 32:
        raise ValueError('Hotspot SSID must contain 1 to 32 bytes.')
    if band not in ('bg', 'a'):
        raise ValueError('Invalid band selection')
    if type(open_network) is not bool:
        raise ValueError('Hotspot security selection must be a boolean.')
    if not open_network and len(psk) < 8:
        raise ValueError('PSK must be 8+ characters')
    return 'createHotspot', (interface, ssid, band, psk), {'nosecurity': open_network}
