"""Register an already-published FITS without replaying filesystem effects."""
import sqlite3
import time

from sqlalchemy.exc import OperationalError


def register_fits(session, model, values):
    for attempt in range(3):
        entry = model(**values)
        try:
            session.add(entry)
            session.commit()
            return entry
        except OperationalError as exc:
            session.rollback()
            code = getattr(exc.orig, 'sqlite_errorcode', None)
            if (not isinstance(exc.orig, sqlite3.Error) or code is None or
                    (code & 0xff) not in (sqlite3.SQLITE_BUSY, sqlite3.SQLITE_LOCKED) or
                    attempt == 2):
                raise
            # A new instance and transaction avoid an expired read snapshot or
            # a rolled-back pending INSERT. The FITS has already been published.
            time.sleep(0.1 * (attempt + 1))
