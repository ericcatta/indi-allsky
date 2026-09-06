"""Small synthetic but decodable image/video outputs, confined to fixture media root."""
from datetime import date, datetime
from pathlib import Path
from shutil import copyfile
import subprocess


def seed_generated_media(app):
    from PIL import Image
    from indi_allsky.flask import db
    from indi_allsky.flask.source_media_views import MEDIA_DOWNLOAD_MODELS
    with app.app_context():
        root=Path(app.config['INDI_ALLSKY_IMAGE_FOLDER'])
        for cid in (1,2):
            clip=root/('fixture-clip-'+str(cid)+'.mp4')
            subprocess.run(['ffmpeg','-nostdin','-v','error','-f','lavfi','-i',
                'color=c='+('blue' if cid==1 else 'green')+':s=64x48:r=10','-t','2',
                '-c:v','libx264','-pix_fmt','yuv420p',str(clip)],check=True)
            for kind in ('video','mini-video','keogram','startrail','startrail-video','panorama','panorama-video'):
                model=MEDIA_DOWNLOAD_MODELS[kind]
                video='video' in kind
                path=root/(kind+'-camera-'+str(cid)+('.mp4' if video else '.jpg'))
                if video: copyfile(clip,path)
                else: Image.new('RGB',(64,48),(20*cid,40,60)).save(path)
                fields=dict(id=cid,filename=str(path),dayDate=date.today(),camera_id=cid,
                    width=64,height=48,fileSize=path.stat().st_size,night=True,data={})
                if kind=='panorama':fields.update(exposure=.5,gain=10)
                else:fields.update(success=True,frames=20)
                if kind=='mini-video':fields.update(targetDate=datetime.now(),startDate=datetime.now(),endDate=datetime.now(),note='Dedicated fixture',framerate=10)
                db.session.add(model(**fields))
        db.session.commit()
