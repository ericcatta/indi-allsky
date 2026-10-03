"""Hybrid storage protection settings; the worker reloads this global policy."""
from copy import deepcopy
from pathlib import Path
from flask import abort, current_app, redirect, request, url_for
from flask_login import current_user
from . import db
from ..exceptions import ConfigSaveException
from .storage_estimate import storage_forecast
from ..modern_admin_settings_runtime import ModernAdminSettingsRuntimeService
from ..storage_pressure import StoragePressureOptions
from ..archive_policy import DEFAULTS, validate_archive_config
from ..archive_volume import verify_archive, current_volume_uuid, ArchiveUnavailable


class StorageSettingsMixin:
    methods = ['GET', 'POST']
    page_title = 'Storage Protection'
    modern_admin_active_endpoint = 'indi_allsky.modern_admin_settings_view'

    def dispatch_request(self):
        error, status = None, 200
        archive_operation = request.form.get('operation') == 'archive'
        volume_operation = request.form.get('operation') == 'volume'
        archive_root = Path(current_app.config['INDI_ALLSKY_IMAGE_FOLDER']).resolve()
        volume_spec = self.indi_allsky_config.get('ARCHIVE_VOLUME')
        volume_error = None
        try:
            verify_archive(archive_root, volume_spec)
            volume_uuid = current_volume_uuid(archive_root)
        except (OSError, ValueError) as exc:
            volume_uuid = None
            volume_error = str(exc)
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
            elif not volume_operation:
                values = dict(ENABLE=request.form.get('enabled') == 'on',
                              MIN_FREE_GIB=request.form.get('minimum', ''),
                              TARGET_FREE_GIB=request.form.get('target', ''),
                              KEEP_DAYS=request.form.get('days', ''))
            if request.form.get('revision') != str(revision):
                error, status = 'Settings changed. Reload before saving.', 409
            else:
                try:
                    config = deepcopy(self.indi_allsky_config)
                    if volume_operation:
                        if request.form.get('volume_required') == 'on':
                            configured_root = Path(config.get('IMAGE_FOLDER') or archive_root).resolve()
                            if configured_root != archive_root or not volume_uuid:
                                raise ValueError('Apply the archive path with the installer and connect its disk first')
                            spec = dict(ROOT=str(archive_root), UUID=volume_uuid)
                            verify_archive(archive_root, spec, writable=True)
                            config['ARCHIVE_VOLUME'] = spec
                        else:
                            config['ARCHIVE_VOLUME'] = None
                    elif archive_operation:
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
                        config, username, 'Hybrid archive volume protection' if volume_operation else 'Hybrid archive formats' if archive_operation else 'Hybrid storage protection settings', expected_config_id=revision)
                    return redirect(url_for('indi_allsky.modern_admin_storage_protection_settings_view', saved='volume' if volume_operation else 'archive' if archive_operation else '1',
                        camera_id=request.args.get('camera_id', self.camera.id), profile_id=request.args.get('profile_id')), code=303)
                except ConfigSaveException as exc:
                    db.session.rollback()
                    error, status = str(exc), 409
                except (ValueError, TypeError, ArchiveUnavailable):
                    error, status = ('Connect the archive disk and apply its path with the installer before enabling protection.' if volume_operation else 'Choose a supported format for day and night.' if archive_operation else 'Use positive thresholds, a recovery target above the threshold and at least one whole day of retention.'), 400
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
                       archive_display_type=self.indi_allsky_config.get('IMAGE_FILE_TYPE', 'jpg').upper(),
                       archive_root=str(archive_root), volume_uuid=volume_uuid, volume_required=bool(volume_spec),
                       volume_error=volume_error, volume_saved=request.args.get('saved') == 'volume')
        return self.render_template(context), status
