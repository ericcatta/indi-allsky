#!/usr/bin/env python3
"""Actual Observatory evidence and destinations with Classic imports prohibited."""
from datetime import datetime, timedelta
import html
import re
from unittest.mock import patch
from hybrid_runtime_fixture import isolated_app, login_client
from hybrid_generation_fixture import seed_generation
from hybrid_source_media_fixture import seed_source_media


def run():
    with isolated_app(multi_camera=True) as app:
        seed_generation(app); seed_source_media(app)
        from indi_allsky.flask import db
        from indi_allsky.flask.models import (IndiAllSkyDbImageTable as Image,
            IndiAllSkyDbConfigTable as Config, IndiAllSkyDbTaskQueueTable as Task,
            TaskQueueState, TaskQueueQueue)
        from indi_allsky.observatory_runtime import ObservatoryRuntime
        from sqlalchemy.exc import SQLAlchemyError
        now = datetime.now()
        with app.app_context():
            db.session.get(Image,1).createDate=now-timedelta(seconds=20)
            db.session.get(Image,2).createDate=now-timedelta(hours=2)
            for state in (TaskQueueState.QUEUED,TaskQueueState.QUEUED,TaskQueueState.FAILED):
                db.session.add(Task(queue=TaskQueueQueue.VIDEO,state=state,data={}))
            db.session.commit()
            config=db.session.get(Config,1).data
            snapshot=ObservatoryRuntime().snapshot(config,now)
            assert [c['health'][0]['status'] for c in snapshot['cameras']]==['ok','stale']
            assert [c['image_id'] for c in snapshot['cameras']]==[1,2]
            assert [c['profiles'][0]['id'] for c in snapshot['cameras']]==['test-profile-1','test-profile-2']
            assert all(source['latest'] for c in snapshot['cameras'] for source in c['sources'])
            assert {(r['state'],r['count']) for r in snapshot['tasks']}=={('Queued',2),('Failed',1)}
            assert snapshot['storage']['total']>0
        endpoint='/indi-allsky/modern-admin/observatory'
        for uid in (1,2):
            client=login_client(app,uid)
            response=client.get(endpoint)
            assert response.status_code==200,response.text[:500]
            assert 'Latest frame is fresh.' in response.text and 'Latest frame is stale.' in response.text
            assert 'test-profile-1' in response.text and 'test-profile-2' in response.text
            for removed in ('Future backend contract','Static Product Contract','Nothing is claimed yet','prototype'):
                assert removed not in response.text
            # Verify every content navigation destination renders, including per-camera sources.
            main=response.text.split('<main ',1)[1].split('</main>',1)[0]
            for target in re.findall(r'href="([^"]+)"',main):
                result=client.get(html.unescape(target))
                assert result.status_code==200,(target,result.status_code,result.text[:300])
        assert app.test_client().get(endpoint).status_code==302
        client=login_client(app,1)
        with patch.object(ObservatoryRuntime,'camera_records',side_effect=SQLAlchemyError('private DB details')), \
             patch.object(ObservatoryRuntime,'task_counts',side_effect=SQLAlchemyError('private task details')), \
             patch('indi_allsky.observatory_runtime.shutil.disk_usage',side_effect=OSError('private path')):
            response=client.get(endpoint)
            assert response.status_code==200
            assert 'Camera records could not be read.' in response.text
            assert 'Task records could not be read.' in response.text
            assert 'media filesystem could not be inspected' in response.text
            assert 'private' not in response.text and 'No task records.' not in response.text
            assert 'data-observatory-camera' not in response.text
        with app.app_context():
            Image.query.delete();Task.query.delete();db.session.commit()
        response=client.get(endpoint)
        assert response.text.count('No latest frame metadata.')==2
        assert 'No task records.' in response.text
        assert 'latest record' in response.text  # source-only acquisition remains visible
        print('Observatory: live records, fresh/stale/missing cameras, source-only, task counts, capacity, both roles, all content links, sanitized failures and authentication: PASS')


if __name__=='__main__':run()
