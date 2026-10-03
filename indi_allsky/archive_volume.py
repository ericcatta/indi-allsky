"""Pin an archive to its filesystem UUID; never treat a missing disk as empty."""
import errno
import os
from pathlib import Path
import re
import stat


class ArchiveUnavailable(OSError):
    def __init__(self, message):
        super().__init__(errno.ENODEV, message)


def validate_volume_spec(spec):
    if spec is None:
        return None
    if (not isinstance(spec, dict) or set(spec) != {'ROOT', 'UUID'}
            or not isinstance(spec['ROOT'], str) or not Path(spec['ROOT']).is_absolute()
            or not isinstance(spec['UUID'], str)
            or not re.fullmatch(r'[A-Za-z0-9-]{1,80}', spec['UUID'])):
        raise ValueError('Archive protection requires an absolute directory and filesystem UUID')
    return spec


def device_identity(uuid):
    device = Path('/dev/disk/by-uuid') / uuid
    info = device.stat()
    if not stat.S_ISBLK(info.st_mode):
        raise ArchiveUnavailable('The configured archive UUID is not a block device')
    return info.st_rdev


def verify_archive(root, spec, *, writable=False):
    if validate_volume_spec(spec) is None:
        return
    root = Path(root).resolve()
    if root != Path(spec['ROOT']).resolve():
        raise ArchiveUnavailable('Archive paths disagree. Apply the storage configuration before using media.')
    try:
        if root.stat().st_dev != device_identity(spec['UUID']):
            raise ArchiveUnavailable('The configured archive disk is not mounted at its directory')
        if writable and os.statvfs(root).f_flag & os.ST_RDONLY:
            raise ArchiveUnavailable('The archive disk is read-only')
    except OSError as error:
        if isinstance(error, ArchiveUnavailable):
            raise
        raise ArchiveUnavailable('The configured archive disk is unavailable') from error


def current_volume_uuid(root):
    device = Path(root).stat().st_dev
    for candidate in sorted(Path('/dev/disk/by-uuid').glob('*')):
        try:
            if device_identity(candidate.name) == device:
                return candidate.name
        except OSError:
            continue
    return None


def verify_app_archive(*, writable=False):
    from flask import current_app, g
    from .flask.models import IndiAllSkyDbConfigTable
    if not hasattr(g, '_hybrid_archive_volume'):
        latest = IndiAllSkyDbConfigTable.query.order_by(IndiAllSkyDbConfigTable.id.desc()).first()
        g._hybrid_archive_volume = (latest.data or {}).get('ARCHIVE_VOLUME') if latest else None
    verify_archive(current_app.config['INDI_ALLSKY_IMAGE_FOLDER'],
                   g._hybrid_archive_volume, writable=writable)
