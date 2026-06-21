from datetime import datetime
from datetime import timezone

SKY_TREND_UNKNOWN = 'unknown'
SKY_TREND_IMPROVING = 'improving'
SKY_TREND_STABLE = 'stable'
SKY_TREND_DEGRADING = 'degrading'

SKY_TREND_VALUES = (
    SKY_TREND_UNKNOWN,
    SKY_TREND_IMPROVING,
    SKY_TREND_STABLE,
    SKY_TREND_DEGRADING,
)

_SKY_CONDITION_SCORES = {
    'excellent': 95.0,
    'good': 82.0,
    'usable': 65.0,
    'poor': 42.0,
    'unusable': 20.0,
}

_CLOUD_CONDITION_SCORES = {
    'clear': 95.0,
    'mostly_clear': 82.0,
    'partly_cloudy': 65.0,
    'cloudy': 42.0,
    'overcast': 20.0,
}

_CRITICAL_FLAGS = frozenset((
    'capture_error',
    'capture_not_processed',
    'exposure_invalid',
    'gain_invalid',
))


def classify_sky_trend(metadata_series, profile_config=None):
    """Classify sky trend from a single camera/profile metadata sequence.

    This is a read-only diagnostic classifier. It uses existing metadata only and
    returns ``unknown`` for mixed camera/profile sequences or insufficient data.
    """
    frames = list(metadata_series or [])
    if len(frames) < 2:
        return SKY_TREND_UNKNOWN

    if _has_mixed_identity(frames):
        return SKY_TREND_UNKNOWN

    scored_frames = []
    for index, frame in enumerate(frames):
        score = _frame_score(frame)
        if score is None:
            continue
        scored_frames.append((_parse_timestamp(frame.get('timestamp')), index, score))

    if len(scored_frames) < 2:
        return SKY_TREND_UNKNOWN

    scored_frames = _sort_scored_frames(scored_frames)
    scores = [score for timestamp, index, score in scored_frames]
    midpoint = max(1, int(len(scores) / 2))
    first_scores = scores[:midpoint]
    last_scores = scores[midpoint:] or scores[midpoint - 1:]

    first_average = _average(first_scores)
    last_average = _average(last_scores)
    if first_average is None or last_average is None:
        return SKY_TREND_UNKNOWN

    delta = last_average - first_average
    if delta >= 10.0:
        return SKY_TREND_IMPROVING
    if delta <= -10.0:
        return SKY_TREND_DEGRADING
    return SKY_TREND_STABLE


def _has_mixed_identity(frames):
    camera_ids = set()
    profile_ids = set()
    for frame in frames:
        camera_id = _string_value(frame.get('camera_id'))
        profile_id = _string_value(frame.get('profile_id'))
        if camera_id:
            camera_ids.add(camera_id)
        if profile_id:
            profile_ids.add(profile_id)

    return len(camera_ids) > 1 or len(profile_ids) > 1


def _frame_score(frame):
    flags = _normalize_flags(frame.get('quality_flags'))
    capture_status = _string_value(frame.get('capture_status')).lower()
    if capture_status and capture_status != 'processed':
        return 0.0
    if flags.intersection(_CRITICAL_FLAGS):
        return 0.0

    quality_score = _optional_float(frame.get('quality_score'))
    if quality_score is not None:
        return max(0.0, min(100.0, quality_score))

    sky_condition = frame.get('sky_condition')
    if isinstance(sky_condition, dict):
        sky_condition = sky_condition.get('sky_condition')
    sky_score = _SKY_CONDITION_SCORES.get(_string_value(sky_condition).lower())
    if sky_score is not None:
        return sky_score

    cloud_score = _CLOUD_CONDITION_SCORES.get(_string_value(frame.get('cloud_condition')).lower())
    if cloud_score is not None:
        return cloud_score

    return None


def _sort_scored_frames(scored_frames):
    if all(timestamp is not None for timestamp, index, score in scored_frames):
        return sorted(scored_frames, key=lambda item: item[0])
    return sorted(scored_frames, key=lambda item: item[1])


def _average(values):
    if not values:
        return None
    return sum(values) / len(values)


def _normalize_flags(flags):
    if isinstance(flags, list):
        return frozenset(_string_value(flag) for flag in flags if _string_value(flag))

    flag_value = _string_value(flags)
    if not flag_value:
        return frozenset()
    return frozenset((flag_value,))


def _optional_float(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _string_value(value):
    if value is None:
        return ''
    return str(value)


def _parse_timestamp(timestamp):
    timestamp_str = _string_value(timestamp).strip()
    if not timestamp_str:
        return None
    if timestamp_str.endswith('Z'):
        timestamp_str = '{0:s}+00:00'.format(timestamp_str[:-1])

    try:
        timestamp_dt = datetime.fromisoformat(timestamp_str)
    except ValueError:
        return None

    if timestamp_dt.tzinfo is None:
        return timestamp_dt.replace(tzinfo=timezone.utc)

    return timestamp_dt.astimezone(timezone.utc)
