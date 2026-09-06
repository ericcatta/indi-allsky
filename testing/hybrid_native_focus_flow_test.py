#!/usr/bin/env python3
"""Native Focus camera isolation, local policy, roles and live-source ownership."""
import argparse
from pathlib import Path
from unittest.mock import patch
from hybrid_runtime_fixture import isolated_app, login_client
from hybrid_generation_fixture import seed_generation


def run(runtime_config):
    with isolated_app(runtime_config,multi_camera=True) as app:
        seed_generation(app)
        from indi_allsky.flask import db
        from indi_allsky.flask.models import IndiAllSkyDbConfigTable, IndiAllSkyDbCameraTable
        from indi_allsky.flask.views import ModernAdminFocusView
        from sqlalchemy.exc import SQLAlchemyError
        page='/indi-allsky/modern-admin/tools/focus'
        api=page+'/preview'
        for uid in (1,2):
            client=login_client(app,uid)
            for cid in (1,2):
                response=client.get(page+'?camera_id='+str(cid))
                assert response.status_code==200 and 'focus-preview-form' in response.text
                assert 'Focuser movement controls remain disabled' not in response.text
                assert 'id="focus-movement" disabled' in response.text
                response=client.get(api+'?camera_id='+str(cid))
                assert response.status_code==200 and response.json['camera_id']==cid,response.text
                assert response.json['image_b64'] and response.json['source']=='Saved frame'
                assert response.headers['Cache-Control']=='no-store'
            for query in ('profile_id=bad','camera_id=bad','camera_id=1&profile_id=test-profile-2','camera_id=1&zoom=0'):
                assert client.get(api+'?'+query).status_code==400,query
        assert app.test_client().get(api+'?camera_id=1').status_code==302
        with app.app_context():
            camera=db.session.get(IndiAllSkyDbCameraTable,2)
            camera.web_nonlocal_images=True;camera.web_local_images_admin=False
            row=db.session.get(IndiAllSkyDbConfigTable,1)
            row.data=dict(row.data,FOCUS_MODE=True,FOCUSER=dict(row.data['FOCUSER'],CLASSNAME='focuser_simulator'))
            db.session.commit()
        assert client.get(api+'?camera_id=2').status_code==403
        with app.app_context():
            camera=db.session.get(IndiAllSkyDbCameraTable,2);camera.web_nonlocal_images=False;db.session.commit()
            root=Path(app.config['INDI_ALLSKY_IMAGE_FOLDER'])
            row=db.session.get(IndiAllSkyDbConfigTable,1)
            extension=row.data['IMAGE_FILE_TYPE']
        import cv2,numpy as np
        cv2.imwrite(str(root/('latest.'+extension)),np.zeros((48,64,3),dtype=np.uint8))
        response=client.get(api+'?camera_id=1')
        assert response.status_code==200 and response.json['source']=='Live focus frame',response.text
        assert client.get(api+'?camera_id=2').status_code==409 # Never substitute primary camera frame.
        admin=login_client(app,1)
        with patch.object(ModernAdminFocusView,'verify_admin_network',return_value=True):
            assert 'id="focus-movement" disabled' not in admin.get(page).text
        with patch.object(ModernAdminFocusView,'verify_admin_network',return_value=False):
            assert 'id="focus-movement" disabled' in admin.get(page).text
        print('Native Focus: two cameras/roles, actual previews, input/local policy, primary live source, no cross-camera fallback and movement gate: PASS')

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--runtime-config',default='/etc/indi-allsky/flask.json')
    run(parser.parse_args().runtime_config)
