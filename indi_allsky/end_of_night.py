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
