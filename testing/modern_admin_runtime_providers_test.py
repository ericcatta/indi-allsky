#!/usr/bin/env python3

import inspect
import sys
from datetime import datetime
from datetime import timedelta
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

import indi_allsky.modern_admin_runtime_providers as runtime_providers
from indi_allsky.modern_admin_runtime_providers import ModernAdminCameraRuntimeMetadataProvider
from indi_allsky.modern_admin_runtime_providers import ModernAdminCaptureHealthSummaryProvider
from indi_allsky.modern_admin_runtime_providers import ModernAdminCurrentCaptureMetadataRepository
from indi_allsky.modern_admin_runtime_providers import ModernAdminLocationMetadataProvider
from indi_allsky.modern_admin_runtime_providers import ModernAdminSensorWeatherMetadataProvider
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


class FakeLocationCamera:
    def __init__(self, latitude=None, longitude=None, elevation=None):
        self.latitude = latitude
        self.longitude = longitude
        self.elevation = elevation


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


def test_capture_health_provider_reports_fresh_frame():
    now = datetime(2026, 7, 4, 10, 0, 0)
    provider = ModernAdminCaptureHealthSummaryProvider()
    summary = provider.get_capture_health_summary(
        profile_configs=[{
            'enabled': True,
            'profile_id': 'wide',
            'camera_id': 1,
            'label': 'IMX708 Wide',
            'exposure_period': 45,
            'exposure_timeout': 90,
        }],
        latest_frames=[{
            'camera_id': 1,
            'timestamp': now - timedelta(seconds=30),
        }],
        now=now,
    )

    assert_true(summary['status'] == 'ok', 'fresh frame summary should be ok')
    assert_true(summary['tone'] == 'good', 'fresh frame summary tone should be good')
    assert_true(summary['camera_health'][0]['status'] == 'ok', 'fresh camera health should be ok')
    assert_true(summary['camera_health'][0]['latest_frame_age_seconds'] == 30, 'fresh age should be computed')
    assert_true(summary['camera_health'][0]['stale_after_seconds'] == 135.0, 'stale threshold should derive from interval')


def test_capture_health_provider_reports_stale_frame():
    now = datetime(2026, 7, 4, 10, 0, 0)
    provider = ModernAdminCaptureHealthSummaryProvider()
    summary = provider.get_capture_health_summary(
        profile_configs=[{
            'enabled': True,
            'profile_id': 'zwo',
            'camera_id': 2,
            'label': 'ASI678MC',
            'expected_interval_seconds': 45,
        }],
        latest_frames=[{
            'camera_id': 2,
            'timestamp': now - timedelta(seconds=180),
        }],
        now=now,
    )

    assert_true(summary['status'] == 'stale', 'single stale frame summary should be stale')
    assert_true(summary['tone'] == 'warn', 'stale frame summary tone should warn')
    assert_true(summary['camera_health'][0]['status'] == 'stale', 'stale camera health should be stale')
    assert_true(summary['camera_health'][0]['status_label'] == 'Latest frame is stale.', 'stale label should be product-safe')


def test_capture_health_provider_reports_missing_frame():
    provider = ModernAdminCaptureHealthSummaryProvider()
    summary = provider.get_capture_health_summary(
        profile_configs=[{
            'enabled': True,
            'profile_id': 'zwo',
            'camera_id': 2,
            'label': 'ASI678MC',
        }],
        latest_frames=[],
        now=datetime(2026, 7, 4, 10, 0, 0),
    )

    assert_true(summary['status'] == 'missing', 'missing frame summary should be missing')
    assert_true(summary['tone'] == 'muted', 'missing frame summary tone should be muted')
    assert_true(summary['camera_health'][0]['status'] == 'missing', 'missing camera health should be missing')
    assert_true(summary['camera_health'][0]['latest_frame_timestamp'] is None, 'missing frame timestamp should stay None')


def test_capture_health_provider_reports_multi_camera_mixed_state():
    now = datetime(2026, 7, 4, 10, 0, 0)
    provider = ModernAdminCaptureHealthSummaryProvider()
    summary = provider.get_capture_health_summary(
        profile_configs=[
            {
                'enabled': True,
                'profile_id': 'wide',
                'camera_id': 1,
                'label': 'IMX708 Wide',
                'exposure_period': 45,
            },
            {
                'enabled': True,
                'profile_id': 'zwo',
                'camera_id': 2,
                'label': 'ASI678MC',
                'exposure_period': 45,
            },
        ],
        latest_frames=[
            {
                'camera_id': 1,
                'timestamp': now - timedelta(seconds=20),
            },
            {
                'camera_id': 2,
                'timestamp': now - timedelta(seconds=200),
            },
        ],
        now=now,
    )

    statuses = [item['status'] for item in summary['camera_health']]

    assert_true(summary['status'] == 'mixed', 'mixed multi-camera state should be explicit')
    assert_true(summary['tone'] == 'warn', 'mixed multi-camera state should warn')
    assert_true(statuses == ['ok', 'stale'], 'per-camera statuses should be preserved')


def test_modern_capture_health_summary_uses_hybrid_provider_static():
    views_source = (REPO_ROOT / 'indi_allsky' / 'flask' / 'views.py').read_text()
    function_start = views_source.index('def get_modern_admin_capture_health_summary')
    function_end = views_source.index('def get_latest_capture_health_frames', function_start)
    function_source = views_source[function_start:function_end]

    assert_true(
        'ModernAdminCaptureHealthSummaryProvider' in function_source,
        'Modern capture health summary must enter through the Hybrid provider',
    )
    assert_true(
        'latest_frames=latest_frames' in function_source,
        'Flask layer should pass latest frame metadata as adapter data',
    )
    assert_true(
        'IndiAllSkyDbImageTable.query' not in function_source,
        'DB query execution should stay outside the Hybrid summary provider call',
    )


def test_location_metadata_provider_reports_camera_location():
    provider = ModernAdminLocationMetadataProvider()
    metadata = provider.get_location_metadata(
        camera=FakeLocationCamera(latitude=45.1, longitude=9.2, elevation=240),
        config={
            'GPS_ENABLE': False,
            'LOCATION_NAME': 'Backyard',
            'LOCATION_LATITUDE': 1.0,
            'LOCATION_LONGITUDE': 2.0,
            'LOCATION_ELEVATION': 3,
        },
    )

    assert_true(metadata == {
        'status'          : 'available',
        'tone'            : 'good',
        'source'          : 'camera_metadata',
        'location_name'   : 'Backyard',
        'latitude'        : 45.1,
        'longitude'       : 9.2,
        'elevation'       : 240.0,
        'gps_enabled'     : False,
        'gps_status_label': 'GPS disabled',
        'status_label'    : 'Location metadata available from saved configuration.',
    }, 'camera location metadata should be normalized without live GPS polling')


def test_location_metadata_provider_uses_config_fallback():
    provider = ModernAdminLocationMetadataProvider()
    metadata = provider.get_location_metadata(
        camera=FakeLocationCamera(latitude=None, longitude=None, elevation=None),
        config={
            'GPS_ENABLE': True,
            'LOCATION_LATITUDE': '45.5',
            'LOCATION_LONGITUDE': '9.5',
            'LOCATION_ELEVATION': '200',
        },
    )

    assert_true(metadata['status'] == 'available', 'config fallback location should be available')
    assert_true(metadata['source'] == 'config', 'camera without location should report config source')
    assert_true(metadata['latitude'] == 45.5, 'latitude should be converted to float')
    assert_true(metadata['longitude'] == 9.5, 'longitude should be converted to float')
    assert_true(metadata['elevation'] == 200.0, 'elevation should be converted to float')
    assert_true(metadata['gps_status_label'] == 'GPS enabled', 'GPS enabled label should be explicit')


def test_location_metadata_provider_handles_missing_location_safely():
    provider = ModernAdminLocationMetadataProvider()
    metadata = provider.get_location_metadata(
        camera=FakeLocationCamera(latitude='bad', longitude=None, elevation=None),
        config={
            'GPS_ENABLE': True,
            'LOCATION_LATITUDE': 'bad',
            'LOCATION_LONGITUDE': None,
        },
    )

    assert_true(metadata['status'] == 'unknown', 'invalid/missing location should be unknown')
    assert_true(metadata['tone'] == 'muted', 'unknown location tone should be muted')
    assert_true(metadata['latitude'] is None, 'invalid latitude should be None')
    assert_true(metadata['longitude'] is None, 'missing longitude should be None')
    assert_true(metadata['status_label'] == 'GPS enabled, but location metadata is unavailable.', 'missing GPS location label should be safe')


def test_modern_virtualsky_uses_hybrid_location_provider_static():
    views_source = (REPO_ROOT / 'indi_allsky' / 'flask' / 'views.py').read_text()
    class_start = views_source.index('class ModernAdminVirtualSkyView')
    class_end = views_source.index('class ModernAdminLogView', class_start)
    class_source = views_source[class_start:class_end]

    assert_true(
        'ModernAdminLocationMetadataProvider' in class_source,
        'Modern VirtualSky must use the Hybrid location metadata provider',
    )
    assert_true(
        "context['modern_admin_location_metadata'] = location_metadata" in class_source,
        'Modern VirtualSky should expose provider payload without reshaping in template',
    )
    assert_true(
        'self.location_metadata_provider.get_location_metadata' in class_source,
        'Location metadata must enter through the provider boundary',
    )


def test_sensor_weather_metadata_provider_reports_available_latest_metadata():
    now = datetime(2026, 7, 4, 10, 0, 0)
    provider = ModernAdminSensorWeatherMetadataProvider()
    metadata = provider.get_sensor_weather_metadata(
        latest_image_data={
            'sensor_user_0': 0.0,
            'sensor_user_10': '21.5',
            'sensor_temp_0': -5.2,
            'sensor_temp_1': 'not numeric',
        },
        latest_image_timestamp=now - timedelta(seconds=120),
        now=now,
    )

    assert_true(metadata['status'] == 'available', 'fresh persisted sensor metadata should be available')
    assert_true(metadata['tone'] == 'good', 'available sensor metadata tone should be good')
    assert_true(metadata['latest_timestamp'] == '2026-07-04T09:58:00', 'timestamp should be JSON-safe text')
    assert_true(metadata['age_seconds'] == 120, 'age should be computed from latest frame timestamp')
    assert_true(metadata['sensor_user_count'] == 2, 'numeric user slots should be counted, including zero')
    assert_true(metadata['sensor_temp_count'] == 1, 'non-numeric temp slots should be ignored')
    assert_true(metadata['sensor_field_count'] == 3, 'field count should summarize all persisted sensor slots')
    assert_true(
        metadata['source_status'] == 'Persisted sensor/weather metadata available from latest frame.',
        'available metadata source wording should be product-safe',
    )


def test_sensor_weather_metadata_provider_reports_stale_metadata():
    now = datetime(2026, 7, 4, 10, 0, 0)
    provider = ModernAdminSensorWeatherMetadataProvider()
    metadata = provider.get_sensor_weather_metadata(
        latest_image_data={
            'sensor_user_10': 21.5,
        },
        latest_image_timestamp=now - timedelta(seconds=1200),
        now=now,
        stale_after_seconds=900,
    )

    assert_true(metadata['status'] == 'stale', 'old persisted sensor metadata should be stale')
    assert_true(metadata['tone'] == 'warn', 'stale sensor metadata should warn')
    assert_true(metadata['age_seconds'] == 1200, 'stale age should be preserved')
    assert_true(
        metadata['source_status'] == 'Persisted sensor/weather metadata is stale.',
        'stale metadata source wording should be product-safe',
    )


def test_sensor_weather_metadata_provider_handles_missing_metadata_safely():
    provider = ModernAdminSensorWeatherMetadataProvider()
    metadata = provider.get_sensor_weather_metadata(
        latest_image_data=None,
        latest_image_timestamp=None,
        now=datetime(2026, 7, 4, 10, 0, 0),
    )

    assert_true(metadata['status'] == 'missing', 'missing sensor metadata should be explicit')
    assert_true(metadata['tone'] == 'muted', 'missing sensor metadata tone should be muted')
    assert_true(metadata['latest_timestamp'] is None, 'missing timestamp should stay None')
    assert_true(metadata['age_seconds'] is None, 'missing age should stay None')
    assert_true(metadata['sensor_field_count'] == 0, 'missing metadata should expose zero fields')
    assert_true(
        metadata['source_status'] == 'No persisted sensor/weather metadata found.',
        'missing metadata source wording should be safe',
    )


def test_modern_sensor_panel_uses_hybrid_sensor_weather_provider_static():
    views_source = (REPO_ROOT / 'indi_allsky' / 'flask' / 'views.py').read_text()
    class_start = views_source.index('class ModernAdminSensorPanelView')
    class_end = views_source.index('class ModernAdminSystemToolView', class_start)
    class_source = views_source[class_start:class_end]

    assert_true(
        'ModernAdminSensorWeatherMetadataProvider' in class_source,
        'Modern Sensor Panel must use the Hybrid sensor/weather metadata provider',
    )
    assert_true(
        "context['modern_admin_sensor_weather_metadata']" in class_source,
        'Modern Sensor Panel should expose sensor/weather provider payload as a context key',
    )
    assert_true(
        'sensor_user_count' not in class_source,
        'sensor/weather metadata summary policy should not remain inline in views.py',
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
        test_capture_health_provider_reports_fresh_frame,
        test_capture_health_provider_reports_stale_frame,
        test_capture_health_provider_reports_missing_frame,
        test_capture_health_provider_reports_multi_camera_mixed_state,
        test_modern_capture_health_summary_uses_hybrid_provider_static,
        test_location_metadata_provider_reports_camera_location,
        test_location_metadata_provider_uses_config_fallback,
        test_location_metadata_provider_handles_missing_location_safely,
        test_modern_virtualsky_uses_hybrid_location_provider_static,
        test_sensor_weather_metadata_provider_reports_available_latest_metadata,
        test_sensor_weather_metadata_provider_reports_stale_metadata,
        test_sensor_weather_metadata_provider_handles_missing_metadata_safely,
        test_modern_sensor_panel_uses_hybrid_sensor_weather_provider_static,
        test_modern_current_capture_repository_uses_hybrid_watchdog_provider_static,
    ]

    for test in tests:
        test()


if __name__ == '__main__':
    run_tests()
