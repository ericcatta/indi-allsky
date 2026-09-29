"""Publish complete encoded frames without exposing a partial copy to readers."""
import os
from pathlib import Path
import shutil
import tempfile


def publish_image_file(source, target, overwrite=True):
    """Stage on the destination filesystem; preserve an existing archive entry."""
    target = Path(target)
    descriptor, temporary = tempfile.mkstemp(prefix='.image-', dir=target.parent)
    os.close(descriptor)
    temporary = Path(temporary)
    try:
        shutil.copy2(source, temporary)
        temporary.chmod(0o644)
        if overwrite:
            os.replace(temporary, target)
        else:
            try:
                os.link(temporary, target)
            except FileExistsError:
                return False
        return True
    finally:
        temporary.unlink(missing_ok=True)
