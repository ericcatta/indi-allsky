"""Cached JPEG derivatives of an authorized FITS exposure and frozen recipe."""
import hashlib
import json
from pathlib import Path

from .preview_cache import PreviewCache
from .render_assets import RenderAssetStore
from .source_rendering import render_source


def source_preview_jpeg(path, recipe, *, camera_id, source_id, media_root, cache=None):
    basis = recipe.get('basis', {})
    if basis.get('camera_id') != camera_id or basis.get('source_id') != source_id:
        raise ValueError('Source recipe identity mismatch')
    quality = int(recipe['jpeg_quality'])
    if not 0 <= quality <= 100:
        raise ValueError('Invalid archived JPEG quality')
    path = Path(path).resolve(strict=True)
    st = path.stat()
    identity = {
        'version': 1, 'recipe': recipe, 'path': str(path),
        'device': st.st_dev, 'inode': st.st_ino, 'size': st.st_size,
        'mtime_ns': st.st_mtime_ns, 'ctime_ns': st.st_ctime_ns,
    }
    key = hashlib.sha256(json.dumps(identity, sort_keys=True, allow_nan=False,
                                   separators=(',', ':')).encode()).hexdigest()
    assets = RenderAssetStore(Path(media_root) / '.render-assets')
    if cache is None:
        cache = PreviewCache(Path(media_root) / '.render-cache')

    def render():
        import cv2
        pixels = render_source(path, recipe, assets, camera_id=camera_id, source_id=source_id)
        encoded, jpeg = cv2.imencode('.jpg', pixels, [cv2.IMWRITE_JPEG_QUALITY, quality])
        if not encoded:
            raise ValueError('JPEG encoding failed')
        return jpeg.tobytes()

    return cache.get_or_create(key, render)
