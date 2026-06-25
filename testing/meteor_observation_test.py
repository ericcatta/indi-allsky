import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from indi_allsky.meteor_observation import METEOR_OBSERVATION_SCHEMA_VERSION
from indi_allsky.meteor_observation import MeteorObservation
from indi_allsky.meteor_observation import build_meteor_observation_id


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


if __name__ == '__main__':
    test_meteor_observation_serialization()
    test_meteor_observation_schema_version_is_forced()
    test_meteor_observation_requires_core_fields()
    test_meteor_observation_deterministic_id()
    test_meteor_observation_status_and_validation_state_are_constrained()
    test_meteor_observation_stays_detector_independent()
    print('meteor observation tests OK')
