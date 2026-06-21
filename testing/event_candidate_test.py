import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from indi_allsky.event_candidate import EventCandidate
from indi_allsky.event_candidate import EventCandidateAnalytics
from indi_allsky.event_candidate import EventCandidateWriter
from indi_allsky.event_candidate import EventTimelineAnalytics
from indi_allsky.event_candidate import EventTimelineSegment
from indi_allsky.event_candidate import EventTimelineWriter
from indi_allsky.event_candidate import build_event_candidate_from_metadata
from indi_allsky.event_candidate import build_event_timeline_segments
from indi_allsky.event_candidate import default_event_candidate_dir
from indi_allsky.event_candidate import default_event_timeline_dir


def _candidate(candidate_id='asi678mc:2:42', camera_id=2, profile_id='asi678mc', frame_id=42, score=12.5, reasons=None, timestamp='2026-06-21T22:15:00+00:00'):
    return EventCandidate(
        candidate_id=candidate_id,
        camera_id=camera_id,
        profile_id=profile_id,
        frame_id=frame_id,
        timestamp_utc=timestamp,
        night_id=timestamp[:10],
        candidate_score=score,
        reasons=reasons if reasons is not None else ['low_quality'],
        source_metrics={
            'meter_value_smoothed': 43.0,
            'target_meter': 95.0,
            'exposure_us': 14000000,
            'gain': 300.0,
        },
        quality_context={
            'quality_score': 42.0,
            'quality_flags': ['low_meter'],
        },
        environment_context={
            'sky_condition': 'poor',
            'cloud_condition': 'cloudy',
            'sky_trend': 'degrading',
            'possible_condensation': False,
        },
    )


def _write_candidates(candidate_dir, date, candidates):
    candidate_dir.mkdir(parents=True, exist_ok=True)
    with candidate_dir.joinpath('{0:s}.jsonl'.format(date)).open('w', encoding='utf-8') as f_candidate:
        for candidate in candidates:
            json.dump(candidate.to_dict(), f_candidate, sort_keys=True, separators=(',', ':'))
            f_candidate.write('\n')


def test_event_candidate_v0_serialization():
    row = _candidate().to_dict()

    assert row['schema_version'] == 'event_candidate_v0'
    assert row['candidate_type'] == 'unclassified'
    assert row['shadow_only'] is True
    assert row['camera_id'] == 2
    assert row['profile_id'] == 'asi678mc'
    assert row['quality_context']['quality_score'] == 42.0
    assert row['environment_context']['cloud_condition'] == 'cloudy'


def test_candidate_type_is_always_unclassified():
    candidate = _candidate()
    candidate.candidate_type = 'meteor'
    candidate.__post_init__()

    assert candidate.to_dict()['candidate_type'] == 'unclassified'


def test_event_candidate_jsonl_persistence():
    with tempfile.TemporaryDirectory() as tmpdir:
        candidate_dir = Path(tmpdir).joinpath('event_candidates')
        writer = EventCandidateWriter(candidate_dir)

        written_path = writer.write(_candidate())

        assert written_path == candidate_dir.joinpath('2026-06-21.jsonl')
        rows = written_path.read_text(encoding='utf-8').splitlines()
        assert len(rows) == 1
        row = json.loads(rows[0])
        assert row['candidate_id'] == 'asi678mc:2:42'
        assert row['candidate_type'] == 'unclassified'


def test_event_candidate_default_directory():
    with tempfile.TemporaryDirectory() as tmpdir:
        assert default_event_candidate_dir(tmpdir) == Path(tmpdir).joinpath('event_candidates')


def test_event_candidate_multi_camera_fields_preserved():
    with tempfile.TemporaryDirectory() as tmpdir:
        candidate_dir = Path(tmpdir)
        writer = EventCandidateWriter(candidate_dir)

        writer.write(_candidate(camera_id=1, profile_id='imx708-wide', frame_id=11, candidate_id='imx708-wide:1:11'))
        writer.write(_candidate(camera_id=2, profile_id='asi678mc', frame_id=22, candidate_id='asi678mc:2:22'))

        rows = [json.loads(line) for line in candidate_dir.joinpath('2026-06-21.jsonl').read_text(encoding='utf-8').splitlines()]
        assert rows[0]['camera_id'] == 1
        assert rows[0]['profile_id'] == 'imx708-wide'
        assert rows[1]['camera_id'] == 2
        assert rows[1]['profile_id'] == 'asi678mc'


def test_event_candidate_nightly_analytics_counts():
    with tempfile.TemporaryDirectory() as tmpdir:
        candidate_dir = Path(tmpdir)
        _write_candidates(candidate_dir, '2026-06-21', [
            _candidate(camera_id=2, profile_id='asi678mc', frame_id=1, score=10.0, reasons=['low_quality', 'high_meter']),
            _candidate(camera_id=2, profile_id='asi678mc', frame_id=2, score=20.0, reasons=['low_quality']),
            _candidate(camera_id=1, profile_id='imx708-wide', frame_id=3, score=40.0, reasons=['capture_error']),
        ])

        summary = EventCandidateAnalytics(candidate_dir).get_nightly_event_summary('2026-06-21')

        assert summary['total_event_candidates'] == 3
        assert summary['event_candidates_by_camera'] == {'1': 1, '2': 2}
        assert summary['event_candidates_by_reason']['low_quality'] == 2
        assert summary['event_candidates_by_reason']['capture_error'] == 1
        assert summary['average_candidate_score'] == 70.0 / 3.0
        assert summary['max_candidate_score'] == 40.0


def test_placeholder_builder_is_disabled_without_reasons():
    assert build_event_candidate_from_metadata({
        'frame_id': 42,
        'timestamp': '2026-06-21T22:15:00+00:00',
        'camera_id': 2,
        'profile_id': 'asi678mc',
    }) is None


def test_placeholder_builder_uses_existing_metadata_only():
    candidate = build_event_candidate_from_metadata(
        {
            'frame_id': 42,
            'timestamp': '2026-06-21T22:15:00+00:00',
            'camera_id': 2,
            'profile_id': 'asi678mc',
            'meter_value_raw': 250.0,
            'meter_value_smoothed': 249.0,
            'target_meter': 95.0,
            'meter_error': -154.0,
            'exposure_us': 14000000,
            'gain': 300.0,
            'capture_status': 'processed',
            'quality_score': 10.0,
            'quality_flags': ['meter_saturated_high'],
        },
        reasons=['meter_saturated_high'],
        candidate_score=25.0,
        environment_context={'sky_condition': 'poor'},
    )

    row = candidate.to_dict()
    assert row['candidate_id'] == 'asi678mc:2:42'
    assert row['candidate_type'] == 'unclassified'
    assert row['source_metrics']['meter_value_smoothed'] == 249.0
    assert row['quality_context']['quality_flags'] == ['meter_saturated_high']
    assert row['environment_context']['sky_condition'] == 'poor'


def test_event_timeline_single_candidate_segment():
    segments = build_event_timeline_segments([_candidate()])

    assert len(segments) == 1
    row = segments[0].to_dict()
    assert row['schema_version'] == 'event_timeline_segment_v0'
    assert row['segment_type'] == 'unclassified'
    assert row['shadow_only'] is True
    assert row['candidate_count'] == 1
    assert row['candidate_ids'] == ['asi678mc:2:42']
    assert row['duration_seconds'] == 0.0


def test_event_timeline_groups_nearby_same_camera_profile_night():
    candidates = [
        _candidate(candidate_id='asi678mc:2:1', frame_id=1, timestamp='2026-06-21T22:15:00+00:00', score=10.0),
        _candidate(candidate_id='asi678mc:2:2', frame_id=2, timestamp='2026-06-21T22:15:01+00:00', score=30.0, reasons=['high_meter']),
    ]

    segments = build_event_timeline_segments(candidates, max_gap_seconds=2.0)

    assert len(segments) == 1
    assert segments[0].candidate_count == 2
    assert segments[0].candidate_ids == ['asi678mc:2:1', 'asi678mc:2:2']
    assert segments[0].duration_seconds == 1.0
    assert segments[0].max_candidate_score == 30.0
    assert segments[0].average_candidate_score == 20.0
    assert segments[0].reasons == ['high_meter', 'low_quality']


def test_event_timeline_splits_candidates_beyond_gap():
    candidates = [
        _candidate(candidate_id='asi678mc:2:1', frame_id=1, timestamp='2026-06-21T22:15:00+00:00'),
        _candidate(candidate_id='asi678mc:2:2', frame_id=2, timestamp='2026-06-21T22:15:04+00:00'),
    ]

    segments = build_event_timeline_segments(candidates, max_gap_seconds=2.0)

    assert len(segments) == 2
    assert [segment.candidate_count for segment in segments] == [1, 1]


def test_event_timeline_splits_different_cameras():
    candidates = [
        _candidate(candidate_id='imx708-wide:1:1', camera_id=1, profile_id='imx708-wide', frame_id=1, timestamp='2026-06-21T22:15:00+00:00'),
        _candidate(candidate_id='asi678mc:2:2', camera_id=2, profile_id='asi678mc', frame_id=2, timestamp='2026-06-21T22:15:01+00:00'),
    ]

    segments = build_event_timeline_segments(candidates, max_gap_seconds=2.0)

    assert len(segments) == 2
    assert {str(segment.camera_id) for segment in segments} == {'1', '2'}


def test_event_timeline_splits_different_profiles():
    candidates = [
        _candidate(candidate_id='profile-a:2:1', camera_id=2, profile_id='profile-a', frame_id=1, timestamp='2026-06-21T22:15:00+00:00'),
        _candidate(candidate_id='profile-b:2:2', camera_id=2, profile_id='profile-b', frame_id=2, timestamp='2026-06-21T22:15:01+00:00'),
    ]

    segments = build_event_timeline_segments(candidates, max_gap_seconds=2.0)

    assert len(segments) == 2
    assert {segment.profile_id for segment in segments} == {'profile-a', 'profile-b'}


def test_event_timeline_splits_different_nights():
    candidates = [
        _candidate(candidate_id='asi678mc:2:1', frame_id=1, timestamp='2026-06-21T23:59:59+00:00'),
        _candidate(candidate_id='asi678mc:2:2', frame_id=2, timestamp='2026-06-22T00:00:00+00:00'),
    ]

    segments = build_event_timeline_segments(candidates, max_gap_seconds=2.0)

    assert len(segments) == 2
    assert {segment.night_id for segment in segments} == {'2026-06-21', '2026-06-22'}


def test_event_timeline_type_is_always_unclassified():
    segment = EventTimelineSegment(
        timeline_id='x',
        camera_id=2,
        profile_id='asi678mc',
        night_id='2026-06-21',
        start_timestamp_utc='2026-06-21T22:15:00+00:00',
        end_timestamp_utc='2026-06-21T22:15:00+00:00',
        duration_seconds=0.0,
        candidate_count=1,
    )
    segment.segment_type = 'meteor'
    segment.shadow_only = False
    segment.__post_init__()

    assert segment.segment_type == 'unclassified'
    assert segment.shadow_only is True


def test_event_timeline_jsonl_persistence():
    with tempfile.TemporaryDirectory() as tmpdir:
        timeline_dir = Path(tmpdir).joinpath('event_timelines')
        writer = EventTimelineWriter(timeline_dir)
        segment = build_event_timeline_segments([_candidate()])[0]

        written_path = writer.write(segment)

        assert written_path == timeline_dir.joinpath('2026-06-21.jsonl')
        rows = written_path.read_text(encoding='utf-8').splitlines()
        assert len(rows) == 1
        row = json.loads(rows[0])
        assert row['segment_type'] == 'unclassified'
        assert row['shadow_only'] is True


def test_event_timeline_default_directory():
    with tempfile.TemporaryDirectory() as tmpdir:
        assert default_event_timeline_dir(tmpdir) == Path(tmpdir).joinpath('event_timelines')


def test_event_timeline_nightly_analytics_counts():
    with tempfile.TemporaryDirectory() as tmpdir:
        timeline_dir = Path(tmpdir)
        segments = build_event_timeline_segments([
            _candidate(candidate_id='asi678mc:2:1', camera_id=2, profile_id='asi678mc', frame_id=1, score=10.0, reasons=['low_quality'], timestamp='2026-06-21T22:15:00+00:00'),
            _candidate(candidate_id='asi678mc:2:2', camera_id=2, profile_id='asi678mc', frame_id=2, score=20.0, reasons=['high_meter'], timestamp='2026-06-21T22:15:01+00:00'),
            _candidate(candidate_id='imx708-wide:1:3', camera_id=1, profile_id='imx708-wide', frame_id=3, score=40.0, reasons=['capture_error'], timestamp='2026-06-21T22:16:00+00:00'),
        ])
        writer = EventTimelineWriter(timeline_dir)
        for segment in segments:
            writer.write(segment)

        summary = EventTimelineAnalytics(timeline_dir).get_nightly_timeline_summary('2026-06-21')

        assert summary['total_timeline_segments'] == 2
        assert summary['timeline_segments_by_camera'] == {'1': 1, '2': 1}
        assert summary['average_segment_duration_seconds'] == 0.5
        assert summary['max_segment_duration_seconds'] == 1.0
        assert summary['average_candidates_per_segment'] == 1.5
        assert summary['max_candidates_per_segment'] == 2.0
        assert summary['timeline_segments_by_reason']['low_quality'] == 1
        assert summary['timeline_segments_by_reason']['high_meter'] == 1
        assert summary['timeline_segments_by_reason']['capture_error'] == 1


if __name__ == '__main__':
    test_event_candidate_v0_serialization()
    test_candidate_type_is_always_unclassified()
    test_event_candidate_jsonl_persistence()
    test_event_candidate_default_directory()
    test_event_candidate_multi_camera_fields_preserved()
    test_event_candidate_nightly_analytics_counts()
    test_placeholder_builder_is_disabled_without_reasons()
    test_placeholder_builder_uses_existing_metadata_only()
    test_event_timeline_single_candidate_segment()
    test_event_timeline_groups_nearby_same_camera_profile_night()
    test_event_timeline_splits_candidates_beyond_gap()
    test_event_timeline_splits_different_cameras()
    test_event_timeline_splits_different_profiles()
    test_event_timeline_splits_different_nights()
    test_event_timeline_type_is_always_unclassified()
    test_event_timeline_jsonl_persistence()
    test_event_timeline_default_directory()
    test_event_timeline_nightly_analytics_counts()
    print('event candidate tests OK')
