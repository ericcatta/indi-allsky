#!/usr/bin/env python3
"""Real files and task rows: scoped generation protects sources during cleanup."""
from datetime import datetime, timedelta
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
from hybrid_runtime_fixture import isolated_app


def run():
    with isolated_app(multi_camera=True) as app, app.app_context():
        from indi_allsky.flask import db, models
        from indi_allsky.storage_pressure import GIB
        from indi_allsky.storage_pressure_runtime import StoragePressureRuntime
        from indi_allsky.generation_retention import generation_scope
        root = Path(app.config['INDI_ALLSKY_IMAGE_FOLDER'])
        now = datetime.now()
        day = (now - timedelta(days=5)).date()
        image = models.IndiAllSkyDbImageTable
        entries = []
        for ident, camera, night, offset in ((1,1,True,0),(2,1,False,0),(3,2,True,0),(4,1,True,-1)):
            path = root / ('scope-%d.jpg' % ident)
            path.write_bytes(b'dedicated disposable fixture')
            entry = image(id=ident, camera_id=camera, filename=str(path),
                createDate=now-timedelta(days=5)+timedelta(days=offset),
                dayDate=day+timedelta(days=offset), night=night, exposure=1,
                gain=0, adu=.1, data={})
            db.session.add(entry); entries.append(entry)
        db.session.commit()
        task = models.IndiAllSkyDbTaskQueueTable(queue=models.TaskQueueQueue.VIDEO,
            state=models.TaskQueueState.RUNNING, data={'action':'generateKeogramStarTrails',
                'kwargs':{'camera_id':1,'timespec':day.strftime('%Y%m%d'),'night':True}})
        db.session.add(task); db.session.commit()
        runtime = StoragePressureRuntime({},db.session,models,root,
            disk_usage=lambda p:SimpleNamespace(free=4*GIB))
        assert [runtime.protected(e,[task]) for e in entries] == [True,False,False,False]
        result = runtime.run(now)
        assert result['deleted'] == 3, result
        assert Path(entries[0].filename).exists()
        assert image.query.count() == 1
        # A generation published after the candidate scan must still win under
        # the existing exclusive deletion/shared publication lock.
        task.setSuccess('fixture generation finished')
        candidate = next(runtime.candidates(runtime.options.cutoff(now)))
        task.state = models.TaskQueueState.QUEUED; db.session.commit()
        try:
            runtime.delete(candidate)
        except RuntimeError:
            db.session.rollback()
        else:
            raise AssertionError('queued generation lost its source')
        assert Path(entries[0].filename).exists()
        for action in ('generateVideo','generatePanoramaVideo','generateKeogramStarTrails'):
            data={'action':action,'kwargs':{'camera_id':1,'timespec':day.strftime('%Y%m%d'),'night':True}}
            scope=generation_scope(data,lambda _:None)
            assert scope.protects(entries[0])
            for bad in ({}, {'camera_id':True}, {'camera_id':1,'timespec':'invalid','night':True}):
                assert generation_scope({'action':action,'kwargs':bad},lambda _:None) is None
        anchor=entries[0]
        data={'action':'generateMiniVideo','kwargs':{'camera_id':1,'image_id':1,'pre_seconds':30,'post_seconds':60}}
        scope=generation_scope(data,lambda _:anchor)
        # Exact inclusive range, irrespective of night/day boundary.
        for delta,expected in ((-31,False),(-30,True),(0,True),(60,True),(61,False)):
            sample=image(camera_id=1,createDate=anchor.createDate+timedelta(seconds=delta),night=False)
            assert scope.protects(sample) == expected
        assert generation_scope(data,lambda _:None) is None
        task.data={'action':'generateVideo'}; db.session.commit()
        assert runtime.run(now)['status'] == 'generation_pending'
        from indi_allsky.storage_worker import StorageWorker, recover_interrupted_cleanup
        from indi_allsky.video import VideoWorker
        cleanup = models.IndiAllSkyDbTaskQueueTable(queue=models.TaskQueueQueue.VIDEO,
            state=models.TaskQueueState.QUEUED, data={'action':'storagePressureCleanup'})
        db.session.add(cleanup); db.session.commit()
        worker = object.__new__(StorageWorker)
        with patch.object(VideoWorker, 'processTask', return_value='dispatched') as parent:
            assert worker.processTask({'task_id':cleanup.id}) == 'dispatched'
            parent.assert_called_once()
            worker.processTask({'task_id':task.id})
            assert parent.call_count == 1  # generation never runs in this consumer
        assert task.state == models.TaskQueueState.FAILED
        task.state = models.TaskQueueState.RUNNING
        db.session.commit()
        recover_interrupted_cleanup()
        assert cleanup.state == models.TaskQueueState.FAILED
        assert task.state == models.TaskQueueState.RUNNING  # live video untouched
    print('Scoped generation retention: camera/day/night, mini boundaries, missing scope and publication race PASS')


if __name__ == '__main__':
    run()
