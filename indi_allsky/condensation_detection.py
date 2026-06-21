from datetime import datetime
from datetime import timezone

from .sky_trend import classify_sky_trend

_NEGATIVE_FLAGS = frozenset((
    'controller_at_limit',
    'exposure_adjusting',
    'gain_adjusting',
    'meter_far_from_target',
    'meter_near_black',
    'meter_near_edge',
    'meter_off_target',
))

_CRITICAL_FLAGS = frozenset((
    'capture_error',
    'capture_not_processed',
    'exposure_invalid',
    'gain_invalid',
))


def detect_possible_condensation(metadata_series, profile_config=None):
    """Return True when metadata suggests possible lens/dome condensation.

    This diagnostic intentionally stays conservative: no image analysis, no
    weather fusion, no dew-heater control, and no runtime decisions.
    """
    frames = list(metadata_series or [])
    if len(frames) < 4:
        return False

    if _has_mixed_identity(frames):
        return False

    sorted_frames = _sort_frames(frames)
    if _has_invalid_capture(sorted_frames):
        return False

    quality_scores = [
        _optional_float(frame.get('quality_score'))
        for frame in sorted_frames
    ]
    quality_scores = [score for score in quality_scores if score is not None]
    if len(quality_scores) < 3:
        return False

    first_frames, last_frames = _split_frames(sorted_frames)
    first_quality = _quality_average(first_frames)
    last_quality = _quality_average(last_frames)
    if first_quality is None or last_quality is None:
        return False

    quality_drop = first_quality - last_quality
    if quality_drop < 20.0 or last_quality > 65.0:
        return False

    if classify_sky_trend(sorted_frames) != 'degrading':
        return False

    exposure_coherent = _metric_increasing_or_high(first_frames, last_frames, 'exposure_us')
    gain_coherent = _metric_increasing_or_high(first_frames, last_frames, 'gain')
    negative_flags_persistent = _negative_flags_persistent(last_frames)

    return exposure_coherent or gain_coherent or negative_flags_persistent


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


def _has_invalid_capture(frames):
    for frame in frames:
        status = _string_value(frame.get('capture_status')).lower()
        flags = _normalize_flags(frame.get('quality_flags'))
        if status and status != 'processed':
            return True
        if flags.intersection(_CRITICAL_FLAGS):
            return True
    return False


def _sort_frames(frames):
    indexed_frames = []
    for index, frame in enumerate(frames):
        indexed_frames.append((_parse_timestamp(frame.get('timestamp')), index, frame))
    if all(timestamp is not None for timestamp, index, frame in indexed_frames):
        return [frame for timestamp, index, frame in sorted(indexed_frames, key=lambda item: item[0])]
    return [frame for timestamp, index, frame in sorted(indexed_frames, key=lambda item: item[1])]


def _split_frames(frames):
    midpoint = max(1, int(len(frames) / 2))
    return frames[:midpoint], frames[midpoint:] or frames[midpoint - 1:]


def _quality_average(frames):
    values = [
        _optional_float(frame.get('quality_score'))
        for frame in frames
    ]
    values = [value for value in values if value is not None]
    return _average(values)


def _metric_increasing_or_high(first_frames, last_frames, key):
    first_values = [_optional_float(frame.get(key)) for frame in first_frames]
    last_values = [_optional_float(frame.get(key)) for frame in last_frames]
    first_values = [value for value in first_values if value is not None]
    last_values = [value for value in last_values if value is not None]
    first_average = _average(first_values)
    last_average = _average(last_values)
    if first_average is None or last_average is None:
        return False

    if first_average <= 0.0:
        return last_average > 0.0

    return last_average >= (first_average * 1.2)


def _negative_flags_persistent(frames):
    if not frames:
        return False

    negative_count = 0
    for frame in frames:
        flags = _normalize_flags(frame.get('quality_flags'))
        if flags.intersection(_NEGATIVE_FLAGS):
            negative_count += 1

    return negative_count >= max(2, int(len(frames) / 2))


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
