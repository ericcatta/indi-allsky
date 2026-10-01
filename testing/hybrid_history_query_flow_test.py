#!/usr/bin/env python3
"""Reject malformed history controls before date arithmetic or unbounded queries."""
from datetime import datetime
from unittest.mock import patch
from hybrid_generation_fixture import seed_generation
from hybrid_runtime_fixture import isolated_app, login_client


PAGES = ('/modern-admin/loop', '/modern-admin/media/raw-loop',
         '/modern-admin/observatory/charts', '/modern-admin/observatory/virtualsky',
         '/modern-admin/cameras/image-lag', '/modern-admin/cameras/adu-history')
APIS = ('/js/loop', '/js/looppanorama', '/js/loopraw', '/js/charts')


def run():
    with isolated_app(multi_camera=True) as app:
        seed_generation(app)
        from indi_allsky.flask.views import JsonImageLoopView
        from indi_allsky.flask.base_views import BaseView
        from indi_allsky.flask import db
        from indi_allsky.flask.models import IndiAllSkyDbConfigTable, IndiAllSkyDbTaskQueueTable, IndiAllSkyDbImageTable, IndiAllSkyDbCameraTable
        for uid in (1, 2):
            client = login_client(app, uid)
            for route in PAGES + APIS:
                for value in ('bad', '', '1.5', 'NaN', '999999999999999999999999', '-999999999999999999999999'):
                    response = client.get('/indi-allsky' + route, query_string={'camera_id':1,'timestamp':value})
                    assert response.status_code == 400, (route, value, response.status_code)
                    assert 'timestamp' in response.text.lower(), response.text[:200]
            for route in APIS:
                for key in ('limit_s', 'camera_id'):
                    for value in ('bad', '', '1.5', '-1'):
                        response = client.get('/indi-allsky' + route, query_string={'camera_id':1,key:value})
                        assert response.status_code == 400, (route, key, value, response.status_code)
            for route in APIS:
                assert client.get('/indi-allsky' + route, query_string={'camera_id':2**80}).status_code == 400
            for route in APIS[:3]:
                for value in ('bad', '', '-1'):
                    assert client.get('/indi-allsky' + route, query_string={'camera_id':1,'limit':value}).status_code == 400
            seen = []
            def images(view, *args):
                seen.append((view.limit, args[-1], args[0]))
                return []
            with patch.object(JsonImageLoopView, 'getLoopImages', images):
                for limit, expected in (('0',0), ('12',12), ('100000000000000000000',1000)):
                    response = client.get('/indi-allsky/js/loop', query_string={'camera_id':1,'limit':limit,'limit_s':99999999999999999999})
                    assert response.status_code == 200, response.text[:200]
                    assert seen[-1] == (expected,14400,1), seen
                assert client.get('/indi-allsky/js/loop').status_code == 200
                assert seen[-1] == (1000,900,0), 'Missing camera must retain All Cameras'
        with app.app_context():
            for row in db.session.query(IndiAllSkyDbImageTable):
                row.createDate = datetime.now()
            db.session.commit()
        client = login_client(app, 1)
        endpoint = '/indi-allsky/js/loop'
        with patch.object(BaseView, 'verify_admin_network', return_value=False):
            response = client.get(endpoint)
            assert response.status_code == 200 and len(response.json['image_list']) == 2
            with app.app_context():
                camera = db.session.get(IndiAllSkyDbCameraTable, 2)
                camera.web_nonlocal_images = True
                camera.web_local_images_admin = True
                camera.s3_prefix = 'https://example.invalid/camera-two'
                db.session.commit()
            assert len(client.get(endpoint).json['image_list']) == 1
            with app.app_context():
                row = db.session.get(IndiAllSkyDbImageTable, 2)
                row.remote_url = ''
                row.s3_key = ''
                db.session.commit()
            assert len(client.get(endpoint).json['image_list']) == 1
            assert client.get(endpoint+'?camera_id=2').json['image_list'] == []
            with app.app_context():
                db.session.get(IndiAllSkyDbImageTable, 2).s3_key = 'frame.jpg'
                db.session.commit()
            rows = client.get(endpoint).json['image_list']
            assert len(rows) == 2
            assert any(row['url'] == 'https://example.invalid/camera-two/frame.jpg' for row in rows)
            with app.app_context():
                db.session.get(IndiAllSkyDbImageTable, 2).s3_key = None
                db.session.commit()
        with patch.object(BaseView, 'verify_admin_network', return_value=True):
            assert len(client.get(endpoint).json['image_list']) == 2
        for route in PAGES:
            assert app.test_client().get('/indi-allsky'+route+'?timestamp=bad').status_code == 302
        with app.app_context():
            assert db.session.query(IndiAllSkyDbConfigTable).count() == 1
            assert db.session.query(IndiAllSkyDbTaskQueueTable).count() == 0
        print('History controls: malformed/overflow timestamps, invalid scope/ranges, bounded loop queries, roles and no mutations PASS')


if __name__ == '__main__':
    run()
