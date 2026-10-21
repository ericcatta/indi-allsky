#!/usr/bin/env python3
"""Live-child and real-filesystem evidence; no camera or application needed."""
import ast
import importlib.util
import json
import logging
import multiprocessing
import os
from pathlib import Path
import select
import subprocess
import sys
import tempfile
import time
from types import SimpleNamespace
from unittest.mock import Mock

ROOT = Path(__file__).resolve().parents[1]
HELPER = ROOT / 'indi_allsky/camera/timeout_diagnostics.py'
spec = importlib.util.spec_from_file_location('timeout_diagnostics_test_helper', HELPER)
diag = importlib.util.module_from_spec(spec)
spec.loader.exec_module(diag)


def write(root, name, content):
    target = root / name
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(content if isinstance(content, bytes) else content.encode())


def fixture(root):
    write(root, '123/status', 'Name:\tfixture\nState:\tS (sleeping)\nThreads:\t40\nVmRSS:\t64 kB\nVmSwap:\t0 kB\nSecret:\tNEVER_LOG_THIS\n')
    write(root, '123/io', 'read_bytes: 1024\nwrite_bytes: 2048\n')
    for tid in range(123, 163):
        write(root, '123/task/%d/status' % tid, 'State:\tS (sleeping)\n')
        write(root, '123/task/%d/wchan' % tid, 'futex_wait_queue')
        write(root, '123/task/%d/schedstat' % tid, '100 200 3\n')
    write(root, 'meminfo', 'MemAvailable: 123 kB\nSwapTotal: 456 kB\nSwapFree: 400 kB\nDirty: 2 kB\nWriteback: 0 kB\n')
    write(root, 'vmstat', 'pgmajfault 12\npswpin 5\npswpout 6\npgscan_direct 7\nallocstall_normal 8\noom_kill 0\n')
    for name in ('cpu', 'io', 'memory'):
        write(root, 'pressure/' + name, 'some avg10=0.00 avg60=0.00 avg300=0.00 total=10\n')
    # These files are never needed for the requested diagnostic.
    for name in ('cmdline', 'environ', 'maps', 'mem'):
        write(root, '123/' + name, 'NEVER_LOG_THIS')


def collect_in_child(root, sending):
    sending.send(diag.collect_timeout_diagnostics(123, proc_root=root))
    sending.close()


def test_files_bounds_and_races():
    with tempfile.TemporaryDirectory() as folder:
        root = Path(folder)
        fixture(root)
        data = diag.collect_timeout_diagnostics(123, proc_root=root)
        assert data['available'] and data['status']['Threads'] == '40'
        assert len(data['threads']) == 8 and data['threads_limited']
        assert data['threads'][0]['tid'] == 123
        assert data['threads'][0]['schedstat'] == dict(cpu_ns=100, runqueue_ns=200, timeslices=3)
        assert data['io']['read_bytes'] == '1024'
        assert data['memory']['MemAvailable'] == '123 kB'
        assert data['vmstat']['pgmajfault'] == 12
        assert 'NEVER_LOG_THIS' not in json.dumps(data)
        assert data['read_bytes'] <= diag.MAX_READ_BYTES
        tiny = diag.collect_timeout_diagnostics(123, proc_root=root, max_read_bytes=31)
        assert tiny['read_bytes'] <= 31 and tiny['read_limit_reached']
        assert len(diag.collect_timeout_diagnostics(123, proc_root=root, max_threads=1)['threads']) == 1
        assert len(diag.collect_timeout_diagnostics(123, proc_root=root, max_threads=1000)['threads']) == 8

        # Disappearing process/thread files must produce bounded errors, not an
        # exception that could prevent terminating the camera process.
        for path in (root / '123').rglob('*'):
            if path.is_file():
                path.unlink()
        missing = diag.collect_timeout_diagnostics(123, proc_root=root)
        assert not missing['available'] and 0 < len(missing['errors']) <= 8
        for pid in (None, True, -1, '../123'):
            assert diag.collect_timeout_diagnostics(pid, proc_root=root)['errors'] == ['invalid_pid']

    # A pathological virtual/file replacement may not turn a diagnostic read
    # into a blocking FIFO open or an EOF-draining loop.
    with tempfile.TemporaryDirectory() as folder:
        root = Path(folder)
        fixture(root)
        (root / '123/io').unlink()
        os.mkfifo(root / '123/io')
        context = multiprocessing.get_context('fork')
        receiving, sending = context.Pipe(duplex=False)
        child = context.Process(target=collect_in_child, args=(root, sending))
        child.start()
        try:
            assert receiving.poll(3), 'Collector blocked on a file without a writer'
            assert receiving.recv()['available']
            child.join(3)
            assert child.exitcode == 0
        finally:
            if child.is_alive():
                child.kill()
                child.join(3)
            receiving.close()
            sending.close()

    # Cap serialized output as well as reads, even for hostile control bytes
    # and oversized fields. The helper must return valid bounded JSON.
    with tempfile.TemporaryDirectory() as folder:
        root = Path(folder)
        fixture(root)
        control = b'\x01' * 8192
        write(root, '123/status', b'State: ' + control[:80] + b'\nVmRSS: ' + control[:80] + b'\n')
        for tid in range(123, 163):
            write(root, '123/task/%d/status' % tid, b'State: ' + control + b'\n')
            write(root, '123/task/%d/wchan' % tid, control)
        for name in ('cpu', 'io', 'memory'):
            write(root, 'pressure/' + name, control)
        payload = diag.timeout_diagnostics_json(123, proc_root=root)
        assert len(payload.encode('ascii')) <= diag.MAX_LOG_BYTES
        assert json.loads(payload)['payload_limited']


def test_live_child_and_abort_integration():
    command = [sys.executable, '-u', '-c',
               'import threading,time; threading.Thread(target=lambda: time.sleep(60),daemon=True).start(); print("ready",flush=True); time.sleep(60)']
    child = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    try:
        assert select.select([child.stdout], [], [], 5)[0], 'Child did not initialize'
        assert child.stdout.readline() == b'ready\n'
        data = diag.collect_timeout_diagnostics(child.pid)
        if Path('/proc/self/status').exists():
            assert data['available']
            assert int(data['status']['Threads']) >= 2
            main = next(t for t in data['threads'] if t['tid'] == child.pid)
            assert main['status']['State'] and main['schedstat'] is not None
            assert data['memory'].get('MemAvailable')
            assert 'cmdline' not in json.dumps(data)
            platform_result = 'Linux live process fields verified'
        else:
            assert not data['available'] and data['errors']
            platform_result = 'live child retained; Linux/proc unavailable on this platform'
        assert child.poll() is None, 'Collector changed process state'

        source = ROOT / 'indi_allsky/camera/libcamera.py'
        tree = ast.parse(source.read_text())
        method = next(n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)
                      and n.name == '_abortTimedOutLibcameraExposure')
        events = []
        logger = Mock(spec=logging.Logger)

        def sample(pid):
            assert pid == child.pid and child.poll() is None
            events.append('sample live child')
            return diag.timeout_diagnostics_json(pid)

        def abort(**kwargs):
            events.append('abort')
            assert kwargs == {'timeout_diagnostics': True}
            return True

        client = SimpleNamespace(libcamera_process=child, current_libcamera_cmd=['camera'],
                                 current_exposure_file_p=None, current_metadata_file_p=None,
                                 exposure=.25, _libcameraFileStats=lambda _: 'exists=False',
                                 abortCcdExposure=abort)
        scope = dict(logger=logger, _multi_camera_diag=Mock(), timeout_diagnostics_json=sample)
        exec(compile(ast.Module(body=[method], type_ignores=[]), str(source), 'exec'), scope)
        assert scope['_abortTimedOutLibcameraExposure'](client, 12.3, 12.25)
        assert events == ['sample live child', 'abort']
        resource_log = next(call for call in logger.error.call_args_list if 'timeout resources' in call.args[0])
        assert len(resource_log.args[-1].encode('ascii')) <= diag.MAX_LOG_BYTES
        for problem in (PermissionError('proc disappeared'), RuntimeError('diagnostic failed')):
            events.clear()

            def fail(pid):
                events.append('diagnostic failure')
                raise problem

            scope['timeout_diagnostics_json'] = fail
            assert scope['_abortTimedOutLibcameraExposure'](client, 12.3, 12.25)
            assert events == ['diagnostic failure', 'abort']
        print(platform_result)
    finally:
        if child.poll() is None:
            child.kill()
        child.wait()
        child.stdout.close()
        child.stderr.close()
    gone = diag.collect_timeout_diagnostics(child.pid)
    assert not gone['available'] and gone['errors']


def run():
    test_files_bounds_and_races()
    test_live_child_and_abort_integration()
    print('Timeout diagnostics: real files/process, pre-signal integration, missing/race/FIFO, thread/read/log bounds and abort resilience PASS')


if __name__ == '__main__':
    run()
