#!/usr/bin/env python3
"""Numerical highlight metering checks; these are not hardware acceptance."""
from pathlib import Path
import sys
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from indi_allsky.auto_meter import measure_auto_exposure
from indi_allsky.auto_exposure_controller import AutoExposureController
from indi_allsky.capture_profiles import derive_capture_profiles, build_profile_config


def check_closed_loop():
    # A window occupies 10% of an otherwise dim scene. Begin overexposed,
    # then change its illumination. Test both day/night controller policies.
    for day in (False, True):
        controller = AutoExposureController()
        exposure, gain, smoothed = 9.0, 16.0, None
        trend, previous = 0, 0
        clipped = []
        for frame in range(600):
            scene = np.full((20, 20), 10.0)
            scene[:2] = 1000 if frame < 300 else 100
            image = np.clip(scene * exposure * gain, 0, 255).astype(np.uint8)
            measurement = measure_auto_exposure(image, mode='highlight_protected', target=80)
            measured = measurement.measured_value
            smoothed = measured if smoothed is None else .75 * smoothed + .25 * measured
            direction = 1 if 80 - smoothed > 1.5 else -1 if 80 - smoothed < -1.5 else 0
            trend = (trend + 1 if previous == direction else 1) if direction else 0
            previous = direction
            decision = controller.decide(
                smoothed_value=smoothed, measured_value=measured,
                highlight_saturated=measurement.highlight_saturated,
                current_exposure=exposure, current_gain=gain,
                exposure_min=.000032, exposure_max=9, gain_min=1,
                gain_max=16, target=80, trend_count=trend, is_day=day)
            if decision.proposed_exposure < exposure:
                assert gain == 1, 'Reduce gain before exposure'
            if decision.proposed_gain > gain:
                assert exposure == 9, 'Increase exposure before gain'
            exposure, gain = decision.proposed_exposure, decision.proposed_gain
            clipped.append(float(np.mean(image >= 250)))
            if 250 <= frame < 300 or frame >= 550:
                assert abs(measured - 80) <= 1.5, (day, frame, measured)
                assert clipped[-1] <= .01


def check_profiles():
    config = {'MULTI_CAMERA_CAPTURE_ENABLE': True,
              'AUTO_EXPOSURE_HIGHLIGHT_CLIP_PERCENT': 2.0,
              'MULTI_CAMERA': {'profiles': [
                  {'profile_id': 'first', 'enabled': True, 'primary': True,
                   'camera_interface': 'indi', 'auto_exposure': {
                       'metering_mode': 'highlight_protected', 'highlight_clip_percent': .5}},
                  {'profile_id': 'second', 'enabled': True, 'camera_interface': 'indi'}]}}
    profiles = derive_capture_profiles(config)
    first, second = [build_profile_config(config, p) for p in profiles]
    assert first['AUTO_EXPOSURE_HIGHLIGHT_CLIP_PERCENT'] == .5
    assert first['AUTO_EXPOSURE_METERING_MODE'] == 'highlight_protected'
    assert second['AUTO_EXPOSURE_HIGHLIGHT_CLIP_PERCENT'] == 2.0
    assert second['AUTO_EXPOSURE_METERING_MODE'] == 'default'
    assert config['AUTO_EXPOSURE_HIGHLIGHT_CLIP_PERCENT'] == 2.0


def run():
    check_closed_loop()
    check_profiles()
    image = np.full((100, 100, 3), 100, dtype=np.uint8)
    image[:10, :, 2] = 255
    roi = np.zeros((100, 100), dtype=np.uint8)
    roi[40:60, 40:60] = 255
    protected = measure_auto_exposure(image, mask=roi, mode='highlight_protected', target=80)
    assert abs(protected.measured_value - 255 * 80 / 235) < .0001
    assert protected.sample_count == 10000
    # Existing modes still honor the ROI and preserve their target units.
    average = measure_auto_exposure(image, mask=roi, mode='average', target=80)
    assert average.measured_value == 100 and average.sample_count == 400
    image[:] = 100
    image[0, :50] = 255  # Small bright sources below a one-percent budget.
    result = measure_auto_exposure(image, mode='highlight_protected', target=80)
    assert abs(result.measured_value - 100 * 80 / 235) < .0001
    strict = measure_auto_exposure(image, mode='highlight_protected', target=80, highlight_clip_percent=.1)
    assert strict.measured_value > 80
    # Bit depth is the source depth, not necessarily the storage container.
    twelve = np.full((20, 20), 4095, dtype=np.uint16)
    result = measure_auto_exposure(twelve, mode='highlight_protected', target=100, bit_depth=12)
    assert abs(result.measured_value - 255 * 100 / 235) < .0001
    for budget in (0, -1, 11, float('nan'), float('inf')):
        try:
            measure_auto_exposure(image, mode='highlight_protected', highlight_clip_percent=budget)
        except ValueError:
            pass
        else:
            raise AssertionError(budget)
    print('Hybrid highlight metering: PASS')


if __name__ == '__main__':
    run()
