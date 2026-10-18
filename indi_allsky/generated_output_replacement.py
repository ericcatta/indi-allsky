"""Safe lifecycle for replacing generated media outputs."""
import logging
from pathlib import Path

from .media_task_guard import media_task_lock


logger = logging.getLogger('indi_allsky')


class PendingGeneratedOutputTransfer(RuntimeError):
    pass


class GeneratedOutputReplacement:
    """Keep old generated outputs until complete candidates can replace them."""

    def __init__(self, session, task_model, thumbnail_model, queue_enum, state_enum, root):
        self.session = session
        self.task_model = task_model
        self.thumbnail_model = thumbnail_model
        self.queue_enum = queue_enum
        self.state_enum = state_enum
        self.root = Path(root)
        self.existing = {}
        self.candidates = {}
        self.ready = set()
        self.preserved = set()
        self.finalized = False

    def set_existing(self, kind, entry):
        self.existing[kind] = entry

    def register(self, kind, entry):
        self.candidates[kind] = entry

    def mark_ready(self, kind):
        self.ready.add(kind)

    def _active_transfer_for(self, entry):
        if entry is None:
            return False
        tasks = self.session.query(self.task_model).filter(
            self.task_model.queue == self.queue_enum.UPLOAD,
            self.task_model.state.in_((self.state_enum.QUEUED, self.state_enum.RUNNING)),
        ).all()
        identities = {(type(entry).__name__, entry.id)}
        if entry.thumbnail_uuid:
            thumbnail = self.session.query(self.thumbnail_model).filter(
                self.thumbnail_model.uuid == entry.thumbnail_uuid).one_or_none()
            if thumbnail is not None:
                identities.add((type(thumbnail).__name__, thumbnail.id))
        return any(
            isinstance(task.data, dict)
            and (task.data.get('model'), task.data.get('id')) in identities
            for task in tasks
        )

    def ensure_replaceable(self):
        for kind, entry in self.existing.items():
            if self._active_transfer_for(entry):
                raise PendingGeneratedOutputTransfer(
                    '{0} has a pending transfer; retry after it completes'.format(kind))

    def _entry_assets(self, entry):
        assets = []
        try:
            assets.append(Path(entry.getFilesystemPath()))
        except (OSError, ValueError):
            logger.exception('Unable to resolve generated output path for cleanup')
        thumbnail = None
        if entry.thumbnail_uuid:
            thumbnail = self.session.query(self.thumbnail_model).filter(
                self.thumbnail_model.uuid == entry.thumbnail_uuid).one_or_none()
            if thumbnail is not None:
                try:
                    assets.append(Path(thumbnail.getFilesystemPath()))
                except (OSError, ValueError):
                    logger.exception('Unable to resolve generated thumbnail path for cleanup')
        return thumbnail, assets

    def _stage_delete(self, entry, assets):
        thumbnail, entry_assets = self._entry_assets(entry)
        if thumbnail is not None:
            self.session.delete(thumbnail)
        self.session.delete(entry)
        assets.extend(entry_assets)

    @staticmethod
    def is_candidate(entry):
        return bool((entry.data or {}).get('_replacement_candidate'))

    @staticmethod
    def _clear_candidate_marker(entry):
        data = dict(entry.data or {})
        data.pop('_replacement_candidate', None)
        entry.data = data

    def _commit(self):
        self.session.commit()

    @staticmethod
    def _unlink_assets(assets):
        for path in assets:
            try:
                path.unlink()
            except FileNotFoundError:
                pass
            except OSError:
                # The replacement is already durable. A stale old file is safer
                # than invalidating the new record after the database commit.
                logger.exception('Unable to remove superseded generated asset: %s', path)

    def finalize(self):
        """Publish ready candidates and preserve old outputs for skipped kinds."""
        assets = []
        with media_task_lock(exclusive=True, root=self.root):
            self.ensure_replaceable()
            try:
                for kind, old_entry in self.existing.items():
                    candidate = self.candidates.get(kind)
                    if kind in self.ready:
                        if old_entry is not None:
                            self._stage_delete(old_entry, assets)
                        if candidate is not None:
                            self._clear_candidate_marker(candidate)
                    elif old_entry is not None:
                        if candidate is not None:
                            self._stage_delete(candidate, assets)
                        self.preserved.add(kind)
                    elif candidate is not None:
                        # Keep the historical unsuccessful row when there was no
                        # previous output to preserve.
                        self._clear_candidate_marker(candidate)
                self._commit()
            except Exception:
                self.session.rollback()
                raise
        self.finalized = True
        self._unlink_assets(assets)

    def discard_abandoned(self, entries):
        """Remove only marked candidates left by an interrupted prior attempt."""
        abandoned = [entry for entry in entries if self.is_candidate(entry)]
        if not abandoned:
            return
        assets = []
        with media_task_lock(exclusive=True, root=self.root):
            try:
                for entry in abandoned:
                    if self._active_transfer_for(entry):
                        raise PendingGeneratedOutputTransfer(
                            'Interrupted candidate has a pending transfer; retry after it completes')
                    self._stage_delete(entry, assets)
                self._commit()
            except Exception:
                self.session.rollback()
                raise
        self._unlink_assets(assets)

    def result_entry(self, kind):
        if kind in self.preserved:
            return self.existing[kind]
        return self.candidates.get(kind)

    def result_path(self, kind, candidate_path):
        if kind in self.preserved:
            return Path(self.existing[kind].getFilesystemPath())
        return candidate_path

    def abort(self):
        """Remove unpublished candidates after a failed render or DB publish."""
        if self.finalized or not self.candidates:
            return
        assets = []
        self.session.rollback()
        try:
            for entry in self.candidates.values():
                if entry is not None:
                    loaded = self.session.get(type(entry), entry.id)
                    if loaded is not None:
                        self._stage_delete(loaded, assets)
            self._commit()
        except Exception:
            self.session.rollback()
            logger.exception('Unable to remove failed generated output candidates')
            return
        self._unlink_assets(assets)

