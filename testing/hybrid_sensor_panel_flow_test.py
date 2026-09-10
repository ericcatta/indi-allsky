#!/usr/bin/env python3
"""Real camera-scoped recorded readings and Hybrid used/all slots."""
from datetime import datetime, timedelta, timezone
from hybrid_runtime_fixture import isolated_app, login_client
from hybrid_generation_fixture import seed_generation


def run():
    with isolated_app(multi_camera=True) as app:
        seed_generation(app)
        from indi_allsky.flask import db
        from indi_allsky.flask.models import IndiAllSkyDbImageTable, IndiAllSkyDbCameraTable
        with app.app_context():
            for cid in (1,2):
                row=db.session.get(IndiAllSkyDbImageTable,cid)
                row.createDate=datetime.now(timezone.utc).replace(tzinfo=None)
                row.data={'sensor_user_0':cid*10, 'sensor_user_1':0, 'sensor_temp_0':None, 'sensor_user_59':'<test reading>'}
                camera=db.session.get(IndiAllSkyDbCameraTable,cid)
                camera.data={**(camera.data or {}),'sensor_user_0':'Camera '+str(cid),'sensor_user_30':'User Slot 30'}
            db.session.commit()
        for uid in (1,2):
            client=login_client(app,uid)
            for cid in (1,2):
                page=client.get('/indi-allsky/modern-admin/observatory/sensor-panel',query_string={'camera_id':cid})
                assert page.status_code==200,page.text[:500]
                assert f'data-camera="{cid}"' in page.text, 'Sensor page ignored selected camera'
                assert 'Camera '+str(cid) in page.text
                assert 'Recovery controls are unavailable on this page.' not in page.text
                assert 'Unavailable' in page.text and '&lt;test reading&gt;' in page.text
                assert 'sensor_user_59' in page.text and 'sensor_temp_59' in page.text
                response=client.get('/indi-allsky/js/sensor_panel',query_string={'camera_id':cid})
                assert response.status_code==200,response.text[:500]
                data=response.json
                assert data['sensor_user'][0]==cid*10 and data['sensor_user'][1]==0
                assert data['sensor_user'][2] is None
                assert data['readings']['user'][0]['label']=='Camera '+str(cid)
                assert data['readings']['user'][30]['used'] is False
                assert data['readings']['user'][59]['used'] is True
                assert data['readings']['temp'][0]['value'] is None
                assert len(data['readings']['user'])==60 and len(data['readings']['temp'])==60
                assert 'id="sensor-show-all" checked' in client.get('/indi-allsky/modern-admin/observatory/sensor-panel',query_string={'camera_id':cid,'all':1}).text
        with app.app_context():
            db.session.get(IndiAllSkyDbImageTable,2).createDate=datetime.now(timezone.utc).replace(tzinfo=None)-timedelta(hours=2)
            db.session.commit()
        stale=client.get('/indi-allsky/js/sensor_panel',query_string={'camera_id':2}).json
        assert stale['last_update'] is None and all(value is None for value in stale['sensor_user'])
        assert all(row['value'] is None for row in stale['readings']['user'])
        assert app.test_client().get('/indi-allsky/modern-admin/observatory/sensor-panel').status_code==302
        print('Sensor panel: both roles/cameras, zero versus absent readings, null values, used/all slots, escaped text, stale image and Classic disabled: PASS')


if __name__=='__main__':run()
