import os
import re
import logging
import atexit
import threading
from collections import deque
from datetime import datetime
from pathlib import Path


logger = logging.getLogger('indi_allsky')


DIAG_PATHS = (
    Path('/tmp/indi-allsky-multicamera-diag.log'),
    Path('/var/lib/indi-allsky/multicamera-diag.log'),
)

PROFILE_RE = re.compile(r'\[MULTI_CAMERA_[^\]]+\]\[([^\]]+)\]')
CAMERA_RE = re.compile(r'\[camera_id=([^\]]+)\]')
MAX_PENDING_RECORDS = 256
MAX_RECORD_CHARS = 16384


def _format_line(message):
    timestamp = datetime.now().isoformat(timespec='seconds')
    profile_match = PROFILE_RE.search(message)
    camera_match = CAMERA_RE.search(message)
    profile_id = profile_match.group(1) if profile_match else 'unknown'
    camera_id = camera_match.group(1) if camera_match else 'unknown'
    return (
        '{timestamp} pid={pid} profile_id={profile_id} camera_id={camera_id} event={event}\n'
    ).format(
        timestamp=timestamp,
        pid=os.getpid(),
        profile_id=profile_id,
        camera_id=camera_id,
        event=message,
    )

def _write_record(message, line):
    # Even logging handlers can wait on I/O: only the writer thread runs them.
    try:
        logger.debug(message)
    except Exception:
        pass
    for path in DIAG_PATHS:
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open('a', buffering=1, encoding='utf-8') as diag_f:
                diag_f.write(line)
        except Exception:
            # Diagnostics must never interfere with capture.
            continue


class _DiagnosticWriter:
    """Best-effort FIFO: no file or logging I/O on the capture thread."""

    def __init__(self, sink=_write_record, capacity=MAX_PENDING_RECORDS):
        self._sink = sink
        self._capacity = capacity
        self._records = deque()
        self._condition = threading.Condition()
        self._active = False
        self._stopping = False
        self._dropped = 0
        self._thread = threading.Thread(target=self._run, name='multicamera-diag', daemon=True)
        self._thread.start()

    def submit(self, message, line):
        with self._condition:
            if self._stopping or len(self._records) >= self._capacity:
                self._dropped += 1
                return False
            self._records.append((message, line))
            self._condition.notify()
            return True

    def flush(self, timeout=0.2):
        with self._condition:
            return self._condition.wait_for(
                lambda: not self._records and not self._active, timeout=timeout)

    def close(self, timeout=0.2):
        with self._condition:
            self._stopping = True
            self._condition.notify()
        self._thread.join(timeout)
        return not self._thread.is_alive()

    def _run(self):
        while True:
            with self._condition:
                self._condition.wait_for(lambda: self._records or self._stopping)
                if not self._records:
                    return
                record = self._records.popleft()
                dropped, self._dropped = self._dropped, 0
                self._active = True
            try:
                if dropped:
                    warning = '[MULTI_CAMERA_DIAG] dropped_records=%d reason=queue_full' % dropped
                    self._sink(warning, _format_line(warning))
                self._sink(*record)
            except Exception:
                # A failed diagnostic sink must not kill its writer or capture.
                pass
            finally:
                with self._condition:
                    self._active = False
                    self._condition.notify_all()


_writer = None
_writer_lock = threading.Lock()


def _reset_after_fork():
    # A fork inherits neither a running writer thread nor usable held locks.
    global _writer, _writer_lock
    _writer = None
    _writer_lock = threading.Lock()


os.register_at_fork(after_in_child=_reset_after_fork)


def _shutdown():
    if _writer is not None:
        _writer.close(timeout=0.2)


atexit.register(_shutdown)


def write_multicamera_diag(message, *args):
    global _writer
    if args:
        message = message % args
    if len(message) > MAX_RECORD_CHARS:
        message = message[:MAX_RECORD_CHARS] + ' [diagnostic truncated]'
    line = _format_line(message)
    try:
        with _writer_lock:
            if _writer is None:
                _writer = _DiagnosticWriter()
                # multiprocessing workers use finalizers rather than atexit.
                from multiprocessing.util import Finalize
                Finalize(None, _shutdown, exitpriority=10)
            writer = _writer
        writer.submit(message, line)
    except Exception:
        # Thread/resource exhaustion must not turn diagnostics into a failure.
        return
