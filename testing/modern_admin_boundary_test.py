#!/usr/bin/env python3

import re
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
VIEWS_PATH = REPO_ROOT / 'indi_allsky/flask/views.py'


BOUNDARIES = (
    {
        'boundary': 'ModernAdminProductView',
        'parent': 'TemplateView',
        'wrappers': (
            'ModernAdminNowView',
            'ModernAdminHighlightsView',
            'ModernAdminMomentDetailView',
            'ModernAdminOutputDetailView',
            'ModernAdminLibraryView',
            'ModernAdminSkyCycleView',
            'ModernAdminObservatoryView',
        ),
    },
    {
        'boundary': 'ModernAdminObservatoryToolView',
        'parent': 'ModernAdminContextMixin',
        'wrappers': (
            'ModernAdminSqmView',
            'ModernAdminChartsView',
            'ModernAdminSensorPanelView',
            'ModernAdminRealtimeKeogramView',
            'ModernAdminLongTermKeogramView',
            'ModernAdminAstroPanelView',
            'ModernAdminVirtualSkyView',
        ),
    },
    {
        'boundary': 'ModernAdminCameraToolView',
        'parent': 'ModernAdminContextMixin',
        'wrappers': (
            'ModernAdminCameraInfoView',
            'ModernAdminImageLagView',
            'ModernAdminAduHistoryView',
            'ModernAdminDarkLibraryView',
            'ModernAdminMaskView',
        ),
    },
    {
        'boundary': 'ModernAdminSystemToolView',
        'parent': 'ModernAdminContextMixin',
        'decorator': 'login_required',
        'wrappers_defer_decorator': True,
        'wrappers': (
            'ModernAdminSystemInfoView',
            'ModernAdminSupportInfoView',
            'ModernAdminLogView',
            'ModernAdminLogDetailView',
        ),
    },
    {
        'boundary': 'ModernAdminTaskStatusView',
        'parent': 'ModernAdminContextMixin',
        'decorator': 'login_required',
        'wrappers_defer_decorator': True,
        'wrappers': (
            'ModernAdminTaskQueueView',
            'ModernAdminTaskDetailView',
        ),
    },
    {
        'boundary': 'ModernAdminMediaMetadataView',
        'parent': 'ModernAdminContextMixin',
        'decorator': 'login_required',
        'wrappers_defer_decorator': True,
        'decorator_delegates': (
            'ModernAdminFitsDetailView',
        ),
        'wrappers': (
            'ModernAdminMediaStartrailVideosView',
            'ModernAdminMediaKeogramsView',
            'ModernAdminMediaStartrailsView',
            'ModernAdminMediaMiniTimelapsesView',
            'ModernAdminMediaPanoramaView',
            'ModernAdminMediaRawImagesView',
            'ModernAdminFitsView',
        ),
    },
    {
        'boundary': 'ModernAdminMediaBrowseView',
        'parent': 'ModernAdminContextMixin',
        'wrappers': (
            'ModernAdminMediaListView',
        ),
    },
)


def assert_true(condition, message):
    if not condition:
        raise AssertionError(message)


def read_views():
    return VIEWS_PATH.read_text(encoding='utf-8')


def class_bases(views_text, class_name):
    match = re.search(
        r'^class\s+{0:s}\(([^)]*)\):'.format(re.escape(class_name)),
        views_text,
        flags=re.MULTILINE,
    )
    if not match:
        return None

    return tuple(base.strip() for base in match.group(1).split(',') if base.strip())


def class_body(views_text, class_name):
    match = re.search(
        r'^class\s+{0:s}\([^)]*\):\n'.format(re.escape(class_name)),
        views_text,
        flags=re.MULTILINE,
    )
    if not match:
        return None

    start = match.end()
    next_class = re.search(r'^class\s+\w+\(', views_text[start:], flags=re.MULTILINE)
    if not next_class:
        return views_text[start:]

    return views_text[start:start + next_class.start()]


def test_boundaries_exist_with_expected_parent():
    views_text = read_views()

    for spec in BOUNDARIES:
        bases = class_bases(views_text, spec['boundary'])
        assert_true(
            bases == (spec['parent'],),
            '{0:s} must inherit only from {1:s}'.format(spec['boundary'], spec['parent']),
        )


def test_boundary_owned_decorators_stay_on_boundary():
    views_text = read_views()

    for spec in BOUNDARIES:
        decorator = spec.get('decorator')
        if not decorator:
            continue

        boundary_body = class_body(views_text, spec['boundary'])
        assert_true(
            boundary_body is not None and 'decorators = [{0:s}]'.format(decorator) in boundary_body,
            '{0:s} must own decorators = [{1:s}]'.format(spec['boundary'], decorator),
        )

        if not spec.get('wrappers_defer_decorator'):
            continue

        decorator_delegates = spec['wrappers'] + spec.get('decorator_delegates', ())
        for class_name in decorator_delegates:
            wrapper_body = class_body(views_text, class_name)
            assert_true(
                wrapper_body is not None and 'decorators =' not in wrapper_body,
                '{0:s} must inherit decorators from {1:s}'.format(class_name, spec['boundary']),
            )


def test_wrappers_use_expected_hybrid_boundary():
    views_text = read_views()

    for spec in BOUNDARIES:
        boundary = spec['boundary']
        for class_name in spec['wrappers']:
            bases = class_bases(views_text, class_name)
            assert_true(bases is not None, '{0:s} class is missing'.format(class_name))
            assert_true(
                bases[0] == boundary,
                '{0:s} must use {1:s} as its first base'.format(class_name, boundary),
            )


def test_isolated_wrappers_do_not_bypass_hybrid_boundaries():
    views_text = read_views()

    for spec in BOUNDARIES:
        for class_name in spec['wrappers']:
            bases = class_bases(views_text, class_name)
            assert_true(
                bases is not None and 'ModernAdminContextMixin' not in bases,
                '{0:s} must not inherit directly from ModernAdminContextMixin'.format(class_name),
            )


def run_tests():
    test_boundaries_exist_with_expected_parent()
    test_boundary_owned_decorators_stay_on_boundary()
    test_wrappers_use_expected_hybrid_boundary()
    test_isolated_wrappers_do_not_bypass_hybrid_boundaries()
    print('Modern admin boundary checks passed')


if __name__ == '__main__':
    run_tests()
