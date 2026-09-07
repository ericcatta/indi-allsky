#!/usr/bin/env python3
"""Exercise real worker ADU and apply methods without loading hardware libraries."""
import ast
import bisect
import copy
import functools
import logging
from multiprocessing import Array
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from indi_allsky import constants
from indi_allsky.auto_exposure_controller import AutoExposureController


def worker(enabled, minimum, gain):
    path = Path(__file__).resolve().parents[1] / 'indi_allsky/image.py'
    tree = ast.parse(path.read_text())
    names = {'calculate_exposure', 'recalculate_exposure',
             '_apply_auto_exposure_decision', '_clamp_auto_exposure_apply_value',
             '_auto_exposure_enabled'}
    cls = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == 'ImageWorker')
    methods = [n for n in cls.body if isinstance(n, ast.FunctionDef) and n.name in names]
    assert len(methods) == len(names)
    namespace = dict(constants=constants, copy=copy, functools=functools,
                     bisect=bisect, logger=logging.getLogger('pipeline-test'))
    exec(compile(ast.Module(body=methods, type_ignores=[]), str(path), 'exec'), namespace)
    Worker = type('Worker', (), {name: namespace[name] for name in names})
    w = Worker()
    w.config = dict(AUTO_EXPOSURE_ENABLED=enabled, TARGET_ADU=80, TARGET_ADU_DAY=80)
    w.exposure_av = Array('d', [9, 9, 0, .000032, .000032, 9, 0])
    w.gain_av = Array('d', [gain, gain, 0, minimum, 16, minimum, 16, minimum, 16, 0])
    w.binning_av = Array('i', [1] * 6)
    w.night_av = [0, 0]
    w.current_adu_target = 80
    w.target_adu_found = False
    w.hist_adu = []
    w._log_adu_diag = lambda *args: None
    w._auto_gain_enabled = lambda: False
    w._save_auto_gain_runtime_state = lambda *args: None
    w._adu_key = lambda profile, camera: (profile, camera)
    w.profile_id = 'test'
    w.camera_id = 1
    w._auto_gain_mode = lambda: 'day'
    return w


def run():
    for minimum in (0, 1.13):
        for gain, measured, expected in ((minimum + 1, 80, 'hold'),
                                         (minimum + 1, 160, 'decrease_gain'),
                                         (minimum, 160, 'decrease_exposure')):
            w = worker(True, minimum, gain)
            decision = AutoExposureController().decide(
                smoothed_value=measured, current_exposure=9, current_gain=gain,
                exposure_min=.000032, exposure_max=9, gain_min=minimum,
                gain_max=16, target=80, trend_count=10, is_day=True,
                day_step_factor=.35, day_min_step=.00025, day_max_step=.005,
                allow_gain_control=True)
            assert decision.action == expected
            w.auto_meter_states = {('test', 1): dict(last_decision=decision,
                                                   smoothed_value=measured, mode='day')}
            # Legacy ADU disagrees with Hybrid metering, as in the observed bug.
            adu, average = w.calculate_exposure(160, 9, gain)
            assert (adu, average) == (160, 0)
            assert w.exposure_av[constants.EXPOSURE_NEXT] == 9
            assert w.gain_av[constants.GAIN_NEXT] == gain
            w._apply_auto_exposure_decision('test', 1)
            assert w.exposure_av[constants.EXPOSURE_NEXT] == decision.proposed_exposure
            assert w.gain_av[constants.GAIN_NEXT] == decision.proposed_gain
            # Tracking brightness stability remains available for mask generation.
            w.calculate_exposure(80, 9, gain)
            assert w.target_adu_found and w.current_adu_target == 80
    legacy = worker(False, 0, 0)
    legacy.calculate_exposure(160, 9, 0)
    assert legacy.exposure_av[constants.EXPOSURE_NEXT] == 4.5
    print('Hybrid exposure pipeline: PASS')


if __name__ == '__main__':
    run()
