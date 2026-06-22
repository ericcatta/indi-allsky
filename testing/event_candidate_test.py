import json
import sys
import tempfile
import importlib.util
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from indi_allsky.event_candidate import EventCandidate
from indi_allsky.event_candidate import EventCandidateAnalytics
from indi_allsky.event_candidate import EventCandidateRuntimeDiagnostics
from indi_allsky.event_candidate import EventCandidateWriter
from indi_allsky.event_candidate import EventClassification
from indi_allsky.event_candidate import EventClassificationWriter
from indi_allsky.event_candidate import EventTimelineAnalytics
from indi_allsky.event_candidate import EventTimelineSegment
from indi_allsky.event_candidate import EventTimelineWriter
from indi_allsky.event_candidate import RuleBasedEventClassifierV1
from indi_allsky.event_candidate import build_event_candidate_from_metadata
from indi_allsky.event_candidate import build_event_timeline_segments
from indi_allsky.event_candidate import default_event_classification_dir
from indi_allsky.event_candidate import default_event_candidate_dir
from indi_allsky.event_candidate import default_event_candidate_runtime_path
from indi_allsky.event_candidate import default_event_timeline_dir
from indi_allsky.event_candidate import evaluate_candidate_triggers
from indi_allsky.event_candidate import persist_event_candidates_shadow


_SMOKE_SCRIPT_PATH = Path(__file__).resolve().parent.joinpath('event_foundation_smoke_test.py')
_SMOKE_SPEC = importlib.util.spec_from_file_location('event_foundation_smoke_test', _SMOKE_SCRIPT_PATH)
event_foundation_smoke_test = importlib.util.module_from_spec(_SMOKE_SPEC)
_SMOKE_SPEC.loader.exec_module(event_foundation_smoke_test)

_TRIGGER_SMOKE_SCRIPT_PATH = Path(__file__).resolve().parent.joinpath('candidate_trigger_smoke_test.py')
_TRIGGER_SMOKE_SPEC = importlib.util.spec_from_file_location('candidate_trigger_smoke_test', _TRIGGER_SMOKE_SCRIPT_PATH)
candidate_trigger_smoke_test = importlib.util.module_from_spec(_TRIGGER_SMOKE_SPEC)
_TRIGGER_SMOKE_SPEC.loader.exec_module(candidate_trigger_smoke_test)


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


def _metadata(frame_id=42, camera_id=2, profile_id='asi678mc', timestamp='2026-06-21T22:15:00+00:00', meter=95.0, target=95.0, quality=95.0, sky_condition='good', cloud_condition='mostly_clear', possible_condensation=False):
    return {
        'frame_id': frame_id,
        'timestamp': timestamp,
        'camera_id': camera_id,
        'profile_id': profile_id,
        'meter_value_raw': meter,
        'meter_value_smoothed': meter,
        'target_meter': target,
        'meter_error': target - meter,
        'exposure_us': 1000000,
        'gain': 0.0,
        'capture_status': 'processed',
        'quality_score': quality,
        'quality_flags': [],
        'sky_condition': sky_condition,
        'cloud_condition': cloud_condition,
        'sky_trend': 'stable',
        'possible_condensation': possible_condensation,
    }


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


def test_event_candidate_analytics_missing_empty_and_malformed_files():
    with tempfile.TemporaryDirectory() as tmpdir:
        candidate_dir = Path(tmpdir)
        analytics = EventCandidateAnalytics(candidate_dir)
        assert analytics.get_nightly_event_summary('2026-06-21')['total_event_candidates'] == 0

        candidate_dir.joinpath('2026-06-21.jsonl').write_text('\nnot-json\n', encoding='utf-8')
        assert analytics.load_day('2026-06-21') == []

        _write_candidates(candidate_dir, '2026-06-21', [_candidate()])
        with candidate_dir.joinpath('2026-06-21.jsonl').open('a', encoding='utf-8') as f_candidate:
            f_candidate.write('not-json\n')
        assert analytics.get_nightly_event_summary('2026-06-21')['total_event_candidates'] == 1


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


def test_candidate_triggers_normal_input_creates_no_candidate():
    candidates = evaluate_candidate_triggers(
        _metadata(frame_id=2, meter=96.0, quality=94.0),
        previous_metadata=_metadata(frame_id=1, meter=95.0, quality=95.0),
    )

    assert candidates == []


def test_candidate_triggers_brightness_spike():
    candidates = evaluate_candidate_triggers(
        _metadata(frame_id=2, meter=180.0, target=95.0, quality=92.0),
        previous_metadata=_metadata(frame_id=1, meter=95.0, target=95.0, quality=93.0),
    )

    assert len(candidates) == 1
    row = candidates[0].to_dict()
    assert row['reasons'] == ['brightness_spike']
    assert row['candidate_type'] == 'unclassified'
    assert row['shadow_only'] is True
    assert row['source_metrics']['meter_value_smoothed'] == 180.0


def test_candidate_triggers_quality_drop():
    candidates = evaluate_candidate_triggers(
        _metadata(frame_id=2, meter=95.0, quality=35.0),
        previous_metadata=_metadata(frame_id=1, meter=95.0, quality=94.0),
    )

    assert len(candidates) == 1
    assert candidates[0].reasons == ['quality_drop']
    assert candidates[0].quality_context['quality_score'] == 35.0


def test_candidate_triggers_condensation_onset():
    candidates = evaluate_candidate_triggers(
        _metadata(frame_id=2, possible_condensation=True),
        previous_metadata=_metadata(frame_id=1, possible_condensation=False),
    )

    assert len(candidates) == 1
    assert candidates[0].reasons == ['condensation_onset']
    assert candidates[0].environment_context['possible_condensation'] is True


def test_candidate_triggers_sky_condition_transition():
    candidates = evaluate_candidate_triggers(
        _metadata(frame_id=2, quality=80.0, sky_condition='poor', cloud_condition='cloudy'),
        previous_metadata=_metadata(frame_id=1, quality=82.0, sky_condition='excellent', cloud_condition='clear'),
    )

    assert len(candidates) == 1
    assert candidates[0].reasons == ['sky_condition_transition']


def test_candidate_triggers_missing_fields_create_no_candidate():
    assert evaluate_candidate_triggers({'quality_score': 20.0}) == []
    assert evaluate_candidate_triggers(_metadata(frame_id=2, quality=None)) == []


def test_candidate_triggers_preserve_multi_camera_profile_fields():
    candidates = evaluate_candidate_triggers(
        _metadata(frame_id=77, camera_id=1, profile_id='imx708_south', meter=190.0, quality=90.0),
        previous_metadata=_metadata(frame_id=76, camera_id=1, profile_id='imx708_south', meter=95.0, quality=92.0),
    )

    assert len(candidates) == 1
    assert candidates[0].camera_id == 1
    assert candidates[0].profile_id == 'imx708_south'
    assert candidates[0].candidate_type == 'unclassified'
    assert candidates[0].shadow_only is True


def test_candidate_triggers_profile_config_can_disable_all():
    candidates = evaluate_candidate_triggers(
        _metadata(frame_id=2, meter=180.0, target=95.0, quality=30.0),
        previous_metadata=_metadata(frame_id=1, meter=95.0, target=95.0, quality=95.0),
        profile_config={'event_candidate_triggers': {'enabled': False}},
    )

    assert candidates == []


def test_candidate_triggers_profile_config_can_override_thresholds():
    candidates = evaluate_candidate_triggers(
        _metadata(frame_id=2, meter=140.0, target=95.0, quality=90.0),
        previous_metadata=_metadata(frame_id=1, meter=95.0, target=95.0, quality=95.0),
    )
    assert candidates == []

    candidates = evaluate_candidate_triggers(
        _metadata(frame_id=2, meter=140.0, target=95.0, quality=90.0),
        previous_metadata=_metadata(frame_id=1, meter=95.0, target=95.0, quality=95.0),
        profile_config={
            'event_candidate_triggers': {
                'brightness_spike_meter_delta': 40.0,
                'brightness_spike_over_target': 40.0,
            },
        },
    )
    assert len(candidates) == 1
    assert candidates[0].reasons == ['brightness_spike']


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


def test_event_timeline_analytics_missing_empty_and_malformed_files():
    with tempfile.TemporaryDirectory() as tmpdir:
        timeline_dir = Path(tmpdir)
        analytics = EventTimelineAnalytics(timeline_dir)
        assert analytics.get_nightly_timeline_summary('2026-06-21')['total_timeline_segments'] == 0

        timeline_dir.joinpath('2026-06-21.jsonl').write_text('\nnot-json\n', encoding='utf-8')
        assert analytics.load_day('2026-06-21') == []

        writer = EventTimelineWriter(timeline_dir)
        writer.write(build_event_timeline_segments([_candidate()])[0])
        with timeline_dir.joinpath('2026-06-21.jsonl').open('a', encoding='utf-8') as f_timeline:
            f_timeline.write('not-json\n')
        assert analytics.get_nightly_timeline_summary('2026-06-21')['total_timeline_segments'] == 1


def test_event_classification_v1_serialization():
    classification = EventClassification(
        timeline_id='timeline-1',
        camera_id=2,
        profile_id='asi678mc',
        created_at='2026-06-21T22:15:00+00:00',
        confidence=0.25,
        rules_matched=['synthetic_rule'],
        alternative_labels=['meteor'],
        features_used={'candidate_count': 2},
    )
    classification.label = 'meteor'
    classification.status = 'active'
    classification.method = 'ai'
    classification.__post_init__()

    row = classification.to_dict()

    assert row['schema_version'] == 'event_classification_v1'
    assert row['timeline_id'] == 'timeline-1'
    assert row['camera_id'] == 2
    assert row['profile_id'] == 'asi678mc'
    assert row['label'] == 'unknown_event'
    assert row['confidence'] == 0.25
    assert row['status'] == 'shadow'
    assert row['method'] == 'rule_based_v1'
    assert row['rules_matched'] == ['synthetic_rule']
    assert row['alternative_labels'] == ['meteor']
    assert row['features_used']['candidate_count'] == 2


def test_event_classification_jsonl_persistence():
    with tempfile.TemporaryDirectory() as tmpdir:
        classification_dir = Path(tmpdir).joinpath('event_classifications')
        writer = EventClassificationWriter(classification_dir)
        classification = EventClassification(
            timeline_id='timeline-1',
            camera_id=2,
            profile_id='asi678mc',
            created_at='2026-06-21T22:15:00+00:00',
        )

        written_path = writer.write(classification)

        assert written_path == classification_dir.joinpath('2026-06-21.jsonl')
        rows = written_path.read_text(encoding='utf-8').splitlines()
        assert len(rows) == 1
        row = json.loads(rows[0])
        assert row['timeline_id'] == 'timeline-1'
        assert row['label'] == 'unknown_event'
        assert row['status'] == 'shadow'
        assert row['method'] == 'rule_based_v1'


def test_event_classification_default_directory():
    with tempfile.TemporaryDirectory() as tmpdir:
        assert default_event_classification_dir(tmpdir) == Path(tmpdir).joinpath('event_classifications')


def test_rule_based_event_classifier_v1_noop_unknown_event():
    timeline = build_event_timeline_segments([
        _candidate(candidate_id='asi678mc:2:1', frame_id=1, timestamp='2026-06-21T22:15:00+00:00', score=10.0),
        _candidate(candidate_id='asi678mc:2:2', frame_id=2, timestamp='2026-06-21T22:15:01+00:00', score=30.0, reasons=['high_meter']),
    ])[0]

    classification = RuleBasedEventClassifierV1().classify_timeline(
        timeline,
        created_at='2026-06-21T22:16:00+00:00',
    )
    row = classification.to_dict()

    assert row['timeline_id'] == timeline.timeline_id
    assert row['camera_id'] == 2
    assert row['profile_id'] == 'asi678mc'
    assert row['label'] == 'unknown_event'
    assert row['confidence'] == 0.0
    assert row['status'] == 'shadow'
    assert row['method'] == 'rule_based_v1'
    assert row['rules_matched'] == []
    assert row['alternative_labels'] == []
    assert row['features_used']['candidate_count'] == 2
    assert row['features_used']['duration_seconds'] == 1.0
    assert row['features_used']['reasons'] == ['high_meter', 'low_quality']


def test_event_foundation_smoke_cleanup_removes_candidates_and_timelines():
    with tempfile.TemporaryDirectory() as tmpdir:
        date = '2026-06-21'
        base_dir = Path(tmpdir)
        candidate_dir = default_event_candidate_dir(base_dir)
        timeline_dir = default_event_timeline_dir(base_dir)

        candidates = event_foundation_smoke_test.build_synthetic_candidates(date)
        candidate_writer = EventCandidateWriter(candidate_dir)
        for candidate in candidates:
            candidate_writer.write(candidate)

        timeline_writer = EventTimelineWriter(timeline_dir)
        for segment in build_event_timeline_segments(candidates):
            timeline_writer.write(segment)

        assert EventCandidateAnalytics(candidate_dir).get_nightly_event_summary(date)['total_event_candidates'] == 5
        assert EventTimelineAnalytics(timeline_dir).get_nightly_timeline_summary(date)['total_timeline_segments'] == 3

        removed_candidates, removed_timelines = event_foundation_smoke_test.cleanup_synthetic(candidate_dir, timeline_dir, date)

        assert removed_candidates == 5
        assert removed_timelines == 3
        assert EventCandidateAnalytics(candidate_dir).get_nightly_event_summary(date)['total_event_candidates'] == 0
        assert EventTimelineAnalytics(timeline_dir).get_nightly_timeline_summary(date)['total_timeline_segments'] == 0


def test_candidate_trigger_smoke_cases_and_cleanup():
    with tempfile.TemporaryDirectory() as tmpdir:
        date = '2026-06-21'
        base_dir = Path(tmpdir)
        candidate_dir = default_event_candidate_dir(base_dir)
        timeline_dir = default_event_timeline_dir(base_dir)

        candidates, case_results = candidate_trigger_smoke_test.build_synthetic_trigger_candidates(date)
        assert dict(case_results) == {
            'normal': [],
            'brightness_spike': ['brightness_spike'],
            'quality_drop': ['quality_drop'],
            'condensation_onset': ['condensation_onset'],
            'sky_condition_transition': ['sky_condition_transition'],
        }

        candidate_writer = EventCandidateWriter(candidate_dir)
        for candidate in candidates:
            candidate_writer.write(candidate)

        timeline_writer = EventTimelineWriter(timeline_dir)
        for segment in build_event_timeline_segments(candidates):
            timeline_writer.write(segment)

        candidate_summary = EventCandidateAnalytics(candidate_dir).get_nightly_event_summary(date)
        timeline_summary = EventTimelineAnalytics(timeline_dir).get_nightly_timeline_summary(date)
        assert candidate_summary['total_event_candidates'] == 4
        assert candidate_summary['event_candidates_by_reason'] == {
            'brightness_spike': 1,
            'condensation_onset': 1,
            'quality_drop': 1,
            'sky_condition_transition': 1,
        }
        assert timeline_summary['total_timeline_segments'] == 4

        removed_candidates, removed_timelines = candidate_trigger_smoke_test.cleanup_synthetic(candidate_dir, timeline_dir, date)
        assert removed_candidates == 4
        assert removed_timelines == 4
        assert EventCandidateAnalytics(candidate_dir).get_nightly_event_summary(date)['total_event_candidates'] == 0
        assert EventTimelineAnalytics(timeline_dir).get_nightly_timeline_summary(date)['total_timeline_segments'] == 0


def test_runtime_shadow_integration_disabled_by_default():
    with tempfile.TemporaryDirectory() as tmpdir:
        base_dir = Path(tmpdir)
        candidate_dir = default_event_candidate_dir(base_dir)
        timeline_dir = default_event_timeline_dir(base_dir)
        diagnostics_path = default_event_candidate_runtime_path(base_dir)

        result = persist_event_candidates_shadow(
            _metadata(frame_id=2, meter=180.0, target=95.0, quality=30.0),
            previous_metadata=_metadata(frame_id=1, meter=95.0, target=95.0, quality=95.0),
            candidate_dir=candidate_dir,
            timeline_dir=timeline_dir,
            diagnostics_path=diagnostics_path,
        )
        diagnostics = EventCandidateRuntimeDiagnostics(diagnostics_path).read_summary()

        assert result['status'] == 'disabled'
        assert result['candidate_count'] == 0
        assert diagnostics_path.exists()
        assert diagnostics['enabled'] is False
        assert diagnostics['total_evaluations'] == 0
        assert diagnostics['last_status'] == 'disabled'
        assert not candidate_dir.exists()
        assert not timeline_dir.exists()


def test_runtime_shadow_integration_enabled_no_candidates_records_evaluation():
    with tempfile.TemporaryDirectory() as tmpdir:
        base_dir = Path(tmpdir)
        candidate_dir = default_event_candidate_dir(base_dir)
        timeline_dir = default_event_timeline_dir(base_dir)
        diagnostics_path = default_event_candidate_runtime_path(base_dir)

        result = persist_event_candidates_shadow(
            _metadata(frame_id=2, meter=95.0, target=95.0, quality=95.0),
            previous_metadata=_metadata(frame_id=1, meter=94.0, target=95.0, quality=95.0),
            profile_config={'event_candidate_triggers': {'enabled': True}},
            candidate_dir=candidate_dir,
            timeline_dir=timeline_dir,
            diagnostics_path=diagnostics_path,
        )
        diagnostics = EventCandidateRuntimeDiagnostics(diagnostics_path).read_summary()

        assert result['status'] == 'no_candidates'
        assert result['reason'] == 'no_trigger_rules_matched'
        assert result['candidate_count'] == 0
        assert diagnostics_path.exists()
        assert diagnostics['enabled'] is True
        assert diagnostics['total_evaluations'] == 1
        assert diagnostics['total_generated_candidates'] == 0
        assert not candidate_dir.exists()
        assert not timeline_dir.exists()


def test_runtime_shadow_integration_enabled_persists_candidates_and_timelines():
    with tempfile.TemporaryDirectory() as tmpdir:
        base_dir = Path(tmpdir)
        candidate_dir = default_event_candidate_dir(base_dir)
        timeline_dir = default_event_timeline_dir(base_dir)
        date = '2026-06-21'

        result = persist_event_candidates_shadow(
            _metadata(frame_id=2, meter=180.0, target=95.0, quality=30.0),
            previous_metadata=_metadata(frame_id=1, meter=95.0, target=95.0, quality=95.0),
            profile_config={'event_candidate_triggers': {'enabled': True}},
            candidate_dir=candidate_dir,
            timeline_dir=timeline_dir,
        )

        assert result['status'] == 'written'
        assert result['candidate_count'] == 2
        assert EventCandidateAnalytics(candidate_dir).get_nightly_event_summary(date)['total_event_candidates'] == 2
        assert EventTimelineAnalytics(timeline_dir).get_nightly_timeline_summary(date)['total_timeline_segments'] == 1


def test_runtime_shadow_integration_populates_diagnostics():
    with tempfile.TemporaryDirectory() as tmpdir:
        base_dir = Path(tmpdir)
        candidate_dir = default_event_candidate_dir(base_dir)
        timeline_dir = default_event_timeline_dir(base_dir)
        diagnostics_path = default_event_candidate_runtime_path(base_dir)

        result = persist_event_candidates_shadow(
            _metadata(frame_id=2, meter=180.0, target=95.0, quality=30.0),
            previous_metadata=_metadata(frame_id=1, meter=95.0, target=95.0, quality=95.0),
            profile_config={'event_candidate_triggers': {'enabled': True}},
            candidate_dir=candidate_dir,
            timeline_dir=timeline_dir,
            diagnostics_path=diagnostics_path,
        )
        diagnostics = EventCandidateRuntimeDiagnostics(diagnostics_path).read_summary()

        assert result['status'] == 'written'
        assert diagnostics['enabled'] is True
        assert diagnostics['total_evaluations'] == 1
        assert diagnostics['total_generated_candidates'] == 2
        assert diagnostics['trigger_evaluation_failures'] == 0
        assert diagnostics['candidates_by_reason'] == {
            'brightness_spike': 1,
            'quality_drop': 1,
        }


def test_runtime_shadow_integration_rate_limit_caps_candidates():
    with tempfile.TemporaryDirectory() as tmpdir:
        base_dir = Path(tmpdir)
        candidate_dir = default_event_candidate_dir(base_dir)
        timeline_dir = default_event_timeline_dir(base_dir)
        diagnostics_path = default_event_candidate_runtime_path(base_dir)
        config = {'event_candidate_triggers': {'enabled': True, 'max_candidates_per_hour': 1}}

        result = persist_event_candidates_shadow(
            _metadata(frame_id=2, meter=180.0, target=95.0, quality=30.0),
            previous_metadata=_metadata(frame_id=1, meter=95.0, target=95.0, quality=95.0),
            profile_config=config,
            candidate_dir=candidate_dir,
            timeline_dir=timeline_dir,
            diagnostics_path=diagnostics_path,
        )
        assert result['status'] == 'rate_limited'
        assert result['candidate_count'] == 1
        assert EventCandidateAnalytics(candidate_dir).get_nightly_event_summary('2026-06-21')['total_event_candidates'] == 1

        result = persist_event_candidates_shadow(
            _metadata(frame_id=3, meter=190.0, target=95.0, quality=30.0),
            previous_metadata=_metadata(frame_id=2, meter=95.0, target=95.0, quality=95.0),
            profile_config=config,
            candidate_dir=candidate_dir,
            timeline_dir=timeline_dir,
            diagnostics_path=diagnostics_path,
        )
        diagnostics = EventCandidateRuntimeDiagnostics(diagnostics_path).read_summary()

        assert result['status'] == 'rate_limited'
        assert result['candidate_count'] == 0
        assert diagnostics['total_evaluations'] == 1
        assert diagnostics['total_generated_candidates'] == 1
        assert diagnostics['rate_limited_events'] == 2
        assert EventCandidateAnalytics(candidate_dir).get_nightly_event_summary('2026-06-21')['total_event_candidates'] == 1


def test_runtime_shadow_integration_rebuilds_timeline_without_duplicates():
    with tempfile.TemporaryDirectory() as tmpdir:
        base_dir = Path(tmpdir)
        candidate_dir = default_event_candidate_dir(base_dir)
        timeline_dir = default_event_timeline_dir(base_dir)
        date = '2026-06-21'
        config = {'event_candidate_triggers': {'enabled': True}}

        persist_event_candidates_shadow(
            _metadata(frame_id=2, timestamp='2026-06-21T22:15:00+00:00', meter=180.0, target=95.0, quality=95.0),
            previous_metadata=_metadata(frame_id=1, timestamp='2026-06-21T22:14:59+00:00', meter=95.0, target=95.0, quality=95.0),
            profile_config=config,
            candidate_dir=candidate_dir,
            timeline_dir=timeline_dir,
        )
        persist_event_candidates_shadow(
            _metadata(frame_id=3, timestamp='2026-06-21T22:15:01+00:00', meter=190.0, target=95.0, quality=95.0),
            previous_metadata=_metadata(frame_id=2, timestamp='2026-06-21T22:15:00+00:00', meter=95.0, target=95.0, quality=95.0),
            profile_config=config,
            candidate_dir=candidate_dir,
            timeline_dir=timeline_dir,
        )

        assert EventCandidateAnalytics(candidate_dir).get_nightly_event_summary(date)['total_event_candidates'] == 2
        assert EventTimelineAnalytics(timeline_dir).get_nightly_timeline_summary(date)['total_timeline_segments'] == 1


def test_runtime_shadow_integration_trigger_failure_is_isolated():
    def broken_evaluator(*args, **kwargs):
        raise RuntimeError('synthetic trigger failure')

    with tempfile.TemporaryDirectory() as tmpdir:
        base_dir = Path(tmpdir)
        candidate_dir = default_event_candidate_dir(base_dir)
        timeline_dir = default_event_timeline_dir(base_dir)

        result = persist_event_candidates_shadow(
            _metadata(frame_id=2, meter=180.0, target=95.0, quality=30.0),
            previous_metadata=_metadata(frame_id=1, meter=95.0, target=95.0, quality=95.0),
            profile_config={'event_candidate_triggers': {'enabled': True}},
            candidate_dir=candidate_dir,
            timeline_dir=timeline_dir,
            diagnostics_path=default_event_candidate_runtime_path(base_dir),
            trigger_evaluator=broken_evaluator,
        )
        diagnostics = EventCandidateRuntimeDiagnostics(default_event_candidate_runtime_path(base_dir)).read_summary()

        assert result['status'] == 'error'
        assert result['candidate_count'] == 0
        assert 'synthetic trigger failure' in result['reason']
        assert diagnostics['trigger_evaluation_failures'] == 1
        assert EventCandidateAnalytics(candidate_dir).get_nightly_event_summary('2026-06-21')['total_event_candidates'] == 0
        assert EventTimelineAnalytics(timeline_dir).get_nightly_timeline_summary('2026-06-21')['total_timeline_segments'] == 0


if __name__ == '__main__':
    test_event_candidate_v0_serialization()
    test_candidate_type_is_always_unclassified()
    test_event_candidate_jsonl_persistence()
    test_event_candidate_default_directory()
    test_event_candidate_multi_camera_fields_preserved()
    test_event_candidate_nightly_analytics_counts()
    test_event_candidate_analytics_missing_empty_and_malformed_files()
    test_placeholder_builder_is_disabled_without_reasons()
    test_placeholder_builder_uses_existing_metadata_only()
    test_candidate_triggers_normal_input_creates_no_candidate()
    test_candidate_triggers_brightness_spike()
    test_candidate_triggers_quality_drop()
    test_candidate_triggers_condensation_onset()
    test_candidate_triggers_sky_condition_transition()
    test_candidate_triggers_missing_fields_create_no_candidate()
    test_candidate_triggers_preserve_multi_camera_profile_fields()
    test_candidate_triggers_profile_config_can_disable_all()
    test_candidate_triggers_profile_config_can_override_thresholds()
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
    test_event_timeline_analytics_missing_empty_and_malformed_files()
    test_event_classification_v1_serialization()
    test_event_classification_jsonl_persistence()
    test_event_classification_default_directory()
    test_rule_based_event_classifier_v1_noop_unknown_event()
    test_event_foundation_smoke_cleanup_removes_candidates_and_timelines()
    test_candidate_trigger_smoke_cases_and_cleanup()
    test_runtime_shadow_integration_disabled_by_default()
    test_runtime_shadow_integration_enabled_no_candidates_records_evaluation()
    test_runtime_shadow_integration_enabled_persists_candidates_and_timelines()
    test_runtime_shadow_integration_populates_diagnostics()
    test_runtime_shadow_integration_rate_limit_caps_candidates()
    test_runtime_shadow_integration_rebuilds_timeline_without_duplicates()
    test_runtime_shadow_integration_trigger_failure_is_isolated()
    print('event candidate tests OK')
