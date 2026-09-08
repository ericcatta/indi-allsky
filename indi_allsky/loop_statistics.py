"""Hybrid statistics for optional measurements attached to loop images."""
from collections.abc import Mapping
from math import isfinite
from numbers import Real


def measurement_summary(values):
    """Ignore invalid samples; retain the public API's existing empty shape."""
    samples = [value for value in values
               if isinstance(value, Real) and not isinstance(value, bool) and isfinite(value)]
    if not samples:
        return dict(max=0.0, min=0.0, avg=0.0, last=0.0)
    return dict(max=max(samples), min=min(samples), avg=sum(samples) / len(samples), last=samples[0])


def loop_sqm_summaries(images):
    samples = ([], [], [], [])
    for image in images:
        # Panorama models have no SQM attribute; retain their legacy zero value.
        samples[0].append(getattr(image, 'sqm', 0))
        data = image.data if isinstance(image.data, Mapping) else {}
        for values, key in zip(samples[1:], ('sensor_user_8', 'sensor_user_9', 'sensor_user_7')):
            values.append(data.get(key, 0.0))
    return tuple(measurement_summary(values) for values in samples)
