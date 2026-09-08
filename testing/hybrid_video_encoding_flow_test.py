#!/usr/bin/env python3
"""Actual Hybrid request -> coordinator -> VideoWorker -> FFmpeg -> download.

Only disposable SQLite/media fixtures are used. Uploads are disabled; no capture
process, driver, production queue or production file is touched. FFmpeg/ffprobe
are real subprocesses, limited to three tiny frames and one encoding thread.
"""
import argparse
from copy import deepcopy
from datetime import date, timedelta
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
    results=[]; successful_files=[]
    with isolated_app(runtime_config, multi_camera=True) as app:
        app.config['ADMIN_NETWORKS']=['127.0.0.0/8']
        seed_generation(app);seed_preview_frames(app)
        from indi_allsky.flask import db
        from indi_allsky.flask.models import IndiAllSkyDbConfigTable as Config, IndiAllSkyDbTaskQueueTable as Task
        from indi_allsky.flask.models import IndiAllSkyDbImageTable as SourceImage
        from indi_allsky.flask.models import IndiAllSkyDbVideoTable as Video, IndiAllSkyDbMiniVideoTable as Mini, TaskQueueState as State
        # Both real modules bind their application to this isolated database.
        with patch('indi_allsky.flask.create_app', return_value=app):
            from indi_allsky.allsky import IndiAllSky
            from indi_allsky.video import VideoWorker
        with app.app_context():
            config=deepcopy(db.session.get(Config,1).data)
            config.update(FFMPEG_CODEC='libx264',FFMPEG_FRAMERATE=10,FFMPEG_EXTRA_OPTIONS='-threads 1 -preset ultrafast',
                          FFMPEG_VFSCALE='',TIMELAPSE_SKIP_FRAMES=0,TIMELAPSE_OVERWRITE=False)
            config['TIMELAPSE'].update(PRE_PROCESSOR='standard',USE_NIGHT_CONFIG=True,FFMPEG_REPORT=False)
            config['FILETRANSFER']={};config['S3UPLOAD']={'ENABLE':False};config['SYNCAPI']={'ENABLE':False};config['YOUTUBE']={}
            row=db.session.get(Config,1);row.data=config;db.session.commit()
        coordinator=IndiAllSky.__new__(IndiAllSky)
        coordinator.config=config;coordinator.multi_camera_capture_enable=True
        coordinator.capture_profiles=[SimpleNamespace(profile_id='test-profile-'+str(cid)) for cid in (1,2)]
        coordinator.video_q=Queue()
        uploads=Queue()
        worker=VideoWorker(99,config,Queue(),coordinator.video_q,uploads,[1,0],[1])
        admin=login_client(app,1);reader=login_client(app,2)
        root=Path(app.config['INDI_ALLSKY_IMAGE_FOLDER']).resolve()
        for kind in ('video','mini-video'):
            for cid in (1,2):
                if kind=='video':
                    page=admin.get('/indi-allsky/modern-admin/tools/generate?camera_id='+str(cid))
                    url='/indi-allsky/ajax/generate'
                    payload={'CAMERA_ID':str(cid),'ACTION_SELECT':'generate_video','DAY_SELECT':str(date.today())+'_night'}
                else:
                    page=admin.get('/indi-allsky/modern-admin/tools/mini-generate?camera_id='+str(cid))
                    url='/indi-allsky/ajax/minigenerate'
                    payload={'CAMERA_ID':str(cid),'IMAGE_ID':str(cid),'PRE_SECONDS':'5','POST_SECONDS':'5','FRAMERATE':'10','NOTE':'Real isolated encoding'}
                assert page.status_code==200
                token=re.search(r'name="csrf_token"[^>]*value="([^"]+)"',page.text)[1]
                response=admin.post(url,json=payload,headers={'X-CSRFToken':token})
                assert response.status_code==200,response.text
                with app.app_context():
                    task=Task.query.order_by(Task.id.desc()).first();task_id=task.id
                    assert task.state==State.MANUAL
                    coordinator._queueManualTasks()
                    db.session.refresh(task)
                    assert task.state==State.QUEUED,(kind,cid,task.state,task.result)
                    message=coordinator.video_q.get_nowait()
                    assert message['camera_id']==cid and message['profile_id']=='test-profile-'+str(cid),message
                    worker.processTask(message)
                    db.session.refresh(task)
                    assert task.state==State.SUCCESS,(kind,cid,task.state,task.result)
                    model=Video if kind=='video' else Mini
                    entry=model.query.filter_by(camera_id=cid).one();entry_id=entry.id
                    output=Path(entry.getFilesystemPath()).resolve()
                    assert output.is_relative_to(root) and output.is_file()
                    assert entry.success and entry.frames==3 and entry.fileSize==output.stat().st_size
                    content=output.read_bytes()
                    probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-count_frames','-select_streams','v:0','-show_entries','stream=codec_name,width,height,nb_read_frames,r_frame_rate','-of','json',str(output)],timeout=30))['streams'][0]
                    assert (probe['codec_name'],probe['width'],probe['height'],int(probe['nb_read_frames']))==('h264',64,48,3),probe
                    assert probe['r_frame_rate']=='10/1'
                    decoded=subprocess.check_output(['ffmpeg','-v','error','-threads','1','-i',str(output),'-f','rawvideo','-pix_fmt','rgb24','-'],timeout=30)
                    assert len(decoded)==3*64*48*3
                    # Solid-color source frames differ by camera. Validate decoded content,
                    # not just an MP4 header or successful encoder exit status.
                    reds=[sum(decoded[offset:offset+64*48*3:3])/(64*48) for offset in range(0,len(decoded),64*48*3)]
                    assert all(min(abs(value-20*cid),abs(value-80*cid))<10 for value in reds),(cid,reds)
                    assert any(abs(value-80*cid)<10 for value in reds)
                    assert uploads.empty(), 'No external upload may be queued'
                for client in (admin,reader):
                    task_page=client.get('/indi-allsky/modern-admin/tasks/'+str(task_id))
                    assert task_page.status_code==200 and 'SUCCESS' in task_page.text and output.name in task_page.text
                    download=client.get(f'/indi-allsky/modern-admin/media/{kind}/{cid}/{entry_id}/download')
                    assert download.status_code==200 and download.data==content
                    assert client.get(f'/indi-allsky/modern-admin/media/{kind}/{3-cid}/{entry_id}/download').status_code==404
                successful_files.append((output,hashlib.sha256(content).hexdigest()))
                results.append({'kind':kind,'camera_id':cid,'profile_id':message['profile_id'],'task_id':task_id,'task_state':'SUCCESS','bytes':len(content),'sha256':hashlib.sha256(content).hexdigest(),'probe':probe,'decoded_red_means':reds})
        # Real encoder failure on a separate fixture capture day. Existing outputs
        # must remain intact, and no upload or successful asset may be reported.
        failed_day=date.today()-timedelta(days=1)
        with app.app_context():
            for image in SourceImage.query.filter_by(camera_id=1):image.dayDate=failed_day
            db.session.commit()
        worker.config['FFMPEG_EXTRA_OPTIONS']='-threads 1 -hybrid_invalid_encoder_option'
        page=admin.get('/indi-allsky/modern-admin/tools/generate?camera_id=1')
        token=re.search(r'name="csrf_token"[^>]*value="([^\"]+)"',page.text)[1]
        response=admin.post('/indi-allsky/ajax/generate',json={'CAMERA_ID':'1','ACTION_SELECT':'generate_video','DAY_SELECT':str(failed_day)+'_night'},headers={'X-CSRFToken':token})
        assert response.status_code==200,response.text
        with app.app_context():
            task=Task.query.order_by(Task.id.desc()).first();failed_task_id=task.id
            coordinator._queueManualTasks();worker.processTask(coordinator.video_q.get_nowait())
            db.session.refresh(task)
            assert task.state==State.FAILED and 'Failed to generate timelapse' in task.result,task.result
            entry=Video.query.filter_by(camera_id=1,dayDate=failed_day).one()
            assert entry.success is False and not Path(entry.getFilesystemPath()).exists()
            assert uploads.empty()
            for output,digest in successful_files:assert hashlib.sha256(output.read_bytes()).hexdigest()==digest
        for client in (admin,reader):
            page=client.get('/indi-allsky/modern-admin/tasks/'+str(failed_task_id))
            assert page.status_code==200 and 'FAILED' in page.text and 'Failed to generate timelapse' in page.text
        failure={'task_state':'FAILED','encoder':'real FFmpeg rejected intentional invalid option','asset_success':False,'broken_output_exists':False,'successful_outputs_preserved':4,'upload_queue_empty':True}
    report={'scope':'Real coordinator/worker/FFmpeg on isolated SQLite and disposable media; no live capture or external upload','outputs':results,'failure_case':failure}
    if evidence:Path(evidence).write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--runtime-config',default='/etc/indi-allsky/flask.json')
    parser.add_argument('--evidence')
    args=parser.parse_args();run(args.runtime_config,args.evidence)
