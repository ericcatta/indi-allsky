#!/usr/bin/env python3

import inspect
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from indi_allsky.modern_admin_observatory_tools import ModernAdminLongTermKeogramDisplayService
from indi_allsky.modern_admin_observatory_tools import ModernAdminSqmSummaryService
from indi_allsky.modern_admin_observatory_tools import ModernAdminVirtualSkyContextService


class FakeSqmSummary:
    sqm_min = 18.1
    sqm_avg = 19.2
    sqm_max = 20.3
    stars_min = 10
    stars_avg = 20
    stars_max = 30


class FakeCamera:
    az = 123.4
    data = {
        'vs_image_circle_diameter': 2800,
        'vs_latitude_offset'      : 1.25,
        'vs_offset_x'             : -2.5,
        'vs_magnitude'            : 5.5,
        'vs_constellations'       : False,
        'vs_showplanets'          : False,
    }


class FakeCameraWithoutData:
    az = 42.0
    data = None


def test_sqm_summary_service_preserves_context_shape():
    service = ModernAdminSqmSummaryService()
    summary = FakeSqmSummary()

    context = service.build_context(
        image_data={
            'sqm'       : 19.75,
            'stars'     : 42,
            'moon_phase': 64.5,
        },
        sqm_summary=summary,
    )

    assert context == {
        'modern_admin_sqm'        : 19.75,
        'modern_admin_stars'      : 42,
        'modern_admin_moon_phase' : 64.5,
        'modern_admin_sqm_summary': summary,
    }


def test_sqm_summary_service_preserves_safe_defaults():
    service = ModernAdminSqmSummaryService()

    context = service.build_context(image_data={}, sqm_summary=None)

    assert context == {
        'modern_admin_sqm'        : 0.0,
        'modern_admin_stars'      : 0,
        'modern_admin_moon_phase' : 0.0,
        'modern_admin_sqm_summary': None,
    }


def test_longterm_keogram_display_service_preserves_age_format():
    service = ModernAdminLongTermKeogramDisplayService()

    assert service.format_generated_age(0) == 'Generated 0 days, 0 hours, 0 minutes ago'
    assert service.format_generated_age(60) == 'Generated 0 days, 0 hours, 1 minutes ago'
    assert service.format_generated_age(90061) == 'Generated 1 days, 1 hours, 1 minutes ago'


def test_virtualsky_context_service_preserves_form_data_shape():
    service = ModernAdminVirtualSkyContextService()

    data = service.build_form_data(FakeCamera())

    assert data == {
        'AZIMUTH_ANGLE'         : 123.4,
        'IMAGE_CIRCLE_DIAMETER' : 2800,
        'LATITUDE_OFFSET'       : 1.25,
        'LONGITUDE_OFFSET'      : 0.0,
        'OFFSET_X'              : -2.5,
        'OFFSET_Y'              : 0.0,
        'MAGNITUDE'             : 5.5,
        'CONSTELLATIONS'        : False,
        'CONSTELLATIONLABELS'   : False,
        'SHOWSTARS'             : True,
        'SHOWSTARLABELS'        : True,
        'SHOWPLANETS'           : False,
        'SHOWPLANETLABELS'      : True,
    }


def test_virtualsky_context_service_preserves_defaults_without_camera_data():
    service = ModernAdminVirtualSkyContextService()

    data = service.build_form_data(FakeCameraWithoutData())

    assert data['AZIMUTH_ANGLE'] == 42.0
    assert data['IMAGE_CIRCLE_DIAMETER'] == 3500
    assert data['MAGNITUDE'] == 6.0
    assert data['CONSTELLATIONS'] is True
    assert data['CONSTELLATIONLABELS'] is False


def test_modern_sqm_view_uses_observatory_service():
    source = (REPO_ROOT / 'indi_allsky' / 'flask' / 'views.py').read_text()
    start = source.index('class ModernAdminSqmView')
    end = source.index('class ModernAdminChartsView', start)
    source = source[start:end]

    assert 'ModernAdminSqmSummaryService' in source
    assert "context['modern_admin_sqm'] = image_data.get" not in source
    assert 'context.update(self.sqm_summary_service.build_context' in source


def test_modern_longterm_keogram_view_uses_display_service():
    source = (REPO_ROOT / 'indi_allsky' / 'flask' / 'views.py').read_text()
    start = source.index('class ModernAdminLongTermKeogramView')
    end = source.index('class ModernAdminDarkLibraryView', start)
    source = source[start:end]

    assert 'ModernAdminLongTermKeogramDisplayService' in source
    assert 'format_generated_age' in source
    assert 'image_age_days = int(image_age_s / 86400)' not in source
    assert "'Generated {0:d} days" not in source


def test_virtualsky_view_uses_context_service():
    source = (REPO_ROOT / 'indi_allsky' / 'flask' / 'views.py').read_text()
    start = source.index('class VirtualSkyView')
    end = source.index('class RealtimeKeogramView', start)
    source = source[start:end]

    assert 'ModernAdminVirtualSkyContextService' in source
    assert 'build_form_data' in source
    assert "'IMAGE_CIRCLE_DIAMETER' : self.camera.data.get" not in source
    assert "'SHOWPLANETLABELS'      : self.camera.data.get" not in source


def test_observatory_tools_module_has_no_flask_db_or_filesystem_dependency():
    import indi_allsky.modern_admin_observatory_tools as module

    source = inspect.getsource(module)

    assert 'flask' not in source.lower()
    assert 'db.session' not in source
    assert 'request' not in source
    assert 'open(' not in source
    assert 'Path(' not in source


def run_tests():
    test_sqm_summary_service_preserves_context_shape()
    test_sqm_summary_service_preserves_safe_defaults()
    test_longterm_keogram_display_service_preserves_age_format()
    test_virtualsky_context_service_preserves_form_data_shape()
    test_virtualsky_context_service_preserves_defaults_without_camera_data()
    test_modern_sqm_view_uses_observatory_service()
    test_modern_longterm_keogram_view_uses_display_service()
    test_virtualsky_view_uses_context_service()
    test_observatory_tools_module_has_no_flask_db_or_filesystem_dependency()
    print('Modern admin observatory tools checks passed')


if __name__ == '__main__':
    run_tests()
