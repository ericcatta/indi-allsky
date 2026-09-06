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


class ProviderUnavailable(RuntimeError):
    pass

class Controls(HTMLParser):
    """Discover static HTML controls, without claiming computed CSS/JS state."""
    VOID = {'area', 'base', 'br', 'col', 'embed', 'hr', 'img', 'input',
            'link', 'meta', 'param', 'source', 'track', 'wbr'}
    ROLES = {'button', 'link', 'switch', 'checkbox', 'radio', 'tab', 'menuitem',
             'menuitemcheckbox', 'menuitemradio', 'slider', 'spinbutton', 'combobox'}
    DISABLABLE = {'button', 'input', 'select', 'textarea'}

    def __init__(self):
        super().__init__()
        self.controls = []
        self.stack = []
        self.text = []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        parent = self.stack[-1] if self.stack else None
        node = {'tag': tag, 'attrs': a, 'control': None, 'first_legend': None}
        if tag == 'legend' and parent and parent['tag'] == 'fieldset' and parent['first_legend'] is None:
            parent['first_legend'] = node
        ancestors = self.stack + [node]
        form = next((n for n in reversed(self.stack) if n['tag'] == 'form'), None)
        interactive = (tag in ('a', 'button', 'select', 'textarea', 'summary')
                       or (tag == 'input' and a.get('type', 'text').lower() != 'hidden')
                       or a.get('role') in self.ROLES
                       or ('tabindex' in a and a['tabindex'] != '-1'))
        if interactive:
            disabled_by = []
            if tag in self.DISABLABLE:
                if 'disabled' in a:
                    disabled_by.append('self')
                for ancestor in self.stack:
                    if ancestor['tag'] == 'fieldset' and 'disabled' in ancestor['attrs']:
                        # HTML exempts only descendants of the first direct legend.
                        legend = ancestor['first_legend']
                        if legend is None or not any(n is legend for n in self.stack):
                            disabled_by.append('fieldset:' + ancestor['attrs'].get('id', ''))
            collapsed = []
            for index, ancestor in enumerate(self.stack):
                if ancestor['tag'] == 'details' and 'open' not in ancestor['attrs']:
                    child = ancestors[index + 1]
                    if child['tag'] != 'summary':
                        collapsed.append(ancestor['attrs'].get('id', ''))
            fa = form['attrs'] if form else {}
            item = {'tag': tag, 'dom_id': a.get('id', ''), 'name': a.get('name', ''),
                    'type': a.get('type', ''), 'href': a.get('href', ''),
                    'label': a.get('aria-label', ''),
                    'disabled': bool(disabled_by), 'disabled_by': disabled_by,
                    'aria_disabled': any(n['attrs'].get('aria-disabled') == 'true' for n in ancestors),
                    'hidden_attribute': any('hidden' in n['attrs'] for n in ancestors),
                    'inert': any('inert' in n['attrs'] for n in ancestors),
                    'collapsed_details': collapsed,
                    'described_by': list(dict.fromkeys(ref for n in ancestors for ref in n['attrs'].get('aria-describedby', '').split())),
                    'form': ({'id': fa.get('id', ''), 'action': fa.get('action', ''), 'method': fa.get('method', 'get')} if form else None),
                    'data': {k:v for k,v in a.items() if k.startswith('data-')},
                    'status': 'bloccato', 'reason': 'Interaction and effect not yet verified', 'evidence': []}
            self.controls.append(item)
            node['control'] = item
        if tag not in self.VOID:
            self.stack.append(node)

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if tag not in self.VOID:
            self.handle_endtag(tag)

    def handle_endtag(self, tag):
        for index in range(len(self.stack) - 1, -1, -1):
            if self.stack[index]['tag'] == tag:
                del self.stack[index:]
                break

    def handle_data(self, value):
        # Form values and executable/style text are not labels or audit signals.
        if any(n['tag'] in ('textarea', 'script', 'style') for n in self.stack):
            return
        value = value.strip()
        if value:
            self.text.append(value)
            for node in reversed(self.stack):
                if node['control'] is not None:
                    if not node['attrs'].get('aria-label'):
                        item = node['control']
                        item['label'] = (item['label'] + ' ' + value).strip()
                    break

    def identified(self, route):
        seen = {}
        for item in self.controls:
            # Keep previous stable keys; do not include visibility or field values.
            key = item['dom_id'] or hashlib.sha256(json.dumps({k:item[k] for k in ('tag','name','type','href','form','data')},sort_keys=True).encode()).hexdigest()[:16]
            seen[key] = seen.get(key, 0) + 1
            item['id'] = route + '::' + key + '::' + str(seen[key])
            item['label'] = item['label'][:160]
        return self.controls

def collect(runtime_config):
    from hybrid_runtime_fixture import isolated_app, login_client
    report = {'schema_version': 2, 'environment': 'isolated Flask, memory database, synthetic users/cameras',
              'classic_enabled': False, 'live_hardware_effects': False,
              'coverage_note': 'Static HTML discovery only; computed CSS, JavaScript-created controls, external form ownership and browser effects require DOM acceptance. No control is marked passed by discovery.', 'pages': []}
    with isolated_app(runtime_config, multi_camera=True) as app:
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
                for role, uid, camera in [('admin',1,1), ('admin',1,2), ('user',2,1), ('user',2,2), ('anonymous',None,1)]:
                    client = clients[role]
                    with client.session_transaction() as session:
                        session['camera_id'] = camera
                    scope = {'camera_id': camera, 'profile_id': 'test-profile-' + str(camera)}
                    case = {'role':role, **scope, 'controls':[]}
                    started = time.monotonic()
                    try:
                        response = client.get(rule.rule, query_string=scope)
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
