"""UDisks inventory and explicit drive commands, independent of Flask views."""
from datetime import datetime
from pathlib import Path

PREFIX = 'org.freedesktop.UDisks2.'
PROTECTED_FILESYSTEMS = ('/', '/boot', '/boot/firmware', '/boot/efi', '/var', '/home', '/tmp', '/var/tmp', '/run', '/dev', '/dev/shm')


def mount_points(properties):
    return [bytes(value).rstrip(b'\0').decode('utf-8', errors='replace')
            for value in properties.get('MountPoints', [])]


class DriveManager:
    def __init__(self, bus=None, interface=None, protected_paths=()):
        import dbus
        self.bus = bus if bus is not None else dbus.SystemBus()
        self.interface = interface or dbus.Interface
        self.protected_paths = [Path(path).resolve() for path in protected_paths if path]

    def protected(self, mount):
        return mount in PROTECTED_FILESYSTEMS or any(path.is_relative_to(Path(mount).resolve()) for path in self.protected_paths)

    def object_interface(self, path, kind):
        return self.interface(self.bus.get_object(PREFIX[:-1], path), kind)

    def objects(self):
        return self.object_interface('/org/freedesktop/UDisks2', 'org.freedesktop.DBus.ObjectManager').GetManagedObjects()

    def inventory(self):
        objects = self.objects()
        result = []
        for path, props in objects.items():
            if PREFIX+'Drive' not in props:
                continue
            drive = props[PREFIX+'Drive']
            volumes = []
            for block_path, block_props in objects.items():
                block = block_props.get(PREFIX+'Block', {})
                fs = block_props.get(PREFIX+'Filesystem')
                if block.get('Drive') != path or fs is None:
                    continue
                mounts = mount_points(fs)
                volumes.append({'id': str(block.get('Id', '')), 'mounts': mounts,
                                'protected': any(self.protected(mount) for mount in mounts)})
            result.append({'id': str(drive['Id']), 'model': str(drive.get('Model', '')),
                           'vendor': str(drive.get('Vendor', '')), 'size': int(drive.get('Size', 0)),
                           'can_power_off': bool(drive.get('CanPowerOff', False)), 'volumes': volumes})
        return result

    def execute(self, payload):
        if not isinstance(payload, dict):
            raise ValueError('A JSON object is required.')
        command = payload.get('COMMAND')
        if command not in ('getmetadata', 'poweroff', 'mount', 'unmount'):
            raise ValueError('Unknown command')
        drive_command = command in ('getmetadata', 'poweroff')
        key = 'DRIVE_ID' if drive_command else 'DEVICE_ID'
        identifier = payload.get(key)
        if not isinstance(identifier, str) or not identifier.strip():
            raise ValueError('Choose a drive or filesystem.')
        kind = PREFIX+('Drive' if drive_command else 'Block')
        objects = self.objects()
        matches = [(path, props) for path, props in objects.items()
                   if kind in props and str(props[kind].get('Id', '')) == identifier]
        if len(matches) != 1:
            raise ValueError('Drive or device not found, or identifier is ambiguous.')
        path, props = matches[0]
        if command == 'getmetadata':
            drive = props[kind]
            detected = datetime.fromtimestamp(int(drive['TimeDetected']) / 1000000)
            media_detected = datetime.fromtimestamp(int(drive['TimeMediaDetected']) / 1000000) if drive['TimeMediaDetected'] else ''
            values = [('Id', identifier), ('Vendor', str(drive['Vendor'])), ('Model', str(drive['Model'])),
                      ('Size', '{0:0.1f} GB'.format(float(drive['Size']) / 1024**3)),
                      ('ConnectionBus', str(drive['ConnectionBus'])), ('Serial', str(drive['Serial'])),
                      ('Media', str(drive['Media'])), ('MediaCompatibility', ', '.join(str(x) for x in drive['MediaCompatibility'])),
                      ('CanPowerOff', bool(drive['CanPowerOff'])), ('Removable', bool(drive['Removable'])),
                      ('Ejectable', bool(drive['Ejectable'])), ('TimeDetected', detected), ('TimeMediaDetected', media_detected)]
            return {'success-message': '', 'drive_data': [[i, label, value] for i, (label, value) in enumerate(values)]}
        if command == 'poweroff':
            if not props[kind].get('CanPowerOff'):
                raise ValueError('Drive cannot be powered off')
            for other in objects.values():
                if other.get(PREFIX+'Block', {}).get('Drive') == path and mount_points(other.get(PREFIX+'Filesystem', {})):
                    raise ValueError('Unmount every filesystem on this drive before powering it off.')
            self.object_interface(path, PREFIX+'Drive').PowerOff({})
            return {'success-message': 'Power Off Successful'}
        fs = props.get(PREFIX+'Filesystem')
        if fs is None:
            raise ValueError('The selected device has no mountable filesystem.')
        mounts = mount_points(fs)
        interface = self.object_interface(path, PREFIX+'Filesystem')
        if command == 'mount':
            if mounts:
                raise ValueError('Filesystem already mounted')
            interface.Mount({})
            return {'success-message': 'Mount Successful'}
        if not mounts:
            raise ValueError('Filesystem not mounted')
        if any(self.protected(mount) for mount in mounts):
            raise ValueError('Not allowed to unmount a protected filesystem.')
        interface.Unmount({})
        return {'success-message': 'Unmount Successful'}
