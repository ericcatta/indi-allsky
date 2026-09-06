#!/usr/bin/env python3
"""Gallery/list camera selection, owner policy and pagination against real Flask."""
import argparse
import re
from unittest.mock import patch
from hybrid_runtime_fixture import isolated_app, login_client
from hybrid_generation_fixture import seed_generation
from hybrid_archive_fixture import seed_archive


def run(runtime_config):
    with isolated_app(runtime_config, multi_camera=True) as app:
        seed_generation(app); seed_archive(app)
        from indi_allsky.flask import db, views
        from indi_allsky.flask.models import IndiAllSkyDbCameraTable, IndiAllSkyDbImageTable
        from sqlalchemy.exc import SQLAlchemyError
        gallery='/indi-allsky/modern-admin/media/gallery'
        images='/indi-allsky/modern-admin/media/images'
        page=gallery+'/page'
        for uid in (1,2):
            client=login_client(app,uid)
            for route in (gallery,images,page):
                for query in ('profile_id=unknown','camera_id=bad','camera_id=-1',
                              'camera_id=1&profile_id=test-profile-2'):
                    assert client.get(route+'?'+query).status_code==400,(route,query)
                assert client.get(route+'?camera_id=9999').status_code==404
            response=client.get(page+'?profile_id=test-profile-2')
            assert response.status_code==200
            assert {item['camera_id'] for item in response.json['images']}=={2}
            initial=client.get(gallery+'?camera_id=1')
            assert 'data-gallery-has-more="true"' in initial.text
            assert len(re.findall(r'data-media-id="[0-9]+"', initial.text)) == 72
            response=client.get(page+'?camera_id=1&limit=72')
            assert len(response.json['images'])==72 and response.json['has_more']
            first={item['id'] for item in response.json['images']}
            cursor=response.json['next_cursor']
            second=client.get(page+'?camera_id=1&limit=72&before_id='+str(cursor))
            assert len(second.json['images'])==39 and not second.json['has_more']
            assert not first.intersection(item['id'] for item in second.json['images'])
        client=login_client(app,2)
        with app.app_context():
            cam=db.session.get(IndiAllSkyDbCameraTable,2)
            cam.web_nonlocal_images=True; cam.web_local_images_admin=False
            cam.s3_prefix='https://camera-two.example.invalid'
            db.session.commit()
        # Session camera 1 must never grant local file access to camera 2.
        with client.session_transaction() as session:
            session['camera_id']=1
        response=client.get(page+'?camera_id=2')
        item=response.json['images'][0]
        assert item['url'] is None and item['preview_url'] is None,item
        response=client.get(images+'?camera_id=2')
        assert response.status_code==200 and 'src="/indi-allsky/images/generation-camera-2.jpg"' not in response.text
        with app.app_context():
            entry=db.session.get(IndiAllSkyDbImageTable,2)
            entry.s3_key='camera-two.jpg';db.session.commit()
        item=client.get(page+'?camera_id=2').json['images'][0]
        assert item['url']=='https://camera-two.example.invalid/camera-two.jpg',item
        # Selecting restricted camera 2 must not hide local camera 1 records.
        with client.session_transaction() as session:
            session['camera_id']=2
        item=client.get(page+'?camera_id=1&limit=1').json['images'][0]
        assert item['url'].startswith('/indi-allsky/images/'),item
        for cls,route in ((views.ModernAdminMediaImagesView,images),(views.ModernAdminMediaGalleryView,gallery)):
            with patch.object(cls,'get_media_entries',side_effect=SQLAlchemyError('private database error')):
                response=client.get(route)
                assert 'The media list could not be loaded' in response.text
                assert 'No media found' not in response.text and 'private database error' not in response.text
        print('Hybrid gallery: strict selections, camera-owned local/remote URLs, two roles, pagination and provider failures: PASS')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--runtime-config',default='/etc/indi-allsky/flask.json')
    run(parser.parse_args().runtime_config)
