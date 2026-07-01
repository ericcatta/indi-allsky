#!/usr/bin/env python3

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
VIEWS_PATH = REPO_ROOT / 'indi_allsky/flask/views.py'


OBSERVATORY_TOOL_WRAPPERS = (
    'ModernAdminSqmView',
    'ModernAdminChartsView',
    'ModernAdminSensorPanelView',
    'ModernAdminRealtimeKeogramView',
    'ModernAdminLongTermKeogramView',
    'ModernAdminAstroPanelView',
    'ModernAdminVirtualSkyView',
)


def assert_true(condition, message):
    if not condition:
        raise AssertionError(message)


def test_observatory_tools_use_hybrid_boundary():
    views_text = VIEWS_PATH.read_text(encoding='utf-8')

    assert_true(
        'class ModernAdminObservatoryToolView(ModernAdminContextMixin):' in views_text,
        'Observatory tools should have a dedicated Hybrid boundary',
    )

    for class_name in OBSERVATORY_TOOL_WRAPPERS:
        class_prefix = 'class {0:s}(ModernAdminObservatoryToolView,'.format(class_name)
        assert_true(
            class_prefix in views_text,
            '{0:s} must inherit from ModernAdminObservatoryToolView'.format(class_name),
        )


def run_tests():
    test_observatory_tools_use_hybrid_boundary()
    print('Modern admin boundary checks passed')


if __name__ == '__main__':
    run_tests()
