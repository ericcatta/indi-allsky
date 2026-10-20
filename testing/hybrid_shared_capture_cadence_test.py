#!/usr/bin/env python3
"""Deterministic shared rounds across real processes and worker integration."""
import ast
import multiprocessing
import os
import queue
from pathlib import Path
import signal
import sys
import time
from types import SimpleNamespace, ModuleType
from unittest.mock import Mock, patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from indi_allsky.shared_capture_cadence import SharedCaptureCadence


def round_for(cadence, now, *, depth=0, profiles=('one', 'two'), period=45):
    prepared, tickets = {}, {}
    for _ in range(20):
        for profile in profiles:
            if profile in tickets:
                continue
            answer = cadence.poll(profile, now=now, period=period, queue_depth=depth,
                                  prepared_round=prepared.get(profile))
            if answer['action'] == 'prepare':
                prepared[profile] = answer['round']
            elif answer['action'] == 'start':
                tickets[profile] = answer
        if len(tickets) == len(profiles):
            return tickets
    return tickets


def test_shared_policy():
    cadence = SharedCaptureCadence(('one', 'two'), now=0)
    try:
        assert len(round_for(cadence, 0)) == 2
        for now in (10, 20, 30, 40):
            cadence.heartbeat('one', now=now)
            cadence.heartbeat('two', now=now)
        assert not round_for(cadence, 40, depth=5)
        assert not round_for(cadence, 60, depth=5)
        tickets = round_for(cadence, 82.5, depth=5)
        assert len(tickets) == 2 and tickets['one'] == tickets['two']
        assert tickets['one']['epoch'] == 82.5 and tickets['one']['delay'] == 37.5
        # Drained backlog releases one shared delay, never before baseline127.5.
        for now in (100, 120):
            assert not round_for(cadence, now, depth=0)
        tickets = round_for(cadence, 127.5, depth=0)
        assert len(tickets) == 2 and tickets['one'] == tickets['two']
        assert tickets['one']['delay'] == 0
        # Long exposures renew membership past the lease while still busy.
        for now in range(140, 231, 10):
            cadence.heartbeat('one', now=now)
            cadence.heartbeat('two', now=now)
        tickets = round_for(cadence, 230)
        assert len(tickets) == 2 and tickets['one']['members'] == ('one', 'two')
        assert tickets['one']['epoch'] == 230
        assert not round_for(cadence, 230.01)  # No catch-up against old epochs.
    finally:
        cadence.close()


def test_legacy_queue_thresholds():
    for minimum, maximum in ((3, 3), (5, 3)):
        cadence = SharedCaptureCadence(('one', 'two'), now=0,
                                       queue_min=minimum, queue_max=maximum)
        try:
            assert len(round_for(cadence, 0)) == 2
            for now in (10, 20, 30, 40):
                cadence.heartbeat('one', now=now)
                cadence.heartbeat('two', now=now)
            # <=minimum wins even when this depth also reaches maximum.
            tickets = round_for(cadence, 45, depth=minimum)
            assert len(tickets) == 2 and tickets['one']['delay'] == 0
            for now in (60, 80):
                cadence.heartbeat('one', now=now)
                cadence.heartbeat('two', now=now)
            depth = minimum + 1
            assert not round_for(cadence, 90, depth=depth)
            expected_delay = depth / maximum * 45 * .5
            # Release with both peers still in their lease, without sleeping.
            due = 90 + expected_delay
            now = 100
            while now < due:
                cadence.heartbeat('one', now=now)
                cadence.heartbeat('two', now=now)
                now += 10
            tickets = round_for(cadence, due, depth=depth)
            assert len(tickets) == 2 and tickets['one']['delay'] == expected_delay
        finally:
            cadence.close()
    for options in ({'queue_min': -1}, {'queue_max': 0}, {'queue_max': -1},
                    {'queue_min': float('nan')}, {'queue_max': float('inf')},
                    {'queue_min': None}, {'queue_max': '3'},
                    {'backoff': float('nan')}, {'backoff': float('inf')}, {'backoff': -1}):
        try:
            SharedCaptureCadence(('one',), **options)
        except (ValueError, TypeError):
            pass
        else:
            raise AssertionError('Invalid queue policy accepted: %r' % options)


def test_lease_restart_and_preparation():
    cadence = SharedCaptureCadence(('one', 'two'), now=0)
    try:
        # Unfinished hook cannot consume a start grant.
        assert cadence.poll('one', now=0, period=45, queue_depth=0)['action'] == 'wait'
        prepare = cadence.poll('two', now=0, period=45, queue_depth=0)
        assert prepare == {'action': 'prepare', 'round': 1}
        assert cadence.poll('one', now=0, period=45, queue_depth=0)['action'] == 'prepare'
        assert cadence.poll('one', now=1, period=45, queue_depth=0, prepared_round=1)['action'] == 'wait'
        # two dies in its hook; a replacement cannot acknowledge old work.
        assert cadence.reset('two', now=2)
        assert cadence.poll('two', now=2, period=45, queue_depth=0)['action'] == 'prepare'
        tickets = round_for(cadence, 2)
        assert len(tickets) == 2 and tickets['one']['epoch'] == 2
        # Missing heartbeat removes a dead peer after the bounded lease.
        cadence.heartbeat('one', now=20)
        tickets = round_for(cadence, 47, profiles=('one',))
        assert len(tickets) == 1 and tickets['one']['members'] == ('one',)
        # Returning worker joins the NEXT round, never receives47's old ticket.
        assert cadence.poll('two', now=48, period=45, queue_depth=0)['action'] == 'wait'
        cadence.heartbeat('one', now=65)
        assert not round_for(cadence, 70)
        tickets = round_for(cadence, 92)
        assert len(tickets) == 2 and tickets['one'] == tickets['two']
        cadence.suspend('two')  # Explicit focus/SQM/pause membership withdrawal.
        cadence.heartbeat('one', now=110)
        tickets = round_for(cadence, 137, profiles=('one',))
        assert tickets['one']['members'] == ('one',)
    finally:
        cadence.close()


def peer(cadence, profile, pipe):
    while True:
        command = pipe.recv()
        if command is None:
            break
        now, depth = command
        prepared = None
        deadline = time.monotonic() + 5
        while time.monotonic() < deadline:
            result = cadence.poll(profile, period=45, queue_depth=depth, now=now,
                                  prepared_round=prepared)
            if result['action'] == 'prepare':
                prepared = result['round']
            elif result['action'] == 'start':
                pipe.send(result)
                break
            time.sleep(.001)
        else:
            pipe.send({'error': 'no shared grant'})
    pipe.close()


def die_mid_transition(cadence, pipe):
    with cadence._guard(100) as acquired:
        assert acquired
        cadence._round.value = 1000
        cadence._epoch.value = 999999
        cadence._ready[0] = 1
        pipe.send('partial transition written')
        os.kill(os.getpid(), signal.SIGKILL)


def hold_transition(cadence, pipe):
    with cadence._guard(20) as acquired:
        assert acquired
        pipe.send('locked')
        pipe.recv()


def test_suspend_contention():
    ctx = multiprocessing.get_context('fork')
    for kill_holder in (False, True):
        # A long lease proves withdrawal, rather than eventual expiry, permits
        # the healthy peer's next round after contention releases.
        cadence = SharedCaptureCadence(('one', 'two'), now=0, lease_seconds=1000, context=ctx)
        parent, child = ctx.Pipe()
        holder = ctx.Process(target=hold_transition, args=(cadence, child))
        try:
            assert len(round_for(cadence, 0)) == 2
            holder.start()
            assert parent.poll(5) and parent.recv() == 'locked'
            assert cadence.suspend('two')  # One-shot request while lock held.
            assert cadence._suspended[1] and cadence._enabled[1]
            if kill_holder:
                os.kill(holder.pid, signal.SIGKILL)
            else:
                parent.send('release')
            holder.join(5)
            assert not holder.is_alive()
            assert not cadence.heartbeat('two', now=40)
            # Killing a writer deliberately adds a new safe baseline; neither
            # path waits for the missing peer's1000-second lease.
            if kill_holder:
                assert cadence.poll('one', now=40, period=45, queue_depth=0)['action'] == 'wait'
                now = 85
            else:
                now = 45
            tickets = round_for(cadence, now, profiles=('one',))
            assert tickets['one']['members'] == ('one',)
            # Explicit normal ready-poll rejoining cannot replay that grant.
            assert cadence.poll('two', now=now + 1, period=45, queue_depth=0)['action'] == 'wait'
            tickets = round_for(cadence, now + 45)
            assert len(tickets) == 2 and tickets['one'] == tickets['two']
        finally:
            if holder.is_alive():
                holder.kill()
                holder.join(5)
            parent.close()
            child.close()
            cadence.close()


def test_real_processes():
    ctx = multiprocessing.get_context('fork')
    cadence = SharedCaptureCadence(('one', 'two'), now=0, context=ctx)
    processes, pipes = [], []
    try:
        for profile in cadence.profiles:
            parent, child = ctx.Pipe()
            process = ctx.Process(target=peer, args=(cadence, profile, child))
            process.start()
            child.close()
            processes.append(process)
            pipes.append(parent)
        # Same release epoch, round and delay despite concurrent independent polls.
        for now in (0, 45, 90):
            if now:
                for profile in cadence.profiles:
                    cadence.heartbeat(profile, now=now - 10)
            for pipe in pipes:
                pipe.send((now, 0))
            results = []
            for pipe in pipes:
                assert pipe.poll(6), 'Peer failed to return a bounded result'
                results.append(pipe.recv())
            assert results[0] == results[1], results
            assert results[0]['action'] == 'start' and results[0]['epoch'] == now
        for pipe in pipes:
            pipe.send(None)
        for process in processes:
            process.join(5)
            assert process.exitcode == 0

        receiving, sending = ctx.Pipe(duplex=False)
        broken = ctx.Process(target=die_mid_transition, args=(cadence, sending))
        broken.start()
        assert receiving.poll(5) and receiving.recv() == 'partial transition written'
        broken.join(5)
        assert broken.exitcode == -signal.SIGKILL
        # Kernel releases the lock; owner marker repairs partial RawArray writes.
        assert cadence.poll('one', now=200, period=45, queue_depth=0)['action'] == 'wait'
        assert cadence._repairs.value == 1 and cadence._epoch.value == 200
        assert cadence.reset('two', now=200)
        assert not round_for(cadence, 244.99)
        tickets = round_for(cadence, 245)
        assert len(tickets) == 2 and tickets['one'] == tickets['two']
        assert tickets['one']['repairs'] == 1
        receiving.close()
        sending.close()
    finally:
        for process in processes:
            if process.is_alive():
                process.terminate()
                process.join(5)
        for pipe in pipes:
            pipe.close()
        cadence.close()


def test_capture_integration():
    path = ROOT / 'indi_allsky/capture.py'
    tree = ast.parse(path.read_text())
    cls = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == 'CaptureWorker')
    names = {'_shared_cadence_enabled', '_shared_cadence_start', '_shared_cadence_suspend'}
    scope = dict(constants=SimpleNamespace(EXPOSURE_NEXT=0), logger=Mock())
    methods = [n for n in cls.body if isinstance(n, ast.FunctionDef) and n.name in names]
    exec(compile(ast.Module(body=methods, type_ignores=[]), str(path), 'exec'), scope)
    Worker = type('Worker', (), {name: scope[name] for name in names})
    worker = Worker()
    worker.shared_capture_cadence = Mock()
    worker.config = {'MULTI_CAMERA_CAPTURE_ENABLE': True}
    worker.focus_mode = worker.sqm_camera_enable = False
    worker.profile_id = 'one'
    worker.exposure_av = [39]
    worker.gain_av = [7.25]
    worker._effective_exposure_period = lambda _: {'effective': 45}
    worker.image_q = SimpleNamespace(qsize=lambda: 5)
    worker._cadence_prepared_round = None
    worker.capture_pre_hook = Mock()
    worker._notify_image_backlog = Mock()
    grant = dict(action='start', round=2, epoch=100., period=45., delay=37.5,
                 members=('one', 'two'), repairs=0)
    worker.shared_capture_cadence.poll.side_effect = [dict(action='prepare', round=2), grant]
    assert worker._shared_cadence_enabled() and worker._shared_cadence_start()
    worker.capture_pre_hook.assert_called_once()
    worker._notify_image_backlog.assert_called_once()
    assert worker.shared_capture_cadence.poll.call_args.kwargs['prepared_round'] == 2
    assert worker.exposure_av == [39] and worker.gain_av == [7.25]
    worker.capture_pre_hook.side_effect = RuntimeError('hook failed')
    worker.shared_capture_cadence.poll.side_effect = [dict(action='prepare', round=3)]
    try:
        worker._shared_cadence_start()
    except RuntimeError:
        pass
    else:
        raise AssertionError('Hook failure was hidden')
    assert worker._cadence_prepared_round is None
    for attr in ('focus_mode', 'sqm_camera_enable'):
        setattr(worker, attr, True)
        assert not worker._shared_cadence_enabled()
        setattr(worker, attr, False)
    worker.config['MULTI_CAMERA_CAPTURE_ENABLE'] = False
    assert not worker._shared_cadence_enabled()
    # Actual main-loop guard consumes a shared grant before the existing shoot
    # body; local queue backoff is explicitly bypassed for coordinated capture.
    run = next(n for n in cls.body if isinstance(n, ast.FunctionDef) and n.name == 'saferun')
    text = ast.unparse(run)
    assert 'if not self._shared_cadence_start():\n' in text
    assert 'if not shared_cadence:\n' in text
    assert 'self.shared_capture_cadence.heartbeat(self.profile_id)' in text
    # Execute the actual shared-round guard followed by the actual start
    # predicate. An overdue private timer alone must never authorize a start.
    shared_guard = next(n for n in ast.walk(run) if isinstance(n, ast.If)
                        and ast.unparse(n.test) == 'shared_cadence'
                        and '_shared_cadence_start' in ast.unparse(n))
    parent = next(n for n in ast.walk(run) if hasattr(n, 'body') and isinstance(n.body, list)
                  and shared_guard in n.body)
    guard_index = parent.body.index(shared_guard)
    start = parent.body[guard_index + 1]
    assert ast.unparse(start.test) == 'now_time >= next_frame_time'
    predicate = ast.If(test=start.test, body=ast.parse('starts.append(now_time)').body, orelse=[])
    loop = ast.For(target=ast.Name(id='attempt', ctx=ast.Store()),
                   iter=ast.Tuple(elts=[ast.Constant(value=1)], ctx=ast.Load()),
                   body=[shared_guard, predicate], orelse=[])
    program = compile(ast.fix_missing_locations(ast.Module(body=[loop], type_ignores=[])), str(path), 'exec')
    for allowed in (False, True):
        fake = SimpleNamespace(_shared_cadence_start=lambda: allowed)
        state = dict(self=fake, shared_cadence=True, now_time=100, next_frame_time=0, starts=[])
        exec(program, state)
        assert state['starts'] == ([100] if allowed else [])
    supervisor = (ROOT / 'indi_allsky/allsky.py').read_text()
    assert 'shared_capture_cadence=self.shared_capture_cadence' in supervisor
    assert 'self.shared_capture_cadence.reset(profile.profile_id)' in supervisor


def test_supervisor_membership():
    path = ROOT / 'indi_allsky/allsky.py'
    tree = ast.parse(path.read_text())
    wanted = {'_startMultiCaptureWorkers', '_stopMultiCaptureWorkers'}
    methods = [n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name in wanted]
    scope = {'__package__': 'indi_allsky', 'queue': queue,
             '_multi_camera_diag': Mock(), 'logger': Mock()}
    exec(compile(ast.Module(body=methods, type_ignores=[]), str(path), 'exec'), scope)
    Supervisor = type('Supervisor', (), {name: scope[name] for name in wanted})
    starts = []

    class Capture:
        def __init__(self, *args, **kwargs):
            self.cadence = kwargs['shared_capture_cadence']
            self.profile = args[-2].profile_id
            self.alive = False
            self.pid, self.exitcode = 123, 0

        def start(self):
            self.alive = True
            starts.append(self)

        def is_alive(self):
            return self.alive

        def join(self):
            self.alive = False

    capture_module = ModuleType('indi_allsky.capture')
    capture_module.CaptureWorker = Capture
    worker = Supervisor()
    worker.config = {}
    worker.shared_capture_cadence = None
    worker.capture_worker_map = {}
    worker.capture_worker_idx = 0
    worker._terminate = False
    for name in ('image_q', 'video_q', 'upload_q'):
        setattr(worker, name, queue.Queue())
    enabled = [SimpleNamespace(profile_id=p, primary=i == 0) for i, p in enumerate(('one', 'two'))]
    worker._enabled_capture_profiles = lambda: enabled

    def handle(profile):
        if profile.profile_id not in worker.capture_worker_map:
            arrays = {name: [] for name in ('position_av', 'exposure_av', 'gain_av', 'binning_av',
                                           'sensors_temp_av', 'sensors_user_av', 'night_av', 'astro_av')}
            worker.capture_worker_map[profile.profile_id] = dict(
                worker=None, config={}, error_q=queue.Queue(), capture_q=queue.Queue(),
                shared_state=SimpleNamespace(**arrays))
        return worker.capture_worker_map[profile.profile_id]

    worker._capture_worker_handle = handle
    with patch.dict('sys.modules', {'indi_allsky.capture': capture_module}):
        worker._startMultiCaptureWorkers()
        first = worker.shared_capture_cadence
        assert len(starts) == 2 and all(w.cadence is first for w in starts)
        worker._startMultiCaptureWorkers()
        assert len(starts) == 2  # No reset of healthy live members.
        starts[0].alive = False
        worker._startMultiCaptureWorkers()
        assert len(starts) == 3 and starts[-1].cadence is first
        enabled[:] = [enabled[1]]
        worker._startMultiCaptureWorkers()
        assert not Path(first.lock_path).exists()
        assert worker.shared_capture_cadence.profiles == ('two',)
        assert len(starts) == 4 and starts[-1].cadence is worker.shared_capture_cadence
        final = worker.shared_capture_cadence
        worker._stopMultiCaptureWorkers()
        assert not Path(final.lock_path).exists() and worker.shared_capture_cadence is None
        final.close()  # Idempotent cleanup must not mask shutdown.
        enabled.clear()
        worker._startMultiCaptureWorkers()
        assert worker.shared_capture_cadence is None and len(starts) == 4


def run():
    test_shared_policy()
    test_legacy_queue_thresholds()
    test_lease_restart_and_preparation()
    test_real_processes()
    test_suspend_contention()
    test_capture_integration()
    test_supervisor_membership()
    print('Shared cadence: common rounds/pressure, slow camera leases, restart, hook barrier, killed partial writer and integration PASS')


if __name__ == '__main__':
    run()
