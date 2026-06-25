import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from indi_allsky.meteor_observation import METEOR_OBSERVATION_SCHEMA_VERSION
from indi_allsky.meteor_observation import METEOR_REVIEW_SCHEMA_VERSION
from indi_allsky.meteor_observation import MeteorObservation
from indi_allsky.meteor_observation import MeteorObservationWriter
from indi_allsky.meteor_observation import MeteorReview
from indi_allsky.meteor_observation import MeteorReviewWriter
from indi_allsky.meteor_observation import build_meteor_observation_id
from indi_allsky.meteor_observation import build_meteor_review_id
from indi_allsky.meteor_observation import default_meteor_observation_dir
from indi_allsky.meteor_observation import default_meteor_review_dir


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


def _meteor_review(**overrides):
    kwargs = {
        'meteor_id': 'meteor-abc123',
        'review_actor': 'automatic_policy',
        'review_timestamp': '2026-06-25T22:20:00+00:00',
        'review_result': 'pending',
        'confidence': 0.25,
        'evidence_sources': ['timeline-2026-06-25-0001', 'event-2026-06-25-0001'],
        'notes': 'shadow assessment only',
        'created_at': '2026-06-25T22:21:00+00:00',
    }
    kwargs.update(overrides)
    return MeteorReview(**kwargs)


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


def test_meteor_review_serialization():
    row = _meteor_review().to_dict()

    assert row['schema_version'] == METEOR_REVIEW_SCHEMA_VERSION
    assert row['review_id'].startswith('meteor-review-')
    assert row['meteor_id'] == 'meteor-abc123'
    assert row['review_actor'] == 'automatic_policy'
    assert row['review_timestamp'] == '2026-06-25T22:20:00+00:00'
    assert row['review_result'] == 'pending'
    assert row['confidence'] == 0.25
    assert row['evidence_sources'] == ['timeline-2026-06-25-0001', 'event-2026-06-25-0001']
    assert row['notes'] == 'shadow assessment only'
    assert row['created_at'] == '2026-06-25T22:21:00+00:00'
    json.dumps(row, sort_keys=True)


def test_meteor_review_schema_version_is_forced():
    row = _meteor_review(schema_version='future').to_dict()

    assert row['schema_version'] == 'meteor_review_v1'


def test_meteor_review_deterministic_id():
    review_a = _meteor_review(evidence_sources=['b', 'a'])
    review_b = _meteor_review(created_at='2026-06-26T00:00:00+00:00', evidence_sources=['a', 'b'])

    assert review_a.review_id == review_b.review_id
    assert review_a.review_id == build_meteor_review_id(
        'meteor-abc123',
        'automatic_policy',
        '2026-06-25T22:20:00+00:00',
        'pending',
        ['a', 'b'],
    )


def test_meteor_review_requires_core_fields():
    for field_name in (
            'meteor_id',
            'review_actor',
            'review_timestamp',
            'review_result',
    ):
        try:
            _meteor_review(**{field_name: ''})
        except ValueError as exc:
            assert field_name in str(exc)
        else:
            raise AssertionError('Expected ValueError for missing {0:s}'.format(field_name))


def test_meteor_review_actor_and_result_are_constrained():
    for field_name, value in (
            ('review_actor', 'unknown_bot'),
            ('review_result', 'validated'),
    ):
        try:
            _meteor_review(**{field_name: value})
        except ValueError as exc:
            assert field_name in str(exc)
        else:
            raise AssertionError('Expected ValueError for invalid {0:s}'.format(field_name))


def test_meteor_review_is_not_validation_or_detector_specific():
    row = _meteor_review().to_dict()

    assert 'validation_state' not in row
    assert 'rms' not in row
    assert 'magnitude' not in row
    assert 'shower' not in row


def test_meteor_review_jsonl_persistence_writes_one_review():
    with tempfile.TemporaryDirectory() as tmpdir:
        review_dir = Path(tmpdir).joinpath('meteor_reviews')
        writer = MeteorReviewWriter(review_dir)

        written_path = writer.write(_meteor_review())

        assert written_path == review_dir.joinpath('2026-06-25.jsonl')
        rows = written_path.read_text(encoding='utf-8').splitlines()
        assert len(rows) == 1
        row = json.loads(rows[0])
        assert row['schema_version'] == 'meteor_review_v1'
        assert row['review_id'].startswith('meteor-review-')
        assert row['meteor_id'] == 'meteor-abc123'


def test_meteor_review_jsonl_persistence_appends_multiple_reviews():
    with tempfile.TemporaryDirectory() as tmpdir:
        review_dir = Path(tmpdir).joinpath('meteor_reviews')
        writer = MeteorReviewWriter(review_dir)

        writer.write(_meteor_review(review_actor='automatic_policy', review_result='pending'))
        writer.write(_meteor_review(review_actor='human', review_result='accepted'))

        rows = [
            json.loads(line)
            for line in review_dir.joinpath('2026-06-25.jsonl').read_text(encoding='utf-8').splitlines()
        ]
        assert len(rows) == 2
        assert rows[0]['review_actor'] == 'automatic_policy'
        assert rows[1]['review_actor'] == 'human'
        assert rows[0]['review_id'] != rows[1]['review_id']


def test_meteor_review_default_directory():
    with tempfile.TemporaryDirectory() as tmpdir:
        assert default_meteor_review_dir(tmpdir) == Path(tmpdir).joinpath('meteor_reviews')


def test_meteor_review_jsonl_lines_are_valid_assessments_only():
    with tempfile.TemporaryDirectory() as tmpdir:
        writer = MeteorReviewWriter(Path(tmpdir).joinpath('meteor_reviews'))
        written_path = writer.write(_meteor_review())

        for line in written_path.read_text(encoding='utf-8').splitlines():
            row = json.loads(line)
            assert row['schema_version'] == METEOR_REVIEW_SCHEMA_VERSION
            assert 'validation_state' not in row
            assert 'rms' not in row
            assert 'ai_model' not in row
            assert 'magnitude' not in row
            assert 'shower' not in row
            assert 'radiant' not in row
            assert 'velocity' not in row
            assert 'orbit' not in row


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
    test_meteor_review_serialization()
    test_meteor_review_schema_version_is_forced()
    test_meteor_review_deterministic_id()
    test_meteor_review_requires_core_fields()
    test_meteor_review_actor_and_result_are_constrained()
    test_meteor_review_is_not_validation_or_detector_specific()
    test_meteor_review_jsonl_persistence_writes_one_review()
    test_meteor_review_jsonl_persistence_appends_multiple_reviews()
    test_meteor_review_default_directory()
    test_meteor_review_jsonl_lines_are_valid_assessments_only()
    print('meteor observation tests OK')
