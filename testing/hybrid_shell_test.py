#!/usr/bin/env python3
"""Render the independent shells and guard their pre-split DOM contracts."""

import hashlib
from html.parser import HTMLParser
import json
import re
from pathlib import Path
from types import SimpleNamespace

from jinja2 import ChoiceLoader, DictLoader, Environment, FileSystemLoader, meta


ROOT = Path(__file__).resolve().parents[1]
TEMPLATES = ROOT / 'indi_allsky/flask/templates'


class BodyContract(HTMLParser):
    def __init__(self):
        super().__init__()
        self.in_body = False
        self.tokens = []
        self.assets = []

    def handle_starttag(self, tag, attrs):
        if tag == 'body':
            self.in_body = True
        if self.in_body:
            self.tokens.append(('start', tag, attrs))
        elif tag in ('script', 'link'):
            self.assets.append((tag, attrs))

    def handle_endtag(self, tag):
        if self.in_body:
            self.tokens.append(('end', tag))
        if tag == 'body':
            self.in_body = False

    def handle_data(self, data):
        if self.in_body and data.strip():
            self.tokens.append(('text', data.strip()))


def shell_contract(shell, modern, authenticated, original_source=None):
    overrides = {
        'probe.html': "{% extends 'shell.html' %}{% block title %}Probe{% endblock %}"
        "{% block content %}<p id='probe'>Content exactly once</p>{% endblock %}",
        'shell.html': original_source or "{% extends '" + shell + "' %}",
    }
    env = Environment(loader=ChoiceLoader([DictLoader(overrides), FileSystemLoader(TEMPLATES)]))
    env.globals.update({
        'url_for': lambda endpoint, **kwargs: endpoint + '?' + json.dumps(kwargs, sort_keys=True),
        'csrf_token': lambda: 'test-csrf-token',
    })
    html = env.get_template('probe.html').render(
        request=SimpleNamespace(endpoint='indi_allsky.modern_admin_now_view' if modern else 'indi_allsky.index_view'),
        current_user=SimpleNamespace(is_authenticated=authenticated, is_admin=authenticated),
        session={'admin_mode': 'modern' if modern else 'classic'},
        form_camera_select=SimpleNamespace(CAMERA_SELECT=lambda **kwargs: '<select></select>'),
        camera_id=2, camera_count=2,
    )
    assert html.count("<p id='probe'>Content exactly once</p>") == 1
    if modern:
        # Intentional addition: authentication navigation. Preserve all older
        # shell fingerprints after verifying this new section separately.
        account = re.search(r'<div class="hybrid-drawer-section" data-hybrid-account-navigation>(.*?)</div>', html, re.S)
        assert account is not None
        if authenticated:
            assert 'indi_allsky.modern_admin_account_view' in account[1]
            assert 'auth_indi_allsky.logout_view' in account[1]
            assert 'auth_indi_allsky.login_view' not in account[1]
        else:
            assert 'auth_indi_allsky.login_view' in account[1]
            assert 'indi_allsky.modern_admin_account_view' not in account[1]
        html = html[:account.start()] + html[account.end():]
    parser = BodyContract()
    parser.feed(html)
    contract = json.dumps((parser.tokens, parser.assets), sort_keys=True)
    return hashlib.sha256(contract.encode()).hexdigest()


def test_shell_dom_parity():
    # Baselines rendered from base.html at 17c5a322, before the shell split.
    expected = {
        (False, False): 'da24764ffdc54509edae10c1475666dc2ebe6808599afddbbe9fa65426a46010',
        (False, True): '5231472cc413795e3f2b4c2a380db4bc0f7a8205a9e092569f76999d806383fc',
        (True, False): '166b531237b08be4d9ff6414b65b1367bcbc4f1b532d07ed4bcc4386f22ab8da',
        (True, True): '166b531237b08be4d9ff6414b65b1367bcbc4f1b532d07ed4bcc4386f22ab8da',
    }
    for (modern, authenticated), fingerprint in expected.items():
        shell = 'modern_admin/base.html' if modern else 'base.html'
        assert shell_contract(shell, modern, authenticated) == fingerprint, (modern, authenticated)


def test_hybrid_templates_never_load_classic_shell():
    env = Environment(loader=FileSystemLoader(TEMPLATES))
    checked = set()
    pending = [str(path.relative_to(TEMPLATES)) for path in (TEMPLATES / 'modern_admin').glob('*.html')]
    while pending:
        name = pending.pop()
        if name in checked:
            continue
        checked.add(name)
        assert name.startswith(('modern_admin/', 'shared/')), name
        tree = env.parse((TEMPLATES / name).read_text())
        for dependency in meta.find_referenced_templates(tree):
            assert dependency is not None, 'Dynamic template dependency needs an explicit allowlist: ' + name
            pending.append(dependency)
    assert 'shared/document.html' in checked
    assert 'base.html' not in checked
    shell = (TEMPLATES / 'modern_admin/base.html').read_text()
    assert 'admin-mode-switch-classic' not in shell
    assert 'admin_nav_url' not in shell


if __name__ == '__main__':
    test_shell_dom_parity()
    test_hybrid_templates_never_load_classic_shell()
    print('Independent Hybrid shell checks passed')
