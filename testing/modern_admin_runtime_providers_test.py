#!/usr/bin/env python3

import inspect
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

import indi_allsky.modern_admin_runtime_providers as runtime_providers
from indi_allsky.modern_admin_runtime_providers import ModernAdminServiceStatusProvider


def assert_true(condition, message):
    if not condition:
        raise AssertionError(message)


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


def run_tests():
    tests = [
        test_service_status_provider_reports_active_service,
        test_service_status_provider_reports_failed_service,
        test_service_status_provider_reports_stopped_service,
        test_service_status_provider_handles_missing_adapter_safely,
        test_service_status_provider_handles_adapter_error_safely,
        test_service_status_provider_is_framework_free,
        test_modern_capture_service_status_uses_hybrid_provider_static,
    ]

    for test in tests:
        test()


if __name__ == '__main__':
    run_tests()
