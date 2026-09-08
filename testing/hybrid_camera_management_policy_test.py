#!/usr/bin/env python3
"""Camera save plans and bounded relaxation of multicamera output restrictions."""
import ast
from copy import deepcopy
from dataclasses import dataclass, replace
import hashlib
import itertools
import json
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from indi_allsky.hybrid_camera_management import (camera_mode_context, plan_camera_mode,
    plan_camera_switch, multicamera_capture_outputs)


def run():
    root=Path(__file__).resolve().parents[1]
    legacy=json.loads((root/'testing/fixtures/hybrid_multicamera_outputs_legacy.json').read_text())
    assert legacy['sha256']=='ef5afb450a961703907eb6992f0187346e346beb55dfb0fa21a80720c094f1a2'
    assert hashlib.sha256(legacy['source'].encode()).hexdigest()==legacy['sha256']
    namespace={'replace':replace,'_multi_camera_diag':lambda *a:None}
    exec(legacy['source'],namespace)
    @dataclass
    class Profile:
        outputs:dict
        profile_id:str='fixture'
        unrelated:float=12.5
    for values in itertools.product((False,True),repeat=10):
        outputs=dict(zip(('images','timelapse','keogram','startrails','mini_timelapse','panorama','extra_uploads','future_key','longterm_keogram','realtime_keogram'),values))
        profile=Profile(outputs)
        expected=namespace['_images_only_capture_profile'](None,profile)
        # Intentional deltas: both keogram outputs honor their profile values.
        for key in ('longterm_keogram','realtime_keogram'):
            expected.outputs.pop(key)
            if key in outputs:expected.outputs[key]=outputs[key]
        actual=multicamera_capture_outputs(outputs)
        assert actual==expected.outputs and actual is not outputs and profile.outputs==outputs
    for outputs in ({}, {'future_key': {'value': 1}}, {'timelapse': 'custom', 'images': False}):
        expected=namespace['_images_only_capture_profile'](None,Profile(outputs))
        for key in ('longterm_keogram','realtime_keogram'):
            expected.outputs.pop(key)
            if key in outputs:expected.outputs[key]=outputs[key]
        assert multicamera_capture_outputs(outputs)==expected.outputs
    tree=ast.parse((root/'indi_allsky/allsky.py').read_text())
    method=next(n for n in ast.walk(tree) if isinstance(n,ast.FunctionDef) and n.name=='_images_only_capture_profile')
    assert 'multicamera_capture_outputs(profile.outputs)' in ast.unparse(method)
    config={'MULTI_CAMERA_CAPTURE_ENABLE':False,'TIMELAPSE_ENABLE':True,'EXPOSURE_PERIOD_DAY':15,'EXPOSURE_PERIOD':45,
            'MULTI_CAMERA':{'profiles':[{'profile_id':'a','enabled':True,'primary':True,'camera_interface':'libcamera_imx708'},
                                        {'profile_id':'b','enabled':True,'camera_interface':'indi'}]},'extra':{'preserve':123}}
    before=deepcopy(config)
    context=camera_mode_context(config)
    assert context['enable_allowed'] and len(context['profiles'])==2
    assert all(p['generated_capture_enabled'] for p in context['profiles'])
    assert all(p['longterm_capture_enabled'] for p in context['profiles'])
    assert all(p['realtime_capture_enabled'] for p in context['profiles'])
    no_realtime=deepcopy(config)
    no_realtime['MULTI_CAMERA']['profiles'][0]['outputs']={'realtime_keogram':False}
    assert not camera_mode_context(no_realtime)['profiles'][0]['realtime_capture_enabled']
    disabled_samples=deepcopy(config)
    disabled_samples['LONGTERM_KEOGRAM']={'ENABLE':False}
    assert not any(p['longterm_capture_enabled'] for p in camera_mode_context(disabled_samples)['profiles'])
    for outputs in ({'longterm_keogram':False}, {'timelapse':False,'keogram':False,'startrails':False}):
        disabled_samples=deepcopy(config)
        disabled_samples['MULTI_CAMERA']['profiles'][0]['outputs']=outputs
        rows=camera_mode_context(disabled_samples)['profiles']
        assert not rows[0]['longterm_capture_enabled'] and rows[1]['longterm_capture_enabled']
    assert all(not p['capture_outputs']['extra_uploads'] for p in context['profiles'])
    implicit=deepcopy(config)
    for p in implicit['MULTI_CAMERA']['profiles']:p.pop('profile_id')
    assert [p['profile_id'] for p in camera_mode_context(implicit)['profiles']]==['profile-1','profile-2']
    assert camera_mode_context(implicit)['enable_allowed']
    enabled=plan_camera_mode(config,True)
    assert enabled['MULTI_CAMERA_CAPTURE_ENABLE'] and config==before
    invalid=deepcopy(config);invalid['EXPOSURE_PERIOD_DAY']=5
    assert not camera_mode_context(invalid)['enable_allowed']
    for profiles in ([{'profile_id':'a','enabled':True}], ['bad'], [{'profile_id':'a'},{'profile_id':'a'}]):
        invalid=deepcopy(config);invalid['MULTI_CAMERA']['profiles']=profiles
        assert not camera_mode_context(invalid)['enable_allowed']
        try:plan_camera_mode(invalid,True)
        except ValueError:pass
        else:raise AssertionError('Invalid profile configuration enabled')
        assert not plan_camera_mode(dict(invalid,MULTI_CAMERA_CAPTURE_ENABLE=True),False)['MULTI_CAMERA_CAPTURE_ENABLE']
    off=deepcopy(config);off['MULTI_CAMERA']['profiles'][0]['outputs']={'keogram':False}
    assert not camera_mode_context(off)['profiles'][0]['generated_capture_enabled']
    interfaces={'indi','libcamera_imx708','mqtt_imx708','pycurl_camera','indi_passive'}
    for driver,name,expected in [('rpicam-still','libcamera_imx708','libcamera_imx708'),('libcamera-still','libcamera_imx708','libcamera_imx708'),
                                ('indi_asi_ccd','ZWO ASI678MC','indi'),('mqtt_imx708','MQTT camera','mqtt_imx708'),('pycurl_camera','Network camera','pycurl_camera')]:
        planned=plan_camera_switch(config,camera_name=name,driver=driver,supported_interfaces=interfaces)
        assert planned['CAMERA_INTERFACE']==expected and planned['extra']==config['extra'] and config==before
    for candidate,name in ((enabled,'libcamera_imx708'),(config,'Unknown sensor')):
        try:plan_camera_switch(candidate,camera_name=name,driver='rpicam-still',supported_interfaces=interfaces)
        except ValueError:pass
        else:raise AssertionError('Ambiguous or multicamera switch accepted')
    print('Camera management plans and 1027 output-policy cases (long-term/realtime restrictions removed): PASS')

if __name__=='__main__':run()
