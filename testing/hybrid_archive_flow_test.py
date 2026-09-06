#!/usr/bin/env python3
"""Whole archive navigation, per-record file access and stable keyset pagination."""
import argparse
import html
import re
from datetime import datetime
from unittest.mock import patch
from hybrid_runtime_fixture import isolated_app, login_client
from hybrid_generation_fixture import seed_generation
from hybrid_source_media_fixture import seed_source_media
from hybrid_generated_media_fixture import seed_generated_media
from hybrid_archive_fixture import seed_archive


def ids(response):
    assert response.status_code==200,response.text[:500]
    return [int(i) for i in re.findall(r'data-archive-id="(\d+)"',response.text)]


def link(response, direction):
    match=re.search(r'rel="'+direction+r'" href="([^"]+)"',response.text)
    return html.unescape(match[1]) if match else None


def run(runtime_config, entrypoint='archive'):
    with isolated_app(runtime_config,multi_camera=True) as app:
        seed_generation(app);seed_source_media(app);seed_generated_media(app);seed_archive(app)
        from indi_allsky.flask import db
        from indi_allsky.flask.media_archive import ModernAdminMediaArchive, KINDS
        from indi_allsky.flask.models import IndiAllSkyDbImageTable, IndiAllSkyDbCameraTable
        from sqlalchemy.exc import SQLAlchemyError
        user,admin=login_client(app,2),login_client(app,1)
        route='/indi-allsky/modern-admin/'+('library' if entrypoint=='library' else 'media/archive')
        for client in (user,admin):
            for family in ('images','timelapses'):
                detail='/indi-allsky/modern-admin/media/'+family+'/2'
                response=client.get(detail+'?camera_id=2&profile_id=test-profile-2')
                assert response.status_code==200 and 'var camera_id = 2;' in response.text
                assert 'profile_id=test-profile-2' in response.text
                assert client.get(detail+'?camera_id=1').status_code==404
                assert client.get(detail+'?profile_id=test-profile-1').status_code==404
                for query in ('camera_id=bad','profile_id=unknown','camera_id=2&profile_id=test-profile-1'):
                    assert client.get(detail+'?'+query).status_code==400
                assert 'var camera_id = 2;' in client.get(detail).text
            for kind in KINDS:
                for cid in (1,2):
                    page=client.get(route,query_string=dict(kind=kind,camera_id=cid,profile_id='test-profile-'+str(cid)))
                    assert ids(page),(kind,cid,page.status_code)
                    assert set(re.findall(r'data-camera-id="(\d+)"',page.text))=={str(cid)}
                    if link(page,'next'):
                        assert link(page,'next').split('?')[0]==route
                        assert 'profile_id=test-profile-'+str(cid) in link(page,'next')
                    assert ('<h1>Library</h1>' if entrypoint=='library' else '<h1>Media archive</h1>') in page.text
                    for href in re.findall(r'href="([^"]+/download)"',page.text):
                        response=client.get(html.unescape(href))
                        assert response.status_code==200 and response.data
        first=user.get(route+'?kind=image&camera_id=1')
        first_ids=ids(first)
        assert len(first_ids)==48 and first_ids[:3]==[1,209,208]
        assert link(first,'next').split('?')[0]==route
        second=user.get(link(first,'next')); second_ids=ids(second)
        assert len(second_ids)==48 and not set(first_ids)&set(second_ids)
        assert ids(user.get(link(second,'prev')))==first_ids
        third=user.get(link(second,'next'))
        assert len(ids(third))==15 and not link(third,'next')
        assert len(set(first_ids+second_ids+ids(third)))==111
        assert ids(user.get(link(third,'prev')))==second_ids
        oldest=user.get(route+'?camera_id=1&sort=oldest')
        assert ids(oldest)[:3]==[100,101,102]
        assert ids(user.get(link(user.get(link(oldest,'next')),'prev')))==ids(oldest)
        filtered=user.get(route,query_string=dict(kind='image',camera_id=1,start='2024-01-01',end='2024-01-01',period='night',uploaded='yes'))
        assert ids(filtered)==list(reversed([i for i in range(100,210) if i%2==0 and i%3==0]))
        assert ids(user.get(route+'?camera_id=1&search=archive-image-100.jpg'))==[100]
        assert ids(user.get(route+'?camera_id=1&search=%25'))==[] # '%' is literal, not a wildcard.
        assert ids(user.get(route+'?kind=image&camera_id=2'))==[2]
        assert ids(user.get(route+'?camera_id=1&start=1900-01-01&end=1900-01-02'))==[]
        for query in ('camera_id=bad','cursor=2024-01-01%7C99999999999999999999999999999999','kind=bad','camera_id=1&profile_id=test-profile-2','profile_id=bad','start=bad','start=2025-01-01&end=2024-01-01','sort=bad','cursor=bad','cursor=2024-01-01T00:00:00%2B01:00%7C1'):
            assert user.get(route+'?'+query).status_code==400,query
        assert user.get(route+'?camera_id=9999').status_code==404
        assert app.test_client().get(route).status_code==302
        with patch.object(ModernAdminMediaArchive,'query',side_effect=SQLAlchemyError('sensitive backend error')):
            failure=user.get(route)
            assert 'The media archive could not be loaded' in failure.text
            assert 'No media match' not in failure.text and 'sensitive backend error' not in failure.text
        # Cursor positions survive deletion of their anchor; no OFFSET shifts.
        with app.app_context():
            anchor=db.session.get(IndiAllSkyDbImageTable,first_ids[-1])
            db.session.delete(anchor)
            db.session.commit()
        assert ids(user.get(link(first,'next')))==second_ids
        with app.app_context():
            db.session.add(IndiAllSkyDbImageTable(id=3000,camera_id=1,filename='newly-arrived.jpg',
                createDate=datetime(2027,1,1),dayDate=datetime(2027,1,1).date(),exposure=.5,gain=10,adu=.1,data={}))
            db.session.commit()
        assert ids(user.get(link(first,'next')))==second_ids
        with app.app_context():
            camera=db.session.get(IndiAllSkyDbCameraTable,2)
            camera.web_nonlocal_images=True;camera.web_local_images_admin=False
            db.session.commit()
        restricted=user.get(route+'?kind=image&camera_id=2')
        assert 'No browser preview is available' in restricted.text
        assert 'src="/indi-allsky/images/generation-camera-2.jpg"' not in restricted.text
        for url in ('/indi-allsky/modern-admin/media/timelapses/2','/indi-allsky/modern-admin/media/images/2'):
            page=user.get(url)
            assert page.status_code==200 and 'Open legacy' not in page.text
        print('Hybrid complete archive: ten types, both cameras/roles, 111 records, forward/backward/sort, date/upload/name filters, cursor deletion, errors, downloads and remote policy: PASS')

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--runtime-config',default='/etc/indi-allsky/flask.json')
    parser.add_argument('--entrypoint',choices=('archive','library'),default='archive')
    args=parser.parse_args()
    run(args.runtime_config,args.entrypoint)
