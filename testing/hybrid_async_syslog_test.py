#!/usr/bin/env python3
"""Real local syslog saturation, recovery, priorities and fork-safe shutdown."""
import ast
import logging
from logging.handlers import SysLogHandler
import multiprocessing
import os
from pathlib import Path
import socket
import sys
import tempfile
import threading
import time
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from indi_allsky.async_syslog import AsyncUnixSysLogHandler, _Sender, MAX_MESSAGE_BYTES
from run_hybrid_regression import source_hashes


def record(text, level=logging.INFO, args=()):
    return logging.LogRecord('fixture', level, __file__, 1, text, args, None, 'caller')


def fork_emit(handler):
    handler.handle(record('child'))


def run():
    entered, release = threading.Event(), threading.Event()
    delivered = []
    def stalled(payload):
        entered.set(); assert release.wait(5)
        delivered.append(payload)
    sender = _Sender('unused', lambda n, important: f'dropped={n} important={important}'.encode(), capacity=2)
    with patch.object(sender, 'send', side_effect=stalled):
        try:
            sender.submit(logging.INFO, b'active'); assert entered.wait(1)
            sender.submit(logging.INFO, b'info')
            sender.submit(logging.WARNING, b'warning')
            sender.submit(logging.INFO, b'dropped-info')
            sender.submit(logging.ERROR, b'error')
            sender.submit(logging.CRITICAL, b'critical')
            assert len(sender.records) == 2 and sender.dropped == 3 and sender.dropped_important == 1
            assert not sender.drain(.02)
            start = time.monotonic(); assert not sender.close(.02)
            assert time.monotonic() - start < .2
        finally:
            release.set(); assert sender.close(2)
    assert delivered == [b'active', b'dropped=3 important=1', b'error', b'critical'], delivered

    with tempfile.TemporaryDirectory(prefix='hybrid-syslog-', dir='/tmp') as tmp:
        address = str(Path(tmp)/'socket')
        server = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
        server.bind(address); server.settimeout(3)
        handler = AsyncUnixSysLogHandler(address, 'local6')
        handler.setFormatter(logging.Formatter('[%(levelname)s] %(threadName)s %(message)s'))
        try:
            # Do not drain the receiver: fill the kernel's Unix datagram queue.
            start = time.monotonic()
            for i in range(200): handler.handle(record('message %d', args=(i,)))
            elapsed = time.monotonic() - start
            assert elapsed < .5, 'Producer waited for the saturated syslog socket'
            assert not handler.flush(.05)
            packets = []
            def receive():
                for _ in range(200): packets.append(server.recv(65536))
            reader = threading.Thread(target=receive); reader.start()
            assert handler.flush(3); reader.join(3); assert not reader.is_alive()
            assert packets == [f'<182>[INFO] MainThread message {i}\x00'.encode() for i in range(200)]
            mutable = ['original']
            handler.handle(record('mutable=%s', args=(mutable,))); mutable[0] = 'changed'
            assert handler.flush(2)
            assert b"['original']" in server.recv(65536)
            handler.handle(record('é' * MAX_MESSAGE_BYTES)); assert handler.flush(2)
            packet = server.recv(65536); packet.decode('utf-8')
            assert len(packet) < MAX_MESSAGE_BYTES + 80 and (packet.endswith(b' [log truncated]\x00') or packet.endswith(b' [log truncated for transport]\x00'))
            # Compare the unchanged facility/priority/text wire contract directly.
            standard = SysLogHandler(address=address, facility='local6'); standard.setFormatter(handler.formatter)
            msg = record('failure %s', logging.ERROR, ('sample',))
            standard.emit(msg); expected = server.recv(65536); standard.close()
            handler.handle(msg); assert handler.flush(2); assert server.recv(65536) == expected
        finally:
            handler.close(); server.close()

        # Destination absent at first, then available: retry the original message.
        address = str(Path(tmp)/'recovery')
        handler = AsyncUnixSysLogHandler(address, 'local7')
        handler.handle(record('retained during outage'))
        assert not handler.flush(.05)
        server = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM); server.bind(address); server.settimeout(3)
        try:
            assert handler.flush(3)
            assert server.recv(65536) == b'<190>retained during outage\x00'
        finally: handler.close(); server.close()

        # Fork while parent logging and initialization locks are held and its
        # sender is stalled. Child must own a new sender, and drain at exit.
        address = str(Path(tmp)/'fork')
        server = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM); server.bind(address); server.settimeout(3)
        handler = AsyncUnixSysLogHandler(address, 'local6')
        parent = _Sender(address, handler.loss_message)
        parent.socket = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
        parent.socket.connect(address)
        handler.sender = parent
        entered.clear(); release.clear()
        with patch.object(parent, 'send', side_effect=stalled):
            parent.submit(logging.INFO, b'parent-only'); assert entered.wait(1)
            handler.acquire(); handler.sender_lock.acquire()
            child = multiprocessing.get_context('fork').Process(target=fork_emit, args=(handler,))
            try:
                child.start(); child.join(3)
                assert child.exitcode == 0, 'Child inherited stopped sender or held locks'
                assert server.recv(65536) == b'<182>child\x00'
                parent.socket.send(b'parent socket still open')
                assert server.recv(65536) == b'parent socket still open'
            finally:
                if child.is_alive(): child.terminate(); child.join(2)
                handler.sender_lock.release(); handler.release(); release.set(); handler.close(); server.close()
        handler = AsyncUnixSysLogHandler(str(Path(tmp)/'missing'))
        handler.handle(record('outage at shutdown'))
        start = time.monotonic(); handler.close()
        assert time.monotonic() - start < .5

    for file in ('allsky.py', 'indi_allsky/wsgi.py'):
        tree = ast.parse((ROOT/file).read_text())
        assignment = next(n for n in tree.body if isinstance(n, ast.Assign)
                          and any(isinstance(t, ast.Name) and t.id == 'LOG_HANDLER_SYSLOG' for t in n.targets))
        assert isinstance(assignment.value.func, ast.Name) and assignment.value.func.id == 'AsyncUnixSysLogHandler'
    assert "'class'     : 'indi_allsky.async_syslog.AsyncUnixSysLogHandler'" in (ROOT/'indi_allsky/flask/__init__.py').read_text()
    assert 'allsky.py' in source_hashes(ROOT)
    print('Async syslog: real saturation without caller stall, byte parity, outage recovery, priority overflow, fork locks and bounded shutdown: PASS')


if __name__ == '__main__': run()
