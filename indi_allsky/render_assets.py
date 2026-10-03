"""Lossless content-addressed assets for reproducible source rendering."""
import hashlib
import json
import math
import os
from pathlib import Path
import re
import tempfile
import zipfile

import numpy as np
from .render_asset_lifecycle import asset_store_lease

MAX_BYTES = 256 * 1024 * 1024


def _digest(arrays):
    digest = hashlib.sha256()
    total = 0
    for name, value in sorted(arrays.items()):
        if not re.fullmatch(r'[a-z][a-z0-9_]*', name):
            raise ValueError('Invalid render asset array name')
        array = np.ascontiguousarray(value)
        if array.dtype.kind not in 'buif' or array.ndim > 3:
            raise ValueError('Unsupported render asset array')
        total += array.nbytes
        if total > MAX_BYTES:
            raise ValueError('Render asset exceeds size limit')
        header = json.dumps([name, array.dtype.str, array.shape], separators=(',', ':')).encode()
        digest.update(len(header).to_bytes(8, 'big'))
        digest.update(header)
        digest.update(memoryview(array).cast('B'))
    if not arrays:
        raise ValueError('Empty render asset')
    return digest.hexdigest()


class RenderAssetStore:
    def __init__(self, root):
        self.root = Path(root).resolve()

    def _path(self, identity):
        if not isinstance(identity, str) or not re.fullmatch('[0-9a-f]{64}', identity):
            raise ValueError('Invalid render asset identity')
        path = self.root / (identity + '.npz')
        if path.is_symlink():
            raise ValueError('Render assets cannot be symlinks')
        return path

    @asset_store_lease
    def put(self, **arrays):
        identity = _digest(arrays)
        self.root.mkdir(parents=True, exist_ok=True)
        path = self._path(identity)
        if path.is_file():
            return identity
        temporary = None
        try:
            with tempfile.NamedTemporaryFile(dir=self.root, prefix='.hybrid-asset-', suffix='.part', delete=False) as output:
                temporary = Path(output.name)
                np.savez_compressed(output, **arrays)
                output.flush()
                os.fsync(output.fileno())
            os.replace(temporary, path)
            directory = os.open(self.root, os.O_RDONLY | os.O_DIRECTORY)
            try:
                os.fsync(directory)
            finally:
                os.close(directory)
        finally:
            if temporary is not None:
                temporary.unlink(missing_ok=True)
        return identity

    @asset_store_lease
    def get(self, identity):
        path = self._path(identity)
        with zipfile.ZipFile(path) as archive:
            members = archive.infolist()
            if len(members) > 16 or sum(m.file_size for m in members) > MAX_BYTES + 65536:
                raise ValueError('Render asset exceeds size limit')
            declared = 0
            for member in members:
                if not re.fullmatch(r'[a-z][a-z0-9_]*\.npy', member.filename):
                    raise ValueError('Invalid render asset member')
                with archive.open(member) as stream:
                    version = np.lib.format.read_magic(stream)
                    reader = {(1, 0):np.lib.format.read_array_header_1_0,
                              (2, 0):np.lib.format.read_array_header_2_0}.get(version)
                    if reader is None:
                        raise ValueError('Unsupported render asset array format')
                    shape, _, dtype = reader(stream)
                    if dtype.kind not in 'buif' or len(shape) > 3:
                        raise ValueError('Unsupported render asset array')
                    declared += math.prod(shape) * dtype.itemsize
                    if declared > MAX_BYTES:
                        raise ValueError('Render asset exceeds size limit')
        with np.load(path, allow_pickle=False) as archive:
            arrays = {name: archive[name] for name in archive.files}
        if _digest(arrays) != identity:
            raise ValueError('Render asset content does not match identity')
        return arrays

    @asset_store_lease
    def font_path(self, identity):
        """Materialize an immutable font asset for libraries requiring a filename."""
        arrays = self.get(identity)
        data = arrays.get('font')
        if data is None or data.dtype != np.uint8 or data.ndim != 1:
            raise ValueError('Invalid font asset')
        path = self._path(identity).with_suffix('.font')
        if path.is_symlink():
            raise ValueError('Render assets cannot be symlinks')
        payload = data.tobytes()
        if path.is_file() and path.read_bytes() == payload:
            return path
        temporary = None
        try:
            with tempfile.NamedTemporaryFile(dir=self.root, prefix='.hybrid-asset-', suffix='.part', delete=False) as output:
                temporary = Path(output.name)
                output.write(payload)
            os.replace(temporary, path)
        finally:
            if temporary is not None:
                temporary.unlink(missing_ok=True)
        return path
