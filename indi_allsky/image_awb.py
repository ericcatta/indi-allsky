"""Shared numerical AWB operation for capture and archived source rendering."""
import numpy


def apply_rgb_gains(image, red_gain, blue_gain):
    corrected_image = image.astype(numpy.float32, copy=True)
    corrected_image[:, :, 0] *= blue_gain
    corrected_image[:, :, 2] *= red_gain

    if numpy.issubdtype(image.dtype, numpy.integer):
        max_value = numpy.iinfo(image.dtype).max
        corrected_image = numpy.clip(corrected_image, 0, max_value).astype(image.dtype)
    elif numpy.issubdtype(image.dtype, numpy.floating):
        finite_max = float(numpy.nanmax(image))
        if not numpy.isfinite(finite_max) or finite_max <= 1.5:
            max_value = 1.0
        elif finite_max <= 255.0:
            max_value = 255.0
        elif finite_max <= 65535.0:
            max_value = 65535.0
        else:
            max_value = finite_max

        corrected_image = numpy.clip(corrected_image, 0.0, max_value).astype(image.dtype, copy=False)
    else:
        raise ValueError('Unsupported AWB image dtype')
    return corrected_image
