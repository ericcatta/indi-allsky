#!/usr/bin/env python3
"""Encoder failures must preserve the published image and remove partial files."""
import ast
import logging
from pathlib import Path
import shutil
import tempfile
from types import SimpleNamespace
from unittest.mock import patch


def run():
    # Execute the actual worker method without starting hardware or Flask.
    source = Path(__file__).resolve().parents[1] / 'indi_allsky/image.py'
    tree = ast.parse(source.read_text())
    method = next(n for n in ast.walk(tree)
                  if isinstance(n, ast.FunctionDef) and n.name == 'write_img')
    scope = dict(tempfile=tempfile, Path=Path, shutil=shutil,
                 logger=logging.getLogger('encoder-test'),
                 constants=SimpleNamespace(NIGHT_NIGHT=0))
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
    print('Image encoder failure: PNG false/exception and JPEG exception preserve preview; partial files removed PASS')


if __name__ == '__main__':
    run()
