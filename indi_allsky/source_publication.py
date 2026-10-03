"""Atomic publication of a complete display recipe alongside FITS science data."""
from copy import deepcopy
import gzip
import hashlib
import json
import os
from pathlib import Path
import stat
import tempfile

from .fits_context import EXTENSION, read_context, with_context


def scientific_digest(path):
    """Hash all science HDUs; ignore only context and structural checksum cards."""
    import numpy as np
    from astropy.io import fits
    digest = hashlib.sha256()
    with fits.open(path, memmap=False, do_not_scale_image_data=True) as hdus:
        for hdu in hdus:
            if hdu.name == EXTENSION:
                continue
            header = hdu.header.copy()
            for key in ('CHECKSUM', 'DATASUM', 'EXTEND'):
                header.remove(key, remove_all=True, ignore_missing=True)
            encoded = header.tostring().encode('ascii')
            digest.update(len(encoded).to_bytes(8, 'big'))
            digest.update(encoded)
            if hdu.data is not None:
                array = np.ascontiguousarray(hdu.data)
                description = json.dumps([array.dtype.str, array.shape]).encode()
                digest.update(len(description).to_bytes(8, 'big'))
                digest.update(description)
                digest.update(memoryview(array).cast('B'))
    return digest.hexdigest()


def publish_source_recipe(path, recipe):
    """Replace the context atomically, preserving science, permissions and mtime.

    Shared rendering assets stay content-addressed outside the FITS. This avoids
    duplicating fonts/masks for every exposure; the archive volume must keep them.
    """
    from astropy.io import fits
    from .source_rendering import file_digest
    path = Path(path)
    if path.is_symlink():
        raise ValueError('Source publication does not follow symlinks')
    before = path.stat()
    record = deepcopy(recipe)
    basis = record['basis']
    if record.get('version') != 1 or basis.get('version') not in (1, 2):
        raise ValueError('Unsupported source recipe')
    science = scientific_digest(path)
    expected = basis['source_sha256'] if basis['version'] == 1 else basis['scientific_sha256']
    actual = file_digest(path) if basis['version'] == 1 else science
    if actual != expected:
        raise ValueError('Source changed before context publication')
    basis.update(version=2, scientific_sha256=science)
    basis.pop('source_sha256', None)
    pending = None
    try:
        with fits.open(path, memmap=False, do_not_scale_image_data=True) as hdus:
            context = read_context(hdus)
            if context is None:
                context = {'version': 1}
            for key, expected in (('camera_id', basis['camera_id']),
                                  ('exposure_time', basis['exposure_date'])):
                if key in context and context[key] != expected:
                    raise ValueError('FITS acquisition context belongs to another exposure')
            context.update(complete_render_recipe=True, render_source=record)
            suffix = '.fit.gz' if path.name.endswith('.gz') else '.fit'
            with tempfile.NamedTemporaryFile(dir=path.parent, suffix=suffix, delete=False) as output:
                pending = Path(output.name)
            published = with_context(hdus, context)
            if suffix.endswith('.gz'):
                # Recompressing each exposure at level 9 can consume most of a
                # capture interval. Stream the same FITS bytes at fast level 1.
                with pending.open('wb') as stream:
                    with gzip.GzipFile(fileobj=stream, mode='wb', compresslevel=1, mtime=0) as compressed:
                        published.writeto(compressed)
            else:
                published.writeto(pending, overwrite=True)
        if scientific_digest(pending) != science:
            raise ValueError('Context publication changed scientific data')
        pending.chmod(stat.S_IMODE(before.st_mode))
        os.utime(pending, ns=(before.st_atime_ns, before.st_mtime_ns))
        with pending.open('rb') as stream:
            os.fsync(stream.fileno())
        current = path.stat()
        if (current.st_ino, current.st_size, current.st_mtime_ns, current.st_ctime_ns) != (
                before.st_ino, before.st_size, before.st_mtime_ns, before.st_ctime_ns):
            raise ValueError('Source changed during context publication')
        os.replace(pending, path)
        directory = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)
        return record
    finally:
        if pending is not None:
            pending.unlink(missing_ok=True)


def read_source_recipe(path):
    """Read the complete recipe without requiring an Image database JSON copy."""
    from astropy.io import fits
    with fits.open(path, memmap=False) as hdus:
        context = read_context(hdus)
    if context is None or not context.get('complete_render_recipe'):
        return None
    record = context.get('render_source')
    if not isinstance(record, dict) or record.get('version') != 1 or record.get('basis', {}).get('version') != 2:
        raise ValueError('Invalid published source recipe')
    return record
