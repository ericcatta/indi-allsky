import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from indi_allsky.meteor_observation import METEOR_OBSERVATION_SCHEMA_VERSION
from indi_allsky.meteor_observation import MeteorObservation
from indi_allsky.meteor_observation import MeteorObservationWriter
from indi_allsky.meteor_observation import build_meteor_observation_id
from indi_allsky.meteor_observation import default_meteor_observation_dir


def _meteor_observation(**overrides):
    kwargs = {
        'source_event_id': 'event-2026-06-25-0001',
        'source_timeline_id': 'timeline-2026-06-25-0001',
        'detector_id': 'synthetic_meteor_contract_test',
        'detector_version': '0.0.1',
        'confidence': 0.42,
        'validation_state': 'unknown',
        'observation_timestamp': '2026-06-25T22:15:00+00:00',
        'camera_id': 2,
        'profile_id': 'asi678mc',
        'created_at': '2026-06-25T22:16:00+00:00',
        'status': 'shadow',
    }
    kwargs.update(overrides)
    return MeteorObservation(**kwargs)


def test_meteor_observation_serialization():
    row = _meteor_observation().to_dict()

    assert row['schema_version'] == METEOR_OBSERVATION_SCHEMA_VERSION
    assert row['meteor_id'].startswith('meteor-')
    assert row['source_event_id'] == 'event-2026-06-25-0001'
    assert row['source_timeline_id'] == 'timeline-2026-06-25-0001'
    assert row['detector_id'] == 'synthetic_meteor_contract_test'
    assert row['detector_version'] == '0.0.1'
    assert row['confidence'] == 0.42
    assert row['validation_state'] == 'unknown'
    assert row['observation_timestamp'] == '2026-06-25T22:15:00+00:00'
    assert row['camera_id'] == 2
    assert row['profile_id'] == 'asi678mc'
    assert row['created_at'] == '2026-06-25T22:16:00+00:00'
    assert row['status'] == 'shadow'
    json.dumps(row, sort_keys=True)


def test_meteor_observation_schema_version_is_forced():
    row = _meteor_observation(schema_version='future').to_dict()

    assert row['schema_version'] == 'meteor_observation_v1'


def test_meteor_observation_requires_core_fields():
    for field_name in (
            'source_event_id',
            'source_timeline_id',
            'detector_id',
            'detector_version',
            'observation_timestamp',
            'profile_id',
            'validation_state',
            'status',
    ):
        try:
            _meteor_observation(**{field_name: ''})
        except ValueError as exc:
            assert field_name in str(exc)
        else:
            raise AssertionError('Expected ValueError for missing {0:s}'.format(field_name))


def test_meteor_observation_deterministic_id():
    observation_a = _meteor_observation()
    observation_b = _meteor_observation(created_at='2026-06-26T00:00:00+00:00')

    assert observation_a.meteor_id == observation_b.meteor_id
    assert observation_a.meteor_id == build_meteor_observation_id(
        'event-2026-06-25-0001',
        'timeline-2026-06-25-0001',
        'synthetic_meteor_contract_test',
        '0.0.1',
        '2026-06-25T22:15:00+00:00',
        2,
        'asi678mc',
    )


def test_meteor_observation_status_and_validation_state_are_constrained():
    for field_name, value in (
            ('status', 'production'),
            ('validation_state', 'reviewed_by_magic'),
    ):
        try:
            _meteor_observation(**{field_name: value})
        except ValueError as exc:
            assert field_name in str(exc)
        else:
            raise AssertionError('Expected ValueError for invalid {0:s}'.format(field_name))


def test_meteor_observation_stays_detector_independent():
    row = _meteor_observation().to_dict()

    assert 'candidate_type' not in row
    assert 'segment_type' not in row
    assert 'magnitude' not in row
    assert 'shower' not in row
    assert 'radiant' not in row
    assert 'velocity' not in row
    assert 'duration' not in row
    assert 'persistent_train' not in row
    assert 'orbit' not in row
    assert 'rms' not in row


def test_meteor_observation_jsonl_persistence_writes_one_observation():
    with tempfile.TemporaryDirectory() as tmpdir:
        observation_dir = Path(tmpdir).joinpath('meteor_observations')
        writer = MeteorObservationWriter(observation_dir)

        written_path = writer.write(_meteor_observation())

        assert written_path == observation_dir.joinpath('2026-06-25.jsonl')
        rows = written_path.read_text(encoding='utf-8').splitlines()
        assert len(rows) == 1
        row = json.loads(rows[0])
        assert row['schema_version'] == 'meteor_observation_v1'
        assert row['meteor_id'].startswith('meteor-')
        assert row['source_event_id'] == 'event-2026-06-25-0001'


def test_meteor_observation_jsonl_persistence_appends_multiple_observations():
    with tempfile.TemporaryDirectory() as tmpdir:
        observation_dir = Path(tmpdir).joinpath('meteor_observations')
        writer = MeteorObservationWriter(observation_dir)

        writer.write(_meteor_observation(source_event_id='event-a', source_timeline_id='timeline-a'))
        writer.write(_meteor_observation(source_event_id='event-b', source_timeline_id='timeline-b'))

        rows = [
            json.loads(line)
            for line in observation_dir.joinpath('2026-06-25.jsonl').read_text(encoding='utf-8').splitlines()
        ]
        assert len(rows) == 2
        assert rows[0]['source_event_id'] == 'event-a'
        assert rows[1]['source_event_id'] == 'event-b'
        assert rows[0]['meteor_id'] != rows[1]['meteor_id']


def test_meteor_observation_default_directory():
    with tempfile.TemporaryDirectory() as tmpdir:
        assert default_meteor_observation_dir(tmpdir) == Path(tmpdir).joinpath('meteor_observations')


def test_meteor_observation_jsonl_lines_are_valid_and_detector_independent():
    with tempfile.TemporaryDirectory() as tmpdir:
        writer = MeteorObservationWriter(Path(tmpdir).joinpath('meteor_observations'))
        written_path = writer.write(_meteor_observation())

        for line in written_path.read_text(encoding='utf-8').splitlines():
            row = json.loads(line)
            assert row['schema_version'] == METEOR_OBSERVATION_SCHEMA_VERSION
            assert 'magnitude' not in row
            assert 'shower' not in row
            assert 'radiant' not in row
            assert 'velocity' not in row
            assert 'duration' not in row
            assert 'persistent_train' not in row
            assert 'orbit' not in row
            assert 'rms' not in row


if __name__ == '__main__':
    test_meteor_observation_serialization()
    test_meteor_observation_schema_version_is_forced()
    test_meteor_observation_requires_core_fields()
    test_meteor_observation_deterministic_id()
    test_meteor_observation_status_and_validation_state_are_constrained()
    test_meteor_observation_stays_detector_independent()
    test_meteor_observation_jsonl_persistence_writes_one_observation()
    test_meteor_observation_jsonl_persistence_appends_multiple_observations()
    test_meteor_observation_default_directory()
    test_meteor_observation_jsonl_lines_are_valid_and_detector_independent()
    print('meteor observation tests OK')
