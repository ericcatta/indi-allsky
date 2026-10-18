"""Persist an already-published FITS without replaying filesystem effects."""
from .sqlite_transactions import insert_with_retry, retry_sqlite_transaction


def register_fits(session, model, values):
    return insert_with_retry(session, model, values)


def update_fits_metadata(session, model, entry_id, file_size, recipe):
    def write():
        # Rollback expires the previous instance. Reload and merge on every
        # attempt so unrelated metadata committed by another writer survives.
        entry = session.get(model, entry_id)
        if entry is None:
            raise LookupError('FITS entry no longer exists: {0}'.format(entry_id))
        entry.fileSize = file_size
        entry.data = dict(entry.data or {}, render_source=recipe)
        return entry
    return retry_sqlite_transaction(session, write)
