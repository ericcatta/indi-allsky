#!/usr/bin/env python3
"""Real HTTP generation requests and scoped deletion of disposable fixture files."""
import argparse
import re
from datetime import date
from pathlib import Path
from unittest.mock import patch
from hybrid_runtime_fixture import isolated_app, login_client
from hybrid_generation_fixture import seed_generation


def run(runtime_config):
    with isolated_app(runtime_config,multi_camera=True) as app:
        seed_generation(app)
        from indi_allsky.flask import db
        from sqlalchemy.exc import SQLAlchemyError
        from indi_allsky.flask.views import AjaxTimelapseGeneratorView
        from indi_allsky.flask.models import (IndiAllSkyDbTaskQueueTable,IndiAllSkyDbConfigTable,
            IndiAllSkyDbImageTable,IndiAllSkyDbVideoTable,IndiAllSkyDbKeogramTable,
            IndiAllSkyDbStarTrailsTable,IndiAllSkyDbStarTrailsVideoTable,IndiAllSkyDbPanoramaVideoTable)
        with app.app_context():
            config=db.session.get(IndiAllSkyDbConfigTable,1)
            config.data=dict(config.data,FISH2PANO=dict(config.data['FISH2PANO'],ENABLE=False))
            db.session.commit()
        admin=login_client(app,1)
        user=login_client(app,2)
        route='/indi-allsky/modern-admin/tools/generate'
        for cid in (1,2):
            page=admin.get(route+'?camera_id='+str(cid)+'&profile_id=test-profile-'+str(cid))
            assert page.status_code==200, page.text[:500]
            assert 'Disabled in Modern Admin' not in page.text and 'Open Classic' not in page.text
            assert re.search(r'id="CAMERA_ID"[^>]*value="'+str(cid)+'"',page.text)
            ordinary=user.get(route+'?camera_id='+str(cid))
            assert ordinary.status_code==200 and '<fieldset disabled>' in ordinary.text
        assert admin.get(route+'?camera_id=1&profile_id=test-profile-2').status_code==400
        assert admin.get(route+'?profile_id=missing').status_code==400
        token=re.search(r'name="csrf_token"[^>]*value="([^"]+)"',page.text)[1]
        headers={'X-CSRFToken':token}
        url='/indi-allsky/ajax/generate'
        payload={'CAMERA_ID':'2','ACTION_SELECT':'generate_video','DAY_SELECT':str(date.today())+'_night'}
        assert admin.post(url,json=payload).status_code==400
        assert admin.post(url,json=[],headers=headers).status_code==400
        assert admin.post(url,json={},headers=headers).status_code==400
        assert admin.post(url,json=dict(payload,CAMERA_ID='9999'),headers=headers).status_code==404
        with patch.object(AjaxTimelapseGeneratorView,'verify_admin_network',return_value=False):
            assert admin.post(url,json=payload,headers=headers).status_code==400
        with patch.object(AjaxTimelapseGeneratorView,'verify_admin_network',return_value=True):
            assert admin.post(url,json=dict(payload,DAY_SELECT='1900-01-01_night'),headers=headers).status_code==400
            assert admin.post(url,json=dict(payload,ACTION_SELECT='unknown'),headers=headers).status_code==400
            for action, expected in [('generate_video','generateVideo'),('generate_k_st','generateKeogramStarTrails')]:
                response=admin.post(url,json=dict(payload,ACTION_SELECT=action),headers=headers)
                assert response.status_code==200 and response.json['success-message']=='Job submitted'
                with app.app_context():
                    task=IndiAllSkyDbTaskQueueTable.query.order_by(IndiAllSkyDbTaskQueueTable.id.desc()).first()
                    assert task.data=={'action':expected,'kwargs':{'timespec':date.today().strftime('%Y%m%d'),'night':True,'camera_id':2}}
                    assert task.state.name=='MANUAL' and task.queue.name=='VIDEO' and task.priority==100
            with patch.object(db.session,'commit',side_effect=SQLAlchemyError('private database error')):
                failed=admin.post(url,json=payload,headers=headers)
                assert failed.status_code==500 and 'private database error' not in failed.text
            with app.app_context():
                assert IndiAllSkyDbTaskQueueTable.query.count()==2
            disabled=admin.post(url,json=dict(payload,ACTION_SELECT='generate_panorama_video'),headers=headers)
            assert disabled.status_code==200 and disabled.json['success-message']=='Panoramas disabled', disabled.json
            with app.app_context():
                assert IndiAllSkyDbTaskQueueTable.query.count()==2
                config=db.session.get(IndiAllSkyDbConfigTable,1)
                config.data=dict(config.data,FISH2PANO=dict(config.data['FISH2PANO'],ENABLE=True))
                db.session.commit()
            assert admin.post(url,json=dict(payload,ACTION_SELECT='generate_panorama_video'),headers=headers).status_code==200
            assert admin.post(url,json=dict(payload,ACTION_SELECT='generate_video_k_st'),headers=headers).status_code==200
            with app.app_context():
                tasks=IndiAllSkyDbTaskQueueTable.query.order_by(IndiAllSkyDbTaskQueueTable.id).all()
                assert [t.data['action'] for t in tasks][-3:]==['generateKeogramStarTrails','generateVideo','generatePanoramaVideo']
                assert all(t.data['kwargs']['camera_id']==2 for t in tasks)
            assert admin.post(url,json=dict(payload,ACTION_SELECT='upload_endofnight'),headers=headers).status_code==200
            with app.app_context():
                latest=IndiAllSkyDbTaskQueueTable.query.order_by(IndiAllSkyDbTaskQueueTable.id.desc()).first()
                assert latest.data=={'action':'uploadAllskyEndOfNight','kwargs':{'night':True,'camera_id':2}}
            camera2=admin.get(route+'?camera_id=2')
            camera1=admin.get(route+'?camera_id=1')
            assert camera2.text.count('data-generation-task ') == 7
            assert camera1.text.count('data-generation-task ') == 0
            # Only disposable synthetic output markers are removed. This does not test encoding.
            models=[IndiAllSkyDbVideoTable,IndiAllSkyDbKeogramTable,IndiAllSkyDbStarTrailsTable,IndiAllSkyDbStarTrailsVideoTable,IndiAllSkyDbPanoramaVideoTable]
            root=Path(app.config['INDI_ALLSKY_IMAGE_FOLDER'])
            with app.app_context():
                for cid in (1,2):
                    for model in models:
                        path=root/(model.__tablename__+'-'+str(cid)+'.test')
                        path.write_bytes(b'disposable generated-output marker')
                        db.session.add(model(id=cid,filename=str(path),camera_id=cid,dayDate=date.today(),night=True,success=True,data={}))
                db.session.commit()
            deleted=admin.post(url,json=dict(payload,ACTION_SELECT='delete_video_k_st_p'),headers=headers)
            assert deleted.status_code==200
            with app.app_context():
                for model in models:
                    assert db.session.get(model,2) is None
                    assert db.session.get(model,1) is not None
                    assert not (root/(model.__tablename__+'-2.test')).exists()
                    assert (root/(model.__tablename__+'-1.test')).exists()
            # Verify each narrower deletion command as well as the combined one.
            with app.app_context():
                for model in models:
                    path=root/(model.__tablename__+'-2.test')
                    path.write_bytes(b'disposable generated-output marker')
                    db.session.add(model(id=2,filename=str(path),camera_id=2,dayDate=date.today(),night=True,success=True,data={}))
                db.session.commit()
            for action, subset in [('delete_video',models[:1]),('delete_k_st',models[1:4]),('delete_panorama_video',models[4:])]:
                assert admin.post(url,json=dict(payload,ACTION_SELECT=action),headers=headers).status_code==200
                with app.app_context():
                    for model in subset:
                        assert db.session.get(model,2) is None
                        assert not (root/(model.__tablename__+'-2.test')).exists()
                    assert all(db.session.get(model,1) is not None for model in models)
            deleted=admin.post(url,json=dict(payload,ACTION_SELECT='delete_images'),headers=headers)
            assert deleted.status_code==200 and deleted.json['success-message']=='1 images deleted'
            assert not (root/'generation-camera-2.jpg').exists()
            assert (root/'generation-camera-1.jpg').exists()
        user_page=user.get(route+'?camera_id=1')
        user_token=re.search(r'name="csrf_token"[^>]*value="([^"]+)"',user_page.text)[1]
        assert user.post(url,json=payload,headers={'X-CSRFToken':user_token}).status_code==400
        anonymous=app.test_client()
        assert anonymous.get(route).status_code==302
        login_page=anonymous.get('/indi-allsky/login')
        anonymous_token=re.search(r'name="csrf_token"[^>]*value="([^"]+)"',login_page.text)[1]
        assert anonymous.post(url,json=payload,headers={'X-CSRFToken':anonymous_token}).status_code==302
        print('Hybrid generation form, roles/CSRF/network, scoped jobs, FISH2PANO gate, task visibility and dedicated fixture deletion: PASS')

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--runtime-config',default='/etc/indi-allsky/flask.json')
    run(parser.parse_args().runtime_config)
