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
import shutil
import sqlite3
import subprocess
import time


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
        stat = log.stat()
        log_inode, offset = stat.st_ino, stat.st_size
        emit(dict(event='start', utc=started, duration_seconds=args.hours * 3600,
                  checkout=command('git', '-C', args.repository, 'rev-parse', 'HEAD'),
                  config_revision=db.execute('SELECT MAX(id) FROM config').fetchone()[0],
                  camera_cursors=latest, image_cursor=cursor,
                  log_inode=log_inode, log_offset=offset, interval_seconds=60))
        previous = start
        try:
            while True:
                now = time.monotonic()
                record = dict(event='sample', utc=dt.datetime.now(dt.timezone.utc).isoformat(),
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
                    stat = log.stat()
                    record['log_gap'] = stat.st_ino != log_inode or stat.st_size < offset
                    if record['log_gap']:
                        offset = 0
                    with log.open('rb') as logstream:
                        logstream.seek(offset)
                        chunk = logstream.read(8 * 1024 * 1024)
                        record['log_read_capped'] = logstream.tell() < stat.st_size
                        next_offset = logstream.tell()
                    record['log_error_lines'] = sum(
                        b'[ERROR]' in line or b'[CRITICAL]' in line or b'Traceback' in line
                        for line in chunk.splitlines())
                    record['log_bytes'] = len(chunk)
                    record['log_inode'] = stat.st_ino
                    record['log_offset'] = next_offset
                    emit(record)
                    if rows:
                        cursor = rows[-1][0]
                    offset, log_inode = next_offset, stat.st_ino
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
