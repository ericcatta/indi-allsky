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
from indi_allsky.product_view_models import LatestFrameSummaryProvider
from indi_allsky.product_view_models import validate_now_view_payload


REQUIRED_NOW_KEYS = {
    'id',
    'label',
    'status',
    'briefing_title',
    'current_verdict',
    'data_status',
    'generated_at',
    'is_placeholder',
    'current_sky',
    'latest_frame_summary',
    'sky_cycle_briefing',
    'primary_question_answers',
    'evidence_summary',
    'science_context',
    'astrophoto_context',
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


class FakeLatestFrameRepository:
    def __init__(self, metadata=None, raises=False):
        self.metadata = metadata
        self.raises = raises

    def get_latest_frame_metadata(self):
        if self.raises:
            raise RuntimeError('fake repository failure')
        return self.metadata


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
    assert now_view['briefing_title'] == 'Current / Morning Briefing'
    assert now_view['current_verdict'] == 'Observation data not evaluated yet'
    assert_section_status(now_view['current_sky'])
    assert_section_status(now_view['latest_frame_summary'])
    assert_section_status(now_view['sky_cycle_briefing'])
    assert_section_status(now_view['evidence_summary'])
    assert_section_status(now_view['science_context'])
    assert_section_status(now_view['astrophoto_context'])

    for answer in now_view['primary_question_answers']:
        assert_section_status(answer)

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


def test_latest_frame_summary_contract_is_fake_safe():
    now_view = build_now_view()
    latest_frame = now_view['latest_frame_summary']

    assert latest_frame['status'] == 'No recent frame metadata available.'
    assert latest_frame['camera_label'] == 'Camera not evaluated yet'
    assert latest_frame['profile_label'] == 'Profile not evaluated yet'
    assert latest_frame['image_available'] is False
    assert latest_frame['safe_preview_url'] is None
    assert latest_frame['source_status'] == 'Source status not evaluated yet.'
    assert latest_frame['data_status'] == 'not_evaluated'


def test_latest_frame_provider_with_frame_present():
    provider = LatestFrameSummaryProvider(FakeLatestFrameRepository({
        'camera_label': 'North Sky Camera',
        'profile_label': 'Day/Night Primary',
        'timestamp': '2026-06-29 05:32:10',
        'age_label': '2 minutes ago',
        'image_available': True,
        'source_status': 'Metadata row available',
    }))
    latest_frame = provider.build()

    assert latest_frame['status'] == 'Latest frame metadata available.'
    assert latest_frame['camera_label'] == 'North Sky Camera'
    assert latest_frame['profile_label'] == 'Day/Night Primary'
    assert latest_frame['timestamp'] == '2026-06-29 05:32:10'
    assert latest_frame['age_label'] == '2 minutes ago'
    assert latest_frame['image_available'] is True
    assert latest_frame['safe_preview_url'] is None
    assert latest_frame['data_status'] == 'not_evaluated'
    validate_now_view_payload(dict(build_now_view(latest_frame_provider=provider)))


def test_latest_frame_provider_with_no_frame():
    provider = LatestFrameSummaryProvider(FakeLatestFrameRepository(None))
    latest_frame = provider.build()

    assert latest_frame['status'] == 'No recent frame metadata available.'
    assert latest_frame['image_available'] is False
    assert latest_frame['safe_preview_url'] is None
    assert latest_frame['data_status'] == 'not_evaluated'


def test_latest_frame_provider_with_missing_timestamp():
    provider = LatestFrameSummaryProvider(FakeLatestFrameRepository({
        'camera_label': 'North Sky Camera',
        'profile_label': 'Primary',
        'image_available': True,
        'source_status': 'Metadata row available',
    }))
    latest_frame = provider.build()

    assert latest_frame['timestamp'] == 'Not evaluated yet'
    assert latest_frame['age_label'] == 'Not evaluated yet'
    assert latest_frame['safe_preview_url'] is None


def test_latest_frame_provider_with_repository_error():
    provider = LatestFrameSummaryProvider(FakeLatestFrameRepository(raises=True))
    latest_frame = provider.build()

    assert latest_frame['status'] == 'Latest frame metadata unavailable.'
    assert latest_frame['source_status'] == 'Repository error.'
    assert latest_frame['safe_preview_url'] is None
    assert_no_sensitive_text(latest_frame)


def test_latest_frame_provider_rejects_suspicious_metadata():
    provider = LatestFrameSummaryProvider(FakeLatestFrameRepository({
        'camera_label': 'North Sky Camera',
        'profile_label': 'Primary',
        'timestamp': '2026-06-29 05:32:10',
        'age_label': '2 minutes ago',
        'image_available': True,
        'source_status': 'Metadata row available',
        'filename': '/var/lib/indi-allsky/latest.jpg',
    }))
    latest_frame = provider.build()

    assert latest_frame['status'] == 'Latest frame metadata rejected.'
    assert latest_frame['image_available'] is False
    assert latest_frame['safe_preview_url'] is None
    assert 'filename' not in json.dumps(latest_frame, sort_keys=True).lower()
    assert_no_absolute_paths(latest_frame)


def test_build_now_view_accepts_injected_latest_frame_provider():
    provider = LatestFrameSummaryProvider(FakeLatestFrameRepository({
        'camera_label': 'North Sky Camera',
        'profile_label': 'Primary',
        'timestamp': '2026-06-29 05:32:10',
        'age_label': '2 minutes ago',
        'image_available': True,
        'source_status': 'Metadata row available',
    }))
    now_view = build_now_view(latest_frame_provider=provider)

    assert now_view['latest_frame_summary']['camera_label'] == 'North Sky Camera'
    assert now_view['latest_frame_summary']['safe_preview_url'] is None
    json.dumps(now_view, sort_keys=True)


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


def test_validate_now_view_payload_rejects_latest_frame_absolute_preview_path():
    now_view = build_now_view()
    now_view['latest_frame_summary']['safe_preview_url'] = '/var/lib/indi-allsky/latest.jpg'

    try:
        validate_now_view_payload(now_view)
    except ValueError as e:
        assert 'safe_preview_url' in str(e)
    else:
        raise AssertionError('absolute latest frame preview path should fail validation')


def test_validate_now_view_payload_rejects_latest_frame_invalid_status():
    now_view = build_now_view()
    now_view['latest_frame_summary']['data_status'] = 'live_runtime'

    try:
        validate_now_view_payload(now_view)
    except ValueError as e:
        assert 'Invalid data_status' in str(e)
    else:
        raise AssertionError('latest_frame_summary invalid data_status should fail validation')


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
    assert 'filename' not in source


def main():
    tests = [
        test_build_now_view_returns_dict,
        test_build_now_view_is_json_serializable,
        test_build_now_view_has_explicit_placeholder_status,
        test_build_now_view_contains_no_sensitive_payload,
        test_latest_frame_summary_contract_is_fake_safe,
        test_latest_frame_provider_with_frame_present,
        test_latest_frame_provider_with_no_frame,
        test_latest_frame_provider_with_missing_timestamp,
        test_latest_frame_provider_with_repository_error,
        test_latest_frame_provider_rejects_suspicious_metadata,
        test_build_now_view_accepts_injected_latest_frame_provider,
        test_safe_actions_are_metadata_only,
        test_validate_now_view_payload_success,
        test_validate_now_view_payload_requires_sections,
        test_validate_now_view_payload_rejects_invalid_data_status,
        test_validate_now_view_payload_rejects_latest_frame_absolute_preview_path,
        test_validate_now_view_payload_rejects_latest_frame_invalid_status,
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
