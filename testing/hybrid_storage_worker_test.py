#!/usr/bin/env python3
"""Execute the real worker method against isolated tasks and policy reloads."""
import ast
from datetime import timedelta
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
from hybrid_runtime_fixture import isolated_app


def run():
    with isolated_app(multi_camera=True) as app, app.app_context():
        from indi_allsky.flask import db, models
        from indi_allsky.storage_pressure_runtime import StoragePressureRuntime
        from indi_allsky.config import IndiAllSkyConfig
        path = Path(__file__).resolve().parents[1] / 'indi_allsky/video.py'
        tree = ast.parse(path.read_text())
        method = next(n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name == 'storagePressureCleanup')
        scope = {'__package__':'indi_allsky', 'db':db, 'timedelta':timedelta,
                 'NotificationCategory':models.NotificationCategory}
        exec(compile(ast.fix_missing_locations(ast.Module(body=[method],type_ignores=[])),str(path),'exec'),scope)
        notices = []
        worker = SimpleNamespace(image_dir=Path(app.config['INDI_ALLSKY_IMAGE_FOLDER']),
                                 _miscDb=SimpleNamespace(addNotification=lambda *a, **k:notices.append(a)),
                                 config={'STORAGE_PRESSURE': {'ENABLE':True}})
        def task():
            entry = models.IndiAllSkyDbTaskQueueTable(queue=models.TaskQueueQueue.VIDEO,
                state=models.TaskQueueState.RUNNING, data={'action':'storagePressureCleanup','kwargs':{}})
            db.session.add(entry);db.session.commit()
            return entry
        # New global config beats the worker's stale enabled snapshot.
        with patch.object(IndiAllSkyConfig, '__init__', return_value=None), \
             patch.object(IndiAllSkyConfig, 'config', new_callable=lambda:property(lambda self:{'STORAGE_PRESSURE':{'ENABLE':False}})):
            entry = task()
            scope['storagePressureCleanup'](worker, entry)
            assert entry.state == models.TaskQueueState.SUCCESS and 'not needed' in entry.result
        for status, expected in (('insufficient_old_images',models.TaskQueueState.FAILED),
                                 ('generation_pending',models.TaskQueueState.FAILED),
                                 ('recovered',models.TaskQueueState.SUCCESS)):
            entry = task()
            with patch.object(StoragePressureRuntime,'run',return_value={'status':status,'deleted':2,'free_bytes':6*1024**3}):
                scope['storagePressureCleanup'](worker,entry)
            assert entry.state == expected and 'deleted 2' in entry.result
        assert len(notices) == 2
        entry = task()
        with patch.object(StoragePressureRuntime,'run',side_effect=BlockingIOError):
            scope['storagePressureCleanup'](worker,entry)
        assert entry.state == models.TaskQueueState.FAILED and 'deferred' in entry.result
    print('Storage worker: latest disable, observed task results, notifications and lock contention PASS')


if __name__ == '__main__':
    run()
