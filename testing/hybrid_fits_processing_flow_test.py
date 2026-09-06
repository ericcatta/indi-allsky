#!/usr/bin/env python3
"""Real FITS pixels, native controls, output signatures and failure isolation."""
import argparse
import base64
from copy import deepcopy
from datetime import datetime
import hashlib
import json
from pathlib import Path
import re
from shutil import copyfile
from unittest.mock import patch
from hybrid_runtime_fixture import isolated_app,login_client
from hybrid_source_media_fixture import seed_source_media
from hybrid_settings_flow_test import BrowserValues


def payload_from_page(app, html):
    from indi_allsky.flask.forms import IndiAllskyImageProcessingForm
    values=BrowserValues(html)
    with app.test_request_context():
        form=IndiAllskyImageProcessingForm()
        payload={f.name:values.checks.get(f.name,False) if f.type=='BooleanField' else values.values[f.name]
                 for f in form if f.name!='csrf_token'}
    token=re.search(r'name="csrf_token"[^>]*value="([^"]+)"',html)[1]
    return payload,{'X-CSRFToken':token}


def run(runtime_config):
    import cv2,numpy as np
    with isolated_app(runtime_config,multi_camera=True) as app:
        seed_source_media(app)
        from indi_allsky.flask import db
        from indi_allsky.flask.models import IndiAllSkyDbFitsImageTable,IndiAllSkyDbDarkFrameTable,IndiAllSkyDbBadPixelMapTable,IndiAllSkyDbCameraTable,IndiAllSkyDbConfigTable,IndiAllSkyDbTaskQueueTable
        from indi_allsky.flask.image_processing_config import processing_config
        from sqlalchemy.exc import SQLAlchemyError
        admin,user=login_client(app,1),login_client(app,2)
        page='/indi-allsky/modern-admin/tools/process-fits'
        endpoint='/indi-allsky/js/processing'
        baseline=json.loads((Path(__file__).parent/'fixtures/hybrid_fits_processing_parity.json').read_text())
        with app.app_context():
            original=deepcopy(db.session.get(IndiAllSkyDbConfigTable,1).data)
            root=Path(app.config['INDI_ALLSKY_IMAGE_FOLDER'])
            for cid in (1,2):
                source=db.session.get(IndiAllSkyDbFitsImageTable,cid)
                for kind,model in (('dark',IndiAllSkyDbDarkFrameTable),('bpm',IndiAllSkyDbBadPixelMapTable)):
                    target=root/(kind+'-'+str(cid)+'.fit');copyfile(source.filename,target)
                    db.session.add(model(id=cid,camera_id=cid,filename=str(target),bitdepth=16,exposure=1,gain=10,binmode=1,temp=15,width=64,height=48,data={}))
            db.session.commit()
        for client in (admin,user):
            for cid in (1,2):
                response=client.get(page,query_string={'camera_id':cid,'profile_id':'test-profile-'+str(cid)})
                assert response.status_code==200,response.text[:200]
                payload,headers=payload_from_page(app,response.text)
                assert payload['CAMERA_ID']==str(cid) and payload['FITS_ID']==str(cid)
                payload.update(IMAGE_LABEL_SYSTEM='',IMAGE_STACK_COUNT='1')
                for disabled in (True,False):
                    payload['DISABLE_PROCESSING']=disabled
                    result=client.post(endpoint,json=payload,headers=headers)
                    assert result.status_code==200,result.json
                    binary=base64.b64decode(result.json['image_b64'])
                    assert binary.startswith(b'\xff\xd8') and result.json['mime_type']=='image/jpeg'
                    pixels=cv2.imdecode(np.frombuffer(binary,np.uint8),cv2.IMREAD_UNCHANGED)
                    assert list(pixels.shape)==[48,64,3]
                    assert hashlib.sha256(pixels.tobytes()).hexdigest()==baseline['jpeg_pixels_sha256'][str(cid)]
                png=client.post(endpoint,json=dict(payload,OUTPUT_IMAGE_TYPE='png'),headers=headers)
                assert png.status_code==200,png.json
                assert base64.b64decode(png.json['image_b64']).startswith(b'\x89PNG\r\n\x1a\n')
                assert png.json['mime_type']=='image/png' and png.json['camera_id']==cid
        payload,headers=payload_from_page(app,admin.get(page+'?camera_id=2').text)
        payload.update(IMAGE_LABEL_SYSTEM='',IMAGE_STACK_COUNT='1')
        for kind in ('dark','bpm'):
            response=admin.get(page,query_string={'camera_id':2,'type':kind,'id':2})
            body,header=payload_from_page(app,response.text)
            body.update(DISABLE_PROCESSING=True,IMAGE_STACK_COUNT='1')
            result=admin.post(endpoint,json=body,headers=header)
            assert result.status_code==200,result.json
            assert admin.post(endpoint,json=dict(body,IMAGE_STACK_COUNT='2'),headers=header).status_code==400
        assert admin.post(endpoint,json=payload).status_code==400
        assert app.test_client().get(page).status_code==302
        assert app.test_client().post(endpoint,json=payload,headers=headers).status_code==400
        for bad in ([],{},None):assert admin.post(endpoint,json=bad,headers=headers).status_code==400
        for change in ({'CAMERA_ID':'bad'},{'FITS_ID':-1},{'FRAME_TYPE':'bad'},{'OUTPUT_IMAGE_TYPE':'svg'},{'GAMMA_CORRECTION':'nan'},{'IMAGE_EXTRA_TEXT':[]}):
            assert admin.post(endpoint,json=dict(payload,**change),headers=headers).status_code==400,change
        assert admin.post(endpoint,json=dict(payload,FITS_ID=1),headers=headers).status_code==404
        assert admin.get(page+'?camera_id=2&id=1').status_code==404
        assert admin.get(page+'?camera_id=1&profile_id=test-profile-2').status_code==400
        assert admin.get(page+'?profile_id=missing').status_code==400
        assert admin.get(page+'?type=invalid').status_code==400
        private,privateheaders=payload_from_page(app,user.get(page+'?camera_id=2').text)
        assert user.post(endpoint,json=dict(private,IMAGE_EXTRA_TEXT='/etc/passwd'),headers=privateheaders).status_code==403
        for name in ('DETECT_MASK','TEXT_PROPERTIES__PIL_FONT_CUSTOM'):
            assert user.post(endpoint,json=dict(private,**{name:'/etc/passwd'}),headers=privateheaders).status_code==403
        from astropy.io import fits
        opened=[]; original_open=fits.open
        def tracked_open(*args,**kwargs):
            hdus=original_open(*args,**kwargs);opened.append(hdus);return hdus
        with patch('astropy.io.fits.open',side_effect=tracked_open):
            assert admin.post(endpoint,json=payload,headers=headers).status_code==200
        assert opened and all(hdus._file is None or hdus._file.closed for hdus in opened)
        insufficient=admin.post(endpoint,json=dict(payload,IMAGE_STACK_COUNT='2',IMAGE_STACK_ALIGN=False),headers=headers)
        assert insufficient.status_code==200,insufficient.json
        assert 'Stacked 1 images (requested 2)' in insufficient.json['message'], insufficient.json['message']
        with app.app_context():
            target=root/'stack-previous.fit';copyfile(db.session.get(IndiAllSkyDbFitsImageTable,2).filename,target)
            db.session.add(IndiAllSkyDbFitsImageTable(id=3,camera_id=2,filename=str(target),createDate=datetime(2020,1,1),dayDate=datetime(2020,1,1).date(),exposure=.5,gain=20,width=64,height=48,data={}))
            db.session.commit()
        stacked=admin.post(endpoint,json=dict(payload,IMAGE_STACK_COUNT='2',IMAGE_STACK_ALIGN=False),headers=headers)
        assert stacked.status_code==200,stacked.json
        assert 'Stacked 2 images' in stacked.json['message'], stacked.json['message']
        before=deepcopy(original)
        variant=dict(payload,IMAGE_STRETCH__MODE1_GAMMA=4.5,FISH2PANO__DIAMETER=500)
        changed=processing_config(before,variant)
        assert before==original and changed['IMAGE_STRETCH']['MODE1_GAMMA']==4.5
        assert changed['FISH2PANO'] is not before['FISH2PANO']
        with patch('indi_allsky.flask.image_processing_views.processing_config',side_effect=SQLAlchemyError('private detail')):
            failed=admin.post(endpoint,json=payload,headers=headers)
            assert failed.status_code==503 and 'private detail' not in failed.text
        source=root/'ccd_test-camera-2/source-camera-2.fit'
        backup=source.read_bytes()
        source.write_bytes(b'not a FITS file')
        assert admin.post(endpoint,json=payload,headers=headers).status_code==422
        source.write_bytes(backup)
        with patch('cv2.imencode',return_value=(False,None)):
            assert admin.post(endpoint,json=payload,headers=headers).status_code==422
        hidden=source.with_suffix('.hidden');source.rename(hidden)
        assert admin.post(endpoint,json=payload,headers=headers).status_code==404
        hidden.rename(source)
        with app.app_context():
            camera=db.session.get(IndiAllSkyDbCameraTable,2)
            camera.web_nonlocal_images=True;camera.web_local_images_admin=False
            db.session.commit()
        assert admin.post(endpoint,json=payload,headers=headers).status_code==403
        assert 'Local FITS processing is unavailable' in admin.get(page+'?camera_id=2').text
        with app.app_context():
            assert IndiAllSkyDbConfigTable.query.count()==1 and db.session.get(IndiAllSkyDbConfigTable,1).data==original
            assert IndiAllSkyDbTaskQueueTable.query.count()==0
            IndiAllSkyDbFitsImageTable.query.filter_by(camera_id=1).delete();db.session.commit()
        assert 'No light FITS frames' in admin.get(page+'?camera_id=1').text
        print('FITS processing: original pixel parity, real PNG/JPEG, two cameras/roles, dark/BPM, isolated config, CSRF, failures and media policy: PASS')

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--runtime-config',default='/etc/indi-allsky/flask.json')
    run(parser.parse_args().runtime_config)
