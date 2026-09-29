#!/usr/bin/env python3
"""Status readers see whole snapshots; diagnostic I/O cannot reject a frame."""
import ast
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from datetime import datetime
import io
import json
import os
from pathlib import Path
import sys
import tempfile
import threading
from types import SimpleNamespace
from unittest.mock import Mock, patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from indi_allsky import constants
from indi_allsky.status_publication import publish_status_json


def run():
    with tempfile.TemporaryDirectory() as directory:
        target = Path(directory) / 'indi_allsky_status.json'
        old = b'{"time":"1"}'
        target.write_bytes(old)
        payload = {'name': 'caméra', 'time': '2', 'temp': 3.25, 'missing': None}
        legacy = io.StringIO()
        json.dump(payload, legacy, indent=4, ensure_ascii=False)
        entered, release = threading.Event(), threading.Event()
        replace = os.replace

        def stalled_replace(source, destination):
            assert Path(source).parent == target.parent
            assert Path(source).read_text() == legacy.getvalue()
            assert Path(source).stat().st_mode & 0o777 == 0o644
            entered.set()
            assert release.wait(5)
            replace(source, destination)

        with patch('indi_allsky.status_publication.os.replace', side_effect=stalled_replace):
            with ThreadPoolExecutor(max_workers=1) as pool:
                future = pool.submit(publish_status_json, target, payload)
                try:
                    assert entered.wait(2)
                    assert target.read_bytes() == old
                    assert json.loads(target.read_text()) == {'time': '1'}
                finally:
                    release.set()
                future.result(timeout=2)
        assert target.read_bytes() == legacy.getvalue().encode('utf-8')
        assert list(Path(directory).iterdir()) == [target]

        complete = target.read_bytes()
        with patch('indi_allsky.status_publication.os.replace', side_effect=OSError('disk failure')):
            try:
                publish_status_json(target, payload)
                raise AssertionError('Publication failure must propagate to the caller')
            except OSError:
                pass
        assert target.read_bytes() == complete
        assert list(Path(directory).iterdir()) == [target]

        create_temporary = tempfile.NamedTemporaryFile

        @contextmanager
        def partial_write(**kwargs):
            with create_temporary(**kwargs) as stream:
                def write(content):
                    stream.write(content[:5])
                    raise OSError('short write')
                yield SimpleNamespace(name=stream.name, write=write)

        with patch('indi_allsky.status_publication.tempfile.NamedTemporaryFile', side_effect=partial_write):
            try:
                publish_status_json(target, payload)
                raise AssertionError('Short write must fail')
            except OSError:
                pass
        assert target.read_bytes() == complete
        assert list(Path(directory).iterdir()) == [target]

        # Execute the real worker method without importing camera/hardware libraries.
        tree = ast.parse((ROOT / 'indi_allsky/image.py').read_text())
        worker = next(node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == 'ImageWorker')
        method = next(node for node in worker.body if isinstance(node, ast.FunctionDef) and node.name == 'write_status_json')
        logger = Mock()
        namespace = {'__package__': 'indi_allsky', 'constants': constants, 'logger': logger}
        exec(compile(ast.Module(body=[method], type_ignores=[]), 'image.py', 'exec'), namespace)
        owner = SimpleNamespace(
            night_av=[0] * 20, sensors_temp_av=[5.0] * 60,
            sensors_user_av=[2.0] * 110, position_av=[0.0] * 3,
            target_adu_found=True, current_adu_target=40, config={},
            adsb_aircraft_list=[], image_processor=SimpleNamespace(camera_sqm_raw_mag=20),
            varlib_folder_p=Path(directory))
        frame = SimpleNamespace(camera_name='caméra', gain=1, exposure=0.5,
            target_adu=40, sqm_value=20, stars=[], lines=[],
            exp_date=datetime(2026, 1, 1), kpindex=0, ovation_max=0,
            aurora_mag_bt=None, aurora_mag_gsm_bz=None, aurora_plasma_density=None,
            aurora_plasma_speed=None, aurora_plasma_temp=None,
            aurora_n_hemi_gw=None, aurora_s_hemi_gw=None, smoke_rating=0)
        method = namespace['write_status_json']
        method(owner, frame, 42, 41)
        status = json.loads(target.read_text())
        assert status['device'] == 'caméra' and status['current_adu'] == 42
        assert status['sensor_temp_59'] == 5 and status['sensor_user_109'] == 2
        complete = target.read_bytes()
        with patch('indi_allsky.status_publication.publish_status_json', side_effect=OSError('readonly diagnostics')):
            assert method(owner, frame, 42, 41) is None
        logger.exception.assert_called_once_with('[STATUS_JSON_PUBLISH_FAILED] Continuing image processing')
        assert target.read_bytes() == complete
        try:
            method(owner, frame, object(), 41)
            raise AssertionError('Invalid metadata should retain its serialization error')
        except TypeError:
            pass
        assert target.read_bytes() == complete
        assert list(Path(directory).iterdir()) == [target]
    print('Atomic status snapshots, byte parity, failure preservation and nonfatal worker I/O: PASS')


if __name__ == '__main__':
    run()
