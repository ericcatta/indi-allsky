#!/usr/bin/env python3
"""Storage forecast with isolated media/config/state rows and deterministic disk."""
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace
from hybrid_runtime_fixture import isolated_app


def run():
    with isolated_app(multi_camera=True) as app, app.app_context():
        from indi_allsky.flask import db, models
        from indi_allsky.flask.storage_estimate import storage_forecast, duration_label
        from indi_allsky.storage_pressure import GIB
        now = datetime.now()
        config = models.IndiAllSkyDbConfigTable.query.order_by(models.IndiAllSkyDbConfigTable.id.desc()).first()
        config.createDate = datetime.now(timezone.utc).replace(tzinfo=None)-timedelta(hours=4)
        state = db.session.get(models.IndiAllSkyDbStateTable,'CONFIG_ID')
        if state is None:
            state = models.IndiAllSkyDbStateTable(key='CONFIG_ID',value=str(config.id))
            db.session.add(state)
        else: state.value = str(config.id)
        root = Path(app.config['INDI_ALLSKY_IMAGE_FOLDER'])
        for cid in (1,2):
            for hours in (2,1,0):
                db.session.add(models.IndiAllSkyDbImageTable(camera_id=cid,
                    filename=str(root/f'estimate-{cid}-{hours}.jpg'), createDate=now-timedelta(hours=hours),
                    dayDate=now.date(),night=False,exposure=1,gain=0,adu=.1,width=1,height=1,
                    fileSize=GIB//8,data={}))
        db.session.commit()
        args = dict(config={},config_id=config.id,root=root,now=now,
                    disk_usage=lambda path:SimpleNamespace(free=10*GIB,total=30*GIB))
        result = storage_forecast(**args)
        assert result['status']=='estimated', result
        assert result['sample_seconds']==7200 and result['samples']==4
        assert result['gib_per_day']==6 and result['until_threshold']=='0 days, 20 hours'
        assert not result['retention_fits']
        assert duration_label(1)=='less than 1 hour' and duration_label(90000)=='1 days, 1 hours'
        state.value = 'invalid';db.session.commit()
        assert 'confirmed' in storage_forecast(**args)['reason']
        state.value = str(config.id);db.session.commit()
        image = models.IndiAllSkyDbImageTable.query.order_by(models.IndiAllSkyDbImageTable.createDate.desc()).first()
        image.fileSize = None;db.session.commit()
        assert 'recorded size' in storage_forecast(**args)['reason']
        image.fileSize=GIB//8;db.session.commit()
        stale = storage_forecast(**dict(args,now=now+timedelta(hours=1)))
        assert 'stale' in stale['reason']
        config.createDate=datetime.now(timezone.utc).replace(tzinfo=None)-timedelta(minutes=30)
        db.session.commit()
        assert storage_forecast(**args)['status']=='insufficient_data'
    print('Storage estimate: combined camera rate, units, capacity, loaded config, unknown size, stale frames and short observation PASS')


if __name__=='__main__':run()
