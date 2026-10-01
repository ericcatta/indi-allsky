#!/usr/bin/env python3
"""List/detail/return navigation preserves explicit camera and profile scope."""
from datetime import datetime
from flask import template_rendered
from html.parser import HTMLParser
from urllib.parse import parse_qs, urlsplit

from hybrid_runtime_fixture import isolated_app, login_client


class Links(HTMLParser):
    def __init__(self, html):
        super().__init__()
        self.urls = []
        self.entries = []
        self.active = None
        self.feed(html)

    def handle_starttag(self, tag, attrs):
        if tag == 'a':
            self.urls.append(dict(attrs).get('href', ''))
            self.active = {'url': self.urls[-1], 'label': ''}
            self.entries.append(self.active)

    def handle_data(self, value):
        if self.active is not None:
            self.active['label'] += value

    def handle_endtag(self, tag):
        if tag == 'a':
            self.active = None


def run():
    with isolated_app(multi_camera=True) as app:
        from indi_allsky.flask import db, models
        with app.app_context():
            for camera in (1, 2):
                for family in ('Image', 'Video'):
                    model = getattr(models, 'IndiAllSkyDb' + family + 'Table')
                    values = dict(id=camera, camera_id=camera, filename=f'{family}{camera}.jpg',
                                  createDate=datetime.now(), dayDate=datetime.now().date(),
                                  night=False, exposure=1, gain=1, adu=1, success=True, data={})
                    db.session.add(model(**{k: v for k, v in values.items() if k in model.__table__.columns}))
            db.session.commit()
        for user in (1, 2):
            client = login_client(app, user)
            for camera in (1, 2):
                scope = {'camera_id': [str(camera)], 'profile_id': [f'test-profile-{camera}']}
                for family in ('images', 'timelapses'):
                    base = '/indi-allsky/modern-admin/media/' + family
                    page = client.get(base + f'?camera_id={camera}&profile_id=test-profile-{camera}')
                    assert page.status_code == 200
                    links = [u for u in Links(page.text).urls if urlsplit(u).path == base + '/' + str(camera)]
                    assert len(links) == 1, (family, camera, links)
                    assert parse_qs(urlsplit(links[0]).query) == scope, links
                    detail = client.get(links[0])
                    assert detail.status_code == 200
                    returns = [u for u in Links(detail.text).urls if urlsplit(u).path == base]
                    assert any(parse_qs(urlsplit(u).query) == scope for u in returns), returns
                    wrong = client.get(base + f'/{3-camera}?camera_id={camera}&profile_id=test-profile-{camera}')
                    assert wrong.status_code == 404
                keograms = client.get('/indi-allsky/modern-admin/media/keograms',
                                      query_string={'camera_id': camera, 'profile_id': f'test-profile-{camera}'})
                assert keograms.status_code == 200
                entries = Links(keograms.text).entries
                for label, context_key in (('Open Realtime Keogram', 'realtime_camera_id'),
                                           ('Open Long Term Keogram', 'longterm_camera_id')):
                    link = next(e['url'] for e in entries if e['label'].strip() == label)
                    assert parse_qs(urlsplit(link).query) == scope, (label, link)
                    contexts = []
                    def rendered(sender, template, context, **extra):
                        contexts.append(context)
                    with template_rendered.connected_to(rendered, app):
                        destination = client.get(link)
                    assert destination.status_code == 200
                    assert contexts[-1][context_key] == camera
    print('Media list/detail/return: both roles and cameras preserve profile; wrong camera rejected: PASS')


if __name__ == '__main__':
    run()
