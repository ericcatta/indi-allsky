"""Bounded Unix syslog delivery without socket I/O on capture/request threads."""
from collections import deque
import errno
import logging
from logging.handlers import SysLogHandler
import os
import socket
import threading
import weakref


MAX_PENDING_RECORDS = 2048
MAX_MESSAGE_BYTES = 16384
_handlers = weakref.WeakSet()


class _Sender:
    def __init__(self, address, loss_message, capacity=MAX_PENDING_RECORDS):
        self.address = address
        self.loss_message = loss_message
        self.capacity = capacity
        self.records = deque()
        self.condition = threading.Condition()
        self.socket = None
        self.stopping = False
        self.active = False
        self.dropped = 0
        self.dropped_important = 0
        self.thread = threading.Thread(target=self.run, name='hybrid-syslog', daemon=True)
        self.thread.start()

    def submit(self, level, payload):
        with self.condition:
            if self.stopping:
                return
            if len(self.records) >= self.capacity:
                # Preserve warning/error messages ahead of lower-priority noise.
                victim = next((i for i, (queued_level, _) in enumerate(self.records)
                               if queued_level < level), None) if level >= logging.WARNING else None
                lost_level = level
                if victim is not None:
                    lost_level = self.records[victim][0]
                    del self.records[victim]
                self.dropped += 1
                self.dropped_important += int(lost_level >= logging.WARNING)
                if victim is None:
                    return
            self.records.append((level, payload))
            self.condition.notify()

    def drain(self, timeout=0.2):
        with self.condition:
            return self.condition.wait_for(lambda: not self.records and not self.active, timeout)

    def close(self, timeout=0.2):
        with self.condition:
            self.stopping = True
            self.condition.notify()
        self.thread.join(timeout)
        return not self.thread.is_alive()

    def send(self, payload):
        if self.socket is None:
            sock = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
            sock.settimeout(0.2)
            try:
                sock.connect(self.address)
            except OSError as error:
                sock.close()
                if error.errno != errno.EPROTOTYPE:
                    raise
                sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
                sock.settimeout(0.2)
                try:
                    sock.connect(self.address)
                except OSError:
                    sock.close()
                    raise
            self.socket = sock
        self.socket.sendall(payload)

    def deliver(self, payload):
        while True:
            try:
                self.send(payload)
                return True
            except OSError as error:
                # Unix datagram limits differ across hosts. A permanently
                # oversized record must not prevent delivery of later logs.
                if error.errno == errno.EMSGSIZE and len(payload) > 256:
                    prefix = payload[:len(payload) // 2].decode('utf-8', errors='ignore')
                    payload = prefix.encode('utf-8') + b' [log truncated for transport]\x00'
                if self.socket is not None:
                    self.socket.close()
                    self.socket = None
                with self.condition:
                    if self.stopping:
                        return False
                    self.condition.wait(timeout=0.1)

    def run(self):
        try:
            while True:
                with self.condition:
                    self.condition.wait_for(lambda: self.records or self.stopping)
                    if not self.records:
                        return
                    _, payload = self.records.popleft()
                    lost, important = self.dropped, self.dropped_important
                    self.dropped = self.dropped_important = 0
                    self.active = True
                try:
                    if lost and not self.deliver(self.loss_message(lost, important)):
                        return
                    if not self.deliver(payload):
                        return
                finally:
                    with self.condition:
                        self.active = False
                        self.condition.notify_all()
        finally:
            if self.socket is not None:
                self.socket.close()
                self.socket = None


class AsyncUnixSysLogHandler(logging.Handler):
    """Same facility/priority/text/null wire format as local SysLogHandler.

    Pending messages are bounded and best effort during saturation/shutdown.
    Socket failures retry in the sender, never recursively through logging.
    """
    def __init__(self, address='/dev/log', facility=SysLogHandler.LOG_USER):
        super().__init__()
        if not isinstance(address, str):
            raise ValueError('AsyncUnixSysLogHandler requires a local Unix socket path')
        self.address = address
        self.facility = SysLogHandler.facility_names[facility] if isinstance(facility, str) else facility
        self.sender = None
        self.sender_lock = threading.Lock()
        self._finalizer = None
        _handlers.add(self)

    def wire_message(self, levelname, text):
        priority = SysLogHandler.priority_names[SysLogHandler.priority_map.get(levelname, 'warning')]
        body = text.encode('utf-8')
        if len(body) > MAX_MESSAGE_BYTES:
            body = body[:MAX_MESSAGE_BYTES].decode('utf-8', errors='ignore').encode('utf-8') + b' [log truncated]'
        return ('<%d>' % ((self.facility << 3) | priority)).encode('ascii') + body + b'\x00'

    def loss_message(self, count, important):
        return self.wire_message('WARNING',
            '[WARNING] [ASYNC_SYSLOG] pid=%d dropped_records=%d warning_or_higher=%d reason=queue_full'
            % (os.getpid(), count, important))

    def emit(self, record):
        if self._closed:
            return
        # Freeze mutable args/tracebacks while the caller still owns them. Only
        # formatted bytes enter the queue, never image arrays or exception frames.
        try:
            payload = self.wire_message(record.levelname, self.format(record))
            with self.sender_lock:
                if self.sender is None:
                    self.sender = _Sender(self.address, self.loss_message)
                    from multiprocessing.util import Finalize
                    self._finalizer = Finalize(None, self.close, exitpriority=10)
                sender = self.sender
            sender.submit(record.levelno, payload)
        except Exception:
            # A logging failure must not become a capture failure. Do not use
            # handleError here: it can synchronously write to a blocked stderr.
            return

    def flush(self, timeout=0.2):
        return self.sender is None or self.sender.drain(timeout)

    def close(self):
        if self._finalizer is not None:
            self._finalizer.cancel()
            self._finalizer = None
        if self.sender is not None:
            self.sender.close(timeout=0.2)
        super().close()

    def after_fork(self):
        if self.sender is not None and self.sender.socket is not None:
            self.sender.socket.close()
        self.sender = None
        self.sender_lock = threading.Lock()
        if self._finalizer is not None:
            self._finalizer.cancel()
            self._finalizer = None


def _after_fork():
    for handler in _handlers:
        handler.after_fork()


os.register_at_fork(after_in_child=_after_fork)
