"""Preview form defaults, preserving the existing processing parameter contract."""
from .forms import IndiAllskyImageProcessingForm

def processing_form(config, camera_id, fits_id, frame_type):
    form_data = {
        'CAMERA_ID'                      : camera_id,
        'FRAME_TYPE'                     : frame_type,
        'FITS_ID'                        : fits_id,
        'LENS_IMAGE_CIRCLE'              : config.get('LENS_IMAGE_CIRCLE', 3000),
        'LENS_OFFSET_X'                  : config.get('LENS_OFFSET_X', 0),
        'LENS_OFFSET_Y'                  : config.get('LENS_OFFSET_Y', 0),
        'LENS_AZIMUTH'                   : config.get('LENS_AZIMUTH', 0.0),
        'CCD_BIT_DEPTH'                  : str(config.get('CCD_BIT_DEPTH', 0)),  # string in form, int in config
        'NIGHT_CONTRAST_ENHANCE'         : config.get('NIGHT_CONTRAST_ENHANCE', False),
        'CONTRAST_ENHANCE_16BIT'         : config.get('CONTRAST_ENHANCE_16BIT', False),
        'CLAHE_CLIPLIMIT'                : config.get('CLAHE_CLIPLIMIT', 3.0),
        'CLAHE_GRIDSIZE'                 : config.get('CLAHE_GRIDSIZE', 8),
        'IMAGE_STRETCH__CLASSNAME'       : config.get('IMAGE_STRETCH', {}).get('CLASSNAME', ''),
        'IMAGE_STRETCH__MODE1_GAMMA'     : config.get('IMAGE_STRETCH', {}).get('MODE1_GAMMA', 3.0),
        'IMAGE_STRETCH__MODE1_STDDEVS'   : config.get('IMAGE_STRETCH', {}).get('MODE1_STDDEVS', 2.25),
        'IMAGE_STRETCH__MODE2_SHADOWS'   : config.get('IMAGE_STRETCH', {}).get('MODE2_SHADOWS', 0.0),
        'IMAGE_STRETCH__MODE2_MIDTONES'  : config.get('IMAGE_STRETCH', {}).get('MODE2_MIDTONES', 0.35),
        'IMAGE_STRETCH__MODE2_HIGHLIGHTS': config.get('IMAGE_STRETCH', {}).get('MODE2_HIGHLIGHTS', 1.0),
        'IMAGE_STRETCH__MODE3_BLACK_CLIP': config.get('IMAGE_STRETCH', {}).get('MODE3_BLACK_CLIP', -2.8),
        'IMAGE_STRETCH__MODE3_SHADOWS'   : config.get('IMAGE_STRETCH', {}).get('MODE3_SHADOWS', 0.0),
        'IMAGE_STRETCH__MODE3_MIDTONES'  : config.get('IMAGE_STRETCH', {}).get('MODE3_MIDTONES', 0.25),
        'IMAGE_STRETCH__MODE3_HIGHLIGHTS': config.get('IMAGE_STRETCH', {}).get('MODE3_HIGHLIGHTS', 1.0),
        'CFA_PATTERN'                    : config.get('CFA_PATTERN', ''),
        'SCNR_ALGORITHM'                 : config.get('SCNR_ALGORITHM', ''),
        'SCNR_MTF_MIDTONES'              : config.get('SCNR_MTF_MIDTONES', 0.65),
        'IMAGE_DENOISE'                  : config.get('IMAGE_DENOISE', ''),
        'IMAGE_DENOISE_STRENGTH'         : config.get('IMAGE_DENOISE_STRENGTH', 3),
        'BILATERAL_SIGMA_COLOR'          : config.get('BILATERAL_SIGMA_COLOR', 20),
        'BILATERAL_SIGMA_SPACE'          : config.get('BILATERAL_SIGMA_SPACE', 35),
        'WBR_FACTOR'                     : config.get('WBR_FACTOR', 1.0),
        'WBG_FACTOR'                     : config.get('WBG_FACTOR', 1.0),
        'WBB_FACTOR'                     : config.get('WBB_FACTOR', 1.0),
        'AUTO_WB'                        : config.get('AUTO_WB', False),
        'WBR_MTF_MIDTONES'               : config.get('WBR_MTF_MIDTONES', 0.5),
        'WBG_MTF_MIDTONES'               : config.get('WBG_MTF_MIDTONES', 0.5),
        'WBB_MTF_MIDTONES'               : config.get('WBB_MTF_MIDTONES', 0.5),
        'SATURATION_FACTOR'              : config.get('SATURATION_FACTOR', 1.0),
        'GAMMA_CORRECTION'               : config.get('GAMMA_CORRECTION', 1.0),
        'SHARPEN_AMOUNT'                 : config.get('SHARPEN_AMOUNT', 0.0),
        'IMAGE_ROTATE'                   : config.get('IMAGE_ROTATE', ''),
        'IMAGE_ROTATE_ANGLE'             : config.get('IMAGE_ROTATE_ANGLE', 0),
        'IMAGE_FLIP_V'                   : config.get('IMAGE_FLIP_V', True),
        'IMAGE_FLIP_H'                   : config.get('IMAGE_FLIP_H', True),
        'IMAGE_COLORMAP'                 : '',
        'DETECT_MASK'                    : config.get('DETECT_MASK', ''),
        'SQM_FOV_DIV'                    : str(config.get('SQM_FOV_DIV', 4)),  # string in form, int in config
        'IMAGE_STACK_METHOD'             : config.get('IMAGE_STACK_METHOD', 'maximum'),
        'IMAGE_STACK_COUNT'              : str(config.get('IMAGE_STACK_COUNT', 1)),  # string in form, int in config
        'IMAGE_STACK_ALIGN'              : config.get('IMAGE_STACK_ALIGN', False),
        'IMAGE_ALIGN_DETECTSIGMA'        : config.get('IMAGE_ALIGN_DETECTSIGMA', 5),
        'IMAGE_ALIGN_POINTS'             : config.get('IMAGE_ALIGN_POINTS', 50),
        'IMAGE_ALIGN_SOURCEMINAREA'      : config.get('IMAGE_ALIGN_SOURCEMINAREA', 10),
        'FISH2PANO__ENABLE'              : False,
        'FISH2PANO__DIAMETER'            : config.get('FISH2PANO', {}).get('DIAMETER', 3000),
        'FISH2PANO__ROTATE_ANGLE'        : config.get('FISH2PANO', {}).get('ROTATE_ANGLE', 0),
        'FISH2PANO__SCALE'               : config.get('FISH2PANO', {}).get('SCALE', 0.3),
        'FISH2PANO__FLIP_H'              : config.get('FISH2PANO', {}).get('FLIP_H', False),
        'FISH2PANO__ENABLE_CARDINAL_DIRS': config.get('FISH2PANO', {}).get('ENABLE_CARDINAL_DIRS', True),
        'FISH2PANO__DIRS_OFFSET_BOTTOM'  : config.get('FISH2PANO', {}).get('DIRS_OFFSET_BOTTOM', 25),
        'FISH2PANO__OPENCV_FONT_SCALE'   : config.get('FISH2PANO', {}).get('OPENCV_FONT_SCALE', 0.8),
        'FISH2PANO__PIL_FONT_SIZE'       : config.get('FISH2PANO', {}).get('PIL_FONT_SIZE', 30),
        'PROCESSING_SPLIT_SCREEN'        : False,
        'IMAGE_CALIBRATE_DARK'           : False,  # darks are almost always already applied
        'IMAGE_CALIBRATE_BPM'            : False,
        'IMAGE_CALIBRATE_FIX_HOLES'      : config.get('IMAGE_CALIBRATE_FIX_HOLES', False),
        'IMAGE_CALIBRATE_HOLE_THOLD'     : config.get('IMAGE_CALIBRATE_HOLE_THOLD', 30),
        'IMAGE_CALIBRATE_MANUAL_OFFSET'  : config.get('IMAGE_CALIBRATE_MANUAL_OFFSET', 0),
        'IMAGE_LABEL_TEMPLATE'           : config.get('IMAGE_LABEL_TEMPLATE', ''),
        'IMAGE_EXTRA_TEXT'               : config.get('IMAGE_EXTRA_TEXT'),
        'IMAGE_LABEL_SYSTEM'             : '',
        'TEXT_PROPERTIES__FONT_FACE'     : config.get('TEXT_PROPERTIES', {}).get('FONT_FACE', 'FONT_HERSHEY_SIMPLEX'),
        'TEXT_PROPERTIES__FONT_SCALE'    : config.get('TEXT_PROPERTIES', {}).get('FONT_SCALE', 0.8),
        'TEXT_PROPERTIES__FONT_THICKNESS': config.get('TEXT_PROPERTIES', {}).get('FONT_THICKNESS', 1),
        'TEXT_PROPERTIES__FONT_OUTLINE'  : config.get('TEXT_PROPERTIES', {}).get('FONT_OUTLINE', True),
        'TEXT_PROPERTIES__FONT_HEIGHT'   : config.get('TEXT_PROPERTIES', {}).get('FONT_HEIGHT', 30),
        'TEXT_PROPERTIES__FONT_X'        : config.get('TEXT_PROPERTIES', {}).get('FONT_X', 15),
        'TEXT_PROPERTIES__FONT_Y'        : config.get('TEXT_PROPERTIES', {}).get('FONT_Y', 30),
        'TEXT_PROPERTIES__PIL_FONT_FILE' : config.get('TEXT_PROPERTIES', {}).get('PIL_FONT_FILE', 'fonts-freefont-ttf/FreeSans.ttf'),
        'TEXT_PROPERTIES__PIL_FONT_CUSTOM': config.get('TEXT_PROPERTIES', {}).get('PIL_FONT_CUSTOM', ''),
        'TEXT_PROPERTIES__PIL_FONT_SIZE' : config.get('TEXT_PROPERTIES', {}).get('PIL_FONT_SIZE', 30),
        'CARDINAL_DIRS__ENABLE'          : False,
        'CARDINAL_DIRS__SWAP_NS'         : config.get('CARDINAL_DIRS', {}).get('SWAP_NS', False),
        'CARDINAL_DIRS__SWAP_EW'         : config.get('CARDINAL_DIRS', {}).get('SWAP_EW', False),
        'CARDINAL_DIRS__CHAR_NORTH'      : config.get('CARDINAL_DIRS', {}).get('CHAR_NORTH', 'N'),
        'CARDINAL_DIRS__CHAR_EAST'       : config.get('CARDINAL_DIRS', {}).get('CHAR_EAST', 'E'),
        'CARDINAL_DIRS__CHAR_WEST'       : config.get('CARDINAL_DIRS', {}).get('CHAR_WEST', 'W'),
        'CARDINAL_DIRS__CHAR_SOUTH'      : config.get('CARDINAL_DIRS', {}).get('CHAR_SOUTH', 'S'),
        'CARDINAL_DIRS__DIAMETER'        : config.get('CARDINAL_DIRS', {}).get('DIAMETER', 3000),
        'CARDINAL_DIRS__OFFSET_X'        : config.get('CARDINAL_DIRS', {}).get('OFFSET_X', 0),
        'CARDINAL_DIRS__OFFSET_Y'        : config.get('CARDINAL_DIRS', {}).get('OFFSET_Y', 0),
        'CARDINAL_DIRS__OFFSET_TOP'      : config.get('CARDINAL_DIRS', {}).get('OFFSET_TOP', 15),
        'CARDINAL_DIRS__OFFSET_LEFT'     : config.get('CARDINAL_DIRS', {}).get('OFFSET_LEFT', 15),
        'CARDINAL_DIRS__OFFSET_RIGHT'    : config.get('CARDINAL_DIRS', {}).get('OFFSET_RIGHT', 15),
        'CARDINAL_DIRS__OFFSET_BOTTOM'   : config.get('CARDINAL_DIRS', {}).get('OFFSET_BOTTOM', 15),
        'CARDINAL_DIRS__OPENCV_FONT_SCALE' : config.get('CARDINAL_DIRS', {}).get('OPENCV_FONT_SCALE', 0.5),
        'CARDINAL_DIRS__PIL_FONT_SIZE'   : config.get('CARDINAL_DIRS', {}).get('PIL_FONT_SIZE', 20),
        'CARDINAL_DIRS__OUTLINE_CIRCLE'  : config.get('CARDINAL_DIRS', {}).get('OUTLINE_CIRCLE', False),
        'IMAGE_CIRCLE_MASK__ENABLE'      : False,
        'IMAGE_CIRCLE_MASK__DIAMETER'    : config.get('IMAGE_CIRCLE_MASK', {}).get('DIAMETER', 3000),
        'IMAGE_CIRCLE_MASK__OFFSET_X'    : config.get('IMAGE_CIRCLE_MASK', {}).get('OFFSET_X', 0),
        'IMAGE_CIRCLE_MASK__OFFSET_Y'    : config.get('IMAGE_CIRCLE_MASK', {}).get('OFFSET_Y', 0),
        'IMAGE_CIRCLE_MASK__BLUR'        : config.get('IMAGE_CIRCLE_MASK', {}).get('BLUR', 35),
        'IMAGE_CIRCLE_MASK__OPACITY'     : config.get('IMAGE_CIRCLE_MASK', {}).get('OPACITY', 100),
        'IMAGE_CIRCLE_MASK__OUTLINE'     : config.get('IMAGE_CIRCLE_MASK', {}).get('OUTLINE', False),
        'IMAGE_CROP_IMAGE_CIRCLE'        : config.get('IMAGE_CROP_IMAGE_CIRCLE', False),
        'MOON_OVERLAY__ENABLE'           : False,
        'MOON_OVERLAY__X'                : config.get('MOON_OVERLAY', {}).get('X', -500),
        'MOON_OVERLAY__Y'                : config.get('MOON_OVERLAY', {}).get('Y', -200),
        'MOON_OVERLAY__SCALE'            : config.get('MOON_OVERLAY', {}).get('SCALE', 0.5),
        'MOON_OVERLAY__DARK_SIDE_SCALE'  : config.get('MOON_OVERLAY', {}).get('DARK_SIDE_SCALE', 0.4),
        'MOON_OVERLAY__FLIP_V'           : config.get('MOON_OVERLAY', {}).get('FLIP_V', False),
        'MOON_OVERLAY__FLIP_H'           : config.get('MOON_OVERLAY', {}).get('FLIP_H', False),
        'LIGHTGRAPH_OVERLAY__ENABLE'     : False,
        'LIGHTGRAPH_OVERLAY__GRAPH_HEIGHT' : config.get('LIGHTGRAPH_OVERLAY', {}).get('GRAPH_HEIGHT', 30),
        'LIGHTGRAPH_OVERLAY__GRAPH_BORDER' : config.get('LIGHTGRAPH_OVERLAY', {}).get('GRAPH_BORDER', 3),
        'LIGHTGRAPH_OVERLAY__Y'          : config.get('LIGHTGRAPH_OVERLAY', {}).get('Y', 10),
        'LIGHTGRAPH_OVERLAY__OFFSET_X'   : config.get('LIGHTGRAPH_OVERLAY', {}).get('OFFSET_X', 0),
        'LIGHTGRAPH_OVERLAY__SCALE'      : config.get('LIGHTGRAPH_OVERLAY', {}).get('SCALE', 1.0),
        'LIGHTGRAPH_OVERLAY__NOW_MARKER_SIZE' : config.get('LIGHTGRAPH_OVERLAY', {}).get('NOW_MARKER_SIZE', 8),
        'LIGHTGRAPH_OVERLAY__OPACITY'    : config.get('LIGHTGRAPH_OVERLAY', {}).get('OPACITY', 100),
        'LIGHTGRAPH_OVERLAY__PIL_FONT_SIZE' : config.get('LIGHTGRAPH_OVERLAY', {}).get('PIL_FONT_SIZE', 20),
        'LIGHTGRAPH_OVERLAY__OPENCV_FONT_SCALE' : config.get('LIGHTGRAPH_OVERLAY', {}).get('OPENCV_FONT_SCALE', 0.5),
        'LIGHTGRAPH_OVERLAY__LABEL'      : config.get('LIGHTGRAPH_OVERLAY', {}).get('LABEL', True),
        'LIGHTGRAPH_OVERLAY__HOUR_LINES' : config.get('LIGHTGRAPH_OVERLAY', {}).get('HOUR_LINES', True),
        'IMAGE_BORDER__TOP'              : config.get('IMAGE_BORDER', {}).get('TOP', 0),
        'IMAGE_BORDER__LEFT'             : config.get('IMAGE_BORDER', {}).get('LEFT', 0),
        'IMAGE_BORDER__RIGHT'            : config.get('IMAGE_BORDER', {}).get('RIGHT', 0),
        'IMAGE_BORDER__BOTTOM'           : config.get('IMAGE_BORDER', {}).get('BOTTOM', 0),
    }

    # SQM_ROI
    SQM_ROI = config.get('SQM_ROI', [])
    if SQM_ROI is None:
        SQM_ROI = []
    elif isinstance(SQM_ROI, bool):
        SQM_ROI = []

    try:
        form_data['SQM_ROI_X1'] = SQM_ROI[0]
    except IndexError:
        form_data['SQM_ROI_X1'] = 0

    try:
        form_data['SQM_ROI_Y1'] = SQM_ROI[1]
    except IndexError:
        form_data['SQM_ROI_Y1'] = 0

    try:
        form_data['SQM_ROI_X2'] = SQM_ROI[2]
    except IndexError:
        form_data['SQM_ROI_X2'] = 0

    try:
        form_data['SQM_ROI_Y2'] = SQM_ROI[3]
    except IndexError:
        form_data['SQM_ROI_Y2'] = 0

    # Font color
    text_properties__font_color = config.get('TEXT_PROPERTIES', {}).get('FONT_COLOR', [200, 200, 200])
    form_data['TEXT_PROPERTIES__FONT_COLOR'] = ','.join([str(x) for x in text_properties__font_color])

    # Cardinal directions color
    cardinal_dirs__font_color = config.get('CARDINAL_DIRS', {}).get('FONT_COLOR', [200, 0, 0])
    form_data['CARDINAL_DIRS__FONT_COLOR'] = ','.join([str(x) for x in cardinal_dirs__font_color])

    # Border color
    image_border__color = config.get('IMAGE_BORDER', {}).get('COLOR', [0, 0, 0])
    form_data['IMAGE_BORDER__COLOR'] = ','.join([str(x) for x in image_border__color])

    # Lightgraph colors
    lightgraph_overlay__day_color = config.get('LIGHTGRAPH_OVERLAY', {}).get('DAY_COLOR', [150, 150, 150])
    form_data['LIGHTGRAPH_OVERLAY__DAY_COLOR'] = ','.join([str(x) for x in lightgraph_overlay__day_color])

    lightgraph_overlay__dusk_color = config.get('LIGHTGRAPH_OVERLAY', {}).get('DUSK_COLOR', [200, 100, 60])
    form_data['LIGHTGRAPH_OVERLAY__DUSK_COLOR'] = ','.join([str(x) for x in lightgraph_overlay__dusk_color])

    lightgraph_overlay__night_color = config.get('LIGHTGRAPH_OVERLAY', {}).get('NIGHT_COLOR', [30, 30, 30])
    form_data['LIGHTGRAPH_OVERLAY__NIGHT_COLOR'] = ','.join([str(x) for x in lightgraph_overlay__night_color])

    lightgraph_overlay__moonmode_color = config.get('LIGHTGRAPH_OVERLAY', {}).get('MOONMODE_COLOR', [50, 50, 50])
    form_data['LIGHTGRAPH_OVERLAY__MOONMODE_COLOR'] = ','.join([str(x) for x in lightgraph_overlay__moonmode_color])

    lightgraph_overlay__hour_color = config.get('LIGHTGRAPH_OVERLAY', {}).get('HOUR_COLOR', [100, 15, 15])
    form_data['LIGHTGRAPH_OVERLAY__HOUR_COLOR'] = ','.join([str(x) for x in lightgraph_overlay__hour_color])

    lightgraph_overlay__border_color = config.get('LIGHTGRAPH_OVERLAY', {}).get('BORDER_COLOR', [1, 1, 1])
    form_data['LIGHTGRAPH_OVERLAY__BORDER_COLOR'] = ','.join([str(x) for x in lightgraph_overlay__border_color])

    lightgraph_overlay__now_color = config.get('LIGHTGRAPH_OVERLAY', {}).get('NOW_COLOR', [120, 120, 200])
    form_data['LIGHTGRAPH_OVERLAY__NOW_COLOR'] = ','.join([str(x) for x in lightgraph_overlay__now_color])

    lightgraph_overlay__font_color = config.get('LIGHTGRAPH_OVERLAY', {}).get('FONT_COLOR', [150, 150, 150])
    form_data['LIGHTGRAPH_OVERLAY__FONT_COLOR'] = ','.join([str(x) for x in lightgraph_overlay__font_color])

    return IndiAllskyImageProcessingForm(data=form_data)

def processing_groups(form):
    groups = {}
    for field in form:
        if field.type in ('HiddenField','CSRFTokenField') or field.name == 'DISABLE_PROCESSING':
            continue
        name = field.name
        if name.startswith('FISH2PANO'):
            group = 'Panorama'
        elif name.startswith(('TEXT_PROPERTIES','IMAGE_LABEL','IMAGE_EXTRA')):
            group = 'Labels and fonts'
        elif name.startswith(('CARDINAL_DIRS','MOON_OVERLAY','LIGHTGRAPH_OVERLAY','IMAGE_BORDER')):
            group = 'Overlays and borders'
        elif name.startswith('IMAGE_CIRCLE_MASK'):
            group = 'Circular mask'
        elif name.startswith(('LENS_','IMAGE_ROTATE','IMAGE_FLIP','IMAGE_CROP')):
            group = 'Geometry'
        elif name.startswith(('IMAGE_CALIBRATE','CCD_','CFA_','DETECT_MASK')):
            group = 'Calibration and sensor'
        elif name.startswith(('IMAGE_STACK','IMAGE_ALIGN','SQM_')):
            group = 'Stacking and measurement'
        elif name.startswith(('WB','AUTO_WB','SCNR','SATURATION','GAMMA')):
            group = 'Color'
        elif name == 'OUTPUT_IMAGE_TYPE':
            group = 'Output'
        else:
            group = 'Stretch and image detail'
        groups.setdefault(group,[]).append(field)
    return groups
