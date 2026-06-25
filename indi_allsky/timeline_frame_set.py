import json
import hashlib
from dataclasses import asdict
from dataclasses import dataclass
from datetime import datetime
from datetime import timezone
from pathlib import Path

from .scientific_frame import SCIENTIFIC_FRAME_SEQUENCE_METADATA_VERSION
from .scientific_frame import ScientificFrameSequence
from .scientific_frame import build_scientific_frame_sequence
from .scientific_frame_provider import ScientificFrameProvider


TIMELINE_FRAME_SET_SCHEMA_VERSION = 'timeline_frame_set_v1'


@dataclass(frozen=True)
class TimelineFrameSet:
    """Read-only bridge from an event timeline to scientific frame sequence.

    TimelineFrameSet preserves event provenance and missing-data diagnostics
    while keeping detectors independent from EventTimeline internals and raw
    metadata files.  It never reads image files, queries databases, writes data,
    or promotes display images to scientific source/detector input.
    """

    timeline_id: str
    camera_id: int
    profile_id: str
    sequence: ScientificFrameSequence
    candidate_ids: list
    resolved_candidate_ids: list
    missing_candidate_ids: list
    missing_frame_ids: list
    missing_frame_metadata_ids: list
    created_at: str = None
    schema_version: str = TIMELINE_FRAME_SET_SCHEMA_VERSION

    def __post_init__(self):
        object.__setattr__(self, 'schema_version', TIMELINE_FRAME_SET_SCHEMA_VERSION)
        if self.created_at is None:
            object.__setattr__(self, 'created_at', _utc_now())

    def to_dict(self):
        data = asdict(self)
        if hasattr(self.sequence, 'to_dict'):
            data['sequence'] = self.sequence.to_dict()
        return data


def build_timeline_frame_set(
        timeline,
        candidate_path,
        frame_metadata_path=None,
        frame_metadata_dir=None,
):
    timeline_dict = _as_dict(timeline)
    timeline_copy = dict(timeline_dict)
    timeline_id = _string_value(timeline_copy.get('timeline_id'))
    camera_id = timeline_copy.get('camera_id')
    profile_id = timeline_copy.get('profile_id')
    candidate_ids = [_string_value(candidate_id) for candidate_id in timeline_copy.get('candidate_ids') or []]
    candidate_ids = [candidate_id for candidate_id in candidate_ids if candidate_id]

    candidates_by_id = {
        _string_value(candidate.get('candidate_id')): candidate
        for candidate in _load_jsonl(candidate_path)
        if _string_value(candidate.get('candidate_id'))
    }

    resolved_candidates = []
    resolved_candidate_ids = []
    missing_candidate_ids = []
    missing_frame_ids = []

    for candidate_id in candidate_ids:
        candidate = candidates_by_id.get(candidate_id)
        if not candidate:
            missing_candidate_ids.append(candidate_id)
            continue

        frame_id = candidate.get('frame_id')
        if frame_id is None:
            missing_frame_ids.append(candidate_id)
            continue

        resolved_candidates.append(candidate)
        resolved_candidate_ids.append(candidate_id)

    frame_metadata_rows = _load_frame_metadata_rows(
        timeline_copy,
        frame_metadata_path=frame_metadata_path,
        frame_metadata_dir=frame_metadata_dir,
    )
    frame_metadata_by_key = {
        _frame_metadata_key(row): row
        for row in frame_metadata_rows
        if _frame_metadata_key(row) is not None
    }

    resolved_metadata = []
    missing_frame_metadata_ids = []
    for candidate in resolved_candidates:
        key = _candidate_frame_metadata_key(candidate)
        metadata = frame_metadata_by_key.get(key)
        if metadata:
            resolved_metadata.append(metadata)
        else:
            missing_frame_metadata_ids.append(_string_value(candidate.get('frame_id')))

    provider = ScientificFrameProvider()
    scientific_frames = provider.from_frame_metadata_list(resolved_metadata)

    if scientific_frames:
        sequence = build_scientific_frame_sequence(scientific_frames)
    else:
        sequence = _empty_sequence(timeline_copy)

    return TimelineFrameSet(
        timeline_id=timeline_id,
        camera_id=camera_id,
        profile_id=profile_id,
        sequence=sequence,
        candidate_ids=candidate_ids,
        resolved_candidate_ids=resolved_candidate_ids,
        missing_candidate_ids=missing_candidate_ids,
        missing_frame_ids=missing_frame_ids,
        missing_frame_metadata_ids=missing_frame_metadata_ids,
    )


def _load_frame_metadata_rows(timeline, frame_metadata_path=None, frame_metadata_dir=None):
    if frame_metadata_path:
        return _load_jsonl(frame_metadata_path)

    if frame_metadata_dir:
        start_timestamp = timeline.get('start_timestamp_utc') or timeline.get('timestamp_utc')
        summary_date = _date_from_timestamp(start_timestamp)
        if summary_date:
            return _load_jsonl(Path(frame_metadata_dir).joinpath('{0:s}.jsonl'.format(summary_date)))

    return []


def _load_jsonl(path):
    if not path:
        return []

    path_p = Path(path)
    if not path_p.exists():
        return []

    rows = []
    with path_p.open('r', encoding='utf-8') as f_jsonl:
        for line in f_jsonl:
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return rows


def _frame_metadata_key(metadata):
    frame_id = metadata.get('frame_id')
    camera_id = metadata.get('camera_id')
    profile_id = metadata.get('profile_id')
    if frame_id is None or camera_id is None or profile_id is None:
        return None
    return (_string_value(frame_id), _string_value(camera_id), _string_value(profile_id))


def _candidate_frame_metadata_key(candidate):
    return (
        _string_value(candidate.get('frame_id')),
        _string_value(candidate.get('camera_id')),
        _string_value(candidate.get('profile_id')),
    )


def _empty_sequence(timeline):
    timeline_id = _string_value(timeline.get('timeline_id'))
    camera_id = timeline.get('camera_id')
    profile_id = timeline.get('profile_id')
    start_timestamp = timeline.get('start_timestamp_utc')
    end_timestamp = timeline.get('end_timestamp_utc') or start_timestamp
    camera_uuid = timeline.get('camera_uuid')

    identity = '|'.join((
        'empty',
        timeline_id,
        _string_value(camera_id),
        _string_value(profile_id),
        _string_value(start_timestamp),
        _string_value(end_timestamp),
    ))
    digest = hashlib.sha256(identity.encode('utf-8')).hexdigest()[:24]

    return ScientificFrameSequence(
        sequence_id='scientific-sequence-{0:s}'.format(digest),
        camera_id=camera_id,
        camera_uuid=camera_uuid,
        profile_id=profile_id,
        start_timestamp_utc=start_timestamp,
        end_timestamp_utc=end_timestamp,
        frames=(),
        frame_count=0,
        missing_source_count=0,
        metadata_version=SCIENTIFIC_FRAME_SEQUENCE_METADATA_VERSION,
    )


def _date_from_timestamp(timestamp):
    timestamp_str = _string_value(timestamp)
    if not timestamp_str:
        return None
    if timestamp_str.endswith('Z'):
        timestamp_str = '{0:s}+00:00'.format(timestamp_str[:-1])

    try:
        return datetime.fromisoformat(timestamp_str).date().isoformat()
    except ValueError:
        if len(timestamp_str) >= 10:
            return timestamp_str[:10]
        return None


def _as_dict(value):
    if isinstance(value, dict):
        return dict(value)

    to_dict = getattr(value, 'to_dict', None)
    if callable(to_dict):
        return dict(to_dict())

    return dict(getattr(value, '__dict__', {}))


def _string_value(value):
    if value is None:
        return ''
    return str(value)


def _utc_now():
    return datetime.now(tz=timezone.utc).isoformat()
