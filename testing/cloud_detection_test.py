import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from indi_allsky.cloud_detection import classify_cloud_condition


def _metadata(sky_condition=None, quality_score=None, quality_flags=None, capture_status='processed'):
    metadata = {
        'profile_id': 'asi678mc',
        'camera_id': 2,
        'capture_status': capture_status,
        'quality_flags': quality_flags if quality_flags is not None else [],
    }
    if sky_condition is not None:
        metadata['sky_condition'] = sky_condition
    if quality_score is not None:
        metadata['quality_score'] = quality_score
    return metadata


def test_unknown_when_metadata_is_incomplete():
    assert classify_cloud_condition({'profile_id': 'asi678mc', 'camera_id': 2}) == 'unknown'


def test_failed_capture_is_unknown():
    assert classify_cloud_condition(_metadata('excellent', 98, capture_status='bad_image')) == 'unknown'


def test_excellent_sky_maps_to_clear():
    assert classify_cloud_condition(_metadata('excellent', 96)) == 'clear'


def test_good_sky_maps_to_mostly_clear():
    assert classify_cloud_condition(_metadata('good', 82)) == 'mostly_clear'


def test_usable_sky_maps_to_partly_cloudy():
    assert classify_cloud_condition(_metadata('usable', 63)) == 'partly_cloudy'


def test_poor_sky_maps_to_cloudy():
    assert classify_cloud_condition(_metadata('poor', 42)) == 'cloudy'


def test_unusable_low_quality_maps_to_overcast():
    assert classify_cloud_condition(_metadata('unusable', 22)) == 'overcast'


def test_severe_flag_makes_good_sky_partly_cloudy():
    assert classify_cloud_condition(_metadata('good', 86, ['meter_far_from_target'])) == 'partly_cloudy'


def test_dict_sky_condition_is_supported():
    assert classify_cloud_condition(_metadata({'sky_condition': 'excellent'}, 94)) == 'clear'


def test_quality_metadata_can_drive_sky_condition_fallback():
    assert classify_cloud_condition({
        'profile_id': 'imx708-wide',
        'camera_id': 1,
        'capture_status': 'processed',
        'quality_score': 79,
        'quality_flags': [],
    }) == 'mostly_clear'


if __name__ == '__main__':
    test_unknown_when_metadata_is_incomplete()
    test_failed_capture_is_unknown()
    test_excellent_sky_maps_to_clear()
    test_good_sky_maps_to_mostly_clear()
    test_usable_sky_maps_to_partly_cloudy()
    test_poor_sky_maps_to_cloudy()
    test_unusable_low_quality_maps_to_overcast()
    test_severe_flag_makes_good_sky_partly_cloudy()
    test_dict_sky_condition_is_supported()
    test_quality_metadata_can_drive_sky_condition_fallback()
    print('cloud detection tests OK')
