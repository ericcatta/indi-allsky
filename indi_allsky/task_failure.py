"""Persist a worker failure without replaying the failed task's effects."""
import sqlite3
import time

from sqlalchemy.exc import OperationalError


def record_video_failure(session, models, task_id, message):
    """Fresh conditional write; preserve another actor's terminal outcome.

    SQLite cannot upgrade an obsolete read snapshot to a writer. Do not refresh
    the task before this UPDATE; use its immutable queue ID after rollback.
    Retries cover only this status write, never the original effect.
    """
    table = models.IndiAllSkyDbTaskQueueTable
    state = models.TaskQueueState
    session.rollback()
    for attempt in range(3):
        try:
            changed = session.query(table).filter(
                table.id == task_id,
                table.queue == models.TaskQueueQueue.VIDEO,
                table.state.in_((state.QUEUED, state.RUNNING)),
            ).update({table.state: state.FAILED, table.result: message},
                     synchronize_session=False)
            session.commit()
            return bool(changed)
        except OperationalError as exc:
            session.rollback()
            code = getattr(exc.orig, 'sqlite_errorcode', None)
            if (not isinstance(exc.orig, sqlite3.Error) or code is None or
                    (code & 0xff) not in (sqlite3.SQLITE_BUSY, sqlite3.SQLITE_LOCKED) or
                    attempt == 2):
                raise
            time.sleep(0.1 * (attempt + 1))
