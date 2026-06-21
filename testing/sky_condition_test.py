import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from indi_allsky.sky_condition import compute_sky_condition
from indi_allsky.sky_condition import compute_sky_condition_from_frame


def test_unknown_when_metadata_is_insufficient():
    condition = compute_sky_condition(profile_id='asi678mc', camera_id=2)
    assert condition['sky_condition'] == 'unknown'
    assert condition['reason'] == 'insufficient_metadata'
    assert condition['profile_id'] == 'asi678mc'
    assert condition['camera_id'] == '2'


def test_quality_score_maps_to_conditions():
    assert compute_sky_condition(quality_score=95, capture_status='processed')['sky_condition'] == 'excellent'
    assert compute_sky_condition(quality_score=80, capture_status='processed')['sky_condition'] == 'good'
    assert compute_sky_condition(quality_score=60, capture_status='processed')['sky_condition'] == 'usable'
    assert compute_sky_condition(quality_score=40, capture_status='processed')['sky_condition'] == 'poor'
    assert compute_sky_condition(quality_score=20, capture_status='processed')['sky_condition'] == 'unusable'


def test_capture_error_overrides_quality_score():
    condition = compute_sky_condition(
        quality_score=100,
        quality_flags=['nominal'],
        capture_status='bad_image',
    )
    assert condition['sky_condition'] == 'unusable'
    assert condition['reason'] == 'capture_status_not_processed'


def test_critical_quality_flag_overrides_quality_score():
    condition = compute_sky_condition(
        quality_score=100,
        quality_flags=['capture_not_processed'],
        capture_status='processed',
    )
    assert condition['sky_condition'] == 'unusable'
    assert condition['reason'] == 'critical_quality_flag'


def test_severe_quality_flag_caps_condition_at_poor():
    condition = compute_sky_condition(
        quality_score=96,
        quality_flags=['meter_saturated_high'],
        capture_status='processed',
    )
    assert condition['sky_condition'] == 'poor'
    assert condition['reason'] == 'severe_quality_flag'


def test_warning_quality_flag_caps_condition_at_usable():
    condition = compute_sky_condition(
        quality_score=96,
        quality_flags=['meter_off_target'],
        capture_status='processed',
    )
    assert condition['sky_condition'] == 'usable'
    assert condition['reason'] == 'warning_quality_flag'


def test_meter_fallback_when_quality_score_is_missing():
    condition = compute_sky_condition(
        meter_value=92,
        target_meter=95,
        capture_status='processed',
    )
    assert condition['sky_condition'] == 'excellent'
    assert condition['reason'] == 'quality_score'


def test_frame_helper_preserves_profile_and_camera_identity():
    condition = compute_sky_condition_from_frame({
        'profile_id': 'imx708-wide',
        'camera_id': 1,
        'quality_score': 78,
        'quality_flags': [],
        'capture_status': 'processed',
        'meter_value_smoothed': 90,
        'target_meter': 95,
    })
    assert condition['sky_condition'] == 'good'
    assert condition['profile_id'] == 'imx708-wide'
    assert condition['camera_id'] == '1'


if __name__ == '__main__':
    test_unknown_when_metadata_is_insufficient()
    test_quality_score_maps_to_conditions()
    test_capture_error_overrides_quality_score()
    test_critical_quality_flag_overrides_quality_score()
    test_severe_quality_flag_caps_condition_at_poor()
    test_warning_quality_flag_caps_condition_at_usable()
    test_meter_fallback_when_quality_score_is_missing()
    test_frame_helper_preserves_profile_and_camera_identity()
    print('sky condition tests OK')
