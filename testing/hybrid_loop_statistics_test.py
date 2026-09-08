#!/usr/bin/env python3
"""Loop API remains available with absent/invalid optional SQM measurements."""
import argparse
from pathlib import Path
import sys
from types import SimpleNamespace
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from indi_allsky.loop_statistics import measurement_summary, loop_sqm_summaries


def run(runtime_config):
    assert measurement_summary([3, 1, 2]) == dict(max=3, min=1, avg=2, last=3)
    assert measurement_summary([None, float('nan'), 'bad', True, float('inf'), 0, 4]) == dict(max=4, min=0, avg=2, last=0)
    assert measurement_summary([None]) == dict(max=0., min=0., avg=0., last=0.)
    assert loop_sqm_summaries([SimpleNamespace(data=None)])[0]['last'] == 0
    from hybrid_runtime_fixture import isolated_app, login_client
    from hybrid_generation_fixture import seed_generation, seed_preview_frames
    with isolated_app(runtime_config, multi_camera=True) as app:
        seed_generation(app); seed_preview_frames(app)
        from indi_allsky.flask import db
        from indi_allsky.flask.models import IndiAllSkyDbImageTable
        for client in (login_client(app, 1), login_client(app, 2)):
            for cid in (1, 2):
                response = client.get('/indi-allsky/js/loop', query_string={'camera_id':cid, 'limit_s':14400})
                assert response.status_code == 200
                data = response.json
                assert len(data['image_list']) == 3
                assert all('camera-'+str(cid) in image['url'] for image in data['image_list'])
                assert data['jsqm_data'] == dict(max=0., min=0., avg=0., last=0.)
        with app.app_context():
            image = db.session.get(IndiAllSkyDbImageTable, 1)
            image.sqm = 12.5
            image.data = {'sensor_user_8':None, 'sensor_user_9':'invalid', 'sensor_user_7':20.0}
            db.session.commit()
        data = login_client(app, 1).get('/indi-allsky/js/loop?camera_id=1&limit_s=14400').json
        assert data['jsqm_data'] == dict(max=12.5, min=12.5, avg=12.5, last=12.5)
        assert data['camera_sqm_mag_data']['max'] == 0
        assert data['camera_sqm_adu_data']['max'] == 0
        assert data['device_sqm_mag_data']['max'] == 20
        assert len(data['image_list']) == 3
    print('Loop missing/mixed SQM: summaries, both roles/cameras and image availability PASS')


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--runtime-config', default='/etc/indi-allsky/flask.json')
    run(parser.parse_args().runtime_config)
