import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from indi_allsky.frame_quality import compute_frame_quality


def test_quality_nominal_frame():
    score, flags = compute_frame_quality(
        meter_value=94.5,
        target_meter=95.0,
        exposure_us=21686,
        gain=220.0,
        auto_exposure_action='hold',
        auto_gain_action='hold',
        decision_reason='target_reached',
        capture_status='processed',
    )

    assert score == 100.0
    assert flags == ['nominal']


def test_quality_penalizes_meter_far_from_target():
    score, flags = compute_frame_quality(
        meter_value=250.0,
        target_meter=95.0,
        exposure_us=21686,
        gain=220.0,
        auto_exposure_action='decrease_exposure',
        auto_gain_action='hold',
        decision_reason='aggressive_decrease_exposure',
        capture_status='processed',
    )

    assert score < 60.0
    assert 'meter_saturated_high' in flags
    assert 'meter_far_from_target' in flags
    assert 'exposure_adjusting' in flags


def test_quality_penalizes_capture_errors():
    score, flags = compute_frame_quality(
        meter_value=None,
        target_meter=95.0,
        exposure_us=0,
        gain=None,
        auto_exposure_action='unknown',
        auto_gain_action='unknown',
        decision_reason='',
        capture_status='bad_image',
        error_message='bad image data',
    )

    assert score == 0.0
    assert 'capture_not_processed' in flags
    assert 'capture_error' in flags
    assert 'meter_missing' in flags
    assert 'exposure_invalid' in flags
    assert 'gain_missing' in flags


if __name__ == '__main__':
    test_quality_nominal_frame()
    test_quality_penalizes_meter_far_from_target()
    test_quality_penalizes_capture_errors()
    print('frame quality tests OK')
