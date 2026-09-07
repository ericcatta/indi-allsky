"""Exposure budget for cameras sharing a start-to-start capture interval."""
import math

# rpicam-still currently needs about 5.4 s beyond its requested exposure on
# the IMX708. Leave room for readout, process startup and capture polling.
CAPTURE_OVERHEAD_SECONDS = 6.0


def exposure_budget(period, configured_maximum, hardware_minimum, hardware_maximum):
    values = tuple(float(x) for x in (period, configured_maximum, hardware_minimum, hardware_maximum))
    if not all(math.isfinite(x) for x in values):
        raise ValueError('Capture cadence limits must be finite')
    period, configured_maximum, hardware_minimum, hardware_maximum = values
    maximum = min(configured_maximum, hardware_maximum, period - CAPTURE_OVERHEAD_SECONDS)
    if hardware_minimum < 0 or maximum <= 0 or maximum < hardware_minimum:
        raise ValueError('Capture interval is too short for the camera exposure and readout budget')
    return maximum


def validate_capture_cadence(config):
    """Reject impossible shared intervals before saving a config revision."""
    if not config.get('MULTI_CAMERA_CAPTURE_ENABLE', False):
        return
    from .capture_profiles import derive_capture_profiles

    for profile in derive_capture_profiles(config):
        for key, minimum in (('EXPOSURE_PERIOD', profile.exposure_min),
                             ('EXPOSURE_PERIOD_DAY', profile.exposure_min_day)):
            try:
                exposure_budget(config.get(key, 15.0), profile.exposure_max,
                                minimum, profile.exposure_max)
            except (TypeError, ValueError) as error:
                raise ValueError('{} / {}: {}'.format(profile.profile_id, key, error)) from error
