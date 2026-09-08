#!/usr/bin/env python3
"""Real camera-mode revisions without legacy config-file loading or hardware effects."""
from copy import deepcopy
import json
import re
from unittest.mock import patch
from hybrid_runtime_fixture import isolated_app, login_client


def run():
    with isolated_app(multi_camera=True) as app:
        from indi_allsky.flask import db
        from indi_allsky.flask.models import (IndiAllSkyDbCameraTable as Camera,
            IndiAllSkyDbConfigTable as Config, IndiAllSkyDbUserTable as User,
            IndiAllSkyDbTaskQueueTable as Task)
        from indi_allsky.modern_admin_settings_runtime import ModernAdminSettingsRuntimeService
        with app.app_context():
            row=db.session.get(Config,1)
            data=deepcopy(row.data)
            data['MULTI_CAMERA_CAPTURE_ENABLE']=False
            data['EXPOSURE_PERIOD_DAY']=15
            data['EXPOSURE_PERIOD']=45
            data['TIMELAPSE_ENABLE']=True
            data['MULTI_CAMERA']['profiles'][0]['camera_interface']='libcamera_imx708'
            data['MULTI_CAMERA']['profiles'][1]['outputs']['keogram']=False
            row.data=data
            camera=db.session.get(Camera,1);camera.name='libcamera_imx708';camera.driver='rpicam-still'
            camera=db.session.get(Camera,2);camera.name='ZWO ASI678MC';camera.driver='indi_asi_ccd'
            db.session.commit()
            original=deepcopy(data)
        admin,user=login_client(app,1),login_client(app,2)
        route='/indi-allsky/modern-admin/cameras'
        def latest():return Config.query.order_by(Config.id.desc()).first()
        def token(client):
            page=client.get(route)
            assert page.status_code==200
            return re.search(r'name="csrf_token" value="([^"]+)"',page.text)[1]
        def submit(client,action,**values):
            return client.post(route,data=dict(csrf_token=token(client),modern_admin_action=action,**values))
        page=admin.get(route)
        assert 'Images-only MVP' not in page.text and 'Timelapse, keogram, panorama and uploads are disabled' not in page.text
        assert 'Mini timelapses are generated on request' in page.text and 'Timelapse / Keogram' in page.text
        assert 'Automatic mini timelapse' not in page.text
        userpage=user.get(route)
        assert 'Administrator access is required' in userpage.text
        assert re.search(r'<button[^>]*disabled[^>]*>Enable multi-camera',userpage.text)
        assert admin.post(route,data={'modern_admin_action':'multi_camera_enable'}).status_code==400
        submit(user,'multi_camera_enable')
        with app.app_context():assert Config.query.count()==1
        enabled=submit(admin,'multi_camera_enable')
        assert 'Restart indi-allsky to apply' in enabled.text
        with app.app_context():
            assert latest().user_id==1 and latest().data['MULTI_CAMERA_CAPTURE_ENABLE'] is True
            expected=deepcopy(original);expected['MULTI_CAMERA_CAPTURE_ENABLE']=True
            assert latest().data==expected
            saved_id=latest().id
            assert User.query.count()==2 and Task.query.count()==0
        repeated=submit(admin,'multi_camera_enable')
        assert 'already saved' in repeated.text
        forged=submit(admin,'switch',camera_id='2')
        assert 'Disable multi-camera mode' in forged.text or 'already active' in forged.text
        with app.app_context():assert latest().id==saved_id
        submit(user,'multi_camera_disable')
        with app.app_context():assert latest().id==saved_id
        disabled=submit(admin,'multi_camera_disable')
        assert 'disabled in saved configuration' in disabled.text
        with app.app_context():
            assert latest().data==original and latest().user_id==1
        with admin.session_transaction() as session:session['camera_id']=2
        selected=submit(admin,'switch',camera_id='1')
        assert 'Camera selection saved' in selected.text,selected.text[-5000:]
        with app.app_context():
            expected=deepcopy(original);expected['CAMERA_INTERFACE']='libcamera_imx708'
            assert latest().data==expected and latest().user_id==1
            saved_id=latest().id
        repeated=submit(admin,'switch',camera_id='1')
        assert 'already selected in saved configuration' in repeated.text
        with app.app_context():assert latest().id==saved_id
        with admin.session_transaction() as session:session['camera_id']=1
        selected=submit(admin,'switch',camera_id='2')
        assert 'Camera selection saved' in selected.text
        with app.app_context():
            assert latest().data['CAMERA_INTERFACE']=='indi' and latest().data['INDI_CAMERA_NAME']=='ZWO ASI678MC'
            assert latest().data['MULTI_CAMERA']==original['MULTI_CAMERA']
            saved_id=latest().id
        for bad in ('not-a-camera','999'):
            response=submit(admin,'switch',camera_id=bad)
            assert 'Invalid camera id' in response.text or 'Camera not found' in response.text
        with patch.object(ModernAdminSettingsRuntimeService,'save_config_revision',side_effect=RuntimeError('private persistence failure')):
            failure=submit(admin,'multi_camera_enable')
            assert 'Unable to save camera mode' in failure.text and 'private persistence failure' not in failure.text
        with app.app_context():assert latest().id==saved_id and Task.query.count()==0
        # Invalid shared interval must not become an enabled runtime revision.
        with app.app_context():
            row=latest();data=deepcopy(row.data);data['EXPOSURE_PERIOD_DAY']=5;row.data=data;db.session.commit()
            before=Config.query.count()
        rejected=submit(admin,'multi_camera_enable')
        assert 'settings or shared intervals are invalid' in rejected.text
        with app.app_context():assert Config.query.count()==before
        assert app.test_client().get(route).status_code==302
        print(json.dumps({'scope':'Classic-disabled isolated Flask; synthetic config/cameras only',
            'mode':'Enable/disable persist only mode flag; repeated command creates no revision',
            'selection':'rpicam-still resolves libcamera_imx708; INDI uses selected camera name',
            'permissions':'Admin required; CSRF enforced; anonymous redirected',
            'validation':'Malformed IDs, shared interval, multi-mode switch and failed persistence rejected',
            'effects':'No system user created, no tasks queued; restart remains explicit'},indent=2))

if __name__=='__main__':run()
