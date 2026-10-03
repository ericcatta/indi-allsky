"""Reference-based collection and accounting for scientific rendering assets."""
from contextlib import contextmanager
import fcntl
import os
from pathlib import Path
import re
import time
from functools import wraps

IDENTITY = re.compile(r'[0-9a-f]{64}\Z')
ASSET = re.compile(r'([0-9a-f]{64})\.(npz|font)\Z')
PARTIAL = re.compile(r'\.hybrid-asset-[a-z0-9_]+\.part\Z')


def asset_store_lease(method):
    @wraps(method)
    def leased(store, *args, **kwargs):
        with archive_asset_lock(store.root):
            return method(store, *args, **kwargs)
    return leased


def source_render_lease(function):
    @wraps(function)
    def leased(path, recipe, assets, **kwargs):
        with archive_asset_lock(assets.root):
            return function(path, recipe, assets, **kwargs)
    return leased


@contextmanager
def archive_asset_lock(root, *, exclusive=False):
    """Writers/readers lease the archive; collection never waits for them."""
    root = Path(root)
    existed = root.exists()
    root.mkdir(parents=True, exist_ok=True)
    if not existed:
        directory = os.open(root.parent, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)
    fd = os.open(root / '.lifecycle.lock', os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW, 0o600)
    try:
        fcntl.flock(fd, (fcntl.LOCK_EX | fcntl.LOCK_NB) if exclusive else fcntl.LOCK_SH)
        yield
    finally:
        os.close(fd)


def referenced_assets(value):
    """Conservative traversal also understands saved labels/presentation recipes."""
    if isinstance(value, str):
        if IDENTITY.fullmatch(value):
            yield value
    elif isinstance(value, dict):
        for child in value.values():
            yield from referenced_assets(child)
    elif isinstance(value, (list, tuple)):
        for child in value:
            yield from referenced_assets(child)


def asset_usage(root, *, since=None):
    total = recent = 0
    root = Path(root)
    if root.is_symlink():
        raise ValueError('Archive asset directory cannot be a symlink')
    if not root.exists():
        return total, recent
    for path in root.iterdir():
        if path.is_symlink() or not ASSET.fullmatch(path.name) or not path.is_file():
            continue
        try:
            stat = path.stat()
        except FileNotFoundError:
            continue
        total += stat.st_size
        if since is not None and stat.st_mtime > since:
            recent += stat.st_size
    return total, recent


def collect_assets(root, references, *, now=None, grace_seconds=86400, limit=500):
    """Only remove old managed files after a complete successful reference scan."""
    root = Path(root)
    if root.is_symlink():
        raise ValueError('Archive asset directory cannot be a symlink')
    if not root.exists():
        return {'status':'not_needed', 'deleted':0, 'bytes':0}
    if grace_seconds < 0 or limit < 1:
        raise ValueError('Invalid asset collection limits')
    cutoff = (time.time() if now is None else now) - grace_seconds
    try:
        with archive_asset_lock(root, exclusive=True):
            live = set(references())  # Finish before the first irreversible effect.
            deleted = size = 0
            for path in sorted(root.iterdir()):
                match = ASSET.fullmatch(path.name)
                if ((not match and not PARTIAL.fullmatch(path.name))
                        or (match and match[1] in live) or path.is_symlink() or not path.is_file()):
                    continue
                stat = path.stat()
                if stat.st_mtime >= cutoff:
                    continue
                path.unlink()
                deleted += 1
                size += stat.st_size
                if deleted >= limit:
                    break
            if deleted:
                fd = os.open(root, os.O_RDONLY | os.O_DIRECTORY)
                try:
                    os.fsync(fd)
                finally:
                    os.close(fd)
            return {'status':'collected', 'deleted':deleted, 'bytes':size}
    except BlockingIOError:
        return {'status':'busy', 'deleted':0, 'bytes':0}


def archive_references(session, models):
    """Keyset pages bound memory and include both scientific and display records."""
    from .source_publication import read_source_recipe
    for table in (models.IndiAllSkyDbImageTable, models.IndiAllSkyDbFitsImageTable):
        after = 0
        while True:
            rows = session.query(table).filter(table.id > after).order_by(table.id).limit(100).all()
            if not rows:
                break
            after = rows[-1].id
            for row in rows:
                yield from referenced_assets(row.data)
                if table is models.IndiAllSkyDbFitsImageTable and not (row.data or {}).get('render_source'):
                    path = row.getFilesystemPath()
                    if path.is_file():
                        yield from referenced_assets(read_source_recipe(path))
