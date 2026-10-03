"""Resolve archive dependencies without rendering or deleting their sources."""
import errno


def source_identity(data):
    data = data or {}
    if data.get('storage_format') != 'fits':
        return None
    identity = data.get('source_fits_id')
    recipe = data.get('render_source')
    basis = recipe.get('basis') if isinstance(recipe, dict) else None
    if identity is None and isinstance(basis, dict):
        identity = basis.get('source_id')
    if isinstance(identity, bool) or not isinstance(identity, int) or not 0 < identity < 2**63:
        raise ValueError('Invalid scientific source reference')
    return identity


def image_source(entry, session, models):
    if not isinstance(entry, models.IndiAllSkyDbImageTable):
        return None
    identity = source_identity(entry.data)
    if identity is None:
        return None
    source = session.get(models.IndiAllSkyDbFitsImageTable, identity)
    if (source is None or source.camera_id != entry.camera_id
            or source.createDate != entry.createDate):
        raise ValueError('The image scientific source is missing or mismatched')
    return source


def source_dependents(source, session, models):
    if not isinstance(source, models.IndiAllSkyDbFitsImageTable):
        return []
    table = models.IndiAllSkyDbImageTable
    images = session.query(table).filter_by(camera_id=source.camera_id,
                                           createDate=source.createDate).all()
    result = []
    for image in images:
        try:
            identity = source_identity(image.data)
        except ValueError:
            # A damaged source-only record must be repaired before reclaiming
            # the source at that exposure; never silently destroy its recovery.
            result.append(image)
        else:
            if identity == source.id:
                result.append(image)
    return result


def require_unreferenced(source):
    from .flask import db, models
    if source_dependents(source, db.session, models):
        raise OSError(errno.EBUSY, 'FITS source is still required by an archived image', source.filename)
