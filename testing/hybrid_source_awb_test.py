#!/usr/bin/env python3
"""AWB capture/replay shares the frozen numerical behavior, including skips."""
import ast
import json
import sys
from pathlib import Path
from types import SimpleNamespace
from multiprocessing import Array
import numpy
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from indi_allsky import constants
from indi_allsky.image_awb import apply_rgb_gains
fixture=json.loads((ROOT/'testing/fixtures/source_awb_legacy.json').read_text())
tree=ast.parse((ROOT/'indi_allsky/image.py').read_text())
method=next(n for n in ast.walk(tree) if isinstance(n,ast.FunctionDef) and n.name=='apply_hybrid_awb')
noop=lambda *a,**k:None
functions=[]
for text in (fixture['method'],ast.unparse(method)):
    scope=dict(numpy=numpy,constants=constants,apply_rgb_gains=apply_rgb_gains,
               _multi_camera_diag=noop,logger=SimpleNamespace(info=noop,error=noop))
    exec(text,scope);functions.append(scope['apply_hybrid_awb'])
for dtype in (numpy.uint8,numpy.uint16,numpy.float32,numpy.int16,numpy.bool_):
    for scale in (1,255,4095,65536):
        for initialized in (False,True):
            source=(numpy.arange(60).reshape(4,5,3)/60*scale).astype(dtype)
            outputs=[]
            for function in functions:
                state=Array('f',[0]*64)
                state[constants.HYBRID_AWB_INITIALIZED]=int(initialized)
                state[constants.HYBRID_AWB_SAMPLE_COUNT]=5
                state[constants.HYBRID_AWB_RED_GAIN_NEXT]=1.4
                state[constants.HYBRID_AWB_BLUE_GAIN_NEXT]=0.8
                worker=SimpleNamespace(image_processor=SimpleNamespace(image=source.copy()),hybrid_av=state,
                    _hybrid_awb_enabled=lambda:True,_hybrid_awb_backend=lambda:'postprocess_rgb',
                    _log_hybrid_awb_backend_warning=noop,_hybrid_awb_postprocess_skip=noop,
                    _clamp_hybrid_awb_gain=lambda gain:gain)
                function(worker,'test',1);outputs.append(worker.image_processor.image)
            numpy.testing.assert_array_equal(*outputs)
            expected=initialized and dtype!=numpy.bool_
            assert (worker.image_processor.render_awb_gains is not None)==expected
            if expected:
                numpy.testing.assert_array_equal(apply_rgb_gains(source,*worker.image_processor.render_awb_gains),outputs[0])
print('Capture/shared AWB: frozen dtype/range/clip parity and actual applied-gain recording: PASS')
