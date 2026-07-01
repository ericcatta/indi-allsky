#!/usr/bin/env python3

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from indi_allsky import product_view_models


REPO_ROOT = Path(__file__).resolve().parents[1]
VIEWS_PATH = REPO_ROOT / 'indi_allsky/flask/views.py'
TEMPLATE_ROOT = REPO_ROOT / 'indi_allsky/flask/templates/modern_admin'


PRODUCT_SPINE = (
    {
        'name': 'Now',
        'route': '/modern-admin/now',
        'endpoint': 'modern_admin_now_view',
        'view': 'ModernAdminNowView',
        'template': 'now.html',
        'builder': 'build_now_view',
        'validator': 'validate_now_view_payload',
    },
    {
        'name': 'Highlights',
        'route': '/modern-admin/highlights',
        'endpoint': 'modern_admin_highlights_view',
        'view': 'ModernAdminHighlightsView',
        'template': 'highlights.html',
        'builder': 'build_highlights_view',
        'validator': 'validate_highlights_payload',
    },
    {
        'name': 'Moment',
        'route': '/modern-admin/moment',
        'endpoint': 'modern_admin_moment_detail_view',
        'view': 'ModernAdminMomentDetailView',
        'template': 'moment_detail.html',
        'builder': 'build_moment_detail_view',
        'validator': 'validate_moment_detail_payload',
    },
    {
        'name': 'Output',
        'route': '/modern-admin/output',
        'endpoint': 'modern_admin_output_detail_view',
        'view': 'ModernAdminOutputDetailView',
        'template': 'output_detail.html',
        'builder': 'build_output_detail_view',
        'validator': 'validate_output_detail_payload',
    },
    {
        'name': 'Sky Cycle',
        'route': '/modern-admin/sky-cycle',
        'endpoint': 'modern_admin_sky_cycle_view',
        'view': 'ModernAdminSkyCycleView',
        'template': 'sky_cycle.html',
        'builder': 'build_sky_cycle_report_view',
        'validator': 'validate_sky_cycle_report_payload',
    },
    {
        'name': 'Library',
        'route': '/modern-admin/library',
        'endpoint': 'modern_admin_library_view',
        'view': 'ModernAdminLibraryView',
        'template': 'library.html',
        'builder': 'build_library_view',
        'validator': 'validate_library_payload',
    },
    {
        'name': 'Observatory',
        'route': '/modern-admin/observatory',
        'endpoint': 'modern_admin_observatory_view',
        'view': 'ModernAdminObservatoryView',
        'template': 'observatory.html',
        'builder': 'build_observatory_view',
        'validator': 'validate_observatory_payload',
    },
)


FORBIDDEN_TEMPLATE_PATTERNS = (
    (re.compile(r'<form\b', re.IGNORECASE), 'form element'),
    (re.compile(r'\bmethod\s*=\s*["\']?post', re.IGNORECASE), 'POST form method'),
    (re.compile(r'\bfetch\s*\(', re.IGNORECASE), 'fetch call'),
    (re.compile(r'\$\.ajax\s*\(', re.IGNORECASE), 'jQuery AJAX call'),
    (re.compile(r'/ajax/', re.IGNORECASE), 'legacy AJAX route'),
    (re.compile(r'/modern-admin/safe-action/', re.IGNORECASE), 'safe action route'),
)


def assert_true(condition, message):
    if not condition:
        raise AssertionError(message)


def read_text(path):
    return path.read_text(encoding='utf-8')


def test_product_routes_are_registered():
    views_text = read_text(VIEWS_PATH)

    assert_true(
        'class ModernAdminProductView(TemplateView):' in views_text,
        'Product views should have a dedicated Hybrid Product view boundary',
    )

    redirect_snippet = "return redirect(url_for('indi_allsky.modern_admin_now_view'))"
    assert_true(
        redirect_snippet in views_text,
        '/modern-admin entry should redirect to Now as the Product home',
    )

    for surface in PRODUCT_SPINE:
        class_pattern = 'class {0:s}(ModernAdminProductView):'.format(surface['view'])
        assert_true(
            class_pattern in views_text,
            '{0:s} must inherit from ModernAdminProductView'.format(surface['name']),
        )

        route = re.escape(surface['route'])
        view = re.escape(surface['view'])
        endpoint = re.escape(surface['endpoint'])
        template = re.escape('modern_admin/{0:s}'.format(surface['template']))
        pattern = re.compile(
            r"add_url_rule\('{route}',\s*view_func={view}\.as_view\('{endpoint}',\s*template_name='{template}'\)\)".format(
                route=route,
                view=view,
                endpoint=endpoint,
                template=template,
            )
        )
        assert_true(
            pattern.search(views_text),
            '{0:s} Product route registration is missing or changed'.format(surface['name']),
        )


def test_product_builders_return_valid_json_safe_payloads():
    for surface in PRODUCT_SPINE:
        builder = getattr(product_view_models, surface['builder'])
        validator = getattr(product_view_models, surface['validator'])

        payload = builder()
        assert_true(isinstance(payload, dict), '{0:s} builder must return dict'.format(surface['name']))
        validator(payload)
        json.dumps(payload, sort_keys=True)


def test_product_templates_are_server_rendered_and_read_only():
    for surface in PRODUCT_SPINE:
        template_path = TEMPLATE_ROOT / surface['template']
        assert_true(template_path.exists(), '{0:s} template is missing'.format(surface['name']))

        template_text = read_text(template_path)
        assert_true(
            re.search(r"{%\s*extends\s+['\"]base\.html['\"]\s*%}", template_text) is not None,
            '{0:s} template must use the Hybrid shell'.format(surface['name']),
        )

        for pattern, label in FORBIDDEN_TEMPLATE_PATTERNS:
            assert_true(
                not pattern.search(template_text),
                '{0:s} template contains forbidden {1:s}'.format(surface['name'], label),
            )


def run_tests():
    tests = (
        test_product_routes_are_registered,
        test_product_builders_return_valid_json_safe_payloads,
        test_product_templates_are_server_rendered_and_read_only,
    )

    for test in tests:
        test()

    print('Product spine regression checks passed')


if __name__ == '__main__':
    run_tests()
