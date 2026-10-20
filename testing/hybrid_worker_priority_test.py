#!/usr/bin/env python3
"""Real forked workers lower only generation/cleanup child priorities."""
import ast
import multiprocessing
import os
from pathlib import Path
import signal
import traceback

ROOT = Path(__file__).resolve().parents[1]


def report_priority(self):
    self.report.send((os.getpid(), os.getpriority(os.PRIO_PROCESS, 0)))
    self.report.close()


def report_capture_priority(report):
    report.send((os.getpid(), os.getpriority(os.PRIO_PROCESS, 0)))
    report.close()


def run():
    context = multiprocessing.get_context('fork')
    source = ROOT / 'indi_allsky/video.py'
    tree = ast.parse(source.read_text())
    original = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == 'VideoWorker')
    names = {'__init__', 'run', 'sighup_handler_worker', 'sigterm_handler_worker',
             'sigint_handler_worker', 'sigalarm_handler_worker'}
    constructor = next(n for n in original.body if isinstance(n, ast.FunctionDef)
                       and n.name == '__init__')
    # Preserve sensitivity when a regression runner already uses NI19, where
    # another nice(19) would otherwise be capped and mask parent pollution.
    assert not any(isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
                   and n.func.attr == 'nice' for n in ast.walk(constructor))
    cls = ast.ClassDef(name='VideoWorker', bases=original.bases, keywords=[],
                       body=[n for n in original.body if isinstance(n, ast.FunctionDef) and n.name in names],
                       decorator_list=[])
    scope = dict(Process=context.Process, os=os, Path=Path, signal=signal,
                 traceback=traceback, miscDb=lambda *a: None,
                 miscUpload=lambda *a: None, __file__=str(source))
    exec(compile(ast.fix_missing_locations(ast.Module(body=[cls], type_ignores=[])), str(source), 'exec'), scope)
    VideoWorker = scope['VideoWorker']
    VideoWorker.saferun = report_priority
    storage_source = ROOT / 'indi_allsky/storage_worker.py'
    storage_tree = ast.parse(storage_source.read_text())
    storage = next(n for n in storage_tree.body if isinstance(n, ast.ClassDef) and n.name == 'StorageWorker')
    storage.body = [n for n in storage.body if isinstance(n, ast.FunctionDef) and n.name == '__init__']
    exec(compile(ast.Module(body=[storage], type_ignores=[]), str(storage_source), 'exec'), scope)
    StorageWorker = scope['StorageWorker']
    baseline = os.getpriority(os.PRIO_PROCESS, 0)
    parent_pid = os.getpid()
    error_q = context.Queue()
    for index, Worker in enumerate((VideoWorker, StorageWorker), 1):
        receiving, sending = context.Pipe(duplex=False)
        worker = Worker(index, {'IMAGE_FOLDER': '/tmp'}, error_q, None, None, None, None)
        assert os.getpriority(os.PRIO_PROCESS, 0) == baseline, 'Constructor changed supervisor priority'
        worker.report = sending
        worker.start()
        try:
            assert receiving.poll(5), 'Generation child failed to report priority'
            child_pid, priority = receiving.recv()
            assert child_pid != parent_pid
            assert priority == min(19, baseline + 19), (Worker.__name__, priority, baseline)
            worker.join(5)
            assert worker.exitcode == 0
        finally:
            if worker.is_alive():
                worker.terminate()
                worker.join(5)
            receiving.close()
            sending.close()
        assert os.getpriority(os.PRIO_PROCESS, 0) == baseline
        # A camera/image replacement started after worker construction and
        # execution must inherit the supervisor baseline, never NI19 pollution.
        receiving, sending = context.Pipe(duplex=False)
        capture = context.Process(target=report_capture_priority, args=(sending,))
        capture.start()
        try:
            assert receiving.poll(5), 'Capture replacement failed to report'
            child_pid, priority = receiving.recv()
            assert child_pid != parent_pid and priority == baseline
            capture.join(5)
            assert capture.exitcode == 0
        finally:
            if capture.is_alive():
                capture.terminate()
                capture.join(5)
            receiving.close()
            sending.close()
    error_q.close()
    error_q.join_thread()
    print('Worker priority: real Video/Storage child isolation, unchanged supervisor and later capture inheritance PASS (parent NI%s)' % baseline)


if __name__ == '__main__':
    run()
