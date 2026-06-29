"""Product-domain view models for Hybrid AllSky.

This module is intentionally framework-free. It does not import Flask, query the
database, inspect the filesystem, or evaluate camera/runtime state.
"""


NOW_DATA_STATUS_PLACEHOLDER = 'placeholder'
NOW_DATA_STATUS_NOT_EVALUATED = 'not_evaluated'
NOW_DATA_STATUS_FUTURE_CONTRACT = 'future_backend_contract'


def build_now_view():
    """Return the first backend-owned NowView contract.

    The payload is static and fake-safe by design. It gives the Product UI a
    stable shape while real Now/SkyCycle/Moment/Output contracts are still being
    designed.
    """
    return {
        'id': 'now.placeholder',
        'label': 'Now',
        'status': 'Read-only product prototype',
        'data_status': NOW_DATA_STATUS_PLACEHOLDER,
        'generated_at': 'Not evaluated yet',
        'is_placeholder': True,
        'safe_actions_available': [],
        'current_sky': {
            'id': 'current_sky.placeholder',
            'label': 'Current Sky',
            'phase': 'Unknown',
            'latest_image': 'Latest image not evaluated yet',
            'capture_status': 'Capture status placeholder',
            'source_recording': 'Source recording status placeholder',
            'summary': 'Future NowView backend contract will provide sanitized live sky state.',
            'data_status': NOW_DATA_STATUS_NOT_EVALUATED,
            'is_placeholder': True,
        },
        'sky_cycle_briefing': {
            'id': 'sky_cycle.placeholder',
            'label': 'Latest Sky Cycle Briefing',
            'verdict_label': 'Cycle Verdict',
            'verdict': 'Not evaluated yet',
            'source_coverage': 'Placeholder',
            'outputs_status': 'Generated outputs not evaluated here',
            'notable_moments_count': 'Placeholder',
            'summary': 'Future SkyCycleSummary will explain the latest complete day/night cycle.',
            'data_status': NOW_DATA_STATUS_FUTURE_CONTRACT,
            'is_placeholder': True,
        },
        'notable_moments': [
            {
                'id': 'moment.meteor_candidate.placeholder',
                'label': 'Meteor candidate',
                'confidence': 'Placeholder',
                'evidence': 'Future MomentSummary evidence',
                'status': 'Not evaluated yet',
                'data_status': NOW_DATA_STATUS_FUTURE_CONTRACT,
                'is_placeholder': True,
            },
            {
                'id': 'moment.lightning_storm.placeholder',
                'label': 'Lightning or storm candidate',
                'confidence': 'Placeholder',
                'evidence': 'Future weather/sky evidence',
                'status': 'Not evaluated yet',
                'data_status': NOW_DATA_STATUS_FUTURE_CONTRACT,
                'is_placeholder': True,
            },
            {
                'id': 'moment.clear_window.placeholder',
                'label': 'Clear window',
                'confidence': 'Placeholder',
                'evidence': 'Future sky quality timeline',
                'status': 'Not evaluated yet',
                'data_status': NOW_DATA_STATUS_FUTURE_CONTRACT,
                'is_placeholder': True,
            },
            {
                'id': 'moment.anomaly.placeholder',
                'label': 'Anomaly',
                'confidence': 'Placeholder',
                'evidence': 'Future observatory diagnostics',
                'status': 'Not evaluated yet',
                'data_status': NOW_DATA_STATUS_FUTURE_CONTRACT,
                'is_placeholder': True,
            },
        ],
        'generated_outputs': [
            {
                'id': 'output.best_image.placeholder',
                'label': 'Best image',
                'status': 'Placeholder',
                'look': 'No look evaluated',
                'lineage': 'Source lineage placeholder',
                'data_status': NOW_DATA_STATUS_FUTURE_CONTRACT,
                'is_placeholder': True,
            },
            {
                'id': 'output.timelapse.placeholder',
                'label': 'Timelapse',
                'status': 'Placeholder',
                'look': 'No look evaluated',
                'lineage': 'Source lineage placeholder',
                'data_status': NOW_DATA_STATUS_FUTURE_CONTRACT,
                'is_placeholder': True,
            },
            {
                'id': 'output.keogram.placeholder',
                'label': 'Keogram',
                'status': 'Placeholder',
                'look': 'No look evaluated',
                'lineage': 'Source lineage placeholder',
                'data_status': NOW_DATA_STATUS_FUTURE_CONTRACT,
                'is_placeholder': True,
            },
            {
                'id': 'output.startrail.placeholder',
                'label': 'Startrail',
                'status': 'Placeholder',
                'look': 'No look evaluated',
                'lineage': 'Source lineage placeholder',
                'data_status': NOW_DATA_STATUS_FUTURE_CONTRACT,
                'is_placeholder': True,
            },
        ],
        'observatory_health': [
            {
                'id': 'health.camera.placeholder',
                'label': 'Camera',
                'status': 'Not evaluated here',
                'note': 'Future ObservatoryHealth camera state.',
                'data_status': NOW_DATA_STATUS_NOT_EVALUATED,
                'is_placeholder': True,
            },
            {
                'id': 'health.storage.placeholder',
                'label': 'Storage',
                'status': 'Not evaluated here',
                'note': 'Future storage health and source preservation state.',
                'data_status': NOW_DATA_STATUS_NOT_EVALUATED,
                'is_placeholder': True,
            },
            {
                'id': 'health.source_preservation.placeholder',
                'label': 'Source preservation',
                'status': 'Placeholder',
                'note': 'RAW/FITS/source preservation remains a product invariant.',
                'data_status': NOW_DATA_STATUS_PLACEHOLDER,
                'is_placeholder': True,
            },
            {
                'id': 'health.generation.placeholder',
                'label': 'Generation',
                'status': 'Not evaluated here',
                'note': 'Future output job and rendering status.',
                'data_status': NOW_DATA_STATUS_NOT_EVALUATED,
                'is_placeholder': True,
            },
            {
                'id': 'health.upload_integration.placeholder',
                'label': 'Upload / integration',
                'status': 'Not evaluated here',
                'note': 'Future integration health summary.',
                'data_status': NOW_DATA_STATUS_NOT_EVALUATED,
                'is_placeholder': True,
            },
            {
                'id': 'health.warnings.placeholder',
                'label': 'Warnings',
                'status': 'Placeholder',
                'note': 'Future AttentionItem summary.',
                'data_status': NOW_DATA_STATUS_PLACEHOLDER,
                'is_placeholder': True,
            },
        ],
        'attention_items': [
            {
                'id': 'attention.backend_contract.placeholder',
                'label': 'Backend contract needed',
                'status': 'Blocked',
                'note': 'Now will need sanitized domain view models before live data appears here.',
                'data_status': NOW_DATA_STATUS_FUTURE_CONTRACT,
                'is_placeholder': True,
            },
            {
                'id': 'attention.safe_actions.placeholder',
                'label': 'Safe actions unavailable',
                'status': 'Read-only',
                'note': 'This prototype exposes no controls.',
                'data_status': NOW_DATA_STATUS_PLACEHOLDER,
                'is_placeholder': True,
            },
            {
                'id': 'attention.source_lineage.placeholder',
                'label': 'Source lineage placeholder',
                'status': 'Future contract',
                'note': 'Output lineage is shown as a concept only.',
                'data_status': NOW_DATA_STATUS_FUTURE_CONTRACT,
                'is_placeholder': True,
            },
        ],
        'metadata': {
            'contract': 'NowView',
            'contract_version': 'v1-placeholder',
            'source': 'static backend-owned builder',
            'data_status': NOW_DATA_STATUS_PLACEHOLDER,
            'notes': [
                'No runtime state evaluated.',
                'No database, filesystem, camera, source, or media generation access.',
            ],
        },
    }
