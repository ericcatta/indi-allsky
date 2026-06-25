import json
import hashlib
from dataclasses import asdict
from dataclasses import dataclass
from datetime import datetime
from datetime import timezone
from pathlib import Path


METEOR_OBSERVATION_SCHEMA_VERSION = 'meteor_observation_v1'
METEOR_OBSERVATION_STATUS_VALUES = frozenset((
    'shadow',
    'validated',
    'reviewed',
    'ground_truth',
))
METEOR_OBSERVATION_VALIDATION_STATE_VALUES = frozenset((
    'unknown',
    'automatic',
    'human_reviewed',
    'ground_truth',
))
METEOR_REVIEW_SCHEMA_VERSION = 'meteor_review_v1'
METEOR_REVIEW_ACTOR_VALUES = frozenset((
    'automatic_policy',
    'human',
    'external_detector',
    'cross_camera',
    'ai_assisted',
))
METEOR_REVIEW_RESULT_VALUES = frozenset((
    'pending',
    'accepted',
    'rejected',
    'needs_more_evidence',
    'ground_truth',
))
METEOR_VALIDATION_SCHEMA_VERSION = 'meteor_validation_v1'
METEOR_VALIDATION_STATE_VALUES = frozenset((
    'unvalidated',
    'automatically_validated',
    'human_validated',
    'rejected',
    'ground_truth',
    'benchmark',
))
METEOR_VALIDATION_ACTOR_VALUES = frozenset((
    'automatic_policy',
    'human',
    'cross_camera',
    'external_detector',
    'ai_assisted',
))


def build_meteor_observation_id(
        source_event_id,
        source_timeline_id,
        detector_id,
        detector_version,
        observation_timestamp,
        camera_id,
        profile_id,
):
    """Build a stable meteor observation id from detector-independent evidence links."""
    identity_parts = (
        _string_value(source_event_id),
        _string_value(source_timeline_id),
        _string_value(detector_id),
        _string_value(detector_version),
        _string_value(observation_timestamp),
        _string_value(camera_id),
        _string_value(profile_id),
    )
    identity = '|'.join(identity_parts)
    digest = hashlib.sha256(identity.encode('utf-8')).hexdigest()[:24]
    return 'meteor-{0:s}'.format(digest)


def build_meteor_review_id(
        meteor_id,
        review_actor,
        review_timestamp,
        review_result,
        evidence_sources=None,
):
    """Build a stable review id from the assessed meteor and review context."""
    evidence_sources = _list_value(evidence_sources)
    identity_parts = (
        _string_value(meteor_id),
        _string_value(review_actor),
        _string_value(review_timestamp),
        _string_value(review_result),
        '|'.join(sorted(_string_value(source) for source in evidence_sources)),
    )
    identity = '|'.join(identity_parts)
    digest = hashlib.sha256(identity.encode('utf-8')).hexdigest()[:24]
    return 'meteor-review-{0:s}'.format(digest)


def build_meteor_validation_id(
        meteor_id,
        validation_state,
        validation_actor,
        validation_timestamp,
        evidence_review_ids=None,
        evidence_sources=None,
):
    """Build a stable validation id from trust decision context."""
    evidence_review_ids = _list_value(evidence_review_ids)
    evidence_sources = _list_value(evidence_sources)
    identity_parts = (
        _string_value(meteor_id),
        _string_value(validation_state),
        _string_value(validation_actor),
        _string_value(validation_timestamp),
        '|'.join(sorted(_string_value(review_id) for review_id in evidence_review_ids)),
        '|'.join(sorted(_string_value(source) for source in evidence_sources)),
    )
    identity = '|'.join(identity_parts)
    digest = hashlib.sha256(identity.encode('utf-8')).hexdigest()[:24]
    return 'meteor-validation-{0:s}'.format(digest)


@dataclass
class MeteorObservation:
    source_event_id: str
    source_timeline_id: str
    detector_id: str
    detector_version: str
    confidence: float
    validation_state: str
    observation_timestamp: str
    camera_id: int
    profile_id: str
    created_at: str
    status: str
    meteor_id: str = ''
    schema_version: str = METEOR_OBSERVATION_SCHEMA_VERSION

    def __post_init__(self):
        self.schema_version = METEOR_OBSERVATION_SCHEMA_VERSION

        self.source_event_id = _required_string(self.source_event_id, 'source_event_id')
        self.source_timeline_id = _required_string(self.source_timeline_id, 'source_timeline_id')
        self.detector_id = _required_string(self.detector_id, 'detector_id')
        self.detector_version = _required_string(self.detector_version, 'detector_version')
        self.observation_timestamp = _required_string(self.observation_timestamp, 'observation_timestamp')
        self.profile_id = _required_string(self.profile_id, 'profile_id')
        self.created_at = _string_value(self.created_at) or _utc_now()

        self.camera_id = int(self.camera_id)
        self.confidence = float(self.confidence or 0.0)
        self.confidence = max(0.0, min(1.0, self.confidence))

        self.validation_state = _required_string(self.validation_state, 'validation_state')
        if self.validation_state not in METEOR_OBSERVATION_VALIDATION_STATE_VALUES:
            raise ValueError('Invalid MeteorObservation validation_state: {0:s}'.format(self.validation_state))

        self.status = _required_string(self.status, 'status')
        if self.status not in METEOR_OBSERVATION_STATUS_VALUES:
            raise ValueError('Invalid MeteorObservation status: {0:s}'.format(self.status))

        self.meteor_id = _string_value(self.meteor_id)
        if not self.meteor_id:
            self.meteor_id = build_meteor_observation_id(
                self.source_event_id,
                self.source_timeline_id,
                self.detector_id,
                self.detector_version,
                self.observation_timestamp,
                self.camera_id,
                self.profile_id,
            )

    def to_dict(self):
        return asdict(self)


@dataclass
class MeteorReview:
    meteor_id: str
    review_actor: str
    review_timestamp: str
    review_result: str
    confidence: float
    evidence_sources: list
    notes: str
    created_at: str
    review_id: str = ''
    schema_version: str = METEOR_REVIEW_SCHEMA_VERSION

    def __post_init__(self):
        self.schema_version = METEOR_REVIEW_SCHEMA_VERSION

        self.meteor_id = _required_string(self.meteor_id, 'meteor_id')
        self.review_timestamp = _required_string(self.review_timestamp, 'review_timestamp')
        self.created_at = _string_value(self.created_at) or _utc_now()
        self.notes = _string_value(self.notes)

        self.review_actor = _required_string(self.review_actor, 'review_actor')
        if self.review_actor not in METEOR_REVIEW_ACTOR_VALUES:
            raise ValueError('Invalid MeteorReview review_actor: {0:s}'.format(self.review_actor))

        self.review_result = _required_string(self.review_result, 'review_result')
        if self.review_result not in METEOR_REVIEW_RESULT_VALUES:
            raise ValueError('Invalid MeteorReview review_result: {0:s}'.format(self.review_result))

        self.confidence = float(self.confidence or 0.0)
        self.confidence = max(0.0, min(1.0, self.confidence))
        self.evidence_sources = _list_value(self.evidence_sources)

        self.review_id = _string_value(self.review_id)
        if not self.review_id:
            self.review_id = build_meteor_review_id(
                self.meteor_id,
                self.review_actor,
                self.review_timestamp,
                self.review_result,
                self.evidence_sources,
            )

    def to_dict(self):
        return asdict(self)


@dataclass
class MeteorValidation:
    meteor_id: str
    validation_state: str
    validation_actor: str
    validation_timestamp: str
    confidence: float
    evidence_review_ids: list
    evidence_sources: list
    reason: str
    created_at: str
    validation_id: str = ''
    schema_version: str = METEOR_VALIDATION_SCHEMA_VERSION

    def __post_init__(self):
        self.schema_version = METEOR_VALIDATION_SCHEMA_VERSION

        self.meteor_id = _required_string(self.meteor_id, 'meteor_id')
        self.validation_timestamp = _required_string(self.validation_timestamp, 'validation_timestamp')
        self.created_at = _string_value(self.created_at) or _utc_now()
        self.reason = _string_value(self.reason)

        self.validation_state = _required_string(self.validation_state, 'validation_state')
        if self.validation_state not in METEOR_VALIDATION_STATE_VALUES:
            raise ValueError('Invalid MeteorValidation validation_state: {0:s}'.format(self.validation_state))

        self.validation_actor = _required_string(self.validation_actor, 'validation_actor')
        if self.validation_actor not in METEOR_VALIDATION_ACTOR_VALUES:
            raise ValueError('Invalid MeteorValidation validation_actor: {0:s}'.format(self.validation_actor))

        self.confidence = float(self.confidence or 0.0)
        self.confidence = max(0.0, min(1.0, self.confidence))
        self.evidence_review_ids = _list_value(self.evidence_review_ids)
        self.evidence_sources = _list_value(self.evidence_sources)

        self.validation_id = _string_value(self.validation_id)
        if not self.validation_id:
            self.validation_id = build_meteor_validation_id(
                self.meteor_id,
                self.validation_state,
                self.validation_actor,
                self.validation_timestamp,
                self.evidence_review_ids,
                self.evidence_sources,
            )

    def to_dict(self):
        return asdict(self)


class MeteorObservationWriter:
    """Append-only JSONL persistence for detector-independent meteor observations."""

    def __init__(self, observation_dir):
        self.observation_dir = Path(observation_dir)

    def write(self, observation):
        observation_path = self._observation_path_for(observation)
        observation_path.parent.mkdir(parents=True, exist_ok=True)
        with observation_path.open('a', encoding='utf-8') as f_observation:
            json.dump(observation.to_dict(), f_observation, sort_keys=True, separators=(',', ':'))
            f_observation.write('\n')
        return observation_path

    def _observation_path_for(self, observation):
        return self.observation_dir.joinpath('{0:s}.jsonl'.format(_date_from_timestamp(observation.observation_timestamp)))


class MeteorReviewWriter:
    """Append-only JSONL persistence for meteor review assessments."""

    def __init__(self, review_dir):
        self.review_dir = Path(review_dir)

    def write(self, review):
        review_path = self._review_path_for(review)
        review_path.parent.mkdir(parents=True, exist_ok=True)
        with review_path.open('a', encoding='utf-8') as f_review:
            json.dump(review.to_dict(), f_review, sort_keys=True, separators=(',', ':'))
            f_review.write('\n')
        return review_path

    def _review_path_for(self, review):
        return self.review_dir.joinpath('{0:s}.jsonl'.format(_date_from_timestamp(review.review_timestamp)))


class MeteorValidationWriter:
    """Append-only JSONL persistence for meteor trust decisions."""

    def __init__(self, validation_dir):
        self.validation_dir = Path(validation_dir)

    def write(self, validation):
        validation_path = self._validation_path_for(validation)
        validation_path.parent.mkdir(parents=True, exist_ok=True)
        with validation_path.open('a', encoding='utf-8') as f_validation:
            json.dump(validation.to_dict(), f_validation, sort_keys=True, separators=(',', ':'))
            f_validation.write('\n')
        return validation_path

    def _validation_path_for(self, validation):
        return self.validation_dir.joinpath('{0:s}.jsonl'.format(_date_from_timestamp(validation.validation_timestamp)))


def default_meteor_observation_dir(varlib_folder):
    return Path(varlib_folder).joinpath('meteor_observations')


def default_meteor_review_dir(varlib_folder):
    return Path(varlib_folder).joinpath('meteor_reviews')


def default_meteor_validation_dir(varlib_folder):
    return Path(varlib_folder).joinpath('meteor_validations')


def _required_string(value, field_name):
    value = _string_value(value)
    if not value:
        raise ValueError('MeteorObservation requires {0:s}'.format(field_name))
    return value


def _string_value(value):
    if value is None:
        return ''
    return str(value).strip()


def _list_value(value):
    if value is None:
        return []
    if isinstance(value, (list, tuple)):
        return [_string_value(item) for item in value if _string_value(item)]
    return [_string_value(value)] if _string_value(value) else []


def _utc_now():
    return datetime.now(tz=timezone.utc).isoformat()


def _date_from_timestamp(timestamp):
    timestamp_str = _string_value(timestamp)
    if timestamp_str.endswith('Z'):
        timestamp_str = '{0:s}+00:00'.format(timestamp_str[:-1])

    try:
        return datetime.fromisoformat(timestamp_str).date().isoformat()
    except ValueError:
        if len(timestamp_str) >= 10:
            return datetime.fromisoformat(timestamp_str[:10]).date().isoformat()
        raise
