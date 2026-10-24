#!/usr/bin/env python3
"""Storage cleanup yields SQLite's writer slot after a completed delete."""
import multiprocessing
from pathlib import Path
import sqlite3
import tempfile
from unittest.mock import Mock, patch

from indi_allsky.storage_pressure_runtime import StoragePressureRuntime


class CommittingCleanup(StoragePressureRuntime):
    def __init__(self, database, committed):
        self.connection = sqlite3.connect(database, timeout=0)
        self.committed = committed
        self.sqlite_writer_fairness = True

    def _delete_once(self, candidate):
        self.connection.execute("INSERT INTO writes(source) VALUES ('cleanup')")
        self.connection.commit()
        self.committed.set()


def locked_writer(database, locked, release):
    connection = sqlite3.connect(database, timeout=0)
    try:
        connection.execute('BEGIN IMMEDIATE')
        connection.execute("INSERT INTO writes(source) VALUES ('baseline')")
        locked.set()
        release.wait(5)
        connection.commit()
    finally:
        connection.close()


def yielding_cleanup(database, committed, yielded, release):
    runtime = CommittingCleanup(database, committed)

    def controlled_yield(seconds):
        assert seconds == 0.01
        assert committed.is_set()
        yielded.set()
        release.wait(5)

    try:
        with patch('indi_allsky.storage_pressure_runtime.time.sleep', controlled_yield):
            runtime.delete(None)
    finally:
        runtime.connection.close()


def contender(database, ready, result, done):
    connection = sqlite3.connect(database, timeout=0)
    try:
        ready.wait(5)
        connection.execute("INSERT INTO writes(source) VALUES ('capture')")
        connection.commit()
        result.put('committed')
    except sqlite3.OperationalError as error:
        result.put(str(error))
    finally:
        done.set()
        connection.close()


def stop(process):
    process.join(5)
    if process.is_alive():
        process.terminate()
        process.join(5)
    if process.is_alive():
        process.kill()
        process.join(5)


with tempfile.TemporaryDirectory(prefix='hybrid-storage-fairness-') as folder:
    database = str(Path(folder) / 'archive.sqlite')
    connection = sqlite3.connect(database)
    connection.execute('PRAGMA journal_mode=WAL')
    connection.execute('CREATE TABLE writes (id INTEGER PRIMARY KEY, source TEXT NOT NULL)')
    connection.commit()
    connection.close()

    context = multiprocessing.get_context('fork')

    # Baseline: a contender cannot write while cleanup still owns SQLite's
    # writer slot. This establishes that the test detects real contention.
    locked = context.Event()
    release = context.Event()
    done = context.Event()
    result = context.Queue()
    cleanup = context.Process(target=locked_writer, args=(database, locked, release))
    capture = context.Process(target=contender, args=(database, locked, result, done))
    try:
        cleanup.start()
        capture.start()
        baseline = result.get(timeout=5)
        assert 'locked' in baseline, baseline
    finally:
        release.set()
        stop(capture)
        stop(cleanup)
        result.close()
        result.join_thread()

    # Fixed path: production delete commits first, exits _delete_once (and its
    # media lock), then yields. Hold that yield open so the assertion does not
    # depend on process scheduling or a narrow timing window.
    committed = context.Event()
    yielded = context.Event()
    release = context.Event()
    done = context.Event()
    result = context.Queue()
    cleanup = context.Process(
        target=yielding_cleanup, args=(database, committed, yielded, release))
    capture = context.Process(target=contender, args=(database, yielded, result, done))
    try:
        cleanup.start()
        capture.start()
        fixed = result.get(timeout=5)
        assert fixed == 'committed', fixed
        assert committed.is_set()
        assert yielded.is_set()
        assert done.is_set()
    finally:
        release.set()
        stop(capture)
        stop(cleanup)
        result.close()
        result.join_thread()

    connection = sqlite3.connect(database)
    try:
        assert connection.execute(
            "SELECT count(*) FROM writes WHERE source='capture'").fetchone()[0] == 1
    finally:
        connection.close()

# A failed effect must not be delayed or presented as a completed fairness
# handoff. Retry handling retains its existing bounded backoff instead.
failed = object.__new__(StoragePressureRuntime)
failed.sqlite_writer_fairness = True
failed._delete_once = Mock(side_effect=RuntimeError('delete failed'))
with patch('indi_allsky.storage_pressure_runtime.time.sleep') as sleep:
    try:
        failed.delete(None)
    except RuntimeError as error:
        assert str(error) == 'delete failed'
    else:
        raise AssertionError('failed delete unexpectedly returned')
sleep.assert_not_called()

print('Storage SQLite fairness: baseline contention fails; post-commit yield permits capture PASS')
