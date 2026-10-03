#!/usr/bin/env python3
"""Filesystem identity failures must neither create paths nor touch media."""
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from indi_allsky.archive_volume import ArchiveUnavailable, validate_volume_spec, verify_archive


def unavailable(root, spec, **kwargs):
    try:
        verify_archive(root, spec, **kwargs)
    except ArchiveUnavailable:
        return
    raise AssertionError('Unavailable archive accepted')


with tempfile.TemporaryDirectory() as directory:
    root = Path(directory)
    media = root / 'untouched.fits'
    media.write_bytes(b'scientific-source')
    spec = dict(ROOT=str(root), UUID='test-uuid')
    device = root.stat().st_dev
    for invalid in ({}, {'ROOT':'relative','UUID':'test'}, {'ROOT':str(root),'UUID':'../../disk'}, False):
        try: validate_volume_spec(invalid)
        except ValueError: pass
        else: raise AssertionError('Invalid volume accepted')
    verify_archive(root / 'missing', None)
    with patch('indi_allsky.archive_volume.device_identity', return_value=device):
        verify_archive(root, spec, writable=True)
        unavailable(root / 'other', spec)
        with patch('indi_allsky.archive_volume.os.statvfs', return_value=SimpleNamespace(f_flag=1)):
            verify_archive(root, spec)
            unavailable(root, spec, writable=True)
    with patch('indi_allsky.archive_volume.device_identity', return_value=device + 1):
        unavailable(root, spec)
    with patch('indi_allsky.archive_volume.device_identity', side_effect=FileNotFoundError):
        unavailable(root, spec)
    with patch('indi_allsky.archive_volume.device_identity', return_value=device):
        verify_archive(root, spec, writable=True)  # reconnect
    assert media.read_bytes() == b'scientific-source'
    assert list(root.iterdir()) == [media]
print('Archive volume: matching disk, absence, wrong disk, read-only, reconnect and untouched media PASS')

# Execute the real supervisor method without starting hardware or worker threads.
import ast
import logging
source=Path(__file__).resolve().parents[1] / 'indi_allsky/allsky.py'
cls=next(n for n in ast.parse(source.read_text()).body if isinstance(n,ast.ClassDef) and n.name=='IndiAllSky')
method=next(n for n in cls.body if isinstance(n,ast.FunctionDef) and n.name=='_wait_for_archive')
namespace={'__package__':'indi_allsky','logger':logging.getLogger('archive-test')}
exec(compile(ast.Module(body=[method],type_ignores=[]),str(source),'exec'),namespace)
events=[]
worker=SimpleNamespace(config={'ARCHIVE_VOLUME':{'ROOT':'/archive','UUID':'test'}},image_dir='/archive',
                       _shutdown=False,_terminate=False,_miscDb=SimpleNamespace(setState=lambda *a:events.append(a)))
sleeps=[]
namespace['time']=SimpleNamespace(sleep=lambda seconds:sleeps.append(seconds))
with patch('indi_allsky.archive_volume.verify_archive',side_effect=[ArchiveUnavailable('missing'),ArchiveUnavailable('missing'),None]):
    assert namespace['_wait_for_archive'](worker)
assert sleeps==[5,5] and len(events)==2 and events[-1]==('ARCHIVE_STATUS','ready')
namespace['time']=SimpleNamespace(sleep=lambda seconds:setattr(worker,'_shutdown',True))
with patch('indi_allsky.archive_volume.verify_archive',side_effect=ArchiveUnavailable('missing')):
    assert namespace['_wait_for_archive'](worker) is False
print('Archive supervisor: bounded waits, recovery, deduplicated error state and shutdown PASS')
