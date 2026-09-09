#!/usr/bin/env python3
"""Regression for acceptance discovery blind spots; no Flask/hardware needed."""
import json
from hybrid_ui_acceptance_test import Controls, route_kind
from types import SimpleNamespace


def parse(html):
    parser = Controls()
    parser.feed(html)
    return parser, {item['dom_id']: item for item in parser.identified('/example')}


parser, controls = parse('''
<form id="settings" action="/save" method="post">
<fieldset id="permission" disabled aria-describedby="permission-reason">
<legend><button id="legend-help">Help</button></legend>
<input id="gain" value="secret-not-a-label">
<fieldset><legend><input id="nested-legend"></legend></fieldset>
<legend><button id="second-legend">Other</button></legend>
<a id="docs" href="/docs">Documentation</a>
</fieldset>
<button id="save">Save <span>settings</span></button>
<textarea id="config" aria-label="Configuration">private-area-value</textarea>
<input type="hidden" id="csrf" value="csrf-secret">
</form><button id="outside">Outside</button>
''')
assert not controls['legend-help']['disabled']
for key in ('gain', 'nested-legend', 'second-legend'):
    assert controls[key]['disabled_by'] == ['fieldset:permission'], controls[key]
    assert controls[key]['described_by'] == ['permission-reason']
assert not controls['docs']['disabled']  # fieldset does not disable links
assert not controls['save']['disabled']
assert controls['save']['form'] == {'id': 'settings', 'action': '/save', 'method': 'post'}
assert controls['save']['label'] == 'Save settings'
assert controls['outside']['form'] is None
assert controls['config']['label'] == 'Configuration'
assert 'csrf' not in controls
serialized = json.dumps(controls) + ' '.join(parser.text)
for secret in ('secret-not-a-label', 'private-area-value', 'csrf-secret'):
    assert secret not in serialized

parser, controls = parse('''
<details id="advanced"><summary id="toggle"><span>Advanced</span></summary>
<button id="inside">Edit</button>
<details id="inner" open><summary id="inner-toggle">Inner</summary></details>
</details>
<details open><summary id="open-toggle">Open</summary><input id="visible"></details>
<section hidden="false"><button id="hidden">Hidden</button></section>
<section inert aria-disabled="true"><div role="tab" id="tab">Tab</div></section>
<div tabindex="0" id="custom">Custom control</div>
<button id="explicit" disabled aria-label="Action"><span>Different</span></button>
<script>not implemented</script><style>coming later</style>
''')
assert 'not implemented' not in ' '.join(parser.text)
assert 'coming later' not in ' '.join(parser.text)
assert controls['toggle']['tag'] == 'summary'
assert controls['toggle']['collapsed_details'] == []
assert controls['inside']['collapsed_details'] == ['advanced']
assert controls['inner-toggle']['collapsed_details'] == ['advanced']
assert controls['visible']['collapsed_details'] == []
assert controls['hidden']['hidden_attribute']
assert controls['tab']['inert'] and controls['tab']['aria_disabled']
assert not controls['tab']['disabled']  # ARIA does not enforce native disabling
assert controls['custom']['tag'] == 'div'
assert controls['explicit']['disabled_by'] == ['self']
assert controls['explicit']['label'] == 'Action'
assert all(item['status'] == 'bloccato' and not item['evidence'] for item in controls.values())

_, first = parse('<form id="f"><input name="gain" value="1"></form>')
_, second = parse('<form id="f"><input name="gain" value="2" disabled></form>')
assert first['']['id'] == second['']['id'], 'Field values/state must not change stable identity'
print('Hybrid acceptance HTML discovery: PASS (fieldset, disclosure, state, secret exclusion, identity)')

class TemplateBase: pass
class Page(TemplateBase): pass
class Redirect: pass

def rule(path, endpoint='indi_allsky.modern_admin_example_view', methods=('GET',)):
    return SimpleNamespace(rule=path, endpoint=endpoint, methods=methods)

assert route_kind(rule('/modern-admin/now'), Page, TemplateBase) == 'page'
assert route_kind(rule('/modern-admin/settings/storage'), Redirect, TemplateBase) == 'settings-entry'
assert route_kind(rule('/modern-admin/settings/camera-profile'), None, TemplateBase) == 'settings-entry'
assert route_kind(rule('/modern-admin/provider'), None, TemplateBase) == 'unclassified-get'
assert route_kind(rule('/modern-admin/action', methods=('POST',)), Page, TemplateBase) is None
assert route_kind(rule('/external', endpoint='other.view'), Page, TemplateBase) is None
print('Hybrid GET discovery includes factory and redirect entries: PASS')

assert route_kind(rule('/indi-allsky/modern-admin/settings/storage'), Redirect, TemplateBase) == 'settings-entry'
