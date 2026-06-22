import json
from collections import Counter
from dataclasses import asdict
from dataclasses import dataclass
from dataclasses import field
from datetime import datetime
from pathlib import Path


EVENT_CANDIDATE_SCHEMA_VERSION = 'event_candidate_v0'
EVENT_CANDIDATE_TYPE = 'unclassified'
EVENT_TIMELINE_SCHEMA_VERSION = 'event_timeline_segment_v0'
EVENT_TIMELINE_TYPE = 'unclassified'
EVENT_CLASSIFICATION_SCHEMA_VERSION = 'event_classification_v1'
EVENT_CLASSIFICATION_LABEL = 'unknown_event'
EVENT_CLASSIFICATION_STATUS = 'shadow'
EVENT_CLASSIFICATION_METHOD = 'rule_based_v1'
DEFAULT_TRIGGER_CONFIG = {
    'enabled': True,
    'brightness_spike_meter_delta': 60.0,
    'brightness_spike_over_target': 50.0,
    'quality_drop_score': 45.0,
    'quality_drop_delta': 25.0,
}
DEFAULT_RUNTIME_TRIGGER_CONFIG = {
    **DEFAULT_TRIGGER_CONFIG,
    'enabled': False,
    'max_candidates_per_hour': 100,
}


@dataclass
class EventCandidate:
    candidate_id: str
    camera_id: int
    profile_id: str
    frame_id: int
    timestamp_utc: str
    night_id: str
    candidate_score: float = 0.0
    reasons: list = field(default_factory=list)
    source_metrics: dict = field(default_factory=dict)
    quality_context: dict = field(default_factory=dict)
    environment_context: dict = field(default_factory=dict)
    schema_version: str = EVENT_CANDIDATE_SCHEMA_VERSION
    candidate_type: str = EVENT_CANDIDATE_TYPE
    shadow_only: bool = True

    def __post_init__(self):
        self.schema_version = EVENT_CANDIDATE_SCHEMA_VERSION
        self.candidate_type = EVENT_CANDIDATE_TYPE
        self.shadow_only = True

        if self.reasons is None:
            self.reasons = []
        if self.source_metrics is None:
            self.source_metrics = {}
        if self.quality_context is None:
            self.quality_context = {}
        if self.environment_context is None:
            self.environment_context = {}

        self.candidate_score = float(self.candidate_score or 0.0)

    def to_dict(self):
        return asdict(self)


@dataclass
class EventTimelineSegment:
    timeline_id: str
    camera_id: int
    profile_id: str
    night_id: str
    start_timestamp_utc: str
    end_timestamp_utc: str
    duration_seconds: float
    candidate_count: int
    candidate_ids: list = field(default_factory=list)
    reasons: list = field(default_factory=list)
    max_candidate_score: float = 0.0
    average_candidate_score: float = 0.0
    quality_context_summary: dict = field(default_factory=dict)
    environment_context_summary: dict = field(default_factory=dict)
    schema_version: str = EVENT_TIMELINE_SCHEMA_VERSION
    segment_type: str = EVENT_TIMELINE_TYPE
    shadow_only: bool = True

    def __post_init__(self):
        self.schema_version = EVENT_TIMELINE_SCHEMA_VERSION
        self.segment_type = EVENT_TIMELINE_TYPE
        self.shadow_only = True

        if self.candidate_ids is None:
            self.candidate_ids = []
        if self.reasons is None:
            self.reasons = []
        if self.quality_context_summary is None:
            self.quality_context_summary = {}
        if self.environment_context_summary is None:
            self.environment_context_summary = {}

        self.duration_seconds = float(self.duration_seconds or 0.0)
        self.max_candidate_score = float(self.max_candidate_score or 0.0)
        self.average_candidate_score = float(self.average_candidate_score or 0.0)

    def to_dict(self):
        return asdict(self)


@dataclass
class EventClassification:
    timeline_id: str
    camera_id: int
    profile_id: str
    created_at: str
    confidence: float = 0.0
    rules_matched: list = field(default_factory=list)
    alternative_labels: list = field(default_factory=list)
    features_used: dict = field(default_factory=dict)
    schema_version: str = EVENT_CLASSIFICATION_SCHEMA_VERSION
    label: str = EVENT_CLASSIFICATION_LABEL
    status: str = EVENT_CLASSIFICATION_STATUS
    method: str = EVENT_CLASSIFICATION_METHOD

    def __post_init__(self):
        self.schema_version = EVENT_CLASSIFICATION_SCHEMA_VERSION
        self.label = EVENT_CLASSIFICATION_LABEL
        self.status = EVENT_CLASSIFICATION_STATUS
        self.method = EVENT_CLASSIFICATION_METHOD

        if self.rules_matched is None:
            self.rules_matched = []
        if self.alternative_labels is None:
            self.alternative_labels = []
        if self.features_used is None:
            self.features_used = {}

        self.confidence = float(self.confidence or 0.0)

    def to_dict(self):
        return asdict(self)


class EventCandidateWriter:
    """Append-only JSONL persistence for shadow event candidates."""

    def __init__(self, candidate_dir):
        self.candidate_dir = Path(candidate_dir)

    def write(self, candidate):
        candidate_path = self._candidate_path_for(candidate)
        candidate_path.parent.mkdir(parents=True, exist_ok=True)
        with candidate_path.open('a', encoding='utf-8') as f_candidate:
            json.dump(candidate.to_dict(), f_candidate, sort_keys=True, separators=(',', ':'))
            f_candidate.write('\n')
        return candidate_path

    def _candidate_path_for(self, candidate):
        return self.candidate_dir.joinpath('{0:s}.jsonl'.format(self._date_from_timestamp(candidate.timestamp_utc)))

    def _date_from_timestamp(self, timestamp):
        timestamp_str = str(timestamp or '').strip()
        if timestamp_str.endswith('Z'):
            timestamp_str = '{0:s}+00:00'.format(timestamp_str[:-1])

        try:
            return datetime.fromisoformat(timestamp_str).date().isoformat()
        except ValueError:
            if len(timestamp_str) >= 10:
                return datetime.fromisoformat(timestamp_str[:10]).date().isoformat()
            raise


class EventTimelineWriter:
    """Append-only JSONL persistence for shadow event timeline segments."""

    def __init__(self, timeline_dir):
        self.timeline_dir = Path(timeline_dir)

    def write(self, segment):
        timeline_path = self._timeline_path_for(segment)
        timeline_path.parent.mkdir(parents=True, exist_ok=True)
        with timeline_path.open('a', encoding='utf-8') as f_timeline:
            json.dump(segment.to_dict(), f_timeline, sort_keys=True, separators=(',', ':'))
            f_timeline.write('\n')
        return timeline_path

    def write_day(self, date, segments):
        timeline_path = self.timeline_dir.joinpath('{0:s}.jsonl'.format(str(date)))
        timeline_path.parent.mkdir(parents=True, exist_ok=True)
        with timeline_path.open('w', encoding='utf-8') as f_timeline:
            for segment in segments or []:
                json.dump(segment.to_dict(), f_timeline, sort_keys=True, separators=(',', ':'))
                f_timeline.write('\n')
        return timeline_path

    def _timeline_path_for(self, segment):
        return self.timeline_dir.joinpath('{0:s}.jsonl'.format(_date_from_timestamp(segment.start_timestamp_utc)))


class EventClassificationWriter:
    """Append-only JSONL persistence for shadow event classifications."""

    def __init__(self, classification_dir):
        self.classification_dir = Path(classification_dir)

    def write(self, classification):
        classification_path = self._classification_path_for(classification)
        classification_path.parent.mkdir(parents=True, exist_ok=True)
        with classification_path.open('a', encoding='utf-8') as f_classification:
            json.dump(classification.to_dict(), f_classification, sort_keys=True, separators=(',', ':'))
            f_classification.write('\n')
        return classification_path

    def _classification_path_for(self, classification):
        return self.classification_dir.joinpath('{0:s}.jsonl'.format(_date_from_timestamp(classification.created_at)))


class RuleBasedEventClassifierV1:
    """Shadow-only no-op classifier foundation for event timelines."""

    def classify_timeline(self, timeline, created_at=None):
        timeline_dict = timeline.to_dict() if hasattr(timeline, 'to_dict') else dict(timeline)
        created_at_value = created_at or datetime.utcnow().replace(microsecond=0).isoformat()

        return EventClassification(
            timeline_id=timeline_dict.get('timeline_id'),
            camera_id=timeline_dict.get('camera_id'),
            profile_id=timeline_dict.get('profile_id'),
            created_at=created_at_value,
            confidence=0.0,
            rules_matched=[],
            alternative_labels=[],
            features_used={
                'candidate_count': timeline_dict.get('candidate_count'),
                'duration_seconds': timeline_dict.get('duration_seconds'),
                'max_candidate_score': timeline_dict.get('max_candidate_score'),
                'average_candidate_score': timeline_dict.get('average_candidate_score'),
                'reasons': timeline_dict.get('reasons') or [],
            },
        )


class EventCandidateAnalytics:
    """Lightweight reader/summary layer for shadow event candidate JSONL files."""

    def __init__(self, candidate_dir):
        self.candidate_dir = Path(candidate_dir)

    def load_day(self, date):
        candidate_path = self._day_path(date)
        if not candidate_path.exists():
            return []

        rows = []
        with candidate_path.open('r', encoding='utf-8') as f_candidate:
            for line in f_candidate:
                line = line.strip()
                if not line:
                    continue
                try:
                    rows.append(json.loads(line))
                except ValueError:
                    continue

        return rows

    def get_nightly_event_summary(self, date=None):
        summary_date = self._latest_day() if date is None else str(date)
        candidates = self.load_day(summary_date) if summary_date else []
        scores = [
            score for score in (
                self._optional_float(candidate.get('candidate_score'))
                for candidate in candidates
            )
            if score is not None
        ]
        camera_counts = Counter()
        reason_counts = Counter()

        for candidate in candidates:
            camera_id = self._string_value(candidate.get('camera_id'))
            if camera_id:
                camera_counts.update([camera_id])

            reasons = candidate.get('reasons')
            if isinstance(reasons, list):
                reason_counts.update(self._string_value(reason) for reason in reasons if self._string_value(reason))

        return {
            'date': summary_date,
            'total_event_candidates': len(candidates),
            'event_candidates_by_camera': dict(camera_counts),
            'event_candidates_by_reason': dict(reason_counts),
            'average_candidate_score': self._average(scores),
            'max_candidate_score': max(scores) if scores else None,
        }

    def _day_path(self, date):
        return self.candidate_dir.joinpath('{0:s}.jsonl'.format(str(date)))

    def _latest_day(self):
        files = sorted(self.candidate_dir.glob('*.jsonl'))
        if not files:
            return None
        return files[-1].stem

    def _average(self, values):
        if not values:
            return None
        return sum(values) / len(values)

    def _optional_float(self, value):
        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    def _string_value(self, value):
        if value is None:
            return ''
        return str(value)


class EventTimelineAnalytics:
    """Lightweight reader/summary layer for shadow event timeline JSONL files."""

    def __init__(self, timeline_dir):
        self.timeline_dir = Path(timeline_dir)

    def load_day(self, date):
        timeline_path = self._day_path(date)
        if not timeline_path.exists():
            return []

        rows = []
        with timeline_path.open('r', encoding='utf-8') as f_timeline:
            for line in f_timeline:
                line = line.strip()
                if not line:
                    continue
                try:
                    rows.append(json.loads(line))
                except ValueError:
                    continue

        return rows

    def get_nightly_timeline_summary(self, date=None):
        summary_date = self._latest_day() if date is None else str(date)
        segments = self.load_day(summary_date) if summary_date else []
        durations = [
            value for value in (
                _optional_float(segment.get('duration_seconds'))
                for segment in segments
            )
            if value is not None
        ]
        candidate_counts = [
            value for value in (
                _optional_float(segment.get('candidate_count'))
                for segment in segments
            )
            if value is not None
        ]
        camera_counts = Counter()
        reason_counts = Counter()

        for segment in segments:
            camera_id = _string_value(segment.get('camera_id'))
            if camera_id:
                camera_counts.update([camera_id])

            reasons = segment.get('reasons')
            if isinstance(reasons, list):
                reason_counts.update(_string_value(reason) for reason in reasons if _string_value(reason))

        return {
            'date': summary_date,
            'total_timeline_segments': len(segments),
            'timeline_segments_by_camera': dict(camera_counts),
            'average_segment_duration_seconds': _average(durations),
            'max_segment_duration_seconds': max(durations) if durations else None,
            'average_candidates_per_segment': _average(candidate_counts),
            'max_candidates_per_segment': max(candidate_counts) if candidate_counts else None,
            'timeline_segments_by_reason': dict(reason_counts),
        }

    def _day_path(self, date):
        return self.timeline_dir.joinpath('{0:s}.jsonl'.format(str(date)))

    def _latest_day(self):
        files = sorted(self.timeline_dir.glob('*.jsonl'))
        if not files:
            return None
        return files[-1].stem


class EventCandidateRuntimeDiagnostics:
    """Small JSON counter store for shadow runtime trigger observability."""

    def __init__(self, diagnostics_path):
        self.diagnostics_path = Path(diagnostics_path)

    def read_summary(self):
        summary = self._empty_summary()
        try:
            if self.diagnostics_path.exists():
                with self.diagnostics_path.open('r', encoding='utf-8') as f_diagnostics:
                    stored_summary = json.load(f_diagnostics)
                if isinstance(stored_summary, dict):
                    summary.update({
                        key: stored_summary.get(key, summary.get(key))
                        for key in summary.keys()
                    })
        except (OSError, ValueError):
            return summary

        summary['total_evaluations'] = int(summary.get('total_evaluations') or 0)
        summary['total_generated_candidates'] = int(summary.get('total_generated_candidates') or 0)
        summary['trigger_evaluation_failures'] = int(summary.get('trigger_evaluation_failures') or 0)
        summary['candidates_by_reason'] = self._counter_dict(summary.get('candidates_by_reason'))
        summary['candidates_by_hour'] = self._counter_dict(summary.get('candidates_by_hour'))
        summary['rate_limited_events'] = int(summary.get('rate_limited_events') or 0)
        return summary

    def candidates_this_hour(self, timestamp):
        summary = self.read_summary()
        return int(summary.get('candidates_by_hour', {}).get(self._hour_key(timestamp), 0))

    def record_evaluation(self, enabled, max_candidates_per_hour):
        summary = self.read_summary()
        summary['enabled'] = bool(enabled)
        summary['max_candidates_per_hour'] = int(max_candidates_per_hour)
        summary['total_evaluations'] = int(summary.get('total_evaluations') or 0) + 1
        summary['last_status'] = 'evaluated'
        self.write_summary(summary)
        return summary

    def record_disabled(self, max_candidates_per_hour):
        summary = self.read_summary()
        summary['enabled'] = False
        summary['max_candidates_per_hour'] = int(max_candidates_per_hour)
        summary['last_status'] = 'disabled'
        self.write_summary(summary)
        return summary

    def record_generated(self, candidates, timestamp, enabled, max_candidates_per_hour):
        summary = self.read_summary()
        summary['enabled'] = bool(enabled)
        summary['max_candidates_per_hour'] = int(max_candidates_per_hour)
        summary['total_generated_candidates'] = int(summary.get('total_generated_candidates') or 0) + len(candidates)
        summary['last_status'] = 'generated'

        reason_counter = Counter(summary.get('candidates_by_reason') or {})
        for candidate in candidates:
            for reason in getattr(candidate, 'reasons', []) or []:
                reason_value = _string_value(reason)
                if reason_value:
                    reason_counter.update([reason_value])
        summary['candidates_by_reason'] = dict(reason_counter)

        hour_key = self._hour_key(timestamp)
        hour_counter = Counter(summary.get('candidates_by_hour') or {})
        hour_counter.update({hour_key: len(candidates)})
        summary['candidates_by_hour'] = dict(hour_counter)

        self.write_summary(summary)
        return summary

    def record_failure(self, enabled, max_candidates_per_hour):
        summary = self.read_summary()
        summary['enabled'] = bool(enabled)
        summary['max_candidates_per_hour'] = int(max_candidates_per_hour)
        summary['trigger_evaluation_failures'] = int(summary.get('trigger_evaluation_failures') or 0) + 1
        summary['last_status'] = 'failure'
        self.write_summary(summary)
        return summary

    def record_rate_limited(self, enabled, max_candidates_per_hour):
        summary = self.read_summary()
        summary['enabled'] = bool(enabled)
        summary['max_candidates_per_hour'] = int(max_candidates_per_hour)
        summary['rate_limited_events'] = int(summary.get('rate_limited_events') or 0) + 1
        summary['last_status'] = 'rate_limited'
        self.write_summary(summary)
        return summary

    def write_summary(self, summary):
        self.diagnostics_path.parent.mkdir(parents=True, exist_ok=True)
        tmp_path = self.diagnostics_path.with_suffix('{0:s}.tmp'.format(self.diagnostics_path.suffix))
        with tmp_path.open('w', encoding='utf-8') as f_diagnostics:
            json.dump(summary, f_diagnostics, sort_keys=True, separators=(',', ':'))
            f_diagnostics.write('\n')
        tmp_path.replace(self.diagnostics_path)

    def _empty_summary(self):
        return {
            'enabled': False,
            'max_candidates_per_hour': int(DEFAULT_RUNTIME_TRIGGER_CONFIG['max_candidates_per_hour']),
            'total_evaluations': 0,
            'total_generated_candidates': 0,
            'candidates_by_reason': {},
            'trigger_evaluation_failures': 0,
            'rate_limited_events': 0,
            'candidates_by_hour': {},
            'last_status': 'none',
        }

    def _hour_key(self, timestamp):
        timestamp_dt = _parse_timestamp(timestamp)
        if timestamp_dt is not None:
            return timestamp_dt.replace(minute=0, second=0, microsecond=0).isoformat()

        timestamp_str = _string_value(timestamp)
        if len(timestamp_str) >= 13:
            return timestamp_str[:13]
        return 'unknown'

    def _counter_dict(self, value):
        if not isinstance(value, dict):
            return {}
        return {
            _string_value(key): int(count or 0)
            for key, count in value.items()
            if _string_value(key)
        }


def default_event_candidate_dir(varlib_folder):
    return Path(varlib_folder).joinpath('event_candidates')


def default_event_timeline_dir(varlib_folder):
    return Path(varlib_folder).joinpath('event_timelines')


def default_event_classification_dir(varlib_folder):
    return Path(varlib_folder).joinpath('event_classifications')


def default_event_candidate_runtime_path(varlib_folder):
    return Path(varlib_folder).joinpath('event_candidate_runtime.json')


def build_event_candidate_from_metadata(frame_metadata, reasons=None, candidate_score=0.0, environment_context=None):
    """Build a shadow candidate from existing metadata only.

    This helper is intentionally inert unless explicit reasons are supplied.
    It does not classify the event and does not write anything by itself.
    """
    candidate_reasons = list(reasons or [])
    if not candidate_reasons:
        return None

    frame_id = frame_metadata.get('frame_id')
    timestamp = frame_metadata.get('timestamp')
    profile_id = frame_metadata.get('profile_id')
    camera_id = frame_metadata.get('camera_id')

    return EventCandidate(
        candidate_id='{0:s}:{1:s}:{2:s}'.format(str(profile_id or 'unknown'), str(camera_id or 'unknown'), str(frame_id or 'unknown')),
        camera_id=camera_id,
        profile_id=profile_id,
        frame_id=frame_id,
        timestamp_utc=timestamp,
        night_id=str(timestamp or '')[:10],
        candidate_score=candidate_score,
        reasons=candidate_reasons,
        source_metrics={
            'meter_value_raw': frame_metadata.get('meter_value_raw'),
            'meter_value_smoothed': frame_metadata.get('meter_value_smoothed'),
            'target_meter': frame_metadata.get('target_meter'),
            'meter_error': frame_metadata.get('meter_error'),
            'exposure_us': frame_metadata.get('exposure_us'),
            'gain': frame_metadata.get('gain'),
            'capture_status': frame_metadata.get('capture_status'),
        },
        quality_context={
            'quality_score': frame_metadata.get('quality_score'),
            'quality_flags': frame_metadata.get('quality_flags') or [],
        },
        environment_context=environment_context or {},
    )


def evaluate_candidate_triggers(current_metadata, previous_metadata=None, profile_config=None):
    """Evaluate metadata-only Event Candidate trigger rules.

    This function is deliberately pure/test-only: it does not persist, does not
    classify real-world event types, and is not called by capture/runtime code.
    """
    config = _trigger_config(profile_config)
    if not config.get('enabled', True):
        return []

    if not _has_candidate_identity(current_metadata):
        return []

    candidates = []
    for reason, score in _candidate_trigger_reasons(current_metadata, previous_metadata, config):
        candidate = build_event_candidate_from_metadata(
            current_metadata,
            reasons=[reason],
            candidate_score=score,
            environment_context=_environment_context_from_metadata(current_metadata),
        )
        if candidate is not None:
            candidate.candidate_id = '{0:s}:{1:s}'.format(candidate.candidate_id, reason)
            candidates.append(candidate)

    return candidates


def persist_event_candidates_shadow(
        current_metadata,
        previous_metadata=None,
        profile_config=None,
        candidate_dir=None,
        timeline_dir=None,
        diagnostics_path=None,
        trigger_evaluator=evaluate_candidate_triggers,
):
    """Evaluate and persist shadow event candidates without touching capture.

    Runtime integration intentionally defaults to disabled. Callers can invoke
    this after frame metadata persistence; failures are converted into a status
    payload so image saving/metadata generation can continue unchanged.
    """
    config = _trigger_config(profile_config, default_config=DEFAULT_RUNTIME_TRIGGER_CONFIG)
    max_candidates_per_hour = max(0, int(config.get('max_candidates_per_hour', DEFAULT_RUNTIME_TRIGGER_CONFIG['max_candidates_per_hour']) or 0))
    diagnostics = EventCandidateRuntimeDiagnostics(diagnostics_path) if diagnostics_path else None
    if not config.get('enabled', False):
        if diagnostics:
            diagnostics.record_disabled(max_candidates_per_hour)
        return {
            'enabled': False,
            'status': 'disabled',
            'candidate_count': 0,
            'timeline_count': 0,
        }

    if candidate_dir is None or timeline_dir is None:
        return {
            'enabled': True,
            'status': 'skipped',
            'reason': 'missing_persistence_path',
            'candidate_count': 0,
            'timeline_count': 0,
        }

    try:
        if diagnostics and max_candidates_per_hour > 0:
            current_hour_count = diagnostics.candidates_this_hour(current_metadata.get('timestamp'))
            if current_hour_count >= max_candidates_per_hour:
                diagnostics.record_rate_limited(True, max_candidates_per_hour)
                return {
                    'enabled': True,
                    'status': 'rate_limited',
                    'reason': 'max_candidates_per_hour_exceeded',
                    'candidate_count': 0,
                    'timeline_count': 0,
                }

        if diagnostics:
            diagnostics.record_evaluation(True, max_candidates_per_hour)

        candidates = trigger_evaluator(
            current_metadata,
            previous_metadata=previous_metadata,
            profile_config={'event_candidate_triggers': config},
        )
        if not candidates:
            return {
                'enabled': True,
                'status': 'no_candidates',
                'reason': 'no_trigger_rules_matched',
                'candidate_count': 0,
                'timeline_count': 0,
            }

        rate_limited = False
        if diagnostics and max_candidates_per_hour > 0:
            current_hour_count = diagnostics.candidates_this_hour(current_metadata.get('timestamp'))
            remaining_candidates = max_candidates_per_hour - current_hour_count
            if remaining_candidates <= 0:
                diagnostics.record_rate_limited(True, max_candidates_per_hour)
                return {
                    'enabled': True,
                    'status': 'rate_limited',
                    'reason': 'max_candidates_per_hour_exceeded',
                    'candidate_count': 0,
                    'timeline_count': 0,
                }
            if len(candidates) > remaining_candidates:
                candidates = candidates[:remaining_candidates]
                rate_limited = True
                diagnostics.record_rate_limited(True, max_candidates_per_hour)

        candidate_writer = EventCandidateWriter(candidate_dir)
        candidate_paths = [candidate_writer.write(candidate) for candidate in candidates]
        summary_date = _date_from_timestamp(current_metadata.get('timestamp'))
        all_candidates = EventCandidateAnalytics(candidate_dir).load_day(summary_date)
        segments = build_event_timeline_segments(all_candidates)
        timeline_path = EventTimelineWriter(timeline_dir).write_day(summary_date, segments)
        if diagnostics:
            diagnostics.record_generated(candidates, current_metadata.get('timestamp'), True, max_candidates_per_hour)

        return {
            'enabled': True,
            'status': 'rate_limited' if rate_limited else 'written',
            'reason': 'max_candidates_per_hour_exceeded' if rate_limited else '',
            'candidate_count': len(candidates),
            'timeline_count': len(segments),
            'candidate_path': str(candidate_paths[0]) if candidate_paths else '',
            'timeline_path': str(timeline_path),
        }
    except Exception as exc:
        if diagnostics:
            diagnostics.record_failure(True, max_candidates_per_hour)
        return {
            'enabled': True,
            'status': 'error',
            'reason': str(exc),
            'candidate_count': 0,
            'timeline_count': 0,
        }


def _trigger_config(profile_config, default_config=None):
    config = dict(default_config or DEFAULT_TRIGGER_CONFIG)
    if isinstance(profile_config, dict):
        event_config = profile_config.get('event_candidate_triggers')
        if isinstance(event_config, dict):
            config.update(event_config)
        config.update({
            key: value for key, value in profile_config.items()
            if key in config
        })
    return config


def _has_candidate_identity(metadata):
    if not isinstance(metadata, dict):
        return False
    return all(_string_value(metadata.get(key)) for key in ('frame_id', 'timestamp', 'camera_id', 'profile_id'))


def _candidate_trigger_reasons(current_metadata, previous_metadata, config):
    reasons = []

    brightness_spike = _brightness_spike_score(current_metadata, previous_metadata, config)
    if brightness_spike is not None:
        reasons.append(('brightness_spike', brightness_spike))

    quality_drop = _quality_drop_score(current_metadata, previous_metadata, config)
    if quality_drop is not None:
        reasons.append(('quality_drop', quality_drop))

    if _condensation_onset(current_metadata, previous_metadata):
        reasons.append(('condensation_onset', 35.0))

    if _sky_condition_transition(current_metadata, previous_metadata):
        reasons.append(('sky_condition_transition', 30.0))

    return reasons


def _brightness_spike_score(current_metadata, previous_metadata, config):
    if not isinstance(previous_metadata, dict):
        return None

    current_meter = _optional_float(current_metadata.get('meter_value_smoothed'))
    previous_meter = _optional_float(previous_metadata.get('meter_value_smoothed'))
    target_meter = _optional_float(current_metadata.get('target_meter'))
    if current_meter is None or previous_meter is None or target_meter is None:
        return None

    meter_delta = current_meter - previous_meter
    over_target = current_meter - target_meter
    if meter_delta < float(config.get('brightness_spike_meter_delta', 60.0)):
        return None
    if over_target < float(config.get('brightness_spike_over_target', 50.0)):
        return None

    return min(100.0, max(0.0, (meter_delta + over_target) / 2.0))


def _quality_drop_score(current_metadata, previous_metadata, config):
    current_quality = _optional_float(current_metadata.get('quality_score'))
    if current_quality is None:
        return None

    quality_threshold = float(config.get('quality_drop_score', 45.0))
    if current_quality <= quality_threshold:
        return min(100.0, quality_threshold - current_quality + 20.0)

    if isinstance(previous_metadata, dict):
        previous_quality = _optional_float(previous_metadata.get('quality_score'))
        if previous_quality is not None:
            quality_delta = previous_quality - current_quality
            if quality_delta >= float(config.get('quality_drop_delta', 25.0)):
                return min(100.0, quality_delta)

    return None


def _condensation_onset(current_metadata, previous_metadata):
    if not isinstance(previous_metadata, dict):
        return False
    return (
        _metadata_bool(current_metadata, 'possible_condensation')
        and not _metadata_bool(previous_metadata, 'possible_condensation')
    )


def _sky_condition_transition(current_metadata, previous_metadata):
    if not isinstance(previous_metadata, dict):
        return False

    previous_sky = _condition_rank(_metadata_value(previous_metadata, 'sky_condition'), ('excellent', 'good', 'usable', 'poor', 'unusable'))
    current_sky = _condition_rank(_metadata_value(current_metadata, 'sky_condition'), ('excellent', 'good', 'usable', 'poor', 'unusable'))
    if previous_sky is not None and current_sky is not None and current_sky - previous_sky >= 2:
        return True

    previous_cloud = _condition_rank(_metadata_value(previous_metadata, 'cloud_condition'), ('clear', 'mostly_clear', 'partly_cloudy', 'cloudy', 'overcast'))
    current_cloud = _condition_rank(_metadata_value(current_metadata, 'cloud_condition'), ('clear', 'mostly_clear', 'partly_cloudy', 'cloudy', 'overcast'))
    return previous_cloud is not None and current_cloud is not None and current_cloud - previous_cloud >= 2


def _condition_rank(value, ordered_values):
    value_str = _string_value(value)
    if value_str not in ordered_values:
        return None
    return ordered_values.index(value_str)


def _metadata_bool(metadata, key):
    value = _metadata_value(metadata, key)
    if isinstance(value, bool):
        return value
    return _string_value(value).lower() in ('1', 'true', 'yes', 'on')


def _metadata_value(metadata, key):
    if not isinstance(metadata, dict):
        return None
    if key in metadata:
        return metadata.get(key)
    environment_context = metadata.get('environment_context')
    if isinstance(environment_context, dict):
        return environment_context.get(key)
    return None


def _environment_context_from_metadata(metadata):
    return {
        'sky_condition': _metadata_value(metadata, 'sky_condition'),
        'cloud_condition': _metadata_value(metadata, 'cloud_condition'),
        'sky_trend': _metadata_value(metadata, 'sky_trend'),
        'possible_condensation': _metadata_bool(metadata, 'possible_condensation'),
    }


def build_event_timeline_segments(candidates, max_gap_seconds=2.0):
    normalized_candidates = _normalize_candidates(candidates)
    segments = []
    current_group = []

    for timestamp, candidate in normalized_candidates:
        if not current_group:
            current_group = [(timestamp, candidate)]
            continue

        previous_timestamp, previous_candidate = current_group[-1]
        if _same_timeline_group(previous_candidate, candidate) and (timestamp - previous_timestamp).total_seconds() <= float(max_gap_seconds):
            current_group.append((timestamp, candidate))
            continue

        segments.append(_timeline_segment_from_group(current_group))
        current_group = [(timestamp, candidate)]

    if current_group:
        segments.append(_timeline_segment_from_group(current_group))

    return segments


def _normalize_candidates(candidates):
    rows = []
    for candidate in candidates or []:
        candidate_dict = candidate.to_dict() if hasattr(candidate, 'to_dict') else dict(candidate)
        timestamp = _parse_timestamp(candidate_dict.get('timestamp_utc'))
        if timestamp is None:
            continue
        rows.append((timestamp, candidate_dict))

    return sorted(rows, key=lambda row: (
        _string_value(row[1].get('night_id')),
        _string_value(row[1].get('camera_id')),
        _string_value(row[1].get('profile_id')),
        row[0],
    ))


def _same_timeline_group(left, right):
    return (
        _string_value(left.get('camera_id')) == _string_value(right.get('camera_id'))
        and _string_value(left.get('profile_id')) == _string_value(right.get('profile_id'))
        and _string_value(left.get('night_id')) == _string_value(right.get('night_id'))
    )


def _timeline_segment_from_group(group):
    start_timestamp, first_candidate = group[0]
    end_timestamp, last_candidate = group[-1]
    candidates = [candidate for timestamp, candidate in group]
    scores = [
        score for score in (
            _optional_float(candidate.get('candidate_score'))
            for candidate in candidates
        )
        if score is not None
    ]
    candidate_ids = [_string_value(candidate.get('candidate_id')) for candidate in candidates if _string_value(candidate.get('candidate_id'))]
    reasons = sorted(set(
        _string_value(reason)
        for candidate in candidates
        for reason in (candidate.get('reasons') if isinstance(candidate.get('reasons'), list) else [])
        if _string_value(reason)
    ))
    timeline_id = '{0:s}:{1:s}:{2:s}:{3:s}:{4:s}'.format(
        _string_value(first_candidate.get('profile_id')) or 'unknown',
        _string_value(first_candidate.get('camera_id')) or 'unknown',
        _string_value(first_candidate.get('night_id')) or 'unknown',
        _string_value(first_candidate.get('candidate_id')) or 'start',
        _string_value(last_candidate.get('candidate_id')) or 'end',
    )

    return EventTimelineSegment(
        timeline_id=timeline_id,
        camera_id=first_candidate.get('camera_id'),
        profile_id=first_candidate.get('profile_id'),
        night_id=first_candidate.get('night_id'),
        start_timestamp_utc=first_candidate.get('timestamp_utc'),
        end_timestamp_utc=last_candidate.get('timestamp_utc'),
        duration_seconds=(end_timestamp - start_timestamp).total_seconds(),
        candidate_count=len(candidates),
        candidate_ids=candidate_ids,
        reasons=reasons,
        max_candidate_score=max(scores) if scores else 0.0,
        average_candidate_score=_average(scores) or 0.0,
        quality_context_summary=_quality_context_summary(candidates),
        environment_context_summary=_environment_context_summary(candidates),
    )


def _quality_context_summary(candidates):
    scores = [
        score for score in (
            _optional_float((candidate.get('quality_context') or {}).get('quality_score'))
            for candidate in candidates
        )
        if score is not None
    ]
    flags = Counter()
    for candidate in candidates:
        quality_flags = (candidate.get('quality_context') or {}).get('quality_flags')
        if isinstance(quality_flags, list):
            flags.update(_string_value(flag) for flag in quality_flags if _string_value(flag))

    return {
        'average_quality_score': _average(scores),
        'min_quality_score': min(scores) if scores else None,
        'max_quality_score': max(scores) if scores else None,
        'quality_flags': dict(flags),
    }


def _environment_context_summary(candidates):
    counters = {
        'sky_condition': Counter(),
        'cloud_condition': Counter(),
        'sky_trend': Counter(),
    }
    possible_condensation = False
    for candidate in candidates:
        environment_context = candidate.get('environment_context') or {}
        for key, counter in counters.items():
            value = _string_value(environment_context.get(key))
            if value:
                counter.update([value])
        possible_condensation = possible_condensation or bool(environment_context.get('possible_condensation'))

    return {
        'sky_condition': dict(counters['sky_condition']),
        'cloud_condition': dict(counters['cloud_condition']),
        'sky_trend': dict(counters['sky_trend']),
        'possible_condensation': possible_condensation,
    }


def _parse_timestamp(timestamp):
    timestamp_str = str(timestamp or '').strip()
    if not timestamp_str:
        return None
    if timestamp_str.endswith('Z'):
        timestamp_str = '{0:s}+00:00'.format(timestamp_str[:-1])

    try:
        return datetime.fromisoformat(timestamp_str)
    except ValueError:
        return None


def _date_from_timestamp(timestamp):
    timestamp_dt = _parse_timestamp(timestamp)
    if timestamp_dt is not None:
        return timestamp_dt.date().isoformat()

    timestamp_str = str(timestamp or '').strip()
    if len(timestamp_str) >= 10:
        return datetime.fromisoformat(timestamp_str[:10]).date().isoformat()
    raise ValueError('Invalid timestamp for event timeline: {0:s}'.format(timestamp_str))


def _average(values):
    if not values:
        return None
    return sum(values) / len(values)


def _optional_float(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _string_value(value):
    if value is None:
        return ''
    return str(value)
