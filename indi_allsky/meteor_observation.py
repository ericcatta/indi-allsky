import hashlib
from dataclasses import asdict
from dataclasses import dataclass
from datetime import datetime
from datetime import timezone


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


def _required_string(value, field_name):
    value = _string_value(value)
    if not value:
        raise ValueError('MeteorObservation requires {0:s}'.format(field_name))
    return value


def _string_value(value):
    if value is None:
        return ''
    return str(value).strip()


def _utc_now():
    return datetime.now(tz=timezone.utc).isoformat()
