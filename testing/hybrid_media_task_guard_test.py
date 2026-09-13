#!/usr/bin/env python3
"""Race real upload publication against real deletion on separate SQLite sessions."""
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from datetime import datetime, timedelta
from pathlib import Path
from threading import Event
from unittest.mock import patch
from hybrid_runtime_fixture import isolated_app


def run():
    with isolated_app(multi_camera=True, file_database=True) as app:
        from indi_allsky.flask import db, models
        from indi_allsky import media_task_guard as guard, storage_pressure_runtime as runtime_module
        model = models.IndiAllSkyDbImageTable
        task_model = models.IndiAllSkyDbTaskQueueTable
        root = Path(app.config['INDI_ALLSKY_IMAGE_FOLDER'])
        now = datetime.now()
        with app.app_context():
            for identity in (1, 2):
                path = root/f'race-{identity}.jpg'
                path.write_bytes(b'disposable concurrency fixture')
                db.session.add(model(id=identity, camera_id=identity, filename=str(path),
                    createDate=now-timedelta(days=5), dayDate=now.date(), night=False,
                    exposure=1,gain=0,adu=.1,width=1,height=1,data={}))
            db.session.commit()
        original_lock = guard.media_task_lock
        for producer_first, identity in ((True,1),(False,2)):
            held, attempted, release = Event(), Event(), Event()
            @contextmanager
            def observed_lock(*, exclusive, root=None):
                first = exclusive != producer_first
                if not first:
                    attempted.set()
                with original_lock(exclusive=exclusive,root=root):
                    if first:
                        held.set()
                        assert release.wait(20), 'coordinator did not release lock'
                    yield
            def publish():
                with app.app_context():
                    task=task_model(queue=models.TaskQueueQueue.UPLOAD,state=models.TaskQueueState.QUEUED,
                         data={'action':'upload','model':model.__name__,'id':identity,'profile_id':'test-profile-'+str(identity)})
                    try:
                        guard.persist_upload_task(task)
                        return 'queued'
                    except FileNotFoundError:
                        db.session.rollback()
                        return 'removed'
            def delete():
                with app.app_context():
                    runtime=runtime_module.StoragePressureRuntime({},db.session,models,root)
                    candidate=runtime_module.ImageCandidate(now-timedelta(days=5),model,identity)
                    try:
                        runtime.delete(candidate)
                        return 'deleted'
                    except RuntimeError as error:
                        assert 'queued for transfer' in str(error), error
                        db.session.rollback()
                        return 'protected'
            with patch.object(guard,'media_task_lock',observed_lock), \
                 patch.object(runtime_module,'media_task_lock',observed_lock), \
                 ThreadPoolExecutor(max_workers=2) as pool:
                first=pool.submit(publish if producer_first else delete)
                try:
                    assert held.wait(20)
                    second=pool.submit(delete if producer_first else publish)
                    assert attempted.wait(20)
                    assert not second.done(), 'conflicting effect bypassed the lock'
                finally:
                    release.set()
                assert (first.result(timeout=20),second.result(timeout=20)) == (
                    ('queued','protected') if producer_first else ('deleted','removed'))
            with app.app_context():
                assert (db.session.get(model,identity) is not None) == producer_first
                assert (root/f'race-{identity}.jpg').exists() == producer_first
                tasks=task_model.query.all()
                assert len(tasks)==1 and tasks[0].data['id']==1
        # Both legacy latest-file jobs and all media families use the centralized
        # publication point, rather than retaining inline add/commit pairs.
        source=(Path(__file__).resolve().parents[1]/'indi_allsky/miscUpload.py').read_text()
        assert 'db.session.add(' not in source
        assert source.count('persist_upload_task(')==26
    print('Media task guard: separate SQLite sessions, producer wins preserves file, deletion wins rejects orphan task, 26 publication sites PASS')


if __name__=='__main__':run()
