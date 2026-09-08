"""Publish a complete per-camera long-term preview without truncating its cache."""
from pathlib import Path
import os
import tempfile


def write_longterm_keogram_cache(root, camera_uuid, content):
    root = Path(root).resolve()
    target = (root / ('ccd_' + str(camera_uuid)) / 'longterm_keogram.jpg').resolve()
    if not target.is_relative_to(root):
        raise ValueError('Camera cache path is outside the media folder')
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(dir=target.parent, prefix='.longterm-', delete=False) as stream:
            temporary = Path(stream.name)
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        temporary.chmod(0o644)
        os.replace(temporary, target)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
    return target
