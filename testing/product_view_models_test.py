#!/usr/bin/env python3

import copy
import inspect
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import indi_allsky.product_view_models as product_view_models
from indi_allsky.product_view_models import build_now_view
from indi_allsky.product_view_models import validate_now_view_payload


REQUIRED_NOW_KEYS = {
    'id',
    'label',
    'status',
    'data_status',
    'generated_at',
    'is_placeholder',
    'current_sky',
    'sky_cycle_briefing',
    'notable_moments',
    'generated_outputs',
    'observatory_health',
    'attention_items',
    'metadata',
}

REQUIRED_SECTION_KEYS = {
    'data_status',
    'is_placeholder',
}

SENSITIVE_PATTERNS = (
    'token',
    'secret',
    'password',
    'api_key',
    'apikey',
    'refresh_token',
    'client_secret',
)


def walk_payload(value):
    yield value
    if isinstance(value, dict):
        for key, item in value.items():
            yield key
            yield from walk_payload(item)
    elif isinstance(value, list):
        for item in value:
            yield from walk_payload(item)


def assert_no_callables(payload):
    for value in walk_payload(payload):
        assert not callable(value), 'NowView payload contains callable value'


def assert_no_sensitive_text(payload):
    payload_text = json.dumps(payload, sort_keys=True).lower()
    for pattern in SENSITIVE_PATTERNS:
        assert pattern not in payload_text


def assert_no_absolute_paths(payload):
    payload_text = json.dumps(payload, sort_keys=True)
    assert not re.search(r'(^|["\s:])/[A-Za-z0-9_.-]+/', payload_text)
    assert not re.search(r'[A-Za-z]:\\\\', payload_text)


def assert_section_status(section):
    assert isinstance(section, dict)
    assert REQUIRED_SECTION_KEYS.issubset(section.keys())
    assert section['data_status'] in {
        'placeholder',
        'not_evaluated',
        'future_backend_contract',
    }


def test_build_now_view_returns_dict():
    now_view = build_now_view()

    assert isinstance(now_view, dict)
    assert REQUIRED_NOW_KEYS.issubset(now_view.keys())


def test_build_now_view_is_json_serializable():
    now_view = build_now_view()
    json.dumps(now_view, sort_keys=True)


def test_build_now_view_has_explicit_placeholder_status():
    now_view = build_now_view()

    assert now_view['is_placeholder'] is True
    assert now_view['data_status'] == 'placeholder'
    assert_section_status(now_view['current_sky'])
    assert_section_status(now_view['sky_cycle_briefing'])

    for moment in now_view['notable_moments']:
        assert_section_status(moment)

    for output in now_view['generated_outputs']:
        assert_section_status(output)

    for health_item in now_view['observatory_health']:
        assert_section_status(health_item)

    for attention_item in now_view['attention_items']:
        assert_section_status(attention_item)


def test_build_now_view_contains_no_sensitive_payload():
    now_view = build_now_view()

    assert_no_sensitive_text(now_view)
    assert_no_absolute_paths(now_view)
    assert_no_callables(now_view)


def test_safe_actions_are_metadata_only():
    now_view = build_now_view()

    assert 'safe_actions_available' in now_view
    assert isinstance(now_view['safe_actions_available'], list)
    assert now_view['safe_actions_available'] == []


def test_validate_now_view_payload_success():
    assert validate_now_view_payload(build_now_view()) is True


def test_validate_now_view_payload_requires_sections():
    now_view = build_now_view()
    del now_view['current_sky']

    try:
        validate_now_view_payload(now_view)
    except ValueError as e:
        assert 'current_sky' in str(e)
    else:
        raise AssertionError('missing section should fail validation')


def test_validate_now_view_payload_rejects_invalid_data_status():
    now_view = build_now_view()
    now_view['current_sky']['data_status'] = 'live_runtime'

    try:
        validate_now_view_payload(now_view)
    except ValueError as e:
        assert 'Invalid data_status' in str(e)
    else:
        raise AssertionError('invalid data_status should fail validation')


def test_validate_now_view_payload_rejects_sensitive_keys():
    now_view = build_now_view()
    now_view['metadata']['api_token'] = 'do-not-render'

    try:
        validate_now_view_payload(now_view)
    except ValueError as e:
        assert 'Sensitive key' in str(e)
    else:
        raise AssertionError('sensitive key should fail validation')


def test_validate_now_view_payload_rejects_absolute_paths():
    now_view = build_now_view()
    now_view['metadata']['source_hint'] = '/var/lib/indi-allsky/image.fit'

    try:
        validate_now_view_payload(now_view)
    except ValueError as e:
        assert 'Absolute paths' in str(e)
    else:
        raise AssertionError('absolute path should fail validation')


def test_validate_now_view_payload_rejects_direct_safe_actions():
    now_view = build_now_view()
    now_view['safe_actions_available'] = [
        {
            'label': 'Do something',
            'url': 'modern-admin-action',
        },
    ]

    try:
        validate_now_view_payload(now_view)
    except ValueError as e:
        assert 'direct action' in str(e)
    else:
        raise AssertionError('direct safe action should fail validation')


def test_validate_now_view_payload_rejects_callables():
    now_view = copy.deepcopy(build_now_view())
    now_view['metadata']['callable'] = lambda: None

    try:
        validate_now_view_payload(now_view)
    except ValueError as e:
        assert 'Callable' in str(e)
    else:
        raise AssertionError('callable payload should fail validation')


def test_product_view_model_module_has_no_framework_or_db_imports():
    source = inspect.getsource(product_view_models).lower()

    assert 'from flask' not in source
    assert 'import flask' not in source
    assert 'db.session' not in source
    assert 'open(' not in source


def main():
    tests = [
        test_build_now_view_returns_dict,
        test_build_now_view_is_json_serializable,
        test_build_now_view_has_explicit_placeholder_status,
        test_build_now_view_contains_no_sensitive_payload,
        test_safe_actions_are_metadata_only,
        test_validate_now_view_payload_success,
        test_validate_now_view_payload_requires_sections,
        test_validate_now_view_payload_rejects_invalid_data_status,
        test_validate_now_view_payload_rejects_sensitive_keys,
        test_validate_now_view_payload_rejects_absolute_paths,
        test_validate_now_view_payload_rejects_direct_safe_actions,
        test_validate_now_view_payload_rejects_callables,
        test_product_view_model_module_has_no_framework_or_db_imports,
    ]

    for test in tests:
        test()

    print('product_view_models_test: ok ({0:d} tests)'.format(len(tests)))


if __name__ == '__main__':
    main()
