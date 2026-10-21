"""Bounded, read-only Linux scheduling/I/O evidence for a live timed-out child.

No command line, environment, file paths, mappings or memory contents are read.
Counters are snapshots, not proof of the cause of a timeout. Collection performs
no subprocess calls, retries, sleeps or directory-wide materialization.
"""
import json
import os
from pathlib import Path


MAX_THREADS = 8
MAX_READ_BYTES = 16384
MAX_LOG_BYTES = 12288


def collect_timeout_diagnostics(pid, *, proc_root='/proc', max_threads=MAX_THREADS,
                                max_read_bytes=MAX_READ_BYTES):
    root = Path(proc_root)
    result = dict(pid=pid, available=False, threads=[], errors=[], read_bytes=0,
                  read_limit_reached=False, threads_limited=False)
    if type(pid) is not int or pid <= 0:
        result['errors'].append('invalid_pid')
        return result
    # Callers cannot accidentally remove the production bounds.
    max_threads = max(1, min(int(max_threads), MAX_THREADS))
    remaining = max(0, min(int(max_read_bytes), MAX_READ_BYTES))

    def error(label, exc):
        if len(result['errors']) < 8:
            result['errors'].append('%s:errno=%s' % (label, getattr(exc, 'errno', None)))

    def read(relative, limit):
        nonlocal remaining
        limit = min(limit, remaining)
        if limit <= 0:
            result['read_limit_reached'] = True
            return ''
        try:
            # proc counters are regular virtual files. Each read has a hard
            # size bound; never follow a stream until EOF or wait for a process.
            descriptor = os.open(root / relative, os.O_RDONLY | os.O_NONBLOCK | os.O_CLOEXEC)
            try:
                data = os.read(descriptor, limit)
            finally:
                os.close(descriptor)
        except OSError as exc:
            error(relative, exc)
            return ''
        remaining -= len(data)
        result['read_bytes'] += len(data)
        if len(data) == limit:
            result['read_limit_reached'] = True
        return data.decode('ascii', errors='replace')

    def fields(text, wanted):
        parsed = {}
        for line in text.splitlines():
            key, separator, value = line.partition(':')
            if separator and key in wanted:
                parsed[key] = value.strip()[:80]
        return parsed

    def scheduling(relative):
        value = read(relative, 128).split()
        if len(value) == 3 and all(v.isdecimal() and len(v) <= 24 for v in value):
            return dict(zip(('cpu_ns', 'runqueue_ns', 'timeslices'), map(int, value)))
        return None

    base = str(pid)
    status = read(base + '/status', 2048)
    result['available'] = bool(status)
    result['status'] = fields(status, {'State', 'Threads', 'VmRSS', 'VmSwap',
                                       'voluntary_ctxt_switches', 'nonvoluntary_ctxt_switches'})
    result['io'] = fields(read(base + '/io', 1024),
                          {'rchar', 'wchar', 'syscr', 'syscw', 'read_bytes',
                           'write_bytes', 'cancelled_write_bytes'})
    ids = [pid]
    try:
        with os.scandir(root / base / 'task') as entries:
            for scanned, entry in enumerate(entries):
                if scanned >= max_threads:
                    result['threads_limited'] = True
                    break
                if not entry.name.isdecimal() or len(entry.name) > 20 or int(entry.name) == pid:
                    continue
                if len(ids) >= max_threads:
                    result['threads_limited'] = True
                    break
                ids.append(int(entry.name))
    except OSError as exc:
        error(base + '/task', exc)
    for identity in ids:
        thread = '%s/task/%s' % (base, identity)
        result['threads'].append(dict(
            tid=identity,
            status=fields(read(thread + '/status', 256), {'State'}),
            wchan=read(thread + '/wchan', 128).strip()[:80],
            schedstat=scheduling(thread + '/schedstat'),
        ))
    result['memory'] = fields(read('meminfo', 4096),
                               {'MemAvailable', 'SwapTotal', 'SwapFree', 'Dirty', 'Writeback'})
    vm = {}
    for line in read('vmstat', 4096).splitlines():
        parts = line.split()
        if len(parts) != 2:
            continue
        key, value = parts
        if (key in ('pgmajfault', 'pswpin', 'pswpout', 'oom_kill')
                or key.startswith(('pgscan_', 'allocstall_'))):
            if value.isdecimal() and len(value) <= 24:
                vm[key] = int(value)
    result['vmstat'] = vm
    result['pressure'] = {name: read('pressure/' + name, 384).strip()[:256]
                          for name in ('cpu', 'io', 'memory')}
    return result


def timeout_diagnostics_json(pid, **kwargs):
    """Bound the final log payload too, including adversarial/partial reads."""
    result = collect_timeout_diagnostics(pid, **kwargs)
    result['payload_limited'] = False
    encoded = json.dumps(result, separators=(',', ':'), ensure_ascii=True)
    if len(encoded.encode('ascii')) <= MAX_LOG_BYTES:
        return encoded
    # A bounded summary is preferable to truncating JSON or dumping unbounded
    # diagnostics. Keep main-thread evidence and aggregate counters when possible.
    result['payload_limited'] = True
    while len(result['threads']) > 1:
        result['threads'].pop()
        encoded = json.dumps(result, separators=(',', ':'), ensure_ascii=True)
        if len(encoded) <= MAX_LOG_BYTES:
            return encoded
    return json.dumps(dict(pid=result['pid'], available=result['available'],
                           read_bytes=result['read_bytes'], payload_limited=True,
                           errors=['diagnostic_payload_limit']), separators=(',', ':'))
