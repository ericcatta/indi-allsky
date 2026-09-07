"""Read-only aurora status for configured web templates; no provider effects."""
import math
import time
from collections.abc import Mapping


class MissingReading(str):
    """Keep user numeric format specifications usable without inventing zero."""

    def __new__(cls):
        return super().__new__(cls, '—')

    def __format__(self, spec):
        return str(self)


FIELDS = {
    'kpindex': ('kpindex', 'KPINDEX_CURRENT', float),
    'ovation_max': ('ovation', 'OVATION_MAX', int),
    'aurora_mag_bt': ('mag', 'AURORA_MAG_BT', float),
    'aurora_mag_gsm_bz': ('mag', 'AURORA_MAG_GSM_BZ', float),
    'aurora_plasma_density': ('plasma', 'AURORA_PLASMA_DENSITY', float),
    'aurora_plasma_speed': ('plasma', 'AURORA_PLASMA_SPEED', float),
    'aurora_plasma_temp': ('plasma', 'AURORA_PLASMA_TEMP', int),
    'aurora_n_hemi_gw': ('hemi_power', 'AURORA_N_HEMI_GW', int),
    'aurora_s_hemi_gw': ('hemi_power', 'AURORA_S_HEMI_GW', int),
}


def _number(value, convert=float):
    try:
        if value is None or isinstance(value, bool) or not math.isfinite(float(value)):
            return None
        return convert(value)
    except (TypeError, ValueError, OverflowError):
        return None


def build_aurora_status(camera_data, now=None):
    """Use per-feed freshness; legacy records retain their global timestamp."""
    data = camera_data if isinstance(camera_data, Mapping) else {}
    now = time.time() if now is None else now
    components = data.get('AURORA_COMPONENT_STATUS')
    components = components if isinstance(components, Mapping) else {}
    values, states = {}, {}
    for output, (component, source, convert) in FIELDS.items():
        value = _number(data.get(source), convert)
        values[output] = value if value is not None else MissingReading()
        record = components.get(component)
        record = record if isinstance(record, Mapping) else {}
        timestamp = _number(record.get('last_success') if components else data.get('AURORA_DATA_TS'))
        if record.get('state') == 'unavailable':
            state = 'error'
        elif value is None:
            state = 'missing'
        elif (components and record.get('state') != 'available') or timestamp is None or timestamp <= 0 or timestamp > now:
            state = 'unknown'
        elif timestamp < now - 6 * 3600:
            state = 'stale'
        else:
            state = 'available'
        # Every required measurement in a component must be valid.
        priority = {'available': 0, 'stale': 1, 'unknown': 2, 'missing': 3, 'error': 4}
        if priority[state] >= priority.get(states.get(component), -1):
            states[component] = state

    labels = {'available': '', 'stale': '[old]', 'unknown': '[age unknown]',
              'missing': 'No data', 'error': '[update failed]'}
    summary = set(states.values())
    if summary == {'available'}:
        status = ''
    elif len(summary) == 1:
        status = labels[next(iter(summary))]
    else:
        status = '[partial: ' + '; '.join(name + ' ' + labels[state]
                                         for name, state in states.items() if state != 'available') + ']'
    values.update(aurora_data_status=status, kpindex_status=labels[states['kpindex']],
                  ovation_max_status=labels[states['ovation']], kpindex_trend='', kpindex_rating='')
    if states['kpindex'] == 'available':
        coef = _number(data.get('KPINDEX_COEF'))
        if coef:
            values['kpindex_trend'] = '&nearr;' if coef >= 2 else '&searr;' if coef <= 0.5 else '&rarr;'
        kp = values['kpindex']
        if 0 < kp < 5:
            values['kpindex_rating'] = '<span class="text-secondary">LOW</span>'
        elif 5 <= kp < 6:
            values['kpindex_rating'] = '<span class="text-warning">MEDIUM</span>'
        elif 6 <= kp < 8:
            values['kpindex_rating'] = '<span class="text-danger">HIGH</span>'
        elif kp >= 8:
            values['kpindex_rating'] = '<span class="text-danger">VERY HIGH</span>'
        elif kp < 0:
            values['kpindex_rating'] = 'ERROR'
    return values
