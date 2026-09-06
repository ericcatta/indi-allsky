#!/usr/bin/env python3
"""Real generated-output detail and downloads without Classic view imports."""
import html
import re
from pathlib import Path
from unittest.mock import patch
from hybrid_runtime_fixture import isolated_app, login_client
from hybrid_generated_media_fixture import seed_generated_media


def run():
    with isolated_app(multi_camera=True) as app:
        seed_generated_media(app)
        from indi_allsky.flask import db
        from indi_allsky.flask.models import IndiAllSkyDbCameraTable as Camera
        from indi_allsky.flask.media_archive import ModernAdminMediaArchive
        from sqlalchemy.exc import SQLAlchemyError
        endpoint='/indi-allsky/modern-admin/output'
        kinds=('video','mini-video','keogram','startrail','startrail-video','panorama','panorama-video')
        for uid in (1,2):
            client=login_client(app,uid)
            picker=client.get(endpoint+'?camera_id=2&profile_id=test-profile-2')
            assert picker.status_code==200 and 'Choose a saved output' in picker.text
            assert picker.text.count('profile_id=test-profile-2')==7
            for kind in kinds:
                for cid in (1,2):
                    response=client.get(endpoint,query_string={'kind':kind,'id':cid,'camera_id':cid,'profile_id':'test-profile-'+str(cid)})
                    assert response.status_code==200,response.text
                    assert f'data-camera-id="{cid}"' in response.text
                    assert f'{kind}-camera-{cid}' in response.text and 'Static' not in response.text
                    match=re.search(r'href="([^"]+/download)"',response.text)
                    download=client.get(html.unescape(match[1]))
                    assert download.status_code==200 and download.data
                    library=client.get('/indi-allsky/modern-admin/library',query_string={'kind':kind,'camera_id':cid,'profile_id':'test-profile-'+str(cid)})
                    detail=re.search(r'href="([^"]+)"\s*>Output details</a>',library.text)
                    assert detail and client.get(html.unescape(detail[1])).status_code==200
            for query in ('id=0','id=abc','id=9223372036854775808','kind=image&id=1','kind=unknown','id=1&camera_id=1&profile_id=test-profile-2','profile_id=missing'):
                assert client.get(endpoint+'?'+query).status_code==400,query
            assert client.get(endpoint+'?kind=video&id=1&camera_id=2').status_code==404
            assert client.get(endpoint+'?id=9999').status_code==404
        assert app.test_client().get(endpoint).status_code==302
        client=login_client(app,2)
        with patch.object(ModernAdminMediaArchive,'item',side_effect=SQLAlchemyError('private details')):
            response=client.get(endpoint+'?kind=video&id=1')
            assert response.status_code==200 and 'could not be loaded' in response.text
            assert 'private details' not in response.text and 'Download original' not in response.text
        with app.app_context():
            camera=db.session.get(Camera,2)
            camera.web_nonlocal_images=True;camera.web_local_images_admin=False
            db.session.commit()
        for kind in kinds:
            response=client.get(endpoint+f'?kind={kind}&id=2')
            assert response.status_code==200 and 'No browser preview is available' in response.text
        (Path(app.config['INDI_ALLSKY_IMAGE_FOLDER'])/'video-camera-1.mp4').unlink()
        assert client.get('/indi-allsky/modern-admin/media/video/1/1/download').status_code==404
        print('Output detail: seven types, both cameras/roles, Library links, original bytes, scope, missing files, provider error and remote policy: PASS')


if __name__=='__main__':run()
