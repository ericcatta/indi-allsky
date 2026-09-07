"""Hybrid presentation of recorded sensor readings, without fabricated defaults."""
import math


def build_sensor_rows(camera_data, image_data):
    labels = camera_data if isinstance(camera_data, dict) else {}
    readings = image_data if isinstance(image_data, dict) else {}
    groups = {}
    for group in ('user', 'temp'):
        rows = []
        for index in range(60):
            key = f'sensor_{group}_{index}'
            label = labels.get(key) or key
            raw = readings.get(key)
            value = raw if isinstance(raw, (str, int, float)) and not isinstance(raw, bool) else None
            if isinstance(value, float) and not math.isfinite(value):
                value = None
            configured = label not in (key, f'User Slot {index}') and not str(label).startswith('Future Use')
            rows.append({'slot': key, 'label': str(label), 'value': value,
                         'used': configured or value is not None or (index < 10 if group == 'user' else index == 0)})
        groups[group] = rows
    return groups
