#!/usr/bin/env python3
"""Real ranked image metadata, empty/error states and exact Moment targets."""
import html
import re
from unittest.mock import patch
from hybrid_runtime_fixture import isolated_app, login_client
from hybrid_generation_fixture import seed_generation
from hybrid_archive_fixture import seed_archive


def ids(response):
    assert response.status_code==200,response.text[:500]
    return [int(value) for value in re.findall(r'data-archive-id="(\d+)"',response.text)]


def run():
    with isolated_app(multi_camera=True) as app:
        seed_generation(app);seed_archive(app)
        from indi_allsky.flask import db
        from indi_allsky.flask.models import IndiAllSkyDbImageTable as Image, IndiAllSkyDbCameraTable as Camera
        from indi_allsky.flask.media_archive import ModernAdminMediaArchive
        from sqlalchemy.exc import SQLAlchemyError
        with app.app_context():
            Image.query.update({'detections':0,'stars':0,'sqm':0})
            db.session.get(Image,100).detections=10
            db.session.get(Image,101).stars=999
            db.session.commit()
        endpoint='/indi-allsky/modern-admin/highlights'
        for uid in (1,2):
            client=login_client(app,uid)
            response=client.get(endpoint+'?camera_id=1&profile_id=test-profile-1')
            assert len(ids(response))==8 and ids(response)[:2]==[100,101]
            assert set(re.findall(r'data-camera-id="(\d+)"',response.text))=={'1'}
            for href in re.findall(r'href="([^"]+)"\s*>Inspect image</a>',response.text):
                detail=client.get(html.unescape(href))
                assert detail.status_code==302 and 'camera_id=1' in detail.location and 'profile_id=test-profile-1' in detail.location
                assert client.get(detail.location).status_code==200
            assert ids(client.get(endpoint+'?profile_id=test-profile-2'))==[2]
            for route in ('highlights','moment'):
                assert client.get('/indi-allsky/modern-admin/'+route+'?camera_id=1&profile_id=test-profile-2').status_code==400
                assert client.get('/indi-allsky/modern-admin/'+route+'?profile_id=unknown').status_code==400
            assert client.get('/indi-allsky/modern-admin/moment?id=100&camera_id=2').status_code==404
            assert client.get('/indi-allsky/modern-admin/moment?id=bad').status_code==400
            assert client.get('/indi-allsky/modern-admin/moment?id=9999').status_code==404
            picker=client.get('/indi-allsky/modern-admin/moment?profile_id=test-profile-2')
            assert picker.status_code==302 and '/library?' in picker.location and 'profile_id=test-profile-2' in picker.location
        assert app.test_client().get(endpoint).status_code==302
        assert app.test_client().get('/indi-allsky/modern-admin/moment').status_code==302
        with patch.object(ModernAdminMediaArchive,'item',side_effect=SQLAlchemyError('private details')):
            response=client.get(endpoint)
            assert 'Image metadata could not be loaded' in response.text and 'private details' not in response.text
            assert 'No saved images' not in response.text and not ids(response)
        with app.app_context():
            camera=db.session.get(Camera,2);camera.web_nonlocal_images=True;camera.web_local_images_admin=False
            db.session.commit()
        assert 'No browser preview is available' in client.get(endpoint+'?camera_id=2').text
        with app.app_context():Image.query.delete();db.session.commit()
        response=client.get(endpoint)
        assert not ids(response) and 'No saved images are available' in response.text
        assert 'Possible meteor' not in response.text and 'placeholder' not in response.text.lower()
        print('Highlights/Moment: actual rank and limit, camera/profile isolation, exact image links, roles, empty/error and media policy: PASS')


if __name__=='__main__':run()
