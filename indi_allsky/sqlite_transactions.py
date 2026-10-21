"""Bounded retry of database-only mutations after SQLite contention."""
import logging
import os
import sqlite3
import time

from sqlalchemy import event
from sqlalchemy import exc as sqlalchemy_exc
from sqlalchemy.exc import OperationalError

logger = logging.getLogger('indi_allsky')


def install_sqlite_fork_guard(engine):
    """Invalidate a pooled SQLite connection when checked out after fork."""
    if engine.dialect.name != 'sqlite':
        return
    if getattr(engine, '_indi_allsky_fork_guard', False):
        return

    @event.listens_for(engine, 'connect')
    def remember_pid(dbapi_connection, connection_record):
        connection_record.info['indi_allsky_connection_pid'] = os.getpid()

    @event.listens_for(engine, 'checkout')
    def reject_parent_connection(dbapi_connection, connection_record, connection_proxy):
        if connection_record.info.get('indi_allsky_connection_pid') == os.getpid():
            return
        # SQLAlchemy replaces this record with a connection opened in the
        # current process. The parent's descriptor remains owned by its pool.
        connection_record.dbapi_connection = connection_proxy.dbapi_connection = None
        raise sqlalchemy_exc.DisconnectionError('SQLite connection belongs to a different process')

    engine._indi_allsky_fork_guard = True


def retry_sqlite_transaction(session, write):
    started = time.monotonic()
    for attempt in range(3):
        try:
            entry = write()
            session.commit()
            return entry
        except OperationalError as exc:
            session.rollback()
            code = getattr(exc.orig, 'sqlite_errorcode', None)
            base_code = (code & 0xff) if isinstance(code, int) else None
            logger.warning(
                '[SQLITE_TRANSACTION_RETRY] attempt=%d limit=3 elapsed=%.3fs '
                'error_type=%s sqlite_errorcode=%s sqlite_basecode=%s retryable=%s',
                attempt + 1,
                time.monotonic() - started,
                type(exc.orig).__name__,
                code,
                base_code,
                isinstance(exc.orig, sqlite3.Error)
                and base_code in (sqlite3.SQLITE_BUSY, sqlite3.SQLITE_LOCKED)
                and attempt < 2,
            )
            if (not isinstance(exc.orig, sqlite3.Error) or code is None or
                    base_code not in (sqlite3.SQLITE_BUSY, sqlite3.SQLITE_LOCKED) or
                    attempt == 2):
                raise
            # Replay database mutations only, never filesystem or upload effects.
            time.sleep(0.1 * (attempt + 1))


def insert_with_retry(session, model, values):
    def write():
        entry = model(**values)
        session.add(entry)
        return entry
    return retry_sqlite_transaction(session, write)

