#!/usr/bin/env python3
"""Atomic focus publication and real worker write_img integration, without capture."""
import ast
import logging
from pathlib import Path
import shutil
import sys
import tempfile
from types import SimpleNamespace
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from indi_allsky.focus_frames import focus_frame_path, publish_focus_frame


def run():
    import cv2
    import numpy as np
    root=Path(__file__).resolve().parents[1]
    tree=ast.parse((root/'indi_allsky/image.py').read_text())
    cls=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='ImageWorker')
    method=next(n for n in cls.body if isinstance(n,ast.FunctionDef) and n.name=='write_img')
    ns={'__package__':'indi_allsky','tempfile':tempfile,'Path':Path,'cv2':cv2,'shutil':shutil,'logger':logging.getLogger('test')}
    exec(compile(ast.Module(body=[method],type_ignores=[]),'<worker-write-img>','exec'),ns)
    with tempfile.TemporaryDirectory() as folder:
        directory=Path(folder)
        source=directory/'source.png';source.write_bytes(b'first')
        one=publish_focus_frame(source,directory,1,'png')
        two=publish_focus_frame(source,directory,2,'png')
        source.write_bytes(b'second')
        with patch('indi_allsky.focus_frames.os.replace',side_effect=OSError('disk failure')):
            try:publish_focus_frame(source,directory,1,'png')
            except OSError:pass
            else:raise AssertionError('publish should fail')
        assert one.read_bytes()==two.read_bytes()==b'first'
        assert not list(directory.glob('.focus-*'))
        publish_focus_frame(source,directory,1,'png')
        assert one.read_bytes()==b'second' and two.read_bytes()==b'first'
        for cid in (1,2):
            self=SimpleNamespace(config={'IMAGE_FILE_TYPE':'png','IMAGE_FILE_COMPRESSION':{'png':1},'FOCUS_MODE':True},
                                 image_dir=directory,profile_id='test-'+str(cid))
            data=np.full((48,64,3),cid*60,dtype=np.uint8)
            result=ns['write_img'](self,data,SimpleNamespace(camera_id=cid),SimpleNamespace(id=cid),write_latest=cid==1)
            assert result==(None,None)
            assert np.array_equal(cv2.imread(str(focus_frame_path(directory,cid,'png'))),data)
        assert np.all(cv2.imread(str(directory/'latest.png'))==60)
        assert np.all(cv2.imread(str(two))==120)
        assert not list(directory.glob('.focus-*'))
        with patch('indi_allsky.focus_frames.publish_focus_frame',side_effect=OSError('disk failure')) as publisher:
            assert ns['write_img'](self,data,SimpleNamespace(camera_id=2),SimpleNamespace(id=2),write_latest=False)==(None,None)
            assert not publisher.call_args.args[0].exists()
        assert np.all(cv2.imread(str(two))==120)
        link=directory/'focus-camera-3.png';link.symlink_to(source)
        try:focus_frame_path(directory,3,'png')
        except ValueError:pass
        else:raise AssertionError('symlink allowed')
    print('Focus frames: camera isolation, atomic replacement failure, temporary cleanup, worker primary/secondary publication and unchanged primary latest: PASS')

if __name__=='__main__':run()
