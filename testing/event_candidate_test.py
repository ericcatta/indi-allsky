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
from indi_allsky.event_candidate import ClassificationRule
from indi_allsky.event_candidate import ClassificationRuleRegistry
from indi_allsky.event_candidate import ClassificationRuleResult
from indi_allsky.event_candidate import EventTimelineAnalytics
from indi_allsky.event_candidate import EventTimelineSegment
from indi_allsky.event_candidate import EventTimelineWriter
from indi_allsky.event_candidate import RuleBasedEventClassifierV1
from indi_allsky.event_candidate import WeatherOrCloudEventRule
from indi_allsky.event_candidate import build_event_candidate_from_metadata
from indi_allsky.event_candidate import build_event_timeline_segments
from indi_allsky.event_candidate import build_event_pipeline_offline_report
from indi_allsky.event_candidate import classify_event_timelines_offline
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


class _SyntheticClassificationRule(ClassificationRule):
    def __init__(self, rule_id, target_label, matched=True, score=0.0, reason='synthetic'):
        self.rule_id = rule_id
        self.target_label = target_label
        self.matched = matched
        self.score = score
        self.reason = reason

    def evaluate(self, timeline, features=None):
        return ClassificationRuleResult(
            matched=self.matched,
            score=self.score,
            reason=self.reason,
        )


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


def _timeline_with_context(reasons=None, environment_context_summary=None, quality_context_summary=None):
    return EventTimelineSegment(
        timeline_id='timeline-weather-test',
        camera_id=2,
        profile_id='asi678mc',
        night_id='2026-06-21',
        start_timestamp_utc='2026-06-21T22:15:00+00:00',
        end_timestamp_utc='2026-06-21T22:15:01+00:00',
        duration_seconds=1.0,
        candidate_count=1,
        candidate_ids=['asi678mc:2:1'],
        reasons=reasons or [],
        max_candidate_score=95.0,
        average_candidate_score=95.0,
        quality_context_summary=quality_context_summary or {},
        environment_context_summary=environment_context_summary or {},
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


def test_candidate_triggers_suppress_sky_condition_transition_when_exposure_adjusting():
    current_metadata = _metadata(frame_id=2, quality=80.0, sky_condition='poor', cloud_condition='cloudy')
    current_metadata['quality_flags'] = ['exposure_adjusting']

    candidates = evaluate_candidate_triggers(
        current_metadata,
        previous_metadata=_metadata(frame_id=1, quality=82.0, sky_condition='excellent', cloud_condition='clear'),
    )

    assert candidates == []


def test_candidate_triggers_suppress_sky_condition_transition_when_meter_near_edge():
    current_metadata = _metadata(frame_id=2, quality=80.0, sky_condition='poor', cloud_condition='cloudy')
    current_metadata['quality_flags'] = ['meter_near_edge']

    candidates = evaluate_candidate_triggers(
        current_metadata,
        previous_metadata=_metadata(frame_id=1, quality=82.0, sky_condition='excellent', cloud_condition='clear'),
    )

    assert candidates == []


def test_candidate_triggers_quality_drop_with_unstable_metering_flag_still_creates_candidate():
    current_metadata = _metadata(frame_id=2, meter=95.0, quality=35.0)
    current_metadata['quality_flags'] = ['exposure_adjusting']

    candidates = evaluate_candidate_triggers(
        current_metadata,
        previous_metadata=_metadata(frame_id=1, meter=95.0, quality=94.0),
    )

    assert len(candidates) == 1
    assert candidates[0].reasons == ['quality_drop']


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
    assert row['label'] == 'meteor'
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
    assert row['features_used']['candidate_ids'] == ['asi678mc:2:1', 'asi678mc:2:2']
    assert row['features_used']['start_timestamp_utc'] == '2026-06-21T22:15:00+00:00'
    assert row['features_used']['end_timestamp_utc'] == '2026-06-21T22:15:01+00:00'
    assert 'quality_context_summary' in row['features_used']
    assert 'environment_context_summary' in row['features_used']


def test_classification_rule_registry_registration_and_ordering():
    registry = ClassificationRuleRegistry()
    first = _SyntheticClassificationRule('first_rule', 'synthetic_first')
    second = _SyntheticClassificationRule('second_rule', 'synthetic_second')

    registry.register(first)
    registry.register(second)

    assert registry.get_rules() == [first, second]


def test_classification_rule_registry_requires_rule_id_and_label():
    registry = ClassificationRuleRegistry()

    try:
        registry.register(_SyntheticClassificationRule('', 'synthetic'))
        assert False, 'missing rule_id should raise'
    except ValueError:
        pass

    try:
        registry.register(_SyntheticClassificationRule('synthetic_rule', ''))
        assert False, 'missing target_label should raise'
    except ValueError:
        pass


def test_rule_based_event_classifier_v1_selects_best_rule_match():
    timeline = build_event_timeline_segments([
        _candidate(candidate_id='asi678mc:2:1', frame_id=1, timestamp='2026-06-21T22:15:00+00:00', score=10.0),
    ])[0]
    registry = ClassificationRuleRegistry([
        _SyntheticClassificationRule('low_score_rule', 'synthetic_low', score=0.25),
        _SyntheticClassificationRule('high_score_rule', 'synthetic_high', score=0.75),
    ])

    row = RuleBasedEventClassifierV1(registry=registry).classify_timeline(
        timeline,
        created_at='2026-06-21T22:16:00+00:00',
    ).to_dict()

    assert row['label'] == 'synthetic_high'
    assert row['confidence'] == 0.75
    assert row['rules_matched'] == [
        {
            'rule_id': 'low_score_rule',
            'target_label': 'synthetic_low',
            'score': 0.25,
            'reason': 'synthetic',
        },
        {
            'rule_id': 'high_score_rule',
            'target_label': 'synthetic_high',
            'score': 0.75,
            'reason': 'synthetic',
        },
    ]
    assert row['alternative_labels'] == ['synthetic_low']
    assert row['status'] == 'shadow'
    assert row['method'] == 'rule_based_v1'


def test_rule_based_event_classifier_v1_uses_registration_order_for_ties():
    timeline = build_event_timeline_segments([
        _candidate(candidate_id='asi678mc:2:1', frame_id=1, timestamp='2026-06-21T22:15:00+00:00', score=10.0),
    ])[0]
    registry = ClassificationRuleRegistry([
        _SyntheticClassificationRule('first_rule', 'synthetic_first', score=0.50),
        _SyntheticClassificationRule('second_rule', 'synthetic_second', score=0.50),
    ])

    row = RuleBasedEventClassifierV1(registry=registry).classify_timeline(
        timeline,
        created_at='2026-06-21T22:16:00+00:00',
    ).to_dict()

    assert row['label'] == 'synthetic_first'
    assert row['confidence'] == 0.50
    assert row['rules_matched'] == [
        {
            'rule_id': 'first_rule',
            'target_label': 'synthetic_first',
            'score': 0.5,
            'reason': 'synthetic',
        },
        {
            'rule_id': 'second_rule',
            'target_label': 'synthetic_second',
            'score': 0.5,
            'reason': 'synthetic',
        },
    ]
    assert row['alternative_labels'] == ['synthetic_second']


def test_event_classification_explainable_rule_match_reason():
    timeline = build_event_timeline_segments([
        _candidate(candidate_id='asi678mc:2:1', frame_id=1, timestamp='2026-06-21T22:15:00+00:00', score=10.0),
    ])[0]
    registry = ClassificationRuleRegistry([
        _SyntheticClassificationRule(
            'explainable_rule',
            'synthetic_explainable',
            score=0.60,
            reason='matched_synthetic_signal',
        ),
    ])

    row = RuleBasedEventClassifierV1(registry=registry).classify_timeline(
        timeline,
        created_at='2026-06-21T22:16:00+00:00',
    ).to_dict()

    assert row['rules_matched'] == [
        {
            'rule_id': 'explainable_rule',
            'target_label': 'synthetic_explainable',
            'score': 0.6,
            'reason': 'matched_synthetic_signal',
        },
    ]
    assert row['features_used']['quality_context_summary']
    assert row['features_used']['environment_context_summary']


def test_weather_or_cloud_rule_classifies_strong_cloudy_timeline():
    timeline = _timeline_with_context(
        environment_context_summary={
            'cloud_condition': {'cloudy': 2},
            'sky_trend': {'stable': 1},
            'possible_condensation': False,
        },
    )
    registry = ClassificationRuleRegistry([WeatherOrCloudEventRule()])

    row = RuleBasedEventClassifierV1(registry=registry).classify_timeline(
        timeline,
        created_at='2026-06-21T22:16:00+00:00',
    ).to_dict()

    assert row['label'] == 'weather_or_cloud_event'
    assert 0.35 <= row['confidence'] <= 0.65
    assert row['rules_matched'] == [
        {
            'rule_id': 'weather_or_cloud_event_v1',
            'target_label': 'weather_or_cloud_event',
            'score': row['confidence'],
            'reason': 'cloud_condition_cloudy',
        },
    ]
    assert row['status'] == 'shadow'
    assert row['method'] == 'rule_based_v1'


def test_weather_or_cloud_rule_classifies_overcast_timeline():
    timeline = _timeline_with_context(
        environment_context_summary={
            'cloud_condition': {'overcast': 1},
            'sky_trend': {'unknown': 1},
            'possible_condensation': False,
        },
    )
    registry = ClassificationRuleRegistry([WeatherOrCloudEventRule()])

    row = RuleBasedEventClassifierV1(registry=registry).classify_timeline(
        timeline,
        created_at='2026-06-21T22:16:00+00:00',
    ).to_dict()

    assert row['label'] == 'weather_or_cloud_event'
    assert row['rules_matched'][0]['reason'] == 'cloud_condition_overcast'


def test_weather_or_cloud_rule_classifies_degrading_trend_timeline():
    timeline = _timeline_with_context(
        environment_context_summary={
            'cloud_condition': {'partly_cloudy': 1},
            'sky_trend': {'degrading': 1},
            'possible_condensation': False,
        },
    )
    registry = ClassificationRuleRegistry([WeatherOrCloudEventRule()])

    row = RuleBasedEventClassifierV1(registry=registry).classify_timeline(
        timeline,
        created_at='2026-06-21T22:16:00+00:00',
    ).to_dict()

    assert row['label'] == 'weather_or_cloud_event'
    assert row['rules_matched'][0]['reason'] == 'sky_trend_degrading'


def test_weather_or_cloud_rule_classifies_possible_condensation_timeline():
    timeline = _timeline_with_context(
        environment_context_summary={
            'cloud_condition': {'partly_cloudy': 1},
            'sky_trend': {'unknown': 1},
            'possible_condensation': True,
        },
    )
    registry = ClassificationRuleRegistry([WeatherOrCloudEventRule()])

    row = RuleBasedEventClassifierV1(registry=registry).classify_timeline(
        timeline,
        created_at='2026-06-21T22:16:00+00:00',
    ).to_dict()

    assert row['label'] == 'weather_or_cloud_event'
    assert row['rules_matched'][0]['reason'] == 'possible_condensation'


def test_weather_or_cloud_rule_classifies_condensation_onset_reason():
    timeline = _timeline_with_context(
        reasons=['condensation_onset'],
        environment_context_summary={
            'cloud_condition': {'partly_cloudy': 1},
            'sky_trend': {'unknown': 1},
            'possible_condensation': False,
        },
    )
    registry = ClassificationRuleRegistry([WeatherOrCloudEventRule()])

    row = RuleBasedEventClassifierV1(registry=registry).classify_timeline(
        timeline,
        created_at='2026-06-21T22:16:00+00:00',
    ).to_dict()

    assert row['label'] == 'weather_or_cloud_event'
    assert row['rules_matched'][0]['reason'] == 'reason_condensation_onset'


def test_weather_or_cloud_rule_classifies_condensation_timeline():
    timeline = _timeline_with_context(
        reasons=['condensation_onset'],
        environment_context_summary={
            'cloud_condition': {'mostly_clear': 1},
            'sky_trend': {'degrading': 1},
            'possible_condensation': True,
        },
    )
    registry = ClassificationRuleRegistry([WeatherOrCloudEventRule()])

    row = RuleBasedEventClassifierV1(registry=registry).classify_timeline(
        timeline,
        created_at='2026-06-21T22:16:00+00:00',
    ).to_dict()

    assert row['label'] == 'weather_or_cloud_event'
    assert row['confidence'] == 0.65
    assert row['rules_matched'][0]['rule_id'] == 'weather_or_cloud_event_v1'
    assert row['rules_matched'][0]['target_label'] == 'weather_or_cloud_event'
    assert row['rules_matched'][0]['reason'] == 'sky_trend_degrading,possible_condensation,reason_condensation_onset'


def test_weather_or_cloud_rule_ignores_weak_ambiguous_timeline():
    timeline = _timeline_with_context(
        reasons=['brightness_spike'],
        environment_context_summary={
            'cloud_condition': {'mostly_clear': 1},
            'sky_trend': {'stable': 1},
            'possible_condensation': False,
        },
    )
    registry = ClassificationRuleRegistry([WeatherOrCloudEventRule()])

    row = RuleBasedEventClassifierV1(registry=registry).classify_timeline(
        timeline,
        created_at='2026-06-21T22:16:00+00:00',
    ).to_dict()

    assert row['label'] == 'unknown_event'
    assert row['confidence'] == 0.0
    assert row['rules_matched'] == []


def test_weather_or_cloud_rule_ignores_partly_cloudy_transition_without_strong_signal():
    timeline = _timeline_with_context(
        reasons=['sky_condition_transition'],
        environment_context_summary={
            'cloud_condition': {'partly_cloudy': 1},
            'sky_trend': {'unknown': 1},
            'possible_condensation': False,
        },
    )
    registry = ClassificationRuleRegistry([WeatherOrCloudEventRule()])

    row = RuleBasedEventClassifierV1(registry=registry).classify_timeline(
        timeline,
        created_at='2026-06-21T22:16:00+00:00',
    ).to_dict()

    assert row['label'] == 'unknown_event'
    assert row['rules_matched'] == []


def test_weather_or_cloud_rule_uses_sky_transition_as_supporting_signal_only():
    timeline = _timeline_with_context(
        reasons=['sky_condition_transition'],
        environment_context_summary={
            'cloud_condition': {'cloudy': 1},
            'sky_trend': {'unknown': 1},
            'possible_condensation': False,
        },
    )
    registry = ClassificationRuleRegistry([WeatherOrCloudEventRule()])

    row = RuleBasedEventClassifierV1(registry=registry).classify_timeline(
        timeline,
        created_at='2026-06-21T22:16:00+00:00',
    ).to_dict()

    assert row['label'] == 'weather_or_cloud_event'
    assert row['rules_matched'][0]['reason'] == 'cloud_condition_cloudy,reason_sky_condition_transition'


def test_weather_or_cloud_rule_ignores_missing_environment_summary():
    timeline = _timeline_with_context(
        reasons=['brightness_spike'],
        environment_context_summary={},
    )
    registry = ClassificationRuleRegistry([WeatherOrCloudEventRule()])

    row = RuleBasedEventClassifierV1(registry=registry).classify_timeline(
        timeline,
        created_at='2026-06-21T22:16:00+00:00',
    ).to_dict()

    assert row['label'] == 'unknown_event'
    assert row['rules_matched'] == []


def test_offline_event_classification_runner_writes_classifications_and_counts_labels():
    with tempfile.TemporaryDirectory() as tmpdir:
        base_dir = Path(tmpdir)
        timeline_path = base_dir.joinpath('event_timelines', '2026-06-21.jsonl')
        classification_dir = base_dir.joinpath('event_classifications')
        timeline_path.parent.mkdir(parents=True, exist_ok=True)

        strong_timeline = _timeline_with_context(
            environment_context_summary={
                'cloud_condition': {'overcast': 1},
                'sky_trend': {'degrading': 1},
                'possible_condensation': False,
            },
        )
        ambiguous_timeline = _timeline_with_context(
            reasons=['brightness_spike'],
            environment_context_summary={
                'cloud_condition': {'mostly_clear': 1},
                'sky_trend': {'stable': 1},
                'possible_condensation': False,
            },
        )
        malformed_timeline = {'timeline_id': 'missing-required-fields'}

        with timeline_path.open('w', encoding='utf-8') as f_timeline:
            json.dump(strong_timeline.to_dict(), f_timeline, sort_keys=True, separators=(',', ':'))
            f_timeline.write('\n')
            f_timeline.write('not-json\n')
            json.dump(ambiguous_timeline.to_dict(), f_timeline, sort_keys=True, separators=(',', ':'))
            f_timeline.write('\n')
            json.dump(malformed_timeline, f_timeline, sort_keys=True, separators=(',', ':'))
            f_timeline.write('\n')

        summary = classify_event_timelines_offline(
            timeline_path,
            classification_dir,
            created_at='2026-06-21T23:00:00+00:00',
        )

        assert summary == {
            'total_lines': 4,
            'timelines_classified': 2,
            'classifications_written': 2,
            'skipped_lines': 2,
            'labels_count': {
                'unknown_event': 1,
                'weather_or_cloud_event': 1,
            },
        }

        rows = [
            json.loads(line)
            for line in classification_dir.joinpath('2026-06-21.jsonl').read_text(encoding='utf-8').splitlines()
        ]
        assert len(rows) == 2
        assert [row['label'] for row in rows] == ['weather_or_cloud_event', 'unknown_event']
        assert rows[0]['rules_matched'][0]['rule_id'] == 'weather_or_cloud_event_v1'
        assert rows[1]['rules_matched'] == []


def test_offline_event_classification_runner_does_not_change_default_classifier_registry():
    timeline = _timeline_with_context(
        environment_context_summary={
            'cloud_condition': {'overcast': 1},
            'sky_trend': {'degrading': 1},
            'possible_condensation': False,
        },
    )

    row = RuleBasedEventClassifierV1().classify_timeline(
        timeline,
        created_at='2026-06-21T23:00:00+00:00',
    ).to_dict()

    assert row['label'] == 'unknown_event'
    assert row['rules_matched'] == []


def test_event_pipeline_offline_report_counts_jsonl_inputs():
    with tempfile.TemporaryDirectory() as tmpdir:
        base_dir = Path(tmpdir)
        candidate_path = base_dir.joinpath('event_candidates', '2026-06-21.jsonl')
        timeline_path = base_dir.joinpath('event_timelines', '2026-06-21.jsonl')
        classification_path = base_dir.joinpath('event_classifications', '2026-06-21.jsonl')
        candidate_path.parent.mkdir(parents=True, exist_ok=True)
        timeline_path.parent.mkdir(parents=True, exist_ok=True)
        classification_path.parent.mkdir(parents=True, exist_ok=True)

        candidate = _candidate(
            candidate_id='asi678mc:2:1',
            camera_id=2,
            profile_id='asi678mc',
            frame_id=1,
            reasons=['brightness_spike', 'quality_drop'],
        )
        with candidate_path.open('w', encoding='utf-8') as f_candidate:
            json.dump(candidate.to_dict(), f_candidate, sort_keys=True, separators=(',', ':'))
            f_candidate.write('\n')
            f_candidate.write('not-json\n')

        timeline = _timeline_with_context(
            reasons=['brightness_spike', 'sky_condition_transition'],
            environment_context_summary={
                'cloud_condition': {'cloudy': 2},
                'sky_condition': {'poor': 1},
                'sky_trend': {'degrading': 1},
                'possible_condensation': True,
            },
            quality_context_summary={
                'quality_flags': {'low_meter': 2, 'nominal': 1},
            },
        )
        with timeline_path.open('w', encoding='utf-8') as f_timeline:
            json.dump(timeline.to_dict(), f_timeline, sort_keys=True, separators=(',', ':'))
            f_timeline.write('\n')

        classification = EventClassification(
            timeline_id='timeline-weather-test',
            camera_id=2,
            profile_id='asi678mc',
            created_at='2026-06-21T23:00:00+00:00',
            label='weather_or_cloud_event',
            confidence=0.45,
            features_used=timeline.to_dict(),
        )
        with classification_path.open('w', encoding='utf-8') as f_classification:
            json.dump(classification.to_dict(), f_classification, sort_keys=True, separators=(',', ':'))
            f_classification.write('\n')

        report = build_event_pipeline_offline_report(
            candidate_path=candidate_path,
            timeline_path=timeline_path,
            classification_path=classification_path,
        )

        assert report['total_candidate_lines'] == 1
        assert report['total_timeline_lines'] == 1
        assert report['total_classification_lines'] == 1
        assert report['malformed_lines']['candidates'] == 1
        assert report['malformed_lines']['timelines'] == 0
        assert report['malformed_lines']['classifications'] == 0
        assert report['counts_by_profile_id'] == {'asi678mc': 3}
        assert report['counts_by_camera_id'] == {'2': 3}
        assert report['counts_by_candidate_reasons'] == {'brightness_spike': 1, 'quality_drop': 1}
        assert report['counts_by_timeline_reasons'] == {'brightness_spike': 1, 'sky_condition_transition': 1}
        assert report['counts_by_classification_label'] == {'weather_or_cloud_event': 1}
        assert report['counts_by_quality_flags']['low_meter'] == 5
        assert report['counts_by_quality_flags']['nominal'] == 2
        assert report['counts_by_environment_cloud_condition']['cloudy'] == 5
        assert report['counts_by_sky_condition']['poor'] == 3
        assert report['counts_by_sky_trend']['degrading'] == 3
        assert report['possible_condensation_true'] == 2


def test_event_pipeline_offline_report_tolerates_missing_empty_and_malformed_files():
    with tempfile.TemporaryDirectory() as tmpdir:
        base_dir = Path(tmpdir)
        malformed_path = base_dir.joinpath('bad.jsonl')
        malformed_path.write_text('not-json\n[]\n', encoding='utf-8')

        report = build_event_pipeline_offline_report(
            candidate_path=base_dir.joinpath('missing-candidates.jsonl'),
            timeline_path=malformed_path,
            classification_path=None,
        )

        assert report['total_candidate_lines'] == 0
        assert report['total_timeline_lines'] == 0
        assert report['total_classification_lines'] == 0
        assert report['malformed_lines']['candidates'] == 0
        assert report['malformed_lines']['timelines'] == 2
        assert report['malformed_lines']['classifications'] == 0
        assert report['counts_by_profile_id'] == {}


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
    test_classification_rule_registry_registration_and_ordering()
    test_classification_rule_registry_requires_rule_id_and_label()
    test_rule_based_event_classifier_v1_selects_best_rule_match()
    test_rule_based_event_classifier_v1_uses_registration_order_for_ties()
    test_event_classification_explainable_rule_match_reason()
    test_weather_or_cloud_rule_classifies_strong_cloudy_timeline()
    test_weather_or_cloud_rule_classifies_overcast_timeline()
    test_weather_or_cloud_rule_classifies_degrading_trend_timeline()
    test_weather_or_cloud_rule_classifies_possible_condensation_timeline()
    test_weather_or_cloud_rule_classifies_condensation_onset_reason()
    test_weather_or_cloud_rule_classifies_condensation_timeline()
    test_weather_or_cloud_rule_ignores_weak_ambiguous_timeline()
    test_weather_or_cloud_rule_ignores_partly_cloudy_transition_without_strong_signal()
    test_weather_or_cloud_rule_uses_sky_transition_as_supporting_signal_only()
    test_weather_or_cloud_rule_ignores_missing_environment_summary()
    test_offline_event_classification_runner_writes_classifications_and_counts_labels()
    test_offline_event_classification_runner_does_not_change_default_classifier_registry()
    test_event_pipeline_offline_report_counts_jsonl_inputs()
    test_event_pipeline_offline_report_tolerates_missing_empty_and_malformed_files()
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
