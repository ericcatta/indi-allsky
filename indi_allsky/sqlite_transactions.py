"""Bounded retry of database-only mutations after SQLite contention."""
import sqlite3
import time

from sqlalchemy.exc import OperationalError


def retry_sqlite_transaction(session, write):
    for attempt in range(3):
        try:
            entry = write()
            session.commit()
            return entry
        except OperationalError as exc:
            session.rollback()
            code = getattr(exc.orig, 'sqlite_errorcode', None)
            if (not isinstance(exc.orig, sqlite3.Error) or code is None or
                    (code & 0xff) not in (sqlite3.SQLITE_BUSY, sqlite3.SQLITE_LOCKED) or
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

