#!/usr/bin/env python3

import inspect
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))


from indi_allsky.modern_admin_settings_contracts import ModernAdminNotificationsSettingsContract
from indi_allsky.modern_admin_settings_contracts import ModernAdminStorageSettingsContract


def assert_true(condition, message):
    if not condition:
        raise AssertionError(message)


def test_notifications_settings_contract_preserves_context_shape():
    contract = ModernAdminNotificationsSettingsContract()
    notifications_group = {
        'group_id': 'notifications',
        'label': 'Notifications',
    }

    context = contract.build_context((
        {'group_id': 'other'},
        notifications_group,
    ))

    assert_true(
        context['modern_admin_notifications_settings_group'] is notifications_group,
        'notifications group must be selected from settings inventory groups',
    )
    assert_true(
        len(context['modern_admin_notifications_overview_cards']) == 6,
        'notifications overview cards shape changed',
    )
    assert_true(
        len(context['modern_admin_notifications_config_sections']) == 4,
        'notifications config sections shape changed',
    )
    assert_true(
        len(context['modern_admin_notifications_proposed_layout']) == 4,
        'notifications proposed layout shape changed',
    )
    assert_true(
        context['modern_admin_notifications_overview_cards'][0]['current_status'] == 'not evaluated here',
        'notifications overview current status changed',
    )
    assert_true(
        context['modern_admin_notifications_config_sections'][0]['key_count'] == 2,
        'notifications config key count changed',
    )
    assert_true(
        context['modern_admin_notifications_proposed_layout'][0]['note'] == 'read-only proposal',
        'notifications layout note changed',
    )


def test_notifications_settings_contract_handles_missing_group():
    contract = ModernAdminNotificationsSettingsContract()
    context = contract.build_context(())

    assert_true(
        context['modern_admin_notifications_settings_group'] is None,
        'missing notifications group must remain a safe None fallback',
    )


def test_notifications_settings_view_uses_hybrid_contract():
    views_text = (REPO_ROOT / 'indi_allsky/flask/views.py').read_text(encoding='utf-8')
    start = views_text.index('class ModernAdminNotificationsSettingsView')
    end = views_text.index('class ModernAdminCameraProfileSettingsView', start)
    notifications_view = views_text[start:end]

    assert_true(
        'ModernAdminNotificationsSettingsContract' in notifications_view,
        'notifications settings view must use the Hybrid settings contract',
    )
    assert_true(
        'settings_contract' in notifications_view,
        'notifications settings view must expose the contract dependency explicitly',
    )
    assert_true(
        'NOTIFICATIONS_CONFIG_SECTIONS' not in notifications_view,
        'notifications static config sections must not remain inline on the view',
    )
    assert_true(
        'get_notifications_overview_cards' not in notifications_view,
        'notifications overview formatting must not remain inline on the view',
    )


def test_storage_settings_contract_preserves_context_shape():
    contract = ModernAdminStorageSettingsContract()
    storage_group = {
        'group_id': 'storage_drives',
        'label': 'Storage / Drives',
    }

    context = contract.build_context((
        {'group_id': 'other'},
        storage_group,
    ))

    assert_true(
        context['modern_admin_storage_settings_group'] is storage_group,
        'storage group must be selected from settings inventory groups',
    )
    assert_true(
        len(context['modern_admin_storage_overview_cards']) == 6,
        'storage overview cards shape changed',
    )
    assert_true(
        len(context['modern_admin_storage_config_sections']) == 4,
        'storage config sections shape changed',
    )
    assert_true(
        len(context['modern_admin_storage_proposed_layout']) == 4,
        'storage proposed layout shape changed',
    )
    assert_true(
        context['modern_admin_storage_overview_cards'][0]['current_status'] == 'not evaluated here',
        'storage overview current status changed',
    )
    assert_true(
        context['modern_admin_storage_config_sections'][1]['key_count'] == 6,
        'storage retention/path config key count changed',
    )
    assert_true(
        context['modern_admin_storage_proposed_layout'][0]['note'] == 'read-only proposal',
        'storage layout note changed',
    )


def test_storage_settings_contract_handles_missing_group():
    contract = ModernAdminStorageSettingsContract()
    context = contract.build_context(())

    assert_true(
        context['modern_admin_storage_settings_group'] is None,
        'missing storage group must remain a safe None fallback',
    )


def test_storage_settings_view_uses_hybrid_contract():
    views_text = (REPO_ROOT / 'indi_allsky/flask/views.py').read_text(encoding='utf-8')
    start = views_text.index('class ModernAdminStorageSettingsView')
    end = views_text.index('class ModernAdminNotificationsSettingsView', start)
    storage_view = views_text[start:end]

    assert_true(
        'ModernAdminStorageSettingsContract' in storage_view,
        'storage settings view must use the Hybrid settings contract',
    )
    assert_true(
        'settings_contract' in storage_view,
        'storage settings view must expose the contract dependency explicitly',
    )
    assert_true(
        'STORAGE_CONFIG_SECTIONS' not in storage_view,
        'storage static config sections must not remain inline on the view',
    )
    assert_true(
        'get_storage_overview_cards' not in storage_view,
        'storage overview formatting must not remain inline on the view',
    )


def test_settings_contract_module_has_no_flask_or_runtime_config_dependency():
    import indi_allsky.modern_admin_settings_contracts as module

    source = inspect.getsource(module)
    lower_source = source.lower()

    forbidden_tokens = (
        'flask',
        'request',
        'db.session',
        'open(',
        'app.config',
    )

    for token in forbidden_tokens:
        assert_true(
            token not in lower_source,
            'settings contract module must not depend on {0:s}'.format(token),
        )


def run_tests():
    test_notifications_settings_contract_preserves_context_shape()
    test_notifications_settings_contract_handles_missing_group()
    test_notifications_settings_view_uses_hybrid_contract()
    test_storage_settings_contract_preserves_context_shape()
    test_storage_settings_contract_handles_missing_group()
    test_storage_settings_view_uses_hybrid_contract()
    test_settings_contract_module_has_no_flask_or_runtime_config_dependency()


if __name__ == '__main__':
    run_tests()
