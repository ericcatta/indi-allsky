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

    def _timeline_path_for(self, segment):
        return self.timeline_dir.joinpath('{0:s}.jsonl'.format(_date_from_timestamp(segment.start_timestamp_utc)))


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


def default_event_candidate_dir(varlib_folder):
    return Path(varlib_folder).joinpath('event_candidates')


def default_event_timeline_dir(varlib_folder):
    return Path(varlib_folder).joinpath('event_timelines')


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
