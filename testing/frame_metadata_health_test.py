import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from indi_allsky.frame_metadata_analytics import FrameMetadataAnalytics


def _write_day(metadata_dir, date, frames):
    metadata_dir.mkdir(parents=True, exist_ok=True)
    with metadata_dir.joinpath('{0:s}.jsonl'.format(date)).open('w', encoding='utf-8') as f_metadata:
        for frame in frames:
            json.dump(frame, f_metadata, sort_keys=True, separators=(',', ':'))
            f_metadata.write('\n')


def _health_frame(frame_id=1, **overrides):
    frame = {
        'frame_id': frame_id,
        'timestamp': '2026-06-21T00:00:00+00:00',
        'camera_id': 2,
        'profile_id': 'asi678mc',
        'image_file_path': '/tmp/{0:d}.jpg'.format(frame_id),
        'exposure_us': 1000,
        'gain': 0.0,
        'meter_value_raw': 94.0,
        'meter_value_smoothed': 95.0,
        'target_meter': 95.0,
        'meter_error': 0.0,
        'auto_exposure_action': 'hold',
        'auto_gain_action': 'hold',
        'decision_reason': 'target_reached',
        'capture_status': 'processed',
        'error_message': '',
        'quality_score': 100.0,
        'quality_flags': ['nominal'],
    }
    frame.update(overrides)
    return frame


def test_metadata_health_complete_rows():
    with tempfile.TemporaryDirectory() as tmpdir:
        metadata_dir = Path(tmpdir)
        _write_day(metadata_dir, '2026-06-21', [
            _health_frame(1),
            _health_frame(2, timestamp='2026-06-21T00:01:00+00:00', quality_score=93.0),
        ])

        report = FrameMetadataAnalytics(metadata_dir).get_metadata_health_report()
        assert report['total_frames_checked'] == 2
        assert report['valid_frames'] == 2
        assert report['invalid_frames'] == 0
        assert report['missing_field_counts'] == {}
        assert report['invalid_value_counts'] == {}
        assert report['quality_coverage_percentage'] == 100.0
        assert report['metadata_completeness_percentage'] == 100.0


def test_metadata_health_reports_legacy_quality_without_invalidating_rows():
    with tempfile.TemporaryDirectory() as tmpdir:
        metadata_dir = Path(tmpdir)
        legacy_frame = _health_frame(1)
        del legacy_frame['quality_score']
        del legacy_frame['quality_flags']
        _write_day(metadata_dir, '2026-06-21', [legacy_frame])

        report = FrameMetadataAnalytics(metadata_dir).get_metadata_health_report()
        assert report['total_frames_checked'] == 1
        assert report['valid_frames'] == 1
        assert report['invalid_frames'] == 0
        assert report['missing_field_counts']['quality_score'] == 1
        assert report['missing_field_counts']['quality_flags'] == 1
        assert report['quality_coverage_percentage'] == 0.0
        assert report['metadata_completeness_percentage'] < 100.0


def test_metadata_health_invalid_values_and_required_missing_fields():
    with tempfile.TemporaryDirectory() as tmpdir:
        metadata_dir = Path(tmpdir)
        invalid_frame = _health_frame(
            1,
            timestamp='not-a-date',
            profile_id='',
            exposure_us=-1,
            gain=-2,
            quality_score=120,
            quality_flags='nominal',
        )
        del invalid_frame['camera_id']
        _write_day(metadata_dir, '2026-06-21', [invalid_frame])

        report = FrameMetadataAnalytics(metadata_dir).get_metadata_health_report('2026-06-21')
        assert report['total_frames_checked'] == 1
        assert report['valid_frames'] == 0
        assert report['invalid_frames'] == 1
        assert report['missing_field_counts']['camera_id'] == 1
        assert report['invalid_value_counts']['timestamp'] == 1
        assert report['invalid_value_counts']['camera_id'] == 1
        assert report['invalid_value_counts']['profile_id'] == 1
        assert report['invalid_value_counts']['exposure_us'] == 1
        assert report['invalid_value_counts']['gain'] == 1
        assert report['invalid_value_counts']['quality_score'] == 1
        assert report['invalid_value_counts']['quality_flags'] == 1


if __name__ == '__main__':
    test_metadata_health_complete_rows()
    test_metadata_health_reports_legacy_quality_without_invalidating_rows()
    test_metadata_health_invalid_values_and_required_missing_fields()
    print('frame metadata health tests OK')
