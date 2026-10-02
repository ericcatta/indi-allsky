"""Snapshot and replay presentation overlays with immutable assets and clocks.

This operates on a prepared display image after tone, geometry, colour and mask
processing. It does not claim to reconstruct those earlier stages from a FITS.
"""
from copy import deepcopy
from datetime import datetime
from pathlib import Path
import numpy as np

from .image_labels import STYLE_KEYS
from .overlay.moonOverlay import IndiAllSkyMoonOverlay
from .overlay.lightgraphOverlay import IndiAllSkyLightgraphOverlay
from .overlay.imageOverlay import IndiAllSkyImageOverlay
from .overlay.cardinalDirsLabel import IndiAllskyCardinalDirsLabel
from .overlay.orb import IndiAllskyOrbGenerator

GROUPS = {
    'TEXT_PROPERTIES': STYLE_KEYS,
    'IMAGE_BORDER': ('TOP','BOTTOM','LEFT','RIGHT','COLOR'),
    'MOON_OVERLAY': ('ENABLE','X','Y','SCALE','FLIP_V','FLIP_H','DARK_SIDE_SCALE'),
    'LIGHTGRAPH_OVERLAY': ('ENABLE','GRAPH_HEIGHT','GRAPH_BORDER','NOW_MARKER_SIZE','Y','OFFSET_X','SCALE','LABEL','HOUR_LINES','DAY_COLOR','DUSK_COLOR','NIGHT_COLOR','MOONMODE_COLOR','HOUR_COLOR','BORDER_COLOR','NOW_COLOR','FONT_COLOR','OPACITY','PIL_FONT_SIZE','OPENCV_FONT_SCALE'),
    'CARDINAL_DIRS': ('ENABLE','CHAR_NORTH','CHAR_EAST','CHAR_WEST','CHAR_SOUTH','OFFSET_TOP','OFFSET_LEFT','OFFSET_RIGHT','OFFSET_BOTTOM','DIAMETER','SWAP_NS','SWAP_EW','FONT_COLOR','OPENCV_FONT_SCALE','PIL_FONT_SIZE','OUTLINE_CIRCLE'),
    'ORB_PROPERTIES': ('MODE','RADIUS','SUN_COLOR','MOON_COLOR','AZ_OFFSET','RETROGRADE'),
    'IMAGE_OVERLAY': ('ENABLE',),  # No URL, username, password or transfer settings.
}
STATE = {
    'moon': ('scale','x','y','flip_v','flip_h','dark_side_scale','dark'),
    'graph': ('graph_height','graph_border','now_marker_size','y','offset_x','scale','opacity','label','hour_lines','top_border','text_area_height'),
    'cardinal': ('NORTH_CHAR','EAST_CHAR','WEST_CHAR','SOUTH_CHAR','x_offset','y_offset','top_offset','left_offset','right_offset','bottom_offset','az','diameter'),
}
SCALARS = ('IMAGE_SCALE','IMAGE_LABEL_SYSTEM','IMAGE_FLIP_V','IMAGE_FLIP_H','LENS_OFFSET_X','LENS_OFFSET_Y','LENS_AZIMUTH','NIGHT_SUN_ALT_DEG')


def _config(config, assets, font_root):
    result = {k:deepcopy(config[k]) for k in SCALARS if k in config}
    for group, keys in GROUPS.items():
        values = config.get(group, {})
        result[group] = {k:deepcopy(values[k]) for k in keys if k in values}
    style = config.get('TEXT_PROPERTIES', {})
    name = style.get('PIL_FONT_FILE')
    path = Path(style.get('PIL_FONT_CUSTOM', '')) if name == 'custom' else Path(font_root) / (name or '')
    font = assets.put(font=np.frombuffer(path.read_bytes(), dtype=np.uint8)) if path.is_file() else None
    # The asset is sufficient; do not archive private absolute font paths.
    result['TEXT_PROPERTIES']['PIL_FONT_CUSTOM'] = ''
    return {'values':result, 'font':font}


def _state(obj, kind):
    return {key:deepcopy(getattr(obj,key)) for key in STATE[kind]}


def snapshot_presentation(processor, binning, assets):
    p = processor
    result = {'version':1, 'binning':binning, 'focus':p.focus_mode,
              'config':_config(p.config, assets, p.font_path),
              'text_color':list(p.text_color_rgb),
              'logo':None, 'moon':None, 'graph':None, 'images':None, 'orb':None,
              'cardinal':None}
    if p.config.get('LOGO_OVERLAY'):
        logo = p._overlay_dict.get(binning)
        if isinstance(logo, np.ndarray):
            # Logo masks contain three equal planes; preserve float precision.
            alpha = p._alpha_mask_dict[binning]
            compact = alpha.ndim == 3 and np.array_equal(alpha[:,:,0],alpha[:,:,1]) and np.array_equal(alpha[:,:,0],alpha[:,:,2])
            result['logo'] = {'asset':assets.put(pixels=logo, alpha=alpha[:,:,0] if compact else alpha), 'compact_alpha':compact}
        else:
            result['logo'] = {'asset':None}  # Preserve absence; never load today's logo.
    if p.focus_mode:
        return result
    if p.config.get('MOON_OVERLAY',{}).get('ENABLE', True):
        overlay = p._moon_overlay
        result['moon'] = {'asset':assets.put(pixels=overlay.moon_orig),
                          'state':_state(overlay,'moon'),
                          'cycle':p.astrometric_data['moon_cycle'], 'phase':p.astrometric_data['moon_phase']}
    if p.config.get('LIGHTGRAPH_OVERLAY',{}).get('ENABLE', True):
        overlay = p._lightgraph_overlay
        result['graph'] = {'asset':assets.put(pixels=overlay.lightgraph),
                           'state':_state(overlay,'graph'), 'time':overlay.last_draw_time.isoformat(),
                           'config':_config(overlay.config,assets,overlay.font_path)}
    if p.config.get('IMAGE_OVERLAY',{}).get('ENABLE', True):
        result['images'] = [{'x':v['x'],'y':v['y'],
            'asset':None if v['data'] is None else assets.put(pixels=v['data'])}
            for v in p._image_overlay_o.images_dict.values()]
    if p.config.get('ORB_PROPERTIES',{}).get('MODE','ha') != 'off':
        result['orb'] = {'operations':deepcopy(p._orb.draw_operations),
                         'line_thickness':p._orb.line_thickness, 'shape':list(p.image.shape[:2]),
                         'config':_config(p._orb.config,assets,p.font_path)}
    if p.config.get('CARDINAL_DIRS',{}).get('ENABLE'):
        overlay = p._cardinal_dirs_label
        result['cardinal'] = {'state':_state(overlay,'cardinal'),
                              'config':_config(overlay.config,assets,overlay.font_path)}
    return result


def _restore_config(record, assets):
    config = deepcopy(record['values'])
    if record['font']:
        config['TEXT_PROPERTIES'].update(PIL_FONT_FILE='custom', PIL_FONT_CUSTOM=str(assets.font_path(record['font'])))
    return config


def _restore_state(obj, record):
    for key, value in record['state'].items():
        setattr(obj,key,deepcopy(value))


def render_saved_presentation(processor, record, assets):
    """Replay only recorded assets; do not fetch overlays or consult current time.

    Use a dedicated replay processor; this prepares its presentation state.
    """
    if record.get('version') != 1:
        raise ValueError('Unsupported presentation snapshot')
    p = processor
    p.config = _restore_config(record['config'],assets)
    p.focus_mode = record['focus']
    p.text_color_rgb = list(record['text_color'])
    binning = record['binning']
    if record['logo']:
        p.config['LOGO_OVERLAY'] = 'recorded asset'
        logo = record['logo']
        if logo['asset']:
            data = assets.get(logo['asset'])
            p._overlay_dict[binning] = data['pixels']
            p._alpha_mask_dict[binning] = np.dstack([data['alpha']]*3) if logo['compact_alpha'] else data['alpha']
        else:
            p._overlay_dict[binning] = False
    else:
        p.config['LOGO_OVERLAY'] = ''
    p.apply_logo_overlay(binning)
    p.scale_image()
    p.add_border()
    if record['moon']:
        item = record['moon']
        p._moon_overlay = IndiAllSkyMoonOverlay(p.config)
        _restore_state(p._moon_overlay,item)
        p._moon_overlay.moon_orig = assets.get(item['asset'])['pixels']
        p.astrometric_data['moon_cycle'], p.astrometric_data['moon_phase'] = item['cycle'], item['phase']
        p.moon_overlay()
    if record['graph']:
        item = record['graph']
        p._lightgraph_overlay = IndiAllSkyLightgraphOverlay(_restore_config(item['config'],assets),p.position_av)
        _restore_state(p._lightgraph_overlay,item)
        p._lightgraph_overlay.lightgraph = assets.get(item['asset'])['pixels']
        p.lightgraph_overlay(at_time=datetime.fromisoformat(item['time']), refresh=False)
    if record['images'] is not None:
        p._image_overlay_o = IndiAllSkyImageOverlay(p.config)
        p._image_overlay_o.images_dict = {str(i):dict(x=v['x'],y=v['y'],data=None if v['asset'] is None else assets.get(v['asset'])['pixels']) for i,v in enumerate(record['images'])}
        p.image_overlay(refresh=False)
    if record['orb']:
        item = record['orb']
        p._orb = IndiAllskyOrbGenerator(_restore_config(item['config'],assets))
        p._orb.line_thickness = item['line_thickness']
        if list(p.image.shape[:2]) != item['shape']:
            raise ValueError('Saved orb geometry does not match the frame')
        for operation in item['operations']:
            draw = {'circle':p._orb.drawEdgeCircle_opencv, 'line':p._orb.drawEdgeLine_opencv}.get(operation['kind'])
            if draw is None:
                raise ValueError('Unsupported saved orb operation')
            draw(p.image,tuple(operation['point']),tuple(operation['color']))
    if record['cardinal']:
        item = record['cardinal']
        p._cardinal_dirs_label = IndiAllskyCardinalDirsLabel(_restore_config(item['config'],assets))
        _restore_state(p._cardinal_dirs_label,item)
        p.cardinal_dirs_label()
    return p.image
