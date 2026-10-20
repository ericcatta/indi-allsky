#!/usr/bin/env python3
"""Timeout diagnostics, process ownership and failed-frame accounting."""
import ast
import logging
import os
import signal
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'indi_allsky/camera/libcamera.py'


def driver_type(logger):
    tree = ast.parse(SOURCE.read_text())
    cls = next(n for n in tree.body if isinstance(n, ast.ClassDef)
               and n.name == 'IndiClientLibCameraGeneric')
    names = {'_startLibcameraProcess', '_closeLibcameraOutput',
             '_resetLibcameraProcessState', '_libCameraProcessRunning',
             '_logLibcameraTimeoutOutput', 'abortCcdExposure',
             '_abortTimedOutLibcameraExposure', '_libcameraFileStats',
             'getCcdExposureStatus'}
    methods = [n for n in cls.body if isinstance(n, ast.FunctionDef) and n.name in names]
    assert len(methods) == len(names)
    scope = dict(tempfile=tempfile, subprocess=subprocess, time=time, os=os,
                 logger=logger, _multi_camera_diag=Mock())
    exec(compile(ast.Module(body=methods, type_ignores=[]), str(SOURCE), 'exec'), scope)
    return type('Driver', (), {name: scope[name] for name in names})


def client_for(Driver, tmp):
    client = Driver()
    client.active_exposure = True
    client.exposure = 5.25
    client.exposureStartTime = time.time()
    client.exposureStartMonotonic = time.monotonic()
    client.libcamera_output_f = None
    client.libcamera_process = None
    client.current_libcamera_cmd = ['test-camera']
    client.current_exposure_file_p = tmp / 'image.jpg'
    client.current_metadata_file_p = tmp / 'metadata.json'
    client.current_exposure_file_p.touch()
    client.current_metadata_file_p.touch()
    return client


def test_real_timeout(Driver, logger, ignore_term):
    with tempfile.TemporaryDirectory() as directory:
        tmp = Path(directory)
        ready = tmp / 'ready'
        code = ('import os, signal, time; from pathlib import Path; '
                + ('signal.signal(signal.SIGTERM, signal.SIG_IGN); ' if ignore_term else '')
                + 'os.write(1, b"x" * 100000 + b"\\nlast diagnostic \\xff\\n"); '
                + 'Path(%r).touch(); time.sleep(60)' % str(ready))
        client = client_for(Driver, tmp)
        client._startLibcameraProcess([sys.executable, '-c', code])
        child, output = client.libcamera_process, client.libcamera_output_f
        try:
            deadline = time.monotonic() + 5
            while not ready.exists() and time.monotonic() < deadline:
                time.sleep(0.01)
            assert ready.exists(), 'Child did not initialize'
            offset = output.tell()
            client._logLibcameraTimeoutOutput()
            assert output.tell() == offset, 'Diagnostic read moved child stdout offset'
            client._libcameraProcessTimedOut = lambda: True
            client._libcameraExposureTimeout = lambda: 17.25
            client._queueImage = Mock()
            assert client.getCcdExposureStatus() == (True, 'TIMEOUT')
            assert child.poll() == (-signal.SIGKILL if ignore_term else -signal.SIGTERM)
            assert output.closed and client.libcamera_process is None
            assert not client.active_exposure
            assert not (tmp / 'image.jpg').exists()
            assert not (tmp / 'metadata.json').exists()
            client._queueImage.assert_not_called()
            records = [c for c in logger.error.call_args_list
                       if c.args[0].startswith('rpicam-still timeout output')]
            record = records[-1].args
            assert record[5] > 100000 and record[6] == 16384 and record[7] is True
            assert len(record[8]) <= 16384 and 'last diagnostic' in record[8]
            assert '\ufffd' in record[8]
        finally:
            if child.poll() is None:
                child.kill()
            child.wait()
            client._closeLibcameraOutput()


def test_unreaped_process(Driver):
    with tempfile.TemporaryDirectory() as directory:
        client = client_for(Driver, Path(directory))
        process = Mock(pid=123, returncode=None)
        process.poll.return_value = None
        process.wait.side_effect = subprocess.TimeoutExpired('test-camera', 2.5)
        client.libcamera_process = process
        client.libcamera_output_f = tempfile.TemporaryFile(mode='w+b')
        output = client.libcamera_output_f
        try:
            client._libcameraProcessTimedOut = lambda: True
            client._libcameraExposureTimeout = lambda: 17.25
            assert client.getCcdExposureStatus() == (False, 'BUSY')
            assert client.active_exposure and client.libcamera_process is process
            assert not output.closed and client.current_exposure_file_p.exists()
            process.terminate.assert_called_once()
            process.kill.assert_called_once()
            assert process.wait.call_count == 2
            # Eventual exit of the killed child still completes an abort; it
            # must never enter the normal metadata/image completion path.
            process.poll.return_value = -signal.SIGKILL
            process.wait.side_effect = None
            process.wait.return_value = -signal.SIGKILL
            process.returncode = -signal.SIGKILL
            client._queueImage = Mock()
            assert client.getCcdExposureStatus() == (True, 'TIMEOUT')
            assert client.libcamera_process is None and not client.active_exposure
            assert output.closed
            client._queueImage.assert_not_called()
        finally:
            output.close()


def test_capture_timeout_branch():
    source = ROOT / 'indi_allsky/capture.py'
    tree = ast.parse(source.read_text())
    # Execute the actual adjacent timeout and frame-received branches. A timeout
    # must skip the entire existing success branch, including frame timestamps.
    branch = next(n for n in ast.walk(tree) if isinstance(n, ast.If)
                  and ast.unparse(n.test) == "exposure_state == 'TIMEOUT'")
    container = next(n for n in ast.walk(tree) if hasattr(n, 'body')
                     and isinstance(n.body, list) and branch in n.body)
    index = container.body.index(branch)
    success = container.body[index + 1]
    assert ast.unparse(success.test) == 'waiting_for_frame'
    client = SimpleNamespace(_libcamera_watchdog_cycles=0,
                             camera_runtime_state=SimpleNamespace(last_frame_ts=10),
                             _last_libcamera_frame_ts=10)
    scope = dict(self=client, exposure_state='TIMEOUT', waiting_for_frame=True,
                 waiting_for_sqm_frame=True, next_frame_time=99, logger=Mock())
    exec(compile(ast.Module(body=[branch, success], type_ignores=[]), str(source), 'exec'), scope)
    assert not scope['waiting_for_frame'] and not scope['waiting_for_sqm_frame']
    assert client._libcamera_watchdog_cycles == 1
    assert client.camera_runtime_state.last_frame_ts == 10
    assert client._last_libcamera_frame_ts == 10
    assert scope['next_frame_time'] == 99


def test_sync_wait_retains_owner_until_reaped():
    tree = ast.parse(SOURCE.read_text())
    capture = next(n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)
                   and n.name == 'setCcdExposure')
    wait_branch = next(n for n in ast.walk(capture) if isinstance(n, ast.Try)
                       and any(isinstance(h.type, ast.Attribute)
                               and h.type.attr == 'TimeoutExpired' for h in n.handlers))
    events = []
    process = Mock()
    process.wait.side_effect = subprocess.TimeoutExpired('test-camera', 17.25)
    client = SimpleNamespace(libcamera_process=process, exposureStartTime=10,
                             _queueImage=Mock())
    client._abortTimedOutLibcameraExposure = Mock(
        side_effect=lambda *args, **kwargs: events.append('initial abort') or False)
    outcomes = iter((False, True))

    def retry_abort():
        result = next(outcomes)
        events.append('reaped' if result else 'still busy')
        return result

    client.abortCcdExposure = Mock(side_effect=retry_abort)
    clock = SimpleNamespace(time=lambda: 30,
                            sleep=Mock(side_effect=lambda delay: events.append(('sleep', delay))))

    class ExposureTimeout(Exception):
        def __init__(self, message):
            assert events[-1] == 'reaped', 'Caller unwound before child exit'
            super().__init__(message)

    scope = dict(self=client, wait_timeout=17.25, subprocess=subprocess,
                 time=clock, TimeOutException=ExposureTimeout)
    try:
        exec(compile(ast.Module(body=[wait_branch], type_ignores=[]), str(SOURCE), 'exec'), scope)
    except ExposureTimeout as exc:
        assert str(exc) == 'Timeout waiting for exposure'
    else:
        raise AssertionError('Synchronous timeout did not propagate after reap')
    assert events == ['initial abort', ('sleep', 0.1), 'still busy', ('sleep', 0.1), 'reaped']
    client._abortTimedOutLibcameraExposure.assert_called_once_with(20, 17.25, sync=True)
    assert client.abortCcdExposure.call_count == 2
    assert all(not call.kwargs for call in client.abortCcdExposure.call_args_list)
    client._queueImage.assert_not_called()


def run():
    logger = Mock(spec=logging.Logger)
    Driver = driver_type(logger)
    test_real_timeout(Driver, logger, False)
    test_real_timeout(Driver, logger, True)
    test_unreaped_process(Driver)
    test_capture_timeout_branch()
    test_sync_wait_retains_owner_until_reaped()
    print('Libcamera timeout tail, terminate/kill reap, retained busy state and failed-frame accounting passed')


if __name__ == '__main__':
    run()
