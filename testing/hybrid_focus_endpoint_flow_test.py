#!/usr/bin/env python3
"""Existing focus URL delegates to shared measurements with useful input errors."""
import argparse
from pathlib import Path
from hybrid_runtime_fixture import isolated_app, login_client


def run(runtime_config):
    with isolated_app(runtime_config) as app:
        import cv2
        import numpy as np
        from indi_allsky.flask import db
        from indi_allsky.flask.models import IndiAllSkyDbConfigTable
        with app.app_context():
            row=db.session.get(IndiAllSkyDbConfigTable,1)
            config=dict(row.data,IMAGE_FILE_TYPE='png');row.data=config;db.session.commit()
        path=Path(app.config['INDI_ALLSKY_IMAGE_FOLDER'])/'latest.png'
        cv2.imwrite(str(path),np.zeros((100,100,3),dtype=np.uint8))
        route='/indi-allsky/js/focus'
        for uid in (1,2):
            client=login_client(app,uid)
            response=client.get(route)
            assert response.status_code==200 and response.json['image_b64'],response.text
            assert response.json['blur_score']==0 and response.json['star_count']==0
            for query in ('zoom=0','zoom=bad','zoom=101','zoom=2&x_offset=-1','y_offset=999999'):
                response=client.get(route+'?'+query)
                assert response.status_code==400 and response.json['error'],query
        assert app.test_client().get(route).status_code==302
        path.unlink()
        assert client.get(route).status_code==400
        print('Focus endpoint: real preview, both roles, invalid regions, missing file, anonymous redirect: PASS')

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--runtime-config',default='/etc/indi-allsky/flask.json')
    run(parser.parse_args().runtime_config)
