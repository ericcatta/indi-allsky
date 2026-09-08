#!/usr/bin/env python3
"""Alternating real ImageProcessors, per-camera history reload and corruption recovery."""
from copy import deepcopy
from multiprocessing import Array
from pathlib import Path
from types import SimpleNamespace,MethodType
from unittest.mock import patch
import json
import ast
import re
import html
from urllib.parse import urljoin
from queue import Queue
import numpy as np
from hybrid_runtime_fixture import isolated_app,login_client


def run():
    with isolated_app(multi_camera=True) as app:
        from indi_allsky.image import ImageWorker
        from indi_allsky.config import IndiAllSkyConfigBase
        config=deepcopy(IndiAllSkyConfigBase().base_config)
        root=Path(app.config['INDI_ALLSKY_IMAGE_FOLDER'])
        config.update(MULTI_CAMERA_CAPTURE_ENABLE=True,IMAGE_FOLDER=str(root),VARLIB_FOLDER=str(root),KEOGRAM_ANGLE=0)
        config['REALTIME_KEOGRAM'].update(MAX_ENTRIES=5,LABEL=False)
        def new_worker():
            w=SimpleNamespace(config=deepcopy(config),image_processors={},image_processor=None,
                position_av=Array('f',[46,8,200]),gain_av=Array('f',[0]*8),binning_av=Array('i',[1]),
                sensors_temp_av=Array('f',[0]*60),sensors_user_av=Array('f',[0]*110),
                night_av=Array('i',[1,0]),astro_av=Array('f',[0]*3),_images_only_diag=lambda *a,**kw:None)
            w._new_image_processor=MethodType(ImageWorker._new_image_processor,w)
            return w
        def select(w,cid):
            ImageWorker._select_image_processor(w,'profile-'+str(cid),cid,False)
            p=w.image_processor
            # Same camera-keyed filenames assigned by ImageProcessor._add; no real sensor input.
            p._keogram_store_p=root/p._keogram_store_tmpl.format(cid)
            p._keogram_store_metadata_p=root/p._keogram_store_metadata_tmpl.format(cid)
            p.image=np.full((48 if cid==1 else 64,64,3),(cid*30,60,180-cid*20),np.uint8)
            return p
        from indi_allsky.hybrid_camera_management import multicamera_capture_outputs
        tree=ast.parse((Path(__file__).resolve().parents[1]/'indi_allsky/image.py').read_text())
        process=next(n for n in ast.walk(tree) if isinstance(n,ast.FunctionDef) and n.name=='processImage')
        gate=next(n for n in process.body if isinstance(n,ast.If) and "profile_outputs.get('realtime_keogram'" in ast.unparse(n.test))
        gate_code=compile(ast.Module(body=[gate],type_ignores=[]),'image.py:realtime-gate','exec')
        def update(w,cid,outputs=None,images_only=False):
            import logging
            exec(gate_code,dict(self=w,profile_outputs=multicamera_capture_outputs(outputs or {}),
                images_only=images_only,profile_id='profile-'+str(cid),camera_id=cid,logger=logging.getLogger('test')))
        worker=new_worker()
        expected={}
        for index in range(8):
            for cid in (1,2):
                p=select(worker,cid)
                with patch('indi_allsky.processing.time.time',return_value=10000+index*15):update(worker,cid)
                assert p.realtime_keogram_data.shape[1]==min(index+1,5)
                assert len(p.realtime_keogram_timestamps)==min(index+1,5)
                expected[cid]=(p.realtime_keogram_data.copy(),list(p.realtime_keogram_timestamps))
        ImageWorker._save_realtime_keogram_processors(worker)
        restarted=new_worker()
        for cid in (1,2):
            p=select(restarted,cid)
            data,timestamps=p.realtimeKeogramDataLoad()
            assert np.array_equal(data,expected[cid][0])
            assert list(timestamps)==expected[cid][1]
            with patch('indi_allsky.processing.time.time',return_value=10200):p.realtimeKeogramUpdate()
            assert p.realtime_keogram_data.shape[1]==5
            assert p.realtime_keogram_timestamps==expected[cid][1][1:]+[10200]
            assert np.array_equal(p.realtime_keogram_data[:,:4],expected[cid][0][:,1:])
        # Syntactically valid NumPy with wrong metadata shape must not kill capture.
        np.save(select(restarted,1)._keogram_store_metadata_p,np.array(3))
        recovered=select(new_worker(),1)
        recovered.realtimeKeogramUpdate()
        assert recovered.realtime_keogram_data.shape[1]==1
        assert len(recovered.realtime_keogram_timestamps)==1
        other_data,other_times=select(new_worker(),2).realtimeKeogramDataLoad()
        assert np.array_equal(other_data,expected[2][0]) and list(other_times)==expected[2][1]
        unreadable=select(new_worker(),1)
        with patch.object(unreadable,'realtimeKeogramDataLoad',side_effect=PermissionError('fixture unreadable cache')):
            unreadable.realtimeKeogramUpdate()
        assert unreadable.realtime_keogram_data.shape[1]==1
        undiscardable=select(new_worker(),1)
        with patch.object(undiscardable,'realtimeKeogramDataLoad',side_effect=ValueError('fixture invalid cache')), patch('pathlib.Path.unlink',side_effect=PermissionError('fixture protected cache')):
            undiscardable.realtimeKeogramUpdate()
        assert undiscardable.realtime_keogram_data.shape[1]==1
        from indi_allsky.miscUpload import miscUpload
        from indi_allsky.capture_profiles import derive_capture_profiles,build_profile_config
        from dataclasses import replace
        profile=derive_capture_profiles(config)[0]
        config['FILETRANSFER']['UPLOAD_REALTIME_KEOGRAM']=1
        effective=build_profile_config(config,replace(profile,outputs=multicamera_capture_outputs(profile.outputs)))
        assert effective['FILETRANSFER']['UPLOAD_REALTIME_KEOGRAM'] is False
        upload_queue=Queue()
        restarted._miscUpload=miscUpload(effective,upload_queue,restarted.night_av)
        restarted.image_dir=root
        restarted.image_count=1
        restarted.config=effective
        files={}
        for cid in (1,2):
            p=select(restarted,cid)
            prior=p.realtime_keogram_data.copy()
            update(restarted,cid,{'realtime_keogram':False})
            assert np.array_equal(prior,p.realtime_keogram_data)
            update(restarted,cid,images_only=True)
            assert np.array_equal(prior,p.realtime_keogram_data)
            camera=SimpleNamespace(id=cid,uuid='test-camera-'+str(cid))
            ImageWorker.write_realtime_keogram(restarted,p.realtime_keogram_trimmed,camera)
            files[cid]=root/('ccd_test-camera-'+str(cid))/('realtime_keogram.'+config['IMAGE_FILE_TYPE'])
            assert files[cid].is_file() and files[cid].stat().st_size>0
        saved=[]
        effective['REALTIME_KEOGRAM']['SAVE_INTERVAL']=2
        for cid in (1,2):
            p=select(restarted,cid)
            p.realtime_save_count=0
            original=p.realtimeKeogramDataSave
            p.realtimeKeogramDataSave=lambda cid=cid,original=original:(saved.append(cid),original())[1]
        for count,cid in enumerate((1,2,1,2),1):
            p=select(restarted,cid)
            restarted.image_count=count
            ImageWorker.write_realtime_keogram(restarted,p.realtime_keogram_trimmed,
                SimpleNamespace(id=cid,uuid='test-camera-'+str(cid)))
        assert saved==[1,2],saved
        assert upload_queue.empty()
        for uid in (1,2):
            client=login_client(app,uid)
            for cid in (1,2):
                page=client.get('/indi-allsky/modern-admin/observatory/realtime-keogram?profile_id=test-profile-'+str(cid))
                assert page.status_code==200,page.text[:400]
                assert 'Test Camera '+str(cid) in page.text and 'Saved preview available.' in page.text
                src=html.unescape(re.search(r'id="modern-admin-keogram-image"[^>]*src="([^"]+)"',page.text)[1])
                assert 'ccd_test-camera-'+str(cid) in src
                download=client.get(urljoin(page.request.path,src))
                assert download.status_code==200 and download.data==files[cid].read_bytes()
            for query,code in [('camera_id=999',404),('camera_id=bad',400),('camera_id=1&profile_id=test-profile-2',400)]:
                assert client.get('/indi-allsky/modern-admin/observatory/realtime-keogram?'+query).status_code==code
        files[1].unlink()
        page=client.get('/indi-allsky/modern-admin/observatory/realtime-keogram?camera_id=1')
        assert 'No realtime keogram has been generated' in page.text
        assert '<img id="modern-admin-keogram-image" src=' not in page.text
        assert app.test_client().get('/indi-allsky/modern-admin/observatory/realtime-keogram').status_code==302
        print(json.dumps({'scope':'Real processors/generator and temporary NumPy stores; synthetic BGR frames',
            'alternating_frames':16,'history_limit':5,'periodic_save':'Each camera saved after its own two frames','restart':'Both camera histories restored exactly and continued',
            'corrupt_metadata':'Camera 1 resets; camera 2 history unchanged',
            'cache_io_errors':'Unreadable or non-removable cache does not prevent the next sample',
            'preview':'Actual worker publication and matching Flask downloads for both cameras and roles',
            'profile_guards':'Opt-out and images-only respected; upload queue remains empty',
            'selection':'Unknown/mismatched cameras rejected; missing file explicit; anonymous login required'},indent=2))

if __name__=='__main__':run()
