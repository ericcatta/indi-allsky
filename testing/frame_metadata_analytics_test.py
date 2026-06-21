import json
import sys
import tempfile
from datetime import datetime
from datetime import timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from indi_allsky.frame_metadata_analytics import FrameMetadataAnalytics


def _frame(frame_id, timestamp, camera_id, exposure_us, gain, meter_value, exposure_action='hold', gain_action='hold', reason='target_reached', quality_flags=None, capture_status='processed'):
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
        'capture_status': capture_status,
        'error_message': '',
        'quality_score': max(0.0, min(100.0, 100.0 - abs(95.0 - meter_value))),
        'quality_flags': quality_flags if quality_flags is not None else [],
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
        assert summary['average_quality_score'] == 95.0
        assert summary['minimum_quality_score'] == 95.0
        assert summary['maximum_quality_score'] == 95.0


def test_recent_frames_filters_by_timestamp():
    with tempfile.TemporaryDirectory() as tmpdir:
        metadata_dir = Path(tmpdir)
        _write_day(metadata_dir, '2026-06-20', [
            _frame(1, '2026-06-20T23:00:00+00:00', 2, 1000, 0.0, 90.0),
        ])
        _write_day(metadata_dir, '2026-06-21', [
            _frame(2, '2026-06-21T12:00:00+00:00', 2, 2000, 1.0, 95.0),
            _frame(3, '2026-06-21T23:30:00+00:00', 1, 3000, 16.0, 100.0),
        ])

        rows = FrameMetadataAnalytics(metadata_dir).get_recent_frames(
            hours=24,
            now=datetime(2026, 6, 21, 23, 45, tzinfo=timezone.utc),
        )

        assert [row['frame_id'] for row in rows] == [2, 3]


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


def test_nightly_summary_per_camera():
    with tempfile.TemporaryDirectory() as tmpdir:
        metadata_dir = Path(tmpdir)
        _write_day(metadata_dir, '2026-06-21', [
            _frame(1, '2026-06-21T00:00:00+00:00', 2, 1000, 0.0, 95.0, reason='target_reached', quality_flags=['nominal']),
            _frame(2, '2026-06-21T00:01:00+00:00', 2, 3000, 2.0, 40.0, reason='gain_already_max', quality_flags=['meter_far_from_target']),
            _frame(3, '2026-06-21T00:02:00+00:00', 1, 5000, 16.0, 250.0, reason='exposure_and_gain_already_max', quality_flags=['meter_saturated_high']),
            _frame(5, '2026-06-21T00:03:00+00:00', 1, 5200, 16.0, 100.0, reason='target_reached', quality_flags=['nominal']),
            _frame(6, '2026-06-21T00:04:00+00:00', 1, 5300, 16.0, 100.0, reason='target_reached', quality_flags=['nominal']),
            _frame(4, '2026-06-21T00:08:00+00:00', 1, 6000, 16.0, 100.0, reason='bad_image', quality_flags=['capture_not_processed'], capture_status='bad_image'),
        ])

        summary = FrameMetadataAnalytics(metadata_dir).get_nightly_summary('2026-06-21')
        assert summary['date'] == '2026-06-21'
        assert len(summary['cameras']) == 2

        camera_2 = [camera for camera in summary['cameras'] if camera['camera_id'] == '2'][0]
        assert camera_2['frame_count'] == 2
        assert camera_2['profile_id'] == 'asi678mc'
        assert camera_2['average_meter_value'] == 67.5
        assert camera_2['percentages']['nominal_quality'] == 50.0
        assert camera_2['percentages']['low_meter'] == 50.0
        assert camera_2['percentages']['gain_max'] == 50.0
        assert camera_2['most_common_quality_flags'][0]['label'] == 'nominal'
        assert camera_2['missing_frames']['count'] == 0
        assert camera_2['best_frame']['frame_id'] == 1
        assert camera_2['worst_frame']['frame_id'] == 2
        assert camera_2['anomaly_events']['count'] == 3
        assert camera_2['night_trend']['meter']['direction'] == 'down'
        assert camera_2['sky_condition']['sky_condition'] == 'poor'
        assert camera_2['sky_condition']['profile_id'] == 'asi678mc'
        assert camera_2['cloud_condition'] == 'cloudy'
        assert camera_2['sky_trend'] == 'degrading'
        assert camera_2['possible_condensation'] is False

        camera_1 = [camera for camera in summary['cameras'] if camera['camera_id'] == '1'][0]
        assert camera_1['frame_count'] == 4
        assert camera_1['percentages']['high_meter'] == 25.0
        assert camera_1['percentages']['exposure_max'] == 25.0
        assert camera_1['percentages']['gain_max'] == 25.0
        assert camera_1['percentages']['capture_errors'] == 25.0
        assert camera_1['missing_frames']['count'] == 3
        assert camera_1['anomaly_events']['count'] == 5
        assert camera_1['sky_condition']['sky_condition'] == 'unusable'
        assert camera_1['cloud_condition'] == 'unknown'
        assert camera_1['sky_trend'] == 'stable'
        assert camera_1['possible_condensation'] is False


def test_nightly_summary_tolerates_legacy_rows():
    with tempfile.TemporaryDirectory() as tmpdir:
        metadata_dir = Path(tmpdir)
        _write_day(metadata_dir, '2026-06-21', [
            {
                'frame_id': 1,
                'timestamp': '2026-06-21T00:00:00+00:00',
                'camera_id': 2,
                'profile_id': 'asi678mc',
                'exposure_us': 1000,
                'gain': 0.0,
                'meter_value_smoothed': 90.0,
                'target_meter': 95.0,
                'decision_reason': 'target_reached',
                'capture_status': 'processed',
            },
        ])

        summary = FrameMetadataAnalytics(metadata_dir).get_nightly_summary('2026-06-21')
        assert summary['cameras'][0]['frame_count'] == 1
        assert summary['cameras'][0]['average_quality_score'] is None
        assert summary['cameras'][0]['percentages']['capture_errors'] == 0.0


if __name__ == '__main__':
    test_load_day()
    test_latest_frames_across_days()
    test_camera_summary()
    test_recent_frames_filters_by_timestamp()
    test_multi_camera_statistics_and_decision_counts()
    test_nightly_summary_per_camera()
    test_nightly_summary_tolerates_legacy_rows()
    print('frame metadata analytics tests OK')
