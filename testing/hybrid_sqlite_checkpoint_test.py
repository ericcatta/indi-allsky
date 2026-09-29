"""Fallback policy everywhere; actual process lifecycle on SQLite >=3.51.3."""
import json
import os
from pathlib import Path
import sqlite3
import sys
import tempfile
import time
from types import SimpleNamespace
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from indi_allsky import sqlite_checkpoint as checkpoint


def wait_for(predicate, timeout=60):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if predicate():
            return
        time.sleep(.05)
    raise AssertionError('Maintenance condition did not complete')


def main():
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / 'frames.sqlite'
        state = Path(tmp) / 'state.json'
        db = sqlite3.connect(path)
        db.execute('pragma journal_mode=WAL')
        db.execute('create table frames(id integer primary key, payload text)')
        db.commit()
        record = SimpleNamespace(info={})
        pages = lambda: db.execute('pragma wal_autocheckpoint').fetchone()[0]
        with patch.dict(os.environ, {checkpoint.STATE_ENV: str(state)}), patch.object(checkpoint, 'supported', return_value=True):
            checkpoint.configure_checkout(db, record)
            assert pages() == 1000  # no helper
            state.write_text(json.dumps({'database': str(path.resolve()), 'heartbeat': time.monotonic()}))
            checkpoint.configure_checkout(db, record)
            assert pages() == 0
            state.write_text(json.dumps({'database': str(path.resolve()), 'heartbeat': time.monotonic()-31}))
            checkpoint.configure_checkout(db, record)
            assert pages() == 1000  # stopped or stalled helper
            for value in ('not-json', 'null', '{}', json.dumps({'database':str(path.resolve()),'heartbeat':'bad'}), json.dumps({'database':str(path.resolve()),'heartbeat':time.monotonic()+100}), json.dumps({'database':str(path)+'other','heartbeat':time.monotonic()})):
                state.write_text(value)
                checkpoint.configure_checkout(db, record)
                assert pages() == 1000
            state.write_text(json.dumps({'database':str(path.resolve()),'heartbeat':time.monotonic()}))
            checkpoint.configure_checkout(db, record)
            assert pages() == 0
            with patch.object(checkpoint,'supported',return_value=False):
                checkpoint.configure_checkout(db,record)
                assert pages() == 1000
            checkpoint.configure_checkout(db,record)
            os.environ.pop(checkpoint.STATE_ENV)
            checkpoint.configure_checkout(db,record)
            assert pages() == 1000  # opt-out updates pooled connection too
        engine = SimpleNamespace(dialect=SimpleNamespace(name='sqlite'),url=SimpleNamespace(database=str(path)))
        with patch.dict(os.environ, {'INDI_ALLSKY_BACKGROUND_CHECKPOINT':'0'}):
            assert checkpoint.start_for_engine(engine) is None
        with patch.dict(os.environ, {'INDI_ALLSKY_BACKGROUND_CHECKPOINT':'1'}), patch.object(checkpoint,'supported',return_value=False):
            assert checkpoint.start_for_engine(engine) is None
        with patch.dict(os.environ, {'INDI_ALLSKY_BACKGROUND_CHECKPOINT':'1'}), patch.object(checkpoint,'supported',return_value=True), patch.object(checkpoint.subprocess,'Popen',side_effect=OSError('test launch failure')):
            assert checkpoint.start_for_engine(engine) is None
            assert checkpoint.STATE_ENV not in os.environ
        if checkpoint.supported():
            old_state = os.environ.get(checkpoint.STATE_ENV)
            worker = checkpoint.CheckpointSupervisor(path)
            try:
                worker.ensure_running()
                wait_for(worker.state_path.exists)
                checkpoint.configure_checkout(db,record)
                assert pages() == 0
                # Over the real default threshold; the helper must checkpoint
                # while the writing connection stays open.
                db.executemany('insert into frames(payload) values(?)', [('x'*4096,)]*1100)
                db.commit()
                def complete():
                    busy, total, done = db.execute('pragma wal_checkpoint(NOOP)').fetchone()
                    return not busy and total > 0 and done == total
                wait_for(complete)
                assert db.execute('select count(*) from frames').fetchone()[0] == 1100
                assert db.execute('pragma integrity_check').fetchone() == ('ok',)
                first_pid = worker.process.pid
                worker.process.kill(); worker.process.wait(timeout=5)
                # Expiry protects checkouts even before supervisor notices exit.
                worker.state_path.write_text(json.dumps({'database':str(path.resolve()),'heartbeat':time.monotonic()-31}))
                checkpoint.configure_checkout(db,record)
                assert pages() == 1000
                worker.ensure_running()
                assert worker.process.pid != first_pid
                wait_for(worker.state_path.exists)
                checkpoint.configure_checkout(db,record)
                assert pages() == 0
            finally:
                worker.close()
            assert worker.process.poll() is not None
            assert not worker.state_path.parent.exists()
            assert os.environ.get(checkpoint.STATE_ENV) == old_state
            checkpoint.configure_checkout(db,record)
            assert pages() == 1000
            # Keep the opt-in environment active for the entire owned lifetime;
            # patch.dict restores all keys, including the helper's state path.
            with patch.dict(os.environ, {'INDI_ALLSKY_BACKGROUND_CHECKPOINT':'1'}):
                opted = checkpoint.start_for_engine(engine)
                assert opted is not None
                try:
                    wait_for(opted.state_path.exists)
                    checkpoint.configure_checkout(db,record)
                    assert pages() == 0
                finally:
                    opted.close()
            checkpoint.configure_checkout(db,record)
            assert pages() == 1000
            print('PASS real checkpoint, integrity, crash/restart, shutdown and environment restoration')
        else:
            print('PASS unsupported-runtime fallback; real lifecycle requires SQLite >=3.51.3')
        db.close()
    print('PASS heartbeat expiry, malformed state, database isolation and pooled fallback')


if __name__ == '__main__':
    main()
