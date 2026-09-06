"""Independent preview configuration; never mutate saved/shared nested values."""
from copy import deepcopy

REQUIRED_FIELDS = ('AUTO_WB',
 'BILATERAL_SIGMA_COLOR',
 'BILATERAL_SIGMA_SPACE',
 'CAMERA_ID',
 'CARDINAL_DIRS__CHAR_EAST',
 'CARDINAL_DIRS__CHAR_NORTH',
 'CARDINAL_DIRS__CHAR_SOUTH',
 'CARDINAL_DIRS__CHAR_WEST',
 'CARDINAL_DIRS__DIAMETER',
 'CARDINAL_DIRS__ENABLE',
 'CARDINAL_DIRS__FONT_COLOR',
 'CARDINAL_DIRS__OFFSET_BOTTOM',
 'CARDINAL_DIRS__OFFSET_LEFT',
 'CARDINAL_DIRS__OFFSET_RIGHT',
 'CARDINAL_DIRS__OFFSET_TOP',
 'CARDINAL_DIRS__OFFSET_X',
 'CARDINAL_DIRS__OFFSET_Y',
 'CARDINAL_DIRS__OPENCV_FONT_SCALE',
 'CARDINAL_DIRS__OUTLINE_CIRCLE',
 'CARDINAL_DIRS__PIL_FONT_SIZE',
 'CARDINAL_DIRS__SWAP_EW',
 'CARDINAL_DIRS__SWAP_NS',
 'CCD_BIT_DEPTH',
 'CFA_PATTERN',
 'CLAHE_CLIPLIMIT',
 'CLAHE_GRIDSIZE',
 'CONTRAST_ENHANCE_16BIT',
 'DETECT_MASK',
 'DISABLE_PROCESSING',
 'FISH2PANO__DIAMETER',
 'FISH2PANO__DIRS_OFFSET_BOTTOM',
 'FISH2PANO__ENABLE',
 'FISH2PANO__ENABLE_CARDINAL_DIRS',
 'FISH2PANO__FLIP_H',
 'FISH2PANO__OPENCV_FONT_SCALE',
 'FISH2PANO__PIL_FONT_SIZE',
 'FISH2PANO__ROTATE_ANGLE',
 'FISH2PANO__SCALE',
 'FITS_ID',
 'FRAME_TYPE',
 'GAMMA_CORRECTION',
 'IMAGE_ALIGN_DETECTSIGMA',
 'IMAGE_ALIGN_POINTS',
 'IMAGE_ALIGN_SOURCEMINAREA',
 'IMAGE_BORDER__BOTTOM',
 'IMAGE_BORDER__COLOR',
 'IMAGE_BORDER__LEFT',
 'IMAGE_BORDER__RIGHT',
 'IMAGE_BORDER__TOP',
 'IMAGE_CALIBRATE_BPM',
 'IMAGE_CALIBRATE_DARK',
 'IMAGE_CALIBRATE_FIX_HOLES',
 'IMAGE_CALIBRATE_HOLE_THOLD',
 'IMAGE_CALIBRATE_MANUAL_OFFSET',
 'IMAGE_CIRCLE_MASK__BLUR',
 'IMAGE_CIRCLE_MASK__DIAMETER',
 'IMAGE_CIRCLE_MASK__ENABLE',
 'IMAGE_CIRCLE_MASK__OFFSET_X',
 'IMAGE_CIRCLE_MASK__OFFSET_Y',
 'IMAGE_CIRCLE_MASK__OPACITY',
 'IMAGE_CIRCLE_MASK__OUTLINE',
 'IMAGE_COLORMAP',
 'IMAGE_CROP_IMAGE_CIRCLE',
 'IMAGE_DENOISE',
 'IMAGE_DENOISE_STRENGTH',
 'IMAGE_EXTRA_TEXT',
 'IMAGE_FLIP_H',
 'IMAGE_FLIP_V',
 'IMAGE_LABEL_SYSTEM',
 'IMAGE_LABEL_TEMPLATE',
 'IMAGE_ROTATE',
 'IMAGE_ROTATE_ANGLE',
 'IMAGE_STACK_ALIGN',
 'IMAGE_STACK_COUNT',
 'IMAGE_STACK_METHOD',
 'IMAGE_STRETCH__CLASSNAME',
 'IMAGE_STRETCH__MODE1_GAMMA',
 'IMAGE_STRETCH__MODE1_STDDEVS',
 'IMAGE_STRETCH__MODE2_HIGHLIGHTS',
 'IMAGE_STRETCH__MODE2_MIDTONES',
 'IMAGE_STRETCH__MODE2_SHADOWS',
 'IMAGE_STRETCH__MODE3_BLACK_CLIP',
 'IMAGE_STRETCH__MODE3_HIGHLIGHTS',
 'IMAGE_STRETCH__MODE3_MIDTONES',
 'IMAGE_STRETCH__MODE3_SHADOWS',
 'LENS_AZIMUTH',
 'LENS_IMAGE_CIRCLE',
 'LENS_OFFSET_X',
 'LENS_OFFSET_Y',
 'LIGHTGRAPH_OVERLAY__BORDER_COLOR',
 'LIGHTGRAPH_OVERLAY__DAY_COLOR',
 'LIGHTGRAPH_OVERLAY__DUSK_COLOR',
 'LIGHTGRAPH_OVERLAY__ENABLE',
 'LIGHTGRAPH_OVERLAY__FONT_COLOR',
 'LIGHTGRAPH_OVERLAY__GRAPH_BORDER',
 'LIGHTGRAPH_OVERLAY__GRAPH_HEIGHT',
 'LIGHTGRAPH_OVERLAY__HOUR_COLOR',
 'LIGHTGRAPH_OVERLAY__HOUR_LINES',
 'LIGHTGRAPH_OVERLAY__LABEL',
 'LIGHTGRAPH_OVERLAY__MOONMODE_COLOR',
 'LIGHTGRAPH_OVERLAY__NIGHT_COLOR',
 'LIGHTGRAPH_OVERLAY__NOW_COLOR',
 'LIGHTGRAPH_OVERLAY__NOW_MARKER_SIZE',
 'LIGHTGRAPH_OVERLAY__OFFSET_X',
 'LIGHTGRAPH_OVERLAY__OPACITY',
 'LIGHTGRAPH_OVERLAY__OPENCV_FONT_SCALE',
 'LIGHTGRAPH_OVERLAY__PIL_FONT_SIZE',
 'LIGHTGRAPH_OVERLAY__SCALE',
 'LIGHTGRAPH_OVERLAY__Y',
 'MOON_OVERLAY__DARK_SIDE_SCALE',
 'MOON_OVERLAY__ENABLE',
 'MOON_OVERLAY__FLIP_H',
 'MOON_OVERLAY__FLIP_V',
 'MOON_OVERLAY__SCALE',
 'MOON_OVERLAY__X',
 'MOON_OVERLAY__Y',
 'NIGHT_CONTRAST_ENHANCE',
 'OUTPUT_IMAGE_TYPE',
 'SATURATION_FACTOR',
 'SCNR_ALGORITHM',
 'SCNR_MTF_MIDTONES',
 'SHARPEN_AMOUNT',
 'SQM_FOV_DIV',
 'SQM_ROI_X1',
 'SQM_ROI_X2',
 'SQM_ROI_Y1',
 'SQM_ROI_Y2',
 'TEXT_PROPERTIES__FONT_COLOR',
 'TEXT_PROPERTIES__FONT_FACE',
 'TEXT_PROPERTIES__FONT_HEIGHT',
 'TEXT_PROPERTIES__FONT_OUTLINE',
 'TEXT_PROPERTIES__FONT_SCALE',
 'TEXT_PROPERTIES__FONT_THICKNESS',
 'TEXT_PROPERTIES__FONT_X',
 'TEXT_PROPERTIES__FONT_Y',
 'TEXT_PROPERTIES__PIL_FONT_CUSTOM',
 'TEXT_PROPERTIES__PIL_FONT_FILE',
 'TEXT_PROPERTIES__PIL_FONT_SIZE',
 'WBB_FACTOR',
 'WBB_MTF_MIDTONES',
 'WBG_FACTOR',
 'WBG_MTF_MIDTONES',
 'WBR_FACTOR',
 'WBR_MTF_MIDTONES')

def processing_config(config, payload):
    p_config = deepcopy(config)

    p_config['LENS_IMAGE_CIRCLE']                    = int(payload['LENS_IMAGE_CIRCLE'])
    p_config['LENS_OFFSET_X']                        = int(payload['LENS_OFFSET_X'])
    p_config['LENS_OFFSET_Y']                        = int(payload['LENS_OFFSET_Y'])
    p_config['LENS_AZIMUTH']                         = float(payload['LENS_AZIMUTH'])
    p_config['CCD_BIT_DEPTH']                        = int(payload['CCD_BIT_DEPTH'])
    p_config['IMAGE_CALIBRATE_DARK']                 = bool(payload['IMAGE_CALIBRATE_DARK'])
    p_config['IMAGE_CALIBRATE_BPM']                  = bool(payload['IMAGE_CALIBRATE_BPM'])
    p_config['IMAGE_CALIBRATE_FIX_HOLES']            = bool(payload['IMAGE_CALIBRATE_FIX_HOLES'])
    p_config['IMAGE_CALIBRATE_HOLE_THOLD']           = int(payload['IMAGE_CALIBRATE_HOLE_THOLD'])
    p_config['IMAGE_CALIBRATE_MANUAL_OFFSET']        = int(payload['IMAGE_CALIBRATE_MANUAL_OFFSET'])
    p_config['NIGHT_CONTRAST_ENHANCE']               = bool(payload['NIGHT_CONTRAST_ENHANCE'])
    p_config['IMAGE_COLORMAP']                       = str(payload['IMAGE_COLORMAP'])
    p_config['CONTRAST_ENHANCE_16BIT']               = bool(payload['CONTRAST_ENHANCE_16BIT'])
    p_config['CLAHE_CLIPLIMIT']                      = float(payload['CLAHE_CLIPLIMIT'])
    p_config['CLAHE_GRIDSIZE']                       = int(payload['CLAHE_GRIDSIZE'])
    p_config['IMAGE_STRETCH']['CLASSNAME']           = str(payload['IMAGE_STRETCH__CLASSNAME'])
    p_config['IMAGE_STRETCH']['MODE1_GAMMA']         = float(payload['IMAGE_STRETCH__MODE1_GAMMA'])
    p_config['IMAGE_STRETCH']['MODE1_STDDEVS']       = float(payload['IMAGE_STRETCH__MODE1_STDDEVS'])
    p_config['IMAGE_STRETCH']['MODE2_SHADOWS']       = float(payload['IMAGE_STRETCH__MODE2_SHADOWS'])
    p_config['IMAGE_STRETCH']['MODE2_MIDTONES']      = float(payload['IMAGE_STRETCH__MODE2_MIDTONES'])
    p_config['IMAGE_STRETCH']['MODE2_HIGHLIGHTS']    = float(payload['IMAGE_STRETCH__MODE2_HIGHLIGHTS'])
    p_config['IMAGE_STRETCH']['MODE3_BLACK_CLIP']    = float(payload['IMAGE_STRETCH__MODE3_BLACK_CLIP'])
    p_config['IMAGE_STRETCH']['MODE3_SHADOWS']       = float(payload['IMAGE_STRETCH__MODE3_SHADOWS'])
    p_config['IMAGE_STRETCH']['MODE3_MIDTONES']      = float(payload['IMAGE_STRETCH__MODE3_MIDTONES'])
    p_config['IMAGE_STRETCH']['MODE3_HIGHLIGHTS']    = float(payload['IMAGE_STRETCH__MODE3_HIGHLIGHTS'])
    p_config['IMAGE_STRETCH']['SPLIT']               = False
    p_config['CFA_PATTERN']                          = str(payload['CFA_PATTERN'])
    p_config['SCNR_ALGORITHM']                       = str(payload['SCNR_ALGORITHM'])
    p_config['SCNR_MTF_MIDTONES']                    = float(payload['SCNR_MTF_MIDTONES'])
    p_config['IMAGE_DENOISE']                        = str(payload['IMAGE_DENOISE'])
    p_config['IMAGE_DENOISE_STRENGTH']               = int(payload['IMAGE_DENOISE_STRENGTH'])
    p_config['BILATERAL_SIGMA_COLOR']                = int(payload['BILATERAL_SIGMA_COLOR'])
    p_config['BILATERAL_SIGMA_SPACE']                = int(payload['BILATERAL_SIGMA_SPACE'])
    p_config['WBR_FACTOR']                           = float(payload['WBR_FACTOR'])
    p_config['WBG_FACTOR']                           = float(payload['WBG_FACTOR'])
    p_config['WBB_FACTOR']                           = float(payload['WBB_FACTOR'])
    p_config['WBR_MTF_MIDTONES']                     = float(payload['WBR_MTF_MIDTONES'])
    p_config['WBG_MTF_MIDTONES']                     = float(payload['WBG_MTF_MIDTONES'])
    p_config['WBB_MTF_MIDTONES']                     = float(payload['WBB_MTF_MIDTONES'])
    p_config['AUTO_WB']                              = bool(payload['AUTO_WB'])
    p_config['SATURATION_FACTOR']                    = float(payload['SATURATION_FACTOR'])
    p_config['GAMMA_CORRECTION']                     = float(payload['GAMMA_CORRECTION'])
    p_config['SHARPEN_AMOUNT']                       = float(payload['SHARPEN_AMOUNT'])
    p_config['IMAGE_ROTATE']                         = str(payload['IMAGE_ROTATE'])
    p_config['IMAGE_ROTATE_ANGLE']                   = int(payload['IMAGE_ROTATE_ANGLE'])
    p_config['IMAGE_FLIP_V']                         = bool(payload['IMAGE_FLIP_V'])
    p_config['IMAGE_FLIP_H']                         = bool(payload['IMAGE_FLIP_H'])
    p_config['DETECT_MASK']                          = str(payload['DETECT_MASK'])
    p_config['SQM_FOV_DIV']                          = int(payload['SQM_FOV_DIV'])
    p_config['IMAGE_STACK_METHOD']                   = str(payload['IMAGE_STACK_METHOD'])
    p_config['IMAGE_STACK_COUNT']                    = int(payload['IMAGE_STACK_COUNT'])
    p_config['IMAGE_STACK_ALIGN']                    = bool(payload['IMAGE_STACK_ALIGN'])
    p_config['IMAGE_ALIGN_DETECTSIGMA']              = int(payload['IMAGE_ALIGN_DETECTSIGMA'])
    p_config['IMAGE_ALIGN_POINTS']                   = int(payload['IMAGE_ALIGN_POINTS'])
    p_config['IMAGE_ALIGN_SOURCEMINAREA']            = int(payload['IMAGE_ALIGN_SOURCEMINAREA'])
    p_config['IMAGE_STACK_SPLIT']                    = False
    p_config['FISH2PANO']['ENABLE']                  = bool(payload['FISH2PANO__ENABLE'])
    p_config['FISH2PANO']['DIAMETER']                = int(payload['FISH2PANO__DIAMETER'])
    p_config['FISH2PANO']['ROTATE_ANGLE']            = int(payload['FISH2PANO__ROTATE_ANGLE'])
    p_config['FISH2PANO']['SCALE']                   = float(payload['FISH2PANO__SCALE'])
    p_config['FISH2PANO']['FLIP_H']                  = bool(payload['FISH2PANO__FLIP_H'])
    p_config['FISH2PANO']['ENABLE_CARDINAL_DIRS']    = bool(payload['FISH2PANO__ENABLE_CARDINAL_DIRS'])
    p_config['FISH2PANO']['DIRS_OFFSET_BOTTOM']      = int(payload['FISH2PANO__DIRS_OFFSET_BOTTOM'])
    p_config['FISH2PANO']['OPENCV_FONT_SCALE']       = float(payload['FISH2PANO__OPENCV_FONT_SCALE'])
    p_config['FISH2PANO']['PIL_FONT_SIZE']           = int(payload['FISH2PANO__PIL_FONT_SIZE'])
    p_config['PROCESSING_SPLIT_SCREEN']              = bool(payload.get('PROCESSING_SPLIT_SCREEN', False))
    p_config['IMAGE_LABEL_TEMPLATE']                 = str(payload['IMAGE_LABEL_TEMPLATE'])
    p_config['IMAGE_EXTRA_TEXT']                     = str(payload['IMAGE_EXTRA_TEXT'])
    p_config['IMAGE_LABEL_SYSTEM']                   = str(payload['IMAGE_LABEL_SYSTEM'])
    p_config['TEXT_PROPERTIES']['FONT_FACE']         = str(payload['TEXT_PROPERTIES__FONT_FACE'])
    p_config['TEXT_PROPERTIES']['FONT_SCALE']        = float(payload['TEXT_PROPERTIES__FONT_SCALE'])
    p_config['TEXT_PROPERTIES']['FONT_THICKNESS']    = int(payload['TEXT_PROPERTIES__FONT_THICKNESS'])
    p_config['TEXT_PROPERTIES']['FONT_OUTLINE']      = bool(payload['TEXT_PROPERTIES__FONT_OUTLINE'])
    p_config['TEXT_PROPERTIES']['FONT_HEIGHT']       = int(payload['TEXT_PROPERTIES__FONT_HEIGHT'])
    p_config['TEXT_PROPERTIES']['FONT_X']            = int(payload['TEXT_PROPERTIES__FONT_X'])
    p_config['TEXT_PROPERTIES']['FONT_Y']            = int(payload['TEXT_PROPERTIES__FONT_Y'])
    p_config['TEXT_PROPERTIES']['PIL_FONT_FILE']     = str(payload['TEXT_PROPERTIES__PIL_FONT_FILE'])
    p_config['TEXT_PROPERTIES']['PIL_FONT_CUSTOM']   = str(payload['TEXT_PROPERTIES__PIL_FONT_CUSTOM'])
    p_config['TEXT_PROPERTIES']['PIL_FONT_SIZE']     = int(payload['TEXT_PROPERTIES__PIL_FONT_SIZE'])
    p_config['CARDINAL_DIRS']['ENABLE']              = bool(payload['CARDINAL_DIRS__ENABLE'])
    p_config['CARDINAL_DIRS']['SWAP_NS']             = bool(payload['CARDINAL_DIRS__SWAP_NS'])
    p_config['CARDINAL_DIRS']['SWAP_EW']             = bool(payload['CARDINAL_DIRS__SWAP_EW'])
    p_config['CARDINAL_DIRS']['CHAR_NORTH']          = str(payload['CARDINAL_DIRS__CHAR_NORTH'])
    p_config['CARDINAL_DIRS']['CHAR_EAST']           = str(payload['CARDINAL_DIRS__CHAR_EAST'])
    p_config['CARDINAL_DIRS']['CHAR_WEST']           = str(payload['CARDINAL_DIRS__CHAR_WEST'])
    p_config['CARDINAL_DIRS']['CHAR_SOUTH']          = str(payload['CARDINAL_DIRS__CHAR_SOUTH'])
    p_config['CARDINAL_DIRS']['DIAMETER']            = int(payload['CARDINAL_DIRS__DIAMETER'])
    p_config['CARDINAL_DIRS']['OFFSET_X']            = int(payload['CARDINAL_DIRS__OFFSET_X'])
    p_config['CARDINAL_DIRS']['OFFSET_Y']            = int(payload['CARDINAL_DIRS__OFFSET_Y'])
    p_config['CARDINAL_DIRS']['OFFSET_TOP']          = int(payload['CARDINAL_DIRS__OFFSET_TOP'])
    p_config['CARDINAL_DIRS']['OFFSET_LEFT']         = int(payload['CARDINAL_DIRS__OFFSET_LEFT'])
    p_config['CARDINAL_DIRS']['OFFSET_RIGHT']        = int(payload['CARDINAL_DIRS__OFFSET_RIGHT'])
    p_config['CARDINAL_DIRS']['OFFSET_BOTTOM']       = int(payload['CARDINAL_DIRS__OFFSET_BOTTOM'])
    p_config['CARDINAL_DIRS']['OPENCV_FONT_SCALE']   = float(payload['CARDINAL_DIRS__OPENCV_FONT_SCALE'])
    p_config['CARDINAL_DIRS']['PIL_FONT_SIZE']       = int(payload['CARDINAL_DIRS__PIL_FONT_SIZE'])
    p_config['CARDINAL_DIRS']['OUTLINE_CIRCLE']      = bool(payload['CARDINAL_DIRS__OUTLINE_CIRCLE'])
    p_config['IMAGE_CIRCLE_MASK']['ENABLE']          = bool(payload['IMAGE_CIRCLE_MASK__ENABLE'])
    p_config['IMAGE_CIRCLE_MASK']['DIAMETER']        = int(payload['IMAGE_CIRCLE_MASK__DIAMETER'])
    p_config['IMAGE_CIRCLE_MASK']['OFFSET_X']        = int(payload['IMAGE_CIRCLE_MASK__OFFSET_X'])
    p_config['IMAGE_CIRCLE_MASK']['OFFSET_Y']        = int(payload['IMAGE_CIRCLE_MASK__OFFSET_Y'])
    p_config['IMAGE_CIRCLE_MASK']['BLUR']            = int(payload['IMAGE_CIRCLE_MASK__BLUR'])
    p_config['IMAGE_CIRCLE_MASK']['OPACITY']         = int(payload['IMAGE_CIRCLE_MASK__OPACITY'])
    p_config['IMAGE_CIRCLE_MASK']['OUTLINE']         = bool(payload['IMAGE_CIRCLE_MASK__OUTLINE'])
    p_config['IMAGE_CROP_IMAGE_CIRCLE']              = bool(payload['IMAGE_CROP_IMAGE_CIRCLE'])
    p_config['IMAGE_BORDER']['TOP']                  = int(payload['IMAGE_BORDER__TOP'])
    p_config['IMAGE_BORDER']['LEFT']                 = int(payload['IMAGE_BORDER__LEFT'])
    p_config['IMAGE_BORDER']['RIGHT']                = int(payload['IMAGE_BORDER__RIGHT'])
    p_config['IMAGE_BORDER']['BOTTOM']               = int(payload['IMAGE_BORDER__BOTTOM'])
    p_config['MOON_OVERLAY']['ENABLE']               = bool(payload['MOON_OVERLAY__ENABLE'])
    p_config['MOON_OVERLAY']['X']                    = int(payload['MOON_OVERLAY__X'])
    p_config['MOON_OVERLAY']['Y']                    = int(payload['MOON_OVERLAY__Y'])
    p_config['MOON_OVERLAY']['SCALE']                = float(payload['MOON_OVERLAY__SCALE'])
    p_config['MOON_OVERLAY']['DARK_SIDE_SCALE']      = float(payload['MOON_OVERLAY__DARK_SIDE_SCALE'])
    p_config['MOON_OVERLAY']['FLIP_V']               = bool(payload['MOON_OVERLAY__FLIP_V'])
    p_config['MOON_OVERLAY']['FLIP_H']               = bool(payload['MOON_OVERLAY__FLIP_H'])
    p_config['LIGHTGRAPH_OVERLAY']['ENABLE']         = bool(payload['LIGHTGRAPH_OVERLAY__ENABLE'])
    p_config['LIGHTGRAPH_OVERLAY']['GRAPH_HEIGHT']   = int(payload['LIGHTGRAPH_OVERLAY__GRAPH_HEIGHT'])
    p_config['LIGHTGRAPH_OVERLAY']['GRAPH_BORDER']   = int(payload['LIGHTGRAPH_OVERLAY__GRAPH_BORDER'])
    p_config['LIGHTGRAPH_OVERLAY']['Y']              = int(payload['LIGHTGRAPH_OVERLAY__Y'])
    p_config['LIGHTGRAPH_OVERLAY']['OFFSET_X']       = int(payload['LIGHTGRAPH_OVERLAY__OFFSET_X'])
    p_config['LIGHTGRAPH_OVERLAY']['SCALE']          = float(payload['LIGHTGRAPH_OVERLAY__SCALE'])
    p_config['LIGHTGRAPH_OVERLAY']['NOW_MARKER_SIZE']  = int(payload['LIGHTGRAPH_OVERLAY__NOW_MARKER_SIZE'])
    p_config['LIGHTGRAPH_OVERLAY']['OPACITY']        = int(payload['LIGHTGRAPH_OVERLAY__OPACITY'])
    p_config['LIGHTGRAPH_OVERLAY']['PIL_FONT_SIZE']  = int(payload['LIGHTGRAPH_OVERLAY__PIL_FONT_SIZE'])
    p_config['LIGHTGRAPH_OVERLAY']['OPENCV_FONT_SCALE'] = float(payload['LIGHTGRAPH_OVERLAY__OPENCV_FONT_SCALE'])
    p_config['LIGHTGRAPH_OVERLAY']['LABEL']          = bool(payload['LIGHTGRAPH_OVERLAY__LABEL'])
    p_config['LIGHTGRAPH_OVERLAY']['HOUR_LINES']     = bool(payload['LIGHTGRAPH_OVERLAY__HOUR_LINES'])

    # allow extended time for stacking/registration
    p_config['EXPOSURE_PERIOD'] = 120

    # disable these
    p_config['ADSB']['ENABLE']                       = False
    p_config['SATELLITE_TRACK']['ENABLE']            = False

    # SQM_ROI
    sqm_roi_x1 = int(payload['SQM_ROI_X1'])
    sqm_roi_y1 = int(payload['SQM_ROI_Y1'])
    sqm_roi_x2 = int(payload['SQM_ROI_X2'])
    sqm_roi_y2 = int(payload['SQM_ROI_Y2'])

    # the x2 and y2 values must be positive integers in order to be enabled and valid
    if sqm_roi_x2 and sqm_roi_y2:
        p_config['SQM_ROI'] = [sqm_roi_x1, sqm_roi_y1, sqm_roi_x2, sqm_roi_y2]
    else:
        p_config['SQM_ROI'] = []

    # TEXT_PROPERTIES FONT_COLOR
    font_color_str = str(payload['TEXT_PROPERTIES__FONT_COLOR'])
    p_config['TEXT_PROPERTIES']['FONT_COLOR'] = [int(x) for x in font_color_str.split(',')]

    # CARDINAL_DIRS FONT_COLOR
    cardinal_dirs_color_str = str(payload['CARDINAL_DIRS__FONT_COLOR'])
    p_config['CARDINAL_DIRS']['FONT_COLOR'] = [int(x) for x in cardinal_dirs_color_str.split(',')]

    # IMAGE_BORDER COLOR
    image_border__color_str = str(payload['IMAGE_BORDER__COLOR'])
    p_config['IMAGE_BORDER']['COLOR'] = [int(x) for x in image_border__color_str.split(',')]

    # LIGHTGRAPH COLORS
    lightgraph_overlay__day_color_str = str(payload['LIGHTGRAPH_OVERLAY__DAY_COLOR'])
    p_config['LIGHTGRAPH_OVERLAY']['DAY_COLOR'] = [int(x) for x in lightgraph_overlay__day_color_str.split(',')]

    lightgraph_overlay__dusk_color_str = str(payload['LIGHTGRAPH_OVERLAY__DUSK_COLOR'])
    p_config['LIGHTGRAPH_OVERLAY']['DUSK_COLOR'] = [int(x) for x in lightgraph_overlay__dusk_color_str.split(',')]

    lightgraph_overlay__night_color_str = str(payload['LIGHTGRAPH_OVERLAY__NIGHT_COLOR'])
    p_config['LIGHTGRAPH_OVERLAY']['NIGHT_COLOR'] = [int(x) for x in lightgraph_overlay__night_color_str.split(',')]

    lightgraph_overlay__moonmode_color_str = str(payload['LIGHTGRAPH_OVERLAY__MOONMODE_COLOR'])
    p_config['LIGHTGRAPH_OVERLAY']['MOONMODE_COLOR'] = [int(x) for x in lightgraph_overlay__moonmode_color_str.split(',')]

    lightgraph_overlay__hour_color_str = str(payload['LIGHTGRAPH_OVERLAY__HOUR_COLOR'])
    p_config['LIGHTGRAPH_OVERLAY']['HOUR_COLOR'] = [int(x) for x in lightgraph_overlay__hour_color_str.split(',')]

    lightgraph_overlay__border_color_str = str(payload['LIGHTGRAPH_OVERLAY__BORDER_COLOR'])
    p_config['LIGHTGRAPH_OVERLAY']['BORDER_COLOR'] = [int(x) for x in lightgraph_overlay__border_color_str.split(',')]

    lightgraph_overlay__now_color_str = str(payload['LIGHTGRAPH_OVERLAY__NOW_COLOR'])
    p_config['LIGHTGRAPH_OVERLAY']['NOW_COLOR'] = [int(x) for x in lightgraph_overlay__now_color_str.split(',')]

    lightgraph_overlay__font_color_str = str(payload['LIGHTGRAPH_OVERLAY__FONT_COLOR'])
    p_config['LIGHTGRAPH_OVERLAY']['FONT_COLOR'] = [int(x) for x in lightgraph_overlay__font_color_str.split(',')]

    return p_config
