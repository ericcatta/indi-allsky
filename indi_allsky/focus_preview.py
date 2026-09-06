"""Focus image decoding and measurement shared by Hybrid and compatibility APIs."""
import base64


def load_focus_image(path):
    import cv2
    import numpy
    if path.suffix.lower() in ('.jpg', '.jpeg'):
        import simplejpeg
        return simplejpeg.decode_jpeg(path.read_bytes(), colorspace='BGR')
    if path.suffix.lower() == '.png':
        data = cv2.imread(str(path), cv2.IMREAD_COLOR)
        if data is None:
            raise ValueError('Unreadable PNG')
        return data
    if path.suffix.lower() in ('.fit', '.fits'):
        from astropy.io import fits
        with fits.open(path) as hdus:
            data = numpy.array(hdus[0].data, copy=True)
        if data.ndim == 2:
            return cv2.cvtColor(data, cv2.COLOR_GRAY2BGR)
        if data.ndim != 3 or data.shape[0] != 3:
            raise ValueError('Unsupported FITS focus image shape')
        data = numpy.swapaxes(numpy.swapaxes(data, 0, 2), 0, 1)
        return cv2.cvtColor(data, cv2.COLOR_RGB2BGR)
    from PIL import Image
    with Image.open(path) as image:
        return cv2.cvtColor(numpy.array(image.convert('RGB')), cv2.COLOR_RGB2BGR)


def focus_preview(image_data, config, *, zoom=2, x_offset=0, y_offset=0):
    import cv2
    from .stars import IndiAllSkyStars
    if zoom < 2 or zoom > 100:
        raise ValueError('Zoom must be between 2 and 100')
    height, width = image_data.shape[:2]
    x1 = int((width / 2) - (width / zoom) + x_offset)
    y1 = int((height / 2) - (height / zoom) - y_offset)
    x2 = int((width / 2) + (width / zoom) + x_offset)
    y2 = int((height / 2) + (height / zoom) - y_offset)
    # Negative NumPy indices would wrap into another region of the source.
    if not (0 <= x1 < x2 <= width and 0 <= y1 < y2 <= height):
        raise ValueError('Focus region lies outside the image')
    stars = IndiAllSkyStars(config, mask={1: None}).detectObjects(image_data, 1)
    roi = image_data[y1:y2, x1:x2]
    success, encoded = cv2.imencode('.jpg', roi, [cv2.IMWRITE_JPEG_QUALITY, 90])
    if not success:
        raise ValueError('Focus JPEG encoding failed')
    return {
        'focus_mode': config.get('FOCUS_MODE', False),
        'image_b64': base64.b64encode(encoded.tobytes()).decode('utf-8'),
        'blur_score': float(cv2.Laplacian(roi, cv2.CV_32F).var()),
        'star_count': len(stars),
    }
