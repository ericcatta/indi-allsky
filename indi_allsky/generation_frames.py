"""Read one display frame without depending on an evictable cache pathname."""
import io
import logging
from pathlib import Path

import cv2

from .source_preview import source_preview_jpeg
from .source_publication import read_source_recipe

logger = logging.getLogger('indi_allsky')


def read_generation_frame(entry, media_root, fits_lookup):
    """Return (diagnostic path, BGR pixels, exposure timestamp), or absent legacy frame.

    Archived display files retain their historical decoding and timestamp behavior.
    An absent display file with an archival recipe must reconstruct successfully;
    silently skipping that exposure would hide a damaged scientific archive.
    """
    path = Path(entry.getFilesystemPath())
    if not path.exists():
        recipe = (entry.data or {}).get('render_source')
        source_id = (recipe['basis']['source_id'] if recipe is not None
                     else (entry.data or {}).get('source_fits_id'))
        if source_id is None:
            logger.error('File not found: %s', path)
            return None
        source = fits_lookup(source_id)
        if (source.camera_id != entry.camera_id or source.id != source_id
                or source.createDate != entry.createDate):
            raise ValueError('Generation source does not match the camera/exposure')
        source_path = Path(source.getFilesystemPath()).resolve(strict=True)
        source_path.relative_to(Path(media_root).resolve(strict=True))
        if recipe is None:
            recipe = read_source_recipe(source_path)
            if recipe is None:
                raise ValueError('Source lacks a complete rendering recipe')
        jpeg = source_preview_jpeg(source_path, recipe, camera_id=entry.camera_id,
                                   source_id=source.id, media_root=media_root)
        import simplejpeg
        pixels = simplejpeg.decode_jpeg(jpeg, colorspace='BGR')
        return source_path, pixels, entry.createDate.timestamp()
    if path.stat().st_size == 0:
        return None
    if path.suffix in ('.jpg', '.jpeg'):
        import simplejpeg
        try:
            with io.open(str(path), 'rb') as stream:
                pixels = simplejpeg.decode_jpeg(stream.read(), colorspace='BGR')
        except ValueError as error:
            logger.error('Unable to read image - %s: %s', str(error), path)
            return None
    elif path.suffix == '.png':
        pixels = cv2.imread(str(path), cv2.IMREAD_COLOR)
        if pixels is None:
            logger.error('Unable to read %s', path)
            return None
    else:
        import numpy
        import PIL
        from PIL import Image
        try:
            with Image.open(str(path)) as image:
                pixels = cv2.cvtColor(numpy.array(image), cv2.COLOR_RGB2BGR)
        except PIL.UnidentifiedImageError:
            logger.error('Unable to read image: %s', path)
            return None
    return path, pixels, path.stat().st_mtime
