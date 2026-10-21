#!/usr/bin/env python3
"""Forked workers must not reuse the supervisor's pooled SQLite connection."""
import multiprocessing
import sys

from hybrid_runtime_fixture import isolated_app


def child_check(app, result):
    with app.app_context():
        from indi_allsky.flask import db
        with db.engine.connect() as connection:
            result.put({
                'parent_marker': connection.info.get('parent_pool_marker'),
                'journal_mode': connection.exec_driver_sql('PRAGMA journal_mode').scalar(),
                'busy_timeout': connection.exec_driver_sql('PRAGMA busy_timeout').scalar(),
            })


runtime_config = sys.argv[1] if len(sys.argv) > 1 else '/etc/indi-allsky/flask.json'
with isolated_app(runtime_config, file_database=True) as app:
    ctx = multiprocessing.get_context('fork')
    with app.app_context():
        from indi_allsky.flask import db
        # Return a marked connection to the parent's pool before forking. A
        # copied QueuePool would otherwise hand this same DBAPI connection to
        # each independent worker process.
        with db.engine.connect() as connection:
            connection.info['parent_pool_marker'] = 'must-not-cross-fork'
        result = ctx.Queue()
        child = ctx.Process(target=child_check, args=(app, result))
        try:
            child.start()
            observed = result.get(timeout=10)
            child.join(10)
            assert child.exitcode == 0
            assert observed == {
                'parent_marker': None,
                'journal_mode': 'wal',
                'busy_timeout': 20000,
            }, observed
            # Child invalidation must not close or replace the parent pool.
            with db.engine.connect() as connection:
                assert connection.info['parent_pool_marker'] == 'must-not-cross-fork'
        finally:
            if child.is_alive():
                child.terminate()
                child.join(10)
            if child.is_alive():
                child.kill()
                child.join(10)
            result.close()
            result.join_thread()

print('SQLite fork pool: child opens an independent configured connection; parent pool remains valid PASS')
