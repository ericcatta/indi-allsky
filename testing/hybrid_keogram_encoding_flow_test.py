#!/usr/bin/env python3
"""Real Keogram/Startrail effects through Hybrid with Classic disabled.

Only disposable SQLite/media fixtures are used. Uploads are disabled; no capture
process, driver, production queue or production file is touched. FFmpeg/ffprobe
are real subprocesses, limited to three tiny frames and one encoding thread.
"""
import argparse
from copy import deepcopy
from datetime import date
import hashlib
import json
from pathlib import Path
from queue import Queue
import re
import shutil
import subprocess
from types import SimpleNamespace
from unittest.mock import patch
from hybrid_runtime_fixture import isolated_app, login_client
from hybrid_generation_fixture import seed_generation, seed_preview_frames


def run(runtime_config, evidence=None):
    assert shutil.which('ffmpeg') and shutil.which('ffprobe'), 'Install FFmpeg/ffprobe to run real encoding acceptance'
    results=[]
    with isolated_app(runtime_config, multi_camera=True) as app:
        app.config['ADMIN_NETWORKS']=['127.0.0.0/8']
        seed_generation(app);seed_preview_frames(app)
        from indi_allsky.flask import db
        from indi_allsky.flask.models import IndiAllSkyDbConfigTable as Config, IndiAllSkyDbTaskQueueTable as Task
        from indi_allsky.flask.models import IndiAllSkyDbKeogramTable as Keogram, IndiAllSkyDbStarTrailsTable as Startrail, IndiAllSkyDbStarTrailsVideoTable as StarVideo
        from PIL import Image
        from indi_allsky.flask.models import TaskQueueState as State
        from indi_allsky.flask.models import IndiAllSkyDbCameraTable as Camera
        import piexif
        # Both real modules bind their application to this isolated database.
        with patch('indi_allsky.flask.create_app', return_value=app):
            from indi_allsky.allsky import IndiAllSky
            from indi_allsky.video import VideoWorker
        with app.app_context():
            missing=db.session.get(Camera,1)
            missing.lensName=None;missing.lensFocalLength=None;missing.lensFocalRatio=None
            camera=db.session.get(Camera,2)
            camera.lensName='Synthetic Lens';camera.lensFocalLength=2.8;camera.lensFocalRatio=1.4
            config=deepcopy(db.session.get(Config,1).data)
            config.update(FFMPEG_CODEC='libx264',FFMPEG_FRAMERATE=10,FFMPEG_EXTRA_OPTIONS='-threads 1 -preset ultrafast',
                          FFMPEG_VFSCALE='',TIMELAPSE_SKIP_FRAMES=0,TIMELAPSE_OVERWRITE=False)
            config['TIMELAPSE'].update(PRE_PROCESSOR='standard',USE_NIGHT_CONFIG=True,FFMPEG_REPORT=False)
            config['FILETRANSFER']={};config['S3UPLOAD']={'ENABLE':False};config['SYNCAPI']={'ENABLE':False};config['YOUTUBE']={}
            config.update(KEOGRAM_LABEL=False, KEOGRAM_H_SCALE=100, KEOGRAM_V_SCALE=100,
                          STARTRAILS_SUN_ALT_THOLD=91, STARTRAILS_MOONMODE_THOLD=False,
                          STARTRAILS_MOON_ALT_THOLD=91, STARTRAILS_MOON_PHASE_THOLD=101,
                          STARTRAILS_MAX_ADU=255, STARTRAILS_MASK_THOLD=255,
                          STARTRAILS_MIN_STARS=0, STARTRAILS_TIMELAPSE=True,
                          STARTRAILS_TIMELAPSE_MINFRAMES=3)
            row=db.session.get(Config,1);row.data=config;db.session.commit()
        # Inspect actual pre-compression pixels as well: no synthetic leading
        # column, and exactly one sample for each source image.
        import numpy as np
        from indi_allsky.keogram import KeogramGenerator
        kg=KeogramGenerator(config,skip_frames=0)
        kg.angle=0
        for index,value in enumerate((20,80,160)):
            kg.processImage(np.full((48,64,3),value,dtype=np.uint8),index+1)
        assert kg.keogram_data.shape==(48,3,3),kg.keogram_data.shape
        for index,value in enumerate((20,80,160)):
            assert np.all(kg.keogram_data[:,index,:]==value)
        coordinator=IndiAllSky.__new__(IndiAllSky)
        coordinator.config=config;coordinator.multi_camera_capture_enable=True
        coordinator.capture_profiles=[SimpleNamespace(profile_id='test-profile-'+str(cid)) for cid in (1,2)]
        coordinator.video_q=Queue()
        uploads=Queue()
        worker=VideoWorker(99,config,Queue(),coordinator.video_q,uploads,[1,0],[1])
        admin=login_client(app,1);reader=login_client(app,2)
        root=Path(app.config['INDI_ALLSKY_IMAGE_FOLDER']).resolve()
        for cid in (1,2):
            page=admin.get('/indi-allsky/modern-admin/tools/generate?camera_id='+str(cid))
            assert page.status_code==200
            token=re.search(r'name="csrf_token"[^>]*value="([^"]+)"',page.text)[1]
            response=admin.post('/indi-allsky/ajax/generate',json={'CAMERA_ID':str(cid),'ACTION_SELECT':'generate_k_st','DAY_SELECT':str(date.today())+'_night'},headers={'X-CSRFToken':token})
            assert response.status_code==200,response.text
            with app.app_context():
                task=Task.query.order_by(Task.id.desc()).first();task_id=task.id
                assert task.state==State.MANUAL
                coordinator._queueManualTasks()
                message=coordinator.video_q.get_nowait()
                assert message['camera_id']==cid and message['profile_id']=='test-profile-'+str(cid)
                worker.processTask(message);db.session.refresh(task)
                assert task.state==State.SUCCESS,(task.state,task.result)
                outcome=task.data['generation_outcome']
                assert outcome['status']=='complete',outcome
                assert all(item['status']=='generated' for item in outcome['outputs']),outcome
                outputs=[]
                for kind,model in (('keogram',Keogram),('startrail',Startrail),('startrail-video',StarVideo)):
                    entry=model.query.filter_by(camera_id=cid).one()
                    output=Path(entry.getFilesystemPath()).resolve()
                    assert output.is_relative_to(root) and output.is_file() and entry.success
                    content=output.read_bytes();assert len(content)==entry.fileSize>0
                    if kind=='keogram':
                        assert entry.frames==3 and entry.width==3,(entry.frames,entry.width)
                    if kind=='startrail-video':
                        probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-count_frames','-select_streams','v:0','-show_entries','stream=width,height,nb_read_frames','-of','json',str(output)],timeout=30))['streams'][0]
                        assert int(probe['nb_read_frames'])==3 and (probe['width'],probe['height'])==(64,48),probe
                    else:
                        exif=piexif.load(content)['Exif']
                        if cid==1:
                            assert piexif.ExifIFD.LensModel not in exif
                            assert piexif.ExifIFD.FocalLength not in exif
                            assert piexif.ExifIFD.FNumber not in exif
                        else:
                            assert exif[piexif.ExifIFD.LensModel]==b'Synthetic Lens'
                            if kind=='startrail':
                                assert exif[piexif.ExifIFD.FocalLength]==(14,5)
                                assert exif[piexif.ExifIFD.FNumber]==(7,5)
                        with Image.open(output) as image:
                            image.load();pixels=image.convert('RGB');width,height=image.size
                            assert width>0 and height>0
                            red=sum(pixels.tobytes()[::3])/(width*height)
                            # Keogram trim/resampling changes the mean; its bright
                            # source column still identifies the selected camera.
                            measured=red if kind=='startrail' else max(pixels.tobytes()[::3])
                            assert abs(measured-80*cid)<15,(kind,cid,measured)
                    outputs.append((kind,entry.id,output.name,content))
                assert uploads.empty()
            for client in (admin,reader):
                page=client.get('/indi-allsky/modern-admin/tasks/'+str(task_id))
                assert page.status_code==200 and 'Complete generation' in page.text
                for kind,eid,name,content in outputs:
                    response=client.get(f'/indi-allsky/modern-admin/media/{kind}/{cid}/{eid}/download')
                    assert response.status_code==200 and response.data==content,(kind,response.status_code)
                    assert client.get(f'/indi-allsky/modern-admin/media/{kind}/{3-cid}/{eid}/download').status_code==404
            results.append({'camera_id':cid,'profile_id':message['profile_id'],'task_id':task_id,'outcome':outcome,'outputs':[{'kind':kind,'bytes':len(content),'sha256':hashlib.sha256(content).hexdigest()} for kind,eid,name,content in outputs]})
    report={'scope':'Real Keogram, Startrail and FFmpeg algorithms on synthetic isolated fixtures; configured thresholds permit synthetic frames; not scientific or live capture acceptance','results':results}
    if evidence:Path(evidence).write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--runtime-config',default='/etc/indi-allsky/flask.json')
    parser.add_argument('--evidence')
    args=parser.parse_args();run(args.runtime_config,args.evidence)
