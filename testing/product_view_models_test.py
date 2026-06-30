#!/usr/bin/env python3

import copy
from datetime import datetime
from datetime import timedelta
import inspect
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import indi_allsky.product_view_models as product_view_models
from indi_allsky.product_view_models import build_now_view
from indi_allsky.product_view_models import build_current_phase_summary
from indi_allsky.product_view_models import build_highlights_view
from indi_allsky.product_view_models import build_moment_detail_view
from indi_allsky.product_view_models import build_output_detail_view
from indi_allsky.product_view_models import build_library_view
from indi_allsky.product_view_models import build_observatory_view
from indi_allsky.product_view_models import build_sky_cycle_report_view
from indi_allsky.product_view_models import build_source_confidence_summary
from indi_allsky.product_view_models import LatestFrameImageTableRepository
from indi_allsky.product_view_models import LatestFrameSummaryProvider
from indi_allsky.product_view_models import validate_sky_cycle_report_payload
from indi_allsky.product_view_models import validate_highlights_payload
from indi_allsky.product_view_models import validate_moment_detail_payload
from indi_allsky.product_view_models import validate_now_view_payload
from indi_allsky.product_view_models import validate_output_detail_payload
from indi_allsky.product_view_models import validate_library_payload
from indi_allsky.product_view_models import validate_observatory_payload


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
    'current_phase_summary',
    'latest_frame_summary',
    'source_confidence_summary',
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

SKY_CYCLE_TEMPLATE = Path('indi_allsky/flask/templates/modern_admin/sky_cycle.html')
HIGHLIGHTS_TEMPLATE = Path('indi_allsky/flask/templates/modern_admin/highlights.html')
MOMENT_DETAIL_TEMPLATE = Path('indi_allsky/flask/templates/modern_admin/moment_detail.html')
OUTPUT_DETAIL_TEMPLATE = Path('indi_allsky/flask/templates/modern_admin/output_detail.html')
LIBRARY_TEMPLATE = Path('indi_allsky/flask/templates/modern_admin/library.html')
OBSERVATORY_TEMPLATE = Path('indi_allsky/flask/templates/modern_admin/observatory.html')

REQUIRED_SKY_CYCLE_KEYS = {
    'id',
    'label',
    'status',
    'data_status',
    'generated_at',
    'is_placeholder',
    'safe_actions_available',
    'cycle_summary',
    'phase_timeline',
    'moments_summary',
    'outputs_summary',
    'source_confidence_summary',
    'observatory_health_summary',
    'attention_items',
    'metadata',
}

REQUIRED_MOMENT_DETAIL_KEYS = {
    'id',
    'label',
    'status',
    'data_status',
    'generated_at',
    'is_placeholder',
    'safe_actions_available',
    'moment_summary',
    'evidence_summary',
    'source_trust_summary',
    'related_outputs',
    'sky_cycle_context',
    'observatory_context',
    'metadata',
}

REQUIRED_OUTPUT_DETAIL_KEYS = {
    'id',
    'label',
    'status',
    'data_status',
    'generated_at',
    'is_placeholder',
    'safe_actions_available',
    'output_summary',
    'preview_summary',
    'recipe_summary',
    'source_lineage_summary',
    'related_moments',
    'sky_cycle_context',
    'share_readiness_summary',
    'metadata',
}

REQUIRED_LIBRARY_KEYS = {
    'id',
    'label',
    'status',
    'data_status',
    'generated_at',
    'is_placeholder',
    'safe_actions_available',
    'library_summary',
    'collection_summary',
    'search_summary',
    'filter_summary',
    'recent_items',
    'memory_model_summary',
    'metadata',
}

REQUIRED_OBSERVATORY_KEYS = {
    'id',
    'label',
    'status',
    'data_status',
    'generated_at',
    'is_placeholder',
    'safe_actions_available',
    'observatory_summary',
    'camera_system_summary',
    'capture_pipeline_summary',
    'source_preservation_summary',
    'storage_summary',
    'generation_summary',
    'integration_summary',
    'attention_items',
    'metadata',
}


class FakeLatestFrameRepository:
    def __init__(self, metadata=None, raises=False):
        self.metadata = metadata
        self.raises = raises

    def get_latest_frame_metadata(self):
        if self.raises:
            raise RuntimeError('fake repository failure')
        return self.metadata


class FakeImageRow:
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)


class FakeImageQuery:
    def __init__(self, row=None, raises=False):
        self.row = row
        self.raises = raises
        self.order_by_calls = list()
        self.limit_calls = list()
        self.first_calls = 0

    def order_by(self, expression):
        self.order_by_calls.append(expression)
        return self

    def limit(self, value):
        self.limit_calls.append(value)
        return self

    def first(self):
        self.first_calls += 1
        if self.raises:
            raise RuntimeError('fake query failure')
        return self.row


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
    assert_section_status(now_view['current_phase_summary'])
    assert_section_status(now_view['latest_frame_summary'])
    assert_section_status(now_view['source_confidence_summary'])
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


def test_build_sky_cycle_report_view_returns_dict():
    report = build_sky_cycle_report_view()

    assert isinstance(report, dict)
    assert REQUIRED_SKY_CYCLE_KEYS.issubset(report.keys())
    assert report['metadata']['contract'] == 'SkyCycleReportView'


def test_build_sky_cycle_report_view_is_json_serializable():
    report = build_sky_cycle_report_view()
    json.dumps(report, sort_keys=True)


def test_build_sky_cycle_report_view_has_required_sections():
    report = build_sky_cycle_report_view()

    assert_section_status(report['cycle_summary'])
    assert_section_status(report['moments_summary'])
    assert_section_status(report['outputs_summary'])
    assert_section_status(report['source_confidence_summary'])
    assert_section_status(report['observatory_health_summary'])
    assert_section_status(report['attention_items'])
    assert isinstance(report['phase_timeline'], list)
    assert [phase['phase'] for phase in report['phase_timeline']] == [
        'day',
        'sunset_twilight',
        'night',
        'sunrise_twilight',
    ]

    for phase in report['phase_timeline']:
        assert_section_status(phase)
        assert isinstance(phase['supported'], bool)
        assert 'observation_value' in phase
        assert 'source_expectation' in phase
        assert 'output_expectation' in phase
        assert 'science_note' in phase
        assert 'astrophoto_note' in phase
        assert 'unsupported_reason' in phase

    twilight_phases = [
        phase for phase in report['phase_timeline']
        if phase['phase'] in ('sunset_twilight', 'sunrise_twilight')
    ]
    assert len(twilight_phases) == 2
    for phase in twilight_phases:
        assert phase['supported'] is False
        assert phase['data_status'] == 'future_backend_contract'
        assert 'No phase engine' in phase['unsupported_reason']

    moments_summary = report['moments_summary']
    assert moments_summary['count_label'] == 'No moments evaluated yet'
    assert moments_summary['primary_moment'] == 'No primary moment selected'
    assert moments_summary['detection_status'] == 'Detector evidence pending backend contract.'
    assert moments_summary['review_queue_status'] == 'Review queue not evaluated yet.'
    assert isinstance(moments_summary['moment_categories'], list)
    assert isinstance(moments_summary['items'], list)
    assert len(moments_summary['items']) >= 3

    for moment in moments_summary['items']:
        assert_section_status(moment)
        assert moment['type'] in {
            'meteor',
            'aurora',
            'lightning',
            'storm',
            'clouds',
            'clear_window',
            'sunrise',
            'sunset',
            'moon',
            'sky_quality',
            'camera_anomaly',
            'generation_issue',
            'unknown',
        }
        assert moment['phase'] in {'day', 'sunset_twilight', 'night', 'sunrise_twilight', 'unknown'}
        assert isinstance(moment['evidence'], list)
        assert 'source_lineage_status' in moment
        assert 'related_outputs_status' in moment
        assert 'science_note' in moment
        assert 'astrophoto_note' in moment
        assert 'review_status' in moment

    outputs_summary = report['outputs_summary']
    assert outputs_summary['count_label'] == 'No generated outputs evaluated yet'
    assert outputs_summary['generation_status'] == 'Rendering/generation status not connected yet.'
    assert outputs_summary['look_policy_status'] == 'Look policy not connected yet.'
    assert outputs_summary['share_readiness_status'] == 'Share readiness not evaluated yet.'
    assert isinstance(outputs_summary['items'], list)
    assert len(outputs_summary['items']) >= 5

    for output in outputs_summary['items']:
        assert_section_status(output)
        assert output['type'] in {
            'best_image',
            'latest_image',
            'timelapse',
            'day_timelapse',
            'night_timelapse',
            'keogram',
            'startrail',
            'startrail_video',
            'storm_highlight',
            'aurora_highlight',
            'meteor_highlight',
            'cycle_summary_video',
            'unknown',
        }
        assert output['phase'] in {'day', 'sunset_twilight', 'night', 'sunrise_twilight', 'unknown'}
        assert 'generation_status' in output
        assert 'look_applied' in output
        assert 'source_lineage_status' in output
        assert 'related_moments_status' in output
        assert 'share_status' in output
        assert 'quality_note' in output
        assert 'astrophoto_note' in output
        assert 'science_note' in output
        assert output['safe_actions_available'] == []

    source_confidence = report['source_confidence_summary']
    assert source_confidence['confidence_label'] == 'Pending source coverage contract'
    assert source_confidence['coverage_label'] == 'Not evaluated yet'
    assert isinstance(source_confidence['source_types'], list)
    assert 'image metadata' in source_confidence['source_types']
    assert 'source files' in source_confidence['source_types']
    assert 'preservation_status' in source_confidence
    assert 'retention_status' in source_confidence
    assert 'lineage_status' in source_confidence
    assert 'gap_status' in source_confidence
    assert source_confidence['risk_level'] == 'unknown'
    assert isinstance(source_confidence['evidence'], list)

    health_summary = report['observatory_health_summary']
    assert health_summary['overall_label'] == 'Health not evaluated yet'
    assert health_summary['camera_status'] == 'Camera status not evaluated here.'
    assert health_summary['capture_status'] == 'Capture continuity not evaluated here.'
    assert health_summary['storage_status'] == 'Storage status not evaluated here.'
    assert health_summary['generation_status'] == 'Generation status not evaluated here.'
    assert health_summary['integration_status'] == 'Upload/integration status not evaluated here.'
    assert health_summary['warnings_count_label'] == 'Warnings not evaluated yet'
    assert health_summary['risk_level'] == 'unknown'
    assert isinstance(health_summary['evidence'], list)


def test_build_sky_cycle_report_view_contains_no_sensitive_payload():
    report = build_sky_cycle_report_view()

    assert_no_sensitive_text(report)
    assert_no_absolute_paths(report)
    assert_no_callables(report)


def test_build_highlights_view_returns_dict():
    highlights = build_highlights_view()

    assert isinstance(highlights, dict)
    assert highlights['id'] == 'highlights.placeholder'
    assert highlights['metadata']['contract'] == 'HighlightsView'


def test_build_highlights_view_is_json_serializable():
    highlights = build_highlights_view()

    json.dumps(highlights, sort_keys=True)


def test_build_highlights_view_has_required_sections():
    highlights = build_highlights_view()

    assert_section_status(highlights['highlights_summary'])
    assert_section_status(highlights['source_trust_summary'])
    assert_section_status(highlights['review_queue_summary'])
    assert_section_status(highlights['selection_policy_summary'])
    assert_section_status(highlights['attention_items'])
    assert isinstance(highlights['highlight_items'], list)
    assert len(highlights['highlight_items']) >= 4

    for item in highlights['highlight_items']:
        assert item['type'] in {
            'best_image',
            'meteor_candidate',
            'aurora_candidate',
            'lightning_candidate',
            'clear_window',
            'storm_activity',
            'sky_quality',
            'generated_output',
            'observatory_issue',
            'user_selected',
            'unknown',
        }
        assert item['target_kind'] in {
            'moment',
            'output',
            'source',
            'sky_cycle',
            'observatory_issue',
            'unknown',
        }
        assert item['origin'] in {
            'hybrid_suggested',
            'user_selected',
            'future_ai',
            'detector',
            'rule',
            'unknown',
        }
        assert isinstance(item['evidence'], list)
        assert item['safe_actions_available'] == []

    assert highlights['source_trust_summary']['risk_level'] == 'unknown'
    assert isinstance(highlights['source_trust_summary']['evidence'], list)
    assert isinstance(highlights['selection_policy_summary']['allowed_origins'], list)


def test_build_highlights_view_contains_no_sensitive_payload():
    highlights = build_highlights_view()

    assert_no_sensitive_text(highlights)
    assert_no_absolute_paths(highlights)
    assert_no_callables(highlights)


def test_validate_highlights_payload_success():
    assert validate_highlights_payload(build_highlights_view()) is True


def test_validate_highlights_payload_requires_sections():
    highlights = build_highlights_view()
    del highlights['highlights_summary']

    try:
        validate_highlights_payload(highlights)
    except ValueError as e:
        assert 'missing required keys' in str(e)
    else:
        raise AssertionError('missing highlights_summary should fail validation')


def test_validate_highlights_payload_rejects_invalid_type():
    highlights = build_highlights_view()
    highlights['highlight_items'][0]['type'] = 'meteor_download'

    try:
        validate_highlights_payload(highlights)
    except ValueError as e:
        assert 'Invalid Highlight type' in str(e)
    else:
        raise AssertionError('invalid Highlight type should fail validation')


def test_validate_highlights_payload_rejects_invalid_target_kind():
    highlights = build_highlights_view()
    highlights['highlight_items'][0]['target_kind'] = 'route'

    try:
        validate_highlights_payload(highlights)
    except ValueError as e:
        assert 'Invalid Highlight target_kind' in str(e)
    else:
        raise AssertionError('invalid Highlight target_kind should fail validation')


def test_validate_highlights_payload_rejects_invalid_origin():
    highlights = build_highlights_view()
    highlights['highlight_items'][0]['origin'] = 'crawler'

    try:
        validate_highlights_payload(highlights)
    except ValueError as e:
        assert 'Invalid Highlight origin' in str(e)
    else:
        raise AssertionError('invalid Highlight origin should fail validation')


def test_validate_highlights_payload_rejects_evidence_not_list():
    highlights = build_highlights_view()
    highlights['highlight_items'][0]['evidence'] = 'Detector evidence pending'

    try:
        validate_highlights_payload(highlights)
    except ValueError as e:
        assert 'evidence must be a list' in str(e)
    else:
        raise AssertionError('Highlight evidence string should fail validation')


def test_validate_highlights_payload_rejects_direct_safe_action():
    highlights = build_highlights_view()
    highlights['highlight_items'][0]['safe_actions_available'] = [
        {
            'label': 'Confirm Highlight',
            'url': '/modern-admin/highlights/action',
        },
    ]

    try:
        validate_highlights_payload(highlights)
    except ValueError as e:
        assert 'direct action' in str(e)
    else:
        raise AssertionError('direct Highlight safe action should fail validation')


def test_validate_highlights_payload_rejects_path_secret_callable():
    highlights = build_highlights_view()
    highlights['highlight_items'][0]['evidence'].append('/var/lib/indi-allsky/source')

    try:
        validate_highlights_payload(highlights)
    except ValueError as e:
        assert 'Absolute paths' in str(e)
    else:
        raise AssertionError('Highlight absolute path should fail validation')

    highlights = build_highlights_view()
    highlights['source_trust_summary']['evidence'].append({'token': 'value'})

    try:
        validate_highlights_payload(highlights)
    except ValueError as e:
        assert 'Sensitive key' in str(e)
    else:
        raise AssertionError('Highlight secret should fail validation')

    highlights = build_highlights_view()
    highlights['highlight_items'][0]['evidence'].append(lambda: None)

    try:
        validate_highlights_payload(highlights)
    except ValueError as e:
        assert 'Callable' in str(e)
    else:
        raise AssertionError('Highlight callable should fail validation')


def test_highlights_template_has_no_mutative_controls():
    template_text = HIGHLIGHTS_TEMPLATE.read_text(encoding='utf-8').lower()

    assert '<form' not in template_text
    assert 'post' not in template_text
    assert 'fetch' not in template_text
    assert '/ajax/' not in template_text


def test_build_moment_detail_view_returns_dict():
    moment = build_moment_detail_view()

    assert isinstance(moment, dict)
    assert REQUIRED_MOMENT_DETAIL_KEYS.issubset(moment.keys())
    assert moment['id'] == 'moment_detail.placeholder'
    assert moment['metadata']['contract'] == 'MomentDetailView'


def test_build_moment_detail_view_is_json_serializable():
    moment = build_moment_detail_view()

    json.dumps(moment, sort_keys=True)


def test_build_moment_detail_view_has_required_sections():
    moment = build_moment_detail_view()

    assert_section_status(moment['moment_summary'])
    assert_section_status(moment['evidence_summary'])
    assert_section_status(moment['source_trust_summary'])
    assert_section_status(moment['related_outputs'])
    assert_section_status(moment['sky_cycle_context'])
    assert_section_status(moment['observatory_context'])

    assert moment['moment_summary']['type'] in {
        'meteor_candidate',
        'aurora_candidate',
        'lightning_candidate',
        'storm_activity',
        'clouds',
        'clear_window',
        'sunrise',
        'sunset',
        'moon',
        'sky_quality',
        'camera_anomaly',
        'generation_issue',
        'unknown',
    }
    assert moment['moment_summary']['phase'] in {
        'day',
        'sunset_twilight',
        'night',
        'sunrise_twilight',
        'unknown',
    }
    assert isinstance(moment['evidence_summary']['evidence'], list)
    assert isinstance(moment['related_outputs']['outputs'], list)
    for output in moment['related_outputs']['outputs']:
        assert output['type'] in {
            'best_image',
            'latest_image',
            'timelapse',
            'keogram',
            'startrail',
            'highlight_clip',
            'unknown',
        }


def test_build_moment_detail_view_contains_no_sensitive_payload():
    moment = build_moment_detail_view()

    assert_no_sensitive_text(moment)
    assert_no_absolute_paths(moment)
    assert_no_callables(moment)


def test_validate_moment_detail_payload_success():
    assert validate_moment_detail_payload(build_moment_detail_view()) is True


def test_validate_moment_detail_payload_requires_sections():
    moment = build_moment_detail_view()
    del moment['moment_summary']

    try:
        validate_moment_detail_payload(moment)
    except ValueError as e:
        assert 'missing required keys' in str(e)
    else:
        raise AssertionError('missing moment_summary should fail validation')


def test_validate_moment_detail_payload_rejects_invalid_type():
    moment = build_moment_detail_view()
    moment['moment_summary']['type'] = 'gallery_item'

    try:
        validate_moment_detail_payload(moment)
    except ValueError as e:
        assert 'Invalid Moment type' in str(e)
    else:
        raise AssertionError('invalid Moment type should fail validation')


def test_validate_moment_detail_payload_rejects_invalid_phase():
    moment = build_moment_detail_view()
    moment['moment_summary']['phase'] = 'golden_hour'

    try:
        validate_moment_detail_payload(moment)
    except ValueError as e:
        assert 'Invalid Moment phase' in str(e)
    else:
        raise AssertionError('invalid Moment phase should fail validation')


def test_validate_moment_detail_payload_rejects_evidence_not_list():
    moment = build_moment_detail_view()
    moment['evidence_summary']['evidence'] = 'Detector evidence pending'

    try:
        validate_moment_detail_payload(moment)
    except ValueError as e:
        assert 'evidence must be a list' in str(e)
    else:
        raise AssertionError('Moment evidence string should fail validation')


def test_validate_moment_detail_payload_rejects_invalid_output_type():
    moment = build_moment_detail_view()
    moment['related_outputs']['outputs'][0]['type'] = 'share_card'

    try:
        validate_moment_detail_payload(moment)
    except ValueError as e:
        assert 'Invalid related output type' in str(e)
    else:
        raise AssertionError('invalid related output type should fail validation')


def test_validate_moment_detail_payload_rejects_output_not_list():
    moment = build_moment_detail_view()
    moment['related_outputs']['outputs'] = 'No output connected'

    try:
        validate_moment_detail_payload(moment)
    except ValueError as e:
        assert 'outputs must be a list' in str(e)
    else:
        raise AssertionError('Moment output string should fail validation')


def test_validate_moment_detail_payload_rejects_path_secret_callable():
    moment = build_moment_detail_view()
    moment['evidence_summary']['evidence'].append('/var/lib/indi-allsky/source.fit')

    try:
        validate_moment_detail_payload(moment)
    except ValueError as e:
        assert 'Absolute paths' in str(e)
    else:
        raise AssertionError('Moment evidence path should fail validation')

    moment = build_moment_detail_view()
    moment['source_trust_summary']['note'] = {'secret': 'value'}

    try:
        validate_moment_detail_payload(moment)
    except ValueError as e:
        assert 'Sensitive key' in str(e)
    else:
        raise AssertionError('Moment secret should fail validation')

    moment = build_moment_detail_view()
    moment['observatory_context']['note'] = lambda: None

    try:
        validate_moment_detail_payload(moment)
    except ValueError as e:
        assert 'Callable' in str(e)
    else:
        raise AssertionError('Moment callable should fail validation')


def test_moment_detail_template_has_no_mutative_controls():
    template_text = MOMENT_DETAIL_TEMPLATE.read_text(encoding='utf-8').lower()

    assert '<form' not in template_text
    assert 'post' not in template_text
    assert 'fetch' not in template_text
    assert '/ajax/' not in template_text


def test_build_output_detail_view_returns_dict():
    output = build_output_detail_view()

    assert isinstance(output, dict)
    assert REQUIRED_OUTPUT_DETAIL_KEYS.issubset(output.keys())
    assert output['id'] == 'output_detail.placeholder'
    assert output['metadata']['contract'] == 'OutputDetailView'


def test_build_output_detail_view_is_json_serializable():
    output = build_output_detail_view()

    json.dumps(output, sort_keys=True)


def test_build_output_detail_view_has_required_sections():
    output = build_output_detail_view()

    assert_section_status(output['output_summary'])
    assert_section_status(output['preview_summary'])
    assert_section_status(output['recipe_summary'])
    assert_section_status(output['source_lineage_summary'])
    assert_section_status(output['related_moments'])
    assert_section_status(output['sky_cycle_context'])
    assert_section_status(output['share_readiness_summary'])

    assert output['output_summary']['type'] in {
        'best_image',
        'latest_image',
        'timelapse',
        'day_timelapse',
        'night_timelapse',
        'keogram',
        'startrail',
        'startrail_video',
        'storm_highlight',
        'aurora_highlight',
        'meteor_highlight',
        'cycle_summary_video',
        'unknown',
    }
    assert output['output_summary']['phase'] in {
        'day',
        'sunset_twilight',
        'night',
        'sunrise_twilight',
        'unknown',
    }
    assert output['preview_summary']['safe_preview_url'] is None
    assert output['preview_summary']['preview_available'] is False
    assert output['source_lineage_summary']['trust_level'] in {'unknown', 'low', 'medium', 'high'}
    assert isinstance(output['source_lineage_summary']['source_types'], list)
    assert isinstance(output['source_lineage_summary']['evidence'], list)
    assert isinstance(output['related_moments']['items'], list)
    assert isinstance(output['share_readiness_summary']['limitations'], list)
    assert output['share_readiness_summary']['safe_actions_available'] == []


def test_build_output_detail_view_contains_no_sensitive_payload():
    output = build_output_detail_view()

    assert_no_sensitive_text(output)
    assert_no_absolute_paths(output)
    assert_no_callables(output)


def test_validate_output_detail_payload_success():
    assert validate_output_detail_payload(build_output_detail_view()) is True


def test_validate_output_detail_payload_requires_sections():
    output = build_output_detail_view()
    del output['output_summary']

    try:
        validate_output_detail_payload(output)
    except ValueError as e:
        assert 'missing required keys' in str(e)
    else:
        raise AssertionError('missing output_summary should fail validation')


def test_validate_output_detail_payload_rejects_invalid_type():
    output = build_output_detail_view()
    output['output_summary']['type'] = 'gallery_card'

    try:
        validate_output_detail_payload(output)
    except ValueError as e:
        assert 'Invalid output type' in str(e)
    else:
        raise AssertionError('invalid output type should fail validation')


def test_validate_output_detail_payload_rejects_invalid_trust_level():
    output = build_output_detail_view()
    output['source_lineage_summary']['trust_level'] = 'certain'

    try:
        validate_output_detail_payload(output)
    except ValueError as e:
        assert 'Invalid trust_level' in str(e)
    else:
        raise AssertionError('invalid trust level should fail validation')


def test_validate_output_detail_payload_rejects_evidence_not_list():
    output = build_output_detail_view()
    output['source_lineage_summary']['evidence'] = 'Source lineage pending'

    try:
        validate_output_detail_payload(output)
    except ValueError as e:
        assert 'evidence must be a list' in str(e)
    else:
        raise AssertionError('Output evidence string should fail validation')


def test_validate_output_detail_payload_rejects_direct_safe_action():
    output = build_output_detail_view()
    output['share_readiness_summary']['safe_actions_available'] = [
        {
            'label': 'Regenerate',
            'url': '/modern-admin/output/action',
        },
    ]

    try:
        validate_output_detail_payload(output)
    except ValueError as e:
        assert 'direct action' in str(e)
    else:
        raise AssertionError('direct output action should fail validation')


def test_validate_output_detail_payload_rejects_path_secret_callable():
    output = build_output_detail_view()
    output['preview_summary']['safe_preview_url'] = '/var/lib/indi-allsky/output.jpg'

    try:
        validate_output_detail_payload(output)
    except ValueError as e:
        assert 'absolute path' in str(e).lower() or 'Absolute paths' in str(e)
    else:
        raise AssertionError('Output preview path should fail validation')

    output = build_output_detail_view()
    output['source_lineage_summary']['evidence'].append({'token': 'value'})

    try:
        validate_output_detail_payload(output)
    except ValueError as e:
        assert 'Sensitive key' in str(e)
    else:
        raise AssertionError('Output secret should fail validation')

    output = build_output_detail_view()
    output['recipe_summary']['note'] = lambda: None

    try:
        validate_output_detail_payload(output)
    except ValueError as e:
        assert 'Callable' in str(e)
    else:
        raise AssertionError('Output callable should fail validation')


def test_output_detail_template_has_no_mutative_controls():
    template_text = OUTPUT_DETAIL_TEMPLATE.read_text(encoding='utf-8').lower()

    assert '<form' not in template_text
    assert 'post' not in template_text
    assert 'fetch' not in template_text
    assert '/ajax/' not in template_text


def test_build_library_view_returns_dict():
    library = build_library_view()

    assert isinstance(library, dict)
    assert REQUIRED_LIBRARY_KEYS.issubset(library.keys())
    assert library['id'] == 'library.placeholder'
    assert library['metadata']['contract'] == 'LibraryView'


def test_build_library_view_is_json_serializable():
    library = build_library_view()

    json.dumps(library, sort_keys=True)


def test_build_library_view_has_required_sections():
    library = build_library_view()

    assert_section_status(library['library_summary'])
    assert_section_status(library['collection_summary'])
    assert_section_status(library['search_summary'])
    assert_section_status(library['filter_summary'])
    assert_section_status(library['recent_items'])
    assert_section_status(library['memory_model_summary'])

    assert isinstance(library['collection_summary']['collections'], list)
    assert len(library['collection_summary']['collections']) >= 5
    for collection in library['collection_summary']['collections']:
        assert collection['type'] in {
            'highlights',
            'moments',
            'outputs',
            'sky_cycles',
            'favorites',
            'source_backed',
            'phenomena',
            'unknown',
        }

    assert isinstance(library['search_summary']['indexed_fields'], list)
    assert isinstance(library['filter_summary']['available_filters'], list)
    assert isinstance(library['filter_summary']['disabled_filters'], list)
    assert isinstance(library['recent_items']['items'], list)
    for item in library['recent_items']['items']:
        assert item['kind'] in {
            'highlight',
            'moment',
            'output',
            'sky_cycle',
            'source',
            'favorite',
            'unknown',
        }
        assert item['phase'] in {
            'day',
            'sunset_twilight',
            'night',
            'sunrise_twilight',
            'unknown',
        }


def test_build_library_view_contains_no_sensitive_payload():
    library = build_library_view()

    assert_no_sensitive_text(library)
    assert_no_absolute_paths(library)
    assert_no_callables(library)


def test_validate_library_payload_success():
    assert validate_library_payload(build_library_view()) is True


def test_validate_library_payload_requires_sections():
    library = build_library_view()
    del library['library_summary']

    try:
        validate_library_payload(library)
    except ValueError as e:
        assert 'missing required keys' in str(e)
    else:
        raise AssertionError('missing library_summary should fail validation')


def test_validate_library_payload_rejects_invalid_kind():
    library = build_library_view()
    library['recent_items']['items'][0]['kind'] = 'gallery'

    try:
        validate_library_payload(library)
    except ValueError as e:
        assert 'Invalid Library item kind' in str(e)
    else:
        raise AssertionError('invalid Library item kind should fail validation')


def test_validate_library_payload_rejects_invalid_collection_type():
    library = build_library_view()
    library['collection_summary']['collections'][0]['type'] = 'albums'

    try:
        validate_library_payload(library)
    except ValueError as e:
        assert 'Invalid collection type' in str(e)
    else:
        raise AssertionError('invalid Library collection type should fail validation')


def test_validate_library_payload_rejects_indexed_fields_not_list():
    library = build_library_view()
    library['search_summary']['indexed_fields'] = 'kind,date'

    try:
        validate_library_payload(library)
    except ValueError as e:
        assert 'indexed_fields must be a list' in str(e)
    else:
        raise AssertionError('Library indexed_fields string should fail validation')


def test_validate_library_payload_rejects_path_secret_callable():
    library = build_library_view()
    library['recent_items']['items'][0]['note'] = '/var/lib/indi-allsky/archive'

    try:
        validate_library_payload(library)
    except ValueError as e:
        assert 'Absolute paths' in str(e)
    else:
        raise AssertionError('Library path should fail validation')

    library = build_library_view()
    library['search_summary']['note'] = {'password': 'value'}

    try:
        validate_library_payload(library)
    except ValueError as e:
        assert 'Sensitive key' in str(e)
    else:
        raise AssertionError('Library secret should fail validation')

    library = build_library_view()
    library['memory_model_summary']['explanation'] = lambda: None

    try:
        validate_library_payload(library)
    except ValueError as e:
        assert 'Callable' in str(e)
    else:
        raise AssertionError('Library callable should fail validation')


def test_library_template_has_no_mutative_controls():
    template_text = LIBRARY_TEMPLATE.read_text(encoding='utf-8').lower()

    assert '<form' not in template_text
    assert 'post' not in template_text
    assert 'fetch' not in template_text
    assert '/ajax/' not in template_text


def test_build_observatory_view_returns_dict():
    observatory = build_observatory_view()

    assert isinstance(observatory, dict)
    assert REQUIRED_OBSERVATORY_KEYS.issubset(observatory.keys())
    assert observatory['id'] == 'observatory.placeholder'
    assert observatory['metadata']['contract'] == 'ObservatoryView'


def test_build_observatory_view_is_json_serializable():
    observatory = build_observatory_view()

    json.dumps(observatory, sort_keys=True)


def test_build_observatory_view_has_required_sections():
    observatory = build_observatory_view()

    assert_section_status(observatory['observatory_summary'])
    assert_section_status(observatory['camera_system_summary'])
    assert_section_status(observatory['capture_pipeline_summary'])
    assert_section_status(observatory['source_preservation_summary'])
    assert_section_status(observatory['storage_summary'])
    assert_section_status(observatory['generation_summary'])
    assert_section_status(observatory['integration_summary'])
    assert_section_status(observatory['attention_items'])

    allowed_statuses = {'ok', 'warning', 'blocked', 'not_evaluated', 'unknown'}
    assert observatory['observatory_summary']['overall_status'] in allowed_statuses
    assert observatory['camera_system_summary']['status'] in allowed_statuses
    assert observatory['capture_pipeline_summary']['status'] in allowed_statuses
    assert observatory['source_preservation_summary']['status'] in allowed_statuses
    assert observatory['storage_summary']['status'] in allowed_statuses
    assert observatory['generation_summary']['status'] in allowed_statuses
    assert observatory['integration_summary']['status'] in allowed_statuses
    assert observatory['source_preservation_summary']['trust_level'] in {'unknown', 'low', 'medium', 'high'}
    assert observatory['storage_summary']['risk_level'] in {'unknown', 'low', 'medium', 'high'}
    assert isinstance(observatory['attention_items']['items'], list)


def test_build_observatory_view_contains_no_sensitive_payload():
    observatory = build_observatory_view()

    assert_no_sensitive_text(observatory)
    assert_no_absolute_paths(observatory)
    assert_no_callables(observatory)


def test_validate_observatory_payload_success():
    assert validate_observatory_payload(build_observatory_view()) is True


def test_validate_observatory_payload_requires_sections():
    observatory = build_observatory_view()
    del observatory['observatory_summary']

    try:
        validate_observatory_payload(observatory)
    except ValueError as e:
        assert 'missing required keys' in str(e)
    else:
        raise AssertionError('missing observatory_summary should fail validation')


def test_validate_observatory_payload_rejects_invalid_status():
    observatory = build_observatory_view()
    observatory['camera_system_summary']['status'] = 'online'

    try:
        validate_observatory_payload(observatory)
    except ValueError as e:
        assert 'Invalid Observatory status' in str(e)
    else:
        raise AssertionError('invalid Observatory status should fail validation')


def test_validate_observatory_payload_rejects_invalid_trust_or_risk():
    observatory = build_observatory_view()
    observatory['source_preservation_summary']['trust_level'] = 'certain'

    try:
        validate_observatory_payload(observatory)
    except ValueError as e:
        assert 'Invalid risk_level' in str(e)
    else:
        raise AssertionError('invalid Observatory trust should fail validation')

    observatory = build_observatory_view()
    observatory['storage_summary']['risk_level'] = 'critical'

    try:
        validate_observatory_payload(observatory)
    except ValueError as e:
        assert 'Invalid risk_level' in str(e)
    else:
        raise AssertionError('invalid Observatory risk should fail validation')


def test_validate_observatory_payload_rejects_attention_items_not_list():
    observatory = build_observatory_view()
    observatory['attention_items']['items'] = 'No attention items'

    try:
        validate_observatory_payload(observatory)
    except ValueError as e:
        assert 'items must be a list' in str(e)
    else:
        raise AssertionError('Observatory attention items string should fail validation')


def test_validate_observatory_payload_rejects_path_secret_callable():
    observatory = build_observatory_view()
    observatory['storage_summary']['note'] = '/var/lib/indi-allsky/storage'

    try:
        validate_observatory_payload(observatory)
    except ValueError as e:
        assert 'Absolute paths' in str(e)
    else:
        raise AssertionError('Observatory path should fail validation')

    observatory = build_observatory_view()
    observatory['integration_summary']['note'] = {'token': 'value'}

    try:
        validate_observatory_payload(observatory)
    except ValueError as e:
        assert 'Sensitive key' in str(e)
    else:
        raise AssertionError('Observatory secret should fail validation')

    observatory = build_observatory_view()
    observatory['generation_summary']['note'] = lambda: None

    try:
        validate_observatory_payload(observatory)
    except ValueError as e:
        assert 'Callable' in str(e)
    else:
        raise AssertionError('Observatory callable should fail validation')


def test_observatory_template_has_no_mutative_controls():
    template_text = OBSERVATORY_TEMPLATE.read_text(encoding='utf-8').lower()

    assert '<form' not in template_text
    assert 'post' not in template_text
    assert 'fetch' not in template_text
    assert '/ajax/' not in template_text


def test_validate_sky_cycle_report_payload_success():
    assert validate_sky_cycle_report_payload(build_sky_cycle_report_view()) is True


def test_validate_sky_cycle_report_payload_requires_sections():
    report = build_sky_cycle_report_view()
    del report['cycle_summary']

    try:
        validate_sky_cycle_report_payload(report)
    except ValueError as e:
        assert 'cycle_summary' in str(e)
    else:
        raise AssertionError('missing sky cycle section should fail validation')


def test_validate_sky_cycle_report_payload_rejects_invalid_status():
    report = build_sky_cycle_report_view()
    report['cycle_summary']['data_status'] = 'live_runtime'

    try:
        validate_sky_cycle_report_payload(report)
    except ValueError as e:
        assert 'Invalid data_status' in str(e)
    else:
        raise AssertionError('invalid sky cycle status should fail validation')


def test_validate_sky_cycle_report_payload_rejects_invalid_phase():
    report = build_sky_cycle_report_view()
    report['phase_timeline'][0]['phase'] = 'storm_window'

    try:
        validate_sky_cycle_report_payload(report)
    except ValueError as e:
        assert 'Invalid phase' in str(e)
    else:
        raise AssertionError('invalid sky cycle phase should fail validation')


def test_validate_sky_cycle_report_payload_rejects_incomplete_phase_item():
    report = build_sky_cycle_report_view()
    del report['phase_timeline'][0]['observation_value']

    try:
        validate_sky_cycle_report_payload(report)
    except ValueError as e:
        assert 'missing required keys' in str(e)
    else:
        raise AssertionError('incomplete sky cycle phase should fail validation')


def test_validate_sky_cycle_report_payload_rejects_non_boolean_supported():
    report = build_sky_cycle_report_view()
    report['phase_timeline'][0]['supported'] = 'yes'

    try:
        validate_sky_cycle_report_payload(report)
    except ValueError as e:
        assert 'supported must be a boolean' in str(e)
    else:
        raise AssertionError('non-boolean sky cycle supported flag should fail validation')


def test_validate_sky_cycle_report_payload_rejects_invalid_moment_type():
    report = build_sky_cycle_report_view()
    report['moments_summary']['items'][0]['type'] = 'airplane'

    try:
        validate_sky_cycle_report_payload(report)
    except ValueError as e:
        assert 'Invalid moment type' in str(e)
    else:
        raise AssertionError('invalid moment type should fail validation')


def test_validate_sky_cycle_report_payload_rejects_moment_evidence_not_list():
    report = build_sky_cycle_report_view()
    report['moments_summary']['items'][0]['evidence'] = 'detector evidence pending'

    try:
        validate_sky_cycle_report_payload(report)
    except ValueError as e:
        assert 'evidence must be a list' in str(e)
    else:
        raise AssertionError('moment evidence string should fail validation')


def test_validate_sky_cycle_report_payload_rejects_incomplete_moment_item():
    report = build_sky_cycle_report_view()
    del report['moments_summary']['items'][0]['source_lineage_status']

    try:
        validate_sky_cycle_report_payload(report)
    except ValueError as e:
        assert 'missing required keys' in str(e)
    else:
        raise AssertionError('incomplete moment item should fail validation')


def test_validate_sky_cycle_report_payload_rejects_moment_path_secret_callable():
    report = build_sky_cycle_report_view()
    report['moments_summary']['items'][0]['evidence'].append('/var/lib/indi-allsky/source.fit')

    try:
        validate_sky_cycle_report_payload(report)
    except ValueError as e:
        assert 'Absolute paths' in str(e)
    else:
        raise AssertionError('moment evidence path should fail validation')

    report = build_sky_cycle_report_view()
    report['moments_summary']['items'][0]['evidence'].append({'secret': 'value'})

    try:
        validate_sky_cycle_report_payload(report)
    except ValueError as e:
        assert 'Sensitive key' in str(e)
    else:
        raise AssertionError('moment evidence secret should fail validation')

    report = build_sky_cycle_report_view()
    report['moments_summary']['items'][0]['evidence'].append(lambda: None)

    try:
        validate_sky_cycle_report_payload(report)
    except ValueError as e:
        assert 'Callable' in str(e)
    else:
        raise AssertionError('moment evidence callable should fail validation')


def test_validate_sky_cycle_report_payload_rejects_invalid_output_type():
    report = build_sky_cycle_report_view()
    report['outputs_summary']['items'][0]['type'] = 'download'

    try:
        validate_sky_cycle_report_payload(report)
    except ValueError as e:
        assert 'Invalid output type' in str(e)
    else:
        raise AssertionError('invalid output type should fail validation')


def test_validate_sky_cycle_report_payload_rejects_incomplete_output_item():
    report = build_sky_cycle_report_view()
    del report['outputs_summary']['items'][0]['source_lineage_status']

    try:
        validate_sky_cycle_report_payload(report)
    except ValueError as e:
        assert 'missing required keys' in str(e)
    else:
        raise AssertionError('incomplete output item should fail validation')


def test_validate_sky_cycle_report_payload_rejects_output_direct_safe_action():
    report = build_sky_cycle_report_view()
    report['outputs_summary']['items'][0]['safe_actions_available'] = [
        {
            'label': 'Generate output',
            'url': '/modern-admin/action',
        },
    ]

    try:
        validate_sky_cycle_report_payload(report)
    except ValueError as e:
        assert 'direct action' in str(e)
    else:
        raise AssertionError('direct output safe action should fail validation')


def test_validate_sky_cycle_report_payload_rejects_output_path_secret_callable():
    report = build_sky_cycle_report_view()
    report['outputs_summary']['items'][0]['quality_note'] = '/var/lib/indi-allsky/output.mp4'

    try:
        validate_sky_cycle_report_payload(report)
    except ValueError as e:
        assert 'Absolute paths' in str(e)
    else:
        raise AssertionError('output path should fail validation')

    report = build_sky_cycle_report_view()
    report['outputs_summary']['items'][0]['science_note'] = {'token': 'value'}

    try:
        validate_sky_cycle_report_payload(report)
    except ValueError as e:
        assert 'Sensitive key' in str(e)
    else:
        raise AssertionError('output secret should fail validation')

    report = build_sky_cycle_report_view()
    report['outputs_summary']['items'][0]['astrophoto_note'] = lambda: None

    try:
        validate_sky_cycle_report_payload(report)
    except ValueError as e:
        assert 'Callable' in str(e)
    else:
        raise AssertionError('output callable should fail validation')


def test_validate_sky_cycle_report_payload_rejects_source_invalid_risk():
    report = build_sky_cycle_report_view()
    report['source_confidence_summary']['risk_level'] = 'critical'

    try:
        validate_sky_cycle_report_payload(report)
    except ValueError as e:
        assert 'Invalid risk_level' in str(e)
    else:
        raise AssertionError('source confidence invalid risk should fail validation')


def test_validate_sky_cycle_report_payload_rejects_source_evidence_not_list():
    report = build_sky_cycle_report_view()
    report['source_confidence_summary']['evidence'] = 'No evidence connected'

    try:
        validate_sky_cycle_report_payload(report)
    except ValueError as e:
        assert 'evidence must be a list' in str(e)
    else:
        raise AssertionError('source confidence evidence string should fail validation')


def test_validate_sky_cycle_report_payload_rejects_source_types_not_list():
    report = build_sky_cycle_report_view()
    report['source_confidence_summary']['source_types'] = 'image metadata'

    try:
        validate_sky_cycle_report_payload(report)
    except ValueError as e:
        assert 'source_types must be a list' in str(e)
    else:
        raise AssertionError('source confidence source_types string should fail validation')


def test_validate_sky_cycle_report_payload_rejects_source_missing_field():
    report = build_sky_cycle_report_view()
    del report['source_confidence_summary']['lineage_status']

    try:
        validate_sky_cycle_report_payload(report)
    except ValueError as e:
        assert 'missing required keys' in str(e)
    else:
        raise AssertionError('source confidence missing field should fail validation')


def test_validate_sky_cycle_report_payload_rejects_health_invalid_risk():
    report = build_sky_cycle_report_view()
    report['observatory_health_summary']['risk_level'] = 'critical'

    try:
        validate_sky_cycle_report_payload(report)
    except ValueError as e:
        assert 'Invalid risk_level' in str(e)
    else:
        raise AssertionError('health invalid risk should fail validation')


def test_validate_sky_cycle_report_payload_rejects_health_evidence_not_list():
    report = build_sky_cycle_report_view()
    report['observatory_health_summary']['evidence'] = 'No health evidence connected'

    try:
        validate_sky_cycle_report_payload(report)
    except ValueError as e:
        assert 'evidence must be a list' in str(e)
    else:
        raise AssertionError('health evidence string should fail validation')


def test_validate_sky_cycle_report_payload_rejects_health_missing_field():
    report = build_sky_cycle_report_view()
    del report['observatory_health_summary']['storage_status']

    try:
        validate_sky_cycle_report_payload(report)
    except ValueError as e:
        assert 'missing required keys' in str(e)
    else:
        raise AssertionError('health missing field should fail validation')


def test_validate_sky_cycle_report_payload_rejects_source_health_path_secret_callable():
    report = build_sky_cycle_report_view()
    report['source_confidence_summary']['evidence'].append('/var/lib/indi-allsky/source')

    try:
        validate_sky_cycle_report_payload(report)
    except ValueError as e:
        assert 'Absolute paths' in str(e)
    else:
        raise AssertionError('source confidence path should fail validation')

    report = build_sky_cycle_report_view()
    report['observatory_health_summary']['evidence'].append({'password': 'value'})

    try:
        validate_sky_cycle_report_payload(report)
    except ValueError as e:
        assert 'Sensitive key' in str(e)
    else:
        raise AssertionError('health secret should fail validation')

    report = build_sky_cycle_report_view()
    report['observatory_health_summary']['evidence'].append(lambda: None)

    try:
        validate_sky_cycle_report_payload(report)
    except ValueError as e:
        assert 'Callable' in str(e)
    else:
        raise AssertionError('health callable should fail validation')


def test_sky_cycle_template_has_no_mutative_controls():
    template_text = SKY_CYCLE_TEMPLATE.read_text(encoding='utf-8').lower()

    assert '<form' not in template_text
    assert 'post' not in template_text
    assert 'fetch(' not in template_text
    assert '/ajax/' not in template_text


def test_current_phase_summary_maps_day():
    phase_summary = build_current_phase_summary(night=0)

    assert phase_summary['phase'] == 'day'
    assert phase_summary['source'] == 'template_context.night'
    assert phase_summary['confidence'] == 'bounded_context'
    assert phase_summary['is_placeholder'] is False
    assert phase_summary['unsupported_phases'][0]['phase'] == 'twilight'
    assert phase_summary['unsupported_phases'][0]['data_status'] == 'not_evaluated'


def test_current_phase_summary_maps_night():
    phase_summary = build_current_phase_summary(night=1)

    assert phase_summary['phase'] == 'night'
    assert phase_summary['source'] == 'template_context.night'
    assert phase_summary['confidence'] == 'bounded_context'
    assert phase_summary['is_placeholder'] is False


def test_current_phase_summary_maps_unknown():
    for night_value in (None, 'unknown', 2):
        phase_summary = build_current_phase_summary(night=night_value)
        assert phase_summary['phase'] == 'unknown'
        assert phase_summary['confidence'] == 'unknown'
        assert phase_summary['is_placeholder'] is True


def test_build_now_view_accepts_current_phase_context():
    day_view = build_now_view(current_phase_night=0)
    night_view = build_now_view(current_phase_night=1)

    assert day_view['current_phase_summary']['phase'] == 'day'
    assert night_view['current_phase_summary']['phase'] == 'night'


def test_source_confidence_summary_contract_is_fake_safe():
    now_view = build_now_view()
    source_confidence = now_view['source_confidence_summary']

    assert source_confidence['status'] == 'Source coverage pending bounded backend contract.'
    assert source_confidence['data_status'] == 'not_evaluated'
    assert source_confidence['confidence_label'] == 'Pending source coverage contract'
    assert source_confidence['coverage_label'] == 'Not evaluated yet'
    assert source_confidence['source_types'] == ['image metadata', 'source files']
    assert source_confidence['preservation_status'] == 'RAW/FITS/source preservation not evaluated in this prototype.'
    assert source_confidence['retention_status'] == 'Source retention policy not evaluated yet.'
    assert source_confidence['lineage_status'] == 'Lineage between outputs and source frames is not connected yet.'
    assert source_confidence['gap_status'] == 'Source gaps not evaluated yet.'
    assert source_confidence['risk_level'] == 'unknown'
    assert source_confidence['next_backend_contract'] == 'bounded source coverage summary'
    assert isinstance(source_confidence['evidence'], list)
    assert source_confidence['is_placeholder'] is True
    json.dumps(source_confidence, sort_keys=True)


def test_build_source_confidence_summary_is_static_contract():
    source_confidence = build_source_confidence_summary()

    assert source_confidence['status'] == 'Source coverage pending bounded backend contract.'
    assert source_confidence['data_status'] == 'not_evaluated'
    assert source_confidence['risk_level'] == 'unknown'
    assert source_confidence['source_types'] == ['image metadata', 'source files']
    assert 'retention_status' in source_confidence
    assert 'lineage_status' in source_confidence
    assert 'gap_status' in source_confidence
    assert_no_sensitive_text(source_confidence)
    assert_no_absolute_paths(source_confidence)
    assert_no_callables(source_confidence)


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


def test_latest_frame_image_table_adapter_with_row_present():
    created_at = datetime(2026, 6, 29, 5, 32, 10)
    query = FakeImageQuery(FakeImageRow(createDate=created_at, filename='/var/lib/indi-allsky/private.jpg'))
    adapter = LatestFrameImageTableRepository(
        query,
        order_by_expression='created-desc',
        camera_label='North Sky Camera',
        profile_label='Primary',
        clock=lambda: created_at + timedelta(minutes=2),
    )
    provider = LatestFrameSummaryProvider(adapter)
    now_view = build_now_view(latest_frame_provider=provider)
    latest_frame = now_view['latest_frame_summary']

    assert query.order_by_calls == ['created-desc']
    assert query.limit_calls == [1]
    assert query.first_calls == 1
    assert latest_frame['status'] == 'Latest frame metadata available.'
    assert latest_frame['camera_label'] == 'North Sky Camera'
    assert latest_frame['profile_label'] == 'Primary'
    assert latest_frame['timestamp'] == '2026-06-29 05:32:10'
    assert latest_frame['age_label'] == '2 minutes ago'
    assert latest_frame['image_available'] is True
    assert latest_frame['safe_preview_url'] is None
    assert_no_absolute_paths(latest_frame)
    assert 'private.jpg' not in json.dumps(latest_frame, sort_keys=True)


def test_latest_frame_image_table_adapter_with_no_row():
    query = FakeImageQuery(None)
    adapter = LatestFrameImageTableRepository(query, order_by_expression='created-desc')
    latest_frame = LatestFrameSummaryProvider(adapter).build()

    assert query.order_by_calls == ['created-desc']
    assert query.limit_calls == [1]
    assert query.first_calls == 1
    assert latest_frame['status'] == 'No recent frame metadata available.'
    assert latest_frame['image_available'] is False
    assert latest_frame['safe_preview_url'] is None


def test_latest_frame_image_table_adapter_with_query_error():
    query = FakeImageQuery(raises=True)
    adapter = LatestFrameImageTableRepository(query, order_by_expression='created-desc')
    latest_frame = LatestFrameSummaryProvider(adapter).build()

    assert query.limit_calls == [1]
    assert query.first_calls == 1
    assert latest_frame['status'] == 'Latest frame metadata unavailable.'
    assert latest_frame['source_status'] == 'Repository error.'
    assert latest_frame['safe_preview_url'] is None


def test_latest_frame_image_table_adapter_with_missing_attributes():
    query = FakeImageQuery(FakeImageRow())
    adapter = LatestFrameImageTableRepository(query)
    latest_frame = LatestFrameSummaryProvider(adapter).build()

    assert latest_frame['timestamp'] == 'Not evaluated yet'
    assert latest_frame['age_label'] == 'Not evaluated yet'
    assert latest_frame['image_available'] is True
    assert latest_frame['safe_preview_url'] is None
    json.dumps(latest_frame, sort_keys=True)


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


def test_validate_now_view_payload_rejects_invalid_current_phase():
    now_view = build_now_view()
    now_view['current_phase_summary']['phase'] = 'twilight'

    try:
        validate_now_view_payload(now_view)
    except ValueError as e:
        assert 'Invalid phase' in str(e)
    else:
        raise AssertionError('current_phase_summary invalid phase should fail validation')


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


def test_validate_now_view_payload_rejects_invalid_source_confidence_risk():
    now_view = build_now_view()
    now_view['source_confidence_summary']['risk_level'] = 'critical'

    try:
        validate_now_view_payload(now_view)
    except ValueError as e:
        assert 'Invalid risk_level' in str(e)
    else:
        raise AssertionError('source_confidence_summary invalid risk_level should fail validation')


def test_validate_now_view_payload_rejects_source_confidence_path():
    now_view = build_now_view()
    now_view['source_confidence_summary']['evidence'].append('/var/lib/indi-allsky/source')

    try:
        validate_now_view_payload(now_view)
    except ValueError as e:
        assert 'Absolute path' in str(e)
    else:
        raise AssertionError('source_confidence_summary absolute path should fail validation')


def test_validate_now_view_payload_rejects_source_confidence_secret():
    now_view = build_now_view()
    now_view['source_confidence_summary']['evidence'].append({'api_key': 'redacted'})

    try:
        validate_now_view_payload(now_view)
    except ValueError as e:
        assert 'Sensitive key' in str(e)
    else:
        raise AssertionError('source_confidence_summary sensitive key should fail validation')


def test_validate_now_view_payload_rejects_source_confidence_callable():
    now_view = build_now_view()
    now_view['source_confidence_summary']['evidence'].append(lambda: None)

    try:
        validate_now_view_payload(now_view)
    except ValueError as e:
        assert 'Callable' in str(e)
    else:
        raise AssertionError('source_confidence_summary callable should fail validation')


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
        test_build_sky_cycle_report_view_returns_dict,
        test_build_sky_cycle_report_view_is_json_serializable,
        test_build_sky_cycle_report_view_has_required_sections,
        test_build_sky_cycle_report_view_contains_no_sensitive_payload,
        test_build_highlights_view_returns_dict,
        test_build_highlights_view_is_json_serializable,
        test_build_highlights_view_has_required_sections,
        test_build_highlights_view_contains_no_sensitive_payload,
        test_validate_highlights_payload_success,
        test_validate_highlights_payload_requires_sections,
        test_validate_highlights_payload_rejects_invalid_type,
        test_validate_highlights_payload_rejects_invalid_target_kind,
        test_validate_highlights_payload_rejects_invalid_origin,
        test_validate_highlights_payload_rejects_evidence_not_list,
        test_validate_highlights_payload_rejects_direct_safe_action,
        test_validate_highlights_payload_rejects_path_secret_callable,
        test_highlights_template_has_no_mutative_controls,
        test_build_moment_detail_view_returns_dict,
        test_build_moment_detail_view_is_json_serializable,
        test_build_moment_detail_view_has_required_sections,
        test_build_moment_detail_view_contains_no_sensitive_payload,
        test_validate_moment_detail_payload_success,
        test_validate_moment_detail_payload_requires_sections,
        test_validate_moment_detail_payload_rejects_invalid_type,
        test_validate_moment_detail_payload_rejects_invalid_phase,
        test_validate_moment_detail_payload_rejects_evidence_not_list,
        test_validate_moment_detail_payload_rejects_invalid_output_type,
        test_validate_moment_detail_payload_rejects_output_not_list,
        test_validate_moment_detail_payload_rejects_path_secret_callable,
        test_moment_detail_template_has_no_mutative_controls,
        test_build_output_detail_view_returns_dict,
        test_build_output_detail_view_is_json_serializable,
        test_build_output_detail_view_has_required_sections,
        test_build_output_detail_view_contains_no_sensitive_payload,
        test_validate_output_detail_payload_success,
        test_validate_output_detail_payload_requires_sections,
        test_validate_output_detail_payload_rejects_invalid_type,
        test_validate_output_detail_payload_rejects_invalid_trust_level,
        test_validate_output_detail_payload_rejects_evidence_not_list,
        test_validate_output_detail_payload_rejects_direct_safe_action,
        test_validate_output_detail_payload_rejects_path_secret_callable,
        test_output_detail_template_has_no_mutative_controls,
        test_build_library_view_returns_dict,
        test_build_library_view_is_json_serializable,
        test_build_library_view_has_required_sections,
        test_build_library_view_contains_no_sensitive_payload,
        test_validate_library_payload_success,
        test_validate_library_payload_requires_sections,
        test_validate_library_payload_rejects_invalid_kind,
        test_validate_library_payload_rejects_invalid_collection_type,
        test_validate_library_payload_rejects_indexed_fields_not_list,
        test_validate_library_payload_rejects_path_secret_callable,
        test_library_template_has_no_mutative_controls,
        test_build_observatory_view_returns_dict,
        test_build_observatory_view_is_json_serializable,
        test_build_observatory_view_has_required_sections,
        test_build_observatory_view_contains_no_sensitive_payload,
        test_validate_observatory_payload_success,
        test_validate_observatory_payload_requires_sections,
        test_validate_observatory_payload_rejects_invalid_status,
        test_validate_observatory_payload_rejects_invalid_trust_or_risk,
        test_validate_observatory_payload_rejects_attention_items_not_list,
        test_validate_observatory_payload_rejects_path_secret_callable,
        test_observatory_template_has_no_mutative_controls,
        test_validate_sky_cycle_report_payload_success,
        test_validate_sky_cycle_report_payload_requires_sections,
        test_validate_sky_cycle_report_payload_rejects_invalid_status,
        test_validate_sky_cycle_report_payload_rejects_invalid_phase,
        test_validate_sky_cycle_report_payload_rejects_incomplete_phase_item,
        test_validate_sky_cycle_report_payload_rejects_non_boolean_supported,
        test_validate_sky_cycle_report_payload_rejects_invalid_moment_type,
        test_validate_sky_cycle_report_payload_rejects_moment_evidence_not_list,
        test_validate_sky_cycle_report_payload_rejects_incomplete_moment_item,
        test_validate_sky_cycle_report_payload_rejects_moment_path_secret_callable,
        test_validate_sky_cycle_report_payload_rejects_invalid_output_type,
        test_validate_sky_cycle_report_payload_rejects_incomplete_output_item,
        test_validate_sky_cycle_report_payload_rejects_output_direct_safe_action,
        test_validate_sky_cycle_report_payload_rejects_output_path_secret_callable,
        test_validate_sky_cycle_report_payload_rejects_source_invalid_risk,
        test_validate_sky_cycle_report_payload_rejects_source_evidence_not_list,
        test_validate_sky_cycle_report_payload_rejects_source_types_not_list,
        test_validate_sky_cycle_report_payload_rejects_source_missing_field,
        test_validate_sky_cycle_report_payload_rejects_health_invalid_risk,
        test_validate_sky_cycle_report_payload_rejects_health_evidence_not_list,
        test_validate_sky_cycle_report_payload_rejects_health_missing_field,
        test_validate_sky_cycle_report_payload_rejects_source_health_path_secret_callable,
        test_sky_cycle_template_has_no_mutative_controls,
        test_current_phase_summary_maps_day,
        test_current_phase_summary_maps_night,
        test_current_phase_summary_maps_unknown,
        test_build_now_view_accepts_current_phase_context,
        test_source_confidence_summary_contract_is_fake_safe,
        test_build_source_confidence_summary_is_static_contract,
        test_latest_frame_summary_contract_is_fake_safe,
        test_latest_frame_provider_with_frame_present,
        test_latest_frame_provider_with_no_frame,
        test_latest_frame_provider_with_missing_timestamp,
        test_latest_frame_provider_with_repository_error,
        test_latest_frame_provider_rejects_suspicious_metadata,
        test_build_now_view_accepts_injected_latest_frame_provider,
        test_latest_frame_image_table_adapter_with_row_present,
        test_latest_frame_image_table_adapter_with_no_row,
        test_latest_frame_image_table_adapter_with_query_error,
        test_latest_frame_image_table_adapter_with_missing_attributes,
        test_safe_actions_are_metadata_only,
        test_validate_now_view_payload_success,
        test_validate_now_view_payload_requires_sections,
        test_validate_now_view_payload_rejects_invalid_data_status,
        test_validate_now_view_payload_rejects_invalid_current_phase,
        test_validate_now_view_payload_rejects_latest_frame_absolute_preview_path,
        test_validate_now_view_payload_rejects_latest_frame_invalid_status,
        test_validate_now_view_payload_rejects_invalid_source_confidence_risk,
        test_validate_now_view_payload_rejects_source_confidence_path,
        test_validate_now_view_payload_rejects_source_confidence_secret,
        test_validate_now_view_payload_rejects_source_confidence_callable,
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
