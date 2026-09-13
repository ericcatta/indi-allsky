#!/usr/bin/env python3
"""Preserve System context behavior while removing Classic inheritance."""
import ast
import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
# Complete class AST captured at 93593eb0; only the owning class names normalized.
FINGERPRINTS = {'HybridSystemInfoContextView': '1b616543c1c21fd808c0a8067764d197b304e659477287aa3bb5724c9b895ddf', 'HybridLogContextView': 'c46e157feea79f1fa7338a9b59f025a1cefa63f67c1d8db0c1d4bea7508e5c2f', 'HybridSupportContextView': '35a9c8943d1815058aed835bb1539ef318ef3055fe466352ea48232b4eece045'}


def run():
    tree = ast.parse((ROOT/'indi_allsky/flask/system_context_views.py').read_text())
    classes = {n.name:n for n in tree.body if isinstance(n, ast.ClassDef)}
    assert set(classes) == set(FINGERPRINTS)
    for name, fingerprint in FINGERPRINTS.items():
        assert hashlib.sha256(ast.dump(classes[name], include_attributes=False).encode()).hexdigest() == fingerprint, name
    assert not any(isinstance(n, ast.ImportFrom) and n.module in ('views', 'classic_views') for n in ast.walk(tree))
    handlers = ast.parse((ROOT/'indi_allsky/flask/views.py').read_text())
    wrappers = {'ModernAdminSystemInfoView':'HybridSystemInfoContextView', 'ModernAdminLogView':'HybridLogContextView', 'ModernAdminSupportInfoView':'HybridSupportContextView'}
    for node in handlers.body:
        if isinstance(node, ast.ClassDef) and node.name in wrappers:
            assert ast.unparse(node.bases[-1]) == wrappers[node.name]
    print('System context: three unchanged class fingerprints and Hybrid ownership PASS')


if __name__ == '__main__':
    run()
