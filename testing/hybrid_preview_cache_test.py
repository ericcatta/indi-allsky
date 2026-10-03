#!/usr/bin/env python3
"""Bounded regeneration, corruption recovery and real process concurrency."""
from contextlib import redirect_stderr
import hashlib
import multiprocessing
import os
from pathlib import Path
import sys
import time
from tempfile import TemporaryDirectory
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from indi_allsky.preview_cache import PreviewCache


def key(value):
    return hashlib.sha256(value.encode()).hexdigest()


def concurrent_reader(root, ready, output):
    cache=PreviewCache(root,max_bytes=1024,max_entries=4)
    ready.wait(10)
    def render():
        with (Path(root)/'renders.txt').open('a') as stream:stream.write('render\n')
        return b'the same complete frame'
    output.put(cache.get_or_create(key('shared'),render))


def distinct_reader(root, identity, ready, output):
    cache=PreviewCache(root)
    ready.wait(10)
    def render():
        with (Path(root)/'activity.txt').open('a') as stream:stream.write('start:'+identity+'\n')
        time.sleep(0.05)
        with (Path(root)/'activity.txt').open('a') as stream:stream.write('end:'+identity+'\n')
        return identity.encode()
    output.put(cache.get_or_create(identity,render))


def held_renderer(root, started, release):
    def render():
        started.set();release.wait(10)
        return b'cold frame'
    PreviewCache(root).get_or_create('1'*63+'2',render)


def warm_reader(root, output):
    output.put(PreviewCache(root).get_or_create('1'*64,
        lambda:(_ for _ in ()).throw(AssertionError('Cached frame should exist'))))


with TemporaryDirectory() as directory:
    root=Path(directory)/'cache';cache=PreviewCache(root,max_bytes=160,max_entries=2)
    original=Path(directory)/'source.fit';original.write_bytes(b'scientific source')
    assert cache.get_or_create(key('one'),lambda:b'a'*10)==b'a'*10
    cache.get_or_create(key('two'),lambda:b'b'*10)
    os.utime(root/(key('one')+'.cache'),ns=(100,100))
    os.utime(root/(key('two')+'.cache'),ns=(200,200))
    assert cache.get_or_create(key('one'),lambda:(_ for _ in ()).throw(AssertionError('Repeated rendering')))==b'a'*10
    cache.get_or_create(key('three'),lambda:b'c'*10)
    assert not (root/(key('two')+'.cache')).exists(), 'Evict least recently accessed'
    assert sum(p.stat().st_size for p in root.glob('*.cache'))<=160
    assert len(list(root.glob('*.cache')))==2
    path=root/(key('one')+'.cache');path.write_bytes(b'corrupt or partial')
    assert cache.get_or_create(key('one'),lambda:b'rebuilt')==b'rebuilt'
    path.unlink();path.symlink_to(original)
    assert cache.get_or_create(key('one'),lambda:b'rebuilt')==b'rebuilt'
    assert original.read_bytes()==b'scientific source'
    try:cache.get_or_create('../escape',lambda:b'x')
    except ValueError:pass
    else:raise AssertionError('Traversal accepted')
    before=set(root.glob('*.cache'))
    assert cache.get_or_create(key('too-big'),lambda:b'x'*500)==b'x'*500
    assert set(root.glob('*.cache'))==before
    try:cache.get_or_create(key('failure'),lambda:(_ for _ in ()).throw(ValueError('Failed rendering')))
    except ValueError:pass
    else:raise AssertionError('Failed rendering swallowed')
    assert not (root/(key('failure')+'.cache')).exists()
    with patch.object(cache,'_publish',side_effect=OSError('No space')):
        assert cache.get_or_create(key('no-space'),lambda:b'usable')==b'usable'
    part=root/'abandoned.part';part.write_bytes(b'partial');os.utime(part,(1,1))
    cache.get_or_create(key('fresh'),lambda:b'new')
    assert not part.exists()
    cache.clear();assert not list(root.glob('*.cache'))
    assert original.read_bytes()==b'scientific source'
    assert cache.get_or_create(key('one'),lambda:b'regenerated')==b'regenerated'
    disabled=PreviewCache(root/'disabled',max_bytes=0)
    assert disabled.get_or_create(key('one'),lambda:b'no-cache')==b'no-cache'
    assert not list(disabled.root.glob('*.cache'))
    # Independent processes exercise the same locks as concurrent Gunicorn workers.
    parallel=root/'parallel';parallel.mkdir()
    ctx=multiprocessing.get_context('fork');event=ctx.Event();out=ctx.Queue()
    workers=[ctx.Process(target=concurrent_reader,args=(parallel,event,out)) for _ in range(4)]
    for worker in workers:worker.start()
    event.set()
    results=[out.get(timeout=15) for _ in workers]
    for worker in workers:
        worker.join(15);assert worker.exitcode==0
    assert results==[b'the same complete frame']*4
    assert (parallel/'renders.txt').read_text()=='render\n'
    assert len(list(parallel.glob('*.cache')))==1
    assert not list(parallel.glob('*.part'))
    # Different keys/lock stripes must still share the expensive-render slot.
    event.clear()
    workers=[ctx.Process(target=distinct_reader,args=(parallel,identity,event,out))
             for identity in ('1'*64,'2'*64)]
    for worker in workers:worker.start()
    event.set()
    assert sorted(out.get(timeout=15) for _ in workers)==[b'1'*64,b'2'*64]
    for worker in workers:
        worker.join(15);assert worker.exitcode==0
    events=(parallel/'activity.txt').read_text().splitlines()
    assert [item.split(':')[0] for item in events]==['start','end','start','end']
    started=ctx.Event();release=ctx.Event()
    cold=ctx.Process(target=held_renderer,args=(parallel,started,release));cold.start()
    warm=ctx.Process(target=warm_reader,args=(parallel,out))
    try:
        assert started.wait(10)
        warm.start()
        assert out.get(timeout=3)==b'1'*64, 'Warm read blocked behind a cold reconstruction'
    finally:
        release.set();cold.join(15)
        if warm.pid is not None:warm.join(15)
    assert cold.exitcode==0 and warm.exitcode==0
print('Preview cache: bounded LRU, corruption/eviction regeneration, source isolation, failure handling and cross-process single rendering: PASS')
