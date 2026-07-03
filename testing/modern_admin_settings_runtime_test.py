#!/usr/bin/env python3

import inspect
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from indi_allsky.modern_admin_settings_runtime import ModernAdminSettingsRuntimeService
from indi_allsky.modern_admin_settings_runtime import ModernAdminSettingsRevisionMetadataService


class FakeConfigAdapter:
    def __init__(self):
        self.config = None
        self.save_calls = []


    def save(self, username, note):
        self.save_calls.append({
            'username': username,
            'note': note,
            'config': self.config,
        })
        return 'saved-config-row'


class FakeUser:
    def __init__(self, user_id=1, username='admin'):
        self.id = user_id
        self.username = username


class FakeConfigRevision:
    def __init__(self, revision_id, created, data=None, level='system', encrypted=False, note='Saved config', user=None):
        self.id = revision_id
        self.createDate = created
        self.data = data
        self.level = level
        self.encrypted = encrypted
        self.note = note
        self.user = user


class FakeField:
    def __eq__(self, value):
        return ('eq', value)


class FakeCreatedField:
    def desc(self):
        return 'created-desc'


class FakeRevisionQuery:
    def __init__(self, rows):
        self.rows = list(rows)
        self.order_by_calls = []
        self.limit_calls = []
        self.filter_calls = []


    def order_by(self, expression):
        self.order_by_calls.append(expression)
        return self


    def limit(self, limit):
        self.limit_calls.append(limit)
        return self


    def filter(self, expression):
        self.filter_calls.append(expression)
        return self


    def one(self):
        if not self.rows:
            raise LookupError('not found')
        return self.rows[0]


    def __iter__(self):
        return iter(self.rows)


def test_settings_runtime_service_saves_config_revision_through_adapter():
    adapter = FakeConfigAdapter()
    service = ModernAdminSettingsRuntimeService(config_adapter_factory=lambda: adapter)
    config = {'CAMERA_INTERFACE': 'indi'}

    result = service.save_config_revision(
        config=config,
        username='admin',
        note='Modern Admin test save',
    )

    assert result == 'saved-config-row'
    assert adapter.config is config
    assert adapter.save_calls == [{
        'username': 'admin',
        'note': 'Modern Admin test save',
        'config': config,
    }]


def test_settings_runtime_service_propagates_adapter_exception():
    class FailingConfigAdapter(FakeConfigAdapter):
        def save(self, username, note):
            raise RuntimeError('save failed')

    service = ModernAdminSettingsRuntimeService(config_adapter_factory=FailingConfigAdapter)

    try:
        service.save_config_revision({}, 'admin', 'note')
    except RuntimeError as e:
        assert str(e) == 'save failed'
    else:
        raise AssertionError('Adapter exception was not propagated')


def test_settings_runtime_service_has_no_flask_or_db_dependency():
    import indi_allsky.modern_admin_settings_runtime as module

    source = inspect.getsource(module)

    assert 'from flask' not in source
    assert 'import flask' not in source
    assert 'db.session' not in source


def test_settings_revision_history_context_formats_metadata_rows():
    revision = FakeConfigRevision(
        revision_id=7,
        created='2026-07-03 09:10:11',
        data={'A': 1, 'B': 2},
        level='user',
        encrypted=True,
        note='Modern save',
        user=FakeUser(user_id=3, username='eric'),
    )
    query = FakeRevisionQuery([revision])
    service = ModernAdminSettingsRevisionMetadataService(
        query=query,
        id_field=FakeField(),
        created_field=FakeCreatedField(),
    )

    context = service.history_context(limit=25)

    assert query.order_by_calls == ['created-desc']
    assert query.limit_calls == [25]
    assert context['modern_admin_config_history_count'] == 1
    assert context['modern_admin_config_history_rows'] == [{
        'id'        : 7,
        'created'   : '2026-07-03 09:10:11',
        'user'      : 'eric',
        'user_id'   : 3,
        'level'     : 'user',
        'encrypted' : 'Yes',
        'note'      : 'Modern save',
        'summary'   : 'Keys: 2',
        'data_size' : '0.0 KB',
    }]
    assert context['modern_admin_config_history_encrypted_count'] == 1
    assert context['modern_admin_config_history_levels'] == ['user']
    assert context['modern_admin_config_history_encrypted_states'] == ['Yes']


def test_settings_revision_restore_context_adds_restore_metadata_only():
    revisions = [
        FakeConfigRevision(8, 'now', data={'A': 1}, encrypted=False, user=None),
        FakeConfigRevision(9, 'later', data={}, encrypted=True, user=FakeUser()),
    ]
    service = ModernAdminSettingsRevisionMetadataService(
        query=FakeRevisionQuery(revisions),
        created_field=FakeCreatedField(),
    )

    context = service.restore_context(limit=10)

    assert context['modern_admin_config_restore_count'] == 2
    assert context['modern_admin_config_restore_likely_count'] == 1
    assert context['modern_admin_config_restore_encrypted_count'] == 1
    assert context['modern_admin_config_restore_rows'][0]['restore_state'] == 'Likely restore candidate'
    assert context['modern_admin_config_restore_rows'][0]['user'] == 'Deleted user'
    assert context['modern_admin_config_restore_rows'][1]['restore_state'] == 'Unavailable'
    assert context['modern_admin_config_restore_warning'] == (
        'Read-only inspection only. Actual restore flow remains in Classic UI.'
    )


def test_settings_revision_restore_detail_uses_injected_lookup():
    revision = FakeConfigRevision(10, 'created', data={'A': 1}, user=FakeUser())
    query = FakeRevisionQuery([revision])
    service = ModernAdminSettingsRevisionMetadataService(
        query=query,
        id_field=FakeField(),
    )

    context = service.restore_detail_context(10)

    assert query.filter_calls == [('eq', 10)]
    assert context['modern_admin_config_restore_detail']['id'] == 10
    assert context['modern_admin_config_restore_detail']['restore_state'] == 'Likely restore candidate'
    assert context['modern_admin_config_restore_warning'] == (
        'Read-only metadata inspection only. Raw config payload and restore actions are intentionally hidden.'
    )


def test_modern_settings_views_use_runtime_service_for_config_revision_save():
    views_path = Path(__file__).resolve().parents[1] / 'indi_allsky' / 'flask' / 'views.py'
    source = views_path.read_text()
    start = source.index('class ModernAdminSettingsInventoryView')
    end = source.index('bp_allsky.add_url_rule')
    modern_settings_source = source[start:end]

    assert 'from ..config import IndiAllSkyConfig\n' not in modern_settings_source
    assert 'config_obj = IndiAllSkyConfig()' not in modern_settings_source
    assert modern_settings_source.count('save_settings_config_revision(') >= 7


def test_modern_config_history_views_use_revision_metadata_service():
    views_path = Path(__file__).resolve().parents[1] / 'indi_allsky' / 'flask' / 'views.py'
    source = views_path.read_text()
    start = source.index('class ModernAdminConfigRevisionMetadataMixin')
    end = source.index('class ConfigListView')
    modern_history_source = source[start:end]

    assert 'ModernAdminSettingsRevisionMetadataService' in modern_history_source
    assert '.order_by(IndiAllSkyDbConfigTable.createDate.desc())' not in modern_history_source
    assert 'summarize_config_data' not in modern_history_source
    assert 'format_config_datetime' not in modern_history_source


if __name__ == '__main__':
    test_settings_runtime_service_saves_config_revision_through_adapter()
    test_settings_runtime_service_propagates_adapter_exception()
    test_settings_runtime_service_has_no_flask_or_db_dependency()
    test_settings_revision_history_context_formats_metadata_rows()
    test_settings_revision_restore_context_adds_restore_metadata_only()
    test_settings_revision_restore_detail_uses_injected_lookup()
    test_modern_settings_views_use_runtime_service_for_config_revision_save()
    test_modern_config_history_views_use_revision_metadata_service()
    print('Modern admin settings runtime tests passed')
