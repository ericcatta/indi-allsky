"""Hybrid storage protection settings; the worker reloads this global policy."""
from copy import deepcopy
from flask import abort, current_app, redirect, request, url_for
from flask_login import current_user
from . import db
from ..exceptions import ConfigSaveException
from .storage_estimate import storage_forecast
from ..modern_admin_settings_runtime import ModernAdminSettingsRuntimeService
from ..storage_pressure import StoragePressureOptions
from ..archive_policy import DEFAULTS, validate_archive_config


class StorageSettingsMixin:
    methods = ['GET', 'POST']
    page_title = 'Storage Protection'
    modern_admin_active_endpoint = 'indi_allsky.modern_admin_settings_view'

    def dispatch_request(self):
        error, status = None, 200
        archive_operation = request.form.get('operation') == 'archive'
        archive_configured = 'IMAGE_ARCHIVE' in self.indi_allsky_config
        archive_values = dict(self.indi_allsky_config.get('IMAGE_ARCHIVE') or DEFAULTS)
        archive_compressed = self.indi_allsky_config.get('IMAGE_SAVE_FITS_COMPRESSED', False) if archive_configured else True
        revision = self._indi_allsky_config_obj.config_id
        values = dict(ENABLE=True, MIN_FREE_GIB=5, TARGET_FREE_GIB=8, KEEP_DAYS=3)
        configured = self.indi_allsky_config.get('STORAGE_PRESSURE', {})
        if isinstance(configured, dict):
            values.update(configured)
        if request.method == 'POST':
            if not current_app.config['LOGIN_DISABLED'] and not current_user.is_admin:
                abort(403)
            if archive_operation:
                archive_values = dict(NIGHT=request.form.get('archive_night'), DAY=request.form.get('archive_day'))
                archive_compressed = request.form.get('archive_compressed') == 'on'
            else:
                values = dict(ENABLE=request.form.get('enabled') == 'on',
                              MIN_FREE_GIB=request.form.get('minimum', ''),
                              TARGET_FREE_GIB=request.form.get('target', ''),
                              KEEP_DAYS=request.form.get('days', ''))
            if request.form.get('revision') != str(revision):
                error, status = 'Settings changed. Reload before saving.', 409
            else:
                try:
                    config = deepcopy(self.indi_allsky_config)
                    if archive_operation:
                        config['IMAGE_ARCHIVE'] = validate_archive_config(archive_values)
                        config['IMAGE_SAVE_FITS_COMPRESSED'] = archive_compressed
                    else:
                        parsed = dict(values, KEEP_DAYS=int(values['KEEP_DAYS']))
                        options = StoragePressureOptions.from_config({'STORAGE_PRESSURE': parsed})
                        config['STORAGE_PRESSURE'] = dict(ENABLE=options.enabled,
                            MIN_FREE_GIB=options.minimum_free_gib, TARGET_FREE_GIB=options.target_free_gib,
                            KEEP_DAYS=options.keep_days)
                    username = 'system' if current_app.config['LOGIN_DISABLED'] else current_user.username
                    ModernAdminSettingsRuntimeService().save_config_revision(
                        config, username, 'Hybrid archive formats' if archive_operation else 'Hybrid storage protection settings', expected_config_id=revision)
                    return redirect(url_for('indi_allsky.modern_admin_storage_protection_settings_view', saved='archive' if archive_operation else '1',
                        camera_id=request.args.get('camera_id', self.camera.id), profile_id=request.args.get('profile_id')), code=303)
                except ConfigSaveException as exc:
                    db.session.rollback()
                    error, status = str(exc), 409
                except (ValueError, TypeError):
                    error, status = ('Choose a supported format for day and night.' if archive_operation else 'Use positive thresholds, a recovery target above the threshold and at least one whole day of retention.'), 400
                except Exception:
                    db.session.rollback()
                    current_app.logger.exception('Unable to save storage protection settings')
                    error, status = 'Save could not be confirmed. Check configuration history before retrying.', 500
        try:
            forecast = storage_forecast(self.indi_allsky_config, revision,
                                        current_app.config['INDI_ALLSKY_IMAGE_FOLDER'])
        except Exception:
            db.session.rollback()
            current_app.logger.exception('Storage estimate unavailable')
            forecast = {'status': 'unavailable', 'reason': 'Storage information is temporarily unavailable. Check service logs.'}
        context = self.get_context()
        context.update(storage_forecast=forecast, storage_values=values, storage_revision=revision, storage_error=error,
                       storage_saved=request.args.get('saved') == '1',
                       archive_values=archive_values, archive_configured=archive_configured,
                       archive_compressed=archive_compressed, archive_saved=request.args.get('saved') == 'archive',
                       archive_display_type=self.indi_allsky_config.get('IMAGE_FILE_TYPE', 'jpg').upper())
        return self.render_template(context), status
