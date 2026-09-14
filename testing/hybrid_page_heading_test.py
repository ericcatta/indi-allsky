#!/usr/bin/env python3
"""Render actual page heading declarations and their shared Hybrid partial."""
from html.parser import HTMLParser
from pathlib import Path
import re

from jinja2 import ChainableUndefined, Environment, FileSystemLoader

ROOT = Path(__file__).resolve().parents[1]
TEMPLATES = ROOT / 'indi_allsky/flask/templates'
INCLUDE = "{% include 'modern_admin/_shell_header.html' %}"


class Headings(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids = []
        self.labels = []
        self.headings = []
        self.in_heading = False

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if 'id' in attrs:
            self.ids.append(attrs['id'])
        if tag == 'main':
            self.labels.extend(attrs.get('aria-labelledby', '').split())
        if tag == 'h1':
            self.headings.append([attrs.get('id'), ''])
            self.in_heading = True

    def handle_endtag(self, tag):
        if tag == 'h1':
            self.in_heading = False

    def handle_data(self, text):
        if self.in_heading:
            self.headings[-1][1] += text


def run():
    env = Environment(loader=FileSystemLoader(TEMPLATES), autoescape=True,
                      undefined=ChainableUndefined)
    env.globals['url_for'] = lambda endpoint, **kwargs: '/test/' + endpoint
    env.globals['get_flashed_messages'] = lambda **kwargs: [('info', 'Saved successfully')]
    checked = []
    for path in sorted((TEMPLATES / 'modern_admin').glob('*.html')):
        source = path.read_text()
        if INCLUDE not in source:
            continue
        prefix, suffix = source.split(INCLUDE, 1)
        prefix = prefix.split('{% block content %}', 1)[1]
        # YouTube supplies its visible heading immediately after the partial.
        match = re.search(r'{% if is_hybrid_shell_ui %}<h1[^>]*>.*?</h1>{% endif %}', suffix, re.S)
        visible_heading = match[0] if match else ''
        html = env.from_string(prefix + INCLUDE + visible_heading + '</main>').render(
            is_hybrid_shell_ui=True, timestamp=1700000000, camera_id=1, refreshInterval=30,
            modern_admin_upload_provider_label='Test provider',
            modern_admin_section='Test media', modern_admin_log_label='Test log',
            modern_admin_safe_title='Test tool', settings_level_title='Basic',
        )
        parser = Headings()
        parser.feed(html)
        assert len(parser.headings) == 1, (path.name, parser.headings)
        heading_id, heading = parser.headings[0]
        assert heading.strip(), path.name
        assert heading_id in parser.labels, (path.name, parser.labels, heading_id)
        assert parser.ids.count(heading_id) == 1, path.name
        assert 'Saved successfully' in html, path.name
        checked.append(path.name)
    assert len(checked) >= 50, 'Heading coverage unexpectedly shrank'
    print(f'{len(checked)} actual page heading declarations: unique H1, resolved main label and flash messages PASS')


if __name__ == '__main__':
    run()
