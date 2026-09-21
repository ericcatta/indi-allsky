"""Resolve explicit camera/profile navigation before template context is built."""
from flask import abort, request, session


def settings_profile_camera_id(profile, cameras):
    """Use explicit DB bindings or one exact device identity, never list order."""
    for key in ('db_camera_id', 'camera_db_id', 'camera_id'):
        if key in profile:
            try:
                return int(profile[key])
            except (TypeError, ValueError):
                continue
    indi = profile.get('indi')
    names = {str(value).strip().casefold() for value in (
        profile.get('indi_camera_name'), profile.get('camera_name'),
        indi.get('camera_name') if isinstance(indi, dict) else None,
    ) if value}
    interface = str(profile.get('camera_interface') or '')
    if interface.startswith('libcamera_'):
        names.add(interface.casefold())
    matches = [camera.id for camera in cameras if names.intersection(
        str(getattr(camera, field, '') or '').strip().casefold()
        for field in ('name', 'name_alt1', 'name_alt2')
    )]
    return matches[0] if len(matches) == 1 else None


class CameraScopedTemplateMixin:
    def setupSession(self):
        if request.args.get('camera_id') or request.args.get('profile_id'):
            selected = self.get_selected_media_camera_filter()
            self.camera = self.getCameraById(selected['camera_id'])
            if self.camera.id != selected['camera_id']:
                abort(404, description='Camera is unavailable.')
            session['camera_id'] = self.camera.id
            return
        super().setupSession()
