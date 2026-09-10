#!/usr/bin/env python3
"""Charts rendered without Classic, real camera-scoped queries and image histogram."""
from datetime import datetime
from pathlib import Path
import re
from hybrid_runtime_fixture import isolated_app, login_client
from hybrid_generation_fixture import seed_generation


def run():
    with isolated_app(multi_camera=True) as app:
        seed_generation(app)
        from indi_allsky.flask import db
        from indi_allsky.flask.models import IndiAllSkyDbImageTable
        stamp = datetime(2026, 9, 7, 8, 0)
        with app.app_context():
            for cid in (1, 2):
                row = db.session.get(IndiAllSkyDbImageTable, cid)
                row.createDate = stamp
                row.sqm = 10 + cid
                row.stars = 20 + cid
                row.temp = 15 + cid
                row.gain = 30 + cid
                row.detections = cid - 1
                row.data = {'sensor_user_'+str(i): cid*100+i for i in range(10, 19)}
            db.session.commit()
        keys = ['jsqm','stars','temp','exp','gain','detection'] + ['custom_'+str(i) for i in range(1,10)]
        for uid in (1, 2):
            client = login_client(app, uid)
            for cid in (1, 2):
                page = client.get('/indi-allsky/modern-admin/observatory/charts', query_string={'camera_id':cid})
                assert page.status_code == 200, page.text[:500]
                assert f'data-camera="{cid}"' in page.text, 'Chart page ignored selected camera'
                assert re.findall('data-key="([^"]+)"', page.text) == keys + ['histogram']
                assert 'modern_admin/charts.js' in page.text
                query = {'camera_id':cid, 'timestamp':int(stamp.timestamp()), 'limit_s':900}
                response = client.get('/indi-allsky/js/charts', query_string=query)
                assert response.status_code == 200, response.text[:500]
                data = response.json['chart_data']
                assert data['jsqm'] == [{'x':'08:00:00','y':10+cid}], data
                assert data['gain'][0]['y'] == 30+cid
                assert data['detection'][0]['y'] == cid-1
                for i in range(1,10):
                    assert data['custom_'+str(i)][0]['y'] == cid*100+i+9
                assert all(len(data['histogram'][channel]) == 256 for channel in ('red','green','blue'))
                assert data['histogram']['gray'] == []
                assert sum(point['y'] for point in data['histogram']['red']) > 0
                query['timestamp'] -= 86400
                empty = client.get('/indi-allsky/js/charts', query_string=query).json
                assert all(empty['chart_data'][key] == [] for key in keys)
                assert empty['message']
        with app.app_context():
            Path(db.session.get(IndiAllSkyDbImageTable, 2).filename).unlink()
        query.update(camera_id=2, timestamp=int(stamp.timestamp()))
        missing = client.get('/indi-allsky/js/charts', query_string=query).json['chart_data']
        assert missing['gain'][0]['y'] == 32
        assert all(not points for points in missing['histogram'].values())
        with app.app_context():
            row = db.session.get(IndiAllSkyDbImageTable, 2)
            row.stars = None
            row.temp = None
            row.data = {}
            db.session.commit()
        absent = client.get('/indi-allsky/js/charts', query_string=query)
        assert absent.status_code == 200
        for key in ['stars', 'temp'] + ['custom_'+str(i) for i in range(1, 10)]:
            assert absent.json['chart_data'][key][0]['y'] is None, key
        assert app.test_client().get('/indi-allsky/modern-admin/observatory/charts').status_code == 302
        print('Charts: both roles/cameras, all series, actual histogram, empty history and missing file with Classic disabled: PASS')


if __name__ == '__main__':
    run()
