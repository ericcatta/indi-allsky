"""Adapt NOAA's operational RTSW records to the existing solar-wind tables."""
from datetime import datetime, timezone
import math


def normalize_rtsw(data, kind):
    fields = {'mag': ('bt', 'bz_gsm'), 'wind': ('density', 'speed', 'temperature')}[kind]
    if not isinstance(data, list) or not data:
        raise ValueError('Missing RTSW records')
    # Preserve the historical table contract for saved inputs and parity tests.
    if isinstance(data[0], list):
        return data
    samples = {}
    for record in data:
        if not isinstance(record, dict) or record.get('active') is not True or record.get('overall_quality') != 0:
            continue
        try:
            stamp = datetime.fromisoformat(record['time_tag'].replace('Z', '+00:00'))
            if stamp.tzinfo is None:
                stamp = stamp.replace(tzinfo=timezone.utc)
            values = [record[field if kind == 'mag' else 'proton_' + field] for field in fields]
            if any(value is None or isinstance(value, bool) or not math.isfinite(float(value)) for value in values):
                continue
            timestamp = stamp.astimezone(timezone.utc).strftime('%Y-%m-%d %H:%M:%S.%f')
            sample = (record.get('source'), values)
        except (KeyError, TypeError, ValueError, AttributeError):
            continue
        if timestamp in samples and samples[timestamp] != sample:
            raise ValueError('Conflicting active RTSW samples')
        samples[timestamp] = sample
    if not samples:
        raise ValueError('No valid active RTSW records')
    return [['time_tag', *fields], *[[stamp, *samples[stamp][1]] for stamp in sorted(samples)]]
