SKY_CONDITION_UNKNOWN = 'unknown'
SKY_CONDITION_EXCELLENT = 'excellent'
SKY_CONDITION_GOOD = 'good'
SKY_CONDITION_USABLE = 'usable'
SKY_CONDITION_POOR = 'poor'
SKY_CONDITION_UNUSABLE = 'unusable'

SKY_CONDITION_VALUES = (
    SKY_CONDITION_UNKNOWN,
    SKY_CONDITION_EXCELLENT,
    SKY_CONDITION_GOOD,
    SKY_CONDITION_USABLE,
    SKY_CONDITION_POOR,
    SKY_CONDITION_UNUSABLE,
)

_CONDITION_RANKS = {
    SKY_CONDITION_EXCELLENT: 5,
    SKY_CONDITION_GOOD: 4,
    SKY_CONDITION_USABLE: 3,
    SKY_CONDITION_POOR: 2,
    SKY_CONDITION_UNUSABLE: 1,
    SKY_CONDITION_UNKNOWN: 0,
}

_RANK_CONDITIONS = {
    rank: condition
    for condition, rank in _CONDITION_RANKS.items()
}

_CRITICAL_FLAGS = frozenset((
    'capture_error',
    'capture_not_processed',
    'exposure_invalid',
    'gain_invalid',
))

_SEVERE_FLAGS = frozenset((
    'meter_saturated_high',
    'meter_near_black',
    'meter_far_from_target',
))

_WARNING_FLAGS = frozenset((
    'controller_at_limit',
    'exposure_adjusting',
    'gain_adjusting',
    'meter_near_edge',
    'meter_off_target',
))


def compute_sky_condition(
        quality_score=None,
        quality_flags=None,
        capture_status=None,
        meter_value=None,
        target_meter=None,
        profile_id=None,
        camera_id=None):
    """Classify current sky condition from existing metadata only.

    This foundation intentionally avoids cloud, dew, trend, image-analysis, and
    operational control logic. It returns ``unknown`` when metadata is too thin.
    """
    flags = _normalize_flags(quality_flags)
    status = _string_value(capture_status).lower()
    quality = _optional_float(quality_score)
    meter = _optional_float(meter_value)
    target = _optional_float(target_meter)

    if status and status != 'processed':
        return _result(
            SKY_CONDITION_UNUSABLE,
            'capture_status_not_processed',
            profile_id,
            camera_id,
            flags,
        )

    if flags.intersection(_CRITICAL_FLAGS):
        return _result(
            SKY_CONDITION_UNUSABLE,
            'critical_quality_flag',
            profile_id,
            camera_id,
            flags,
        )

    if quality is None:
        if meter is None or target is None:
            return _result(
                SKY_CONDITION_UNKNOWN,
                'insufficient_metadata',
                profile_id,
                camera_id,
                flags,
            )
        quality = _quality_from_meter(meter, target)

    condition = _condition_from_quality(quality)
    reason = 'quality_score'

    if flags.intersection(_SEVERE_FLAGS):
        condition = _cap_condition(condition, SKY_CONDITION_POOR)
        reason = 'severe_quality_flag'
    elif flags.intersection(_WARNING_FLAGS):
        condition = _cap_condition(condition, SKY_CONDITION_USABLE)
        reason = 'warning_quality_flag'

    return _result(condition, reason, profile_id, camera_id, flags)


def compute_sky_condition_from_frame(frame):
    frame = frame or {}
    return compute_sky_condition(
        quality_score=frame.get('quality_score'),
        quality_flags=frame.get('quality_flags'),
        capture_status=frame.get('capture_status'),
        meter_value=frame.get('meter_value_smoothed'),
        target_meter=frame.get('target_meter'),
        profile_id=frame.get('profile_id'),
        camera_id=frame.get('camera_id'),
    )


def _condition_from_quality(quality_score):
    if quality_score >= 90.0:
        return SKY_CONDITION_EXCELLENT
    if quality_score >= 75.0:
        return SKY_CONDITION_GOOD
    if quality_score >= 55.0:
        return SKY_CONDITION_USABLE
    if quality_score >= 35.0:
        return SKY_CONDITION_POOR
    return SKY_CONDITION_UNUSABLE


def _quality_from_meter(meter_value, target_meter):
    return max(0.0, min(100.0, 100.0 - abs(target_meter - meter_value)))


def _cap_condition(condition, maximum_condition):
    condition_rank = _CONDITION_RANKS.get(condition, 0)
    maximum_rank = _CONDITION_RANKS.get(maximum_condition, 0)
    return _RANK_CONDITIONS.get(min(condition_rank, maximum_rank), SKY_CONDITION_UNKNOWN)


def _result(condition, reason, profile_id, camera_id, flags):
    return {
        'sky_condition': condition,
        'reason': reason,
        'profile_id': _string_value(profile_id),
        'camera_id': _string_value(camera_id),
        'quality_flags': sorted(flags),
    }


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
