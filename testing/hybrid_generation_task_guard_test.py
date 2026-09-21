#!/usr/bin/env python3
"""Generation publication and storage cleanup must serialize across DB sessions."""
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from datetime import datetime, timedelta
from pathlib import Path
from threading import Event
from unittest.mock import patch
from hybrid_runtime_fixture import isolated_app, login_client
from hybrid_account_input_test import csrf


def run():
    with isolated_app(multi_camera=True, file_database=True) as app:
        from indi_allsky.flask import db, models
        from indi_allsky import media_task_guard as guard, storage_pressure_runtime as runtime_module
        from indi_allsky.modern_admin_runtime_effects import ModernAdminTaskEnqueueEffectAdapter
        root = Path(app.config['INDI_ALLSKY_IMAGE_FOLDER'])
        model = models.IndiAllSkyDbImageTable
        now = datetime.now()
        original_lock = guard.media_task_lock
        for identity, action in enumerate(sorted(runtime_module.GENERATION_ACTIONS), 1):
            with app.app_context():
                path = root / f'generation-race-{identity}.jpg'
                path.write_bytes(b'disposable generation fixture')
                db.session.add(model(id=identity, camera_id=1, filename=str(path),
                    createDate=now-timedelta(days=5), dayDate=now.date(), night=False,
                    exposure=1, gain=0, adu=.1, width=1, height=1, data={}))
                db.session.commit()
            held, attempted, release = Event(), Event(), Event()

            @contextmanager
            def observed_lock(*, exclusive, root=None):
                if exclusive:
                    attempted.set()
                with original_lock(exclusive=exclusive, root=root):
                    if not exclusive:
                        held.set()
                        assert release.wait(10), 'coordinator did not release publication'
                    yield

            def publish():
                with app.app_context():
                    adapter = ModernAdminTaskEnqueueEffectAdapter(models.IndiAllSkyDbTaskQueueTable,
                        db.session, models.TaskQueueQueue, models.TaskQueueState)
                    result = adapter.enqueue('VIDEO', 'MANUAL', 100,
                        {'action': action, 'kwargs': {'camera_id': 1, 'image_id': identity}})
                    return result.task_id

            def delete():
                with app.app_context():
                    runtime = runtime_module.StoragePressureRuntime({}, db.session, models, root)
                    candidate = runtime_module.ImageCandidate(now-timedelta(days=5), model, identity)
                    try:
                        runtime.delete(candidate)
                    except RuntimeError as error:
                        assert 'generation was queued' in str(error), error
                        db.session.rollback()
                        return 'protected'
                    return 'deleted'

            with patch.object(guard, 'media_task_lock', observed_lock), \
                 patch.object(runtime_module, 'media_task_lock', observed_lock), \
                 ThreadPoolExecutor(max_workers=2) as pool:
                first = pool.submit(publish)
                try:
                    assert held.wait(5), 'Generation publication bypassed the media lock'
                    second = pool.submit(delete)
                    assert attempted.wait(5)
                    assert not second.done(), 'Cleanup bypassed pending publication'
                finally:
                    release.set()
                task_id = first.result(timeout=10)
                assert second.result(timeout=10) == 'protected'
            with app.app_context():
                assert path.is_file() and db.session.get(model, identity) is not None
                task = db.session.get(models.IndiAllSkyDbTaskQueueTable, task_id)
                task.setSuccess('isolated generation fixture completed')
        # Cleanup wins before mini publication: reject the now-missing anchor,
        # preserving the other source and creating no orphan generation task.
        from indi_allsky.flask import mini_generation
        admin = login_client(app, 1)
        headers = {'X-CSRFToken': csrf(admin, '/indi-allsky/modern-admin/account')}
        with app.app_context():
            count_before = models.IndiAllSkyDbTaskQueueTable.query.count()

        @contextmanager
        def cleanup_wins(*, exclusive):
            assert not exclusive
            runtime = runtime_module.StoragePressureRuntime({}, db.session, models, root)
            runtime.delete(runtime_module.ImageCandidate(now-timedelta(days=5), model, 1))
            with original_lock(exclusive=False):
                yield

        with patch.object(mini_generation, 'media_task_lock', cleanup_wins):
            response = admin.post('/indi-allsky/ajax/minigenerate', headers=headers, json={
                'CAMERA_ID': 1, 'IMAGE_ID': 1, 'PRE_SECONDS': 30,
                'POST_SECONDS': 30, 'FRAMERATE': 2, 'NOTE': 'disposable race fixture'})
        assert response.status_code == 404
        with app.app_context():
            assert models.IndiAllSkyDbTaskQueueTable.query.count() == count_before
            assert db.session.get(model, 1) is None
            assert db.session.get(model, 2) is not None
        assert not (root / 'generation-race-1.jpg').exists()
        assert (root / 'generation-race-2.jpg').is_file()
    print('Generation guard: all four actions protect source files during concurrent publication PASS')


if __name__ == '__main__':
    run()
