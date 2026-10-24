#!/usr/bin/env python3
"""Guard the sole Hybrid shell DOM contract and retired frontend absence."""

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


def shell_contract(shell, modern, authenticated, original_source=None, endpoint_name=None):
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
        request=SimpleNamespace(endpoint=endpoint_name or ('indi_allsky.modern_admin_now_view' if modern else 'indi_allsky.index_view')),
        current_user=SimpleNamespace(is_authenticated=authenticated, is_admin=authenticated),
        session={'admin_mode': 'modern' if modern else 'classic'},
        config={'LOGIN_DISABLED': False},
        form_camera_select=SimpleNamespace(CAMERA_SELECT=lambda **kwargs: '<select></select>'),
        camera_id=2, camera_count=2,
    )
    assert html.count("<p id='probe'>Content exactly once</p>") == 1
    if modern:
        assert html.count('<meta name="viewport" content="width=device-width, initial-scale=1">') == 1
        assert html.count('hybrid-product-ui-shell-009') == 1
        assert 'Observation' in html and 'Management' in html
        assert 'aria-current="page"' in html
        assert 'hybrid-control-disclosure' in html
        assert 'Skip to content' in html
        assert '>Home</a>' not in html
        assert '>Moment</a>' not in html and '>Output</a>' not in html
        assert 'More tools' not in html
        assert html.count('class="hybrid-nav-icon"') == 7
        assert '⚙' not in html
        assert ('data-hybrid-system-command="reboot"' in html) == (endpoint_name == 'indi_allsky.modern_admin_system_view')
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
    for asset in ('css/style.css', 'js/indi-allsky-tabs.js'):
        assert (asset in html) == (not modern), asset
    contract = json.dumps((parser.tokens, parser.assets), sort_keys=True)
    return contract


def test_shell_dom_parity():
    assert not (TEMPLATES / 'base.html').exists()
    for authenticated in (False, True):
        shell_contract('modern_admin/base.html', True, authenticated)
        shell_contract('modern_admin/base.html', True, authenticated, endpoint_name='indi_allsky.modern_admin_system_view')


def test_navigation_detail_context():
    env = Environment(loader=FileSystemLoader(TEMPLATES))
    env.globals['url_for'] = lambda endpoint, **kwargs: endpoint
    expected = {
        'media_image_detail': 'library', 'output_detail': 'library',
        'sky_cycle': 'library', 'camera_info': 'cameras', 'image_circle_helper': 'cameras',
        'full_settings': 'settings', 'config_restore_detail': 'settings',
        'virtualsky': 'observatory', 'task_detail': 'system',
    }
    for page, section in expected.items():
        html = env.get_template('modern_admin/_shell_navigation.html').render(
            request=SimpleNamespace(endpoint='indi_allsky.modern_admin_' + page + '_view'),
            current_user=SimpleNamespace(is_authenticated=True),
        )
        active = re.findall(r'href="([^"]+)" aria-current="page"', html)
        assert active == ['indi_allsky.modern_admin_' + section + '_view'], (page, active)


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
    partial = (TEMPLATES / 'modern_admin/_shell_header.html').read_text()
    assert 'modern_admin_mode_view' not in partial
    assert 'data-modern-admin-system-command' not in partial
    assert 'get_flashed_messages' in partial


if __name__ == '__main__':
    test_shell_dom_parity()
    test_navigation_detail_context()
    test_hybrid_templates_never_load_classic_shell()
    print('Independent Hybrid shell checks passed')
