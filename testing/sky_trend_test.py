import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from indi_allsky.sky_trend import classify_sky_trend


def _frame(frame_id, quality_score=None, camera_id=2, profile_id='asi678mc', timestamp=None, **extra):
    frame = {
        'frame_id': frame_id,
        'timestamp': timestamp or '2026-06-21T00:{0:02d}:00+00:00'.format(frame_id),
        'camera_id': camera_id,
        'profile_id': profile_id,
        'capture_status': 'processed',
        'quality_flags': [],
    }
    if quality_score is not None:
        frame['quality_score'] = quality_score
    frame.update(extra)
    return frame


def test_empty_series_is_unknown():
    assert classify_sky_trend([]) == 'unknown'


def test_single_frame_is_unknown():
    assert classify_sky_trend([_frame(1, 80)]) == 'unknown'


def test_obvious_improvement_is_improving():
    assert classify_sky_trend([
        _frame(1, 42),
        _frame(2, 48),
        _frame(3, 78),
        _frame(4, 85),
    ]) == 'improving'


def test_obvious_degradation_is_degrading():
    assert classify_sky_trend([
        _frame(1, 86),
        _frame(2, 79),
        _frame(3, 48),
        _frame(4, 40),
    ]) == 'degrading'


def test_small_variation_is_stable():
    assert classify_sky_trend([
        _frame(1, 76),
        _frame(2, 78),
        _frame(3, 80),
        _frame(4, 77),
    ]) == 'stable'


def test_incomplete_metadata_is_unknown():
    assert classify_sky_trend([
        _frame(1, None),
        _frame(2, None),
    ]) == 'unknown'


def test_mixed_camera_series_is_unknown():
    assert classify_sky_trend([
        _frame(1, 40, camera_id=2),
        _frame(2, 80, camera_id=1),
    ]) == 'unknown'


def test_mixed_profile_series_is_unknown():
    assert classify_sky_trend([
        _frame(1, 40, profile_id='asi678mc'),
        _frame(2, 80, profile_id='imx708-wide'),
    ]) == 'unknown'


def test_sky_condition_fallback_can_drive_trend():
    assert classify_sky_trend([
        _frame(1, None, sky_condition={'sky_condition': 'poor'}),
        _frame(2, None, sky_condition={'sky_condition': 'good'}),
    ]) == 'improving'


def test_cloud_condition_fallback_can_drive_trend():
    assert classify_sky_trend([
        _frame(1, None, cloud_condition='mostly_clear'),
        _frame(2, None, cloud_condition='cloudy'),
    ]) == 'degrading'


if __name__ == '__main__':
    test_empty_series_is_unknown()
    test_single_frame_is_unknown()
    test_obvious_improvement_is_improving()
    test_obvious_degradation_is_degrading()
    test_small_variation_is_stable()
    test_incomplete_metadata_is_unknown()
    test_mixed_camera_series_is_unknown()
    test_mixed_profile_series_is_unknown()
    test_sky_condition_fallback_can_drive_trend()
    test_cloud_condition_fallback_can_drive_trend()
    print('sky trend tests OK')
