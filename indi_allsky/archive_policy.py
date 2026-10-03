"""Day/night archive choices; scientific acquisition and display remain separate."""
from dataclasses import dataclass

MODES = ('legacy', 'processed', 'fits', 'both')
DEFAULTS = {'NIGHT': 'fits', 'DAY': 'processed'}


def validate_archive_config(values):
    if not isinstance(values, dict) or set(values) != {'NIGHT', 'DAY'}:
        raise ValueError('Choose an archive format for day and night')
    if any(value not in MODES for value in values.values()):
        raise ValueError('Unsupported archive format')
    return dict(values)


@dataclass(frozen=True)
class ArchivePolicy:
    mode: str

    @classmethod
    def from_config(cls, config, night):
        values = config.get('IMAGE_ARCHIVE')
        # Existing installations keep their explicit output settings until the
        # new format settings are saved. The form defaults to FITS night/JPEG day.
        if values is None:
            return cls('legacy')
        values = validate_archive_config(values)
        return cls(values['NIGHT' if night else 'DAY'])

    def save_fits(self, config, images_only):
        if self.mode == 'legacy':
            return not images_only and bool(config.get('IMAGE_SAVE_FITS'))
        return self.mode in ('fits', 'both') and not config.get('FOCUS_MODE', False)

    def save_raw(self, config, images_only):
        return self.mode == 'legacy' and not images_only and bool(config.get('IMAGE_EXPORT_RAW'))

    @property
    def every_frame(self):
        return self.mode in ('fits', 'both')


def retain_scientific_only(entry, source_result, recipe, session, models):
    """Publish the dependency before unlinking the redundant display file.

    A failed/missing scientific publication leaves the ordinary image untouched.
    Filesystem failure restores the original record; failure to restore propagates.
    """
    from pathlib import Path
    if not source_result or not recipe:
        return False
    source = session.get(models.IndiAllSkyDbFitsImageTable, source_result['db_id'])
    if (source is None or source.camera_id != entry.camera_id
            or source.createDate != entry.createDate
            or (source.data or {}).get('render_source') != recipe
            or not source.getFilesystemPath().is_file()):
        return False
    path = Path(entry.getFilesystemPath())
    original_data, original_size = entry.data, entry.fileSize
    entry.data = dict(original_data or {}, storage_format='fits', source_fits_id=source.id)
    entry.fileSize = 0
    try:
        session.commit()
        path.unlink(missing_ok=True)
    except Exception:
        session.rollback()
        entry.data, entry.fileSize = original_data, original_size
        session.commit()
        return False
    return True
