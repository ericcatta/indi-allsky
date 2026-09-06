#!/usr/bin/env python3
"""Public latest/view/download contracts with Classic views and templates forbidden."""
import argparse
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
from hybrid_runtime_fixture import isolated_app, login_client
from hybrid_generation_fixture import seed_generation
from hybrid_source_media_fixture import seed_source_media
from hybrid_generated_media_fixture import seed_generated_media
from hybrid_public_media_fixture import seed_public_media


def run(runtime_config):
    with isolated_app(runtime_config,multi_camera=True) as app:
        seed_generation(app);seed_source_media(app);seed_generated_media(app);seed_public_media(app)
        from indi_allsky.flask import db
        from indi_allsky.flask.models import IndiAllSkyDbCameraTable,IndiAllSkyDbImageTable,IndiAllSkyDbRawImageTable,IndiAllSkyDbConfigTable
        app.config.update(INDI_ALLSKY_AUTH_ALL_VIEWS=False,INDI_ALLSKY_AUTH_MEDIA_VIEWS=False)
        original_loader=app.jinja_env.loader.get_source
        def source(environment,template):
            assert template not in ('base.html','view_image.html','watch_video.html'),template
            return original_loader(environment,template)
        root=Path(app.config['INDI_ALLSKY_IMAGE_FOLDER'])
        mappings=[('image','image','view_image'),('timelapse','video','watch_timelapse'),('keogram','keogram','view_keogram'),
            ('startrail','startrail','view_startrail'),('panorama','panorama','view_panorama'),('raw','raw','view_raw'),
            ('startrailvideo','startrail-video','watch_startrail'),('panoramavideo','panorama-video','watch_panorama')]
        anonymous=app.test_client()
        clients=(anonymous,login_client(app,2),login_client(app,1))
        with patch.object(app.jinja_env.loader,'get_source',side_effect=source):
            for client in clients:
                for cid in (1,2):
                    for latest,kind,viewer in mappings:
                        name='latest'+latest
                        result=client.get('/indi-allsky/'+name+'?camera_id='+str(cid))
                        assert result.status_code==302,(name,result.status_code)
                        # Preserve relative public images redirects; resolve as a browser would.
                        from urllib.parse import urljoin,urlsplit
                        location=urlsplit(urljoin('http://localhost/indi-allsky/'+name,result.location)).path
                        assert client.get(location).status_code==200,(name,location)
                        suffix='watch' if 'video' in kind or kind=='video' else 'view'
                        latest_view='latest'+latest+suffix
                        if latest=='timelapse':latest_view='latesttimelapsewatch'
                        result=client.get('/indi-allsky/'+latest_view+'?camera_id='+str(cid))
                        assert result.status_code==302,(latest_view,result.status_code)
                        assert viewer in result.location and 'camera_id='+str(cid) in result.location
                        page=client.get(result.location)
                        assert page.status_code==200 and 'Copy link' in page.text and 'Download original' in page.text,(latest_view,page.status_code)
                        assert 'admin-mode-switch-classic' not in page.text
                        assert 'camera-'+str(cid) in page.text
                        assert client.get('/indi-allsky/'+viewer+'?id='+str(cid)+'&camera_id='+str(3-cid)).status_code==404
                        original='/indi-allsky/media/'+kind+'/'+str(cid)+'/'+str(cid)+'/original?download=1'
                        download=client.get(original)
                        assert download.status_code==200 and download.data
                        assert download.headers['X-Content-Type-Options']=='nosniff'
                        assert 'attachment' in download.headers['Content-Disposition']
                        assert client.get(original,headers={'Range':'bytes=0-9'}).status_code==206
                        empty_night = '1' if kind == 'raw' and cid == 2 else '0'
                        assert client.get('/indi-allsky/'+name+'?camera_id='+str(cid)+'&night='+empty_night).status_code==404,(kind,cid)
                    thumb=client.get('/indi-allsky/latestthumbnail?camera_id='+str(cid)+'&night=1')
                    assert thumb.status_code==302 and 'thumbnail-camera-'+str(cid) in thumb.location
                    assert client.get('/indi-allsky/watch_mini_timelapse?id='+str(cid)).status_code==200
            for query in ('camera_id=bad','camera_id=9999','night=bad'):
                assert anonymous.get('/indi-allsky/latestimage?'+query).status_code in (400,404)
            for query in ('id=bad','id=9999','camera_id=bad'):
                assert anonymous.get('/indi-allsky/view_image?'+query).status_code in (400,404)
            assert anonymous.get('/indi-allsky/media/fits/1/1/original').status_code==404
            for all_views,media_views in ((True,False),(False,True)):
                app.config.update(INDI_ALLSKY_AUTH_ALL_VIEWS=all_views,INDI_ALLSKY_AUTH_MEDIA_VIEWS=media_views)
                assert anonymous.get('/indi-allsky/view_image?id=1').status_code==302
                assert anonymous.get('/indi-allsky/media/image/1/1/original').status_code==302
                assert clients[1].get('/indi-allsky/view_image?id=1').status_code==200
                assert anonymous.get('/indi-allsky/latestimage?camera_id=1').status_code==302
            app.config.update(INDI_ALLSKY_AUTH_ALL_VIEWS=False,INDI_ALLSKY_AUTH_MEDIA_VIEWS=False)
            # Public RAW can resolve the configured export root without depending on images/.
            with TemporaryDirectory(prefix='hybrid-public-raw-') as directory:
                path=Path(directory)/'raw-export.png'
                path.write_bytes((root/'ccd_test-camera-1/raw-camera-1.png').read_bytes())
                with app.app_context():
                    config=db.session.get(IndiAllSkyDbConfigTable,1)
                    saved=dict(config.data);config.data=dict(saved,IMAGE_EXPORT_FOLDER=directory)
                    raw=db.session.get(IndiAllSkyDbRawImageTable,1);saved_filename=raw.filename;raw.filename=str(path)
                    db.session.commit()
                assert anonymous.get('/indi-allsky/view_raw?id=1').status_code==200
                assert anonymous.get('/indi-allsky/media/raw/1/1/original').data==path.read_bytes()
                with app.app_context():
                    db.session.get(IndiAllSkyDbConfigTable,1).data=saved
                    db.session.get(IndiAllSkyDbRawImageTable,1).filename=saved_filename
                    db.session.commit()
            with app.app_context():
                camera=db.session.get(IndiAllSkyDbCameraTable,2)
                camera.web_nonlocal_images=True;camera.web_local_images_admin=False
                image=db.session.get(IndiAllSkyDbImageTable,2);image.remote_url='https://example.invalid/camera2.jpg'
                db.session.commit()
            assert anonymous.get('/indi-allsky/latestimage?camera_id=2').location=='https://example.invalid/camera2.jpg'
            page=anonymous.get('/indi-allsky/view_image?id=2')
            assert 'src="https://example.invalid/camera2.jpg"' in page.text
            assert anonymous.get('/indi-allsky/media/image/2/2/original').location=='https://example.invalid/camera2.jpg'
            with app.app_context():
                image=db.session.get(IndiAllSkyDbImageTable,2);image.remote_url=None;db.session.commit()
            assert anonymous.get('/indi-allsky/latestimage?camera_id=2').status_code==404
            assert anonymous.get('/indi-allsky/view_image?id=2').status_code==404
            with app.app_context():
                image=db.session.get(IndiAllSkyDbImageTable,2);image.remote_url='javascript:alert(1)';db.session.commit()
            assert anonymous.get('/indi-allsky/latestimage?camera_id=2').status_code==404
            with app.app_context():
                IndiAllSkyDbImageTable.query.delete();db.session.commit()
            assert anonymous.get('/indi-allsky/latestimage?camera_id=1').status_code==404
            assert anonymous.get('/indi-allsky/latestthumbnail?camera_id=1').status_code==404
        print('Hybrid public latest, thumbnail, nine viewers, original/range, both cameras, optional authentication, RAW export, empty and remote policy contracts: PASS')

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--runtime-config',default='/etc/indi-allsky/flask.json')
    run(parser.parse_args().runtime_config)
