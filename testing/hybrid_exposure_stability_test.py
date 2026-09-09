#!/usr/bin/env python3
"""Closed-loop exposure tests with a constant-scene linear sensor model.

This model demonstrates controller stability, not physical camera acceptance.
"""
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from indi_allsky.auto_exposure_controller import AutoExposureController


def simulate(illumination, *, latest=True, day=False):
    controller = AutoExposureController()
    exposure, gain, smoothed = 9.0, 1.0, None
    trend, previous_direction = 0, 0
    values = []
    for frame in range(400):
        light = illumination(frame) if callable(illumination) else illumination
        measured = min(255.0, light * exposure * gain)
        smoothed = measured if smoothed is None else .75 * smoothed + .25 * measured
        error = 80 - smoothed
        direction = 1 if error > 1.5 else -1 if error < -1.5 else 0
        trend = (trend + 1 if previous_direction == direction else 1) if direction else 0
        previous_direction = direction
        decision = controller.decide(
            smoothed_value=smoothed, measured_value=measured if latest else None,
            current_exposure=exposure, current_gain=gain,
            exposure_min=.000032, exposure_max=9, gain_min=1, gain_max=16,
            target=80, trend_count=trend, is_day=day,
        )
        assert .000032 <= decision.proposed_exposure <= 9
        assert 1 <= decision.proposed_gain <= 16
        if decision.proposed_exposure < exposure:
            assert gain == 1, 'Must reduce gain before exposure'
        if decision.proposed_gain > gain:
            assert exposure == 9, 'Must increase exposure before gain'
        exposure, gain = decision.proposed_exposure, decision.proposed_gain
        values.append(measured)
    return values


def run():
    # The original path oscillates indefinitely despite a constant scene.
    for light in (100, 1000):
        old = simulate(light, latest=False)[-100:]
        new = simulate(light)[-100:]
        assert max(old) - min(old) > 30, (light, min(old), max(old))
        assert max(new) - min(new) < .01, (light, min(new), max(new))
        assert all(abs(value - 80) <= 1.5 for value in new)
    for day in (False, True):
        for light in (5, 100, 1000):
            values = simulate(light, day=day)
            assert all(abs(value - 80) <= 1.5 for value in values[-50:])
        # Saturation recovery and a large illumination change still converge.
        values = simulate(lambda frame: 5 if frame < 180 else 1000, day=day)
        assert all(abs(value - 80) <= 1.5 for value in values[-50:])

    controller = AutoExposureController()
    kwargs = dict(smoothed_value=100, current_exposure=1, current_gain=1,
                  exposure_min=.000032, exposure_max=9, gain_min=1,
                  gain_max=16, target=80)
    baseline = controller.decide(**kwargs)
    for missing in (None, float('nan'), float('inf'), -1, 'bad'):
        assert controller.decide(**kwargs, measured_value=missing) == baseline
    held = controller.decide(**kwargs, measured_value=80)
    assert held.action == 'hold' and held.proposed_exposure == 1
    assert held.reason == 'latest_frame_target_reached'
    # Direct severe overexposure retains the existing fast bounded response.
    saturated = controller.decide(**dict(kwargs, smoothed_value=255,
                                        current_exposure=6.7), measured_value=255)
    assert saturated.proposed_exposure == 3.35
    print('Hybrid exposure stability: PASS')


if __name__ == '__main__':
    run()
