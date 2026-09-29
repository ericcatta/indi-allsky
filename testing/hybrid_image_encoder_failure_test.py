#!/usr/bin/env python3
"""Encoder failures must preserve the published image and remove partial files."""
import ast
from datetime import datetime
import importlib.util
import logging
import os
from pathlib import Path
import shutil
import tempfile
from types import SimpleNamespace
from unittest.mock import patch


def run():
    # Execute the actual worker method without starting hardware or Flask.
    source = Path(__file__).resolve().parents[1] / 'indi_allsky/image.py'
    spec = importlib.util.spec_from_file_location('image_publication', source.with_name('image_publication.py'))
    publication = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(publication)
    tree = ast.parse(source.read_text())
    method = next(n for n in ast.walk(tree)
                  if isinstance(n, ast.FunctionDef) and n.name == 'write_img')
    scope = dict(tempfile=tempfile, Path=Path, shutil=shutil,
                 logger=logging.getLogger('encoder-test'),
                 constants=SimpleNamespace(NIGHT_NIGHT=0),
                 publish_image_file=publication.publish_image_file)
    exec(compile(ast.fix_missing_locations(ast.Module(body=[method], type_ignores=[])),
                 str(source), 'exec'), scope)
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        worker = SimpleNamespace(
            config={'IMAGE_FILE_TYPE': 'png', 'IMAGE_FILE_COMPRESSION': {'png': 3, 'jpg': 90},
                    'DAYTIME_CAPTURE': True, 'DAYTIME_CAPTURE_SAVE': False},
            profile_id='test', image_dir=root, night_av=[0])
        original_factory = tempfile.NamedTemporaryFile
        for extension, failure in (('png', 'false'), ('png', 'exception'), ('jpg', 'exception')):
            latest = root / ('latest.' + extension)
            latest.write_bytes(b'previous-valid-image')
            worker.config['IMAGE_FILE_TYPE'] = extension
            problem = OSError('injected disk write failure')

            def encode(path, *args, **kwargs):
                Path(path).write_bytes(b'partial-encoding')
                if failure == 'false':
                    return False
                raise problem

            scope['cv2'] = SimpleNamespace(imwrite=encode, IMWRITE_PNG_COMPRESSION=16,
                                            COLOR_BGR2RGB=4, cvtColor=lambda *args: None)
            scope['Image'] = SimpleNamespace(fromarray=lambda *args: SimpleNamespace(save=encode))
            with patch.object(tempfile, 'NamedTemporaryFile',
                              side_effect=lambda **kw: original_factory(dir=root, **kw)):
                try:
                    scope['write_img'](worker, None, SimpleNamespace(camera_id=1),
                                       SimpleNamespace(id=1), jpeg_exif=b'')
                except OSError as exc:
                    if failure == 'exception':
                        assert exc is problem, 'Original failure must propagate'
                else:
                    raise AssertionError('Encoder failure reported as a saved image')
            assert latest.read_bytes() == b'previous-valid-image'
            assert sorted(p.name for p in root.iterdir()) == sorted(
                p.name for p in root.glob('latest.*')), 'Partial temporary image leaked'
    # Run the actual worker through publication, including partially written copies.
    for failure in ('latest-copy', 'latest-replace', 'archive-copy', 'archive-link', None):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            latest = root / 'latest.png'
            latest.write_bytes(b'previous-valid-image')
            worker.config.update(IMAGE_FILE_TYPE='png', DAYTIME_CAPTURE_SAVE=True)
            worker.image_dir = root
            worker.filename_t = 'frame-{}-{}.{}'
            worker._getImageFolder = lambda *args: root
            stamp = datetime(2026, 9, 29, 9)
            ref = SimpleNamespace(camera_id=1, exp_date=stamp, day_date=stamp.date())
            archive = root / 'frame-1-20260929_090000.png'
            problem = OSError('injected publication failure')
            copies = []
            original_copy = shutil.copy2

            def encode(path, *args, **kwargs):
                Path(path).write_bytes(b'complete-encoded-frame')
                return True

            def copy(source, destination):
                copies.append(destination)
                # Readers must still see the complete old preview during copying.
                if len(copies) == 1:
                    assert latest.read_bytes() == b'previous-valid-image'
                if failure == ('latest-copy' if len(copies) == 1 else 'archive-copy'):
                    Path(destination).write_bytes(b'partial')
                    raise problem
                return original_copy(source, destination)

            scope['cv2'].imwrite = encode
            with patch.object(tempfile, 'NamedTemporaryFile',
                              side_effect=lambda **kw: original_factory(dir=root, **kw)), \
                 patch.object(shutil, 'copy2', side_effect=copy), \
                 patch.object(os, 'replace', side_effect=problem if failure == 'latest-replace' else os.replace), \
                 patch.object(os, 'link', side_effect=problem if failure == 'archive-link' else os.link):
                try:
                    result = scope['write_img'](worker, None, ref, SimpleNamespace(id=1))
                except OSError as exc:
                    assert failure and exc is problem
                else:
                    assert failure is None
                    assert result == (latest, archive)
            assert latest.read_bytes() == (b'previous-valid-image' if failure and failure.startswith('latest')
                                            else b'complete-encoded-frame')
            assert archive.exists() == (failure is None)
            assert set(root.iterdir()) == ({latest} if failure else {latest, archive})
            if not failure:
                assert archive.read_bytes() == latest.read_bytes()
                assert archive.stat().st_mode & 0o777 == 0o644
                # An existing archive must survive even if it appears after the caller's check.
                latest.write_bytes(b'another-frame')
                assert publication.publish_image_file(latest, archive, overwrite=False) is False
                assert archive.read_bytes() == b'complete-encoded-frame'
                assert set(root.iterdir()) == {latest, archive}
    print('Image encoder failure: PNG false/exception and JPEG exception preserve preview; partial files removed PASS')
    print('Image publication: copy/replace/link failures, cleanup, success and duplicate preservation PASS')


if __name__ == '__main__':
    run()
