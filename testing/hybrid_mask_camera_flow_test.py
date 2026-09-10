#!/usr/bin/env python3
"""Mask bases retain camera ownership through publication and Hybrid selection."""
import argparse
import ast
from pathlib import Path
import tempfile
from unittest.mock import patch
from types import SimpleNamespace
import logging
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from hybrid_runtime_fixture import isolated_app, login_client


def run(runtime_config):
    import cv2
    import numpy as np
    from indi_allsky.mask_frames import publish_mask_base, mask_frame_path
    with tempfile.TemporaryDirectory() as directory:
        root=Path(directory)
        a=np.full((20,30,3),40,dtype=np.uint8)
        b=np.full((25,35,3),180,dtype=np.uint8)
        publish_mask_base(a,root,1,1);publish_mask_base(b,root,2,1)
        assert np.array_equal(cv2.imread(str(mask_frame_path(root,1))),a)
        assert np.array_equal(cv2.imread(str(mask_frame_path(root,2))),b)
        assert np.array_equal(cv2.imread(str(root/'mask_base.png')),b)
        with patch('indi_allsky.mask_frames.os.replace',side_effect=OSError('disk failure')):
            try:publish_mask_base(b,root,1,1)
            except OSError:pass
            else:raise AssertionError('Expected write failure')
        assert np.array_equal(cv2.imread(str(mask_frame_path(root,1))),a)
        assert not list(root.glob('.mask-*'))
        with patch('cv2.imwrite',return_value=False):
            try:publish_mask_base(b,root,1,1)
            except OSError:pass
            else:raise AssertionError('Expected encoding failure')
        assert not list(root.glob('.mask-*'))
        tree=ast.parse((Path(__file__).resolve().parents[1]/'indi_allsky/image.py').read_text())
        worker=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='ImageWorker')
        method=next(n for n in worker.body if isinstance(n,ast.FunctionDef) and n.name=='write_mask_base_img')
        ns={'__package__':'indi_allsky','logger':logging.getLogger('mask-test')}
        exec(compile(ast.Module(body=[method],type_ignores=[]),'<mask-worker>','exec'),ns)
        ns['write_mask_base_img'](SimpleNamespace(image_dir=root,config={'IMAGE_FILE_COMPRESSION':{'png':1}}),a,2)
        assert np.array_equal(cv2.imread(str(mask_frame_path(root,2))),a)
    with isolated_app(runtime_config,multi_camera=True) as app:
        from indi_allsky.flask import db
        from indi_allsky.flask.models import IndiAllSkyDbCameraTable
        from indi_allsky.flask.views import ModernAdminMaskView, MaskView
        assert not issubclass(ModernAdminMaskView,MaskView)
        root=Path(app.config['INDI_ALLSKY_IMAGE_FOLDER'])
        publish_mask_base(a,root,1,1);publish_mask_base(b,root,2,1)
        page='/indi-allsky/modern-admin/cameras/mask-base'
        for uid in (1,2):
            client=login_client(app,uid)
            for cid in (1,2):
                response=client.get(page,query_string={'camera_id':cid,'profile_id':'test-profile-'+str(cid)})
                assert response.status_code==200,response.text
                assert 'mask-camera-'+str(cid)+'.png' in response.text
                assert 'images/mask_base.png' not in response.text
            assert client.get(page+'?camera_id=1&profile_id=test-profile-2').status_code==400
        assert app.test_client().get(page).status_code==302
        mask_frame_path(root,2).unlink()
        response=client.get(page+'?camera_id=2')
        assert 'No mask base available' in response.text
        assert 'images/mask_base.png' not in response.text
        (root/'mask-camera-2.png').symlink_to(root/'mask-camera-1.png')
        response=client.get(page+'?camera_id=2')
        assert response.status_code==200 and 'could not be accessed safely' in response.text
        assert '<img src=' not in response.text
        with app.app_context():
            camera=db.session.get(IndiAllSkyDbCameraTable,1)
            camera.web_nonlocal_images=True;camera.web_local_images_admin=False;db.session.commit()
        response=client.get(page+'?camera_id=1')
        assert 'media policy' in response.text
        assert '<img src=' not in response.text
    print('Mask base: camera-isolated publication, worker delegation, atomic failure, roles, selection, missing data and media policy: PASS')

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--runtime-config',default='/etc/indi-allsky/flask.json')
    run(parser.parse_args().runtime_config)
