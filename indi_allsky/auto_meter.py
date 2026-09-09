import logging
from dataclasses import dataclass

import cv2
import numpy


logger = logging.getLogger('indi_allsky')


AUTO_EXPOSURE_METERING_MODES = {
    'default',
    'average',
    'median',
    'sigma_clipped',
    'background',
    'moon_aware',
    'stars_only',
    'highlight_protected',
}

DEFAULT_AUTO_EXPOSURE_METERING_MODE = 'default'
DEFAULT_METERING_STRATEGY = 'moon_aware'


@dataclass(frozen=True)
class MeteringResult:
    mode: str
    strategy: str
    measured_value: float
    sample_count: int
    excluded_pixels: int
    status: str = 'ok'
    highlight_saturated: bool = False


class MeteringStrategy:
    name = 'default'

    def measure(self, luminance):
        samples = luminance[numpy.isfinite(luminance)]
        if samples.size == 0:
            return MeteringResult(self.name, self.name, 0.0, 0, int(luminance.size), status='no_samples')

        return MeteringResult(self.name, self.name, float(numpy.mean(samples)), int(samples.size), 0)


class AverageMeter(MeteringStrategy):
    name = 'average'

    def measure(self, luminance):
        samples = luminance[numpy.isfinite(luminance)]
        if samples.size == 0:
            return MeteringResult(self.name, self.name, 0.0, 0, int(luminance.size), status='no_samples')

        return MeteringResult(self.name, self.name, float(numpy.mean(samples)), int(samples.size), 0)


class MedianMeter(MeteringStrategy):
    name = 'median'

    def measure(self, luminance):
        samples = luminance[numpy.isfinite(luminance)]
        if samples.size == 0:
            return MeteringResult(self.name, self.name, 0.0, 0, int(luminance.size), status='no_samples')

        return MeteringResult(self.name, self.name, float(numpy.median(samples)), int(samples.size), 0)


class SigmaClippedMeter(MeteringStrategy):
    name = 'sigma_clipped'

    def measure(self, luminance):
        samples = luminance[numpy.isfinite(luminance)]
        if samples.size == 0:
            return MeteringResult(self.name, self.name, 0.0, 0, int(luminance.size), status='no_samples')

        mean = float(numpy.mean(samples))
        stddev = float(numpy.std(samples))
        if stddev <= 0.0:
            return MeteringResult(self.name, self.name, mean, int(samples.size), 0)

        clipped = samples[numpy.abs(samples - mean) <= (2.5 * stddev)]
        if clipped.size == 0:
            return MeteringResult(self.name, self.name, mean, int(samples.size), 0, status='clip_empty')

        return MeteringResult(
            self.name,
            self.name,
            float(numpy.mean(clipped)),
            int(clipped.size),
            int(samples.size - clipped.size),
        )


class BackgroundMeter(MeteringStrategy):
    name = 'background'

    def measure(self, luminance):
        samples = luminance[numpy.isfinite(luminance)]
        if samples.size == 0:
            return MeteringResult(self.name, self.name, 0.0, 0, int(luminance.size), status='no_samples')

        low, high = numpy.percentile(samples, [10.0, 70.0])
        background = samples[(samples >= low) & (samples <= high)]
        if background.size == 0:
            return MeteringResult(self.name, self.name, float(numpy.median(samples)), int(samples.size), 0, status='background_empty')

        return MeteringResult(
            self.name,
            self.name,
            float(numpy.median(background)),
            int(background.size),
            int(samples.size - background.size),
        )


class MoonAwareMeter(MeteringStrategy):
    name = 'moon_aware'

    def measure(self, luminance):
        samples = luminance[numpy.isfinite(luminance)]
        if samples.size == 0:
            return MeteringResult(self.name, self.name, 0.0, 0, int(luminance.size), status='no_samples')

        high_cut = numpy.percentile(samples, 97.0)
        clipped = samples[samples <= high_cut]
        if clipped.size == 0:
            return MeteringResult(self.name, self.name, float(numpy.median(samples)), int(samples.size), 0, status='moon_clip_empty')

        background_high = numpy.percentile(clipped, 75.0)
        background = clipped[clipped <= background_high]
        if background.size == 0:
            background = clipped

        return MeteringResult(
            self.name,
            self.name,
            float(numpy.median(background)),
            int(background.size),
            int(samples.size - background.size),
        )


class StarsOnlyMeter(MeteringStrategy):
    name = 'stars_only'

    def measure(self, luminance):
        samples = luminance[numpy.isfinite(luminance)]
        if samples.size == 0:
            return MeteringResult(self.name, self.name, 0.0, 0, int(luminance.size), status='no_samples')

        star_floor = numpy.percentile(samples, 97.5)
        stars = samples[samples >= star_floor]
        if stars.size == 0:
            return MeteringResult(self.name, self.name, 0.0, 0, int(samples.size), status='stars_empty')

        return MeteringResult(
            self.name,
            self.name,
            float(numpy.median(stars)),
            int(stars.size),
            int(samples.size - stars.size),
        )


class HighlightProtectedMeter(MeteringStrategy):
    name = 'highlight_protected'

    def measure(self, luminance):
        return measure_highlights(numpy.atleast_2d(luminance), 75.0)


METERING_STRATEGIES = {
    'highlight_protected': HighlightProtectedMeter(),
    'average': AverageMeter(),
    'median': MedianMeter(),
    'sigma_clipped': SigmaClippedMeter(),
    'background': BackgroundMeter(),
    'moon_aware': MoonAwareMeter(),
    'stars_only': StarsOnlyMeter(),
}


def normalize_metering_mode(mode):
    mode = str(mode or DEFAULT_AUTO_EXPOSURE_METERING_MODE).strip().lower()
    if mode in AUTO_EXPOSURE_METERING_MODES:
        return mode

    logger.warning('Unknown AUTO_EXPOSURE_METERING_MODE %r, using %s', mode, DEFAULT_AUTO_EXPOSURE_METERING_MODE)
    return DEFAULT_AUTO_EXPOSURE_METERING_MODE


def resolve_metering_strategy(mode):
    mode = normalize_metering_mode(mode)
    strategy_name = DEFAULT_METERING_STRATEGY if mode == 'default' else mode
    return METERING_STRATEGIES[strategy_name], mode, strategy_name


def image_to_luminance_8bit(image):
    if len(image.shape) == 2:
        luminance = image.astype(numpy.float32, copy=False)
    else:
        luminance = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY).astype(numpy.float32, copy=False)

    if numpy.issubdtype(image.dtype, numpy.integer):
        dtype_max = float(numpy.iinfo(image.dtype).max)
        if dtype_max > 255.0:
            luminance = luminance * (255.0 / dtype_max)
    else:
        max_value = float(numpy.nanmax(luminance)) if luminance.size else 0.0
        if max_value <= 1.0:
            luminance = luminance * 255.0

    return numpy.clip(luminance, 0.0, 255.0)


def measure_auto_exposure(image, mask=None, mode=DEFAULT_AUTO_EXPOSURE_METERING_MODE,
                          target=75.0, highlight_clip_percent=1.0, bit_depth=None):
    if normalize_metering_mode(mode) == 'highlight_protected':
        return measure_highlights(image, target, highlight_clip_percent, bit_depth)
    strategy, normalized_mode, strategy_name = resolve_metering_strategy(mode)
    luminance = image_to_luminance_8bit(image)

    if mask is not None:
        mask_bool = mask > 0
        excluded_by_mask = int(mask_bool.size - numpy.count_nonzero(mask_bool))
        luminance = luminance[mask_bool]
    else:
        excluded_by_mask = 0
        luminance = luminance.reshape(-1)

    result = strategy.measure(luminance)
    return MeteringResult(
        normalized_mode,
        strategy_name,
        result.measured_value,
        result.sample_count,
        result.excluded_pixels + excluded_by_mask,
        result.status,
    )


def measure_highlights(image, target, clip_percent=1.0, bit_depth=None):
    """Meter whole-frame channel peaks, allowing a small bright-source budget.

    The percentile is mapped to the controller's existing target units. A
    value of 235/255 leaves headroom; this is an exposure objective, not a
    guarantee that saturated data can be recovered. ROI is deliberately not
    applied in this mode so bright regions outside it are still protected.
    """
    clip_percent = float(clip_percent)
    target = float(target)
    if not numpy.isfinite(clip_percent) or not .01 <= clip_percent <= 10:
        raise ValueError('Highlight pixel budget must be between 0.01 and 10 percent.')
    if not numpy.isfinite(target) or target <= 0:
        raise ValueError('Highlight metering requires a positive target.')
    peaks = image if image.ndim == 2 else numpy.max(image, axis=2)
    if numpy.issubdtype(image.dtype, numpy.integer):
        depth = numpy.iinfo(image.dtype).bits if bit_depth is None else int(bit_depth)
        if not 1 <= depth <= numpy.iinfo(image.dtype).bits:
            raise ValueError('Invalid source bit depth.')
        peaks = peaks.astype(numpy.float32) * (255.0 / ((1 << depth) - 1))
    else:
        peaks = image_to_luminance_8bit(peaks)
    samples = peaks[numpy.isfinite(peaks)]
    if not samples.size:
        raise ValueError('No valid pixels for highlight metering.')
    percentile = float(numpy.percentile(samples, 100.0 - clip_percent))
    return MeteringResult('highlight_protected', 'highlight_protected',
                         percentile * target / 235.0, int(samples.size),
                         int(peaks.size - samples.size),
                         highlight_saturated=percentile >= 250.0)
