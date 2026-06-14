from copy import deepcopy
from dataclasses import asdict
from dataclasses import dataclass
from typing import Any
from typing import Dict
from typing import List
from typing import Mapping


@dataclass(frozen=True)
class CaptureProfile:
    """Normalized read-only description of one camera capture target.

    This is intentionally a passive data object for the first multi-camera
    refactor step. Runtime workers still use the legacy flat config directly.
    """

    profile_id: str
    enabled: bool
    primary: bool
    camera_interface: str
    indi_server: str
    indi_port: int
    indi_camera_name: str
    libcamera_camera_id: int
    ccd_config: Dict[str, Any]
    exposure_min: float
    exposure_min_day: float
    exposure_max: float
    exposure_default: float
    exposure_timeout: float
    exposure_period: float
    exposure_period_day: float
    gain_night: float
    gain_moonmode: float
    gain_day: float
    binning_night: int
    binning_moonmode: int
    binning_day: int
    cooling_enabled: bool
    cooling_enabled_day: bool
    target_temperature: float
    target_temperature_day: float
    libcamera_image_file_type: str
    libcamera_image_file_type_day: str
    libcamera_immediate: bool
    libcamera_immediate_day: bool
    libcamera_awb: str
    libcamera_awb_day: str
    libcamera_awb_enable: bool
    libcamera_awb_enable_day: bool
    libcamera_ccm_disable: bool
    libcamera_ccm_disable_day: bool
    libcamera_extra_options: str
    libcamera_extra_options_day: str
    camera_sqm: Dict[str, Any]
    focus_mode: bool
    focus_delay: float
    daytime_capture: bool
    daytime_capture_save: bool
    daytime_timelapse: bool
    cfa_pattern: str
    ccd_bit_depth: int

    def as_dict(self) -> Dict[str, Any]:
        return asdict(self)


def _float_config(config: Mapping[str, Any], key: str, default: float) -> float:
    try:
        return float(config.get(key, default))
    except (TypeError, ValueError):
        return default


def _int_config(config: Mapping[str, Any], key: str, default: int) -> int:
    try:
        return int(config.get(key, default))
    except (TypeError, ValueError):
        return default


def _bool_config(config: Mapping[str, Any], key: str, default: bool) -> bool:
    return bool(config.get(key, default))


def _mapping_float(config: Mapping[str, Any], key: str, default: float) -> float:
    try:
        return float(config.get(key, default))
    except (TypeError, ValueError):
        return default


def _mapping_int(config: Mapping[str, Any], key: str, default: int) -> int:
    try:
        return int(config.get(key, default))
    except (TypeError, ValueError):
        return default


def derive_capture_profiles(config: Mapping[str, Any]) -> List[CaptureProfile]:
    """Derive capture profiles from the current single-camera config.

    The first version deliberately returns exactly one default profile. It does
    not mutate the config and does not enable multi-camera runtime behavior.
    """

    ccd_config = deepcopy(config.get('CCD_CONFIG') or {})
    libcamera_config = config.get('LIBCAMERA') or {}
    camera_sqm = deepcopy(config.get('CAMERA_SQM') or {})

    ccd_night = ccd_config.get('NIGHT') or {}
    ccd_moonmode = ccd_config.get('MOONMODE') or {}
    ccd_day = ccd_config.get('DAY') or {}

    try:
        indi_port = int(config.get('INDI_PORT', 7624))
    except (TypeError, ValueError):
        indi_port = 7624

    try:
        libcamera_camera_id = int(libcamera_config.get('CAMERA_ID', 0))
    except (TypeError, ValueError):
        libcamera_camera_id = 0

    return [
        CaptureProfile(
            profile_id='default',
            enabled=True,
            primary=True,
            camera_interface=str(config.get('CAMERA_INTERFACE', 'indi') or 'indi'),
            indi_server=str(config.get('INDI_SERVER', 'localhost') or 'localhost'),
            indi_port=indi_port,
            indi_camera_name=str(config.get('INDI_CAMERA_NAME', '') or ''),
            libcamera_camera_id=libcamera_camera_id,
            # MULTI_CAMERA_PREP: mirror per-camera tuning from the legacy
            # global config without changing runtime behavior yet.
            ccd_config=ccd_config,
            exposure_min=_float_config(config, 'CCD_EXPOSURE_MIN', 0.0),
            exposure_min_day=_float_config(config, 'CCD_EXPOSURE_MIN_DAY', 0.0),
            exposure_max=_float_config(config, 'CCD_EXPOSURE_MAX', 15.0),
            exposure_default=_float_config(config, 'CCD_EXPOSURE_DEF', 0.0),
            exposure_timeout=_float_config(config, 'CCD_EXPOSURE_TIMEOUT', 330.0),
            exposure_period=_float_config(config, 'EXPOSURE_PERIOD', 15.0),
            exposure_period_day=_float_config(config, 'EXPOSURE_PERIOD_DAY', 15.0),
            gain_night=_mapping_float(ccd_night, 'GAIN', 100.0),
            gain_moonmode=_mapping_float(ccd_moonmode, 'GAIN', 75.0),
            gain_day=_mapping_float(ccd_day, 'GAIN', 0.0),
            binning_night=_mapping_int(ccd_night, 'BINNING', 1),
            binning_moonmode=_mapping_int(ccd_moonmode, 'BINNING', 1),
            binning_day=_mapping_int(ccd_day, 'BINNING', 1),
            cooling_enabled=_bool_config(config, 'CCD_COOLING', False),
            cooling_enabled_day=_bool_config(config, 'CCD_COOLING_DAY', False),
            target_temperature=_float_config(config, 'CCD_TEMP', 15.0),
            target_temperature_day=_float_config(config, 'CCD_TEMP_DAY', 35.0),
            libcamera_image_file_type=str(libcamera_config.get('IMAGE_FILE_TYPE', 'jpg') or 'jpg'),
            libcamera_image_file_type_day=str(libcamera_config.get('IMAGE_FILE_TYPE_DAY', 'jpg') or 'jpg'),
            libcamera_immediate=bool(libcamera_config.get('IMMEDIATE', True)),
            libcamera_immediate_day=bool(libcamera_config.get('IMMEDIATE_DAY', True)),
            libcamera_awb=str(libcamera_config.get('AWB', 'auto') or 'auto'),
            libcamera_awb_day=str(libcamera_config.get('AWB_DAY', 'auto') or 'auto'),
            libcamera_awb_enable=bool(libcamera_config.get('AWB_ENABLE', True)),
            libcamera_awb_enable_day=bool(libcamera_config.get('AWB_ENABLE_DAY', True)),
            libcamera_ccm_disable=bool(libcamera_config.get('CCM_DISABLE', False)),
            libcamera_ccm_disable_day=bool(libcamera_config.get('CCM_DISABLE_DAY', False)),
            libcamera_extra_options=str(libcamera_config.get('EXTRA_OPTIONS', '') or ''),
            libcamera_extra_options_day=str(libcamera_config.get('EXTRA_OPTIONS_DAY', '') or ''),
            camera_sqm=camera_sqm,
            focus_mode=_bool_config(config, 'FOCUS_MODE', False),
            focus_delay=_float_config(config, 'FOCUS_DELAY', 4.0),
            daytime_capture=_bool_config(config, 'DAYTIME_CAPTURE', True),
            daytime_capture_save=_bool_config(config, 'DAYTIME_CAPTURE_SAVE', True),
            daytime_timelapse=_bool_config(config, 'DAYTIME_TIMELAPSE', True),
            cfa_pattern=str(config.get('CFA_PATTERN', '') or ''),
            ccd_bit_depth=_int_config(config, 'CCD_BIT_DEPTH', 0),
        ),
    ]
