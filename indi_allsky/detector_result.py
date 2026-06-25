import hashlib
import json
from dataclasses import asdict
from dataclasses import dataclass
from dataclasses import field
from datetime import datetime
from datetime import timezone
from pathlib import Path


DETECTOR_RESULT_SCHEMA_VERSION = 'detector_result_v1'
DETECTOR_RESULT_STATUS_VALUES = frozenset((
    'shadow',
    'candidate',
    'rejected',
    'error',
))
DETECTOR_RESULT_LABEL_VALUES = frozenset((
    'unclassified',
    'meteor_candidate',
    'satellite_or_aircraft_candidate',
    'weather_or_cloud_event',
    'light_pollution_or_artifact',
    'unknown_event',
))


def build_detector_evidence_id(
        evidence_type,
        frame_ids=None,
        timestamps_utc=None,
        camera_id=None,
        profile_id=None,
):
    identity_parts = (
        _string_value(evidence_type),
        '|'.join(sorted(_string_value(frame_id) for frame_id in _list_value(frame_ids))),
        '|'.join(sorted(_string_value(timestamp) for timestamp in _list_value(timestamps_utc))),
        _string_value(camera_id),
        _string_value(profile_id),
    )
    digest = hashlib.sha256('|'.join(identity_parts).encode('utf-8')).hexdigest()[:24]
    return 'detector-evidence-{0:s}'.format(digest)


def build_detector_result_id(
        detector_id,
        detector_version,
        detector_type,
        label,
        profile_id,
        camera_id,
        sequence_id=None,
        timeline_id=None,
        evidence=None,
):
    evidence_ids = []
    for evidence_item in evidence or []:
        if isinstance(evidence_item, DetectorEvidence):
            evidence_ids.append(evidence_item.evidence_id)
        elif isinstance(evidence_item, dict):
            evidence_ids.append(_string_value(evidence_item.get('evidence_id')))

    identity_parts = (
        _string_value(detector_id),
        _string_value(detector_version),
        _string_value(detector_type),
        _string_value(label),
        _string_value(profile_id),
        _string_value(camera_id),
        _string_value(sequence_id),
        _string_value(timeline_id),
        '|'.join(sorted(evidence_id for evidence_id in evidence_ids if evidence_id)),
    )
    digest = hashlib.sha256('|'.join(identity_parts).encode('utf-8')).hexdigest()[:24]
    return 'detector-result-{0:s}'.format(digest)


@dataclass
class DetectorEvidence:
    evidence_type: str
    frame_ids: list
    timestamps_utc: list
    camera_id: int
    profile_id: str
    score: float = 0.0
    confidence: float = 0.0
    geometry: dict = field(default_factory=dict)
    metrics: dict = field(default_factory=dict)
    reasons: list = field(default_factory=list)
    created_at: str = ''
    evidence_id: str = ''

    def __post_init__(self):
        self.evidence_type = _required_string(self.evidence_type, 'evidence_type')
        self.profile_id = _required_string(self.profile_id, 'profile_id')
        self.camera_id = int(self.camera_id)
        self.frame_ids = _list_value(self.frame_ids)
        self.timestamps_utc = _list_value(self.timestamps_utc)
        self.geometry = _dict_value(self.geometry)
        self.metrics = _dict_value(self.metrics)
        self.reasons = _list_value(self.reasons)
        self.created_at = _string_value(self.created_at) or _utc_now()
        self.score = float(self.score or 0.0)
        self.confidence = _clamp_confidence(self.confidence)

        self.evidence_id = _string_value(self.evidence_id)
        if not self.evidence_id:
            self.evidence_id = build_detector_evidence_id(
                self.evidence_type,
                self.frame_ids,
                self.timestamps_utc,
                self.camera_id,
                self.profile_id,
            )

    def to_dict(self):
        return asdict(self)


@dataclass
class DetectorResult:
    detector_id: str
    detector_version: str
    detector_type: str
    status: str
    label: str
    confidence: float
    profile_id: str
    camera_id: int
    sequence_id: str = ''
    timeline_id: str = ''
    evidence: list = field(default_factory=list)
    reasons: list = field(default_factory=list)
    created_at: str = ''
    detector_result_id: str = ''
    schema_version: str = DETECTOR_RESULT_SCHEMA_VERSION

    def __post_init__(self):
        self.schema_version = DETECTOR_RESULT_SCHEMA_VERSION
        self.detector_id = _required_string(self.detector_id, 'detector_id')
        self.detector_version = _required_string(self.detector_version, 'detector_version')
        self.detector_type = _required_string(self.detector_type, 'detector_type')
        self.profile_id = _required_string(self.profile_id, 'profile_id')
        self.camera_id = int(self.camera_id)
        self.sequence_id = _string_value(self.sequence_id)
        self.timeline_id = _string_value(self.timeline_id)
        self.status = _required_string(self.status, 'status')
        if self.status not in DETECTOR_RESULT_STATUS_VALUES:
            raise ValueError('Invalid DetectorResult status: {0:s}'.format(self.status))

        self.label = _required_string(self.label, 'label')
        if self.label not in DETECTOR_RESULT_LABEL_VALUES:
            raise ValueError('Invalid DetectorResult label: {0:s}'.format(self.label))

        self.confidence = _clamp_confidence(self.confidence)
        self.evidence = [
            item if isinstance(item, DetectorEvidence) else DetectorEvidence(**item)
            for item in (self.evidence or [])
        ]
        self.reasons = _list_value(self.reasons)
        self.created_at = _string_value(self.created_at) or _utc_now()

        self.detector_result_id = _string_value(self.detector_result_id)
        if not self.detector_result_id:
            self.detector_result_id = build_detector_result_id(
                self.detector_id,
                self.detector_version,
                self.detector_type,
                self.label,
                self.profile_id,
                self.camera_id,
                self.sequence_id,
                self.timeline_id,
                self.evidence,
            )

    def to_dict(self):
        data = asdict(self)
        data['evidence'] = [
            evidence_item.to_dict() if hasattr(evidence_item, 'to_dict') else dict(evidence_item)
            for evidence_item in self.evidence
        ]
        return data


class DetectorResultWriter:
    """Append-only JSONL persistence for detector-agnostic shadow results."""

    def __init__(self, result_dir):
        self.result_dir = Path(result_dir)

    def write(self, result):
        result_path = self._result_path_for(result)
        result_path.parent.mkdir(parents=True, exist_ok=True)
        with result_path.open('a', encoding='utf-8') as f_result:
            json.dump(result.to_dict(), f_result, sort_keys=True, separators=(',', ':'))
            f_result.write('\n')
        return result_path

    def _result_path_for(self, result):
        return self.result_dir.joinpath('{0:s}.jsonl'.format(_date_from_timestamp(result.created_at)))


def default_detector_result_dir(varlib_folder):
    return Path(varlib_folder).joinpath('detector_results')


def _clamp_confidence(value):
    confidence = float(value or 0.0)
    return max(0.0, min(1.0, confidence))


def _required_string(value, field_name):
    value = _string_value(value)
    if not value:
        raise ValueError('DetectorResult requires {0:s}'.format(field_name))
    return value


def _string_value(value):
    if value is None:
        return ''
    return str(value)


def _list_value(value):
    if value is None:
        return []
    if isinstance(value, (list, tuple)):
        return list(value)
    return [value]


def _dict_value(value):
    if value is None:
        return {}
    return dict(value)


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
