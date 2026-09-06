"""Camera-specific transient focus frames, independent of the media archive."""
import os
from pathlib import Path
import shutil
import tempfile


def focus_frame_path(image_dir, camera_id, extension):
    camera_id = int(camera_id)
    if camera_id <= 0 or extension not in ('jpg', 'jpeg', 'png', 'webp', 'tif', 'tiff'):
        raise ValueError('Invalid focus frame target')
    root = Path(image_dir).resolve()
    path = root / ('focus-camera-{0}.{1}'.format(camera_id, extension))
    if path.is_symlink():
        raise ValueError('Focus frame target cannot be a symlink')
    return path


def publish_focus_frame(source, image_dir, camera_id, extension):
    """Replace one camera's last frame only after the complete file is available."""
    target = focus_frame_path(image_dir, camera_id, extension)
    descriptor, temporary = tempfile.mkstemp(prefix='.focus-', suffix='.'+extension, dir=target.parent)
    os.close(descriptor)
    temporary = Path(temporary)
    try:
        shutil.copy2(source, temporary)
        temporary.chmod(0o644)
        os.replace(temporary, target)
    finally:
        temporary.unlink(missing_ok=True)
    return target
