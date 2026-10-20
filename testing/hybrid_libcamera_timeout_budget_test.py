#!/usr/bin/env python3
"""Budget the unchanged preview-to-still protocol separately from shutter time."""
import ast
import math
import re
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

SOURCE = Path(__file__).resolve().parents[1] / 'indi_allsky/camera/libcamera.py'


def run():
    tree = ast.parse(SOURCE.read_text())
    cls = next(n for n in tree.body if isinstance(n, ast.ClassDef)
               and n.name == 'IndiClientLibCameraGeneric')
    names = {'_cmdHasOption', '_libcameraPreviewSeconds', '_libcameraExposureTimeout',
             '_libcameraProfileContextEnabled', '_libcameraProcessTimedOut',
             '_libCameraProcessRunning', 'getCcdExposureStatus'}
    methods = [n for n in cls.body if isinstance(n, ast.FunctionDef) and n.name in names]
    clock = SimpleNamespace(now=100.0, wall=100.0)
    scope = dict(math=math, re=re, time=SimpleNamespace(time=lambda: clock.wall,
                                                     monotonic=lambda: clock.now))
    exec(compile(ast.Module(body=methods, type_ignores=[]), str(SOURCE), 'exec'), scope)
    Driver = type('Driver', (), {name: scope[name] for name in names})
    client = Driver()
    client.config = {'MULTI_CAMERA_ACTIVE_PROFILE': 'imx708-wide', 'CCD_EXPOSURE_TIMEOUT': 330}
    client.exposure = 9
    command = ['rpicam-still', '--nopreview', '--shutter', '9000000', '--gain', '2.48',
               '--awb', 'daylight']
    client.current_libcamera_cmd = command
    assert client._libcameraPreviewSeconds() == 5
    assert client._libcameraExposureTimeout() == 26
    assert client.current_libcamera_cmd == command
    cases = [(['--timeout', '2000'], 2), (['--timeout=2s'], 2),
             (['-t', '2sec'], 2), (['-t2000ms'], 2), (['-t=2000000us'], 2),
             (['--timeout', '2000000000ns'], 2), (['--timeout', '0.5min'], 30),
             (['--timeout', '2e3'], 2), (['--timeout', '0'], 0),
             (['--timeout', 'inf'], 5), (['--timeout', '1e309min'], 5),
             (['--timeout', 'nan'], 5), (['--timeout', '-1'], 5),
             (['--timeout'], 5)]
    for arguments, seconds in cases:
        client.current_libcamera_cmd = command + arguments
        before = list(client.current_libcamera_cmd)
        assert client._libcameraPreviewSeconds() == seconds, arguments
        assert client._libcameraExposureTimeout() == 21 + seconds, arguments
        assert client.current_libcamera_cmd == before
    client.current_libcamera_cmd = command + ['--immediate', '--timeout', '5000']
    assert client._libcameraPreviewSeconds() == 0
    assert client._libcameraExposureTimeout() == 21
    client.exposure = 0.2
    assert client._libcameraExposureTimeout() == 12.2

    # Production tails show startup7.213s + preview5.067s before the9s still.
    # At21.04s the previous watchdog killed it before even this minimal budget
    # (21.28s, excluding save overhead) could finish. Model completion22s to
    # prove the real watchdog allows that work, while still bounding a hang26s.
    client.exposure = 9
    client.current_libcamera_cmd = command
    client.exposureStartTime = 100
    client.exposureStartMonotonic = 100
    client.libcamera_process = SimpleNamespace(poll=lambda: None)
    clock.now = 121.04
    assert not client._libcameraProcessTimedOut()
    clock.now = 122
    client.libcamera_process.poll = lambda: 0
    assert not client._libcameraProcessTimedOut()
    client.libcamera_process.poll = lambda: None
    clock.now = 126.01
    assert client._libcameraProcessTimedOut()

    # Reproduce the former expression with separate clocks: an NTP jump
    # forward aborts early, while a jump backward suppresses a real timeout.
    # The actual driver watchdog must follow only elapsed monotonic time.
    client.current_libcamera_cmd = command + ['--immediate', '--timeout', '1']
    client.exposure = .54711527
    timeout = client._libcameraExposureTimeout()
    assert timeout == 12.54711527
    client.active_exposure = True
    client._abortTimedOutLibcameraExposure = Mock(return_value=True)
    clock.now, clock.wall = 101, 3700
    assert clock.wall - client.exposureStartTime > timeout  # Old false timeout.
    assert not client._libcameraProcessTimedOut()
    assert client.getCcdExposureStatus() == (False, 'BUSY')
    client._abortTimedOutLibcameraExposure.assert_not_called()
    clock.now, clock.wall = 113, -3500
    assert not clock.wall - client.exposureStartTime > timeout  # Old missed timeout.
    assert client._libcameraProcessTimedOut()
    assert client.getCcdExposureStatus() == (True, 'TIMEOUT')
    client._abortTimedOutLibcameraExposure.assert_called_once_with(13, timeout, sync=False)
    assert client.exposureStartTime == 100  # Wall timestamp retained for metadata.
    client.exposure = .5
    timeout = client._libcameraExposureTimeout()  # Exactly representable12.5s.
    clock.now = 100 + timeout
    assert not client._libcameraProcessTimedOut()  # Existing strict deadline.
    clock.now += .001
    assert client._libcameraProcessTimedOut()
    client.libcamera_process.poll = lambda: 0
    assert not client._libcameraProcessTimedOut()  # Finished process still wins.
    client.exposureStartMonotonic = 0
    client.libcamera_process.poll = lambda: None
    assert not client._libcameraProcessTimedOut()  # No registered exposure.

    # Keep the default/current-config timeout policy unchanged.
    for profile in ('default', 'current-config', None):
        client.config['MULTI_CAMERA_ACTIVE_PROFILE'] = profile
        assert client._libcameraExposureTimeout() == 330

    capture = next(n for n in cls.body if isinstance(n, ast.FunctionDef)
                   and n.name == 'setCcdExposure')
    assignments = [n for n in ast.walk(capture) if isinstance(n, ast.Assign)]
    cmd_assignment = next(n for n in assignments
                          if any(isinstance(t, ast.Attribute) and t.attr == 'current_libcamera_cmd'
                                 for t in n.targets))
    timeout_assignment = next(n for n in assignments
                              if any(isinstance(t, ast.Attribute) and t.attr == 'libcamera_timeout'
                                     for t in n.targets))
    assert cmd_assignment.lineno < timeout_assignment.lineno
    assert '_normalizeLibcameraPreviewTimeout' not in SOURCE.read_text()
    print('Libcamera timeout budget: unchanged AF/argv, preview units/aliases, clock jumps, finite recovery and delayed completion passed')


if __name__ == '__main__':
    run()
