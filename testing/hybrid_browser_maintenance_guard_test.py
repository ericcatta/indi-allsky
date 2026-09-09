#!/usr/bin/env python3
"""The explicit browser fixture must not permit service/power effects."""
import ast
from pathlib import Path
import re
from types import SimpleNamespace

source = Path(__file__).with_name('hybrid_browser_sandbox.py')
tree = ast.parse(source.read_text())
node = next(n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name == 'restrict_sandbox_effects')
node.decorator_list = []
namespace = dict(app=SimpleNamespace(config={'ALLSKY_SERVICE_NAME':'capture.service'}),
                 re=re, upgrade_fixture=None, jsonify=lambda x:x)
exec(compile(ast.Module(body=[node],type_ignores=[]),str(source),'exec'),namespace)

def check(enabled, service, command, payload_override=False):
    payload = {'SERVICE_HIDDEN':service,'COMMAND_HIDDEN':command} if payload_override is False else payload_override
    namespace.update(maintenance_fixture=enabled, request=SimpleNamespace(
        method='POST',path='/indi-allsky/ajax/system',get_json=lambda **kw:payload))
    return namespace['restrict_sandbox_effects']()

for command in ('backup_db','expire_data','validate_db','flush_images','flush_16min_images','flush_timelapses','flush_daytime'):
    assert check(True,'system',command) is None
    assert check(False,'system',command)[1] == 409
    assert check(True,'other',command)[1] == 409
assert check(True,'capture.service','hup') is None
assert check(False,'capture.service','hup')[1] == 409
for command in ('start','stop','restart','enable','disable','reboot','poweroff','invalid'):
    for service in ('system','capture.service','indi.service','gunicorn.service'):
        assert check(True,service,command)[1] == 409
for payload in (None,[],{},'invalid'):
    assert check(True,'system','backup_db',payload)[1] == 409
print('Browser maintenance guard: opt-in only, exact service/command pairs, malformed payloads and all service/power commands blocked: PASS')
