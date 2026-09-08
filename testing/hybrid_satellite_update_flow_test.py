#!/usr/bin/env python3
"""Real SQLite replacement, worker outcome and Hybrid rendering; no live provider writes."""
from types import SimpleNamespace
from unittest.mock import patch
from hybrid_runtime_fixture import isolated_app, login_client
from hybrid_astropanel_satellite_test import checksum


def run():
    with isolated_app(multi_camera=True) as app:
        from sqlalchemy import text
        from indi_allsky.flask import db
        from indi_allsky.flask.models import IndiAllSkyDbTleDataTable as Tle
        from indi_allsky.flask.models import IndiAllSkyDbTaskQueueTable as Task, TaskQueueQueue, TaskQueueState
        from indi_allsky.satellite_download import IndiAllskyUpdateSatelliteData as Provider
        from indi_allsky.video import VideoWorker
        import requests
        line1=checksum('1 25544U 98067A   26250.00000000  .00010000  00000-0  18000-3 0  999')
        line2=checksum('2 25544  51.6400 100.0000 0005000  20.0000 340.0000 15.5000000040000')
        valid='NEW SATELLITE\n'+line1+'\n'+line2+'\n'
        closed=[]
        responses={}
        def download(url,**kwargs):
            assert kwargs==dict(allow_redirects=True,verify=True,timeout=(15.0,30.0))
            name=next(name for name in ('visual','starlink','stations') if 'GROUP='+name+'&' in url)
            value=responses.get(name,(200,valid))
            if isinstance(value,Exception): raise value
            return SimpleNamespace(status_code=value[0],text=value[1],close=lambda:closed.append(name))
        worker=VideoWorker.__new__(VideoWorker);worker.config={}
        with app.app_context():
            for group in Provider.tle_urls:
                db.session.add(Tle(title='OLD-'+str(group),line1=line1,line2=line2,group=group))
            db.session.add(Tle(title='UNRELATED',line1=line1,line2=line2,group=-1))
            db.session.commit()
            def snapshot(group):
                return [(r.id,r.title,r.line1,r.line2,r.createDate) for r in Tle.query.filter_by(group=group).order_by(Tle.id)]
            old_starlink=snapshot(801);other=snapshot(-1)
            task=Task(queue=TaskQueueQueue.VIDEO,state=TaskQueueState.QUEUED,
                      data={'action':'updateSatelliteTleData','unrelated':'preserve'})
            db.session.add(task);db.session.commit();task_id=task.id
            responses['starlink']=(403,'denied')
            with patch('indi_allsky.satellite_download.requests.get',side_effect=download):
                worker.updateSatelliteTleData(task)
            db.session.expire_all();task=db.session.get(Task,task_id)
            assert task.state==TaskQueueState.FAILED and '2/3' in task.result and 'starlink' in task.result
            assert task.data['unrelated']=='preserve'
            assert task.data['satellite_update_outcome']['failed']==['starlink']
            assert task.data['satellite_update_outcome']['groups'][1]['reason']=='HTTP 403'
            assert snapshot(801)==old_starlink and snapshot(-1)==other
            assert Tle.query.filter_by(group=800).one().title=='NEW SATELLITE'
            assert closed==['visual','starlink','stations']
        for uid in (1,2):
            page=login_client(app,uid).get('/indi-allsky/modern-admin/tasks/'+str(task_id))
            assert page.status_code==200
            assert 'Satellite update</h2>' in page.text and 'HTTP 403; previous catalog retained' in page.text
            assert 'Visual satellites</dt><dd><strong>Updated' in page.text
            assert 'Starlink</dt><dd><strong>Failed' in page.text
            assert 'Space stations</dt><dd><strong>Updated' in page.text
        assert app.test_client().get('/indi-allsky/modern-admin/tasks/'+str(task_id)).status_code==302
        with app.app_context():
            # All malformed response variants preserve exact old rows/timestamps.
            provider=Provider({})
            malformed=['', '   ', '<html>error</html>', 'TRUNCATED\n'+line1,
                       valid+'INCOMPLETE\n', 'TITLE\n'+'x'*69+'\n'+'y'*69,
                       'TITLE\n'+line1+'\n'+line2[:2]+'99999'+line2[7:]]
            for body in malformed:
                responses['starlink']=(200,body)
                with patch('indi_allsky.satellite_download.requests.get',side_effect=download):
                    result=provider.update()
                assert result['failed']==['starlink'] and snapshot(801)==old_starlink
            for error in (requests.exceptions.ReadTimeout(),requests.exceptions.SSLError(),requests.exceptions.TooManyRedirects()):
                responses['starlink']=error
                with patch('indi_allsky.satellite_download.requests.get',side_effect=download):
                    result=provider.update()
                assert result['failed']==['starlink'] and snapshot(801)==old_starlink
            # Real SQLite failure after DELETE must roll the deletion back.
            responses.clear()
            db.session.execute(text("CREATE TRIGGER reject_starlink BEFORE INSERT ON tle_data WHEN NEW.\"group\"=801 BEGIN SELECT RAISE(FAIL, 'fixture insertion failure'); END"))
            db.session.commit()
            with patch('indi_allsky.satellite_download.requests.get',side_effect=download):
                result=provider.update()
            assert result['failed']==['starlink'] and result['groups'][1]['reason']=='Database update failed'
            assert snapshot(801)==old_starlink and snapshot(-1)==other
            db.session.execute(text('DROP TRIGGER reject_starlink'));db.session.commit()
            task=db.session.get(Task,task_id)
            with patch('indi_allsky.satellite_download.requests.get',side_effect=download):
                worker.updateSatelliteTleData(task)
            db.session.expire_all();task=db.session.get(Task,task_id)
            assert task.state==TaskQueueState.SUCCESS and task.result=='Satellite data updated'
            assert task.data['satellite_update_outcome']['failed']==[]
            assert len(task.data['satellite_update_outcome']['updated'])==3
            assert all(Tle.query.filter_by(group=g).one().title=='NEW SATELLITE' for g in Provider.tle_urls)
            # Identical valid text does not duplicate entries on a repeated update.
            with patch('indi_allsky.satellite_download.requests.get',side_effect=download):
                worker.updateSatelliteTleData(task)
            assert Tle.query.count()==4
        print('Satellite groups: partial HTTP failure, empty/malformed feeds, network failures, real SQL rollback, recovery, task persistence and both Hybrid roles: PASS')


if __name__=='__main__':run()
