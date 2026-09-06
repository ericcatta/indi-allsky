#!/usr/bin/env python3
"""Compare real focus scores/JPEG bytes against the captured legacy implementation."""
import ast
import base64
import hashlib
import io
import json
import logging
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import cv2
import numpy as np
from indi_allsky.config import IndiAllSkyConfigBase
from indi_allsky.focus_preview import focus_preview, load_focus_image


def run():
    fixture=json.loads((Path(__file__).parent/'fixtures/focus_preview_legacy.json').read_text())
    node=ast.parse(fixture['source']).body[0]
    assert hashlib.sha256(ast.dump(node,include_attributes=False).encode()).hexdigest()==fixture['class_ast_sha256']
    function=next(n for n in node.body if isinstance(n,ast.FunctionDef) and n.name=='dispatch_request')
    namespace={'__package__':'indi_allsky.flask','Path':Path,'io':io,'base64':base64,
               'jsonify':lambda value:value,'app':SimpleNamespace(logger=logging.getLogger('test'))}
    exec(compile(ast.Module(body=[function],type_ignores=[]),'<captured-focus>','exec'),namespace)
    config=IndiAllSkyConfigBase().base_config
    yy,xx=np.indices((480,640))
    data=np.stack(((xx*7+yy)%256,(xx+yy*3)%256,(xx*2+yy*5)%256),axis=-1).astype(np.uint8)
    with tempfile.TemporaryDirectory() as directory:
        path=Path(directory)/'latest.png';cv2.imwrite(str(path),data)
        config=dict(config,IMAGE_FOLDER=directory,IMAGE_FILE_TYPE='png')
        self=SimpleNamespace(indi_allsky_config=config)
        count=0
        for zoom in (2,5,10,20,40,60,80,100):
            for x,y in ((0,0),(12,-15),(-17,20)):
                if zoom==2 and (x or y):continue
                namespace['request']=SimpleNamespace(args={'zoom':str(zoom),'x_offset':str(x),'y_offset':str(y)})
                expected=namespace['dispatch_request'](self)
                actual=focus_preview(load_focus_image(path),config,zoom=zoom,x_offset=x,y_offset=y)
                assert actual==expected,(zoom,x,y)
                count+=1
        for args in ({'zoom':0},{'zoom':101},{'zoom':2,'x_offset':-1},{'zoom':10,'y_offset':10000}):
            try:focus_preview(data,config,**args)
            except ValueError:pass
            else:raise AssertionError(args)
        from astropy.io import fits
        fits_path=Path(directory)/'rgb.fits'
        fits.writeto(fits_path,np.moveaxis(data,2,0))
        opened=[]
        original_open=fits.open
        def record_open(*args,**kwargs):
            hdus=original_open(*args,**kwargs)
            opened.append(hdus)
            return hdus
        with patch('astropy.io.fits.open',side_effect=record_open):
            result=load_focus_image(fits_path)
            assert np.array_equal(result,cv2.cvtColor(data,cv2.COLOR_RGB2BGR))
            assert len(opened)==1 and opened[0]._file.closed
        assert fits_path.is_file()
    print('Focus preview parity: '+str(count)+' real JPEG/score/star cases, invalid regions and RGB FITS decode: PASS')

if __name__=='__main__':run()
