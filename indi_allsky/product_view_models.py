"""Product-domain view models for Hybrid AllSky.

This module is intentionally framework-free. It does not import web framework
objects, query the database, inspect the filesystem, or evaluate camera/runtime
state.
"""

from dataclasses import asdict
from dataclasses import dataclass
import json
import re


NOW_DATA_STATUS_PLACEHOLDER = 'placeholder'
NOW_DATA_STATUS_NOT_EVALUATED = 'not_evaluated'
NOW_DATA_STATUS_FUTURE_CONTRACT = 'future_backend_contract'

NOW_ALLOWED_DATA_STATUSES = frozenset((
    NOW_DATA_STATUS_PLACEHOLDER,
    NOW_DATA_STATUS_NOT_EVALUATED,
    NOW_DATA_STATUS_FUTURE_CONTRACT,
))

NOW_REQUIRED_KEYS = frozenset((
    'id',
    'label',
    'status',
    'data_status',
    'generated_at',
    'is_placeholder',
    'safe_actions_available',
    'current_sky',
    'sky_cycle_briefing',
    'notable_moments',
    'generated_outputs',
    'observatory_health',
    'attention_items',
    'metadata',
))

NOW_REQUIRED_SECTIONS = frozenset((
    'current_sky',
    'sky_cycle_briefing',
    'notable_moments',
    'generated_outputs',
    'observatory_health',
    'attention_items',
))

NOW_SENSITIVE_KEY_TOKENS = frozenset((
    'apikey',
    'api_key',
    'client_secret',
    'password',
    'refresh_token',
    'secret',
    'token',
))

NOW_DIRECT_ACTION_KEYS = frozenset((
    'endpoint',
    'href',
    'method',
    'post',
    'route',
    'url',
))

NOW_ABSOLUTE_PATH_RE = re.compile(r'(^|["\s:])/[A-Za-z0-9_.-]+/')
NOW_WINDOWS_PATH_RE = re.compile(r'[A-Za-z]:\\\\')


@dataclass(frozen=True)
class NowSection:
    id: str
    label: str
    status: str
    data_status: str
    is_placeholder: bool
    summary: str = ''
    note: str = ''

    def to_dict(self):
        data = asdict(self)
        return {key: value for key, value in data.items() if value != ''}


@dataclass(frozen=True)
class CurrentSkySection:
    id: str
    label: str
    phase: str
    latest_image: str
    capture_status: str
    source_recording: str
    summary: str
    data_status: str
    is_placeholder: bool

    def to_dict(self):
        return asdict(self)


@dataclass(frozen=True)
class SkyCycleBriefingSection:
    id: str
    label: str
    verdict_label: str
    verdict: str
    source_coverage: str
    outputs_status: str
    notable_moments_count: str
    summary: str
    data_status: str
    is_placeholder: bool

    def to_dict(self):
        return asdict(self)


@dataclass(frozen=True)
class NowMoment:
    id: str
    label: str
    confidence: str
    evidence: str
    status: str
    data_status: str
    is_placeholder: bool

    def to_dict(self):
        return asdict(self)


@dataclass(frozen=True)
class GeneratedOutput:
    id: str
    label: str
    status: str
    look: str
    lineage: str
    data_status: str
    is_placeholder: bool

    def to_dict(self):
        return asdict(self)


def build_now_view():
    """Return the first backend-owned NowView contract.

    The payload is static and fake-safe by design. It gives the Product UI a
    stable shape while real Now/SkyCycle/Moment/Output contracts are still being
    designed.
    """
    payload = {
        'id': 'now.placeholder',
        'label': 'Now',
        'status': 'Read-only product prototype',
        'data_status': NOW_DATA_STATUS_PLACEHOLDER,
        'generated_at': 'Not evaluated yet',
        'is_placeholder': True,
        'safe_actions_available': [],
        'current_sky': _build_current_sky(),
        'sky_cycle_briefing': _build_sky_cycle_briefing(),
        'notable_moments': _build_notable_moments(),
        'generated_outputs': _build_generated_outputs(),
        'observatory_health': _build_observatory_health(),
        'attention_items': _build_attention_items(),
        'metadata': _build_now_metadata(),
    }

    validate_now_view_payload(payload)
    return payload


def validate_now_view_payload(payload):
    """Validate a NowView payload before it reaches presentation templates."""
    if not isinstance(payload, dict):
        raise ValueError('NowView payload must be a dict')

    missing_keys = sorted(NOW_REQUIRED_KEYS.difference(payload.keys()))
    if missing_keys:
        raise ValueError('NowView payload missing required keys: {0:s}'.format(', '.join(missing_keys)))

    for section_key in NOW_REQUIRED_SECTIONS:
        _validate_required_section(payload, section_key)

    _validate_data_statuses(payload)
    _validate_no_callables(payload)
    _validate_no_sensitive_keys(payload)
    _validate_no_absolute_paths(payload)
    _validate_safe_actions(payload)
    _validate_json_safe(payload)

    return True


def _build_current_sky():
    return CurrentSkySection(
        id='current_sky.placeholder',
        label='Current Sky',
        phase='Unknown',
        latest_image='Latest image not evaluated yet',
        capture_status='Capture status placeholder',
        source_recording='Source recording status placeholder',
        summary='Future NowView backend contract will provide sanitized live sky state.',
        data_status=NOW_DATA_STATUS_NOT_EVALUATED,
        is_placeholder=True,
    ).to_dict()


def _build_sky_cycle_briefing():
    return SkyCycleBriefingSection(
        id='sky_cycle.placeholder',
        label='Latest Sky Cycle Briefing',
        verdict_label='Cycle Verdict',
        verdict='Not evaluated yet',
        source_coverage='Placeholder',
        outputs_status='Generated outputs not evaluated here',
        notable_moments_count='Placeholder',
        summary='Future SkyCycleSummary will explain the latest complete day/night cycle.',
        data_status=NOW_DATA_STATUS_FUTURE_CONTRACT,
        is_placeholder=True,
    ).to_dict()


def _build_notable_moments():
    return [
        NowMoment(
            id='moment.meteor_candidate.placeholder',
            label='Meteor candidate',
            confidence='Placeholder',
            evidence='Future MomentSummary evidence',
            status='Not evaluated yet',
            data_status=NOW_DATA_STATUS_FUTURE_CONTRACT,
            is_placeholder=True,
        ).to_dict(),
        NowMoment(
            id='moment.lightning_storm.placeholder',
            label='Lightning or storm candidate',
            confidence='Placeholder',
            evidence='Future weather/sky evidence',
            status='Not evaluated yet',
            data_status=NOW_DATA_STATUS_FUTURE_CONTRACT,
            is_placeholder=True,
        ).to_dict(),
        NowMoment(
            id='moment.clear_window.placeholder',
            label='Clear window',
            confidence='Placeholder',
            evidence='Future sky quality timeline',
            status='Not evaluated yet',
            data_status=NOW_DATA_STATUS_FUTURE_CONTRACT,
            is_placeholder=True,
        ).to_dict(),
        NowMoment(
            id='moment.anomaly.placeholder',
            label='Anomaly',
            confidence='Placeholder',
            evidence='Future observatory diagnostics',
            status='Not evaluated yet',
            data_status=NOW_DATA_STATUS_FUTURE_CONTRACT,
            is_placeholder=True,
        ).to_dict(),
    ]


def _build_generated_outputs():
    return [
        GeneratedOutput(
            id='output.best_image.placeholder',
            label='Best image',
            status='Placeholder',
            look='No look evaluated',
            lineage='Source lineage placeholder',
            data_status=NOW_DATA_STATUS_FUTURE_CONTRACT,
            is_placeholder=True,
        ).to_dict(),
        GeneratedOutput(
            id='output.timelapse.placeholder',
            label='Timelapse',
            status='Placeholder',
            look='No look evaluated',
            lineage='Source lineage placeholder',
            data_status=NOW_DATA_STATUS_FUTURE_CONTRACT,
            is_placeholder=True,
        ).to_dict(),
        GeneratedOutput(
            id='output.keogram.placeholder',
            label='Keogram',
            status='Placeholder',
            look='No look evaluated',
            lineage='Source lineage placeholder',
            data_status=NOW_DATA_STATUS_FUTURE_CONTRACT,
            is_placeholder=True,
        ).to_dict(),
        GeneratedOutput(
            id='output.startrail.placeholder',
            label='Startrail',
            status='Placeholder',
            look='No look evaluated',
            lineage='Source lineage placeholder',
            data_status=NOW_DATA_STATUS_FUTURE_CONTRACT,
            is_placeholder=True,
        ).to_dict(),
    ]


def _build_observatory_health():
    return [
        NowSection(
            id='health.camera.placeholder',
            label='Camera',
            status='Not evaluated here',
            note='Future ObservatoryHealth camera state.',
            data_status=NOW_DATA_STATUS_NOT_EVALUATED,
            is_placeholder=True,
        ).to_dict(),
        NowSection(
            id='health.storage.placeholder',
            label='Storage',
            status='Not evaluated here',
            note='Future storage health and source preservation state.',
            data_status=NOW_DATA_STATUS_NOT_EVALUATED,
            is_placeholder=True,
        ).to_dict(),
        NowSection(
            id='health.source_preservation.placeholder',
            label='Source preservation',
            status='Placeholder',
            note='RAW/FITS/source preservation remains a product invariant.',
            data_status=NOW_DATA_STATUS_PLACEHOLDER,
            is_placeholder=True,
        ).to_dict(),
        NowSection(
            id='health.generation.placeholder',
            label='Generation',
            status='Not evaluated here',
            note='Future output job and rendering status.',
            data_status=NOW_DATA_STATUS_NOT_EVALUATED,
            is_placeholder=True,
        ).to_dict(),
        NowSection(
            id='health.upload_integration.placeholder',
            label='Upload / integration',
            status='Not evaluated here',
            note='Future integration health summary.',
            data_status=NOW_DATA_STATUS_NOT_EVALUATED,
            is_placeholder=True,
        ).to_dict(),
        NowSection(
            id='health.warnings.placeholder',
            label='Warnings',
            status='Placeholder',
            note='Future AttentionItem summary.',
            data_status=NOW_DATA_STATUS_PLACEHOLDER,
            is_placeholder=True,
        ).to_dict(),
    ]


def _build_attention_items():
    return [
        NowSection(
            id='attention.backend_contract.placeholder',
            label='Backend contract needed',
            status='Blocked',
            note='Now will need sanitized domain view models before live data appears here.',
            data_status=NOW_DATA_STATUS_FUTURE_CONTRACT,
            is_placeholder=True,
        ).to_dict(),
        NowSection(
            id='attention.safe_actions.placeholder',
            label='Safe actions unavailable',
            status='Read-only',
            note='This prototype exposes no controls.',
            data_status=NOW_DATA_STATUS_PLACEHOLDER,
            is_placeholder=True,
        ).to_dict(),
        NowSection(
            id='attention.source_lineage.placeholder',
            label='Source lineage placeholder',
            status='Future contract',
            note='Output lineage is shown as a concept only.',
            data_status=NOW_DATA_STATUS_FUTURE_CONTRACT,
            is_placeholder=True,
        ).to_dict(),
    ]


def _build_now_metadata():
    return {
        'contract': 'NowView',
        'contract_version': 'v1-placeholder',
        'source': 'static backend-owned builder',
        'data_status': NOW_DATA_STATUS_PLACEHOLDER,
        'notes': [
            'No runtime state evaluated.',
            'No database, filesystem, camera, source, or media generation access.',
        ],
    }


def _validate_required_section(payload, section_key):
    value = payload.get(section_key)
    if value in (None, '', [], {}):
        raise ValueError('NowView section is missing or empty: {0:s}'.format(section_key))


def _validate_data_statuses(value, path='now'):
    if isinstance(value, dict):
        if 'data_status' in value and value['data_status'] not in NOW_ALLOWED_DATA_STATUSES:
            raise ValueError('Invalid data_status at {0:s}: {1!r}'.format(path, value['data_status']))

        for key, item in value.items():
            _validate_data_statuses(item, '{0:s}.{1:s}'.format(path, str(key)))
    elif isinstance(value, list):
        for index, item in enumerate(value):
            _validate_data_statuses(item, '{0:s}[{1:d}]'.format(path, index))


def _validate_no_callables(value, path='now'):
    if callable(value):
        raise ValueError('Callable value is not allowed at {0:s}'.format(path))

    if isinstance(value, dict):
        for key, item in value.items():
            if callable(key):
                raise ValueError('Callable key is not allowed at {0:s}'.format(path))
            _validate_no_callables(item, '{0:s}.{1:s}'.format(path, str(key)))
    elif isinstance(value, list):
        for index, item in enumerate(value):
            _validate_no_callables(item, '{0:s}[{1:d}]'.format(path, index))


def _validate_no_sensitive_keys(value, path='now'):
    if isinstance(value, dict):
        for key, item in value.items():
            key_lower = str(key).lower()
            if any(token in key_lower for token in NOW_SENSITIVE_KEY_TOKENS):
                raise ValueError('Sensitive key is not allowed at {0:s}: {1:s}'.format(path, str(key)))
            _validate_no_sensitive_keys(item, '{0:s}.{1:s}'.format(path, str(key)))
    elif isinstance(value, list):
        for index, item in enumerate(value):
            _validate_no_sensitive_keys(item, '{0:s}[{1:d}]'.format(path, index))


def _validate_no_absolute_paths(payload):
    payload_text = json.dumps(payload, sort_keys=True)
    if NOW_ABSOLUTE_PATH_RE.search(payload_text) or NOW_WINDOWS_PATH_RE.search(payload_text):
        raise ValueError('Absolute paths are not allowed in NowView payload')


def _validate_safe_actions(payload):
    actions = payload.get('safe_actions_available')
    if not isinstance(actions, list):
        raise ValueError('safe_actions_available must be a list')

    if not actions:
        return

    for index, action in enumerate(actions):
        if not isinstance(action, dict):
            raise ValueError('safe_actions_available item must be metadata dict at index {0:d}'.format(index))

        action_keys = set(str(key).lower() for key in action.keys())
        if action_keys.intersection(NOW_DIRECT_ACTION_KEYS):
            raise ValueError('safe_actions_available cannot include direct action data at index {0:d}'.format(index))


def _validate_json_safe(payload):
    try:
        json.dumps(payload, sort_keys=True)
    except (TypeError, ValueError) as e:
        raise ValueError('NowView payload must be JSON-safe: {0:s}'.format(str(e)))
