#!/usr/bin/env python3
"""Persistent, bounded archive-observer log tail behavior on temporary files."""
import importlib.util
from pathlib import Path
import tempfile


def load_observer():
    path = Path(__file__).parent / 'operational' / 'observe_archive.py'
    spec = importlib.util.spec_from_file_location('observe_archive_fixture', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def run():
    observer = load_observer()
    with tempfile.TemporaryDirectory(prefix='observe-archive-log-') as directory:
        log = Path(directory) / 'indi-allsky.log'
        log.write_bytes(b'old startup line\n')
        tail = observer.LogTail(log, max_bytes=128)
        try:
            with log.open('ab') as stream:
                stream.write(b'[ERROR] Starlink provider HTTP 403\n')
                stream.write(b'[CRITICAL] Capture worker stopped token=private-value\n')
            sample = tail.read()
            assert sample['error_count'] == sample['error_lines'] == 2
            assert 'Starlink provider HTTP 403' in sample['error_details'][0]
            assert 'Capture worker stopped' in sample['error_details'][1]
            assert 'private-value' not in sample['error_details'][1]
            assert not sample['read_capped'] and not sample['gap_detected']

            rotated = log.with_suffix('.log.1')
            log.rename(rotated)
            with rotated.open('ab') as stream:
                stream.write(b'[ERROR] tail from renamed file\n')
            log.write_bytes(b'[CRITICAL] first line in new file\n')
            sample = tail.read()
            assert sample['rotation_detected']
            assert sample['rotation_gap_possible']
            assert not sample['gap_detected']
            assert sample['error_count'] == 2
            assert 'renamed file' in sample['error_details'][0]
            assert 'new file' in sample['error_details'][1]

            with log.open('ab') as stream:
                stream.write(b'x' * 160 + b'\n[ERROR] after cap\n')
            sample = tail.read()
            assert sample['bytes'] == 128 and sample['read_capped']
            sample = tail.read()
            assert sample['error_count'] == 1 and 'after cap' in sample['error_details'][0]

            with log.open('ab') as stream:
                stream.write(b'z' * 124 + b'[ERROR] split marker' + b'q' * 5000 + b'\nTraceback split check\n')
            first = tail.read()
            assert first['read_capped']
            counted = first['error_count']
            fragment_truncated = first['line_fragment_truncated']
            while first['read_capped']:
                first = tail.read()
                counted += first['error_count']
                fragment_truncated = fragment_truncated or first['line_fragment_truncated']
            assert counted == 2 and fragment_truncated

            log.write_bytes(b'[ERROR] after copytruncate\n')
            sample = tail.read()
            assert sample['copytruncate_detected'] and sample['gap_detected']
            assert sample['gap_reasons'] == ['copytruncate']
            assert sample['error_count'] == 1 and 'after copytruncate' in sample['error_details'][0]

            log.rename(rotated)
            missing = tail.read()
            assert missing['gap_reasons'] == ['rotation_path_missing']
            log.write_bytes(b'[ERROR] resumed after missing path\n')
            resumed = tail.read()
            assert resumed['error_count'] == 1
            assert 'resumed after missing path' in resumed['error_details'][0]
        finally:
            tail.close()
    print('Archive observer persistent log tail rotation, cap and copytruncate PASS')


if __name__ == '__main__':
    run()
