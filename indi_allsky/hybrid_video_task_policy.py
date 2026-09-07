"""Multicamera dispatch policy for verified video-worker responsibilities."""
CAMERA_ACTIONS = frozenset({
    'generateVideo', 'generateKeogramStarTrails', 'generatePanoramaVideo',
    'updateAuroraData', 'updateSmokeData',
})
GLOBAL_ACTIONS = frozenset({'updateSatelliteTleData', 'backupDatabase', 'systemHealthCheck'})


def multicamera_rejection(action, camera_id):
    if action not in CAMERA_ACTIONS | GLOBAL_ACTIONS:
        return 'Action is not supported by multicamera dispatch'
    if action in CAMERA_ACTIONS and not camera_id:
        return 'Camera-scoped action requires camera_id'
    return None
