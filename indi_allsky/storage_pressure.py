"""Storage-pressure policy and observed retention estimates, without effects."""
from dataclasses import dataclass
from datetime import timedelta
import math

GIB = 1024 ** 3


@dataclass(frozen=True)
class StoragePressureOptions:
    enabled: bool = True
    minimum_free_gib: float = 5.0
    target_free_gib: float = 8.0
    keep_days: int = 3

    @classmethod
    def from_config(cls, config):
        values = config.get('STORAGE_PRESSURE', {})
        if not isinstance(values, dict):
            raise ValueError('Storage protection settings must be an object.')
        enabled = values.get('ENABLE', True)
        raw_minimum = values.get('MIN_FREE_GIB', 5.0)
        raw_target = values.get('TARGET_FREE_GIB', 8.0)
        if isinstance(raw_minimum, bool) or isinstance(raw_target, bool):
            raise ValueError('Storage thresholds must be numbers.')
        try:
            minimum, target = float(raw_minimum), float(raw_target)
        except (TypeError, ValueError) as exc:
            raise ValueError('Storage thresholds must be numbers.') from exc
        days = values.get('KEEP_DAYS', 3)
        if not isinstance(enabled, bool):
            raise ValueError('Storage protection must be enabled or disabled.')
        if not all(math.isfinite(x) for x in (minimum, target)) or not 0 < minimum < target:
            raise ValueError('The recovery target must exceed the positive free-space threshold.')
        if isinstance(days, bool) or not isinstance(days, int) or days < 1:
            raise ValueError('Keep at least one complete day of recent images.')
        return cls(enabled, minimum, target, days)

    def needs_cleanup(self, free_bytes):
        return self.enabled and free_bytes < self.minimum_free_gib * GIB

    def cutoff(self, now):
        return now - timedelta(days=self.keep_days)


def retention_estimate(*, free_bytes, stored_image_bytes, observed_bytes,
                       observed_seconds, samples, options):
    """Estimate from a measured window; do not infer a rate from missing data.

    The caller must exclude stale configurations and count each output once.
    Durations describe storage capacity, not a promise of future image sizes.
    """
    if (samples < 2 or observed_seconds < 3600 or observed_bytes <= 0
            or any(not math.isfinite(x) or x < 0 for x in
                   (observed_seconds, observed_bytes, free_bytes, stored_image_bytes))):
        return {'status': 'insufficient_data', 'seconds_to_threshold': None,
                'retained_seconds': None}
    rate = observed_bytes / observed_seconds
    reserve = options.minimum_free_gib * GIB
    return {
        'status': 'estimated',
        'bytes_per_second': rate,
        'sample_seconds': observed_seconds,
        'samples': samples,
        'seconds_to_threshold': max(0, free_bytes - reserve) / rate,
        'retained_seconds': max(0, stored_image_bytes + free_bytes - reserve) / rate,
    }


def reclaim_old_images(*, options, now, free_bytes, candidates, delete,
                       max_files=500, continuing=False):
    """Bounded reclamation using effect adapters supplied by the worker.

    Candidates must be ordered oldest first and have a ``created`` attribute.
    The adapter must protect active jobs and calibration assets. Recheck actual
    free space after each effect; file sizes alone do not prove reclaimed space.
    """
    if isinstance(max_files, bool) or not isinstance(max_files, int) or max_files < 1:
        raise ValueError('Cleanup batch size must be a positive integer.')
    current_free = free_bytes()
    triggered = options.needs_cleanup(current_free) or (
        continuing and options.enabled and current_free < options.target_free_gib * GIB)
    if not triggered:
        return {'status': 'not_needed', 'deleted': 0, 'free_bytes': current_free}
    cutoff = options.cutoff(now)
    count = 0
    previous = None
    for candidate in candidates(cutoff):
        if previous is not None and candidate.created < previous:
            raise ValueError('Cleanup candidates must be ordered oldest first.')
        previous = candidate.created
        if candidate.created >= cutoff:
            break
        # Another process may have recovered space since the previous iteration.
        current_free = free_bytes()
        if current_free >= options.target_free_gib * GIB:
            return {'status': 'recovered', 'deleted': count, 'free_bytes': current_free}
        delete(candidate)
        count += 1
        current_free = free_bytes()
        if current_free >= options.target_free_gib * GIB:
            return {'status': 'recovered', 'deleted': count, 'free_bytes': current_free}
        if count >= max_files:
            return {'status': 'more_work', 'deleted': count, 'free_bytes': current_free}
    return {'status': 'insufficient_old_images', 'deleted': count, 'free_bytes': current_free}
