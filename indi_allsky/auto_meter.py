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


METERING_STRATEGIES = {
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


def measure_auto_exposure(image, mask=None, mode=DEFAULT_AUTO_EXPOSURE_METERING_MODE):
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
