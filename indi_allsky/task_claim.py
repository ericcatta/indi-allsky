"""Atomic ownership of queued upload work, independent of frontend views."""


def claim_upload_task(task_id, *, session=None):
    """Commit QUEUED -> RUNNING only once before allowing any upload effect.

    Called in a fresh worker transaction. A lost commit acknowledgement is not
    retried: the task may be RUNNING and needs inspection, rather than a second
    upload. This protects one task ID, not distinct tasks for the same file.
    """
    from .flask import db, models

    if session is None:
        session = db.session
    model = models.IndiAllSkyDbTaskQueueTable
    try:
        changed = session.query(model).filter(
            model.id == task_id,
            model.queue == models.TaskQueueQueue.UPLOAD,
            model.state == models.TaskQueueState.QUEUED,
        ).update({model.state: models.TaskQueueState.RUNNING}, synchronize_session=False)
        if changed != 1:
            session.rollback()
            return None
        session.commit()
    except Exception:
        session.rollback()
        raise

    # Refresh even if a caller's identity map contained an earlier task state.
    task = session.get(model, task_id, populate_existing=True)
    if task is None or task.state != models.TaskQueueState.RUNNING:
        return None
    return task
