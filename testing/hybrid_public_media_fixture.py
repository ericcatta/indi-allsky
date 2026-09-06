"""Public media thumbnail fixtures linked to each camera's source image."""
from pathlib import Path
from shutil import copyfile


def seed_public_media(app):
    from indi_allsky.flask import db
    from indi_allsky.flask.models import IndiAllSkyDbImageTable, IndiAllSkyDbThumbnailTable
    with app.app_context():
        root=Path(app.config['INDI_ALLSKY_IMAGE_FOLDER'])
        for cid in (1,2):
            path=root/('thumbnail-camera-'+str(cid)+'.jpg')
            copyfile(root/('generation-camera-'+str(cid)+'.jpg'),path)
            uuid='public-thumbnail-'+str(cid)
            db.session.add(IndiAllSkyDbThumbnailTable(id=cid,uuid=uuid,filename=str(path),camera_id=cid,width=64,height=48,fileSize=path.stat().st_size))
            db.session.get(IndiAllSkyDbImageTable,cid).thumbnail_uuid=uuid
        db.session.commit()
