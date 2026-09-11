#!/usr/bin/env python3
"""Preserve Observatory context behavior while removing Classic inheritance."""
import ast
import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
# Complete class AST captured at aa3c2dfd; only the owning class names normalized.
FINGERPRINTS = {'HybridVirtualSkyContextView': '0c8aef738ba13a748896c39fb40dcc9baa4355b061bcd6049921c9071f894219', 'HybridSqmContextView': '9842b29068779366b3c5e19b5463e4cbb868cbfc2fec1196ad94aa8cfc43c0fd', 'HybridChartContextView': 'ef71141a82445ebcbd66a9dd66ff2d1c83cbdbbf2c90f5419e54552ea8469165', 'HybridSensorPanelContextView': '325d746a47d029a7525757e48bc0a9e737279141034d8e9fe5122c6b4d3908d1'}


def run():
    tree = ast.parse((ROOT/'indi_allsky/flask/observatory_context_views.py').read_text())
    classes = {n.name:n for n in tree.body if isinstance(n, ast.ClassDef)}
    assert set(classes) == set(FINGERPRINTS)
    for name, fingerprint in FINGERPRINTS.items():
        assert hashlib.sha256(ast.dump(classes[name], include_attributes=False).encode()).hexdigest() == fingerprint, name
    assert not any(isinstance(n, ast.ImportFrom) and n.module in ('views', 'classic_views') for n in ast.walk(tree))
    handlers = ast.parse((ROOT/'indi_allsky/flask/views.py').read_text())
    wrappers = {'ModernAdminSqmView':'HybridSqmContextView',
                'ModernAdminChartsView':'HybridChartContextView',
                'ModernAdminSensorPanelView':'HybridSensorPanelContextView',
                'ModernAdminVirtualSkyView':'HybridVirtualSkyContextView'}
    for node in handlers.body:
        if isinstance(node, ast.ClassDef) and node.name in wrappers:
            assert ast.unparse(node.bases[-1]) == wrappers[node.name]
    print('Observatory context: four unchanged class fingerprints and Hybrid ownership PASS')


if __name__ == '__main__':
    run()
