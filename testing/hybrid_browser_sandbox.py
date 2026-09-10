#!/usr/bin/env python3
"""Local-only browser acceptance server. Never connect it to production data.

Synthetic identities are provided by hybrid_runtime_fixture. All media and DB
state disappear on exit. External effects and integration writes are blocked.
"""
import argparse
from contextlib import ExitStack
from pathlib import Path
import re
from unittest.mock import patch
from hybrid_runtime_fixture import isolated_app
from hybrid_operations_fixture import seed_operations
from hybrid_source_media_fixture import seed_source_media
from hybrid_generation_fixture import seed_generation, seed_preview_frames, seed_cleanup_frames
from hybrid_generated_media_fixture import seed_generated_media
from hybrid_archive_fixture import seed_archive
from hybrid_public_media_fixture import seed_public_media

class SandboxEffectBlocked(RuntimeError):
    pass

def run(runtime_config, port, upgrade_fixture=None, maintenance_fixture=False):
    with isolated_app(runtime_config, multi_camera=True) as app:
        app.jinja_env.auto_reload = True
        app.config.update(INDI_ALLSKY_AUTH_ALL_VIEWS=False, INDI_ALLSKY_AUTH_MEDIA_VIEWS=False)
        app.config['ADMIN_NETWORKS'] = ['127.0.0.0/8', '::1/128']
        seed_operations(app)
        seed_source_media(app)
        seed_generation(app)
        seed_preview_frames(app)
        seed_generated_media(app)
        seed_archive(app)
        seed_public_media(app)
        if maintenance_fixture:
            seed_cleanup_frames(app)
        from flask import request, jsonify
        from indi_allsky.flask.views import AjaxConfigRestoreView, JsonLogView
        from indi_allsky.flask.forms import IndiAllskyNetworkManagerForm
        synthetic_log = Path(app.config['INDI_ALLSKY_IMAGE_FOLDER']) / 'browser-acceptance.log'
        synthetic_log.write_text('Synthetic log header\nCamera 1: synthetic capture ready\nCamera 2: synthetic capture ready\nSynthetic upload completed\n')
        def sandbox_path(value, *parts):
            if str(value) == '/var/log/indi-allsky/indi-allsky.log' and not parts:
                return synthetic_log
            return Path(value, *parts)
        original_log_dispatch = JsonLogView.dispatch_request
        def synthetic_log_dispatch(view):
            with patch('indi_allsky.flask.views.Path', side_effect=sandbox_path):
                return original_log_dispatch(view)
        # Read-only browser fixtures; command requests remain blocked below.
        def network_connections(self):
            return {'Wi-Fi': [('sandbox-wifi', 'Synthetic Wi-Fi — Active [prio: 0]')],
                    'Ethernet': [('sandbox-ethernet', 'Synthetic Ethernet — Not Active')]}
        def network_devices(self):
            return [('sandbox-wlan', 'Synthetic wireless interface')]
        @app.before_request
        def restrict_sandbox_effects():
            if request.method not in ('POST', 'PUT', 'PATCH', 'DELETE'):
                return None
            # Only generation queues into the in-memory DB; no worker consumes it.
            payload = request.get_json(silent=True)
            if maintenance_fixture and request.path == '/indi-allsky/ajax/system' and isinstance(payload, dict):
                command = payload.get('COMMAND_HIDDEN')
                service = payload.get('SERVICE_HIDDEN')
                # Only synthetic DB/file operations; no service or power effects.
                if service == 'system' and command in ('backup_db', 'expire_data', 'validate_db', 'flush_images', 'flush_16min_images', 'flush_timelapses', 'flush_daytime'):
                    return None
                if service == app.config['ALLSKY_SERVICE_NAME'] and command == 'hup':
                    return None  # Enqueued in memory; no capture worker consumes it.
            if request.path == '/indi-allsky/js/log':
                return None  # Read-only, redirected to the synthetic log below.
            if upgrade_fixture and request.path == '/indi-allsky/modern-admin/updates/start':
                return None  # Only the explicit synthetic service below can execute.
            if request.path == '/indi-allsky/modern-admin/settings/cameras' and request.form.get('modern_admin_action') == 'lens_optics' and not request.form.get('modern_admin_save_sync'):
                return None
            # FITS previews read only synthetic files; no source/config is overwritten.
            if request.path == '/indi-allsky/js/processing':
                return None
            if request.path == '/indi-allsky/ajax/minigenerate':
                return None
            if request.path == '/indi-allsky/ajax/generate' and isinstance(payload, dict) and payload.get('ACTION_SELECT') in ('generate_video', 'generate_k_st', 'generate_video_k_st', 'generate_panorama_video'):
                return None
            if re.fullmatch(r'/indi-allsky/modern-admin/config-restore/[1-9][0-9]*/apply', request.path):
                return None  # Writes only a new in-memory config revision; no reload or key reset.
            notification_ack = re.fullmatch(r'/indi-allsky/modern-admin/notifications/[1-3]/acknowledge', request.path)
            if not notification_ack and request.path not in ('/indi-allsky/login', '/indi-allsky/ajax/config',
                                    '/indi-allsky/ajax/user', '/indi-allsky/ajax/config/restore', '/indi-allsky/modern-admin/operations/export'):
                return jsonify({'form_global':['External effects are blocked in this isolated acceptance server.']}), 409
            if request.path.endswith('/config/restore') and (request.form.get('RESET_KEYS') or request.form.get('FLUSH_CONFIGS')):
                return jsonify({'form_global':['Security-key reset and history purge are blocked in this browser sandbox.']}), 409
            return None
        def blocked(*args, **kwargs):
            raise SandboxEffectBlocked('External effect blocked in isolated acceptance server')
        def blocked_bus(*args, **kwargs):
            import dbus
            raise dbus.exceptions.DBusException('D-Bus unavailable in synthetic browser fixture')
        # Defense in depth: even accidentally called adapters cannot reach Pi services.
        with ExitStack() as stack, patch('subprocess.Popen', side_effect=blocked), patch('os.system', side_effect=blocked), \
             patch('dbus.SystemBus', side_effect=blocked_bus), patch('dbus.SessionBus', side_effect=blocked_bus), \
             patch.object(JsonLogView, 'dispatch_request', synthetic_log_dispatch), \
             patch.object(IndiAllskyNetworkManagerForm, 'getConnections', network_connections), \
             patch.object(IndiAllskyNetworkManagerForm, 'getWifiDevices', network_devices), \
             patch.object(AjaxConfigRestoreView, 'reset_security_keys_after_restore', side_effect=blocked):
            if upgrade_fixture:
                from hybrid_upgrade_browser_fixture import install_upgrade_fixture
                install_upgrade_fixture(stack, upgrade_fixture)
            print('Isolated acceptance server; no production data or effects.', flush=True)
            app.run(host='127.0.0.1', port=port, debug=False, use_reloader=False, threaded=False)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--runtime-config', default='/etc/indi-allsky/flask.json')
    parser.add_argument('--port', type=int, default=8099)
    parser.add_argument('--upgrade-fixture', type=Path, help='Explicit synthetic upgrade state JSON; never a production service')
    parser.add_argument('--maintenance-fixture', action='store_true', help='Allow maintenance only against disposable synthetic DB/media; queued tasks have no worker')
    args = parser.parse_args()
    run(args.runtime_config, args.port, args.upgrade_fixture, args.maintenance_fixture)
