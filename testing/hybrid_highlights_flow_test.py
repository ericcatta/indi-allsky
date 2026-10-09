#!/usr/bin/env python3
"""Real ranked image metadata, empty/error states and exact Moment targets."""
from datetime import datetime
import html
import re
from unittest.mock import patch
from hybrid_runtime_fixture import isolated_app, login_client
from hybrid_generation_fixture import seed_generation
from hybrid_archive_fixture import seed_archive
from hybrid_source_media_fixture import seed_source_media


def ids(response):
    assert response.status_code==200,response.text[:500]
    return [int(value) for value in re.findall(r'data-archive-id="(\d+)"',response.text)]


def run():
    with isolated_app(multi_camera=True) as app:
        seed_generation(app);seed_archive(app);seed_source_media(app)
        from indi_allsky.flask import db
        from indi_allsky.flask.models import IndiAllSkyDbImageTable as Image, IndiAllSkyDbCameraTable as Camera, IndiAllSkyDbFitsImageTable as Fits, IndiAllSkyDbRawImageTable as Raw
        from indi_allsky.flask.media_archive import ModernAdminMediaArchive
        from sqlalchemy.exc import SQLAlchemyError
        with app.app_context():
            Image.query.update({'detections':0,'stars':0,'sqm':0})
            db.session.get(Image,100).detections=10
            db.session.get(Image,101).stars=999
            db.session.get(Image,100).createDate=datetime(2026,1,1,12,0,0)
            db.session.get(Image,101).createDate=datetime(2026,1,1,12,1,0)
            for model in (Fits, Raw):
                db.session.get(model,1).createDate=db.session.get(Image,100).createDate
                # Same time as another camera-1 image must not cross camera scope.
                db.session.get(model,2).createDate=db.session.get(Image,101).createDate
            db.session.commit()
        endpoint='/indi-allsky/modern-admin/highlights'
        for uid in (1,2):
            client=login_client(app,uid)
            response=client.get(endpoint+'?camera_id=1&profile_id=test-profile-1')
            assert len(ids(response))==8 and ids(response)[:2]==[100,101]
            assert set(re.findall(r'data-camera-id="(\d+)"',response.text))=={'1'}
            assert 'Download original' not in response.text
            assert 'Download processed JPEG' in response.text
            cards = re.findall(r'<article.*?</article>', response.text, re.S)
            for kind in ('fits', 'raw'):
                target='/indi-allsky/modern-admin/media/%s/1/1/download' % kind
                assert target in cards[0]
                delivered=client.get(target)
                assert delivered.status_code==200 and len(delivered.data)>100
                assert 'attachment;' in delivered.headers['Content-Disposition']
                assert '/media/%s/' % kind not in cards[1]
            assert 'FITS unavailable for this exposure.' in cards[1]
            detail = client.get('/indi-allsky/modern-admin/media/images/100?camera_id=1')
            assert detail.status_code == 200 and 'Download processed JPEG' in detail.text
            for kind in ('fits', 'raw'):
                assert '/media/%s/1/1/download' % kind in detail.text
            other_detail = client.get('/indi-allsky/modern-admin/media/images/101?camera_id=1')
            assert '/media/fits/' not in other_detail.text and '/media/raw/' not in other_detail.text

            # Library and archive must offer the same exact-exposure originals,
            # rather than calling the processed JPEG an original.
            for archive in ('library', 'media/archive'):
                base = '/indi-allsky/modern-admin/' + archive
                page = client.get(base + '?camera_id=1&search=archive-image-100.jpg')
                assert ids(page) == [100]
                assert 'Download processed JPEG' in page.text
                for kind in ('fits', 'raw'):
                    target = '/indi-allsky/modern-admin/media/%s/1/1/download' % kind
                    assert target in page.text and 'Download original ' + kind.upper() in page.text
                    original = client.get(target)
                    assert original.status_code == 200 and len(original.data) > 100
                    assert 'attachment;' in original.headers['Content-Disposition']
                other = client.get(base + '?camera_id=1&search=archive-image-101.jpg')
                assert ids(other) == [101]
                assert '/media/fits/' not in other.text and '/media/raw/' not in other.text
                assert 'FITS unavailable for this exposure.' in other.text

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
        with app.app_context():
            original=db.session.get(Fits,1)
            db.session.add(Fits(id=9,camera_id=1,filename=original.filename+'.duplicate',
                createDate=original.createDate,dayDate=original.dayDate,exposure=original.exposure,
                gain=original.gain,night=original.night))
            db.session.commit()
        ambiguous=client.get(endpoint+'?camera_id=1').text
        first=re.findall(r'<article.*?</article>',ambiguous,re.S)[0]
        assert '/media/fits/' not in first and '/media/raw/1/1/download' in first
        detail = client.get('/indi-allsky/modern-admin/media/images/100?camera_id=1')
        assert '/media/fits/' not in detail.text and '/media/raw/1/1/download' in detail.text
        for archive in ('library', 'media/archive'):
            ambiguous = client.get('/indi-allsky/modern-admin/' + archive +
                                   '?camera_id=1&search=archive-image-100.jpg')
            assert ids(ambiguous) == [100]
            assert '/media/fits/' not in ambiguous.text
            assert '/media/raw/1/1/download' in ambiguous.text
        with app.app_context():Image.query.delete();db.session.commit()
        response=client.get(endpoint)
        assert not ids(response) and 'No saved images are available' in response.text
        assert 'Possible meteor' not in response.text and 'placeholder' not in response.text.lower()
        print('Highlights/Moment: actual rank and limit, camera/profile isolation, exact image links, roles, empty/error and media policy: PASS')


if __name__=='__main__':run()
