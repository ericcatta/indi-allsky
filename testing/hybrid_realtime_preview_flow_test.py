#!/usr/bin/env python3
"""Real encoding/publishing parity and failure recovery without live capture."""
import hashlib
import json
import logging
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
import tempfile
import shutil
from hybrid_runtime_fixture import isolated_app


def run():
    import cv2
    import numpy as np
    from PIL import Image
    with isolated_app(multi_camera=True) as app:
        from indi_allsky.image import ImageWorker
        from indi_allsky.realtime_keogram_preview import publish_realtime_keogram
        from indi_allsky.config import IndiAllSkyConfigBase
        from copy import deepcopy
        root=Path(app.config['INDI_ALLSKY_IMAGE_FOLDER'])
        fixture=json.loads((Path(__file__).parent/'fixtures/hybrid_realtime_preview_legacy.json').read_text())
        assert fixture['sha256']=='e55ada856462179112e59fe19d6ca33509229717c4e7c58f5131a2facaa17e8a'
        assert hashlib.sha256(fixture['source'].encode()).hexdigest()==fixture['sha256']
        namespace=dict(cv2=cv2,Image=Image,Path=Path,tempfile=tempfile,shutil=shutil,logger=logging.getLogger('test'))
        exec(fixture['source'],namespace)
        old=namespace['write_realtime_keogram']
        camera=SimpleNamespace(uuid='test-camera-1',id=1)
        config=deepcopy(IndiAllSkyConfigBase().base_config)
        config.update(KEOGRAM_H_SCALE=100,KEOGRAM_V_SCALE=33)
        data=(np.arange(48*12*3).reshape(48,12,3)%255).astype(np.uint8)
        uploaded=[]
        worker=SimpleNamespace(config=config,image_count=1,image_dir=root/'old',
            image_processor=SimpleNamespace(realtimeKeogramApplyLabels=lambda x:x),
            _miscUpload=SimpleNamespace(upload_realtime_keogram=lambda p,c:uploaded.append((p,c.id))))
        formats=[]
        for extension in ('jpg','jpeg','png','webp','tif','tiff'):
            config['IMAGE_FILE_TYPE']=extension
            old(worker,data,camera)
            previous=uploaded[-1][0]
            target=publish_realtime_keogram(root/'new',camera.uuid,data,config,lambda x:x)
            with Image.open(previous) as a,Image.open(target) as b:
                assert a.size==b.size and np.array_equal(np.array(a),np.array(b)),extension
            formats.append(extension)
        config['IMAGE_FILE_TYPE']='jpg'
        target=publish_realtime_keogram(root/'new',camera.uuid,data,config,lambda x:x)
        before=target.read_bytes()
        for failure in ('encoder','replace'):
            context=patch('cv2.imwrite',return_value=False) if failure=='encoder' else patch('indi_allsky.realtime_keogram_preview.os.replace',side_effect=OSError('fixture disk failure'))
            worker.image_dir=root/'new';count=len(uploaded)
            with context:
                ImageWorker.write_realtime_keogram(worker,data,camera)
            assert target.read_bytes()==before and len(uploaded)==count
            assert not list(target.parent.glob('.realtime-*'))
        config['KEOGRAM_H_SCALE']=25
        tiny=data[:3,:1]
        target=publish_realtime_keogram(root/'new',camera.uuid,tiny,config,lambda x:x)
        with Image.open(target) as image:assert image.size==(1,1)
        other=publish_realtime_keogram(root/'new','test-camera-2',data,config,lambda x:x)
        assert other!=target and target.exists()
        try:publish_realtime_keogram(root,'../../../escape',data,config,lambda x:x)
        except ValueError:pass
        else:raise AssertionError('Escaping camera path accepted')
        saved=[]
        def fail_store():
            saved.append('failed')
            raise OSError('fixture store failure')
        first=SimpleNamespace(realtimeKeogramDataSave=fail_store)
        second=SimpleNamespace(realtimeKeogramDataSave=lambda:saved.append('second'))
        ImageWorker._save_realtime_keogram_processors(SimpleNamespace(
            image_processors={'profile-1:1':first,'profile-2:2':second},image_processor=second))
        assert saved==['failed','second'],saved
        worker.image_processor.realtimeKeogramDataSave=fail_store
        worker.image_count=25
        count=len(uploaded)
        ImageWorker.write_realtime_keogram(worker,data,camera)
        assert len(uploaded)==count+1 and uploaded[-1][0].is_file()
        from indi_allsky.capture_profiles import derive_capture_profiles,build_profile_config
        from dataclasses import replace
        profile=derive_capture_profiles(config)[0]
        config['FILETRANSFER']['UPLOAD_REALTIME_KEOGRAM']=1
        effective=build_profile_config(config,replace(profile,outputs=dict(profile.outputs,extra_uploads=False)))
        assert effective['FILETRANSFER']['UPLOAD_REALTIME_KEOGRAM'] is False
        print(json.dumps({'scope':'Isolated real codecs and ImageWorker publish adapter; no live camera',
            'formats_with_exact_decoded_pixel_parity':formats,'failed_write_preserves_previous':True,
            'failed_write_does_not_upload':True,'first_column_below_100_percent':'1x1 valid output',
            'camera_isolation':True,'temporary_files_cleaned':True,
            'shutdown':'All processors attempted once, including after store failure',
            'store_failure':'Preview publication still succeeds',
            'upload_opt_out':'Profile extra_uploads false also disables realtime uploads'},indent=2))

if __name__=='__main__':run()
