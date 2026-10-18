#!/usr/bin/env python3
"""Read-only, bounded 24-hour Pi observation. Never changes capture or media.

JSONL records are evidence, not an automatic pass verdict. Review sampling gaps,
log rotation gaps, frame intervals, errors and source publication after collection.
"""
import argparse
import datetime as dt
import json
import os
from pathlib import Path
import re
import shutil
import sqlite3
import subprocess
import time


MAX_LOG_READ_BYTES = 8 * 1024 * 1024
MAX_LOG_ERROR_LINES = 100
MAX_LOG_LINE_BYTES = 4096
SENSITIVE_LOG_VALUE = re.compile(
    r'(?i)(password|passwd|secret|token|api[_-]?key|authorization)(\s*[:=]\s*)([^\s,;]+)')


def safe_log_line(line):
    text = line[:MAX_LOG_LINE_BYTES].decode('utf-8', 'replace')
    return SENSITIVE_LOG_VALUE.sub(r'\1\2[REDACTED]', text)


class LogTail:
    """Bounded persistent tail which drains a renamed file before reopening."""

    def __init__(self, path, *, start_at_end=True, max_bytes=MAX_LOG_READ_BYTES):
        self.path = Path(path)
        self.max_bytes = max_bytes
        self.stream = self.path.open('rb')
        self.inode = os.fstat(self.stream.fileno()).st_ino
        self.line_prefix = b''
        self.line_tail = b''
        self.line_bytes = 0
        self.line_matches = False
        if start_at_end:
            self.stream.seek(0, os.SEEK_END)

    @property
    def offset(self):
        return self.stream.tell()

    def close(self):
        self.stream.close()

    def _open_current(self):
        new_stream = self.path.open('rb')
        new_inode = os.fstat(new_stream.fileno()).st_ino
        old_stream = self.stream
        self.stream = new_stream
        self.inode = new_inode
        old_stream.close()

    def _error_records(self, data):
        count = 0
        details = []
        truncated = False
        parts = data.split(b'\n')
        for index, part in enumerate(parts):
            joined = self.line_tail + part
            if any(marker in joined for marker in (b'[ERROR]', b'[CRITICAL]', b'Traceback')):
                self.line_matches = True
            available = MAX_LOG_LINE_BYTES - len(self.line_prefix)
            if available > 0:
                self.line_prefix += part[:available]
            self.line_bytes += len(part)
            self.line_tail = joined[-16:]
            if index == len(parts) - 1:
                continue
            if self.line_matches:
                count += 1
                if len(details) < MAX_LOG_ERROR_LINES:
                    details.append(safe_log_line(self.line_prefix))
            truncated = truncated or self.line_bytes > MAX_LOG_LINE_BYTES
            self.line_prefix = b''
            self.line_tail = b''
            self.line_bytes = 0
            self.line_matches = False
        return count, details, truncated or self.line_bytes > MAX_LOG_LINE_BYTES

    def read(self):
        chunks = []
        remaining = self.max_bytes
        rotated = False
        copytruncate = False
        rotation_pending = False
        gap_reasons = []

        try:
            path_stat = self.path.stat()
        except FileNotFoundError:
            return {
                'bytes': 0, 'inode': self.inode, 'offset': self.offset,
                'read_capped': False, 'rotation_detected': False,
                'rotation_pending_old_fd': True, 'rotation_gap_possible': True,
                'copytruncate_detected': False, 'gap_detected': True,
                'gap_reasons': ['rotation_path_missing'], 'gap': True,
                'error_count': 0, 'error_lines': 0, 'error_details': [],
                'error_details_capped': False,
                'line_fragment_truncated': self.line_bytes > MAX_LOG_LINE_BYTES,
            }
        if path_stat.st_ino == self.inode and path_stat.st_size < self.offset:
            # Bytes written and removed between samples cannot be reconstructed.
            copytruncate = True
            gap_reasons.append('copytruncate')
            self.stream.seek(0)

        if path_stat.st_ino != self.inode:
            rotated = True
            chunk = self.stream.read(remaining)
            chunks.append(chunk)
            remaining -= len(chunk)
            if remaining == 0:
                rotation_pending = bool(self.stream.read(1))
                if rotation_pending:
                    self.stream.seek(-1, os.SEEK_CUR)
            if not rotation_pending:
                # The old descriptor reached EOF. A second rotation before this
                # reopen cannot be reconstructed from the current pathname.
                before = self.path.stat().st_ino
                try:
                    self._open_current()
                except FileNotFoundError:
                    rotation_pending = True
                    gap_reasons.append('rotation_path_missing')
                else:
                    after = self.inode
                    if before != after:
                        gap_reasons.append('multiple_rotations_during_reopen')

        if remaining and not rotation_pending:
            chunk = self.stream.read(remaining)
            chunks.append(chunk)
            remaining -= len(chunk)

        current_stat = os.fstat(self.stream.fileno())
        capped = remaining == 0 and self.offset < current_stat.st_size
        data = b''.join(chunks)
        error_count, error_details, fragment_truncated = self._error_records(data)
        return {
            'bytes': len(data),
            'inode': self.inode,
            'offset': self.offset,
            'read_capped': capped or rotation_pending,
            'rotation_detected': rotated,
            'rotation_pending_old_fd': rotation_pending,
            'rotation_gap_possible': rotated,
            'copytruncate_detected': copytruncate,
            'gap_detected': bool(gap_reasons),
            'gap_reasons': gap_reasons,
            'gap': bool(gap_reasons) or rotated,
            'error_count': error_count,
            'error_lines': error_count,
            'error_details': error_details,
            'error_details_capped': error_count > len(error_details),
            'line_fragment_truncated': fragment_truncated,
        }


def command(*args):
    return subprocess.check_output(args, text=True, timeout=10).strip()


def run(args):
    output = Path(args.output)
    # Exclusive creation prevents a retry overwriting an unfinished observation.
    with output.open('x') as stream:
        def emit(record):
            stream.write(json.dumps(record, separators=(',', ':')) + '\n')
            stream.flush()
            os.fsync(stream.fileno())

        db = sqlite3.connect('file:' + args.database + '?mode=ro', uri=True,
                             timeout=5)
        db.execute('PRAGMA query_only=ON')
        latest = db.execute('SELECT camera_id, MAX(id) FROM image GROUP BY camera_id').fetchall()
        cursor = max((row[1] for row in latest), default=0)
        start = time.monotonic()
        started = dt.datetime.now(dt.timezone.utc).isoformat()
        log = Path(args.log)
        log_tail = LogTail(log)
        emit(dict(event='start', utc=started, duration_seconds=args.hours * 3600,
                  checkout=command('git', '-C', args.repository, 'rev-parse', 'HEAD'),
                  config_revision=db.execute('SELECT MAX(id) FROM config').fetchone()[0],
                  camera_cursors=latest, image_cursor=cursor,
                  log_inode=log_tail.inode, log_offset=log_tail.offset,
                  log_read_limit_bytes=MAX_LOG_READ_BYTES,
                  log_error_line_limit=MAX_LOG_ERROR_LINES,
                  log_rotation_limit='A persistent descriptor drains one renamed file; multiple rotations between samples may leave an unobservable gap.',
                  log_copytruncate_limit='Copytruncate is detected when size falls below the saved offset; truncate-and-regrow beyond that offset between samples is not observable.',
                  interval_seconds=60))
        previous = start
        sample_index = 0
        try:
            while True:
                now = time.monotonic()
                sample_index += 1
                record = dict(event='sample', utc=dt.datetime.now(dt.timezone.utc).isoformat(),
                              sample_index=sample_index,
                              elapsed_seconds=round(now-start, 3),
                              sample_gap_seconds=round(now-previous, 3))
                try:
                    rows = db.execute('''SELECT i.id, i.camera_id, i.createDate,
                        i.night, i.fileSize, json_extract(i.data, '$.storage_format'),
                        json_extract(i.data, '$.source_fits_id'), i.filename,
                        f.filename, f.fileSize FROM image i LEFT JOIN fitsimage f
                        ON f.id=json_extract(i.data, '$.source_fits_id')
                        WHERE i.id>? ORDER BY i.id LIMIT 10000''', (cursor,)).fetchall()
                    frames = []
                    for row in rows:
                        source = row[8] if row[5] == 'fits' else row[7]
                        path = Path(args.media) / source if source else None
                        frames.append(list(row[:7]) + [row[9], bool(path and path.is_file())])
                    record['frames'] = frames
                    record['frame_columns'] = ['id', 'camera', 'created', 'night',
                        'display_bytes', 'storage_format', 'source_fits_id', 'fits_bytes', 'file_exists']
                    record['row_limit_reached'] = len(rows) == 10000
                    record['latest_by_camera'] = db.execute(
                        'SELECT camera_id, MAX(createDate) FROM image GROUP BY camera_id').fetchall()
                    record['task_counts'] = db.execute(
                        'SELECT state, COUNT(*) FROM taskqueue GROUP BY state').fetchall()
                    record['latest_cleanup'] = db.execute('''SELECT id, createDate,state,result
                        FROM taskqueue WHERE json_extract(data,'$.action')='storagePressureCleanup'
                        ORDER BY id DESC LIMIT 1''').fetchall()
                    record['config_revision'] = db.execute('SELECT MAX(id) FROM config').fetchone()[0]
                    record['free_bytes'] = shutil.disk_usage(args.media).free
                    record['service'] = command('systemctl', '--user', 'show',
                        'indi-allsky.service', '-p', 'ActiveState', '-p', 'MainPID', '-p', 'NRestarts')
                    record['web'] = command('systemctl', '--user', 'is-active', 'gunicorn-indi-allsky.service')
                    log_sample = log_tail.read()
                    for key, value in log_sample.items():
                        record['log_' + key] = value
                    emit(record)
                    if rows:
                        cursor = rows[-1][0]
                except Exception as error:
                    record['error'] = type(error).__name__ + ': ' + str(error)
                    emit(record)
                previous = now
                if time.monotonic() - start >= args.hours * 3600:
                    emit(dict(event='end', utc=dt.datetime.now(dt.timezone.utc).isoformat(),
                              elapsed_seconds=time.monotonic()-start))
                    break
                time.sleep(min(60, max(0, args.hours * 3600-(time.monotonic()-start))))
        finally:
            log_tail.close()
            db.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True)
    parser.add_argument('--hours', type=float, default=24)
    parser.add_argument('--repository', default='/home/eric/indi-allsky')
    parser.add_argument('--database', default='/var/lib/indi-allsky/indi-allsky.sqlite')
    parser.add_argument('--media', default='/var/www/html/allsky/images')
    parser.add_argument('--log', default='/var/log/indi-allsky/indi-allsky.log')
    args = parser.parse_args()
    if not 0 < args.hours <= 48:
        parser.error('--hours must be positive and no greater than 48')
    run(args)
