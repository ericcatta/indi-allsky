"""Hybrid timelapse settings, independent of Classic view implementations."""
from copy import deepcopy

from flask import abort, current_app, redirect, request, url_for
from flask_login import current_user

from . import db
from ..modern_admin_settings_runtime import ModernAdminSettingsRuntimeService
from ..timelapse_options import deflicker_options


class TimelapseSettingsMixin:
    methods = ['GET', 'POST']
    page_title = 'Timelapse Settings'
    modern_admin_active_endpoint = 'indi_allsky.modern_admin_settings_view'

    def dispatch_request(self):
        error = None
        status = 200
        enabled, window = deflicker_options(self.indi_allsky_config)
        revision = self._indi_allsky_config_obj.config_id
        if request.method == 'POST':
            if not current_app.config['LOGIN_DISABLED'] and not current_user.is_admin:
                abort(403)
            enabled = request.form.get('deflicker') == 'on'
            try:
                window = int(request.form.get('window', ''))
                if request.form.get('revision') != str(revision):
                    error = 'Settings changed since this page was opened. Reload before saving.'
                    status = 409
                else:
                    config = deepcopy(self.indi_allsky_config)
                    config.setdefault('TIMELAPSE', {}).update(
                        DEFLICKER=enabled, DEFLICKER_WINDOW=window)
                    deflicker_options(config)
                    username = 'system' if current_app.config['LOGIN_DISABLED'] else current_user.username
                    ModernAdminSettingsRuntimeService().save_config_revision(
                        config, username, 'Hybrid timelapse settings')
                    return redirect(url_for('indi_allsky.modern_admin_timelapse_settings_view', saved='1'), code=303)
            except (ValueError, TypeError):
                error = 'Choose a smoothing window of 3, 5 or 9 frames.'
                status = 400
            except Exception:
                db.session.rollback()
                current_app.logger.exception('Unable to save timelapse settings')
                error = 'The save could not be confirmed. Check configuration history before retrying.'
                status = 500
        context = self.get_context()
        context.update(timelapse_deflicker=enabled, timelapse_window=window,
                       timelapse_revision=revision, timelapse_error=error,
                       timelapse_saved=request.args.get('saved') == '1')
        return self.render_template(context), status
