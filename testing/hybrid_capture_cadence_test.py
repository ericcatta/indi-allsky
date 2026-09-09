#!/usr/bin/env python3
"""Shared cadence resolution, mode budgets and actual driver requests."""
import ast
from copy import deepcopy
import logging
from multiprocessing import Array
from pathlib import Path
import sys
import time
from unittest.mock import Mock
from types import SimpleNamespace
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from capture_profiles_test import _base_config
from indi_allsky import constants
from indi_allsky.capture_cadence import exposure_budget, validate_capture_cadence
from indi_allsky.capture_profiles import derive_capture_profiles, build_profile_config


def run():
    config = _base_config({'images': True})
    config.update(EXPOSURE_PERIOD=45, EXPOSURE_PERIOD_DAY=15)
    one = config['MULTI_CAMERA']['profiles'][0]
    one['exposure'] = {'max':40, 'min':0, 'min_day':0, 'period':90, 'period_day':30}
    two = deepcopy(one)
    two.update(profile_id='imx708', primary=False, camera_interface='libcamera_imx708')
    two['exposure'].update(max=12, period=60, period_day=20)
    config['MULTI_CAMERA']['profiles'].append(two)
    original = deepcopy(config)
    profiles = derive_capture_profiles(config)
    resolved = [build_profile_config(config, profile) for profile in profiles]
    assert len(resolved) == 2
    assert all(p['EXPOSURE_PERIOD'] == 45 and p['EXPOSURE_PERIOD_DAY'] == 15 for p in resolved)
    assert [p['CCD_EXPOSURE_MAX'] for p in resolved] == [40,12]
    assert original == config
    validate_capture_cadence(config)
    for value in (0, 6, float('nan'), float('inf')):
        bad = deepcopy(config); bad['EXPOSURE_PERIOD_DAY'] = value
        try: validate_capture_cadence(bad)
        except ValueError: pass
        else: raise AssertionError(value)
    bad = deepcopy(config); bad['MULTI_CAMERA']['profiles'][1]['exposure']['min_day'] = 10
    try: validate_capture_cadence(bad)
    except ValueError: pass
    else: raise AssertionError('Minimum exceeds day budget')
    single = deepcopy(config); single['MULTI_CAMERA_CAPTURE_ENABLE'] = False
    inherited = build_profile_config(single, profiles[0])
    assert inherited['EXPOSURE_PERIOD'] == 90 and inherited['EXPOSURE_PERIOD_DAY'] == 30
    assert exposure_budget(15,40,0.000032,200) == 9
    assert exposure_budget(45,40,0.000032,200) == 39
    assert exposure_budget(45,12,0.000032,200) == 12
    tree = ast.parse((Path(__file__).resolve().parents[1]/'indi_allsky/capture.py').read_text())
    cls = next(node for node in tree.body if isinstance(node,ast.ClassDef) and node.name == 'CaptureWorker')
    names = ('_configured_exposure_period','_limit_exposure_to_cadence','shoot')
    methods = [node for node in cls.body if isinstance(node,ast.FunctionDef) and node.name in names]
    namespace = dict(constants=constants, exposure_budget=exposure_budget, logger=logging.getLogger('test'), time=time)
    exec(compile(ast.Module(body=methods,type_ignores=[]),'<capture-methods>','exec'),namespace)
    # Model a four-second setup/hook delay: the next start must be 15s
    # after the actual request, not 11s after it using a stale loop timestamp.
    frame_start = next(node for node in ast.walk(cls) if isinstance(node,ast.Assign)
                       and any(isinstance(target,ast.Name) and target.id=='frame_start_time' for target in node.targets)
                       and isinstance(node.value,ast.Call)
                       and isinstance(node.value.func,ast.Attribute) and node.lineno>1000)
    timing={'now_time':100.0,'time':SimpleNamespace(time=lambda:104.0)}
    exec(compile(ast.Module(body=[frame_start],type_ignores=[]),'<frame-start-clock>','exec'),timing)
    assert timing['frame_start_time']==104.0
    assert timing['frame_start_time']+15.0==119.0
    worker_type = type('Worker',(),{name:namespace[name] for name in names})
    worker = worker_type()
    worker.config = resolved[0]; worker.focus_mode=False; worker.night=False; worker.moonmode=False
    worker.profile_id='test'; worker._hardware_exposure_max=200
    worker.exposure_av = Array('d', [0.0]*20)
    worker.exposure_av[constants.EXPOSURE_MAX]=40
    worker.exposure_av[constants.EXPOSURE_NEXT]=40
    worker.camera_runtime_state=SimpleNamespace()
    requests=[]
    worker.indiclient=SimpleNamespace(setCcdExposure=lambda *args,**kw:requests.append((args,kw)))
    worker.shoot(40,1.13,1)
    assert requests[-1][0] == (9,1.13,1)
    assert worker.exposure_av[constants.EXPOSURE_MAX] == 9
    worker.night=True
    worker.shoot(40,1.13,1)
    assert requests[-1][0][0] == 39
    worker.shoot(40,1.13,1,sqm_exposure=True)
    assert requests[-1][0][0] == 40  # Scientific SQM remains explicit.
    worker.focus_mode=True
    worker.shoot(40,1.13,1)
    assert requests[-1][0][0] == 40
    # Actual shoot() diagnostics must use the interval selected by the
    # preceding request, in both transition directions, and still report lateness.
    worker.focus_mode = False
    del worker._last_cadence_start
    del worker._last_cadence_period
    clock = iter((100.0, 145.04, 160.04, 180.04, 225.04))
    diagnostic_log = Mock()
    namespace['time'] = SimpleNamespace(monotonic=lambda: next(clock))
    namespace['logger'] = diagnostic_log
    worker.night = True
    worker.shoot(39, 1.13, 1)   # schedules a 45s interval
    worker.night = False
    worker.shoot(9, 1.13, 1)    # timely night-to-day transition
    worker.shoot(9, 1.13, 1)    # timely 15s daytime interval
    assert diagnostic_log.warning.call_count == 0
    worker.night = True
    worker.shoot(39, 1.13, 1)   # 20s after a day request: genuinely late
    assert diagnostic_log.warning.call_count == 1
    assert diagnostic_log.warning.call_args.args[-1] == 15.0
    worker.shoot(39, 1.13, 1)   # timely 45s night interval
    assert diagnostic_log.warning.call_count == 1
    assert requests[-1][0] == (39, 1.13, 1)
    print('Shared cadence: profile isolation, day/night limits, invalid saves and actual driver request cap: PASS')


if __name__ == '__main__': run()
