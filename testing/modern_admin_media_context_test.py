#!/usr/bin/env python3
"""Preserve Media context behavior while removing Classic inheritance."""
import ast
import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
# Complete class AST captured at 5692e45f; only the owning class names normalized.
FINGERPRINTS = {'HybridAduHistoryContextView': '27db6cb8e82fb6ebf5288d6a96c33f9c6f63c1caf4cff5d7444d7a373eb60a0a', 'HybridLoopContextView': 'eb0b18f3715356013040ecdfae917ea67ad2174b7d45e9abb63b468e65b0166d', 'HybridFileSpaceContextView': 'e80886cb407e9eee61ef6bc18a4e3691e39b3909ed104f0c50b0e2ee83e0fc43'}


def run():
    tree = ast.parse((ROOT/'indi_allsky/flask/media_context_views.py').read_text())
    classes = {n.name:n for n in tree.body if isinstance(n, ast.ClassDef)}
    assert set(classes) == set(FINGERPRINTS)
    for name, fingerprint in FINGERPRINTS.items():
        assert hashlib.sha256(ast.dump(classes[name], include_attributes=False).encode()).hexdigest() == fingerprint, name
    assert not any(isinstance(n, ast.ImportFrom) and n.module in ('views', 'classic_views') for n in ast.walk(tree))
    handlers = ast.parse((ROOT/'indi_allsky/flask/views.py').read_text())
    wrappers = {'ModernAdminAduHistoryView': 'HybridAduHistoryContextView', 'ModernAdminLoopView': 'HybridLoopContextView', 'ModernAdminFileSpaceUsageView': 'HybridFileSpaceContextView'}
    for node in handlers.body:
        if isinstance(node, ast.ClassDef) and node.name in wrappers:
            assert ast.unparse(node.bases[-1]) == wrappers[node.name]
    print('Media context: three unchanged class fingerprints and Hybrid ownership PASS')


if __name__ == '__main__':
    run()
