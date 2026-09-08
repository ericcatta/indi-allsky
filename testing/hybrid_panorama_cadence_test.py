#!/usr/bin/env python3
"""Exercise the real panorama admission block with alternating camera processors."""
import ast
from pathlib import Path
from types import SimpleNamespace


def run():
    source=(Path(__file__).resolve().parents[1]/'indi_allsky/image.py').read_text()
    process=next(n for n in ast.walk(ast.parse(source)) if isinstance(n,ast.FunctionDef) and n.name=='processImage')
    gate=next(n for n in process.body if isinstance(n,ast.If) and "profile_outputs.get('panorama'" in ast.unparse(n.test))
    code=compile(ast.Module(body=[gate],type_ignores=[]),'image.py:panorama-gate','exec')
    generated=[]
    processors={cid:SimpleNamespace(fish2pano=lambda binning,cid=cid:cid,
        fish2pano_cardinal_dirs_label=lambda data:data) for cid in (1,2)}
    worker=SimpleNamespace(config={'MULTI_CAMERA_CAPTURE_ENABLE':True,'FISH2PANO':{'ENABLE':True,'MODULUS':2}},
        write_panorama_img=lambda data,ref,camera,**kw:generated.append(camera.id))
    def frame(cid,count,outputs=None,images_only=False):
        worker.image_processor=processors[cid];worker.image_count=count
        exec(code,dict(self=worker,images_only=images_only,profile_outputs=outputs or {},
             i_ref=SimpleNamespace(binning=1),camera=SimpleNamespace(id=cid),jpeg_exif=b'',profile_primary=cid==1))
    for count,cid in enumerate((1,2,1,2),1):frame(cid,count)
    assert generated==[1,2],generated
    generated.clear()
    for cid in (1,2):
        frame(cid,6,{'panorama':False});frame(cid,8,images_only=True)
    assert not generated
    assert all(p.panorama_frame_count==2 for p in processors.values())
    worker.config['FISH2PANO']['ENABLE']=False
    frame(1,10);assert not generated
    worker.config['FISH2PANO']['ENABLE']=True
    worker.config['MULTI_CAMERA_CAPTURE_ENABLE']=False
    for count in (1,2,3,4):frame(1,count)
    assert generated==[1,1],generated
    worker.config['MULTI_CAMERA_CAPTURE_ENABLE']=True
    for modulus,sequence,expected in ((1,(2,1,2),(2,1,2)),(3,(1,1,2,1,2,2),(1,2)),(5,(1,2,1,2),())):
        generated.clear();worker.config['FISH2PANO']['MODULUS']=modulus
        for p in processors.values():p.panorama_frame_count=0
        for count,cid in enumerate(sequence,1):frame(cid,count)
        assert tuple(generated)==expected,(modulus,generated)
    print('Panorama cadence: independent per-camera frames; config/profile/images-only gates; unchanged single-camera modulo: PASS')

if __name__=='__main__':run()
