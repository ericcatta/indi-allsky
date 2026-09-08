#!/usr/bin/env python3
"""Real panorama transform/encoding, files, SQL and Hybrid download acceptance."""
from copy import deepcopy
from datetime import datetime,timedelta
from pathlib import Path
from queue import Queue
from types import SimpleNamespace,MethodType
from unittest.mock import patch
import hashlib,html,io,json,logging,re,shutil,tempfile
from hybrid_runtime_fixture import isolated_app,login_client


def run():
    import cv2
    import numpy as np
    from PIL import Image
    with isolated_app(multi_camera=True) as app:
        from indi_allsky.flask import db
        from indi_allsky.flask.models import IndiAllSkyDbConfigTable as Config,IndiAllSkyDbCameraTable as Camera,IndiAllSkyDbPanoramaImageTable as Panorama
        from indi_allsky.image import ImageWorker
        from indi_allsky.processing import ImageProcessor
        from indi_allsky.flask.miscDb import miscDb
        from indi_allsky.miscUpload import miscUpload
        from indi_allsky.panorama_publication import encode_panorama
        root=Path(app.config['INDI_ALLSKY_IMAGE_FOLDER'])
        with app.app_context():config=deepcopy(db.session.get(Config,1).data)
        config.update(MULTI_CAMERA_CAPTURE_ENABLE=True,IMAGE_FILE_TYPE='jpg',DAYTIME_CAPTURE=True,DAYTIME_CAPTURE_SAVE=True)
        config['FILETRANSFER']={};config['S3UPLOAD']={'ENABLE':False};config['SYNCAPI']={'ENABLE':False};config['MQTTPUBLISH']={'ENABLE':False}
        config['FISH2PANO'].update(ENABLE=True,DIAMETER=40,SCALE=1,ROTATE_ANGLE=0)
        instant=datetime.now().replace(microsecond=0)
        def reference(cid,offset=0):
            return SimpleNamespace(exp_date=instant+timedelta(seconds=offset),day_date=instant.date(),camera_id=cid,camera_uuid='test-camera-'+str(cid),
                exposure=2.0,gain=4,binning=1,sqm_value=20,stars=[],lines=[],kpindex=0,ovation_max=0,smoke_rating=0,
                aurora_mag_bt=None,aurora_mag_gsm_bz=None,aurora_plasma_density=None,aurora_plasma_speed=None,aurora_plasma_temp=None,aurora_n_hemi_gw=None,aurora_s_hemi_gw=None)
        from indi_allsky.capture_profiles import derive_capture_profiles,build_profile_config
        from indi_allsky.hybrid_camera_management import multicamera_capture_outputs
        from dataclasses import replace
        config['FILETRANSFER']['UPLOAD_PANORAMA']=1
        profiles=derive_capture_profiles(config)
        effective=build_profile_config(config,replace(profiles[0],outputs=multicamera_capture_outputs(profiles[0].outputs)))
        assert effective['FISH2PANO']['ENABLE'] and effective['FILETRANSFER']['UPLOAD_PANORAMA'] is False
        upload_queue=Queue()
        worker=SimpleNamespace(config=config,image_dir=root,filename_t='ccd{0:d}_{1:s}.{2:s}',night_av=[1,0],
            _miscDb=miscDb(config),_miscUpload=miscUpload(effective,upload_queue,[1,0]))
        worker._getImageFolder=MethodType(ImageWorker._getImageFolder,worker)
        def processor(cid):
            data=(np.arange(48*64*3).reshape(48,64,3)+cid*37).astype(np.uint8)
            p=SimpleNamespace(config=config,image=data,astrometric_data={'moon_phase':25},camera_sqm_raw_mag=20)
            p.fish2pano_warpPolar=MethodType(ImageProcessor.fish2pano_warpPolar,p)
            worker.image_processor=p
            return ImageProcessor.fish2pano(p,1)
        data=processor(1)
        fixture=json.loads((Path(__file__).parent/'fixtures/hybrid_panorama_publication_legacy.json').read_text())
        assert fixture['sha256']=='7e2e063d5f72383f838750b2f0b95d05405ec1e4b21d471df10db055397979c3'
        assert hashlib.sha256(fixture['source'].encode()).hexdigest()==fixture['sha256']
        namespace={'__name__':'legacy','Path':Path,'tempfile':tempfile,'shutil':shutil,'cv2':cv2,'Image':Image,'logger':logging.getLogger('test')}
        from indi_allsky import constants
        namespace['constants']=constants;exec(fixture['source'],namespace)
        paths=[]
        no_upload=SimpleNamespace(**{name:lambda *args:None for name in ('syncapi_panorama','s3_upload_panorama','mqtt_publish_image','upload_panorama')})
        old=SimpleNamespace(**worker.__dict__);old.image_dir=root/'legacy'
        old.image_dir.mkdir()
        old._getImageFolder=MethodType(ImageWorker._getImageFolder,old)
        old._miscDb=SimpleNamespace(addPanoramaImage=lambda filename,*args:paths.append(old.image_dir/filename))
        old._miscUpload=no_upload
        parity=[]
        for extension in ('jpg','jpeg','png','webp','tif','tiff'):
            config['IMAGE_FILE_TYPE']=extension
            namespace['write_panorama_img'](old,data,reference(1),SimpleNamespace(id=1,uuid='test-camera-1'),jpeg_exif=b'')
            with Image.open(paths[-1]) as before,Image.open(io.BytesIO(encode_panorama(data,config,b''))) as after:
                assert before.size==after.size and np.array_equal(np.array(before),np.array(after)),extension
            parity.append(extension)
        config['IMAGE_FILE_TYPE']='jpg'
        saved={};previews={}
        with app.app_context():
            for cid in (1,2):
                data=processor(cid);camera=db.session.get(Camera,cid)
                entry=ImageWorker.write_panorama_img(worker,data,reference(cid),camera,jpeg_exif=b'',write_latest=cid==1)
                assert entry is not None
                path=root/entry.filename
                assert path.is_file() and entry.fileSize==path.stat().st_size and entry.camera_id==cid
                with Image.open(path) as image:assert image.size==(data.shape[1],data.shape[0])
                saved[cid]=(entry.id,path.read_bytes())
                previews[cid]=(root/('ccd_test-camera-'+str(cid))/'panorama.jpg').read_bytes()
            assert (root/'panorama.jpg').read_bytes()==previews[1] and previews[1]!=previews[2]
            camera=db.session.get(Camera,2);data=processor(2)
            assert ImageWorker.write_panorama_img(worker,data,reference(2),camera,write_latest=False) is None
            assert Panorama.query.count()==2
            assert ImageWorker.write_panorama_img(worker,data,reference(1),camera,write_latest=False) is None
            assert Panorama.query.count()==2
            before_files=set(root.rglob('panorama_ccd*'))
            def failed_sql(*args):
                db.session.add(Panorama(filename='invalid',camera_id=None))
                db.session.commit()
            with patch.object(worker._miscDb,'addPanoramaImage',side_effect=failed_sql):
                assert ImageWorker.write_panorama_img(worker,data,reference(2,10),camera,write_latest=False) is None
            assert Panorama.query.count()==2 and set(root.rglob('panorama_ccd*'))==before_files
            with patch('indi_allsky.panorama_publication.os.link',side_effect=OSError('fixture full disk')):
                assert ImageWorker.write_panorama_img(worker,data,reference(2,20),camera,write_latest=False) is None
            assert Panorama.query.count()==2 and set(root.rglob('panorama_ccd*'))==before_files
            assert (root/'ccd_test-camera-2'/'panorama.jpg').read_bytes()==previews[2]
            config['IMAGE_FILE_TYPE']='png'
            with patch('cv2.imencode',return_value=(False,None)):
                assert ImageWorker.write_panorama_img(worker,data,reference(2,30),camera,write_latest=False) is None
            config['IMAGE_FILE_TYPE']='jpg'
            with patch.object(worker._miscUpload,'syncapi_panorama',side_effect=OSError('fixture effect failed')):
                entry=ImageWorker.write_panorama_img(worker,data,reference(2,40),camera,write_latest=False)
                assert entry is not None and (root/entry.filename).is_file()
            with patch('indi_allsky.panorama_publication.os.replace',side_effect=OSError('fixture preview failed')):
                entry=ImageWorker.write_panorama_img(worker,255-data,reference(2,45),camera,write_latest=False)
                assert entry is not None and (root/entry.filename).is_file()
            assert (root/'ccd_test-camera-2'/'panorama.jpg').read_bytes()==previews[2]
            count=Panorama.query.count()
            config['FOCUS_MODE']=True
            assert ImageWorker.write_panorama_img(worker,data,reference(2,50),camera,write_latest=False) is None
            config['FOCUS_MODE']=False;config['DAYTIME_CAPTURE_SAVE']=False;worker.night_av=[0,0]
            assert ImageWorker.write_panorama_img(worker,data,reference(2,60),camera,write_latest=False) is None
            assert Panorama.query.count()==count
            assert upload_queue.empty() and not list(root.rglob('.panorama-*'))
        for uid in (1,2):
            client=login_client(app,uid)
            for cid,(entry_id,content) in saved.items():
                page=client.get('/indi-allsky/modern-admin/output',query_string={'kind':'panorama','id':entry_id,'camera_id':cid,'profile_id':'test-profile-'+str(cid)})
                assert page.status_code==200,page.text[:300]
                link=re.search(r'href="([^"]+/download)"',page.text)
                assert link,page.text
                download=client.get(html.unescape(link[1]))
                assert download.status_code==200 and download.data==content
        with app.app_context():
            row=db.session.get(Config,1)
            updated=deepcopy(row.data);updated['FOCUS_MODE']=True
            row.data=updated;db.session.commit()
        client=login_client(app,1)
        for cid in (1,2):
            result=client.get('/indi-allsky/js/latest_panorama',query_string={'camera_id':cid,'night':0})
            assert result.status_code==200,result.text
            url=result.json['latest_image']['url']
            assert '/ccd_test-camera-'+str(cid)+'/panorama.jpg' in url,url
            response=client.get('/indi-allsky/'+url)
            assert response.status_code==200 and response.data==(root/('ccd_test-camera-'+str(cid))/'panorama.jpg').read_bytes()
        (root/'ccd_test-camera-2'/'panorama.jpg').unlink()
        missing=client.get('/indi-allsky/js/latest_panorama?camera_id=2&night=0')
        assert missing.json['latest_image']['url'] is None
        assert (root/'panorama.jpg').is_file()
        with app.app_context():
            row=db.session.get(Config,1);updated=deepcopy(row.data);updated['FOCUS_MODE']=False;row.data=updated
            camera=db.session.get(Camera,1);camera.daytime_capture=True;camera.daytime_capture_save=False
            db.session.commit()
        day=client.get('/indi-allsky/js/latest_panorama?camera_id=1&night=0')
        assert 'ccd_test-camera-1/panorama.jpg' in day.json['latest_image']['url'],day.text
        print(json.dumps({'scope':'Classic-disabled isolated Flask; real warpPolar, six codecs, file publication, SQL and downloads; synthetic frames',
            'pixel_parity_formats':parity,'camera_isolation':'Separate previews; global compatibility preview remains primary; mismatched frame/camera rejected',
            'profile_policy':'Panorama setting honored; global upload enabled but profile opt-out keeps queue empty',
            'failures':'Duplicate/archive write/encoding/SQL errors leave no false new DB entry; SQL failure removes own archive; previous preview retained',
            'optional_effect':'Failed upload enqueue does not remove valid local archive',
            'preview_only':'Focus and no-day-save do not create archive rows',
            'downloads':'Both roles receive matching per-camera saved bytes',
            'latest_api':'Focus and no-day-save resolve the requested camera; missing secondary preview never falls back to primary'},indent=2))

if __name__=='__main__':run()
