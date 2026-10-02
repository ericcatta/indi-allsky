"""Portable acquisition context in FITS, without image mutation or credentials.

This records the context at source-save time, not a complete replay recipe: later
stack/AWB, detections and formatted labels must be captured separately before a
source can replace its processed archive image.
"""
import json
import math
from datetime import date, datetime
from numbers import Integral, Real

EXTENSION = 'HYBRID_CTX'
VERSION = 1
MAX_BYTES = 1024 * 1024

# Deliberately explicit: never archive the full configuration (upload passwords,
# API tokens, hooks and connection settings have no place in a downloadable FITS).
RENDER_KEYS = frozenset('''
AUTO_WB AUTO_WB_DAY CCD_BIT_DEPTH CFA_PATTERN CLAHE_CLIPLIMIT CLAHE_GRIDSIZE
CONTRAST_ENHANCE_16BIT DAYTIME_CONTRAST_ENHANCE NIGHT_CONTRAST_ENHANCE
DAYTIME_GRAYSCALE NIGHT_GRAYSCALE GAMMA_CORRECTION GAMMA_CORRECTION_DAY
IMAGE_ALIGN_DETECTSIGMA IMAGE_ALIGN_POINTS IMAGE_ALIGN_SOURCEMINAREA
IMAGE_BORDER IMAGE_CALIBRATE_BPM IMAGE_CALIBRATE_DARK IMAGE_CALIBRATE_FIX_HOLES
IMAGE_CALIBRATE_HOLE_THOLD IMAGE_CALIBRATE_MANUAL_OFFSET IMAGE_CIRCLE_MASK
IMAGE_COLORMAP IMAGE_CROP_IMAGE_CIRCLE IMAGE_CROP_ROI IMAGE_DENOISE IMAGE_DENOISE_DAY
IMAGE_DENOISE_STRENGTH IMAGE_DENOISE_STRENGTH_DAY
IMAGE_FLIP_H IMAGE_FLIP_V IMAGE_LABEL_SYSTEM IMAGE_LABEL_TEMPLATE IMAGE_ROTATE
IMAGE_ROTATE_ANGLE IMAGE_ROTATE_KEEP_SIZE IMAGE_SCALE IMAGE_STACK_ALIGN
IMAGE_STACK_COUNT IMAGE_STACK_DAY IMAGE_STACK_METHOD IMAGE_STACK_MOONMODE
IMAGE_STACK_SPLIT IMAGE_STRETCH LENS_IMAGE_CIRCLE LENS_OFFSET_X LENS_OFFSET_Y
SATURATION_FACTOR SATURATION_FACTOR_DAY SCNR_ALGORITHM SCNR_ALGORITHM_DAY
SHARPEN_AMOUNT SHARPEN_AMOUNT_DAY TEMP_DISPLAY USE_NIGHT_COLOR
WBB_FACTOR WBB_FACTOR_DAY WBB_MTF_MIDTONES WBG_FACTOR WBG_FACTOR_DAY WBG_MTF_MIDTONES
WBR_FACTOR WBR_FACTOR_DAY WBR_MTF_MIDTONES
'''.split())
# Select nested values too: an unknown/extension key must never leak accidentally.
RENDER_GROUPS = {
    'IMAGE_BORDER': ('TOP', 'BOTTOM', 'LEFT', 'RIGHT', 'COLOR'),
    'IMAGE_CIRCLE_MASK': ('ENABLE', 'DIAMETER', 'OFFSET_X', 'OFFSET_Y', 'BLUR', 'OPACITY', 'OUTLINE'),
    'IMAGE_STRETCH': ('CLASSNAME', 'MODE1_GAMMA', 'MODE1_STDDEVS', 'MODE2_SHADOWS', 'MODE2_MIDTONES', 'MODE2_HIGHLIGHTS', 'SPLIT'),
}


def _json_value(value):
    if value is None or isinstance(value, (str, bool)):
        return value
    if isinstance(value, Integral):
        return int(value)
    if isinstance(value, Real):
        return float(value) if math.isfinite(value) else None
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    if isinstance(value, (list, tuple)):
        return [_json_value(v) for v in value]
    raise ValueError('Unsupported FITS context value type')


def capture_context(config, ref, *, profile_id, night, moonmode):
    settings = {}
    for key in sorted(RENDER_KEYS.intersection(config)):
        value = config[key]
        if key in RENDER_GROUPS and isinstance(value, dict):
            settings[key] = {k: _json_value(value[k]) for k in RENDER_GROUPS[key] if k in value}
        else:
            settings[key] = _json_value(value)
    offset = ref.exp_date.utcoffset()
    if offset is None:
        offset = ref.exp_date.astimezone().utcoffset()
    return {
        'version': VERSION,
        'stage': 'pre_calibration' if config.get('IMAGE_SAVE_FITS_PRE_DARK') else 'post_calibration',
        'camera_id': int(ref.camera_id), 'camera_uuid': str(ref.camera_uuid),
        'profile_id': str(profile_id), 'exposure_time': ref.exp_date.isoformat(),
        'utc_offset_seconds': offset.total_seconds(),
        'exposure_seconds': _json_value(ref.exposure), 'gain': _json_value(ref.gain),
        'binning': int(ref.binning), 'night': bool(night), 'moonmode': bool(moonmode),
        'calibrated': bool(getattr(ref, 'calibrated', False)),
        'rendering_settings': settings,
        'complete_render_recipe': False,
    }


def with_context(hdulist, context):
    """Return a write-only HDU list sharing pixels; do not mutate/close the input."""
    import numpy as np
    from astropy.io import fits
    payload = json.dumps(context, sort_keys=True, separators=(',', ':'), allow_nan=False).encode('utf-8')
    if len(payload) > MAX_BYTES:
        raise ValueError('FITS context exceeds its size limit')
    extension = fits.ImageHDU(np.frombuffer(payload, dtype=np.uint8).copy(), name=EXTENSION)
    extension.header['CTXVER'] = VERSION
    return fits.HDUList([hdu for hdu in hdulist if hdu.name != EXTENSION] + [extension])


def _reject_nonfinite(token):
    raise ValueError('Non-finite JSON number')


def read_context(hdulist):
    """Read an optional context from an already open FITS without touching pixels."""
    matches = [h for h in hdulist if h.name == EXTENSION]
    if not matches:
        return None
    if len(matches) != 1:
        raise ValueError('Ambiguous FITS context')
    hdu = matches[0]
    if hdu.header.get('CTXVER') != VERSION:
        raise ValueError('Unsupported FITS context version')
    # Bound before loading data; opening a scientific image must not imply loading it.
    if hdu.header.get('BITPIX') != 8 or hdu.header.get('NAXIS') != 1 or not 0 < hdu.header.get('NAXIS1', 0) <= MAX_BYTES:
        raise ValueError('Invalid FITS context shape or size')
    try:
        value = json.loads(hdu.data.tobytes().decode('utf-8'),
                           parse_constant=_reject_nonfinite)
    except (ValueError, UnicodeError, AttributeError, RecursionError) as exc:
        raise ValueError('Invalid FITS context JSON') from exc
    if not isinstance(value, dict) or value.get('version') != VERSION:
        raise ValueError('Unsupported FITS context payload')
    return value
