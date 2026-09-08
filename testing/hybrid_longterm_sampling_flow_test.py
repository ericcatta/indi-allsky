#!/usr/bin/env python3
"""Actual worker sampling -> camera-scoped DB -> Hybrid generated JPEG, isolated."""
import ast
import base64
from copy import deepcopy
from datetime import datetime,timedelta
import hashlib
import io
import json
import logging
from pathlib import Path
import re
from types import SimpleNamespace,MethodType
from unittest.mock import patch
from hybrid_runtime_fixture import isolated_app,login_client


def run():
    import numpy as np
    from PIL import Image
    with isolated_app(multi_camera=True) as app:
        from indi_allsky.flask import db
        from indi_allsky.flask.models import IndiAllSkyDbLongTermKeogramTable as Sample, IndiAllSkyDbConfigTable as Config
        from indi_allsky.flask.miscDb import miscDb
        from indi_allsky.image import ImageWorker
        from indi_allsky.capture_profiles import derive_capture_profiles,build_profile_config
        from indi_allsky.hybrid_camera_management import multicamera_capture_outputs
        from indi_allsky.longterm_keogram_sampling import longterm_keogram_pixels
        root=Path(__file__).resolve().parents[1]
        legacy=json.loads((root/'testing/fixtures/hybrid_longterm_sampling_legacy.json').read_text())
        assert legacy['sha256']=='8289093d7559704d807e111393a048ca41c32ef9bf9355db36900301d85c844f'
        assert hashlib.sha256(legacy['source'].encode()).hexdigest()==legacy['sha256']
        logger=logging.getLogger('indi_allsky');logger.setLevel(logging.WARNING);logger.propagate=False
        messages=[];handler=logging.Handler();handler.emit=lambda record:messages.append(record.getMessage());logger.addHandler(handler)
        namespace={'logger':logger};exec(legacy['source'],namespace)
        parity_count=0
        for height,width in ((5,3),(12,10),(48,64)):
            pixels=(np.arange(height*width*3).reshape(height,width,3)%255).astype(np.uint8)
            for x in (0,width//2,width-1):
                for y in (0,(height-5)//2,height-5):
                    offsets={'ENABLE':True,'OFFSET_X':x-width//2,'OFFSET_Y':height//2-y}
                    old=SimpleNamespace(config={'LONGTERM_KEOGRAM':offsets},image_processor=SimpleNamespace(focus_mode=False,image=pixels),
                        _miscDb=SimpleNamespace(add_long_term_keogram_data=lambda *args:None))
                    expected=namespace['save_longterm_keogram_data'](old,datetime.now(),1)
                    assert longterm_keogram_pixels(pixels,offsets['OFFSET_X'],offsets['OFFSET_Y'])==expected
                    parity_count+=1
        with app.app_context():
            config=deepcopy(db.session.get(Config,1).data);original=deepcopy(config)
            config['MULTI_CAMERA_CAPTURE_ENABLE']=True
            config['LONGTERM_KEOGRAM']={'ENABLE':True,'OFFSET_X':0,'OFFSET_Y':0}
            profiles=derive_capture_profiles(config)
            writer=miscDb(config)
            worker=SimpleNamespace(config=config,_miscDb=writer,image_processor=SimpleNamespace(focus_mode=False,image=None))
            worker.save_longterm_keogram_data=MethodType(ImageWorker.save_longterm_keogram_data,worker)
            # Execute the original processImage gate as well as the real worker method.
            tree=ast.parse((root/'indi_allsky/image.py').read_text())
            process=next(n for n in ast.walk(tree) if isinstance(n,ast.FunctionDef) and n.name=='processImage')
            gate=next(n for n in process.body if isinstance(n,ast.If) and "profile_outputs.get('longterm_keogram'" in ast.unparse(n.test))
            gate_code=compile(ast.Module(body=[gate],type_ignores=[]),'image.py:longterm-gate','exec')
            def capture(cid,when,outputs,images_only=False):
                env=dict(self=worker,profile_outputs=outputs,images_only=images_only,profile_id='test-profile-'+str(cid),
                         camera_id=cid,exp_date=when,logger=logger)
                exec(gate_code,env)
                return env['longterm_keogram_pixels']
            start=datetime.now().replace(hour=16,minute=0,second=0,microsecond=0)-timedelta(days=1)
            for index in range(120):
                for cid,profile in enumerate(profiles,1):
                    worker.config=build_profile_config(config,profile)
                    worker.image_processor.image=np.full((48,64,3),(cid*30,40,180-cid*20),dtype=np.uint8)
                    result=capture(cid,start+timedelta(seconds=60*index),multicamera_capture_outputs(profile.outputs))
                    assert result==[[180-cid*20,40,cid*30]]*5
            assert Sample.query.filter_by(camera_id=1).count()==Sample.query.filter_by(camera_id=2).count()==120
            for cid in (1,2):
                for row in Sample.query.filter_by(camera_id=cid):
                    assert (row.r1,row.g1,row.b1)==(180-cid*20,40,cid*30)
            count=Sample.query.count()
            assert capture(2,start,{'longterm_keogram':False}) is None
            assert capture(2,start,{'longterm_keogram':True},images_only=True) is None
            worker.image_processor.focus_mode=True
            assert capture(2,start,{'longterm_keogram':True}) is None
            worker.image_processor.focus_mode=False
            worker.config['LONGTERM_KEOGRAM']['ENABLE']=False
            assert capture(2,start,{'longterm_keogram':True}) is None
            worker.config['LONGTERM_KEOGRAM']['ENABLE']=True
            for x,y in ((-33,0),(32,0),(0,25),(0,-24),(None,0)):
                worker.config['LONGTERM_KEOGRAM'].update(OFFSET_X=x,OFFSET_Y=y)
                assert capture(2,start,{'longterm_keogram':True}) is None
            worker.config['LONGTERM_KEOGRAM'].update(OFFSET_X=0,OFFSET_Y=0)
            worker.image_processor.image=np.zeros((2,2,3),np.uint8)
            assert capture(2,start,{'longterm_keogram':True}) is None
            worker.image_processor.image=np.zeros((48,64),np.uint8)
            assert capture(2,start,{'longterm_keogram':True}) is None
            assert Sample.query.count()==count and any('LONGTERM_SAMPLE_SKIPPED' in m and 'camera_id=2' in m for m in messages)
            worker.image_processor.image=np.full((48,64,3),(60,40,140),np.uint8)
            def fail_transaction(*args):
                db.session.add(Sample(ts=int(start.timestamp()),camera_id=None))
                db.session.commit()
            with patch.object(writer,'add_long_term_keogram_data',side_effect=fail_transaction):
                assert capture(2,start,{'longterm_keogram':True}) is None
            assert Sample.query.count()==count
            assert any('LONGTERM_SAMPLE_FAILED' in m and 'camera_id=2' in m for m in messages)
            assert capture(2,start,{'longterm_keogram':True})==[[140,40,60]]*5
            assert Sample.query.count()==count+1
        outputs=[]
        for cid in (1,2):
            client=login_client(app,cid)
            page=client.get('/indi-allsky/modern-admin/observatory/long-term-keogram?camera_id='+str(cid))
            token=re.search(r'name="csrf_token"[^>]*value="([^"]+)"',page.text)[1]
            payload=dict(CAMERA_ID=str(cid),END_SELECT='today',DAYS_SELECT='42',PIXELS_SELECT='5',ALIGNMENT_SELECT='60',OFFSET_SELECT='0',REVERSE=False,LABEL=False)
            with patch('indi_allsky.flask.create_app',return_value=app):
                result=client.post('/indi-allsky/js/longtermkeogram',json=payload,headers={'X-CSRFToken':token})
            assert result.status_code==200 and not result.json['failure-message'],result.text
            content=base64.b64decode(result.json['image_b64'][0])
            with Image.open(io.BytesIO(content)) as jpeg:
                jpeg.load();assert jpeg.width==1440 and jpeg.height>=5
                assert abs(max(jpeg.convert('RGB').tobytes()[::3])-(180-cid*20))<25
            cached=Path(app.config['INDI_ALLSKY_IMAGE_FOLDER'])/('ccd_test-camera-'+str(cid))/'longterm_keogram.jpg'
            assert cached.read_bytes()==content
            outputs.append({'camera_id':cid,'bytes':len(content),'sha256':hashlib.sha256(content).hexdigest()})
        with app.app_context():
            assert db.session.get(Config,1).data==original
        print(json.dumps({'scope':'Isolated Classic-disabled Flask; real worker sampling, SQL writes and JPEG generator; synthetic frames',
            'pixel_parity_cases':parity_count,'samples_per_camera':[120,121],'outputs':outputs,
            'guards':'Profile/global opt-out, images-only, focus, invalid offsets/shapes',
            'recovery':'Failed SQL transaction rolled back; next valid sample persisted',
            'performance':'In-memory fixture; not a live SD-card latency or 24h test'},indent=2))

if __name__=='__main__':run()
