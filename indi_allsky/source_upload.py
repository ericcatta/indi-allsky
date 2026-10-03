"""Short-lived display files for transfer adapters that require a pathname."""
from contextlib import contextmanager
from copy import deepcopy
from pathlib import Path
import tempfile

from .source_preview import source_display_bytes
from .source_publication import read_source_recipe


@contextmanager
def source_upload_file(entry, media_root, metadata):
    from .flask import db
    from .flask.models import IndiAllSkyDbFitsImageTable

    data = entry.data or {}
    recipe = data.get('render_source')
    identity = data.get('source_fits_id')
    basis = recipe.get('basis') if isinstance(recipe, dict) else None
    if identity is None and isinstance(basis, dict):
        identity = basis.get('source_id')
    if isinstance(identity, bool) or not isinstance(identity, int) or not 0 < identity < 2**63:
        raise ValueError('Invalid scientific source reference')
    source = db.session.get(IndiAllSkyDbFitsImageTable, identity)
    if (source is None or source.camera_id != entry.camera_id
            or source.createDate != entry.createDate):
        raise ValueError('Upload source does not match the camera/exposure')
    path = Path(source.getFilesystemPath()).resolve(strict=True)
    path.relative_to(Path(media_root).resolve(strict=True))
    if recipe is None:
        recipe = read_source_recipe(path)
    if recipe is None:
        raise ValueError('Source lacks a complete rendering recipe')
    suffix = Path(entry.filename).suffix.lower()
    content = source_display_bytes(path, recipe, camera_id=entry.camera_id,
                                   source_id=source.id, media_root=media_root,
                                   file_type=suffix.lstrip('.'))
    exported = deepcopy(metadata)
    if exported is not None:
        if not isinstance(exported, dict):
            raise ValueError('Upload metadata must be an object')
        exported['fileSize'] = len(content)
        exported['file_size'] = len(content)
        # The receiver owns a display file, not this database's scientific source.
        if isinstance(exported.get('data'), dict):
            for key in ('storage_format', 'source_fits_id', 'render_source'):
                exported['data'].pop(key, None)
    with tempfile.NamedTemporaryFile(prefix='hybrid-upload-', suffix=suffix) as output:
        output.write(content)
        output.flush()
        yield Path(output.name), exported
