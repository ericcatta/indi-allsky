"""Small real FITS/RAW files in the disposable acceptance media directory."""
from datetime import date
from pathlib import Path


def seed_source_media(app):
    import numpy as np
    from astropy.io import fits
    from PIL import Image
    from indi_allsky.flask import db
    from indi_allsky.flask.models import IndiAllSkyDbFitsImageTable, IndiAllSkyDbRawImageTable
    with app.app_context():
        root = Path(app.config['INDI_ALLSKY_IMAGE_FOLDER'])
        for cid in (1, 2):
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
                db.session.add(model(id=cid, camera_id=cid, filename=str(path), dayDate=date.today(),
                    exposure=0.5, gain=cid*10, width=64, height=48, fileSize=path.stat().st_size,
                    night=cid==1, uploaded=False, data={}))
        db.session.commit()
