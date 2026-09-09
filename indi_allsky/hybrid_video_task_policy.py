"""Multicamera dispatch policy for verified video-worker responsibilities."""
CAMERA_ACTIONS = frozenset({
    'generateVideo', 'generateMiniVideo', 'generateKeogramStarTrails', 'generatePanoramaVideo',
    'updateAuroraData', 'updateSmokeData', 'uploadAllskyEndOfNight', 'expireData',
})
GLOBAL_ACTIONS = frozenset({'updateSatelliteTleData', 'backupDatabase', 'systemHealthCheck'})


def multicamera_rejection(action, camera_id):
    if action not in CAMERA_ACTIONS | GLOBAL_ACTIONS:
        return 'Action is not supported by multicamera dispatch'
    if action in CAMERA_ACTIONS and not camera_id:
        return 'Camera-scoped action requires camera_id'
    return None


def video_task_profile_id(config, camera_id, global_profile_id, *, camera_name=None):
    """Associate camera work with an explicit ID or exact local camera identity.

    Historical/unbound cameras remain usable, with neutral metadata rather than
    being mislabeled as the first active camera. Global work retains its route.
    """
    if not camera_id:
        return global_profile_id
    try:
        target = int(camera_id)
    except (TypeError, ValueError):
        return 'default'
    multi = config.get('MULTI_CAMERA', {})
    profiles = multi.get('profiles', []) if isinstance(multi, dict) else []
    matches = []
    named_matches = []
    for profile in profiles if isinstance(profiles, list) else []:
        if not isinstance(profile, dict):
            continue
        bound = 0
        for key in ('db_camera_id', 'camera_db_id', 'camera_id'):
            try:
                bound = int(profile.get(key) or 0)
            except (TypeError, ValueError):
                continue
            if bound > 0:
                if bound == target:
                    matches.append(profile.get('profile_id'))
                break
        if bound <= 0 and isinstance(camera_name, str) and camera_name:
            indi = profile.get('indi')
            names = [profile.get('camera_name'), profile.get('indi_camera_name')]
            if isinstance(indi, dict):
                names.append(indi.get('camera_name'))
            interface = profile.get('camera_interface')
            if isinstance(interface, str) and interface.startswith('libcamera'):
                names.append(interface)
            if camera_name in names:
                named_matches.append(profile.get('profile_id'))
    if not matches:
        matches = named_matches
    if len(matches) == 1 and isinstance(matches[0], str) and matches[0].strip():
        return matches[0]
    return 'default'
