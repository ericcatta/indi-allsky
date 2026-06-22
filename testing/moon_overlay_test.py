import sys
from pathlib import Path

import numpy

try:
    import cv2
except ModuleNotFoundError:
    print('moon overlay tests skipped: cv2 not installed')
    sys.exit(0)

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from indi_allsky.overlay.moonOverlay import IndiAllSkyMoonOverlay


def _mask():
    return numpy.zeros((64, 64, 3), dtype=numpy.uint8)


def test_safe_ellipse_skips_negative_axes():
    mask = _mask()

    result = IndiAllSkyMoonOverlay._safe_ellipse(
        img=mask.copy(),
        center=(32, 32),
        axes=(20, -5),
        angle=270,
        startAngle=0,
        endAngle=360,
        color=(255, 255, 255),
        thickness=cv2.FILLED,
    )

    assert numpy.array_equal(result, mask)


def test_safe_ellipse_skips_invalid_thickness():
    mask = _mask()

    result = IndiAllSkyMoonOverlay._safe_ellipse(
        img=mask.copy(),
        center=(32, 32),
        axes=(20, 10),
        angle=270,
        startAngle=0,
        endAngle=360,
        color=(255, 255, 255),
        thickness=0,
    )

    assert numpy.array_equal(result, mask)


def test_safe_ellipse_skips_invalid_shift():
    mask = _mask()

    result = IndiAllSkyMoonOverlay._safe_ellipse(
        img=mask.copy(),
        center=(32, 32),
        axes=(20, 10),
        angle=270,
        startAngle=0,
        endAngle=360,
        color=(255, 255, 255),
        thickness=cv2.FILLED,
        shift=17,
    )

    assert numpy.array_equal(result, mask)


def test_safe_ellipse_draws_valid_ellipse():
    mask = _mask()

    result = IndiAllSkyMoonOverlay._safe_ellipse(
        img=mask.copy(),
        center=(32, 32),
        axes=(20, 10),
        angle=270,
        startAngle=0,
        endAngle=360,
        color=(255, 255, 255),
        thickness=cv2.FILLED,
    )

    assert int(result.sum()) > 0


if __name__ == '__main__':
    test_safe_ellipse_skips_negative_axes()
    test_safe_ellipse_skips_invalid_thickness()
    test_safe_ellipse_skips_invalid_shift()
    test_safe_ellipse_draws_valid_ellipse()
    print('moon overlay tests OK')
