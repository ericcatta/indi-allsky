#!/usr/bin/env python3
"""RAW playback ingress, actual files and owning-camera policy without Classic."""
from datetime import datetime, timedelta
import io
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
from hybrid_runtime_fixture import isolated_app, login_client
from hybrid_source_media_fixture import seed_source_media


def run():
    with isolated_app(multi_camera=True) as app:
        seed_source_media(app)
        from PIL import Image
        from indi_allsky.flask import db
        from indi_allsky.flask.models import IndiAllSkyDbRawImageTable as Raw, IndiAllSkyDbCameraTable as Camera, IndiAllSkyDbConfigTable as Config
        from indi_allsky.flask.views import JsonRawImageLoopView
        now = datetime.now().replace(microsecond=0)
        with app.app_context():
            for entry in Raw.query.all():
                entry.createDate = now - timedelta(seconds=10)
            db.session.commit()
        def query(client, cid, **extra):
            return client.get('/indi-allsky/js/loopraw', query_string=dict(camera_id=cid, timestamp=int(now.timestamp()), limit_s=900, **extra))
        for uid in (1, 2):
            client = login_client(app, uid)
            for cid in (1, 2):
                page = client.get('/indi-allsky/modern-admin/media/raw-loop', query_string={'profile_id':'test-profile-'+str(cid)})
                assert page.status_code == 200 and 'Recent RAW image loop' in page.text
                assert '/indi-allsky/js/loopraw?' in page.text
                assert 'data-loop-camera="camera-'+str(cid)+'"' in page.text
                assert 'data-loop-camera="camera-'+str(3-cid)+'"' not in page.text
                assert '/modern-admin/media/raw-loop?profile_id=test-profile-' in page.text
                assert 'Playback requires a browser-supported image format' in page.text
                result = query(client, cid)
                assert result.status_code == 200, result.text[:200]
                frames = result.json['image_list']
                assert len(frames) == 1 and 'raw-camera-'+str(cid)+'.png' in frames[0]['url']
                assert frames[0]['width'] == 64 and frames[0]['height'] == 48
                url = frames[0]['url']
                response = client.get('/indi-allsky/'+url if url.startswith('images/') else url)
                assert response.status_code == 200
                with Image.open(io.BytesIO(response.data)) as image:
                    assert image.size == (64, 48)
                source = client.get('/indi-allsky/modern-admin/media/raw?camera_id='+str(cid))
                assert '/modern-admin/media/raw-loop?camera_id='+str(cid) in source.text
            all_cameras = client.get('/indi-allsky/modern-admin/media/raw-loop')
            assert all('data-loop-camera="camera-'+str(cid)+'"' in all_cameras.text for cid in (1, 2))
            ordinary = client.get('/indi-allsky/modern-admin/loop')
            assert 'Recent image loop' in ordinary.text and '/indi-allsky/js/loop?' in ordinary.text
        # A separate configured export folder is served through the existing
        # camera-scoped original handler, never through an arbitrary file URL.
        with TemporaryDirectory(prefix='hybrid-raw-loop-export-') as folder:
            with app.app_context():
                entry = db.session.get(Raw, 1)
                original = Path(entry.filename)
                exported = Path(folder)/'export.png'; exported.write_bytes(original.read_bytes())
                entry.filename = str(exported)
                config = db.session.get(Config, 1)
                config.data = dict(config.data, IMAGE_EXPORT_FOLDER=folder)
                db.session.commit()
            frames = query(client, 1).json['image_list']
            assert len(frames) == 1
            assert frames[0]['url'] == '/indi-allsky/media/raw/1/1/original'
            assert client.get(frames[0]['url']).data == exported.read_bytes()
            assert client.get('/indi-allsky/media/raw/2/1/original').status_code == 404
            exported.unlink()
            assert query(client, 1).json['image_list'] == []
            assert len(query(client, 2).json['image_list']) == 1
            exported.write_bytes(original.read_bytes())
            with app.app_context():
                camera = db.session.get(Camera, 1)
                camera.web_nonlocal_images = True
                camera.web_local_images_admin = False
                db.session.commit()
            with patch.object(JsonRawImageLoopView, 'verify_admin_network', return_value=False):
                assert query(client, 1).json['image_list'] == []
                assert len(query(client, 2).json['image_list']) == 1
                with app.app_context():
                    entry = db.session.get(Raw, 1)
                    entry.remote_url = 'https://example.invalid/raw-one.png'
                    db.session.commit()
                assert query(client, 1).json['image_list'][0]['url'] == 'https://example.invalid/raw-one.png'
        assert app.test_client().get('/indi-allsky/modern-admin/media/raw-loop').status_code == 302
    print('RAW Loop: Hybrid ingress, both roles/cameras, real PNGs, export root, missing files and remote policy PASS')


if __name__ == '__main__':
    run()
