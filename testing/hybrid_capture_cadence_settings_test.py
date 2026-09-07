#!/usr/bin/env python3
"""Persist shared cadence through each profile with role/CSRF enforcement."""
from copy import deepcopy
import re
from hybrid_runtime_fixture import isolated_app, login_client
from hybrid_settings_flow_test import BrowserValues, payload_from_page


def run():
    with isolated_app(multi_camera=True) as app:
        from indi_allsky.flask import db
        from indi_allsky.flask.models import IndiAllSkyDbConfigTable
        with app.app_context():
            row = db.session.get(IndiAllSkyDbConfigTable,1)
            config = deepcopy(row.data)
            config['MULTI_CAMERA_CAPTURE_ENABLE'] = True
            row.data = config
            db.session.commit()
        admin, user = login_client(app,1), login_client(app,2)
        route='/indi-allsky/modern-admin/settings/cameras'
        def latest():
            return IndiAllSkyDbConfigTable.query.order_by(IndiAllSkyDbConfigTable.id.desc()).first()
        for cid, day, night in ((1,15,45),(2,20,50)):
            url=route+'?profile_id=test-profile-'+str(cid)
            page=admin.get(url)
            assert page.status_code==200
            assert 'Shared interval Day' in page.text and 'All cameras' in page.text
            values=BrowserValues(page.text).values
            payload={key.removeprefix('camera-capture-'):value for key,value in values.items() if key.startswith('camera-capture-')}
            token=re.search(r'name="csrf_token" value="([^"]+)"',page.text)[1]
            payload.update(modern_admin_action='capture',csrf_token=token,exposure_period=str(night),exposure_period_day=str(day))
            with app.app_context():
                before=latest().id
                other_before=deepcopy(latest().data['MULTI_CAMERA']['profiles'][2-cid])
            assert admin.post(url,data={k:v for k,v in payload.items() if k!='csrf_token'}).status_code==400
            response=admin.post(url,data=payload)
            with app.app_context():
                saved=deepcopy(latest().data)
                assert latest().id>before,response.text[-5000:]
                assert saved['EXPOSURE_PERIOD']==night and saved['EXPOSURE_PERIOD_DAY']==day
                assert saved['MULTI_CAMERA']['profiles'][2-cid]==other_before
                saved_id=latest().id
            for check_id in (1,2):
                response=admin.get(route+'?profile_id=test-profile-'+str(check_id))
                rendered=BrowserValues(response.text).values
                assert float(rendered['camera-capture-exposure_period'])==night
                assert float(rendered['camera-capture-exposure_period_day'])==day
                from indi_allsky.flask.views import ModernAdminCameraSettingsView
                view=object.__new__(ModernAdminCameraSettingsView)
                view.indi_allsky_config=saved
                stale={'exposure':{'period':99,'period_day':88}}
                for key,expected in (('EXPOSURE_PERIOD',night),('exposure_period_day',day)):
                    assert view.get_camera_settings_effective_value(key,stale,None)==(expected,'global config')
                    assert view.estimate_camera_settings_scope(key)=='all cameras'
            response=admin.post(url,data=dict(payload,exposure_period_day='5'))
            assert 'Shared interval must exceed' in response.text
            with app.app_context(): assert latest().id==saved_id
            userpage=user.get(url)
            usertoken=re.search(r'name="csrf_token" value="([^"]+)"',userpage.text)[1]
            user.post(url,data=dict(payload,csrf_token=usertoken,exposure_period_day='25'))
            with app.app_context(): assert latest().id==saved_id
        page=admin.get('/indi-allsky/modern-admin/settings/full')
        payload,token=payload_from_page(page.text)
        payload['EXPOSURE_PERIOD_DAY']=5
        response=admin.post('/indi-allsky/ajax/config',json=payload,headers={'X-CSRFToken':token})
        assert response.status_code==400,response.json
        with app.app_context(): assert latest().id==saved_id
        print('Shared cadence Settings: both profiles persist common values, role/CSRF and Full Config reject invalid intervals: PASS')


if __name__=='__main__':run()
