"""Restore an internal Settings snapshot without exporting its secrets."""
from cryptography.fernet import InvalidToken
from flask import abort, current_app, jsonify, request
from flask_login import current_user, login_required
from .base_views import BaseView
from .models import IndiAllSkyDbConfigTable
from ..exceptions import ConfigSaveException
from ..modern_admin_settings_runtime import (
    ModernAdminSettingsRestoreService, ModernAdminSettingsRestoreValidationError,
)


class ModernAdminSnapshotRestoreView(BaseView):
    decorators = [login_required]
    methods = ['POST']

    def dispatch_request(self, config_id):
        if not current_user.is_admin:
            abort(403)
        if request.form.get('CONFIRM_RESTORE') != 'yes':
            return jsonify(form_global=['Confirm restoration of this whole configuration.']), 400
        latest = IndiAllSkyDbConfigTable.query.order_by(IndiAllSkyDbConfigTable.id.desc()).first()
        if latest is None or request.form.get('EXPECTED_CONFIG_ID') != str(latest.id):
            return jsonify(form_global=['Configuration changed. Reload this page and review before restoring.']), 409
        snapshot = IndiAllSkyDbConfigTable.query.filter_by(id=config_id).first_or_404()
        try:
            restored = ModernAdminSettingsRestoreService().restore_snapshot(
                snapshot, current_user.username, self._indi_allsky_config_obj,
                password_key_adapter=lambda: current_app.config['PASSWORD_KEY'],
            )
        except (ModernAdminSettingsRestoreValidationError, ConfigSaveException, InvalidToken, KeyError, ValueError):
            return jsonify(form_global=['Snapshot could not be restored. Check its format and encryption key.']), 400
        return jsonify({'success-message': 'Restored snapshot {0} as revision {1}. Capture was not restarted.'.format(config_id, restored.id)})
