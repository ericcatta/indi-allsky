#!/usr/bin/env python3
"""Exercise actual exposure recalculation with on-grid parity and off-grid gains."""
import ast
import bisect
import copy
from contextlib import nullcontext
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from indi_allsky import constants

class Shared(dict):
    def get_lock(self):return nullcontext()

def load(path, method=False):
    tree=ast.parse(path.read_text())
    if method:
        cls=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='ImageWorker')
        fn=next(n for n in cls.body if isinstance(n,ast.FunctionDef) and n.name=='recalculate_exposure')
        tree=ast.Module(body=[fn],type_ignores=[])
    env={'bisect':bisect,'constants':constants,'copy':copy,'logger':Mock()}
    exec(compile(tree,str(path),'exec'),env)
    return env['recalculate_exposure']

def calculate(fn,gain,exposure,adu,steps):
    worker=SimpleNamespace(_auto_gain_enabled=lambda:True,_auto_gain_limits=lambda:(steps[0],steps[-1]),
        auto_gain_step_list=steps,auto_gain_exposure_cutoff_low=32,auto_gain_exposure_cutoff_mid=35.75,
        auto_gain_exposure_cutoff_high=39.5,profile_id='test',camera_id=1,
        _auto_gain_mode=lambda:'night',_save_auto_gain_runtime_state=Mock(),
        night_av={constants.NIGHT_NIGHT:1,constants.NIGHT_MOONMODE:0},
        exposure_av=Shared({constants.EXPOSURE_MIN_NIGHT:.001,constants.EXPOSURE_MAX:40,constants.EXPOSURE_DELTA:0}),
        gain_av=Shared({constants.GAIN_NEXT:gain}),binning_av=Shared({constants.BINNING_NIGHT:1}))
    fn(worker,exposure,gain,adu,50,45,55,1)
    return dict(worker.exposure_av),dict(worker.gain_av),dict(worker.binning_av)

def run():
    actual=load(ROOT/'indi_allsky/image.py',True)
    legacy=load(ROOT/'testing/fixtures/legacy_auto_gain_recalculate.py')
    steps=[1.13,4.85,8.56,12.28,16.0]
    for gain in steps:
        for exposure in (1,32,39.5,40):
            for adu in (10,80):
                assert calculate(actual,gain,exposure,adu,steps)==calculate(legacy,gain,exposure,adu,steps)
    # Previously index fallback 0 caused -1 to select maximum when dimming.
    for gain in (1.2,4.9,8.5,12.3,15.999):
        down=calculate(actual,gain,1,80,steps)[1][constants.GAIN_NEXT]
        up=calculate(actual,gain,39.5,10,steps)[1][constants.GAIN_NEXT]
        assert down<gain<up,(gain,down,up)
        assert down in steps and up in steps
    assert calculate(legacy,8.5,1,80,steps)[1][constants.GAIN_NEXT]==16
    for gain in (0,16.001,100):
        for adu in (10,80):
            result=calculate(actual,gain,1 if adu==80 else 39.5,adu,steps)[1][constants.GAIN_NEXT]
            assert steps[0]<=result<=steps[-1]
    print('Legacy Auto Gain: 40 on-grid parity cases, off-grid direction, bounded extremes and reproduced old wraparound: PASS')

if __name__=='__main__':run()
