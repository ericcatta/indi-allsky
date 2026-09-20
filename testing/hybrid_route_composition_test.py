#!/usr/bin/env python3
"""Guard the first Classic isolation step without requiring camera libraries."""

import ast
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FLASK = ROOT / 'indi_allsky/flask'


def test_route_contract_is_unchanged():
    # Exact registrations from 6bb1431a: URL, endpoint, view, template, methods.
    calls = []
    for name in ('views.py',):
        for node in ast.walk(ast.parse((FLASK / name).read_text())):
            if (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Attribute)
                and node.func.attr == 'add_url_rule'
                and node.args[0].value not in ('/modern-admin/settings/storage-protection', '/modern-admin/config-restore/<int:config_id>/apply', '/modern-admin/settings/timelapse', '/modern-admin/media/raw-loop', '/modern-admin/updates/start', '/modern-admin/tools/focus/preview', '/media/<kind>/<int:camera_id>/<int:media_id>/original', '/modern-admin/media/archive', '/modern-admin/tools/mini-generate', '/modern-admin/tools/mini-preview', '/images/<path:path>', '/modern-admin/account', '/modern-admin/notifications/<int:notification_id>/acknowledge', '/modern-admin/operations/export', '/modern-admin/media/<kind>/<int:camera_id>/<int:media_id>/download')
            ):
                if node.args[0].value in ('/modern-admin/settings/analytics', '/modern-admin/settings/storage', '/modern-admin/settings/notifications', '/modern-admin/settings/acquisition-save', '/modern-admin/settings/fits-source'):
                    # These entries are now redirects and must not carry template arguments.
                    view = next(k for k in node.keywords if k.arg == 'view_func').value
                    assert not view.keywords
                    slug = node.args[0].value.rsplit('/', 1)[1].replace('-', '_')
                    view.keywords.append(ast.keyword(arg='template_name', value=ast.Constant(value='modern_admin/settings_' + slug + '.html')))
                if node.args[0].value == '/modern-admin/settings/ready':
                    view = next(k for k in node.keywords if k.arg == 'view_func').value
                    assert not view.keywords
                    view.keywords.append(ast.keyword(arg='template_name', value=ast.Constant(value='modern_admin/settings_basic.html')))
                if node.args[0].value == '/modern-admin/classic/<classic_page>':
                    # A redirect has no template. Verify the replacement before
                    # restoring its historical registration for the fingerprint.
                    view = next(k for k in node.keywords if k.arg == 'view_func').value
                    assert ast.unparse(view) == "ModernAdminCompatibilityRedirectView.as_view('modern_admin_classic_placeholder_view')"
                    view.func.value.id = 'ModernAdminClassicPlaceholderView'
                    view.keywords.append(ast.keyword(arg='template_name', value=ast.Constant(value='modern_admin/placeholder.html')))
                if node.args[0].value in ('/modern-admin/tools/camera-simulator', '/modern-admin/tools/generate', '/modern-admin/tools/image-circle-helper', '/modern-admin/tools/process-fits', '/modern-admin/tools/focus', '/modern-admin/system/gpio-control', '/modern-admin/storage/drives', '/modern-admin/system/network'):
                    template = next(k for k in node.keywords if k.arg == 'view_func').value
                    setting = next(k for k in template.keywords if k.arg == 'template_name')
                    assert setting.value.value == {'/modern-admin/tools/camera-simulator':'modern_admin/camera_simulator.html', '/modern-admin/tools/generate':'modern_admin/generate.html', '/modern-admin/tools/image-circle-helper':'modern_admin/image_geometry.html', '/modern-admin/tools/process-fits':'modern_admin/image_processing.html', '/modern-admin/tools/focus':'modern_admin/focus.html', '/modern-admin/system/gpio-control':'modern_admin/manual_gpio.html', '/modern-admin/storage/drives':'modern_admin/drives.html', '/modern-admin/system/network':'modern_admin/network.html'}[node.args[0].value]
                    setting.value.value = 'modern_admin/safe_controls.html'
                if node.args[0].value in ('/view_image','/view_panorama','/view_startrail','/view_keogram','/view_raw','/watch_timelapse','/watch_mini_timelapse','/watch_startrail','/watch_panorama'):
                    template = next(k for k in node.keywords if k.arg == 'view_func').value
                    setting = next(k for k in template.keywords if k.arg == 'template_name')
                    assert setting.value.value == 'modern_admin/public_media.html'
                    setting.value.value = 'watch_video.html' if node.args[0].value.startswith('/watch_') else 'view_image.html'
                calls.append(ast.dump(node, include_attributes=False))
    retired_path = ROOT / 'testing/classic_frontend_contract.json'
    assert hashlib.sha256(retired_path.read_bytes()).hexdigest() == 'd900dc6e78d62ea2bc56d7ef83a6c65e0e3480016e418ac1f93eec2a2e623057'
    retired = json.loads(retired_path.read_text())
    calls.extend(row['ast'] for row in retired['registrations'])
    # These former previews now redirect to the camera editors. Check the new
    # registry, then retain the historical entries in the unchanged fingerprint.
    entry_tree = ast.parse((FLASK / 'settings_entries.py').read_text())
    entries = ast.literal_eval(next(n.value for n in entry_tree.body if isinstance(n, ast.Assign)
                                   and any(isinstance(t, ast.Name) and t.id == 'CAMERA_SETTINGS_ENTRIES' for t in n.targets)))
    expected = {
        'camera-profile': ('modern_admin_camera_profile_settings_view', 'driver-connection', 'CameraProfile'),
        'camera-connection': ('modern_admin_camera_connection_settings_view', 'driver-connection', 'CameraConnection'),
        'exposure-gain': ('modern_admin_exposure_gain_settings_view', 'acquisition', 'ExposureGain'),
        'auto-exposure-gain': ('modern_admin_auto_exposure_gain_settings_view', 'acquisition', 'AutoExposureGain'),
        'hybrid-awb': ('modern_admin_hybrid_awb_settings_view', 'hybrid-controller', 'HybridAwb'),
    }
    assert entries == {key: value[:2] for key, value in expected.items()}
    assert 'register_camera_settings_entries(bp_allsky)' in (FLASK / 'views.py').read_text()
    for path, (endpoint, anchor, class_part) in expected.items():
        template = 'modern_admin/settings_' + path.replace('-', '_') + '.html'
        historical = "bp_allsky.add_url_rule('/modern-admin/settings/" + path + "', view_func=ModernAdmin" + class_part + "SettingsView.as_view('" + endpoint + "', template_name='" + template + "'))"
        calls.append(ast.dump(ast.parse(historical).body[0].value, include_attributes=False))
    snapshot_calls = [n for n in ast.walk(ast.parse((FLASK / 'views.py').read_text()))
                      if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
                      and n.func.attr == 'add_url_rule' and n.args
                      and isinstance(n.args[0], ast.Constant)
                      and n.args[0].value == '/modern-admin/config-restore/<int:config_id>/apply']
    assert len(snapshot_calls) == 1
    snapshot_view = next(k.value for k in snapshot_calls[0].keywords if k.arg == 'view_func')
    assert ast.unparse(snapshot_view) == "ModernAdminSnapshotRestoreView.as_view('modern_admin_snapshot_restore_view')"
    # New Storage route has its own explicit contract; historical fingerprints
    # still cover exactly the pre-existing routes without being rewritten.
    storage_calls = [n for n in ast.walk(ast.parse((FLASK / 'views.py').read_text()))
                     if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
                     and n.func.attr == 'add_url_rule' and n.args
                     and isinstance(n.args[0], ast.Constant)
                     and n.args[0].value == '/modern-admin/settings/storage-protection']
    assert len(storage_calls) == 1
    storage_view = next(k.value for k in storage_calls[0].keywords if k.arg == 'view_func')
    assert ast.unparse(storage_view) == "ModernAdminStorageProtectionSettingsView.as_view('modern_admin_storage_protection_settings_view', template_name='modern_admin/settings_storage_protection.html')"
    assert len(calls) == 224
    fingerprint = hashlib.sha256('\n'.join(sorted(calls)).encode()).hexdigest()
    assert fingerprint == '17514e70700d7f9d255e1026f2ffb42d6bdf96db13a97e65b9cdb4d9e8233d92'



def test_upgrade_route_is_hybrid_owned():
    tree = ast.parse((FLASK / 'views.py').read_text())
    registration = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'register_hybrid_routes')
    calls = [n for n in ast.walk(registration) if isinstance(n, ast.Call)
             and isinstance(n.func, ast.Attribute) and n.func.attr == 'add_url_rule'
             and n.args[0].value == '/modern-admin/updates/start']
    assert len(calls) == 1
    assert "ModernAdminUpgradeStartView.as_view('modern_admin_upgrade_start_view')" in ast.unparse(calls[0])
    view = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == 'ModernAdminUpgradeStartView')
    assert "methods = ['POST']" in ast.unparse(view)
    assert 'decorators = [login_required]' in ast.unparse(view)


def test_account_route_is_hybrid_owned():
    tree = ast.parse((FLASK / 'views.py').read_text())
    registration = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == 'register_hybrid_routes')
    additions = [node for node in ast.walk(registration) if isinstance(node, ast.Call)
                 and isinstance(node.func, ast.Attribute) and node.func.attr == 'add_url_rule'
                 and node.args[0].value == '/modern-admin/account']
    assert len(additions) == 1
    assert "ModernAdminAccountView.as_view('modern_admin_account_view', template_name='modern_admin/account.html')" in ast.unparse(additions[0])


def test_notification_ack_route_is_hybrid_owned():
    tree = ast.parse((FLASK / 'views.py').read_text())
    registration = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == 'register_hybrid_routes')
    calls = [node for node in ast.walk(registration) if isinstance(node, ast.Call)
             and isinstance(node.func, ast.Attribute) and node.func.attr == 'add_url_rule'
             and node.args[0].value == '/modern-admin/notifications/<int:notification_id>/acknowledge']
    assert len(calls) == 1
    assert "methods=['POST']" in ast.unparse(calls[0])
    exports = [node for node in ast.walk(registration) if isinstance(node, ast.Call)
               and isinstance(node.func, ast.Attribute) and node.func.attr == 'add_url_rule'
               and node.args[0].value == '/modern-admin/operations/export']
    assert len(exports) == 1 and "methods=['POST']" in ast.unparse(exports[0])

    assert 'ModernAdminNotificationAcknowledgeView.as_view' in ast.unparse(calls[0])


def test_source_download_is_hybrid_owned():
    tree = ast.parse((FLASK / 'views.py').read_text())
    register = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'register_hybrid_routes')
    calls = [n for n in ast.walk(register) if isinstance(n, ast.Call)
             and isinstance(n.func, ast.Attribute) and n.func.attr == 'add_url_rule'
             and n.args[0].value == '/modern-admin/media/<kind>/<int:camera_id>/<int:media_id>/download']
    assert len(calls) == 1 and 'ModernAdminSourceDownloadView.as_view' in ast.unparse(calls[0])


def test_classic_frontend_is_absent_and_bookmarks_are_retained():
    assert not (FLASK / 'classic_views.py').exists()
    retired = json.loads((ROOT / 'testing/classic_frontend_contract.json').read_text())
    from modern_admin_classic_page_isolation_test import run
    run()
    redirect_tree = ast.parse((FLASK / 'navigation_redirects.py').read_text())
    groups = ast.literal_eval(next(n.value for n in redirect_tree.body if isinstance(n, ast.Assign)
        and any(isinstance(t, ast.Name) and t.id == 'NAVIGATION_GROUPS' for t in n.targets)))
    retained = {path for paths in groups.values() for path in paths}
    assert {r['route'] for r in retired['registrations']} <= retained


def test_only_hybrid_blueprints_are_created_per_app():
    source = (FLASK / 'route_registry.py').read_text()
    tree = ast.parse(source)
    factory = next(node for node in tree.body if isinstance(node, ast.FunctionDef))
    assert not factory.args.args and not factory.args.kwonlyargs
    assert not any(isinstance(n, ast.ImportFrom) and n.module == 'classic_views' for n in ast.walk(tree))
    assert 'register_navigation_redirects(bp_allsky)' in source
    assert any(isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == 'Blueprint'
               for n in ast.walk(factory))
    source = (FLASK / '__init__.py').read_text()
    assert 'HYBRID_ENABLE_CLASSIC_UI' not in source
    assert 'app.register_blueprint(create_allsky_blueprint())' in source
    assert 'app.add_template_filter(basename)' in source
    assert 'from .views import bp_allsky' not in source


if __name__ == '__main__':
    test_route_contract_is_unchanged()
    test_upgrade_route_is_hybrid_owned()
    test_account_route_is_hybrid_owned()
    test_notification_ack_route_is_hybrid_owned()
    test_source_download_is_hybrid_owned()
    test_classic_frontend_is_absent_and_bookmarks_are_retained()
    test_only_hybrid_blueprints_are_created_per_app()
    print('Hybrid route composition checks passed')
