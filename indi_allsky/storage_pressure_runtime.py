"""Storage-pressure task planning and local image effects shared by workers."""
from contextlib import contextmanager
from dataclasses import asdict, dataclass
from datetime import datetime
import fcntl
import heapq
import json
import tempfile
import os
from pathlib import Path
import shutil

from .media_task_guard import media_task_lock
from .storage_pressure import GIB, StoragePressureOptions, reclaim_old_images

IMAGE_FAMILIES = ('Image', 'FitsImage', 'RawImage', 'PanoramaImage')
GENERATION_ACTIONS = frozenset(('generateVideo', 'generateMiniVideo',
                              'generateKeogramStarTrails', 'generatePanoramaVideo'))
ACTION = 'storagePressureCleanup'


def pending_storage_cleanup(tasks):
    return any((task.data or {}).get('action') == ACTION for task in tasks)


@dataclass(frozen=True)
class ImageCandidate:
    created: datetime
    table: object
    identity: int


class StoragePressureRuntime:
    def __init__(self, config, session, models, image_root, *, disk_usage=shutil.disk_usage):
        self.options = StoragePressureOptions.from_config(config)
        self.session = session
        self.models = models
        self.root = Path(image_root).resolve()
        self.disk_usage = disk_usage
        self.tables = [getattr(models, 'IndiAllSkyDb' + name + 'Table') for name in IMAGE_FAMILIES]

    def free_bytes(self):
        return self.disk_usage(self.root).free

    def pending_tasks(self):
        m = self.models
        return m.IndiAllSkyDbTaskQueueTable.query.filter(
            m.IndiAllSkyDbTaskQueueTable.state.in_((m.TaskQueueState.MANUAL, m.TaskQueueState.QUEUED, m.TaskQueueState.RUNNING)),
        ).all()

    def path(self, entry):
        path = entry.getFilesystemPath()
        resolved = path.resolve()
        if not resolved.is_relative_to(self.root) or resolved == self.root:
            raise ValueError('Storage cleanup found an image outside its configured directory.')
        return path

    def protected(self, entry, pending):
        if not pending:
            return False
        assets = [entry]
        # deleteAsset also deletes the thumbnail. A pending thumbnail upload
        # therefore protects its parent even if no task names the parent image.
        if entry.thumbnail_uuid:
            thumbnail = self.models.IndiAllSkyDbThumbnailTable.query.filter_by(
                uuid=entry.thumbnail_uuid).first()
            if thumbnail is not None:
                assets.append(thumbnail)
        for task in pending:
            data = task.data or {}
            for asset in assets:
                if data.get('model') == type(asset).__name__ and data.get('id') == asset.id:
                    return True
                local = data.get('local_file')
                if local and Path(local).resolve() == self.path(asset).resolve():
                    return True
        return False

    def candidates(self, cutoff):
        # Streaming each family avoids starving eligible files behind an arbitrary
        # prefix of missing/remote files. Merge before deletion across all cameras.
        pending = self.pending_tasks()
        device = self.root.stat().st_dev

        def family(table):
            after = None
            while True:
                query = table.query.filter(table.createDate < cutoff)
                if after is not None:
                    created, identity = after
                    query = query.filter((table.createDate > created) |
                                         ((table.createDate == created) & (table.id > identity)))
                # Materialize one page before effects commit. No open DB cursor
                # crosses a deletion and keyset paging cannot skip shifted rows.
                rows = query.order_by(table.createDate, table.id).limit(200).all()
                if not rows:
                    return
                after = (rows[-1].createDate, rows[-1].id)
                for entry in rows:
                    path = self.path(entry)
                    try:
                        eligible = path.is_file() and path.stat().st_dev == device
                    except FileNotFoundError:
                        continue
                    if eligible and not self.protected(entry, pending):
                        yield ImageCandidate(entry.createDate, table, entry.id)

        return heapq.merge(*(family(table) for table in self.tables),
                           key=lambda item: (item.created, item.table.__name__, item.identity))

    def delete(self, candidate):
        with media_task_lock(exclusive=True):
            # End the candidate scan snapshot before checking newly published tasks.
            self.session.commit()
            entry = self.session.get(candidate.table, candidate.identity, populate_existing=True)
            if entry is None:
                raise RuntimeError('An image changed during storage cleanup; retry on the next check.')
            pending = self.pending_tasks()
            if any((task.data or {}).get('action') in GENERATION_ACTIONS for task in pending):
                raise RuntimeError('A generation was queued during storage cleanup; retry later.')
            if self.protected(entry, pending):
                raise RuntimeError('An image was queued for transfer during storage cleanup; retry later.')
            path = self.path(entry)
            if entry.thumbnail_uuid:
                thumbnail = self.models.IndiAllSkyDbThumbnailTable.query.filter_by(uuid=entry.thumbnail_uuid).first()
                if thumbnail:
                    self.path(thumbnail)
            entry.deleteAsset()
            self.session.delete(entry)
            self.session.commit()

    @contextmanager
    def lock(self):
        fd = os.open(self.root / '.hybrid-storage-cleanup.lock',
                     os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            yield
        finally:
            os.close(fd)

    def recovering(self):
        try:
            state = json.loads((self.root / '.hybrid-storage-recovery.json').read_text())
        except (FileNotFoundError, ValueError):
            return False
        return state == asdict(self.options)

    def set_recovering(self, active):
        path = self.root / '.hybrid-storage-recovery.json'
        if not active:
            path.unlink(missing_ok=True)
            return
        # Atomic, private state: retain the target across bounded jobs/restarts.
        fd, temporary = tempfile.mkstemp(prefix='.hybrid-storage-', dir=self.root)
        try:
            with os.fdopen(fd, 'w') as stream:
                json.dump(asdict(self.options), stream)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, path)
        finally:
            Path(temporary).unlink(missing_ok=True)

    def needs_work(self):
        free = self.free_bytes()
        return self.options.needs_cleanup(free) or (self.options.enabled and
            self.recovering() and free < self.options.target_free_gib * GIB)

    def enqueue(self, dispatch):
        """One pending task at a time, serialized across scheduling attempts."""
        with self.lock():
            if not self.needs_work():
                self.set_recovering(False)
                return None
            if pending_storage_cleanup(self.pending_tasks()):
                return None
            task = self.models.IndiAllSkyDbTaskQueueTable(
                queue=self.models.TaskQueueQueue.VIDEO,
                state=self.models.TaskQueueState.QUEUED,
                data={'action': ACTION, 'kwargs': {}},
            )
            self.session.add(task)
            self.session.commit()
            try:
                dispatch(task)
            except Exception:
                self.session.rollback()
                task.setFailed('Storage cleanup could not be dispatched; retry on next check.')
                raise
            return task

    def run(self, now=None):
        with self.lock():
            if not self.needs_work():
                self.set_recovering(False)
                return {'status': 'not_needed', 'deleted': 0, 'free_bytes': self.free_bytes()}
            self.set_recovering(True)
            if any((task.data or {}).get('action') in GENERATION_ACTIONS for task in self.pending_tasks()):
                return {'status': 'generation_pending', 'deleted': 0, 'free_bytes': self.free_bytes()}
            result = reclaim_old_images(options=self.options, now=now or datetime.now(),
                                        free_bytes=self.free_bytes, candidates=self.candidates,
                                        delete=self.delete, continuing=True)
            if result['status'] in ('recovered', 'not_needed'):
                self.set_recovering(False)
            return result
