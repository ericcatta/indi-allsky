#!/usr/bin/env python3
"""Generated media pages and byte-exact originals without Classic routes."""
import argparse
from pathlib import Path
from hybrid_runtime_fixture import isolated_app, login_client
from hybrid_generation_fixture import seed_generation
from hybrid_generated_media_fixture import seed_generated_media


def run(runtime_config):
    with isolated_app(runtime_config,multi_camera=True) as app:
        seed_generation(app); seed_generated_media(app)
        from indi_allsky.flask import db
        from indi_allsky.flask.models import IndiAllSkyDbCameraTable, IndiAllSkyDbKeogramTable, IndiAllSkyDbTaskQueueTable
        kinds=('video','mini-video','keogram','startrail','startrail-video','panorama','panorama-video')
        pages=('keograms','startrails','startrail-videos','mini-timelapses','panorama')
        root=Path(app.config['INDI_ALLSKY_IMAGE_FOLDER'])
        for uid in (1,2):
            client=login_client(app,uid)
            for cid in (1,2):
                for page in pages:
                    response=client.get('/indi-allsky/modern-admin/media/'+page+'?camera_id='+str(cid)+'&profile_id=test-profile-'+str(cid))
                    assert response.status_code==200,(page,response.status_code)
                    assert 'Open legacy' not in response.text
                    assert 'camera-'+str(cid)+'.' in response.text
                    assert 'camera-'+str(3-cid)+'.' not in response.text
                    assert 'camera_id='+str(cid) in response.text
                for kind in kinds:
                    url='/indi-allsky/modern-admin/media/'+kind+'/'+str(cid)+'/'+str(cid)+'/download'
                    result=client.get(url)
                    path=root/(kind+'-camera-'+str(cid)+('.mp4' if 'video' in kind else '.jpg'))
                    assert result.status_code==200 and result.data==path.read_bytes(),(kind,result.status_code)
                    assert result.cache_control.private and 'attachment' in result.headers['Content-Disposition']
                    assert client.get(url,headers={'Range':'bytes=0-9'}).status_code==206
                    assert client.get(url.replace('/'+str(cid)+'/'+str(cid)+'/', '/'+str(3-cid)+'/'+str(cid)+'/')).status_code==404
                    assert app.test_client().get(url).status_code==302
                detail=client.get('/indi-allsky/modern-admin/media/images/'+str(cid))
                assert detail.status_code==200 and 'Create mini timelapse around this image' in detail.text
        # Selected/session camera cannot override the file owner's access policy.
        with app.app_context():
            camera=db.session.get(IndiAllSkyDbCameraTable,2)
            camera.web_nonlocal_images=True;camera.web_local_images_admin=False
            entry=db.session.get(IndiAllSkyDbKeogramTable,2)
            entry.remote_url='https://example.invalid/camera2-keogram.jpg'
            db.session.commit()
        all_cameras=client.get('/indi-allsky/modern-admin/media/keograms')
        assert 'https://example.invalid/camera2-keogram.jpg' in all_cameras.text
        assert 'src="/indi-allsky/images/keogram-camera-2.jpg"' not in all_cameras.text
        assert 'src="/indi-allsky/images/keogram-camera-1.jpg"' in all_cameras.text
        remote=client.get('/indi-allsky/modern-admin/media/keogram/2/2/download')
        assert remote.status_code==302 and remote.location=='https://example.invalid/camera2-keogram.jpg'
        with app.app_context(): assert IndiAllSkyDbTaskQueueTable.query.count()==0
        print('Hybrid generated media: five pages, seven original types, both cameras/roles, range, isolation and remote policy: PASS')

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--runtime-config',default='/etc/indi-allsky/flask.json')
    run(parser.parse_args().runtime_config)
