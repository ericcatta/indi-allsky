def compute_frame_quality(
    *,
    meter_value,
    target_meter,
    exposure_us,
    gain,
    auto_exposure_action,
    auto_gain_action,
    decision_reason,
    capture_status,
    error_message='',
):
    """Simple metadata-only observational quality score.

    This intentionally avoids image analysis, AI, star detection, and quality
    inference beyond the already-persisted controller metadata.
    """
    flags = []
    score = 100.0

    capture_status_str = _string_value(capture_status).lower()
    if capture_status_str != 'processed':
        flags.append('capture_not_processed')
        score -= 60.0

    if _string_value(error_message):
        flags.append('capture_error')
        score -= 20.0

    meter = _optional_float(meter_value)
    target = _optional_float(target_meter)
    if meter is None:
        flags.append('meter_missing')
        score -= 25.0
    if target is None:
        flags.append('target_missing')
        score -= 15.0

    if meter is not None:
        if meter >= 245.0:
            flags.append('meter_saturated_high')
            score -= 35.0
        elif meter <= 5.0:
            flags.append('meter_near_black')
            score -= 35.0

    if meter is not None and target is not None:
        error_abs = abs(target - meter)
        if error_abs > 50.0:
            flags.append('meter_far_from_target')
            score -= 35.0
        elif error_abs > 20.0:
            flags.append('meter_off_target')
            score -= 20.0
        elif error_abs > 10.0:
            flags.append('meter_near_edge')
            score -= 8.0

    exposure = _optional_float(exposure_us)
    if exposure is None:
        flags.append('exposure_missing')
        score -= 10.0
    elif exposure <= 0:
        flags.append('exposure_invalid')
        score -= 20.0

    gain_value = _optional_float(gain)
    if gain_value is None:
        flags.append('gain_missing')
        score -= 10.0
    elif gain_value < 0:
        flags.append('gain_invalid')
        score -= 20.0

    exposure_action = _string_value(auto_exposure_action)
    gain_action = _string_value(auto_gain_action)
    reason = _string_value(decision_reason)
    if exposure_action.startswith(('increase_', 'decrease_')) and exposure_action != 'hold':
        flags.append('exposure_adjusting')
        score -= 5.0
    if gain_action.startswith(('increase_', 'decrease_')) and gain_action != 'hold':
        flags.append('gain_adjusting')
        score -= 5.0
    if 'already_max' in reason or 'already_min' in reason:
        flags.append('controller_at_limit')
        score -= 10.0

    flags = sorted(set(flags))
    if not flags:
        flags.append('nominal')

    return max(0.0, min(100.0, round(score, 1))), flags


def _optional_float(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _string_value(value):
    if value is None:
        return ''
    return str(value).strip()
