#!/usr/bin/env python3
"""A real storage child consumes cleanup while scoped generation stays protected."""
from datetime import datetime, timedelta
import multiprocessing
from pathlib import Path
import time
from unittest.mock import patch

from hybrid_runtime_fixture import isolated_app


def run():
    multiprocessing.set_start_method('fork')
    with isolated_app(file_database=True, multi_camera=True) as app:
        from indi_allsky.flask import db, models
        from indi_allsky.storage_pressure import GIB
        from indi_allsky.storage_pressure_runtime import StoragePressureRuntime
        from indi_allsky.storage_worker import StorageWorker

        root = Path(app.config['INDI_ALLSKY_IMAGE_FOLDER'])
        now = datetime.now()
        day = (now - timedelta(days=6)).date()
        protected_path = root / 'process-protected.jpg'
        disposable_path = root / 'process-disposable.jpg'
        protected_path.write_bytes(b'protected generation source')
        disposable_path.write_bytes(b'dedicated disposable fixture')

        with app.app_context():
            image = models.IndiAllSkyDbImageTable
            db.session.add(image(id=1, camera_id=1, filename=str(protected_path),
                createDate=now-timedelta(days=6), dayDate=day, night=True,
                exposure=1, gain=0, adu=.1, width=1, height=1, data={}))
            db.session.add(image(id=2, camera_id=2, filename=str(disposable_path),
                createDate=now-timedelta(days=6), dayDate=day, night=True,
                exposure=1, gain=0, adu=.1, width=1, height=1, data={}))
            generation = models.IndiAllSkyDbTaskQueueTable(
                queue=models.TaskQueueQueue.VIDEO,
                state=models.TaskQueueState.RUNNING,
                data={'action':'generateVideo', 'kwargs':{
                    'camera_id':1, 'timespec':day.strftime('%Y%m%d'), 'night':True}})
            cleanup = models.IndiAllSkyDbTaskQueueTable(
                queue=models.TaskQueueQueue.VIDEO,
                state=models.TaskQueueState.QUEUED,
                data={'action':'storagePressureCleanup', 'kwargs':{}})
            db.session.add_all((generation, cleanup))
            db.session.commit()
            cleanup_id = cleanup.id
            generation_id = generation.id
            config = models.IndiAllSkyDbConfigTable.query.one().data
            db.session.remove()

        error_q = multiprocessing.Queue()
        storage_q = multiprocessing.Queue()
        upload_q = multiprocessing.Queue()
        worker = StorageWorker(1, config, error_q, storage_q, upload_q, [], [])
        try:
            with patch.object(StoragePressureRuntime, 'free_bytes', lambda self: 4 * GIB):
                worker.start()
                storage_q.put({'task_id':cleanup_id})
                deadline = time.monotonic() + 30
                state = None
                while time.monotonic() < deadline:
                    with app.app_context():
                        db.session.remove()
                        task = db.session.get(models.IndiAllSkyDbTaskQueueTable, cleanup_id)
                        state = task.state
                        if state in (models.TaskQueueState.SUCCESS, models.TaskQueueState.FAILED):
                            break
                    time.sleep(.1)
                assert state in (models.TaskQueueState.SUCCESS, models.TaskQueueState.FAILED), state

            with app.app_context():
                db.session.remove()
                cleanup = db.session.get(models.IndiAllSkyDbTaskQueueTable, cleanup_id)
                generation = db.session.get(models.IndiAllSkyDbTaskQueueTable, generation_id)
                assert cleanup.state == models.TaskQueueState.FAILED, cleanup.state
                assert generation.state == models.TaskQueueState.RUNNING
                assert db.session.get(models.IndiAllSkyDbImageTable, 1) is not None
                assert db.session.get(models.IndiAllSkyDbImageTable, 2) is None
                assert protected_path.is_file()
                assert not disposable_path.exists()
        finally:
            if worker.is_alive():
                storage_q.put({'stop':True})
                worker.join(10)
            if worker.is_alive():
                worker.terminate()
                worker.join(5)
            if worker.is_alive() and hasattr(worker, 'kill'):
                worker.kill()
                worker.join(5)
            assert not worker.is_alive()
            for channel in (error_q, storage_q, upload_q):
                channel.close()
                channel.join_thread()
    print('Storage process: real child cleanup consumption and scoped protection PASS')


if __name__ == '__main__':
    run()
