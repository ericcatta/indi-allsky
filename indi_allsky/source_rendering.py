"""Rebuild an archived frame without capture effects or current live metadata.

Ordinary calibrated single frames use FITS pixels directly. Pre-calibration FITS
and multi-frame stacks additionally retain their lossless prepared basis, since
that result cannot be recovered from this exposure alone. Those assets are real
archive dependencies, not disposable preview cache.
"""
from copy import deepcopy
from datetime import datetime
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace

import numpy as np

from . import constants
from .fits_context import RENDER_KEYS, RENDER_GROUPS, _json_value
from .image_awb import apply_rgb_gains
from .image_labels import snapshot_label, render_saved_label
from .image_rendering import render_tone, render_geometry_and_color
from .image_presentation import render_saved_presentation
from .render_asset_lifecycle import source_render_lease

EXTRA_KEYS = frozenset('''
FOCUS_MODE DETECT_DRAW DETECT_METEORS DETECT_STARS
ADU_ROI ADU_FOV_DIV SQM_ROI SQM_FOV_DIV
SCNR_AMOUNT SCNR_MTF_MIDTONES SCNR_MTF_MIDTONES_DAY
DENOISE_PROTECT_STARS DENOISE_STAR_PERCENTILE DENOISE_STAR_SIGMA
DENOISE_STAR_FWHM DENOISE_STAR_PROTECT_RADIUS DENOISE_MAX_LUM_GAIN DENOISE_MIN_LUM_GAIN
ADAPTIVE_BLEND BILATERAL_BLEND BILATERAL_SCALE_EXP BILATERAL_SCALE_FACTOR
BILATERAL_SIGMA_COLOR BILATERAL_SIGMA_SPACE GAUSSIAN_BLEND GAUSSIAN_SIGMA
LOCAL_STATS_KSIZE MEDIAN_BLEND WAVELET_BLEND WAVELET_MIN_SIGMA WAVELET_SCALE
EXPOSURE_PERIOD EXPOSURE_PERIOD_DAY
'''.split())
STRETCH_KEYS = RENDER_GROUPS['IMAGE_STRETCH'] + (
    'DAYTIME', 'MOONMODE', 'MODE3_BLACK_CLIP', 'MODE3_SHADOWS',
    'MODE3_MIDTONES', 'MODE3_HIGHLIGHTS',
)


def file_digest(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def pixel_digest(image):
    image = np.ascontiguousarray(image)
    digest = hashlib.sha256(json.dumps([image.dtype.str, image.shape]).encode())
    digest.update(memoryview(image).cast('B'))
    return digest.hexdigest()


def _settings(config):
    result = {}
    for key in sorted((RENDER_KEYS | EXTRA_KEYS).intersection(config)):
        # Labels are already formatted. Do not retain templates/custom paths.
        if key == 'IMAGE_LABEL_TEMPLATE':
            continue
        value = config[key]
        if key in RENDER_GROUPS:
            keys = STRETCH_KEYS if key == 'IMAGE_STRETCH' else RENDER_GROUPS[key]
            result[key] = {k: _json_value(value[k]) for k in keys if k in value}
        else:
            result[key] = _json_value(value)
    return result


def snapshot_source_basis(processor, source, assets):
    """Call immediately after stacking, before AWB and tone alter the pixels."""
    p = processor
    ref = p.getLatestImage()
    pre_calibration = bool(p.config.get('IMAGE_SAVE_FITS_PRE_DARK'))
    stacked = not p.focus_mode and len([r for r in p.image_list if r is not None]) > 1
    checkpoint = pre_calibration or stacked
    return {
        'version': 1, 'source_id': source['db_id'],
        'source_sha256': file_digest(source['path']),
        'camera_id': int(ref.camera_id), 'camera_uuid': str(ref.camera_uuid),
        'exposure_date': ref.exp_date.isoformat(), 'exposure': float(ref.exposure),
        'gain': float(ref.gain), 'binning': int(ref.binning),
        'night': bool(p.night_av[constants.NIGHT_NIGHT]),
        'moonmode': bool(p.night_av[constants.NIGHT_MOONMODE]),
        'image_bitpix': ref.image_bitpix, 'image_bayerpat': ref.image_bayerpat,
        'max_bit_depth': p.max_bit_depth, 'libcamera_raw': p.libcamera_raw,
        'prepared_shape': list(p.image.shape),
        'prepared_asset': assets.put(pixels=p.image) if checkpoint else None,
        'prepared_reason': ('pre_calibration_and_stack' if pre_calibration and stacked
                            else 'pre_calibration' if pre_calibration else 'stack' if stacked else None),
    }


def snapshot_source_recipe(processor, basis, presentation, assets, *, ccm=None):
    """Complete a recipe after the formatted label has actually been painted."""
    p = processor
    ref = p.getLatestImage()
    if basis['camera_id'] != ref.camera_id or basis['exposure_date'] != ref.exp_date.isoformat():
        raise ValueError('Source basis belongs to another exposure')
    binning = ref.binning
    mask = p._detection_mask_dict.get(binning)
    circle = p._image_circle_alpha_mask_dict.get(binning)
    lookups = {}
    for key, value in (('gamma', p._gamma_lut), ('wbb', p._wbb_mtf_lut),
                       ('wbg', p._wbg_mtf_lut), ('wbr', p._wbr_mtf_lut),
                       ('scnr', p._ia_scnr._mtf_lut),
                       ('stretch', getattr(p._stretch_o, '_mtf_lut', None))):
        if value is not None:
            lookups[key] = value
    mask_key = (binning, basis['prepared_shape'][1], basis['prepared_shape'][0])
    stretch_mask = getattr(p._stretch_o, '_numpy_mask_dict', {}).get(mask_key)
    stretch_state = {name: _json_value(getattr(p._stretch_o, name)) for name in (
        'gamma', 'stddevs', 'shadows', 'midtones', 'highlights', 'black_clip',
        'stride', 'scale_factor', 'operation_count') if hasattr(p._stretch_o, name)}
    label = snapshot_label(p)
    label['style']['PIL_FONT_CUSTOM'] = ''
    record = {
        'version': 1, 'basis': deepcopy(basis), 'settings': _settings(p.config),
        'awb_gains': deepcopy(getattr(p, 'render_awb_gains', None)),
        'ccm': None if ccm is None else np.asarray(ccm).tolist(),
        'denoise_star_time': getattr(p._ia_denoise, 'last_star_mask_time', None),
        'lookups': assets.put(**lookups) if lookups else None,
        'wb_mtf_night': p._wb_mtf_night, 'scnr_night': p._ia_scnr.night,
        'stretch_state': stretch_state,
        'stretch_mask': None if stretch_mask is None else assets.put(pixels=stretch_mask),
        'detection_mask': None if mask is None else assets.put(pixels=mask),
        'circle_mask': None if circle is None else assets.put(pixels=circle),
        'lines': np.asarray(ref.lines).tolist(), 'stars': np.asarray(ref.stars).tolist(),
        'presentation': deepcopy(presentation), 'label': label,
        'pixels_sha256': pixel_digest(p.image),
        'jpeg_quality': int(p.config['IMAGE_FILE_COMPRESSION']['jpg']),
    }
    # Ensure database/portable serialization cannot quietly change numeric values.
    return json.loads(json.dumps(record, allow_nan=False))


@source_render_lease
def render_source(path, recipe, assets, *, camera_id, source_id):
    """Return display pixels; leave the source, database and live providers untouched.

    The caller resolves/authorizes the source and assets. Explicit identities and
    content checks prevent a valid recipe being paired with a different exposure.
    No fallback to current processing parameters or current resource files occurs.
    """
    from astropy.io import fits
    from .config import IndiAllSkyConfigBase
    from .processing import ImageProcessor

    if recipe.get('version') != 1 or recipe.get('basis', {}).get('version') not in (1, 2):
        raise ValueError('Unsupported source rendering recipe')
    basis = recipe['basis']
    if basis['camera_id'] != camera_id or basis['source_id'] != source_id:
        raise ValueError('Source recipe identity mismatch')
    from .source_publication import scientific_digest
    integrity = (file_digest(path) == basis['source_sha256'] if basis['version'] == 1
                 else scientific_digest(path) == basis['scientific_sha256'])
    if not integrity:
        raise ValueError('Source content differs from the archived exposure')
    config = deepcopy(IndiAllSkyConfigBase().base_config)
    # Defaults supply infrastructure-only constructor keys. Rendering values are
    # frozen by the recipe; current user settings are never loaded.
    for key in RENDER_KEYS | EXTRA_KEYS:
        config.pop(key, None)
    config.update(deepcopy(recipe['settings']))
    config['TEXT_PROPERTIES'] = deepcopy(recipe['presentation']['config']['values']['TEXT_PROPERTIES'])
    config['DETECT_MASK'] = ''
    night = [int(basis['night']), int(basis['moonmode'])]
    binning = basis['binning']
    p = ImageProcessor(config, [0.0]*5, [basis['gain']], [binning],
                       [0.0]*60, [0.0]*110, night, [0.0]*3)
    mask = None if recipe['detection_mask'] is None else assets.get(recipe['detection_mask'])['pixels']
    p.post_init(detection_mask={binning: mask})
    p.max_bit_depth = basis['max_bit_depth']
    p.libcamera_raw = basis['libcamera_raw']
    lookups = {} if recipe['lookups'] is None else assets.get(recipe['lookups'])
    p._gamma_lut = lookups.get('gamma')
    for key in ('wbb', 'wbg', 'wbr'):
        setattr(p, '_' + key + '_mtf_lut', lookups.get(key))
    p._wb_mtf_night = recipe['wb_mtf_night']
    p._ia_scnr._mtf_lut = lookups.get('scnr')
    p._ia_scnr.night = recipe['scnr_night']
    if p._stretch_o is not None:
        if 'stretch' in lookups:
            p._stretch_o._mtf_lut = lookups['stretch']
        for name, value in recipe['stretch_state'].items():
            setattr(p._stretch_o, name, value)
        if recipe['stretch_mask'] is not None:
            key = (binning, basis['prepared_shape'][1], basis['prepared_shape'][0])
            p._stretch_o._numpy_mask_dict[key] = assets.get(recipe['stretch_mask'])['pixels']
    p._ia_denoise.star_mask_time_override = recipe['denoise_star_time']
    # None means denoise did not consult this gate. Still never consult today's
    # clock during archival replay; algorithms not using it are unaffected.
    if p._ia_denoise.star_mask_time_override is None:
        p._ia_denoise.star_mask_time_override = False
    with fits.open(path, memmap=False) as source:
        # Copy the scientific array; float FITS conversion can modify it in-place.
        hdus = fits.HDUList([fits.PrimaryHDU(source[0].data.copy(), source[0].header.copy())])
    ref = SimpleNamespace(hdulist=hdus, image_bitpix=hdus[0].header['BITPIX'],
        image_bayerpat=basis['image_bayerpat'], binning=binning,
        exp_date=datetime.fromisoformat(basis['exposure_date']))
    p.image_list = [ref]
    try:
        if basis['prepared_asset']:
            ref.image_bitpix = basis['image_bitpix']
            p.image = assets.get(basis['prepared_asset'])['pixels']
        else:
            p.debayer()
            p.image = ref.opencv_data
        if recipe['awb_gains'] is not None:
            p.image = apply_rgb_gains(p.image, *recipe['awb_gains'])
        if recipe['ccm'] is not None:
            p.apply_color_correction_matrix(recipe['ccm'])
        render_tone(p, config, night)
        if config.get('DETECT_DRAW') and not p.focus_mode:
            # Paint the detections actually found during acquisition, in order.
            p._lineDetect._drawLines(p.image, recipe['lines'])
            p._stars_detect._drawCircles(p.image, recipe['stars'])
            p.drawDetections()
        render_geometry_and_color(p, config, night)
        p.colormap()
        if recipe['circle_mask'] is not None:
            p._image_circle_alpha_mask_dict[binning] = assets.get(recipe['circle_mask'])['pixels']
        p.apply_image_circle_mask(binning)
        render_saved_presentation(p, recipe['presentation'], assets)
        label = deepcopy(recipe['label'])
        font = recipe['presentation']['config']['font']
        if font:
            label['style'].update(PIL_FONT_FILE='custom', PIL_FONT_CUSTOM=str(assets.font_path(font)))
        render_saved_label(p, label)
        if pixel_digest(p.image) != recipe['pixels_sha256']:
            raise ValueError('Source replay differs from the recorded display pixels')
        return p.image
    finally:
        hdus.close()
