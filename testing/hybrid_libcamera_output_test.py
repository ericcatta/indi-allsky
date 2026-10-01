#!/usr/bin/env python3
"""Real subprocess output must not block capture waiting for process exit."""
import ast
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from unittest.mock import patch


SOURCE = Path(__file__).resolve().parents[1] / 'indi_allsky/camera/libcamera.py'


def driver_methods():
    tree = ast.parse(SOURCE.read_text())
    cls = next(n for n in tree.body if isinstance(n, ast.ClassDef)
               and n.name == 'IndiClientLibCameraGeneric')
    names = {'_startLibcameraProcess', '_readLibcameraOutput', '_closeLibcameraOutput'}
    methods = [n for n in cls.body if isinstance(n, ast.FunctionDef) and n.name in names]
    assert len(methods) == len(names)
    scope = {'tempfile': tempfile, 'subprocess': subprocess}
    exec(compile(ast.Module(body=methods, type_ignores=[]), str(SOURCE), 'exec'), scope)
    # Prevent a tested helper from being bypassed by the real capture entrypoint.
    capture = next(n for n in cls.body if isinstance(n, ast.FunctionDef)
                   and n.name == 'setCcdExposure')
    calls = [n.func.attr for n in ast.walk(capture)
             if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)]
    assert calls.count('_startLibcameraProcess') == 1
    assert 'Popen' not in calls
    return type('DriverMethods', (), {name: scope[name] for name in names})


def run():
    Driver = driver_methods()
    payload_size = 4 * 1024 * 1024
    command = [sys.executable, '-c',
               'import os; os.write(1, b"x" * %d); os.write(2, b"\\nend\\n")' % payload_size]
    for images_only in (False, True):
        for sync in (False, True):
            client = Driver()
            client.images_only = images_only
            client.libcamera_process = None
            client.libcamera_output_f = None
            client._startLibcameraProcess(command)
            output = client.libcamera_output_f
            child = client.libcamera_process
            try:
                if sync:
                    child.wait(timeout=5)
                else:
                    deadline = time.monotonic() + 5
                    while child.poll() is None and time.monotonic() < deadline:
                        time.sleep(0.01)
                    assert child.poll() is not None, 'Unread output blocked capture completion'
                assert child.returncode == 0
                assert b''.join(client._readLibcameraOutput()) == b'x' * payload_size + b'\nend\n'
                # A second diagnostic read must still return the captured output.
                assert b''.join(client._readLibcameraOutput()).endswith(b'\nend\n')
            finally:
                if child.poll() is None:
                    child.kill()
                child.wait()
                client._closeLibcameraOutput()
            assert output.closed and client.libcamera_output_f is None
            client._closeLibcameraOutput()

    # Failed process creation must retain the original error and close its file.
    for problem in (FileNotFoundError('missing executable'), ValueError('invalid arguments'),
                    KeyboardInterrupt()):
        client = Driver()
        client.libcamera_process = None
        with tempfile.TemporaryFile(mode='w+b') as output:
            with patch.object(tempfile, 'TemporaryFile', return_value=output), \
                    patch.object(subprocess, 'Popen', side_effect=problem):
                try:
                    client._startLibcameraProcess(['unavailable-rpicam'])
                except BaseException as exc:
                    assert exc is problem
                else:
                    raise AssertionError('Process creation failure swallowed')
            assert output.closed and client.libcamera_output_f is None
            assert client.libcamera_process is None
    print('Libcamera output: full/secondary profiles, sync/poll, stderr, repeated reads and failed-start cleanup passed')


if __name__ == '__main__':
    run()
