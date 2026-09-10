"""Camera-owned mask base publication; the unscoped file is compatibility only."""
import os
from pathlib import Path
import shutil
import tempfile


def mask_frame_path(image_dir, camera_id):
    camera_id = int(camera_id)
    if camera_id <= 0:
        raise ValueError('Invalid mask camera')
    path = Path(image_dir).resolve() / ('mask-camera-{0}.png'.format(camera_id))
    if path.is_symlink():
        raise ValueError('Mask target cannot be a symlink')
    return path


def publish_mask_base(data, image_dir, camera_id, compression):
    import cv2
    target = mask_frame_path(image_dir, camera_id)
    descriptor, name = tempfile.mkstemp(prefix='.mask-', suffix='.png', dir=target.parent)
    os.close(descriptor)
    temporary = Path(name)
    try:
        if not cv2.imwrite(str(temporary), data, [cv2.IMWRITE_PNG_COMPRESSION, compression]):
            raise OSError('Unable to encode mask base')
        temporary.chmod(0o644)
        os.replace(temporary, target)
        # Keep historical consumers working; Hybrid never reads this ambiguous file.
        shutil.copy2(target, temporary)
        os.replace(temporary, target.parent / 'mask_base.png')
    finally:
        temporary.unlink(missing_ok=True)
    return target
