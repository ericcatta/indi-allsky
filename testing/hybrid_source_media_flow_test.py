#!/usr/bin/env python3
"""Exercise real source downloads and FITS previews with Classic import forbidden."""
import argparse
import io
from datetime import date
from pathlib import Path
from unittest.mock import patch
from tempfile import TemporaryDirectory
from hybrid_runtime_fixture import isolated_app, login_client
from hybrid_source_media_fixture import seed_source_media


def run(runtime_config):
    with isolated_app(runtime_config, multi_camera=True) as app:
        seed_source_media(app)
        from PIL import Image
        from astropy.io import fits
        from indi_allsky.flask import db
        from indi_allsky.flask.models import IndiAllSkyDbCameraTable, IndiAllSkyDbFitsImageTable, IndiAllSkyDbRawImageTable, IndiAllSkyDbTaskQueueTable, IndiAllSkyDbConfigTable
        from indi_allsky.flask.source_media_views import ModernAdminSourceDownloadView
        root = Path(app.config['INDI_ALLSKY_IMAGE_FOLDER'])
        for uid in (1, 2):
            client = login_client(app, uid)
            for cid in (1, 2):
                context = '?camera_id='+str(cid)+'&profile_id=test-profile-'+str(cid)
                for page in ('fits','fits/'+str(cid),'media/fits','media/raw'):
                    result = client.get('/indi-allsky/modern-admin/'+page+context)
                    assert result.status_code == 200, (uid,cid,page,result.status_code)
                    assert 'Open legacy' not in result.text
                for kind, filename in (('fits','source-camera-'+str(cid)+'.fit'), ('raw','raw-camera-'+str(cid)+'.png')):
                    path=root/('ccd_test-camera-'+str(cid))/filename
                    url='/indi-allsky/modern-admin/media/'+kind+'/'+str(cid)+'/'+str(cid)+'/download'
                    response=client.get(url)
                    assert response.status_code==200 and response.data==path.read_bytes()
                    assert response.mimetype=='application/octet-stream'
                    assert response.cache_control.private
                    assert 'attachment' in response.headers['Content-Disposition'] and filename in response.headers['Content-Disposition']
                    partial=client.get(url,headers={'Range':'bytes=0-9'})
                    assert partial.status_code==206 and partial.data==path.read_bytes()[:10]
                    assert client.get(url.replace('/'+str(cid)+'/'+str(cid)+'/', '/'+str(3-cid)+'/'+str(cid)+'/')).status_code==404
                original=(root/('ccd_test-camera-'+str(cid))/('source-camera-'+str(cid)+'.fit')).read_bytes()
                jpeg=client.get('/indi-allsky/fits2jpeg?id='+str(cid))
                assert jpeg.status_code==200, (jpeg.status_code,jpeg.text[:200])
                assert jpeg.mimetype=='image/jpeg'
                with Image.open(io.BytesIO(jpeg.data)) as image:
                    assert image.size==(64,48)
                assert original==(root/('ccd_test-camera-'+str(cid))/('source-camera-'+str(cid)+'.fit')).read_bytes()
        for suffix in ('', '?id=bad', '?id=9999'):
            assert client.get('/indi-allsky/fits2jpeg'+suffix).status_code in (400,404)
        assert client.get('/indi-allsky/modern-admin/media/unknown/1/1/download').status_code==404
        with app.app_context():
            entry=db.session.get(IndiAllSkyDbFitsImageTable,1)
            filename=entry.filename
            contents=Path(filename).read_bytes()
            Path(filename).unlink()
        assert client.get('/indi-allsky/modern-admin/media/fits/1/1/download').status_code==404
        assert client.get('/indi-allsky/fits2jpeg?id=1').status_code==404
        Path(filename).write_bytes(contents)
        with fits.open(filename,mode='update') as hdus:
            hdus[0].header['GAIN']='invalid'
        assert client.get('/indi-allsky/fits2jpeg?id=1').status_code==422
        # Original remains downloadable, including the invalid scientific header.
        assert client.get('/indi-allsky/modern-admin/media/fits/1/1/download').data==Path(filename).read_bytes()
        # Configured RAW export may be a separate mounted directory.
        with TemporaryDirectory(prefix='hybrid-export-') as export_dir:
            raw=Path(export_dir)/'external-raw.png'
            raw.write_bytes(b'synthetic raw export')
            with app.app_context():
                config=db.session.get(IndiAllSkyDbConfigTable,1)
                saved=dict(config.data)
                config.data=dict(saved, IMAGE_EXPORT_FOLDER=export_dir)
                entry=db.session.get(IndiAllSkyDbRawImageTable,1)
                entry.filename=str(raw)
                db.session.commit()
            assert client.get('/indi-allsky/modern-admin/media/raw/1/1/download').data==raw.read_bytes()
            with app.app_context():
                db.session.get(IndiAllSkyDbConfigTable,1).data=saved
                db.session.commit()
        # Symlink traversal cannot expose non-media files.
        link=root/'escape.png'
        link.symlink_to('/etc/passwd')
        with app.app_context():
            db.session.get(IndiAllSkyDbRawImageTable,1).filename=str(link)
            db.session.commit()
        assert client.get('/indi-allsky/modern-admin/media/raw/1/1/download').status_code==404
        with patch('indi_allsky.flask.source_media_views.send_file',side_effect=PermissionError('private path')):
            failed=client.get('/indi-allsky/modern-admin/media/fits/2/2/download')
            assert failed.status_code==403 and 'private path' not in failed.text
        with app.app_context():
            entry=db.session.get(IndiAllSkyDbRawImageTable,1)
            entry.filename='/etc/passwd'
            db.session.commit()
        assert client.get('/indi-allsky/modern-admin/media/raw/1/1/download').status_code==404
        with app.app_context():
            camera=db.session.get(IndiAllSkyDbCameraTable,1)
            camera.web_nonlocal_images=True
            entry=db.session.get(IndiAllSkyDbFitsImageTable,1)
            entry.remote_url='https://example.invalid/test-original.fit'
            db.session.commit()
        remote=client.get('/indi-allsky/modern-admin/media/fits/1/1/download')
        assert remote.status_code==302 and remote.location=='https://example.invalid/test-original.fit'
        assert client.get('/indi-allsky/fits2jpeg?id=1').status_code==403
        # Camera 2 remains local, even when current session camera is 1.
        assert client.get('/indi-allsky/modern-admin/media/fits/2/2/download').status_code==200
        with app.app_context():
            entry=db.session.get(IndiAllSkyDbFitsImageTable,1)
            entry.remote_url='javascript:alert(1)'
            db.session.commit()
        assert client.get('/indi-allsky/modern-admin/media/fits/1/1/download').status_code==404
        with app.app_context():
            entry=db.session.get(IndiAllSkyDbFitsImageTable,1)
            entry.remote_url=None
            db.session.commit()
        assert client.get('/indi-allsky/modern-admin/media/fits/1/1/download').status_code==404
        anonymous=app.test_client()
        for route in ('modern-admin/fits','modern-admin/media/raw','modern-admin/media/fits/2/2/download','fits2jpeg?id=2'):
            assert anonymous.get('/indi-allsky/'+route).status_code==302
        with app.app_context():
            assert IndiAllSkyDbTaskQueueTable.query.count()==0
            assert IndiAllSkyDbConfigTable.query.count()==1
        print('Hybrid FITS/RAW pages, byte-exact downloads, JPEG processing, roles, camera isolation, missing/invalid files and remote policy: PASS')

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--runtime-config',default='/etc/indi-allsky/flask.json')
    run(parser.parse_args().runtime_config)
