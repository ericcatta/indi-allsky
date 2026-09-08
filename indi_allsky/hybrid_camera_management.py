"""Hybrid camera-mode decisions, shared capture output policy and save plans."""
from copy import deepcopy
from dataclasses import replace


DEFERRED_CAPTURE_OUTPUTS = (
    'mini_timelapse', 'realtime_keogram', 'longterm_keogram',
    'panorama', 'panorama_loop', 'extra_uploads',
)


def multicamera_capture_outputs(outputs):
    """Preserve the existing live-capture restrictions, including unknown keys."""
    result = dict(outputs)
    for key in DEFERRED_CAPTURE_OUTPUTS:
        result[key] = False
    result['images'] = True
    return result


def camera_mode_context(config):
    from .capture_profiles import derive_capture_profiles, build_profile_config
    enabled = bool(config.get('MULTI_CAMERA_CAPTURE_ENABLE', False))
    result = dict(enabled=enabled, status_label='Enabled in saved configuration' if enabled else 'Disabled in saved configuration',
                  mode_label='Independent camera profiles', profiles=[], enabled_count=0,
                  enable_allowed=False, enable_block_reason='At least two enabled camera profiles are required.')
    multi = config.get('MULTI_CAMERA') or {}
    raw = multi.get('profiles') if isinstance(multi, dict) else None
    if raw is None:
        return result
    if not isinstance(raw, list) or any(not isinstance(p, dict) for p in raw):
        result['enable_block_reason'] = 'Camera profiles are invalid. Correct them in Camera Settings before enabling multi-camera capture.'
        return result
    ids = [str(p.get('profile_id') or 'profile-' + str(index + 1)) for index, p in enumerate(raw)]
    if any(not i.strip() for i in ids) or len(set(ids)) != len(ids):
        result['enable_block_reason'] = 'Camera profiles must have unique, non-empty IDs.'
        return result
    try:
        proposed = dict(config, MULTI_CAMERA_CAPTURE_ENABLE=True)
        derived = derive_capture_profiles(proposed) if raw else []
        from .capture_cadence import validate_capture_cadence
        validate_capture_cadence(proposed)
    except (TypeError, ValueError, AttributeError, KeyError):
        result['enable_block_reason'] = 'Camera settings or shared intervals are invalid. Correct them in Camera Settings before enabling multi-camera capture.'
        return result
    for source, profile in zip(raw, derived):
        row = deepcopy(source)
        row.update(profile_id=profile.profile_id, enabled=profile.enabled, primary=profile.primary,
                   camera_interface=profile.camera_interface, capture_outputs=multicamera_capture_outputs(profile.outputs))
        effective = build_profile_config(proposed, replace(profile, outputs=row['capture_outputs']))
        row['generated_capture_enabled'] = bool(effective.get('TIMELAPSE_ENABLE', True))
        result['profiles'].append(row)
    result['enabled_count'] = sum(p['enabled'] for p in result['profiles'])
    result['enable_allowed'] = result['enabled_count'] >= 2
    if result['enable_allowed']:
        result['enable_block_reason'] = ''
    return result


def plan_camera_mode(config, enabled):
    if enabled:
        context = camera_mode_context(config)
        if not context['enable_allowed']:
            raise ValueError(context['enable_block_reason'])
    result = deepcopy(config)
    result['MULTI_CAMERA_CAPTURE_ENABLE'] = bool(enabled)
    return result


def plan_camera_switch(config, *, camera_name, driver, supported_interfaces):
    if config.get('MULTI_CAMERA_CAPTURE_ENABLE'):
        raise ValueError('Disable multi-camera mode before selecting a single capture camera.')
    name, driver = str(camera_name or ''), str(driver or '')
    if driver in supported_interfaces:
        interface = driver
    elif name in supported_interfaces:
        interface = name
    elif driver in ('rpicam-still', 'libcamera-still'):
        raise ValueError('The libcamera sensor interface could not be identified. Select it in Camera Settings.')
    elif driver.startswith(('libcamera_', 'mqtt_')):
        raise ValueError('The camera interface is not supported by these settings. Select an available interface in Camera Settings.')
    else:
        interface = 'indi'
    result = deepcopy(config)
    result['CAMERA_INTERFACE'] = interface
    if interface == 'indi':
        result['INDI_CAMERA_NAME'] = name
    return result
