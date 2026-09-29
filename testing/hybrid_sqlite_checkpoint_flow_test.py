"""Verify checkout wiring on real Flask/SQLAlchemy pooled connections."""
import json
import os
from pathlib import Path
import tempfile
import time
from unittest.mock import patch

from hybrid_runtime_fixture import isolated_app


def run():
    with isolated_app(file_database=True) as app:
        from indi_allsky.flask import db
        from indi_allsky import sqlite_checkpoint as checkpoint
        with app.app_context(), tempfile.TemporaryDirectory() as tmp:
            engine = db.engine
            state = Path(tmp) / 'state.json'
            database = str(Path(engine.url.database).resolve())
            with patch.dict(os.environ, {checkpoint.STATE_ENV: str(state)}), patch.object(checkpoint, 'supported', return_value=True):
                with engine.connect() as conn:
                    assert conn.exec_driver_sql('pragma wal_autocheckpoint').scalar() == 1000
                    assert conn.exec_driver_sql('pragma synchronous').scalar() == 1
                state.write_text(json.dumps({'database':database,'heartbeat':time.monotonic()}))
                with engine.begin() as conn:
                    assert conn.exec_driver_sql('pragma wal_autocheckpoint').scalar() == 0
                    conn.exec_driver_sql('create table checkpoint_probe (value integer)')
                    conn.exec_driver_sql('insert into checkpoint_probe values (42)')
                state.unlink()
                with engine.connect() as conn:
                    assert conn.exec_driver_sql('pragma wal_autocheckpoint').scalar() == 1000
                    assert conn.exec_driver_sql('pragma synchronous').scalar() == 1
                    assert conn.exec_driver_sql('select value from checkpoint_probe').scalar() == 42
    print('PASS Flask checkout enable/fallback and committed data; synthetic heartbeat, no hardware')


if __name__ == '__main__':
    run()
