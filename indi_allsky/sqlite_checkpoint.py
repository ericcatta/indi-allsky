"""Supervised passive SQLite checkpoints, outside capture and image commits.

Opt in with INDI_ALLSKY_BACKGROUND_CHECKPOINT=1 on SQLite >=3.51.3.
Unhealthy/missing maintenance restores SQLite's 1000-page automatic checkpoint.
This does not remove disk contention or guarantee power-loss durability with NORMAL.
"""
import json
import logging
import os
from pathlib import Path
import signal
import sqlite3
import subprocess
import sys
import tempfile
import time

logger = logging.getLogger('indi_allsky')
STATE_ENV = 'INDI_ALLSKY_CHECKPOINT_STATE'
MAX_HEARTBEAT_AGE = 30
AUTOCHECKPOINT_PAGES = 1000


def supported():
    # Also requires wal_checkpoint(NOOP), introduced in 3.51.0.
    return sqlite3.sqlite_version_info >= (3, 51, 3)


def configure_checkout(connection, record, proxy=None):
    """Called on every pool checkout, including previously opened connections."""
    state_path = os.environ.get(STATE_ENV)
    if not state_path and 'hybrid_autocheckpoint' not in record.info:
        return
    pages = AUTOCHECKPOINT_PAGES
    if state_path and supported():
        try:
            state = json.loads(Path(state_path).read_text())
            age = time.monotonic() - state['heartbeat']
            database = next(row[2] for row in connection.execute('PRAGMA database_list') if row[1] == 'main')
            if database and str(Path(database).resolve()) == state['database'] and 0 <= age < MAX_HEARTBEAT_AGE:
                pages = 0
        except (OSError, ValueError, TypeError, KeyError, StopIteration):
            pass
    if record.info.get('hybrid_autocheckpoint') != pages:
        connection.execute('PRAGMA wal_autocheckpoint=%d' % pages)
        record.info['hybrid_autocheckpoint'] = pages


class CheckpointSupervisor:
    def __init__(self, database):
        self.database = str(Path(database).resolve())
        self.directory = tempfile.TemporaryDirectory(prefix='hybrid-checkpoint-')
        self.state_path = Path(self.directory.name) / 'state.json'
        self.process = None
        self.previous_state = os.environ.get(STATE_ENV)
        os.environ[STATE_ENV] = str(self.state_path)

    def ensure_running(self):
        if self.process is not None and self.process.poll() is None:
            return True
        self.state_path.unlink(missing_ok=True)
        try:
            self.process = subprocess.Popen(
                [sys.executable, '-m', 'indi_allsky.sqlite_checkpoint', self.database,
                 str(self.state_path), str(os.getpid())],
                stdin=subprocess.DEVNULL,
                cwd=Path(__file__).resolve().parents[1],
            )
        except OSError:
            self.process = None
            logger.exception('[SQLITE_CHECKPOINT] Cannot launch maintenance; automatic fallback remains active')
            return False
        logger.info('[SQLITE_CHECKPOINT] started pid=%s', self.process.pid)
        return True

    def close(self):
        if os.environ.get(STATE_ENV) == str(self.state_path):
            if self.previous_state is None:
                os.environ.pop(STATE_ENV, None)
            else:
                os.environ[STATE_ENV] = self.previous_state
        if self.process is not None and self.process.poll() is None:
            self.process.terminate()
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait()
        self.directory.cleanup()


def start_for_engine(engine):
    if os.environ.get('INDI_ALLSKY_BACKGROUND_CHECKPOINT') != '1':
        return None
    if engine.dialect.name != 'sqlite' or not engine.url.database or engine.url.database == ':memory:':
        return None
    if not supported():
        logger.warning('[SQLITE_CHECKPOINT] SQLite >=3.51.3 required; retaining automatic checkpoints')
        return None
    try:
        supervisor = CheckpointSupervisor(engine.url.database)
    except OSError:
        logger.exception('[SQLITE_CHECKPOINT] Could not start maintenance; retaining automatic checkpoints')
        return None
    if not supervisor.ensure_running():
        supervisor.close()
        return None
    return supervisor


def maintain(database, state_path, parent_pid):
    if not supported():
        raise RuntimeError('SQLite >=3.51.3 required')
    database = str(Path(database).resolve())
    state_path = Path(state_path)
    stopping = False

    def stop(signum, frame):
        nonlocal stopping
        stopping = True

    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)
    connection = sqlite3.connect(Path(database).as_uri() + '?mode=rw', uri=True, timeout=0)
    last_warning = 0
    try:
        if connection.execute('PRAGMA journal_mode').fetchone()[0] != 'wal':
            raise RuntimeError('Background checkpoints require an existing WAL database')
        connection.execute('PRAGMA synchronous=NORMAL')
        while not stopping and os.getppid() == parent_pid:
            # Publish only after SQLite has responded. An I/O stall expires the
            # heartbeat and returns future checkouts to the automatic fallback.
            busy, frames, completed = connection.execute('PRAGMA wal_checkpoint(NOOP)').fetchone()
            if not busy and frames >= AUTOCHECKPOINT_PAGES and completed < frames:
                started = time.monotonic()
                busy, frames, completed = connection.execute('PRAGMA wal_checkpoint(PASSIVE)').fetchone()
                elapsed = time.monotonic() - started
                if elapsed >= 2:
                    logger.warning('[SQLITE_CHECKPOINT] seconds=%.3f frames=%s completed=%s', elapsed, frames, completed)
            now = time.monotonic()
            if frames - completed >= 16384 and now - last_warning >= 60:
                logger.warning('[SQLITE_CHECKPOINT] backlog frames=%s completed=%s; check long readers and storage', frames, completed)
                last_warning = now
            pending = state_path.with_suffix('.tmp')
            pending.write_text(json.dumps({'database': database, 'heartbeat': now}))
            pending.replace(state_path)
            time.sleep(1)
    finally:
        state_path.unlink(missing_ok=True)
        connection.close()


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    maintain(sys.argv[1], sys.argv[2], int(sys.argv[3]))
