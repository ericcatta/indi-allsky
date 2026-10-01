#!/usr/bin/env python3
"""Real temporary files/SQLite: pressure cleanup scope, paging and protection."""
from datetime import datetime, timedelta
from pathlib import Path
from types import SimpleNamespace
import tempfile
from hybrid_runtime_fixture import isolated_app


def run():
    with isolated_app(multi_camera=True) as app, app.app_context():
        from indi_allsky.flask import db, models
        from indi_allsky.storage_pressure import GIB
        from indi_allsky.storage_pressure_runtime import StoragePressureRuntime, pending_storage_cleanup
        root = Path(app.config['INDI_ALLSKY_IMAGE_FOLDER'])
        now = datetime.now()
        table = models.IndiAllSkyDbImageTable
        def add(ident, days, present=True):
            path = root / ('pressure-%s.jpg' % ident)
            if present:
                path.write_bytes(b'dedicated disposable fixture')
            db.session.add(table(id=ident, camera_id=1 if ident % 2 else 2,
                                filename=str(path), createDate=now-timedelta(days=days),
                                dayDate=now.date(), night=False, exposure=1, gain=0,
                                adu=.1, width=1, height=1, data={}))
            return path
        # More missing entries than the old fixed prefix: do not starve real files.
        for ident in range(1, 2002):
            add(ident, 9, False)
        files = [add(ident, 5) for ident in range(2002, 2207)]
        recent = add(2207, 2)
        db.session.commit()
        runtime = StoragePressureRuntime({}, db.session, models, root,
                                         disk_usage=lambda path: SimpleNamespace(free=4*GIB))
        candidates = list(runtime.candidates(runtime.options.cutoff(now)))
        assert [c.identity for c in candidates] == list(range(2002, 2207))
        task = models.IndiAllSkyDbTaskQueueTable(queue=models.TaskQueueQueue.UPLOAD,
                    state=models.TaskQueueState.QUEUED,
                    data={'action':'upload', 'model':table.__name__, 'id':2002})
        db.session.add(task); db.session.commit()
        result = runtime.run(now)
        assert result['status'] == 'insufficient_old_images' and result['deleted'] == 204, result
        assert files[0].exists() and recent.exists()
        assert all(not path.exists() for path in files[1:])
        assert table.query.count() == 2003  # missing rows, protected upload, recent
        task.data = {'action':'generateVideo'}; db.session.commit()
        assert runtime.run(now)['status'] == 'generation_pending'

        assert files[0].exists()
        task.data = {'action':'storagePressureCleanup'}; db.session.commit()
        assert pending_storage_cleanup(runtime.pending_tasks())
        with runtime.lock():
            try:
                with runtime.lock():
                    raise AssertionError('second cleanup acquired the same lock')
            except BlockingIOError:
                pass
        entry = db.session.get(table, 2002)
        original = entry.filename
        entry.filename = str(root.parent / 'outside.jpg')
        try:
            runtime.path(entry)
        except ValueError:
            pass
        else:
            raise AssertionError('outside-root deletion allowed')
        entry.filename = original
        db.session.rollback()
        assert files[0].exists() and recent.exists()
        task.setSuccess('fixture task completed')
        dispatched = []
        queued = runtime.enqueue(dispatched.append)
        assert queued and dispatched == [queued]
        assert runtime.enqueue(dispatched.append) is None and len(dispatched) == 1
        queued.setSuccess('fixture cleanup completed')
        def fail_dispatch(task):
            raise RuntimeError('synthetic queue failure')
        try:
            runtime.enqueue(fail_dispatch)
        except RuntimeError:
            pass
        else:
            raise AssertionError('dispatch failure hidden')
        assert not pending_storage_cleanup(runtime.pending_tasks())
        disabled = StoragePressureRuntime({'STORAGE_PRESSURE': {'ENABLE': False}},
                        db.session, models, root, disk_usage=lambda path: SimpleNamespace(free=0))
        assert disabled.enqueue(dispatched.append) is None
        assert disabled.run(now)['status'] == 'not_needed'
        assert not runtime.recovering()
        runtime.set_recovering(True)
        midway = StoragePressureRuntime({}, db.session, models, root,
                                        disk_usage=lambda path: SimpleNamespace(free=6*GIB))
        assert midway.needs_work()  # reconstructing the worker retains recovery
        completed = StoragePressureRuntime({}, db.session, models, root,
                                           disk_usage=lambda path: SimpleNamespace(free=8*GIB))
        assert not completed.needs_work()
        assert completed.run(now)['status'] == 'not_needed'
        assert not midway.needs_work()
        runtime.set_recovering(True)
        changed = StoragePressureRuntime({'STORAGE_PRESSURE': {'KEEP_DAYS': 4}},
                    db.session, models, root, disk_usage=lambda path: SimpleNamespace(free=6*GIB))
        assert not changed.needs_work()
        thumb_path = root / 'pressure-thumbnail.jpg'
        thumb_path.write_bytes(b'disposable thumbnail fixture')
        thumbnail = models.IndiAllSkyDbThumbnailTable(uuid='pressure-fixture',
                        filename=str(thumb_path), camera_id=1, data={})
        db.session.add(thumbnail)
        entry = db.session.get(table, 2002)
        entry.thumbnail_uuid = thumbnail.uuid
        db.session.commit()
        task = models.IndiAllSkyDbTaskQueueTable(queue=models.TaskQueueQueue.UPLOAD,
                    state=models.TaskQueueState.MANUAL,
                    data={'action':'upload', 'model':type(thumbnail).__name__, 'id':thumbnail.id})
        db.session.add(task); db.session.commit()
        result = runtime.run(now)
        assert result['deleted'] == 0 and files[0].exists() and thumb_path.exists()
        task.data = {'action':'upload', 'local_file':str(thumb_path)}
        db.session.commit()
        assert runtime.run(now)['deleted'] == 0
        task.data = {'action':'generateVideo'}
        db.session.commit()
        assert runtime.run(now)['status'] == 'generation_pending'
        # Work published after the scan must still protect the selected file.
        task.setSuccess('fixture generation finished')
        candidate = next(runtime.candidates(runtime.options.cutoff(now)))
        for data in ({'action': 'generateVideo'},
                     {'action': 'upload', 'model': table.__name__, 'id': 2002},
                     {'action': 'upload', 'local_file': str(thumb_path)}):
            task.data = data
            task.state = models.TaskQueueState.QUEUED
            db.session.commit()
            try:
                runtime.delete(candidate)
            except RuntimeError:
                db.session.rollback()
            else:
                raise AssertionError('work queued after scan lost its source image')
            assert files[0].exists() and thumb_path.exists()
            assert db.session.get(table, 2002) is not None
            task.setSuccess('fixture protected work finished')

        # A thumbnail resolving outside the media root must stop deletion before
        # either part of the asset is removed, even after candidate selection.
        with tempfile.NamedTemporaryFile(prefix='hybrid-pressure-outside-',
                                         dir=root.parent, delete=False) as stream:
            stream.write(b'dedicated outside-root fixture')
            outside = Path(stream.name)
        original_thumbnail = thumbnail.filename
        link = root / 'pressure-thumbnail-link.jpg'
        link.symlink_to(outside)
        try:
            thumbnail.filename = str(link)
            db.session.commit()
            try:
                runtime.delete(candidate)
            except ValueError:
                db.session.rollback()
            else:
                raise AssertionError('outside-root thumbnail deletion allowed')
            assert outside.read_bytes() == b'dedicated outside-root fixture'
            assert files[0].exists() and thumb_path.exists() and link.is_symlink()
            assert db.session.get(table, 2002) is not None
        finally:
            thumbnail.filename = original_thumbnail
            db.session.commit()
            link.unlink(missing_ok=True)
            outside.unlink(missing_ok=True)

    print('Storage cleanup: real files, two cameras, missing-prefix paging, commit paging, upload/generation protection, lock and path boundary PASS')


if __name__ == '__main__':
    run()
