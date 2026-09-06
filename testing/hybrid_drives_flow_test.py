#!/usr/bin/env python3
"""Drive inventory/commands with real Flask and an isolated UDisks object graph."""
import argparse
import re
from types import SimpleNamespace
from unittest.mock import patch
from hybrid_runtime_fixture import isolated_app, login_client


def run(runtime_config):
    with isolated_app(runtime_config) as app:
        from indi_allsky.drive_manager import DriveManager, PREFIX
        import dbus
        drive_path='/org/freedesktop/UDisks2/drives/test'
        volume_path='/org/freedesktop/UDisks2/block_devices/test1'
        drive={'Id':'test-drive','Vendor':'Test','Model':'Fixture','Size':1073741824,'CanPowerOff':True,
               'TimeDetected':0,'TimeMediaDetected':0,'ConnectionBus':'usb','Serial':'test','Media':'flash',
               'MediaCompatibility':['flash'],'Removable':True,'Ejectable':True}
        filesystem={'MountPoints':[]}
        graph={drive_path:{PREFIX+'Drive':drive},volume_path:{PREFIX+'Block':{'Id':'test-volume','Drive':drive_path},PREFIX+'Filesystem':filesystem}}
        effects=[]
        def mount(options): effects.append('mount');filesystem['MountPoints']=[b'/media/test\0']
        def unmount(options):effects.append('unmount');filesystem['MountPoints']=[]
        def poweroff(options):effects.append('poweroff')
        def interface(path,kind):
            if kind=='org.freedesktop.DBus.ObjectManager':return SimpleNamespace(GetManagedObjects=lambda:graph)
            if kind==PREFIX+'Filesystem':return SimpleNamespace(Mount=mount,Unmount=unmount)
            if kind==PREFIX+'Drive':return SimpleNamespace(PowerOff=poweroff)
            raise AssertionError(kind)
        bus=SimpleNamespace(get_object=lambda service,path:path)
        real=DriveManager
        factory=lambda **kw:real(bus=bus,interface=interface,**kw)
        endpoint='/indi-allsky/ajax/drives';page='/indi-allsky/modern-admin/storage/drives'
        with patch('indi_allsky.drive_manager.DriveManager',side_effect=factory):
            admin=login_client(app,1);ordinary=login_client(app,2)
            for client in (admin,ordinary):
                response=client.get(page)
                assert response.status_code==200 and 'Fixture' in response.text and 'Not mounted' in response.text
            assert effects==[]
            token=re.search(r'name="csrf_token"[^>]*value="([^"]+)"',admin.get('/indi-allsky/modern-admin/account').text)[1]
            headers={'X-CSRFToken':token}
            def command(name,**fields):return admin.post(endpoint,json=dict(COMMAND=name,**fields),headers=headers)
            for payload in (None,[],{}, {'COMMAND':'bad'}, {'COMMAND':'mount'}, {'COMMAND':'mount','DEVICE_ID':'missing'}):
                assert admin.post(endpoint,json=payload,headers=headers).status_code==400
            assert effects==[]
            metadata=command('getmetadata',DRIVE_ID='test-drive')
            assert metadata.status_code==200 and len(metadata.json['drive_data'])==13
            assert metadata.json['drive_data'][3]==[3,'Size','1.0 GB']
            assert command('mount',DEVICE_ID='test-volume').status_code==200
            assert effects==['mount']
            assert command('mount',DEVICE_ID='test-volume').status_code==400 # Even one mount blocks.
            assert command('poweroff',DRIVE_ID='test-drive').status_code==400
            filesystem['MountPoints'].append(b'/\0')
            assert command('unmount',DEVICE_ID='test-volume').status_code==400 # Second mount is protected.
            filesystem['MountPoints']=[b'/media/test\0']
            assert 'Unmount' in admin.get(page).text
            assert command('unmount',DEVICE_ID='test-volume').status_code==200
            assert command('poweroff',DRIVE_ID='test-drive').status_code==200
            assert effects==['mount','unmount','poweroff']
            count=len(effects)
            assert admin.post(endpoint,json={'COMMAND':'mount','DEVICE_ID':'test-volume'}).status_code==400
            user_token=re.search(r'name="csrf_token"[^>]*value="([^"]+)"',ordinary.get('/indi-allsky/modern-admin/account').text)[1]
            assert ordinary.post(endpoint,json={'COMMAND':'mount','DEVICE_ID':'test-volume'},headers={'X-CSRFToken':user_token}).status_code==400
            assert len(effects)==count
            filesystem['MountPoints']=[b'/media/test\0']
            manager=factory(protected_paths=['/media/test/images'])
            assert manager.inventory()[0]['volumes'][0]['protected']
            try:manager.execute({'COMMAND':'unmount','DEVICE_ID':'test-volume'})
            except ValueError:pass
            else:raise AssertionError('Configured media mount allowed')
        with patch('indi_allsky.drive_manager.DriveManager',side_effect=dbus.exceptions.DBusException('private details')):
            response=admin.get(page)
            assert response.status_code==200 and 'UDisks2 is unavailable' in response.text and 'private details' not in response.text
            response=admin.post(endpoint,json={'COMMAND':'mount','DEVICE_ID':'test-volume'},headers=headers)
            assert response.status_code==503 and 'private details' not in response.text
        assert app.test_client().get(page).status_code==302
        print('Hybrid drives: inventory, metadata, mount/unmount/poweroff, mounted/protected/media guards, roles/CSRF and provider failures: PASS')

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--runtime-config',default='/etc/indi-allsky/flask.json')
    run(parser.parse_args().runtime_config)
