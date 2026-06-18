import os
import re
import logging
from datetime import datetime
from pathlib import Path


logger = logging.getLogger('indi_allsky')


DIAG_PATHS = (
    Path('/tmp/indi-allsky-multicamera-diag.log'),
    Path('/var/lib/indi-allsky/multicamera-diag.log'),
)

PROFILE_RE = re.compile(r'\[MULTI_CAMERA_[^\]]+\]\[([^\]]+)\]')
CAMERA_RE = re.compile(r'\[camera_id=([^\]]+)\]')


def write_multicamera_diag(message, *args):
    if args:
        message = message % args

    logger.debug(message)

    timestamp = datetime.now().isoformat(timespec='seconds')
    profile_match = PROFILE_RE.search(message)
    camera_match = CAMERA_RE.search(message)
    profile_id = profile_match.group(1) if profile_match else 'unknown'
    camera_id = camera_match.group(1) if camera_match else 'unknown'
    line = (
        '{timestamp} pid={pid} profile_id={profile_id} camera_id={camera_id} event={event}\n'
    ).format(
        timestamp=timestamp,
        pid=os.getpid(),
        profile_id=profile_id,
        camera_id=camera_id,
        event=message,
    )

    for path in DIAG_PATHS:
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open('a', buffering=1, encoding='utf-8') as diag_f:
                diag_f.write(line)
        except Exception:
            # Diagnostics must never interfere with capture.
            continue
