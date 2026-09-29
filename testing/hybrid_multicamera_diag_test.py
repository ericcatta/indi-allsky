#!/usr/bin/env python3
"""Slow diagnostics cannot stall capture; real files, overflow and fork lifecycle."""
import multiprocessing
import os
from pathlib import Path
import sys
import tempfile
import threading
import time
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from indi_allsky import multicamera_diag as diag


def child_record():
    diag.write_multicamera_diag('[MULTI_CAMERA_DIAG][child][camera_id=2] child event')
    # multiprocessing finalization must drain this small pending record.


def run():
    entered, release = threading.Event(), threading.Event()
    records = []
    def slow_sink(message, line):
        entered.set()
        assert release.wait(5), 'Test did not release stalled sink'
        records.append((message, line))
    writer = diag._DiagnosticWriter(sink=slow_sink, capacity=2)
    try:
        assert writer.submit('first', 'first\n')
        assert entered.wait(1)
        start = time.monotonic()
        assert writer.submit('second', 'second\n')
        assert writer.submit('third', 'third\n')
        assert not writer.submit('overflow', 'overflow\n')
        assert time.monotonic() - start < .2
        assert len(writer._records) == 2
        assert not writer.flush(.02)
        start = time.monotonic()
        assert not writer.close(.02)
        assert time.monotonic() - start < .2, 'Shutdown waited for blocked disk'
    finally:
        release.set()
        assert writer.close(2)
    assert [m for m, _ in records if 'dropped_records' not in m] == ['first', 'second', 'third']
    assert any('dropped_records=1 reason=queue_full' in m for m, _ in records)

    # Sink exceptions must not strand subsequent records.
    attempts = []
    def failing_sink(message, line):
        attempts.append(message)
        if message == 'fail': raise OSError('disk unavailable')
    writer = diag._DiagnosticWriter(sink=failing_sink)
    writer.submit('fail', 'fail\n'); writer.submit('recovery', 'recovery\n')
    assert writer.flush(2) and writer.close(2)
    assert attempts == ['fail', 'recovery']

    with tempfile.TemporaryDirectory(prefix='hybrid-diag-') as tmp:
        root = Path(tmp)
        paths = (root/'first'/'diag.log', root/'second'/'diag.log')
        with patch.object(diag, 'DIAG_PATHS', paths):
            diag._reset_after_fork()
            diag.write_multicamera_diag('[MULTI_CAMERA_DIAG][camera-a][camera_id=%s] event %s', 1, 'saved')
            assert diag._writer.flush(2)
            first = paths[0].read_text()
            assert first == paths[1].read_text()
            assert f'pid={os.getpid()} profile_id=camera-a camera_id=1 event=' in first
            assert first.endswith('[MULTI_CAMERA_DIAG][camera-a][camera_id=1] event saved\n')
            diag.write_multicamera_diag('x' * (diag.MAX_RECORD_CHARS * 2))
            assert diag._writer.flush(2)
            assert paths[0].read_text().endswith(' [diagnostic truncated]\n')
            assert diag._writer.close(2)
            diag._reset_after_fork()

            # Fork while parent owns initialization lock and has blocked file I/O.
            entered.clear(); release.clear()
            parent = diag._DiagnosticWriter(sink=slow_sink, capacity=2)
            diag._writer = parent
            parent.submit('parent-only', 'parent-only\n'); assert entered.wait(1)
            diag._writer_lock.acquire()
            child = multiprocessing.get_context('fork').Process(target=child_record)
            try:
                child.start(); child.join(3)
                assert child.exitcode == 0, 'Child reused parent writer/lock or failed to drain on exit'
            finally:
                if child.is_alive(): child.terminate(); child.join(2)
                diag._writer_lock.release(); release.set(); assert parent.close(2)
                diag._reset_after_fork()
            text = paths[0].read_text()
            assert f'pid={child.pid} profile_id=child camera_id=2' in text
            assert text.count('child event') == 1 and 'parent-only' not in text
            assert text == paths[1].read_text()

        # A failed destination must not prevent the second one, nor raise.
        with patch.object(diag, 'DIAG_PATHS', (root/'first'/'diag.log'/'invalid', root/'valid.log')):
            diag._write_record('ok', 'ok\n')
            assert (root/'valid.log').read_text() == 'ok\n'
    with patch.object(diag, '_DiagnosticWriter', side_effect=RuntimeError('thread unavailable')):
        diag.write_multicamera_diag('must not interrupt capture')
    assert diag._writer is None
    print('Diagnostics: nonblocking stalled sink, bounded overflow/close, recovery, file parity, fork locks and worker-exit drain: PASS')


if __name__ == '__main__': run()
