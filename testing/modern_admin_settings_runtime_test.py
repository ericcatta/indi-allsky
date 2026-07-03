#!/usr/bin/env python3

import inspect
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from indi_allsky.modern_admin_settings_runtime import ModernAdminSettingsRuntimeService


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


def test_modern_settings_views_use_runtime_service_for_config_revision_save():
    views_path = Path(__file__).resolve().parents[1] / 'indi_allsky' / 'flask' / 'views.py'
    source = views_path.read_text()
    start = source.index('class ModernAdminSettingsInventoryView')
    end = source.index('bp_allsky.add_url_rule')
    modern_settings_source = source[start:end]

    assert 'from ..config import IndiAllSkyConfig\n' not in modern_settings_source
    assert 'config_obj = IndiAllSkyConfig()' not in modern_settings_source
    assert modern_settings_source.count('save_settings_config_revision(') >= 7


if __name__ == '__main__':
    test_settings_runtime_service_saves_config_revision_through_adapter()
    test_settings_runtime_service_propagates_adapter_exception()
    test_settings_runtime_service_has_no_flask_or_db_dependency()
    test_modern_settings_views_use_runtime_service_for_config_revision_save()
    print('Modern admin settings runtime tests passed')
