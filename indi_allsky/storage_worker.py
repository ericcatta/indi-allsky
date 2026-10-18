"""Dedicated queue consumer for bounded archive cleanup batches.

Reuse the existing task/error/notification executor, but never consume video
generation work. The database queue remains VIDEO for compatible task history.
"""
from .video import VideoWorker
from .flask.models import IndiAllSkyDbTaskQueueTable, TaskQueueState, TaskQueueQueue


class StorageWorker(VideoWorker):
    def __init__(self, idx, *args):
        super().__init__(idx, *args)
        self.name = 'Storage-{0:d}'.format(idx)

    def processTask(self, payload):
        task = IndiAllSkyDbTaskQueueTable.query.filter_by(
            id=payload['task_id'], state=TaskQueueState.QUEUED,
            queue=TaskQueueQueue.VIDEO).first()
        if task is None:
            return
        if not isinstance(task.data, dict) or task.data.get('action') != 'storagePressureCleanup':
            task.setFailed('Storage worker only accepts storage cleanup tasks.')
            return
        return super().processTask(payload)


def recover_interrupted_cleanup():
    from .flask import db
    tasks = IndiAllSkyDbTaskQueueTable.query.filter(
        IndiAllSkyDbTaskQueueTable.queue == TaskQueueQueue.VIDEO,
        IndiAllSkyDbTaskQueueTable.state.in_((TaskQueueState.QUEUED, TaskQueueState.RUNNING)),
    ).all()
    for task in tasks:
        if isinstance(task.data, dict) and task.data.get('action') == 'storagePressureCleanup':
            task.state = TaskQueueState.FAILED
            task.result = 'Storage worker stopped; cleanup will retry on the next pressure check.'
    db.session.commit()
