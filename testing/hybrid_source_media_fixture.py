"""Small real FITS/RAW files in the disposable acceptance media directory."""
from datetime import date
from pathlib import Path


def seed_source_media(app, *, pair_generation_images=False):
    import numpy as np
    from astropy.io import fits
    from PIL import Image
    from indi_allsky.flask import db
    from indi_allsky.flask.models import IndiAllSkyDbFitsImageTable, IndiAllSkyDbRawImageTable, IndiAllSkyDbImageTable
    with app.app_context():
        root = Path(app.config['INDI_ALLSKY_IMAGE_FOLDER'])
        for cid in (1, 2):
            paired = {}
            if pair_generation_images:
                image = db.session.get(IndiAllSkyDbImageTable, cid)
                assert image is not None and image.camera_id == cid
                paired = dict(createDate=image.createDate, dayDate=image.dayDate,
                              night=image.night, exposure=image.exposure, gain=image.gain)
            folder = root / ('ccd_test-camera-' + str(cid))
            folder.mkdir(exist_ok=True)
            pixels = (np.arange(64*48, dtype=np.uint16).reshape(48, 64) * cid)
            hdu = fits.PrimaryHDU(pixels)
            hdu.header['EXPTIME'] = 0.5
            hdu.header['GAIN'] = cid * 10
            hdu.header['XBINNING'] = 1
            hdu.header['CCD-TEMP'] = 15.0
            fits_path = folder / ('source-camera-' + str(cid) + '.fit')
            hdu.writeto(fits_path)
            raw_path = folder / ('raw-camera-' + str(cid) + '.png')
            Image.fromarray(pixels).save(raw_path)
            for model, path in ((IndiAllSkyDbFitsImageTable, fits_path), (IndiAllSkyDbRawImageTable, raw_path)):
                metadata = dict(dayDate=date.today(), exposure=0.5, gain=cid*10, night=cid==1)
                metadata.update(paired)
                db.session.add(model(id=cid, camera_id=cid, filename=str(path),
                    width=64, height=48, fileSize=path.stat().st_size,
                    uploaded=False, data={}, **metadata))
        db.session.commit()
