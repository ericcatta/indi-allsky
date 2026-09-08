#!/usr/bin/env python3
"""Persist generation receipt and read it through the actual Hybrid task page."""
from pathlib import Path
from hybrid_runtime_fixture import isolated_app, login_client
from hybrid_generated_media_fixture import seed_generated_media


def run():
    with isolated_app(multi_camera=True) as app:
        seed_generated_media(app)
        from indi_allsky.flask import db
        from indi_allsky.flask.models import IndiAllSkyDbTaskQueueTable as Task, TaskQueueQueue, TaskQueueState
        from indi_allsky.flask.models import IndiAllSkyDbKeogramTable as Keogram, IndiAllSkyDbStarTrailsTable as Startrail
        from indi_allsky.generation_result import finish_keogram_task
        with app.app_context():
            root=Path(app.config['INDI_ALLSKY_IMAGE_FOLDER'])
            kg=Keogram.query.filter_by(camera_id=2).first();st=Startrail.query.filter_by(camera_id=2).first()
            assert kg and st
            def path(row):
                value=Path(row.filename);return value if value.is_absolute() else root/value
            task=Task(queue=TaskQueueQueue.VIDEO,state=TaskQueueState.RUNNING,
                      data={'action':'generateKeogramStarTrails','kwargs':{'camera_id':2},'profile_id':'test-profile-2'})
            db.session.add(task);db.session.commit();task_id=task.id
            finish_keogram_task(task,camera_id=2,night=True,keogram=(kg,path(kg)),startrail=(st,path(st)),
                                video=(None,root/'absent.mp4'),frames=59,min_frames=250,video_enabled=True)
            db.session.expire_all();saved=db.session.get(Task,task_id)
            assert saved.state==TaskQueueState.SUCCESS and 'Partial generation' in saved.result
            assert saved.data['generation_outcome']['outputs'][2]['eligible_frames']==59
        endpoint='/indi-allsky/modern-admin/tasks/'+str(task_id)
        for uid in (1,2):
            client=login_client(app,uid)
            response=client.get(endpoint)
            assert response.status_code==200,response.text[:500]
            assert 'Partial generation' in response.text and '59/250 eligible frames' in response.text
            assert 'test-profile-2' in response.text and 'Insufficient eligible frames' in response.text
            import re
            from html import unescape
            for label in ('Keogram','Startrail'):
                match=re.search(r'<a href="([^"]+)">Open '+re.escape(label)+r'</a>',response.text)
                link={'href':unescape(match.group(1))} if match else None
                assert link and 'camera_id=2' in link['href'] and 'profile_id=test-profile-2' in link['href']
                assert client.get(link['href']).status_code==200
            assert '>Open Startrail video</a>' not in response.text
        assert app.test_client().get(endpoint).status_code==302
        with app.app_context():
            kg=Keogram.query.filter_by(camera_id=2).first();st=Startrail.query.filter_by(camera_id=2).first()
            task=db.session.get(Task,task_id)
            finish_keogram_task(task,camera_id=2,night=False,keogram=(kg,root/'absent.jpg'),
                                startrail=(st,path(st)),video=(None,root/'absent.mp4'),frames=0,min_frames=250,video_enabled=True)
            db.session.expire_all()
            assert db.session.get(Task,task_id).state==TaskQueueState.FAILED
            assert Keogram.query.filter_by(camera_id=2).first().success is False
        print('Generation receipt persists with camera/profile, renders to both roles, and commits missing-output failure: PASS')

if __name__=='__main__':run()
