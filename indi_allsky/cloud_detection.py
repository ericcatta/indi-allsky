from .sky_condition import compute_sky_condition_from_frame

CLOUD_CONDITION_UNKNOWN = 'unknown'
CLOUD_CONDITION_CLEAR = 'clear'
CLOUD_CONDITION_MOSTLY_CLEAR = 'mostly_clear'
CLOUD_CONDITION_PARTLY_CLOUDY = 'partly_cloudy'
CLOUD_CONDITION_CLOUDY = 'cloudy'
CLOUD_CONDITION_OVERCAST = 'overcast'

CLOUD_CONDITION_VALUES = (
    CLOUD_CONDITION_UNKNOWN,
    CLOUD_CONDITION_CLEAR,
    CLOUD_CONDITION_MOSTLY_CLEAR,
    CLOUD_CONDITION_PARTLY_CLOUDY,
    CLOUD_CONDITION_CLOUDY,
    CLOUD_CONDITION_OVERCAST,
)

_CRITICAL_FLAGS = frozenset((
    'capture_error',
    'capture_not_processed',
    'exposure_invalid',
    'gain_invalid',
))

_SEVERE_FLAGS = frozenset((
    'meter_far_from_target',
    'meter_near_black',
    'meter_saturated_high',
))


def classify_cloud_condition(metadata, profile_config=None):
    """Classify cloud condition from existing metadata only.

    This is a shadow/read-only foundation. It intentionally does not use image
    analysis, weather APIs, event detection, AI, or operational control state.
    """
    metadata = metadata or {}
    flags = _normalize_flags(metadata.get('quality_flags'))
    capture_status = _string_value(metadata.get('capture_status')).lower()

    if capture_status and capture_status != 'processed':
        return CLOUD_CONDITION_UNKNOWN

    if flags.intersection(_CRITICAL_FLAGS):
        return CLOUD_CONDITION_UNKNOWN

    sky_condition = _resolve_sky_condition(metadata)
    if sky_condition == 'unknown':
        return CLOUD_CONDITION_UNKNOWN

    quality_score = _optional_float(metadata.get('quality_score'))
    severe_flags = flags.intersection(_SEVERE_FLAGS)

    if sky_condition == 'excellent':
        if severe_flags:
            return CLOUD_CONDITION_PARTLY_CLOUDY
        return CLOUD_CONDITION_CLEAR

    if sky_condition == 'good':
        if severe_flags:
            return CLOUD_CONDITION_PARTLY_CLOUDY
        return CLOUD_CONDITION_MOSTLY_CLEAR

    if sky_condition == 'usable':
        return CLOUD_CONDITION_PARTLY_CLOUDY

    if sky_condition == 'poor':
        return CLOUD_CONDITION_CLOUDY

    if sky_condition == 'unusable':
        if quality_score is not None and quality_score <= 35.0:
            return CLOUD_CONDITION_OVERCAST
        if severe_flags:
            return CLOUD_CONDITION_OVERCAST
        return CLOUD_CONDITION_UNKNOWN

    return CLOUD_CONDITION_UNKNOWN


def _resolve_sky_condition(metadata):
    sky_condition = metadata.get('sky_condition')
    if isinstance(sky_condition, dict):
        return _string_value(sky_condition.get('sky_condition')).lower()

    sky_condition_value = _string_value(sky_condition).lower()
    if sky_condition_value:
        return sky_condition_value

    return compute_sky_condition_from_frame(metadata).get('sky_condition', CLOUD_CONDITION_UNKNOWN)


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
