"""More than a page and more than the former 100-row archive limit."""
from datetime import date, datetime
from pathlib import Path
from shutil import copyfile


def seed_archive(app):
    from indi_allsky.flask import db
    from indi_allsky.flask.models import IndiAllSkyDbImageTable
    with app.app_context():
        root=Path(app.config['INDI_ALLSKY_IMAGE_FOLDER'])
        for iid in range(100,210):
            path=root/('archive-image-'+str(iid)+'.jpg')
            copyfile(root/'generation-camera-1.jpg',path)
            db.session.add(IndiAllSkyDbImageTable(id=iid,camera_id=1,filename=str(path),
                createDate=datetime(2024,1,2,3,4,5),dayDate=date(2024,1,1),
                exposure=.5,gain=10,adu=.1,night=iid%2==0,uploaded=iid%3==0,
                data={},width=64,height=48,fileSize=path.stat().st_size))
        db.session.commit()
