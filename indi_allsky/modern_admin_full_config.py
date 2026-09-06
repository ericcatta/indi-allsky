"""Hybrid-owned complete interpretation of the existing Full Config payload.

Form validation and persistence belong to their separate boundaries. This
parser preserves legacy casts and incremental mutation, including on errors.
"""

import json
from dataclasses import dataclass

from .modern_admin_settings_runtime import ModernAdminFullConfigAcquisitionModeParser
from .modern_admin_settings_runtime import ModernAdminFullConfigAutoGainParser
from .modern_admin_settings_runtime import ModernAdminFullConfigAutoWhiteBalanceParser
from .modern_admin_settings_runtime import ModernAdminFullConfigCameraConnectionParser
from .modern_admin_settings_runtime import ModernAdminFullConfigCameraSqmParser
from .modern_admin_settings_runtime import ModernAdminFullConfigCapturePolicyParser
from .modern_admin_settings_runtime import ModernAdminFullConfigColorProcessingParser
from .modern_admin_settings_runtime import ModernAdminFullConfigContrastEnhancementParser
from .modern_admin_settings_runtime import ModernAdminFullConfigDenoiseParser
from .modern_admin_settings_runtime import ModernAdminFullConfigDisplayUnitsParser
from .modern_admin_settings_runtime import ModernAdminFullConfigEnvironmentParser
from .modern_admin_settings_runtime import ModernAdminFullConfigExposureGainParser
from .modern_admin_settings_runtime import ModernAdminFullConfigFish2PanoParser
from .modern_admin_settings_runtime import ModernAdminFullConfigFocusParser
from .modern_admin_settings_runtime import ModernAdminFullConfigImageCalibrationParser
from .modern_admin_settings_runtime import ModernAdminFullConfigImageEnhancementParser
from .modern_admin_settings_runtime import ModernAdminFullConfigImageOutputParser
from .modern_admin_settings_runtime import ModernAdminFullConfigImageStretchParser
from .modern_admin_settings_runtime import ModernAdminFullConfigImageTransformParser
from .modern_admin_settings_runtime import ModernAdminFullConfigKeogramParser
from .modern_admin_settings_runtime import ModernAdminFullConfigLensGeometryParser
from .modern_admin_settings_runtime import ModernAdminFullConfigLensMetadataParser
from .modern_admin_settings_runtime import ModernAdminFullConfigLongTermKeogramParser
from .modern_admin_settings_runtime import ModernAdminFullConfigPhotometryParser
from .modern_admin_settings_runtime import ModernAdminFullConfigRealtimeKeogramParser
from .modern_admin_settings_runtime import ModernAdminFullConfigSkyModeThresholdParser
from .modern_admin_settings_runtime import ModernAdminFullConfigStartrailsParser
from .modern_admin_settings_runtime import ModernAdminFullConfigStationIdentityParser
from .modern_admin_settings_runtime import ModernAdminFullConfigTimelapseParser
from .modern_admin_settings_runtime import ModernAdminFullConfigWebStatusParser
from .modern_admin_settings_runtime import ModernAdminFullConfigWhiteBalanceParser


@dataclass(frozen=True)
class ModernAdminFullConfigParseResult:
    config: dict
    reload_on_save: bool
    config_note: str


class ModernAdminFullConfigParser:
    """Parse an already-prepared config in place, without Flask or I/O."""

    def full_config_camera_connection_parser(self):
        return ModernAdminFullConfigCameraConnectionParser()

    def full_config_station_identity_parser(self):
        return ModernAdminFullConfigStationIdentityParser()

    def full_config_lens_metadata_parser(self):
        return ModernAdminFullConfigLensMetadataParser()

    def full_config_lens_geometry_parser(self):
        return ModernAdminFullConfigLensGeometryParser()

    def full_config_exposure_gain_parser(self):
        return ModernAdminFullConfigExposureGainParser()

    def full_config_acquisition_mode_parser(self):
        return ModernAdminFullConfigAcquisitionModeParser()

    def full_config_auto_gain_parser(self):
        return ModernAdminFullConfigAutoGainParser()

    def full_config_auto_white_balance_parser(self):
        return ModernAdminFullConfigAutoWhiteBalanceParser()

    def full_config_camera_sqm_parser(self):
        return ModernAdminFullConfigCameraSqmParser()

    def full_config_capture_policy_parser(self):
        return ModernAdminFullConfigCapturePolicyParser()

    def full_config_focus_parser(self):
        return ModernAdminFullConfigFocusParser()

    def full_config_color_processing_parser(self):
        return ModernAdminFullConfigColorProcessingParser()

    def full_config_contrast_enhancement_parser(self):
        return ModernAdminFullConfigContrastEnhancementParser()

    def full_config_denoise_parser(self):
        return ModernAdminFullConfigDenoiseParser()

    def full_config_display_units_parser(self):
        return ModernAdminFullConfigDisplayUnitsParser()

    def full_config_environment_parser(self):
        return ModernAdminFullConfigEnvironmentParser()

    def full_config_photometry_parser(self):
        return ModernAdminFullConfigPhotometryParser()

    def full_config_sky_mode_threshold_parser(self):
        return ModernAdminFullConfigSkyModeThresholdParser()

    def full_config_timelapse_parser(self):
        return ModernAdminFullConfigTimelapseParser()

    def full_config_web_status_parser(self):
        return ModernAdminFullConfigWebStatusParser()

    def full_config_white_balance_parser(self):
        return ModernAdminFullConfigWhiteBalanceParser()

    def full_config_image_enhancement_parser(self):
        return ModernAdminFullConfigImageEnhancementParser()

    def full_config_image_stretch_parser(self):
        return ModernAdminFullConfigImageStretchParser()

    def full_config_keogram_parser(self):
        return ModernAdminFullConfigKeogramParser()

    def full_config_longterm_keogram_parser(self):
        return ModernAdminFullConfigLongTermKeogramParser()

    def full_config_realtime_keogram_parser(self):
        return ModernAdminFullConfigRealtimeKeogramParser()

    def full_config_startrails_parser(self):
        return ModernAdminFullConfigStartrailsParser()

    def full_config_image_calibration_parser(self):
        return ModernAdminFullConfigImageCalibrationParser()

    def full_config_image_output_parser(self):
        return ModernAdminFullConfigImageOutputParser()

    def full_config_image_transform_parser(self):
        return ModernAdminFullConfigImageTransformParser()

    def full_config_fish2pano_parser(self):
        return ModernAdminFullConfigFish2PanoParser()


    def parse(self, config, payload):
        self.full_config_camera_connection_parser().apply(config, payload)
        station_identity_parser = self.full_config_station_identity_parser()
        station_identity_parser.apply(config, payload)
        self.full_config_lens_metadata_parser().apply(config, payload)
        self.full_config_lens_geometry_parser().apply(config, payload)
        exposure_gain_parser = self.full_config_exposure_gain_parser()
        acquisition_mode_parser = self.full_config_acquisition_mode_parser()
        exposure_gain_parser.apply_night_gain(config, payload)
        acquisition_mode_parser.apply_night_binning(config, payload)
        exposure_gain_parser.apply_moonmode_gain(config, payload)
        acquisition_mode_parser.apply_moonmode_binning(config, payload)
        exposure_gain_parser.apply_day_gain(config, payload)
        acquisition_mode_parser.apply_day_binning(config, payload)
        self.full_config_auto_gain_parser().apply(config, payload)
        exposure_gain_parser.apply_exposure_limits(config, payload)
        acquisition_mode_parser.apply_bit_depth(config, payload)
        exposure_gain_parser.apply_exposure_periods(config, payload)
        self.full_config_camera_sqm_parser().apply(config, payload)
        self.full_config_focus_parser().apply(config, payload)
        self.full_config_color_processing_parser().apply(config, payload)
        self.full_config_denoise_parser().apply(config, payload)
        self.full_config_white_balance_parser().apply(config, payload)
        self.full_config_image_enhancement_parser().apply(config, payload)
        environment_parser = self.full_config_environment_parser()
        environment_parser.apply_camera_temperature(config, payload)
        self.full_config_auto_white_balance_parser().apply(config, payload)
        self.full_config_display_units_parser().apply(config, payload)
        environment_parser.apply_runtime_sources(config, payload)
        self.full_config_photometry_parser().apply(config, payload)
        config['DETECT_STARS']                         = bool(payload['DETECT_STARS'])
        config['DETECT_STARS_THOLD']                   = float(payload['DETECT_STARS_THOLD'])
        config['DETECT_METEORS']                       = bool(payload['DETECT_METEORS'])
        config['DETECT_METEORS_THOLD']                 = int(payload['DETECT_METEORS_THOLD'])
        config['DETECT_MASK']                          = str(payload['DETECT_MASK'])
        config['DETECT_DRAW']                          = bool(payload['DETECT_DRAW'])
        config['EVENT_CANDIDATE_TRIGGERS']['enabled']  = bool(payload.get('EVENT_CANDIDATE_TRIGGERS__ENABLED', payload.get('EVENT_CANDIDATE_TRIGGERS__enabled', False)))
        config['EVENT_CANDIDATE_TRIGGERS']['max_candidates_per_hour'] = int(payload.get('EVENT_CANDIDATE_TRIGGERS__MAX_CANDIDATES_PER_HOUR', payload.get('EVENT_CANDIDATE_TRIGGERS__max_candidates_per_hour', 100)))
        config['LOGO_OVERLAY']                         = str(payload['LOGO_OVERLAY'])
        config['HEALTHCHECK']['DISK_USAGE']            = float(payload['HEALTHCHECK__DISK_USAGE'])
        config['HEALTHCHECK']['SWAP_USAGE']            = float(payload['HEALTHCHECK__SWAP_USAGE'])
        station_identity_parser.apply_location(config, payload)
        self.full_config_timelapse_parser().apply(config, payload)
        self.full_config_capture_policy_parser().apply(config, payload)
        self.full_config_contrast_enhancement_parser().apply(config, payload)
        self.full_config_sky_mode_threshold_parser().apply(config, payload)
        self.full_config_web_status_parser().apply(config, payload)
        self.full_config_image_stretch_parser().apply(config, payload)
        self.full_config_keogram_parser().apply(config, payload)
        self.full_config_longterm_keogram_parser().apply(config, payload)
        self.full_config_realtime_keogram_parser().apply(config, payload)
        self.full_config_startrails_parser().apply(config, payload)
        self.full_config_image_calibration_parser().apply(config, payload)
        self.full_config_image_output_parser().apply(config, payload)
        self.full_config_image_transform_parser().apply(config, payload)
        #config['IMAGE_ROTATE_WITH_OFFSET']             = bool(payload['IMAGE_ROTATE_WITH_OFFSET'])
        self.full_config_fish2pano_parser().apply(config, payload)
        config['IMAGE_SAVE_FITS']                      = bool(payload['IMAGE_SAVE_FITS'])
        config['IMAGE_SAVE_FITS_COMPRESSED']           = bool(payload['IMAGE_SAVE_FITS_COMPRESSED'])
        config['IMAGE_SAVE_FITS_PERIOD']               = int(payload['IMAGE_SAVE_FITS_PERIOD'])
        config['NIGHT_GRAYSCALE']                      = bool(payload['NIGHT_GRAYSCALE'])
        config['DAYTIME_GRAYSCALE']                    = bool(payload['DAYTIME_GRAYSCALE'])
        config['MOON_OVERLAY']['ENABLE']               = bool(payload['MOON_OVERLAY__ENABLE'])
        config['MOON_OVERLAY']['X']                    = int(payload['MOON_OVERLAY__X'])
        config['MOON_OVERLAY']['Y']                    = int(payload['MOON_OVERLAY__Y'])
        config['MOON_OVERLAY']['SCALE']                = float(payload['MOON_OVERLAY__SCALE'])
        config['MOON_OVERLAY']['DARK_SIDE_SCALE']      = float(payload['MOON_OVERLAY__DARK_SIDE_SCALE'])
        config['MOON_OVERLAY']['FLIP_V']               = bool(payload['MOON_OVERLAY__FLIP_V'])
        config['MOON_OVERLAY']['FLIP_H']               = bool(payload['MOON_OVERLAY__FLIP_H'])
        config['LIGHTGRAPH_OVERLAY']['ENABLE']         = bool(payload['LIGHTGRAPH_OVERLAY__ENABLE'])
        config['LIGHTGRAPH_OVERLAY']['GRAPH_HEIGHT']   = int(payload['LIGHTGRAPH_OVERLAY__GRAPH_HEIGHT'])
        config['LIGHTGRAPH_OVERLAY']['GRAPH_BORDER']   = int(payload['LIGHTGRAPH_OVERLAY__GRAPH_BORDER'])
        config['LIGHTGRAPH_OVERLAY']['Y']              = int(payload['LIGHTGRAPH_OVERLAY__Y'])
        config['LIGHTGRAPH_OVERLAY']['OFFSET_X']       = int(payload['LIGHTGRAPH_OVERLAY__OFFSET_X'])
        config['LIGHTGRAPH_OVERLAY']['SCALE']          = float(payload['LIGHTGRAPH_OVERLAY__SCALE'])
        config['LIGHTGRAPH_OVERLAY']['NOW_MARKER_SIZE']  = int(payload['LIGHTGRAPH_OVERLAY__NOW_MARKER_SIZE'])
        config['LIGHTGRAPH_OVERLAY']['OPACITY']        = int(payload['LIGHTGRAPH_OVERLAY__OPACITY'])
        config['LIGHTGRAPH_OVERLAY']['PIL_FONT_SIZE']  = int(payload['LIGHTGRAPH_OVERLAY__PIL_FONT_SIZE'])
        config['LIGHTGRAPH_OVERLAY']['OPENCV_FONT_SCALE'] = float(payload['LIGHTGRAPH_OVERLAY__OPENCV_FONT_SCALE'])
        config['LIGHTGRAPH_OVERLAY']['LABEL']          = bool(payload['LIGHTGRAPH_OVERLAY__LABEL'])
        config['LIGHTGRAPH_OVERLAY']['HOUR_LINES']     = bool(payload['LIGHTGRAPH_OVERLAY__HOUR_LINES'])
        config['IMAGE_OVERLAY']['ENABLE']              = bool(payload['IMAGE_OVERLAY__ENABLE'])
        config['IMAGE_OVERLAY']['LOAD_INTERVAL']       = int(payload['IMAGE_OVERLAY__LOAD_INTERVAL'])
        config['IMAGE_OVERLAY']['A_URL']               = str(payload['IMAGE_OVERLAY__A_URL'])
        config['IMAGE_OVERLAY']['A_IMAGE_FILE_TYPE']   = str(payload['IMAGE_OVERLAY__A_IMAGE_FILE_TYPE'])
        config['IMAGE_OVERLAY']['A_WIDTH']             = int(payload['IMAGE_OVERLAY__A_WIDTH'])
        config['IMAGE_OVERLAY']['A_HEIGHT']            = int(payload['IMAGE_OVERLAY__A_HEIGHT'])
        config['IMAGE_OVERLAY']['A_X']                 = int(payload['IMAGE_OVERLAY__A_X'])
        config['IMAGE_OVERLAY']['A_Y']                 = int(payload['IMAGE_OVERLAY__A_Y'])
        config['IMAGE_OVERLAY']['A_USERNAME']          = str(payload['IMAGE_OVERLAY__A_USERNAME'])
        config['IMAGE_OVERLAY']['A_PASSWORD']          = str(payload['IMAGE_OVERLAY__A_PASSWORD'])
        config['IMAGE_EXPORT_RAW']                     = str(payload['IMAGE_EXPORT_RAW'])
        config['IMAGE_EXPORT_FOLDER']                  = str(payload['IMAGE_EXPORT_FOLDER'])
        config['IMAGE_EXPORT_FLIP_V']                  = bool(payload['IMAGE_EXPORT_FLIP_V'])
        config['IMAGE_EXPORT_FLIP_H']                  = bool(payload['IMAGE_EXPORT_FLIP_H'])
        config['IMAGE_STACK_METHOD']                   = str(payload['IMAGE_STACK_METHOD'])
        config['IMAGE_STACK_COUNT']                    = int(payload['IMAGE_STACK_COUNT'])
        config['IMAGE_STACK_ALIGN']                    = bool(payload['IMAGE_STACK_ALIGN'])
        config['IMAGE_ALIGN_DETECTSIGMA']              = int(payload['IMAGE_ALIGN_DETECTSIGMA'])
        config['IMAGE_ALIGN_POINTS']                   = int(payload['IMAGE_ALIGN_POINTS'])
        config['IMAGE_ALIGN_SOURCEMINAREA']            = int(payload['IMAGE_ALIGN_SOURCEMINAREA'])
        config['IMAGE_STACK_SPLIT']                    = bool(payload['IMAGE_STACK_SPLIT'])
        config['IMAGE_STACK_MOONMODE']                 = bool(payload['IMAGE_STACK_MOONMODE'])
        config['IMAGE_STACK_DAY']                      = bool(payload['IMAGE_STACK_DAY'])
        config['IMAGE_QUEUE_MAX']                      = int(payload['IMAGE_QUEUE_MAX'])
        config['IMAGE_QUEUE_MIN']                      = int(payload['IMAGE_QUEUE_MIN'])
        config['IMAGE_QUEUE_BACKOFF']                  = float(payload['IMAGE_QUEUE_BACKOFF'])
        config['IMAGE_SAVE_HOOK_PRE']                  = str(payload['IMAGE_SAVE_HOOK_PRE'])
        config['IMAGE_SAVE_HOOK_POST']                 = str(payload['IMAGE_SAVE_HOOK_POST'])
        config['IMAGE_SAVE_HOOK_TIMEOUT']              = int(payload['IMAGE_SAVE_HOOK_TIMEOUT'])
        config['CAPTURE_HOOK_PRE']                     = str(payload['CAPTURE_HOOK_PRE'])
        config['CAPTURE_HOOK_TIMEOUT']                 = int(payload['CAPTURE_HOOK_TIMEOUT'])
        config['BACKUP_DB_PERIOD_DAYS']                = int(payload['BACKUP_DB_PERIOD_DAYS'])
        config['IMAGE_EXPIRE_DAYS']                    = int(payload['IMAGE_EXPIRE_DAYS'])
        config['IMAGE_RAW_EXPIRE_DAYS']                = int(payload['IMAGE_RAW_EXPIRE_DAYS'])
        config['IMAGE_FITS_EXPIRE_DAYS']               = int(payload['IMAGE_FITS_EXPIRE_DAYS'])
        config['TIMELAPSE_EXPIRE_DAYS']                = int(payload['TIMELAPSE_EXPIRE_DAYS'])
        config['TIMELAPSE_OVERWRITE']                  = bool(payload['TIMELAPSE_OVERWRITE'])
        config['FFMPEG_FRAMERATE']                     = int(payload['FFMPEG_FRAMERATE'])
        config['FFMPEG_FRAMERATE_DAY']                 = int(payload['FFMPEG_FRAMERATE_DAY'])
        config['FFMPEG_BITRATE']                       = str(payload['FFMPEG_BITRATE'])
        config['FFMPEG_BITRATE_DAY']                   = str(payload['FFMPEG_BITRATE_DAY'])
        config['FFMPEG_VFSCALE']                       = str(payload['FFMPEG_VFSCALE'])
        config['FFMPEG_VFSCALE_DAY']                   = str(payload['FFMPEG_VFSCALE_DAY'])
        config['FFMPEG_VFSCALE_STARTRAIL']             = str(payload['FFMPEG_VFSCALE_STARTRAIL'])
        config['FFMPEG_CODEC']                         = str(payload['FFMPEG_CODEC'])
        config['FFMPEG_EXTRA_OPTIONS']                 = str(payload['FFMPEG_EXTRA_OPTIONS'])
        config['FFMPEG_EXTRA_OPTIONS_DAY']             = str(payload['FFMPEG_EXTRA_OPTIONS_DAY'])
        config['IMAGE_LABEL_SYSTEM']                   = str(payload['IMAGE_LABEL_SYSTEM'])
        config['TEXT_PROPERTIES']['FONT_FACE']         = str(payload['TEXT_PROPERTIES__FONT_FACE'])
        config['TEXT_PROPERTIES']['FONT_SCALE']        = float(payload['TEXT_PROPERTIES__FONT_SCALE'])
        config['TEXT_PROPERTIES']['FONT_THICKNESS']    = int(payload['TEXT_PROPERTIES__FONT_THICKNESS'])
        config['TEXT_PROPERTIES']['FONT_OUTLINE']      = bool(payload['TEXT_PROPERTIES__FONT_OUTLINE'])
        config['TEXT_PROPERTIES']['FONT_HEIGHT']       = int(payload['TEXT_PROPERTIES__FONT_HEIGHT'])
        config['TEXT_PROPERTIES']['FONT_X']            = int(payload['TEXT_PROPERTIES__FONT_X'])
        config['TEXT_PROPERTIES']['FONT_Y']            = int(payload['TEXT_PROPERTIES__FONT_Y'])
        config['TEXT_PROPERTIES']['PIL_FONT_FILE']     = str(payload['TEXT_PROPERTIES__PIL_FONT_FILE'])
        config['TEXT_PROPERTIES']['PIL_FONT_CUSTOM']   = str(payload['TEXT_PROPERTIES__PIL_FONT_CUSTOM'])
        config['TEXT_PROPERTIES']['PIL_FONT_SIZE']     = int(payload['TEXT_PROPERTIES__PIL_FONT_SIZE'])
        config['CARDINAL_DIRS']['ENABLE']              = bool(payload['CARDINAL_DIRS__ENABLE'])
        config['CARDINAL_DIRS']['SWAP_NS']             = bool(payload['CARDINAL_DIRS__SWAP_NS'])
        config['CARDINAL_DIRS']['SWAP_EW']             = bool(payload['CARDINAL_DIRS__SWAP_EW'])
        config['CARDINAL_DIRS']['CHAR_NORTH']          = str(payload['CARDINAL_DIRS__CHAR_NORTH'])
        config['CARDINAL_DIRS']['CHAR_EAST']           = str(payload['CARDINAL_DIRS__CHAR_EAST'])
        config['CARDINAL_DIRS']['CHAR_WEST']           = str(payload['CARDINAL_DIRS__CHAR_WEST'])
        config['CARDINAL_DIRS']['CHAR_SOUTH']          = str(payload['CARDINAL_DIRS__CHAR_SOUTH'])
        config['CARDINAL_DIRS']['DIAMETER']            = int(payload['CARDINAL_DIRS__DIAMETER'])
        config['CARDINAL_DIRS']['OFFSET_X']            = int(payload['CARDINAL_DIRS__OFFSET_X'])
        config['CARDINAL_DIRS']['OFFSET_Y']            = int(payload['CARDINAL_DIRS__OFFSET_Y'])
        config['CARDINAL_DIRS']['OFFSET_TOP']          = int(payload['CARDINAL_DIRS__OFFSET_TOP'])
        config['CARDINAL_DIRS']['OFFSET_LEFT']         = int(payload['CARDINAL_DIRS__OFFSET_LEFT'])
        config['CARDINAL_DIRS']['OFFSET_RIGHT']        = int(payload['CARDINAL_DIRS__OFFSET_RIGHT'])
        config['CARDINAL_DIRS']['OFFSET_BOTTOM']       = int(payload['CARDINAL_DIRS__OFFSET_BOTTOM'])
        config['CARDINAL_DIRS']['OPENCV_FONT_SCALE']   = float(payload['CARDINAL_DIRS__OPENCV_FONT_SCALE'])
        config['CARDINAL_DIRS']['PIL_FONT_SIZE']       = int(payload['CARDINAL_DIRS__PIL_FONT_SIZE'])
        config['CARDINAL_DIRS']['OUTLINE_CIRCLE']      = bool(payload['CARDINAL_DIRS__OUTLINE_CIRCLE'])
        config['ORB_PROPERTIES']['MODE']               = str(payload['ORB_PROPERTIES__MODE'])
        config['ORB_PROPERTIES']['RADIUS']             = int(payload['ORB_PROPERTIES__RADIUS'])
        config['ORB_PROPERTIES']['AZ_OFFSET']          = float(payload['ORB_PROPERTIES__AZ_OFFSET'])
        config['ORB_PROPERTIES']['RETROGRADE']         = bool(payload['ORB_PROPERTIES__RETROGRADE'])
        config['IMAGE_BORDER']['TOP']                  = int(payload['IMAGE_BORDER__TOP'])
        config['IMAGE_BORDER']['LEFT']                 = int(payload['IMAGE_BORDER__LEFT'])
        config['IMAGE_BORDER']['RIGHT']                = int(payload['IMAGE_BORDER__RIGHT'])
        config['IMAGE_BORDER']['BOTTOM']               = int(payload['IMAGE_BORDER__BOTTOM'])
        config['UPLOAD_WORKERS']                       = int(payload['UPLOAD_WORKERS'])
        config['FILETRANSFER']['CLASSNAME']            = str(payload['FILETRANSFER__CLASSNAME'])
        config['FILETRANSFER']['HOST']                 = str(payload['FILETRANSFER__HOST'])
        config['FILETRANSFER']['PORT']                 = int(payload['FILETRANSFER__PORT'])
        config['FILETRANSFER']['USERNAME']             = str(payload['FILETRANSFER__USERNAME'])
        config['FILETRANSFER']['PASSWORD']             = str(payload['FILETRANSFER__PASSWORD'])
        config['FILETRANSFER']['PRIVATE_KEY']          = str(payload['FILETRANSFER__PRIVATE_KEY'])
        config['FILETRANSFER']['PUBLIC_KEY']           = str(payload['FILETRANSFER__PUBLIC_KEY'])
        config['FILETRANSFER']['CONNECT_TIMEOUT']      = float(payload['FILETRANSFER__CONNECT_TIMEOUT'])
        config['FILETRANSFER']['TIMEOUT']              = float(payload['FILETRANSFER__TIMEOUT'])
        config['FILETRANSFER']['CERT_BYPASS']          = bool(payload['FILETRANSFER__CERT_BYPASS'])
        config['FILETRANSFER']['ATOMIC_TRANSFERS']     = bool(payload['FILETRANSFER__ATOMIC_TRANSFERS'])
        config['FILETRANSFER']['FORCE_IPV4']           = bool(payload['FILETRANSFER__FORCE_IPV4'])
        config['FILETRANSFER']['FORCE_IPV6']           = bool(payload['FILETRANSFER__FORCE_IPV6'])
        config['FILETRANSFER']['REMOTE_IMAGE_NAME']        = str(payload['FILETRANSFER__REMOTE_IMAGE_NAME'])
        config['FILETRANSFER']['REMOTE_IMAGE_FOLDER']      = str(payload['FILETRANSFER__REMOTE_IMAGE_FOLDER'])
        config['FILETRANSFER']['REMOTE_PANORAMA_NAME']     = str(payload['FILETRANSFER__REMOTE_PANORAMA_NAME'])
        config['FILETRANSFER']['REMOTE_PANORAMA_FOLDER']   = str(payload['FILETRANSFER__REMOTE_PANORAMA_FOLDER'])
        config['FILETRANSFER']['REMOTE_METADATA_NAME']     = str(payload['FILETRANSFER__REMOTE_METADATA_NAME'])
        config['FILETRANSFER']['REMOTE_METADATA_FOLDER']   = str(payload['FILETRANSFER__REMOTE_METADATA_FOLDER'])
        config['FILETRANSFER']['REMOTE_RAW_NAME']          = str(payload['FILETRANSFER__REMOTE_RAW_NAME'])
        config['FILETRANSFER']['REMOTE_RAW_FOLDER']        = str(payload['FILETRANSFER__REMOTE_RAW_FOLDER'])
        config['FILETRANSFER']['REMOTE_FITS_NAME']         = str(payload['FILETRANSFER__REMOTE_FITS_NAME'])
        config['FILETRANSFER']['REMOTE_FITS_FOLDER']       = str(payload['FILETRANSFER__REMOTE_FITS_FOLDER'])
        config['FILETRANSFER']['REMOTE_VIDEO_NAME']        = str(payload['FILETRANSFER__REMOTE_VIDEO_NAME'])
        config['FILETRANSFER']['REMOTE_VIDEO_FOLDER']      = str(payload['FILETRANSFER__REMOTE_VIDEO_FOLDER'])
        config['FILETRANSFER']['REMOTE_MINI_VIDEO_NAME']   = str(payload['FILETRANSFER__REMOTE_MINI_VIDEO_NAME'])
        config['FILETRANSFER']['REMOTE_MINI_VIDEO_FOLDER'] = str(payload['FILETRANSFER__REMOTE_MINI_VIDEO_FOLDER'])
        config['FILETRANSFER']['REMOTE_KEOGRAM_NAME']      = str(payload['FILETRANSFER__REMOTE_KEOGRAM_NAME'])
        config['FILETRANSFER']['REMOTE_KEOGRAM_FOLDER']    = str(payload['FILETRANSFER__REMOTE_KEOGRAM_FOLDER'])
        config['FILETRANSFER']['REMOTE_STARTRAIL_NAME']    = str(payload['FILETRANSFER__REMOTE_STARTRAIL_NAME'])
        config['FILETRANSFER']['REMOTE_STARTRAIL_FOLDER']  = str(payload['FILETRANSFER__REMOTE_STARTRAIL_FOLDER'])
        config['FILETRANSFER']['REMOTE_STARTRAIL_VIDEO_NAME']   = str(payload['FILETRANSFER__REMOTE_STARTRAIL_VIDEO_NAME'])
        config['FILETRANSFER']['REMOTE_STARTRAIL_VIDEO_FOLDER'] = str(payload['FILETRANSFER__REMOTE_STARTRAIL_VIDEO_FOLDER'])
        config['FILETRANSFER']['REMOTE_PANORAMA_VIDEO_NAME']    = str(payload['FILETRANSFER__REMOTE_PANORAMA_VIDEO_NAME'])
        config['FILETRANSFER']['REMOTE_PANORAMA_VIDEO_FOLDER']  = str(payload['FILETRANSFER__REMOTE_PANORAMA_VIDEO_FOLDER'])
        config['FILETRANSFER']['REMOTE_REALTIME_KEOGRAM_NAME']  = str(payload['FILETRANSFER__REMOTE_REALTIME_KEOGRAM_NAME'])
        config['FILETRANSFER']['REMOTE_REALTIME_KEOGRAM_FOLDER'] = str(payload['FILETRANSFER__REMOTE_REALTIME_KEOGRAM_FOLDER'])
        config['FILETRANSFER']['REMOTE_ENDOFNIGHT_FOLDER']      = str(payload['FILETRANSFER__REMOTE_ENDOFNIGHT_FOLDER'])
        config['FILETRANSFER']['REMOTE_LATEST_FOLDER']          = str(payload['FILETRANSFER__REMOTE_LATEST_FOLDER'])
        config['FILETRANSFER']['REMOTE_DB_BACKUP_FOLDER']       = str(payload['FILETRANSFER__REMOTE_DB_BACKUP_FOLDER'])
        config['FILETRANSFER']['UPLOAD_IMAGE']         = int(payload['FILETRANSFER__UPLOAD_IMAGE'])
        config['FILETRANSFER']['UPLOAD_PANORAMA']      = int(payload['FILETRANSFER__UPLOAD_PANORAMA'])
        config['FILETRANSFER']['UPLOAD_METADATA']      = bool(payload['FILETRANSFER__UPLOAD_METADATA'])
        config['FILETRANSFER']['UPLOAD_VIDEO']         = bool(payload['FILETRANSFER__UPLOAD_VIDEO'])
        config['FILETRANSFER']['UPLOAD_MINI_VIDEO']    = bool(payload['FILETRANSFER__UPLOAD_MINI_VIDEO'])
        config['FILETRANSFER']['UPLOAD_RAW']           = bool(payload['FILETRANSFER__UPLOAD_RAW'])
        config['FILETRANSFER']['UPLOAD_FITS']          = bool(payload['FILETRANSFER__UPLOAD_FITS'])
        config['FILETRANSFER']['UPLOAD_KEOGRAM']       = bool(payload['FILETRANSFER__UPLOAD_KEOGRAM'])
        config['FILETRANSFER']['UPLOAD_STARTRAIL']     = bool(payload['FILETRANSFER__UPLOAD_STARTRAIL'])
        config['FILETRANSFER']['UPLOAD_STARTRAIL_VIDEO']  = bool(payload['FILETRANSFER__UPLOAD_STARTRAIL_VIDEO'])
        config['FILETRANSFER']['UPLOAD_PANORAMA_VIDEO']   = bool(payload['FILETRANSFER__UPLOAD_PANORAMA_VIDEO'])
        config['FILETRANSFER']['UPLOAD_REALTIME_KEOGRAM'] = int(payload['FILETRANSFER__UPLOAD_REALTIME_KEOGRAM'])
        config['FILETRANSFER']['UPLOAD_ENDOFNIGHT']       = bool(payload['FILETRANSFER__UPLOAD_ENDOFNIGHT'])
        config['FILETRANSFER']['UPLOAD_LATEST_IMAGE']     = bool(payload['FILETRANSFER__UPLOAD_LATEST_IMAGE'])
        config['FILETRANSFER']['UPLOAD_LATEST_PANORAMA']  = bool(payload['FILETRANSFER__UPLOAD_LATEST_PANORAMA'])
        config['FILETRANSFER']['UPLOAD_LATEST_RAW']       = bool(payload['FILETRANSFER__UPLOAD_LATEST_RAW'])
        config['FILETRANSFER']['UPLOAD_LATEST_VIDEO']     = bool(payload['FILETRANSFER__UPLOAD_LATEST_VIDEO'])
        config['FILETRANSFER']['UPLOAD_DB_BACKUP']        = bool(payload['FILETRANSFER__UPLOAD_DB_BACKUP'])
        config['S3UPLOAD']['CLASSNAME']                = str(payload['S3UPLOAD__CLASSNAME'])
        config['S3UPLOAD']['ENABLE']                   = bool(payload['S3UPLOAD__ENABLE'])
        config['S3UPLOAD']['ACCESS_KEY']               = str(payload['S3UPLOAD__ACCESS_KEY'])
        config['S3UPLOAD']['SECRET_KEY']               = str(payload['S3UPLOAD__SECRET_KEY'])
        config['S3UPLOAD']['CREDS_FILE']               = str(payload['S3UPLOAD__CREDS_FILE'])
        config['S3UPLOAD']['BUCKET']                   = str(payload['S3UPLOAD__BUCKET'])
        config['S3UPLOAD']['REGION']                   = str(payload['S3UPLOAD__REGION'])
        config['S3UPLOAD']['NAMESPACE']                = str(payload['S3UPLOAD__NAMESPACE'])
        config['S3UPLOAD']['HOST']                     = str(payload['S3UPLOAD__HOST'])
        config['S3UPLOAD']['ENDPOINT_URL']             = str(payload['S3UPLOAD__ENDPOINT_URL'])
        config['S3UPLOAD']['PORT']                     = int(payload['S3UPLOAD__PORT'])
        config['S3UPLOAD']['CONNECT_TIMEOUT']          = float(payload['S3UPLOAD__CONNECT_TIMEOUT'])
        config['S3UPLOAD']['TIMEOUT']                  = float(payload['S3UPLOAD__TIMEOUT'])
        config['S3UPLOAD']['URL_TEMPLATE']             = str(payload['S3UPLOAD__URL_TEMPLATE'])
        config['S3UPLOAD']['STORAGE_CLASS']            = str(payload['S3UPLOAD__STORAGE_CLASS'])
        config['S3UPLOAD']['ACL']                      = str(payload['S3UPLOAD__ACL'])
        config['S3UPLOAD']['TLS']                      = bool(payload['S3UPLOAD__TLS'])
        config['S3UPLOAD']['CERT_BYPASS']              = bool(payload['S3UPLOAD__CERT_BYPASS'])
        config['S3UPLOAD']['UPLOAD_FITS']              = bool(payload['S3UPLOAD__UPLOAD_FITS'])
        config['S3UPLOAD']['UPLOAD_RAW']               = bool(payload['S3UPLOAD__UPLOAD_RAW'])
        config['MQTTPUBLISH']['ENABLE']                = bool(payload['MQTTPUBLISH__ENABLE'])
        config['MQTTPUBLISH']['TRANSPORT']             = str(payload['MQTTPUBLISH__TRANSPORT'])
        config['MQTTPUBLISH']['PROTOCOL']              = str(payload['MQTTPUBLISH__PROTOCOL'])
        config['MQTTPUBLISH']['HOST']                  = str(payload['MQTTPUBLISH__HOST'])
        config['MQTTPUBLISH']['PORT']                  = int(payload['MQTTPUBLISH__PORT'])
        config['MQTTPUBLISH']['USERNAME']              = str(payload['MQTTPUBLISH__USERNAME'])
        config['MQTTPUBLISH']['PASSWORD']              = str(payload['MQTTPUBLISH__PASSWORD'])
        config['MQTTPUBLISH']['BASE_TOPIC']            = str(payload['MQTTPUBLISH__BASE_TOPIC'])
        config['MQTTPUBLISH']['QOS']                   = int(payload['MQTTPUBLISH__QOS'])
        config['MQTTPUBLISH']['TLS']                   = bool(payload['MQTTPUBLISH__TLS'])
        config['MQTTPUBLISH']['CERT_BYPASS']           = bool(payload['MQTTPUBLISH__CERT_BYPASS'])
        config['MQTTPUBLISH']['PUBLISH_IMAGE']         = bool(payload['MQTTPUBLISH__PUBLISH_IMAGE'])
        config['SYNCAPI']['ENABLE']                    = bool(payload['SYNCAPI__ENABLE'])
        config['SYNCAPI']['BASEURL']                   = str(payload['SYNCAPI__BASEURL'])
        config['SYNCAPI']['USERNAME']                  = str(payload['SYNCAPI__USERNAME'])
        config['SYNCAPI']['APIKEY']                    = str(payload['SYNCAPI__APIKEY'])
        config['SYNCAPI']['CERT_BYPASS']               = bool(payload['SYNCAPI__CERT_BYPASS'])
        config['SYNCAPI']['POST_S3']                   = bool(payload['SYNCAPI__POST_S3'])
        config['SYNCAPI']['EMPTY_FILE']                = bool(payload['SYNCAPI__EMPTY_FILE'])
        config['SYNCAPI']['UPLOAD_IMAGE']              = int(payload['SYNCAPI__UPLOAD_IMAGE'])
        config['SYNCAPI']['UPLOAD_PANORAMA']           = int(payload['SYNCAPI__UPLOAD_PANORAMA'])
        #config['SYNCAPI']['UPLOAD_VIDEO']              = bool(payload['SYNCAPI__UPLOAD_VIDEO'])  # cannot be changed
        config['SYNCAPI']['CONNECT_TIMEOUT']           = float(payload['SYNCAPI__CONNECT_TIMEOUT'])
        config['SYNCAPI']['TIMEOUT']                   = float(payload['SYNCAPI__TIMEOUT'])
        config['YOUTUBE']['ENABLE']                    = bool(payload['YOUTUBE__ENABLE'])
        config['YOUTUBE']['SECRETS_FILE']              = str(payload['YOUTUBE__SECRETS_FILE'])
        config['YOUTUBE']['PRIVACY_STATUS']            = str(payload['YOUTUBE__PRIVACY_STATUS'])
        config['YOUTUBE']['TITLE_TEMPLATE']            = str(payload['YOUTUBE__TITLE_TEMPLATE'])
        config['YOUTUBE']['DESCRIPTION_TEMPLATE']      = str(payload['YOUTUBE__DESCRIPTION_TEMPLATE'])
        config['YOUTUBE']['CATEGORY']                  = int(payload['YOUTUBE__CATEGORY'])
        config['YOUTUBE']['UPLOAD_VIDEO']              = bool(payload['YOUTUBE__UPLOAD_VIDEO'])
        config['YOUTUBE']['UPLOAD_MINI_VIDEO']         = bool(payload['YOUTUBE__UPLOAD_MINI_VIDEO'])
        config['YOUTUBE']['UPLOAD_STARTRAIL_VIDEO']    = bool(payload['YOUTUBE__UPLOAD_STARTRAIL_VIDEO'])
        config['YOUTUBE']['UPLOAD_PANORAMA_VIDEO']     = bool(payload['YOUTUBE__UPLOAD_PANORAMA_VIDEO'])
        config['FITSHEADERS'][0][0]                    = str(payload['FITSHEADERS__0__KEY'])
        config['FITSHEADERS'][0][1]                    = str(payload['FITSHEADERS__0__VAL'])
        config['FITSHEADERS'][1][0]                    = str(payload['FITSHEADERS__1__KEY'])
        config['FITSHEADERS'][1][1]                    = str(payload['FITSHEADERS__1__VAL'])
        config['FITSHEADERS'][2][0]                    = str(payload['FITSHEADERS__2__KEY'])
        config['FITSHEADERS'][2][1]                    = str(payload['FITSHEADERS__2__VAL'])
        config['FITSHEADERS'][3][0]                    = str(payload['FITSHEADERS__3__KEY'])
        config['FITSHEADERS'][3][1]                    = str(payload['FITSHEADERS__3__VAL'])
        config['FITSHEADERS'][4][0]                    = str(payload['FITSHEADERS__4__KEY'])
        config['FITSHEADERS'][4][1]                    = str(payload['FITSHEADERS__4__VAL'])
        config['LIBCAMERA']['IMAGE_FILE_TYPE']         = str(payload['LIBCAMERA__IMAGE_FILE_TYPE'])
        config['LIBCAMERA']['IMAGE_FILE_TYPE_DAY']     = str(payload['LIBCAMERA__IMAGE_FILE_TYPE_DAY'])
        config['LIBCAMERA']['IMMEDIATE']               = bool(payload['LIBCAMERA__IMMEDIATE'])
        config['LIBCAMERA']['IMMEDIATE_DAY']           = bool(payload['LIBCAMERA__IMMEDIATE_DAY'])
        config['LIBCAMERA']['AWB']                     = str(payload['LIBCAMERA__AWB'])
        config['LIBCAMERA']['AWB_DAY']                 = str(payload['LIBCAMERA__AWB_DAY'])
        config['LIBCAMERA']['AWB_ENABLE']              = bool(payload['LIBCAMERA__AWB_ENABLE'])
        config['LIBCAMERA']['AWB_ENABLE_DAY']          = bool(payload['LIBCAMERA__AWB_ENABLE_DAY'])
        config['LIBCAMERA']['CCM_DISABLE']             = bool(payload['LIBCAMERA__CCM_DISABLE'])
        config['LIBCAMERA']['CCM_DISABLE_DAY']         = bool(payload['LIBCAMERA__CCM_DISABLE_DAY'])
        config['LIBCAMERA']['CAMERA_ID']               = int(payload['LIBCAMERA__CAMERA_ID'])
        config['LIBCAMERA']['EXTRA_OPTIONS']           = str(payload['LIBCAMERA__EXTRA_OPTIONS'])
        config['LIBCAMERA']['EXTRA_OPTIONS_DAY']       = str(payload['LIBCAMERA__EXTRA_OPTIONS_DAY'])
        config['LIBCAMERA']['MQTT_TRANSPORT']          = str(payload['LIBCAMERA__MQTT_TRANSPORT'])
        config['LIBCAMERA']['MQTT_PROTOCOL']           = str(payload['LIBCAMERA__MQTT_PROTOCOL'])
        config['LIBCAMERA']['MQTT_HOST']               = str(payload['LIBCAMERA__MQTT_HOST'])
        config['LIBCAMERA']['MQTT_PORT']               = int(payload['LIBCAMERA__MQTT_PORT'])
        config['LIBCAMERA']['MQTT_USERNAME']           = str(payload['LIBCAMERA__MQTT_USERNAME'])
        config['LIBCAMERA']['MQTT_PASSWORD']           = str(payload['LIBCAMERA__MQTT_PASSWORD'])
        config['LIBCAMERA']['MQTT_QOS']                = int(payload['LIBCAMERA__MQTT_QOS'])
        config['LIBCAMERA']['MQTT_TLS']                = bool(payload['LIBCAMERA__MQTT_TLS'])
        config['LIBCAMERA']['MQTT_CERT_BYPASS']        = bool(payload['LIBCAMERA__MQTT_CERT_BYPASS'])
        config['LIBCAMERA']['MQTT_EXPOSURE_TOPIC']     = str(payload['LIBCAMERA__MQTT_EXPOSURE_TOPIC'])
        config['LIBCAMERA']['MQTT_IMAGE_TOPIC']        = str(payload['LIBCAMERA__MQTT_IMAGE_TOPIC'])
        config['LIBCAMERA']['MQTT_METADATA_TOPIC']     = str(payload['LIBCAMERA__MQTT_METADATA_TOPIC'])
        config['PYCURL_CAMERA']['URL']                 = str(payload['PYCURL_CAMERA__URL'])
        config['PYCURL_CAMERA']['IMAGE_FILE_TYPE']     = str(payload['PYCURL_CAMERA__IMAGE_FILE_TYPE'])
        config['PYCURL_CAMERA']['USERNAME']            = str(payload['PYCURL_CAMERA__USERNAME'])
        config['PYCURL_CAMERA']['PASSWORD']            = str(payload['PYCURL_CAMERA__PASSWORD'])
        config['ACCUM_CAMERA']['SUB_EXPOSURE_MAX']     = float(payload['ACCUM_CAMERA__SUB_EXPOSURE_MAX'])
        config['ACCUM_CAMERA']['EVEN_EXPOSURES']       = bool(payload['ACCUM_CAMERA__EVEN_EXPOSURES'])
        config['ACCUM_CAMERA']['CLAMP_16BIT']          = bool(payload['ACCUM_CAMERA__CLAMP_16BIT'])
        config['TEST_CAMERA']['WIDTH']                 = int(payload['TEST_CAMERA__WIDTH'])
        config['TEST_CAMERA']['HEIGHT']                = int(payload['TEST_CAMERA__HEIGHT'])
        config['TEST_CAMERA']['IMAGE_CIRCLE_DIAMETER'] = int(payload['TEST_CAMERA__IMAGE_CIRCLE_DIAMETER'])
        config['TEST_CAMERA']['IMAGE_CIRCLE_OFFSET_X'] = int(payload['TEST_CAMERA__IMAGE_CIRCLE_OFFSET_X'])
        config['TEST_CAMERA']['IMAGE_CIRCLE_OFFSET_Y'] = int(payload['TEST_CAMERA__IMAGE_CIRCLE_OFFSET_Y'])
        config['TEST_CAMERA']['ROTATING_STAR_COUNT']   = int(payload['TEST_CAMERA__ROTATING_STAR_COUNT'])
        config['TEST_CAMERA']['ROTATING_STAR_FACTOR']  = float(payload['TEST_CAMERA__ROTATING_STAR_FACTOR'])
        config['TEST_CAMERA']['BUBBLE_COUNT']          = int(payload['TEST_CAMERA__BUBBLE_COUNT'])
        config['VIRTUALSKY']['MAGNITUDE']              = float(payload['VIRTUALSKY__MAGNITUDE'])
        config['VIRTUALSKY']['CONSTELLATIONS']         = bool(payload['VIRTUALSKY__CONSTELLATIONS'])
        config['VIRTUALSKY']['CONSTELLATIONLABELS']    = bool(payload['VIRTUALSKY__CONSTELLATIONLABELS'])
        config['VIRTUALSKY']['SHOWSTARS']              = bool(payload['VIRTUALSKY__SHOWSTARS'])
        config['VIRTUALSKY']['SHOWSTARLABELS']         = bool(payload['VIRTUALSKY__SHOWSTARLABELS'])
        config['VIRTUALSKY']['SHOWPLANETS']            = bool(payload['VIRTUALSKY__SHOWPLANETS'])
        config['VIRTUALSKY']['SHOWPLANETLABELS']       = bool(payload['VIRTUALSKY__SHOWPLANETLABELS'])
        config['VIRTUALSKY']['IMAGE_CIRCLE_DIAMETER']  = int(payload['VIRTUALSKY__IMAGE_CIRCLE_DIAMETER'])
        config['VIRTUALSKY']['LATITUDE_OFFSET']        = float(payload['VIRTUALSKY__LATITUDE_OFFSET'])
        config['VIRTUALSKY']['LONGITUDE_OFFSET']       = float(payload['VIRTUALSKY__LONGITUDE_OFFSET'])
        config['VIRTUALSKY']['OFFSET_X']               = int(payload['VIRTUALSKY__OFFSET_X'])
        config['VIRTUALSKY']['OFFSET_Y']               = int(payload['VIRTUALSKY__OFFSET_Y'])
        #config['VIRTUALSKY']['FLIP_NS']                = bool(payload['VIRTUALSKY__FLIP_NS'])
        #config['VIRTUALSKY']['FLIP_EW']                = bool(payload['VIRTUALSKY__FLIP_EW'])
        config['CIRCULAR_DISPLAY']['ENABLE']           = bool(payload['CIRCULAR_DISPLAY__ENABLE'])
        config['CIRCULAR_DISPLAY']['RESOLUTION']       = int(payload['CIRCULAR_DISPLAY__RESOLUTION'])
        config['CIRCULAR_DISPLAY']['IMAGE_CIRCLE_DIAMETER'] = int(payload['CIRCULAR_DISPLAY__IMAGE_CIRCLE_DIAMETER'])
        config['FOCUSER']['CLASSNAME']                 = str(payload['FOCUSER__CLASSNAME'])
        config['FOCUSER']['GPIO_PIN_1']                = str(payload['FOCUSER__GPIO_PIN_1'])
        config['FOCUSER']['GPIO_PIN_2']                = str(payload['FOCUSER__GPIO_PIN_2'])
        config['FOCUSER']['GPIO_PIN_3']                = str(payload['FOCUSER__GPIO_PIN_3'])
        config['FOCUSER']['GPIO_PIN_4']                = str(payload['FOCUSER__GPIO_PIN_4'])
        config['FOCUSER']['I2C_ADDRESS']               = str(payload['FOCUSER__I2C_ADDRESS'])
        config['DEW_HEATER']['CLASSNAME']              = str(payload['DEW_HEATER__CLASSNAME'])
        config['DEW_HEATER']['I2C_ADDRESS']            = str(payload['DEW_HEATER__I2C_ADDRESS'])
        config['DEW_HEATER']['PIN_1']                  = str(payload['DEW_HEATER__PIN_1'])
        config['DEW_HEATER']['INVERT_OUTPUT']          = bool(payload['DEW_HEATER__INVERT_OUTPUT'])
        config['DEW_HEATER']['ENABLE_DAY']             = bool(payload['DEW_HEATER__ENABLE_DAY'])
        config['DEW_HEATER']['LEVEL_DEF']              = int(payload['DEW_HEATER__LEVEL_DEF'])
        config['DEW_HEATER']['THOLD_ENABLE']           = bool(payload['DEW_HEATER__THOLD_ENABLE'])
        config['DEW_HEATER']['MANUAL_TARGET']          = float(payload['DEW_HEATER__MANUAL_TARGET'])
        config['DEW_HEATER']['TEMP_USER_VAR_SLOT']     = str(payload['DEW_HEATER__TEMP_USER_VAR_SLOT'])
        config['DEW_HEATER']['DEWPOINT_USER_VAR_SLOT'] = str(payload['DEW_HEATER__DEWPOINT_USER_VAR_SLOT'])
        config['DEW_HEATER']['LEVEL_LOW']              = int(payload['DEW_HEATER__LEVEL_LOW'])
        config['DEW_HEATER']['LEVEL_MED']              = int(payload['DEW_HEATER__LEVEL_MED'])
        config['DEW_HEATER']['LEVEL_HIGH']             = int(payload['DEW_HEATER__LEVEL_HIGH'])
        config['DEW_HEATER']['THOLD_DIFF_LOW']         = int(payload['DEW_HEATER__THOLD_DIFF_LOW'])
        config['DEW_HEATER']['THOLD_DIFF_MED']         = int(payload['DEW_HEATER__THOLD_DIFF_MED'])
        config['DEW_HEATER']['THOLD_DIFF_HIGH']        = int(payload['DEW_HEATER__THOLD_DIFF_HIGH'])
        config['DEW_HEATER']['HOLD_SECONDS']           = int(payload['DEW_HEATER__HOLD_SECONDS'])
        config['DEW_HEATER']['PWM_FREQUENCY']          = int(payload['DEW_HEATER__PWM_FREQUENCY'])
        config['FAN']['CLASSNAME']                     = str(payload['FAN__CLASSNAME'])
        config['FAN']['I2C_ADDRESS']                   = str(payload['FAN__I2C_ADDRESS'])
        config['FAN']['PIN_1']                         = str(payload['FAN__PIN_1'])
        config['FAN']['INVERT_OUTPUT']                 = bool(payload['FAN__INVERT_OUTPUT'])
        config['FAN']['ENABLE_NIGHT']                  = bool(payload['FAN__ENABLE_NIGHT'])
        config['FAN']['LEVEL_DEF']                     = int(payload['FAN__LEVEL_DEF'])
        config['FAN']['THOLD_ENABLE']                  = bool(payload['FAN__THOLD_ENABLE'])
        config['FAN']['TARGET']                        = float(payload['FAN__TARGET'])
        config['FAN']['TEMP_USER_VAR_SLOT']            = str(payload['FAN__TEMP_USER_VAR_SLOT'])
        config['FAN']['LEVEL_LOW']                     = int(payload['FAN__LEVEL_LOW'])
        config['FAN']['LEVEL_MED']                     = int(payload['FAN__LEVEL_MED'])
        config['FAN']['LEVEL_HIGH']                    = int(payload['FAN__LEVEL_HIGH'])
        config['FAN']['THOLD_DIFF_LOW']                = int(payload['FAN__THOLD_DIFF_LOW'])
        config['FAN']['THOLD_DIFF_MED']                = int(payload['FAN__THOLD_DIFF_MED'])
        config['FAN']['THOLD_DIFF_HIGH']               = int(payload['FAN__THOLD_DIFF_HIGH'])
        config['FAN']['HOLD_SECONDS']                  = int(payload['FAN__HOLD_SECONDS'])
        config['FAN']['PWM_FREQUENCY']                 = int(payload['FAN__PWM_FREQUENCY'])
        config['GENERIC_GPIO']['A_CLASSNAME']          = str(payload['GENERIC_GPIO__A_CLASSNAME'])
        config['GENERIC_GPIO']['A_I2C_ADDRESS']        = str(payload['GENERIC_GPIO__A_I2C_ADDRESS'])
        config['GENERIC_GPIO']['A_PIN_1']              = str(payload['GENERIC_GPIO__A_PIN_1'])
        config['GENERIC_GPIO']['A_INVERT_OUTPUT']      = bool(payload['GENERIC_GPIO__A_INVERT_OUTPUT'])
        config['MANUAL_GPIO']['A_CLASSNAME']           = str(payload['MANUAL_GPIO__A_CLASSNAME'])
        config['MANUAL_GPIO']['A_PIN_1']               = str(payload['MANUAL_GPIO__A_PIN_1'])
        config['MANUAL_GPIO']['A_PIN_2']               = str(payload['MANUAL_GPIO__A_PIN_2'])
        config['MANUAL_GPIO']['A_PIN_3']               = str(payload['MANUAL_GPIO__A_PIN_3'])
        config['DEVICE']['MQTT_TRANSPORT']             = str(payload['DEVICE__MQTT_TRANSPORT'])
        config['DEVICE']['MQTT_PROTOCOL']              = str(payload['DEVICE__MQTT_PROTOCOL'])
        config['DEVICE']['MQTT_HOST']                  = str(payload['DEVICE__MQTT_HOST'])
        config['DEVICE']['MQTT_PORT']                  = int(payload['DEVICE__MQTT_PORT'])
        config['DEVICE']['MQTT_USERNAME']              = str(payload['DEVICE__MQTT_USERNAME'])
        config['DEVICE']['MQTT_PASSWORD']              = str(payload['DEVICE__MQTT_PASSWORD'])
        config['DEVICE']['MQTT_QOS']                   = int(payload['DEVICE__MQTT_QOS'])
        config['DEVICE']['MQTT_TLS']                   = bool(payload['DEVICE__MQTT_TLS'])
        config['DEVICE']['MQTT_CERT_BYPASS']           = bool(payload['DEVICE__MQTT_CERT_BYPASS'])
        config['TEMP_SENSOR']['A_CLASSNAME']           = str(payload['TEMP_SENSOR__A_CLASSNAME'])
        config['TEMP_SENSOR']['A_LABEL']               = str(payload['TEMP_SENSOR__A_LABEL'])
        config['TEMP_SENSOR']['A_PIN_1']               = str(payload['TEMP_SENSOR__A_PIN_1'])
        config['TEMP_SENSOR']['A_PIN_2']               = str(payload['TEMP_SENSOR__A_PIN_2'])
        config['TEMP_SENSOR']['A_USER_VAR_SLOT']       = str(payload['TEMP_SENSOR__A_USER_VAR_SLOT'])
        config['TEMP_SENSOR']['A_I2C_ADDRESS']         = str(payload['TEMP_SENSOR__A_I2C_ADDRESS'])
        config['TEMP_SENSOR']['A_TITLE_TEMPLATE']      = str(payload['TEMP_SENSOR__A_TITLE_TEMPLATE'])
        config['TEMP_SENSOR']['B_CLASSNAME']           = str(payload['TEMP_SENSOR__B_CLASSNAME'])
        config['TEMP_SENSOR']['B_LABEL']               = str(payload['TEMP_SENSOR__B_LABEL'])
        config['TEMP_SENSOR']['B_PIN_1']               = str(payload['TEMP_SENSOR__B_PIN_1'])
        config['TEMP_SENSOR']['B_PIN_2']               = str(payload['TEMP_SENSOR__B_PIN_2'])
        config['TEMP_SENSOR']['B_USER_VAR_SLOT']       = str(payload['TEMP_SENSOR__B_USER_VAR_SLOT'])
        config['TEMP_SENSOR']['B_I2C_ADDRESS']         = str(payload['TEMP_SENSOR__B_I2C_ADDRESS'])
        config['TEMP_SENSOR']['B_TITLE_TEMPLATE']      = str(payload['TEMP_SENSOR__B_TITLE_TEMPLATE'])
        config['TEMP_SENSOR']['C_CLASSNAME']           = str(payload['TEMP_SENSOR__C_CLASSNAME'])
        config['TEMP_SENSOR']['C_LABEL']               = str(payload['TEMP_SENSOR__C_LABEL'])
        config['TEMP_SENSOR']['C_PIN_1']               = str(payload['TEMP_SENSOR__C_PIN_1'])
        config['TEMP_SENSOR']['C_PIN_2']               = str(payload['TEMP_SENSOR__C_PIN_2'])
        config['TEMP_SENSOR']['C_USER_VAR_SLOT']       = str(payload['TEMP_SENSOR__C_USER_VAR_SLOT'])
        config['TEMP_SENSOR']['C_I2C_ADDRESS']         = str(payload['TEMP_SENSOR__C_I2C_ADDRESS'])
        config['TEMP_SENSOR']['C_TITLE_TEMPLATE']      = str(payload['TEMP_SENSOR__C_TITLE_TEMPLATE'])
        config['TEMP_SENSOR']['D_CLASSNAME']           = str(payload['TEMP_SENSOR__D_CLASSNAME'])
        config['TEMP_SENSOR']['D_LABEL']               = str(payload['TEMP_SENSOR__D_LABEL'])
        config['TEMP_SENSOR']['D_PIN_1']               = str(payload['TEMP_SENSOR__D_PIN_1'])
        config['TEMP_SENSOR']['D_PIN_2']               = str(payload['TEMP_SENSOR__D_PIN_2'])
        config['TEMP_SENSOR']['D_USER_VAR_SLOT']       = str(payload['TEMP_SENSOR__D_USER_VAR_SLOT'])
        config['TEMP_SENSOR']['D_I2C_ADDRESS']         = str(payload['TEMP_SENSOR__D_I2C_ADDRESS'])
        config['TEMP_SENSOR']['D_TITLE_TEMPLATE']      = str(payload['TEMP_SENSOR__D_TITLE_TEMPLATE'])
        config['TEMP_SENSOR']['E_CLASSNAME']           = str(payload['TEMP_SENSOR__E_CLASSNAME'])
        config['TEMP_SENSOR']['E_LABEL']               = str(payload['TEMP_SENSOR__E_LABEL'])
        config['TEMP_SENSOR']['E_PIN_1']               = str(payload['TEMP_SENSOR__E_PIN_1'])
        config['TEMP_SENSOR']['E_PIN_2']               = str(payload['TEMP_SENSOR__E_PIN_2'])
        config['TEMP_SENSOR']['E_USER_VAR_SLOT']       = str(payload['TEMP_SENSOR__E_USER_VAR_SLOT'])
        config['TEMP_SENSOR']['E_I2C_ADDRESS']         = str(payload['TEMP_SENSOR__E_I2C_ADDRESS'])
        config['TEMP_SENSOR']['E_TITLE_TEMPLATE']      = str(payload['TEMP_SENSOR__E_TITLE_TEMPLATE'])
        config['TEMP_SENSOR']['F_CLASSNAME']           = str(payload['TEMP_SENSOR__F_CLASSNAME'])
        config['TEMP_SENSOR']['F_LABEL']               = str(payload['TEMP_SENSOR__F_LABEL'])
        config['TEMP_SENSOR']['F_PIN_1']               = str(payload['TEMP_SENSOR__F_PIN_1'])
        config['TEMP_SENSOR']['F_PIN_2']               = str(payload['TEMP_SENSOR__F_PIN_2'])
        config['TEMP_SENSOR']['F_USER_VAR_SLOT']       = str(payload['TEMP_SENSOR__F_USER_VAR_SLOT'])
        config['TEMP_SENSOR']['F_I2C_ADDRESS']         = str(payload['TEMP_SENSOR__F_I2C_ADDRESS'])
        config['TEMP_SENSOR']['F_TITLE_TEMPLATE']      = str(payload['TEMP_SENSOR__F_TITLE_TEMPLATE'])
        config['TEMP_SENSOR']['FC37_ACTIVE_LOW']       = bool(payload['TEMP_SENSOR__FC37_ACTIVE_LOW'])
        config['TEMP_SENSOR']['OPENWEATHERMAP_APIKEY'] = str(payload['TEMP_SENSOR__OPENWEATHERMAP_APIKEY'])
        config['TEMP_SENSOR']['WUNDERGROUND_APIKEY']   = str(payload['TEMP_SENSOR__WUNDERGROUND_APIKEY'])
        config['TEMP_SENSOR']['ASTROSPHERIC_APIKEY']   = str(payload['TEMP_SENSOR__ASTROSPHERIC_APIKEY'])
        config['TEMP_SENSOR']['AMBIENTWEATHER_APIKEY']         = str(payload['TEMP_SENSOR__AMBIENTWEATHER_APIKEY'])
        config['TEMP_SENSOR']['AMBIENTWEATHER_APPLICATIONKEY'] = str(payload['TEMP_SENSOR__AMBIENTWEATHER_APPLICATIONKEY'])
        config['TEMP_SENSOR']['AMBIENTWEATHER_MACADDRESS']     = str(payload['TEMP_SENSOR__AMBIENTWEATHER_MACADDRESS'])
        config['TEMP_SENSOR']['ECOWITT_APIKEY']         = str(payload['TEMP_SENSOR__ECOWITT_APIKEY'])
        config['TEMP_SENSOR']['ECOWITT_APPLICATIONKEY'] = str(payload['TEMP_SENSOR__ECOWITT_APPLICATIONKEY'])
        config['TEMP_SENSOR']['ECOWITT_MACADDRESS']     = str(payload['TEMP_SENSOR__ECOWITT_MACADDRESS'])
        config['TEMP_SENSOR']['MQTT_TRANSPORT']        = str(payload['TEMP_SENSOR__MQTT_TRANSPORT'])
        config['TEMP_SENSOR']['MQTT_PROTOCOL']         = str(payload['TEMP_SENSOR__MQTT_PROTOCOL'])
        config['TEMP_SENSOR']['MQTT_HOST']             = str(payload['TEMP_SENSOR__MQTT_HOST'])
        config['TEMP_SENSOR']['MQTT_PORT']             = int(payload['TEMP_SENSOR__MQTT_PORT'])
        config['TEMP_SENSOR']['MQTT_USERNAME']         = str(payload['TEMP_SENSOR__MQTT_USERNAME'])
        config['TEMP_SENSOR']['MQTT_PASSWORD']         = str(payload['TEMP_SENSOR__MQTT_PASSWORD'])
        config['TEMP_SENSOR']['MQTT_TLS']              = bool(payload['TEMP_SENSOR__MQTT_TLS'])
        config['TEMP_SENSOR']['MQTT_CERT_BYPASS']      = bool(payload['TEMP_SENSOR__MQTT_CERT_BYPASS'])
        config['TEMP_SENSOR']['DHT_USE_PULSEIO']       = bool(payload['TEMP_SENSOR__DHT_USE_PULSEIO'])
        config['TEMP_SENSOR']['SHT3X_HEATER_NIGHT']    = bool(payload['TEMP_SENSOR__SHT3X_HEATER_NIGHT'])
        config['TEMP_SENSOR']['SHT3X_HEATER_DAY']      = bool(payload['TEMP_SENSOR__SHT3X_HEATER_DAY'])
        config['TEMP_SENSOR']['SHT4X_MODE_NIGHT']      = str(payload['TEMP_SENSOR__SHT4X_MODE_NIGHT'])
        config['TEMP_SENSOR']['SHT4X_MODE_DAY']        = str(payload['TEMP_SENSOR__SHT4X_MODE_DAY'])
        config['TEMP_SENSOR']['SI7021_HEATER_LEVEL_NIGHT'] = int(payload['TEMP_SENSOR__SI7021_HEATER_LEVEL_NIGHT'])
        config['TEMP_SENSOR']['SI7021_HEATER_LEVEL_DAY'] = int(payload['TEMP_SENSOR__SI7021_HEATER_LEVEL_DAY'])
        config['TEMP_SENSOR']['HTU31D_HEATER_NIGHT']   = bool(payload['TEMP_SENSOR__HTU31D_HEATER_NIGHT'])
        config['TEMP_SENSOR']['HTU31D_HEATER_DAY']     = bool(payload['TEMP_SENSOR__HTU31D_HEATER_DAY'])
        config['TEMP_SENSOR']['HDC302X_HEATER_NIGHT']  = str(payload['TEMP_SENSOR__HDC302X_HEATER_NIGHT'])
        config['TEMP_SENSOR']['HDC302X_HEATER_DAY']    = str(payload['TEMP_SENSOR__HDC302X_HEATER_DAY'])
        config['TEMP_SENSOR']['TSL2561_GAIN_NIGHT']    = int(payload['TEMP_SENSOR__TSL2561_GAIN_NIGHT'])
        config['TEMP_SENSOR']['TSL2561_GAIN_DAY']      = int(payload['TEMP_SENSOR__TSL2561_GAIN_DAY'])
        config['TEMP_SENSOR']['TSL2561_INT_NIGHT']     = int(payload['TEMP_SENSOR__TSL2561_INT_NIGHT'])
        config['TEMP_SENSOR']['TSL2561_INT_DAY']       = int(payload['TEMP_SENSOR__TSL2561_INT_DAY'])
        config['TEMP_SENSOR']['TSL2561_DISABLE_DAY']   = bool(payload['TEMP_SENSOR__TSL2561_DISABLE_DAY'])
        config['TEMP_SENSOR']['TSL2591_GAIN_NIGHT']    = str(payload['TEMP_SENSOR__TSL2591_GAIN_NIGHT'])
        config['TEMP_SENSOR']['TSL2591_GAIN_DAY']      = str(payload['TEMP_SENSOR__TSL2591_GAIN_DAY'])
        config['TEMP_SENSOR']['TSL2591_INT_NIGHT']     = str(payload['TEMP_SENSOR__TSL2591_INT_NIGHT'])
        config['TEMP_SENSOR']['TSL2591_INT_DAY']       = str(payload['TEMP_SENSOR__TSL2591_INT_DAY'])
        config['TEMP_SENSOR']['TSL2591_DISABLE_DAY']   = bool(payload['TEMP_SENSOR__TSL2591_DISABLE_DAY'])
        config['TEMP_SENSOR']['VEML7700_GAIN_NIGHT']   = str(payload['TEMP_SENSOR__VEML7700_GAIN_NIGHT'])
        config['TEMP_SENSOR']['VEML7700_GAIN_DAY']     = str(payload['TEMP_SENSOR__VEML7700_GAIN_DAY'])
        config['TEMP_SENSOR']['VEML7700_INT_NIGHT']    = str(payload['TEMP_SENSOR__VEML7700_INT_NIGHT'])
        config['TEMP_SENSOR']['VEML7700_INT_DAY']      = str(payload['TEMP_SENSOR__VEML7700_INT_DAY'])
        config['TEMP_SENSOR']['SI1145_VIS_GAIN_NIGHT'] = str(payload['TEMP_SENSOR__SI1145_VIS_GAIN_NIGHT'])
        config['TEMP_SENSOR']['SI1145_VIS_GAIN_DAY']   = str(payload['TEMP_SENSOR__SI1145_VIS_GAIN_DAY'])
        config['TEMP_SENSOR']['SI1145_IR_GAIN_NIGHT']  = str(payload['TEMP_SENSOR__SI1145_IR_GAIN_NIGHT'])
        config['TEMP_SENSOR']['SI1145_IR_GAIN_DAY']    = str(payload['TEMP_SENSOR__SI1145_IR_GAIN_DAY'])
        config['TEMP_SENSOR']['LTR390_GAIN_NIGHT']     = str(payload['TEMP_SENSOR__LTR390_GAIN_NIGHT'])
        config['TEMP_SENSOR']['LTR390_GAIN_DAY']       = str(payload['TEMP_SENSOR__LTR390_GAIN_DAY'])
        config['TEMP_SENSOR']['INA3221_CH1_ENABLE']    = bool(payload['TEMP_SENSOR__INA3221_CH1_ENABLE'])
        config['TEMP_SENSOR']['INA3221_CH2_ENABLE']    = bool(payload['TEMP_SENSOR__INA3221_CH2_ENABLE'])
        config['TEMP_SENSOR']['INA3221_CH3_ENABLE']    = bool(payload['TEMP_SENSOR__INA3221_CH3_ENABLE'])
        config['TEMP_SENSOR']['AS3935_OUTDOOR_MODE']   = bool(payload['TEMP_SENSOR__AS3935_OUTDOOR_MODE'])
        config['TEMP_SENSOR']['AS3935_MASK_DISTURBER'] = bool(payload['TEMP_SENSOR__AS3935_MASK_DISTURBER'])
        config['TEMP_SENSOR']['AS3935_NOISE_LEVEL']    = int(payload['TEMP_SENSOR__AS3935_NOISE_LEVEL'])
        config['TEMP_SENSOR']['AS3935_SPIKE_REJECTION'] = int(payload['TEMP_SENSOR__AS3935_SPIKE_REJECTION'])
        config['TEMP_SENSOR']['LUX_MAGNITUDE_OFFSET']  = float(payload['TEMP_SENSOR__LUX_MAGNITUDE_OFFSET'])
        config['CHARTS']['CUSTOM_SLOT_1']              = str(payload['CHARTS__CUSTOM_SLOT_1'])
        config['CHARTS']['CUSTOM_SLOT_1_MIN']          = float(payload['CHARTS__CUSTOM_SLOT_1_MIN'])
        config['CHARTS']['CUSTOM_SLOT_2']              = str(payload['CHARTS__CUSTOM_SLOT_2'])
        config['CHARTS']['CUSTOM_SLOT_2_MIN']          = float(payload['CHARTS__CUSTOM_SLOT_2_MIN'])
        config['CHARTS']['CUSTOM_SLOT_3']              = str(payload['CHARTS__CUSTOM_SLOT_3'])
        config['CHARTS']['CUSTOM_SLOT_3_MIN']          = float(payload['CHARTS__CUSTOM_SLOT_3_MIN'])
        config['CHARTS']['CUSTOM_SLOT_4']              = str(payload['CHARTS__CUSTOM_SLOT_4'])
        config['CHARTS']['CUSTOM_SLOT_4_MIN']          = float(payload['CHARTS__CUSTOM_SLOT_4_MIN'])
        config['CHARTS']['CUSTOM_SLOT_5']              = str(payload['CHARTS__CUSTOM_SLOT_5'])
        config['CHARTS']['CUSTOM_SLOT_5_MIN']          = float(payload['CHARTS__CUSTOM_SLOT_5_MIN'])
        config['CHARTS']['CUSTOM_SLOT_6']              = str(payload['CHARTS__CUSTOM_SLOT_6'])
        config['CHARTS']['CUSTOM_SLOT_6_MIN']          = float(payload['CHARTS__CUSTOM_SLOT_6_MIN'])
        config['CHARTS']['CUSTOM_SLOT_7']              = str(payload['CHARTS__CUSTOM_SLOT_7'])
        config['CHARTS']['CUSTOM_SLOT_7_MIN']          = float(payload['CHARTS__CUSTOM_SLOT_7_MIN'])
        config['CHARTS']['CUSTOM_SLOT_8']              = str(payload['CHARTS__CUSTOM_SLOT_8'])
        config['CHARTS']['CUSTOM_SLOT_8_MIN']          = float(payload['CHARTS__CUSTOM_SLOT_8_MIN'])
        config['CHARTS']['CUSTOM_SLOT_9']              = str(payload['CHARTS__CUSTOM_SLOT_9'])
        config['CHARTS']['CUSTOM_SLOT_9_MIN']          = float(payload['CHARTS__CUSTOM_SLOT_9_MIN'])
        config['ADSB']['ENABLE']                       = bool(payload['ADSB__ENABLE'])
        config['ADSB']['DUMP1090_URL']                 = str(payload['ADSB__DUMP1090_URL'])
        config['ADSB']['USERNAME']                     = str(payload['ADSB__USERNAME'])
        config['ADSB']['PASSWORD']                     = str(payload['ADSB__PASSWORD'])
        config['ADSB']['CERT_BYPASS']                  = bool(payload['ADSB__CERT_BYPASS'])
        config['ADSB']['ALT_DEG_MIN']                  = float(payload['ADSB__ALT_DEG_MIN'])
        config['ADSB']['LABEL_ENABLE']                 = bool(payload['ADSB__LABEL_ENABLE'])
        config['ADSB']['LABEL_LIMIT']                  = int(payload['ADSB__LABEL_LIMIT'])
        config['ADSB']['AIRCRAFT_LABEL_TEMPLATE']      = str(payload['ADSB__AIRCRAFT_LABEL_TEMPLATE'])
        config['ADSB']['IMAGE_LABEL_TEMPLATE_PREFIX']  = str(payload['ADSB__IMAGE_LABEL_TEMPLATE_PREFIX'])
        config['SATELLITE_TRACK']['ENABLE']            = bool(payload['SATELLITE_TRACK__ENABLE'])
        config['SATELLITE_TRACK']['DAYTIME_TRACK']     = bool(payload['SATELLITE_TRACK__DAYTIME_TRACK'])
        config['SATELLITE_TRACK']['ALT_DEG_MIN']       = float(payload['SATELLITE_TRACK__ALT_DEG_MIN'])
        config['SATELLITE_TRACK']['LABEL_ENABLE']      = bool(payload['SATELLITE_TRACK__LABEL_ENABLE'])
        config['SATELLITE_TRACK']['LABEL_LIMIT']       = int(payload['SATELLITE_TRACK__LABEL_LIMIT'])
        config['SATELLITE_TRACK']['SAT_LABEL_TEMPLATE'] = str(payload['SATELLITE_TRACK__SAT_LABEL_TEMPLATE'])
        config['SATELLITE_TRACK']['IMAGE_LABEL_TEMPLATE_PREFIX']  = str(payload['SATELLITE_TRACK__IMAGE_LABEL_TEMPLATE_PREFIX'])

        config['FILETRANSFER']['LIBCURL_OPTIONS']      = json.loads(str(payload['FILETRANSFER__LIBCURL_OPTIONS']))
        config['INDI_CONFIG_DEFAULTS']                 = json.loads(str(payload['INDI_CONFIG_DEFAULTS']))
        config['INDI_CONFIG_DAY']                      = json.loads(str(payload['INDI_CONFIG_DAY']))
        config['ENCRYPT_PASSWORDS']                    = bool(payload['ENCRYPT_PASSWORDS'])


        ### never disable
        #config['THUMBNAILS']['IMAGES_AUTO']            = True


        ### Not a config option
        reload_on_save                                                  = bool(payload['RELOAD_ON_SAVE'])
        config_note                                                     = str(payload['CONFIG_NOTE'])


        # ADU_ROI
        adu_roi_x1 = int(payload['ADU_ROI_X1'])
        adu_roi_y1 = int(payload['ADU_ROI_Y1'])
        adu_roi_x2 = int(payload['ADU_ROI_X2'])
        adu_roi_y2 = int(payload['ADU_ROI_Y2'])

        # the x2 and y2 values must be positive integers in order to be enabled and valid
        if adu_roi_x2 and adu_roi_y2:
            config['ADU_ROI'] = [adu_roi_x1, adu_roi_y1, adu_roi_x2, adu_roi_y2]
        else:
            config['ADU_ROI'] = []


        # SQM_ROI
        sqm_roi_x1 = int(payload['SQM_ROI_X1'])
        sqm_roi_y1 = int(payload['SQM_ROI_Y1'])
        sqm_roi_x2 = int(payload['SQM_ROI_X2'])
        sqm_roi_y2 = int(payload['SQM_ROI_Y2'])

        # the x2 and y2 values must be positive integers in order to be enabled and valid
        if sqm_roi_x2 and sqm_roi_y2:
            config['SQM_ROI'] = [sqm_roi_x1, sqm_roi_y1, sqm_roi_x2, sqm_roi_y2]
        else:
            config['SQM_ROI'] = []


        # IMAGE_CROP_ROI
        image_crop_roi_x1 = int(payload['IMAGE_CROP_ROI_X1'])
        image_crop_roi_y1 = int(payload['IMAGE_CROP_ROI_Y1'])
        image_crop_roi_x2 = int(payload['IMAGE_CROP_ROI_X2'])
        image_crop_roi_y2 = int(payload['IMAGE_CROP_ROI_Y2'])

        # the x2 and y2 values must be positive integers in order to be enabled and valid
        if image_crop_roi_x2 and image_crop_roi_y2:
            config['IMAGE_CROP_ROI'] = [image_crop_roi_x1, image_crop_roi_y1, image_crop_roi_x2, image_crop_roi_y2]
        else:
            config['IMAGE_CROP_ROI'] = []



        # TEXT_PROPERTIES FONT_COLOR
        font_color_str = str(payload['TEXT_PROPERTIES__FONT_COLOR'])
        config['TEXT_PROPERTIES']['FONT_COLOR'] = [int(x) for x in font_color_str.split(',')]

        # CARDINAL_DIRS FONT_COLOR
        cardinal_dirs_color_str = str(payload['CARDINAL_DIRS__FONT_COLOR'])
        config['CARDINAL_DIRS']['FONT_COLOR'] = [int(x) for x in cardinal_dirs_color_str.split(',')]

        # ORB_PROPERTIES SUN_COLOR
        sun_color_str = str(payload['ORB_PROPERTIES__SUN_COLOR'])
        config['ORB_PROPERTIES']['SUN_COLOR'] = [int(x) for x in sun_color_str.split(',')]

        # ORB_PROPERTIES MOON_COLOR
        moon_color_str = str(payload['ORB_PROPERTIES__MOON_COLOR'])
        config['ORB_PROPERTIES']['MOON_COLOR'] = [int(x) for x in moon_color_str.split(',')]

        # IMAGE_BORDER COLOR
        image_border__color_str = str(payload['IMAGE_BORDER__COLOR'])
        config['IMAGE_BORDER']['COLOR'] = [int(x) for x in image_border__color_str.split(',')]

        # LIGHTGRAPH COLORS
        lightgraph_overlay__day_color_str = str(payload['LIGHTGRAPH_OVERLAY__DAY_COLOR'])
        config['LIGHTGRAPH_OVERLAY']['DAY_COLOR'] = [int(x) for x in lightgraph_overlay__day_color_str.split(',')]

        lightgraph_overlay__dusk_color_str = str(payload['LIGHTGRAPH_OVERLAY__DUSK_COLOR'])
        config['LIGHTGRAPH_OVERLAY']['DUSK_COLOR'] = [int(x) for x in lightgraph_overlay__dusk_color_str.split(',')]

        lightgraph_overlay__night_color_str = str(payload['LIGHTGRAPH_OVERLAY__NIGHT_COLOR'])
        config['LIGHTGRAPH_OVERLAY']['NIGHT_COLOR'] = [int(x) for x in lightgraph_overlay__night_color_str.split(',')]

        lightgraph_overlay__moonmode_color_str = str(payload['LIGHTGRAPH_OVERLAY__MOONMODE_COLOR'])
        config['LIGHTGRAPH_OVERLAY']['MOONMODE_COLOR'] = [int(x) for x in lightgraph_overlay__moonmode_color_str.split(',')]

        lightgraph_overlay__hour_color_str = str(payload['LIGHTGRAPH_OVERLAY__HOUR_COLOR'])
        config['LIGHTGRAPH_OVERLAY']['HOUR_COLOR'] = [int(x) for x in lightgraph_overlay__hour_color_str.split(',')]

        lightgraph_overlay__border_color_str = str(payload['LIGHTGRAPH_OVERLAY__BORDER_COLOR'])
        config['LIGHTGRAPH_OVERLAY']['BORDER_COLOR'] = [int(x) for x in lightgraph_overlay__border_color_str.split(',')]

        lightgraph_overlay__now_color_str = str(payload['LIGHTGRAPH_OVERLAY__NOW_COLOR'])
        config['LIGHTGRAPH_OVERLAY']['NOW_COLOR'] = [int(x) for x in lightgraph_overlay__now_color_str.split(',')]

        lightgraph_overlay__font_color_str = str(payload['LIGHTGRAPH_OVERLAY__FONT_COLOR'])
        config['LIGHTGRAPH_OVERLAY']['FONT_COLOR'] = [int(x) for x in lightgraph_overlay__font_color_str.split(',')]


        # Youtube tags
        youtube__tags_str = str(payload['YOUTUBE__TAGS_STR'])
        tags_set = set()
        for tag in youtube__tags_str.split(','):
            tag_s = tag.strip()

            if tag_s:
                tags_set.add(tag_s)

        config['YOUTUBE']['TAGS'] = list(tags_set)

        return ModernAdminFullConfigParseResult(config, reload_on_save, config_note)
