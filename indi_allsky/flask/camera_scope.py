"""Resolve explicit camera/profile navigation before template context is built."""
from flask import abort, request, session


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
