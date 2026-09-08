"""Smoke status presentation; unavailable readings must not appear fresh."""
import math
import time
from collections.abc import Mapping
from . import constants


def build_smoke_status(camera_data, now=None):
    data = camera_data if isinstance(camera_data, Mapping) else {}
    now = time.time() if now is None else now
    rating = data.get('SMOKE_RATING')
    label = constants.SMOKE_RATING_MAP_STR.get(rating, 'No data') if type(rating) in (int, float) else 'No data'
    status = data.get('SMOKE_UPDATE_STATUS')
    state = status.get('state') if isinstance(status, Mapping) else None
    if state == 'unavailable':
        freshness = '[update failed]'
    elif state == 'not_covered':
        label, freshness = 'No data', '[outside provider coverage]'
    elif label == 'No data':
        freshness = ''
    else:
        try:
            timestamp = float(data.get('SMOKE_DATA_TS'))
            if isinstance(data.get('SMOKE_DATA_TS'), bool) or not math.isfinite(timestamp) or timestamp <= 0 or timestamp > now:
                raise ValueError('Unknown timestamp')
            freshness = '[old]' if timestamp < now - 86400 else ''
        except (TypeError, ValueError, OverflowError):
            freshness = '[age unknown]'
    return {'smoke_rating': label, 'smoke_rating_status': freshness}
