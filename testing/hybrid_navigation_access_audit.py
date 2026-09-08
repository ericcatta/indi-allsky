#!/usr/bin/env python3
"""Compare navigation authentication gates, without importing Classic views.

This executes the real authentication decorators against an isolated Flask app.
It does not claim to render every page or verify the sensitivity of its payload.
"""
import argparse
import ast
from collections import Counter
import json
from pathlib import Path
from hybrid_runtime_fixture import isolated_app, login_client

ROOT = Path(__file__).resolve().parents[1]


def classic_gates():
    classes = {}
    for file in ('base_views.py', 'views.py', 'classic_views.py'):
        tree = ast.parse((ROOT/'indi_allsky/flask'/file).read_text())
        classes.update({node.name: node for node in tree.body if isinstance(node, ast.ClassDef)})
    cache = {'object': object}
    def skeleton(name):
        if name in cache:
            return cache[name]
        node = classes.get(name)
        bases = tuple(skeleton(base.id) for base in node.bases if isinstance(base, ast.Name)) if node else ()
        attrs = {}
        for statement in node.body if node else []:
            if isinstance(statement, ast.Assign) and any(isinstance(target, ast.Name) and target.id == 'decorators' for target in statement.targets):
                assert isinstance(statement.value, ast.List)
                attrs['decorators'] = [value.id for value in statement.value.elts]
        cache[name] = type(name, bases or (object,), attrs)
        return cache[name]
    tree = ast.parse((ROOT/'indi_allsky/flask/classic_views.py').read_text())
    result = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == 'add_url_rule':
            view = next(value.value for value in node.keywords if value.arg == 'view_func').func.value.id
            gates = skeleton(view).decorators
            assert len(gates) == 1
            result[node.args[0].value] = {'class': view, 'gate': gates[0]}
    return result


def collect():
    legacy = classic_gates()
    with isolated_app(multi_camera=True) as app:
        from flask_login import login_required
        from indi_allsky.flask.misc import login_optional, login_optional_media
        from indi_allsky.flask.navigation_redirects import NAVIGATION_GROUPS
        gates = {gate.__name__: gate for gate in (login_required, login_optional, login_optional_media)}
        for name, gate in gates.items():
            app.add_url_rule('/audit-gate/'+name, endpoint='audit_'+name, view_func=gate(lambda: 'Allowed'))
        clients = {'anonymous': app.test_client(), 'user': login_client(app, 2), 'admin': login_client(app, 1)}
        gate_results = {}
        for all_views in (False, True):
            for media_views in (False, True):
                app.config.update(INDI_ALLSKY_AUTH_ALL_VIEWS=all_views, INDI_ALLSKY_AUTH_MEDIA_VIEWS=media_views)
                key = f'all={all_views},media={media_views}'
                gate_results[key] = {name: {} for name in gates}
                for name in gates:
                    for role, client in clients.items():
                        response = client.get('/audit-gate/'+name)
                        expected = 302 if role == 'anonymous' and (name == 'login_required' or all_views or (name == 'login_optional_media' and media_views)) else 200
                        assert response.status_code == expected, (name, key, role, response.status_code)
                        gate_results[key][name][role] = response.status_code
        rows = []
        for target, paths in NAVIGATION_GROUPS.items():
            cls = app.view_functions['indi_allsky.'+target].view_class
            decorators = cls.decorators
            assert len(decorators) == 1 and decorators[0].__name__ in gates
            for path in paths:
                rows.append({'path': path, 'legacy_class': legacy[path]['class'],
                             'legacy_gate': legacy[path]['gate'], 'hybrid_endpoint': target,
                             'hybrid_gate': decorators[0].__name__,
                             'different_gate': legacy[path]['gate'] != decorators[0].__name__})
        assert len(rows) == len(legacy) == 56
        return {'scope': 'Authentication gates only: actual decorators in isolated Flask, Classic inheritance read via AST; no Classic import or live effect.',
                'legacy_gate_counts': dict(Counter(row['legacy_gate'] for row in rows)),
                'hybrid_gate_counts': dict(Counter(row['hybrid_gate'] for row in rows)),
                'different_gate_count': sum(row['different_gate'] for row in rows),
                'gate_results': gate_results, 'routes': rows,
                'open': 'Choose public navigation policy before Classic retirement; public media/API handlers are separate. This audit does not validate page payload disclosure or every authorization inside a view.'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = collect()
    args.output.write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps({key: result[key] for key in ('legacy_gate_counts', 'hybrid_gate_counts', 'different_gate_count')}, indent=2))
