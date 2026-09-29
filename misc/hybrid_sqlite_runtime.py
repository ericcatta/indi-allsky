#!/usr/bin/env python3
"""Install/remove a checksum-verified SQLite library in a dedicated virtualenv.

Run with system Python so removal works even if the virtualenv bootstrap fails.
This never changes the system SQLite library. Existing managed files are refused.
"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def install(prefix, library, sha256, version='3.51.3'):
    prefix = Path(prefix).resolve()
    library = Path(library).resolve()
    if not (prefix / 'pyvenv.cfg').is_file() or digest(library) != sha256:
        raise ValueError('Virtualenv or library checksum does not match')
    python = prefix / 'bin/python'
    site = Path(subprocess.check_output([str(python), '-c', 'import sysconfig; print(sysconfig.get_path("purelib"))'], text=True).strip()).resolve()
    if prefix not in site.parents:
        raise ValueError('Site-packages is outside the requested virtualenv')
    target = prefix / 'lib/hybrid-sqlite/libsqlite3.so.0'
    module = site / '_hybrid_sqlite_runtime.py'
    pth = site / '00_hybrid_sqlite_runtime.pth'
    manifest = prefix / 'hybrid-sqlite-runtime.json'
    for path in (target, module, pth, manifest):
        if path.exists():
            raise FileExistsError(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(library, target)
    bootstrap = f'''# Managed by misc/hybrid_sqlite_runtime.py; remove the .pth to roll back.
try:
    import ctypes, hashlib
    from pathlib import Path
    if hashlib.sha256(Path({str(target)!r}).read_bytes()).hexdigest() != {sha256!r}:
        raise RuntimeError('SQLite runtime checksum mismatch')
    ctypes.CDLL({str(target)!r}, mode=ctypes.RTLD_GLOBAL)
    import sqlite3
    if sqlite3.sqlite_version != {version!r}:
        raise RuntimeError('Unexpected SQLite version: ' + sqlite3.sqlite_version)
except Exception as error:
    raise SystemExit('Hybrid SQLite bootstrap failed; remove 00_hybrid_sqlite_runtime.pth to roll back: ' + str(error))
'''
    module.write_text(bootstrap)
    state = {'version': version, 'files': {str(target): digest(target), str(module): digest(module)}, 'pth': str(pth)}
    manifest.write_text(json.dumps(state, indent=2)+'\n')
    try:
        pth.write_text('import _hybrid_sqlite_runtime\n')
        actual = subprocess.check_output([str(python), '-c', 'import sqlite3; print(sqlite3.sqlite_version)'], text=True).strip()
        if actual != version:
            raise RuntimeError('Runtime activation failed')
    except BaseException:
        pth.unlink(missing_ok=True)
        raise
    return state


def remove(prefix):
    prefix = Path(prefix).resolve()
    manifest = prefix / 'hybrid-sqlite-runtime.json'
    state = json.loads(manifest.read_text())
    paths = [Path(state['pth']), *(Path(p) for p in state['files'])]
    if any(prefix not in p.resolve().parents for p in paths):
        raise ValueError('Manifest path outside virtualenv')
    # Stop bootstrap first; retain any unexpectedly modified artifact.
    pth = Path(state['pth'])
    if pth.exists() and pth.read_text() != 'import _hybrid_sqlite_runtime\n':
        raise ValueError('Bootstrap changed; refusing to remove unrelated content')
    pth.unlink(missing_ok=True)
    for name, expected in state['files'].items():
        path = Path(name)
        if path.exists() and digest(path) == expected:
            path.unlink()
    manifest.unlink()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--venv', type=Path, required=True)
    parser.add_argument('--library', type=Path)
    parser.add_argument('--sha256')
    parser.add_argument('--version', default='3.51.3')
    parser.add_argument('--remove', action='store_true')
    args = parser.parse_args()
    if args.remove:
        remove(args.venv)
    elif args.library and args.sha256:
        print(json.dumps(install(args.venv, args.library, args.sha256, args.version)))
    else:
        parser.error('Installation requires --library and --sha256')
