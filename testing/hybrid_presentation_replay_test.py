#!/usr/bin/env python3
"""Replay all presentation layers after fonts/logos/time/network have changed."""
from copy import deepcopy
from datetime import datetime
from multiprocessing import Array
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
import json
import shutil
import time
import cv2
import numpy as np
from hybrid_runtime_fixture import isolated_app

with isolated_app() as app, app.app_context():
    from indi_allsky.config import IndiAllSkyConfigBase
    from indi_allsky.processing import ImageProcessor
    from indi_allsky.image_rendering import render_presentation
    from indi_allsky.image_presentation import snapshot_presentation, render_saved_presentation
    from indi_allsky.render_assets import RenderAssetStore
    root = Path(app.config['INDI_ALLSKY_IMAGE_FOLDER'])
    store = RenderAssetStore(root/'assets')
    config = deepcopy(IndiAllSkyConfigBase().base_config)
    config.update(IMAGE_SCALE=80, IMAGE_LABEL_SYSTEM='pillow')
    config['MOON_OVERLAY'].update(ENABLE=True, X=20,Y=40,SCALE=0.15)
    config['LIGHTGRAPH_OVERLAY'].update(ENABLE=True,SCALE=0.5,Y=300,LABEL=True)
    config['IMAGE_OVERLAY'].update(ENABLE=True,A_X=200,A_Y=40,A_URL='https://private.invalid/secret',A_PASSWORD='secret')
    config['CARDINAL_DIRS'].update(ENABLE=True,DIAMETER=500)
    config['IMAGE_BORDER'].update(TOP=3,BOTTOM=5,LEFT=2,RIGHT=4)
    font = root/'original-font.ttf'
    shutil.copyfile(Path(__file__).resolve().parents[1]/'indi_allsky/fonts'/config['TEXT_PROPERTIES']['PIL_FONT_FILE'],font)
    config['TEXT_PROPERTIES'].update(PIL_FONT_FILE='custom',PIL_FONT_CUSTOM=str(font))
    logo = np.zeros((720,1280,4),dtype=np.uint8);logo[:,:,2]=150;logo[:,:,3]=30
    logo_path = root/'logo.png';assert cv2.imwrite(str(logo_path),logo)
    config['LOGO_OVERLAY']=str(logo_path)
    base = (np.arange(720*1280*3).reshape(720,1280,3)%180).astype(np.uint8)
    def processor(settings):
        p=ImageProcessor(deepcopy(settings),Array('f',[46,8,200]),Array('f',[0]),Array('i',[1]),
                         Array('f',[0]*60),Array('f',[0]*110),Array('i',[1,0]),Array('f',[0]*3))
        p.image_list=[SimpleNamespace(exp_date=datetime(2020,1,1,12))]
        p.astrometric_data.update(moon_cycle=30,moon_phase=65)
        p.image=base.copy()
        return p
    live=processor(config)
    live._image_overlay_o.next_load_time=float('inf')
    live._image_overlay_o.images_dict['a']['data']=np.full((30,40,3),[20,150,30],dtype=np.uint8)
    render_presentation(live,1)
    expected=live.image.copy()
    record=json.loads(json.dumps(snapshot_presentation(live,1,store)))
    assert 'secret' not in json.dumps(record)
    assert 'position' not in record, 'Do not expose precise location in presentation metadata'
    count=len(list(store.root.glob('*.npz')))
    assert snapshot_presentation(live,1,store)['logo']==record['logo']
    assert len(list(store.root.glob('*.npz')))==count, 'Identical resources must be deduplicated'
    font.unlink();logo_path.unlink()
    changed=deepcopy(config);changed['IMAGE_SCALE']=40;changed['ORB_PROPERTIES']['MODE']='off'
    replay=processor(changed)
    class NoCurrentClock(datetime):
        @classmethod
        def now(cls,*args,**kwargs):raise AssertionError('Current time consulted during replay')
    with patch('indi_allsky.processing.datetime',NoCurrentClock), \
         patch('indi_allsky.overlay.lightgraphOverlay.datetime',NoCurrentClock), \
         patch('indi_allsky.overlay.lightgraphOverlay.IndiAllSkyLightgraphOverlay.generate',side_effect=AssertionError('Lightgraph regenerated')), \
         patch('indi_allsky.overlay.imageOverlay.IndiAllSkyImageOverlay.load_image',side_effect=AssertionError('Network overlay reloaded')):
        render_saved_presentation(replay,record,store)
    np.testing.assert_array_equal(replay.image,expected)
    # Missing/corrupt immutable assets must fail rather than substitute current data.
    asset=record['logo']['asset']; path=store.root/(asset+'.npz')
    content=path.read_bytes();path.unlink()
    try:render_saved_presentation(processor(config),record,store)
    except FileNotFoundError:pass
    else:raise AssertionError('Missing asset silently replaced')
    path.write_bytes(content)
    for mode in ('ha','az','alt'):
        c=deepcopy(config);c['LOGO_OVERLAY']='';c['IMAGE_LABEL_SYSTEM']='opencv'
        for key in ('MOON_OVERLAY','LIGHTGRAPH_OVERLAY','IMAGE_OVERLAY','CARDINAL_DIRS'):c[key]['ENABLE']=False
        c['ORB_PROPERTIES']['MODE']=mode
        live=processor(c);render_presentation(live,1)
        record=json.loads(json.dumps(snapshot_presentation(live,1,store)))
        replay=processor(c);render_saved_presentation(replay,record,store)
        np.testing.assert_array_equal(replay.image,live.image)
print('Presentation replay: pixel parity for all layers, saved clocks/fonts/logos/network pixels, all orb modes, deduplicated assets and missing-asset rejection: PASS')
