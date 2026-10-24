#!/usr/bin/env python3
"""Render the hybrid UI without Flask and guard its navigation structure."""
from html.parser import HTMLParser
from pathlib import Path
from types import SimpleNamespace
from urllib.parse import parse_qs, urlencode, urlsplit

from jinja2 import Environment, FileSystemLoader


ROOT = Path(__file__).resolve().parents[1]
TEMPLATES = ROOT / 'indi_allsky' / 'flask' / 'templates'


class Node:
    def __init__(self, tag='root', attrs=()):
        self.tag = tag
        self.attrs = dict(attrs)
        self.children = []
        self.text_parts = []

    @property
    def text(self):
        return ''.join(self.text_parts + [child.text for child in self.children]).strip()

    def find_all(self, tag=None, **attrs):
        found = []
        if (tag is None or self.tag == tag) and all(self.attrs.get(key) == value for key, value in attrs.items()):
            found.append(self)
        for child in self.children:
            found.extend(child.find_all(tag, **attrs))
        return found


class TreeParser(HTMLParser):
    VOID = {'area', 'base', 'br', 'col', 'embed', 'hr', 'img', 'input', 'link', 'meta', 'source', 'track', 'wbr'}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.root = Node()
        self.stack = [self.root]

    def handle_starttag(self, tag, attrs):
        node = Node(tag, attrs)
        self.stack[-1].children.append(node)
        if tag not in self.VOID:
            self.stack.append(node)

    def handle_startendtag(self, tag, attrs):
        self.stack[-1].children.append(Node(tag, attrs))

    def handle_endtag(self, tag):
        for index in range(len(self.stack) - 1, 0, -1):
            if self.stack[index].tag == tag:
                del self.stack[index:]
                return

    def handle_data(self, data):
        self.stack[-1].text_parts.append(data)


def endpoint_path(endpoint, **values):
    query_values = {key: value for key, value in values.items() if value is not None and key not in ('filename', 'v')}
    query = urlencode(query_values, doseq=True)
    return '/endpoint/' + endpoint + (('?' + query) if query else '')


def render(template_name, endpoint, **context):
    environment = Environment(loader=FileSystemLoader(TEMPLATES), autoescape=True)
    environment.globals.update(
        url_for=endpoint_path,
        csrf_token=lambda: 'test-csrf-token',
        get_flashed_messages=lambda **kwargs: [],
    )
    defaults = {
        'website_title': 'Hybrid test',
        'page_title': 'Test page',
        'camera_id': 7,
        'config': {'LOGIN_DISABLED': False},
        'current_user': SimpleNamespace(is_authenticated=True, is_admin=True),
        'request': SimpleNamespace(endpoint=endpoint, args={'profile_id': 'north'}, full_path='/archive?kind=image'),
    }
    defaults.update(context)
    parser = TreeParser()
    parser.feed(environment.get_template(template_name).render(**defaults))
    return parser.root


def direct_links(node):
    return [item for item in node.find_all('a') if item.attrs.get('href')]


def link_label(link):
    strong = link.find_all('strong')
    return strong[0].text if strong else link.text.rstrip('›').strip()


def assert_global_navigation(root):
    navigation = root.find_all('nav', **{'aria-label': 'Main navigation'})
    assert len(navigation) == 1
    links = direct_links(navigation[0])
    assert [link.text for link in links] == [
        'Now', 'Highlights', 'Library', 'Observatory', 'Cameras', 'Settings', 'System',
    ]
    assert len(links) == 7
    assert not navigation[0].find_all('details')
    assert all('tool' not in link.text.lower() for link in links)


def test_hubs_and_global_navigation():
    settings = render('modern_admin/settings_inventory.html', 'indi_allsky.modern_admin_settings_view')
    system = render(
        'modern_admin/system.html',
        'indi_allsky.modern_admin_system_view',
        modern_admin_system_metrics=[],
    )
    for page in (settings, system):
        assert_global_navigation(page)

    settings_links = {link_label(link): link.attrs['href'] for link in direct_links(settings)}
    for label in ('Camera', 'Storage and archive', 'Video and timelapse', 'Analytics',
                  'Acquisition and save', 'FITS and source files', 'Full Settings',
                  'Config History', 'Restore Config'):
        assert label in settings_links
    assert 'Notifications' not in settings_links

    system_links = {link_label(link): link.attrs['href'] for link in direct_links(system)}
    for label in ('System Info', 'Support Info', 'Logs', 'Tasks', 'Notifications', 'Updates',
                  'Storage', 'Drives', 'Uploads', 'YouTube', 'Users', 'Network', 'GPIO Control'):
        assert label in system_links


def archive_context(**overrides):
    values = dict(kind='image', start='2026-10-01', end='2026-10-24', sort='oldest',
                  search='', period='', uploaded='')
    values.update(overrides)
    return {
        'archive_title': 'Archive',
        'archive_values': SimpleNamespace(**values),
        'archive_kinds': {'image': 'Images', 'video': 'Videos'},
        'modern_admin_media_camera_filters': [SimpleNamespace(camera_id=7, active=True, label='North')],
        'modern_admin_media_selected_filter': SimpleNamespace(camera_id=7, profile_id='north'),
        'modern_admin_media_selected_label': 'North',
        'archive_endpoint': 'indi_allsky.modern_admin_media_archive_view',
        'archive_scope': dict(kind='image', camera_id=7, profile_id='north', start='2026-10-01',
                              end='2026-10-24', sort='oldest', search=values['search'],
                              period=values['period'], uploaded=values['uploaded']),
        'archive': {'items': [], 'previous': 'prev-token', 'next': 'next-token'},
        'archive_error': None,
    }


def selected_value(form, name):
    controls = [node for node in form.find_all() if node.attrs.get('name') == name]
    assert len(controls) == 1, name
    control = controls[0]
    if control.tag == 'input':
        return control.attrs.get('value', '')
    selected = [option for option in control.find_all('option') if 'selected' in option.attrs]
    assert len(selected) <= 1, name
    option = selected[0] if selected else control.find_all('option')[0]
    return option.attrs.get('value', '')


def test_archive_filter_structure_and_scope():
    inactive = render('modern_admin/_media_archive_content.html', 'indi_allsky.modern_admin_media_archive_view',
                      **archive_context())
    form = inactive.find_all('form', id='hybrid-archive-filters')[0]
    for name, expected in {'kind': 'image', 'camera_id': '7', 'start': '2026-10-01',
                           'end': '2026-10-24', 'sort': 'oldest', 'search': '',
                           'period': '', 'uploaded': ''}.items():
        assert selected_value(form, name) == expected
    more = [node for node in form.find_all('details') if node.find_all('summary')[0].text == 'More filters'][0]
    assert 'open' not in more.attrs

    active = render('modern_admin/_media_archive_content.html', 'indi_allsky.modern_admin_media_archive_view',
                    **archive_context(search='meteor', period='night', uploaded='no'))
    active_form = active.find_all('form', id='hybrid-archive-filters')[0]
    active_more = active_form.find_all('details')[0]
    assert 'open' in active_more.attrs
    assert selected_value(active_form, 'search') == 'meteor'
    assert selected_value(active_form, 'period') == 'night'
    assert selected_value(active_form, 'uploaded') == 'no'

    reset = next(link for link in direct_links(active_form) if link.text == 'Reset filters')
    reset_query = parse_qs(urlsplit(reset.attrs['href']).query)
    assert reset_query == {'kind': ['image'], 'camera_id': ['7'], 'profile_id': ['north']}
    page_links = active.find_all('nav', **{'aria-label': 'Archive pages'})[0].find_all('a')
    for link in page_links:
        query = parse_qs(urlsplit(link.attrs['href']).query)
        assert query['camera_id'] == ['7'] and query['profile_id'] == ['north']
        assert query['search'] == ['meteor'] and query['period'] == ['night'] and query['uploaded'] == ['no']


def test_camera_tools_preserve_scope():
    camera = SimpleNamespace(
        id=7, profile_id='north', profile_mode=True, selected=True, badge='Running', name='North camera',
        driver='indi', enabled=True, role_badge='Primary', status='Running', last_image_age='5 seconds',
        settings_url='/settings?camera_id=7&profile_id=north',
        acquisition_url='/acquisition?camera_id=7&profile_id=north', gallery_url='/gallery?camera_id=7',
        switch_enabled=False,
    )
    multi_camera = SimpleNamespace(enabled=True, profiles=[], status_label='Enabled', mode_label='Multi-camera',
                                   enable_block_reason='', enable_allowed=True)
    page = render(
        'modern_admin/cameras.html', 'indi_allsky.modern_admin_cameras_view',
        modern_admin_cameras=[camera], modern_admin_multi_camera=multi_camera,
        modern_admin_can_manage_cameras=True, modern_admin_section_links=[],
        modern_admin_camera_switch_error=None, modern_admin_camera_switch_success=None,
        modern_admin_multi_camera_error=None, modern_admin_multi_camera_success=None,
    )
    tools = page.find_all('nav', **{'aria-label': 'Tools for North camera'})
    assert len(tools) == 1
    links = direct_links(tools[0])
    assert len(links) == 6
    for link in links:
        query = parse_qs(urlsplit(link.attrs['href']).query)
        assert query == {'camera_id': ['7'], 'profile_id': ['north']}, (link.text, query)


def run():
    test_hubs_and_global_navigation()
    test_archive_filter_structure_and_scope()
    test_camera_tools_preserve_scope()
    print('Hybrid UI structure: navigation hubs, archive filters and camera scope: PASS')


if __name__ == '__main__':
    run()
