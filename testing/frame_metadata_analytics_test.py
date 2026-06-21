import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from indi_allsky.frame_metadata_analytics import FrameMetadataAnalytics


def _frame(frame_id, timestamp, camera_id, exposure_us, gain, meter_value, exposure_action='hold', gain_action='hold', reason='target_reached'):
    return {
        'frame_id': frame_id,
        'timestamp': timestamp,
        'camera_id': camera_id,
        'profile_id': 'asi678mc' if camera_id == 2 else 'imx708-wide',
        'image_file_path': '/tmp/{0:d}.jpg'.format(frame_id),
        'exposure_us': exposure_us,
        'gain': gain,
        'meter_value_raw': meter_value,
        'meter_value_smoothed': meter_value,
        'target_meter': 95.0,
        'meter_error': 95.0 - meter_value,
        'auto_exposure_action': exposure_action,
        'auto_gain_action': gain_action,
        'decision_reason': reason,
        'capture_status': 'processed',
        'error_message': '',
        'quality_score': 0.0,
        'quality_flags': [],
    }


def _write_day(metadata_dir, date, frames):
    metadata_dir.mkdir(parents=True, exist_ok=True)
    with metadata_dir.joinpath('{0:s}.jsonl'.format(date)).open('w', encoding='utf-8') as f_metadata:
        for frame in frames:
            json.dump(frame, f_metadata, sort_keys=True, separators=(',', ':'))
            f_metadata.write('\n')


def test_load_day():
    with tempfile.TemporaryDirectory() as tmpdir:
        metadata_dir = Path(tmpdir)
        _write_day(metadata_dir, '2026-06-21', [
            _frame(1, '2026-06-21T00:00:00+00:00', 2, 1000, 0.0, 90.0),
            _frame(2, '2026-06-21T00:01:00+00:00', 2, 2000, 1.0, 95.0),
        ])

        rows = FrameMetadataAnalytics(metadata_dir).load_day('2026-06-21')
        assert len(rows) == 2
        assert rows[0]['frame_id'] == 1
        assert rows[1]['frame_id'] == 2


def test_latest_frames_across_days():
    with tempfile.TemporaryDirectory() as tmpdir:
        metadata_dir = Path(tmpdir)
        _write_day(metadata_dir, '2026-06-21', [
            _frame(1, '2026-06-21T00:00:00+00:00', 2, 1000, 0.0, 90.0),
            _frame(2, '2026-06-21T00:01:00+00:00', 2, 2000, 1.0, 95.0),
        ])
        _write_day(metadata_dir, '2026-06-22', [
            _frame(3, '2026-06-22T00:00:00+00:00', 1, 3000, 2.0, 100.0),
            _frame(4, '2026-06-22T00:01:00+00:00', 1, 4000, 3.0, 105.0),
        ])

        rows = FrameMetadataAnalytics(metadata_dir).get_latest_frames(limit=3)
        assert [row['frame_id'] for row in rows] == [4, 3, 2]


def test_camera_summary():
    with tempfile.TemporaryDirectory() as tmpdir:
        metadata_dir = Path(tmpdir)
        _write_day(metadata_dir, '2026-06-21', [
            _frame(1, '2026-06-21T00:00:00+00:00', 2, 1000, 0.0, 90.0),
            _frame(2, '2026-06-21T00:01:00+00:00', 2, 3000, 2.0, 100.0),
            _frame(3, '2026-06-21T00:02:00+00:00', 1, 5000, 16.0, 120.0),
        ])

        summary = FrameMetadataAnalytics(metadata_dir).get_camera_summary(camera_id=2)
        assert summary['frame_count'] == 2
        assert summary['first_timestamp'] == '2026-06-21T00:00:00+00:00'
        assert summary['last_timestamp'] == '2026-06-21T00:01:00+00:00'
        assert summary['average_exposure'] == 2000.0
        assert summary['minimum_exposure'] == 1000.0
        assert summary['maximum_exposure'] == 3000.0
        assert summary['average_gain'] == 1.0
        assert summary['minimum_gain'] == 0.0
        assert summary['maximum_gain'] == 2.0
        assert summary['average_meter_value'] == 95.0
        assert summary['minimum_meter_value'] == 90.0
        assert summary['maximum_meter_value'] == 100.0


def test_multi_camera_statistics_and_decision_counts():
    with tempfile.TemporaryDirectory() as tmpdir:
        metadata_dir = Path(tmpdir)
        _write_day(metadata_dir, '2026-06-21', [
            _frame(1, '2026-06-21T00:00:00+00:00', 2, 1000, 0.0, 90.0, exposure_action='increase_exposure', gain_action='hold', reason='too_dark'),
            _frame(2, '2026-06-21T00:01:00+00:00', 2, 3000, 2.0, 100.0, exposure_action='hold', gain_action='increase_gain', reason='target_reached'),
            _frame(3, '2026-06-21T00:02:00+00:00', 1, 5000, 16.0, 120.0, exposure_action='decrease_exposure', gain_action='hold', reason='too_bright'),
        ])

        analytics = FrameMetadataAnalytics(metadata_dir)
        camera_1 = analytics.get_camera_summary(camera_id=1)
        camera_2 = analytics.get_camera_summary(camera_id=2)
        assert camera_1['frame_count'] == 1
        assert camera_2['frame_count'] == 2

        stats = analytics.get_decision_statistics()
        assert stats['auto_exposure_action']['increase_exposure'] == 1
        assert stats['auto_exposure_action']['decrease_exposure'] == 1
        assert stats['auto_gain_action']['hold'] == 2
        assert stats['decision_reason']['target_reached'] == 1

        camera_stats = analytics.get_decision_statistics(camera_id=2)
        assert camera_stats['auto_exposure_action']['hold'] == 1
        assert 'too_bright' not in camera_stats['decision_reason']


if __name__ == '__main__':
    test_load_day()
    test_latest_frames_across_days()
    test_camera_summary()
    test_multi_camera_statistics_and_decision_counts()
    print('frame metadata analytics tests OK')
