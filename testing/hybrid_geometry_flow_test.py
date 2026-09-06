#!/usr/bin/env python3
"""Geometry previews and actual reviewed profile/global Settings persistence."""
import argparse
from copy import deepcopy
import re
from hybrid_runtime_fixture import isolated_app, login_client
from hybrid_generation_fixture import seed_generation
from hybrid_settings_flow_test import BrowserValues, payload_from_page


def run(runtime_config):
    with isolated_app(runtime_config,multi_camera=True) as app:
        seed_generation(app)
        from indi_allsky.flask import db
        from indi_allsky.flask.models import IndiAllSkyDbCameraTable, IndiAllSkyDbImageTable, IndiAllSkyDbConfigTable, IndiAllSkyDbTaskQueueTable
        admin,user=login_client(app,1),login_client(app,2)
        page='/indi-allsky/modern-admin/tools/image-circle-helper'
        settings='/indi-allsky/modern-admin/settings/cameras'
        full='/indi-allsky/modern-admin/settings/full'
        draft={'helper_diameter':'320','helper_offset_x':'-25','helper_offset_y':'35'}
        with app.app_context():
            camera=db.session.get(IndiAllSkyDbCameraTable,2)
            camera.lensImageCircle=360;camera.lensOffsetX=10;camera.lensOffsetY=-20
            row=db.session.get(IndiAllSkyDbConfigTable,1)
            initial=deepcopy(row.data)
            initial['MULTI_CAMERA']['profiles'][1]['lens']={'focal_length':2.8,'extension':'preserve'}
            initial['MULTI_CAMERA']['profiles'][1]['image_circle_mask']={'opacity':85,'extension':'preserve'}
            row.data=initial
            db.session.commit()
            original=deepcopy(db.session.get(IndiAllSkyDbConfigTable,1).data)
        for client in (admin,user):
            for cid in (1,2):
                response=client.get(page,query_string={'camera_id':cid,'profile_id':'test-profile-'+str(cid)})
                assert response.status_code==200,response.text[:300]
                assert 'Preview generation remains disabled' not in response.text
                assert 'Review values in Camera Settings' in response.text
                if cid==2:
                    values=BrowserValues(response.text).values
                    assert values['IMAGE_CIRCLE_DIAMETER']=='360' and values['OFFSET_X']=='10' and values['OFFSET_Y']=='-20'
        assert app.test_client().get(page).status_code==302
        for query in ({'camera_id':'invalid'},{'camera_id':1,'profile_id':'test-profile-2'},{'profile_id':'missing'},{'image_id':'bad'}):
            assert admin.get(page,query_string=query).status_code==400,query
        assert admin.get(page+'?camera_id=2&image_id=1').status_code==404
        assert admin.get(page+'?camera_id=2&image_id=2').status_code==200
        for change in ({'helper_diameter':'0'},{'helper_offset_x':'bad'},{'helper_offset_y':'100001'}):
            for route in (settings,full):
                assert admin.get(route,query_string=dict(draft,profile_id='test-profile-2',**change)).status_code==400
        assert admin.get(settings,query_string=dict(draft,profile_id='missing')).status_code==400
        response=admin.get(settings,query_string=dict(draft,profile_id='test-profile-2'))
        assert response.status_code==200 and 'Unsaved geometry' in response.text
        values=BrowserValues(response.text).values
        payload={key.removeprefix('camera-lens-'):value for key,value in values.items() if key.startswith('camera-lens-')}
        assert payload['lens_image_circle']=='320' and payload['lens_offset_x']=='-25' and payload['lens_offset_y']=='35'
        token=re.search(r'name="csrf_token" value="([^"]+)"',response.text)[1]
        payload.update(modern_admin_action='lens_optics',csrf_token=token)
        with app.app_context(): assert IndiAllSkyDbConfigTable.query.count()==1
        failed=admin.post(settings+'?profile_id=test-profile-2',data={k:v for k,v in payload.items() if k!='csrf_token'})
        assert failed.status_code==400
        response=admin.post(settings+'?profile_id=test-profile-2',data=payload)
        assert response.status_code==200,response.text[:300]
        with app.app_context():
            assert IndiAllSkyDbConfigTable.query.count()==2,response.text[-1000:]
            saved=IndiAllSkyDbConfigTable.query.order_by(IndiAllSkyDbConfigTable.id.desc()).first().data
            expected=deepcopy(original)
            expected['MULTI_CAMERA']['profiles'][1]['lens'].update(image_circle=320,offset_x=-25,offset_y=35)
            assert saved==expected
            assert IndiAllSkyDbTaskQueueTable.query.count()==0
        userpage=user.get(settings,query_string=dict(draft,profile_id='test-profile-1'))
        assert 'Only an administrator can save or sync camera settings.' in userpage.text
        assert all('disabled' in button for button in re.findall(r'<button[^>]*type="submit"[^>]*>',userpage.text))
        usertoken=re.search(r'name="csrf_token" value="([^"]+)"',userpage.text)[1]
        rejected=user.post(settings+'?profile_id=test-profile-1',data=dict(payload,csrf_token=usertoken))
        assert 'Only an admin user can change camera profile settings.' in rejected.text
        with app.app_context(): assert IndiAllSkyDbConfigTable.query.count()==2
        response=admin.get(full,query_string=draft)
        assert 'Unsaved geometry' in response.text
        global_payload,token=payload_from_page(response.text)
        assert str(global_payload['LENS_IMAGE_CIRCLE'])=='320'
        assert str(global_payload['LENS_OFFSET_X'])=='-25'
        response=admin.post('/indi-allsky/ajax/config',json=global_payload,headers={'X-CSRFToken':token})
        assert response.status_code==200,response.json
        with app.app_context():
            saved=IndiAllSkyDbConfigTable.query.order_by(IndiAllSkyDbConfigTable.id.desc()).first().data
            assert saved['MULTI_CAMERA']==expected['MULTI_CAMERA'] and saved['LENS_IMAGE_CIRCLE']==320
            camera=db.session.get(IndiAllSkyDbCameraTable,2)
            camera.web_nonlocal_images=True;camera.web_local_images_admin=False
            db.session.commit()
        response=user.get(page+'?camera_id=2')
        assert 'no preview allowed' in response.text
        with app.app_context():
            IndiAllSkyDbImageTable.query.filter_by(camera_id=1).delete();db.session.commit()
        assert 'No saved images' in admin.get(page+'?camera_id=1').text
        print('Geometry: native previews, identities, role/CSRF, validated drafts, real profile/global saves, unchanged other profile, media policy and empty state: PASS')

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--runtime-config',default='/etc/indi-allsky/flask.json')
    run(parser.parse_args().runtime_config)
