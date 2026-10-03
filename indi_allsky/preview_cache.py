"""Bounded, disposable display-byte cache. Scientific assets never live here."""
from contextlib import contextmanager, ExitStack
import fcntl
import hashlib
import logging
import os
from pathlib import Path
import re
import tempfile
import time

logger = logging.getLogger('indi_allsky')
_ENTRY = re.compile(r'[0-9a-f]{64}\.cache\Z')


class PreviewCache:
    def __init__(self, root, *, max_bytes=512 * 1024 * 1024, max_entries=1024):
        self.root = Path(root).resolve()
        self.max_bytes = int(max_bytes)
        self.max_entries = int(max_entries)
        if self.max_bytes < 0 or self.max_entries < 0:
            raise ValueError('Preview cache limits cannot be negative')

    @contextmanager
    def _lock(self, name):
        fd = os.open(self.root / name, os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW, 0o600)
        try:
            fcntl.flock(fd, fcntl.LOCK_EX)
            yield
        finally:
            os.close(fd)

    def _read(self, path):
        with self._lock('index.lock'):
            if path.is_symlink():
                path.unlink()
                return None
            try:
                if path.stat().st_size > self.max_bytes:
                    path.unlink()
                    return None
                data = path.read_bytes()
            except FileNotFoundError:
                return None
            digest, separator, payload = data.partition(b'\n')
            if separator != b'\n' or digest != hashlib.sha256(payload).hexdigest().encode():
                path.unlink()
                return None
            os.utime(path, None)  # LRU access time; never the exposure timestamp.
            self._prune()
            return payload

    def _prune(self):
        """Caller holds index.lock. Never traverse source/asset directories."""
        entries = []
        now = time.time()
        for path in self.root.iterdir():
            if path.is_symlink():
                continue
            if _ENTRY.fullmatch(path.name) and path.is_file():
                st = path.stat()
                entries.append((st.st_mtime_ns, path.name, path, st.st_size))
            elif path.name.endswith('.part') and path.is_file():
                if now - path.stat().st_mtime > 3600:
                    path.unlink(missing_ok=True)
        total = sum(item[3] for item in entries)
        count = len(entries)
        for _, _, path, size in sorted(entries):
            if total <= self.max_bytes and count <= self.max_entries:
                break
            path.unlink(missing_ok=True)
            total -= size
            count -= 1

    def _publish(self, path, data):
        if len(data) + 65 > self.max_bytes:
            return  # A large result remains usable without exceeding the cache.
        pending = None
        try:
            with tempfile.NamedTemporaryFile(dir=self.root, suffix='.part', delete=False) as out:
                pending = Path(out.name)
                out.write(hashlib.sha256(data).hexdigest().encode() + b'\n' + data)
                out.flush()
                os.fsync(out.fileno())
            with self._lock('index.lock'):
                os.replace(pending, path)
                self._prune()
        finally:
            if pending is not None:
                pending.unlink(missing_ok=True)

    def _uncached(self, producer):
        # Disabling persistence must not disable the memory/concurrency bound.
        self.root.mkdir(parents=True, exist_ok=True, mode=0o700)
        with self._lock('reconstruction.lock'):
            return producer()

    def get_or_create(self, key, producer):
        if not isinstance(key, str) or re.fullmatch(r'[0-9a-f]{64}', key) is None:
            raise ValueError('Invalid preview cache key')
        if not self.max_bytes or not self.max_entries:
            return self._uncached(producer)
        with ExitStack() as locks:
            try:
                self.root.mkdir(parents=True, exist_ok=True, mode=0o700)
            except OSError:
                logger.warning('Preview cache unavailable; trying uncached rendering')
                return self._uncached(producer)
            path = self.root / (key + '.cache')
            try:
                data = self._read(path)
            except OSError:
                data = None
            if data is not None:
                return data
            try:
                # Fixed lock stripes prevent millions of lingering per-frame locks.
                locks.enter_context(self._lock('render-%02d.lock' % (int(key[:2], 16) % 64)))
            except OSError:
                logger.warning('Preview cache lock unavailable; trying uncached rendering')
                return self._uncached(producer)
            # A previous requester may have populated this key while we waited.
            try:
                data = self._read(path)
            except OSError:
                data = None
            if data is not None:
                return data
            # Cold full-resolution rendering has a large memory footprint. Keep
            # one reconstruction in flight per cache across all worker processes;
            # already cached reads never wait for this resource slot.
            locks.enter_context(self._lock('reconstruction.lock'))
            # Renderer errors propagate; a failed reconstruction is never cached.
            data = producer()
            if not isinstance(data, bytes):
                raise TypeError('Preview producer must return bytes')
            try:
                self._publish(path, data)
            except OSError:
                logger.warning('Preview cache write failed; serving reconstructed image')
            return data

    def clear(self):
        if not self.root.is_dir():
            return
        with self._lock('index.lock'):
            for path in self.root.iterdir():
                if _ENTRY.fullmatch(path.name):
                    path.unlink(missing_ok=True)
