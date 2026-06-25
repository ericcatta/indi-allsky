import copy
import sys
import types
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

sys.modules.setdefault(
    'cv2',
    types.SimpleNamespace(COLOR_BGR2GRAY=0, cvtColor=lambda image, _: image),
)

from indi_allsky.capture_profiles import build_profile_config
from indi_allsky.capture_profiles import derive_capture_profiles


def _base_config(outputs):
    return {
        'MULTI_CAMERA_CAPTURE_ENABLE': True,
        'CAMERA_INTERFACE': 'indi',
        'INDI_SERVER': 'localhost',
        'INDI_PORT': 7624,
        'INDI_CAMERA_NAME': 'ZWO CCD ASI678MC',
        'CCD_CONFIG': {
            'NIGHT': {'GAIN': 100.0, 'BINNING': 1},
            'MOONMODE': {'GAIN': 75.0, 'BINNING': 1},
            'DAY': {'GAIN': 0.0, 'BINNING': 1},
            'AUTO_GAIN_ENABLE': False,
            'AUTO_GAIN_LEVELS': 5,
        },
        'HYBRID': {'AWB': {}},
        'LIBCAMERA': {},
        'CAMERA_SQM': {},
        'IMAGE_STRETCH': {},
        'FISH2PANO': {'ENABLE': True},
        'FILETRANSFER': {},
        'S3UPLOAD': {},
        'SYNCAPI': {},
        'MQTTPUBLISH': {},
        'IMAGE_SAVE_FITS': True,
        'IMAGE_SAVE_FITS_PRE_DARK': True,
        'IMAGE_EXPORT_RAW': 'tif',
        'IMAGE_SAVE_HOOK_PRE': 'pre-hook',
        'IMAGE_SAVE_HOOK_POST': 'post-hook',
        'CIRCULAR_DISPLAY': {'ENABLE': True},
        'TIMELAPSE_ENABLE': True,
        'MULTI_CAMERA': {
            'profiles': [
                {
                    'profile_id': 'asi678mc',
                    'enabled': True,
                    'primary': True,
                    'camera_interface': 'indi',
                    'outputs': outputs,
                },
            ],
        },
    }


def _resolved_config(outputs):
    config = _base_config(outputs)
    profile = derive_capture_profiles(config)[0]
    return build_profile_config(config, profile)


def test_optional_outputs_disabled_preserve_fits_raw():
    outputs = {
        'images': True,
        'timelapse': True,
        'keogram': True,
        'startrails': True,
        'mini_timelapse': False,
        'realtime_keogram': False,
        'longterm_keogram': False,
        'panorama': False,
        'panorama_loop': False,
        'extra_uploads': False,
    }

    resolved = _resolved_config(outputs)

    assert resolved['IMAGE_SAVE_FITS'] is True
    assert resolved['IMAGE_SAVE_FITS_PRE_DARK'] is True
    assert resolved['IMAGE_EXPORT_RAW'] == 'tif'
    assert resolved['IMAGE_SAVE_HOOK_PRE'] == 'pre-hook'
    assert resolved['IMAGE_SAVE_HOOK_POST'] == 'post-hook'


def test_true_images_only_profile_disables_fits_raw():
    outputs = {
        'images': True,
        'timelapse': False,
        'keogram': False,
        'startrails': False,
        'mini_timelapse': False,
        'realtime_keogram': False,
        'longterm_keogram': False,
        'panorama': False,
        'panorama_loop': False,
        'extra_uploads': False,
    }

    resolved = _resolved_config(outputs)

    assert resolved['IMAGE_SAVE_FITS'] is False
    assert resolved['IMAGE_SAVE_FITS_PRE_DARK'] is False
    assert resolved['IMAGE_EXPORT_RAW'] == ''
    assert resolved['IMAGE_SAVE_HOOK_PRE'] == ''
    assert resolved['IMAGE_SAVE_HOOK_POST'] == ''
    assert resolved['CIRCULAR_DISPLAY']['ENABLE'] is False


def test_profile_resolution_does_not_mutate_base_config():
    outputs = {
        'images': True,
        'timelapse': False,
        'keogram': False,
        'startrails': False,
    }
    config = _base_config(outputs)
    original = copy.deepcopy(config)
    profile = derive_capture_profiles(config)[0]

    build_profile_config(config, profile)

    assert config == original


if __name__ == '__main__':
    test_optional_outputs_disabled_preserve_fits_raw()
    test_true_images_only_profile_disables_fits_raw()
    test_profile_resolution_does_not_mutate_base_config()
    print('capture profiles tests OK')
