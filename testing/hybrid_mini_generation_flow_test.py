#!/usr/bin/env python3
"""Mini timelapse controls, preview parity and real isolated queue persistence."""
import argparse
import re
from datetime import timedelta
from unittest.mock import patch
from hybrid_runtime_fixture import isolated_app, login_client
from hybrid_generation_fixture import seed_generation


def run(runtime_config):
    with isolated_app(runtime_config, multi_camera=True) as app:
        seed_generation(app)
        from indi_allsky.flask import db
        from indi_allsky.flask.models import IndiAllSkyDbImageTable, IndiAllSkyDbTaskQueueTable, IndiAllSkyDbCameraTable
        from sqlalchemy.exc import SQLAlchemyError
        admin, user = login_client(app, 1), login_client(app, 2)
        base='/indi-allsky/modern-admin/tools/mini-generate'
        preview='/indi-allsky/modern-admin/tools/mini-preview'
        post='/indi-allsky/ajax/minigenerate'
        for client in (admin,user):
            for cid in (1,2):
                page=client.get(base+'?camera_id='+str(cid)+'&profile_id=test-profile-'+str(cid))
                assert page.status_code==200, page.text[:500]
                assert re.search(r'id="IMAGE_ID"[^>]*value="'+str(cid)+'"',page.text)
                assert re.search(r'id="CAMERA_ID"[^>]*value="'+str(cid)+'"',page.text)
                assert 'Open legacy' not in page.text
        page=admin.get(base+'?camera_id=2')
        assert 'required' not in re.search(r'<input[^>]*id="NOTE"[^>]*>',page.text)[0]
        token=re.search(r'name="csrf_token"[^>]*value="([^"]+)"',page.text)[1]
        headers={'X-CSRFToken':token}
        payload=dict(CAMERA_ID='2',IMAGE_ID='2',PRE_SECONDS='240',POST_SECONDS='120',FRAMERATE='10',NOTE='<b>safe literal note</b>')
        assert admin.get(base+'?camera_id=1&image_id=2').status_code==404
        assert admin.get(base+'?camera_id=1&profile_id=test-profile-2').status_code==400
        assert admin.get(base+'?profile_id=missing').status_code==400
        assert admin.get(base+'?image_id=bad').status_code==400
        assert admin.post(post,json=payload).status_code==400
        usertoken=re.search(r'name="csrf_token"[^>]*value="([^"]+)"',user.get(base).text)[1]
        assert user.post(post,json=payload,headers={'X-CSRFToken':usertoken}).status_code==400
        for change in ({'IMAGE_ID':0},{'PRE_SECONDS':-1},{'POST_SECONDS':43201},{'FRAMERATE':'nan'},{'FRAMERATE':0},{'FRAMERATE':1e-300},{'FRAMERATE':1000},{'NOTE':'x'*256}):
            assert admin.post(post,json=dict(payload,**change),headers=headers).status_code==400,change
        for invalid in ([],{},None):
            assert admin.post(post,json=invalid,headers=headers).status_code==400
        assert admin.post(post,json=dict(payload,CAMERA_ID=1),headers=headers).status_code==404
        response=admin.post(post,json=payload,headers=headers)
        assert response.status_code==200, response.text
        assert admin.get(response.json['task_url']).status_code==200
        with app.app_context():
            task=IndiAllSkyDbTaskQueueTable.query.one()
            assert task.data=={'action':'generateMiniVideo','kwargs':{'image_id':2,'camera_id':2,'pre_seconds':240,'post_seconds':120,'framerate':10.,'note':'<b>safe literal note</b>'}}
            assert (task.queue.name,task.state.name,task.priority)==('VIDEO','MANUAL',100)
        with patch.object(db.session,'commit',side_effect=SQLAlchemyError('secret detail')):
            failed=admin.post(post,json=payload,headers=headers)
            assert failed.status_code==500 and 'secret detail' not in failed.text
        with app.app_context():
            assert IndiAllSkyDbTaskQueueTable.query.count()==1
            target=db.session.get(IndiAllSkyDbImageTable,2)
            for iid,seconds,excluded in ((3,-240,False),(4,120,False),(5,121,False),(6,-241,False),(7,0,True),(8,-18000,False)):
                db.session.add(IndiAllSkyDbImageTable(id=iid,camera_id=2,filename='frame-'+str(iid)+'.jpg',dayDate=target.dayDate,
                    createDate=target.createDate+timedelta(seconds=seconds),exposure=.5,gain=10,adu=.1,exclude=excluded,data={}))
            db.session.commit()
        result=user.get(preview,query_string=payload)
        assert result.status_code==200 and result.json['count']==3
        assert [i['id'] for i in result.json['images']]==[3,2,4],result.json
        assert result.json['seconds']==.3
        assert user.get(preview,query_string=dict(payload,PRE_SECONDS=21600)).json['count']==5
        assert user.get(preview,query_string=dict(payload,CAMERA_ID=1)).status_code==404
        assert user.get(preview,query_string=dict(payload,FRAMERATE='inf')).status_code==400
        with app.app_context():
            camera=db.session.get(IndiAllSkyDbCameraTable,2)
            camera.web_nonlocal_images=True;camera.web_local_images_admin=False
            db.session.commit()
        no_urls=user.get(preview,query_string=payload)
        assert no_urls.json['count']==3 and no_urls.json['images']==[]
        with app.app_context():
            IndiAllSkyDbImageTable.query.filter_by(camera_id=1).delete()
            db.session.commit()
        empty=admin.get(base+'?camera_id=1')
        assert empty.status_code==200 and 'No saved images are available' in empty.text
        for path in (base,preview):
            assert app.test_client().get(path).status_code==302
        print('Hybrid mini generation: identities, scope, CSRF, validation, queue payload/rollback, empty state and exact preview boundaries: PASS')

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--runtime-config',default='/etc/indi-allsky/flask.json')
    run(parser.parse_args().runtime_config)
