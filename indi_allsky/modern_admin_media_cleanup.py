"""Hybrid policy for bounded progress through existing scoped media queries."""


class MediaCleanupIncomplete(Exception):
    def __init__(self, deleted_count, failed_count):
        self.deleted_count = deleted_count
        self.failed_count = failed_count
        super().__init__(
            f'Cleanup stopped after deleting {deleted_count} files; '
            f'{failed_count} files in the current batch could not be deleted. '
            'Check file permissions and logs before retrying.'
        )


def flush_media_batches(asset_lists, delete_batch):
    """Keep existing query order/effects; never retry a failed batch forever."""
    deleted_count = 0
    for query, table in asset_lists:
        while True:
            ids = [entry.id for entry in query.limit(500)]
            if not ids:
                break
            count = delete_batch(table, ids)
            deleted_count += count
            if count != len(ids):
                raise MediaCleanupIncomplete(deleted_count, len(ids) - count)
    return deleted_count


def prune_empty_camera_directories(image_root, camera_uuid):
    """Prune only this camera tree, bottom-up, without following symlinks."""
    import os
    from pathlib import Path
    identity = str(camera_uuid)
    if not identity or Path(identity).name != identity:
        raise ValueError('Invalid camera folder identity')
    root = Path(image_root) / ('ccd_' + identity)
    if root.is_symlink() or not root.exists():
        return 0
    errors = []
    for folder, _, _ in os.walk(root, topdown=False, followlinks=False, onerror=errors.append):
        path = Path(folder)
        if path.is_symlink():
            continue
        try:
            if not any(path.iterdir()):
                path.rmdir()
        except OSError as error:
            errors.append(error)
    return len(errors)
