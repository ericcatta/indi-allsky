#!/usr/bin/env python3
"""Guard the first Classic isolation step without requiring camera libraries."""

import ast
import hashlib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FLASK = ROOT / 'indi_allsky/flask'


def test_route_contract_is_unchanged():
    # Exact registrations from 6bb1431a: URL, endpoint, view, template, methods.
    calls = []
    for name in ('views.py', 'classic_views.py'):
        for node in ast.walk(ast.parse((FLASK / name).read_text())):
            if (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Attribute)
                and node.func.attr == 'add_url_rule'
                and node.args[0].value not in ('/images/<path:path>', '/modern-admin/account', '/modern-admin/notifications/<int:notification_id>/acknowledge', '/modern-admin/operations/export')
            ):
                calls.append(ast.dump(node, include_attributes=False))
    assert len(calls) == 224
    fingerprint = hashlib.sha256('\n'.join(sorted(calls)).encode()).hexdigest()
    assert fingerprint == '17514e70700d7f9d255e1026f2ffb42d6bdf96db13a97e65b9cdb4d9e8233d92'



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


def test_classic_class_bodies_are_preserved_and_isolated():
    tree = ast.parse((FLASK / 'classic_views.py').read_text())
    classes = [node for node in tree.body if isinstance(node, ast.ClassDef)]
    assert len(classes) == 27
    fingerprint = hashlib.sha256('\n'.join(
        ast.dump(node, include_attributes=False) for node in classes
    ).encode()).hexdigest()
    assert fingerprint == 'b65f733a214c77f48be79d5d174e7e71882a55cfeec1425de0d4540fba575614'
    classic_names = {node.name for node in classes}
    handlers = ast.parse((FLASK / 'views.py').read_text())
    assert classic_names.isdisjoint(
        node.id for node in ast.walk(handlers) if isinstance(node, ast.Name)
    )
    assert not any(
        isinstance(node, ast.ImportFrom) and node.module == 'classic_views'
        for node in ast.walk(handlers)
    )


def test_classic_import_is_conditional_and_blueprints_are_per_app():
    tree = ast.parse((FLASK / 'route_registry.py').read_text())
    factory = next(node for node in tree.body if isinstance(node, ast.FunctionDef))
    conditional = next(node for node in factory.body if isinstance(node, ast.If))
    assert ast.unparse(conditional.test) == 'enable_classic_ui'
    imports = [node for node in ast.walk(tree) if isinstance(node, ast.ImportFrom) and node.module == 'classic_views']
    assert len(imports) == 1 and imports[0] in conditional.body
    assert any(
        isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == 'Blueprint'
        for node in ast.walk(factory)
    )
    source = (FLASK / '__init__.py').read_text()
    assert "app.config.setdefault('HYBRID_ENABLE_CLASSIC_UI', True)" in source
    assert 'app.add_template_filter(basename)' in source
    assert 'from .views import bp_allsky' not in source


if __name__ == '__main__':
    test_route_contract_is_unchanged()
    test_account_route_is_hybrid_owned()
    test_notification_ack_route_is_hybrid_owned()
    test_classic_class_bodies_are_preserved_and_isolated()
    test_classic_import_is_conditional_and_blueprints_are_per_app()
    print('Hybrid route composition checks passed')
