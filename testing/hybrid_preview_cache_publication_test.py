#!/usr/bin/env python3
"""Disposable cache publication, plus an opt-in bounded storage benchmark.

--benchmark-root must name a scratch directory on the filesystem being measured.
The benchmark restores the former flush+fsync barrier through a temporary-file
wrapper; both variants execute the actual PreviewCache publication code.
"""
import argparse
from contextlib import contextmanager
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from indi_allsky.preview_cache import PreviewCache


class PublicationTest(unittest.TestCase):
    def test_identity_without_durability_barrier(self):
        payload = bytes(range(256)) * 4096
        key = hashlib.sha256(b'frame').hexdigest()
        with tempfile.TemporaryDirectory() as root:
            cache = PreviewCache(root)
            with patch('indi_allsky.preview_cache.os.fsync', side_effect=AssertionError('cache fsync')):
                self.assertEqual(cache.get_or_create(key, lambda: payload), payload)
                self.assertEqual(cache.get_or_create(key, lambda: self.fail('cache miss')), payload)
            self.assertEqual((Path(root) / (key + '.cache')).read_bytes(),
                             hashlib.sha256(payload).hexdigest().encode() + b'\n' + payload)
            self.assertEqual(list(Path(root).glob('*.part')), [])

    def test_lost_or_corrupt_cache_regenerates(self):
        payload = b'complete derived display bytes'
        key = hashlib.sha256(b'frame').hexdigest()
        with tempfile.TemporaryDirectory() as root:
            cache = PreviewCache(root)
            path = Path(root) / (key + '.cache')
            cache.get_or_create(key, lambda: payload)
            # Model partial persistence after a crash, including a valid header
            # whose payload no longer matches its checksum.
            for damaged in (b'', b'partial header', path.read_bytes()[:-3]):
                path.write_bytes(damaged)
                calls = []
                def render():
                    calls.append(1)
                    return payload
                self.assertEqual(cache.get_or_create(key, render), payload)
                self.assertEqual(calls, [1])
                self.assertEqual(cache.get_or_create(key, lambda: self.fail('cache miss')), payload)
            path.unlink()
            self.assertEqual(cache.get_or_create(key, lambda: payload), payload)


def benchmark(root):
    """16 x 1 MiB per variant; only private temporary subdirectories are removed."""
    root = Path(root)
    if not root.is_dir():
        raise ValueError('benchmark root must already exist')
    payload = bytes(range(256)) * 4096
    real_temporary_file = tempfile.NamedTemporaryFile
    results = []
    for durable in (True, False):
        sync_times = []
        @contextmanager
        def temporary_file(*args, **kwargs):
            with real_temporary_file(*args, **kwargs) as stream:
                yield stream
                if durable:
                    stream.flush()
                    started = time.monotonic()
                    # This is precisely the removed per-publication barrier.
                    import os
                    os.fsync(stream.fileno())
                    sync_times.append(time.monotonic() - started)
        with tempfile.TemporaryDirectory(prefix='preview-publish-bench-', dir=root) as directory:
            cache = PreviewCache(directory)
            timings = []
            with patch('indi_allsky.preview_cache.tempfile.NamedTemporaryFile', temporary_file):
                for frame in range(16):
                    key = hashlib.sha256(str(frame).encode()).hexdigest()
                    started = time.monotonic()
                    assert cache.get_or_create(key, lambda: payload) == payload
                    timings.append(time.monotonic() - started)
                    stored = (Path(directory) / (key + '.cache')).read_bytes()
                    assert stored == hashlib.sha256(payload).hexdigest().encode() + b'\n' + payload
            results.append(dict(variant='former_fsync' if durable else 'disposable_atomic',
                                publications=16, payload_bytes=len(payload),
                                fsync_count=len(sync_times), fsync_seconds=sum(sync_times),
                                publish_seconds=timings, total_seconds=sum(timings)))
    print(json.dumps({'benchmark_root': str(root.resolve()), 'results': results}, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--benchmark-root')
    args, remaining = parser.parse_known_args()
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(PublicationTest)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if not result.wasSuccessful():
        sys.exit(1)
    if args.benchmark_root:
        benchmark(args.benchmark_root)
