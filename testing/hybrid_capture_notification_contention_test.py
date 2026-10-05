#!/usr/bin/env python3
"""A real SQLite writer conflict must not kill capture for a diagnostic notice."""
import ast
from datetime import timedelta
import logging
from pathlib import Path
import sqlite3
from types import SimpleNamespace
from unittest.mock import Mock

from sqlalchemy.exc import OperationalError
from hybrid_runtime_fixture import isolated_app


def run():
    with isolated_app(file_database=True) as app:
        from indi_allsky.flask import db
        from indi_allsky.flask.miscDb import miscDb
        from indi_allsky.flask.models import NotificationCategory, IndiAllSkyDbNotificationTable
        tree = ast.parse((Path(__file__).resolve().parents[1] / 'indi_allsky/capture.py').read_text())
        cls = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == 'CaptureWorker')
        method = next(n for n in cls.body if isinstance(n, ast.FunctionDef) and n.name == '_notify_image_backlog')
        namespace = dict(db=db, sqlite3=sqlite3, OperationalError=OperationalError,
                         NotificationCategory=NotificationCategory, timedelta=timedelta,
                         logger=logging.getLogger('notification-contention-test'))
        exec(compile(ast.Module(body=[method], type_ignores=[]), '<capture-notification>', 'exec'), namespace)
        notify = namespace['_notify_image_backlog']
        assert any(isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
                   and n.func.attr == '_notify_image_backlog' for n in ast.walk(cls))
        with app.app_context():
            worker = SimpleNamespace(_miscDb=miscDb({}), profile_id='test-profile-1', camera_id=1)
            db.session.connection().exec_driver_sql('PRAGMA busy_timeout=0')
            writer = sqlite3.connect(db.engine.url.database, timeout=0)
            try:
                writer.execute('BEGIN IMMEDIATE')
                try:
                    worker._miscDb.addNotification(
                        NotificationCategory.WORKER, 'image_queue_depth', 'backlog')
                except OperationalError as error:
                    assert error.orig.sqlite_errorcode & 0xff == sqlite3.SQLITE_BUSY
                    db.session.rollback()
                else:
                    raise AssertionError('Fixture did not reproduce the production writer conflict')
                notify(worker)  # Real INSERT fails with SQLITE_BUSY, rolls back, returns.
                assert db.session.is_active
            finally:
                writer.rollback()
                writer.close()
            assert IndiAllSkyDbNotificationTable.query.count() == 0
            notify(worker)
            notices = IndiAllSkyDbNotificationTable.query.all()
            assert len(notices) == 1 and notices[0].item == 'image_queue_depth'
            notify(worker)
            assert IndiAllSkyDbNotificationTable.query.count() == 1
            # Unrelated storage failures must still surface; no blanket swallowing.
            error = OperationalError('INSERT', {}, sqlite3.OperationalError('disk I/O error'))
            worker._miscDb = SimpleNamespace(addNotification=Mock(side_effect=error))
            try:
                notify(worker)
            except OperationalError as caught:
                assert caught is error
            else:
                raise AssertionError('Non-contention database failure was hidden')
        print('Capture diagnostic SQLite contention, rollback, recovery and deduplication: PASS')


if __name__ == '__main__':
    run()
