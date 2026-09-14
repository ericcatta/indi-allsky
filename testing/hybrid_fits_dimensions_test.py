#!/usr/bin/env python3
"""Persist real mono/RGB FITS files and verify dimensions, pixels and Hybrid UI."""
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace

import numpy as np
from astropy.io import fits

from hybrid_runtime_fixture import isolated_app, login_client


with isolated_app(multi_camera=True) as app, app.app_context():
    from indi_allsky.image import ImageWorker
    from indi_allsky.fits_schedule import FitsSchedule
    from indi_allsky.flask.miscDb import miscDb
    from indi_allsky.flask.models import IndiAllSkyDbFitsImageTable

    root = Path(app.config['INDI_ALLSKY_IMAGE_FOLDER'])
    uploads = []
    worker = SimpleNamespace(
        config={'IMAGE_SAVE_FITS_PERIOD': 0},
        fits_schedule=FitsSchedule(), night_av=[1, 0], image_dir=root,
        filename_t='ccd{0}_{1}.{2}',
        image_processor=SimpleNamespace(astrometric_data={'moon_phase': 0}, camera_sqm_raw_mag=0),
        _getImageFolder=lambda *args: root / 'fits',
        _miscDb=miscDb({}),
        _miscUpload=SimpleNamespace(
            s3_upload_fits=lambda entry, metadata: uploads.append(metadata.copy()),
            upload_fits_image=lambda entry: None,
        ),
    )
    for camera_id, shape, dtype in ((1, (3, 48, 64), np.uint8), (2, (48, 64), np.uint16)):
        worker.profile_id = 'test-profile-' + str(camera_id)
        worker.current_camera_id = camera_id
        pixels = np.arange(np.prod(shape), dtype=dtype).reshape(shape)
        with fits.HDUList([fits.PrimaryHDU(pixels)]) as hdulist:
            captured = datetime(2026, 9, 14, 1, 0, camera_id)
            ref = SimpleNamespace(
                camera_id=camera_id, camera_uuid='test-camera-' + str(camera_id),
                hdulist=hdulist, exp_date=captured, day_date=captured.date(),
                exposure=1.0, gain=0, binning=1, sqm_value=0, stars=[], lines=[],
                kpindex=0, ovation_max=0, smoke_rating=0, aurora_mag_bt=0,
                aurora_mag_gsm_bz=0, aurora_plasma_density=0, aurora_plasma_speed=0,
                aurora_plasma_temp=0, aurora_n_hemi_gw=0, aurora_s_hemi_gw=0,
                camera_sqm_raw_mag=0,
            )
            for compressed in (False, True):
                worker.config['IMAGE_SAVE_FITS_COMPRESSED'] = compressed
                result = ImageWorker.write_fit(worker, ref, None)
                entry = IndiAllSkyDbFitsImageTable.query.filter_by(id=result['db_id']).one()
                assert (entry.width, entry.height) == (64, 48), (shape, compressed)
                assert (uploads[-1]['width'], uploads[-1]['height']) == (64, 48)
                with fits.open(result['path']) as saved:
                    assert saved[0].data.shape == shape
                    np.testing.assert_array_equal(saved[0].data, pixels)
                    assert (saved[0].header['NAXIS1'], saved[0].header['NAXIS2']) == (64, 48)
                assert entry.fileSize == Path(result['path']).stat().st_size > 0

    client = login_client(app, 1)
    for camera_id in (1, 2):
        response = client.get('/indi-allsky/modern-admin/library', query_string={
            'kind': 'fits', 'camera_id': camera_id,
        })
        assert response.status_code == 200
        assert '64 × 48' in response.text
        assert '48 × 3' not in response.text

print('FITS mono/RGB plain/gzip: dimensions, database, upload metadata, unchanged pixels and Hybrid rendering: PASS')
