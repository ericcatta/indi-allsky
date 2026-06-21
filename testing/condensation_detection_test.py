import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from indi_allsky.condensation_detection import detect_possible_condensation


def _frame(frame_id, quality_score, exposure_us=1000000, gain=10.0, camera_id=2, profile_id='asi678mc', quality_flags=None, capture_status='processed'):
    return {
        'frame_id': frame_id,
        'timestamp': '2026-06-21T00:{0:02d}:00+00:00'.format(frame_id),
        'camera_id': camera_id,
        'profile_id': profile_id,
        'capture_status': capture_status,
        'quality_score': quality_score,
        'quality_flags': quality_flags if quality_flags is not None else [],
        'exposure_us': exposure_us,
        'gain': gain,
    }


def test_empty_series_is_false():
    assert detect_possible_condensation([]) is False


def test_single_frame_is_false():
    assert detect_possible_condensation([_frame(1, 80)]) is False


def test_small_quality_degradation_is_false():
    assert detect_possible_condensation([
        _frame(1, 90),
        _frame(2, 88),
        _frame(3, 84),
        _frame(4, 80),
    ]) is False


def test_cloudiness_without_exposure_gain_or_flags_is_false():
    assert detect_possible_condensation([
        _frame(1, 95, exposure_us=1000000, gain=10),
        _frame(2, 85, exposure_us=1000000, gain=10),
        _frame(3, 55, exposure_us=1000000, gain=10),
        _frame(4, 38, exposure_us=1000000, gain=10),
    ]) is False


def test_persistent_degradation_with_exposure_gain_is_true():
    assert detect_possible_condensation([
        _frame(1, 94, exposure_us=1000000, gain=10),
        _frame(2, 82, exposure_us=1300000, gain=12),
        _frame(3, 54, exposure_us=1800000, gain=18, quality_flags=['meter_off_target']),
        _frame(4, 34, exposure_us=2500000, gain=25, quality_flags=['meter_far_from_target']),
    ]) is True


def test_failed_capture_is_false():
    assert detect_possible_condensation([
        _frame(1, 94, exposure_us=1000000, gain=10),
        _frame(2, 82, exposure_us=1300000, gain=12),
        _frame(3, 54, exposure_us=1800000, gain=18),
        _frame(4, 34, exposure_us=2500000, gain=25, capture_status='bad_image'),
    ]) is False


def test_mixed_camera_series_is_false():
    assert detect_possible_condensation([
        _frame(1, 94, camera_id=2),
        _frame(2, 82, camera_id=2),
        _frame(3, 54, camera_id=1),
        _frame(4, 34, camera_id=1),
    ]) is False


def test_mixed_profile_series_is_false():
    assert detect_possible_condensation([
        _frame(1, 94, profile_id='asi678mc'),
        _frame(2, 82, profile_id='asi678mc'),
        _frame(3, 54, profile_id='imx708-wide'),
        _frame(4, 34, profile_id='imx708-wide'),
    ]) is False


if __name__ == '__main__':
    test_empty_series_is_false()
    test_single_frame_is_false()
    test_small_quality_degradation_is_false()
    test_cloudiness_without_exposure_gain_or_flags_is_false()
    test_persistent_degradation_with_exposure_gain_is_true()
    test_failed_capture_is_false()
    test_mixed_camera_series_is_false()
    test_mixed_profile_series_is_false()
    print('condensation detection tests OK')
