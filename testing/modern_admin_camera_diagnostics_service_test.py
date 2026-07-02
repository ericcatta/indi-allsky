#!/usr/bin/env python3

import math
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from indi_allsky.modern_admin_camera_diagnostics import ModernAdminCameraInfoService


class FakeCamera:
    id = 7
    name = 'Camera'
    owner = 'Observatory Owner'
    cfa = 1
    width = 4000
    height = 3000
    pixelSize = 2.9
    lensFocalLength = 8.0
    lensFocalRatio = 2.0
    lensImageCircle = 3200


def test_camera_info_service_preserves_camera_lens_context_shape():
    service = ModernAdminCameraInfoService(cfa_map={1: 'RGGB'})

    context = service.build_context(FakeCamera(), privacy_mode=False)

    assert context['camera'].__class__ is FakeCamera
    assert context['owner'] == 'Observatory Owner'
    assert context['camera_cfa'] == 'RGGB'
    assert context['lensAperture'] == 4.0
    assert context['camera_width_mm'] == 11.6
    assert context['camera_height_mm'] == 8.7
    assert round(context['camera_diagonal_mm'], 3) == round(math.hypot(11.6, 8.7), 3)
    assert round(context['arcsec_pixel'], 6) == round(2.9 / 8.0 * 206.2648, 6)
    assert context['dms_pixel'][0] == 0.0
    assert round(context['arcsec_um'], 6) == round(context['arcsec_pixel'] / 2.9, 6)
    assert round(context['deg2_px'], 10) == round((context['arcsec_pixel'] / 3600) ** 2, 10)
    assert context['image_circle_diameter'] == 3200
    assert context['image_circle_diameter_mm'] == 9.28
    assert round(context['deg_fov_width'], 6) == round(3200 * context['arcsec_pixel'] * 1.2 / 3600, 6)
    assert round(context['deg_fov_height'], 6) == round(3000 * context['arcsec_pixel'] * 1.2 / 3600, 6)
    assert round(context['deg_fov_diagonal'], 6) == round(3200 * context['arcsec_pixel'] * 1.2 / 3600, 6)


def test_camera_info_service_preserves_privacy_owner():
    service = ModernAdminCameraInfoService(cfa_map={1: 'RGGB'})

    context = service.build_context(FakeCamera(), privacy_mode=True)

    assert context['owner'] == 'Private'


def test_modern_camera_info_view_uses_camera_info_service():
    source = (REPO_ROOT / 'indi_allsky' / 'flask' / 'views.py').read_text()
    start = source.index('class ModernAdminCameraInfoView')
    end = source.index('class ModernAdminImageLagView', start)
    source = source[start:end]

    assert 'ModernAdminCameraInfoService' in source
    assert 'lensFocalLength / camera.lensFocalRatio' not in source
    assert 'camera_width_mm = camera.width * camera.pixelSize' not in source


def test_camera_info_service_has_no_flask_db_or_filesystem_dependency():
    import inspect
    import indi_allsky.modern_admin_camera_diagnostics as module

    source = inspect.getsource(module)

    assert 'flask' not in source.lower()
    assert 'db.session' not in source
    assert 'request' not in source
    assert 'open(' not in source
    assert 'getFilesystemPath' not in source


def run_tests():
    test_camera_info_service_preserves_camera_lens_context_shape()
    test_camera_info_service_preserves_privacy_owner()
    test_modern_camera_info_view_uses_camera_info_service()
    test_camera_info_service_has_no_flask_db_or_filesystem_dependency()
    print('Modern admin camera diagnostics service checks passed')


if __name__ == '__main__':
    run_tests()
