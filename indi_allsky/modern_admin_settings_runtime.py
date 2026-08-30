from datetime import datetime
from datetime import timezone

from cryptography.fernet import Fernet

from .exceptions import ConfigSaveException


class ModernAdminFullConfigPayloadPreparationService:
    """Hybrid-owned structural preparation for the legacy full-config parser."""

    DICT_SECTIONS = (
        'WEBSITE',
        'CCD_CONFIG',
        'CAMERA_SQM',
        'IMAGE_FILE_COMPRESSION',
        'IMAGE_CIRCLE_MASK',
        'FISH2PANO',
        'TEXT_PROPERTIES',
        'CARDINAL_DIRS',
        'IMAGE_STRETCH',
        'ORB_PROPERTIES',
        'IMAGE_BORDER',
        'FILETRANSFER',
        'S3UPLOAD',
        'MQTTPUBLISH',
        'SYNCAPI',
        'YOUTUBE',
        'LIBCAMERA',
        'PYCURL_CAMERA',
        'ACCUM_CAMERA',
        'TEST_CAMERA',
        'VIRTUALSKY',
        'CIRCULAR_DISPLAY',
        'FOCUSER',
        'DEW_HEATER',
        'FAN',
        'GENERIC_GPIO',
        'MANUAL_GPIO',
        'DEVICE',
        'TEMP_SENSOR',
        'THUMBNAILS',
        'HEALTHCHECK',
        'CHARTS',
        'TIMELAPSE',
        'MOON_OVERLAY',
        'LIGHTGRAPH_OVERLAY',
        'IMAGE_OVERLAY',
        'ADSB',
        'SATELLITE_TRACK',
        'LONGTERM_KEOGRAM',
        'REALTIME_KEOGRAM',
        'STARTRAILS',
        'EVENT_CANDIDATE_TRIGGERS',
    )

    CCD_MODES = (
        'NIGHT',
        'MOONMODE',
        'DAY',
    )

    def prepare(self, config):
        for section in self.DICT_SECTIONS:
            if not isinstance(config.get(section), dict):
                config[section] = {}

        for mode in self.CCD_MODES:
            if not config['CCD_CONFIG'].get(mode):
                config['CCD_CONFIG'][mode] = {}

        if not config.get('FITSHEADERS'):
            config['FITSHEADERS'] = [['', ''], ['', ''], ['', ''], ['', ''], ['', '']]

        return config


class ModernAdminFullConfigCameraConnectionParser:
    """Hybrid-owned parser for the full-config camera connection fields."""

    REQUIRED_FIELDS = (
        'CAMERA_INTERFACE',
        'INDI_SERVER',
        'INDI_PORT',
        'INDI_CAMERA_NAME',
    )

    def apply(self, config, payload):
        config['CAMERA_INTERFACE'] = str(payload['CAMERA_INTERFACE'])
        config['INDI_SERVER'] = str(payload['INDI_SERVER'])
        config['INDI_PORT'] = int(payload['INDI_PORT'])
        config['INDI_CAMERA_NAME'] = str(payload['INDI_CAMERA_NAME'])
        return config


class ModernAdminFullConfigStationIdentityParser:
    """Hybrid-owned parser for the full-config station identity fields."""

    IDENTITY_FIELDS = (
        'WEBSITE__TITLE',
        'OWNER',
    )
    LOCATION_FIELDS = (
        'LOCATION_NAME',
        'LOCATION_LATITUDE',
        'LOCATION_LONGITUDE',
        'LOCATION_ELEVATION',
    )
    REQUIRED_FIELDS = IDENTITY_FIELDS + LOCATION_FIELDS

    def apply(self, config, payload):
        config['WEBSITE']['TITLE'] = str(payload['WEBSITE__TITLE'])
        config['OWNER'] = str(payload['OWNER'])
        return config

    def apply_location(self, config, payload):
        config['LOCATION_NAME'] = str(payload['LOCATION_NAME'])
        config['LOCATION_LATITUDE'] = float(round(float(payload['LOCATION_LATITUDE']), 3))
        config['LOCATION_LONGITUDE'] = float(round(float(payload['LOCATION_LONGITUDE']), 3))
        config['LOCATION_ELEVATION'] = int(payload['LOCATION_ELEVATION'])
        return config


class ModernAdminFullConfigLensMetadataParser:
    """Hybrid-owned parser for descriptive full-config lens metadata."""

    REQUIRED_FIELDS = (
        'LENS_NAME',
        'LENS_FOCAL_LENGTH',
        'LENS_FOCAL_RATIO',
    )

    def apply(self, config, payload):
        config['LENS_NAME'] = str(payload['LENS_NAME'])
        config['LENS_FOCAL_LENGTH'] = float(payload['LENS_FOCAL_LENGTH'])
        config['LENS_FOCAL_RATIO'] = float(payload['LENS_FOCAL_RATIO'])
        return config


class ModernAdminFullConfigLensGeometryParser:
    """Hybrid-owned parser for full-config lens geometry fields."""

    REQUIRED_FIELDS = (
        'LENS_IMAGE_CIRCLE',
        'LENS_OFFSET_X',
        'LENS_OFFSET_Y',
        'LENS_ALTITUDE',
        'LENS_AZIMUTH',
    )

    def apply(self, config, payload):
        config['LENS_IMAGE_CIRCLE'] = int(payload['LENS_IMAGE_CIRCLE'])
        config['LENS_OFFSET_X'] = int(payload['LENS_OFFSET_X'])
        config['LENS_OFFSET_Y'] = int(payload['LENS_OFFSET_Y'])
        config['LENS_ALTITUDE'] = float(payload['LENS_ALTITUDE'])
        config['LENS_AZIMUTH'] = float(payload['LENS_AZIMUTH'])
        return config


class ModernAdminFullConfigExposureGainParser:
    """Hybrid-owned parser for manual full-config exposure and gain fields."""

    REQUIRED_FIELDS = (
        'CCD_CONFIG__NIGHT__GAIN',
        'CCD_CONFIG__MOONMODE__GAIN',
        'CCD_CONFIG__DAY__GAIN',
        'CCD_EXPOSURE_MAX',
        'CCD_EXPOSURE_DEF',
        'CCD_EXPOSURE_MIN',
        'CCD_EXPOSURE_MIN_DAY',
        'CCD_EXPOSURE_TIMEOUT',
        'EXPOSURE_PERIOD',
        'EXPOSURE_PERIOD_DAY',
    )

    def apply_night_gain(self, config, payload):
        config['CCD_CONFIG']['NIGHT']['GAIN'] = float(round(float(payload['CCD_CONFIG__NIGHT__GAIN']), 2))
        return config


    def apply_moonmode_gain(self, config, payload):
        config['CCD_CONFIG']['MOONMODE']['GAIN'] = float(round(float(payload['CCD_CONFIG__MOONMODE__GAIN']), 2))
        return config


    def apply_day_gain(self, config, payload):
        config['CCD_CONFIG']['DAY']['GAIN'] = float(round(float(payload['CCD_CONFIG__DAY__GAIN']), 2))
        return config


    def apply_exposure_limits(self, config, payload):
        config['CCD_EXPOSURE_MAX'] = float(round(float(payload['CCD_EXPOSURE_MAX']), 6))
        config['CCD_EXPOSURE_DEF'] = float(round(float(payload['CCD_EXPOSURE_DEF']), 6))
        config['CCD_EXPOSURE_MIN'] = float(round(float(payload['CCD_EXPOSURE_MIN']), 6))
        config['CCD_EXPOSURE_MIN_DAY'] = float(round(float(payload['CCD_EXPOSURE_MIN_DAY']), 6))
        config['CCD_EXPOSURE_TIMEOUT'] = int(payload['CCD_EXPOSURE_TIMEOUT'])
        return config


    def apply_exposure_periods(self, config, payload):
        config['EXPOSURE_PERIOD'] = float(payload['EXPOSURE_PERIOD'])
        config['EXPOSURE_PERIOD_DAY'] = float(payload['EXPOSURE_PERIOD_DAY'])
        return config


class ModernAdminFullConfigAcquisitionModeParser:
    """Hybrid-owned parser for full-config binning and bit depth fields."""

    REQUIRED_FIELDS = (
        'CCD_CONFIG__NIGHT__BINNING',
        'CCD_CONFIG__MOONMODE__BINNING',
        'CCD_CONFIG__DAY__BINNING',
        'CCD_BIT_DEPTH',
    )

    def apply_night_binning(self, config, payload):
        config['CCD_CONFIG']['NIGHT']['BINNING'] = int(payload['CCD_CONFIG__NIGHT__BINNING'])
        return config


    def apply_moonmode_binning(self, config, payload):
        config['CCD_CONFIG']['MOONMODE']['BINNING'] = int(payload['CCD_CONFIG__MOONMODE__BINNING'])
        return config


    def apply_day_binning(self, config, payload):
        config['CCD_CONFIG']['DAY']['BINNING'] = int(payload['CCD_CONFIG__DAY__BINNING'])
        return config


    def apply_bit_depth(self, config, payload):
        config['CCD_BIT_DEPTH'] = int(payload['CCD_BIT_DEPTH'])
        return config


class ModernAdminFullConfigAutoGainParser:
    """Hybrid-owned parser for legacy full-config Auto Gain fields."""

    REQUIRED_FIELDS = (
        'CCD_CONFIG__AUTO_GAIN_ENABLE',
        'CCD_CONFIG__AUTO_GAIN_LEVELS',
    )

    def apply(self, config, payload):
        config['CCD_CONFIG']['AUTO_GAIN_ENABLE'] = bool(payload['CCD_CONFIG__AUTO_GAIN_ENABLE'])
        config['CCD_CONFIG']['AUTO_GAIN_LEVELS'] = int(payload['CCD_CONFIG__AUTO_GAIN_LEVELS'])
        return config


class ModernAdminFullConfigCameraSqmParser:
    """Hybrid-owned parser for full-config camera SQM fields."""

    REQUIRED_FIELDS = (
        'CAMERA_SQM__ENABLE',
        'CAMERA_SQM__ENABLE_DAY',
        'CAMERA_SQM__EXPOSURE',
        'CAMERA_SQM__GAIN',
        'CAMERA_SQM__BINNING',
        'CAMERA_SQM__EXPOSURE_PERIOD',
        'CAMERA_SQM__MAGNITUDE_OFFSET',
    )

    def apply(self, config, payload):
        config['CAMERA_SQM']['ENABLE'] = bool(payload['CAMERA_SQM__ENABLE'])
        config['CAMERA_SQM']['ENABLE_DAY'] = bool(payload['CAMERA_SQM__ENABLE_DAY'])
        config['CAMERA_SQM']['EXPOSURE'] = float(round(float(payload['CAMERA_SQM__EXPOSURE']), 6))
        config['CAMERA_SQM']['GAIN'] = float(round(float(payload['CAMERA_SQM__GAIN']), 2))
        config['CAMERA_SQM']['BINNING'] = int(payload['CAMERA_SQM__BINNING'])
        config['CAMERA_SQM']['EXPOSURE_PERIOD'] = int(payload['CAMERA_SQM__EXPOSURE_PERIOD'])
        config['CAMERA_SQM']['MAGNITUDE_OFFSET'] = float(payload['CAMERA_SQM__MAGNITUDE_OFFSET'])
        return config


class ModernAdminFullConfigFocusParser:
    """Hybrid-owned parser for legacy full-config focus timing fields."""

    REQUIRED_FIELDS = (
        'FOCUS_MODE',
        'FOCUS_DELAY',
    )

    def apply(self, config, payload):
        config['FOCUS_MODE'] = bool(payload['FOCUS_MODE'])
        config['FOCUS_DELAY'] = float(payload['FOCUS_DELAY'])
        return config


class ModernAdminFullConfigColorProcessingParser:
    """Hybrid-owned parser for full-config CFA and SCNR fields."""

    REQUIRED_FIELDS = (
        'CFA_PATTERN',
        'USE_NIGHT_COLOR',
        'SCNR_ALGORITHM',
        'SCNR_ALGORITHM_DAY',
        'SCNR_MTF_MIDTONES',
        'SCNR_MTF_MIDTONES_DAY',
    )

    def apply(self, config, payload):
        config['CFA_PATTERN'] = str(payload['CFA_PATTERN'])
        config['USE_NIGHT_COLOR'] = bool(payload['USE_NIGHT_COLOR'])
        config['SCNR_ALGORITHM'] = str(payload['SCNR_ALGORITHM'])
        config['SCNR_ALGORITHM_DAY'] = str(payload['SCNR_ALGORITHM_DAY'])
        config['SCNR_MTF_MIDTONES'] = float(payload['SCNR_MTF_MIDTONES'])
        config['SCNR_MTF_MIDTONES_DAY'] = float(payload['SCNR_MTF_MIDTONES_DAY'])
        return config


class ModernAdminFullConfigDenoiseParser:
    """Hybrid-owned parser for full-config denoise and bilateral fields."""

    REQUIRED_FIELDS = (
        'IMAGE_DENOISE',
        'IMAGE_DENOISE_DAY',
        'IMAGE_DENOISE_STRENGTH',
        'IMAGE_DENOISE_STRENGTH_DAY',
        'BILATERAL_SIGMA_COLOR',
        'BILATERAL_SIGMA_COLOR_DAY',
        'BILATERAL_SIGMA_SPACE',
        'BILATERAL_SIGMA_SPACE_DAY',
    )

    def apply(self, config, payload):
        config['IMAGE_DENOISE'] = str(payload['IMAGE_DENOISE'])
        config['IMAGE_DENOISE_DAY'] = str(payload['IMAGE_DENOISE_DAY'])
        config['IMAGE_DENOISE_STRENGTH'] = int(payload['IMAGE_DENOISE_STRENGTH'])
        config['IMAGE_DENOISE_STRENGTH_DAY'] = int(payload['IMAGE_DENOISE_STRENGTH_DAY'])
        config['BILATERAL_SIGMA_COLOR'] = int(payload['BILATERAL_SIGMA_COLOR'])
        config['BILATERAL_SIGMA_COLOR_DAY'] = int(payload['BILATERAL_SIGMA_COLOR_DAY'])
        config['BILATERAL_SIGMA_SPACE'] = int(payload['BILATERAL_SIGMA_SPACE'])
        config['BILATERAL_SIGMA_SPACE_DAY'] = int(payload['BILATERAL_SIGMA_SPACE_DAY'])
        return config


class ModernAdminFullConfigWhiteBalanceParser:
    """Hybrid-owned parser for manual full-config white balance fields."""

    REQUIRED_FIELDS = (
        'WBR_FACTOR',
        'WBG_FACTOR',
        'WBB_FACTOR',
        'WBR_FACTOR_DAY',
        'WBG_FACTOR_DAY',
        'WBB_FACTOR_DAY',
        'WBR_MTF_MIDTONES',
        'WBG_MTF_MIDTONES',
        'WBB_MTF_MIDTONES',
        'WBR_MTF_MIDTONES_DAY',
        'WBG_MTF_MIDTONES_DAY',
        'WBB_MTF_MIDTONES_DAY',
    )

    def apply(self, config, payload):
        config['WBR_FACTOR'] = float(payload['WBR_FACTOR'])
        config['WBG_FACTOR'] = float(payload['WBG_FACTOR'])
        config['WBB_FACTOR'] = float(payload['WBB_FACTOR'])
        config['WBR_FACTOR_DAY'] = float(payload['WBR_FACTOR_DAY'])
        config['WBG_FACTOR_DAY'] = float(payload['WBG_FACTOR_DAY'])
        config['WBB_FACTOR_DAY'] = float(payload['WBB_FACTOR_DAY'])
        config['WBR_MTF_MIDTONES'] = float(payload['WBR_MTF_MIDTONES'])
        config['WBG_MTF_MIDTONES'] = float(payload['WBG_MTF_MIDTONES'])
        config['WBB_MTF_MIDTONES'] = float(payload['WBB_MTF_MIDTONES'])
        config['WBR_MTF_MIDTONES_DAY'] = float(payload['WBR_MTF_MIDTONES_DAY'])
        config['WBG_MTF_MIDTONES_DAY'] = float(payload['WBG_MTF_MIDTONES_DAY'])
        config['WBB_MTF_MIDTONES_DAY'] = float(payload['WBB_MTF_MIDTONES_DAY'])
        return config


class ModernAdminFullConfigImageEnhancementParser:
    """Hybrid-owned parser for full-config image enhancement fields."""

    REQUIRED_FIELDS = (
        'SATURATION_FACTOR',
        'SATURATION_FACTOR_DAY',
        'GAMMA_CORRECTION',
        'GAMMA_CORRECTION_DAY',
        'SHARPEN_AMOUNT',
        'SHARPEN_AMOUNT_DAY',
    )

    def apply(self, config, payload):
        config['SATURATION_FACTOR'] = float(payload['SATURATION_FACTOR'])
        config['SATURATION_FACTOR_DAY'] = float(payload['SATURATION_FACTOR_DAY'])
        config['GAMMA_CORRECTION'] = float(payload['GAMMA_CORRECTION'])
        config['GAMMA_CORRECTION_DAY'] = float(payload['GAMMA_CORRECTION_DAY'])
        config['SHARPEN_AMOUNT'] = float(payload['SHARPEN_AMOUNT'])
        config['SHARPEN_AMOUNT_DAY'] = float(payload['SHARPEN_AMOUNT_DAY'])
        return config


class ModernAdminFullConfigAutoWhiteBalanceParser:
    """Hybrid-owned parser for full-config automatic white balance flags."""

    REQUIRED_FIELDS = (
        'AUTO_WB',
        'AUTO_WB_DAY',
    )

    def apply(self, config, payload):
        config['AUTO_WB'] = bool(payload['AUTO_WB'])
        config['AUTO_WB_DAY'] = bool(payload['AUTO_WB_DAY'])
        return config


class ModernAdminFullConfigDisplayUnitsParser:
    """Hybrid-owned parser for full-config display unit preferences."""

    REQUIRED_FIELDS = (
        'TEMP_DISPLAY',
        'PRESSURE_DISPLAY',
        'WINDSPEED_DISPLAY',
    )

    def apply(self, config, payload):
        config['TEMP_DISPLAY'] = str(payload['TEMP_DISPLAY'])
        config['PRESSURE_DISPLAY'] = str(payload['PRESSURE_DISPLAY'])
        config['WINDSPEED_DISPLAY'] = str(payload['WINDSPEED_DISPLAY'])
        return config


class ModernAdminFullConfigEnvironmentParser:
    """Hybrid-owned parser for full-config camera environment fields."""

    CAMERA_TEMPERATURE_FIELDS = (
        'CCD_COOLING',
        'CCD_COOLING_DAY',
        'CCD_TEMP',
        'CCD_TEMP_DAY',
    )
    RUNTIME_SOURCE_FIELDS = (
        'GPS_ENABLE',
        'CCD_TEMP_SCRIPT',
    )
    REQUIRED_FIELDS = CAMERA_TEMPERATURE_FIELDS + RUNTIME_SOURCE_FIELDS

    def apply_camera_temperature(self, config, payload):
        config['CCD_COOLING'] = bool(payload['CCD_COOLING'])
        config['CCD_COOLING_DAY'] = bool(payload['CCD_COOLING_DAY'])
        config['CCD_TEMP'] = float(payload['CCD_TEMP'])
        config['CCD_TEMP_DAY'] = float(payload['CCD_TEMP_DAY'])
        return config

    def apply_runtime_sources(self, config, payload):
        config['GPS_ENABLE'] = bool(payload['GPS_ENABLE'])
        config['CCD_TEMP_SCRIPT'] = str(payload['CCD_TEMP_SCRIPT'])
        return config


class ModernAdminFullConfigPhotometryParser:
    """Hybrid-owned parser for full-config ADU and SQM measurement fields."""

    REQUIRED_FIELDS = (
        'TARGET_ADU',
        'TARGET_ADU_DAY',
        'TARGET_ADU_DEV',
        'TARGET_ADU_DEV_DAY',
        'ADU_FOV_DIV',
        'SQM_FOV_DIV',
    )

    def apply(self, config, payload):
        config['TARGET_ADU'] = int(payload['TARGET_ADU'])
        config['TARGET_ADU_DAY'] = int(payload['TARGET_ADU_DAY'])
        config['TARGET_ADU_DEV'] = int(payload['TARGET_ADU_DEV'])
        config['TARGET_ADU_DEV_DAY'] = int(payload['TARGET_ADU_DEV_DAY'])
        config['ADU_FOV_DIV'] = int(payload['ADU_FOV_DIV'])
        config['SQM_FOV_DIV'] = int(payload['SQM_FOV_DIV'])
        return config


class ModernAdminFullConfigTimelapseParser:
    """Hybrid-owned parser for full-config timelapse fields."""

    REQUIRED_FIELDS = (
        'TIMELAPSE_ENABLE',
        'TIMELAPSE_SKIP_FRAMES',
        'TIMELAPSE__PRE_PROCESSOR',
        'TIMELAPSE__PRE_PROCESSOR_DAY',
        'TIMELAPSE__IMAGE_CIRCLE',
        'TIMELAPSE__KEOGRAM_RATIO',
        'TIMELAPSE__PRE_SCALE',
        'TIMELAPSE__FFMPEG_REPORT',
        'TIMELAPSE__USE_NIGHT_CONFIG',
    )

    def apply(self, config, payload):
        config['TIMELAPSE_ENABLE'] = bool(payload['TIMELAPSE_ENABLE'])
        config['TIMELAPSE_SKIP_FRAMES'] = int(payload['TIMELAPSE_SKIP_FRAMES'])
        config['TIMELAPSE']['PRE_PROCESSOR'] = str(payload['TIMELAPSE__PRE_PROCESSOR'])
        config['TIMELAPSE']['PRE_PROCESSOR_DAY'] = str(payload['TIMELAPSE__PRE_PROCESSOR_DAY'])
        config['TIMELAPSE']['IMAGE_CIRCLE'] = int(payload['TIMELAPSE__IMAGE_CIRCLE'])
        config['TIMELAPSE']['KEOGRAM_RATIO'] = float(payload['TIMELAPSE__KEOGRAM_RATIO'])
        config['TIMELAPSE']['PRE_SCALE'] = int(payload['TIMELAPSE__PRE_SCALE'])
        config['TIMELAPSE']['FFMPEG_REPORT'] = bool(payload['TIMELAPSE__FFMPEG_REPORT'])
        config['TIMELAPSE']['USE_NIGHT_CONFIG'] = bool(payload['TIMELAPSE__USE_NIGHT_CONFIG'])
        return config


class ModernAdminFullConfigCapturePolicyParser:
    """Hybrid-owned parser for full-config capture policy flags."""

    REQUIRED_FIELDS = (
        'CAPTURE_PAUSE',
        'DAYTIME_CAPTURE',
        'DAYTIME_CAPTURE_SAVE',
        'DAYTIME_TIMELAPSE',
    )

    def apply(self, config, payload):
        config['CAPTURE_PAUSE'] = bool(payload['CAPTURE_PAUSE'])
        config['DAYTIME_CAPTURE'] = bool(payload['DAYTIME_CAPTURE'])
        config['DAYTIME_CAPTURE_SAVE'] = bool(payload['DAYTIME_CAPTURE_SAVE'])
        config['DAYTIME_TIMELAPSE'] = bool(payload['DAYTIME_TIMELAPSE'])
        return config


class ModernAdminFullConfigContrastEnhancementParser:
    """Hybrid-owned parser for full-config contrast enhancement fields."""

    REQUIRED_FIELDS = (
        'DAYTIME_CONTRAST_ENHANCE',
        'NIGHT_CONTRAST_ENHANCE',
        'CONTRAST_ENHANCE_16BIT',
        'CLAHE_CLIPLIMIT',
        'CLAHE_GRIDSIZE',
    )

    def apply(self, config, payload):
        config['DAYTIME_CONTRAST_ENHANCE'] = bool(payload['DAYTIME_CONTRAST_ENHANCE'])
        config['NIGHT_CONTRAST_ENHANCE'] = bool(payload['NIGHT_CONTRAST_ENHANCE'])
        config['CONTRAST_ENHANCE_16BIT'] = bool(payload['CONTRAST_ENHANCE_16BIT'])
        config['CLAHE_CLIPLIMIT'] = float(payload['CLAHE_CLIPLIMIT'])
        config['CLAHE_GRIDSIZE'] = int(payload['CLAHE_GRIDSIZE'])
        return config


class ModernAdminFullConfigSkyModeThresholdParser:
    """Hybrid-owned parser for full-config night and moon mode thresholds."""

    REQUIRED_FIELDS = (
        'NIGHT_SUN_ALT_DEG',
        'NIGHT_MOONMODE_ALT_DEG',
        'NIGHT_MOONMODE_PHASE',
    )

    def apply(self, config, payload):
        config['NIGHT_SUN_ALT_DEG'] = float(payload['NIGHT_SUN_ALT_DEG'])
        config['NIGHT_MOONMODE_ALT_DEG'] = float(payload['NIGHT_MOONMODE_ALT_DEG'])
        config['NIGHT_MOONMODE_PHASE'] = float(payload['NIGHT_MOONMODE_PHASE'])
        return config


class ModernAdminFullConfigWebStatusParser:
    """Hybrid-owned parser for full-config web status fields."""

    REQUIRED_FIELDS = (
        'WEB_STATUS_TEMPLATE',
        'WEB_EXTRA_TEXT',
        'WEB_NONLOCAL_IMAGES',
        'WEB_LOCAL_IMAGES_ADMIN',
    )

    def apply(self, config, payload):
        config['WEB_STATUS_TEMPLATE'] = str(payload['WEB_STATUS_TEMPLATE'])
        config['WEB_EXTRA_TEXT'] = str(payload['WEB_EXTRA_TEXT'])
        config['WEB_NONLOCAL_IMAGES'] = bool(payload['WEB_NONLOCAL_IMAGES'])
        config['WEB_LOCAL_IMAGES_ADMIN'] = bool(payload['WEB_LOCAL_IMAGES_ADMIN'])
        return config


class ModernAdminFullConfigImageStretchParser:
    """Hybrid-owned parser for full-config image stretch fields."""

    REQUIRED_FIELDS = (
        'IMAGE_STRETCH__CLASSNAME',
        'IMAGE_STRETCH__MODE1_GAMMA',
        'IMAGE_STRETCH__MODE1_STDDEVS',
        'IMAGE_STRETCH__MODE2_SHADOWS',
        'IMAGE_STRETCH__MODE2_MIDTONES',
        'IMAGE_STRETCH__MODE2_HIGHLIGHTS',
        'IMAGE_STRETCH__MODE3_BLACK_CLIP',
        'IMAGE_STRETCH__MODE3_SHADOWS',
        'IMAGE_STRETCH__MODE3_MIDTONES',
        'IMAGE_STRETCH__MODE3_HIGHLIGHTS',
        'IMAGE_STRETCH__SPLIT',
        'IMAGE_STRETCH__MOONMODE',
        'IMAGE_STRETCH__DAYTIME',
    )

    def apply(self, config, payload):
        image_stretch = config['IMAGE_STRETCH']
        image_stretch['CLASSNAME'] = str(payload['IMAGE_STRETCH__CLASSNAME'])
        image_stretch['MODE1_GAMMA'] = float(payload['IMAGE_STRETCH__MODE1_GAMMA'])
        image_stretch['MODE1_STDDEVS'] = float(payload['IMAGE_STRETCH__MODE1_STDDEVS'])
        image_stretch['MODE2_SHADOWS'] = float(payload['IMAGE_STRETCH__MODE2_SHADOWS'])
        image_stretch['MODE2_MIDTONES'] = float(payload['IMAGE_STRETCH__MODE2_MIDTONES'])
        image_stretch['MODE2_HIGHLIGHTS'] = float(payload['IMAGE_STRETCH__MODE2_HIGHLIGHTS'])
        image_stretch['MODE3_BLACK_CLIP'] = float(payload['IMAGE_STRETCH__MODE3_BLACK_CLIP'])
        image_stretch['MODE3_SHADOWS'] = float(payload['IMAGE_STRETCH__MODE3_SHADOWS'])
        image_stretch['MODE3_MIDTONES'] = float(payload['IMAGE_STRETCH__MODE3_MIDTONES'])
        image_stretch['MODE3_HIGHLIGHTS'] = float(payload['IMAGE_STRETCH__MODE3_HIGHLIGHTS'])
        image_stretch['SPLIT'] = bool(payload['IMAGE_STRETCH__SPLIT'])
        image_stretch['MOONMODE'] = bool(payload['IMAGE_STRETCH__MOONMODE'])
        image_stretch['DAYTIME'] = bool(payload['IMAGE_STRETCH__DAYTIME'])
        return config


class ModernAdminFullConfigKeogramParser:
    """Hybrid-owned parser for full-config keogram fields."""

    REQUIRED_FIELDS = (
        'KEOGRAM_ANGLE',
        'KEOGRAM_H_SCALE',
        'KEOGRAM_V_SCALE',
        'KEOGRAM_CROP_TOP',
        'KEOGRAM_CROP_BOTTOM',
        'KEOGRAM_LABEL',
    )

    def apply(self, config, payload):
        config['KEOGRAM_ANGLE'] = float(payload['KEOGRAM_ANGLE'])
        config['KEOGRAM_H_SCALE'] = int(payload['KEOGRAM_H_SCALE'])
        config['KEOGRAM_V_SCALE'] = int(payload['KEOGRAM_V_SCALE'])
        config['KEOGRAM_CROP_TOP'] = int(payload['KEOGRAM_CROP_TOP'])
        config['KEOGRAM_CROP_BOTTOM'] = int(payload['KEOGRAM_CROP_BOTTOM'])
        config['KEOGRAM_LABEL'] = bool(payload['KEOGRAM_LABEL'])
        return config


class ModernAdminFullConfigLongTermKeogramParser:
    """Hybrid-owned parser for full-config long-term keogram fields."""

    REQUIRED_FIELDS = (
        'LONGTERM_KEOGRAM__ENABLE',
        'LONGTERM_KEOGRAM__OFFSET_X',
        'LONGTERM_KEOGRAM__OFFSET_Y',
        'LONGTERM_KEOGRAM__OPENCV_FONT_SCALE',
        'LONGTERM_KEOGRAM__PIL_FONT_SIZE',
        'LONGTERM_KEOGRAM__MONTH_LABEL_TEMPLATE',
    )

    def apply(self, config, payload):
        longterm_keogram = config['LONGTERM_KEOGRAM']
        longterm_keogram['ENABLE'] = bool(payload['LONGTERM_KEOGRAM__ENABLE'])
        longterm_keogram['OFFSET_X'] = int(payload['LONGTERM_KEOGRAM__OFFSET_X'])
        longterm_keogram['OFFSET_Y'] = int(payload['LONGTERM_KEOGRAM__OFFSET_Y'])
        longterm_keogram['OPENCV_FONT_SCALE'] = float(payload['LONGTERM_KEOGRAM__OPENCV_FONT_SCALE'])
        longterm_keogram['PIL_FONT_SIZE'] = int(payload['LONGTERM_KEOGRAM__PIL_FONT_SIZE'])
        longterm_keogram['MONTH_LABEL_TEMPLATE'] = str(payload['LONGTERM_KEOGRAM__MONTH_LABEL_TEMPLATE'])
        return config


class ModernAdminFullConfigRealtimeKeogramParser:
    """Hybrid-owned parser for full-config realtime keogram fields."""

    REQUIRED_FIELDS = (
        'REALTIME_KEOGRAM__MAX_ENTRIES',
        'REALTIME_KEOGRAM__SAVE_INTERVAL',
        'REALTIME_KEOGRAM__LABEL',
    )

    def apply(self, config, payload):
        realtime_keogram = config['REALTIME_KEOGRAM']
        realtime_keogram['MAX_ENTRIES'] = int(payload['REALTIME_KEOGRAM__MAX_ENTRIES'])
        realtime_keogram['SAVE_INTERVAL'] = int(payload['REALTIME_KEOGRAM__SAVE_INTERVAL'])
        realtime_keogram['LABEL'] = bool(payload['REALTIME_KEOGRAM__LABEL'])
        return config


class ModernAdminSettingsConfigValidationService:
    """Hybrid-owned type validation for config payloads before persistence."""

    SKIP_KEYS = (
        'INDI_CONFIG_DEFAULTS',
        'INDI_CONFIG_DAY',
    )

    SKIP_NESTED_KEYS = (
        ('FILETRANSFER', 'LIBCURL_OPTIONS'),
    )

    def __init__(self, base_config, logger=None):
        self.base_config = base_config
        self.logger = logger


    def validate(self, config):
        for key in config.keys():
            if key in self.SKIP_KEYS:
                continue

            if isinstance(config[key], dict):
                self.validate_nested_config(config, key)
            else:
                self.validate_value(config, key)

        return True


    def validate_nested_config(self, config, key):
        for nested_key in config[key].keys():
            if (key, nested_key) in self.SKIP_NESTED_KEYS:
                continue

            try:
                expected_value = self.base_config[key][nested_key]
            except KeyError:
                self.log_warning(
                    'Config key not found in base config: [%s][%s]',
                    str(key),
                    str(nested_key),
                )
                continue

            value = config[key][nested_key]
            if not isinstance(value, self.valid_types(value, expected_value)):
                self.log_error(
                    'Config key has wrong type: [%s][%s] (%s vs %s)',
                    str(key),
                    str(nested_key),
                    str(type(expected_value)),
                    str(type(value)),
                )
                raise ConfigSaveException(
                    'Config key has wrong type: [{0:s}][{1:s}]'.format(
                        str(key),
                        str(nested_key),
                    ),
                )


    def validate_value(self, config, key):
        try:
            expected_value = self.base_config[key]
        except KeyError:
            self.log_warning('Config key not found in base config: [%s]', str(key))
            return

        value = config[key]
        if not isinstance(value, self.valid_types(value, expected_value)):
            self.log_error(
                'Config key has wrong type: [%s] (%s vs %s)',
                str(key),
                str(type(expected_value)),
                str(type(value)),
            )
            raise ConfigSaveException(
                'Config key has wrong type: [{0:s}]'.format(str(key)),
            )


    def valid_types(self, value, expected_value):
        if isinstance(value, int):
            return (int, float)

        return type(expected_value)


    def log_error(self, message, *args):
        if self.logger is not None:
            self.logger.error(message, *args)


    def log_warning(self, message, *args):
        if self.logger is not None:
            self.logger.warning(message, *args)


class ModernAdminSettingsCredentialEncryptionService:
    """Hybrid-owned credential encryption for config revision persistence."""

    CREDENTIAL_FIELDS = (
        ('FILETRANSFER', 'PASSWORD', 'PASSWORD_E'),
        ('S3UPLOAD', 'SECRET_KEY', 'SECRET_KEY_E'),
        ('MQTTPUBLISH', 'PASSWORD', 'PASSWORD_E'),
        ('SYNCAPI', 'APIKEY', 'APIKEY_E'),
        ('PYCURL_CAMERA', 'PASSWORD', 'PASSWORD_E'),
        ('TEMP_SENSOR', 'OPENWEATHERMAP_APIKEY', 'OPENWEATHERMAP_APIKEY_E'),
        ('TEMP_SENSOR', 'WUNDERGROUND_APIKEY', 'WUNDERGROUND_APIKEY_E'),
        ('TEMP_SENSOR', 'ASTROSPHERIC_APIKEY', 'ASTROSPHERIC_APIKEY_E'),
        ('TEMP_SENSOR', 'MQTT_PASSWORD', 'MQTT_PASSWORD_E'),
        ('DEVICE', 'MQTT_PASSWORD', 'MQTT_PASSWORD_E'),
        ('LIBCAMERA', 'MQTT_PASSWORD', 'MQTT_PASSWORD_E'),
        ('ADSB', 'PASSWORD', 'PASSWORD_E'),
        ('IMAGE_OVERLAY', 'A_PASSWORD', 'A_PASSWORD_E'),
    )

    def __init__(self, password_key_adapter, cipher_factory=None):
        self.password_key_adapter = password_key_adapter
        self.cipher_factory = cipher_factory or Fernet


    def encrypt_config(self, config):
        encrypted = bool(config['ENCRYPT_PASSWORDS'])
        cipher = None
        if encrypted:
            cipher = self.cipher_factory(self.password_key_adapter().encode())

        encrypted_values = []
        for section, plain_key, encrypted_key in self.CREDENTIAL_FIELDS:
            plain_value = str(config.get(section, {}).get(plain_key, ''))
            if encrypted and plain_value:
                encrypted_value = cipher.encrypt(plain_value.encode()).decode()
                plain_value = ''
            else:
                encrypted_value = ''

            encrypted_values.append((
                section,
                plain_key,
                encrypted_key,
                plain_value,
                encrypted_value,
            ))

        encrypted_config = config.copy()
        for section, _plain_key, _encrypted_key in self.CREDENTIAL_FIELDS:
            if not isinstance(encrypted_config.get(section), dict):
                encrypted_config[section] = {}

        for section, plain_key, encrypted_key, plain_value, encrypted_value in encrypted_values:
            encrypted_config[section][plain_key] = plain_value
            encrypted_config[section][encrypted_key] = encrypted_value

        return encrypted_config, encrypted


class ModernAdminSettingsCredentialDecryptionService:
    """Hybrid-owned credential decryption for config revision reads."""

    CREDENTIAL_FIELDS = (
        ('FILETRANSFER', 'PASSWORD', 'PASSWORD_E', 'PASSWORD'),
        ('S3UPLOAD', 'SECRET_KEY', 'SECRET_KEY_E', 'SECRET_KEY'),
        ('MQTTPUBLISH', 'PASSWORD', 'PASSWORD_E', 'PASSWORD'),
        ('SYNCAPI', 'APIKEY', 'APIKEY_E', 'APIKEY'),
        ('PYCURL_CAMERA', 'PASSWORD', 'PASSWORD_E', 'PASSWORD'),
        ('TEMP_SENSOR', 'OPENWEATHERMAP_APIKEY', 'OPENWEATHERMAP_APIKEY_E', 'OPENWEATHERMAP_APIKEY'),
        ('TEMP_SENSOR', 'WUNDERGROUND_APIKEY', 'WUNDERGROUND_APIKEY_E', 'WUNDERGROUND_APIKEY'),
        ('TEMP_SENSOR', 'ASTROSPHERIC_APIKEY', 'ASTROSPHERIC_APIKEY_E', 'ASTROSPHERIC_APIKEY'),
        ('TEMP_SENSOR', 'MQTT_PASSWORD', 'MQTT_PASSWORD_E', 'MQTT_PASSWORD'),
        ('DEVICE', 'MQTT_PASSWORD', 'MQTT_PASSWORD_E', 'MQTT_PASSWORD'),
        ('LIBCAMERA', 'MQTT_PASSWORD', 'MQTT_PASSWORD_E', 'MQTT_PASSWORD'),
        ('ADSB', 'PASSWORD', 'PASSWORD_E', 'PASSWORD'),
        ('IMAGE_OVERLAY', 'A_PASSWORD', 'A_PASSWORD_E', 'APASSWORD'),
    )

    def __init__(self, password_key_adapter, cipher_factory=None):
        self.password_key_adapter = password_key_adapter
        self.cipher_factory = cipher_factory or Fernet


    def decrypt_config(self, config):
        encrypted = bool(config['ENCRYPT_PASSWORDS'])
        cipher = None
        if encrypted:
            cipher = self.cipher_factory(self.password_key_adapter().encode())

        decrypted_values = []
        for section, plain_key, encrypted_key, encrypted_fallback_key in self.CREDENTIAL_FIELDS:
            if encrypted:
                encrypted_value = config.get(section, {}).get(encrypted_key, '')
                if encrypted_value:
                    plain_value = cipher.decrypt(encrypted_value.encode()).decode()
                else:
                    plain_value = config.get(section, {}).get(encrypted_fallback_key, '')
            else:
                plain_value = config.get(section, {}).get(plain_key, '')

            decrypted_values.append((section, plain_key, encrypted_key, plain_value))

        decrypted_config = config.copy()
        for section, _plain_key, _encrypted_key, _fallback_key in self.CREDENTIAL_FIELDS:
            if not isinstance(decrypted_config.get(section), dict):
                decrypted_config[section] = {}

        for section, plain_key, encrypted_key, plain_value in decrypted_values:
            decrypted_config[section][plain_key] = plain_value
            decrypted_config[section][encrypted_key] = ''

        return decrypted_config


class ModernAdminConfigRevisionPersistenceAdapter:
    """Hybrid-owned persistence for an already validated config revision."""

    def __init__(self, config_model, db_session, config_level, clock=None):
        self.config_model = config_model
        self.db_session = db_session
        self.config_level = config_level
        self.clock = clock or self.utcnow


    def save_revision(self, config, user_entry, note, encrypted):
        config_entry = self.config_model(
            data=config,
            createDate=self.clock(),
            level=str(self.config_level),
            user_id=user_entry.id,
            note=str(note),
            encrypted=encrypted,
        )

        self.db_session.add(config_entry)
        self.db_session.commit()
        return config_entry


    def utcnow(self):
        return datetime.now(tz=timezone.utc).replace(tzinfo=None)


class ModernAdminSettingsRevisionRollbackService:
    """Hybrid-owned application of a confirmed config revision rollback."""

    ROLLBACK_NOTE = 'Revert to config: {revision_id:d}'

    def apply_revision(self, revision, current_config, save_adapter, username='system'):
        current_config.update(revision.data)
        return save_adapter(
            username,
            self.ROLLBACK_NOTE.format(revision_id=revision.id),
        )


class ModernAdminSettingsRuntimeService:
    """Hybrid-owned boundary for Modern settings runtime persistence.

    The service owns the Modern settings save intent. The default config adapter
    still delegates to the existing config implementation so persistence
    behavior stays unchanged.
    """

    def __init__(self, config_adapter_factory=None):
        self.config_adapter_factory = config_adapter_factory or self.default_config_adapter_factory


    def save_config_revision(self, config, username, note):
        config_adapter = self.config_adapter_factory()
        config_adapter.config = config
        return config_adapter.save(username, note)


    def save_full_config(self, config, username, note, config_adapter):
        config_adapter.config = config
        return config_adapter.save(username, note)


    def default_config_adapter_factory(self):
        from .config import IndiAllSkyConfig

        return IndiAllSkyConfig()


class ModernAdminSettingsRestoreValidationError(ValueError):
    pass


class ModernAdminSettingsRestoreService:
    """Hybrid-owned boundary for settings restore execution intent.

    The service validates the restore target and delegates persistence to the
    existing config adapter so restore behavior and storage semantics remain
    unchanged.
    """

    REQUIRED_CONFIG_KEYS = (
        'INDI_SERVER',
        'CCD_CONFIG',
        'INDI_CONFIG_DEFAULTS',
    )

    DEFAULT_RESTORE_NOTE = 'Manual config restore from upload'

    def post_restore_cleanup(self, flush_configs=None, reset_keys=None, flush_adapter=None, reset_adapter=None):
        cleanup_flags = self.normalize_post_restore_flags(
            flush_configs=flush_configs,
            reset_keys=reset_keys,
        )

        if cleanup_flags['flush_configs'] and flush_adapter is not None:
            flush_adapter()

        if cleanup_flags['reset_keys'] and reset_adapter is not None:
            reset_adapter()

        return cleanup_flags


    def normalize_post_restore_flags(self, flush_configs=None, reset_keys=None):
        return {
            'flush_configs': bool(flush_configs),
            'reset_keys': bool(reset_keys),
        }


    def restore_config(self, config, username, config_adapter, note=None):
        self.validate_restore_target(config)
        config_adapter.config = config
        return config_adapter.save(username, note or self.DEFAULT_RESTORE_NOTE)


    def validate_restore_target(self, config):
        if not isinstance(config, dict):
            raise ModernAdminSettingsRestoreValidationError('Not a valid indi-allsky config')

        if (
            not isinstance(config.get('INDI_SERVER'), str)
            or not isinstance(config.get('CCD_CONFIG'), dict)
            or not isinstance(config.get('INDI_CONFIG_DEFAULTS'), dict)
        ):
            raise ModernAdminSettingsRestoreValidationError('Not a valid indi-allsky config')

        return True


class ModernAdminSettingsReloadCommandService:
    """Hybrid-owned reload/restart intent boundary for settings saves."""

    RELOAD_ACTION = 'reload'
    SAVE_MESSAGE = 'Saved new config'
    RELOAD_MESSAGE = 'Saved new config,  Reloading indi-allsky service.'

    def execute_after_save(self, reload_requested=None, status_adapter=None, task_adapter=None):
        plan = self.build_after_save_plan(reload_requested=reload_requested)

        if plan['reload_requested']:
            if status_adapter is not None:
                status_adapter()

            if task_adapter is not None:
                task_adapter(plan['task_action'])

        return plan


    def build_after_save_plan(self, reload_requested=None):
        reload_enabled = self.normalize_reload_intent(reload_requested)
        return {
            'reload_requested': reload_enabled,
            'task_action': self.RELOAD_ACTION if reload_enabled else None,
            'success_message': self.RELOAD_MESSAGE if reload_enabled else self.SAVE_MESSAGE,
        }


    def normalize_reload_intent(self, reload_requested=None):
        return bool(reload_requested)


class ModernAdminSettingsRevisionMetadataService:
    """Hybrid-owned read model for config revision metadata.

    The DB/query object is injected by the Flask layer. This keeps restore
    execution and persistence unchanged while moving history/restore metadata
    ownership out of Modern views.
    """

    RESTORE_WARNING = 'Read-only inspection only. Actual restore flow remains in Classic UI.'
    RESTORE_DETAIL_WARNING = 'Read-only metadata inspection only. Raw config payload and restore actions are intentionally hidden.'

    def __init__(self, query, id_field=None, created_field=None):
        self.query = query
        self.id_field = id_field
        self.created_field = created_field


    def history_context(self, limit=25):
        rows = self.list_revisions(limit=limit, include_restore_state=False)
        return {
            'modern_admin_config_history_rows'             : rows,
            'modern_admin_config_history_count'            : len(rows),
            'modern_admin_config_history_display_limit'    : limit,
            'modern_admin_config_history_encrypted_count'  : len([
                row for row in rows if row['encrypted'] == 'Yes'
            ]),
            'modern_admin_config_history_levels'           : sorted({row['level'] for row in rows}),
            'modern_admin_config_history_encrypted_states' : sorted({row['encrypted'] for row in rows}),
        }


    def restore_context(self, limit=25):
        rows = self.list_revisions(limit=limit, include_restore_state=True)
        return {
            'modern_admin_config_restore_rows'             : rows,
            'modern_admin_config_restore_count'            : len(rows),
            'modern_admin_config_restore_display_limit'    : limit,
            'modern_admin_config_restore_likely_count'     : len([
                row for row in rows if row['restore_state'] == 'Likely restore candidate'
            ]),
            'modern_admin_config_restore_encrypted_count'  : len([
                row for row in rows if row['encrypted'] == 'Yes'
            ]),
            'modern_admin_config_restore_levels'           : sorted({row['level'] for row in rows}),
            'modern_admin_config_restore_states'           : sorted({row['restore_state'] for row in rows}),
            'modern_admin_config_restore_warning'          : self.RESTORE_WARNING,
        }


    def restore_detail_context(self, config_id):
        entry = self.lookup_revision(config_id)
        return {
            'modern_admin_config_restore_detail'  : self.format_revision(
                entry,
                include_restore_state=True,
            ),
            'modern_admin_config_restore_warning' : self.RESTORE_DETAIL_WARNING,
        }


    def list_revisions(self, limit=25, include_restore_state=False):
        query = self.query
        if self.created_field is not None and hasattr(query, 'order_by'):
            query = query.order_by(self.created_field.desc())

        if hasattr(query, 'limit'):
            query = query.limit(limit)

        return [
            self.format_revision(entry, include_restore_state=include_restore_state)
            for entry in query
        ]


    def lookup_revision(self, config_id):
        query = self.query
        if self.id_field is not None and hasattr(query, 'filter'):
            query = query.filter(self.id_field == config_id)

        return query.one()


    def format_revision(self, entry, include_restore_state=False):
        user_row = getattr(entry, 'user', None)
        entry_data = entry.data if isinstance(getattr(entry, 'data', None), dict) else {}
        summary, data_size = self.summarize_config_data(entry_data)

        row = {
            'id'         : entry.id,
            'created'    : self.format_datetime(getattr(entry, 'createDate', None)),
            'user'       : user_row.username if user_row else 'Deleted user',
            'user_id'    : user_row.id if user_row else 'N/A',
            'level'      : entry.level or 'Unknown',
            'encrypted'  : 'Yes' if bool(entry.encrypted) else 'No',
            'note'       : entry.note or 'No note',
            'summary'    : summary,
            'data_size'  : data_size,
        }

        if include_restore_state:
            row['restore_state'] = self.restore_state(entry_data, summary)

        return row


    def restore_state(self, data, summary):
        if data and summary != 'Non-dict payload':
            return 'Likely restore candidate'

        return 'Unavailable'


    def format_datetime(self, value, default='Unknown'):
        if not value:
            return default
        if hasattr(value, 'strftime'):
            return value.strftime('%Y-%m-%d %H:%M:%S')
        return str(value)


    def summarize_config_data(self, data):
        if not isinstance(data, dict):
            if data is None:
                return 'No config snapshot', 'N/A'
            return 'Non-dict payload', 'N/A'

        try:
            import json

            size_bytes = len(json.dumps(data, default=str).encode('utf-8'))
            size_display = '{:.1f} KB'.format(size_bytes / 1024.0)
        except (TypeError, ValueError):
            size_display = 'Unavailable'

        summary = 'Keys: {0:d}'.format(len(data))
        return summary, size_display
