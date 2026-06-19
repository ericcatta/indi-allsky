from copy import deepcopy
from dataclasses import asdict
from dataclasses import dataclass
from typing import Any
from typing import Dict
from typing import List
from typing import Mapping
from typing import Optional

from .auto_meter import AUTO_EXPOSURE_METERING_MODES
from .auto_meter import DEFAULT_AUTO_EXPOSURE_METERING_MODE


LIBCAMERA_AWB_MODES = {
    'auto',
    'fixed',
    'daylight',
    'cloudy',
    'tungsten',
    'fluorescent',
    'indoor',
}

PROCESSING_MODES = {
    'classic',
    'hybrid',
}

HYBRID_AWB_APPLY_MODES = {
    'auto',
    'capture_driver',
    'postprocess_rgb',
    'disabled',
}


@dataclass(frozen=True)
class CaptureProfile:
    """Normalized read-only description of one camera capture target.

    This is intentionally a passive data object for the first multi-camera
    refactor step. Runtime workers still use the legacy flat config directly.
    """

    profile_id: str
    enabled: bool
    primary: bool
    processing_mode: str
    hybrid_awb_apply_mode: str
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
    auto_exposure_metering_mode: str
    target_adu: int
    target_adu_day: int
    target_adu_dev: int
    target_adu_dev_day: int
    gain_default: float
    gain_min: float
    gain_max: float
    gain_night: float
    gain_moonmode: float
    gain_day: float
    auto_gain_enable: bool
    auto_gain_day: bool
    auto_gain_night: bool
    auto_gain_moonmode: bool
    auto_gain_levels: int
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
    libcamera_awb_mode_configured: bool
    libcamera_awb_mode: str
    libcamera_awb_red_gain: float
    libcamera_awb_blue_gain: float
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
    outputs: Dict[str, Any]

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


def _libcamera_awb_mode(config: Mapping[str, Any]) -> str:
    awb_mode = str(config.get('AWB_MODE', config.get('awb_mode', '')) or '').strip().lower()
    if not awb_mode:
        if bool(config.get('AWB_ENABLE', True)):
            awb_mode = str(config.get('AWB', 'auto') or 'auto').strip().lower()
        else:
            awb_mode = 'fixed'

    if awb_mode not in LIBCAMERA_AWB_MODES:
        return 'auto'

    return awb_mode


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


def _default_outputs(config: Mapping[str, Any]) -> Dict[str, bool]:
    fish2pano_config = config.get('FISH2PANO') or {}

    return {
        'images': True,
        'timelapse': bool(config.get('TIMELAPSE_ENABLE', True)),
        'mini_timelapse': bool(config.get('TIMELAPSE_ENABLE', True)),
        'keogram': bool(config.get('TIMELAPSE_ENABLE', True)),
        'realtime_keogram': True,
        'longterm_keogram': True,
        'startrails': bool(config.get('TIMELAPSE_ENABLE', True)),
        'panorama': bool(fish2pano_config.get('ENABLE', False)),
        'panorama_loop': bool(fish2pano_config.get('ENABLE', False)),
        'extra_uploads': True,
    }


def _coerce_outputs(config: Mapping[str, Any], raw_outputs: Optional[Mapping[str, Any]]) -> Dict[str, bool]:
    outputs = _default_outputs(config)

    if raw_outputs:
        for key, value in raw_outputs.items():
            outputs[str(key)] = bool(value)

    return outputs


def _deep_update(base_config: Dict[str, Any], override_config: Mapping[str, Any]) -> Dict[str, Any]:
    for key, value in override_config.items():
        if isinstance(value, Mapping) and isinstance(base_config.get(key), dict):
            _deep_update(base_config[key], value)
        else:
            base_config[key] = deepcopy(value)

    return base_config


def _mapping_config(config: Mapping[str, Any], key: str) -> Mapping[str, Any]:
    value = config.get(key) or {}
    if isinstance(value, Mapping):
        return value

    return {}


def _known_profile_gain_defaults(profile_id: str, camera_interface: str, indi_camera_name: str = '') -> Dict[str, float]:
    profile_id_l = str(profile_id or '').strip().lower()
    camera_interface_l = str(camera_interface or '').strip().lower()
    indi_camera_name_l = str(indi_camera_name or '').strip().lower()

    if 'imx708' in profile_id_l or 'imx708' in camera_interface_l:
        return {
            'night': 16.0,
            'moonmode': 16.0,
            'day': 1.13,
        }
    elif 'asi678' in profile_id_l or 'asi678' in indi_camera_name_l:
        return {
            'night': 220.0,
            'moonmode': 75.0,
            'day': 0.0,
        }

    return {}


def _processing_mode(profile_config: Mapping[str, Any]) -> str:
    awb_config = _mapping_config(profile_config, 'awb')
    processing_mode = str(profile_config.get('processing_mode', awb_config.get('mode', 'classic')) or 'classic').strip().lower()
    if processing_mode not in PROCESSING_MODES:
        return 'classic'

    return processing_mode


def _hybrid_awb_apply_mode(
    profile_config: Mapping[str, Any],
    *,
    profile_id: str = '',
    camera_interface: str = '',
    indi_camera_name: str = '',
) -> str:
    apply_mode_candidates = (
        ('awb', 'apply_mode'),
        ('hybrid', 'awb', 'apply_mode'),
        ('HYBRID', 'AWB', 'APPLY_MODE'),
        ('HYBRID', 'awb', 'apply_mode'),
        ('hybrid', 'AWB', 'APPLY_MODE'),
        ('hybrid_awb_apply_mode',),
    )
    for path in apply_mode_candidates:
        current = profile_config
        for key in path:
            if not isinstance(current, Mapping) or key not in current:
                current = None
                break

            current = current[key]

        if current is None:
            continue

        apply_mode = str(current or 'auto').strip().lower()
        if apply_mode in HYBRID_AWB_APPLY_MODES:
            return apply_mode

    if _processing_mode(profile_config) == 'hybrid' and _known_profile_gain_defaults(profile_id, camera_interface, indi_camera_name):
        return 'postprocess_rgb'

    return 'auto'


def _auto_exposure_metering_mode(config: Mapping[str, Any], profile_config: Mapping[str, Any]) -> str:
    auto_exposure_config = _mapping_config(profile_config, 'auto_exposure')
    configured_mode = auto_exposure_config.get(
        'metering_mode',
        profile_config.get(
            'AUTO_EXPOSURE_METERING_MODE',
            profile_config.get(
                'auto_exposure_metering_mode',
                config.get('AUTO_EXPOSURE_METERING_MODE', DEFAULT_AUTO_EXPOSURE_METERING_MODE),
            ),
        ),
    )
    mode = str(configured_mode or DEFAULT_AUTO_EXPOSURE_METERING_MODE).strip().lower()
    if mode in AUTO_EXPOSURE_METERING_MODES:
        return mode

    return DEFAULT_AUTO_EXPOSURE_METERING_MODE


def _profile_from_config(
    config: Mapping[str, Any],
    profile_config: Optional[Mapping[str, Any]] = None,
    *,
    default_profile_id: str = 'default',
    default_enabled: bool = True,
    default_primary: bool = True,
) -> CaptureProfile:
    profile_config = profile_config or {}
    profile_id = str(profile_config.get('profile_id', default_profile_id) or default_profile_id)
    camera_interface = profile_config.get('camera_interface', config.get('CAMERA_INTERFACE', 'indi'))
    indi_config = profile_config.get('indi') or {}
    indi_camera_name = str(indi_config.get('camera_name', profile_config.get('indi_camera_name', config.get('INDI_CAMERA_NAME', ''))) or '')
    known_gain_defaults = _known_profile_gain_defaults(profile_id, camera_interface, indi_camera_name)
    exposure_config = _mapping_config(profile_config, 'exposure')
    gain_config = _mapping_config(profile_config, 'gain')
    target_adu_config = _mapping_config(profile_config, 'target_adu')
    awb_config = _mapping_config(profile_config, 'awb')

    ccd_config = deepcopy(config.get('CCD_CONFIG') or {})
    profile_ccd_config = profile_config.get('ccd_config') or {}
    if isinstance(profile_ccd_config, Mapping):
        _deep_update(ccd_config, profile_ccd_config)

    ccd_config.setdefault('NIGHT', {})
    ccd_config.setdefault('MOONMODE', {})
    ccd_config.setdefault('DAY', {})

    # Existing DB profiles may already contain a legacy ccd_config copied from
    # the global defaults. In multicamera mode, known camera profiles need safe
    # per-camera gain defaults unless the new gain block or legacy top-level
    # gain aliases explicitly override them.
    if not gain_config:
        if 'night' in known_gain_defaults and 'gain_night' not in profile_config and 'gain_max' not in profile_config:
            ccd_config['NIGHT']['GAIN'] = known_gain_defaults['night']
        if 'moonmode' in known_gain_defaults and 'gain_moonmode' not in profile_config:
            ccd_config['MOONMODE']['GAIN'] = known_gain_defaults['moonmode']
        if 'day' in known_gain_defaults and 'gain_day' not in profile_config and 'gain_min' not in profile_config:
            ccd_config['DAY']['GAIN'] = known_gain_defaults['day']

    if 'night' in gain_config:
        ccd_config['NIGHT']['GAIN'] = deepcopy(gain_config['night'])
    if 'moonmode' in gain_config:
        ccd_config['MOONMODE']['GAIN'] = deepcopy(gain_config['moonmode'])
    if 'day' in gain_config:
        ccd_config['DAY']['GAIN'] = deepcopy(gain_config['day'])
    if 'auto' in gain_config:
        ccd_config['AUTO_GAIN_ENABLE'] = deepcopy(gain_config['auto'])
    if 'auto_day' in gain_config:
        ccd_config['AUTO_GAIN_ENABLE_DAY'] = deepcopy(gain_config['auto_day'])
    if 'auto_night' in gain_config:
        ccd_config['AUTO_GAIN_ENABLE_NIGHT'] = deepcopy(gain_config['auto_night'])
    if 'auto_moonmode' in gain_config:
        ccd_config['AUTO_GAIN_ENABLE_MOONMODE'] = deepcopy(gain_config['auto_moonmode'])
    if 'auto_levels' in gain_config:
        ccd_config['AUTO_GAIN_LEVELS'] = deepcopy(gain_config['auto_levels'])
    libcamera_config = deepcopy(config.get('LIBCAMERA') or {})
    libcamera_config.update(profile_config.get('libcamera') or {})
    if 'libcamera_awb' in awb_config:
        libcamera_config['AWB'] = awb_config['libcamera_awb']
    if 'libcamera_awb_day' in awb_config:
        libcamera_config['AWB_DAY'] = awb_config['libcamera_awb_day']
    if 'libcamera_awb_enable' in awb_config:
        libcamera_config['AWB_ENABLE'] = awb_config['libcamera_awb_enable']
    if 'libcamera_awb_enable_day' in awb_config:
        libcamera_config['AWB_ENABLE_DAY'] = awb_config['libcamera_awb_enable_day']
    if 'libcamera_awb_mode' in awb_config:
        libcamera_config['AWB_MODE'] = awb_config['libcamera_awb_mode']
    if 'red_gain' in awb_config:
        libcamera_config['AWB_RED_GAIN'] = awb_config['red_gain']
    if 'blue_gain' in awb_config:
        libcamera_config['AWB_BLUE_GAIN'] = awb_config['blue_gain']
    camera_sqm = deepcopy(config.get('CAMERA_SQM') or {})
    profile_camera_sqm = profile_config.get('camera_sqm') or {}
    if isinstance(profile_camera_sqm, Mapping):
        _deep_update(camera_sqm, profile_camera_sqm)
    if 'sqm' in gain_config:
        camera_sqm['GAIN'] = deepcopy(gain_config['sqm'])

    ccd_night = ccd_config.get('NIGHT') or {}
    ccd_moonmode = ccd_config.get('MOONMODE') or {}
    ccd_day = ccd_config.get('DAY') or {}

    try:
        indi_port = int(indi_config.get('port', profile_config.get('indi_port', config.get('INDI_PORT', 7624))))
    except (TypeError, ValueError):
        indi_port = 7624

    try:
        libcamera_camera_id = int(
            libcamera_config.get(
                'camera_id',
                libcamera_config.get('CAMERA_ID', profile_config.get('camera_id_hint', 0)),
            )
        )
    except (TypeError, ValueError):
        libcamera_camera_id = 0

    outputs = _coerce_outputs(config, profile_config.get('outputs'))

    return CaptureProfile(
        profile_id=profile_id,
        enabled=bool(profile_config.get('enabled', default_enabled)),
        primary=bool(profile_config.get('primary', default_primary)),
        processing_mode=_processing_mode(profile_config),
        hybrid_awb_apply_mode=_hybrid_awb_apply_mode(
            profile_config,
            profile_id=profile_id,
            camera_interface=str(camera_interface or ''),
            indi_camera_name=indi_camera_name,
        ),
        camera_interface=str(camera_interface or 'indi'),
        indi_server=str(indi_config.get('server', profile_config.get('indi_server', config.get('INDI_SERVER', 'localhost'))) or 'localhost'),
        indi_port=indi_port,
        indi_camera_name=indi_camera_name,
        libcamera_camera_id=libcamera_camera_id,
        # MULTI_CAMERA_PREP: mirror per-camera tuning from the legacy
        # global config without changing runtime behavior yet.
        ccd_config=ccd_config,
        exposure_min=_mapping_float(exposure_config, 'min', _float_config(profile_config, 'exposure_min', _float_config(config, 'CCD_EXPOSURE_MIN', 0.0))),
        exposure_min_day=_mapping_float(exposure_config, 'min_day', _float_config(profile_config, 'exposure_min_day', _float_config(config, 'CCD_EXPOSURE_MIN_DAY', 0.0))),
        exposure_max=_mapping_float(exposure_config, 'max', _float_config(profile_config, 'exposure_max', _float_config(config, 'CCD_EXPOSURE_MAX', 15.0))),
        exposure_default=_mapping_float(exposure_config, 'default', _float_config(profile_config, 'exposure_default', _float_config(config, 'CCD_EXPOSURE_DEF', 0.0))),
        exposure_timeout=_mapping_float(exposure_config, 'timeout', _float_config(profile_config, 'exposure_timeout', _float_config(config, 'CCD_EXPOSURE_TIMEOUT', 330.0))),
        exposure_period=_mapping_float(exposure_config, 'period', _float_config(profile_config, 'exposure_period', _float_config(config, 'EXPOSURE_PERIOD', 15.0))),
        exposure_period_day=_mapping_float(exposure_config, 'period_day', _float_config(profile_config, 'exposure_period_day', _float_config(config, 'EXPOSURE_PERIOD_DAY', 15.0))),
        auto_exposure_metering_mode=_auto_exposure_metering_mode(config, profile_config),
        target_adu=_mapping_int(target_adu_config, 'night', _int_config(profile_config, 'target_adu', _int_config(config, 'TARGET_ADU', 75))),
        target_adu_day=_mapping_int(target_adu_config, 'day', _int_config(profile_config, 'target_adu_day', _int_config(config, 'TARGET_ADU_DAY', 75))),
        target_adu_dev=_mapping_int(target_adu_config, 'dev', _int_config(profile_config, 'target_adu_dev', _int_config(config, 'TARGET_ADU_DEV', 10))),
        target_adu_dev_day=_mapping_int(target_adu_config, 'dev_day', _int_config(profile_config, 'target_adu_dev_day', _int_config(config, 'TARGET_ADU_DEV_DAY', 20))),
        gain_default=_float_config(profile_config, 'gain_default', _mapping_float(ccd_night, 'GAIN', 100.0)),
        gain_min=_float_config(profile_config, 'gain_min', _mapping_float(ccd_day, 'GAIN', 0.0)),
        gain_max=_float_config(profile_config, 'gain_max', _mapping_float(ccd_night, 'GAIN', 100.0)),
        gain_night=_mapping_float(ccd_night, 'GAIN', _float_config(profile_config, 'gain_max', 100.0)),
        gain_moonmode=_mapping_float(ccd_moonmode, 'GAIN', 75.0),
        gain_day=_mapping_float(ccd_day, 'GAIN', _float_config(profile_config, 'gain_min', 0.0)),
        auto_gain_enable=bool(profile_config.get('auto_gain_enable', bool(ccd_config.get('AUTO_GAIN_ENABLE', False)))),
        auto_gain_day=bool(profile_config.get('auto_gain_day', bool(ccd_config.get('AUTO_GAIN_ENABLE_DAY', ccd_config.get('AUTO_GAIN_ENABLE', False))))),
        auto_gain_night=bool(profile_config.get('auto_gain_night', bool(ccd_config.get('AUTO_GAIN_ENABLE_NIGHT', ccd_config.get('AUTO_GAIN_ENABLE', False))))),
        auto_gain_moonmode=bool(profile_config.get('auto_gain_moonmode', bool(ccd_config.get('AUTO_GAIN_ENABLE_MOONMODE', ccd_config.get('AUTO_GAIN_ENABLE', False))))),
        auto_gain_levels=_int_config(profile_config, 'auto_gain_levels', _mapping_int(ccd_config, 'AUTO_GAIN_LEVELS', 5)),
        binning_night=_int_config(profile_config, 'binning_night', _mapping_int(ccd_night, 'BINNING', 1)),
        binning_moonmode=_mapping_int(ccd_moonmode, 'BINNING', 1),
        binning_day=_int_config(profile_config, 'binning_day', _mapping_int(ccd_day, 'BINNING', 1)),
        cooling_enabled=bool(profile_config.get('cooling_enabled', _bool_config(config, 'CCD_COOLING', False))),
        cooling_enabled_day=bool(profile_config.get('cooling_enabled_day', _bool_config(config, 'CCD_COOLING_DAY', False))),
        target_temperature=_float_config(profile_config, 'target_temperature', _float_config(config, 'CCD_TEMP', 15.0)),
        target_temperature_day=_float_config(profile_config, 'target_temperature_day', _float_config(config, 'CCD_TEMP_DAY', 35.0)),
        libcamera_image_file_type=str(libcamera_config.get('IMAGE_FILE_TYPE', 'jpg') or 'jpg'),
        libcamera_image_file_type_day=str(libcamera_config.get('IMAGE_FILE_TYPE_DAY', 'jpg') or 'jpg'),
        libcamera_immediate=bool(libcamera_config.get('IMMEDIATE', True)),
        libcamera_immediate_day=bool(libcamera_config.get('IMMEDIATE_DAY', True)),
        libcamera_awb=str(libcamera_config.get('AWB', 'auto') or 'auto'),
        libcamera_awb_day=str(libcamera_config.get('AWB_DAY', 'auto') or 'auto'),
        libcamera_awb_enable=bool(libcamera_config.get('AWB_ENABLE', True)),
        libcamera_awb_enable_day=bool(libcamera_config.get('AWB_ENABLE_DAY', True)),
        libcamera_awb_mode_configured='AWB_MODE' in libcamera_config or 'awb_mode' in libcamera_config,
        libcamera_awb_mode=_libcamera_awb_mode(libcamera_config),
        libcamera_awb_red_gain=_mapping_float(libcamera_config, 'AWB_RED_GAIN', _mapping_float(libcamera_config, 'awb_red_gain', 1.0)),
        libcamera_awb_blue_gain=_mapping_float(libcamera_config, 'AWB_BLUE_GAIN', _mapping_float(libcamera_config, 'awb_blue_gain', 1.0)),
        libcamera_ccm_disable=bool(libcamera_config.get('CCM_DISABLE', False)),
        libcamera_ccm_disable_day=bool(libcamera_config.get('CCM_DISABLE_DAY', False)),
        libcamera_extra_options=str(libcamera_config.get('EXTRA_OPTIONS', '') or ''),
        libcamera_extra_options_day=str(libcamera_config.get('EXTRA_OPTIONS_DAY', '') or ''),
        camera_sqm=camera_sqm,
        focus_mode=bool(profile_config.get('focus_mode', _bool_config(config, 'FOCUS_MODE', False))),
        focus_delay=_float_config(profile_config, 'focus_delay', _float_config(config, 'FOCUS_DELAY', 4.0)),
        daytime_capture=bool(profile_config.get('daytime_capture', _bool_config(config, 'DAYTIME_CAPTURE', True))),
        daytime_capture_save=bool(profile_config.get('daytime_capture_save', _bool_config(config, 'DAYTIME_CAPTURE_SAVE', True))),
        daytime_timelapse=bool(profile_config.get('daytime_timelapse', _bool_config(config, 'DAYTIME_TIMELAPSE', True))),
        cfa_pattern=str(profile_config.get('cfa_pattern', config.get('CFA_PATTERN', '')) or ''),
        ccd_bit_depth=_int_config(profile_config, 'ccd_bit_depth', _int_config(config, 'CCD_BIT_DEPTH', 0)),
        outputs=outputs,
    )


def build_profile_config(config: Mapping[str, Any], profile: CaptureProfile) -> Dict[str, Any]:
    """Return a per-profile config overlay without mutating the base config."""

    profile_config = deepcopy(dict(config))
    profile_config['PROCESSING_MODE'] = profile.processing_mode
    hybrid_config = deepcopy(profile_config.get('HYBRID') or {})
    hybrid_awb_config = deepcopy(hybrid_config.get('AWB') or {})
    hybrid_awb_config['APPLY_MODE'] = profile.hybrid_awb_apply_mode
    hybrid_config['AWB'] = hybrid_awb_config
    profile_config['HYBRID'] = hybrid_config
    profile_config['CAMERA_INTERFACE'] = profile.camera_interface
    profile_config['INDI_SERVER'] = profile.indi_server
    profile_config['INDI_PORT'] = profile.indi_port
    profile_config['INDI_CAMERA_NAME'] = profile.indi_camera_name
    ccd_config = deepcopy(profile.ccd_config)
    ccd_night = deepcopy(ccd_config.get('NIGHT') or {})
    ccd_moonmode = deepcopy(ccd_config.get('MOONMODE') or {})
    ccd_day = deepcopy(ccd_config.get('DAY') or {})
    ccd_night['GAIN'] = profile.gain_night
    ccd_night['BINNING'] = profile.binning_night
    ccd_moonmode['GAIN'] = profile.gain_moonmode
    ccd_moonmode['BINNING'] = profile.binning_moonmode
    ccd_day['GAIN'] = profile.gain_day
    ccd_day['BINNING'] = profile.binning_day
    ccd_config['NIGHT'] = ccd_night
    ccd_config['MOONMODE'] = ccd_moonmode
    ccd_config['DAY'] = ccd_day
    ccd_config['AUTO_GAIN_ENABLE'] = bool(profile.auto_gain_day or profile.auto_gain_night or profile.auto_gain_moonmode)
    ccd_config['AUTO_GAIN_ENABLE_DAY'] = profile.auto_gain_day
    ccd_config['AUTO_GAIN_ENABLE_NIGHT'] = profile.auto_gain_night
    ccd_config['AUTO_GAIN_ENABLE_MOONMODE'] = profile.auto_gain_moonmode
    ccd_config['AUTO_GAIN_LEVELS'] = profile.auto_gain_levels
    profile_config['CCD_CONFIG'] = ccd_config
    profile_config['CCD_EXPOSURE_MIN'] = profile.exposure_min
    profile_config['CCD_EXPOSURE_MIN_DAY'] = profile.exposure_min_day
    profile_config['CCD_EXPOSURE_MAX'] = profile.exposure_max
    profile_config['CCD_EXPOSURE_DEF'] = profile.exposure_default
    profile_config['CCD_EXPOSURE_TIMEOUT'] = profile.exposure_timeout
    profile_config['EXPOSURE_PERIOD'] = profile.exposure_period
    profile_config['EXPOSURE_PERIOD_DAY'] = profile.exposure_period_day
    profile_config['AUTO_EXPOSURE_METERING_MODE'] = profile.auto_exposure_metering_mode
    profile_config['TARGET_ADU'] = profile.target_adu
    profile_config['TARGET_ADU_DAY'] = profile.target_adu_day
    profile_config['TARGET_ADU_DEV'] = profile.target_adu_dev
    profile_config['TARGET_ADU_DEV_DAY'] = profile.target_adu_dev_day
    profile_config['CCD_COOLING'] = profile.cooling_enabled
    profile_config['CCD_COOLING_DAY'] = profile.cooling_enabled_day
    profile_config['CCD_TEMP'] = profile.target_temperature
    profile_config['CCD_TEMP_DAY'] = profile.target_temperature_day
    profile_config['FOCUS_MODE'] = profile.focus_mode
    profile_config['FOCUS_DELAY'] = profile.focus_delay
    profile_config['DAYTIME_CAPTURE'] = profile.daytime_capture
    profile_config['DAYTIME_CAPTURE_SAVE'] = profile.daytime_capture_save
    profile_config['DAYTIME_TIMELAPSE'] = profile.daytime_timelapse
    profile_config['CFA_PATTERN'] = profile.cfa_pattern
    profile_config['CCD_BIT_DEPTH'] = profile.ccd_bit_depth
    profile_config['CAMERA_SQM'] = deepcopy(profile.camera_sqm)

    libcamera_config = deepcopy(profile_config.get('LIBCAMERA') or {})
    libcamera_config['CAMERA_ID'] = profile.libcamera_camera_id
    libcamera_config['IMAGE_FILE_TYPE'] = profile.libcamera_image_file_type
    libcamera_config['IMAGE_FILE_TYPE_DAY'] = profile.libcamera_image_file_type_day
    libcamera_config['IMMEDIATE'] = profile.libcamera_immediate
    libcamera_config['IMMEDIATE_DAY'] = profile.libcamera_immediate_day
    libcamera_config['AWB'] = profile.libcamera_awb
    libcamera_config['AWB_DAY'] = profile.libcamera_awb_day
    libcamera_config['AWB_ENABLE'] = profile.libcamera_awb_enable
    libcamera_config['AWB_ENABLE_DAY'] = profile.libcamera_awb_enable_day
    if profile.libcamera_awb_mode_configured:
        libcamera_config['AWB_MODE'] = profile.libcamera_awb_mode
        libcamera_config['AWB_RED_GAIN'] = profile.libcamera_awb_red_gain
        libcamera_config['AWB_BLUE_GAIN'] = profile.libcamera_awb_blue_gain
        if profile.libcamera_awb_mode == 'fixed':
            libcamera_config['AWB_ENABLE'] = False
            libcamera_config['AWB_ENABLE_DAY'] = False
        else:
            libcamera_config['AWB'] = profile.libcamera_awb_mode
            libcamera_config['AWB_DAY'] = profile.libcamera_awb_mode
            libcamera_config['AWB_ENABLE'] = True
            libcamera_config['AWB_ENABLE_DAY'] = True
    libcamera_config['CCM_DISABLE'] = profile.libcamera_ccm_disable
    libcamera_config['CCM_DISABLE_DAY'] = profile.libcamera_ccm_disable_day
    libcamera_config['EXTRA_OPTIONS'] = profile.libcamera_extra_options
    libcamera_config['EXTRA_OPTIONS_DAY'] = profile.libcamera_extra_options_day
    profile_config['LIBCAMERA'] = libcamera_config

    if not profile.outputs.get('timelapse', True):
        profile_config['TIMELAPSE_ENABLE'] = False

    if not profile.outputs.get('keogram', True):
        profile_config['TIMELAPSE_ENABLE'] = False

    if not profile.outputs.get('panorama', True):
        fish2pano_config = deepcopy(profile_config.get('FISH2PANO') or {})
        fish2pano_config['ENABLE'] = False
        profile_config['FISH2PANO'] = fish2pano_config

    if not profile.outputs.get('extra_uploads', True):
        filetransfer_config = deepcopy(profile_config.get('FILETRANSFER') or {})
        filetransfer_config['UPLOAD_IMAGE'] = False
        filetransfer_config['UPLOAD_METADATA'] = False
        profile_config['FILETRANSFER'] = filetransfer_config

        s3upload_config = deepcopy(profile_config.get('S3UPLOAD') or {})
        s3upload_config['ENABLE'] = False
        profile_config['S3UPLOAD'] = s3upload_config

        syncapi_config = deepcopy(profile_config.get('SYNCAPI') or {})
        syncapi_config['ENABLE'] = False
        profile_config['SYNCAPI'] = syncapi_config

        mqttpublish_config = deepcopy(profile_config.get('MQTTPUBLISH') or {})
        mqttpublish_config['ENABLE'] = False
        profile_config['MQTTPUBLISH'] = mqttpublish_config

    if profile.outputs.get('images') and not all((
        profile.outputs.get('timelapse', True),
        profile.outputs.get('mini_timelapse', True),
        profile.outputs.get('keogram', True),
        profile.outputs.get('realtime_keogram', True),
        profile.outputs.get('longterm_keogram', True),
        profile.outputs.get('startrails', True),
        profile.outputs.get('panorama', True),
        profile.outputs.get('panorama_loop', True),
        profile.outputs.get('extra_uploads', True),
    )):
        profile_config['IMAGE_SAVE_FITS'] = False
        profile_config['IMAGE_SAVE_FITS_PRE_DARK'] = False
        profile_config['IMAGE_EXPORT_RAW'] = ''
        profile_config['IMAGE_SAVE_HOOK_PRE'] = ''
        profile_config['IMAGE_SAVE_HOOK_POST'] = ''

        circular_display_config = deepcopy(profile_config.get('CIRCULAR_DISPLAY') or {})
        circular_display_config['ENABLE'] = False
        profile_config['CIRCULAR_DISPLAY'] = circular_display_config

    profile_config['MULTI_CAMERA_ACTIVE_PROFILE'] = profile.profile_id
    profile_config['MULTI_CAMERA_PROFILE_OUTPUTS'] = deepcopy(profile.outputs)

    return profile_config


def derive_capture_profiles(config: Mapping[str, Any]) -> List[CaptureProfile]:
    """Derive capture profiles from the current config.

    When MULTI_CAMERA profiles are absent, this deliberately returns exactly
    one default profile. It does not mutate the config and the runtime still
    decides whether multiple enabled profiles may start.
    """

    if not bool(config.get('MULTI_CAMERA_CAPTURE_ENABLE', False)):
        return [_profile_from_config(config)]

    multi_camera_config = config.get('MULTI_CAMERA') or {}
    profile_configs = multi_camera_config.get('profiles') or []

    if profile_configs:
        profiles = [
            _profile_from_config(
                config,
                profile_config,
                default_profile_id='profile-{0:d}'.format(idx + 1),
                default_enabled=False,
                default_primary=(idx == 0),
            )
            for idx, profile_config in enumerate(profile_configs)
        ]

        if profiles:
            return profiles

    return [_profile_from_config(config)]
