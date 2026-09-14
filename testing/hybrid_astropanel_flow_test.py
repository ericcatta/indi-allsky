#!/usr/bin/env python3
"""Real ephemeris response and Hybrid detail contract, without Classic imports."""
import re
import ast
import hashlib
from pathlib import Path
from unittest.mock import patch
from sqlalchemy.exc import SQLAlchemyError
from hybrid_runtime_fixture import isolated_app, login_client


FINGERPRINTS = {'get': '8f3119781c7c11630a26fdd3aaf4aba3506aa4af802e7e91597b4a1407cca17b', 'astropanel_get_moon_phase': 'ff79bfbca7b8a5a69fcbccc5b9c739ecf3d750d4a56deeb384fa3ca36be3d88e', 'astropanel_get_body_positions': '608db8d84a6231cb5a2aa3ece9ccb6aaf028dfeef3d2cec03e6aa3806a31794f', 'astropanel_get_sun_twilights': 'f25590f74f5eeedc3215927c70bac59b7bad10ab4a0238bcfcd706836f7b23d9', 'astropanel_get_polaris_data': '7856057c333d21a87f17202bbb9dc770e906be09a64280aa170f96a91f3b03eb'}


def run():
    # Five calculation methods captured before extraction from e27fa1bb.
    path=Path(__file__).resolve().parents[1]/"indi_allsky/flask/astropanel_views.py"
    tree=ast.parse(path.read_text())
    owner=next(n for n in tree.body if isinstance(n,ast.ClassDef))
    for method in owner.body:
        if isinstance(method,ast.FunctionDef) and method.name in FINGERPRINTS:
            assert hashlib.sha256(ast.dump(method,include_attributes=False).encode()).hexdigest()==FINGERPRINTS[method.name]
    assert not any(isinstance(n,ast.ImportFrom) and n.module in ("views","classic_views") for n in ast.walk(tree))
    with isolated_app(multi_camera=True) as app:
        for uid in (1, 2):
            client = login_client(app, uid)
            for cid in (1, 2):
                page = client.get('/indi-allsky/modern-admin/observatory/astropanel', query_string={'camera_id':cid})
                assert page.status_code == 200
                assert 'modern_admin/astropanel.js' in page.text
                assert 'id="astropanel-refresh"' in page.text
                assert 'aria-label="Astropanel camera"' in page.text
                from html.parser import HTMLParser
                class CameraLinks(HTMLParser):
                    active = False
                    links = []
                    def handle_starttag(self, tag, attrs):
                        attrs = dict(attrs)
                        if tag == 'nav':
                            self.active = attrs.get('aria-label') == 'Astropanel camera'
                        elif tag == 'a' and self.active:
                            self.links.append(attrs)
                    def handle_endtag(self, tag):
                        if tag == 'nav':
                            self.active = False
                choices = CameraLinks(); choices.links = []; choices.feed(page.text)
                assert len(choices.links) == 2
                for other, link in enumerate(choices.links, 1):
                    assert 'camera_id=' + str(other) in link['href']
                    assert 'profile_id=test-profile-' + str(other) in link['href']
                    assert (link.get('aria-current') == 'page') == (other == cid)
                    selected = client.get(link['href'])
                    assert selected.status_code == 200 and 'data-camera="' + str(other) + '"' in selected.text
                for bad in ({'camera_id':'bad'}, {'camera_id':cid,'profile_id':'test-profile-'+str(3-cid)}, {'profile_id':'missing'}):
                    assert client.get('/indi-allsky/modern-admin/observatory/astropanel',query_string=bad).status_code == 400

                response = client.get('/indi-allsky/ajax/astropanel', query_string={'camera_id':cid})
                assert response.status_code == 200, response.text[:500]
                data = response.json
                for key in re.findall('data-astro-field="([^"]+)"', page.text):
                    assert key in data and isinstance(data[key], (int, float, str)), key
                assert data['satellite_list'] == []
                assert isinstance(data['polaris_hour_angle'], (int,float))
                for planet in ('mercury','venus','mars','jupiter','saturn','uranus','neptune'):
                    for suffix in ('rise','transit','set','alt','az'):
                        assert planet+'_'+suffix in data
        from indi_allsky.flask.astropanel_views import AjaxAstroPanelView
        for client in (app.test_client(),login_client(app,1),login_client(app,2)):
            endpoint='/indi-allsky/ajax/astropanel'
            for value in (None,'','bad','0','-1','1.5',str(2**63)):
                response=client.get(endpoint,query_string={} if value is None else {'camera_id':value})
                assert response.status_code==400 and response.json['message']=='A valid camera_id is required.'
            response=client.get(endpoint,query_string={'camera_id':999999})
            assert response.status_code==404 and response.json['message']=='Camera not found.'
            with patch.object(AjaxAstroPanelView,'get',side_effect=SQLAlchemyError('private provider details')):
                response=client.get(endpoint,query_string={'camera_id':1})
                assert response.status_code==503 and 'private provider details' not in response.text
            assert client.get(endpoint,query_string={'camera_id':1}).status_code==200
        assert app.test_client().get('/indi-allsky/modern-admin/observatory/astropanel').status_code == 302
        print('Astropanel: actual ephemerides, all new detail fields, both cameras/roles, no satellites and Classic disabled: PASS')


if __name__ == '__main__':
    run()
