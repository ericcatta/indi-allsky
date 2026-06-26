import hashlib
import json
from collections import Counter
from dataclasses import asdict
from dataclasses import dataclass
from dataclasses import field
from datetime import datetime
from datetime import timezone
from pathlib import Path

from .event_candidate import EventClassification
from .event_candidate import EventClassificationWriter
from .meteor_observation import MeteorObservation
from .meteor_observation import MeteorObservationWriter


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


def build_detector_result_offline_report(result_path=None):
    result_rows, malformed_lines = _load_jsonl_rows(result_path)

    detector_counter = Counter()
    detector_type_counter = Counter()
    status_counter = Counter()
    label_counter = Counter()
    profile_counter = Counter()
    camera_counter = Counter()
    sequence_counter = Counter()
    timeline_counter = Counter()
    evidence_type_counter = Counter()
    confidence_by_label = {}
    evidence_count_total = 0

    for row in result_rows:
        _count_value(detector_counter, row.get('detector_id'))
        _count_value(detector_type_counter, row.get('detector_type'))
        _count_value(status_counter, row.get('status'))
        _count_value(label_counter, row.get('label'))
        _count_value(profile_counter, row.get('profile_id'))
        _count_value(camera_counter, row.get('camera_id'))
        _count_value(sequence_counter, row.get('sequence_id'))
        _count_value(timeline_counter, row.get('timeline_id'))

        label = _string_value(row.get('label'))
        if label:
            confidence_by_label.setdefault(label, []).append(float(row.get('confidence') or 0.0))

        evidence_items = row.get('evidence') or []
        if not isinstance(evidence_items, list):
            continue

        evidence_count_total += len(evidence_items)
        for evidence_item in evidence_items:
            if isinstance(evidence_item, dict):
                _count_value(evidence_type_counter, evidence_item.get('evidence_type'))

    return {
        'total_result_lines': len(result_rows),
        'malformed_lines': malformed_lines,
        'counts_by_detector_id': dict(sorted(detector_counter.items())),
        'counts_by_detector_type': dict(sorted(detector_type_counter.items())),
        'counts_by_status': dict(sorted(status_counter.items())),
        'counts_by_label': dict(sorted(label_counter.items())),
        'counts_by_profile_id': dict(sorted(profile_counter.items())),
        'counts_by_camera_id': dict(sorted(camera_counter.items())),
        'counts_by_sequence_id': dict(sorted(sequence_counter.items())),
        'counts_by_timeline_id': dict(sorted(timeline_counter.items())),
        'evidence_count_total': evidence_count_total,
        'counts_by_evidence_type': dict(sorted(evidence_type_counter.items())),
        'average_confidence_by_label': _average_confidence_by_label(confidence_by_label),
    }


def render_detector_result_text_summary(report, date=None):
    report = report or {}
    lines = []

    title = 'Detector Result Summary'
    if date:
        title = '{0:s} - {1:s}'.format(title, _string_value(date))
    lines.append(title)
    lines.append('Results: {0:d}'.format(_int_value(report.get('total_result_lines'))))

    label_counts = _dict_value(report.get('counts_by_label'))
    if label_counts:
        lines.append('By label: {0:s}'.format(_format_counts(label_counts)))

    detector_counts = _dict_value(report.get('counts_by_detector_id'))
    if detector_counts:
        lines.append('By detector: {0:s}'.format(_format_counts(detector_counts)))

    malformed_lines = _int_value(report.get('malformed_lines'))
    if malformed_lines:
        lines.append('Warning: malformed JSONL lines: {0:d}'.format(malformed_lines))

    return '\n'.join(lines)


def convert_detector_results_to_event_classifications_offline(
        detector_result_path,
        output_dir=None,
        method='detector_result_bridge_v1',
):
    """Convert DetectorResult JSONL rows into shadow EventClassification JSONL.

    This is an offline/manual bridge only.  It does not validate events, review
    events, create MeteorObservation records, or integrate with runtime capture.
    """
    result_rows, malformed_lines = _load_jsonl_rows(detector_result_path)
    labels_counter = Counter()
    classifications_written = 0
    skipped_error_results = 0
    skipped_missing_label = 0
    skipped_missing_required = 0
    output_paths = set()

    writer = None
    if result_rows:
        writer = EventClassificationWriter(
            _resolve_event_classification_output_dir(detector_result_path, output_dir)
        )

    for row in result_rows:
        label = _string_value(row.get('label'))
        if not label:
            skipped_missing_label += 1
            continue

        labels_counter[label] += 1

        if _string_value(row.get('status')) == 'error':
            skipped_error_results += 1
            continue

        classification = _event_classification_from_detector_result(row, method)
        if classification is None:
            skipped_missing_required += 1
            continue

        output_path = writer.write(classification)
        output_paths.add(str(output_path))
        classifications_written += 1

    return {
        'total_lines': len(result_rows) + malformed_lines,
        'classifications_written': classifications_written,
        'skipped_error_results': skipped_error_results,
        'skipped_missing_label': skipped_missing_label,
        'skipped_missing_required': skipped_missing_required,
        'malformed_lines': malformed_lines,
        'labels_count': dict(sorted(labels_counter.items())),
        'output_paths': sorted(output_paths),
        'append_only_duplicates_possible': True,
    }


def convert_detector_results_to_meteor_observations_offline(
        detector_result_path,
        output_dir=None,
        detector_id_fallback='detector_result_bridge',
        detector_version_fallback='detector_result_bridge_v1',
):
    """Convert meteor_candidate DetectorResult JSONL rows into MeteorObservation JSONL.

    This is an offline/manual bridge only.  It does not create reviews,
    validations, EventClassification records, detector output, or runtime hooks.
    """
    result_rows, malformed_lines = _load_jsonl_rows(detector_result_path)
    labels_counter = Counter()
    meteor_results_found = 0
    observations_written = 0
    skipped_non_meteor_labels = 0
    skipped_error_results = 0
    skipped_missing_required = 0
    output_paths = set()

    writer = None
    if result_rows:
        writer = MeteorObservationWriter(
            _resolve_meteor_observation_output_dir(detector_result_path, output_dir)
        )

    for row in result_rows:
        label = _string_value(row.get('label'))
        if label:
            labels_counter[label] += 1

        if _string_value(row.get('status')) == 'error':
            skipped_error_results += 1
            continue

        if label != 'meteor_candidate':
            skipped_non_meteor_labels += 1
            continue

        meteor_results_found += 1
        observation = _meteor_observation_from_detector_result(
            row,
            detector_id_fallback=detector_id_fallback,
            detector_version_fallback=detector_version_fallback,
        )
        if observation is None:
            skipped_missing_required += 1
            continue

        output_path = writer.write(observation)
        output_paths.add(str(output_path))
        observations_written += 1

    return {
        'total_lines': len(result_rows) + malformed_lines,
        'meteor_results_found': meteor_results_found,
        'observations_written': observations_written,
        'skipped_non_meteor_labels': skipped_non_meteor_labels,
        'skipped_error_results': skipped_error_results,
        'skipped_missing_required': skipped_missing_required,
        'malformed_lines': malformed_lines,
        'labels_count': dict(sorted(labels_counter.items())),
        'output_paths': sorted(output_paths),
        'append_only_duplicates_possible': True,
    }


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


def _load_jsonl_rows(path):
    if not path:
        return [], 0

    path = Path(path)
    if not path.exists() or not path.is_file():
        return [], 0

    rows = []
    malformed = 0
    with path.open('r', encoding='utf-8') as f_jsonl:
        for line in f_jsonl:
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                malformed += 1
                continue
            if isinstance(row, dict):
                rows.append(row)
            else:
                malformed += 1
    return rows, malformed


def _count_value(counter, value):
    value = _string_value(value)
    if value:
        counter[value] += 1


def _average_confidence_by_label(confidence_by_label):
    averages = {}
    for label, confidence_values in confidence_by_label.items():
        if not confidence_values:
            continue
        averages[label] = sum(confidence_values) / len(confidence_values)
    return dict(sorted(averages.items()))


def _int_value(value):
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0


def _format_counts(counts):
    return ', '.join(
        '{0:s}={1:d}'.format(_string_value(key), _int_value(value))
        for key, value in sorted(_dict_value(counts).items())
    )


def _event_classification_from_detector_result(row, method):
    try:
        classification = EventClassification(
            timeline_id=_string_value(row.get('timeline_id')),
            camera_id=int(row.get('camera_id')),
            profile_id=_required_string(row.get('profile_id'), 'profile_id'),
            created_at=_string_value(row.get('created_at')) or _utc_now(),
            confidence=_clamp_confidence(row.get('confidence')),
            rules_matched=[],
            alternative_labels=[],
            features_used={
                'detector_result_id': _string_value(row.get('detector_result_id')),
                'detector_id': _string_value(row.get('detector_id')),
                'detector_version': _string_value(row.get('detector_version')),
                'detector_type': _string_value(row.get('detector_type')),
                'sequence_id': _string_value(row.get('sequence_id')),
                'evidence_count': _evidence_count(row.get('evidence')),
                'reasons': _list_value(row.get('reasons')),
            },
            label=_string_value(row.get('label')),
        )
    except (TypeError, ValueError):
        return None

    classification.method = _string_value(method) or 'detector_result_bridge_v1'
    return classification


def _evidence_count(evidence_items):
    if isinstance(evidence_items, list):
        return len(evidence_items)
    return 0


def _resolve_event_classification_output_dir(detector_result_path, output_dir):
    if output_dir:
        return Path(output_dir)

    if not detector_result_path:
        return Path('event_classifications')

    detector_result_path = Path(detector_result_path)
    parent = detector_result_path.parent
    if parent.name == 'detector_results':
        return parent.parent.joinpath('event_classifications')

    return parent.joinpath('event_classifications')


def _meteor_observation_from_detector_result(
        row,
        detector_id_fallback='detector_result_bridge',
        detector_version_fallback='detector_result_bridge_v1',
):
    try:
        return MeteorObservation(
            source_event_id=_required_string(row.get('detector_result_id'), 'detector_result_id'),
            source_timeline_id=_string_value(row.get('timeline_id')),
            detector_id=_string_value(row.get('detector_id')) or detector_id_fallback,
            detector_version=_string_value(row.get('detector_version')) or detector_version_fallback,
            confidence=_clamp_confidence(row.get('confidence')),
            validation_state='unknown',
            observation_timestamp=_detector_result_observation_timestamp(row),
            camera_id=int(row.get('camera_id')),
            profile_id=_required_string(row.get('profile_id'), 'profile_id'),
            created_at=_string_value(row.get('created_at')) or _utc_now(),
            status='shadow',
        )
    except (TypeError, ValueError):
        return None


def _detector_result_observation_timestamp(row):
    created_at = _string_value(row.get('created_at'))
    if created_at:
        return created_at

    evidence_items = row.get('evidence') or []
    if not isinstance(evidence_items, list):
        return ''

    for evidence_item in evidence_items:
        if not isinstance(evidence_item, dict):
            continue
        timestamps = _list_value(evidence_item.get('timestamps_utc'))
        for timestamp in timestamps:
            timestamp = _string_value(timestamp)
            if timestamp:
                return timestamp
    return ''


def _resolve_meteor_observation_output_dir(detector_result_path, output_dir):
    if output_dir:
        return Path(output_dir)

    if not detector_result_path:
        return Path('meteor_observations')

    detector_result_path = Path(detector_result_path)
    parent = detector_result_path.parent
    if parent.name == 'detector_results':
        return parent.parent.joinpath('meteor_observations')

    return parent.joinpath('meteor_observations')
