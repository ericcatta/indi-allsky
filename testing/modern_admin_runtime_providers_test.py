#!/usr/bin/env python3

import inspect
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

import indi_allsky.modern_admin_runtime_providers as runtime_providers
from indi_allsky.modern_admin_runtime_providers import ModernAdminCameraRuntimeMetadataProvider
from indi_allsky.modern_admin_runtime_providers import ModernAdminCurrentCaptureMetadataRepository
from indi_allsky.modern_admin_runtime_providers import ModernAdminServiceStatusProvider
from indi_allsky.modern_admin_runtime_providers import ModernAdminWatchdogStatusSummaryProvider


def assert_true(condition, message):
    if not condition:
        raise AssertionError(message)


class FakeCamera:
    def __init__(self, friendly_name=None, name=None, driver=None):
        self.friendlyName = friendly_name
        self.name = name
        self.driver = driver


def test_service_status_provider_reports_active_service():
    calls = []

    def adapter(service_name):
        calls.append(service_name)
        return {
            'output': 'active\n',
        }

    provider = ModernAdminServiceStatusProvider(status_adapter=adapter)
    status = provider.get_service_status('indi-allsky.service')

    assert_true(calls == ['indi-allsky.service'], 'provider must call adapter with service name')
    assert_true(status == {
        'state'          : 'active',
        'running'        : True,
        'label'          : '● Running',
        'tone'           : 'good',
        'toggle_command' : 'stop',
        'toggle_label'   : 'Stop Capture',
        'output'         : 'active',
    }, 'active status payload must match existing Modern/Admin shape')


def test_service_status_provider_reports_failed_service():
    provider = ModernAdminServiceStatusProvider(status_adapter=lambda service_name: {'output': 'failed'})
    status = provider.get_service_status('indi-allsky.service')

    assert_true(status['state'] == 'failed', 'failed service state must be preserved')
    assert_true(status['running'] is False, 'failed service must not be marked running')
    assert_true(status['label'] == '● Failed', 'failed service label must match existing UI contract')
    assert_true(status['tone'] == 'danger', 'failed service tone must match existing UI contract')
    assert_true(status['toggle_command'] == 'start', 'failed service should offer start command')


def test_service_status_provider_reports_stopped_service():
    provider = ModernAdminServiceStatusProvider(status_adapter=lambda service_name: {'output': 'inactive'})
    status = provider.get_service_status('indi-allsky.service')

    assert_true(status['state'] == 'inactive', 'inactive service state must be preserved')
    assert_true(status['running'] is False, 'inactive service must not be marked running')
    assert_true(status['label'] == '○ Stopped', 'inactive service label must match existing UI contract')
    assert_true(status['tone'] == 'muted', 'inactive service tone must match existing UI contract')
    assert_true(status['toggle_command'] == 'start', 'inactive service should offer start command')


def test_service_status_provider_handles_missing_adapter_safely():
    provider = ModernAdminServiceStatusProvider()
    status = provider.get_service_status('indi-allsky.service')

    assert_true(status['state'] == 'unknown', 'missing adapter should produce unknown state')
    assert_true(status['running'] is False, 'missing adapter must not be marked running')
    assert_true(status['label'] == '? Unknown', 'missing adapter label must match existing fallback shape')
    assert_true(status['toggle_command'] == 'start', 'missing adapter should offer start command')


def test_service_status_provider_handles_adapter_error_safely():
    def adapter(service_name):
        raise OSError('systemctl missing')

    provider = ModernAdminServiceStatusProvider(status_adapter=adapter)
    status = provider.get_service_status('indi-allsky.service')

    assert_true(status['state'] == 'unknown', 'adapter error should produce unknown state')
    assert_true(status['running'] is False, 'adapter error must not be marked running')
    assert_true(status['output'] == 'systemctl missing', 'adapter error should preserve safe text output')


def test_service_status_provider_is_framework_free():
    source = inspect.getsource(runtime_providers)

    forbidden = (
        'flask',
        'request',
        'current_user',
        'db.session',
        'subprocess',
        'systemctl',
    )

    for token in forbidden:
        assert_true(token not in source, 'runtime provider must not depend on {0:s}'.format(token))


def test_modern_capture_service_status_uses_hybrid_provider_static():
    views_source = (REPO_ROOT / 'indi_allsky' / 'flask' / 'views.py').read_text()
    function_start = views_source.index('def get_modern_admin_capture_service_status')
    function_end = views_source.index('class ModernAdminView')
    function_source = views_source[function_start:function_end]

    assert_true(
        'ModernAdminServiceStatusProvider' in function_source,
        'Modern capture service status must enter through the Hybrid provider',
    )
    assert_true(
        'status_adapter=systemctl_status_adapter' in function_source,
        'systemctl must remain an injected adapter for the Hybrid provider',
    )
    assert_true(
        "'state'          : state" not in function_source,
        'status payload policy should not remain inline in views.py',
    )


def test_camera_runtime_provider_reports_multi_camera_active():
    provider = ModernAdminCameraRuntimeMetadataProvider()
    status = provider.get_runtime_status(
        multi_camera_enabled=True,
        profile_configs=[
            {'enabled': True, 'label': 'IMX708 Wide'},
            {'enabled': True, 'label': 'ASI678MC'},
        ],
        recent_camera_ids=[1, 2],
        recent_camera_labels=['IMX708 Wide', 'ASI678MC'],
    )

    assert_true(status == {
        'label' : 'Runtime: Multi-camera active · IMX708 Wide + ASI678MC',
        'tone'  : 'good',
    }, 'multi-camera active payload must match existing shell contract')


def test_camera_runtime_provider_reports_restart_required_for_one_recent_camera():
    provider = ModernAdminCameraRuntimeMetadataProvider()
    status = provider.get_runtime_status(
        multi_camera_enabled=True,
        profile_configs=[
            {'enabled': True, 'label': 'IMX708 Wide'},
            {'enabled': True, 'label': 'ASI678MC'},
        ],
        recent_camera_ids=[1],
        recent_camera_labels=['IMX708 Wide'],
    )

    assert_true(status == {
        'label' : 'Runtime: Restart required or only one camera active · IMX708 Wide',
        'tone'  : 'warn',
    }, 'one recent camera should preserve existing restart-required message')


def test_camera_runtime_provider_reports_config_enabled_without_recent_cameras():
    provider = ModernAdminCameraRuntimeMetadataProvider()
    status = provider.get_runtime_status(
        multi_camera_enabled=True,
        profile_configs=[
            {'enabled': True, 'label': 'IMX708 Wide'},
            {'enabled': False, 'label': 'Disabled Camera'},
            {'enabled': True, 'camera_name': 'ASI678MC'},
        ],
        recent_camera_ids=[],
        recent_camera_labels=[],
    )

    assert_true(status == {
        'label' : 'Config: Multi-camera enabled · Restart may be required · IMX708 Wide + ASI678MC',
        'tone'  : 'warn',
    }, 'config-only multi-camera status should use enabled profile labels')


def test_camera_runtime_provider_reports_single_camera_with_current_camera_fallback():
    provider = ModernAdminCameraRuntimeMetadataProvider()
    status = provider.get_runtime_status(
        multi_camera_enabled=False,
        recent_camera_ids=[],
        recent_camera_labels=[],
        current_camera=FakeCamera(friendly_name='', name='ASI678MC', driver='ZWO'),
    )

    assert_true(status == {
        'label' : 'Capture: Single camera · ASI678MC',
        'tone'  : 'muted',
    }, 'single-camera fallback should use current camera identity')


def test_camera_runtime_provider_handles_missing_camera_safely():
    provider = ModernAdminCameraRuntimeMetadataProvider()
    status = provider.get_runtime_status(
        multi_camera_enabled=False,
        recent_camera_ids=[],
        recent_camera_labels=[],
        current_camera=None,
    )

    assert_true(status == {
        'label' : 'Capture: Single camera',
        'tone'  : 'muted',
    }, 'missing current camera should produce safe single-camera fallback')


def test_camera_runtime_provider_formats_long_camera_list():
    provider = ModernAdminCameraRuntimeMetadataProvider()

    assert_true(
        provider.format_camera_list(['A', 'B', 'C']) == 'A + B + 1 more',
        'long camera list should preserve existing compact shell format',
    )


def test_modern_runtime_status_uses_hybrid_camera_provider_static():
    views_source = (REPO_ROOT / 'indi_allsky' / 'flask' / 'views.py').read_text()
    function_start = views_source.index('def get_modern_admin_runtime_status')
    function_end = views_source.index('def get_recent_image_camera_ids')
    function_source = views_source[function_start:function_end]

    assert_true(
        'ModernAdminCameraRuntimeMetadataProvider' in function_source,
        'Modern runtime status must enter through the Hybrid camera provider',
    )
    assert_true(
        'multi_camera_enabled=multi_camera_enabled' in function_source,
        'Flask layer should pass normalized config intent into the provider',
    )
    assert_true(
        "Runtime: Multi-camera active" not in function_source,
        'camera runtime status copy/policy should not remain inline in views.py',
    )


def test_watchdog_status_provider_reports_healthy_running_capture():
    provider = ModernAdminWatchdogStatusSummaryProvider()
    metadata = provider.get_current_capture_metadata(
        status_code=1,
        status_map={1: 'running'},
        watchdog_age_seconds=12,
        camera_label='ASI678MC',
    )

    assert_true(metadata == {
        'capture_state': 'running',
        'is_acquiring': True,
        'camera_label': 'ASI678MC',
        'policy_label': 'Capture policy allows normal acquisition.',
        'source_status': 'Persisted capture status and watchdog are available.',
        'watchdog_age_seconds': 12,
    }, 'healthy watchdog metadata must preserve current capture summary contract')


def test_watchdog_status_provider_reports_stale_error_capture():
    provider = ModernAdminWatchdogStatusSummaryProvider()
    metadata = provider.get_current_capture_metadata(
        status_code=9,
        status_map={9: 'error'},
        watchdog_age_seconds=700,
        camera_label='ASI678MC',
    )

    assert_true(metadata['capture_state'] == 'error', 'error status code should map to error state')
    assert_true(metadata['is_acquiring'] is False, 'error state must not be acquiring')
    assert_true(
        metadata['source_status'] == 'Persisted capture watchdog is stale.',
        'stale watchdog should preserve existing source status wording',
    )


def test_watchdog_status_provider_handles_missing_watchdog_safely():
    provider = ModernAdminWatchdogStatusSummaryProvider()
    metadata = provider.get_current_capture_metadata(
        status_code=None,
        status_map={},
        watchdog_age_seconds=None,
        camera_label='Camera not evaluated yet',
    )

    assert_true(metadata['capture_state'] == 'unknown', 'missing status should map to unknown')
    assert_true(metadata['is_acquiring'] is False, 'unknown state must not be acquiring')
    assert_true(
        metadata['source_status'] == 'Persisted capture status read; watchdog age not evaluated.',
        'missing watchdog age should preserve safe fallback wording',
    )


def test_watchdog_status_provider_prioritizes_pause_and_policy():
    provider = ModernAdminWatchdogStatusSummaryProvider()
    metadata = provider.get_current_capture_metadata(
        status_code=1,
        status_map={1: 'running'},
        watchdog_age_seconds='unknown',
        capture_pause=True,
        daytime_capture=True,
        daytime_capture_save=False,
    )

    assert_true(metadata['capture_state'] == 'paused', 'capture pause should override raw running state')
    assert_true(metadata['is_acquiring'] is False, 'paused state must not be acquiring')
    assert_true(metadata['policy_label'] == 'Capture intentionally paused.', 'pause policy label must be preserved')
    assert_true(
        metadata['source_status'] == 'Persisted capture status read; watchdog age unavailable.',
        'non-numeric watchdog age should preserve unavailable wording',
    )


def test_current_capture_metadata_repository_returns_copy():
    repository = ModernAdminCurrentCaptureMetadataRepository({
        'capture_state': 'running',
        'watchdog_age_seconds': 5,
    })

    metadata = repository.get_current_capture_metadata()
    metadata['capture_state'] = 'mutated'

    assert_true(
        repository.get_current_capture_metadata()['capture_state'] == 'running',
        'repository adapter should not expose mutable internal metadata',
    )


def test_modern_current_capture_repository_uses_hybrid_watchdog_provider_static():
    views_source = (REPO_ROOT / 'indi_allsky' / 'flask' / 'views.py').read_text()
    function_start = views_source.index('def get_current_capture_repository')
    function_end = views_source.index('class ModernAdminHighlightsView')
    function_source = views_source[function_start:function_end]

    assert_true(
        'ModernAdminWatchdogStatusSummaryProvider' in function_source,
        'Now current capture repository must enter through the Hybrid watchdog provider',
    )
    assert_true(
        'ModernAdminCurrentCaptureMetadataRepository' in function_source,
        'Now should expose provider metadata through the Product repository contract',
    )
    assert_true(
        'CurrentCaptureStatusRepository' not in function_source,
        'Modern path should not use the Product repository as runtime ownership boundary',
    )


def run_tests():
    tests = [
        test_service_status_provider_reports_active_service,
        test_service_status_provider_reports_failed_service,
        test_service_status_provider_reports_stopped_service,
        test_service_status_provider_handles_missing_adapter_safely,
        test_service_status_provider_handles_adapter_error_safely,
        test_service_status_provider_is_framework_free,
        test_modern_capture_service_status_uses_hybrid_provider_static,
        test_camera_runtime_provider_reports_multi_camera_active,
        test_camera_runtime_provider_reports_restart_required_for_one_recent_camera,
        test_camera_runtime_provider_reports_config_enabled_without_recent_cameras,
        test_camera_runtime_provider_reports_single_camera_with_current_camera_fallback,
        test_camera_runtime_provider_handles_missing_camera_safely,
        test_camera_runtime_provider_formats_long_camera_list,
        test_modern_runtime_status_uses_hybrid_camera_provider_static,
        test_watchdog_status_provider_reports_healthy_running_capture,
        test_watchdog_status_provider_reports_stale_error_capture,
        test_watchdog_status_provider_handles_missing_watchdog_safely,
        test_watchdog_status_provider_prioritizes_pause_and_policy,
        test_current_capture_metadata_repository_returns_copy,
        test_modern_current_capture_repository_uses_hybrid_watchdog_provider_static,
    ]

    for test in tests:
        test()


if __name__ == '__main__':
    run_tests()
