### Mode 3 stretch is the Midtone Transfer Function based on PixInsight and Siril
###
### https://pixinsight.com/forum/index.php?threads/auto-histogram-settings-to-replicate-auto-stf.8205/#post-55143
### https://siril.readthedocs.io/en/latest/processing/stretching.html

import time
import numpy
import logging

from .stretchBase import IndiAllSky_Stretch_Base

logger = logging.getLogger('indi_allsky')


class IndiAllSky_Mode3_Adaptive_MTF_Stretch(IndiAllSky_Stretch_Base):

    def __init__(self, *args, **kwargs):
        super(IndiAllSky_Mode3_Adaptive_MTF_Stretch, self).__init__(*args, **kwargs)

        self.black_clip = self.config.get('IMAGE_STRETCH', {}).get('MODE3_BLACK_CLIP', -2.8)
        self.shadows = self.config.get('IMAGE_STRETCH', {}).get('MODE3_SHADOWS', 0.0)
        self.midtones = self.config.get('IMAGE_STRETCH', {}).get('MODE3_MIDTONES', 0.25)
        self.highlights = self.config.get('IMAGE_STRETCH', {}).get('MODE3_HIGHLIGHTS', 1.0)
        # Recipes written before the corrected implementation have no version.
        # Keep their arithmetic byte-for-byte compatible during archival replay.
        self.algorithm_version = int(
            self.config.get('IMAGE_STRETCH', {}).get('MODE3_ALGORITHM_VERSION', 1)
        )

        self.stride = 20
        self.scale_factor = 1.4826


    def stretch(self, data, image_bit_depth, binning):
        if self.algorithm_version >= 2:
            return self._stretch_v2(data, image_bit_depth)

        return self._stretch_legacy(data, image_bit_depth)


    def _stretch_legacy(self, data, image_bit_depth):
        #logger.info('MTF: Shadows - Shadows %0.2f, Midtones %0.2f, Highlights %0.2f', self.shadows, self.midtones, self.highlights)

        stretch_start = time.time()

        if image_bit_depth == 8:
            numpy_dtype = numpy.uint8
        else:
            numpy_dtype = numpy.uint16

        data_max = (2 ** image_bit_depth) - 1
        shadows_val = int(self.shadows * data_max)
        highlights_val = int(self.highlights * data_max)

        if data.shape[0] > self.stride and data.shape[1] > self.stride:
            samples = data[::self.stride, ::self.stride]
        else:
            samples = data

        # these will result in 0.0 to 1.0 normalized values
        samples = (samples / data_max).astype(numpy.float32)
        axis = (0, 1)

        m = numpy.mean(numpy.median(samples, axis=axis)).astype(numpy.float32)
        d = numpy.mean(self._mdev(samples, axis)).astype(numpy.float32)
        c = numpy.clip(m + self.black_clip * self.scale_factor * d, 0.0, 1.0)

        lut = numpy.arange(data_max + 1, dtype=numpy.float32) / data_max

        stretched_lut = self._mtf(self._mtf(self.midtones, m - c), numpy.maximum(0.0, (lut - c) / (1 - c)))
        stretched_lut = stretched_lut * data_max  # scale back to real values
        stretched_lut = self._normalize_to_range(stretched_lut, 0 - shadows_val, data_max + (data_max - highlights_val))
        stretched_lut = numpy.clip(stretched_lut, 0, data_max)
        stretched_lut = stretched_lut.astype(numpy_dtype)

        stretched_image = stretched_lut.take(data, mode='raise')

        stretch_elapsed_s = time.time() - stretch_start
        logger.info('Stretch in %0.4f s', stretch_elapsed_s)

        return stretched_image


    def _stretch_v2(self, data, image_bit_depth):
        """Apply the corrected adaptive MTF without undefined divide results."""
        stretch_start = time.time()

        if not data.size:
            return data.copy()

        if image_bit_depth == 8:
            numpy_dtype = numpy.uint8
        else:
            numpy_dtype = numpy.uint16

        data_max = (2 ** image_bit_depth) - 1
        shadows_val = int(self.shadows * data_max)
        highlights_val = int(self.highlights * data_max)

        if data.shape[0] > self.stride and data.shape[1] > self.stride:
            samples = data[::self.stride, ::self.stride]
        else:
            samples = data

        samples = (samples / data_max).astype(numpy.float32)
        axis = (0, 1)
        channel_median = numpy.median(samples, axis=axis)
        m = float(numpy.mean(channel_median))
        channel_mad = numpy.median(numpy.abs(samples - channel_median), axis=axis)
        d = float(numpy.mean(channel_mad)) * self.scale_factor
        c = float(numpy.clip(m + self.black_clip * d, 0.0, 1.0))

        # A flat frame has no distribution to stretch. Returning the input also
        # makes all-black calibration and synthetic frames deterministic.
        if (
            not numpy.isfinite(m)
            or not numpy.isfinite(d)
            or d <= numpy.finfo(numpy.float32).eps
            or c >= 1.0
            or m <= c
            or not 0.0 < self.midtones < 1.0
        ):
            logger.info('Adaptive MTF v2 skipped for a degenerate distribution')
            return data.copy()

        median_position = (m - c) / (1.0 - c)
        transfer_midtones = self._mtf_v2(self.midtones, median_position)
        if not 0.0 < transfer_midtones < 1.0:
            logger.info('Adaptive MTF v2 skipped for an invalid transfer function')
            return data.copy()

        lut = numpy.arange(data_max + 1, dtype=numpy.float32) / data_max
        normalized = numpy.maximum(0.0, (lut - c) / (1.0 - c))
        stretched_lut = self._mtf_v2(transfer_midtones, normalized) * data_max
        stretched_lut = self._normalize_to_range(
            stretched_lut,
            0 - shadows_val,
            data_max + (data_max - highlights_val),
        )
        stretched_lut = numpy.nan_to_num(
            stretched_lut,
            nan=0.0,
            posinf=float(data_max),
            neginf=0.0,
        )
        stretched_lut = numpy.clip(stretched_lut, 0, data_max).astype(numpy_dtype)
        stretched_image = stretched_lut.take(data, mode='raise')

        stretch_elapsed_s = time.time() - stretch_start
        logger.info('Stretch v2 in %0.4f s', stretch_elapsed_s)
        return stretched_image


    def _mdev(self, data, axis=None):
        med = numpy.median(data, axis=axis)
        mad = numpy.abs(data - med)
        return numpy.median(mad) * self.scale_factor


    def _mtf(self, midtones, data):
        a = (midtones - 1) * data
        b = ((2 * midtones - 1) * data) - midtones
        return numpy.divide(a, b, where=b != 0)


    def _mtf_v2(self, midtones, data):
        values = numpy.asarray(data, dtype=numpy.float32)
        a = (midtones - 1.0) * values
        b = ((2.0 * midtones - 1.0) * values) - midtones
        result = numpy.zeros_like(values, dtype=numpy.float32)
        numpy.divide(a, b, out=result, where=numpy.abs(b) > numpy.finfo(numpy.float32).eps)
        result = numpy.nan_to_num(result, nan=0.0, posinf=1.0, neginf=0.0)
        result = numpy.clip(result, 0.0, 1.0)
        if result.ndim == 0:
            return float(result)

        return result


    def _normalize_to_range(self, a, min_value, max_value):
        a_min = numpy.min(a)
        a_max = numpy.max(a)

        if a_max - a_min == 0:
            return numpy.full_like(a, (a_min + a_max) / 2)

        return ((a - a_min) / (a_max - a_min)) * (max_value - min_value) + min_value
