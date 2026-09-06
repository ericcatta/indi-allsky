#!/usr/bin/env python3
"""Real processing of alternating 16-bit INDI and 8-bit libcamera frames."""
from copy import deepcopy
from multiprocessing import Array
from types import SimpleNamespace,MethodType
import numpy as np
from hybrid_runtime_fixture import isolated_app

with isolated_app(multi_camera=True) as app, app.app_context():
    from indi_allsky.image import ImageWorker
    from indi_allsky.config import IndiAllSkyConfigBase
    config=deepcopy(IndiAllSkyConfigBase().base_config)
    config.update(MULTI_CAMERA_CAPTURE_ENABLE=True,IMAGE_FOLDER=app.config['INDI_ALLSKY_IMAGE_FOLDER'])
    config['IMAGE_STRETCH'].update(CLASSNAME='mode1_stddev_cutoff',SPLIT=False)
    worker=SimpleNamespace(config=config,image_processors={},image_processor=None,
        position_av=Array('f',[46,8,200]),gain_av=Array('f',[0]*8),binning_av=Array('i',[1]),
        sensors_temp_av=Array('f',[0]*60),sensors_user_av=Array('f',[0]*110),
        night_av=Array('i',[1,0]),astro_av=Array('f',[0]*3),_images_only_diag=lambda *a,**kw:None)
    worker._new_image_processor=MethodType(ImageWorker._new_image_processor,worker)
    select=MethodType(ImageWorker._select_image_processor,worker)
    identities={}
    for cid,depth,h,w in ((2,16,48,64),(1,8,72,96),(2,16,48,64),(1,8,72,96)):
        worker.config=deepcopy(config);worker.config['CCD_BIT_DEPTH']=depth
        # images_only_diag=False is the regression: full FITS/output profiles still isolate.
        select('profile-'+str(cid),cid,False)
        p=worker.image_processor
        assert p is not None
        if cid in identities:assert p is identities[cid]
        else:identities[cid]=p;p.post_init()
        assert p.config['CCD_BIT_DEPTH']==depth
        if depth==8:assert p.max_bit_depth==8,'16-bit camera contaminated libcamera range'
        p.max_bit_depth=depth
        data=(np.arange(h*w*3).reshape(h,w,3)%((2**depth)-1)).astype(np.uint8 if depth==8 else np.uint16)
        p.image=data
        ref=SimpleNamespace(binning=1,image_bitpix=depth)
        p.image_list=[ref]
        p.stretch();p.convert_16bit_to_8bit()
        assert p.image.dtype==np.uint8
        p._stars_detect.detectObjects(p.image,1)
    assert identities[1] is not identities[2]
    assert identities[1].image_list is not identities[2].image_list
    worker.config=deepcopy(config);select('another-profile',1,False)
    assert worker.image_processor is not identities[1]
    existing=worker.image_processor;worker.config['MULTI_CAMERA_CAPTURE_ENABLE']=False
    select('default',1,False);assert worker.image_processor is existing
    select('images-only',1,True);assert worker.image_processor is not existing
print('Full-output multicamera processor isolation: bit depth, stacks, config, real stretch/star detection and legacy/images-only paths: PASS')
