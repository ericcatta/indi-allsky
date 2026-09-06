"""Dedicated source images for generation-request acceptance; never production files."""
from datetime import date
from pathlib import Path

def seed_generation(app):
    from PIL import Image
    from indi_allsky.flask import db
    from indi_allsky.flask.models import IndiAllSkyDbImageTable
    with app.app_context():
        root=Path(app.config['INDI_ALLSKY_IMAGE_FOLDER'])
        for cid in (1,2):
            path=root/('generation-camera-'+str(cid)+'.jpg')
            Image.new('RGB',(64,48),(20*cid,30,40)).save(path)
            db.session.add(IndiAllSkyDbImageTable(id=cid,filename=str(path),camera_id=cid,
                dayDate=date.today(),exposure=0.5,gain=10,adu=0.1,night=True,data={},
                width=64,height=48,fileSize=path.stat().st_size))
        db.session.commit()
