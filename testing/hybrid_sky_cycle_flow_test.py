#!/usr/bin/env python3
"""Persisted cycle summaries with camera/date isolation and actual Flask pages."""
from datetime import datetime, date, timedelta
from unittest.mock import patch
from hybrid_runtime_fixture import isolated_app, login_client


def run():
    with isolated_app(multi_camera=True) as app:
        from indi_allsky.flask import db
        from indi_allsky.flask.models import IndiAllSkyDbImageTable as Image, IndiAllSkyDbVideoTable as Video, IndiAllSkyDbCameraTable as Camera
        from indi_allsky.sky_cycle_runtime import camera_cycle
        from indi_allsky.flask.models import IndiAllSkyDbFitsImageTable as Fits
        from sqlalchemy.exc import SQLAlchemyError
        day=date(2026,1,5)
        with app.app_context():
            for cid, offset, night in ((1,0,False),(1,1,True),(1,2,True),(2,0,True)):
                db.session.add(Image(filename=f'/synthetic/{cid}-{offset}.jpg',camera_id=cid,
                    dayDate=day,createDate=datetime(2026,1,5,12)+timedelta(hours=offset),
                    night=night,exposure=1,gain=1,adu=.1))
            db.session.add(Image(filename='/synthetic/old.jpg',camera_id=1,dayDate=day-timedelta(days=1),
                createDate=datetime(2026,1,4,12),night=True,exposure=1,gain=1,adu=.1))
            for cid, delta, success in ((1,0,True),(1,0,False),(2,0,True),(1,-1,True)):
                db.session.add(Video(filename=f'/synthetic/video-{cid}-{delta}-{success}',camera_id=cid,
                    dayDate=day+timedelta(days=delta),night=True,success=success))
            db.session.commit()
            result=camera_cycle(db.session.get(Camera,1),Image,[],[('Video',Video)])
            assert result['day_date']==day and result['latest']==datetime(2026,1,5,14)
            assert [p['count'] for p in result['phases']]==[1,2]
            assert result['outputs']==[{'label':'Video','count':2,'successful':1}]
            other=camera_cycle(db.session.get(Camera,2),Image,[],[('Video',Video)])
            assert [p['count'] for p in other['phases']]==[1]
            assert other['outputs'][0]['count']==1
        endpoint='/indi-allsky/modern-admin/sky-cycle'
        for uid in (1,2):
            response=login_client(app,uid).get(endpoint)
            assert response.status_code==200,response.text
            assert 'Test Camera 1' in response.text and 'Test Camera 2' in response.text
            assert '2026-01-05' in response.text and '2 image records' in response.text
            assert 'Static placeholders' not in response.text and 'FITS: 0 records' in response.text
        assert app.test_client().get(endpoint).status_code==302
        client=login_client(app,1)
        with patch('indi_allsky.sky_cycle_runtime.camera_cycle',side_effect=SQLAlchemyError('private details')):
            response=client.get(endpoint)
            assert response.status_code==200 and 'could not be read' in response.text
            assert 'private details' not in response.text and '2 image records' not in response.text
        with app.app_context():
            Image.query.delete();db.session.commit()
        assert client.get(endpoint).text.count('No saved image, FITS or RAW records for this camera.')==2
        with app.app_context():
            for cid, offset in ((1,0),(1,-1),(2,0)):
                db.session.add(Fits(filename=f'/synthetic/source-{cid}-{offset}.fits',camera_id=cid,
                    dayDate=day+timedelta(days=offset),createDate=datetime(2026,1,5,12)+timedelta(days=offset),
                    night=True,exposure=1,gain=1))
            db.session.commit()
            result=camera_cycle(db.session.get(Camera,1),Image,[('FITS',Fits)],[('Video',Video)])
            assert result['status']=='available' and result['phases']==[]
            assert result['sources']==[{'label':'FITS','count':1}]
        response=client.get(endpoint)
        assert response.text.count('FITS: 1 records')==2
        assert response.text.count('No processed image records for this cycle.')==2
        print('Sky Cycle: camera/date isolation, day/night aggregates, output success, roles, empty and provider failure: PASS')


if __name__=='__main__':run()
