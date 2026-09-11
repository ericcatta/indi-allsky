"""Hybrid-owned initial Full Config form values, without Flask dependencies."""

import json


def build_full_config_form_defaults(config):
    return {
            'CAMERA_INTERFACE'               : config.get('CAMERA_INTERFACE', 'indi'),
            'INDI_SERVER'                    : config.get('INDI_SERVER', 'localhost'),
            'INDI_PORT'                      : config.get('INDI_PORT', 7624),
            'INDI_CAMERA_NAME'               : config.get('INDI_CAMERA_NAME', ''),
            'WEBSITE__TITLE'                 : config.get('WEBSITE', {}).get('TITLE', 'indi-allsky'),
            'OWNER'                          : config.get('OWNER', ''),
            'LENS_NAME'                      : config.get('LENS_NAME', 'AllSky Lens'),
            'LENS_FOCAL_LENGTH'              : config.get('LENS_FOCAL_LENGTH', 2.5),
            'LENS_FOCAL_RATIO'               : config.get('LENS_FOCAL_RATIO', 2.0),
            'LENS_IMAGE_CIRCLE'              : config.get('LENS_IMAGE_CIRCLE', 3000),
            'LENS_OFFSET_X'                  : config.get('LENS_OFFSET_X', 0),
            'LENS_OFFSET_Y'                  : config.get('LENS_OFFSET_Y', 0),
            'LENS_ALTITUDE'                  : config.get('LENS_ALTITUDE', 90.0),
            'LENS_AZIMUTH'                   : config.get('LENS_AZIMUTH', 0.0),
            'CCD_CONFIG__NIGHT__GAIN'        : round(config.get('CCD_CONFIG', {}).get('NIGHT', {}).get('GAIN', 100.0), 2),  # limit to 2 decimals
            'CCD_CONFIG__NIGHT__BINNING'     : config.get('CCD_CONFIG', {}).get('NIGHT', {}).get('BINNING', 1),
            'CCD_CONFIG__MOONMODE__GAIN'     : round(config.get('CCD_CONFIG', {}).get('MOONMODE', {}).get('GAIN', 75.0), 2),  # limit to 2 decimals
            'CCD_CONFIG__MOONMODE__BINNING'  : config.get('CCD_CONFIG', {}).get('MOONMODE', {}).get('BINNING', 1),
            'CCD_CONFIG__DAY__GAIN'          : round(config.get('CCD_CONFIG', {}).get('DAY', {}).get('GAIN', 0.0), 2),  # limit to 2 decimals
            'CCD_CONFIG__DAY__BINNING'       : config.get('CCD_CONFIG', {}).get('DAY', {}).get('BINNING', 1),
            'CCD_CONFIG__AUTO_GAIN_ENABLE'   : config.get('CCD_CONFIG', {}).get('AUTO_GAIN_ENABLE', False),
            'CCD_CONFIG__AUTO_GAIN_LEVELS'   : str(config.get('CCD_CONFIG', {}).get('AUTO_GAIN_LEVELS', 8)),  # string in form, int in config
            'CCD_EXPOSURE_MAX'               : config.get('CCD_EXPOSURE_MAX', 15.0),
            'CCD_EXPOSURE_DEF'               : '{0:.6f}'.format(config.get('CCD_EXPOSURE_DEF', 0.0)),  # force 6 digits of precision
            'CCD_EXPOSURE_MIN'               : '{0:.6f}'.format(config.get('CCD_EXPOSURE_MIN', 0.0)),
            'CCD_EXPOSURE_MIN_DAY'           : '{0:.6f}'.format(config.get('CCD_EXPOSURE_MIN_DAY', 0.0)),
            'CCD_EXPOSURE_TIMEOUT'           : config.get('CCD_EXPOSURE_TIMEOUT', 330),
            'CCD_BIT_DEPTH'                  : str(config.get('CCD_BIT_DEPTH', 0)),  # string in form, int in config
            'EXPOSURE_PERIOD'                : config.get('EXPOSURE_PERIOD', 15.0),
            'EXPOSURE_PERIOD_DAY'            : config.get('EXPOSURE_PERIOD_DAY', 15.0),
            'CAMERA_SQM__ENABLE'             : config.get('CAMERA_SQM', {}).get('ENABLE', False),
            'CAMERA_SQM__ENABLE_DAY'         : config.get('CAMERA_SQM', {}).get('ENABLE_DAY', False),
            'CAMERA_SQM__EXPOSURE'           : '{0:.6f}'.format(config.get('CAMERA_SQM', {}).get('EXPOSURE', 10.0)),  # force 6 digits of precision
            'CAMERA_SQM__GAIN'               : round(config.get('CAMERA_SQM', {}).get('GAIN', 10.0), 2),  # limit to 2 decimals
            'CAMERA_SQM__BINNING'            : config.get('CAMERA_SQM', {}).get('BINNING', 1),
            'CAMERA_SQM__EXPOSURE_PERIOD'    : config.get('CAMERA_SQM', {}).get('EXPOSURE_PERIOD', 900),
            'CAMERA_SQM__MAGNITUDE_OFFSET'   : config.get('CAMERA_SQM', {}).get('MAGNITUDE_OFFSET', 25.0),
            'FOCUS_MODE'                     : config.get('FOCUS_MODE', False),
            'FOCUS_DELAY'                    : config.get('FOCUS_DELAY', 4.0),
            'CFA_PATTERN'                    : config.get('CFA_PATTERN', ''),
            'USE_NIGHT_COLOR'                : config.get('USE_NIGHT_COLOR', True),
            'SCNR_ALGORITHM'                 : config.get('SCNR_ALGORITHM', ''),
            'SCNR_ALGORITHM_DAY'             : config.get('SCNR_ALGORITHM_DAY', ''),
            'SCNR_MTF_MIDTONES'              : config.get('SCNR_MTF_MIDTONES', 0.55),
            'SCNR_MTF_MIDTONES_DAY'          : config.get('SCNR_MTF_MIDTONES_DAY', 0.55),
            'IMAGE_DENOISE'                  : config.get('IMAGE_DENOISE', ''),
            'IMAGE_DENOISE_DAY'              : config.get('IMAGE_DENOISE_DAY', ''),
            'IMAGE_DENOISE_STRENGTH'         : config.get('IMAGE_DENOISE_STRENGTH', 3),
            'IMAGE_DENOISE_STRENGTH_DAY'     : config.get('IMAGE_DENOISE_STRENGTH_DAY', 3),
            'BILATERAL_SIGMA_COLOR'          : config.get('BILATERAL_SIGMA_COLOR', 20),
            'BILATERAL_SIGMA_COLOR_DAY'      : config.get('BILATERAL_SIGMA_COLOR_DAY', 20),
            'BILATERAL_SIGMA_SPACE'          : config.get('BILATERAL_SIGMA_SPACE', 35),
            'BILATERAL_SIGMA_SPACE_DAY'      : config.get('BILATERAL_SIGMA_SPACE_DAY', 35),
            'WBR_FACTOR'                     : config.get('WBR_FACTOR', 1.0),
            'WBG_FACTOR'                     : config.get('WBG_FACTOR', 1.0),
            'WBB_FACTOR'                     : config.get('WBB_FACTOR', 1.0),
            'WBR_FACTOR_DAY'                 : config.get('WBR_FACTOR_DAY', 1.0),
            'WBG_FACTOR_DAY'                 : config.get('WBG_FACTOR_DAY', 1.0),
            'WBB_FACTOR_DAY'                 : config.get('WBB_FACTOR_DAY', 1.0),
            'AUTO_WB'                        : config.get('AUTO_WB', False),
            'AUTO_WB_DAY'                    : config.get('AUTO_WB_DAY', False),
            'WBR_MTF_MIDTONES'               : config.get('WBR_MTF_MIDTONES', 0.5),
            'WBG_MTF_MIDTONES'               : config.get('WBG_MTF_MIDTONES', 0.5),
            'WBB_MTF_MIDTONES'               : config.get('WBB_MTF_MIDTONES', 0.5),
            'WBR_MTF_MIDTONES_DAY'           : config.get('WBR_MTF_MIDTONES_DAY', 0.5),
            'WBG_MTF_MIDTONES_DAY'           : config.get('WBG_MTF_MIDTONES_DAY', 0.5),
            'WBB_MTF_MIDTONES_DAY'           : config.get('WBB_MTF_MIDTONES_DAY', 0.5),
            'SATURATION_FACTOR'              : config.get('SATURATION_FACTOR', 1.0),
            'SATURATION_FACTOR_DAY'          : config.get('SATURATION_FACTOR_DAY', 1.0),
            'GAMMA_CORRECTION'               : config.get('GAMMA_CORRECTION', 1.0),
            'GAMMA_CORRECTION_DAY'           : config.get('GAMMA_CORRECTION_DAY', 1.0),
            'SHARPEN_AMOUNT'                 : config.get('SHARPEN_AMOUNT', 0.0),
            'SHARPEN_AMOUNT_DAY'             : config.get('SHARPEN_AMOUNT_DAY', 0.0),
            'CCD_COOLING'                    : config.get('CCD_COOLING', False),
            'CCD_COOLING_DAY'                : config.get('CCD_COOLING_DAY', False),
            'CCD_TEMP'                       : config.get('CCD_TEMP', 15.0),
            'CCD_TEMP_DAY'                   : config.get('CCD_TEMP_DAY', 35.0),
            'TEMP_DISPLAY'                   : config.get('TEMP_DISPLAY', 'c'),
            'PRESSURE_DISPLAY'               : config.get('PRESSURE_DISPLAY', 'hpa'),
            'WINDSPEED_DISPLAY'              : config.get('WINDSPEED_DISPLAY', 'ms'),
            'CCD_TEMP_SCRIPT'                : config.get('CCD_TEMP_SCRIPT', ''),
            'GPS_ENABLE'                     : config.get('GPS_ENABLE', False),
            'TARGET_ADU'                     : config.get('TARGET_ADU', 75),
            'TARGET_ADU_DAY'                 : config.get('TARGET_ADU_DAY', 75),
            'TARGET_ADU_DEV'                 : config.get('TARGET_ADU_DEV', 10),
            'TARGET_ADU_DEV_DAY'             : config.get('TARGET_ADU_DEV_DAY', 20),
            'ADU_FOV_DIV'                    : str(config.get('ADU_FOV_DIV', 4)),  # string in form, int in config
            'SQM_FOV_DIV'                    : str(config.get('SQM_FOV_DIV', 4)),  # string in form, int in config
            'DETECT_STARS'                   : config.get('DETECT_STARS', True),
            'DETECT_STARS_THOLD'             : config.get('DETECT_STARS_THOLD', 0.6),
            'DETECT_METEORS'                 : config.get('DETECT_METEORS', False),
            'DETECT_METEORS_THOLD'           : config.get('DETECT_METEORS_THOLD', 125),
            'DETECT_MASK'                    : config.get('DETECT_MASK', ''),
            'DETECT_DRAW'                    : config.get('DETECT_DRAW', False),
            'EVENT_CANDIDATE_TRIGGERS__ENABLED'                 : config.get('EVENT_CANDIDATE_TRIGGERS', {}).get('enabled', False),
            'EVENT_CANDIDATE_TRIGGERS__MAX_CANDIDATES_PER_HOUR' : config.get('EVENT_CANDIDATE_TRIGGERS', {}).get('max_candidates_per_hour', 100),
            'LOGO_OVERLAY'                   : config.get('LOGO_OVERLAY', ''),
            'HEALTHCHECK__DISK_USAGE'        : config.get('HEALTHCHECK', {}).get('DISK_USAGE', 90.0),
            'HEALTHCHECK__SWAP_USAGE'        : config.get('HEALTHCHECK', {}).get('SWAP_USAGE', 90.0),
            'LOCATION_NAME'                  : config.get('LOCATION_NAME', ''),
            'LOCATION_LATITUDE'              : '{0:+0.3f}'.format(config.get('LOCATION_LATITUDE', 0.0)),
            'LOCATION_LONGITUDE'             : '{0:+0.3f}'.format(config.get('LOCATION_LONGITUDE', 0.0)),
            'LOCATION_ELEVATION'             : config.get('LOCATION_ELEVATION', 0),
            'TIMELAPSE_ENABLE'               : config.get('TIMELAPSE_ENABLE', True),
            'TIMELAPSE_SKIP_FRAMES'          : config.get('TIMELAPSE_SKIP_FRAMES', 4),
            'TIMELAPSE__PRE_PROCESSOR'       : config.get('TIMELAPSE', {}).get('PRE_PROCESSOR', 'standard'),
            'TIMELAPSE__PRE_PROCESSOR_DAY'   : config.get('TIMELAPSE', {}).get('PRE_PROCESSOR_DAY', 'standard'),
            'TIMELAPSE__IMAGE_CIRCLE'        : config.get('TIMELAPSE', {}).get('IMAGE_CIRCLE', 2000),
            'TIMELAPSE__KEOGRAM_RATIO'       : config.get('TIMELAPSE', {}).get('KEOGRAM_RATIO', 0.15),
            'TIMELAPSE__PRE_SCALE'           : config.get('TIMELAPSE', {}).get('PRE_SCALE', 50),
            'TIMELAPSE__FFMPEG_REPORT'       : config.get('TIMELAPSE', {}).get('FFMPEG_REPORT', False),
            'TIMELAPSE__USE_NIGHT_CONFIG'    : config.get('TIMELAPSE', {}).get('USE_NIGHT_CONFIG', True),
            'CAPTURE_PAUSE'                  : config.get('CAPTURE_PAUSE', False),
            'DAYTIME_CAPTURE'                : config.get('DAYTIME_CAPTURE', True),
            'DAYTIME_CAPTURE_SAVE'           : config.get('DAYTIME_CAPTURE_SAVE', True),
            'DAYTIME_TIMELAPSE'              : config.get('DAYTIME_TIMELAPSE', True),
            'DAYTIME_CONTRAST_ENHANCE'       : config.get('DAYTIME_CONTRAST_ENHANCE', False),
            'NIGHT_CONTRAST_ENHANCE'         : config.get('NIGHT_CONTRAST_ENHANCE', False),
            'CONTRAST_ENHANCE_16BIT'         : config.get('CONTRAST_ENHANCE_16BIT', False),
            'CLAHE_CLIPLIMIT'                : config.get('CLAHE_CLIPLIMIT', 3.0),
            'CLAHE_GRIDSIZE'                 : config.get('CLAHE_GRIDSIZE', 8),
            'NIGHT_SUN_ALT_DEG'              : '{0:+0.1f}'.format(config.get('NIGHT_SUN_ALT_DEG', -6.0)),
            'NIGHT_MOONMODE_ALT_DEG'         : '{0:+0.1f}'.format(config.get('NIGHT_MOONMODE_ALT_DEG', 5.0)),
            'NIGHT_MOONMODE_PHASE'           : config.get('NIGHT_MOONMODE_PHASE', 50.0),
            'WEB_STATUS_TEMPLATE'            : config.get('WEB_STATUS_TEMPLATE', ''),
            'WEB_EXTRA_TEXT'                 : config.get('WEB_EXTRA_TEXT', ''),
            'WEB_NONLOCAL_IMAGES'            : config.get('WEB_NONLOCAL_IMAGES', False),
            'WEB_LOCAL_IMAGES_ADMIN'         : config.get('WEB_LOCAL_IMAGES_ADMIN', False),
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
            'IMAGE_STRETCH__SPLIT'           : config.get('IMAGE_STRETCH', {}).get('SPLIT', False),
            'IMAGE_STRETCH__MOONMODE'        : config.get('IMAGE_STRETCH', {}).get('MOONMODE', False),
            'IMAGE_STRETCH__DAYTIME'         : config.get('IMAGE_STRETCH', {}).get('DAYTIME', False),
            'KEOGRAM_ANGLE'                  : config.get('KEOGRAM_ANGLE', 0.0),
            'KEOGRAM_H_SCALE'                : config.get('KEOGRAM_H_SCALE', 100),
            'KEOGRAM_V_SCALE'                : config.get('KEOGRAM_V_SCALE', 33),
            'KEOGRAM_CROP_TOP'               : config.get('KEOGRAM_CROP_TOP', 0),
            'KEOGRAM_CROP_BOTTOM'            : config.get('KEOGRAM_CROP_BOTTOM', 0),
            'KEOGRAM_LABEL'                  : config.get('KEOGRAM_LABEL', True),
            'LONGTERM_KEOGRAM__ENABLE'       : config.get('LONGTERM_KEOGRAM', {}).get('ENABLE', True),
            'LONGTERM_KEOGRAM__OFFSET_X'     : config.get('LONGTERM_KEOGRAM', {}).get('OFFSET_X', 0),
            'LONGTERM_KEOGRAM__OFFSET_Y'     : config.get('LONGTERM_KEOGRAM', {}).get('OFFSET_Y', 0),
            'LONGTERM_KEOGRAM__OPENCV_FONT_SCALE'    : config.get('LONGTERM_KEOGRAM', {}).get('OPENCV_FONT_SCALE', 0.8),
            'LONGTERM_KEOGRAM__PIL_FONT_SIZE'        : config.get('LONGTERM_KEOGRAM', {}).get('PIL_FONT_SIZE', 30),
            'LONGTERM_KEOGRAM__MONTH_LABEL_TEMPLATE' : config.get('LONGTERM_KEOGRAM', {}).get('MONTH_LABEL_TEMPLATE', '{month:%B %Y}'),
            'REALTIME_KEOGRAM__MAX_ENTRIES'  : config.get('REALTIME_KEOGRAM', {}).get('MAX_ENTRIES', 1000),
            'REALTIME_KEOGRAM__SAVE_INTERVAL': config.get('REALTIME_KEOGRAM', {}).get('SAVE_INTERVAL', 25),
            'REALTIME_KEOGRAM__LABEL'        : config.get('REALTIME_KEOGRAM', {}).get('LABEL', False),
            'STARTRAILS_SUN_ALT_THOLD'       : '{0:+0.1f}'.format(config.get('STARTRAILS_SUN_ALT_THOLD', -15.0)),
            'STARTRAILS_MOONMODE_THOLD'      : config.get('STARTRAILS_MOONMODE_THOLD', True),
            'STARTRAILS_MOON_ALT_THOLD'      : '{0:+0.1f}'.format(config.get('STARTRAILS_MOON_ALT_THOLD', 91.0)),
            'STARTRAILS_MOON_PHASE_THOLD'    : config.get('STARTRAILS_MOON_PHASE_THOLD', 101.0),
            'STARTRAILS_MAX_ADU'             : config.get('STARTRAILS_MAX_ADU', 65),
            'STARTRAILS_MASK_THOLD'          : config.get('STARTRAILS_MASK_THOLD', 255),
            'STARTRAILS_PIXEL_THOLD'         : config.get('STARTRAILS_PIXEL_THOLD', 1.0),
            'STARTRAILS_MIN_STARS'           : config.get('STARTRAILS_MIN_STARS', 0),
            'STARTRAILS_TIMELAPSE'           : config.get('STARTRAILS_TIMELAPSE', True),
            'STARTRAILS_TIMELAPSE_MINFRAMES' : config.get('STARTRAILS_TIMELAPSE_MINFRAMES', 250),
            'STARTRAILS_USE_DB_DATA'         : config.get('STARTRAILS_USE_DB_DATA', True),
            'STARTRAILS__IMAGE_CIRCLE_MASK_ENABLE'  : config.get('STARTRAILS', {}).get('IMAGE_CIRCLE_MASK_ENABLE', False),
            'STARTRAILS__IMAGE_CIRCLE_MASK_DIAMETER': config.get('STARTRAILS', {}).get('IMAGE_CIRCLE_MASK_DIAMETER', 3000),
            'STARTRAILS__IMAGE_CIRCLE_MASK_BLUR'    : config.get('STARTRAILS', {}).get('IMAGE_CIRCLE_MASK_BLUR', 35),
            'STARTRAILS__IMAGE_CIRCLE_MASK_OPACITY' : config.get('STARTRAILS', {}).get('IMAGE_CIRCLE_MASK_OPACITY', 100),
            'IMAGE_CALIBRATE_DARK'           : config.get('IMAGE_CALIBRATE_DARK', True),
            'IMAGE_CALIBRATE_BPM'            : config.get('IMAGE_CALIBRATE_BPM', False),
            'IMAGE_CALIBRATE_FIX_HOLES'      : config.get('IMAGE_CALIBRATE_FIX_HOLES', False),
            'IMAGE_CALIBRATE_HOLE_THOLD'     : config.get('IMAGE_CALIBRATE_HOLE_THOLD', 30),
            'IMAGE_CALIBRATE_MANUAL_OFFSET'  : config.get('IMAGE_CALIBRATE_MANUAL_OFFSET', 0),
            'IMAGE_SAVE_FITS_PRE_DARK'       : config.get('IMAGE_SAVE_FITS_PRE_DARK', False),
            'PRIVACY_MODE'                   : config.get('PRIVACY_MODE', False),
            'IMAGE_EXIF_PRIVACY'             : config.get('IMAGE_EXIF_PRIVACY', False),
            'IMAGE_FILE_TYPE'                : config.get('IMAGE_FILE_TYPE', 'jpg'),
            'IMAGE_FILE_COMPRESSION__JPG'    : config.get('IMAGE_FILE_COMPRESSION', {}).get('jpg', 90),
            'IMAGE_FILE_COMPRESSION__PNG'    : config.get('IMAGE_FILE_COMPRESSION', {}).get('png', 5),
            'IMAGE_FILE_COMPRESSION__TIF'    : 'LZW',
            'IMAGE_FOLDER'                   : config.get('IMAGE_FOLDER', '/var/www/html/allsky/images'),
            'VARLIB_FOLDER'                  : config.get('VARLIB_FOLDER', '/var/lib/indi-allsky'),
            'IMAGE_LABEL_TEMPLATE'           : config.get('IMAGE_LABEL_TEMPLATE', ''),
            'IMAGE_EXTRA_TEXT'               : config.get('IMAGE_EXTRA_TEXT', ''),
            'IMAGE_ROTATE'                   : config.get('IMAGE_ROTATE', ''),
            'IMAGE_ROTATE_ANGLE'             : config.get('IMAGE_ROTATE_ANGLE', 0),
            'IMAGE_ROTATE_KEEP_SIZE'         : config.get('IMAGE_ROTATE_KEEP_SIZE', False),
            #'IMAGE_ROTATE_WITH_OFFSET'       : config.get('IMAGE_ROTATE_WITH_OFFSET', False),
            'IMAGE_FLIP_V'                   : config.get('IMAGE_FLIP_V', True),
            'IMAGE_FLIP_H'                   : config.get('IMAGE_FLIP_H', True),
            'IMAGE_SCALE'                    : config.get('IMAGE_SCALE', 100),
            'IMAGE_COLORMAP'                 : config.get('IMAGE_COLORMAP', ''),
            'IMAGE_CIRCLE_MASK__ENABLE'      : config.get('IMAGE_CIRCLE_MASK', {}).get('ENABLE', False),
            'IMAGE_CIRCLE_MASK__DIAMETER'    : config.get('IMAGE_CIRCLE_MASK', {}).get('DIAMETER', 3000),
            'IMAGE_CIRCLE_MASK__OFFSET_X'    : config.get('IMAGE_CIRCLE_MASK', {}).get('OFFSET_X', 0),
            'IMAGE_CIRCLE_MASK__OFFSET_Y'    : config.get('IMAGE_CIRCLE_MASK', {}).get('OFFSET_Y', 0),
            'IMAGE_CIRCLE_MASK__BLUR'        : config.get('IMAGE_CIRCLE_MASK', {}).get('BLUR', 35),
            'IMAGE_CIRCLE_MASK__OPACITY'     : config.get('IMAGE_CIRCLE_MASK', {}).get('OPACITY', 100),
            'IMAGE_CIRCLE_MASK__OUTLINE'     : config.get('IMAGE_CIRCLE_MASK', {}).get('OUTLINE', False),
            'IMAGE_CROP_IMAGE_CIRCLE'        : config.get('IMAGE_CROP_IMAGE_CIRCLE', False),
            'FISH2PANO__ENABLE'              : config.get('FISH2PANO', {}).get('ENABLE', True),
            'FISH2PANO__DIAMETER'            : config.get('FISH2PANO', {}).get('DIAMETER', 3000),
            'FISH2PANO__OFFSET_X'            : config.get('FISH2PANO', {}).get('OFFSET_X', 0),
            'FISH2PANO__OFFSET_Y'            : config.get('FISH2PANO', {}).get('OFFSET_Y', 0),
            'FISH2PANO__ROTATE_ANGLE'        : config.get('FISH2PANO', {}).get('ROTATE_ANGLE', -90),
            'FISH2PANO__SCALE'               : config.get('FISH2PANO', {}).get('SCALE', 0.5),
            'FISH2PANO__MODULUS'             : config.get('FISH2PANO', {}).get('MODULUS', 2),
            'FISH2PANO__FLIP_H'              : config.get('FISH2PANO', {}).get('FLIP_H', False),
            'FISH2PANO__ENABLE_CARDINAL_DIRS': config.get('FISH2PANO', {}).get('ENABLE_CARDINAL_DIRS', True),
            'FISH2PANO__DIRS_OFFSET_BOTTOM'  : config.get('FISH2PANO', {}).get('DIRS_OFFSET_BOTTOM', 25),
            'FISH2PANO__OPENCV_FONT_SCALE'   : config.get('FISH2PANO', {}).get('OPENCV_FONT_SCALE', 0.8),
            'FISH2PANO__PIL_FONT_SIZE'       : config.get('FISH2PANO', {}).get('PIL_FONT_SIZE', 30),
            'IMAGE_SAVE_FITS'                : config.get('IMAGE_SAVE_FITS', False),
            'IMAGE_SAVE_FITS_COMPRESSED'     : config.get('IMAGE_SAVE_FITS_COMPRESSED', False),
            'IMAGE_SAVE_FITS_PERIOD'         : str(config.get('IMAGE_SAVE_FITS_PERIOD', 7200)),  # string in form, int in config
            'NIGHT_GRAYSCALE'                : config.get('NIGHT_GRAYSCALE', False),
            'DAYTIME_GRAYSCALE'              : config.get('DAYTIME_GRAYSCALE', False),
            'MOON_OVERLAY__ENABLE'           : config.get('MOON_OVERLAY', {}).get('ENABLE', True),
            'MOON_OVERLAY__X'                : config.get('MOON_OVERLAY', {}).get('X', -500),
            'MOON_OVERLAY__Y'                : config.get('MOON_OVERLAY', {}).get('Y', -200),
            'MOON_OVERLAY__SCALE'            : config.get('MOON_OVERLAY', {}).get('SCALE', 0.5),
            'MOON_OVERLAY__DARK_SIDE_SCALE'  : config.get('MOON_OVERLAY', {}).get('DARK_SIDE_SCALE', 0.4),
            'MOON_OVERLAY__FLIP_V'           : config.get('MOON_OVERLAY', {}).get('FLIP_V', False),
            'MOON_OVERLAY__FLIP_H'           : config.get('MOON_OVERLAY', {}).get('FLIP_H', False),
            'LIGHTGRAPH_OVERLAY__ENABLE'     : config.get('LIGHTGRAPH_OVERLAY', {}).get('ENABLE', False),
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
            'IMAGE_OVERLAY__ENABLE'          : config.get('IMAGE_OVERLAY', {}).get('ENABLE', False),
            'IMAGE_OVERLAY__LOAD_INTERVAL'   : config.get('IMAGE_OVERLAY', {}).get('LOAD_INTERVAL', 600),
            'IMAGE_OVERLAY__A_URL'           : config.get('IMAGE_OVERLAY', {}).get('A_URL', ''),
            'IMAGE_OVERLAY__A_IMAGE_FILE_TYPE' : config.get('IMAGE_OVERLAY', {}).get('A_IMAGE_FILE_TYPE', 'jpg'),
            'IMAGE_OVERLAY__A_WIDTH'         : config.get('IMAGE_OVERLAY', {}).get('A_WIDTH', 250),
            'IMAGE_OVERLAY__A_HEIGHT'        : config.get('IMAGE_OVERLAY', {}).get('A_HEIGHT', 250),
            'IMAGE_OVERLAY__A_X'             : config.get('IMAGE_OVERLAY', {}).get('A_X', 300),
            'IMAGE_OVERLAY__A_Y'             : config.get('IMAGE_OVERLAY', {}).get('A_Y', -300),
            'IMAGE_OVERLAY__A_USERNAME'      : config.get('IMAGE_OVERLAY', {}).get('A_USERNAME', ''),
            'IMAGE_OVERLAY__A_PASSWORD'      : config.get('IMAGE_OVERLAY', {}).get('A_PASSWORD', ''),
            'IMAGE_EXPORT_RAW'               : config.get('IMAGE_EXPORT_RAW', ''),
            'IMAGE_EXPORT_FOLDER'            : config.get('IMAGE_EXPORT_FOLDER', '/var/www/html/allsky/images/export'),
            'IMAGE_EXPORT_FLIP_V'            : config.get('IMAGE_EXPORT_FLIP_V', False),
            'IMAGE_EXPORT_FLIP_H'            : config.get('IMAGE_EXPORT_FLIP_H', False),
            'IMAGE_STACK_METHOD'             : config.get('IMAGE_STACK_METHOD', 'maximum'),
            'IMAGE_STACK_COUNT'              : str(config.get('IMAGE_STACK_COUNT', 1)),  # string in form, int in config
            'IMAGE_STACK_ALIGN'              : config.get('IMAGE_STACK_ALIGN', False),
            'IMAGE_ALIGN_DETECTSIGMA'        : config.get('IMAGE_ALIGN_DETECTSIGMA', 5),
            'IMAGE_ALIGN_POINTS'             : config.get('IMAGE_ALIGN_POINTS', 50),
            'IMAGE_ALIGN_SOURCEMINAREA'      : config.get('IMAGE_ALIGN_SOURCEMINAREA', 10),
            'IMAGE_STACK_SPLIT'              : config.get('IMAGE_STACK_SPLIT', False),
            'IMAGE_STACK_MOONMODE'           : config.get('IMAGE_STACK_MOONMODE', False),
            'IMAGE_STACK_DAY'                : config.get('IMAGE_STACK_DAY', False),
            'IMAGE_QUEUE_MAX'                : config.get('IMAGE_QUEUE_MAX', 3),
            'IMAGE_QUEUE_MIN'                : config.get('IMAGE_QUEUE_MIN', 1),
            'IMAGE_QUEUE_BACKOFF'            : config.get('IMAGE_QUEUE_BACKOFF', 0.5),
            'IMAGE_SAVE_HOOK_PRE'            : config.get('IMAGE_SAVE_HOOK_PRE', ''),
            'IMAGE_SAVE_HOOK_POST'           : config.get('IMAGE_SAVE_HOOK_POST', ''),
            'IMAGE_SAVE_HOOK_TIMEOUT'        : config.get('IMAGE_SAVE_HOOK_TIMEOUT', 5),
            'CAPTURE_HOOK_PRE'               : config.get('CAPTURE_HOOK_PRE', ''),
            'CAPTURE_HOOK_TIMEOUT'           : config.get('CAPTURE_HOOK_TIMEOUT', 5),
            'BACKUP_DB_PERIOD_DAYS'          : config.get('BACKUP_DB_PERIOD_DAYS', 7),
            'IMAGE_EXPIRE_DAYS'              : config.get('IMAGE_EXPIRE_DAYS', 10),
            'IMAGE_RAW_EXPIRE_DAYS'          : config.get('IMAGE_RAW_EXPIRE_DAYS', 10),
            'IMAGE_FITS_EXPIRE_DAYS'         : config.get('IMAGE_FITS_EXPIRE_DAYS', 10),
            'TIMELAPSE_EXPIRE_DAYS'          : config.get('TIMELAPSE_EXPIRE_DAYS', 365),
            'TIMELAPSE_OVERWRITE'            : config.get('TIMELAPSE_OVERWRITE', False),
            'FFMPEG_FRAMERATE'               : config.get('FFMPEG_FRAMERATE', 25),
            'FFMPEG_FRAMERATE_DAY'           : config.get('FFMPEG_FRAMERATE_DAY', 25),
            'FFMPEG_BITRATE'                 : config.get('FFMPEG_BITRATE', '5000k'),
            'FFMPEG_BITRATE_DAY'             : config.get('FFMPEG_BITRATE_DAY', '5000k'),
            'FFMPEG_VFSCALE'                 : config.get('FFMPEG_VFSCALE', ''),
            'FFMPEG_VFSCALE_DAY'             : config.get('FFMPEG_VFSCALE_DAY', ''),
            'FFMPEG_VFSCALE_STARTRAIL'       : config.get('FFMPEG_VFSCALE_STARTRAIL', ''),
            'FFMPEG_CODEC'                   : config.get('FFMPEG_CODEC', 'libx264'),
            'FFMPEG_EXTRA_OPTIONS'           : config.get('FFMPEG_EXTRA_OPTIONS', '-level 3.1'),
            'FFMPEG_EXTRA_OPTIONS_DAY'       : config.get('FFMPEG_EXTRA_OPTIONS_DAY', '-level 3.1'),
            'IMAGE_LABEL_SYSTEM'             : config.get('IMAGE_LABEL_SYSTEM', 'pillow'),
            'TEXT_PROPERTIES__FONT_FACE'     : config.get('TEXT_PROPERTIES', {}).get('FONT_FACE', 'FONT_HERSHEY_SIMPLEX'),
            'TEXT_PROPERTIES__FONT_SCALE'    : config.get('TEXT_PROPERTIES', {}).get('FONT_SCALE', 0.8),
            'TEXT_PROPERTIES__FONT_THICKNESS': config.get('TEXT_PROPERTIES', {}).get('FONT_THICKNESS', 1),
            'TEXT_PROPERTIES__FONT_OUTLINE'  : config.get('TEXT_PROPERTIES', {}).get('FONT_OUTLINE', True),
            'TEXT_PROPERTIES__FONT_HEIGHT'   : config.get('TEXT_PROPERTIES', {}).get('FONT_HEIGHT', 30),
            'TEXT_PROPERTIES__FONT_X'        : config.get('TEXT_PROPERTIES', {}).get('FONT_X', 15),
            'TEXT_PROPERTIES__FONT_Y'        : config.get('TEXT_PROPERTIES', {}).get('FONT_Y', 30),
            'TEXT_PROPERTIES__PIL_FONT_FILE' : config.get('TEXT_PROPERTIES', {}).get('PIL_FONT_FILE', 'fonts-freefont-ttf/FreeSans.ttf'),
            'TEXT_PROPERTIES__PIL_FONT_CUSTOM' : config.get('TEXT_PROPERTIES', {}).get('PIL_FONT_CUSTOM', ''),
            'TEXT_PROPERTIES__PIL_FONT_SIZE' : config.get('TEXT_PROPERTIES', {}).get('PIL_FONT_SIZE', 30),
            'CARDINAL_DIRS__ENABLE'          : config.get('CARDINAL_DIRS', {}).get('ENABLE', True),
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
            'ORB_PROPERTIES__MODE'           : config.get('ORB_PROPERTIES', {}).get('MODE', 'ha'),
            'ORB_PROPERTIES__RADIUS'         : config.get('ORB_PROPERTIES', {}).get('RADIUS', 9),
            'ORB_PROPERTIES__AZ_OFFSET'      : config.get('ORB_PROPERTIES', {}).get('AZ_OFFSET', 0.0),
            'ORB_PROPERTIES__RETROGRADE'     : config.get('ORB_PROPERTIES', {}).get('RETROGRADE', False),
            'IMAGE_BORDER__TOP'              : config.get('IMAGE_BORDER', {}).get('TOP', 0),
            'IMAGE_BORDER__LEFT'             : config.get('IMAGE_BORDER', {}).get('LEFT', 0),
            'IMAGE_BORDER__RIGHT'            : config.get('IMAGE_BORDER', {}).get('RIGHT', 0),
            'IMAGE_BORDER__BOTTOM'           : config.get('IMAGE_BORDER', {}).get('BOTTOM', 0),
            'UPLOAD_WORKERS'                 : config.get('UPLOAD_WORKERS', 2),
            'FILETRANSFER__CLASSNAME'        : config.get('FILETRANSFER', {}).get('CLASSNAME', 'pycurl_sftp'),
            'FILETRANSFER__HOST'             : config.get('FILETRANSFER', {}).get('HOST', ''),
            'FILETRANSFER__PORT'             : config.get('FILETRANSFER', {}).get('PORT', 0),
            'FILETRANSFER__USERNAME'         : config.get('FILETRANSFER', {}).get('USERNAME', ''),
            'FILETRANSFER__PASSWORD'         : config.get('FILETRANSFER', {}).get('PASSWORD', ''),
            'FILETRANSFER__PRIVATE_KEY'      : config.get('FILETRANSFER', {}).get('PRIVATE_KEY', ''),
            'FILETRANSFER__PUBLIC_KEY'       : config.get('FILETRANSFER', {}).get('PUBLIC_KEY', ''),
            'FILETRANSFER__CONNECT_TIMEOUT'  : config.get('FILETRANSFER', {}).get('CONNECT_TIMEOUT', 10.0),
            'FILETRANSFER__TIMEOUT'          : config.get('FILETRANSFER', {}).get('TIMEOUT', 60.0),
            'FILETRANSFER__CERT_BYPASS'      : config.get('FILETRANSFER', {}).get('CERT_BYPASS', True),
            'FILETRANSFER__ATOMIC_TRANSFERS' : config.get('FILETRANSFER', {}).get('ATOMIC_TRANSFERS', False),
            'FILETRANSFER__FORCE_IPV4'       : config.get('FILETRANSFER', {}).get('FORCE_IPV4', False),
            'FILETRANSFER__FORCE_IPV6'       : config.get('FILETRANSFER', {}).get('FORCE_IPV6', False),
            'FILETRANSFER__REMOTE_IMAGE_NAME'         : config.get('FILETRANSFER', {}).get('REMOTE_IMAGE_NAME', 'image_ccd{camera_id:d}_{ts:%Y%m%d_%H%M%S}.{ext}'),
            'FILETRANSFER__REMOTE_IMAGE_FOLDER'       : config.get('FILETRANSFER', {}).get('REMOTE_IMAGE_FOLDER', '/home/allsky/upload/allsky/images/{day_date:%Y%m%d}/{timeofday:s}/{ts:%H}'),
            'FILETRANSFER__REMOTE_PANORAMA_NAME'      : config.get('FILETRANSFER', {}).get('REMOTE_PANORAMA_NAME', 'panorama_ccd{camera_id:d}_{ts:%Y%m%d_%H%M%S}.{ext}'),
            'FILETRANSFER__REMOTE_PANORAMA_FOLDER'    : config.get('FILETRANSFER', {}).get('REMOTE_PANORAMA_FOLDER', '/home/allsky/upload/allsky/panoramas/{day_date:%Y%m%d}/{timeofday:s}/{ts:%H}'),
            'FILETRANSFER__REMOTE_METADATA_NAME'      : config.get('FILETRANSFER', {}).get('REMOTE_METADATA_NAME', 'latest_metadata.json'),
            'FILETRANSFER__REMOTE_METADATA_FOLDER'    : config.get('FILETRANSFER', {}).get('REMOTE_METADATA_FOLDER', '/home/allsky/upload/allsky'),
            'FILETRANSFER__REMOTE_RAW_NAME'           : config.get('FILETRANSFER', {}).get('REMOTE_RAW_NAME', 'raw_ccd{camera_id:d}_{ts:%Y%m%d_%H%M%S}.{ext}'),
            'FILETRANSFER__REMOTE_RAW_FOLDER'         : config.get('FILETRANSFER', {}).get('REMOTE_RAW_FOLDER', '/home/allsky/upload/allsky/export/{day_date:%Y%m%d}/{timeofday:s}/{ts:%H}'),
            'FILETRANSFER__REMOTE_FITS_NAME'          : config.get('FILETRANSFER', {}).get('REMOTE_FITS_NAME', 'image_ccd{camera_id:d}_{ts:%Y%m%d_%H%M%S}.{ext}'),
            'FILETRANSFER__REMOTE_FITS_FOLDER'        : config.get('FILETRANSFER', {}).get('REMOTE_FITS_FOLDER', '/home/allsky/upload/allsky/fits/{day_date:%Y%m%d}/{timeofday:s}/{ts:%H}'),
            'FILETRANSFER__REMOTE_VIDEO_NAME'         : config.get('FILETRANSFER', {}).get('REMOTE_VIDEO_NAME', 'allsky-timelapse_ccd{camera_id:d}_{day_date:%Y%m%d}_{timeofday:s}.{ext}'),
            'FILETRANSFER__REMOTE_VIDEO_FOLDER'       : config.get('FILETRANSFER', {}).get('REMOTE_VIDEO_FOLDER', '/home/allsky/upload/allsky/videos/{day_date:%Y%m%d}'),
            'FILETRANSFER__REMOTE_MINI_VIDEO_NAME'    : config.get('FILETRANSFER', {}).get('REMOTE_MINI_VIDEO_NAME', 'allsky-minitimelapse_ccd{camera_id:d}_{day_date:%Y%m%d}_{timeofday:s}.{ext}'),
            'FILETRANSFER__REMOTE_MINI_VIDEO_FOLDER'  : config.get('FILETRANSFER', {}).get('REMOTE_MINI_VIDEO_FOLDER', '/home/allsky/upload/allsky/videos/{day_date:%Y%m%d}'),
            'FILETRANSFER__REMOTE_KEOGRAM_NAME'       : config.get('FILETRANSFER', {}).get('REMOTE_KEOGRAM_NAME', 'allsky-keogram_ccd{camera_id:d}_{day_date:%Y%m%d}_{timeofday:s}.{ext}'),
            'FILETRANSFER__REMOTE_KEOGRAM_FOLDER'     : config.get('FILETRANSFER', {}).get('REMOTE_KEOGRAM_FOLDER', '/home/allsky/upload/allsky/keograms/{day_date:%Y%m%d}'),
            'FILETRANSFER__REMOTE_STARTRAIL_NAME'     : config.get('FILETRANSFER', {}).get('REMOTE_STARTRAIL_NAME', 'allsky-startrail_ccd{camera_id:d}_{day_date:%Y%m%d}_{timeofday:s}.{ext}'),
            'FILETRANSFER__REMOTE_STARTRAIL_FOLDER'   : config.get('FILETRANSFER', {}).get('REMOTE_STARTRAIL_FOLDER', '/home/allsky/upload/allsky/startrails/{day_date:%Y%m%d}'),
            'FILETRANSFER__REMOTE_STARTRAIL_VIDEO_NAME'   : config.get('FILETRANSFER', {}).get('REMOTE_STARTRAIL_VIDEO_NAME', 'allsky-startrail_timelapse_ccd{camera_id:d}_{day_date:%Y%m%d}_{timeofday:s}.{ext}'),
            'FILETRANSFER__REMOTE_STARTRAIL_VIDEO_FOLDER' : config.get('FILETRANSFER', {}).get('REMOTE_STARTRAIL_VIDEO_FOLDER', '/home/allsky/upload/allsky/videos/{day_date:%Y%m%d}'),
            'FILETRANSFER__REMOTE_PANORAMA_VIDEO_NAME'    : config.get('FILETRANSFER', {}).get('REMOTE_PANORAMA_VIDEO_NAME', 'allsky-panorama_timelapse_ccd{camera_id:d}_{day_date:%Y%m%d}_{timeofday:s}.{ext}'),
            'FILETRANSFER__REMOTE_PANORAMA_VIDEO_FOLDER'  : config.get('FILETRANSFER', {}).get('REMOTE_PANORAMA_VIDEO_FOLDER', '/home/allsky/upload/allsky/videos/{day_date:%Y%m%d}'),
            'FILETRANSFER__REMOTE_REALTIME_KEOGRAM_NAME'  : config.get('FILETRANSFER', {}).get('REMOTE_REALTIME_KEOGRAM_NAME', 'allsky-realtime_keogram_ccd{camera_id:d}.{ext}'),
            'FILETRANSFER__REMOTE_REALTIME_KEOGRAM_FOLDER': config.get('FILETRANSFER', {}).get('REMOTE_REALTIME_KEOGRAM_FOLDER', '/home/allsky/upload/allsky'),
            'FILETRANSFER__REMOTE_ENDOFNIGHT_FOLDER'      : config.get('FILETRANSFER', {}).get('REMOTE_ENDOFNIGHT_FOLDER', '/home/allsky/upload/allsky'),
            'FILETRANSFER__REMOTE_LATEST_FOLDER'          : config.get('FILETRANSFER', {}).get('REMOTE_LATEST_FOLDER', '/home/allsky/upload/allsky'),
            'FILETRANSFER__REMOTE_DB_BACKUP_FOLDER'       : config.get('FILETRANSFER', {}).get('REMOTE_DB_BACKUP_FOLDER', '/home/allsky/upload/backup'),
            'FILETRANSFER__UPLOAD_IMAGE'     : config.get('FILETRANSFER', {}).get('UPLOAD_IMAGE', 0),
            'FILETRANSFER__UPLOAD_PANORAMA'  : config.get('FILETRANSFER', {}).get('UPLOAD_PANORAMA', 0),
            'FILETRANSFER__UPLOAD_METADATA'  : config.get('FILETRANSFER', {}).get('UPLOAD_METADATA', False),
            'FILETRANSFER__UPLOAD_RAW'       : config.get('FILETRANSFER', {}).get('UPLOAD_RAW', False),
            'FILETRANSFER__UPLOAD_FITS'      : config.get('FILETRANSFER', {}).get('UPLOAD_FITS', False),
            'FILETRANSFER__UPLOAD_VIDEO'     : config.get('FILETRANSFER', {}).get('UPLOAD_VIDEO', False),
            'FILETRANSFER__UPLOAD_MINI_VIDEO': config.get('FILETRANSFER', {}).get('UPLOAD_MINI_VIDEO', False),
            'FILETRANSFER__UPLOAD_KEOGRAM'   : config.get('FILETRANSFER', {}).get('UPLOAD_KEOGRAM', False),
            'FILETRANSFER__UPLOAD_STARTRAIL' : config.get('FILETRANSFER', {}).get('UPLOAD_STARTRAIL', False),
            'FILETRANSFER__UPLOAD_STARTRAIL_VIDEO' : config.get('FILETRANSFER', {}).get('UPLOAD_STARTRAIL_VIDEO', False),
            'FILETRANSFER__UPLOAD_PANORAMA_VIDEO'  : config.get('FILETRANSFER', {}).get('UPLOAD_PANORAMA_VIDEO', False),
            'FILETRANSFER__UPLOAD_REALTIME_KEOGRAM': config.get('FILETRANSFER', {}).get('UPLOAD_REALTIME_KEOGRAM', 0),
            'FILETRANSFER__UPLOAD_ENDOFNIGHT'      : config.get('FILETRANSFER', {}).get('UPLOAD_ENDOFNIGHT', False),
            'FILETRANSFER__UPLOAD_LATEST_IMAGE'    : config.get('FILETRANSFER', {}).get('UPLOAD_LATEST_IMAGE', False),
            'FILETRANSFER__UPLOAD_LATEST_PANORAMA' : config.get('FILETRANSFER', {}).get('UPLOAD_LATEST_PANORAMA', False),
            'FILETRANSFER__UPLOAD_LATEST_RAW'      : config.get('FILETRANSFER', {}).get('UPLOAD_LATEST_RAW', False),
            'FILETRANSFER__UPLOAD_LATEST_VIDEO'    : config.get('FILETRANSFER', {}).get('UPLOAD_LATEST_VIDEO', False),
            'FILETRANSFER__UPLOAD_DB_BACKUP'       : config.get('FILETRANSFER', {}).get('UPLOAD_DB_BACKUP', False),
            'S3UPLOAD__CLASSNAME'            : config.get('S3UPLOAD', {}).get('CLASSNAME', 'boto3_s3'),
            'S3UPLOAD__ENABLE'               : config.get('S3UPLOAD', {}).get('ENABLE', False),
            'S3UPLOAD__ACCESS_KEY'           : config.get('S3UPLOAD', {}).get('ACCESS_KEY', ''),
            'S3UPLOAD__SECRET_KEY'           : config.get('S3UPLOAD', {}).get('SECRET_KEY', ''),
            'S3UPLOAD__CREDS_FILE'           : config.get('S3UPLOAD', {}).get('CREDS_FILE', ''),
            'S3UPLOAD__BUCKET'               : config.get('S3UPLOAD', {}).get('BUCKET', 'change-me'),
            'S3UPLOAD__REGION'               : config.get('S3UPLOAD', {}).get('REGION', 'us-east-2'),
            'S3UPLOAD__NAMESPACE'            : config.get('S3UPLOAD', {}).get('NAMESPACE', ''),
            'S3UPLOAD__HOST'                 : config.get('S3UPLOAD', {}).get('HOST', 'amazonaws.com'),
            'S3UPLOAD__ENDPOINT_URL'         : config.get('S3UPLOAD', {}).get('ENDPOINT_URL', ''),
            'S3UPLOAD__PORT'                 : config.get('S3UPLOAD', {}).get('PORT', 0),
            'S3UPLOAD__CONNECT_TIMEOUT'      : config.get('S3UPLOAD', {}).get('CONNECT_TIMEOUT', 10.0),
            'S3UPLOAD__TIMEOUT'              : config.get('S3UPLOAD', {}).get('TIMEOUT', 60.0),
            'S3UPLOAD__URL_TEMPLATE'         : config.get('S3UPLOAD', {}).get('URL_TEMPLATE', 'https://{bucket}.s3.{region}.{host}'),
            'S3UPLOAD__STORAGE_CLASS'        : config.get('S3UPLOAD', {}).get('STORAGE_CLASS', 'STANDARD'),
            'S3UPLOAD__ACL'                  : config.get('S3UPLOAD', {}).get('ACL', ''),
            'S3UPLOAD__TLS'                  : config.get('S3UPLOAD', {}).get('TLS', True),
            'S3UPLOAD__CERT_BYPASS'          : config.get('S3UPLOAD', {}).get('CERT_BYPASS', False),
            'S3UPLOAD__UPLOAD_FITS'          : config.get('S3UPLOAD', {}).get('UPLOAD_FITS', False),
            'S3UPLOAD__UPLOAD_RAW'           : config.get('S3UPLOAD', {}).get('UPLOAD_RAW', False),
            'MQTTPUBLISH__ENABLE'            : config.get('MQTTPUBLISH', {}).get('ENABLE', False),
            'MQTTPUBLISH__TRANSPORT'         : config.get('MQTTPUBLISH', {}).get('TRANSPORT', 'tcp'),
            'MQTTPUBLISH__PROTOCOL'          : config.get('MQTTPUBLISH', {}).get('PROTOCOL', 'MQTTv5'),
            'MQTTPUBLISH__HOST'              : config.get('MQTTPUBLISH', {}).get('HOST', 'localhost'),
            'MQTTPUBLISH__PORT'              : config.get('MQTTPUBLISH', {}).get('PORT', 8883),
            'MQTTPUBLISH__USERNAME'          : config.get('MQTTPUBLISH', {}).get('USERNAME', 'indi-allsky'),
            'MQTTPUBLISH__PASSWORD'          : config.get('MQTTPUBLISH', {}).get('PASSWORD', ''),
            'MQTTPUBLISH__BASE_TOPIC'        : config.get('MQTTPUBLISH', {}).get('BASE_TOPIC', 'indi-allsky'),
            'MQTTPUBLISH__QOS'               : config.get('MQTTPUBLISH', {}).get('QOS', 0),
            'MQTTPUBLISH__TLS'               : config.get('MQTTPUBLISH', {}).get('TLS', True),
            'MQTTPUBLISH__CERT_BYPASS'       : config.get('MQTTPUBLISH', {}).get('CERT_BYPASS', True),
            'MQTTPUBLISH__PUBLISH_IMAGE'     : config.get('MQTTPUBLISH', {}).get('PUBLISH_IMAGE', True),
            'SYNCAPI__ENABLE'                : config.get('SYNCAPI', {}).get('ENABLE', False),
            'SYNCAPI__BASEURL'               : config.get('SYNCAPI', {}).get('BASEURL', 'https://example.com/indi-allsky'),
            'SYNCAPI__USERNAME'              : config.get('SYNCAPI', {}).get('USERNAME', ''),
            'SYNCAPI__APIKEY'                : config.get('SYNCAPI', {}).get('APIKEY', ''),
            'SYNCAPI__CERT_BYPASS'           : config.get('SYNCAPI', {}).get('CERT_BYPASS', False),
            'SYNCAPI__POST_S3'               : config.get('SYNCAPI', {}).get('POST_S3', False),
            'SYNCAPI__EMPTY_FILE'            : config.get('SYNCAPI', {}).get('EMPTY_FILE', False),
            'SYNCAPI__UPLOAD_IMAGE'          : config.get('SYNCAPI', {}).get('UPLOAD_IMAGE', 1),
            'SYNCAPI__UPLOAD_PANORAMA'       : config.get('SYNCAPI', {}).get('UPLOAD_PANORAMA', 1),
            'SYNCAPI__UPLOAD_VIDEO'          : True,  # cannot be changed
            'SYNCAPI__CONNECT_TIMEOUT'       : config.get('SYNCAPI', {}).get('CONNECT_TIMEOUT', 10.0),
            'SYNCAPI__TIMEOUT'               : config.get('SYNCAPI', {}).get('TIMEOUT', 60.0),
            'YOUTUBE__ENABLE'                : config.get('YOUTUBE', {}).get('ENABLE', False),
            'YOUTUBE__SECRETS_FILE'          : config.get('YOUTUBE', {}).get('SECRETS_FILE', ''),
            'YOUTUBE__PRIVACY_STATUS'        : config.get('YOUTUBE', {}).get('PRIVACY_STATUS', 'private'),
            'YOUTUBE__TITLE_TEMPLATE'        : config.get('YOUTUBE', {}).get('TITLE_TEMPLATE', 'Allsky {asset_label} - {day_date:%Y-%m-%d} - {timeofday}'),
            'YOUTUBE__DESCRIPTION_TEMPLATE'  : config.get('YOUTUBE', {}).get('DESCRIPTION_TEMPLATE', ''),
            'YOUTUBE__CATEGORY'              : config.get('YOUTUBE', {}).get('CATEGORY', 22),
            'YOUTUBE__UPLOAD_VIDEO'          : config.get('YOUTUBE', {}).get('UPLOAD_VIDEO', False),
            'YOUTUBE__UPLOAD_MINI_VIDEO'     : config.get('YOUTUBE', {}).get('UPLOAD_MINI_VIDEO', False),
            'YOUTUBE__UPLOAD_STARTRAIL_VIDEO': config.get('YOUTUBE', {}).get('UPLOAD_STARTRAIL_VIDEO', False),
            'YOUTUBE__UPLOAD_PANORAMA_VIDEO' : config.get('YOUTUBE', {}).get('UPLOAD_PANORAMA_VIDEO', False),
            'LIBCAMERA__IMAGE_FILE_TYPE'     : config.get('LIBCAMERA', {}).get('IMAGE_FILE_TYPE', 'jpg'),
            'LIBCAMERA__IMAGE_FILE_TYPE_DAY' : config.get('LIBCAMERA', {}).get('IMAGE_FILE_TYPE_DAY', 'jpg'),
            'LIBCAMERA__IMMEDIATE'           : config.get('LIBCAMERA', {}).get('IMMEDIATE', True),
            'LIBCAMERA__IMMEDIATE_DAY'       : config.get('LIBCAMERA', {}).get('IMMEDIATE_DAY', True),
            'LIBCAMERA__AWB'                 : config.get('LIBCAMERA', {}).get('AWB', 'auto'),
            'LIBCAMERA__AWB_DAY'             : config.get('LIBCAMERA', {}).get('AWB_DAY', 'auto'),
            'LIBCAMERA__AWB_ENABLE'          : config.get('LIBCAMERA', {}).get('AWB_ENABLE', True),
            'LIBCAMERA__AWB_ENABLE_DAY'      : config.get('LIBCAMERA', {}).get('AWB_ENABLE_DAY', True),
            'LIBCAMERA__CCM_DISABLE'         : config.get('LIBCAMERA', {}).get('CCM_DISABLE', False),
            'LIBCAMERA__CCM_DISABLE_DAY'     : config.get('LIBCAMERA', {}).get('CCM_DISABLE_DAY', False),
            'LIBCAMERA__CAMERA_ID'           : str(config.get('LIBCAMERA', {}).get('CAMERA_ID', 0)),  # string in form, int in config
            'LIBCAMERA__EXTRA_OPTIONS'       : config.get('LIBCAMERA', {}).get('EXTRA_OPTIONS', ''),
            'LIBCAMERA__EXTRA_OPTIONS_DAY'   : config.get('LIBCAMERA', {}).get('EXTRA_OPTIONS_DAY', ''),
            'LIBCAMERA__MQTT_TRANSPORT'      : config.get('LIBCAMERA', {}).get('MQTT_TRANSPORT', 'tcp'),
            'LIBCAMERA__MQTT_PROTOCOL'       : config.get('LIBCAMERA', {}).get('MQTT_PROTOCOL', 'MQTTv5'),
            'LIBCAMERA__MQTT_HOST'           : config.get('LIBCAMERA', {}).get('MQTT_HOST', 'localhost'),
            'LIBCAMERA__MQTT_PORT'           : config.get('LIBCAMERA', {}).get('MQTT_PORT', 8883),
            'LIBCAMERA__MQTT_USERNAME'       : config.get('LIBCAMERA', {}).get('MQTT_USERNAME', 'indi-allsky'),
            'LIBCAMERA__MQTT_PASSWORD'       : config.get('LIBCAMERA', {}).get('MQTT_PASSWORD', ''),
            'LIBCAMERA__MQTT_QOS'            : config.get('LIBCAMERA', {}).get('MQTT_QOS', 0),
            'LIBCAMERA__MQTT_TLS'            : config.get('LIBCAMERA', {}).get('MQTT_TLS', True),
            'LIBCAMERA__MQTT_CERT_BYPASS'    : config.get('LIBCAMERA', {}).get('MQTT_CERT_BYPASS', True),
            'LIBCAMERA__MQTT_EXPOSURE_TOPIC' : config.get('LIBCAMERA', {}).get('MQTT_EXPOSURE_TOPIC', 'libcamera/exposure'),
            'LIBCAMERA__MQTT_IMAGE_TOPIC'    : config.get('LIBCAMERA', {}).get('MQTT_IMAGE_TOPIC', 'libcamera/image'),
            'LIBCAMERA__MQTT_METADATA_TOPIC' : config.get('LIBCAMERA', {}).get('MQTT_METADATA_TOPIC', 'libcamera/metadata'),
            'PYCURL_CAMERA__URL'             : config.get('PYCURL_CAMERA', {}).get('URL', ''),
            'PYCURL_CAMERA__IMAGE_FILE_TYPE' : config.get('PYCURL_CAMERA', {}).get('IMAGE_FILE_TYPE', 'jpg'),
            'PYCURL_CAMERA__USERNAME'        : config.get('PYCURL_CAMERA', {}).get('USERNAME', ''),
            'PYCURL_CAMERA__PASSWORD'        : config.get('PYCURL_CAMERA', {}).get('PASSWORD', ''),
            'ACCUM_CAMERA__SUB_EXPOSURE_MAX' : config.get('ACCUM_CAMERA', {}).get('SUB_EXPOSURE_MAX', 1.0),
            'ACCUM_CAMERA__EVEN_EXPOSURES'   : config.get('ACCUM_CAMERA', {}).get('EVEN_EXPOSURES', True),
            'ACCUM_CAMERA__CLAMP_16BIT'      : config.get('ACCUM_CAMERA', {}).get('CLAMP_16BIT', False),
            'TEST_CAMERA__WIDTH'             : config.get('TEST_CAMERA', {}).get('WIDTH', 4056),
            'TEST_CAMERA__HEIGHT'            : config.get('TEST_CAMERA', {}).get('HEIGHT', 3040),
            'TEST_CAMERA__IMAGE_CIRCLE_DIAMETER': config.get('TEST_CAMERA', {}).get('IMAGE_CIRCLE_DIAMETER', 3500),
            'TEST_CAMERA__IMAGE_CIRCLE_OFFSET_X': config.get('TEST_CAMERA', {}).get('IMAGE_CIRCLE_OFFSET_X', 0),
            'TEST_CAMERA__IMAGE_CIRCLE_OFFSET_Y': config.get('TEST_CAMERA', {}).get('IMAGE_CIRCLE_OFFSET_Y', 0),
            'TEST_CAMERA__ROTATING_STAR_COUNT'  : config.get('TEST_CAMERA', {}).get('ROTATING_STAR_COUNT', 30000),
            'TEST_CAMERA__ROTATING_STAR_FACTOR' : config.get('TEST_CAMERA', {}).get('ROTATING_STAR_FACTOR', 1.0),
            'TEST_CAMERA__BUBBLE_COUNT'      : config.get('TEST_CAMERA', {}).get('BUBBLE_COUNT', 1000),
            'VIRTUALSKY__MAGNITUDE'          : config.get('VIRTUALSKY', {}).get('MAGNITUDE', 6.0),
            'VIRTUALSKY__CONSTELLATIONS'     : config.get('VIRTUALSKY', {}).get('CONSTELLATIONS', True),
            'VIRTUALSKY__CONSTELLATIONLABELS': config.get('VIRTUALSKY', {}).get('CONSTELLATIONLABELS', False),
            'VIRTUALSKY__SHOWSTARS'          : config.get('VIRTUALSKY', {}).get('SHOWSTARS', True),
            'VIRTUALSKY__SHOWSTARLABELS'     : config.get('VIRTUALSKY', {}).get('SHOWSTARLABELS', True),
            'VIRTUALSKY__SHOWPLANETS'        : config.get('VIRTUALSKY', {}).get('SHOWPLANETS', True),
            'VIRTUALSKY__SHOWPLANETLABELS'   : config.get('VIRTUALSKY', {}).get('SHOWPLANETLABELS', True),
            'VIRTUALSKY__IMAGE_CIRCLE_DIAMETER' : config.get('VIRTUALSKY', {}).get('IMAGE_CIRCLE_DIAMETER', 3500),
            'VIRTUALSKY__LATITUDE_OFFSET'    : config.get('VIRTUALSKY', {}).get('LATITUDE_OFFSET', 0.0),
            'VIRTUALSKY__LONGITUDE_OFFSET'   : config.get('VIRTUALSKY', {}).get('LONGITUDE_OFFSET', 0.0),
            'VIRTUALSKY__OFFSET_X'           : config.get('VIRTUALSKY', {}).get('OFFSET_X', 0),
            'VIRTUALSKY__OFFSET_Y'           : config.get('VIRTUALSKY', {}).get('OFFSET_Y', 0),
            #'VIRTUALSKY__FLIP_NS'            : config.get('VIRTUALSKY', {}).get('FLIP_NS', False),
            #'VIRTUALSKY__FLIP_EW'            : config.get('VIRTUALSKY', {}).get('FLIP_EW', False),
            'CIRCULAR_DISPLAY__ENABLE'       : config.get('CIRCULAR_DISPLAY', {}).get('ENABLE', False),
            'CIRCULAR_DISPLAY__RESOLUTION'   : str(config.get('CIRCULAR_DISPLAY', {}).get('RESOLUTION', 800)),  # string in form, int in config
            'CIRCULAR_DISPLAY__IMAGE_CIRCLE_DIAMETER' : config.get('CIRCULAR_DISPLAY', {}).get('IMAGE_CIRCLE_DIAMETER', 3500),
            'FOCUSER__CLASSNAME'             : config.get('FOCUSER', {}).get('CLASSNAME', ''),
            'FOCUSER__GPIO_PIN_1'            : config.get('FOCUSER', {}).get('GPIO_PIN_1', 'D17'),
            'FOCUSER__GPIO_PIN_2'            : config.get('FOCUSER', {}).get('GPIO_PIN_2', 'D18'),
            'FOCUSER__GPIO_PIN_3'            : config.get('FOCUSER', {}).get('GPIO_PIN_3', 'D27'),
            'FOCUSER__GPIO_PIN_4'            : config.get('FOCUSER', {}).get('GPIO_PIN_4', 'D22'),
            'FOCUSER__I2C_ADDRESS'           : config.get('FOCUSER', {}).get('I2C_ADDRESS', '0x60'),
            'DEW_HEATER__CLASSNAME'          : config.get('DEW_HEATER', {}).get('CLASSNAME', ''),
            'DEW_HEATER__I2C_ADDRESS'        : config.get('DEW_HEATER', {}).get('I2C_ADDRESS', '0x10'),
            'DEW_HEATER__PIN_1'              : config.get('DEW_HEATER', {}).get('PIN_1', 'D12'),
            'DEW_HEATER__INVERT_OUTPUT'      : config.get('DEW_HEATER', {}).get('INVERT_OUTPUT', False),
            'DEW_HEATER__ENABLE_DAY'         : config.get('DEW_HEATER', {}).get('ENABLE_DAY', False),
            'DEW_HEATER__LEVEL_DEF'          : config.get('DEW_HEATER', {}).get('LEVEL_DEF', 100),
            'DEW_HEATER__THOLD_ENABLE'       : config.get('DEW_HEATER', {}).get('THOLD_ENABLE', False),
            'DEW_HEATER__MANUAL_TARGET'      : config.get('DEW_HEATER', {}).get('MANUAL_TARGET', 0.0),
            'DEW_HEATER__TEMP_USER_VAR_SLOT' : config.get('DEW_HEATER', {}).get('TEMP_USER_VAR_SLOT', 'sensor_user_10'),
            'DEW_HEATER__DEWPOINT_USER_VAR_SLOT' : config.get('DEW_HEATER', {}).get('DEWPOINT_USER_VAR_SLOT', 'sensor_user_2'),
            'DEW_HEATER__LEVEL_LOW'          : config.get('DEW_HEATER', {}).get('LEVEL_LOW', 33),
            'DEW_HEATER__LEVEL_MED'          : config.get('DEW_HEATER', {}).get('LEVEL_MED', 66),
            'DEW_HEATER__LEVEL_HIGH'         : config.get('DEW_HEATER', {}).get('LEVEL_HIGH', 100),
            'DEW_HEATER__THOLD_DIFF_LOW'     : '{0:+d}'.format(config.get('DEW_HEATER', {}).get('THOLD_DIFF_LOW', 15)),  # str for sign
            'DEW_HEATER__THOLD_DIFF_MED'     : '{0:+d}'.format(config.get('DEW_HEATER', {}).get('THOLD_DIFF_MED', 10)),
            'DEW_HEATER__THOLD_DIFF_HIGH'    : '{0:+d}'.format(config.get('DEW_HEATER', {}).get('THOLD_DIFF_HIGH', 5)),
            'DEW_HEATER__HOLD_SECONDS'       : config.get('DEW_HEATER', {}).get('HOLD_SECONDS', 0),
            'DEW_HEATER__PWM_FREQUENCY'      : config.get('DEW_HEATER', {}).get('PWM_FREQUENCY', 500),
            'FAN__CLASSNAME'                 : config.get('FAN', {}).get('CLASSNAME', ''),
            'FAN__I2C_ADDRESS'               : config.get('FAN', {}).get('I2C_ADDRESS', '0x11'),
            'FAN__PIN_1'                     : config.get('FAN', {}).get('PIN_1', 'D13'),
            'FAN__INVERT_OUTPUT'             : config.get('FAN', {}).get('INVERT_OUTPUT', False),
            'FAN__ENABLE_NIGHT'              : config.get('FAN', {}).get('ENABLE_NIGHT', False),
            'FAN__LEVEL_DEF'                 : config.get('FAN', {}).get('LEVEL_DEF', 100),
            'FAN__THOLD_ENABLE'              : config.get('FAN', {}).get('THOLD_ENABLE', False),
            'FAN__TARGET'                    : config.get('FAN', {}).get('TARGET', 30.0),
            'FAN__TEMP_USER_VAR_SLOT'        : config.get('FAN', {}).get('TEMP_USER_VAR_SLOT', 'sensor_user_10'),
            'FAN__LEVEL_LOW'                 : config.get('FAN', {}).get('LEVEL_LOW', 33),
            'FAN__LEVEL_MED'                 : config.get('FAN', {}).get('LEVEL_MED', 66),
            'FAN__LEVEL_HIGH'                : config.get('FAN', {}).get('LEVEL_HIGH', 100),
            'FAN__THOLD_DIFF_LOW'            : '{0:+d}'.format(config.get('FAN', {}).get('THOLD_DIFF_LOW', -10)),  # str for sign
            'FAN__THOLD_DIFF_MED'            : '{0:+d}'.format(config.get('FAN', {}).get('THOLD_DIFF_MED', -5)),
            'FAN__THOLD_DIFF_HIGH'           : '{0:+d}'.format(config.get('FAN', {}).get('THOLD_DIFF_HIGH', 0)),
            'FAN__HOLD_SECONDS'              : config.get('FAN', {}).get('HOLD_SECONDS', 0),
            'FAN__PWM_FREQUENCY'             : config.get('FAN', {}).get('PWM_FREQUENCY', 500),
            'GENERIC_GPIO__A_CLASSNAME'      : config.get('GENERIC_GPIO', {}).get('A_CLASSNAME', ''),
            'GENERIC_GPIO__A_I2C_ADDRESS'    : config.get('GENERIC_GPIO', {}).get('A_I2C_ADDRESS', '0x12'),
            'GENERIC_GPIO__A_PIN_1'          : config.get('GENERIC_GPIO', {}).get('A_PIN_1', 'D21'),
            'GENERIC_GPIO__A_INVERT_OUTPUT'  : config.get('GENERIC_GPIO', {}).get('A_INVERT_OUTPUT', False),
            'MANUAL_GPIO__A_CLASSNAME'       : config.get('MANUAL_GPIO', {}).get('A_CLASSNAME', ''),
            'MANUAL_GPIO__A_PIN_1'           : config.get('MANUAL_GPIO', {}).get('A_PIN_1', '21'),
            'MANUAL_GPIO__A_PIN_2'           : config.get('MANUAL_GPIO', {}).get('A_PIN_2', '25'),
            'MANUAL_GPIO__A_PIN_3'           : config.get('MANUAL_GPIO', {}).get('A_PIN_3', '16'),
            'DEVICE__MQTT_TRANSPORT'         : config.get('DEVICE', {}).get('MQTT_TRANSPORT', 'tcp'),
            'DEVICE__MQTT_PROTOCOL'          : config.get('DEVICE', {}).get('MQTT_PROTOCOL', 'MQTTv5'),
            'DEVICE__MQTT_HOST'              : config.get('DEVICE', {}).get('MQTT_HOST', 'localhost'),
            'DEVICE__MQTT_PORT'              : config.get('DEVICE', {}).get('MQTT_PORT', 8883),
            'DEVICE__MQTT_USERNAME'          : config.get('DEVICE', {}).get('MQTT_USERNAME', 'indi-allsky'),
            'DEVICE__MQTT_PASSWORD'          : config.get('DEVICE', {}).get('MQTT_PASSWORD', ''),
            'DEVICE__MQTT_QOS'               : config.get('DEVICE', {}).get('MQTT_QOS', 0),
            'DEVICE__MQTT_TLS'               : config.get('DEVICE', {}).get('MQTT_TLS', True),
            'DEVICE__MQTT_CERT_BYPASS'       : config.get('DEVICE', {}).get('MQTT_CERT_BYPASS', True),
            'TEMP_SENSOR__A_CLASSNAME'       : config.get('TEMP_SENSOR', {}).get('A_CLASSNAME', ''),
            'TEMP_SENSOR__A_LABEL'           : config.get('TEMP_SENSOR', {}).get('A_LABEL', 'Sensor A'),
            'TEMP_SENSOR__A_PIN_1'           : config.get('TEMP_SENSOR', {}).get('A_PIN_1', 'D5'),
            'TEMP_SENSOR__A_PIN_2'           : config.get('TEMP_SENSOR', {}).get('A_PIN_2', ''),
            'TEMP_SENSOR__A_I2C_ADDRESS'     : config.get('TEMP_SENSOR', {}).get('A_I2C_ADDRESS', '0x77'),
            'TEMP_SENSOR__A_USER_VAR_SLOT'   : config.get('TEMP_SENSOR', {}).get('A_USER_VAR_SLOT', 'sensor_user_10'),
            'TEMP_SENSOR__A_TITLE_TEMPLATE'  : config.get('TEMP_SENSOR', {}).get('A_TITLE_TEMPLATE', '{name:s} - {label:s} - {probe:s}'),
            'TEMP_SENSOR__B_CLASSNAME'       : config.get('TEMP_SENSOR', {}).get('B_CLASSNAME', ''),
            'TEMP_SENSOR__B_LABEL'           : config.get('TEMP_SENSOR', {}).get('B_LABEL', 'Sensor B'),
            'TEMP_SENSOR__B_PIN_1'           : config.get('TEMP_SENSOR', {}).get('B_PIN_1', 'D6'),
            'TEMP_SENSOR__B_PIN_2'           : config.get('TEMP_SENSOR', {}).get('B_PIN_2', ''),
            'TEMP_SENSOR__B_I2C_ADDRESS'     : config.get('TEMP_SENSOR', {}).get('B_I2C_ADDRESS', '0x76'),
            'TEMP_SENSOR__B_USER_VAR_SLOT'   : config.get('TEMP_SENSOR', {}).get('B_USER_VAR_SLOT', 'sensor_user_20'),
            'TEMP_SENSOR__B_TITLE_TEMPLATE'  : config.get('TEMP_SENSOR', {}).get('B_TITLE_TEMPLATE', '{name:s} - {label:s} - {probe:s}'),
            'TEMP_SENSOR__C_CLASSNAME'       : config.get('TEMP_SENSOR', {}).get('C_CLASSNAME', ''),
            'TEMP_SENSOR__C_LABEL'           : config.get('TEMP_SENSOR', {}).get('C_LABEL', 'Sensor C'),
            'TEMP_SENSOR__C_PIN_1'           : config.get('TEMP_SENSOR', {}).get('C_PIN_1', 'D16'),
            'TEMP_SENSOR__C_PIN_2'           : config.get('TEMP_SENSOR', {}).get('C_PIN_2', ''),
            'TEMP_SENSOR__C_I2C_ADDRESS'     : config.get('TEMP_SENSOR', {}).get('C_I2C_ADDRESS', '0x40'),
            'TEMP_SENSOR__C_USER_VAR_SLOT'   : config.get('TEMP_SENSOR', {}).get('C_USER_VAR_SLOT', 'sensor_user_30'),
            'TEMP_SENSOR__C_TITLE_TEMPLATE'  : config.get('TEMP_SENSOR', {}).get('C_TITLE_TEMPLATE', '{name:s} - {label:s} - {probe:s}'),
            'TEMP_SENSOR__D_CLASSNAME'       : config.get('TEMP_SENSOR', {}).get('D_CLASSNAME', ''),
            'TEMP_SENSOR__D_LABEL'           : config.get('TEMP_SENSOR', {}).get('D_LABEL', 'Sensor D'),
            'TEMP_SENSOR__D_PIN_1'           : config.get('TEMP_SENSOR', {}).get('D_PIN_1', 'D26'),
            'TEMP_SENSOR__D_PIN_2'           : config.get('TEMP_SENSOR', {}).get('D_PIN_2', ''),
            'TEMP_SENSOR__D_I2C_ADDRESS'     : config.get('TEMP_SENSOR', {}).get('D_I2C_ADDRESS', '0x50'),
            'TEMP_SENSOR__D_USER_VAR_SLOT'   : config.get('TEMP_SENSOR', {}).get('D_USER_VAR_SLOT', 'sensor_user_40'),
            'TEMP_SENSOR__D_TITLE_TEMPLATE'  : config.get('TEMP_SENSOR', {}).get('D_TITLE_TEMPLATE', '{name:s} - {label:s} - {probe:s}'),
            'TEMP_SENSOR__E_CLASSNAME'       : config.get('TEMP_SENSOR', {}).get('E_CLASSNAME', ''),
            'TEMP_SENSOR__E_LABEL'           : config.get('TEMP_SENSOR', {}).get('E_LABEL', 'Sensor E'),
            'TEMP_SENSOR__E_PIN_1'           : config.get('TEMP_SENSOR', {}).get('E_PIN_1', 'D25'),
            'TEMP_SENSOR__E_PIN_2'           : config.get('TEMP_SENSOR', {}).get('E_PIN_2', ''),
            'TEMP_SENSOR__E_I2C_ADDRESS'     : config.get('TEMP_SENSOR', {}).get('E_I2C_ADDRESS', '0x51'),
            'TEMP_SENSOR__E_USER_VAR_SLOT'   : config.get('TEMP_SENSOR', {}).get('E_USER_VAR_SLOT', 'sensor_user_50'),
            'TEMP_SENSOR__E_TITLE_TEMPLATE'  : config.get('TEMP_SENSOR', {}).get('E_TITLE_TEMPLATE', '{name:s} - {label:s} - {probe:s}'),
            'TEMP_SENSOR__F_CLASSNAME'       : config.get('TEMP_SENSOR', {}).get('F_CLASSNAME', ''),
            'TEMP_SENSOR__F_LABEL'           : config.get('TEMP_SENSOR', {}).get('F_LABEL', 'Sensor F'),
            'TEMP_SENSOR__F_PIN_1'           : config.get('TEMP_SENSOR', {}).get('F_PIN_1', 'D27'),
            'TEMP_SENSOR__F_PIN_2'           : config.get('TEMP_SENSOR', {}).get('F_PIN_2', ''),
            'TEMP_SENSOR__F_I2C_ADDRESS'     : config.get('TEMP_SENSOR', {}).get('F_I2C_ADDRESS', '0x52'),
            'TEMP_SENSOR__F_USER_VAR_SLOT'   : config.get('TEMP_SENSOR', {}).get('F_USER_VAR_SLOT', 'sensor_user_55'),
            'TEMP_SENSOR__F_TITLE_TEMPLATE'  : config.get('TEMP_SENSOR', {}).get('F_TITLE_TEMPLATE', '{name:s} - {label:s} - {probe:s}'),
            'TEMP_SENSOR__FC37_ACTIVE_LOW'   : config.get('TEMP_SENSOR', {}).get('FC37_ACTIVE_LOW', True),
            'TEMP_SENSOR__OPENWEATHERMAP_APIKEY' : config.get('TEMP_SENSOR', {}).get('OPENWEATHERMAP_APIKEY', ''),
            'TEMP_SENSOR__WUNDERGROUND_APIKEY'   : config.get('TEMP_SENSOR', {}).get('WUNDERGROUND_APIKEY', ''),
            'TEMP_SENSOR__ASTROSPHERIC_APIKEY'   : config.get('TEMP_SENSOR', {}).get('ASTROSPHERIC_APIKEY', ''),
            'TEMP_SENSOR__AMBIENTWEATHER_APIKEY'           : config.get('TEMP_SENSOR', {}).get('AMBIENTWEATHER_APIKEY', ''),
            'TEMP_SENSOR__AMBIENTWEATHER_APPLICATIONKEY'   : config.get('TEMP_SENSOR', {}).get('AMBIENTWEATHER_APPLICATIONKEY', ''),
            'TEMP_SENSOR__AMBIENTWEATHER_MACADDRESS'       : config.get('TEMP_SENSOR', {}).get('AMBIENTWEATHER_MACADDRESS', ''),
            'TEMP_SENSOR__ECOWITT_APIKEY'           : config.get('TEMP_SENSOR', {}).get('ECOWITT_APIKEY', ''),
            'TEMP_SENSOR__ECOWITT_APPLICATIONKEY'   : config.get('TEMP_SENSOR', {}).get('ECOWITT_APPLICATIONKEY', ''),
            'TEMP_SENSOR__ECOWITT_MACADDRESS'       : config.get('TEMP_SENSOR', {}).get('ECOWITT_MACADDRESS', ''),
            'TEMP_SENSOR__MQTT_TRANSPORT'    : config.get('TEMP_SENSOR', {}).get('MQTT_TRANSPORT', 'tcp'),
            'TEMP_SENSOR__MQTT_PROTOCOL'     : config.get('TEMP_SENSOR', {}).get('MQTT_PROTOCOL', 'MQTTv5'),
            'TEMP_SENSOR__MQTT_HOST'         : config.get('TEMP_SENSOR', {}).get('MQTT_HOST', 'localhost'),
            'TEMP_SENSOR__MQTT_PORT'         : config.get('TEMP_SENSOR', {}).get('MQTT_PORT', 8883),
            'TEMP_SENSOR__MQTT_USERNAME'     : config.get('TEMP_SENSOR', {}).get('MQTT_USERNAME', 'indi-allsky'),
            'TEMP_SENSOR__MQTT_PASSWORD'     : config.get('TEMP_SENSOR', {}).get('MQTT_PASSWORD', ''),
            'TEMP_SENSOR__MQTT_TLS'          : config.get('TEMP_SENSOR', {}).get('MQTT_TLS', True),
            'TEMP_SENSOR__MQTT_CERT_BYPASS'  : config.get('TEMP_SENSOR', {}).get('MQTT_CERT_BYPASS', True),
            'TEMP_SENSOR__DHT_USE_PULSEIO'   : config.get('TEMP_SENSOR', {}).get('DHT_USE_PULSEIO', False),
            'TEMP_SENSOR__SHT3X_HEATER_NIGHT': config.get('TEMP_SENSOR', {}).get('SHT3X_HEATER_NIGHT', False),
            'TEMP_SENSOR__SHT3X_HEATER_DAY'  : config.get('TEMP_SENSOR', {}).get('SHT3X_HEATER_DAY', False),
            'TEMP_SENSOR__SHT4X_MODE_NIGHT'  : config.get('TEMP_SENSOR', {}).get('SHT4X_MODE_NIGHT', 'NOHEAT_HIGHPRECISION'),
            'TEMP_SENSOR__SHT4X_MODE_DAY'    : config.get('TEMP_SENSOR', {}).get('SHT4X_MODE_DAY', 'NOHEAT_HIGHPRECISION'),
            'TEMP_SENSOR__SI7021_HEATER_LEVEL_NIGHT' : str(config.get('TEMP_SENSOR', {}).get('SI7021_HEATER_LEVEL_NIGHT', -1)),  # string in form, int in config
            'TEMP_SENSOR__SI7021_HEATER_LEVEL_DAY' : str(config.get('TEMP_SENSOR', {}).get('SI7021_HEATER_LEVEL_DAY', -1)),  # string in form, int in config
            'TEMP_SENSOR__HTU31D_HEATER_NIGHT': config.get('TEMP_SENSOR', {}).get('HTU31D_HEATER_NIGHT', False),
            'TEMP_SENSOR__HTU31D_HEATER_DAY'  : config.get('TEMP_SENSOR', {}).get('HTU31D_HEATER_DAY', False),
            'TEMP_SENSOR__HDC302X_HEATER_NIGHT'  : config.get('TEMP_SENSOR', {}).get('HDC302X_HEATER_NIGHT', 'OFF'),
            'TEMP_SENSOR__HDC302X_HEATER_DAY'    : config.get('TEMP_SENSOR', {}).get('HDC302X_HEATER_DAY', 'OFF'),
            'TEMP_SENSOR__TSL2561_GAIN_NIGHT': str(config.get('TEMP_SENSOR', {}).get('TSL2561_GAIN_NIGHT', 1)),  # string in form, int in config
            'TEMP_SENSOR__TSL2561_GAIN_DAY'  : str(config.get('TEMP_SENSOR', {}).get('TSL2561_GAIN_DAY', 0)),  # string in form, int in config
            'TEMP_SENSOR__TSL2561_INT_NIGHT' : str(config.get('TEMP_SENSOR', {}).get('TSL2561_INT_NIGHT', 1)),  # string in form, int in config
            'TEMP_SENSOR__TSL2561_INT_DAY'   : str(config.get('TEMP_SENSOR', {}).get('TSL2561_INT_DAY', 1)),  # string in form, int in config
            'TEMP_SENSOR__TSL2561_DISABLE_DAY' : config.get('TEMP_SENSOR', {}).get('TSL2561_DISABLE_DAY', False),
            'TEMP_SENSOR__TSL2591_GAIN_NIGHT': config.get('TEMP_SENSOR', {}).get('TSL2591_GAIN_NIGHT', 'GAIN_MED'),
            'TEMP_SENSOR__TSL2591_GAIN_DAY'  : config.get('TEMP_SENSOR', {}).get('TSL2591_GAIN_DAY', 'GAIN_LOW'),
            'TEMP_SENSOR__TSL2591_INT_NIGHT' : config.get('TEMP_SENSOR', {}).get('TSL2591_INT_NIGHT', 'INTEGRATIONTIME_100MS'),
            'TEMP_SENSOR__TSL2591_INT_DAY'   : config.get('TEMP_SENSOR', {}).get('TSL2591_INT_DAY', 'INTEGRATIONTIME_100MS'),
            'TEMP_SENSOR__TSL2591_DISABLE_DAY' : config.get('TEMP_SENSOR', {}).get('TSL2591_DISABLE_DAY', False),
            'TEMP_SENSOR__VEML7700_GAIN_NIGHT': config.get('TEMP_SENSOR', {}).get('VEML7700_GAIN_NIGHT', 'ALS_GAIN_1'),
            'TEMP_SENSOR__VEML7700_GAIN_DAY' : config.get('TEMP_SENSOR', {}).get('VEML7700_GAIN_DAY', 'ALS_GAIN_1_8'),
            'TEMP_SENSOR__VEML7700_INT_NIGHT': config.get('TEMP_SENSOR', {}).get('VEML7700_INT_NIGHT', 'ALS_100MS'),
            'TEMP_SENSOR__VEML7700_INT_DAY'  : config.get('TEMP_SENSOR', {}).get('VEML7700_INT_DAY', 'ALS_100MS'),
            'TEMP_SENSOR__SI1145_VIS_GAIN_NIGHT' : config.get('TEMP_SENSOR', {}).get('SI1145_VIS_GAIN_NIGHT', 'GAIN_ADC_CLOCK_DIV_32'),
            'TEMP_SENSOR__SI1145_VIS_GAIN_DAY'   : config.get('TEMP_SENSOR', {}).get('SI1145_VIS_GAIN_DAY', 'GAIN_ADC_CLOCK_DIV_1'),
            'TEMP_SENSOR__SI1145_IR_GAIN_NIGHT'  : config.get('TEMP_SENSOR', {}).get('SI1145_IR_GAIN_NIGHT', 'GAIN_ADC_CLOCK_DIV_32'),
            'TEMP_SENSOR__SI1145_IR_GAIN_DAY'    : config.get('TEMP_SENSOR', {}).get('SI1145_IR_GAIN_DAY', 'GAIN_ADC_CLOCK_DIV_1'),
            'TEMP_SENSOR__LTR390_GAIN_NIGHT'     : config.get('TEMP_SENSOR', {}).get('LTR390_GAIN_NIGHT', 'GAIN_9X'),
            'TEMP_SENSOR__LTR390_GAIN_DAY'       : config.get('TEMP_SENSOR', {}).get('LTR390_GAIN_DAY', 'GAIN_1X'),
            'TEMP_SENSOR__INA3221_CH1_ENABLE'    : config.get('TEMP_SENSOR', {}).get('INA3221_CH1_ENABLE', True),
            'TEMP_SENSOR__INA3221_CH2_ENABLE'    : config.get('TEMP_SENSOR', {}).get('INA3221_CH2_ENABLE', True),
            'TEMP_SENSOR__INA3221_CH3_ENABLE'    : config.get('TEMP_SENSOR', {}).get('INA3221_CH3_ENABLE', True),
            'TEMP_SENSOR__AS3935_OUTDOOR_MODE'   : config.get('TEMP_SENSOR', {}).get('AS3935_OUTDOOR_MODE', True),
            'TEMP_SENSOR__AS3935_MASK_DISTURBER' : config.get('TEMP_SENSOR', {}).get('AS3935_MASK_DISTURBER', False),
            'TEMP_SENSOR__AS3935_NOISE_LEVEL'    : config.get('TEMP_SENSOR', {}).get('AS3935_NOISE_LEVEL', 2),
            'TEMP_SENSOR__AS3935_SPIKE_REJECTION': config.get('TEMP_SENSOR', {}).get('AS3935_SPIKE_REJECTION', 2),
            'TEMP_SENSOR__LUX_MAGNITUDE_OFFSET'  : config.get('TEMP_SENSOR', {}).get('LUX_MAGNITUDE_OFFSET', 26.0),
            'CHARTS__CUSTOM_SLOT_1'          : config.get('CHARTS', {}).get('CUSTOM_SLOT_1', 'sensor_user_10'),
            'CHARTS__CUSTOM_SLOT_1_MIN'      : config.get('CHARTS', {}).get('CUSTOM_SLOT_1_MIN', 0.0),
            'CHARTS__CUSTOM_SLOT_2'          : config.get('CHARTS', {}).get('CUSTOM_SLOT_2', 'sensor_user_11'),
            'CHARTS__CUSTOM_SLOT_2_MIN'      : config.get('CHARTS', {}).get('CUSTOM_SLOT_2_MIN', 0.0),
            'CHARTS__CUSTOM_SLOT_3'          : config.get('CHARTS', {}).get('CUSTOM_SLOT_3', 'sensor_user_12'),
            'CHARTS__CUSTOM_SLOT_3_MIN'      : config.get('CHARTS', {}).get('CUSTOM_SLOT_3_MIN', 0.0),
            'CHARTS__CUSTOM_SLOT_4'          : config.get('CHARTS', {}).get('CUSTOM_SLOT_4', 'sensor_user_13'),
            'CHARTS__CUSTOM_SLOT_4_MIN'      : config.get('CHARTS', {}).get('CUSTOM_SLOT_4_MIN', 0.0),
            'CHARTS__CUSTOM_SLOT_5'          : config.get('CHARTS', {}).get('CUSTOM_SLOT_5', 'sensor_user_14'),
            'CHARTS__CUSTOM_SLOT_5_MIN'      : config.get('CHARTS', {}).get('CUSTOM_SLOT_5_MIN', 0.0),
            'CHARTS__CUSTOM_SLOT_6'          : config.get('CHARTS', {}).get('CUSTOM_SLOT_6', 'sensor_user_15'),
            'CHARTS__CUSTOM_SLOT_6_MIN'      : config.get('CHARTS', {}).get('CUSTOM_SLOT_6_MIN', 0.0),
            'CHARTS__CUSTOM_SLOT_7'          : config.get('CHARTS', {}).get('CUSTOM_SLOT_7', 'sensor_user_16'),
            'CHARTS__CUSTOM_SLOT_7_MIN'      : config.get('CHARTS', {}).get('CUSTOM_SLOT_7_MIN', 0.0),
            'CHARTS__CUSTOM_SLOT_8'          : config.get('CHARTS', {}).get('CUSTOM_SLOT_8', 'sensor_user_14'),
            'CHARTS__CUSTOM_SLOT_8_MIN'      : config.get('CHARTS', {}).get('CUSTOM_SLOT_8_MIN', 0.0),
            'CHARTS__CUSTOM_SLOT_9'          : config.get('CHARTS', {}).get('CUSTOM_SLOT_9', 'sensor_user_15'),
            'CHARTS__CUSTOM_SLOT_9_MIN'      : config.get('CHARTS', {}).get('CUSTOM_SLOT_9_MIN', 0.0),
            'ADSB__ENABLE'                   : config.get('ADSB', {}).get('ENABLE', False),
            'ADSB__DUMP1090_URL'             : config.get('ADSB', {}).get('DUMP1090_URL', 'https://localhost/dump1090/data/aircraft.json'),
            'ADSB__USERNAME'                 : config.get('ADSB', {}).get('USERNAME', ''),
            'ADSB__PASSWORD'                 : config.get('ADSB', {}).get('PASSWORD', ''),
            'ADSB__CERT_BYPASS'              : config.get('ADSB', {}).get('CERT_BYPASS', True),
            'ADSB__ALT_DEG_MIN'              : config.get('ADSB', {}).get('ALT_DEG_MIN', 20.0),
            'ADSB__LABEL_ENABLE'             : config.get('ADSB', {}).get('LABEL_ENABLE', True),
            'ADSB__LABEL_LIMIT'              : config.get('ADSB', {}).get('LABEL_LIMIT', 10),
            'ADSB__AIRCRAFT_LABEL_TEMPLATE'  : config.get('ADSB', {}).get('AIRCRAFT_LABEL_TEMPLATE', '{id:s} {distance:0.1f}km {alt:0.1f}\u00b0 {dir:s}'),
            'ADSB__IMAGE_LABEL_TEMPLATE_PREFIX' : config.get('ADSB', {}).get('IMAGE_LABEL_TEMPLATE_PREFIX', '# xy:15,300 (Left)\n# anchor:la (Left Justified)\n# color:200,200,200\nAircraft'),
            'SATELLITE_TRACK__ENABLE'              : config.get('SATELLITE_TRACK', {}).get('ENABLE', False),
            'SATELLITE_TRACK__DAYTIME_TRACK'       : config.get('SATELLITE_TRACK', {}).get('DAYTIME_TRACK', False),
            'SATELLITE_TRACK__ALT_DEG_MIN'         : config.get('SATELLITE_TRACK', {}).get('ALT_DEG_MIN', 20.0),
            'SATELLITE_TRACK__LABEL_ENABLE'        : config.get('SATELLITE_TRACK', {}).get('LABEL_ENABLE', True),
            'SATELLITE_TRACK__LABEL_LIMIT'         : config.get('SATELLITE_TRACK', {}).get('LABEL_LIMIT', 10),
            'SATELLITE_TRACK__SAT_LABEL_TEMPLATE'  : config.get('SATELLITE_TRACK', {}).get('SAT_LABEL_TEMPLATE', '{label:s} {alt:0.1f}\u00b0 {dir:s}'),
            'SATELLITE_TRACK__IMAGE_LABEL_TEMPLATE_PREFIX' : config.get('SATELLITE_TRACK', {}).get('IMAGE_LABEL_TEMPLATE_PREFIX', '# xy:-15,200 (Right)\n# anchor:ra (Right Justified)\n# color:200,200,200\nSatellites'),
            'RELOAD_ON_SAVE'                 : False,
            'CONFIG_NOTE'                    : '',
            'ENCRYPT_PASSWORDS'              : config.get('ENCRYPT_PASSWORDS', False),  # do not adjust
        }


def apply_full_config_form_display_fields(config, form_data):
    # ADU_ROI
    ADU_ROI = config.get('ADU_ROI', [])
    if ADU_ROI is None:
        ADU_ROI = []
    elif isinstance(ADU_ROI, bool):
        ADU_ROI = []

    try:
        form_data['ADU_ROI_X1'] = ADU_ROI[0]
    except IndexError:
        form_data['ADU_ROI_X1'] = 0

    try:
        form_data['ADU_ROI_Y1'] = ADU_ROI[1]
    except IndexError:
        form_data['ADU_ROI_Y1'] = 0

    try:
        form_data['ADU_ROI_X2'] = ADU_ROI[2]
    except IndexError:
        form_data['ADU_ROI_X2'] = 0

    try:
        form_data['ADU_ROI_Y2'] = ADU_ROI[3]
    except IndexError:
        form_data['ADU_ROI_Y2'] = 0


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


    # IMAGE_CROP_ROI
    IMAGE_CROP_ROI = config.get('IMAGE_CROP_ROI', [])
    if IMAGE_CROP_ROI is None:
        IMAGE_CROP_ROI = []
    elif isinstance(IMAGE_CROP_ROI, bool):
        IMAGE_CROP_ROI = []

    try:
        form_data['IMAGE_CROP_ROI_X1'] = IMAGE_CROP_ROI[0]
    except IndexError:
        form_data['IMAGE_CROP_ROI_X1'] = 0

    try:
        form_data['IMAGE_CROP_ROI_Y1'] = IMAGE_CROP_ROI[1]
    except IndexError:
        form_data['IMAGE_CROP_ROI_Y1'] = 0

    try:
        form_data['IMAGE_CROP_ROI_X2'] = IMAGE_CROP_ROI[2]
    except IndexError:
        form_data['IMAGE_CROP_ROI_X2'] = 0

    try:
        form_data['IMAGE_CROP_ROI_Y2'] = IMAGE_CROP_ROI[3]
    except IndexError:
        form_data['IMAGE_CROP_ROI_Y2'] = 0


    # Font color
    text_properties__font_color = config.get('TEXT_PROPERTIES', {}).get('FONT_COLOR', [200, 200, 200])
    form_data['TEXT_PROPERTIES__FONT_COLOR'] = ','.join([str(x) for x in text_properties__font_color])

    # Cardinal directions color
    cardinal_dirs__font_color = config.get('CARDINAL_DIRS', {}).get('FONT_COLOR', [200, 0, 0])
    form_data['CARDINAL_DIRS__FONT_COLOR'] = ','.join([str(x) for x in cardinal_dirs__font_color])

    # Sun orb color
    orb_properties__sun_color = config.get('ORB_PROPERTIES', {}).get('SUN_COLOR', [200, 200, 100])
    form_data['ORB_PROPERTIES__SUN_COLOR'] = ','.join([str(x) for x in orb_properties__sun_color])

    # Moon orb color
    orb_properties__moon_color = config.get('ORB_PROPERTIES', {}).get('MOON_COLOR', [128, 128, 128])
    form_data['ORB_PROPERTIES__MOON_COLOR'] = ','.join([str(x) for x in orb_properties__moon_color])

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


    # Youtube
    youtube_tags = config.get('YOUTUBE', {}).get('TAGS', [])
    form_data['YOUTUBE__TAGS_STR'] = ', '.join(youtube_tags)
    return form_data


def apply_full_config_form_encoded_fields(config, form_data):
    # FITS headers
    fitsheaders = config.get('FITSHEADERS', [])

    try:
        form_data['FITSHEADERS__0__KEY'] = str(fitsheaders[0][0]).upper()
        form_data['FITSHEADERS__0__VAL'] = str(fitsheaders[0][1])
    except IndexError:
        form_data['FITSHEADERS__0__KEY'] = 'INSTRUME'
        form_data['FITSHEADERS__0__VAL'] = 'indi-allsky'

    try:
        form_data['FITSHEADERS__1__KEY'] = str(fitsheaders[1][0]).upper()
        form_data['FITSHEADERS__1__VAL'] = str(fitsheaders[1][1])
    except IndexError:
        form_data['FITSHEADERS__1__KEY'] = 'OBSERVER'
        form_data['FITSHEADERS__1__VAL'] = ''

    try:
        form_data['FITSHEADERS__2__KEY'] = str(fitsheaders[2][0]).upper()
        form_data['FITSHEADERS__2__VAL'] = str(fitsheaders[2][1])
    except IndexError:
        form_data['FITSHEADERS__2__KEY'] = 'SITE'
        form_data['FITSHEADERS__2__VAL'] = ''

    try:
        form_data['FITSHEADERS__3__KEY'] = str(fitsheaders[3][0]).upper()
        form_data['FITSHEADERS__3__VAL'] = str(fitsheaders[3][1])
    except IndexError:
        form_data['FITSHEADERS__3__KEY'] = 'OBJECT'
        form_data['FITSHEADERS__3__VAL'] = ''

    try:
        form_data['FITSHEADERS__4__KEY'] = str(fitsheaders[4][0]).upper()
        form_data['FITSHEADERS__4__VAL'] = str(fitsheaders[4][1])
    except IndexError:
        form_data['FITSHEADERS__4__KEY'] = 'NOTES'
        form_data['FITSHEADERS__4__VAL'] = ''


    # libcurl options as json text
    filetransfer__libcurl_options = config.get('FILETRANSFER', {}).get('LIBCURL_OPTIONS', {'VERBOSE' : 0})
    form_data['FILETRANSFER__LIBCURL_OPTIONS'] = json.dumps(filetransfer__libcurl_options, indent=4)


    # INDI config as json text
    indi_config_defaults = config.get('INDI_CONFIG_DEFAULTS', {})
    form_data['INDI_CONFIG_DEFAULTS'] = json.dumps(indi_config_defaults, indent=4)

    indi_config_day = config.get('INDI_CONFIG_DAY', {})
    form_data['INDI_CONFIG_DAY'] = json.dumps(indi_config_day, indent=4)
    return form_data
