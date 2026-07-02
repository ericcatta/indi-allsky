#!/usr/bin/env python3

import inspect
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))


from indi_allsky.modern_admin_settings_contracts import ModernAdminAcquisitionSaveSettingsContract
from indi_allsky.modern_admin_settings_contracts import ModernAdminAutoExposureGainSettingsContract
from indi_allsky.modern_admin_settings_contracts import ModernAdminCameraConnectionSettingsContract
from indi_allsky.modern_admin_settings_contracts import ModernAdminCameraProfileSettingsContract
from indi_allsky.modern_admin_settings_contracts import ModernAdminExposureGainSettingsContract
from indi_allsky.modern_admin_settings_contracts import ModernAdminFitsSourceSettingsContract
from indi_allsky.modern_admin_settings_contracts import ModernAdminHybridAwbSettingsContract
from indi_allsky.modern_admin_settings_contracts import ModernAdminNotificationsSettingsContract
from indi_allsky.modern_admin_settings_contracts import ModernAdminSettingsContractBase
from indi_allsky.modern_admin_settings_contracts import ModernAdminStorageSettingsContract


def assert_true(condition, message):
    if not condition:
        raise AssertionError(message)


def contract_guardrail_cases():
    return (
        {
            'name': 'notifications',
            'contract': ModernAdminNotificationsSettingsContract(),
            'future_key': 'future_editable_actionable',
            'groups': (
                {
                    'group_id': 'notifications',
                    'label': 'Notifications',
                    'visibility': 'Advanced',
                },
            ),
            'selected_group_keys': (
                ('modern_admin_notifications_settings_group', 'notifications'),
            ),
            'group_tuple_key': None,
            'expected_context_keys': (
                'modern_admin_notifications_settings_group',
                'modern_admin_notifications_overview_cards',
                'modern_admin_notifications_config_sections',
                'modern_admin_notifications_proposed_layout',
            ),
            'overview_key': 'modern_admin_notifications_overview_cards',
            'config_key': 'modern_admin_notifications_config_sections',
            'layout_key': 'modern_admin_notifications_proposed_layout',
        },
        {
            'name': 'storage',
            'contract': ModernAdminStorageSettingsContract(),
            'future_key': 'future_editable',
            'groups': (
                {
                    'group_id': 'storage_drives',
                    'label': 'Storage / Drives',
                    'visibility': 'Advanced',
                },
            ),
            'selected_group_keys': (
                ('modern_admin_storage_settings_group', 'storage_drives'),
            ),
            'group_tuple_key': None,
            'expected_context_keys': (
                'modern_admin_storage_settings_group',
                'modern_admin_storage_overview_cards',
                'modern_admin_storage_config_sections',
                'modern_admin_storage_proposed_layout',
            ),
            'overview_key': 'modern_admin_storage_overview_cards',
            'config_key': 'modern_admin_storage_config_sections',
            'layout_key': 'modern_admin_storage_proposed_layout',
        },
        {
            'name': 'camera profile',
            'contract': ModernAdminCameraProfileSettingsContract(),
            'future_key': 'future_editable',
            'groups': (
                {
                    'group_id': 'camera_profile_identity',
                    'label': 'Camera Profile Identity',
                    'visibility': 'Basic',
                },
            ),
            'selected_group_keys': (
                ('modern_admin_camera_profile_settings_group', 'camera_profile_identity'),
            ),
            'group_tuple_key': None,
            'expected_context_keys': (
                'modern_admin_camera_profile_settings_group',
                'modern_admin_camera_profile_overview_cards',
                'modern_admin_camera_profile_config_sections',
                'modern_admin_camera_profile_proposed_layout',
            ),
            'overview_key': 'modern_admin_camera_profile_overview_cards',
            'config_key': 'modern_admin_camera_profile_config_sections',
            'layout_key': 'modern_admin_camera_profile_proposed_layout',
        },
        {
            'name': 'camera connection',
            'contract': ModernAdminCameraConnectionSettingsContract(),
            'future_key': 'future_editable',
            'groups': (
                {
                    'group_id': 'camera_connection',
                    'label': 'Camera Connection',
                    'visibility': 'Advanced',
                },
            ),
            'selected_group_keys': (
                ('modern_admin_camera_connection_settings_group', 'camera_connection'),
            ),
            'group_tuple_key': None,
            'expected_context_keys': (
                'modern_admin_camera_connection_settings_group',
                'modern_admin_camera_connection_overview_cards',
                'modern_admin_camera_connection_config_sections',
                'modern_admin_camera_connection_proposed_layout',
            ),
            'overview_key': 'modern_admin_camera_connection_overview_cards',
            'config_key': 'modern_admin_camera_connection_config_sections',
            'layout_key': 'modern_admin_camera_connection_proposed_layout',
        },
        {
            'name': 'exposure gain',
            'contract': ModernAdminExposureGainSettingsContract(),
            'future_key': 'future_editable',
            'groups': (
                {
                    'group_id': 'exposure',
                    'label': 'Exposure',
                    'visibility': 'Advanced',
                },
                {
                    'group_id': 'gain',
                    'label': 'Gain',
                    'visibility': 'Advanced',
                },
            ),
            'selected_group_keys': (
                ('modern_admin_exposure_settings_group', 'exposure'),
                ('modern_admin_gain_settings_group', 'gain'),
            ),
            'group_tuple_key': 'modern_admin_exposure_gain_settings_groups',
            'expected_context_keys': (
                'modern_admin_exposure_settings_group',
                'modern_admin_gain_settings_group',
                'modern_admin_exposure_gain_settings_groups',
                'modern_admin_exposure_gain_overview_cards',
                'modern_admin_exposure_gain_config_sections',
                'modern_admin_exposure_gain_proposed_layout',
            ),
            'overview_key': 'modern_admin_exposure_gain_overview_cards',
            'config_key': 'modern_admin_exposure_gain_config_sections',
            'layout_key': 'modern_admin_exposure_gain_proposed_layout',
        },
        {
            'name': 'auto exposure gain',
            'contract': ModernAdminAutoExposureGainSettingsContract(),
            'future_key': 'future_editable',
            'groups': (
                {
                    'group_id': 'auto_exposure',
                    'label': 'Auto Exposure',
                    'visibility': 'Advanced',
                },
                {
                    'group_id': 'auto_gain',
                    'label': 'Auto Gain',
                    'visibility': 'Advanced',
                },
            ),
            'selected_group_keys': (
                ('modern_admin_auto_exposure_settings_group', 'auto_exposure'),
                ('modern_admin_auto_gain_settings_group', 'auto_gain'),
            ),
            'group_tuple_key': 'modern_admin_auto_exposure_gain_settings_groups',
            'expected_context_keys': (
                'modern_admin_auto_exposure_settings_group',
                'modern_admin_auto_gain_settings_group',
                'modern_admin_auto_exposure_gain_settings_groups',
                'modern_admin_auto_exposure_gain_overview_cards',
                'modern_admin_auto_exposure_gain_config_sections',
                'modern_admin_auto_exposure_gain_proposed_layout',
            ),
            'overview_key': 'modern_admin_auto_exposure_gain_overview_cards',
            'config_key': 'modern_admin_auto_exposure_gain_config_sections',
            'layout_key': 'modern_admin_auto_exposure_gain_proposed_layout',
        },
        {
            'name': 'hybrid AWB',
            'contract': ModernAdminHybridAwbSettingsContract(),
            'future_key': 'future_editable',
            'groups': (
                {
                    'group_id': 'hybrid_awb',
                    'label': 'Hybrid AWB',
                    'visibility': 'Advanced',
                },
            ),
            'selected_group_keys': (
                ('modern_admin_hybrid_awb_settings_group', 'hybrid_awb'),
            ),
            'group_tuple_key': None,
            'expected_context_keys': (
                'modern_admin_hybrid_awb_settings_group',
                'modern_admin_hybrid_awb_overview_cards',
                'modern_admin_hybrid_awb_config_sections',
                'modern_admin_hybrid_awb_proposed_layout',
            ),
            'overview_key': 'modern_admin_hybrid_awb_overview_cards',
            'config_key': 'modern_admin_hybrid_awb_config_sections',
            'layout_key': 'modern_admin_hybrid_awb_proposed_layout',
        },
        {
            'name': 'acquisition save',
            'contract': ModernAdminAcquisitionSaveSettingsContract(),
            'future_key': 'future_editable',
            'groups': (
                {
                    'group_id': 'image_acquisition',
                    'label': 'Image Acquisition',
                    'visibility': 'Advanced',
                },
                {
                    'group_id': 'image_save_formats',
                    'label': 'Image Save Formats',
                    'visibility': 'Advanced',
                },
            ),
            'selected_group_keys': (
                ('modern_admin_image_acquisition_settings_group', 'image_acquisition'),
                ('modern_admin_image_save_formats_settings_group', 'image_save_formats'),
            ),
            'group_tuple_key': 'modern_admin_acquisition_save_settings_groups',
            'expected_context_keys': (
                'modern_admin_image_acquisition_settings_group',
                'modern_admin_image_save_formats_settings_group',
                'modern_admin_acquisition_save_settings_groups',
                'modern_admin_acquisition_save_overview_cards',
                'modern_admin_acquisition_save_config_sections',
                'modern_admin_acquisition_save_proposed_layout',
            ),
            'overview_key': 'modern_admin_acquisition_save_overview_cards',
            'config_key': 'modern_admin_acquisition_save_config_sections',
            'layout_key': 'modern_admin_acquisition_save_proposed_layout',
        },
        {
            'name': 'FITS source',
            'contract': ModernAdminFitsSourceSettingsContract(),
            'future_key': 'future_editable',
            'groups': (
                {
                    'group_id': 'fits_source_files',
                    'label': 'FITS / Source Files',
                    'visibility': 'Developer',
                },
            ),
            'selected_group_keys': (
                ('modern_admin_fits_source_settings_group', 'fits_source_files'),
            ),
            'group_tuple_key': None,
            'expected_context_keys': (
                'modern_admin_fits_source_settings_group',
                'modern_admin_fits_source_overview_cards',
                'modern_admin_fits_source_config_sections',
                'modern_admin_fits_source_proposed_layout',
            ),
            'overview_key': 'modern_admin_fits_source_overview_cards',
            'config_key': 'modern_admin_fits_source_config_sections',
            'layout_key': 'modern_admin_fits_source_proposed_layout',
        },
    )


def get_group_by_id(groups, group_id):
    for group in groups:
        if group.get('group_id') == group_id:
            return group

    raise AssertionError('test group fixture missing {0:s}'.format(group_id))


def assert_overview_cards_shape(case, overview_cards):
    assert_true(overview_cards, '{0:s} overview cards must not be empty'.format(case['name']))

    for card in overview_cards:
        relation_keys = [
            key
            for key in ('related_fields', 'related_keys')
            if key in card
        ]
        assert_true(
            tuple(card.keys()) == (
                'label',
                'purpose',
                relation_keys[0],
                'current_status',
                case['future_key'],
                'safety_note',
            ),
            '{0:s} overview card key order/shape changed'.format(case['name']),
        )
        assert_true(
            len(relation_keys) == 1,
            '{0:s} overview cards must expose exactly one relation tuple'.format(case['name']),
        )
        assert_true(
            isinstance(card[relation_keys[0]], tuple),
            '{0:s} overview relation metadata must remain a tuple'.format(case['name']),
        )
        assert_true(
            card['current_status'] == 'not evaluated here',
            '{0:s} overview current status changed'.format(case['name']),
        )


def assert_config_sections_shape(case, config_sections):
    assert_true(config_sections, '{0:s} config sections must not be empty'.format(case['name']))

    for section in config_sections:
        assert_true(
            tuple(section.keys()) == (
                'label',
                'description',
                'key_count',
                'keys',
            ),
            '{0:s} config section key order/shape changed'.format(case['name']),
        )
        assert_true(
            section['key_count'] == len(section['keys']),
            '{0:s} config key_count must match keys length'.format(case['name']),
        )
        for row in section['keys']:
            assert_true(
                tuple(row.keys()) == ('key', 'source', 'notes'),
                '{0:s} config row key order/shape changed'.format(case['name']),
            )


def assert_proposed_layout_shape(case, proposed_layout):
    assert_true(proposed_layout, '{0:s} proposed layout must not be empty'.format(case['name']))

    for row in proposed_layout:
        assert_true(
            tuple(row.keys()) == (
                'label',
                'purpose',
                'source_keys',
                'proposed_level',
                'note',
            ),
            '{0:s} proposed layout key order/shape changed'.format(case['name']),
        )
        assert_true(
            isinstance(row['source_keys'], tuple),
            '{0:s} proposed source_keys must remain a tuple'.format(case['name']),
        )
        assert_true(
            row['note'] == 'read-only proposal',
            '{0:s} proposed layout note changed'.format(case['name']),
        )
        assert_true(
            row['proposed_level'].startswith('Future '),
            '{0:s} proposed level must keep Future visibility metadata'.format(case['name']),
        )
        assert_true(
            any(level in row['proposed_level'] for level in ('Basic', 'Advanced', 'Developer')),
            '{0:s} proposed level must include Basic/Advanced/Developer visibility'.format(case['name']),
        )


def test_migrated_settings_contracts_preserve_top_level_context_contracts():
    for case in contract_guardrail_cases():
        context = case['contract'].build_context((
            {'group_id': 'unrelated', 'label': 'Unrelated', 'visibility': 'Hidden'},
        ) + case['groups'])

        assert_true(
            tuple(context.keys()) == case['expected_context_keys'],
            '{0:s} top-level context keys changed'.format(case['name']),
        )

        for context_key, group_id in case['selected_group_keys']:
            selected_group = context[context_key]
            expected_group = get_group_by_id(case['groups'], group_id)

            assert_true(
                selected_group is expected_group,
                '{0:s} selected settings group object changed'.format(case['name']),
            )
            assert_true(
                selected_group.get('label'),
                '{0:s} selected settings group label was dropped'.format(case['name']),
            )
            assert_true(
                selected_group.get('visibility') in ('Basic', 'Advanced', 'Developer'),
                '{0:s} selected settings group visibility metadata was dropped'.format(case['name']),
            )

        if case['group_tuple_key']:
            expected_groups = tuple(
                get_group_by_id(case['groups'], group_id)
                for _, group_id in case['selected_group_keys']
            )
            assert_true(
                context[case['group_tuple_key']] == expected_groups,
                '{0:s} grouped settings tuple changed'.format(case['name']),
            )

        assert_overview_cards_shape(case, context[case['overview_key']])
        assert_config_sections_shape(case, context[case['config_key']])
        assert_proposed_layout_shape(case, context[case['layout_key']])


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


def test_camera_profile_settings_contract_preserves_context_shape():
    contract = ModernAdminCameraProfileSettingsContract()
    camera_profile_group = {
        'group_id': 'camera_profile_identity',
        'label': 'Camera Profile Identity',
    }

    context = contract.build_context((
        {'group_id': 'other'},
        camera_profile_group,
    ))

    assert_true(
        context['modern_admin_camera_profile_settings_group'] is camera_profile_group,
        'camera profile group must be selected from settings inventory groups',
    )
    assert_true(
        len(context['modern_admin_camera_profile_overview_cards']) == 6,
        'camera profile overview cards shape changed',
    )
    assert_true(
        len(context['modern_admin_camera_profile_config_sections']) == 4,
        'camera profile config sections shape changed',
    )
    assert_true(
        len(context['modern_admin_camera_profile_proposed_layout']) == 5,
        'camera profile proposed layout shape changed',
    )
    assert_true(
        context['modern_admin_camera_profile_overview_cards'][0]['current_status'] == 'not evaluated here',
        'camera profile overview current status changed',
    )
    assert_true(
        context['modern_admin_camera_profile_config_sections'][2]['key_count'] == 4,
        'camera relationship config key count changed',
    )
    assert_true(
        context['modern_admin_camera_profile_proposed_layout'][0]['note'] == 'read-only proposal',
        'camera profile layout note changed',
    )


def test_camera_profile_settings_contract_handles_missing_group():
    contract = ModernAdminCameraProfileSettingsContract()
    context = contract.build_context(())

    assert_true(
        context['modern_admin_camera_profile_settings_group'] is None,
        'missing camera profile group must remain a safe None fallback',
    )


def test_camera_profile_settings_view_uses_hybrid_contract():
    views_text = (REPO_ROOT / 'indi_allsky/flask/views.py').read_text(encoding='utf-8')
    start = views_text.index('class ModernAdminCameraProfileSettingsView')
    end = views_text.index('class ModernAdminCameraConnectionSettingsView', start)
    camera_profile_view = views_text[start:end]

    assert_true(
        'ModernAdminCameraProfileSettingsContract' in camera_profile_view,
        'camera profile settings view must use the Hybrid settings contract',
    )
    assert_true(
        'settings_contract' in camera_profile_view,
        'camera profile settings view must expose the contract dependency explicitly',
    )
    assert_true(
        'CAMERA_PROFILE_CONFIG_SECTIONS' not in camera_profile_view,
        'camera profile static config sections must not remain inline on the view',
    )
    assert_true(
        'get_camera_profile_overview_cards' not in camera_profile_view,
        'camera profile overview formatting must not remain inline on the view',
    )


def test_camera_connection_settings_contract_preserves_context_shape():
    contract = ModernAdminCameraConnectionSettingsContract()
    camera_connection_group = {
        'group_id': 'camera_connection',
        'label': 'Camera Connection',
    }

    context = contract.build_context((
        {'group_id': 'other'},
        camera_connection_group,
    ))

    assert_true(
        context['modern_admin_camera_connection_settings_group'] is camera_connection_group,
        'camera connection group must be selected from settings inventory groups',
    )
    assert_true(
        len(context['modern_admin_camera_connection_overview_cards']) == 6,
        'camera connection overview cards shape changed',
    )
    assert_true(
        len(context['modern_admin_camera_connection_config_sections']) == 5,
        'camera connection config sections shape changed',
    )
    assert_true(
        len(context['modern_admin_camera_connection_proposed_layout']) == 5,
        'camera connection proposed layout shape changed',
    )
    assert_true(
        context['modern_admin_camera_connection_overview_cards'][0]['current_status'] == 'not evaluated here',
        'camera connection overview current status changed',
    )
    assert_true(
        context['modern_admin_camera_connection_config_sections'][1]['key_count'] == 3,
        'camera connection INDI config key count changed',
    )
    assert_true(
        context['modern_admin_camera_connection_proposed_layout'][0]['note'] == 'read-only proposal',
        'camera connection layout note changed',
    )


def test_camera_connection_settings_contract_handles_missing_group():
    contract = ModernAdminCameraConnectionSettingsContract()
    context = contract.build_context(())

    assert_true(
        context['modern_admin_camera_connection_settings_group'] is None,
        'missing camera connection group must remain a safe None fallback',
    )


def test_camera_connection_settings_view_uses_hybrid_contract():
    views_text = (REPO_ROOT / 'indi_allsky/flask/views.py').read_text(encoding='utf-8')
    start = views_text.index('class ModernAdminCameraConnectionSettingsView')
    end = views_text.index('class ModernAdminExposureGainSettingsView', start)
    camera_connection_view = views_text[start:end]

    assert_true(
        'ModernAdminCameraConnectionSettingsContract' in camera_connection_view,
        'camera connection settings view must use the Hybrid settings contract',
    )
    assert_true(
        'settings_contract' in camera_connection_view,
        'camera connection settings view must expose the contract dependency explicitly',
    )
    assert_true(
        'CAMERA_CONNECTION_CONFIG_SECTIONS' not in camera_connection_view,
        'camera connection static config sections must not remain inline on the view',
    )
    assert_true(
        'get_camera_connection_overview_cards' not in camera_connection_view,
        'camera connection overview formatting must not remain inline on the view',
    )


def test_exposure_gain_settings_contract_preserves_context_shape():
    contract = ModernAdminExposureGainSettingsContract()
    exposure_group = {
        'group_id': 'exposure',
        'label': 'Exposure',
    }
    gain_group = {
        'group_id': 'gain',
        'label': 'Gain',
    }

    context = contract.build_context((
        {'group_id': 'other'},
        exposure_group,
        gain_group,
    ))

    assert_true(
        context['modern_admin_exposure_settings_group'] is exposure_group,
        'exposure group must be selected from settings inventory groups',
    )
    assert_true(
        context['modern_admin_gain_settings_group'] is gain_group,
        'gain group must be selected from settings inventory groups',
    )
    assert_true(
        context['modern_admin_exposure_gain_settings_groups'] == (exposure_group, gain_group),
        'exposure/gain grouped context shape changed',
    )
    assert_true(
        len(context['modern_admin_exposure_gain_overview_cards']) == 6,
        'exposure/gain overview cards shape changed',
    )
    assert_true(
        len(context['modern_admin_exposure_gain_config_sections']) == 4,
        'exposure/gain config sections shape changed',
    )
    assert_true(
        len(context['modern_admin_exposure_gain_proposed_layout']) == 5,
        'exposure/gain proposed layout shape changed',
    )
    assert_true(
        context['modern_admin_exposure_gain_overview_cards'][0]['current_status'] == 'not evaluated here',
        'exposure/gain overview current status changed',
    )
    assert_true(
        context['modern_admin_exposure_gain_config_sections'][0]['key_count'] == 7,
        'manual exposure config key count changed',
    )
    assert_true(
        context['modern_admin_exposure_gain_config_sections'][1]['key_count'] == 6,
        'manual gain config key count changed',
    )
    assert_true(
        context['modern_admin_exposure_gain_proposed_layout'][0]['note'] == 'read-only proposal',
        'exposure/gain layout note changed',
    )


def test_exposure_gain_settings_contract_handles_missing_groups():
    contract = ModernAdminExposureGainSettingsContract()
    context = contract.build_context(())

    assert_true(
        context['modern_admin_exposure_settings_group'] is None,
        'missing exposure group must remain a safe None fallback',
    )
    assert_true(
        context['modern_admin_gain_settings_group'] is None,
        'missing gain group must remain a safe None fallback',
    )
    assert_true(
        context['modern_admin_exposure_gain_settings_groups'] == (),
        'missing exposure/gain groups must produce an empty group tuple',
    )


def test_exposure_gain_settings_view_uses_hybrid_contract():
    views_text = (REPO_ROOT / 'indi_allsky/flask/views.py').read_text(encoding='utf-8')
    start = views_text.index('class ModernAdminExposureGainSettingsView')
    end = views_text.index('class ModernAdminAutoExposureGainSettingsView', start)
    exposure_gain_view = views_text[start:end]

    assert_true(
        'ModernAdminExposureGainSettingsContract' in exposure_gain_view,
        'exposure/gain settings view must use the Hybrid settings contract',
    )
    assert_true(
        'settings_contract' in exposure_gain_view,
        'exposure/gain settings view must expose the contract dependency explicitly',
    )
    assert_true(
        'EXPOSURE_GAIN_CONFIG_SECTIONS' not in exposure_gain_view,
        'exposure/gain static config sections must not remain inline on the view',
    )
    assert_true(
        'get_exposure_gain_overview_cards' not in exposure_gain_view,
        'exposure/gain overview formatting must not remain inline on the view',
    )


def test_auto_exposure_gain_settings_contract_preserves_context_shape():
    contract = ModernAdminAutoExposureGainSettingsContract()
    auto_exposure_group = {
        'group_id': 'auto_exposure',
        'label': 'Auto Exposure',
    }
    auto_gain_group = {
        'group_id': 'auto_gain',
        'label': 'Auto Gain',
    }

    context = contract.build_context((
        {'group_id': 'other'},
        auto_exposure_group,
        auto_gain_group,
    ))

    assert_true(
        context['modern_admin_auto_exposure_settings_group'] is auto_exposure_group,
        'auto exposure group must be selected from settings inventory groups',
    )
    assert_true(
        context['modern_admin_auto_gain_settings_group'] is auto_gain_group,
        'auto gain group must be selected from settings inventory groups',
    )
    assert_true(
        context['modern_admin_auto_exposure_gain_settings_groups'] == (auto_exposure_group, auto_gain_group),
        'auto exposure/gain grouped context shape changed',
    )
    assert_true(
        len(context['modern_admin_auto_exposure_gain_overview_cards']) == 6,
        'auto exposure/gain overview cards shape changed',
    )
    assert_true(
        len(context['modern_admin_auto_exposure_gain_config_sections']) == 5,
        'auto exposure/gain config sections shape changed',
    )
    assert_true(
        len(context['modern_admin_auto_exposure_gain_proposed_layout']) == 6,
        'auto exposure/gain proposed layout shape changed',
    )
    assert_true(
        context['modern_admin_auto_exposure_gain_overview_cards'][0]['current_status'] == 'not evaluated here',
        'auto exposure/gain overview current status changed',
    )
    assert_true(
        context['modern_admin_auto_exposure_gain_config_sections'][0]['key_count'] == 4,
        'target ADU config key count changed',
    )
    assert_true(
        context['modern_admin_auto_exposure_gain_config_sections'][2]['key_count'] == 5,
        'auto gain config key count changed',
    )
    assert_true(
        context['modern_admin_auto_exposure_gain_proposed_layout'][0]['note'] == 'read-only proposal',
        'auto exposure/gain layout note changed',
    )


def test_auto_exposure_gain_settings_contract_handles_missing_groups():
    contract = ModernAdminAutoExposureGainSettingsContract()
    context = contract.build_context(())

    assert_true(
        context['modern_admin_auto_exposure_settings_group'] is None,
        'missing auto exposure group must remain a safe None fallback',
    )
    assert_true(
        context['modern_admin_auto_gain_settings_group'] is None,
        'missing auto gain group must remain a safe None fallback',
    )
    assert_true(
        context['modern_admin_auto_exposure_gain_settings_groups'] == (),
        'missing auto exposure/gain groups must produce an empty group tuple',
    )


def test_auto_exposure_gain_settings_view_uses_hybrid_contract():
    views_text = (REPO_ROOT / 'indi_allsky/flask/views.py').read_text(encoding='utf-8')
    start = views_text.index('class ModernAdminAutoExposureGainSettingsView')
    end = views_text.index('class ModernAdminHybridAwbSettingsView', start)
    auto_exposure_gain_view = views_text[start:end]

    assert_true(
        'ModernAdminAutoExposureGainSettingsContract' in auto_exposure_gain_view,
        'auto exposure/gain settings view must use the Hybrid settings contract',
    )
    assert_true(
        'settings_contract' in auto_exposure_gain_view,
        'auto exposure/gain settings view must expose the contract dependency explicitly',
    )
    assert_true(
        'AUTO_EXPOSURE_GAIN_CONFIG_SECTIONS' not in auto_exposure_gain_view,
        'auto exposure/gain static config sections must not remain inline on the view',
    )
    assert_true(
        'get_auto_exposure_gain_overview_cards' not in auto_exposure_gain_view,
        'auto exposure/gain overview formatting must not remain inline on the view',
    )


def test_hybrid_awb_settings_contract_preserves_context_shape():
    contract = ModernAdminHybridAwbSettingsContract()
    hybrid_awb_group = {
        'group_id': 'hybrid_awb',
        'label': 'Hybrid AWB',
    }

    context = contract.build_context((
        {'group_id': 'other'},
        hybrid_awb_group,
    ))

    assert_true(
        context['modern_admin_hybrid_awb_settings_group'] is hybrid_awb_group,
        'hybrid AWB group must be selected from settings inventory groups',
    )
    assert_true(
        len(context['modern_admin_hybrid_awb_overview_cards']) == 6,
        'hybrid AWB overview cards shape changed',
    )
    assert_true(
        len(context['modern_admin_hybrid_awb_config_sections']) == 5,
        'hybrid AWB config sections shape changed',
    )
    assert_true(
        len(context['modern_admin_hybrid_awb_proposed_layout']) == 5,
        'hybrid AWB proposed layout shape changed',
    )
    assert_true(
        context['modern_admin_hybrid_awb_overview_cards'][0]['current_status'] == 'not evaluated here',
        'hybrid AWB overview current status changed',
    )
    assert_true(
        context['modern_admin_hybrid_awb_config_sections'][1]['key_count'] == 7,
        'libcamera AWB config key count changed',
    )
    assert_true(
        context['modern_admin_hybrid_awb_config_sections'][2]['key_count'] == 5,
        'post-process RGB config key count changed',
    )
    assert_true(
        context['modern_admin_hybrid_awb_proposed_layout'][0]['note'] == 'read-only proposal',
        'hybrid AWB layout note changed',
    )


def test_hybrid_awb_settings_contract_handles_missing_group():
    contract = ModernAdminHybridAwbSettingsContract()
    context = contract.build_context(())

    assert_true(
        context['modern_admin_hybrid_awb_settings_group'] is None,
        'missing hybrid AWB group must remain a safe None fallback',
    )


def test_hybrid_awb_settings_view_uses_hybrid_contract():
    views_text = (REPO_ROOT / 'indi_allsky/flask/views.py').read_text(encoding='utf-8')
    start = views_text.index('class ModernAdminHybridAwbSettingsView')
    end = views_text.index('class ModernAdminAcquisitionSaveSettingsView', start)
    hybrid_awb_view = views_text[start:end]

    assert_true(
        'ModernAdminHybridAwbSettingsContract' in hybrid_awb_view,
        'hybrid AWB settings view must use the Hybrid settings contract',
    )
    assert_true(
        'settings_contract' in hybrid_awb_view,
        'hybrid AWB settings view must expose the contract dependency explicitly',
    )
    assert_true(
        'HYBRID_AWB_CONFIG_SECTIONS' not in hybrid_awb_view,
        'hybrid AWB static config sections must not remain inline on the view',
    )
    assert_true(
        'get_hybrid_awb_overview_cards' not in hybrid_awb_view,
        'hybrid AWB overview formatting must not remain inline on the view',
    )


def test_acquisition_save_settings_contract_preserves_context_shape():
    contract = ModernAdminAcquisitionSaveSettingsContract()
    image_acquisition_group = {
        'group_id': 'image_acquisition',
        'label': 'Image Acquisition',
    }
    image_save_formats_group = {
        'group_id': 'image_save_formats',
        'label': 'Image Save Formats',
    }

    context = contract.build_context((
        {'group_id': 'other'},
        image_acquisition_group,
        image_save_formats_group,
    ))

    assert_true(
        context['modern_admin_image_acquisition_settings_group'] is image_acquisition_group,
        'image acquisition group must be selected from settings inventory groups',
    )
    assert_true(
        context['modern_admin_image_save_formats_settings_group'] is image_save_formats_group,
        'image save formats group must be selected from settings inventory groups',
    )
    assert_true(
        context['modern_admin_acquisition_save_settings_groups'] == (image_acquisition_group, image_save_formats_group),
        'acquisition/save grouped context shape changed',
    )
    assert_true(
        len(context['modern_admin_acquisition_save_overview_cards']) == 6,
        'acquisition/save overview cards shape changed',
    )
    assert_true(
        len(context['modern_admin_acquisition_save_config_sections']) == 5,
        'acquisition/save config sections shape changed',
    )
    assert_true(
        len(context['modern_admin_acquisition_save_proposed_layout']) == 6,
        'acquisition/save proposed layout shape changed',
    )
    assert_true(
        context['modern_admin_acquisition_save_overview_cards'][0]['current_status'] == 'not evaluated here',
        'acquisition/save overview current status changed',
    )
    assert_true(
        context['modern_admin_acquisition_save_config_sections'][3]['key_count'] == 5,
        'RAW/FITS/source behavior config key count changed',
    )
    assert_true(
        context['modern_admin_acquisition_save_config_sections'][4]['key_count'] == 4,
        'retention/storage impact config key count changed',
    )
    assert_true(
        context['modern_admin_acquisition_save_proposed_layout'][0]['note'] == 'read-only proposal',
        'acquisition/save layout note changed',
    )


def test_acquisition_save_settings_contract_handles_missing_groups():
    contract = ModernAdminAcquisitionSaveSettingsContract()
    context = contract.build_context(())

    assert_true(
        context['modern_admin_image_acquisition_settings_group'] is None,
        'missing image acquisition group must remain a safe None fallback',
    )
    assert_true(
        context['modern_admin_image_save_formats_settings_group'] is None,
        'missing image save formats group must remain a safe None fallback',
    )
    assert_true(
        context['modern_admin_acquisition_save_settings_groups'] == (),
        'missing acquisition/save groups must produce an empty group tuple',
    )


def test_acquisition_save_settings_view_uses_hybrid_contract():
    views_text = (REPO_ROOT / 'indi_allsky/flask/views.py').read_text(encoding='utf-8')
    start = views_text.index('class ModernAdminAcquisitionSaveSettingsView')
    end = views_text.index('class ModernAdminFitsSourceSettingsView', start)
    acquisition_save_view = views_text[start:end]

    assert_true(
        'ModernAdminAcquisitionSaveSettingsContract' in acquisition_save_view,
        'acquisition/save settings view must use the Hybrid settings contract',
    )
    assert_true(
        'settings_contract' in acquisition_save_view,
        'acquisition/save settings view must expose the contract dependency explicitly',
    )
    assert_true(
        'ACQUISITION_SAVE_CONFIG_SECTIONS' not in acquisition_save_view,
        'acquisition/save static config sections must not remain inline on the view',
    )
    assert_true(
        'get_acquisition_save_overview_cards' not in acquisition_save_view,
        'acquisition/save overview formatting must not remain inline on the view',
    )


def test_fits_source_settings_contract_preserves_context_shape():
    contract = ModernAdminFitsSourceSettingsContract()
    fits_source_group = {
        'group_id': 'fits_source_files',
        'label': 'FITS / Source Files',
    }

    context = contract.build_context((
        {'group_id': 'other'},
        fits_source_group,
    ))

    assert_true(
        context['modern_admin_fits_source_settings_group'] is fits_source_group,
        'FITS/source group must be selected from settings inventory groups',
    )
    assert_true(
        len(context['modern_admin_fits_source_overview_cards']) == 6,
        'FITS/source overview cards shape changed',
    )
    assert_true(
        len(context['modern_admin_fits_source_config_sections']) == 5,
        'FITS/source config sections shape changed',
    )
    assert_true(
        len(context['modern_admin_fits_source_proposed_layout']) == 6,
        'FITS/source proposed layout shape changed',
    )
    assert_true(
        context['modern_admin_fits_source_overview_cards'][0]['current_status'] == 'not evaluated here',
        'FITS/source overview current status changed',
    )
    assert_true(
        context['modern_admin_fits_source_config_sections'][0]['key_count'] == 4,
        'FITS persistence config key count changed',
    )
    assert_true(
        context['modern_admin_fits_source_config_sections'][4]['key_count'] == 3,
        'viewer/file safety config key count changed',
    )
    assert_true(
        context['modern_admin_fits_source_proposed_layout'][0]['note'] == 'read-only proposal',
        'FITS/source layout note changed',
    )


def test_fits_source_settings_contract_handles_missing_group():
    contract = ModernAdminFitsSourceSettingsContract()
    context = contract.build_context(())

    assert_true(
        context['modern_admin_fits_source_settings_group'] is None,
        'missing FITS/source group must remain a safe None fallback',
    )


def test_fits_source_settings_view_uses_hybrid_contract():
    views_text = (REPO_ROOT / 'indi_allsky/flask/views.py').read_text(encoding='utf-8')
    start = views_text.index('class ModernAdminFitsSourceSettingsView')
    end = views_text.index('class ModernAdminFullSettingsView', start)
    fits_source_view = views_text[start:end]

    assert_true(
        'ModernAdminFitsSourceSettingsContract' in fits_source_view,
        'FITS/source settings view must use the Hybrid settings contract',
    )
    assert_true(
        'settings_contract' in fits_source_view,
        'FITS/source settings view must expose the contract dependency explicitly',
    )
    assert_true(
        'FITS_SOURCE_CONFIG_SECTIONS' not in fits_source_view,
        'FITS/source static config sections must not remain inline on the view',
    )
    assert_true(
        'get_fits_source_overview_cards' not in fits_source_view,
        'FITS/source overview formatting must not remain inline on the view',
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


def test_single_group_settings_contracts_share_group_lookup_helper():
    import indi_allsky.modern_admin_settings_contracts as module

    source = inspect.getsource(module)
    single_group_contracts = (
        ModernAdminStorageSettingsContract,
        ModernAdminCameraProfileSettingsContract,
        ModernAdminCameraConnectionSettingsContract,
        ModernAdminHybridAwbSettingsContract,
        ModernAdminFitsSourceSettingsContract,
        ModernAdminNotificationsSettingsContract,
    )

    assert_true(
        source.count('def find_settings_group') == 1,
        'settings group lookup helper should have one shared implementation',
    )

    for contract_class in single_group_contracts:
        assert_true(
            issubclass(contract_class, ModernAdminSettingsContractBase),
            '{0:s} must inherit the shared settings contract base'.format(contract_class.__name__),
        )


def run_tests():
    test_migrated_settings_contracts_preserve_top_level_context_contracts()
    test_notifications_settings_contract_preserves_context_shape()
    test_notifications_settings_contract_handles_missing_group()
    test_notifications_settings_view_uses_hybrid_contract()
    test_storage_settings_contract_preserves_context_shape()
    test_storage_settings_contract_handles_missing_group()
    test_storage_settings_view_uses_hybrid_contract()
    test_camera_profile_settings_contract_preserves_context_shape()
    test_camera_profile_settings_contract_handles_missing_group()
    test_camera_profile_settings_view_uses_hybrid_contract()
    test_camera_connection_settings_contract_preserves_context_shape()
    test_camera_connection_settings_contract_handles_missing_group()
    test_camera_connection_settings_view_uses_hybrid_contract()
    test_exposure_gain_settings_contract_preserves_context_shape()
    test_exposure_gain_settings_contract_handles_missing_groups()
    test_exposure_gain_settings_view_uses_hybrid_contract()
    test_auto_exposure_gain_settings_contract_preserves_context_shape()
    test_auto_exposure_gain_settings_contract_handles_missing_groups()
    test_auto_exposure_gain_settings_view_uses_hybrid_contract()
    test_hybrid_awb_settings_contract_preserves_context_shape()
    test_hybrid_awb_settings_contract_handles_missing_group()
    test_hybrid_awb_settings_view_uses_hybrid_contract()
    test_acquisition_save_settings_contract_preserves_context_shape()
    test_acquisition_save_settings_contract_handles_missing_groups()
    test_acquisition_save_settings_view_uses_hybrid_contract()
    test_fits_source_settings_contract_preserves_context_shape()
    test_fits_source_settings_contract_handles_missing_group()
    test_fits_source_settings_view_uses_hybrid_contract()
    test_settings_contract_module_has_no_flask_or_runtime_config_dependency()
    test_single_group_settings_contracts_share_group_lookup_helper()


if __name__ == '__main__':
    run_tests()
