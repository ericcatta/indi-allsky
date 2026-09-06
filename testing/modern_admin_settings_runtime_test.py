#!/usr/bin/env python3

import inspect
import sys
from datetime import datetime
from datetime import timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from indi_allsky.modern_admin_settings_runtime import ModernAdminConfigRevisionPersistenceAdapter
from indi_allsky.modern_admin_settings_runtime import ModernAdminFullConfigPayloadPreparationService
from indi_allsky.modern_admin_settings_runtime import ModernAdminSettingsConfigValidationService
from indi_allsky.modern_admin_settings_runtime import ModernAdminSettingsCredentialDecryptionService
from indi_allsky.modern_admin_settings_runtime import ModernAdminSettingsCredentialEncryptionService
from indi_allsky.modern_admin_settings_runtime import ModernAdminSettingsRuntimeService
from indi_allsky.modern_admin_settings_runtime import ModernAdminSettingsReloadCommandService
from indi_allsky.modern_admin_settings_runtime import ModernAdminSettingsRevisionMetadataService
from indi_allsky.modern_admin_settings_runtime import ModernAdminSettingsRevisionRollbackService
from indi_allsky.modern_admin_settings_runtime import ModernAdminSettingsRestoreService
from indi_allsky.modern_admin_settings_runtime import ModernAdminSettingsRestoreValidationError
from indi_allsky.exceptions import ConfigSaveException


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


class FakeLogger:
    def __init__(self):
        self.errors = []
        self.warnings = []


    def error(self, message, *args):
        self.errors.append((message, args))


    def warning(self, message, *args):
        self.warnings.append((message, args))


class FakeCipher:
    def __init__(self, key):
        self.key = key
        self.decrypt_calls = []
        self.encrypt_calls = []


    def decrypt(self, value):
        self.decrypt_calls.append(value)
        prefix = b'encrypted:'
        if not value.startswith(prefix):
            raise ValueError('invalid ciphertext')
        return value[len(prefix):]


    def encrypt(self, value):
        self.encrypt_calls.append(value)
        return b'encrypted:' + value


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


def test_full_config_payload_preparation_preserves_structure_policy():
    service = ModernAdminFullConfigPayloadPreparationService()
    website = {'TITLE': 'Hybrid'}
    night = {'GAIN': 100}
    config = {
        'WEBSITE': website,
        'CCD_CONFIG': {
            'NIGHT': night,
            'MOONMODE': None,
            'DAY': '',
        },
        'FILETRANSFER': 'invalid-section',
    }

    result = service.prepare(config)

    assert result is config
    assert result['WEBSITE'] is website
    assert result['CCD_CONFIG']['NIGHT'] is night
    assert result['CCD_CONFIG']['MOONMODE'] == {}
    assert result['CCD_CONFIG']['DAY'] == {}
    assert result['FILETRANSFER'] == {}
    assert all(isinstance(result[section], dict) for section in service.DICT_SECTIONS)
    assert result['FITSHEADERS'] == [['', ''], ['', ''], ['', ''], ['', ''], ['', '']]


def test_full_config_payload_preparation_preserves_existing_fits_headers():
    service = ModernAdminFullConfigPayloadPreparationService()
    fits_headers = [['OBSERVER', 'Hybrid']]
    config = {
        'CCD_CONFIG': {},
        'FITSHEADERS': fits_headers,
    }

    result = service.prepare(config)

    assert result['FITSHEADERS'] is fits_headers


def test_ajax_full_config_parser_uses_hybrid_preparation_boundary():
    views_path = Path(__file__).resolve().parents[1] / 'indi_allsky' / 'flask' / 'views.py'
    source = views_path.read_text()
    start = source.index('class AjaxConfigView')
    end = source.index('class AjaxSetTimeView')
    ajax_config_source = source[start:end]

    assert 'ModernAdminFullConfigPayloadPreparationService' in ajax_config_source
    assert 'full_config_payload_preparation_service().prepare(self.indi_allsky_config)' in ajax_config_source
    assert 'leaf_list = (' not in ajax_config_source
    assert "self.indi_allsky_config['FITSHEADERS'] = [['', '']" not in ajax_config_source


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


def test_settings_config_validation_service_preserves_type_policy():
    service = ModernAdminSettingsConfigValidationService(
        base_config={
            'EXPOSURE': 1.5,
            'NAME': 'camera',
            'CAMERA': {'GAIN': 10, 'LABEL': 'primary'},
        },
    )

    assert service.validate({
        'EXPOSURE': 1,
        'NAME': 'updated',
        'CAMERA': {'GAIN': 12, 'LABEL': 'secondary'},
    }) is True

    try:
        service.validate({'CAMERA': {'GAIN': 12.5}})
    except ConfigSaveException as error:
        assert str(error) == 'Config key has wrong type: [CAMERA][GAIN]'
    else:
        raise AssertionError('Expected asymmetric legacy numeric validation')


def test_settings_config_validation_service_preserves_skip_and_unknown_policy():
    logger = FakeLogger()
    service = ModernAdminSettingsConfigValidationService(
        base_config={
            'INDI_CONFIG_DAY': {},
            'FILETRANSFER': {'LIBCURL_OPTIONS': {}},
        },
        logger=logger,
    )

    assert service.validate({
        'INDI_CONFIG_DAY': 'legacy-unvalidated-value',
        'FILETRANSFER': {'LIBCURL_OPTIONS': 'legacy-unvalidated-value'},
        'UNKNOWN': 'preserved',
        'UNKNOWN_GROUP': {'UNKNOWN_VALUE': 7},
    }) is True
    assert logger.errors == []
    assert logger.warnings == [
        ('Config key not found in base config: [%s]', ('UNKNOWN',)),
        ('Config key not found in base config: [%s][%s]', ('UNKNOWN_GROUP', 'UNKNOWN_VALUE')),
    ]


def test_settings_config_validation_service_rejects_wrong_nested_type():
    logger = FakeLogger()
    service = ModernAdminSettingsConfigValidationService(
        base_config={'CAMERA': {'LABEL': 'primary'}},
        logger=logger,
    )

    try:
        service.validate({'CAMERA': {'LABEL': []}})
    except ConfigSaveException as error:
        assert str(error) == 'Config key has wrong type: [CAMERA][LABEL]'
    else:
        raise AssertionError('Expected ConfigSaveException')

    assert logger.errors == [(
        'Config key has wrong type: [%s][%s] (%s vs %s)',
        ('CAMERA', 'LABEL', "<class 'str'>", "<class 'list'>"),
    )]


def test_classic_config_delegates_validation_to_hybrid_service():
    config_path = Path(__file__).resolve().parents[1] / 'indi_allsky' / 'config.py'
    source = config_path.read_text()
    start = source.index('    def _validateConfig(self):')
    end = source.index('    def _encryptPasswords(self):', start)
    validation_source = source[start:end]

    assert 'ModernAdminSettingsConfigValidationService' in validation_source
    assert ').validate(self.config)' in validation_source
    assert 'return ModernAdminSettingsConfigValidationService' not in validation_source
    assert 'valid_types = ' not in validation_source
    assert 'Config key has wrong type:' not in validation_source


def test_settings_credential_encryption_service_encrypts_all_fields():
    cipher_instances = []

    def cipher_factory(key):
        cipher = FakeCipher(key)
        cipher_instances.append(cipher)
        return cipher

    service = ModernAdminSettingsCredentialEncryptionService(
        password_key_adapter=lambda: 'test-password-key',
        cipher_factory=cipher_factory,
    )
    config = {
        'ENCRYPT_PASSWORDS': True,
        'FILETRANSFER': {'PASSWORD': 'filetransfer'},
        'S3UPLOAD': {'SECRET_KEY': 's3'},
        'MQTTPUBLISH': {'PASSWORD': 'mqtt-publish'},
        'SYNCAPI': {'APIKEY': 'sync'},
        'PYCURL_CAMERA': {'PASSWORD': 'pycurl'},
        'TEMP_SENSOR': {
            'OPENWEATHERMAP_APIKEY': 'openweather',
            'WUNDERGROUND_APIKEY': 'wunderground',
            'ASTROSPHERIC_APIKEY': 'astrospheric',
            'MQTT_PASSWORD': 'sensor-mqtt',
        },
        'DEVICE': {'MQTT_PASSWORD': 'device-mqtt'},
        'LIBCAMERA': {'MQTT_PASSWORD': 'libcamera-mqtt'},
        'ADSB': {'PASSWORD': 'adsb'},
        'IMAGE_OVERLAY': {'A_PASSWORD': 'overlay'},
    }
    expected_values = (
        ('FILETRANSFER', 'PASSWORD', 'PASSWORD_E', 'filetransfer'),
        ('S3UPLOAD', 'SECRET_KEY', 'SECRET_KEY_E', 's3'),
        ('MQTTPUBLISH', 'PASSWORD', 'PASSWORD_E', 'mqtt-publish'),
        ('SYNCAPI', 'APIKEY', 'APIKEY_E', 'sync'),
        ('PYCURL_CAMERA', 'PASSWORD', 'PASSWORD_E', 'pycurl'),
        ('TEMP_SENSOR', 'OPENWEATHERMAP_APIKEY', 'OPENWEATHERMAP_APIKEY_E', 'openweather'),
        ('TEMP_SENSOR', 'WUNDERGROUND_APIKEY', 'WUNDERGROUND_APIKEY_E', 'wunderground'),
        ('TEMP_SENSOR', 'ASTROSPHERIC_APIKEY', 'ASTROSPHERIC_APIKEY_E', 'astrospheric'),
        ('TEMP_SENSOR', 'MQTT_PASSWORD', 'MQTT_PASSWORD_E', 'sensor-mqtt'),
        ('DEVICE', 'MQTT_PASSWORD', 'MQTT_PASSWORD_E', 'device-mqtt'),
        ('LIBCAMERA', 'MQTT_PASSWORD', 'MQTT_PASSWORD_E', 'libcamera-mqtt'),
        ('ADSB', 'PASSWORD', 'PASSWORD_E', 'adsb'),
        ('IMAGE_OVERLAY', 'A_PASSWORD', 'A_PASSWORD_E', 'overlay'),
    )

    result, encrypted = service.encrypt_config(config)

    assert encrypted is True
    assert cipher_instances[0].key == b'test-password-key'
    assert cipher_instances[0].encrypt_calls == [
        value.encode() for _section, _plain_key, _encrypted_key, value in expected_values
    ]
    for section, plain_key, encrypted_key, value in expected_values:
        assert result[section][plain_key] == ''
        assert result[section][encrypted_key] == 'encrypted:' + value

    assert config['FILETRANSFER']['PASSWORD'] == ''


def test_settings_credential_encryption_service_preserves_disabled_fallbacks():
    password_key_calls = []
    service = ModernAdminSettingsCredentialEncryptionService(
        password_key_adapter=lambda: password_key_calls.append(True),
        cipher_factory=lambda _key: (_ for _ in ()).throw(AssertionError('cipher should not be created')),
    )
    config = {
        'ENCRYPT_PASSWORDS': False,
        'FILETRANSFER': {'PASSWORD': 123, 'PASSWORD_E': 'old-ciphertext'},
    }

    result, encrypted = service.encrypt_config(config)

    assert encrypted is False
    assert password_key_calls == []
    assert result['FILETRANSFER']['PASSWORD'] == '123'
    assert result['FILETRANSFER']['PASSWORD_E'] == ''
    assert result['TEMP_SENSOR']['OPENWEATHERMAP_APIKEY'] == ''
    assert result['TEMP_SENSOR']['OPENWEATHERMAP_APIKEY_E'] == ''
    assert result['IMAGE_OVERLAY']['A_PASSWORD'] == ''
    assert result['IMAGE_OVERLAY']['A_PASSWORD_E'] == ''


def test_classic_config_delegates_credential_encryption_to_hybrid_service():
    config_path = Path(__file__).resolve().parents[1] / 'indi_allsky' / 'config.py'
    source = config_path.read_text()
    start = source.index('    def _encryptPasswords(self):')
    end = source.index('    def _encryptPasswordsClassic(self):', start)
    encryption_source = source[start:end]

    assert 'ModernAdminSettingsCredentialEncryptionService' in encryption_source
    assert ').encrypt_config(self.config)' in encryption_source
    assert 'Fernet(' not in encryption_source
    assert "config['FILETRANSFER']['PASSWORD']" not in encryption_source


def test_settings_credential_decryption_service_decrypts_all_fields():
    cipher_instances = []

    def cipher_factory(key):
        cipher = FakeCipher(key)
        cipher_instances.append(cipher)
        return cipher

    service = ModernAdminSettingsCredentialDecryptionService(
        password_key_adapter=lambda: 'test-password-key',
        cipher_factory=cipher_factory,
    )
    expected_values = (
        ('FILETRANSFER', 'PASSWORD', 'PASSWORD_E', 'filetransfer'),
        ('S3UPLOAD', 'SECRET_KEY', 'SECRET_KEY_E', 's3'),
        ('MQTTPUBLISH', 'PASSWORD', 'PASSWORD_E', 'mqtt-publish'),
        ('SYNCAPI', 'APIKEY', 'APIKEY_E', 'sync'),
        ('PYCURL_CAMERA', 'PASSWORD', 'PASSWORD_E', 'pycurl'),
        ('TEMP_SENSOR', 'OPENWEATHERMAP_APIKEY', 'OPENWEATHERMAP_APIKEY_E', 'openweather'),
        ('TEMP_SENSOR', 'WUNDERGROUND_APIKEY', 'WUNDERGROUND_APIKEY_E', 'wunderground'),
        ('TEMP_SENSOR', 'ASTROSPHERIC_APIKEY', 'ASTROSPHERIC_APIKEY_E', 'astrospheric'),
        ('TEMP_SENSOR', 'MQTT_PASSWORD', 'MQTT_PASSWORD_E', 'sensor-mqtt'),
        ('DEVICE', 'MQTT_PASSWORD', 'MQTT_PASSWORD_E', 'device-mqtt'),
        ('LIBCAMERA', 'MQTT_PASSWORD', 'MQTT_PASSWORD_E', 'libcamera-mqtt'),
        ('ADSB', 'PASSWORD', 'PASSWORD_E', 'adsb'),
        ('IMAGE_OVERLAY', 'A_PASSWORD', 'A_PASSWORD_E', 'overlay'),
    )
    config = {'ENCRYPT_PASSWORDS': True}
    for section, plain_key, encrypted_key, value in expected_values:
        config.setdefault(section, {})[plain_key] = 'old-plaintext'
        config[section][encrypted_key] = 'encrypted:' + value

    result = service.decrypt_config(config)

    assert cipher_instances[0].key == b'test-password-key'
    assert cipher_instances[0].decrypt_calls == [
        ('encrypted:' + value).encode()
        for _section, _plain_key, _encrypted_key, value in expected_values
    ]
    for section, plain_key, encrypted_key, value in expected_values:
        assert result[section][plain_key] == value
        assert result[section][encrypted_key] == ''

    assert config['FILETRANSFER']['PASSWORD'] == 'filetransfer'


def test_settings_credential_decryption_service_preserves_encrypted_fallbacks():
    cipher_instances = []

    def cipher_factory(key):
        cipher = FakeCipher(key)
        cipher_instances.append(cipher)
        return cipher

    service = ModernAdminSettingsCredentialDecryptionService(
        password_key_adapter=lambda: 'test-password-key',
        cipher_factory=cipher_factory,
    )
    config = {
        'ENCRYPT_PASSWORDS': True,
        'FILETRANSFER': {'PASSWORD': 'plain-fallback', 'PASSWORD_E': ''},
        'IMAGE_OVERLAY': {
            'A_PASSWORD': 'current-key-value',
            'APASSWORD': 'legacy-fallback',
            'A_PASSWORD_E': '',
        },
    }

    result = service.decrypt_config(config)

    assert cipher_instances[0].decrypt_calls == []
    assert result['FILETRANSFER']['PASSWORD'] == 'plain-fallback'
    assert result['IMAGE_OVERLAY']['A_PASSWORD'] == 'legacy-fallback'
    assert result['IMAGE_OVERLAY']['A_PASSWORD_E'] == ''


def test_settings_credential_decryption_service_preserves_disabled_values():
    password_key_calls = []
    service = ModernAdminSettingsCredentialDecryptionService(
        password_key_adapter=lambda: password_key_calls.append(True),
        cipher_factory=lambda _key: (_ for _ in ()).throw(AssertionError('cipher should not be created')),
    )
    config = {
        'ENCRYPT_PASSWORDS': False,
        'FILETRANSFER': {'PASSWORD': 123, 'PASSWORD_E': 'ignored-ciphertext'},
    }

    result = service.decrypt_config(config)

    assert password_key_calls == []
    assert result['FILETRANSFER']['PASSWORD'] == 123
    assert result['FILETRANSFER']['PASSWORD_E'] == ''
    assert result['TEMP_SENSOR']['OPENWEATHERMAP_APIKEY'] == ''
    assert result['IMAGE_OVERLAY']['A_PASSWORD'] == ''


def test_settings_credential_decryption_service_propagates_cipher_error():
    service = ModernAdminSettingsCredentialDecryptionService(
        password_key_adapter=lambda: 'test-password-key',
        cipher_factory=FakeCipher,
    )

    try:
        service.decrypt_config({
            'ENCRYPT_PASSWORDS': True,
            'FILETRANSFER': {'PASSWORD_E': 'invalid-ciphertext'},
        })
    except ValueError as error:
        assert str(error) == 'invalid ciphertext'
    else:
        raise AssertionError('Expected cipher error to propagate')


def test_classic_config_delegates_credential_decryption_to_hybrid_service():
    config_path = Path(__file__).resolve().parents[1] / 'indi_allsky' / 'config.py'
    source = config_path.read_text()
    start = source.index('    def _decrypt_passwords(self):')
    end = source.index('    def _decrypt_passwordsClassic(self):', start)
    decryption_source = source[start:end]

    assert 'ModernAdminSettingsCredentialDecryptionService' in decryption_source
    assert ').decrypt_config(self.config)' in decryption_source
    assert 'Fernet(' not in decryption_source
    assert "config['FILETRANSFER']['PASSWORD']" not in decryption_source


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


def test_settings_revision_rollback_service_preserves_revert_effect():
    service = ModernAdminSettingsRevisionRollbackService()
    revision = type('Revision', (), {
        'id': 42,
        'data': {
            'CAMERA_INTERFACE': 'libcamera',
            'CCD_CONFIG': {'NIGHT': {'GAIN': 12}},
        },
    })()
    current_config = {
        'CAMERA_INTERFACE': 'indi',
        'UNCHANGED_FALLBACK': True,
    }
    save_calls = []

    def save_adapter(username, note):
        save_calls.append((username, note, dict(current_config)))
        return 'saved-rollback-row'

    result = service.apply_revision(
        revision=revision,
        current_config=current_config,
        save_adapter=save_adapter,
    )

    assert result == 'saved-rollback-row'
    assert current_config == {
        'CAMERA_INTERFACE': 'libcamera',
        'CCD_CONFIG': {'NIGHT': {'GAIN': 12}},
        'UNCHANGED_FALLBACK': True,
    }
    assert save_calls == [(
        'system',
        'Revert to config: 42',
        current_config,
    )]


def test_classic_config_revert_delegates_application_to_hybrid_service():
    config_path = Path(__file__).resolve().parents[1] / 'indi_allsky' / 'config.py'
    source = config_path.read_text()
    start = source.index('    def _revert(self, **kwargs):')
    end = source.index('    def dump(self, **kwargs):', start)
    revert_source = source[start:end]

    assert 'ModernAdminSettingsRevisionRollbackService' in revert_source
    assert '.apply_revision(' in revert_source
    assert 'self._config.update(revert_entry.data)' not in revert_source
    assert "self.save('system', 'Revert to config:" not in revert_source


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
        'Open a snapshot to inspect its metadata and download it. Use Config Restore to restore a configuration file.'
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
        'Snapshot metadata is shown below. Configuration values are omitted because they may contain secrets.'
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
    end = source.index('class ConfigDownloadView')
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
    test_full_config_payload_preparation_preserves_structure_policy()
    test_full_config_payload_preparation_preserves_existing_fits_headers()
    test_ajax_full_config_parser_uses_hybrid_preparation_boundary()
    test_config_revision_persistence_adapter_preserves_database_effect()
    test_settings_config_validation_service_preserves_type_policy()
    test_settings_config_validation_service_preserves_skip_and_unknown_policy()
    test_settings_config_validation_service_rejects_wrong_nested_type()
    test_classic_config_delegates_validation_to_hybrid_service()
    test_settings_credential_encryption_service_encrypts_all_fields()
    test_settings_credential_encryption_service_preserves_disabled_fallbacks()
    test_classic_config_delegates_credential_encryption_to_hybrid_service()
    test_settings_credential_decryption_service_decrypts_all_fields()
    test_settings_credential_decryption_service_preserves_encrypted_fallbacks()
    test_settings_credential_decryption_service_preserves_disabled_values()
    test_settings_credential_decryption_service_propagates_cipher_error()
    test_classic_config_delegates_credential_decryption_to_hybrid_service()
    test_config_revision_persistence_adapter_uses_naive_utc_timestamp()
    test_settings_revision_rollback_service_preserves_revert_effect()
    test_classic_config_revert_delegates_application_to_hybrid_service()
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
