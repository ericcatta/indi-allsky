import json
from collections import Counter
from dataclasses import asdict
from dataclasses import dataclass
from dataclasses import field
from datetime import datetime
from pathlib import Path


EVENT_CANDIDATE_SCHEMA_VERSION = 'event_candidate_v0'
EVENT_CANDIDATE_TYPE = 'unclassified'


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
                rows.append(json.loads(line))

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


def default_event_candidate_dir(varlib_folder):
    return Path(varlib_folder).joinpath('event_candidates')


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
