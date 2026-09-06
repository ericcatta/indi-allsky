#!/usr/bin/env python3
"""Inventory actual rendered Hybrid controls in an isolated Flask application.

This is discovery, not proof that clicks work. Every discovered interaction
starts blocked until an acceptance case verifies its effect. Report files are
written only to the explicit --output path; older inventories are untouched.
"""
import argparse
import hashlib
from html.parser import HTMLParser
import ast
import json
from pathlib import Path
import time
from unittest.mock import patch

from hybrid_runtime_fixture import isolated_app, login_client

class ProviderUnavailable(RuntimeError):
    pass

class Controls(HTMLParser):
    def __init__(self):
        super().__init__()
        self.controls = []
        self.active = []
        self.form = None
        self.text = []
    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == 'form':
            self.form = {'id': a.get('id', ''), 'action': a.get('action', ''), 'method': a.get('method', 'get')}
        interactive = tag in ('a', 'button', 'select', 'textarea') or (tag == 'input' and a.get('type', 'text') != 'hidden') or a.get('role') in ('button', 'link', 'switch')
        if not interactive:
            return
        self.controls.append({'tag': tag, 'dom_id': a.get('id', ''), 'name': a.get('name', ''),
            'type': a.get('type', ''), 'href': a.get('href', ''), 'label': a.get('aria-label', ''),
            'disabled': 'disabled' in a or a.get('aria-disabled') == 'true',
            'form': self.form, 'data': {k:v for k,v in a.items() if k.startswith('data-')},
            'status': 'bloccato', 'reason': 'Interaction and effect not yet verified', 'evidence': []})
        if tag != 'input':
            self.active.append((tag, self.controls[-1]))
    def handle_endtag(self, tag):
        if tag == 'form':
            self.form = None
        if self.active and self.active[-1][0] == tag:
            self.active.pop()
    def handle_data(self, value):
        value = value.strip()
        if value:
            self.text.append(value)
            if self.active:
                item = self.active[-1][1]
                item['label'] = (item['label'] + ' ' + value).strip()
    def identified(self, route):
        seen = {}
        for item in self.controls:
            # Do not record field values (including configuration secrets).
            key = item['dom_id'] or hashlib.sha256(json.dumps({k:item[k] for k in ('tag','name','type','href','form','data')},sort_keys=True).encode()).hexdigest()[:16]
            seen[key] = seen.get(key, 0) + 1
            item['id'] = route + '::' + key + '::' + str(seen[key])
            item['label'] = item['label'][:160]
        return self.controls

def collect(runtime_config):
    report = {'schema_version': 1, 'environment': 'isolated Flask, memory database, synthetic users/cameras',
              'classic_enabled': False, 'live_hardware_effects': False,
              'coverage_note': 'HTTP rendering and control discovery only; no control is marked passed by discovery.', 'pages': []}
    with isolated_app(runtime_config) as app:
        from indi_allsky.flask.base_views import TemplateView
        from indi_allsky.flask import views
        source = ast.parse(Path(views.__file__).read_text())
        registration = next(n for n in source.body if isinstance(n, ast.FunctionDef) and n.name == 'register_hybrid_routes')
        classes = {'indi_allsky.'+n.args[0].value: getattr(views, n.func.value.id)
                   for n in ast.walk(registration) if isinstance(n, ast.Call)
                   and isinstance(n.func, ast.Attribute) and n.func.attr == 'as_view'}
        clients = {'admin': login_client(app, 1), 'user': login_client(app, 2), 'anonymous': app.test_client()}
        # Prevent an accidental hardware/network/service effect in any GET.
        with patch('subprocess.Popen', side_effect=ProviderUnavailable('External process blocked in acceptance discovery')), \
             patch('dbus.SystemBus', side_effect=ProviderUnavailable('Hardware bus unavailable in acceptance discovery')), \
             patch('dbus.SessionBus', side_effect=ProviderUnavailable('Service bus unavailable in acceptance discovery')):
            for rule in sorted(app.url_map.iter_rules(), key=lambda r:r.rule):
                if not rule.endpoint.startswith('indi_allsky.modern_admin_') or 'GET' not in rule.methods:
                    continue
                cls = classes.get(rule.endpoint)
                if cls is None or not issubclass(cls, TemplateView):
                    continue
                page = {'route': rule.rule, 'endpoint': rule.endpoint, 'contexts': []}
                report['pages'].append(page)
                if rule.arguments:
                    page.update(status='bloccato', reason='Detail route requires dedicated fixture parameters')
                    continue
                for role, uid, camera in [('admin',1,1), ('admin',1,2), ('user',2,1), ('anonymous',None,1)]:
                    client = clients[role]
                    with client.session_transaction() as session:
                        session['camera_id'] = camera
                    case = {'role':role, 'camera_id':camera, 'controls':[]}
                    started = time.monotonic()
                    try:
                        response = client.get(rule.rule)
                        case['http_status'] = response.status_code
                        case['redirect'] = response.location
                        if response.status_code == 200:
                            parser = Controls()
                            parser.feed(response.text)
                            case['controls'] = parser.identified(rule.rule)
                            case['render_status'] = 'superato'
                            text = ' '.join(parser.text).lower()
                            case['placeholder_signals'] = [s for s in ['placeholder-only', 'static placeholders', 'coming later', 'not implemented', 'disabled in modern admin', 'future backend contract'] if s in text]
                        else:
                            case['render_status'] = 'bloccato' if response.status_code in (301,302,303,401,403) else 'difetto'
                    except ProviderUnavailable as exc:
                        case.update(render_status='bloccato', error=str(exc))
                    except Exception as exc:
                        case.update(render_status='difetto', error=type(exc).__name__ + ': ' + str(exc)[:250])
                    case['elapsed_ms'] = round((time.monotonic()-started)*1000, 1)
                    page['contexts'].append(case)
                failures = [c for c in page['contexts'] if c['render_status']=='difetto']
                print(rule.rule, 'DEFECT' if failures else 'RENDERED/BLOCKED', (failures[0].get('error','') if failures else ''), flush=True)
    assert len(report['pages']) >= 70, 'Route discovery is incomplete'
    return report

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--runtime-config', default='/etc/indi-allsky/flask.json')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    report = collect(args.runtime_config)
    args.output.write_text(json.dumps(report, indent=2))
    print('Report written:', args.output)
