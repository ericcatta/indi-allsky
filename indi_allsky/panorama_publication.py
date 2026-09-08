"""Panorama encoding and complete, camera-scoped file publication."""
import io
import os
from pathlib import Path
import tempfile


def encode_panorama(data, config, jpeg_exif=None):
    import cv2
    from PIL import Image
    extension = config['IMAGE_FILE_TYPE']
    if extension == 'png':
        success, encoded = cv2.imencode('.png', data, [cv2.IMWRITE_PNG_COMPRESSION, config['IMAGE_FILE_COMPRESSION']['png']])
        if not success:
            raise OSError('Panorama encoder did not produce an image')
        return encoded.tobytes()
    formats = {'jpg':'JPEG', 'jpeg':'JPEG', 'webp':'WEBP', 'tif':'TIFF', 'tiff':'TIFF'}
    if extension not in formats:
        raise ValueError('Unknown panorama file type: ' + str(extension))
    options = {'compression':'tiff_lzw'}
    if extension in ('jpg','jpeg'):
        options = {'quality':config['IMAGE_FILE_COMPRESSION']['jpg'], 'exif':jpeg_exif or b''}
    elif extension == 'webp':
        options = {'quality':90, 'lossless':False, 'exif':jpeg_exif or b''}
    with io.BytesIO() as stream:
        Image.fromarray(cv2.cvtColor(data, cv2.COLOR_BGR2RGB)).save(stream, format=formats[extension], **options)
        return stream.getvalue()


def publish_panorama_file(root, target, content, *, overwrite=True):
    root, target = Path(root).resolve(), Path(target).resolve()
    if not target.is_relative_to(root):
        raise ValueError('Panorama path is outside the media folder')
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(dir=target.parent, prefix='.panorama-', delete=False) as stream:
            temporary = Path(stream.name)
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        temporary.chmod(0o644)
        if overwrite:
            os.replace(temporary, target)
        else:
            # Linking a complete file fails atomically if a capture already exists.
            os.link(temporary, target)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
    return target
