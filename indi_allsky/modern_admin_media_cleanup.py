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
