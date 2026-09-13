"""Hybrid storage protection settings; the worker reloads this global policy."""
from copy import deepcopy
from flask import abort, current_app, redirect, request, url_for
from flask_login import current_user
from . import db
from .storage_estimate import storage_forecast
from ..modern_admin_settings_runtime import ModernAdminSettingsRuntimeService
from ..storage_pressure import StoragePressureOptions


class StorageSettingsMixin:
    methods = ['GET', 'POST']
    page_title = 'Storage Protection'
    modern_admin_active_endpoint = 'indi_allsky.modern_admin_settings_view'

    def dispatch_request(self):
        error, status = None, 200
        revision = self._indi_allsky_config_obj.config_id
        values = dict(ENABLE=True, MIN_FREE_GIB=5, TARGET_FREE_GIB=8, KEEP_DAYS=3)
        configured = self.indi_allsky_config.get('STORAGE_PRESSURE', {})
        if isinstance(configured, dict):
            values.update(configured)
        if request.method == 'POST':
            if not current_app.config['LOGIN_DISABLED'] and not current_user.is_admin:
                abort(403)
            values = dict(ENABLE=request.form.get('enabled') == 'on',
                          MIN_FREE_GIB=request.form.get('minimum', ''),
                          TARGET_FREE_GIB=request.form.get('target', ''),
                          KEEP_DAYS=request.form.get('days', ''))
            if request.form.get('revision') != str(revision):
                error, status = 'Settings changed. Reload before saving.', 409
            else:
                try:
                    parsed = dict(values, KEEP_DAYS=int(values['KEEP_DAYS']))
                    options = StoragePressureOptions.from_config({'STORAGE_PRESSURE': parsed})
                    config = deepcopy(self.indi_allsky_config)
                    config['STORAGE_PRESSURE'] = dict(ENABLE=options.enabled,
                        MIN_FREE_GIB=options.minimum_free_gib, TARGET_FREE_GIB=options.target_free_gib,
                        KEEP_DAYS=options.keep_days)
                    username = 'system' if current_app.config['LOGIN_DISABLED'] else current_user.username
                    ModernAdminSettingsRuntimeService().save_config_revision(
                        config, username, 'Hybrid storage protection settings')
                    return redirect(url_for('indi_allsky.modern_admin_storage_protection_settings_view', saved='1'), code=303)
                except (ValueError, TypeError):
                    error, status = 'Use positive thresholds, a recovery target above the threshold and at least one whole day of retention.', 400
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
                       storage_saved=request.args.get('saved') == '1')
        return self.render_template(context), status
