"""Serialize upload/generation task publication with storage-pressure deletion.

The lock covers database publication only, never network transfer. Multiple
producers may publish concurrently; deletion takes an exclusive lock per image.
"""
from contextlib import contextmanager
import fcntl
import os
from pathlib import Path

GENERATION_ACTIONS = frozenset(('generateVideo', 'generateMiniVideo',
                              'generateKeogramStarTrails', 'generatePanoramaVideo'))

PROTECTED_MODELS = frozenset('IndiAllSkyDb' + family + 'Table' for family in
                            ('Image', 'FitsImage', 'RawImage', 'PanoramaImage', 'Thumbnail'))


@contextmanager
def media_task_lock(*, exclusive, root=None):
    if root is None:
        from flask import current_app
        root = current_app.config['INDI_ALLSKY_IMAGE_FOLDER']
    path = Path(root).resolve() / '.hybrid-media-task.lock'
    fd = os.open(path, os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX if exclusive else fcntl.LOCK_SH)
        yield
    finally:
        os.close(fd)


def persist_upload_task(task):
    """Publish only while the referenced asset cannot be reclaimed.

    If deletion won the race, reject a stale asset reference instead of creating
    an orphan upload task. Existing task shapes and commit semantics are kept.
    """
    from flask import current_app
    from .flask import db, models
    data = task.data or {}
    model_name = data.get('model')
    local = data.get('local_file')
    root = Path(current_app.config['INDI_ALLSKY_IMAGE_FOLDER']).resolve()
    local_path = Path(local).resolve() if local else None
    guarded = model_name in PROTECTED_MODELS or (local_path and local_path.is_relative_to(root))
    if not guarded:
        db.session.add(task)
        db.session.commit()
        return
    with media_task_lock(exclusive=False, root=root):
        if model_name in PROTECTED_MODELS:
            table = getattr(models, model_name)
            with db.session.no_autoflush:
                identity = db.session.query(table.id).filter(table.id == data.get('id')).with_for_update().scalar()
            if identity is None:
                raise FileNotFoundError('Media was removed before the upload could be queued.')
        elif not local_path.is_file():
            raise FileNotFoundError('Media file was removed before the upload could be queued.')
        db.session.add(task)
        db.session.commit()


def persist_generation_tasks(session, tasks, *, lock_factory=None):
    """Publish generation tasks atomically with respect to pressure cleanup.

    Acquire before adding rows: autoflush must not publish them before the lock.
    The existing task ordering and one-commit semantics are preserved.
    """
    with (lock_factory or media_task_lock)(exclusive=False):
        for task in tasks:
            session.add(task)
        session.commit()
