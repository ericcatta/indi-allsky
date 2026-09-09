#!/usr/bin/env python3
"""Validate detail discovery evidence, never promote controls to click passes."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path


def summarize(path):
    report = json.loads(path.read_text())
    assert report['schema_version'] == 3 and report['classic_enabled'] is False
    contexts = [case for page in report['pages'] for case in page['contexts']]
    details = [page for page in report['pages'] if '<' in page['route']]
    assert details
    rows = []
    for page in details:
        if not page['contexts']:
            assert page.get('status') == 'bloccato' and page.get('reason'), page['route']
            rows.append({'route': page['route'], 'contexts': 0, 'status': 'bloccato', 'reason': page['reason'], 'controls_discovered': 0})
            continue
        assert {case['role'] for case in page['contexts']} == {'admin', 'user', 'anonymous'}
        for case in page['contexts']:
            assert case['path_parameters'] and '<' not in case['request_path']
            assert case['render_status'] != 'difetto', case
        rows.append({'route': page['route'], 'contexts': len(page['contexts']),
                     'render_outcomes': dict(Counter(case['render_status'] for case in page['contexts'])),
                     'variants': sorted({case['request_path'] for case in page['contexts']}),
                     'controls_discovered': sum(len(case['controls']) for case in page['contexts'])})
    controls = [control for case in contexts for control in case['controls']]
    assert all(control['status'] == 'bloccato' and not control['evidence'] for control in controls)
    return {'scope': 'Static HTML discovery in isolated Flask. Rendering success is not interaction/effect acceptance.',
            'source_sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
            'pages': len(report['pages']), 'contexts': len(contexts),
            'render_outcomes': dict(Counter(case['render_status'] for case in contexts)),
            'controls_discovered': len(controls), 'controls_verified': 0,
            'detail_pages': rows,
            'blocked_contexts': [{'route': page['route'], 'role': case['role'],
                                 'camera_id': case['camera_id'], 'path_parameters': case['path_parameters'],
                                 'http_status': case.get('http_status'), 'error': case.get('error'),
                                 'redirect': case.get('redirect')}
                                for page in report['pages'] for case in page['contexts']
                                if case['render_status'] != 'superato']}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--report', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = summarize(args.report)
    args.output.write_text(json.dumps(result, indent=2) + '\n')
    print('Detail discovery verified:', len(result['detail_pages']), 'routes;', result['controls_verified'], 'clicks passed')
