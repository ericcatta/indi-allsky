"""Retain bookmarked UI entrances when the optional Classic frontend is absent.

Only navigation URLs belong here. Public media, JSON/AJAX, Sync and Action APIs
keep their independent handlers and are never redirected by this registry.
"""
from urllib.parse import urlencode
from flask import redirect, request, url_for

# Fixed destinations are endpoint names, never supplied by the request.
NAVIGATION_GROUPS = {
    'modern_admin_now_view': ('/', '/index_canvas', '/index_img'),
    'modern_admin_media_panorama_view': ('/panorama', '/panorama_canvas', '/panorama_img'),
    'modern_admin_media_raw_images_view': ('/raw', '/raw_canvas', '/raw_img'),
    'modern_admin_loop_view': ('/loop', '/loop_canvas', '/loop_img'),
    'modern_admin_media_panorama_loop_view': ('/looppanorama', '/looppanorama_canvas', '/looppanorama_img'),
    'modern_admin_raw_loop_view': ('/loopraw', '/loopraw_canvas', '/loopraw_img'),
    'modern_admin_sensor_panel_view': ('/sensor_panel',),
    'modern_admin_realtime_keogram_view': ('/realtime_keogram',),
    'modern_admin_sqm_view': ('/sqm',),
    'modern_admin_charts_view': ('/charts',),
    'modern_admin_media_images_view': ('/imageviewer',),
    'modern_admin_fits_view': ('/fitsimageviewer',),
    'modern_admin_media_gallery_view': ('/gallery',),
    'modern_admin_media_timelapses_view': ('/videoviewer',),
    'modern_admin_media_mini_timelapses_view': ('/minivideoviewer',),
    'modern_admin_generate_view': ('/generate',),
    'modern_admin_mini_generate_view': ('/minigenerate',),
    'modern_admin_full_settings_view': ('/config',),
    'modern_admin_config_history_view': ('/config/list',),
    'modern_admin_config_restore_view': ('/config/restore',),
    'modern_admin_system_info_view': ('/system',),
    'modern_admin_focus_view': ('/focus',),
    'modern_admin_manual_gpio_view': ('/manual_gpio',),
    'modern_admin_log_view': ('/log',),
    'modern_admin_support_info_view': ('/support',),
    'modern_admin_account_view': ('/user',),
    'modern_admin_astropanel_view': ('/astropanel',),
    'modern_admin_image_processing_view': ('/processing',),
    'modern_admin_longterm_keogram_view': ('/longtermkeogram',),
    'modern_admin_camera_info_view': ('/camera',),
    'modern_admin_image_lag_view': ('/lag',),
    'modern_admin_adu_history_view': ('/adu',),
    'modern_admin_dark_library_view': ('/darks',),
    'modern_admin_mask_view': ('/mask',),
    'modern_admin_camera_simulator_view': ('/camerasimulator',),
    'modern_admin_image_circle_helper_view': ('/imagecirclehelper',),
    'modern_admin_file_space_usage_view': ('/filespaceusage',),
    'modern_admin_network_view': ('/network',),
    'modern_admin_drive_manager_view': ('/drives',),
    'modern_admin_virtualsky_view': ('/virtualsky',),
    'modern_admin_cameras_view': ('/cameras',),
    'modern_admin_taskqueue_view': ('/tasks',),
    'modern_admin_notifications_view': ('/notifications',),
    'modern_admin_users_view': ('/users',),
}


def register_navigation_redirects(blueprint):
    for target, paths in NAVIGATION_GROUPS.items():
        def navigate(target=target):
            destination = url_for('indi_allsky.' + target)
            query = urlencode(list(request.args.items(multi=True)))
            return redirect(destination + ('?' + query if query else ''))
        for index, path in enumerate(paths):
            blueprint.add_url_rule(path, endpoint='hybrid_navigation_' + target + '_' + str(index),
                                   view_func=navigate, methods=['GET'])
