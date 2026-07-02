#!/usr/bin/env python3

import inspect
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from indi_allsky.modern_admin_observatory_tools import ModernAdminLongTermKeogramDisplayService
from indi_allsky.modern_admin_observatory_tools import ModernAdminSqmSummaryService


class FakeSqmSummary:
    sqm_min = 18.1
    sqm_avg = 19.2
    sqm_max = 20.3
    stars_min = 10
    stars_avg = 20
    stars_max = 30


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
    test_modern_sqm_view_uses_observatory_service()
    test_modern_longterm_keogram_view_uses_display_service()
    test_observatory_tools_module_has_no_flask_db_or_filesystem_dependency()
    print('Modern admin observatory tools checks passed')


if __name__ == '__main__':
    run_tests()
