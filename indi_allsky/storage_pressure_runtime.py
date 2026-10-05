"""Storage-pressure task planning and local image effects shared by workers."""
from contextlib import contextmanager
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
import fcntl
import heapq
import json
import tempfile
import os
from pathlib import Path
import shutil
import sqlite3
import time

from sqlalchemy.exc import OperationalError

from .media_task_guard import GENERATION_ACTIONS, media_task_lock
from .storage_pressure import GIB, StoragePressureOptions, reclaim_old_images
from .source_retention import image_source, source_dependents

IMAGE_FAMILIES = ('Image', 'FitsImage', 'RawImage', 'PanoramaImage')
GENERATED_FAMILIES = ('Video', 'MiniVideo', 'Keogram', 'StarTrails', 'StarTrailsVideo', 'PanoramaVideo')
ACTION = 'storagePressureCleanup'


def pending_storage_cleanup(tasks):
    return any((task.data or {}).get('action') == ACTION for task in tasks)


@dataclass(frozen=True)
class ImageCandidate:
    created: datetime
    table: object
    identity: int
    priority: int = 0
    expires_before: object = None


class StoragePressureRuntime:
    def __init__(self, config, session, models, image_root, *, disk_usage=shutil.disk_usage):
        self.options = StoragePressureOptions.from_config(config)
        self.volume_spec = config.get('ARCHIVE_VOLUME')
        self.session = session
        self.models = models
        self.root = Path(image_root).resolve()
        self.disk_usage = disk_usage
        self.tables = [getattr(models, 'IndiAllSkyDb' + name + 'Table') for name in IMAGE_FAMILIES]
        self.generated_tables = [getattr(models, 'IndiAllSkyDb' + name + 'Table') for name in GENERATED_FAMILIES]
        days = config.get('TIMELAPSE_EXPIRE_DAYS', 365)
        if isinstance(days, bool) or not isinstance(days, int) or days < 1:
            raise ValueError('Timelapse retention must be a positive number of days.')
        self.generated_keep_days = max(5, days)

    def free_bytes(self):
        from .archive_volume import verify_archive
        verify_archive(self.root, self.volume_spec, writable=True)
        return self.disk_usage(self.root).free

    def pending_tasks(self):
        m = self.models
        return m.IndiAllSkyDbTaskQueueTable.query.filter(
            m.IndiAllSkyDbTaskQueueTable.state.in_((m.TaskQueueState.MANUAL, m.TaskQueueState.QUEUED, m.TaskQueueState.RUNNING)),
        ).all()

    def path(self, entry):
        from .archive_volume import verify_archive
        verify_archive(self.root, self.volume_spec, writable=True)
        path = entry.getFilesystemPath()
        resolved = path.resolve()
        if not resolved.is_relative_to(self.root) or resolved == self.root:
            raise ValueError('Storage cleanup found an image outside its configured directory.')
        return path

    def protected(self, entry, pending):
        if not pending:
            return False
        assets = [entry]
        source = image_source(entry, self.session, self.models)
        if source is not None:
            assets.append(source)
        # deleteAsset also deletes the thumbnail. A pending thumbnail upload
        # therefore protects its parent even if no task names the parent image.
        for parent in list(assets):
            if parent.thumbnail_uuid:
                thumbnail = self.models.IndiAllSkyDbThumbnailTable.query.filter_by(
                    uuid=parent.thumbnail_uuid).first()
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

        emitted = set()

        def family(table, night, expires, priority):
            after = None
            while True:
                query = table.query.filter(table.createDate < expires, table.night == night)
                if after is not None:
                    created, identity = after
                    query = query.filter((table.createDate > created) |
                                         ((table.createDate == created) & (table.id > identity)))
                # Materialize one page before effects commit. No open DB cursor
                # crosses a deletion and keyset paging cannot skip shifted rows.
                rows = query.with_entities(table.createDate, table.id).order_by(table.createDate, table.id).limit(200).all()
                if not rows:
                    return
                after = tuple(rows[-1])
                for created, identity in rows:
                    entry = self.session.get(table, identity, populate_existing=True)
                    if entry is None:
                        continue
                    if source_dependents(entry, self.session, self.models):
                        continue
                    source = image_source(entry, self.session, self.models)
                    path = self.path(source if source is not None else entry)
                    try:
                        eligible = path.is_file() and path.stat().st_dev == device
                    except FileNotFoundError:
                        continue
                    if eligible and not self.protected(entry, pending):
                        yield ImageCandidate(entry.createDate, table, entry.id, priority, expires)

        now = cutoff + timedelta(days=self.options.keep_days)
        generated_cutoff = now - timedelta(days=self.generated_keep_days)
        groups = ((self.tables, False, cutoff), (self.tables, True, cutoff),
                  (self.generated_tables, False, generated_cutoff),
                  (self.generated_tables, True, generated_cutoff))
        for priority, (tables, night, expires) in enumerate(groups):
            merged = heapq.merge(*(family(table, night, expires, priority) for table in tables),
                                key=lambda item: (item.created, item.table.__name__, item.identity))
            for candidate in merged:
                identity = (candidate.table, candidate.identity)
                if identity in emitted:
                    continue
                entry = self.session.get(candidate.table, candidate.identity)
                source = image_source(entry, self.session, self.models) if entry is not None else None
                source_id = source.id if source is not None else None
                emitted.add(identity)
                yield candidate
                # Reclaim the now-unreferenced FITS at the same priority/age,
                # before considering any night image or generated output.
                if source_id is not None:
                    table = self.models.IndiAllSkyDbFitsImageTable
                    source = self.session.get(table, source_id, populate_existing=True)
                    identity = (table, source_id)
                    if (source is not None and identity not in emitted and
                            not source_dependents(source, self.session, self.models) and
                            not self.protected(source, self.pending_tasks())):
                        path = self.path(source)
                        if path.is_file() and path.stat().st_dev == device:
                            emitted.add(identity)
                            yield ImageCandidate(source.createDate, table, source.id, priority, expires)

    def delete(self, candidate):
        # Model deletion tolerates files already removed (including thumbnails).
        # Retain this exact candidate when a commit collides with a writer: a
        # fresh scan could omit it once its file has gone but its row remains.
        for attempt in range(3):
            try:
                return self._delete_once(candidate)
            except OperationalError as exc:
                self.session.rollback()
                code = getattr(exc.orig, 'sqlite_errorcode', None)
                if (not isinstance(exc.orig, sqlite3.Error) or code is None or
                        (code & 0xff) not in (sqlite3.SQLITE_BUSY, sqlite3.SQLITE_LOCKED) or
                        attempt == 2):
                    raise
                # Release the media lock before yielding to the active writer.
                # Every retry reloads the record and pending work protections.
                time.sleep(0.1 * (attempt + 1))

    def _delete_once(self, candidate):
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
            if source_dependents(entry, self.session, self.models):
                raise RuntimeError('The FITS source is still required by an archived image.')
            source = image_source(entry, self.session, self.models)
            if source is not None:
                self.path(source)
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
        from .archive_volume import verify_archive
        verify_archive(self.root, self.volume_spec, writable=True)
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
            from .render_asset_lifecycle import collect_assets, archive_references
            collected = collect_assets(self.root / '.render-assets',
                lambda: archive_references(self.session, self.models))
            result = reclaim_old_images(options=self.options, now=now or datetime.now(),
                                        free_bytes=self.free_bytes, candidates=self.candidates,
                                        delete=self.delete, continuing=True)
            if result['status'] in ('recovered', 'not_needed'):
                self.set_recovering(False)
            if collected['deleted']:
                result['render_assets_deleted'] = collected['deleted']
                result['render_assets_bytes'] = collected['bytes']
            return result
