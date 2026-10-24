#!/usr/bin/env python3
"""Gamma LUT follows live day/night values while frozen replay stays exact."""
import numpy as np

from indi_allsky.processing import ImageProcessor


def processor(image, lut=None, gamma_key=None):
    instance = object.__new__(ImageProcessor)
    instance.image = image.copy()
    instance._gamma_lut = lut
    instance._gamma_lut_gamma = gamma_key
    return instance


source = np.array([[0, 16, 64, 128, 192, 255]], dtype=np.uint8)

# A live processor records the LUT input and rebuilds it when day/night gamma
# changes. Reusing the same value keeps the same immutable lookup object.
live = processor(source)
live._apply_gamma_correction(2.0)
night = live.image.copy()
night_lut = live._gamma_lut
assert live._gamma_lut_gamma == 2.0
live.image = source.copy()
live._apply_gamma_correction(2.0)
assert live._gamma_lut is night_lut
np.testing.assert_array_equal(live.image, night)
live.image = source.copy()
live._apply_gamma_correction(0.5)
assert live._gamma_lut_gamma == 0.5
assert live._gamma_lut is not night_lut
assert not np.array_equal(live.image, night)

# Existing source recipes store the exact LUT but no gamma metadata. None is
# therefore an intentional frozen key: current config must not replace it.
saved_lut = np.arange(255, -1, -1, dtype=np.uint8)
replay = processor(source, lut=saved_lut)
replay._apply_gamma_correction(3.0)
assert replay._gamma_lut is saved_lut
assert replay._gamma_lut_gamma is None
np.testing.assert_array_equal(replay.image, saved_lut.take(source))

print('Gamma LUT cache: live gamma invalidation and metadata-free frozen replay PASS')
