#!/usr/bin/env python3
"""Compare navigation authentication gates, without importing Classic views.

This executes the real authentication decorators against an isolated Flask app.
It does not claim to render every page or verify the sensitivity of its payload.
"""
import argparse
import hashlib
from collections import Counter
import json
from pathlib import Path
from hybrid_runtime_fixture import isolated_app, login_client

ROOT = Path(__file__).resolve().parents[1]


def classic_gates():
    path = ROOT/'testing/classic_navigation_auth_contract.json'
    assert hashlib.sha256(path.read_bytes()).hexdigest() == '385d12c2a4a95464ae0333dce595e6a16801a3960650afa2f50fed783960e1c7'
    contract = json.loads(path.read_text())
    assert len(contract['gates']) == 56
    return contract['gates']


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
        assert all(row['hybrid_gate'] == 'login_required' for row in rows)
        return {'scope': 'Authentication gates only: actual decorators in isolated Flask, historical Classic inheritance preserved in the frozen authentication contract; no Classic import or live effect.',
                'legacy_gate_counts': dict(Counter(row['legacy_gate'] for row in rows)),
                'hybrid_gate_counts': dict(Counter(row['hybrid_gate'] for row in rows)),
                'different_gate_count': sum(row['different_gate'] for row in rows),
                'gate_results': gate_results, 'routes': rows,
                'policy': 'User selected login-required Hybrid UI on 2026-09-20. Historical optional navigation gates are intentionally superseded; public media/API handlers retain their separate contracts.',
                'limits': 'This audit does not verify every authorization inside a view or public media/API behavior.'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = collect()
    args.output.write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps({key: result[key] for key in ('legacy_gate_counts', 'hybrid_gate_counts', 'different_gate_count')}, indent=2))
