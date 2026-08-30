#!/usr/bin/env python3

import inspect
import sys
from datetime import datetime
from datetime import timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from indi_allsky.modern_admin_settings_runtime import ModernAdminConfigRevisionPersistenceAdapter
from indi_allsky.modern_admin_settings_runtime import ModernAdminSettingsRuntimeService
from indi_allsky.modern_admin_settings_runtime import ModernAdminSettingsReloadCommandService
from indi_allsky.modern_admin_settings_runtime import ModernAdminSettingsRevisionMetadataService
from indi_allsky.modern_admin_settings_runtime import ModernAdminSettingsRestoreService
from indi_allsky.modern_admin_settings_runtime import ModernAdminSettingsRestoreValidationError


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


class FakeConfigModel:
    def __init__(self, **kwargs):
        self.values = kwargs


class FakeDbSession:
    def __init__(self):
        self.add_calls = []
        self.commit_calls = 0


    def add(self, entry):
        self.add_calls.append(entry)


    def commit(self):
        self.commit_calls += 1


class CallRecorder:
    def __init__(self):
        self.calls = 0


    def __call__(self):
        self.calls += 1


class ActionRecorder:
    def __init__(self):
        self.actions = []


    def __call__(self, action):
        self.actions.append(action)


class FakeUser:
    def __init__(self, user_id=1, username='admin'):
        self.id = user_id
        self.username = username


def test_config_revision_persistence_adapter_preserves_database_effect():
    db_session = FakeDbSession()
    created = datetime(2026, 8, 30, 12, 0, 0)
    config = {'CAMERA_INTERFACE': 'indi'}
    user = FakeUser(user_id=7, username='admin')
    adapter = ModernAdminConfigRevisionPersistenceAdapter(
        config_model=FakeConfigModel,
        db_session=db_session,
        config_level=4,
        clock=lambda: created,
    )

    result = adapter.save_revision(
        config=config,
        user_entry=user,
        note=123,
        encrypted=True,
    )

    assert result.values == {
        'data'      : config,
        'createDate': created,
        'level'     : '4',
        'user_id'   : 7,
        'note'      : '123',
        'encrypted' : True,
    }
    assert db_session.add_calls == [result]
    assert db_session.commit_calls == 1


def test_config_revision_persistence_adapter_uses_naive_utc_timestamp():
    adapter = ModernAdminConfigRevisionPersistenceAdapter(
        config_model=FakeConfigModel,
        db_session=FakeDbSession(),
        config_level='system',
    )

    created = adapter.utcnow()

    assert created.tzinfo is None
    utcnow = datetime.now(tz=timezone.utc).replace(tzinfo=None)
    assert abs((utcnow - created).total_seconds()) < 2


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


def test_settings_runtime_service_saves_full_config_through_adapter():
    adapter = FakeConfigAdapter()
    service = ModernAdminSettingsRuntimeService()
    config = {'CAMERA_INTERFACE': 'indi', 'OWNER': 'Hybrid'}

    result = service.save_full_config(
        config=config,
        username='admin',
        note='Full config save',
        config_adapter=adapter,
    )

    assert result == 'saved-config-row'
    assert adapter.config is config
    assert adapter.save_calls == [{
        'username': 'admin',
        'note': 'Full config save',
        'config': config,
    }]


def test_settings_runtime_service_has_no_flask_or_db_dependency():
    import indi_allsky.modern_admin_settings_runtime as module

    source = inspect.getsource(module)

    assert 'from flask' not in source
    assert 'import flask' not in source
    assert 'db.session' not in source


def test_classic_config_delegates_revision_persistence_to_hybrid_adapter():
    config_path = Path(__file__).resolve().parents[1] / 'indi_allsky' / 'config.py'
    source = config_path.read_text()
    start = source.index('    def _setConfigEntry(')
    end = source.index('    def _decrypt_passwords(', start)
    body = source[start:end]

    assert 'ModernAdminConfigRevisionPersistenceAdapter' in body
    assert '.save_revision(config, user_entry, note, encrypted)' in body
    assert 'IndiAllSkyDbConfigTable(' not in body
    assert 'db.session.add(' not in body
    assert 'db.session.commit()' not in body


def valid_restore_config():
    return {
        'INDI_SERVER': 'localhost',
        'CCD_CONFIG': {},
        'INDI_CONFIG_DEFAULTS': {},
    }


def test_settings_restore_service_validates_and_delegates_to_adapter():
    adapter = FakeConfigAdapter()
    config = valid_restore_config()
    service = ModernAdminSettingsRestoreService()

    result = service.restore_config(
        config=config,
        username='admin',
        config_adapter=adapter,
    )

    assert result == 'saved-config-row'
    assert adapter.config is config
    assert adapter.save_calls == [{
        'username': 'admin',
        'note': 'Manual config restore from upload',
        'config': config,
    }]


def test_settings_restore_service_rejects_invalid_target_before_save():
    adapter = FakeConfigAdapter()
    service = ModernAdminSettingsRestoreService()

    try:
        service.restore_config(
            config={'INDI_SERVER': 'localhost'},
            username='admin',
            config_adapter=adapter,
        )
    except ModernAdminSettingsRestoreValidationError as e:
        assert str(e) == 'Not a valid indi-allsky config'
    else:
        raise AssertionError('Invalid restore target was not rejected')

    assert adapter.config is None
    assert adapter.save_calls == []


def test_settings_restore_service_skips_post_restore_cleanup_by_default():
    flush_adapter = CallRecorder()
    reset_adapter = CallRecorder()
    service = ModernAdminSettingsRestoreService()

    result = service.post_restore_cleanup(
        flush_adapter=flush_adapter,
        reset_adapter=reset_adapter,
    )

    assert result == {
        'flush_configs': False,
        'reset_keys': False,
    }
    assert flush_adapter.calls == 0
    assert reset_adapter.calls == 0


def test_settings_restore_service_delegates_requested_post_restore_cleanup():
    flush_adapter = CallRecorder()
    reset_adapter = CallRecorder()
    service = ModernAdminSettingsRestoreService()

    result = service.post_restore_cleanup(
        flush_configs='y',
        reset_keys='y',
        flush_adapter=flush_adapter,
        reset_adapter=reset_adapter,
    )

    assert result == {
        'flush_configs': True,
        'reset_keys': True,
    }
    assert flush_adapter.calls == 1
    assert reset_adapter.calls == 1


def test_settings_restore_service_allows_partial_post_restore_cleanup():
    flush_adapter = CallRecorder()
    reset_adapter = CallRecorder()
    service = ModernAdminSettingsRestoreService()

    result = service.post_restore_cleanup(
        flush_configs='y',
        reset_keys=None,
        flush_adapter=flush_adapter,
        reset_adapter=reset_adapter,
    )

    assert result == {
        'flush_configs': True,
        'reset_keys': False,
    }
    assert flush_adapter.calls == 1
    assert reset_adapter.calls == 0


def test_settings_reload_command_service_defaults_to_noop_plan():
    status_adapter = CallRecorder()
    task_adapter = ActionRecorder()
    service = ModernAdminSettingsReloadCommandService()

    plan = service.execute_after_save(
        status_adapter=status_adapter,
        task_adapter=task_adapter,
    )

    assert plan == {
        'reload_requested': False,
        'task_action': None,
        'success_message': 'Saved new config',
    }
    assert status_adapter.calls == 0
    assert task_adapter.actions == []


def test_settings_reload_command_service_delegates_explicit_reload_request():
    status_adapter = CallRecorder()
    task_adapter = ActionRecorder()
    service = ModernAdminSettingsReloadCommandService()

    plan = service.execute_after_save(
        reload_requested='y',
        status_adapter=status_adapter,
        task_adapter=task_adapter,
    )

    assert plan == {
        'reload_requested': True,
        'task_action': 'reload',
        'success_message': 'Saved new config,  Reloading indi-allsky service.',
    }
    assert status_adapter.calls == 1
    assert task_adapter.actions == ['reload']


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


def test_ajax_config_restore_view_uses_restore_service_boundary():
    views_path = Path(__file__).resolve().parents[1] / 'indi_allsky' / 'flask' / 'views.py'
    source = views_path.read_text()
    start = source.index('class AjaxConfigRestoreView')
    end = source.index('class AjaxSelectCameraView')
    ajax_restore_source = source[start:end]

    assert 'ModernAdminSettingsRestoreService' in ajax_restore_source
    assert 'settings_restore_service().restore_config(' in ajax_restore_source
    assert 'settings_restore_service().post_restore_cleanup(' in ajax_restore_source
    assert 'self._indi_allsky_config_obj.save(' not in ajax_restore_source
    assert 'self._indi_allsky_config_obj.config = config_dict' not in ajax_restore_source
    assert 'if flush_configs:' not in ajax_restore_source
    assert 'if reset_keys:' not in ajax_restore_source


def test_ajax_config_view_uses_reload_command_boundary():
    views_path = Path(__file__).resolve().parents[1] / 'indi_allsky' / 'flask' / 'views.py'
    source = views_path.read_text()
    start = source.index('class AjaxConfigView')
    end = source.index('class AjaxSetTimeView')
    ajax_config_source = source[start:end]

    assert 'ModernAdminSettingsReloadCommandService' in ajax_config_source
    assert 'settings_reload_command_service().execute_after_save(' in ajax_config_source
    assert 'ModernAdminTaskEnqueueEffectAdapter' in ajax_config_source
    assert '.enqueue(' in ajax_config_source
    assert "if reload_on_save:" not in ajax_config_source
    assert "'Saved new config,  Reloading indi-allsky service.'" not in ajax_config_source


def test_ajax_config_view_uses_full_config_save_boundary():
    views_path = Path(__file__).resolve().parents[1] / 'indi_allsky' / 'flask' / 'views.py'
    source = views_path.read_text()
    start = source.index('class AjaxConfigView')
    end = source.index('class AjaxSetTimeView')
    ajax_config_source = source[start:end]

    assert 'ModernAdminSettingsRuntimeService' in ajax_config_source
    assert 'settings_runtime_service().save_full_config(' in ajax_config_source
    assert 'self._indi_allsky_config_obj.save(' not in ajax_config_source


if __name__ == '__main__':
    test_config_revision_persistence_adapter_preserves_database_effect()
    test_config_revision_persistence_adapter_uses_naive_utc_timestamp()
    test_settings_runtime_service_saves_config_revision_through_adapter()
    test_settings_runtime_service_propagates_adapter_exception()
    test_settings_runtime_service_saves_full_config_through_adapter()
    test_settings_runtime_service_has_no_flask_or_db_dependency()
    test_classic_config_delegates_revision_persistence_to_hybrid_adapter()
    test_settings_restore_service_validates_and_delegates_to_adapter()
    test_settings_restore_service_rejects_invalid_target_before_save()
    test_settings_restore_service_skips_post_restore_cleanup_by_default()
    test_settings_restore_service_delegates_requested_post_restore_cleanup()
    test_settings_restore_service_allows_partial_post_restore_cleanup()
    test_settings_reload_command_service_defaults_to_noop_plan()
    test_settings_reload_command_service_delegates_explicit_reload_request()
    test_settings_revision_history_context_formats_metadata_rows()
    test_settings_revision_restore_context_adds_restore_metadata_only()
    test_settings_revision_restore_detail_uses_injected_lookup()
    test_modern_settings_views_use_runtime_service_for_config_revision_save()
    test_modern_config_history_views_use_revision_metadata_service()
    test_ajax_config_restore_view_uses_restore_service_boundary()
    test_ajax_config_view_uses_reload_command_boundary()
    test_ajax_config_view_uses_full_config_save_boundary()
    print('Modern admin settings runtime tests passed')
