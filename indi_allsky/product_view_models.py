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
    'current_capture_summary',
    'latest_frame_summary',
    'latest_camera_frames',
    'latest_generated_output_summary',
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
    'current_capture_summary',
    'latest_frame_summary',
    'latest_camera_frames',
    'latest_generated_output_summary',
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
NOW_SUSPICIOUS_URL_TOKENS = frozenset(('..', 'file:', 'http://', 'https://', '\\'))

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
    'frame_metadata',
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
    'frame_metadata',
))

NOW_LATEST_FRAME_METADATA_KEYS = frozenset((
    'id',
    'camera_id',
    'timestamp',
    'exposure',
    'gain',
    'binmode',
    'temp',
    'night',
    'adu',
    'sqm',
    'stars',
    'detections',
    'file_size',
    'width',
    'height',
))

NOW_LATEST_CAMERA_FRAMES_REQUIRED_KEYS = frozenset((
    'id',
    'label',
    'status',
    'data_status',
    'items',
    'note',
    'is_placeholder',
))

NOW_LATEST_CAMERA_FRAME_ITEM_KEYS = frozenset((
    'camera_id',
    'camera_label',
    'timestamp',
    'age_label',
    'image_available',
    'safe_image_url',
    'source_status',
    'note',
))

NOW_SAFE_WEB_ROUTE_KEYS = frozenset((
    'safe_image_url',
))

NOW_LATEST_GENERATED_OUTPUT_REQUIRED_KEYS = frozenset((
    'id',
    'label',
    'status',
    'data_status',
    'output_type',
    'timestamp',
    'day_date',
    'generation_status',
    'uploaded',
    'success',
    'frames',
    'framerate',
    'file_size',
    'width',
    'height',
    'source_table_label',
    'note',
    'is_placeholder',
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

NOW_CURRENT_CAPTURE_REQUIRED_KEYS = frozenset((
    'id',
    'label',
    'status',
    'data_status',
    'capture_state',
    'is_acquiring',
    'camera_label',
    'phase',
    'policy_label',
    'last_frame_status',
    'coherence_label',
    'source_status',
    'note',
    'evidence',
    'is_placeholder',
))

NOW_CAPTURE_STATE_RUNNING = 'running'
NOW_CAPTURE_STATE_IDLE = 'idle'
NOW_CAPTURE_STATE_PAUSED = 'paused'
NOW_CAPTURE_STATE_ERROR = 'error'
NOW_CAPTURE_STATE_UNKNOWN = 'unknown'

NOW_ALLOWED_CAPTURE_STATES = frozenset((
    NOW_CAPTURE_STATE_RUNNING,
    NOW_CAPTURE_STATE_IDLE,
    NOW_CAPTURE_STATE_PAUSED,
    NOW_CAPTURE_STATE_ERROR,
    NOW_CAPTURE_STATE_UNKNOWN,
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
    'retention_status',
    'lineage_status',
    'gap_status',
    'risk_level',
    'note',
    'evidence',
    'next_backend_contract',
    'is_placeholder',
))

NOW_SOURCE_TRUST_TYPES = frozenset((
    'fits_source',
    'raw_source',
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
    'cycle_status',
    'cycle_verdict',
    'cycle_started_label',
    'latest_frame_label',
    'time_range_label',
    'coverage_label',
    'confidence_label',
    'evidence',
    'note',
    'is_placeholder',
))

SKY_CYCLE_STATUS_UNKNOWN = 'unknown'
SKY_CYCLE_STATUS_IN_PROGRESS = 'in_progress'
SKY_CYCLE_STATUS_COMPLETED = 'completed'
SKY_CYCLE_STATUS_INCOMPLETE = 'incomplete'

SKY_CYCLE_ALLOWED_STATUSES = frozenset((
    SKY_CYCLE_STATUS_UNKNOWN,
    SKY_CYCLE_STATUS_IN_PROGRESS,
    SKY_CYCLE_STATUS_COMPLETED,
    SKY_CYCLE_STATUS_INCOMPLETE,
))

SKY_CYCLE_PHASE_REQUIRED_KEYS = frozenset((
    'id',
    'label',
    'phase',
    'status',
    'data_status',
    'time_range_label',
    'observation_value',
    'source_expectation',
    'output_expectation',
    'science_note',
    'astrophoto_note',
    'supported',
    'unsupported_reason',
    'note',
    'is_placeholder',
))

SKY_CYCLE_ALLOWED_PHASES = frozenset((
    'day',
    'sunset_twilight',
    'night',
    'sunrise_twilight',
    'unknown',
))

SKY_CYCLE_MOMENTS_REQUIRED_KEYS = frozenset((
    'id',
    'label',
    'status',
    'data_status',
    'count_label',
    'primary_moment',
    'moment_categories',
    'review_queue_status',
    'detection_status',
    'note',
    'items',
    'is_placeholder',
))

SKY_CYCLE_MOMENT_ITEM_REQUIRED_KEYS = frozenset((
    'id',
    'type',
    'label',
    'phase',
    'data_status',
    'time_label',
    'confidence_label',
    'evidence',
    'source_lineage_status',
    'related_outputs_status',
    'science_note',
    'astrophoto_note',
    'review_status',
    'is_placeholder',
))

SKY_CYCLE_ALLOWED_MOMENT_TYPES = frozenset((
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
))

SKY_CYCLE_OUTPUTS_REQUIRED_KEYS = frozenset((
    'id',
    'label',
    'status',
    'data_status',
    'count_label',
    'generation_status',
    'look_policy_status',
    'share_readiness_status',
    'note',
    'items',
    'is_placeholder',
))

SKY_CYCLE_OUTPUT_ITEM_REQUIRED_KEYS = frozenset((
    'id',
    'type',
    'label',
    'phase',
    'data_status',
    'generation_status',
    'look_applied',
    'source_lineage_status',
    'related_moments_status',
    'share_status',
    'quality_note',
    'astrophoto_note',
    'science_note',
    'safe_actions_available',
    'is_placeholder',
))

SKY_CYCLE_HEALTH_REQUIRED_KEYS = frozenset((
    'id',
    'label',
    'status',
    'data_status',
    'overall_label',
    'camera_status',
    'capture_status',
    'storage_status',
    'generation_status',
    'integration_status',
    'warnings_count_label',
    'risk_level',
    'evidence',
    'note',
    'is_placeholder',
))

SKY_CYCLE_ALLOWED_OUTPUT_TYPES = frozenset((
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
))

HIGHLIGHTS_REQUIRED_KEYS = frozenset((
    'id',
    'label',
    'status',
    'data_status',
    'generated_at',
    'is_placeholder',
    'safe_actions_available',
    'highlights_summary',
    'highlight_items',
    'source_trust_summary',
    'review_queue_summary',
    'selection_policy_summary',
    'attention_items',
    'metadata',
))

HIGHLIGHTS_REQUIRED_SECTIONS = frozenset((
    'highlights_summary',
    'source_trust_summary',
    'review_queue_summary',
    'selection_policy_summary',
    'attention_items',
))

HIGHLIGHTS_SUMMARY_REQUIRED_KEYS = frozenset((
    'id',
    'label',
    'title',
    'data_status',
    'count_label',
    'primary_highlight',
    'attention_verdict',
    'note',
    'is_placeholder',
))

HIGHLIGHT_ITEM_REQUIRED_KEYS = frozenset((
    'highlight_id',
    'title',
    'type',
    'target_kind',
    'target_label',
    'data_status',
    'origin',
    'selection_reason',
    'confidence_label',
    'evidence',
    'phase',
    'sky_cycle_context',
    'source_trust_status',
    'related_output_status',
    'favorite_status',
    'review_status',
    'safe_actions_available',
    'is_placeholder',
))

HIGHLIGHTS_SOURCE_TRUST_REQUIRED_KEYS = frozenset((
    'id',
    'label',
    'status',
    'data_status',
    'coverage_label',
    'preservation_status',
    'lineage_status',
    'risk_level',
    'evidence',
    'note',
    'is_placeholder',
))

HIGHLIGHTS_REVIEW_QUEUE_REQUIRED_KEYS = frozenset((
    'id',
    'label',
    'status',
    'data_status',
    'count_label',
    'suggested_count_label',
    'confirmed_count_label',
    'favorite_count_label',
    'ignored_count_label',
    'note',
    'is_placeholder',
))

HIGHLIGHTS_SELECTION_POLICY_REQUIRED_KEYS = frozenset((
    'id',
    'label',
    'status',
    'data_status',
    'policy_label',
    'explainability_status',
    'reversibility_status',
    'allowed_origins',
    'note',
    'is_placeholder',
))

HIGHLIGHT_ALLOWED_TYPES = frozenset((
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
))

HIGHLIGHT_ALLOWED_TARGET_KINDS = frozenset((
    'moment',
    'output',
    'source',
    'sky_cycle',
    'observatory_issue',
    'unknown',
))

HIGHLIGHT_ALLOWED_ORIGINS = frozenset((
    'hybrid_suggested',
    'user_selected',
    'future_ai',
    'detector',
    'rule',
    'unknown',
))

HIGHLIGHT_METADATA_ALLOWED_FIELDS = frozenset((
    'id',
    'camera_id',
    'timestamp',
    'day_date',
    'night',
    'detections',
    'stars',
    'sqm',
    'adu',
    'kpindex',
    'ovation_max',
    'smoke_rating',
    'moonmode',
    'stable',
    'exclude',
    'width',
    'height',
))

MOMENT_DETAIL_REQUIRED_KEYS = frozenset((
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
))

MOMENT_DETAIL_REQUIRED_SECTIONS = frozenset((
    'moment_summary',
    'evidence_summary',
    'source_trust_summary',
    'related_outputs',
    'sky_cycle_context',
    'observatory_context',
))

MOMENT_DETAIL_SUMMARY_REQUIRED_KEYS = frozenset((
    'id',
    'label',
    'title',
    'type',
    'phase',
    'timestamp_label',
    'confidence_label',
    'data_status',
    'selection_reason',
    'note',
    'is_placeholder',
))

MOMENT_DETAIL_EVIDENCE_REQUIRED_KEYS = frozenset((
    'id',
    'label',
    'data_status',
    'evidence',
    'detector_status',
    'explanation',
    'science_note',
    'is_placeholder',
))

MOMENT_DETAIL_SOURCE_TRUST_REQUIRED_KEYS = frozenset((
    'id',
    'label',
    'data_status',
    'source_status',
    'lineage_status',
    'preservation_status',
    'confidence',
    'note',
    'is_placeholder',
))

MOMENT_DETAIL_RELATED_OUTPUTS_REQUIRED_KEYS = frozenset((
    'id',
    'label',
    'data_status',
    'generation_status',
    'look_status',
    'outputs',
    'note',
    'is_placeholder',
))

MOMENT_DETAIL_OUTPUT_REQUIRED_KEYS = frozenset((
    'id',
    'label',
    'type',
    'status',
    'data_status',
    'source_lineage_status',
    'is_placeholder',
))

MOMENT_DETAIL_SKY_CYCLE_REQUIRED_KEYS = frozenset((
    'id',
    'label',
    'data_status',
    'phase',
    'cycle_label',
    'position_in_cycle',
    'note',
    'is_placeholder',
))

MOMENT_DETAIL_OBSERVATORY_REQUIRED_KEYS = frozenset((
    'id',
    'label',
    'data_status',
    'camera',
    'capture',
    'health_summary',
    'note',
    'is_placeholder',
))

MOMENT_DETAIL_ALLOWED_TYPES = frozenset((
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
))

MOMENT_DETAIL_ALLOWED_OUTPUT_TYPES = frozenset((
    'best_image',
    'latest_image',
    'timelapse',
    'keogram',
    'startrail',
    'highlight_clip',
    'unknown',
))

OUTPUT_DETAIL_REQUIRED_KEYS = frozenset((
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
))

OUTPUT_DETAIL_REQUIRED_SECTIONS = frozenset((
    'output_summary',
    'preview_summary',
    'recipe_summary',
    'source_lineage_summary',
    'related_moments',
    'sky_cycle_context',
    'share_readiness_summary',
))

OUTPUT_DETAIL_SUMMARY_REQUIRED_KEYS = frozenset((
    'id',
    'label',
    'title',
    'type',
    'data_status',
    'generation_status',
    'phase',
    'sky_cycle_label',
    'note',
    'is_placeholder',
))

OUTPUT_DETAIL_PREVIEW_REQUIRED_KEYS = frozenset((
    'id',
    'label',
    'preview_status',
    'data_status',
    'preview_available',
    'safe_preview_url',
    'note',
    'is_placeholder',
))

OUTPUT_DETAIL_RECIPE_REQUIRED_KEYS = frozenset((
    'id',
    'label',
    'data_status',
    'look_applied',
    'recipe_status',
    'rendering_intent',
    'non_destructive_status',
    'version_label',
    'note',
    'is_placeholder',
))

OUTPUT_DETAIL_SOURCE_LINEAGE_REQUIRED_KEYS = frozenset((
    'id',
    'label',
    'data_status',
    'source_status',
    'lineage_status',
    'source_types',
    'source_coverage_label',
    'preservation_status',
    'trust_level',
    'evidence',
    'is_placeholder',
))

OUTPUT_DETAIL_RELATED_MOMENTS_REQUIRED_KEYS = frozenset((
    'id',
    'label',
    'data_status',
    'relation_status',
    'items',
    'note',
    'is_placeholder',
))

OUTPUT_DETAIL_RELATED_MOMENT_REQUIRED_KEYS = frozenset((
    'id',
    'label',
    'type',
    'phase',
    'data_status',
    'relation_label',
    'confidence_label',
    'is_placeholder',
))

OUTPUT_DETAIL_SKY_CYCLE_REQUIRED_KEYS = frozenset((
    'id',
    'label',
    'data_status',
    'cycle_label',
    'phase',
    'time_range_label',
    'context_status',
    'is_placeholder',
))

OUTPUT_DETAIL_SHARE_READINESS_REQUIRED_KEYS = frozenset((
    'id',
    'label',
    'status',
    'data_status',
    'export_status',
    'share_status',
    'limitations',
    'safe_actions_available',
    'is_placeholder',
))

OUTPUT_DETAIL_ALLOWED_TYPES = frozenset((
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
))

OUTPUT_DETAIL_ALLOWED_TRUST_LEVELS = frozenset((
    'unknown',
    'low',
    'medium',
    'high',
))

LIBRARY_REQUIRED_KEYS = frozenset((
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
))

LIBRARY_REQUIRED_SECTIONS = frozenset((
    'library_summary',
    'collection_summary',
    'search_summary',
    'filter_summary',
    'recent_items',
    'memory_model_summary',
))

LIBRARY_SUMMARY_REQUIRED_KEYS = frozenset((
    'id',
    'label',
    'title',
    'data_status',
    'scope_label',
    'total_items_label',
    'note',
    'is_placeholder',
))

LIBRARY_COLLECTION_SUMMARY_REQUIRED_KEYS = frozenset((
    'id',
    'label',
    'data_status',
    'collections',
    'note',
    'is_placeholder',
))

LIBRARY_COLLECTION_REQUIRED_KEYS = frozenset((
    'key',
    'label',
    'type',
    'data_status',
    'count_label',
    'description',
    'example_query',
    'is_placeholder',
))

LIBRARY_SEARCH_SUMMARY_REQUIRED_KEYS = frozenset((
    'id',
    'label',
    'data_status',
    'search_status',
    'indexed_fields',
    'unavailable_reason',
    'note',
    'is_placeholder',
))

LIBRARY_FILTER_SUMMARY_REQUIRED_KEYS = frozenset((
    'id',
    'label',
    'data_status',
    'available_filters',
    'disabled_filters',
    'note',
    'is_placeholder',
))

LIBRARY_RECENT_ITEMS_REQUIRED_KEYS = frozenset((
    'id',
    'label',
    'data_status',
    'items',
    'note',
    'is_placeholder',
))

LIBRARY_RECENT_ITEM_REQUIRED_KEYS = frozenset((
    'item_id',
    'title',
    'kind',
    'data_status',
    'date_label',
    'phase',
    'highlight_status',
    'source_trust_status',
    'output_status',
    'note',
    'is_placeholder',
))

LIBRARY_MEMORY_MODEL_REQUIRED_KEYS = frozenset((
    'id',
    'label',
    'data_status',
    'status',
    'explanation',
    'future_favorites_status',
    'future_tags_status',
    'future_saved_searches_status',
    'is_placeholder',
))

LIBRARY_ALLOWED_KINDS = frozenset((
    'highlight',
    'moment',
    'output',
    'sky_cycle',
    'source',
    'favorite',
    'unknown',
))

LIBRARY_ALLOWED_COLLECTION_TYPES = frozenset((
    'highlights',
    'moments',
    'outputs',
    'sky_cycles',
    'favorites',
    'source_backed',
    'phenomena',
    'unknown',
))

OBSERVATORY_REQUIRED_KEYS = frozenset((
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
))

OBSERVATORY_REQUIRED_SECTIONS = frozenset((
    'observatory_summary',
    'camera_system_summary',
    'capture_pipeline_summary',
    'source_preservation_summary',
    'storage_summary',
    'generation_summary',
    'integration_summary',
    'attention_items',
))

OBSERVATORY_SUMMARY_REQUIRED_KEYS = frozenset((
    'id',
    'label',
    'title',
    'data_status',
    'overall_status',
    'readiness_label',
    'note',
    'is_placeholder',
))

OBSERVATORY_CAMERA_SYSTEM_REQUIRED_KEYS = frozenset((
    'id',
    'label',
    'status',
    'data_status',
    'camera_label',
    'profile_label',
    'capture_status',
    'backend_status',
    'note',
    'is_placeholder',
))

OBSERVATORY_CAPTURE_PIPELINE_REQUIRED_KEYS = frozenset((
    'id',
    'label',
    'status',
    'data_status',
    'latest_frame_status',
    'cadence_status',
    'day_night_status',
    'note',
    'is_placeholder',
))

OBSERVATORY_SOURCE_PRESERVATION_REQUIRED_KEYS = frozenset((
    'id',
    'label',
    'status',
    'data_status',
    'preservation_label',
    'raw_status',
    'fits_status',
    'lineage_status',
    'trust_level',
    'note',
    'is_placeholder',
))

OBSERVATORY_STORAGE_REQUIRED_KEYS = frozenset((
    'id',
    'label',
    'status',
    'data_status',
    'storage_label',
    'retention_status',
    'risk_level',
    'note',
    'is_placeholder',
))

OBSERVATORY_GENERATION_REQUIRED_KEYS = frozenset((
    'id',
    'label',
    'status',
    'data_status',
    'outputs_status',
    'queue_status',
    'rendering_status',
    'note',
    'is_placeholder',
))

OBSERVATORY_INTEGRATION_REQUIRED_KEYS = frozenset((
    'id',
    'label',
    'status',
    'data_status',
    'upload_status',
    'remote_status',
    'notification_status',
    'note',
    'is_placeholder',
))

OBSERVATORY_ATTENTION_REQUIRED_KEYS = frozenset((
    'id',
    'label',
    'data_status',
    'items',
    'note',
    'is_placeholder',
))

OBSERVATORY_ATTENTION_ITEM_REQUIRED_KEYS = frozenset((
    'id',
    'label',
    'status',
    'data_status',
    'risk_level',
    'note',
    'is_placeholder',
))

OBSERVATORY_ALLOWED_STATUSES = frozenset((
    'ok',
    'warning',
    'blocked',
    'not_evaluated',
    'unknown',
))

OBSERVATORY_ALLOWED_RISK_LEVELS = NOW_ALLOWED_RISK_LEVELS


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
    frame_metadata: dict
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
    retention_status: str
    lineage_status: str
    gap_status: str
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
    cycle_status: str
    cycle_verdict: str
    cycle_started_label: str
    latest_frame_label: str
    time_range_label: str
    coverage_label: str
    confidence_label: str
    evidence: list
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
    observation_value: str
    source_expectation: str
    output_expectation: str
    science_note: str
    astrophoto_note: str
    supported: bool
    unsupported_reason: str
    note: str
    is_placeholder: bool

    def to_dict(self):
        return asdict(self)


class StaticLatestFrameRepository:
    """Default repository for the static NowView contract."""

    def get_latest_frame_metadata(self):
        return None


class CurrentCaptureStatusRepository:
    """Repository adapter for bounded current capture status metadata."""

    def __init__(
        self,
        status_code=None,
        status_map=None,
        watchdog_age_seconds=None,
        local_camera=True,
        focus_mode=False,
        capture_pause=False,
        daytime_capture=True,
        daytime_capture_save=True,
        camera_label='Camera not evaluated yet',
    ):
        self.status_code = status_code
        self.status_map = dict(status_map or {})
        self.watchdog_age_seconds = watchdog_age_seconds
        self.local_camera = local_camera
        self.focus_mode = focus_mode
        self.capture_pause = capture_pause
        self.daytime_capture = daytime_capture
        self.daytime_capture_save = daytime_capture_save
        self.camera_label = camera_label

    def get_current_capture_metadata(self):
        raw_state = self.status_map.get(self.status_code, NOW_CAPTURE_STATE_UNKNOWN)
        capture_state = self._resolve_capture_state(raw_state)

        return {
            'capture_state': capture_state,
            'is_acquiring': capture_state == NOW_CAPTURE_STATE_RUNNING,
            'camera_label': self.camera_label,
            'policy_label': self._policy_label(),
            'source_status': self._source_status(raw_state),
            'watchdog_age_seconds': _latest_frame_json_value(self.watchdog_age_seconds),
        }

    def _resolve_capture_state(self, raw_state):
        if self.capture_pause:
            return NOW_CAPTURE_STATE_PAUSED

        if not self.local_camera:
            return NOW_CAPTURE_STATE_UNKNOWN

        if self.focus_mode:
            return NOW_CAPTURE_STATE_IDLE

        if raw_state in (
            NOW_CAPTURE_STATE_RUNNING,
            NOW_CAPTURE_STATE_IDLE,
            NOW_CAPTURE_STATE_PAUSED,
            NOW_CAPTURE_STATE_ERROR,
            NOW_CAPTURE_STATE_UNKNOWN,
        ):
            return raw_state

        return NOW_CAPTURE_STATE_UNKNOWN

    def _policy_label(self):
        if self.capture_pause:
            return 'Capture intentionally paused.'

        if not self.local_camera:
            return 'Remote camera mode; local capture state is not authoritative.'

        if self.focus_mode:
            return 'Focus mode active; normal capture status is not evaluated.'

        if not self.daytime_capture:
            return 'Daytime capture disabled by camera policy.'

        if self.daytime_capture and not self.daytime_capture_save:
            return 'Daytime capture enabled, but daytime frame saving is disabled.'

        return 'Capture policy allows normal acquisition.'

    def _source_status(self, raw_state):
        if self.watchdog_age_seconds is None:
            return 'Persisted capture status read; watchdog age not evaluated.'

        if not isinstance(self.watchdog_age_seconds, (int, float)):
            return 'Persisted capture status read; watchdog age unavailable.'

        if self.watchdog_age_seconds > 600:
            return 'Persisted capture watchdog is stale.'

        return 'Persisted capture status and watchdog are available.'


@dataclass(frozen=True)
class GeneratedOutputDescriptor:
    """Descriptor for one bounded generated-output metadata source."""

    output_type: str
    query: object
    order_by_expression: object = None
    camera_id_field: object = None
    source_table_label: str = 'Generated output source'
    field_map: object = None
    status_label: str = None


class LatestGeneratedOutputRepository:
    """Descriptor-based adapter for latest generated output metadata."""

    DEFAULT_FIELD_MAP = {
        'id': 'id',
        'camera_id': 'camera_id',
        'day_date': 'dayDate',
        'night': 'night',
        'uploaded': 'uploaded',
        'success': 'success',
        'frames': 'frames',
        'framerate': 'framerate',
        'file_size': 'fileSize',
        'width': 'width',
        'height': 'height',
    }

    def __init__(self, descriptors=None, camera_id=None):
        self.descriptors = tuple(descriptors or ())
        self.camera_id = camera_id

    def get_latest_generated_output_metadata(self):
        if self.camera_id in (None, ''):
            return _build_latest_generated_output_unavailable('Camera context unavailable.')

        candidates = []
        failure_count = 0

        for descriptor in self.descriptors:
            try:
                candidate = self._metadata_from_descriptor(descriptor)
            except Exception:
                failure_count += 1
                continue

            if candidate is not None:
                candidates.append(candidate)

        if not candidates:
            if failure_count:
                return _build_latest_generated_output_unavailable('Generated output metadata unavailable.')

            return _build_latest_generated_output_empty()

        latest = max(candidates, key=lambda item: item.get('_sort_key', ''))
        latest.pop('_sort_key', None)

        return {
            'status': 'generated_output_available',
            'data_status': NOW_DATA_STATUS_NOT_EVALUATED,
            'output': latest,
            'partial_failures': failure_count,
            'note': 'Latest generated output metadata selected from bounded descriptors.',
        }

    def _metadata_from_descriptor(self, descriptor):
        query = getattr(descriptor, 'query', None)
        if query is None:
            raise ValueError('generated output descriptor missing query')

        camera_id_field = getattr(descriptor, 'camera_id_field', None)
        if camera_id_field is not None:
            query = query.filter(camera_id_field == self.camera_id)

        order_by_expression = getattr(descriptor, 'order_by_expression', None)
        if order_by_expression is not None:
            query = query.order_by(order_by_expression)

        row = query.limit(1).first()
        if not row:
            return None

        return _latest_generated_output_row_metadata(descriptor, row)


@dataclass(frozen=True)
class SourceTrustDescriptor:
    """Descriptor for one bounded source-file metadata source."""

    source_type: str
    query: object
    order_by_expression: object = None
    camera_id_field: object = None
    source_label: str = 'Source metadata'
    field_map: object = None


class SourceTrustRepository:
    """Descriptor-based adapter for bounded RAW/FITS source metadata."""

    DEFAULT_FIELD_MAP = {
        'id': 'id',
        'camera_id': 'camera_id',
        'day_date': 'dayDate',
        'night': 'night',
        'uploaded': 'uploaded',
        'exposure': 'exposure',
        'gain': 'gain',
        'binmode': 'binmode',
        'file_size': 'fileSize',
        'width': 'width',
        'height': 'height',
    }

    def __init__(self, descriptors=None, camera_id=None):
        self.descriptors = tuple(descriptors or ())
        self.camera_id = camera_id

    def get_source_trust_metadata(self):
        if self.camera_id in (None, ''):
            return _build_source_trust_unavailable('Camera context unavailable.')

        sources = []
        failure_count = 0

        for descriptor in self.descriptors:
            try:
                source = self._metadata_from_descriptor(descriptor)
            except Exception:
                failure_count += 1
                continue

            if source is not None:
                sources.append(source)

        if not sources:
            if failure_count:
                return _build_source_trust_unavailable('Source metadata unavailable.')

            return _build_source_trust_empty()

        return {
            'status': 'source_metadata_available',
            'data_status': NOW_DATA_STATUS_NOT_EVALUATED,
            'sources': sources,
            'partial_failures': failure_count,
            'note': 'Source trust is based on bounded RAW/FITS metadata only.',
        }

    def _metadata_from_descriptor(self, descriptor):
        query = getattr(descriptor, 'query', None)
        if query is None:
            raise ValueError('source trust descriptor missing query')

        source_type = getattr(descriptor, 'source_type', NOW_PHASE_UNKNOWN)
        if source_type not in NOW_SOURCE_TRUST_TYPES:
            raise ValueError('source trust descriptor has unsupported source_type')

        camera_id_field = getattr(descriptor, 'camera_id_field', None)
        if camera_id_field is not None:
            query = query.filter(camera_id_field == self.camera_id)

        order_by_expression = getattr(descriptor, 'order_by_expression', None)
        if order_by_expression is not None:
            query = query.order_by(order_by_expression)

        row = query.limit(1).first()
        if not row:
            return None

        return _source_trust_row_metadata(descriptor, row)


class HighlightsMetadataRepository:
    """Bounded adapter for explainable Highlight candidates from image metadata."""

    def __init__(self, query=None, camera_id=None, camera_id_field=None, order_by_expressions=None, max_items=4):
        self.query = query
        self.camera_id = camera_id
        self.camera_id_field = camera_id_field
        self.order_by_expressions = tuple(order_by_expressions or ())
        self.max_items = max(1, min(int(max_items or 4), 8))

    def get_highlight_metadata(self):
        if self.query is None:
            return _build_highlights_metadata_unavailable('Highlight metadata query unavailable.')

        if self.camera_id in (None, ''):
            return _build_highlights_metadata_unavailable('Camera context unavailable.')

        try:
            query = self.query

            if self.camera_id_field is not None:
                query = query.filter(self.camera_id_field == self.camera_id)

            for order_by_expression in self.order_by_expressions:
                query = query.order_by(order_by_expression)

            query = query.limit(self.max_items)
            rows = query.all()
        except Exception:
            return _build_highlights_metadata_unavailable('Highlight metadata query failed.')

        items = []
        for row in rows or []:
            item = _highlight_item_from_image_metadata(_highlight_image_row_metadata(row))
            if item is not None:
                items.append(item)

        if not items:
            return _build_highlights_metadata_empty()

        return {
            'status': 'highlight_metadata_available',
            'data_status': NOW_DATA_STATUS_NOT_EVALUATED,
            'items': items[:self.max_items],
            'note': 'Highlights are generated from bounded image metadata rules.',
        }


class SkyCycleSummaryRepository:
    """Bounded adapter for a minimal Sky Cycle summary from image metadata."""

    def __init__(
        self,
        latest_query=None,
        cycle_start_query=None,
        camera_id=None,
        camera_id_field=None,
        day_date_field=None,
        latest_order_by_expression=None,
        start_order_by_expression=None,
        current_date=None,
    ):
        self.latest_query = latest_query
        self.cycle_start_query = cycle_start_query
        self.camera_id = camera_id
        self.camera_id_field = camera_id_field
        self.day_date_field = day_date_field
        self.latest_order_by_expression = latest_order_by_expression
        self.start_order_by_expression = start_order_by_expression
        self.current_date = current_date

    def get_sky_cycle_metadata(self):
        if self.latest_query is None or self.cycle_start_query is None:
            return _build_sky_cycle_metadata_unavailable('Sky Cycle metadata query unavailable.')

        if self.camera_id in (None, ''):
            return _build_sky_cycle_metadata_unavailable('Camera context unavailable.')

        try:
            latest_query = self.latest_query
            if self.camera_id_field is not None:
                latest_query = latest_query.filter(self.camera_id_field == self.camera_id)
            if self.latest_order_by_expression is not None:
                latest_query = latest_query.order_by(self.latest_order_by_expression)

            latest_row = latest_query.limit(1).first()
        except Exception:
            return _build_sky_cycle_metadata_unavailable('Latest Sky Cycle metadata query failed.')

        if not latest_row:
            return _build_sky_cycle_metadata_empty()

        latest_metadata = _sky_cycle_image_row_metadata(latest_row)
        day_date = latest_metadata.get('day_date')

        start_metadata = {}
        if day_date not in (None, 'Not evaluated yet'):
            try:
                start_query = self.cycle_start_query
                if self.camera_id_field is not None:
                    start_query = start_query.filter(self.camera_id_field == self.camera_id)
                if self.day_date_field is not None:
                    start_query = start_query.filter(self.day_date_field == getattr(latest_row, 'dayDate', None))
                if self.start_order_by_expression is not None:
                    start_query = start_query.order_by(self.start_order_by_expression)

                start_row = start_query.limit(1).first()
                if start_row:
                    start_metadata = _sky_cycle_image_row_metadata(start_row)
            except Exception:
                start_metadata = {}

        return {
            'status': 'sky_cycle_metadata_available',
            'data_status': NOW_DATA_STATUS_NOT_EVALUATED,
            'latest_frame': latest_metadata,
            'cycle_start': start_metadata,
            'current_date': _latest_generated_output_json_value(self.current_date),
            'note': 'Sky Cycle summary is based on bounded image metadata.',
        }


class LatestFrameImageTableRepository:
    """Repository adapter for one bounded latest image metadata row."""

    def __init__(
        self,
        query,
        order_by_expression=None,
        camera_label='Camera not evaluated yet',
        profile_label='Profile not evaluated yet',
        clock=None,
        camera_id=None,
        camera_id_field=None,
    ):
        self.query = query
        self.order_by_expression = order_by_expression
        self.camera_label = camera_label
        self.profile_label = profile_label
        self.clock = clock
        self.camera_id = camera_id
        self.camera_id_field = camera_id_field

    def get_latest_frame_metadata(self):
        bounded_query = self.query

        if self.camera_id is not None and self.camera_id_field is not None:
            bounded_query = bounded_query.filter(self.camera_id_field == self.camera_id)

        if self.order_by_expression is not None:
            bounded_query = bounded_query.order_by(self.order_by_expression)

        bounded_query = bounded_query.limit(1)
        row = bounded_query.first()

        if not row:
            return None

        created_at = getattr(row, 'createDate', None)
        frame_metadata = _latest_frame_row_metadata(row, created_at)

        return {
            'camera_label': self.camera_label,
            'profile_label': self.profile_label,
            'timestamp': _latest_frame_timestamp_label(created_at),
            'age_label': _latest_frame_age_label(created_at, self.clock),
            'image_available': True,
            'source_status': 'Metadata row available.',
            'frame_metadata': frame_metadata,
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
            frame_metadata=sanitized_metadata['frame_metadata'],
            note='Metadata accepted from injected repository. Preview remains disabled.',
            evidence='Bounded latest frame metadata accepted; no preview URL or source path is exposed.',
            is_placeholder=True,
        ).to_dict()


class StaticLatestCameraFramesRepository:
    """Fallback camera-frame source used when runtime image URLs are unavailable."""

    def get_latest_camera_frames(self):
        return []


class LatestCameraFramesProvider:
    """Build sanitized latest camera frame cards from an injected repository."""

    def __init__(self, repository=None):
        self.repository = repository or StaticLatestCameraFramesRepository()

    def build(self):
        try:
            frames = self.repository.get_latest_camera_frames()
        except Exception:
            frames = []

        items = []
        if isinstance(frames, list):
            for index, frame in enumerate(frames[:2]):
                if not isinstance(frame, dict):
                    continue
                items.append(_sanitize_latest_camera_frame_item(frame, index))

        while len(items) < 2:
            index = len(items)
            items.append(_build_latest_camera_frame_placeholder(index))

        image_count = len([item for item in items if item['image_available'] and item['safe_image_url']])
        status = 'Latest camera images available.' if image_count else 'Latest camera images unavailable.'
        note = (
            'Latest camera frames use existing safe image routes; no filesystem scan or RAW/FITS read is performed by Now.'
            if image_count
            else 'Latest camera frame URLs are not available from the bounded runtime source.'
        )

        return {
            'id': 'latest_camera_frames.summary',
            'label': 'Latest Camera Frames',
            'status': status,
            'data_status': NOW_DATA_STATUS_NOT_EVALUATED,
            'items': items,
            'note': note,
            'is_placeholder': image_count == 0,
        }


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


def build_now_view(
    latest_frame_provider=None,
    latest_camera_frames_provider=None,
    current_phase_night=None,
    latest_generated_output_repository=None,
    current_capture_repository=None,
    source_trust_repository=None,
):
    """Return the first backend-owned NowView contract.

    The payload is built from sanitized view-model inputs. Most sections remain
    fake-safe placeholders while bounded repositories can provide metadata-only
    facts.
    """
    current_phase_summary = build_current_phase_summary(current_phase_night)
    latest_frame_summary = _build_latest_frame_summary(latest_frame_provider=latest_frame_provider)
    latest_generated_output_summary = _build_latest_generated_output_summary(
        latest_generated_output_repository=latest_generated_output_repository,
    )
    current_capture_summary = _build_current_capture_summary(
        current_capture_repository=current_capture_repository,
        current_phase_summary=current_phase_summary,
        latest_frame_summary=latest_frame_summary,
    )
    latest_camera_frames = _build_latest_camera_frames(latest_camera_frames_provider=latest_camera_frames_provider)

    payload = {
        'id': 'now.placeholder',
        'label': 'Now',
        'status': 'Read-only product prototype',
        'briefing_title': 'Current / Morning Briefing',
        'current_verdict': _build_now_current_verdict(
            latest_frame_summary=latest_frame_summary,
            current_capture_summary=current_capture_summary,
            latest_generated_output_summary=latest_generated_output_summary,
        ),
        'data_status': NOW_DATA_STATUS_PLACEHOLDER,
        'generated_at': 'Not evaluated yet',
        'is_placeholder': True,
        'safe_actions_available': [],
        'current_sky': _build_current_sky(),
        'current_phase_summary': current_phase_summary,
        'current_capture_summary': current_capture_summary,
        'latest_frame_summary': latest_frame_summary,
        'latest_camera_frames': latest_camera_frames,
        'latest_generated_output_summary': latest_generated_output_summary,
        'source_confidence_summary': build_source_confidence_summary(
            source_trust_repository=source_trust_repository,
            latest_frame_summary=latest_frame_summary,
        ),
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


def build_sky_cycle_report_view(sky_cycle_repository=None, current_phase_night=None):
    """Return the first Sky Cycle Report product contract."""
    current_phase_summary = build_current_phase_summary(current_phase_night)
    cycle_summary = _build_sky_cycle_report_summary(
        sky_cycle_repository=sky_cycle_repository,
        current_phase_summary=current_phase_summary,
    )

    payload = {
        'id': 'sky_cycle_report.placeholder',
        'label': 'Sky Cycle Report',
        'status': 'Read-only product prototype',
        'data_status': NOW_DATA_STATUS_PLACEHOLDER,
        'generated_at': 'Not evaluated yet',
        'is_placeholder': cycle_summary.get('is_placeholder', True),
        'safe_actions_available': [],
        'cycle_summary': cycle_summary,
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


def build_highlights_view(highlights_repository=None):
    """Return the first Highlights product contract."""
    highlight_items = _build_highlight_items(highlights_repository=highlights_repository)

    payload = {
        'id': 'highlights.placeholder',
        'label': 'Highlights',
        'status': 'Read-only product prototype',
        'data_status': NOW_DATA_STATUS_PLACEHOLDER,
        'generated_at': 'Not evaluated yet',
        'is_placeholder': all(item.get('is_placeholder', True) for item in highlight_items),
        'safe_actions_available': [],
        'highlights_summary': _build_highlights_summary(highlight_items),
        'highlight_items': highlight_items,
        'source_trust_summary': _build_highlights_source_trust_summary(),
        'review_queue_summary': _build_highlights_review_queue_summary(),
        'selection_policy_summary': _build_highlights_selection_policy_summary(),
        'attention_items': _build_highlights_attention_items(),
        'metadata': _build_highlights_metadata(),
    }

    validate_highlights_payload(payload)
    return payload


def build_moment_detail_view():
    """Return the first fake-safe Moment Detail product contract."""
    payload = {
        'id': 'moment_detail.placeholder',
        'label': 'Moment Detail',
        'status': 'Read-only product prototype',
        'data_status': NOW_DATA_STATUS_PLACEHOLDER,
        'generated_at': 'Not evaluated yet',
        'is_placeholder': True,
        'safe_actions_available': [],
        'moment_summary': _build_moment_detail_summary(),
        'evidence_summary': _build_moment_detail_evidence_summary(),
        'source_trust_summary': _build_moment_detail_source_trust_summary(),
        'related_outputs': _build_moment_detail_related_outputs(),
        'sky_cycle_context': _build_moment_detail_sky_cycle_context(),
        'observatory_context': _build_moment_detail_observatory_context(),
        'metadata': _build_moment_detail_metadata(),
    }

    validate_moment_detail_payload(payload)
    return payload


def build_output_detail_view():
    """Return the first fake-safe Output Detail product contract."""
    payload = {
        'id': 'output_detail.placeholder',
        'label': 'Output Detail',
        'status': 'Read-only product prototype',
        'data_status': NOW_DATA_STATUS_PLACEHOLDER,
        'generated_at': 'Not evaluated yet',
        'is_placeholder': True,
        'safe_actions_available': [],
        'output_summary': _build_output_detail_summary(),
        'preview_summary': _build_output_detail_preview_summary(),
        'recipe_summary': _build_output_detail_recipe_summary(),
        'source_lineage_summary': _build_output_detail_source_lineage_summary(),
        'related_moments': _build_output_detail_related_moments(),
        'sky_cycle_context': _build_output_detail_sky_cycle_context(),
        'share_readiness_summary': _build_output_detail_share_readiness_summary(),
        'metadata': _build_output_detail_metadata(),
    }

    validate_output_detail_payload(payload)
    return payload


def build_library_view():
    """Return the first fake-safe Library product contract."""
    payload = {
        'id': 'library.placeholder',
        'label': 'Library',
        'status': 'Read-only product prototype',
        'data_status': NOW_DATA_STATUS_PLACEHOLDER,
        'generated_at': 'Not evaluated yet',
        'is_placeholder': True,
        'safe_actions_available': [],
        'library_summary': _build_library_summary(),
        'collection_summary': _build_library_collection_summary(),
        'search_summary': _build_library_search_summary(),
        'filter_summary': _build_library_filter_summary(),
        'recent_items': _build_library_recent_items(),
        'memory_model_summary': _build_library_memory_model_summary(),
        'metadata': _build_library_metadata(),
    }

    validate_library_payload(payload)
    return payload


def build_observatory_view():
    """Return the first fake-safe Observatory product contract."""
    payload = {
        'id': 'observatory.placeholder',
        'label': 'Observatory',
        'status': 'Read-only product prototype',
        'data_status': NOW_DATA_STATUS_PLACEHOLDER,
        'generated_at': 'Not evaluated yet',
        'is_placeholder': True,
        'safe_actions_available': [],
        'observatory_summary': _build_observatory_summary(),
        'camera_system_summary': _build_observatory_camera_system_summary(),
        'capture_pipeline_summary': _build_observatory_capture_pipeline_summary(),
        'source_preservation_summary': _build_observatory_source_preservation_summary(),
        'storage_summary': _build_observatory_storage_summary(),
        'generation_summary': _build_observatory_generation_summary(),
        'integration_summary': _build_observatory_integration_summary(),
        'attention_items': _build_observatory_attention_items(),
        'metadata': _build_observatory_metadata(),
    }

    validate_observatory_payload(payload)
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
    _validate_current_capture_summary(payload.get('current_capture_summary'))
    _validate_latest_frame_summary(payload.get('latest_frame_summary'))
    _validate_latest_camera_frames(payload.get('latest_camera_frames'))
    _validate_latest_generated_output_summary(payload.get('latest_generated_output_summary'))
    _validate_source_confidence_summary(payload.get('source_confidence_summary'))
    _validate_data_statuses(payload)
    _validate_no_callables(payload)
    _validate_no_sensitive_keys(payload)
    _validate_no_absolute_paths(payload)
    _validate_safe_actions(payload)
    _validate_json_safe(payload)

    return True


def validate_highlights_payload(payload):
    """Validate a Highlights payload before template rendering."""
    if not isinstance(payload, dict):
        raise ValueError('Highlights payload must be a dict')

    missing_keys = sorted(HIGHLIGHTS_REQUIRED_KEYS.difference(payload.keys()))
    if missing_keys:
        raise ValueError('Highlights payload missing required keys: {0:s}'.format(', '.join(missing_keys)))

    for section_key in HIGHLIGHTS_REQUIRED_SECTIONS:
        _validate_required_section(payload, section_key)

    _validate_highlights_summary(payload.get('highlights_summary'))
    _validate_highlight_items(payload.get('highlight_items'))
    _validate_highlights_source_trust_summary(payload.get('source_trust_summary'))
    _validate_highlights_review_queue_summary(payload.get('review_queue_summary'))
    _validate_highlights_selection_policy_summary(payload.get('selection_policy_summary'))
    _validate_data_statuses(payload)
    _validate_no_callables(payload)
    _validate_no_sensitive_keys(payload)
    _validate_no_absolute_paths(payload)
    _validate_safe_actions(payload)
    _validate_json_safe(payload)

    return True


def validate_moment_detail_payload(payload):
    """Validate a Moment Detail payload before template rendering."""
    if not isinstance(payload, dict):
        raise ValueError('MomentDetail payload must be a dict')

    missing_keys = sorted(MOMENT_DETAIL_REQUIRED_KEYS.difference(payload.keys()))
    if missing_keys:
        raise ValueError('MomentDetail payload missing required keys: {0:s}'.format(', '.join(missing_keys)))

    for section_key in MOMENT_DETAIL_REQUIRED_SECTIONS:
        _validate_required_section(payload, section_key)

    _validate_moment_detail_summary(payload.get('moment_summary'))
    _validate_moment_detail_evidence_summary(payload.get('evidence_summary'))
    _validate_moment_detail_source_trust_summary(payload.get('source_trust_summary'))
    _validate_moment_detail_related_outputs(payload.get('related_outputs'))
    _validate_moment_detail_sky_cycle_context(payload.get('sky_cycle_context'))
    _validate_moment_detail_observatory_context(payload.get('observatory_context'))
    _validate_data_statuses(payload)
    _validate_no_callables(payload)
    _validate_no_sensitive_keys(payload)
    _validate_no_absolute_paths(payload)
    _validate_safe_actions(payload)
    _validate_json_safe(payload)

    return True


def validate_output_detail_payload(payload):
    """Validate an Output Detail payload before template rendering."""
    if not isinstance(payload, dict):
        raise ValueError('OutputDetail payload must be a dict')

    missing_keys = sorted(OUTPUT_DETAIL_REQUIRED_KEYS.difference(payload.keys()))
    if missing_keys:
        raise ValueError('OutputDetail payload missing required keys: {0:s}'.format(', '.join(missing_keys)))

    for section_key in OUTPUT_DETAIL_REQUIRED_SECTIONS:
        _validate_required_section(payload, section_key)

    _validate_output_detail_summary(payload.get('output_summary'))
    _validate_output_detail_preview_summary(payload.get('preview_summary'))
    _validate_output_detail_recipe_summary(payload.get('recipe_summary'))
    _validate_output_detail_source_lineage_summary(payload.get('source_lineage_summary'))
    _validate_output_detail_related_moments(payload.get('related_moments'))
    _validate_output_detail_sky_cycle_context(payload.get('sky_cycle_context'))
    _validate_output_detail_share_readiness_summary(payload.get('share_readiness_summary'))
    _validate_data_statuses(payload)
    _validate_no_callables(payload)
    _validate_no_sensitive_keys(payload)
    _validate_no_absolute_paths(payload)
    _validate_safe_actions(payload)
    _validate_json_safe(payload)

    return True


def validate_library_payload(payload):
    """Validate a Library payload before template rendering."""
    if not isinstance(payload, dict):
        raise ValueError('Library payload must be a dict')

    missing_keys = sorted(LIBRARY_REQUIRED_KEYS.difference(payload.keys()))
    if missing_keys:
        raise ValueError('Library payload missing required keys: {0:s}'.format(', '.join(missing_keys)))

    for section_key in LIBRARY_REQUIRED_SECTIONS:
        _validate_required_section(payload, section_key)

    _validate_library_summary(payload.get('library_summary'))
    _validate_library_collection_summary(payload.get('collection_summary'))
    _validate_library_search_summary(payload.get('search_summary'))
    _validate_library_filter_summary(payload.get('filter_summary'))
    _validate_library_recent_items(payload.get('recent_items'))
    _validate_library_memory_model_summary(payload.get('memory_model_summary'))
    _validate_data_statuses(payload)
    _validate_no_callables(payload)
    _validate_no_sensitive_keys(payload)
    _validate_no_absolute_paths(payload)
    _validate_safe_actions(payload)
    _validate_json_safe(payload)

    return True


def validate_observatory_payload(payload):
    """Validate an Observatory payload before template rendering."""
    if not isinstance(payload, dict):
        raise ValueError('Observatory payload must be a dict')

    missing_keys = sorted(OBSERVATORY_REQUIRED_KEYS.difference(payload.keys()))
    if missing_keys:
        raise ValueError('Observatory payload missing required keys: {0:s}'.format(', '.join(missing_keys)))

    for section_key in OBSERVATORY_REQUIRED_SECTIONS:
        _validate_required_section(payload, section_key)

    _validate_observatory_summary(payload.get('observatory_summary'))
    _validate_observatory_camera_system_summary(payload.get('camera_system_summary'))
    _validate_observatory_capture_pipeline_summary(payload.get('capture_pipeline_summary'))
    _validate_observatory_source_preservation_summary(payload.get('source_preservation_summary'))
    _validate_observatory_storage_summary(payload.get('storage_summary'))
    _validate_observatory_generation_summary(payload.get('generation_summary'))
    _validate_observatory_integration_summary(payload.get('integration_summary'))
    _validate_observatory_attention_items(payload.get('attention_items'))
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
    _validate_sky_cycle_moments_summary(payload.get('moments_summary'))
    _validate_sky_cycle_outputs_summary(payload.get('outputs_summary'))
    _validate_source_confidence_summary(payload.get('source_confidence_summary'))
    _validate_sky_cycle_observatory_health_summary(payload.get('observatory_health_summary'))
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
        capture_status='Capture status summarized by the bounded Current Capture contract.',
        source_recording='Source recording status pending backend contract',
        summary='Current phase, latest frame, and current capture status use bounded metadata where available; source recording remains pending.',
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


def _build_latest_camera_frames(latest_camera_frames_provider=None):
    provider = latest_camera_frames_provider or LatestCameraFramesProvider()
    return provider.build()


def _build_now_current_verdict(latest_frame_summary=None, current_capture_summary=None, latest_generated_output_summary=None):
    latest_frame_available = isinstance(latest_frame_summary, dict) and latest_frame_summary.get('image_available')
    capture_state = (
        current_capture_summary.get('capture_state')
        if isinstance(current_capture_summary, dict)
        else None
    )
    latest_output_type = (
        latest_generated_output_summary.get('output_type')
        if isinstance(latest_generated_output_summary, dict)
        else None
    )

    if latest_frame_available and capture_state in ('running', 'idle', 'paused', 'error'):
        return 'Latest frame metadata available; capture state is {0:s}.'.format(capture_state)

    if latest_frame_available:
        return 'Latest frame metadata available.'

    if latest_output_type and latest_output_type not in ('unknown', 'not evaluated'):
        return 'Latest generated output metadata available.'

    return 'Observation data not evaluated yet'


def _build_latest_camera_frame_placeholder(index):
    return {
        'camera_id': None,
        'camera_label': 'Camera {0:d}'.format(index + 1),
        'timestamp': 'No latest frame available',
        'age_label': 'Not evaluated yet',
        'image_available': False,
        'safe_image_url': None,
        'source_status': 'No safe image URL available.',
        'note': 'Camera frame fallback; no image route is connected for this slot.',
    }


def _sanitize_latest_camera_frame_item(frame, index):
    safe_image_url = frame.get('safe_image_url')
    if not _safe_product_image_url(safe_image_url):
        safe_image_url = None

    image_available = bool(frame.get('image_available')) and bool(safe_image_url)

    return {
        'camera_id': _latest_frame_json_value(frame.get('camera_id')),
        'camera_label': _latest_frame_text(frame.get('camera_label'), 'Camera {0:d}'.format(index + 1)),
        'timestamp': _latest_frame_text(frame.get('timestamp'), 'No latest frame available'),
        'age_label': _latest_frame_text(frame.get('age_label'), 'Not evaluated yet'),
        'image_available': image_available,
        'safe_image_url': safe_image_url,
        'source_status': _latest_frame_text(frame.get('source_status'), 'Source status not evaluated yet.'),
        'note': _latest_frame_text(frame.get('note'), 'Latest frame route status not evaluated.'),
    }


def _safe_product_image_url(value):
    if value in (None, ''):
        return False

    if not isinstance(value, str):
        return False

    value = value.strip()
    if not value.startswith('/'):
        return False

    if '/images/' not in value:
        return False

    value_lower = value.lower()
    if any(token in value_lower for token in ('..', '\\', '://', 'file:', '\x00')):
        return False

    return True


def _build_current_capture_summary(current_capture_repository=None, current_phase_summary=None, latest_frame_summary=None):
    empty_metadata = {
        'capture_state': NOW_CAPTURE_STATE_UNKNOWN,
        'is_acquiring': False,
        'camera_label': 'Camera not evaluated yet',
        'policy_label': 'Capture policy not evaluated yet.',
        'source_status': 'Current capture status repository not connected.',
        'watchdog_age_seconds': None,
    }

    if current_capture_repository is None:
        return _current_capture_summary_from_metadata(
            status='Current capture status not connected yet.',
            metadata=empty_metadata,
            current_phase_summary=current_phase_summary,
            latest_frame_summary=latest_frame_summary,
            note='No current capture repository is connected to Now.',
        )

    try:
        metadata = current_capture_repository.get_current_capture_metadata()
    except Exception:
        return _current_capture_summary_from_metadata(
            status='Current capture status unavailable.',
            metadata=empty_metadata,
            current_phase_summary=current_phase_summary,
            latest_frame_summary=latest_frame_summary,
            note='Current capture repository failed; error details are not exposed.',
        )

    if not isinstance(metadata, dict):
        return _current_capture_summary_from_metadata(
            status='Current capture status unavailable.',
            metadata=empty_metadata,
            current_phase_summary=current_phase_summary,
            latest_frame_summary=latest_frame_summary,
            note='Current capture repository returned unsupported metadata.',
        )

    sanitized_metadata = {
        'capture_state': _current_capture_state(metadata.get('capture_state')),
        'is_acquiring': bool(metadata.get('is_acquiring', False)),
        'camera_label': _latest_frame_text(metadata.get('camera_label'), 'Camera not evaluated yet'),
        'policy_label': _latest_frame_text(metadata.get('policy_label'), 'Capture policy not evaluated yet.'),
        'source_status': _latest_frame_text(metadata.get('source_status'), 'Current capture source status not evaluated.'),
        'watchdog_age_seconds': _latest_frame_json_value(metadata.get('watchdog_age_seconds')),
    }

    return _current_capture_summary_from_metadata(
        status='Current capture status available.',
        metadata=sanitized_metadata,
        current_phase_summary=current_phase_summary,
        latest_frame_summary=latest_frame_summary,
        note='Capture status is derived from bounded persisted metadata and camera policy flags.',
    )


def _current_capture_summary_from_metadata(status, metadata, current_phase_summary=None, latest_frame_summary=None, note=''):
    phase = NOW_PHASE_UNKNOWN
    if isinstance(current_phase_summary, dict):
        phase = current_phase_summary.get('phase', NOW_PHASE_UNKNOWN)

    last_frame_status = _current_capture_last_frame_status(latest_frame_summary)
    coherence_label = _current_capture_coherence_label(metadata['capture_state'], latest_frame_summary, phase)

    return {
        'id': 'current_capture.summary',
        'label': 'Current Capture Status',
        'status': status,
        'data_status': NOW_DATA_STATUS_NOT_EVALUATED,
        'capture_state': metadata['capture_state'],
        'is_acquiring': bool(metadata['is_acquiring']),
        'camera_label': metadata['camera_label'],
        'phase': phase,
        'policy_label': metadata['policy_label'],
        'last_frame_status': last_frame_status,
        'coherence_label': coherence_label,
        'source_status': metadata['source_status'],
        'note': _latest_frame_text(note, 'Current capture status not evaluated.'),
        'evidence': _current_capture_evidence(metadata),
        'is_placeholder': metadata['capture_state'] == NOW_CAPTURE_STATE_UNKNOWN,
    }


def _current_capture_state(value):
    if value in NOW_ALLOWED_CAPTURE_STATES:
        return value

    return NOW_CAPTURE_STATE_UNKNOWN


def _current_capture_last_frame_status(latest_frame_summary):
    if not isinstance(latest_frame_summary, dict):
        return 'Latest frame metadata not evaluated.'

    if latest_frame_summary.get('image_available'):
        timestamp = _latest_frame_text(latest_frame_summary.get('timestamp'), 'timestamp unavailable')
        return 'Latest frame metadata available: {0:s}.'.format(timestamp)

    return 'Latest frame metadata not available.'


def _current_capture_coherence_label(capture_state, latest_frame_summary, phase):
    if capture_state == NOW_CAPTURE_STATE_RUNNING and isinstance(latest_frame_summary, dict):
        if latest_frame_summary.get('image_available'):
            return 'Capture state and latest frame metadata are consistent enough for this bounded summary.'

        return 'Capture reports running, but latest frame metadata is not available.'

    if capture_state == NOW_CAPTURE_STATE_PAUSED:
        return 'Capture is paused; a recent frame is not expected from the active capture loop.'

    if capture_state == NOW_CAPTURE_STATE_IDLE:
        return 'Capture is idle; latest frame recency should be interpreted with phase and policy context.'

    if capture_state == NOW_CAPTURE_STATE_ERROR:
        return 'Capture status indicates an error; latest frame metadata may be stale.'

    if phase == NOW_PHASE_DAY:
        return 'Capture state is unknown; daytime policy may explain missing frames.'

    return 'Capture coherence not evaluated yet.'


def _current_capture_evidence(metadata):
    evidence = [
        'Persisted capture status metadata.',
        'Camera capture policy flags.',
    ]

    watchdog_age = metadata.get('watchdog_age_seconds')
    if isinstance(watchdog_age, (int, float)):
        evidence.append('Watchdog age: {0:g} seconds.'.format(watchdog_age))

    return ' '.join(evidence)


def _build_latest_generated_output_summary(latest_generated_output_repository=None):
    empty_output = {
        'output_type': 'not evaluated',
        'timestamp': 'Not evaluated yet',
        'day_date': 'Not evaluated yet',
        'generation_status': 'Generated output metadata not evaluated yet.',
        'uploaded': None,
        'success': None,
        'frames': None,
        'framerate': None,
        'file_size': None,
        'width': None,
        'height': None,
        'source_table_label': 'Generated output source not evaluated yet',
    }

    if latest_generated_output_repository is None:
        return _latest_generated_output_summary_from_metadata(
            status='Generated output metadata not connected yet.',
            output_metadata=empty_output,
            note='No generated-output repository is connected to Now.',
        )

    try:
        repository_metadata = latest_generated_output_repository.get_latest_generated_output_metadata()
    except Exception:
        return _latest_generated_output_summary_from_metadata(
            status='Generated output metadata unavailable.',
            output_metadata=empty_output,
            note='Generated-output repository failed; error details are not exposed.',
        )

    if not isinstance(repository_metadata, dict):
        return _latest_generated_output_summary_from_metadata(
            status='Generated output metadata unavailable.',
            output_metadata=empty_output,
            note='Generated-output repository returned unsupported metadata.',
        )

    output_metadata = repository_metadata.get('output') or {}
    if not output_metadata:
        return _latest_generated_output_summary_from_metadata(
            status='No generated output metadata available.',
            output_metadata=empty_output,
            note=_latest_frame_text(repository_metadata.get('note'), 'No generated output metadata row is available.'),
        )

    generation_status = _latest_frame_text(
        output_metadata.get('status_label'),
        'Generated output metadata available.',
    )

    return _latest_generated_output_summary_from_metadata(
        status='Latest generated output metadata available.',
        output_metadata={
            'output_type': _latest_frame_text(output_metadata.get('output_type'), 'unknown'),
            'timestamp': _latest_frame_text(output_metadata.get('timestamp'), 'Not evaluated yet'),
            'day_date': _latest_frame_text(output_metadata.get('day_date'), 'Not evaluated yet'),
            'generation_status': generation_status,
            'uploaded': output_metadata.get('uploaded'),
            'success': output_metadata.get('success'),
            'frames': output_metadata.get('frames'),
            'framerate': output_metadata.get('framerate'),
            'file_size': output_metadata.get('file_size'),
            'width': output_metadata.get('width'),
            'height': output_metadata.get('height'),
            'source_table_label': _latest_frame_text(output_metadata.get('source_table_label'), 'Generated output source'),
        },
        note='Metadata selected from bounded generated-output descriptors. Preview and file access remain disabled.',
    )


def _latest_generated_output_summary_from_metadata(status, output_metadata, note):
    return {
        'id': 'latest_generated_output.summary',
        'label': 'Latest Generated Output',
        'status': status,
        'data_status': NOW_DATA_STATUS_NOT_EVALUATED,
        'output_type': output_metadata['output_type'],
        'timestamp': output_metadata['timestamp'],
        'day_date': output_metadata['day_date'],
        'generation_status': output_metadata['generation_status'],
        'uploaded': _latest_generated_output_summary_value(output_metadata.get('uploaded')),
        'success': _latest_generated_output_summary_value(output_metadata.get('success')),
        'frames': _latest_generated_output_summary_value(output_metadata.get('frames')),
        'framerate': _latest_generated_output_summary_value(output_metadata.get('framerate')),
        'file_size': _latest_generated_output_summary_value(output_metadata.get('file_size')),
        'width': _latest_generated_output_summary_value(output_metadata.get('width')),
        'height': _latest_generated_output_summary_value(output_metadata.get('height')),
        'source_table_label': output_metadata['source_table_label'],
        'note': note,
        'is_placeholder': True,
    }


def _latest_generated_output_summary_value(value):
    if not _latest_frame_metadata_value_is_json_safe(value):
        return None

    if _latest_frame_value_is_unsafe(value):
        return None

    return value


def build_source_confidence_summary(source_trust_repository=None, latest_frame_summary=None):
    if source_trust_repository is not None:
        try:
            metadata = source_trust_repository.get_source_trust_metadata()
        except Exception:
            metadata = _build_source_trust_unavailable('Source trust repository failed; error details are not exposed.')

        if isinstance(metadata, dict):
            return _build_source_confidence_summary_from_metadata(metadata, latest_frame_summary=latest_frame_summary)

    return SourceConfidenceSummary(
        id='source_confidence.placeholder',
        label='Source Confidence',
        status='Source coverage pending bounded backend contract.',
        data_status=NOW_DATA_STATUS_NOT_EVALUATED,
        confidence_label='Pending source coverage contract',
        coverage_label='Not evaluated yet',
        source_types=[
            'image metadata',
            'source files',
        ],
        preservation_status='RAW/FITS/source preservation not evaluated in this prototype.',
        retention_status='Source retention policy not evaluated yet.',
        lineage_status='Lineage between outputs and source frames is not connected yet.',
        gap_status='Source gaps not evaluated yet.',
        risk_level=NOW_RISK_LEVEL_UNKNOWN,
        note='Source coverage pending bounded backend contract.',
        evidence=[
            'No RAW/FITS/source coverage calculation is connected yet.',
            'Lineage between outputs and source frames is not connected yet.',
        ],
        next_backend_contract='bounded source coverage summary',
        is_placeholder=True,
    ).to_dict()


def _build_source_confidence_summary_from_metadata(metadata, latest_frame_summary=None):
    sources = metadata.get('sources')
    if not isinstance(sources, list):
        sources = []

    sanitized_sources = [
        source for source in (_sanitize_source_trust_source(item) for item in sources)
        if source is not None
    ]
    source_types = sorted(set(source['source_label'] for source in sanitized_sources))
    has_latest_frame = isinstance(latest_frame_summary, dict) and bool(latest_frame_summary.get('frame_metadata'))
    partial_failures = _latest_frame_json_value(metadata.get('partial_failures')) or 0

    if sanitized_sources:
        confidence_label = 'Source metadata available'
        coverage_label = '{0:d} bounded source metadata row(s) found'.format(len(sanitized_sources))
        preservation_status = 'RAW/FITS/source metadata found; file presence was not verified.'
        risk_level = NOW_RISK_LEVEL_LOW if has_latest_frame and partial_failures == 0 else NOW_RISK_LEVEL_MEDIUM
        status = 'Source preservation partially verified by metadata.'
        gap_status = 'Filesystem coverage and per-output lineage are not verified.'
        evidence = [
            'Bounded RAW/FITS metadata rows found for current camera.',
            'No filesystem verification was performed.',
        ]
        is_placeholder = False
    else:
        confidence_label = 'Source metadata not found'
        coverage_label = 'No bounded RAW/FITS source metadata row found'
        preservation_status = 'Source preservation cannot be confirmed from metadata.'
        risk_level = NOW_RISK_LEVEL_MEDIUM if has_latest_frame else NOW_RISK_LEVEL_UNKNOWN
        status = 'Source preservation not verified.'
        gap_status = 'RAW/FITS/source metadata gap or source contract unavailable.'
        evidence = [
            'Latest frame metadata may exist without matching RAW/FITS metadata.',
            'No filesystem verification was performed.',
        ]
        is_placeholder = True

    if partial_failures:
        risk_level = NOW_RISK_LEVEL_MEDIUM
        evidence.append('One or more source metadata descriptors failed safely.')

    if has_latest_frame:
        evidence.append('Latest frame metadata is available as capture evidence.')

    return SourceConfidenceSummary(
        id='source_confidence.metadata',
        label='Source Confidence',
        status=status,
        data_status=NOW_DATA_STATUS_NOT_EVALUATED,
        confidence_label=confidence_label,
        coverage_label=coverage_label,
        source_types=source_types or ['source metadata not found'],
        preservation_status=preservation_status,
        retention_status='Source retention policy is not evaluated by this summary.',
        lineage_status='Generated output lineage is not connected yet.',
        gap_status=gap_status,
        risk_level=risk_level,
        note='Source trust is based on metadata only; no filesystem verification was performed.',
        evidence=evidence,
        next_backend_contract='bounded source lineage summary',
        is_placeholder=is_placeholder,
    ).to_dict()


def _build_sky_cycle_report_summary(sky_cycle_repository=None, current_phase_summary=None):
    if sky_cycle_repository is not None:
        try:
            metadata = sky_cycle_repository.get_sky_cycle_metadata()
        except Exception:
            metadata = _build_sky_cycle_metadata_unavailable('Sky Cycle repository failed safely.')

        if isinstance(metadata, dict):
            summary = _sky_cycle_report_summary_from_metadata(metadata, current_phase_summary=current_phase_summary)
            if summary is not None:
                return summary

    return SkyCycleSummary(
        id='sky_cycle.summary.placeholder',
        label='Cycle Summary',
        title='Sky Cycle Report',
        cycle_label='Current or latest cycle not evaluated yet',
        data_status=NOW_DATA_STATUS_NOT_EVALUATED,
        current_phase='Not evaluated yet',
        cycle_status=SKY_CYCLE_STATUS_UNKNOWN,
        cycle_verdict='Sky cycle data pending backend contract.',
        cycle_started_label='Cycle start not evaluated yet',
        latest_frame_label='Latest frame not evaluated yet',
        time_range_label='Time range not evaluated yet',
        coverage_label='Data coverage not evaluated yet',
        confidence_label='Confidence not evaluated yet',
        evidence=[
            'No Sky Cycle metadata repository is connected.',
        ],
        note='This report is a read-only product prototype. It does not evaluate real cycle boundaries, source coverage, moments, outputs, or health.',
        is_placeholder=True,
    ).to_dict()


def _sky_cycle_report_summary_from_metadata(metadata, current_phase_summary=None):
    latest_frame = metadata.get('latest_frame') if isinstance(metadata, dict) else None
    if not isinstance(latest_frame, dict) or not latest_frame:
        return None

    cycle_start = metadata.get('cycle_start') if isinstance(metadata.get('cycle_start'), dict) else {}
    day_date = _latest_frame_text(latest_frame.get('day_date'), 'Unknown sky day')
    latest_timestamp = _latest_frame_text(latest_frame.get('timestamp'), 'Latest frame time not evaluated')
    start_timestamp = _latest_frame_text(cycle_start.get('timestamp'), 'Cycle start not evaluated yet')
    phase = NOW_PHASE_UNKNOWN
    if isinstance(current_phase_summary, dict):
        phase = current_phase_summary.get('phase', NOW_PHASE_UNKNOWN)

    current_date = _latest_frame_text(metadata.get('current_date'), 'Not evaluated yet')
    cycle_status = _sky_cycle_status(day_date, current_date, bool(cycle_start))
    cycle_verdict = _sky_cycle_verdict(cycle_status, phase)
    time_range_label = 'From {0:s} to {1:s}'.format(start_timestamp, latest_timestamp)
    confidence_label = 'Medium confidence from image metadata' if cycle_start else 'Low confidence; cycle start unavailable'

    evidence = [
        'latest_frame={0:s}'.format(latest_timestamp),
        'sky_day={0:s}'.format(day_date),
        'current_phase={0:s}'.format(phase),
    ]
    if cycle_start:
        evidence.append('cycle_start={0:s}'.format(start_timestamp))
    else:
        evidence.append('cycle_start=not_available')

    return SkyCycleSummary(
        id='sky_cycle.summary.metadata',
        label='Cycle Summary',
        title='Sky Cycle Report',
        cycle_label='Sky Cycle {0:s}'.format(day_date),
        data_status=NOW_DATA_STATUS_NOT_EVALUATED,
        current_phase=phase,
        cycle_status=cycle_status,
        cycle_verdict=cycle_verdict,
        cycle_started_label=start_timestamp,
        latest_frame_label=latest_timestamp,
        time_range_label=time_range_label,
        coverage_label='Latest and start metadata available' if cycle_start else 'Latest metadata available; start metadata unavailable',
        confidence_label=confidence_label,
        evidence=evidence,
        note='Summary is based on bounded image metadata only. Twilight, full coverage, moments, outputs, and source lineage are not evaluated here.',
        is_placeholder=False,
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
            observation_value='Daytime sky monitoring placeholder.',
            source_expectation='Image metadata may define future daytime source coverage.',
            output_expectation='Daytime outputs are not evaluated yet.',
            science_note='Daytime cloud, Sun, weather, and anomaly summaries require future backend evidence.',
            astrophoto_note='Daytime frames may support context and transition media, but no rendering contract is connected.',
            supported=True,
            unsupported_reason='',
            note='Day phase placeholder pending a bounded Sky Cycle backend contract.',
            is_placeholder=True,
        ),
        SkyCyclePhase(
            id='sky_cycle.phase.sunset_twilight',
            label='Sunset / Twilight',
            phase='sunset_twilight',
            status='not_evaluated',
            data_status=NOW_DATA_STATUS_FUTURE_CONTRACT,
            time_range_label='Twilight range not evaluated yet',
            observation_value='Twilight classification pending phase engine.',
            source_expectation='Transition source coverage requires a future phase boundary contract.',
            output_expectation='Sunset/twilight output readiness is not evaluated yet.',
            science_note='No astronomical boundary calculation connected yet.',
            astrophoto_note='Twilight may become useful for transition highlights after source lineage exists.',
            supported=False,
            unsupported_reason='No phase engine or astronomical boundary contract is connected.',
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
            observation_value='Night source/output evaluation pending backend contract.',
            source_expectation='Night source coverage should eventually summarize preserved frames and gaps.',
            output_expectation='Best image, timelapse, keogram, and startrail readiness are not evaluated yet.',
            science_note='Night quality, meteor, aurora, cloud, and sky brightness evidence are not connected.',
            astrophoto_note='Night outputs will eventually reference Looks and source lineage.',
            supported=True,
            unsupported_reason='',
            note='Night phase placeholder pending a bounded Sky Cycle backend contract.',
            is_placeholder=True,
        ),
        SkyCyclePhase(
            id='sky_cycle.phase.sunrise_twilight',
            label='Sunrise / Twilight',
            phase='sunrise_twilight',
            status='not_evaluated',
            data_status=NOW_DATA_STATUS_FUTURE_CONTRACT,
            time_range_label='Twilight range not evaluated yet',
            observation_value='Twilight classification pending phase engine.',
            source_expectation='Transition source coverage requires a future phase boundary contract.',
            output_expectation='Sunrise/twilight output readiness is not evaluated yet.',
            science_note='No astronomical boundary calculation connected yet.',
            astrophoto_note='Sunrise transition highlights require source lineage and output recipes.',
            supported=False,
            unsupported_reason='No phase engine or astronomical boundary contract is connected.',
            note='Sunrise twilight classification is not evaluated in this prototype.',
            is_placeholder=True,
        ),
    )

    return [phase.to_dict() for phase in phases]


def _build_sky_cycle_moments_summary():
    return {
        'id': 'sky_cycle.moments.placeholder',
        'label': 'Notable Moments',
        'status': 'Moment detection not connected yet.',
        'data_status': NOW_DATA_STATUS_FUTURE_CONTRACT,
        'count_label': 'No moments evaluated yet',
        'primary_moment': 'No primary moment selected',
        'moment_categories': [
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
        ],
        'review_queue_status': 'Review queue not evaluated yet.',
        'detection_status': 'Detector evidence pending backend contract.',
        'note': 'Moment detection not connected yet.',
        'items': [
            {
                'id': 'sky_cycle.moment.clear_window.placeholder',
                'type': 'clear_window',
                'label': 'Clear window candidate',
                'phase': 'night',
                'data_status': NOW_DATA_STATUS_FUTURE_CONTRACT,
                'time_label': 'Time not evaluated yet',
                'confidence_label': 'Confidence not evaluated yet',
                'evidence': [
                    'Clear-window evidence pending backend contract.',
                ],
                'source_lineage_status': 'Source lineage pending source contract.',
                'related_outputs_status': 'Related outputs pending rendering contract.',
                'science_note': 'Sky quality and cloud evidence are not connected yet.',
                'astrophoto_note': 'Review value for generated media is not evaluated yet.',
                'review_status': 'Review queue not evaluated yet.',
                'is_placeholder': True,
            },
            {
                'id': 'sky_cycle.moment.meteor.placeholder',
                'type': 'meteor',
                'label': 'Meteor candidate',
                'phase': 'night',
                'data_status': NOW_DATA_STATUS_FUTURE_CONTRACT,
                'time_label': 'Time not evaluated yet',
                'confidence_label': 'Detector confidence not connected',
                'evidence': [
                    'Detector evidence pending backend contract.',
                ],
                'source_lineage_status': 'Source lineage pending source contract.',
                'related_outputs_status': 'Related outputs pending rendering contract.',
                'science_note': 'Meteor classification requires detector evidence and source frames.',
                'astrophoto_note': 'Highlight output status is not evaluated yet.',
                'review_status': 'Review queue not evaluated yet.',
                'is_placeholder': True,
            },
            {
                'id': 'sky_cycle.moment.camera_anomaly.placeholder',
                'type': 'camera_anomaly',
                'label': 'Camera anomaly placeholder',
                'phase': 'unknown',
                'data_status': NOW_DATA_STATUS_FUTURE_CONTRACT,
                'time_label': 'Time not evaluated yet',
                'confidence_label': 'Operational confidence not evaluated yet',
                'evidence': [
                    'Camera anomaly evidence pending observatory health contract.',
                ],
                'source_lineage_status': 'Source lineage pending source contract.',
                'related_outputs_status': 'Related outputs not evaluated yet.',
                'science_note': 'Anomaly context requires bounded camera and source summaries.',
                'astrophoto_note': 'Image-quality impact is not evaluated yet.',
                'review_status': 'Review queue not evaluated yet.',
                'is_placeholder': True,
            },
        ],
        'is_placeholder': True,
    }


def _build_sky_cycle_outputs_summary():
    return {
        'id': 'sky_cycle.outputs.placeholder',
        'label': 'Generated Outputs',
        'status': 'Generated output status pending rendering contract.',
        'data_status': NOW_DATA_STATUS_FUTURE_CONTRACT,
        'count_label': 'No generated outputs evaluated yet',
        'generation_status': 'Rendering/generation status not connected yet.',
        'look_policy_status': 'Look policy not connected yet.',
        'share_readiness_status': 'Share readiness not evaluated yet.',
        'note': 'No media generation, conversion, preview lookup, download, or filesystem read is performed.',
        'items': [
            {
                'id': 'sky_cycle.output.best_image.placeholder',
                'type': 'best_image',
                'label': 'Best image',
                'phase': 'unknown',
                'data_status': NOW_DATA_STATUS_FUTURE_CONTRACT,
                'generation_status': 'Generated output status pending rendering contract.',
                'look_applied': 'Look policy not connected yet.',
                'source_lineage_status': 'Source lineage pending source contract.',
                'related_moments_status': 'Related moments not evaluated yet.',
                'share_status': 'Share readiness not evaluated yet.',
                'quality_note': 'Image quality scoring is not connected yet.',
                'astrophoto_note': 'Astrophoto review value is not evaluated yet.',
                'science_note': 'Scientific source relationship is not evaluated yet.',
                'safe_actions_available': [],
                'is_placeholder': True,
            },
            {
                'id': 'sky_cycle.output.timelapse.placeholder',
                'type': 'timelapse',
                'label': 'Timelapse',
                'phase': 'unknown',
                'data_status': NOW_DATA_STATUS_FUTURE_CONTRACT,
                'generation_status': 'Generated output status pending rendering contract.',
                'look_applied': 'Look policy not connected yet.',
                'source_lineage_status': 'Source lineage pending source contract.',
                'related_moments_status': 'Related moments not evaluated yet.',
                'share_status': 'Share readiness not evaluated yet.',
                'quality_note': 'Frame continuity and output quality are not evaluated yet.',
                'astrophoto_note': 'Timelapse look and cadence are not evaluated yet.',
                'science_note': 'Cycle coverage evidence is not connected yet.',
                'safe_actions_available': [],
                'is_placeholder': True,
            },
            {
                'id': 'sky_cycle.output.keogram.placeholder',
                'type': 'keogram',
                'label': 'Keogram',
                'phase': 'night',
                'data_status': NOW_DATA_STATUS_FUTURE_CONTRACT,
                'generation_status': 'Generated output status pending rendering contract.',
                'look_applied': 'Look policy not connected yet.',
                'source_lineage_status': 'Source lineage pending source contract.',
                'related_moments_status': 'Related moments not evaluated yet.',
                'share_status': 'Share readiness not evaluated yet.',
                'quality_note': 'Keogram quality is not evaluated yet.',
                'astrophoto_note': 'Night transition and sky-pattern value are not evaluated yet.',
                'science_note': 'Sky brightness and cloud continuity evidence are not connected yet.',
                'safe_actions_available': [],
                'is_placeholder': True,
            },
            {
                'id': 'sky_cycle.output.startrail.placeholder',
                'type': 'startrail',
                'label': 'Startrail',
                'phase': 'night',
                'data_status': NOW_DATA_STATUS_FUTURE_CONTRACT,
                'generation_status': 'Generated output status pending rendering contract.',
                'look_applied': 'Look policy not connected yet.',
                'source_lineage_status': 'Source lineage pending source contract.',
                'related_moments_status': 'Related moments not evaluated yet.',
                'share_status': 'Share readiness not evaluated yet.',
                'quality_note': 'Startrail continuity and artifact checks are not evaluated yet.',
                'astrophoto_note': 'Startrail look and composition are not evaluated yet.',
                'science_note': 'Source-frame continuity is not connected yet.',
                'safe_actions_available': [],
                'is_placeholder': True,
            },
            {
                'id': 'sky_cycle.output.meteor_highlight.placeholder',
                'type': 'meteor_highlight',
                'label': 'Meteor highlight',
                'phase': 'night',
                'data_status': NOW_DATA_STATUS_FUTURE_CONTRACT,
                'generation_status': 'Generated output status pending rendering contract.',
                'look_applied': 'Look policy not connected yet.',
                'source_lineage_status': 'Source lineage pending source contract.',
                'related_moments_status': 'Moment relation pending MomentSummary contract.',
                'share_status': 'Share readiness not evaluated yet.',
                'quality_note': 'Highlight quality is not evaluated yet.',
                'astrophoto_note': 'Highlight output depends on future moment evidence and source lineage.',
                'science_note': 'Meteor evidence is not connected yet.',
                'safe_actions_available': [],
                'is_placeholder': True,
            },
        ],
        'is_placeholder': True,
    }


def _build_sky_cycle_observatory_health_summary():
    return {
        'id': 'sky_cycle.observatory_health.placeholder',
        'label': 'Observatory Health',
        'status': 'Observatory health pending bounded backend contract.',
        'data_status': NOW_DATA_STATUS_FUTURE_CONTRACT,
        'overall_label': 'Health not evaluated yet',
        'camera_status': 'Camera status not evaluated here.',
        'capture_status': 'Capture continuity not evaluated here.',
        'storage_status': 'Storage status not evaluated here.',
        'generation_status': 'Generation status not evaluated here.',
        'integration_status': 'Upload/integration status not evaluated here.',
        'warnings_count_label': 'Warnings not evaluated yet',
        'risk_level': NOW_RISK_LEVEL_UNKNOWN,
        'evidence': [
            'No live service checks are performed in this prototype.',
            'Storage and generation status are not evaluated here.',
        ],
        'note': 'Observatory health pending bounded backend contract.',
        'is_placeholder': True,
    }


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


def _build_highlights_summary(highlight_items=None):
    highlight_items = list(highlight_items or [])
    real_items = [item for item in highlight_items if not item.get('is_placeholder', True)]
    primary = real_items[0] if real_items else None

    if primary:
        count_label = '{0:d} metadata Highlight candidate(s)'.format(len(real_items))
        primary_highlight = primary.get('title', 'Metadata Highlight candidate')
        attention_verdict = 'Hybrid selected explainable metadata candidates for review.'
        is_placeholder = False
    else:
        count_label = '4 placeholder Highlights'
        primary_highlight = 'No primary Highlight selected from real data'
        attention_verdict = 'Highlight selection is not connected to real detector data yet.'
        is_placeholder = True

    return {
        'id': 'highlights.summary.placeholder',
        'label': 'Highlights Summary',
        'title': 'Highlights',
        'data_status': NOW_DATA_STATUS_PLACEHOLDER,
        'count_label': count_label,
        'primary_highlight': primary_highlight,
        'attention_verdict': attention_verdict,
        'note': 'Highlights are curated attention objects. They explain what deserves review before the user explores reports or archives.',
        'is_placeholder': is_placeholder,
    }


def _build_highlight_items(highlights_repository=None):
    if highlights_repository is not None:
        try:
            metadata = highlights_repository.get_highlight_metadata()
        except Exception:
            metadata = _build_highlights_metadata_unavailable('Highlight metadata repository failed safely.')

        if isinstance(metadata, dict):
            items = metadata.get('items') or []
            sanitized_items = [
                item for item in (_sanitize_highlight_item(item) for item in items)
                if item is not None
            ]
            if sanitized_items:
                return sanitized_items

    return [
        {
            'highlight_id': 'highlight.placeholder.meteor',
            'title': 'Possible meteor candidate',
            'type': 'meteor_candidate',
            'target_kind': 'moment',
            'target_label': 'Future Moment detail',
            'data_status': NOW_DATA_STATUS_FUTURE_CONTRACT,
            'origin': 'detector',
            'selection_reason': 'Selected because: detector evidence pending backend contract.',
            'confidence_label': 'Confidence not evaluated yet',
            'evidence': [
                'No detector evidence is connected in this prototype.',
                'Source lineage and related output status are placeholders.',
            ],
            'phase': 'night',
            'sky_cycle_context': 'Sky Cycle context pending backend contract.',
            'source_trust_status': 'Source trust not evaluated yet.',
            'related_output_status': 'Related output not evaluated yet.',
            'favorite_status': 'Favorite is a future user decision, not the same as Highlight.',
            'review_status': 'Suggested placeholder',
            'safe_actions_available': [],
            'is_placeholder': True,
        },
        {
            'highlight_id': 'highlight.placeholder.timelapse',
            'title': 'Generated timelapse candidate',
            'type': 'generated_output',
            'target_kind': 'output',
            'target_label': 'Future Output detail',
            'data_status': NOW_DATA_STATUS_FUTURE_CONTRACT,
            'origin': 'hybrid_suggested',
            'selection_reason': 'Selected because: generated output readiness will become an attention signal.',
            'confidence_label': 'Output quality not evaluated yet',
            'evidence': [
                'Generated output status pending rendering contract.',
                'Look policy and share readiness are not connected yet.',
            ],
            'phase': 'unknown',
            'sky_cycle_context': 'Parent Sky Cycle not evaluated yet.',
            'source_trust_status': 'Source lineage pending source contract.',
            'related_output_status': 'Output metadata placeholder only.',
            'favorite_status': 'Not favorited; user decision unavailable in prototype.',
            'review_status': 'Suggested placeholder',
            'safe_actions_available': [],
            'is_placeholder': True,
        },
        {
            'highlight_id': 'highlight.placeholder.storage',
            'title': 'Source preservation attention item',
            'type': 'observatory_issue',
            'target_kind': 'observatory_issue',
            'target_label': 'Future Observatory issue detail',
            'data_status': NOW_DATA_STATUS_FUTURE_CONTRACT,
            'origin': 'rule',
            'selection_reason': 'Selected because: source trust warnings should be promoted before exploration.',
            'confidence_label': 'Risk not evaluated yet',
            'evidence': [
                'No storage, source coverage, or retention check is performed here.',
                'Observatory issues can become Highlights when they affect trust.',
            ],
            'phase': 'unknown',
            'sky_cycle_context': 'Affected Sky Cycle not evaluated yet.',
            'source_trust_status': 'RAW/FITS/source preservation not evaluated in this prototype.',
            'related_output_status': 'Affected outputs not evaluated yet.',
            'favorite_status': 'Operational Highlights are not favorites by default.',
            'review_status': 'Blocked pending bounded health contract',
            'safe_actions_available': [],
            'is_placeholder': True,
        },
        {
            'highlight_id': 'highlight.placeholder.clear-window',
            'title': 'Clear window candidate',
            'type': 'clear_window',
            'target_kind': 'sky_cycle',
            'target_label': 'Future Sky Cycle context',
            'data_status': NOW_DATA_STATUS_FUTURE_CONTRACT,
            'origin': 'future_ai',
            'selection_reason': 'Selected because: future AI may identify visually or scientifically useful clear windows.',
            'confidence_label': 'Future AI suggestion not evaluated yet',
            'evidence': [
                'AI suggestions must be explanatory and reversible.',
                'Sky quality and cloud evidence are not connected yet.',
            ],
            'phase': 'unknown',
            'sky_cycle_context': 'Cycle phase and time range not evaluated yet.',
            'source_trust_status': 'Source coverage pending bounded backend contract.',
            'related_output_status': 'Related best image or timelapse not evaluated yet.',
            'favorite_status': 'User may favorite a confirmed Highlight in the future.',
            'review_status': 'Suggested placeholder',
            'safe_actions_available': [],
            'is_placeholder': True,
        },
    ]


def _build_highlights_source_trust_summary():
    return {
        'id': 'highlights.source_trust.placeholder',
        'label': 'Source Trust',
        'status': 'Source trust not evaluated yet.',
        'data_status': NOW_DATA_STATUS_NOT_EVALUATED,
        'coverage_label': 'Source coverage pending bounded backend contract.',
        'preservation_status': 'RAW/FITS/source preservation not evaluated in this prototype.',
        'lineage_status': 'Highlight to source lineage is not connected yet.',
        'risk_level': NOW_RISK_LEVEL_UNKNOWN,
        'evidence': [
            'No RAW/FITS/source coverage calculation is connected yet.',
            'Highlights must not imply source safety until lineage exists.',
        ],
        'note': 'This panel will explain whether highlighted items are backed by trustworthy preserved source data.',
        'is_placeholder': True,
    }


def _build_highlights_review_queue_summary():
    return {
        'id': 'highlights.review_queue.placeholder',
        'label': 'Review Queue',
        'status': 'Review queue not evaluated yet.',
        'data_status': NOW_DATA_STATUS_FUTURE_CONTRACT,
        'count_label': 'No real review queue connected',
        'suggested_count_label': 'Suggested count placeholder',
        'confirmed_count_label': 'Confirmed count placeholder',
        'favorite_count_label': 'Favorite count placeholder',
        'ignored_count_label': 'Ignored count placeholder',
        'note': 'Hybrid suggestions are explanatory and reversible. Favorites are user decisions; Highlights are curated attention objects.',
        'is_placeholder': True,
    }


def _build_highlights_selection_policy_summary():
    return {
        'id': 'highlights.selection_policy.placeholder',
        'label': 'Selection Policy',
        'status': 'Selection policy not connected yet.',
        'data_status': NOW_DATA_STATUS_FUTURE_CONTRACT,
        'policy_label': 'Attention before exploration',
        'explainability_status': 'Every Highlight must explain why it was selected.',
        'reversibility_status': 'Hybrid suggests; user decides.',
        'allowed_origins': sorted(HIGHLIGHT_ALLOWED_ORIGINS),
        'note': 'Product intelligence must be explainable, bounded, and safe for Raspberry Pi 5.',
        'is_placeholder': True,
    }


def _build_highlights_attention_items():
    return NowSection(
        id='highlights.attention.placeholder',
        label='Attention Items',
        status='No real attention items connected yet.',
        data_status=NOW_DATA_STATUS_FUTURE_CONTRACT,
        is_placeholder=True,
        summary='Highlight selection is static and does not call detector, media, source, or health runtime.',
        note='No safe action, confirmation, favorite, ignore, archive, download, share, or regeneration behavior is connected.',
    ).to_dict()


def _build_highlights_metadata():
    return {
        'contract': 'HighlightsView',
        'contract_version': 'v1.static',
        'source': 'build_highlights_view',
        'data_status': NOW_DATA_STATUS_PLACEHOLDER,
        'is_placeholder': True,
        'rp5_policy': 'No database, detector, filesystem, media generation, preview URL, or runtime health check.',
    }


def _build_moment_detail_summary():
    return {
        'id': 'moment.summary.placeholder',
        'label': 'Moment Summary',
        'title': 'Possible meteor candidate',
        'type': 'meteor_candidate',
        'phase': 'night',
        'timestamp_label': 'Timestamp not evaluated yet',
        'confidence_label': 'Confidence not evaluated yet',
        'data_status': NOW_DATA_STATUS_FUTURE_CONTRACT,
        'selection_reason': 'Selected because: brightness changed across consecutive frames; detector evidence is not connected yet.',
        'note': 'This read-only prototype explains why Hybrid would show this Moment without claiming real detection.',
        'is_placeholder': True,
    }


def _build_moment_detail_evidence_summary():
    return {
        'id': 'moment.evidence.placeholder',
        'label': 'Evidence Summary',
        'data_status': NOW_DATA_STATUS_FUTURE_CONTRACT,
        'evidence': [
            'Detector evidence not connected yet.',
            'Brightness changed across four consecutive frames is placeholder microcopy.',
            'No source frames are read by this prototype.',
        ],
        'detector_status': 'Detector evidence not connected yet.',
        'explanation': 'Hybrid would show this case because a bounded future detector or Highlight target says it deserves review.',
        'science_note': 'Scientific confidence requires detector evidence, source lineage, and preservation status.',
        'is_placeholder': True,
    }


def _build_moment_detail_source_trust_summary():
    return {
        'id': 'moment.source_trust.placeholder',
        'label': 'Source Trust',
        'data_status': NOW_DATA_STATUS_FUTURE_CONTRACT,
        'source_status': 'Source status not evaluated yet.',
        'lineage_status': 'Source lineage pending source contract.',
        'preservation_status': 'Source preservation not evaluated in this prototype.',
        'confidence': 'Unknown until source trust contract exists.',
        'note': 'Moment confidence should not be trusted until source lineage and preservation are connected.',
        'is_placeholder': True,
    }


def _build_moment_detail_related_outputs():
    return {
        'id': 'moment.related_outputs.placeholder',
        'label': 'Related Outputs',
        'data_status': NOW_DATA_STATUS_FUTURE_CONTRACT,
        'generation_status': 'Generated output status pending rendering contract.',
        'look_status': 'Look policy not connected yet.',
        'outputs': [
            {
                'id': 'moment.output.placeholder',
                'label': 'Potential highlight clip',
                'type': 'highlight_clip',
                'status': 'Output not generated or evaluated here.',
                'data_status': NOW_DATA_STATUS_FUTURE_CONTRACT,
                'source_lineage_status': 'Source lineage pending source contract.',
                'is_placeholder': True,
            },
        ],
        'note': 'Related outputs are placeholders until Output Detail and rendering contracts exist.',
        'is_placeholder': True,
    }


def _build_moment_detail_sky_cycle_context():
    return {
        'id': 'moment.sky_cycle_context.placeholder',
        'label': 'Sky Cycle Context',
        'data_status': NOW_DATA_STATUS_FUTURE_CONTRACT,
        'phase': 'night',
        'cycle_label': 'Sky Cycle not evaluated yet',
        'position_in_cycle': 'Position in cycle pending backend contract.',
        'note': 'Sky Cycle context is intentionally static until a bounded cycle context provider exists.',
        'is_placeholder': True,
    }


def _build_moment_detail_observatory_context():
    return {
        'id': 'moment.observatory_context.placeholder',
        'label': 'Observatory Context',
        'data_status': NOW_DATA_STATUS_FUTURE_CONTRACT,
        'camera': 'Camera not evaluated yet',
        'capture': 'Capture status not evaluated here.',
        'health_summary': 'Observatory health pending bounded backend contract.',
        'note': 'No live service check, camera connection, or runtime health evaluation is performed.',
        'is_placeholder': True,
    }


def _build_moment_detail_metadata():
    return {
        'contract': 'MomentDetailView',
        'contract_version': 'v1.static',
        'source': 'build_moment_detail_view',
        'data_status': NOW_DATA_STATUS_PLACEHOLDER,
        'is_placeholder': True,
        'rp5_policy': 'No database, detector, filesystem, media generation, preview URL, or runtime health check.',
    }


def _build_output_detail_summary():
    return {
        'id': 'output.summary.placeholder',
        'label': 'Output Summary',
        'title': 'Generated meteor highlight',
        'type': 'meteor_highlight',
        'data_status': NOW_DATA_STATUS_FUTURE_CONTRACT,
        'generation_status': 'Generated output status pending rendering contract.',
        'phase': 'night',
        'sky_cycle_label': 'Sky Cycle not evaluated yet',
        'note': 'This read-only prototype describes a generated result without reading media or starting rendering.',
        'is_placeholder': True,
    }


def _build_output_detail_preview_summary():
    return {
        'id': 'output.preview.placeholder',
        'label': 'Preview Summary',
        'preview_status': 'Preview intentionally disabled in this prototype.',
        'data_status': NOW_DATA_STATUS_NOT_EVALUATED,
        'preview_available': False,
        'safe_preview_url': None,
        'note': 'Preview remains unavailable until a sanitized preview contract exists.',
        'is_placeholder': True,
    }


def _build_output_detail_recipe_summary():
    return {
        'id': 'output.recipe.placeholder',
        'label': 'Output Recipe',
        'data_status': NOW_DATA_STATUS_FUTURE_CONTRACT,
        'look_applied': 'Look not evaluated yet',
        'recipe_status': 'Output recipe pending rendering contract.',
        'rendering_intent': 'Astrophoto review output; intent not evaluated from real data.',
        'non_destructive_status': 'Rendering is non-destructive; source data remains authoritative.',
        'version_label': 'Recipe version not evaluated yet',
        'note': 'Looks and recipes are metadata until bounded rendering contracts exist.',
        'is_placeholder': True,
    }


def _build_output_detail_source_lineage_summary():
    return {
        'id': 'output.source_lineage.placeholder',
        'label': 'Source Lineage',
        'data_status': NOW_DATA_STATUS_FUTURE_CONTRACT,
        'source_status': 'Source lineage is not connected yet.',
        'lineage_status': 'Output-to-source relationship pending source contract.',
        'source_types': [
            'image metadata',
            'source frames',
        ],
        'source_coverage_label': 'Source coverage not evaluated yet',
        'preservation_status': 'Source preservation not evaluated in this prototype.',
        'trust_level': NOW_RISK_LEVEL_UNKNOWN,
        'evidence': [
            'No source coverage calculation is connected yet.',
            'No source frame or media read is performed by this prototype.',
        ],
        'is_placeholder': True,
    }


def _build_output_detail_related_moments():
    return {
        'id': 'output.related_moments.placeholder',
        'label': 'Related Moments',
        'data_status': NOW_DATA_STATUS_FUTURE_CONTRACT,
        'relation_status': 'Moment relationship pending backend contract.',
        'items': [
            {
                'id': 'output.related_moment.placeholder',
                'label': 'Possible meteor candidate',
                'type': 'meteor_candidate',
                'phase': 'night',
                'data_status': NOW_DATA_STATUS_FUTURE_CONTRACT,
                'relation_label': 'Potential source Moment for this output.',
                'confidence_label': 'Moment confidence not evaluated yet',
                'is_placeholder': True,
            },
        ],
        'note': 'Related Moments explain why an output exists, but no real detector relation is connected.',
        'is_placeholder': True,
    }


def _build_output_detail_sky_cycle_context():
    return {
        'id': 'output.sky_cycle_context.placeholder',
        'label': 'Sky Cycle Context',
        'data_status': NOW_DATA_STATUS_FUTURE_CONTRACT,
        'cycle_label': 'Sky Cycle not evaluated yet',
        'phase': 'night',
        'time_range_label': 'Time range not evaluated yet',
        'context_status': 'Sky Cycle context pending backend contract.',
        'is_placeholder': True,
    }


def _build_output_detail_share_readiness_summary():
    return {
        'id': 'output.share_readiness.placeholder',
        'label': 'Review Readiness',
        'status': 'Not ready for external delivery.',
        'data_status': NOW_DATA_STATUS_FUTURE_CONTRACT,
        'export_status': 'Export readiness not evaluated yet.',
        'share_status': 'External sharing not connected.',
        'limitations': [
            'No preview contract connected.',
            'No source lineage connected.',
            'No rendering recipe connected.',
        ],
        'safe_actions_available': [],
        'is_placeholder': True,
    }


def _build_output_detail_metadata():
    return {
        'contract': 'OutputDetailView',
        'contract_version': 'v1.static',
        'source': 'build_output_detail_view',
        'data_status': NOW_DATA_STATUS_PLACEHOLDER,
        'is_placeholder': True,
        'rp5_policy': 'No database, filesystem, media read, media generation, preview URL, rendering job, or external delivery.',
    }


def _build_library_summary():
    return {
        'id': 'library.summary.placeholder',
        'label': 'Library Summary',
        'title': 'Library',
        'data_status': NOW_DATA_STATUS_PLACEHOLDER,
        'scope_label': 'Highlights, Moments, Outputs, Sky Cycles, and future Favorites',
        'total_items_label': 'No indexed items evaluated yet',
        'note': 'This view will help retrieve notable sky observations over time. Library indexing is not connected yet.',
        'is_placeholder': True,
    }


def _build_library_collection_summary():
    return {
        'id': 'library.collections.placeholder',
        'label': 'Collections',
        'data_status': NOW_DATA_STATUS_FUTURE_CONTRACT,
        'collections': [
            {
                'key': 'highlights',
                'label': 'Highlights',
                'type': 'highlights',
                'data_status': NOW_DATA_STATUS_FUTURE_CONTRACT,
                'count_label': 'No real Highlights indexed',
                'description': 'Curated attention objects selected by Hybrid or the user.',
                'example_query': 'meteor highlights from last winter',
                'is_placeholder': True,
            },
            {
                'key': 'moments',
                'label': 'Moments',
                'type': 'moments',
                'data_status': NOW_DATA_STATUS_FUTURE_CONTRACT,
                'count_label': 'No real Moments indexed',
                'description': 'Cases worth analyzing, such as meteors, storms, clear windows, and anomalies.',
                'example_query': 'clear windows during moonless nights',
                'is_placeholder': True,
            },
            {
                'key': 'outputs',
                'label': 'Outputs',
                'type': 'outputs',
                'data_status': NOW_DATA_STATUS_FUTURE_CONTRACT,
                'count_label': 'No generated Outputs indexed',
                'description': 'Generated or derived results such as timelapse, keogram, startrail, and highlights.',
                'example_query': 'startrails with high source trust',
                'is_placeholder': True,
            },
            {
                'key': 'sky_cycles',
                'label': 'Sky Cycles',
                'type': 'sky_cycles',
                'data_status': NOW_DATA_STATUS_FUTURE_CONTRACT,
                'count_label': 'No Sky Cycles indexed',
                'description': 'Day-and-night observation cycles with phases, source confidence, and output context.',
                'example_query': 'cycles with aurora candidates',
                'is_placeholder': True,
            },
            {
                'key': 'favorites',
                'label': 'Favorites',
                'type': 'favorites',
                'data_status': NOW_DATA_STATUS_FUTURE_CONTRACT,
                'count_label': 'Favorites not connected yet',
                'description': 'Future user-curated items kept for review, export, or long-term memory.',
                'example_query': 'my favorite aurora outputs',
                'is_placeholder': True,
            },
            {
                'key': 'phenomena',
                'label': 'Phenomena',
                'type': 'phenomena',
                'data_status': NOW_DATA_STATUS_FUTURE_CONTRACT,
                'count_label': 'Phenomena index not connected',
                'description': 'Meteor, aurora, storm, cloud, Moon, sky-quality, and anomaly groupings.',
                'example_query': 'lightning candidates in summer',
                'is_placeholder': True,
            },
        ],
        'note': 'Collections are static placeholders until bounded archive contracts exist.',
        'is_placeholder': True,
    }


def _build_library_search_summary():
    return {
        'id': 'library.search.placeholder',
        'label': 'Search Summary',
        'data_status': NOW_DATA_STATUS_FUTURE_CONTRACT,
        'search_status': 'Library search is not connected yet.',
        'indexed_fields': [
            'kind',
            'date',
            'phase',
            'phenomenon',
            'source trust',
            'output status',
        ],
        'unavailable_reason': 'No database, filesystem, media, or index provider is connected.',
        'note': 'Search should become bounded, paginated, and safe for Raspberry Pi 5 before any runtime integration.',
        'is_placeholder': True,
    }


def _build_library_filter_summary():
    return {
        'id': 'library.filters.placeholder',
        'label': 'Filter Summary',
        'data_status': NOW_DATA_STATUS_FUTURE_CONTRACT,
        'available_filters': [
            'kind',
            'phase',
            'phenomenon',
            'source trust',
        ],
        'disabled_filters': [
            'date range',
            'camera',
            'Look',
            'favorite status',
            'saved search',
        ],
        'note': 'Filters are described as product requirements only; no filtering is performed in this prototype.',
        'is_placeholder': True,
    }


def _build_library_recent_items():
    return {
        'id': 'library.recent_items.placeholder',
        'label': 'Recent Items',
        'data_status': NOW_DATA_STATUS_FUTURE_CONTRACT,
        'items': [
            {
                'item_id': 'library.item.highlight.placeholder',
                'title': 'Possible meteor candidate',
                'kind': 'highlight',
                'data_status': NOW_DATA_STATUS_FUTURE_CONTRACT,
                'date_label': 'Date not evaluated yet',
                'phase': 'night',
                'highlight_status': 'Suggested placeholder',
                'source_trust_status': 'Source trust not evaluated yet',
                'output_status': 'Related output not evaluated yet',
                'note': 'Example of a future Highlight retrieved from the archive.',
                'is_placeholder': True,
            },
            {
                'item_id': 'library.item.output.placeholder',
                'title': 'Generated meteor highlight',
                'kind': 'output',
                'data_status': NOW_DATA_STATUS_FUTURE_CONTRACT,
                'date_label': 'Date not evaluated yet',
                'phase': 'night',
                'highlight_status': 'Related Highlight not evaluated yet',
                'source_trust_status': 'Source lineage pending source contract',
                'output_status': 'Generated output status pending rendering contract',
                'note': 'Example of a future Output retrieved by source trust or phenomenon.',
                'is_placeholder': True,
            },
            {
                'item_id': 'library.item.sky_cycle.placeholder',
                'title': 'Sky Cycle with clear-window candidate',
                'kind': 'sky_cycle',
                'data_status': NOW_DATA_STATUS_FUTURE_CONTRACT,
                'date_label': 'Date not evaluated yet',
                'phase': 'unknown',
                'highlight_status': 'Cycle highlights not evaluated yet',
                'source_trust_status': 'Source coverage pending bounded backend contract',
                'output_status': 'Cycle outputs not evaluated yet',
                'note': 'Example of a future Sky Cycle entry retrieved by condition or event.',
                'is_placeholder': True,
            },
        ],
        'note': 'Recent items are static examples and do not read archive, media, or source data.',
        'is_placeholder': True,
    }


def _build_library_memory_model_summary():
    return {
        'id': 'library.memory_model.placeholder',
        'label': 'Memory Model',
        'data_status': NOW_DATA_STATUS_FUTURE_CONTRACT,
        'status': 'Long-term memory model not connected yet.',
        'explanation': 'Library should help retrieve notable sky observations by meaning, not by raw implementation paths.',
        'future_favorites_status': 'Favorites are future user-curation features.',
        'future_tags_status': 'Tags are not connected yet.',
        'future_saved_searches_status': 'Saved searches are future user-curation features.',
        'is_placeholder': True,
    }


def _build_library_metadata():
    return {
        'contract': 'LibraryView',
        'contract_version': 'v1.static',
        'source': 'build_library_view',
        'data_status': NOW_DATA_STATUS_PLACEHOLDER,
        'is_placeholder': True,
        'rp5_policy': 'No database, query, filesystem, media read, indexing provider, preview URL, or archive scan.',
    }


def _build_observatory_summary():
    return {
        'id': 'observatory.summary.placeholder',
        'label': 'Observatory Summary',
        'title': 'Observatory',
        'data_status': NOW_DATA_STATUS_PLACEHOLDER,
        'overall_status': 'not_evaluated',
        'readiness_label': 'System readiness not evaluated yet',
        'note': 'System readiness will summarize whether the observatory can capture reliably. No live service probes are performed in this prototype.',
        'is_placeholder': True,
    }


def _build_observatory_camera_system_summary():
    return {
        'id': 'observatory.camera.placeholder',
        'label': 'Camera System',
        'status': 'not_evaluated',
        'data_status': NOW_DATA_STATUS_FUTURE_CONTRACT,
        'camera_label': 'Camera not evaluated yet',
        'profile_label': 'Profile not evaluated yet',
        'capture_status': 'Capture status pending bounded backend contract.',
        'backend_status': 'Camera backend status not evaluated yet.',
        'note': 'Camera readiness is represented as product health metadata only.',
        'is_placeholder': True,
    }


def _build_observatory_capture_pipeline_summary():
    return {
        'id': 'observatory.capture_pipeline.placeholder',
        'label': 'Capture Pipeline',
        'status': 'not_evaluated',
        'data_status': NOW_DATA_STATUS_FUTURE_CONTRACT,
        'latest_frame_status': 'Latest frame continuity not evaluated yet.',
        'cadence_status': 'Capture cadence not evaluated yet.',
        'day_night_status': 'Day/night capture behavior not evaluated yet.',
        'note': 'Capture pipeline summary is static until a bounded capture health provider exists.',
        'is_placeholder': True,
    }


def _build_observatory_source_preservation_summary():
    return {
        'id': 'observatory.source_preservation.placeholder',
        'label': 'Source Preservation',
        'status': 'not_evaluated',
        'data_status': NOW_DATA_STATUS_FUTURE_CONTRACT,
        'preservation_label': 'Source preservation status pending bounded backend contract.',
        'raw_status': 'RAW/source status not evaluated yet.',
        'fits_status': 'FITS status not evaluated yet.',
        'lineage_status': 'Source lineage not connected yet.',
        'trust_level': NOW_RISK_LEVEL_UNKNOWN,
        'note': 'Source preservation must be trustworthy before generated results can be fully trusted.',
        'is_placeholder': True,
    }


def _build_observatory_storage_summary():
    return {
        'id': 'observatory.storage.placeholder',
        'label': 'Storage',
        'status': 'not_evaluated',
        'data_status': NOW_DATA_STATUS_FUTURE_CONTRACT,
        'storage_label': 'Storage status not evaluated yet.',
        'retention_status': 'Retention policy not evaluated yet.',
        'risk_level': NOW_RISK_LEVEL_UNKNOWN,
        'note': 'Storage health is not connected to live capacity or retention checks in this prototype.',
        'is_placeholder': True,
    }


def _build_observatory_generation_summary():
    return {
        'id': 'observatory.generation.placeholder',
        'label': 'Generation',
        'status': 'not_evaluated',
        'data_status': NOW_DATA_STATUS_FUTURE_CONTRACT,
        'outputs_status': 'Generated outputs status pending rendering contract.',
        'queue_status': 'Generation queue status not evaluated yet.',
        'rendering_status': 'Rendering readiness not evaluated yet.',
        'note': 'No rendering, queue inspection, or media generation is connected.',
        'is_placeholder': True,
    }


def _build_observatory_integration_summary():
    return {
        'id': 'observatory.integrations.placeholder',
        'label': 'Integrations',
        'status': 'not_evaluated',
        'data_status': NOW_DATA_STATUS_FUTURE_CONTRACT,
        'upload_status': 'Upload status not evaluated yet.',
        'remote_status': 'Remote integration status not evaluated yet.',
        'notification_status': 'Notification delivery status not evaluated yet.',
        'note': 'No remote service lookup or integration status lookup is performed.',
        'is_placeholder': True,
    }


def _build_observatory_attention_items():
    return {
        'id': 'observatory.attention.placeholder',
        'label': 'Attention Items',
        'data_status': NOW_DATA_STATUS_FUTURE_CONTRACT,
        'items': [
            {
                'id': 'observatory.attention.source.placeholder',
                'label': 'Source trust not evaluated',
                'status': 'not_evaluated',
                'data_status': NOW_DATA_STATUS_FUTURE_CONTRACT,
                'risk_level': NOW_RISK_LEVEL_UNKNOWN,
                'note': 'Source preservation and lineage require a future bounded health contract.',
                'is_placeholder': True,
            },
            {
                'id': 'observatory.attention.storage.placeholder',
                'label': 'Storage risk not evaluated',
                'status': 'not_evaluated',
                'data_status': NOW_DATA_STATUS_FUTURE_CONTRACT,
                'risk_level': NOW_RISK_LEVEL_UNKNOWN,
                'note': 'Storage capacity and retention are not inspected by this prototype.',
                'is_placeholder': True,
            },
        ],
        'note': 'Attention items are static examples until Observatory Health has bounded data sources.',
        'is_placeholder': True,
    }


def _build_observatory_metadata():
    return {
        'contract': 'ObservatoryView',
        'contract_version': 'v1.static',
        'source': 'build_observatory_view',
        'data_status': NOW_DATA_STATUS_PLACEHOLDER,
        'is_placeholder': True,
        'rp5_policy': 'No database, query, filesystem, device probe, camera connection probe, remote service access, media read, preview URL, or refresh loop.',
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
        frame_metadata={},
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
        frame_metadata={},
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
        frame_metadata={},
        note='Latest frame repository returned unsafe or unsupported metadata.',
        evidence='No unsafe repository values are exposed in the NowView payload.',
        is_placeholder=True,
    ).to_dict()


def _build_latest_generated_output_empty():
    return {
        'status': 'no_generated_output_metadata',
        'data_status': NOW_DATA_STATUS_NOT_EVALUATED,
        'output': {},
        'partial_failures': 0,
        'note': 'No generated output metadata row is available from the injected descriptors.',
    }


def _build_latest_generated_output_unavailable(note):
    return {
        'status': 'generated_output_metadata_unavailable',
        'data_status': NOW_DATA_STATUS_NOT_EVALUATED,
        'output': {},
        'partial_failures': 0,
        'note': _latest_frame_text(note, 'Generated output metadata unavailable.'),
    }


def _build_source_trust_empty():
    return {
        'status': 'no_source_metadata',
        'data_status': NOW_DATA_STATUS_NOT_EVALUATED,
        'sources': [],
        'partial_failures': 0,
        'note': 'No bounded RAW/FITS source metadata row is available from the injected descriptors.',
    }


def _build_source_trust_unavailable(note):
    return {
        'status': 'source_metadata_unavailable',
        'data_status': NOW_DATA_STATUS_NOT_EVALUATED,
        'sources': [],
        'partial_failures': 0,
        'note': _latest_frame_text(note, 'Source metadata unavailable.'),
    }


def _build_highlights_metadata_empty():
    return {
        'status': 'no_highlight_metadata',
        'data_status': NOW_DATA_STATUS_NOT_EVALUATED,
        'items': [],
        'note': 'No bounded image metadata produced an explainable Highlight candidate.',
    }


def _build_highlights_metadata_unavailable(note):
    return {
        'status': 'highlight_metadata_unavailable',
        'data_status': NOW_DATA_STATUS_NOT_EVALUATED,
        'items': [],
        'note': _latest_frame_text(note, 'Highlight metadata unavailable.'),
    }


def _build_sky_cycle_metadata_empty():
    return {
        'status': 'no_sky_cycle_metadata',
        'data_status': NOW_DATA_STATUS_NOT_EVALUATED,
        'latest_frame': {},
        'cycle_start': {},
        'current_date': None,
        'note': 'No image metadata row is available for a Sky Cycle summary.',
    }


def _build_sky_cycle_metadata_unavailable(note):
    return {
        'status': 'sky_cycle_metadata_unavailable',
        'data_status': NOW_DATA_STATUS_NOT_EVALUATED,
        'latest_frame': {},
        'cycle_start': {},
        'current_date': None,
        'note': _latest_frame_text(note, 'Sky Cycle metadata unavailable.'),
    }


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
        'contract_version': 'v1-bounded-metadata',
        'source': 'backend-owned builder with optional bounded metadata repositories',
        'data_status': NOW_DATA_STATUS_PLACEHOLDER,
        'notes': [
            'Only explicitly injected bounded metadata repositories are evaluated.',
            'No filesystem, source file, media read, preview, generation, or mutative action is performed.',
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

    frame_metadata = metadata.get('frame_metadata', {})
    if not isinstance(frame_metadata, dict):
        raise ValueError('latest frame metadata frame_metadata must be a dict')

    frame_metadata_keys = set(frame_metadata.keys())
    unsupported_frame_metadata_keys = frame_metadata_keys.difference(NOW_LATEST_FRAME_METADATA_KEYS)
    if unsupported_frame_metadata_keys:
        raise ValueError('latest frame metadata contains unsupported frame metadata keys')

    for key, value in frame_metadata.items():
        key_lower = str(key).lower()
        if any(token in key_lower for token in NOW_SENSITIVE_KEY_TOKENS):
            raise ValueError('latest frame metadata contains sensitive frame metadata keys')

        if not _latest_frame_metadata_value_is_json_safe(value):
            raise ValueError('latest frame metadata contains non-primitive values')

        if _latest_frame_value_is_unsafe(value):
            raise ValueError('latest frame metadata contains unsafe frame metadata values')

    return {
        'camera_label': _latest_frame_text(metadata.get('camera_label'), 'Camera not evaluated yet'),
        'profile_label': _latest_frame_text(metadata.get('profile_label'), 'Profile not evaluated yet'),
        'timestamp': _latest_frame_text(metadata.get('timestamp'), 'Not evaluated yet'),
        'age_label': _latest_frame_text(metadata.get('age_label'), 'Not evaluated yet'),
        'image_available': bool(metadata.get('image_available', False)),
        'source_status': _latest_frame_text(metadata.get('source_status'), 'Source status not evaluated yet.'),
        'frame_metadata': frame_metadata,
    }


def _latest_frame_row_metadata(row, created_at):
    metadata = {
        'id': _latest_frame_json_value(getattr(row, 'id', None)),
        'camera_id': _latest_frame_json_value(getattr(row, 'camera_id', None)),
        'timestamp': _latest_frame_timestamp_label(created_at),
        'exposure': _latest_frame_json_value(getattr(row, 'exposure', None)),
        'gain': _latest_frame_json_value(getattr(row, 'gain', None)),
        'binmode': _latest_frame_json_value(getattr(row, 'binmode', None)),
        'temp': _latest_frame_json_value(getattr(row, 'temp', None)),
        'night': _latest_frame_json_value(getattr(row, 'night', None)),
        'adu': _latest_frame_json_value(getattr(row, 'adu', None)),
        'sqm': _latest_frame_json_value(getattr(row, 'sqm', None)),
        'stars': _latest_frame_json_value(getattr(row, 'stars', None)),
        'detections': _latest_frame_json_value(getattr(row, 'detections', None)),
        'file_size': _latest_frame_json_value(getattr(row, 'fileSize', None)),
        'width': _latest_frame_json_value(getattr(row, 'width', None)),
        'height': _latest_frame_json_value(getattr(row, 'height', None)),
    }

    return {
        key: value
        for key, value in metadata.items()
        if _latest_frame_metadata_value_is_json_safe(value) and not _latest_frame_value_is_unsafe(value)
    }


def _latest_generated_output_row_metadata(descriptor, row):
    created_at = getattr(row, 'createDate', None)
    timestamp = _latest_frame_timestamp_label(created_at)
    field_map = getattr(descriptor, 'field_map', None) or LatestGeneratedOutputRepository.DEFAULT_FIELD_MAP

    metadata = {
        'output_type': _latest_generated_output_text(getattr(descriptor, 'output_type', None), 'unknown'),
        'timestamp': timestamp,
        'status_label': _latest_generated_output_text(getattr(descriptor, 'status_label', None), 'Generated output metadata available.'),
        'source_table_label': _latest_generated_output_text(getattr(descriptor, 'source_table_label', None), 'Generated output source'),
        '_sort_key': _latest_generated_output_sort_key(created_at, timestamp),
    }

    for output_key, row_key in field_map.items():
        if output_key in metadata:
            continue

        metadata[output_key] = _latest_generated_output_json_value(getattr(row, row_key, None))

    return {
        key: value
        for key, value in metadata.items()
        if key == '_sort_key' or (
            _latest_frame_metadata_value_is_json_safe(value) and not _latest_frame_value_is_unsafe(value)
        )
    }


def _source_trust_row_metadata(descriptor, row):
    created_at = getattr(row, 'createDate', None)
    timestamp = _latest_frame_timestamp_label(created_at)
    field_map = getattr(descriptor, 'field_map', None) or SourceTrustRepository.DEFAULT_FIELD_MAP

    metadata = {
        'source_type': _source_trust_text(getattr(descriptor, 'source_type', None), 'unknown'),
        'source_label': _source_trust_text(getattr(descriptor, 'source_label', None), 'Source metadata'),
        'timestamp': timestamp,
    }

    for output_key, row_key in field_map.items():
        if output_key in metadata:
            continue

        metadata[output_key] = _latest_generated_output_json_value(getattr(row, row_key, None))

    return _sanitize_source_trust_source(metadata)


def _highlight_image_row_metadata(row):
    created_at = getattr(row, 'createDate', None)
    metadata = {
        'id': _latest_frame_json_value(getattr(row, 'id', None)),
        'camera_id': _latest_frame_json_value(getattr(row, 'camera_id', None)),
        'timestamp': _latest_frame_timestamp_label(created_at),
        'day_date': _latest_generated_output_json_value(getattr(row, 'dayDate', None)),
        'night': _latest_frame_json_value(getattr(row, 'night', None)),
        'detections': _latest_frame_json_value(getattr(row, 'detections', None)),
        'stars': _latest_frame_json_value(getattr(row, 'stars', None)),
        'sqm': _latest_frame_json_value(getattr(row, 'sqm', None)),
        'adu': _latest_frame_json_value(getattr(row, 'adu', None)),
        'kpindex': _latest_frame_json_value(getattr(row, 'kpindex', None)),
        'ovation_max': _latest_frame_json_value(getattr(row, 'ovation_max', None)),
        'smoke_rating': _latest_frame_json_value(getattr(row, 'smoke_rating', None)),
        'moonmode': _latest_frame_json_value(getattr(row, 'moonmode', None)),
        'stable': _latest_frame_json_value(getattr(row, 'stable', None)),
        'exclude': _latest_frame_json_value(getattr(row, 'exclude', None)),
        'width': _latest_frame_json_value(getattr(row, 'width', None)),
        'height': _latest_frame_json_value(getattr(row, 'height', None)),
    }

    return {
        key: value
        for key, value in metadata.items()
        if key in HIGHLIGHT_METADATA_ALLOWED_FIELDS
        and _latest_frame_metadata_value_is_json_safe(value)
        and not _latest_frame_value_is_unsafe(value)
    }


def _sky_cycle_image_row_metadata(row):
    created_at = getattr(row, 'createDate', None)
    metadata = {
        'id': _latest_frame_json_value(getattr(row, 'id', None)),
        'camera_id': _latest_frame_json_value(getattr(row, 'camera_id', None)),
        'timestamp': _latest_frame_timestamp_label(created_at),
        'day_date': _latest_generated_output_json_value(getattr(row, 'dayDate', None)),
        'night': _latest_frame_json_value(getattr(row, 'night', None)),
    }

    return {
        key: value
        for key, value in metadata.items()
        if _latest_frame_metadata_value_is_json_safe(value)
        and not _latest_frame_value_is_unsafe(value)
    }


def _sky_cycle_status(day_date, current_date, has_cycle_start):
    if not has_cycle_start:
        return SKY_CYCLE_STATUS_INCOMPLETE

    if day_date in (None, '', 'Unknown sky day') or current_date in (None, '', 'Not evaluated yet'):
        return SKY_CYCLE_STATUS_UNKNOWN

    if day_date == current_date:
        return SKY_CYCLE_STATUS_IN_PROGRESS

    return SKY_CYCLE_STATUS_COMPLETED


def _sky_cycle_verdict(cycle_status, phase):
    if cycle_status == SKY_CYCLE_STATUS_IN_PROGRESS:
        return 'Current Sky Cycle in progress.'

    if cycle_status == SKY_CYCLE_STATUS_COMPLETED:
        return 'Latest Sky Cycle appears completed from metadata.'

    if cycle_status == SKY_CYCLE_STATUS_INCOMPLETE:
        return 'Sky Cycle metadata is incomplete.'

    return 'Sky Cycle status unknown.'


def _highlight_item_from_image_metadata(metadata):
    if not isinstance(metadata, dict) or metadata.get('exclude') is True:
        return None

    timestamp = _latest_frame_text(metadata.get('timestamp'), 'Time not evaluated yet')
    phase = 'night' if metadata.get('night') is True else 'day' if metadata.get('night') is False else 'unknown'
    evidence = []

    detections = _safe_number(metadata.get('detections'))
    stars = _safe_number(metadata.get('stars'))
    sqm = _safe_number(metadata.get('sqm'))
    kpindex = _safe_number(metadata.get('kpindex'))
    ovation_max = _safe_number(metadata.get('ovation_max'))
    smoke_rating = _safe_number(metadata.get('smoke_rating'))
    stable = metadata.get('stable')

    if detections and detections > 0:
        highlight_type = 'meteor_candidate'
        title = 'Detection metadata candidate'
        selection_reason = 'Selected because: image metadata reports {0:g} detection(s).'.format(detections)
        confidence_label = 'Detection metadata present; detector details not connected.'
        evidence.append('detections={0:g}'.format(detections))
    elif (ovation_max and ovation_max >= 50) or (kpindex and kpindex >= 5):
        highlight_type = 'aurora_candidate'
        title = 'Aurora conditions metadata candidate'
        selection_reason = 'Selected because: aurora-related environment metadata is elevated.'
        confidence_label = 'Aurora context metadata present; visual confirmation not connected.'
        if ovation_max is not None:
            evidence.append('ovation_max={0:g}'.format(ovation_max))
        if kpindex is not None:
            evidence.append('kpindex={0:g}'.format(kpindex))
    elif smoke_rating and smoke_rating > 0:
        highlight_type = 'sky_quality'
        title = 'Sky quality attention item'
        selection_reason = 'Selected because: smoke/sky-condition metadata indicates possible reduced transparency.'
        confidence_label = 'Environmental metadata present; cloud classification not connected.'
        evidence.append('smoke_rating={0:g}'.format(smoke_rating))
    elif (stars and stars >= 20) or (sqm and sqm >= 18):
        highlight_type = 'clear_window'
        title = 'Clear window metadata candidate'
        selection_reason = 'Selected because: star/SQM metadata suggests a potentially useful observing window.'
        confidence_label = 'Sky quality metadata present; no image analysis performed.'
        if stars is not None:
            evidence.append('stars={0:g}'.format(stars))
        if sqm is not None:
            evidence.append('sqm={0:g}'.format(sqm))
    elif stable is False:
        highlight_type = 'observatory_issue'
        title = 'Frame stability attention item'
        selection_reason = 'Selected because: image metadata marks the frame as not stable.'
        confidence_label = 'Operational metadata present; root cause not evaluated.'
        evidence.append('stable=False')
    else:
        return None

    evidence.append('timestamp={0:s}'.format(timestamp))
    if metadata.get('id') is not None:
        evidence.append('image_metadata_id={0}'.format(metadata.get('id')))

    return {
        'highlight_id': 'highlight.metadata.{0}'.format(_latest_frame_text(str(metadata.get('id')), 'unknown')),
        'title': title,
        'type': highlight_type,
        'target_kind': 'moment',
        'target_label': 'Moment Detail',
        'data_status': NOW_DATA_STATUS_NOT_EVALUATED,
        'origin': 'rule',
        'selection_reason': selection_reason,
        'confidence_label': confidence_label,
        'evidence': evidence,
        'phase': phase,
        'sky_cycle_context': 'Sky Cycle context is not connected to this metadata candidate yet.',
        'source_trust_status': 'Source trust summarized separately; per-highlight lineage is not connected yet.',
        'related_output_status': 'Related output metadata is not connected to this Highlight yet.',
        'favorite_status': 'Favorite remains a future user decision.',
        'review_status': 'Suggested from metadata',
        'safe_actions_available': [],
        'is_placeholder': False,
    }


def _sanitize_highlight_item(item):
    if not isinstance(item, dict):
        return None

    if item.get('type') not in HIGHLIGHT_ALLOWED_TYPES:
        return None

    if item.get('target_kind') not in HIGHLIGHT_ALLOWED_TARGET_KINDS:
        return None

    if item.get('origin') not in HIGHLIGHT_ALLOWED_ORIGINS:
        return None

    sanitized = {}
    for key in HIGHLIGHT_ITEM_REQUIRED_KEYS:
        value = item.get(key)
        if key in ('evidence', 'safe_actions_available'):
            if not isinstance(value, list):
                return None
            sanitized[key] = [
                evidence_item
                for evidence_item in value
                if _latest_frame_metadata_value_is_json_safe(evidence_item)
                and not _latest_frame_value_is_unsafe(evidence_item)
            ]
            continue

        if key == 'is_placeholder':
            sanitized[key] = bool(value)
            continue

        if not _latest_frame_metadata_value_is_json_safe(value) or _latest_frame_value_is_unsafe(value):
            return None

        sanitized[key] = value

    return sanitized


def _sanitize_source_trust_source(source):
    if not isinstance(source, dict):
        return None

    source_type = source.get('source_type')
    if source_type not in NOW_SOURCE_TRUST_TYPES:
        return None

    allowed_keys = frozenset((
        'source_type',
        'source_label',
        'timestamp',
        'id',
        'camera_id',
        'day_date',
        'night',
        'uploaded',
        'exposure',
        'gain',
        'binmode',
        'file_size',
        'width',
        'height',
    ))

    sanitized = {}
    for key in sorted(allowed_keys):
        if key not in source:
            continue

        value = _latest_generated_output_json_value(source.get(key))
        if _latest_frame_metadata_value_is_json_safe(value) and not _latest_frame_value_is_unsafe(value):
            sanitized[key] = value

    sanitized['source_type'] = source_type
    sanitized.setdefault('source_label', 'Source metadata')
    sanitized.setdefault('timestamp', 'Not evaluated yet')

    return sanitized


def _safe_number(value):
    if isinstance(value, bool):
        return None

    if isinstance(value, (int, float)):
        return value

    return None


def _latest_generated_output_json_value(value):
    if value in (None, ''):
        return None

    if hasattr(value, 'strftime'):
        return value.strftime('%Y-%m-%d')

    return _latest_frame_json_value(value)


def _latest_generated_output_text(value, fallback):
    text = _latest_frame_text(value, fallback)
    if _latest_frame_value_is_unsafe(text):
        return fallback

    return text


def _source_trust_text(value, fallback):
    text = _latest_frame_text(value, fallback)
    if _latest_frame_value_is_unsafe(text):
        return fallback

    return text


def _latest_generated_output_sort_key(value, timestamp):
    if value in (None, ''):
        return ''

    if hasattr(value, 'strftime'):
        return value.strftime('%Y-%m-%d %H:%M:%S')

    if isinstance(timestamp, str) and timestamp != 'Not evaluated yet':
        return timestamp

    return ''


def _latest_frame_json_value(value):
    if value in (None, ''):
        return None

    if isinstance(value, (str, int, float, bool)):
        return value

    return None


def _latest_frame_metadata_value_is_json_safe(value):
    return value is None or isinstance(value, (str, int, float, bool))


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
    try:
        value_text = json.dumps(value, sort_keys=True).lower()
    except TypeError:
        return True

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
        _validate_latest_frame_metadata(summary.get('frame_metadata'))
        return

    if not isinstance(safe_preview_url, str):
        raise ValueError('latest_frame_summary.safe_preview_url must be null or string metadata')

    safe_preview_url_lower = safe_preview_url.lower()
    if safe_preview_url.startswith('/') or safe_preview_url.startswith('~'):
        raise ValueError('latest_frame_summary.safe_preview_url cannot be an absolute path')

    if any(token in safe_preview_url_lower for token in NOW_SUSPICIOUS_URL_TOKENS):
        raise ValueError('latest_frame_summary.safe_preview_url contains unsafe path metadata')

    _validate_latest_frame_metadata(summary.get('frame_metadata'))


def _validate_latest_camera_frames(summary):
    if not isinstance(summary, dict):
        raise ValueError('latest_camera_frames must be a dict')

    missing_keys = sorted(NOW_LATEST_CAMERA_FRAMES_REQUIRED_KEYS.difference(summary.keys()))
    if missing_keys:
        raise ValueError('latest_camera_frames missing required keys: {0:s}'.format(', '.join(missing_keys)))

    if summary['data_status'] not in NOW_ALLOWED_DATA_STATUSES:
        raise ValueError('Invalid data_status at now.latest_camera_frames: {0!r}'.format(summary['data_status']))

    if not isinstance(summary.get('is_placeholder'), bool):
        raise ValueError('latest_camera_frames.is_placeholder must be a boolean')

    items = summary.get('items')
    if not isinstance(items, list):
        raise ValueError('latest_camera_frames.items must be a list')

    if len(items) > 2:
        raise ValueError('latest_camera_frames.items must contain at most two camera frame entries')

    for index, item in enumerate(items):
        if not isinstance(item, dict):
            raise ValueError('latest_camera_frames.items[{0:d}] must be a dict'.format(index))

        missing_item_keys = sorted(NOW_LATEST_CAMERA_FRAME_ITEM_KEYS.difference(item.keys()))
        if missing_item_keys:
            raise ValueError(
                'latest_camera_frames.items[{0:d}] missing required keys: {1:s}'.format(
                    index,
                    ', '.join(missing_item_keys),
                )
            )

        if not isinstance(item.get('image_available'), bool):
            raise ValueError('latest_camera_frames.items[{0:d}].image_available must be boolean'.format(index))

        safe_image_url = item.get('safe_image_url')
        if safe_image_url is not None and not _safe_product_image_url(safe_image_url):
            raise ValueError('latest_camera_frames.items[{0:d}].safe_image_url is not a safe image route'.format(index))

        for key, value in item.items():
            if key == 'safe_image_url':
                continue

            if not _latest_frame_metadata_value_is_json_safe(value):
                raise ValueError(
                    'latest_camera_frames.items[{0:d}] contains non-primitive value: {1:s}'.format(
                        index,
                        str(key),
                    )
                )

            if _latest_frame_value_is_unsafe(value):
                raise ValueError(
                    'latest_camera_frames.items[{0:d}] contains unsafe value: {1:s}'.format(
                        index,
                        str(key),
                    )
                )


def _validate_latest_frame_metadata(frame_metadata):
    if not isinstance(frame_metadata, dict):
        raise ValueError('latest_frame_summary.frame_metadata must be a dict')

    unsupported_keys = set(frame_metadata.keys()).difference(NOW_LATEST_FRAME_METADATA_KEYS)
    if unsupported_keys:
        raise ValueError(
            'latest_frame_summary.frame_metadata contains unsupported keys: {0:s}'.format(
                ', '.join(sorted(unsupported_keys))
            )
        )

    for key, value in frame_metadata.items():
        if not _latest_frame_metadata_value_is_json_safe(value):
            raise ValueError('latest_frame_summary.frame_metadata contains non-primitive value: {0:s}'.format(str(key)))

        if _latest_frame_value_is_unsafe(value):
            raise ValueError('latest_frame_summary.frame_metadata contains unsafe value: {0:s}'.format(str(key)))


def _validate_latest_generated_output_summary(summary):
    if not isinstance(summary, dict):
        raise ValueError('latest_generated_output_summary must be a dict')

    missing_keys = sorted(NOW_LATEST_GENERATED_OUTPUT_REQUIRED_KEYS.difference(summary.keys()))
    if missing_keys:
        raise ValueError('latest_generated_output_summary missing required keys: {0:s}'.format(', '.join(missing_keys)))

    if summary['data_status'] not in NOW_ALLOWED_DATA_STATUSES:
        raise ValueError(
            'Invalid data_status at now.latest_generated_output_summary: {0!r}'.format(summary['data_status'])
        )

    for key, value in summary.items():
        if key == 'is_placeholder':
            if not isinstance(value, bool):
                raise ValueError('latest_generated_output_summary.is_placeholder must be a boolean')
            continue

        if key == 'data_status':
            continue

        if not _latest_frame_metadata_value_is_json_safe(value):
            raise ValueError('latest_generated_output_summary contains non-primitive value: {0:s}'.format(str(key)))

        if _latest_frame_value_is_unsafe(value):
            raise ValueError('latest_generated_output_summary contains unsafe value: {0:s}'.format(str(key)))


def _validate_current_capture_summary(summary):
    if not isinstance(summary, dict):
        raise ValueError('current_capture_summary must be a dict')

    missing_keys = sorted(NOW_CURRENT_CAPTURE_REQUIRED_KEYS.difference(summary.keys()))
    if missing_keys:
        raise ValueError('current_capture_summary missing required keys: {0:s}'.format(', '.join(missing_keys)))

    if summary['data_status'] not in NOW_ALLOWED_DATA_STATUSES:
        raise ValueError('Invalid data_status at now.current_capture_summary: {0!r}'.format(summary['data_status']))

    if summary['capture_state'] not in NOW_ALLOWED_CAPTURE_STATES:
        raise ValueError('Invalid capture_state at now.current_capture_summary: {0!r}'.format(summary['capture_state']))

    if summary['phase'] not in NOW_ALLOWED_PHASES:
        raise ValueError('Invalid phase at now.current_capture_summary: {0!r}'.format(summary['phase']))

    if not isinstance(summary['is_acquiring'], bool):
        raise ValueError('current_capture_summary.is_acquiring must be a boolean')

    if not isinstance(summary['is_placeholder'], bool):
        raise ValueError('current_capture_summary.is_placeholder must be a boolean')

    for key, value in summary.items():
        if key in ('is_acquiring', 'is_placeholder'):
            continue

        if not _latest_frame_metadata_value_is_json_safe(value):
            raise ValueError('current_capture_summary contains non-primitive value: {0:s}'.format(str(key)))

        if _latest_frame_value_is_unsafe(value):
            raise ValueError('current_capture_summary contains unsafe value: {0:s}'.format(str(key)))


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

    if summary['cycle_status'] not in SKY_CYCLE_ALLOWED_STATUSES:
        raise ValueError('Invalid cycle_status at sky_cycle.cycle_summary: {0!r}'.format(summary['cycle_status']))

    if summary['current_phase'] not in NOW_ALLOWED_PHASES and summary['current_phase'] != 'Not evaluated yet':
        raise ValueError('Invalid current_phase at sky_cycle.cycle_summary: {0!r}'.format(summary['current_phase']))

    if not isinstance(summary['evidence'], list):
        raise ValueError('cycle_summary.evidence must be a list')

    for key, value in summary.items():
        if key == 'evidence':
            for evidence_item in value:
                if not _latest_frame_metadata_value_is_json_safe(evidence_item) or _latest_frame_value_is_unsafe(evidence_item):
                    raise ValueError('cycle_summary.evidence contains unsafe value')
            continue

        if key == 'is_placeholder':
            if not isinstance(value, bool):
                raise ValueError('cycle_summary.is_placeholder must be a boolean')
            continue

        if not _latest_frame_metadata_value_is_json_safe(value):
            raise ValueError('cycle_summary contains non-primitive value: {0:s}'.format(str(key)))

        if _latest_frame_value_is_unsafe(value):
            raise ValueError('cycle_summary contains unsafe value: {0:s}'.format(str(key)))


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

        if phase['phase'] not in SKY_CYCLE_ALLOWED_PHASES:
            raise ValueError('Invalid phase at sky_cycle.phase_timeline[{0:d}]: {1!r}'.format(index, phase['phase']))

        if phase['data_status'] not in NOW_ALLOWED_DATA_STATUSES:
            raise ValueError('Invalid data_status at sky_cycle.phase_timeline[{0:d}]: {1!r}'.format(index, phase['data_status']))

        if not isinstance(phase['supported'], bool):
            raise ValueError('phase_timeline[{0:d}].supported must be a boolean'.format(index))


def _validate_sky_cycle_moments_summary(summary):
    if not isinstance(summary, dict):
        raise ValueError('moments_summary must be a dict')

    missing_keys = sorted(SKY_CYCLE_MOMENTS_REQUIRED_KEYS.difference(summary.keys()))
    if missing_keys:
        raise ValueError('moments_summary missing required keys: {0:s}'.format(', '.join(missing_keys)))

    if summary['data_status'] not in NOW_ALLOWED_DATA_STATUSES:
        raise ValueError('Invalid data_status at sky_cycle.moments_summary: {0!r}'.format(summary['data_status']))

    if not isinstance(summary['moment_categories'], list):
        raise ValueError('moments_summary.moment_categories must be a list')

    if not isinstance(summary['items'], list):
        raise ValueError('moments_summary.items must be a list')

    for index, item in enumerate(summary['items']):
        if not isinstance(item, dict):
            raise ValueError('moments_summary.items[{0:d}] must be a dict'.format(index))

        missing_item_keys = sorted(SKY_CYCLE_MOMENT_ITEM_REQUIRED_KEYS.difference(item.keys()))
        if missing_item_keys:
            raise ValueError('moments_summary.items[{0:d}] missing required keys: {1:s}'.format(index, ', '.join(missing_item_keys)))

        if item['type'] not in SKY_CYCLE_ALLOWED_MOMENT_TYPES:
            raise ValueError('Invalid moment type at sky_cycle.moments_summary.items[{0:d}]: {1!r}'.format(index, item['type']))

        if item['phase'] not in SKY_CYCLE_ALLOWED_PHASES:
            raise ValueError('Invalid moment phase at sky_cycle.moments_summary.items[{0:d}]: {1!r}'.format(index, item['phase']))

        if item['data_status'] not in NOW_ALLOWED_DATA_STATUSES:
            raise ValueError('Invalid data_status at sky_cycle.moments_summary.items[{0:d}]: {1!r}'.format(index, item['data_status']))

        if not isinstance(item['evidence'], list):
            raise ValueError('moments_summary.items[{0:d}].evidence must be a list'.format(index))


def _validate_sky_cycle_outputs_summary(summary):
    if not isinstance(summary, dict):
        raise ValueError('outputs_summary must be a dict')

    missing_keys = sorted(SKY_CYCLE_OUTPUTS_REQUIRED_KEYS.difference(summary.keys()))
    if missing_keys:
        raise ValueError('outputs_summary missing required keys: {0:s}'.format(', '.join(missing_keys)))

    if summary['data_status'] not in NOW_ALLOWED_DATA_STATUSES:
        raise ValueError('Invalid data_status at sky_cycle.outputs_summary: {0!r}'.format(summary['data_status']))

    if not isinstance(summary['items'], list):
        raise ValueError('outputs_summary.items must be a list')

    for index, item in enumerate(summary['items']):
        if not isinstance(item, dict):
            raise ValueError('outputs_summary.items[{0:d}] must be a dict'.format(index))

        missing_item_keys = sorted(SKY_CYCLE_OUTPUT_ITEM_REQUIRED_KEYS.difference(item.keys()))
        if missing_item_keys:
            raise ValueError('outputs_summary.items[{0:d}] missing required keys: {1:s}'.format(index, ', '.join(missing_item_keys)))

        if item['type'] not in SKY_CYCLE_ALLOWED_OUTPUT_TYPES:
            raise ValueError('Invalid output type at sky_cycle.outputs_summary.items[{0:d}]: {1!r}'.format(index, item['type']))

        if item['phase'] not in SKY_CYCLE_ALLOWED_PHASES:
            raise ValueError('Invalid output phase at sky_cycle.outputs_summary.items[{0:d}]: {1!r}'.format(index, item['phase']))

        if item['data_status'] not in NOW_ALLOWED_DATA_STATUSES:
            raise ValueError('Invalid data_status at sky_cycle.outputs_summary.items[{0:d}]: {1!r}'.format(index, item['data_status']))

        if not isinstance(item['safe_actions_available'], list):
            raise ValueError('outputs_summary.items[{0:d}].safe_actions_available must be a list'.format(index))

        _validate_safe_actions({'safe_actions_available': item['safe_actions_available']})


def _validate_sky_cycle_observatory_health_summary(summary):
    if not isinstance(summary, dict):
        raise ValueError('observatory_health_summary must be a dict')

    missing_keys = sorted(SKY_CYCLE_HEALTH_REQUIRED_KEYS.difference(summary.keys()))
    if missing_keys:
        raise ValueError('observatory_health_summary missing required keys: {0:s}'.format(', '.join(missing_keys)))

    if summary['data_status'] not in NOW_ALLOWED_DATA_STATUSES:
        raise ValueError('Invalid data_status at sky_cycle.observatory_health_summary: {0!r}'.format(summary['data_status']))

    if summary['risk_level'] not in NOW_ALLOWED_RISK_LEVELS:
        raise ValueError('Invalid risk_level at sky_cycle.observatory_health_summary: {0!r}'.format(summary['risk_level']))

    if not isinstance(summary['evidence'], list):
        raise ValueError('observatory_health_summary.evidence must be a list')


def _validate_highlights_summary(summary):
    if not isinstance(summary, dict):
        raise ValueError('highlights_summary must be a dict')

    missing_keys = sorted(HIGHLIGHTS_SUMMARY_REQUIRED_KEYS.difference(summary.keys()))
    if missing_keys:
        raise ValueError('highlights_summary missing required keys: {0:s}'.format(', '.join(missing_keys)))

    if summary['data_status'] not in NOW_ALLOWED_DATA_STATUSES:
        raise ValueError('Invalid data_status at highlights.highlights_summary: {0!r}'.format(summary['data_status']))


def _validate_highlight_items(items):
    if not isinstance(items, list):
        raise ValueError('highlight_items must be a list')

    for index, item in enumerate(items):
        if not isinstance(item, dict):
            raise ValueError('highlight_items[{0:d}] must be a dict'.format(index))

        missing_keys = sorted(HIGHLIGHT_ITEM_REQUIRED_KEYS.difference(item.keys()))
        if missing_keys:
            raise ValueError('highlight_items[{0:d}] missing required keys: {1:s}'.format(index, ', '.join(missing_keys)))

        if item['type'] not in HIGHLIGHT_ALLOWED_TYPES:
            raise ValueError('Invalid Highlight type at highlights.highlight_items[{0:d}]: {1!r}'.format(index, item['type']))

        if item['target_kind'] not in HIGHLIGHT_ALLOWED_TARGET_KINDS:
            raise ValueError('Invalid Highlight target_kind at highlights.highlight_items[{0:d}]: {1!r}'.format(index, item['target_kind']))

        if item['origin'] not in HIGHLIGHT_ALLOWED_ORIGINS:
            raise ValueError('Invalid Highlight origin at highlights.highlight_items[{0:d}]: {1!r}'.format(index, item['origin']))

        if item['data_status'] not in NOW_ALLOWED_DATA_STATUSES:
            raise ValueError('Invalid data_status at highlights.highlight_items[{0:d}]: {1!r}'.format(index, item['data_status']))

        if not isinstance(item['evidence'], list):
            raise ValueError('highlight_items[{0:d}].evidence must be a list'.format(index))

        if not isinstance(item['safe_actions_available'], list):
            raise ValueError('highlight_items[{0:d}].safe_actions_available must be a list'.format(index))

        _validate_safe_actions({'safe_actions_available': item['safe_actions_available']})


def _validate_highlights_source_trust_summary(summary):
    if not isinstance(summary, dict):
        raise ValueError('source_trust_summary must be a dict')

    missing_keys = sorted(HIGHLIGHTS_SOURCE_TRUST_REQUIRED_KEYS.difference(summary.keys()))
    if missing_keys:
        raise ValueError('source_trust_summary missing required keys: {0:s}'.format(', '.join(missing_keys)))

    if summary['data_status'] not in NOW_ALLOWED_DATA_STATUSES:
        raise ValueError('Invalid data_status at highlights.source_trust_summary: {0!r}'.format(summary['data_status']))

    if summary['risk_level'] not in NOW_ALLOWED_RISK_LEVELS:
        raise ValueError('Invalid risk_level at highlights.source_trust_summary: {0!r}'.format(summary['risk_level']))

    if not isinstance(summary['evidence'], list):
        raise ValueError('source_trust_summary.evidence must be a list')


def _validate_highlights_review_queue_summary(summary):
    if not isinstance(summary, dict):
        raise ValueError('review_queue_summary must be a dict')

    missing_keys = sorted(HIGHLIGHTS_REVIEW_QUEUE_REQUIRED_KEYS.difference(summary.keys()))
    if missing_keys:
        raise ValueError('review_queue_summary missing required keys: {0:s}'.format(', '.join(missing_keys)))

    if summary['data_status'] not in NOW_ALLOWED_DATA_STATUSES:
        raise ValueError('Invalid data_status at highlights.review_queue_summary: {0!r}'.format(summary['data_status']))


def _validate_highlights_selection_policy_summary(summary):
    if not isinstance(summary, dict):
        raise ValueError('selection_policy_summary must be a dict')

    missing_keys = sorted(HIGHLIGHTS_SELECTION_POLICY_REQUIRED_KEYS.difference(summary.keys()))
    if missing_keys:
        raise ValueError('selection_policy_summary missing required keys: {0:s}'.format(', '.join(missing_keys)))

    if summary['data_status'] not in NOW_ALLOWED_DATA_STATUSES:
        raise ValueError('Invalid data_status at highlights.selection_policy_summary: {0!r}'.format(summary['data_status']))

    if not isinstance(summary['allowed_origins'], list):
        raise ValueError('selection_policy_summary.allowed_origins must be a list')

    invalid_origins = sorted(set(summary['allowed_origins']).difference(HIGHLIGHT_ALLOWED_ORIGINS))
    if invalid_origins:
        raise ValueError('Invalid Highlight origins at highlights.selection_policy_summary: {0:s}'.format(', '.join(invalid_origins)))


def _validate_moment_detail_summary(summary):
    if not isinstance(summary, dict):
        raise ValueError('moment_summary must be a dict')

    missing_keys = sorted(MOMENT_DETAIL_SUMMARY_REQUIRED_KEYS.difference(summary.keys()))
    if missing_keys:
        raise ValueError('moment_summary missing required keys: {0:s}'.format(', '.join(missing_keys)))

    if summary['type'] not in MOMENT_DETAIL_ALLOWED_TYPES:
        raise ValueError('Invalid Moment type at moment_detail.moment_summary: {0!r}'.format(summary['type']))

    if summary['phase'] not in SKY_CYCLE_ALLOWED_PHASES:
        raise ValueError('Invalid Moment phase at moment_detail.moment_summary: {0!r}'.format(summary['phase']))

    if summary['data_status'] not in NOW_ALLOWED_DATA_STATUSES:
        raise ValueError('Invalid data_status at moment_detail.moment_summary: {0!r}'.format(summary['data_status']))


def _validate_moment_detail_evidence_summary(summary):
    if not isinstance(summary, dict):
        raise ValueError('evidence_summary must be a dict')

    missing_keys = sorted(MOMENT_DETAIL_EVIDENCE_REQUIRED_KEYS.difference(summary.keys()))
    if missing_keys:
        raise ValueError('evidence_summary missing required keys: {0:s}'.format(', '.join(missing_keys)))

    if summary['data_status'] not in NOW_ALLOWED_DATA_STATUSES:
        raise ValueError('Invalid data_status at moment_detail.evidence_summary: {0!r}'.format(summary['data_status']))

    if not isinstance(summary['evidence'], list):
        raise ValueError('evidence_summary.evidence must be a list')


def _validate_moment_detail_source_trust_summary(summary):
    if not isinstance(summary, dict):
        raise ValueError('source_trust_summary must be a dict')

    missing_keys = sorted(MOMENT_DETAIL_SOURCE_TRUST_REQUIRED_KEYS.difference(summary.keys()))
    if missing_keys:
        raise ValueError('source_trust_summary missing required keys: {0:s}'.format(', '.join(missing_keys)))

    if summary['data_status'] not in NOW_ALLOWED_DATA_STATUSES:
        raise ValueError('Invalid data_status at moment_detail.source_trust_summary: {0!r}'.format(summary['data_status']))


def _validate_moment_detail_related_outputs(summary):
    if not isinstance(summary, dict):
        raise ValueError('related_outputs must be a dict')

    missing_keys = sorted(MOMENT_DETAIL_RELATED_OUTPUTS_REQUIRED_KEYS.difference(summary.keys()))
    if missing_keys:
        raise ValueError('related_outputs missing required keys: {0:s}'.format(', '.join(missing_keys)))

    if summary['data_status'] not in NOW_ALLOWED_DATA_STATUSES:
        raise ValueError('Invalid data_status at moment_detail.related_outputs: {0!r}'.format(summary['data_status']))

    if not isinstance(summary['outputs'], list):
        raise ValueError('related_outputs.outputs must be a list')

    for index, output in enumerate(summary['outputs']):
        if not isinstance(output, dict):
            raise ValueError('related_outputs.outputs[{0:d}] must be a dict'.format(index))

        missing_output_keys = sorted(MOMENT_DETAIL_OUTPUT_REQUIRED_KEYS.difference(output.keys()))
        if missing_output_keys:
            raise ValueError('related_outputs.outputs[{0:d}] missing required keys: {1:s}'.format(index, ', '.join(missing_output_keys)))

        if output['type'] not in MOMENT_DETAIL_ALLOWED_OUTPUT_TYPES:
            raise ValueError('Invalid related output type at moment_detail.related_outputs.outputs[{0:d}]: {1!r}'.format(index, output['type']))

        if output['data_status'] not in NOW_ALLOWED_DATA_STATUSES:
            raise ValueError('Invalid data_status at moment_detail.related_outputs.outputs[{0:d}]: {1!r}'.format(index, output['data_status']))


def _validate_moment_detail_sky_cycle_context(summary):
    if not isinstance(summary, dict):
        raise ValueError('sky_cycle_context must be a dict')

    missing_keys = sorted(MOMENT_DETAIL_SKY_CYCLE_REQUIRED_KEYS.difference(summary.keys()))
    if missing_keys:
        raise ValueError('sky_cycle_context missing required keys: {0:s}'.format(', '.join(missing_keys)))

    if summary['phase'] not in SKY_CYCLE_ALLOWED_PHASES:
        raise ValueError('Invalid phase at moment_detail.sky_cycle_context: {0!r}'.format(summary['phase']))

    if summary['data_status'] not in NOW_ALLOWED_DATA_STATUSES:
        raise ValueError('Invalid data_status at moment_detail.sky_cycle_context: {0!r}'.format(summary['data_status']))


def _validate_moment_detail_observatory_context(summary):
    if not isinstance(summary, dict):
        raise ValueError('observatory_context must be a dict')

    missing_keys = sorted(MOMENT_DETAIL_OBSERVATORY_REQUIRED_KEYS.difference(summary.keys()))
    if missing_keys:
        raise ValueError('observatory_context missing required keys: {0:s}'.format(', '.join(missing_keys)))

    if summary['data_status'] not in NOW_ALLOWED_DATA_STATUSES:
        raise ValueError('Invalid data_status at moment_detail.observatory_context: {0!r}'.format(summary['data_status']))


def _validate_output_detail_summary(summary):
    if not isinstance(summary, dict):
        raise ValueError('output_summary must be a dict')

    missing_keys = sorted(OUTPUT_DETAIL_SUMMARY_REQUIRED_KEYS.difference(summary.keys()))
    if missing_keys:
        raise ValueError('output_summary missing required keys: {0:s}'.format(', '.join(missing_keys)))

    if summary['type'] not in OUTPUT_DETAIL_ALLOWED_TYPES:
        raise ValueError('Invalid output type at output_detail.output_summary: {0!r}'.format(summary['type']))

    if summary['phase'] not in SKY_CYCLE_ALLOWED_PHASES:
        raise ValueError('Invalid output phase at output_detail.output_summary: {0!r}'.format(summary['phase']))

    if summary['data_status'] not in NOW_ALLOWED_DATA_STATUSES:
        raise ValueError('Invalid data_status at output_detail.output_summary: {0!r}'.format(summary['data_status']))


def _validate_output_detail_preview_summary(summary):
    if not isinstance(summary, dict):
        raise ValueError('preview_summary must be a dict')

    missing_keys = sorted(OUTPUT_DETAIL_PREVIEW_REQUIRED_KEYS.difference(summary.keys()))
    if missing_keys:
        raise ValueError('preview_summary missing required keys: {0:s}'.format(', '.join(missing_keys)))

    if summary['data_status'] not in NOW_ALLOWED_DATA_STATUSES:
        raise ValueError('Invalid data_status at output_detail.preview_summary: {0!r}'.format(summary['data_status']))

    if not isinstance(summary['preview_available'], bool):
        raise ValueError('preview_summary.preview_available must be a boolean')

    safe_preview_url = summary.get('safe_preview_url')
    if safe_preview_url is None:
        return

    if not isinstance(safe_preview_url, str):
        raise ValueError('preview_summary.safe_preview_url must be null or string metadata')

    safe_preview_url_lower = safe_preview_url.lower()
    if safe_preview_url.startswith('/') or safe_preview_url.startswith('~'):
        raise ValueError('preview_summary.safe_preview_url cannot be an absolute path')

    if any(token in safe_preview_url_lower for token in NOW_SUSPICIOUS_URL_TOKENS):
        raise ValueError('preview_summary.safe_preview_url contains unsafe path metadata')


def _validate_output_detail_recipe_summary(summary):
    if not isinstance(summary, dict):
        raise ValueError('recipe_summary must be a dict')

    missing_keys = sorted(OUTPUT_DETAIL_RECIPE_REQUIRED_KEYS.difference(summary.keys()))
    if missing_keys:
        raise ValueError('recipe_summary missing required keys: {0:s}'.format(', '.join(missing_keys)))

    if summary['data_status'] not in NOW_ALLOWED_DATA_STATUSES:
        raise ValueError('Invalid data_status at output_detail.recipe_summary: {0!r}'.format(summary['data_status']))


def _validate_output_detail_source_lineage_summary(summary):
    if not isinstance(summary, dict):
        raise ValueError('source_lineage_summary must be a dict')

    missing_keys = sorted(OUTPUT_DETAIL_SOURCE_LINEAGE_REQUIRED_KEYS.difference(summary.keys()))
    if missing_keys:
        raise ValueError('source_lineage_summary missing required keys: {0:s}'.format(', '.join(missing_keys)))

    if summary['data_status'] not in NOW_ALLOWED_DATA_STATUSES:
        raise ValueError('Invalid data_status at output_detail.source_lineage_summary: {0!r}'.format(summary['data_status']))

    if summary['trust_level'] not in OUTPUT_DETAIL_ALLOWED_TRUST_LEVELS:
        raise ValueError('Invalid trust_level at output_detail.source_lineage_summary: {0!r}'.format(summary['trust_level']))

    if not isinstance(summary['source_types'], list):
        raise ValueError('source_lineage_summary.source_types must be a list')

    if not isinstance(summary['evidence'], list):
        raise ValueError('source_lineage_summary.evidence must be a list')


def _validate_output_detail_related_moments(summary):
    if not isinstance(summary, dict):
        raise ValueError('related_moments must be a dict')

    missing_keys = sorted(OUTPUT_DETAIL_RELATED_MOMENTS_REQUIRED_KEYS.difference(summary.keys()))
    if missing_keys:
        raise ValueError('related_moments missing required keys: {0:s}'.format(', '.join(missing_keys)))

    if summary['data_status'] not in NOW_ALLOWED_DATA_STATUSES:
        raise ValueError('Invalid data_status at output_detail.related_moments: {0!r}'.format(summary['data_status']))

    if not isinstance(summary['items'], list):
        raise ValueError('related_moments.items must be a list')

    for index, item in enumerate(summary['items']):
        if not isinstance(item, dict):
            raise ValueError('related_moments.items[{0:d}] must be a dict'.format(index))

        missing_item_keys = sorted(OUTPUT_DETAIL_RELATED_MOMENT_REQUIRED_KEYS.difference(item.keys()))
        if missing_item_keys:
            raise ValueError('related_moments.items[{0:d}] missing required keys: {1:s}'.format(index, ', '.join(missing_item_keys)))

        if item['type'] not in MOMENT_DETAIL_ALLOWED_TYPES:
            raise ValueError('Invalid related moment type at output_detail.related_moments.items[{0:d}]: {1!r}'.format(index, item['type']))

        if item['phase'] not in SKY_CYCLE_ALLOWED_PHASES:
            raise ValueError('Invalid related moment phase at output_detail.related_moments.items[{0:d}]: {1!r}'.format(index, item['phase']))

        if item['data_status'] not in NOW_ALLOWED_DATA_STATUSES:
            raise ValueError('Invalid data_status at output_detail.related_moments.items[{0:d}]: {1!r}'.format(index, item['data_status']))


def _validate_output_detail_sky_cycle_context(summary):
    if not isinstance(summary, dict):
        raise ValueError('sky_cycle_context must be a dict')

    missing_keys = sorted(OUTPUT_DETAIL_SKY_CYCLE_REQUIRED_KEYS.difference(summary.keys()))
    if missing_keys:
        raise ValueError('sky_cycle_context missing required keys: {0:s}'.format(', '.join(missing_keys)))

    if summary['phase'] not in SKY_CYCLE_ALLOWED_PHASES:
        raise ValueError('Invalid phase at output_detail.sky_cycle_context: {0!r}'.format(summary['phase']))

    if summary['data_status'] not in NOW_ALLOWED_DATA_STATUSES:
        raise ValueError('Invalid data_status at output_detail.sky_cycle_context: {0!r}'.format(summary['data_status']))


def _validate_output_detail_share_readiness_summary(summary):
    if not isinstance(summary, dict):
        raise ValueError('share_readiness_summary must be a dict')

    missing_keys = sorted(OUTPUT_DETAIL_SHARE_READINESS_REQUIRED_KEYS.difference(summary.keys()))
    if missing_keys:
        raise ValueError('share_readiness_summary missing required keys: {0:s}'.format(', '.join(missing_keys)))

    if summary['data_status'] not in NOW_ALLOWED_DATA_STATUSES:
        raise ValueError('Invalid data_status at output_detail.share_readiness_summary: {0!r}'.format(summary['data_status']))

    if not isinstance(summary['limitations'], list):
        raise ValueError('share_readiness_summary.limitations must be a list')

    if not isinstance(summary['safe_actions_available'], list):
        raise ValueError('share_readiness_summary.safe_actions_available must be a list')

    _validate_safe_actions({'safe_actions_available': summary['safe_actions_available']})


def _validate_library_summary(summary):
    if not isinstance(summary, dict):
        raise ValueError('library_summary must be a dict')

    missing_keys = sorted(LIBRARY_SUMMARY_REQUIRED_KEYS.difference(summary.keys()))
    if missing_keys:
        raise ValueError('library_summary missing required keys: {0:s}'.format(', '.join(missing_keys)))

    if summary['data_status'] not in NOW_ALLOWED_DATA_STATUSES:
        raise ValueError('Invalid data_status at library.library_summary: {0!r}'.format(summary['data_status']))


def _validate_library_collection_summary(summary):
    if not isinstance(summary, dict):
        raise ValueError('collection_summary must be a dict')

    missing_keys = sorted(LIBRARY_COLLECTION_SUMMARY_REQUIRED_KEYS.difference(summary.keys()))
    if missing_keys:
        raise ValueError('collection_summary missing required keys: {0:s}'.format(', '.join(missing_keys)))

    if summary['data_status'] not in NOW_ALLOWED_DATA_STATUSES:
        raise ValueError('Invalid data_status at library.collection_summary: {0!r}'.format(summary['data_status']))

    if not isinstance(summary['collections'], list):
        raise ValueError('collection_summary.collections must be a list')

    for index, collection in enumerate(summary['collections']):
        if not isinstance(collection, dict):
            raise ValueError('collection_summary.collections[{0:d}] must be a dict'.format(index))

        missing_collection_keys = sorted(LIBRARY_COLLECTION_REQUIRED_KEYS.difference(collection.keys()))
        if missing_collection_keys:
            raise ValueError('collection_summary.collections[{0:d}] missing required keys: {1:s}'.format(index, ', '.join(missing_collection_keys)))

        if collection['type'] not in LIBRARY_ALLOWED_COLLECTION_TYPES:
            raise ValueError('Invalid collection type at library.collection_summary.collections[{0:d}]: {1!r}'.format(index, collection['type']))

        if collection['data_status'] not in NOW_ALLOWED_DATA_STATUSES:
            raise ValueError('Invalid data_status at library.collection_summary.collections[{0:d}]: {1!r}'.format(index, collection['data_status']))


def _validate_library_search_summary(summary):
    if not isinstance(summary, dict):
        raise ValueError('search_summary must be a dict')

    missing_keys = sorted(LIBRARY_SEARCH_SUMMARY_REQUIRED_KEYS.difference(summary.keys()))
    if missing_keys:
        raise ValueError('search_summary missing required keys: {0:s}'.format(', '.join(missing_keys)))

    if summary['data_status'] not in NOW_ALLOWED_DATA_STATUSES:
        raise ValueError('Invalid data_status at library.search_summary: {0!r}'.format(summary['data_status']))

    if not isinstance(summary['indexed_fields'], list):
        raise ValueError('search_summary.indexed_fields must be a list')


def _validate_library_filter_summary(summary):
    if not isinstance(summary, dict):
        raise ValueError('filter_summary must be a dict')

    missing_keys = sorted(LIBRARY_FILTER_SUMMARY_REQUIRED_KEYS.difference(summary.keys()))
    if missing_keys:
        raise ValueError('filter_summary missing required keys: {0:s}'.format(', '.join(missing_keys)))

    if summary['data_status'] not in NOW_ALLOWED_DATA_STATUSES:
        raise ValueError('Invalid data_status at library.filter_summary: {0!r}'.format(summary['data_status']))

    if not isinstance(summary['available_filters'], list):
        raise ValueError('filter_summary.available_filters must be a list')

    if not isinstance(summary['disabled_filters'], list):
        raise ValueError('filter_summary.disabled_filters must be a list')


def _validate_library_recent_items(summary):
    if not isinstance(summary, dict):
        raise ValueError('recent_items must be a dict')

    missing_keys = sorted(LIBRARY_RECENT_ITEMS_REQUIRED_KEYS.difference(summary.keys()))
    if missing_keys:
        raise ValueError('recent_items missing required keys: {0:s}'.format(', '.join(missing_keys)))

    if summary['data_status'] not in NOW_ALLOWED_DATA_STATUSES:
        raise ValueError('Invalid data_status at library.recent_items: {0!r}'.format(summary['data_status']))

    if not isinstance(summary['items'], list):
        raise ValueError('recent_items.items must be a list')

    for index, item in enumerate(summary['items']):
        if not isinstance(item, dict):
            raise ValueError('recent_items.items[{0:d}] must be a dict'.format(index))

        missing_item_keys = sorted(LIBRARY_RECENT_ITEM_REQUIRED_KEYS.difference(item.keys()))
        if missing_item_keys:
            raise ValueError('recent_items.items[{0:d}] missing required keys: {1:s}'.format(index, ', '.join(missing_item_keys)))

        if item['kind'] not in LIBRARY_ALLOWED_KINDS:
            raise ValueError('Invalid Library item kind at library.recent_items.items[{0:d}]: {1!r}'.format(index, item['kind']))

        if item['phase'] not in SKY_CYCLE_ALLOWED_PHASES:
            raise ValueError('Invalid Library item phase at library.recent_items.items[{0:d}]: {1!r}'.format(index, item['phase']))

        if item['data_status'] not in NOW_ALLOWED_DATA_STATUSES:
            raise ValueError('Invalid data_status at library.recent_items.items[{0:d}]: {1!r}'.format(index, item['data_status']))


def _validate_library_memory_model_summary(summary):
    if not isinstance(summary, dict):
        raise ValueError('memory_model_summary must be a dict')

    missing_keys = sorted(LIBRARY_MEMORY_MODEL_REQUIRED_KEYS.difference(summary.keys()))
    if missing_keys:
        raise ValueError('memory_model_summary missing required keys: {0:s}'.format(', '.join(missing_keys)))

    if summary['data_status'] not in NOW_ALLOWED_DATA_STATUSES:
        raise ValueError('Invalid data_status at library.memory_model_summary: {0!r}'.format(summary['data_status']))


def _validate_observatory_summary(summary):
    if not isinstance(summary, dict):
        raise ValueError('observatory_summary must be a dict')

    missing_keys = sorted(OBSERVATORY_SUMMARY_REQUIRED_KEYS.difference(summary.keys()))
    if missing_keys:
        raise ValueError('observatory_summary missing required keys: {0:s}'.format(', '.join(missing_keys)))

    _validate_observatory_status(summary['overall_status'], 'observatory.observatory_summary.overall_status')
    _validate_observatory_data_status(summary, 'observatory.observatory_summary')


def _validate_observatory_camera_system_summary(summary):
    if not isinstance(summary, dict):
        raise ValueError('camera_system_summary must be a dict')

    missing_keys = sorted(OBSERVATORY_CAMERA_SYSTEM_REQUIRED_KEYS.difference(summary.keys()))
    if missing_keys:
        raise ValueError('camera_system_summary missing required keys: {0:s}'.format(', '.join(missing_keys)))

    _validate_observatory_status(summary['status'], 'observatory.camera_system_summary.status')
    _validate_observatory_data_status(summary, 'observatory.camera_system_summary')


def _validate_observatory_capture_pipeline_summary(summary):
    if not isinstance(summary, dict):
        raise ValueError('capture_pipeline_summary must be a dict')

    missing_keys = sorted(OBSERVATORY_CAPTURE_PIPELINE_REQUIRED_KEYS.difference(summary.keys()))
    if missing_keys:
        raise ValueError('capture_pipeline_summary missing required keys: {0:s}'.format(', '.join(missing_keys)))

    _validate_observatory_status(summary['status'], 'observatory.capture_pipeline_summary.status')
    _validate_observatory_data_status(summary, 'observatory.capture_pipeline_summary')


def _validate_observatory_source_preservation_summary(summary):
    if not isinstance(summary, dict):
        raise ValueError('source_preservation_summary must be a dict')

    missing_keys = sorted(OBSERVATORY_SOURCE_PRESERVATION_REQUIRED_KEYS.difference(summary.keys()))
    if missing_keys:
        raise ValueError('source_preservation_summary missing required keys: {0:s}'.format(', '.join(missing_keys)))

    _validate_observatory_status(summary['status'], 'observatory.source_preservation_summary.status')
    _validate_observatory_data_status(summary, 'observatory.source_preservation_summary')
    _validate_observatory_risk(summary['trust_level'], 'observatory.source_preservation_summary.trust_level')


def _validate_observatory_storage_summary(summary):
    if not isinstance(summary, dict):
        raise ValueError('storage_summary must be a dict')

    missing_keys = sorted(OBSERVATORY_STORAGE_REQUIRED_KEYS.difference(summary.keys()))
    if missing_keys:
        raise ValueError('storage_summary missing required keys: {0:s}'.format(', '.join(missing_keys)))

    _validate_observatory_status(summary['status'], 'observatory.storage_summary.status')
    _validate_observatory_data_status(summary, 'observatory.storage_summary')
    _validate_observatory_risk(summary['risk_level'], 'observatory.storage_summary.risk_level')


def _validate_observatory_generation_summary(summary):
    if not isinstance(summary, dict):
        raise ValueError('generation_summary must be a dict')

    missing_keys = sorted(OBSERVATORY_GENERATION_REQUIRED_KEYS.difference(summary.keys()))
    if missing_keys:
        raise ValueError('generation_summary missing required keys: {0:s}'.format(', '.join(missing_keys)))

    _validate_observatory_status(summary['status'], 'observatory.generation_summary.status')
    _validate_observatory_data_status(summary, 'observatory.generation_summary')


def _validate_observatory_integration_summary(summary):
    if not isinstance(summary, dict):
        raise ValueError('integration_summary must be a dict')

    missing_keys = sorted(OBSERVATORY_INTEGRATION_REQUIRED_KEYS.difference(summary.keys()))
    if missing_keys:
        raise ValueError('integration_summary missing required keys: {0:s}'.format(', '.join(missing_keys)))

    _validate_observatory_status(summary['status'], 'observatory.integration_summary.status')
    _validate_observatory_data_status(summary, 'observatory.integration_summary')


def _validate_observatory_attention_items(summary):
    if not isinstance(summary, dict):
        raise ValueError('attention_items must be a dict')

    missing_keys = sorted(OBSERVATORY_ATTENTION_REQUIRED_KEYS.difference(summary.keys()))
    if missing_keys:
        raise ValueError('attention_items missing required keys: {0:s}'.format(', '.join(missing_keys)))

    _validate_observatory_data_status(summary, 'observatory.attention_items')

    if not isinstance(summary['items'], list):
        raise ValueError('attention_items.items must be a list')

    for index, item in enumerate(summary['items']):
        if not isinstance(item, dict):
            raise ValueError('attention_items.items[{0:d}] must be a dict'.format(index))

        missing_item_keys = sorted(OBSERVATORY_ATTENTION_ITEM_REQUIRED_KEYS.difference(item.keys()))
        if missing_item_keys:
            raise ValueError('attention_items.items[{0:d}] missing required keys: {1:s}'.format(index, ', '.join(missing_item_keys)))

        _validate_observatory_status(item['status'], 'observatory.attention_items.items[{0:d}].status'.format(index))
        _validate_observatory_data_status(item, 'observatory.attention_items.items[{0:d}]'.format(index))
        _validate_observatory_risk(item['risk_level'], 'observatory.attention_items.items[{0:d}].risk_level'.format(index))


def _validate_observatory_status(status, path):
    if status not in OBSERVATORY_ALLOWED_STATUSES:
        raise ValueError('Invalid Observatory status at {0:s}: {1!r}'.format(path, status))


def _validate_observatory_risk(risk_level, path):
    if risk_level not in OBSERVATORY_ALLOWED_RISK_LEVELS:
        raise ValueError('Invalid risk_level at {0:s}: {1!r}'.format(path, risk_level))


def _validate_observatory_data_status(summary, path):
    if summary['data_status'] not in NOW_ALLOWED_DATA_STATUSES:
        raise ValueError('Invalid data_status at {0:s}: {1!r}'.format(path, summary['data_status']))


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


def _validate_no_absolute_paths(payload, path='payload', key_name=None):
    if isinstance(payload, dict):
        for key, value in payload.items():
            _validate_no_absolute_paths(value, '{0:s}.{1:s}'.format(path, str(key)), key_name=str(key))
        return

    if isinstance(payload, list):
        for index, value in enumerate(payload):
            _validate_no_absolute_paths(value, '{0:s}[{1:d}]'.format(path, index), key_name=key_name)
        return

    if key_name in NOW_SAFE_WEB_ROUTE_KEYS:
        if payload is not None and not _safe_product_image_url(payload):
            raise ValueError('Unsafe web image route at {0:s}'.format(path))
        return

    if isinstance(payload, str):
        if NOW_ABSOLUTE_PATH_RE.search(payload) or NOW_WINDOWS_PATH_RE.search(payload):
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
