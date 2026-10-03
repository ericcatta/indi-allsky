"""Cached JPEG derivatives of an authorized FITS exposure and frozen recipe."""
import hashlib
import json
from pathlib import Path

from .preview_cache import PreviewCache
from .render_assets import RenderAssetStore
from .source_rendering import render_source


def source_preview_jpeg(path, recipe, *, camera_id, source_id, media_root, cache=None):
    return source_display_bytes(path, recipe, camera_id=camera_id, source_id=source_id,
                                media_root=media_root, cache=cache)


def source_display_bytes(path, recipe, *, camera_id, source_id, media_root,
                         file_type='jpg', cache=None):
    """Encode frozen display pixels in the requested archive/upload format."""
    file_type = {'jpeg': 'jpg', 'tif': 'tiff'}.get(file_type, file_type)
    if file_type not in ('jpg', 'png', 'webp', 'tiff'):
        raise ValueError('Unsupported display format')
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
    if file_type != 'jpg':
        identity['format'] = file_type
    key = hashlib.sha256(json.dumps(identity, sort_keys=True, allow_nan=False,
                                   separators=(',', ':')).encode()).hexdigest()
    assets = RenderAssetStore(Path(media_root) / '.render-assets')
    if cache is None:
        cache = PreviewCache(Path(media_root) / '.render-cache')

    def render():
        import cv2
        pixels = render_source(path, recipe, assets, camera_id=camera_id, source_id=source_id)
        if file_type in ('jpg', 'png'):
            options = ([cv2.IMWRITE_JPEG_QUALITY, quality] if file_type == 'jpg'
                       else [cv2.IMWRITE_PNG_COMPRESSION, 3])
            encoded, data = cv2.imencode('.' + file_type, pixels, options)
            if not encoded:
                raise ValueError('Display encoding failed')
            encoded_bytes = data.tobytes()
            if file_type == 'jpg' and recipe.get('export_exif'):
                import io
                import piexif
                with io.BytesIO() as stream:
                    piexif.insert(bytes.fromhex(recipe['export_exif']), encoded_bytes, stream)
                    encoded_bytes = stream.getvalue()
            return encoded_bytes
        import io
        from PIL import Image
        with io.BytesIO() as stream:
            image = Image.fromarray(cv2.cvtColor(pixels, cv2.COLOR_BGR2RGB))
            if file_type == 'webp':
                image.save(stream, format='WEBP', quality=90, lossless=False,
                           exif=bytes.fromhex(recipe.get('export_exif', '')))
            else:
                image.save(stream, format='TIFF', compression='tiff_lzw')
            return stream.getvalue()

    return cache.get_or_create(key, render)
