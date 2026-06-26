import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from indi_allsky.detector_result import DETECTOR_RESULT_SCHEMA_VERSION
from indi_allsky.detector_result import DetectorEvidence
from indi_allsky.detector_result import DetectorContract
from indi_allsky.detector_result import DetectorRunContext
from indi_allsky.detector_result import DetectorResult
from indi_allsky.detector_result import DetectorRunner
from indi_allsky.detector_result import DetectorResultWriter
from indi_allsky.detector_result import build_detector_result_id
from indi_allsky.detector_result import build_detector_run_id
from indi_allsky.detector_result import build_detector_result_offline_report
from indi_allsky.detector_result import convert_detector_results_to_event_classifications_offline
from indi_allsky.detector_result import convert_detector_results_to_meteor_observations_offline
from indi_allsky.detector_result import default_detector_result_dir
from indi_allsky.detector_result import render_detector_result_text_summary
from indi_allsky.scientific_frame import ScientificFrame
from indi_allsky.scientific_frame import build_scientific_frame_sequence


def _evidence(**overrides):
    kwargs = {
        'evidence_type': 'line_like_signal',
        'frame_ids': [101, 102],
        'timestamps_utc': [
            '2026-06-26T00:00:00+00:00',
            '2026-06-26T00:00:10+00:00',
        ],
        'camera_id': 2,
        'profile_id': 'asi678mc',
        'score': 42.0,
        'confidence': 0.35,
        'geometry': {
            'line': {
                'x1': 10,
                'y1': 20,
                'x2': 100,
                'y2': 120,
            },
        },
        'metrics': {
            'length_px': 134.0,
        },
        'reasons': ['synthetic_line_signal'],
        'created_at': '2026-06-26T00:01:00+00:00',
    }
    kwargs.update(overrides)
    return DetectorEvidence(**kwargs)


def _result(**overrides):
    evidence = overrides.pop('evidence', [_evidence()])
    kwargs = {
        'detector_id': 'synthetic_detector',
        'detector_version': '0.0.1',
        'detector_type': 'rule_based_shadow',
        'status': 'shadow',
        'label': 'unclassified',
        'confidence': 0.35,
        'profile_id': 'asi678mc',
        'camera_id': 2,
        'sequence_id': 'scientific-sequence-abc',
        'timeline_id': 'timeline-abc',
        'evidence': evidence,
        'reasons': ['contract_test'],
        'created_at': '2026-06-26T00:02:00+00:00',
    }
    kwargs.update(overrides)
    return DetectorResult(**kwargs)


class DummyDetector(DetectorContract):
    detector_id = 'dummy_detector'
    detector_version = '1.0'
    detector_type = 'test_shadow'
    supported_labels = ('meteor_candidate',)
    required_input_type = 'ScientificFrameSequence'

    def __init__(self):
        self.last_context = None
        self.last_sequence = None

    def detect(self, input_sequence, context=None):
        self.last_sequence = input_sequence
        self.last_context = context
        return [
            DetectorResult(
                detector_id=self.detector_id,
                detector_version=self.detector_version,
                detector_type=self.detector_type,
                status='candidate',
                label='meteor_candidate',
                confidence=0.44,
                profile_id=input_sequence.profile_id,
                camera_id=input_sequence.camera_id,
                sequence_id=input_sequence.sequence_id,
                timeline_id=context.timeline_id if context else '',
                reasons=['dummy_result'],
                created_at='2026-06-26T04:00:00+00:00',
            ),
        ]


class FailingDetector(DetectorContract):
    detector_id = 'failing_detector'
    detector_version = '1.0'
    detector_type = 'test_shadow'
    supported_labels = ('unknown_event',)
    required_input_type = 'ScientificFrameSequence'

    def detect(self, input_sequence, context=None):
        raise RuntimeError('synthetic failure')


def _sequence():
    return build_scientific_frame_sequence([
        ScientificFrame(
            timestamp='2026-06-26T00:00:00+00:00',
            camera_uuid='camera-uuid-2',
            camera_id=2,
            profile_id='asi678mc',
            source_image_path='/tmp/frame-a.fits',
            detector_image_path='/tmp/frame-a.fits',
            detector_image_type='fits',
        ),
        ScientificFrame(
            timestamp='2026-06-26T00:00:10+00:00',
            camera_uuid='camera-uuid-2',
            camera_id=2,
            profile_id='asi678mc',
            source_image_path='/tmp/frame-b.fits',
            detector_image_path='/tmp/frame-b.fits',
            detector_image_type='fits',
        ),
    ])


def test_detector_evidence_serializes_correctly():
    row = _evidence().to_dict()

    assert row['evidence_id'].startswith('detector-evidence-')
    assert row['evidence_type'] == 'line_like_signal'
    assert row['frame_ids'] == [101, 102]
    assert row['timestamps_utc'][0] == '2026-06-26T00:00:00+00:00'
    assert row['camera_id'] == 2
    assert row['profile_id'] == 'asi678mc'
    assert row['score'] == 42.0
    assert row['confidence'] == 0.35
    assert row['geometry']['line']['x1'] == 10
    assert row['metrics']['length_px'] == 134.0
    assert row['reasons'] == ['synthetic_line_signal']
    json.dumps(row, sort_keys=True)


def test_detector_result_serializes_correctly():
    row = _result().to_dict()

    assert row['schema_version'] == DETECTOR_RESULT_SCHEMA_VERSION
    assert row['detector_result_id'].startswith('detector-result-')
    assert row['detector_id'] == 'synthetic_detector'
    assert row['detector_version'] == '0.0.1'
    assert row['detector_type'] == 'rule_based_shadow'
    assert row['status'] == 'shadow'
    assert row['label'] == 'unclassified'
    assert row['confidence'] == 0.35
    assert row['profile_id'] == 'asi678mc'
    assert row['camera_id'] == 2
    assert row['sequence_id'] == 'scientific-sequence-abc'
    assert row['timeline_id'] == 'timeline-abc'
    assert row['evidence'][0]['evidence_type'] == 'line_like_signal'
    assert row['reasons'] == ['contract_test']
    json.dumps(row, sort_keys=True)


def test_detector_result_schema_version_is_forced():
    row = _result(schema_version='future').to_dict()

    assert row['schema_version'] == DETECTOR_RESULT_SCHEMA_VERSION


def test_detector_result_deterministic_id():
    result_a = _result()
    result_b = _result(created_at='2026-06-26T01:00:00+00:00')

    assert result_a.detector_result_id == result_b.detector_result_id
    assert result_a.detector_result_id == build_detector_result_id(
        'synthetic_detector',
        '0.0.1',
        'rule_based_shadow',
        'unclassified',
        'asi678mc',
        2,
        'scientific-sequence-abc',
        'timeline-abc',
        result_a.evidence,
    )


def test_detector_result_status_is_constrained():
    try:
        _result(status='validated')
    except ValueError as exc:
        assert 'status' in str(exc)
    else:
        raise AssertionError('Expected invalid status to raise ValueError')


def test_detector_result_generic_labels_are_allowed():
    for label in (
            'unclassified',
            'meteor_candidate',
            'satellite_or_aircraft_candidate',
            'weather_or_cloud_event',
            'light_pollution_or_artifact',
            'unknown_event',
    ):
        assert _result(label=label).label == label


def test_detector_result_invalid_label_is_rejected():
    try:
        _result(label='rms_meteor_confirmed')
    except ValueError as exc:
        assert 'label' in str(exc)
    else:
        raise AssertionError('Expected invalid label to raise ValueError')


def test_detector_result_evidence_list_preserved_from_dicts():
    result = _result(evidence=[_evidence().to_dict()])

    assert len(result.evidence) == 1
    assert isinstance(result.evidence[0], DetectorEvidence)
    assert result.evidence[0].evidence_type == 'line_like_signal'


def test_detector_result_stays_detector_agnostic():
    row = _result(label='meteor_candidate').to_dict()

    assert 'meteor_id' not in row
    assert 'meteor_observation' not in row
    assert 'radiant' not in row
    assert 'magnitude' not in row
    assert 'shower' not in row
    assert 'velocity' not in row
    assert 'rms' not in row


def test_detector_result_writer_writes_append_only_jsonl():
    with tempfile.TemporaryDirectory() as tmpdir:
        result_dir = Path(tmpdir).joinpath('detector_results')
        writer = DetectorResultWriter(result_dir)

        path_a = writer.write(_result(timeline_id='timeline-a'))
        path_b = writer.write(_result(timeline_id='timeline-b'))

        assert path_a == path_b
        assert path_a == result_dir.joinpath('2026-06-26.jsonl')
        rows = [
            json.loads(line)
            for line in path_a.read_text(encoding='utf-8').splitlines()
        ]
        assert len(rows) == 2
        assert rows[0]['timeline_id'] == 'timeline-a'
        assert rows[1]['timeline_id'] == 'timeline-b'
        assert rows[0]['schema_version'] == DETECTOR_RESULT_SCHEMA_VERSION


def test_detector_result_default_directory():
    assert default_detector_result_dir('/var/lib/indi-allsky') == Path('/var/lib/indi-allsky/detector_results')


def test_detector_result_offline_report_missing_file_is_safe():
    with tempfile.TemporaryDirectory() as tmpdir:
        report = build_detector_result_offline_report(Path(tmpdir).joinpath('missing.jsonl'))

    assert report['total_result_lines'] == 0
    assert report['malformed_lines'] == 0
    assert report['counts_by_label'] == {}
    assert report['evidence_count_total'] == 0


def test_detector_result_offline_report_counts_malformed_lines():
    with tempfile.TemporaryDirectory() as tmpdir:
        result_path = Path(tmpdir).joinpath('detector_results.jsonl')
        with result_path.open('w', encoding='utf-8') as f_result:
            f_result.write(json.dumps(_result(label='unknown_event').to_dict()))
            f_result.write('\n')
            f_result.write('not-json\n')
            f_result.write('\n')
            f_result.write('[]\n')

        report = build_detector_result_offline_report(result_path)

    assert report['total_result_lines'] == 1
    assert report['malformed_lines'] == 2
    assert report['counts_by_label'] == {'unknown_event': 1}


def test_detector_result_offline_report_counts_populated_fields():
    with tempfile.TemporaryDirectory() as tmpdir:
        result_path = Path(tmpdir).joinpath('detector_results.jsonl')
        rows = [
            _result(
                detector_id='detector-a',
                detector_type='rule_based_shadow',
                status='shadow',
                label='meteor_candidate',
                confidence=0.40,
                camera_id=1,
                profile_id='imx708-wide',
                sequence_id='sequence-a',
                timeline_id='timeline-a',
                evidence=[_evidence(evidence_type='line_like_signal', camera_id=1, profile_id='imx708-wide')],
            ).to_dict(),
            _result(
                detector_id='detector-a',
                detector_type='rule_based_shadow',
                status='candidate',
                label='meteor_candidate',
                confidence=0.60,
                camera_id=1,
                profile_id='imx708-wide',
                sequence_id='sequence-a',
                timeline_id='timeline-b',
                evidence=[_evidence(evidence_type='motion_signal', camera_id=1, profile_id='imx708-wide')],
            ).to_dict(),
            _result(
                detector_id='detector-b',
                detector_type='external_shadow',
                status='rejected',
                label='weather_or_cloud_event',
                confidence=0.20,
                camera_id=2,
                profile_id='asi678mc',
                sequence_id='sequence-b',
                timeline_id='timeline-c',
                evidence=[],
            ).to_dict(),
        ]
        with result_path.open('w', encoding='utf-8') as f_result:
            for row in rows:
                f_result.write(json.dumps(row, sort_keys=True))
                f_result.write('\n')

        report = build_detector_result_offline_report(result_path)

    assert report['total_result_lines'] == 3
    assert report['counts_by_detector_id'] == {'detector-a': 2, 'detector-b': 1}
    assert report['counts_by_detector_type'] == {'external_shadow': 1, 'rule_based_shadow': 2}
    assert report['counts_by_status'] == {'candidate': 1, 'rejected': 1, 'shadow': 1}
    assert report['counts_by_label'] == {'meteor_candidate': 2, 'weather_or_cloud_event': 1}
    assert report['counts_by_profile_id'] == {'asi678mc': 1, 'imx708-wide': 2}
    assert report['counts_by_camera_id'] == {'1': 2, '2': 1}
    assert report['counts_by_sequence_id'] == {'sequence-a': 2, 'sequence-b': 1}
    assert report['counts_by_timeline_id'] == {'timeline-a': 1, 'timeline-b': 1, 'timeline-c': 1}
    assert report['evidence_count_total'] == 2
    assert report['counts_by_evidence_type'] == {'line_like_signal': 1, 'motion_signal': 1}
    assert report['average_confidence_by_label'] == {
        'meteor_candidate': 0.5,
        'weather_or_cloud_event': 0.2,
    }


def test_detector_result_text_summary_empty_report():
    summary = render_detector_result_text_summary({}, date='2026-06-26')

    assert 'Detector Result Summary - 2026-06-26' in summary
    assert 'Results: 0' in summary
    assert 'Warning' not in summary


def test_detector_result_text_summary_populated_report():
    summary = render_detector_result_text_summary({
        'total_result_lines': 3,
        'counts_by_label': {
            'meteor_candidate': 2,
            'weather_or_cloud_event': 1,
        },
        'counts_by_detector_id': {
            'detector-a': 2,
            'detector-b': 1,
        },
        'malformed_lines': 0,
    })

    assert 'Results: 3' in summary
    assert 'By label: meteor_candidate=2, weather_or_cloud_event=1' in summary
    assert 'By detector: detector-a=2, detector-b=1' in summary
    assert 'Warning' not in summary


def test_detector_result_text_summary_malformed_warning_only_when_nonzero():
    clean_summary = render_detector_result_text_summary({
        'total_result_lines': 1,
        'malformed_lines': 0,
    })
    noisy_summary = render_detector_result_text_summary({
        'total_result_lines': 1,
        'malformed_lines': 2,
    })

    assert 'Warning' not in clean_summary
    assert 'Warning: malformed JSONL lines: 2' in noisy_summary


def test_detector_result_classification_bridge_writes_event_classification():
    with tempfile.TemporaryDirectory() as tmpdir:
        base_dir = Path(tmpdir)
        result_path = base_dir.joinpath('detector_results', '2026-06-26.jsonl')
        classification_dir = base_dir.joinpath('event_classifications')
        result_path.parent.mkdir(parents=True, exist_ok=True)

        detector_result = _result(
            label='meteor_candidate',
            status='candidate',
            confidence=0.62,
            created_at='2026-06-26T02:00:00+00:00',
        ).to_dict()
        with result_path.open('w', encoding='utf-8') as f_result:
            json.dump(detector_result, f_result, sort_keys=True, separators=(',', ':'))
            f_result.write('\n')

        summary = convert_detector_results_to_event_classifications_offline(
            result_path,
            output_dir=classification_dir,
        )

        assert summary['total_lines'] == 1
        assert summary['classifications_written'] == 1
        assert summary['skipped_error_results'] == 0
        assert summary['skipped_missing_label'] == 0
        assert summary['malformed_lines'] == 0
        assert summary['labels_count'] == {'meteor_candidate': 1}
        assert summary['append_only_duplicates_possible'] is True

        rows = [
            json.loads(line)
            for line in classification_dir.joinpath('2026-06-26.jsonl').read_text(encoding='utf-8').splitlines()
        ]
        assert len(rows) == 1
        assert rows[0]['schema_version'] == 'event_classification_v1'
        assert rows[0]['label'] == 'meteor_candidate'
        assert rows[0]['status'] == 'shadow'
        assert rows[0]['method'] == 'detector_result_bridge_v1'
        assert rows[0]['timeline_id'] == 'timeline-abc'
        assert rows[0]['camera_id'] == 2
        assert rows[0]['profile_id'] == 'asi678mc'
        assert rows[0]['confidence'] == 0.62
        assert rows[0]['rules_matched'] == []
        assert rows[0]['features_used']['detector_result_id'] == detector_result['detector_result_id']
        assert rows[0]['features_used']['detector_id'] == 'synthetic_detector'
        assert rows[0]['features_used']['detector_version'] == '0.0.1'
        assert rows[0]['features_used']['detector_type'] == 'rule_based_shadow'
        assert rows[0]['features_used']['sequence_id'] == 'scientific-sequence-abc'
        assert rows[0]['features_used']['evidence_count'] == 1
        assert rows[0]['features_used']['reasons'] == ['contract_test']


def test_detector_result_classification_bridge_skips_error_and_missing_label_and_malformed():
    with tempfile.TemporaryDirectory() as tmpdir:
        result_path = Path(tmpdir).joinpath('detector_results', '2026-06-26.jsonl')
        classification_dir = Path(tmpdir).joinpath('event_classifications')
        result_path.parent.mkdir(parents=True, exist_ok=True)

        error_result = _result(status='error', label='unknown_event').to_dict()
        missing_label = _result().to_dict()
        missing_label['label'] = ''
        with result_path.open('w', encoding='utf-8') as f_result:
            json.dump(error_result, f_result, sort_keys=True, separators=(',', ':'))
            f_result.write('\n')
            json.dump(missing_label, f_result, sort_keys=True, separators=(',', ':'))
            f_result.write('\n')
            f_result.write('not-json\n')

        summary = convert_detector_results_to_event_classifications_offline(
            result_path,
            output_dir=classification_dir,
        )

        assert summary['total_lines'] == 3
        assert summary['classifications_written'] == 0
        assert summary['skipped_error_results'] == 1
        assert summary['skipped_missing_label'] == 1
        assert summary['malformed_lines'] == 1
        assert summary['labels_count'] == {'unknown_event': 1}
        assert summary['output_paths'] == []
        assert not classification_dir.exists()


def test_detector_result_classification_bridge_missing_file_is_safe():
    with tempfile.TemporaryDirectory() as tmpdir:
        summary = convert_detector_results_to_event_classifications_offline(
            Path(tmpdir).joinpath('detector_results', 'missing.jsonl'),
            output_dir=Path(tmpdir).joinpath('event_classifications'),
        )

    assert summary == {
        'total_lines': 0,
        'classifications_written': 0,
        'skipped_error_results': 0,
        'skipped_missing_label': 0,
        'skipped_missing_required': 0,
        'malformed_lines': 0,
        'labels_count': {},
        'output_paths': [],
        'append_only_duplicates_possible': True,
    }


def test_detector_result_classification_bridge_appends_duplicates():
    with tempfile.TemporaryDirectory() as tmpdir:
        result_path = Path(tmpdir).joinpath('detector_results', '2026-06-26.jsonl')
        classification_dir = Path(tmpdir).joinpath('event_classifications')
        result_path.parent.mkdir(parents=True, exist_ok=True)

        with result_path.open('w', encoding='utf-8') as f_result:
            json.dump(_result(label='meteor_candidate').to_dict(), f_result, sort_keys=True, separators=(',', ':'))
            f_result.write('\n')

        convert_detector_results_to_event_classifications_offline(result_path, output_dir=classification_dir)
        convert_detector_results_to_event_classifications_offline(result_path, output_dir=classification_dir)

        rows = classification_dir.joinpath('2026-06-26.jsonl').read_text(encoding='utf-8').splitlines()

    assert len(rows) == 2


def test_detector_result_meteor_bridge_writes_meteor_observation():
    with tempfile.TemporaryDirectory() as tmpdir:
        base_dir = Path(tmpdir)
        result_path = base_dir.joinpath('detector_results', '2026-06-26.jsonl')
        observation_dir = base_dir.joinpath('meteor_observations')
        result_path.parent.mkdir(parents=True, exist_ok=True)

        detector_result = _result(
            label='meteor_candidate',
            status='candidate',
            confidence=0.72,
            created_at='2026-06-26T03:00:00+00:00',
        ).to_dict()
        with result_path.open('w', encoding='utf-8') as f_result:
            json.dump(detector_result, f_result, sort_keys=True, separators=(',', ':'))
            f_result.write('\n')

        summary = convert_detector_results_to_meteor_observations_offline(
            result_path,
            output_dir=observation_dir,
        )

        assert summary['total_lines'] == 1
        assert summary['meteor_results_found'] == 1
        assert summary['observations_written'] == 1
        assert summary['skipped_non_meteor_labels'] == 0
        assert summary['skipped_error_results'] == 0
        assert summary['malformed_lines'] == 0
        assert summary['labels_count'] == {'meteor_candidate': 1}
        assert summary['append_only_duplicates_possible'] is True

        rows = [
            json.loads(line)
            for line in observation_dir.joinpath('2026-06-26.jsonl').read_text(encoding='utf-8').splitlines()
        ]
        assert len(rows) == 1
        assert rows[0]['schema_version'] == 'meteor_observation_v1'
        assert rows[0]['source_event_id'] == detector_result['detector_result_id']
        assert rows[0]['source_timeline_id'] == 'timeline-abc'
        assert rows[0]['detector_id'] == 'synthetic_detector'
        assert rows[0]['detector_version'] == '0.0.1'
        assert rows[0]['confidence'] == 0.72
        assert rows[0]['observation_timestamp'] == '2026-06-26T03:00:00+00:00'
        assert rows[0]['camera_id'] == 2
        assert rows[0]['profile_id'] == 'asi678mc'
        assert rows[0]['status'] == 'shadow'
        assert rows[0]['validation_state'] == 'unknown'
        assert 'review_id' not in rows[0]
        assert 'validation_id' not in rows[0]
        assert 'rms' not in rows[0]
        assert 'radiant' not in rows[0]
        assert 'magnitude' not in rows[0]


def test_detector_result_meteor_bridge_uses_fallback_detector_provenance_and_evidence_timestamp():
    with tempfile.TemporaryDirectory() as tmpdir:
        result_path = Path(tmpdir).joinpath('detector_results', '2026-06-26.jsonl')
        observation_dir = Path(tmpdir).joinpath('meteor_observations')
        result_path.parent.mkdir(parents=True, exist_ok=True)

        detector_result = _result(label='meteor_candidate').to_dict()
        detector_result['created_at'] = ''
        detector_result['detector_id'] = ''
        detector_result['detector_version'] = ''
        with result_path.open('w', encoding='utf-8') as f_result:
            json.dump(detector_result, f_result, sort_keys=True, separators=(',', ':'))
            f_result.write('\n')

        convert_detector_results_to_meteor_observations_offline(
            result_path,
            output_dir=observation_dir,
            detector_id_fallback='fallback_detector',
            detector_version_fallback='fallback_v1',
        )

        rows = [
            json.loads(line)
            for line in observation_dir.joinpath('2026-06-26.jsonl').read_text(encoding='utf-8').splitlines()
        ]

    assert rows[0]['detector_id'] == 'fallback_detector'
    assert rows[0]['detector_version'] == 'fallback_v1'
    assert rows[0]['observation_timestamp'] == '2026-06-26T00:00:00+00:00'


def test_detector_result_meteor_bridge_skips_non_meteor_error_and_malformed():
    with tempfile.TemporaryDirectory() as tmpdir:
        result_path = Path(tmpdir).joinpath('detector_results', '2026-06-26.jsonl')
        observation_dir = Path(tmpdir).joinpath('meteor_observations')
        result_path.parent.mkdir(parents=True, exist_ok=True)

        non_meteor = _result(label='weather_or_cloud_event').to_dict()
        error_result = _result(status='error', label='meteor_candidate').to_dict()
        with result_path.open('w', encoding='utf-8') as f_result:
            json.dump(non_meteor, f_result, sort_keys=True, separators=(',', ':'))
            f_result.write('\n')
            json.dump(error_result, f_result, sort_keys=True, separators=(',', ':'))
            f_result.write('\n')
            f_result.write('not-json\n')

        summary = convert_detector_results_to_meteor_observations_offline(
            result_path,
            output_dir=observation_dir,
        )

        assert summary['total_lines'] == 3
        assert summary['meteor_results_found'] == 0
        assert summary['observations_written'] == 0
        assert summary['skipped_non_meteor_labels'] == 1
        assert summary['skipped_error_results'] == 1
        assert summary['malformed_lines'] == 1
        assert summary['labels_count'] == {'meteor_candidate': 1, 'weather_or_cloud_event': 1}
        assert summary['output_paths'] == []
        assert not observation_dir.exists()


def test_detector_result_meteor_bridge_missing_file_is_safe():
    with tempfile.TemporaryDirectory() as tmpdir:
        summary = convert_detector_results_to_meteor_observations_offline(
            Path(tmpdir).joinpath('detector_results', 'missing.jsonl'),
            output_dir=Path(tmpdir).joinpath('meteor_observations'),
        )

    assert summary == {
        'total_lines': 0,
        'meteor_results_found': 0,
        'observations_written': 0,
        'skipped_non_meteor_labels': 0,
        'skipped_error_results': 0,
        'skipped_missing_required': 0,
        'malformed_lines': 0,
        'labels_count': {},
        'output_paths': [],
        'append_only_duplicates_possible': True,
    }


def test_detector_result_meteor_bridge_appends_duplicates_without_reviews_or_validations():
    with tempfile.TemporaryDirectory() as tmpdir:
        base_dir = Path(tmpdir)
        result_path = base_dir.joinpath('detector_results', '2026-06-26.jsonl')
        observation_dir = base_dir.joinpath('meteor_observations')
        result_path.parent.mkdir(parents=True, exist_ok=True)

        with result_path.open('w', encoding='utf-8') as f_result:
            json.dump(_result(label='meteor_candidate').to_dict(), f_result, sort_keys=True, separators=(',', ':'))
            f_result.write('\n')

        convert_detector_results_to_meteor_observations_offline(result_path, output_dir=observation_dir)
        convert_detector_results_to_meteor_observations_offline(result_path, output_dir=observation_dir)

        rows = observation_dir.joinpath('2026-06-26.jsonl').read_text(encoding='utf-8').splitlines()

        assert len(rows) == 2
        assert not base_dir.joinpath('meteor_reviews').exists()
        assert not base_dir.joinpath('meteor_validations').exists()


def test_detector_run_context_serializes_and_builds_run_id():
    context = DetectorRunContext(
        mode='offline_test',
        profile_id='asi678mc',
        camera_id=2,
        timeline_id='timeline-abc',
        sequence_id='sequence-abc',
        config={'threshold': 0.5},
        notes='contract test',
        created_at='2026-06-26T04:00:00+00:00',
    )
    row = context.to_dict()

    assert row['run_id'] == build_detector_run_id(
        'offline_test',
        'asi678mc',
        2,
        'timeline-abc',
        'sequence-abc',
        '2026-06-26T04:00:00+00:00',
    )
    assert row['config'] == {'threshold': 0.5}
    assert row['notes'] == 'contract test'
    json.dumps(row, sort_keys=True)


def test_detector_contract_can_be_implemented_by_dummy_detector():
    detector = DummyDetector()

    assert detector.detector_id == 'dummy_detector'
    assert detector.detector_version == '1.0'
    assert detector.detector_type == 'test_shadow'
    assert detector.supported_labels == ('meteor_candidate',)
    assert detector.required_input_type == 'ScientificFrameSequence'


def test_detector_runner_calls_detector_and_returns_counts_without_writing():
    detector = DummyDetector()
    sequence = _sequence()
    context = DetectorRunContext.from_sequence(
        sequence,
        mode='manual',
        timeline_id='timeline-abc',
        created_at='2026-06-26T04:00:00+00:00',
    )

    summary = DetectorRunner(detector).run(sequence, context=context)

    assert detector.last_sequence is sequence
    assert detector.last_context is context
    assert summary == {
        'detector_id': 'dummy_detector',
        'detector_version': '1.0',
        'total_results': 1,
        'labels_count': {'meteor_candidate': 1},
        'statuses_count': {'candidate': 1},
        'results_written': 0,
        'output_paths': [],
    }


def test_detector_runner_writes_detector_result_jsonl_when_output_dir_is_provided():
    with tempfile.TemporaryDirectory() as tmpdir:
        output_dir = Path(tmpdir).joinpath('detector_results')
        detector = DummyDetector()
        sequence = _sequence()
        context = DetectorRunContext.from_sequence(
            sequence,
            timeline_id='timeline-abc',
            created_at='2026-06-26T04:00:00+00:00',
        )

        summary = DetectorRunner(detector, output_dir=output_dir).run(sequence, context=context)

        rows = [
            json.loads(line)
            for line in output_dir.joinpath('2026-06-26.jsonl').read_text(encoding='utf-8').splitlines()
        ]

    assert summary['results_written'] == 1
    assert len(summary['output_paths']) == 1
    assert rows[0]['schema_version'] == DETECTOR_RESULT_SCHEMA_VERSION
    assert rows[0]['detector_id'] == 'dummy_detector'
    assert rows[0]['label'] == 'meteor_candidate'
    assert rows[0]['timeline_id'] == 'timeline-abc'


def test_detector_runner_handles_detector_exception_as_error_result():
    detector = FailingDetector()
    sequence = _sequence()
    context = DetectorRunContext.from_sequence(
        sequence,
        timeline_id='timeline-abc',
        created_at='2026-06-26T04:00:00+00:00',
    )

    summary = DetectorRunner(detector).run(sequence, context=context)

    assert summary['detector_id'] == 'failing_detector'
    assert summary['total_results'] == 1
    assert summary['labels_count'] == {'unknown_event': 1}
    assert summary['statuses_count'] == {'error': 1}
    assert summary['results_written'] == 0


def test_detector_runner_writes_error_result_for_detector_exception():
    with tempfile.TemporaryDirectory() as tmpdir:
        output_dir = Path(tmpdir).joinpath('detector_results')
        sequence = _sequence()
        context = DetectorRunContext.from_sequence(
            sequence,
            timeline_id='timeline-abc',
            created_at='2026-06-26T04:00:00+00:00',
        )

        DetectorRunner(FailingDetector(), output_dir=output_dir).run(sequence, context=context)

        rows = [
            json.loads(line)
            for line in output_dir.joinpath('2026-06-26.jsonl').read_text(encoding='utf-8').splitlines()
        ]

    assert len(rows) == 1
    assert rows[0]['status'] == 'error'
    assert rows[0]['label'] == 'unknown_event'
    assert rows[0]['profile_id'] == 'asi678mc'
    assert rows[0]['camera_id'] == 2
    assert rows[0]['sequence_id'] == sequence.sequence_id
    assert rows[0]['timeline_id'] == 'timeline-abc'
    assert rows[0]['reasons'][0].startswith('detector_error:RuntimeError:')


if __name__ == '__main__':
    test_detector_evidence_serializes_correctly()
    test_detector_result_serializes_correctly()
    test_detector_result_schema_version_is_forced()
    test_detector_result_deterministic_id()
    test_detector_result_status_is_constrained()
    test_detector_result_generic_labels_are_allowed()
    test_detector_result_invalid_label_is_rejected()
    test_detector_result_evidence_list_preserved_from_dicts()
    test_detector_result_stays_detector_agnostic()
    test_detector_result_writer_writes_append_only_jsonl()
    test_detector_result_default_directory()
    test_detector_result_offline_report_missing_file_is_safe()
    test_detector_result_offline_report_counts_malformed_lines()
    test_detector_result_offline_report_counts_populated_fields()
    test_detector_result_text_summary_empty_report()
    test_detector_result_text_summary_populated_report()
    test_detector_result_text_summary_malformed_warning_only_when_nonzero()
    test_detector_result_classification_bridge_writes_event_classification()
    test_detector_result_classification_bridge_skips_error_and_missing_label_and_malformed()
    test_detector_result_classification_bridge_missing_file_is_safe()
    test_detector_result_classification_bridge_appends_duplicates()
    test_detector_result_meteor_bridge_writes_meteor_observation()
    test_detector_result_meteor_bridge_uses_fallback_detector_provenance_and_evidence_timestamp()
    test_detector_result_meteor_bridge_skips_non_meteor_error_and_malformed()
    test_detector_result_meteor_bridge_missing_file_is_safe()
    test_detector_result_meteor_bridge_appends_duplicates_without_reviews_or_validations()
    test_detector_run_context_serializes_and_builds_run_id()
    test_detector_contract_can_be_implemented_by_dummy_detector()
    test_detector_runner_calls_detector_and_returns_counts_without_writing()
    test_detector_runner_writes_detector_result_jsonl_when_output_dir_is_provided()
    test_detector_runner_handles_detector_exception_as_error_result()
    test_detector_runner_writes_error_result_for_detector_exception()
    print('detector result tests OK')
