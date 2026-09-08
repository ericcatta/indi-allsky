#!/usr/bin/env python3
"""Smoke provider effects, saved-state isolation and Hybrid failure presentation."""
from types import SimpleNamespace
from unittest.mock import patch
from hybrid_runtime_fixture import isolated_app, login_client


def run():
    with isolated_app(multi_camera=True) as app:
        from indi_allsky.flask import db
        from indi_allsky.flask.models import IndiAllSkyDbCameraTable as Camera, IndiAllSkyDbTaskQueueTable as Task, TaskQueueQueue, TaskQueueState
        from indi_allsky.smoke import IndiAllskySmokeUpdate as Provider
        from indi_allsky.video import VideoWorker
        from indi_allsky.modern_admin_smoke_status import build_smoke_status
        import requests
        def kml(coords='-101,39,0\n-99,39,0\n-99,41,0\n-101,41,0\n-101,39,0',folder='Smoke (Heavy)'):
            return ('<kml xmlns="http://www.opengis.net/kml/2.2"><Document><Folder><name>'+folder+'</name><Placemark><Polygon><outerBoundaryIs><LinearRing><coordinates>'+coords+'</coordinates></LinearRing></outerBoundaryIs></Polygon></Placemark></Folder></Document></kml>').encode()
        with app.app_context():
            camera=db.session.get(Camera,1);camera.latitude=40;camera.longitude=-100
            camera.data={'SMOKE_RATING':30,'SMOKE_DATA_TS':123,'unrelated':'preserve'}
            other=db.session.get(Camera,2);other.data={'untouched':True}
            task=Task(queue=TaskQueueQueue.VIDEO,state=TaskQueueState.QUEUED,data={'action':'updateSmokeData','kwargs':{'camera_id':1}})
            db.session.add(task);db.session.commit();task_id=task.id
            worker=VideoWorker.__new__(VideoWorker);worker.config={}
            closed=[]
            with patch('indi_allsky.smoke.requests.get',return_value=SimpleNamespace(status_code=403,text='denied',close=lambda:closed.append(True))):
                worker.updateSmokeData(task,camera_id=1)
            db.session.expire_all();camera=db.session.get(Camera,1);task=db.session.get(Task,task_id)
            assert task.state==TaskQueueState.FAILED and task.data['smoke_update_outcome']['reason']=='HTTP 403'
            assert camera.data['SMOKE_RATING']==30 and camera.data['SMOKE_DATA_TS']==123 and camera.data['unrelated']=='preserve'
            assert camera.data['SMOKE_UPDATE_STATUS']['state']=='unavailable' and closed==[True]
            assert db.session.get(Camera,2).data=={'untouched':True}
            for body in (b'',b'<bad>',b'<kml/>',kml(coords=''),kml(coords='bad'),kml(coords='1,2,0')):
                provider=Provider({})
                with patch.object(provider,'download_kml',return_value=body):
                    result=provider.update(camera)
                assert result['state']=='unavailable',body
                assert camera.data['SMOKE_DATA_TS']==123 and camera.data['SMOKE_RATING']==30
            with patch('indi_allsky.smoke.requests.get',side_effect=requests.exceptions.TooManyRedirects()):
                result=Provider({}).update(camera)
            assert result['state']=='unavailable'
        for uid in (1,2):
            client=login_client(app,uid)
            page=client.get('/indi-allsky/modern-admin/tasks/'+str(task_id))
            assert page.status_code==200 and 'Smoke update failed' in page.text and 'HTTP 403' in page.text
            status=client.get('/indi-allsky/ajax/status_update',query_string={'camera_id':1})
            assert status.status_code==200 and 'Light [update failed]' in status.json['status_text']
            other_status=client.get('/indi-allsky/ajax/status_update',query_string={'camera_id':2})
            assert other_status.status_code==200 and 'Smoke: No data' in other_status.json['status_text']
            assert '[update failed]' not in other_status.json['status_text']
        with app.app_context():
            camera=db.session.get(Camera,1)
            # Real geometry preserves heavy-before-light and one-degree intersection.
            for folder,rating in (('Smoke (Heavy)',90),('Smoke (Medium)',60),('Smoke (Light)',30)):
                with patch('indi_allsky.smoke.IndiAllskySmokeUpdate.download_kml',return_value=kml(folder=folder)):
                    worker.updateSmokeData(db.session.get(Task,task_id),camera_id=1)
                assert camera.data['SMOKE_RATING']==rating and camera.data['SMOKE_DATA_TS']>123
            with patch('indi_allsky.smoke.IndiAllskySmokeUpdate.download_kml',return_value=kml(coords='0,0,0\n1,0,0\n1,1,0\n0,1,0\n0,0,0')):
                worker.updateSmokeData(db.session.get(Task,task_id),camera_id=1)
            assert camera.data['SMOKE_RATING']==1 and db.session.get(Task,task_id).state==TaskQueueState.SUCCESS
            # This matches the configured Swiss cameras: outside the provider's
            # existing NW-hemisphere applicability rule, not a failed download.
            camera.longitude=8;camera.latitude=46;db.session.commit()
            with patch('indi_allsky.smoke.requests.get',side_effect=AssertionError('No download outside coverage')):
                worker.updateSmokeData(db.session.get(Task,task_id),camera_id=1)
            assert camera.data['SMOKE_RATING']==-1 and camera.data['SMOKE_UPDATE_STATUS']['state']=='not_covered'
            assert 'does not cover' in db.session.get(Task,task_id).result
            assert build_smoke_status(camera.data)['smoke_rating_status']=='[outside provider coverage]'
        assert build_smoke_status({'SMOKE_RATING':30,'SMOKE_DATA_TS':1},now=90000)['smoke_rating_status']=='[old]'
        assert build_smoke_status({'SMOKE_RATING':1,'SMOKE_DATA_TS':100},now=100)['smoke_rating']=='Clear'
        for value in (None,[],{},True,'bad',float('nan')):
            assert build_smoke_status({'SMOKE_RATING':value})['smoke_rating']=='No data'
        for value in (None,'bad',float('nan'),True,1001):
            assert build_smoke_status({'SMOKE_RATING':30,'SMOKE_DATA_TS':value},now=1000)['smoke_rating_status']=='[age unknown]'
        assert build_smoke_status({'SMOKE_RATING':30,'SMOKE_UPDATE_STATUS':{'state':'unavailable'}})['smoke_rating_status']=='[update failed]'
        print('Smoke: HTTP/network/malformed failures, retained data, actual geometry, recovery, coverage, worker result and Hybrid roles: PASS')


if __name__=='__main__':run()
