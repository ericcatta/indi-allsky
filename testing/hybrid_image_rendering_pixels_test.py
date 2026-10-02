#!/usr/bin/env python3
"""Compare actual source-derived rendered pixels with frozen capture stages."""
from copy import deepcopy
from datetime import datetime
from multiprocessing import Array
from pathlib import Path
import cv2
import numpy as np
from astropy.io import fits
from hybrid_runtime_fixture import isolated_app
from hybrid_image_rendering_test import legacy, shared, FIXTURE

with isolated_app(multi_camera=True) as app, app.app_context():
    from indi_allsky.config import IndiAllSkyConfigBase
    from indi_allsky.processing import ImageProcessor
    from indi_allsky.flask.models import IndiAllSkyDbCameraTable
    root = Path(app.config['INDI_ALLSKY_IMAGE_FOLDER'])
    for cid, dtype, maximum in ((1, np.uint8, 255), (2, np.uint16, 4095)):
        pixels = (np.arange(128 * 192).reshape(128, 192) % maximum).astype(dtype)
        source = root / f'render-{cid}.fit'
        fits.PrimaryHDU(pixels).writeto(source)
        original = source.read_bytes()
        camera = IndiAllSkyDbCameraTable.query.filter_by(id=cid).one()
        for night in (0, 1):
            for contrast16 in (False, True):
                config = deepcopy(IndiAllSkyConfigBase().base_config)
                config.update(IMAGE_FOLDER=str(root), CONTRAST_ENHANCE_16BIT=contrast16,
                              DAYTIME_CONTRAST_ENHANCE=True, NIGHT_CONTRAST_ENHANCE=True,
                              IMAGE_ROTATE='ROTATE_90_CLOCKWISE', IMAGE_ROTATE_ANGLE=10,
                              IMAGE_SCALE=80, GAMMA_CORRECTION=1.2, GAMMA_CORRECTION_DAY=1.2)
                config['IMAGE_STRETCH'].update(CLASSNAME='mode1_stddev_cutoff', SPLIT=False)
                config['IMAGE_BORDER'].update(TOP=2, BOTTOM=3, LEFT=4, RIGHT=5)
                # Overlay methods still execute; unavailable external assets are disabled.
                for key in ('MOON_OVERLAY', 'LIGHTGRAPH_OVERLAY', 'IMAGE_OVERLAY'):
                    config[key]['ENABLE'] = False
                outputs = []
                for render in (legacy, shared):
                    p = ImageProcessor(deepcopy(config), Array('f', [46, 8, 200]),
                        Array('f', [0]), Array('i', [2]), Array('f', [0]*60),
                        Array('f', [0]*110), Array('i', [night, 0]), Array('f', [0]*3))
                    captured = datetime(2020, 1, 1, 12)
                    p.update_astrometric_data(captured)
                    p.add(source, 1.0, 0, 2, captured, 0.0, camera)
                    p.debayer(); p.stack()
                    for name in FIXTURE['blocks']:
                        if name == 'render_presentation':
                            # Exercise a real alpha overlay without external assets.
                            overlay = np.zeros((p.image.shape[0]*2, p.image.shape[1]*2, 4), dtype=np.uint8)
                            overlay[:, :, 2] = 220
                            overlay[:, :, 3] = 96
                            logo = root / 'render-overlay.png'
                            assert cv2.imwrite(str(logo), overlay)
                            p.config['LOGO_OVERLAY'] = str(logo)
                        render(name, p, config, [night, 0])
                        if name == 'render_presentation':
                            assert isinstance(p._overlay_dict[2], np.ndarray), 'Overlay must be applied, not skipped'
                    outputs.append(p.image.copy())
                np.testing.assert_array_equal(*outputs)
                assert outputs[0].dtype == np.uint8
                assert source.read_bytes() == original
print('Real 8/16-bit day/night rendering: frozen capture/shared pixel parity, stretch, transforms, borders and intact sources: PASS')
