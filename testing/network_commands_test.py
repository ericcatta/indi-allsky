#!/usr/bin/env python3
import ast
import hashlib
import json
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from indi_allsky.network_commands import plan_network_command, CONNECTION_COMMANDS


def run():
    root=Path(__file__).resolve().parents[1]
    expected=json.loads((root/'testing/fixtures/network_effects_legacy.json').read_text())['normalized_method_fingerprints']
    cls=next(n for n in ast.parse((root/'indi_allsky/network_manager_effects.py').read_text()).body if isinstance(n,ast.ClassDef))
    # Intentional recovery fix: a failed state read skips that polling sample.
    # Remove only that exact addition when checking the preserved legacy baseline.
    activation=next(n for n in cls.body if isinstance(n,ast.FunctionDef) and n.name=='activateConnection')
    poll=next(n for n in activation.body if isinstance(n,ast.For))
    handler=next(n for n in poll.body if isinstance(n,ast.Try)).handlers[0]
    assert len(handler.body)==2 and isinstance(handler.body[-1],ast.Continue)
    handler.body.pop()
    actual={n.name:hashlib.sha256(ast.dump(n,include_attributes=False).encode()).hexdigest() for n in cls.body if isinstance(n,ast.FunctionDef)}
    assert actual==expected
    for command,(method,kwargs) in CONNECTION_COMMANDS.items():
        assert plan_network_command({'COMMAND':command,'CONNECTION':'saved-uuid'})==(method,('saved-uuid',),kwargs)
    assert plan_network_command({'COMMAND':'scanap','INTERFACE':'wlan0'})==('scanAPs',('wlan0',),{})
    hotspot={'COMMAND':'createhotspot','INTERFACE':'wlan0','SSID':'Test','BAND':'bg','PSK':'test-only-password','NOSECURITY':False}
    assert plan_network_command(hotspot)[2]=={'nosecurity':False}
    assert plan_network_command(dict(hotspot,NOSECURITY=True,PSK=''))[2]=={'nosecurity':True}
    for security in ('false','true',0,1,None,[],{}):
        try:plan_network_command(dict(hotspot,NOSECURITY=security))
        except ValueError:pass
        else:raise AssertionError(security)
    connect={'COMMAND':'connectap','INTERFACE':'wlan0','AP_PATH':'/org/freedesktop/NetworkManager/AccessPoint/1','PSK':'test-only','PRIORITY':'-10','RETRIES':4}
    assert plan_network_command(connect)[1][-2:]==(-10,4)
    for payload in (None,[],{},dict(connect,PRIORITY=True),dict(connect,RETRIES=-2),dict(connect,AP_PATH=''),dict(hotspot,SSID='é'*17),dict(hotspot,NOSECURITY=False,PSK='short')):
        try:plan_network_command(payload)
        except ValueError:pass
        else:raise AssertionError(payload)
    print('Network commands: all intents, explicit hotspot security, required inputs, bounds and all legacy effect fingerprints: PASS')

if __name__=='__main__':run()
