"""Prepare the owned temporary metadata file for an end-of-night upload."""
import json
import logging
from pathlib import Path
import tempfile


def prepare_end_of_night_payload(data, *, remote_folder, camera_uuid, now, temp_factory=None):
    # Reject malformed destination formatting before allocating a local file.
    remote = Path(remote_folder.format(timestamp=now, ts=now, camera_uuid=camera_uuid)).joinpath('data.json')
    local = None
    try:
        with (temp_factory or tempfile.NamedTemporaryFile)(mode='w', delete=False, encoding='utf-8') as stream:
            local = Path(stream.name)
            json.dump(data, stream, indent=4, ensure_ascii=False)
        return local, remote
    except BaseException:
        if local is not None:
            try:
                local.unlink(missing_ok=True)
            except OSError:
                logging.getLogger(__name__).exception('Could not remove failed EndOfNight temporary payload')
        raise


def handoff_end_of_night_upload(parent, child, *, session, dispatch, camera_id):
    """Commit ownership before dispatch; never delete or retry an uncertain upload."""
    logger = logging.getLogger(__name__)
    original_data = dict(parent.data or {})
    local_file = child.data['local_file']
    child_id = None
    try:
        session.add(child)
        session.flush()
        child_id = child.id
        parent.data = dict(original_data, end_of_night_upload={
            'status': 'prepared', 'task_id': child_id, 'camera_id': camera_id,
        })
        parent.result = 'Prepared EndOfNight upload task {0}; inspect its status for delivery'.format(child_id)
        session.commit()
    except Exception:
        logger.exception('Could not persist EndOfNight upload; metadata retained at %s', local_file)
        session.rollback()
        # A lost commit acknowledgement may hide a persisted child. Keep the
        # file and candidate ID for recovery, and do not submit another task.
        parent.data = dict(original_data, end_of_night_upload={
            'status': 'persistence_uncertain', 'candidate_task_id': child_id,
            'camera_id': camera_id, 'local_file': local_file,
        })
        parent.setFailed('Could not confirm upload persistence; no dispatch attempted. Metadata retained for recovery')
        return False
    try:
        dispatch(child, camera_id=camera_id)
    except Exception:
        logger.exception('EndOfNight upload dispatch outcome unknown for task %s', child_id)
        parent.data = dict(original_data, end_of_night_upload={
            'status': 'dispatch_uncertain', 'task_id': child_id, 'camera_id': camera_id,
        })
        # Do not overwrite child state: a worker may already have received it.
        parent.setFailed('Upload task {0} dispatch could not be confirmed; inspect it before retrying'.format(child_id))
        return False
    parent.data = dict(original_data, end_of_night_upload={
        'status': 'queued', 'task_id': child_id, 'camera_id': camera_id,
    })
    try:
        parent.setSuccess('Queued EndOfNight upload task {0}; delivery is not yet confirmed'.format(child_id))
    except Exception:
        logger.exception('Upload task %s dispatched but parent completion could not be persisted', child_id)
        session.rollback()
        return False
    return True
