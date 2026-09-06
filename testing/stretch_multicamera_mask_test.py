#!/usr/bin/env python3
"""Regression for IMX708/ASI678 night stretch mask reuse across frame shapes."""
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import numpy as np
from indi_allsky.stretch.mode1_stddev_cutoff import IndiAllSky_Mode1_Stretch

config={'IMAGE_STRETCH':{'MODE1_GAMMA':3.,'MODE1_STDDEVS':3.},'SQM_FOV_DIV':4}
for dtype,depth in ((np.uint8,8),(np.uint16,12)):
    shared=IndiAllSky_Mode1_Stretch(config,mask={1:None,2:None})
    for h,w,channels,binning in ((48,64,3,1),(72,96,3,1),(48,64,3,1),(32,40,1,2),(72,96,1,1)):
        shape=(h,w,channels) if channels==3 else (h,w)
        data=(np.arange(np.prod(shape)).reshape(shape)%((2**depth)-1)).astype(dtype)
        fresh=IndiAllSky_Mode1_Stretch(config,mask={binning:None})
        expected=fresh.stretch(data,depth,binning)
        actual=shared.stretch(data,depth,binning)
        np.testing.assert_array_equal(actual,expected)
        assert shared._numpy_mask_dict[(binning,w,h)].shape==(h,w)
    assert len(shared._numpy_mask_dict)==3

image=np.arange(48*64,dtype=np.uint16).reshape(48,64)
external=np.full((48,64),255,np.uint8);external[:12]=0
valid=IndiAllSky_Mode1_Stretch(config,mask={1:external})
valid.stretch(image,12,1)
np.testing.assert_array_equal(valid._numpy_mask_dict[(1,64,48)],external==0)
wrong=IndiAllSky_Mode1_Stretch(config,mask={1:np.ones((72,96),np.uint8)})
fallback=IndiAllSky_Mode1_Stretch(config,mask={1:None})
np.testing.assert_array_equal(wrong.stretch(image,12,1),fallback.stretch(image,12,1))
print('Multicamera stretch: alternating shapes, color/mono, binning, external-mask fallback and independent-frame pixel parity: PASS')
