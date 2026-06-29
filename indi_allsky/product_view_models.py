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

NOW_PHASE_DAY = 'day'
NOW_PHASE_NIGHT = 'night'
NOW_PHASE_UNKNOWN = 'unknown'

NOW_ALLOWED_PHASES = frozenset((
    NOW_PHASE_DAY,
    NOW_PHASE_NIGHT,
    NOW_PHASE_UNKNOWN,
))

NOW_RISK_LEVEL_UNKNOWN = 'unknown'
NOW_RISK_LEVEL_LOW = 'low'
NOW_RISK_LEVEL_MEDIUM = 'medium'
NOW_RISK_LEVEL_HIGH = 'high'

NOW_ALLOWED_RISK_LEVELS = frozenset((
    NOW_RISK_LEVEL_UNKNOWN,
    NOW_RISK_LEVEL_LOW,
    NOW_RISK_LEVEL_MEDIUM,
    NOW_RISK_LEVEL_HIGH,
))

NOW_REQUIRED_KEYS = frozenset((
    'id',
    'label',
    'status',
    'briefing_title',
    'current_verdict',
    'data_status',
    'generated_at',
    'is_placeholder',
    'safe_actions_available',
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
))

NOW_REQUIRED_SECTIONS = frozenset((
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
NOW_SUSPICIOUS_URL_TOKENS = frozenset(('..', 'file:', '\\'))

NOW_LATEST_FRAME_REQUIRED_KEYS = frozenset((
    'id',
    'label',
    'status',
    'data_status',
    'camera_label',
    'profile_label',
    'timestamp',
    'age_label',
    'image_available',
    'safe_preview_url',
    'source_status',
    'note',
    'evidence',
    'is_placeholder',
))

NOW_LATEST_FRAME_REPOSITORY_KEYS = frozenset((
    'camera_label',
    'profile_label',
    'timestamp',
    'age_label',
    'image_available',
    'source_status',
))

NOW_CURRENT_PHASE_REQUIRED_KEYS = frozenset((
    'id',
    'label',
    'phase',
    'data_status',
    'source',
    'confidence',
    'note',
    'supported_phases',
    'unsupported_phases',
    'is_placeholder',
))

NOW_SOURCE_CONFIDENCE_REQUIRED_KEYS = frozenset((
    'id',
    'label',
    'status',
    'data_status',
    'confidence_label',
    'coverage_label',
    'source_types',
    'preservation_status',
    'risk_level',
    'note',
    'evidence',
    'next_backend_contract',
    'is_placeholder',
))

SKY_CYCLE_REQUIRED_KEYS = frozenset((
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
))

SKY_CYCLE_REQUIRED_SECTIONS = frozenset((
    'cycle_summary',
    'moments_summary',
    'outputs_summary',
    'source_confidence_summary',
    'observatory_health_summary',
    'attention_items',
))

SKY_CYCLE_SUMMARY_REQUIRED_KEYS = frozenset((
    'id',
    'label',
    'title',
    'cycle_label',
    'data_status',
    'current_phase',
    'cycle_verdict',
    'time_range_label',
    'note',
    'is_placeholder',
))

SKY_CYCLE_PHASE_REQUIRED_KEYS = frozenset((
    'id',
    'label',
    'phase',
    'status',
    'data_status',
    'time_range_label',
    'note',
    'is_placeholder',
))


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
class CurrentPhaseSummary:
    id: str
    label: str
    phase: str
    data_status: str
    source: str
    confidence: str
    note: str
    supported_phases: list
    unsupported_phases: list
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
class LatestFrameSummary:
    id: str
    label: str
    status: str
    data_status: str
    camera_label: str
    profile_label: str
    timestamp: str
    age_label: str
    image_available: bool
    safe_preview_url: object
    source_status: str
    note: str
    evidence: str
    is_placeholder: bool

    def to_dict(self):
        return asdict(self)


@dataclass(frozen=True)
class SourceConfidenceSummary:
    id: str
    label: str
    status: str
    data_status: str
    confidence_label: str
    coverage_label: str
    source_types: list
    preservation_status: str
    risk_level: str
    note: str
    evidence: list
    next_backend_contract: str
    is_placeholder: bool

    def to_dict(self):
        return asdict(self)


@dataclass(frozen=True)
class SkyCycleSummary:
    id: str
    label: str
    title: str
    cycle_label: str
    data_status: str
    current_phase: str
    cycle_verdict: str
    time_range_label: str
    note: str
    is_placeholder: bool

    def to_dict(self):
        return asdict(self)


@dataclass(frozen=True)
class SkyCyclePhase:
    id: str
    label: str
    phase: str
    status: str
    data_status: str
    time_range_label: str
    note: str
    is_placeholder: bool

    def to_dict(self):
        return asdict(self)


class StaticLatestFrameRepository:
    """Default repository for the static NowView contract."""

    def get_latest_frame_metadata(self):
        return None


class LatestFrameImageTableRepository:
    """Repository adapter for one bounded latest image metadata row."""

    def __init__(
        self,
        query,
        order_by_expression=None,
        camera_label='Camera not evaluated yet',
        profile_label='Profile not evaluated yet',
        clock=None,
    ):
        self.query = query
        self.order_by_expression = order_by_expression
        self.camera_label = camera_label
        self.profile_label = profile_label
        self.clock = clock

    def get_latest_frame_metadata(self):
        bounded_query = self.query

        if self.order_by_expression is not None:
            bounded_query = bounded_query.order_by(self.order_by_expression)

        bounded_query = bounded_query.limit(1)
        row = bounded_query.first()

        if not row:
            return None

        created_at = getattr(row, 'createDate', None)

        return {
            'camera_label': self.camera_label,
            'profile_label': self.profile_label,
            'timestamp': _latest_frame_timestamp_label(created_at),
            'age_label': _latest_frame_age_label(created_at, self.clock),
            'image_available': True,
            'source_status': 'Metadata row available.',
        }


class LatestFrameSummaryProvider:
    """Build a sanitized latest frame summary from an injected repository."""

    def __init__(self, repository=None):
        self.repository = repository or StaticLatestFrameRepository()

    def build(self):
        try:
            metadata = self.repository.get_latest_frame_metadata()
        except Exception:
            return _build_latest_frame_repository_error_summary()

        if not metadata:
            return _build_latest_frame_no_row_summary()

        try:
            sanitized_metadata = _sanitize_latest_frame_metadata(metadata)
        except ValueError:
            return _build_latest_frame_rejected_summary()

        return LatestFrameSummary(
            id='latest_frame.repository',
            label='Latest Frame Summary',
            status='Latest frame metadata available.',
            data_status=NOW_DATA_STATUS_NOT_EVALUATED,
            camera_label=sanitized_metadata['camera_label'],
            profile_label=sanitized_metadata['profile_label'],
            timestamp=sanitized_metadata['timestamp'],
            age_label=sanitized_metadata['age_label'],
            image_available=sanitized_metadata['image_available'],
            safe_preview_url=None,
            source_status=sanitized_metadata['source_status'],
            note='Metadata accepted from injected repository. Preview remains disabled.',
            evidence='Bounded latest frame metadata accepted; no preview URL or source path is exposed.',
            is_placeholder=True,
        ).to_dict()


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


@dataclass(frozen=True)
class PrimaryQuestionAnswer:
    id: str
    question: str
    answer: str
    evidence: str
    data_status: str
    is_placeholder: bool

    def to_dict(self):
        return asdict(self)


def build_now_view(latest_frame_provider=None, current_phase_night=None):
    """Return the first backend-owned NowView contract.

    The payload is static and fake-safe by design. It gives the Product UI a
    stable shape while real Now/SkyCycle/Moment/Output contracts are still being
    designed.
    """
    payload = {
        'id': 'now.placeholder',
        'label': 'Now',
        'status': 'Read-only product prototype',
        'briefing_title': 'Current / Morning Briefing',
        'current_verdict': 'Observation data not evaluated yet',
        'data_status': NOW_DATA_STATUS_PLACEHOLDER,
        'generated_at': 'Not evaluated yet',
        'is_placeholder': True,
        'safe_actions_available': [],
        'current_sky': _build_current_sky(),
        'current_phase_summary': build_current_phase_summary(current_phase_night),
        'latest_frame_summary': _build_latest_frame_summary(latest_frame_provider=latest_frame_provider),
        'source_confidence_summary': build_source_confidence_summary(),
        'sky_cycle_briefing': _build_sky_cycle_briefing(),
        'primary_question_answers': _build_primary_question_answers(),
        'evidence_summary': _build_evidence_summary(),
        'science_context': _build_science_context(),
        'astrophoto_context': _build_astrophoto_context(),
        'notable_moments': _build_notable_moments(),
        'generated_outputs': _build_generated_outputs(),
        'observatory_health': _build_observatory_health(),
        'attention_items': _build_attention_items(),
        'metadata': _build_now_metadata(),
    }

    validate_now_view_payload(payload)
    return payload


def build_sky_cycle_report_view():
    """Return the first fake-safe Sky Cycle Report product contract."""
    payload = {
        'id': 'sky_cycle_report.placeholder',
        'label': 'Sky Cycle Report',
        'status': 'Read-only product prototype',
        'data_status': NOW_DATA_STATUS_PLACEHOLDER,
        'generated_at': 'Not evaluated yet',
        'is_placeholder': True,
        'safe_actions_available': [],
        'cycle_summary': _build_sky_cycle_report_summary(),
        'phase_timeline': _build_sky_cycle_phase_timeline(),
        'moments_summary': _build_sky_cycle_moments_summary(),
        'outputs_summary': _build_sky_cycle_outputs_summary(),
        'source_confidence_summary': build_source_confidence_summary(),
        'observatory_health_summary': _build_sky_cycle_observatory_health_summary(),
        'attention_items': _build_sky_cycle_attention_items(),
        'metadata': _build_sky_cycle_metadata(),
    }

    validate_sky_cycle_report_payload(payload)
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

    _validate_current_phase_summary(payload.get('current_phase_summary'))
    _validate_latest_frame_summary(payload.get('latest_frame_summary'))
    _validate_source_confidence_summary(payload.get('source_confidence_summary'))
    _validate_data_statuses(payload)
    _validate_no_callables(payload)
    _validate_no_sensitive_keys(payload)
    _validate_no_absolute_paths(payload)
    _validate_safe_actions(payload)
    _validate_json_safe(payload)

    return True


def validate_sky_cycle_report_payload(payload):
    """Validate a Sky Cycle Report payload before template rendering."""
    if not isinstance(payload, dict):
        raise ValueError('SkyCycleReport payload must be a dict')

    missing_keys = sorted(SKY_CYCLE_REQUIRED_KEYS.difference(payload.keys()))
    if missing_keys:
        raise ValueError('SkyCycleReport payload missing required keys: {0:s}'.format(', '.join(missing_keys)))

    for section_key in SKY_CYCLE_REQUIRED_SECTIONS:
        _validate_required_section(payload, section_key)

    _validate_sky_cycle_summary(payload.get('cycle_summary'))
    _validate_sky_cycle_phase_timeline(payload.get('phase_timeline'))
    _validate_source_confidence_summary(payload.get('source_confidence_summary'))
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
        latest_image='Latest frame not evaluated yet',
        capture_status='Capture status pending backend contract',
        source_recording='Source recording status pending backend contract',
        summary='Current phase, latest frame, and source recording status are placeholders until a safe NowView data source is connected.',
        data_status=NOW_DATA_STATUS_NOT_EVALUATED,
        is_placeholder=True,
    ).to_dict()


def build_current_phase_summary(night=None):
    phase = _map_current_phase(night)

    if phase == NOW_PHASE_DAY:
        confidence = 'bounded_context'
        note = 'Current phase: Day. Mapped from the existing view context; twilight classification not evaluated yet.'
        is_placeholder = False
    elif phase == NOW_PHASE_NIGHT:
        confidence = 'bounded_context'
        note = 'Current phase: Night. Mapped from the existing view context; twilight classification not evaluated yet.'
        is_placeholder = False
    else:
        confidence = 'unknown'
        note = 'Current phase: Unknown. Existing view context did not provide a reliable day/night flag.'
        is_placeholder = True

    return CurrentPhaseSummary(
        id='current_phase.context_night',
        label='Current Phase Summary',
        phase=phase,
        data_status=NOW_DATA_STATUS_NOT_EVALUATED,
        source='template_context.night',
        confidence=confidence,
        note=note,
        supported_phases=[
            NOW_PHASE_DAY,
            NOW_PHASE_NIGHT,
            NOW_PHASE_UNKNOWN,
        ],
        unsupported_phases=[
            {
                'phase': 'twilight',
                'data_status': NOW_DATA_STATUS_NOT_EVALUATED,
                'note': 'Twilight classification not evaluated yet.',
            },
        ],
        is_placeholder=is_placeholder,
    ).to_dict()


def _map_current_phase(night):
    try:
        night_value = int(night)
    except (TypeError, ValueError):
        return NOW_PHASE_UNKNOWN

    if night_value == 0:
        return NOW_PHASE_DAY

    if night_value == 1:
        return NOW_PHASE_NIGHT

    return NOW_PHASE_UNKNOWN


def _build_latest_frame_summary(latest_frame_provider=None):
    provider = latest_frame_provider or LatestFrameSummaryProvider()
    return provider.build()


def build_source_confidence_summary():
    return SourceConfidenceSummary(
        id='source_confidence.placeholder',
        label='Source Confidence',
        status='not_evaluated',
        data_status=NOW_DATA_STATUS_NOT_EVALUATED,
        confidence_label='Pending source coverage contract',
        coverage_label='Not evaluated yet',
        source_types=[
            'image metadata',
        ],
        preservation_status='Source preservation not evaluated yet',
        risk_level=NOW_RISK_LEVEL_UNKNOWN,
        note='Source coverage not evaluated yet.',
        evidence=[
            'No RAW/FITS/source coverage calculation is connected yet.',
            'This panel will summarize whether generated results are backed by preserved source data.',
        ],
        next_backend_contract='bounded source coverage summary',
        is_placeholder=True,
    ).to_dict()


def _build_sky_cycle_report_summary():
    return SkyCycleSummary(
        id='sky_cycle.summary.placeholder',
        label='Cycle Summary',
        title='Sky Cycle Report',
        cycle_label='Current or latest cycle not evaluated yet',
        data_status=NOW_DATA_STATUS_NOT_EVALUATED,
        current_phase='Not evaluated yet',
        cycle_verdict='Sky cycle data pending backend contract.',
        time_range_label='Time range not evaluated yet',
        note='This report is a read-only product prototype. It does not evaluate real cycle boundaries, source coverage, moments, outputs, or health.',
        is_placeholder=True,
    ).to_dict()


def _build_sky_cycle_phase_timeline():
    phases = (
        SkyCyclePhase(
            id='sky_cycle.phase.day',
            label='Day',
            phase='day',
            status='not_evaluated',
            data_status=NOW_DATA_STATUS_NOT_EVALUATED,
            time_range_label='Day range not evaluated yet',
            note='Day phase placeholder pending a bounded Sky Cycle backend contract.',
            is_placeholder=True,
        ),
        SkyCyclePhase(
            id='sky_cycle.phase.sunset_twilight',
            label='Sunset / Twilight',
            phase='sunset_twilight',
            status='not_evaluated',
            data_status=NOW_DATA_STATUS_NOT_EVALUATED,
            time_range_label='Twilight range not evaluated yet',
            note='Twilight classification is not evaluated in this prototype.',
            is_placeholder=True,
        ),
        SkyCyclePhase(
            id='sky_cycle.phase.night',
            label='Night',
            phase='night',
            status='not_evaluated',
            data_status=NOW_DATA_STATUS_NOT_EVALUATED,
            time_range_label='Night range not evaluated yet',
            note='Night phase placeholder pending a bounded Sky Cycle backend contract.',
            is_placeholder=True,
        ),
        SkyCyclePhase(
            id='sky_cycle.phase.sunrise_twilight',
            label='Sunrise / Twilight',
            phase='sunrise_twilight',
            status='not_evaluated',
            data_status=NOW_DATA_STATUS_NOT_EVALUATED,
            time_range_label='Twilight range not evaluated yet',
            note='Sunrise twilight classification is not evaluated in this prototype.',
            is_placeholder=True,
        ),
    )

    return [phase.to_dict() for phase in phases]


def _build_sky_cycle_moments_summary():
    return NowSection(
        id='sky_cycle.moments.placeholder',
        label='Notable Moments',
        status='Moment detection not connected yet.',
        data_status=NOW_DATA_STATUS_FUTURE_CONTRACT,
        is_placeholder=True,
        summary='Meteors, clouds, lightning, clear windows, anomalies, and other moments require a future MomentSummary backend contract.',
        note='No detector evidence is evaluated by this prototype.',
    ).to_dict()


def _build_sky_cycle_outputs_summary():
    return NowSection(
        id='sky_cycle.outputs.placeholder',
        label='Generated Outputs',
        status='Generated outputs pending rendering contract.',
        data_status=NOW_DATA_STATUS_FUTURE_CONTRACT,
        is_placeholder=True,
        summary='Best image, timelapse, keogram, startrail, and highlight readiness are not evaluated yet.',
        note='No media generation, conversion, preview lookup, or filesystem read is performed.',
    ).to_dict()


def _build_sky_cycle_observatory_health_summary():
    return NowSection(
        id='sky_cycle.observatory_health.placeholder',
        label='Observatory Health',
        status='Observatory health not evaluated yet.',
        data_status=NOW_DATA_STATUS_FUTURE_CONTRACT,
        is_placeholder=True,
        summary='Camera, storage, source preservation, generation, upload, and integration health require bounded backend summaries.',
        note='No runtime service checks are performed by this prototype.',
    ).to_dict()


def _build_sky_cycle_attention_items():
    return NowSection(
        id='sky_cycle.attention.placeholder',
        label='Attention Items',
        status='No attention data connected yet.',
        data_status=NOW_DATA_STATUS_FUTURE_CONTRACT,
        is_placeholder=True,
        summary='Warnings and blocked items will be summarized here after a safe AttentionItem backend contract exists.',
        note='No notification, task, or safe-action execution is connected.',
    ).to_dict()


def _build_sky_cycle_metadata():
    return {
        'contract': 'SkyCycleReportView',
        'contract_version': 'v1.static',
        'source': 'build_sky_cycle_report_view',
        'data_status': NOW_DATA_STATUS_PLACEHOLDER,
        'is_placeholder': True,
    }


def _build_latest_frame_no_row_summary():
    return LatestFrameSummary(
        id='latest_frame.no_row',
        label='Latest Frame Summary',
        status='No recent frame metadata available.',
        data_status=NOW_DATA_STATUS_NOT_EVALUATED,
        camera_label='Camera not evaluated yet',
        profile_label='Profile not evaluated yet',
        timestamp='Not evaluated yet',
        age_label='Not evaluated yet',
        image_available=False,
        safe_preview_url=None,
        source_status='Source status not evaluated yet.',
        note='Repository returned no latest frame metadata.',
        evidence='No bounded latest frame row is available from the injected repository.',
        is_placeholder=True,
    ).to_dict()


def _build_latest_frame_repository_error_summary():
    return LatestFrameSummary(
        id='latest_frame.repository_error',
        label='Latest Frame Summary',
        status='Latest frame metadata unavailable.',
        data_status=NOW_DATA_STATUS_NOT_EVALUATED,
        camera_label='Camera not evaluated yet',
        profile_label='Profile not evaluated yet',
        timestamp='Not evaluated yet',
        age_label='Not evaluated yet',
        image_available=False,
        safe_preview_url=None,
        source_status='Repository error.',
        note='Latest frame repository failed; error details are not exposed.',
        evidence='Provider returned a redacted repository error.',
        is_placeholder=True,
    ).to_dict()


def _build_latest_frame_rejected_summary():
    return LatestFrameSummary(
        id='latest_frame.rejected',
        label='Latest Frame Summary',
        status='Latest frame metadata rejected.',
        data_status=NOW_DATA_STATUS_NOT_EVALUATED,
        camera_label='Camera not evaluated yet',
        profile_label='Profile not evaluated yet',
        timestamp='Not evaluated yet',
        age_label='Not evaluated yet',
        image_available=False,
        safe_preview_url=None,
        source_status='Repository metadata rejected.',
        note='Latest frame repository returned unsafe or unsupported metadata.',
        evidence='No unsafe repository values are exposed in the NowView payload.',
        is_placeholder=True,
    ).to_dict()


def _build_sky_cycle_briefing():
    return SkyCycleBriefingSection(
        id='sky_cycle.placeholder',
        label='Latest Sky Cycle Briefing',
        verdict_label='Cycle Verdict',
        verdict='Observation data not evaluated yet',
        source_coverage='Source coverage pending backend contract',
        outputs_status='Generated output status pending rendering contract',
        notable_moments_count='Moment evidence pending detector contract',
        summary='A future SkyCycleSummary will turn day, twilight, night, moments, outputs, and observatory health into a bounded briefing.',
        data_status=NOW_DATA_STATUS_FUTURE_CONTRACT,
        is_placeholder=True,
    ).to_dict()


def _build_primary_question_answers():
    return [
        PrimaryQuestionAnswer(
            id='answer.what_happened.placeholder',
            question='What happened?',
            answer='Observation data not evaluated yet.',
            evidence='No Sky Cycle or Moment evidence is connected to this prototype.',
            data_status=NOW_DATA_STATUS_FUTURE_CONTRACT,
            is_placeholder=True,
        ).to_dict(),
        PrimaryQuestionAnswer(
            id='answer.worth_reviewing.placeholder',
            question='What is worth reviewing?',
            answer='No detector evidence connected yet.',
            evidence='Future moments will rank meteor, storm, cloud, clear-window, and anomaly candidates.',
            data_status=NOW_DATA_STATUS_FUTURE_CONTRACT,
            is_placeholder=True,
        ).to_dict(),
        PrimaryQuestionAnswer(
            id='answer.sources_trust.placeholder',
            question='Can I trust the sources?',
            answer='Source coverage pending backend contract.',
            evidence='Future SourceLineage and preservation summaries will report bounded source confidence.',
            data_status=NOW_DATA_STATUS_FUTURE_CONTRACT,
            is_placeholder=True,
        ).to_dict(),
        PrimaryQuestionAnswer(
            id='answer.attention.placeholder',
            question='Does anything need attention?',
            answer='Observatory health summarized from placeholder data.',
            evidence='Future AttentionItems will summarize camera, storage, generation, and integration warnings.',
            data_status=NOW_DATA_STATUS_PLACEHOLDER,
            is_placeholder=True,
        ).to_dict(),
    ]


def _build_evidence_summary():
    return NowSection(
        id='evidence.placeholder',
        label='Evidence Summary',
        status='No evidence connected yet',
        summary='Detector, analytics, output, and source-lineage evidence are intentionally not connected in this prototype.',
        note='Future NowView evidence should be bounded, cached, and safe for Raspberry Pi 5.',
        data_status=NOW_DATA_STATUS_FUTURE_CONTRACT,
        is_placeholder=True,
    ).to_dict()


def _build_science_context():
    return NowSection(
        id='science_context.placeholder',
        label='Science Context',
        status='Pending analytics contract',
        summary='SQM, ADU, cloud, phase, and quality context will be reported after a safe science summary contract exists.',
        note='No raw measurements or unbounded analytics are evaluated here.',
        data_status=NOW_DATA_STATUS_FUTURE_CONTRACT,
        is_placeholder=True,
    ).to_dict()


def _build_astrophoto_context():
    return NowSection(
        id='astrophoto_context.placeholder',
        label='Astrophoto Context',
        status='Pending rendering contract',
        summary='Looks, output recipes, and generated media readiness will be summarized after the rendering contract exists.',
        note='No image processing or media generation is triggered by Now.',
        data_status=NOW_DATA_STATUS_FUTURE_CONTRACT,
        is_placeholder=True,
    ).to_dict()


def _build_notable_moments():
    return [
        NowMoment(
            id='moment.meteor_candidate.placeholder',
            label='Meteor candidate',
            confidence='Not evaluated',
            evidence='No detector evidence connected yet',
            status='Pending detector contract',
            data_status=NOW_DATA_STATUS_FUTURE_CONTRACT,
            is_placeholder=True,
        ).to_dict(),
        NowMoment(
            id='moment.lightning_storm.placeholder',
            label='Lightning or storm candidate',
            confidence='Not evaluated',
            evidence='No storm or lightning evidence connected yet',
            status='Pending weather/sky evidence contract',
            data_status=NOW_DATA_STATUS_FUTURE_CONTRACT,
            is_placeholder=True,
        ).to_dict(),
        NowMoment(
            id='moment.clear_window.placeholder',
            label='Clear window',
            confidence='Not evaluated',
            evidence='No sky quality timeline connected yet',
            status='Pending analytics contract',
            data_status=NOW_DATA_STATUS_FUTURE_CONTRACT,
            is_placeholder=True,
        ).to_dict(),
        NowMoment(
            id='moment.anomaly.placeholder',
            label='Anomaly',
            confidence='Not evaluated',
            evidence='No observatory anomaly evidence connected yet',
            status='Pending health contract',
            data_status=NOW_DATA_STATUS_FUTURE_CONTRACT,
            is_placeholder=True,
        ).to_dict(),
    ]


def _build_generated_outputs():
    return [
        GeneratedOutput(
            id='output.best_image.placeholder',
            label='Best image',
            status='Generated output status pending rendering contract',
            look='Look not evaluated',
            lineage='Source lineage pending backend contract',
            data_status=NOW_DATA_STATUS_FUTURE_CONTRACT,
            is_placeholder=True,
        ).to_dict(),
        GeneratedOutput(
            id='output.timelapse.placeholder',
            label='Timelapse',
            status='Generated output status pending rendering contract',
            look='Look not evaluated',
            lineage='Source lineage pending backend contract',
            data_status=NOW_DATA_STATUS_FUTURE_CONTRACT,
            is_placeholder=True,
        ).to_dict(),
        GeneratedOutput(
            id='output.keogram.placeholder',
            label='Keogram',
            status='Generated output status pending rendering contract',
            look='Look not evaluated',
            lineage='Source lineage pending backend contract',
            data_status=NOW_DATA_STATUS_FUTURE_CONTRACT,
            is_placeholder=True,
        ).to_dict(),
        GeneratedOutput(
            id='output.startrail.placeholder',
            label='Startrail',
            status='Generated output status pending rendering contract',
            look='Look not evaluated',
            lineage='Source lineage pending backend contract',
            data_status=NOW_DATA_STATUS_FUTURE_CONTRACT,
            is_placeholder=True,
        ).to_dict(),
    ]


def _build_observatory_health():
    return [
        NowSection(
            id='health.camera.placeholder',
            label='Camera',
            status='Not evaluated',
            note='Camera health pending observatory health contract.',
            data_status=NOW_DATA_STATUS_NOT_EVALUATED,
            is_placeholder=True,
        ).to_dict(),
        NowSection(
            id='health.storage.placeholder',
            label='Storage',
            status='Not evaluated',
            note='Storage capacity and retention safety pending backend contract.',
            data_status=NOW_DATA_STATUS_NOT_EVALUATED,
            is_placeholder=True,
        ).to_dict(),
        NowSection(
            id='health.source_preservation.placeholder',
            label='Source preservation',
            status='Source confidence pending',
            note='RAW/FITS/source preservation remains invariant; coverage is not evaluated yet.',
            data_status=NOW_DATA_STATUS_PLACEHOLDER,
            is_placeholder=True,
        ).to_dict(),
        NowSection(
            id='health.generation.placeholder',
            label='Generation',
            status='Not evaluated',
            note='Rendering and generation queue status pending backend contract.',
            data_status=NOW_DATA_STATUS_NOT_EVALUATED,
            is_placeholder=True,
        ).to_dict(),
        NowSection(
            id='health.upload_integration.placeholder',
            label='Upload / integration',
            status='Not evaluated',
            note='Upload and integration health pending safe status contract.',
            data_status=NOW_DATA_STATUS_NOT_EVALUATED,
            is_placeholder=True,
        ).to_dict(),
        NowSection(
            id='health.warnings.placeholder',
            label='Warnings',
            status='Attention summary pending',
            note='Warning state is placeholder-only until AttentionItems are connected.',
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
            note='Real Now data requires sanitized SkyCycle, Moment, Source, Output, and Observatory contracts.',
            data_status=NOW_DATA_STATUS_FUTURE_CONTRACT,
            is_placeholder=True,
        ).to_dict(),
        NowSection(
            id='attention.safe_actions.placeholder',
            label='Safe actions unavailable',
            status='Read-only',
            note='No actions are exposed. Future interactions must use Safe Actions.',
            data_status=NOW_DATA_STATUS_PLACEHOLDER,
            is_placeholder=True,
        ).to_dict(),
        NowSection(
            id='attention.source_lineage.placeholder',
            label='Source lineage placeholder',
            status='Future contract',
            note='Source lineage is shown as a product requirement, not evaluated data.',
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


def _sanitize_latest_frame_metadata(metadata):
    if not isinstance(metadata, dict):
        raise ValueError('latest frame metadata must be a dict')

    metadata_keys = set(metadata.keys())
    unsupported_keys = metadata_keys.difference(NOW_LATEST_FRAME_REPOSITORY_KEYS)
    if unsupported_keys:
        raise ValueError('latest frame metadata contains unsupported keys')

    for key, value in metadata.items():
        key_lower = str(key).lower()
        if any(token in key_lower for token in NOW_SENSITIVE_KEY_TOKENS):
            raise ValueError('latest frame metadata contains sensitive keys')

        if _latest_frame_value_is_unsafe(value):
            raise ValueError('latest frame metadata contains unsafe values')

    return {
        'camera_label': _latest_frame_text(metadata.get('camera_label'), 'Camera not evaluated yet'),
        'profile_label': _latest_frame_text(metadata.get('profile_label'), 'Profile not evaluated yet'),
        'timestamp': _latest_frame_text(metadata.get('timestamp'), 'Not evaluated yet'),
        'age_label': _latest_frame_text(metadata.get('age_label'), 'Not evaluated yet'),
        'image_available': bool(metadata.get('image_available', False)),
        'source_status': _latest_frame_text(metadata.get('source_status'), 'Source status not evaluated yet.'),
    }


def _latest_frame_text(value, fallback):
    if value in (None, ''):
        return fallback

    if not isinstance(value, str):
        return fallback

    value = value.strip()
    if not value:
        return fallback

    return value


def _latest_frame_timestamp_label(value):
    if value in (None, ''):
        return 'Not evaluated yet'

    if hasattr(value, 'strftime'):
        return value.strftime('%Y-%m-%d %H:%M:%S')

    return _latest_frame_text(value, 'Not evaluated yet')


def _latest_frame_age_label(value, clock):
    if value in (None, '') or not callable(clock):
        return 'Not evaluated yet'

    try:
        age_seconds = int((clock() - value).total_seconds())
    except Exception:
        return 'Not evaluated yet'

    if age_seconds < 0:
        return 'Not evaluated yet'

    if age_seconds < 60:
        return '{0:d} seconds ago'.format(age_seconds)

    age_minutes = int(age_seconds / 60)
    if age_minutes < 60:
        return '{0:d} minutes ago'.format(age_minutes)

    age_hours = int(age_minutes / 60)
    return '{0:d} hours ago'.format(age_hours)


def _latest_frame_value_is_unsafe(value):
    value_text = json.dumps(value, sort_keys=True).lower()
    if NOW_ABSOLUTE_PATH_RE.search(value_text) or NOW_WINDOWS_PATH_RE.search(value_text):
        return True

    if any(token in value_text for token in NOW_SUSPICIOUS_URL_TOKENS):
        return True

    if any(token in value_text for token in NOW_SENSITIVE_KEY_TOKENS):
        return True

    return False


def _validate_latest_frame_summary(summary):
    if not isinstance(summary, dict):
        raise ValueError('latest_frame_summary must be a dict')

    missing_keys = sorted(NOW_LATEST_FRAME_REQUIRED_KEYS.difference(summary.keys()))
    if missing_keys:
        raise ValueError('latest_frame_summary missing required keys: {0:s}'.format(', '.join(missing_keys)))

    if summary['data_status'] not in NOW_ALLOWED_DATA_STATUSES:
        raise ValueError('Invalid data_status at now.latest_frame_summary: {0!r}'.format(summary['data_status']))

    safe_preview_url = summary.get('safe_preview_url')
    if safe_preview_url is None:
        return

    if not isinstance(safe_preview_url, str):
        raise ValueError('latest_frame_summary.safe_preview_url must be null or string metadata')

    safe_preview_url_lower = safe_preview_url.lower()
    if safe_preview_url.startswith('/') or safe_preview_url.startswith('~'):
        raise ValueError('latest_frame_summary.safe_preview_url cannot be an absolute path')

    if any(token in safe_preview_url_lower for token in NOW_SUSPICIOUS_URL_TOKENS):
        raise ValueError('latest_frame_summary.safe_preview_url contains unsafe path metadata')


def _validate_current_phase_summary(summary):
    if not isinstance(summary, dict):
        raise ValueError('current_phase_summary must be a dict')

    missing_keys = sorted(NOW_CURRENT_PHASE_REQUIRED_KEYS.difference(summary.keys()))
    if missing_keys:
        raise ValueError('current_phase_summary missing required keys: {0:s}'.format(', '.join(missing_keys)))

    if summary['phase'] not in NOW_ALLOWED_PHASES:
        raise ValueError('Invalid phase at now.current_phase_summary: {0!r}'.format(summary['phase']))

    if summary['data_status'] not in NOW_ALLOWED_DATA_STATUSES:
        raise ValueError('Invalid data_status at now.current_phase_summary: {0!r}'.format(summary['data_status']))

    if not isinstance(summary['supported_phases'], list):
        raise ValueError('current_phase_summary.supported_phases must be a list')

    if not isinstance(summary['unsupported_phases'], list):
        raise ValueError('current_phase_summary.unsupported_phases must be a list')


def _validate_source_confidence_summary(summary):
    if not isinstance(summary, dict):
        raise ValueError('source_confidence_summary must be a dict')

    missing_keys = sorted(NOW_SOURCE_CONFIDENCE_REQUIRED_KEYS.difference(summary.keys()))
    if missing_keys:
        raise ValueError('source_confidence_summary missing required keys: {0:s}'.format(', '.join(missing_keys)))

    if summary['data_status'] not in NOW_ALLOWED_DATA_STATUSES:
        raise ValueError('Invalid data_status at now.source_confidence_summary: {0!r}'.format(summary['data_status']))

    if summary['risk_level'] not in NOW_ALLOWED_RISK_LEVELS:
        raise ValueError('Invalid risk_level at now.source_confidence_summary: {0!r}'.format(summary['risk_level']))

    if not isinstance(summary['source_types'], list):
        raise ValueError('source_confidence_summary.source_types must be a list')

    if not isinstance(summary['evidence'], list):
        raise ValueError('source_confidence_summary.evidence must be a list')


def _validate_sky_cycle_summary(summary):
    if not isinstance(summary, dict):
        raise ValueError('cycle_summary must be a dict')

    missing_keys = sorted(SKY_CYCLE_SUMMARY_REQUIRED_KEYS.difference(summary.keys()))
    if missing_keys:
        raise ValueError('cycle_summary missing required keys: {0:s}'.format(', '.join(missing_keys)))

    if summary['data_status'] not in NOW_ALLOWED_DATA_STATUSES:
        raise ValueError('Invalid data_status at sky_cycle.cycle_summary: {0!r}'.format(summary['data_status']))


def _validate_sky_cycle_phase_timeline(phase_timeline):
    if not isinstance(phase_timeline, list):
        raise ValueError('phase_timeline must be a list')

    if not phase_timeline:
        raise ValueError('phase_timeline must not be empty')

    for index, phase in enumerate(phase_timeline):
        if not isinstance(phase, dict):
            raise ValueError('phase_timeline[{0:d}] must be a dict'.format(index))

        missing_keys = sorted(SKY_CYCLE_PHASE_REQUIRED_KEYS.difference(phase.keys()))
        if missing_keys:
            raise ValueError('phase_timeline[{0:d}] missing required keys: {1:s}'.format(index, ', '.join(missing_keys)))

        if phase['data_status'] not in NOW_ALLOWED_DATA_STATUSES:
            raise ValueError('Invalid data_status at sky_cycle.phase_timeline[{0:d}]: {1!r}'.format(index, phase['data_status']))


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
