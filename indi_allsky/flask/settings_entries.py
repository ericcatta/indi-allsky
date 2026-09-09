"""Canonical destinations for former camera Settings preview URLs."""
from urllib.parse import urlencode
from flask import redirect, request, url_for

CAMERA_SETTINGS_ENTRIES = {
    'camera-profile': ('modern_admin_camera_profile_settings_view', 'driver-connection'),
    'camera-connection': ('modern_admin_camera_connection_settings_view', 'driver-connection'),
    'exposure-gain': ('modern_admin_exposure_gain_settings_view', 'acquisition'),
    'auto-exposure-gain': ('modern_admin_auto_exposure_gain_settings_view', 'acquisition'),
    'hybrid-awb': ('modern_admin_hybrid_awb_settings_view', 'hybrid-controller'),
}


def register_camera_settings_entries(blueprint):
    for path, (endpoint, anchor) in CAMERA_SETTINGS_ENTRIES.items():
        def navigate(anchor=anchor):
            query = urlencode(list(request.args.items(multi=True)))
            target = url_for('indi_allsky.modern_admin_camera_settings_view')
            return redirect(target + ('?' + query if query else '') + '#' + anchor)
        blueprint.add_url_rule('/modern-admin/settings/' + path,
                               endpoint=endpoint, view_func=navigate, methods=['GET'])
