import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from indi_allsky.detector_result import DETECTOR_RESULT_SCHEMA_VERSION
from indi_allsky.detector_result import DetectorEvidence
from indi_allsky.detector_result import DetectorResult
from indi_allsky.detector_result import DetectorResultWriter
from indi_allsky.detector_result import build_detector_result_id
from indi_allsky.detector_result import default_detector_result_dir


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
    print('detector result tests OK')
