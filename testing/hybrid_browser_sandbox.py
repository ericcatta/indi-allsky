#!/usr/bin/env python3
"""Local-only browser acceptance server. Never connect it to production data.

Synthetic identities are provided by hybrid_runtime_fixture. All media and DB
state disappear on exit. External effects and integration writes are blocked.
"""
import argparse
import re
from unittest.mock import patch
from hybrid_runtime_fixture import isolated_app
from hybrid_operations_fixture import seed_operations
from hybrid_source_media_fixture import seed_source_media
from hybrid_generation_fixture import seed_generation, seed_preview_frames
from hybrid_generated_media_fixture import seed_generated_media
from hybrid_archive_fixture import seed_archive
from hybrid_public_media_fixture import seed_public_media

class SandboxEffectBlocked(RuntimeError):
    pass

def run(runtime_config, port):
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
        from flask import request, jsonify
        from indi_allsky.flask.views import AjaxConfigRestoreView
        @app.before_request
        def restrict_sandbox_effects():
            if request.method not in ('POST', 'PUT', 'PATCH', 'DELETE'):
                return None
            # Only generation queues into the in-memory DB; no worker consumes it.
            payload = request.get_json(silent=True)
            if request.path == '/indi-allsky/modern-admin/settings/cameras' and request.form.get('modern_admin_action') == 'lens_optics' and not request.form.get('modern_admin_save_sync'):
                return None
            # FITS previews read only synthetic files; no source/config is overwritten.
            if request.path == '/indi-allsky/js/processing':
                return None
            if request.path == '/indi-allsky/ajax/minigenerate':
                return None
            if request.path == '/indi-allsky/ajax/generate' and isinstance(payload, dict) and payload.get('ACTION_SELECT') in ('generate_video', 'generate_k_st', 'generate_video_k_st', 'generate_panorama_video'):
                return None
            notification_ack = re.fullmatch(r'/indi-allsky/modern-admin/notifications/[1-3]/acknowledge', request.path)
            if not notification_ack and request.path not in ('/indi-allsky/login', '/indi-allsky/ajax/config',
                                    '/indi-allsky/ajax/user', '/indi-allsky/ajax/config/restore', '/indi-allsky/modern-admin/operations/export'):
                return jsonify({'form_global':['External effects are blocked in this isolated acceptance server.']}), 409
            if request.path.endswith('/config/restore') and (request.form.get('RESET_KEYS') or request.form.get('FLUSH_CONFIGS')):
                return jsonify({'form_global':['Security-key reset and history purge are blocked in this browser sandbox.']}), 409
            return None
        def blocked(*args, **kwargs):
            raise SandboxEffectBlocked('External effect blocked in isolated acceptance server')
        # Defense in depth: even accidentally called adapters cannot reach Pi services.
        with patch('subprocess.Popen', side_effect=blocked), patch('os.system', side_effect=blocked), \
             patch('dbus.SystemBus', side_effect=blocked), patch('dbus.SessionBus', side_effect=blocked), \
             patch.object(AjaxConfigRestoreView, 'reset_security_keys_after_restore', side_effect=blocked):
            print('Isolated acceptance server; no production data or effects.', flush=True)
            app.run(host='127.0.0.1', port=port, debug=False, use_reloader=False, threaded=False)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--runtime-config', default='/etc/indi-allsky/flask.json')
    parser.add_argument('--port', type=int, default=8099)
    args = parser.parse_args()
    run(args.runtime_config, args.port)
