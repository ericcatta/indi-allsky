"""Shared start rounds for normal multicamera capture; no camera controls.

Every live participant finishes its own exposure and preparation before a round
opens. A missing heartbeat removes a participant after a bounded lease. Rejoining
workers never consume an old round. All time values use the monotonic clock.
"""
import math
import os
import fcntl
import tempfile
from contextlib import contextmanager
import multiprocessing
import time


class SharedCaptureCadence:
    def __init__(self, profiles, *, queue_min=1, queue_max=3, backoff=0.5,
                 lease_seconds=30.0, now=None, context=None):
        self.profiles = tuple(profiles)
        if not self.profiles or len(set(self.profiles)) != len(self.profiles):
            raise ValueError('Cadence requires unique profiles')
        # Existing settings permit equal/reversed thresholds. Preserve the
        # capture loop's <=minimum precedence instead of rejecting stored config.
        if (not math.isfinite(queue_min) or queue_min < 0
                or not math.isfinite(queue_max) or queue_max <= 0
                or not math.isfinite(backoff) or backoff < 0):
            raise ValueError('Invalid cadence queue policy')
        if not math.isfinite(lease_seconds) or lease_seconds <= 0:
            raise ValueError('Cadence lease must be finite and positive')
        self.queue_min, self.queue_max, self.backoff = queue_min, queue_max, backoff
        self.lease_seconds = lease_seconds
        ctx = context or multiprocessing.get_context()
        size = len(self.profiles)
        descriptor, self.lock_path = tempfile.mkstemp(prefix="indi-allsky-cadence-", suffix=".lock")
        os.close(descriptor)
        self._owner = ctx.Value("q", 0, lock=False)
        self._repairs = ctx.Value("q", 0, lock=False)
        self._enabled = ctx.Array('b', [1] * size, lock=False)
        # Per-profile withdrawal is a single-byte publication, independent of
        # the transition lock. A one-shot exit/focus request cannot be lost to
        # contention. Only an explicit reset/ready poll resumes membership.
        self._suspended = ctx.Array('b', size, lock=False)
        self._seen = ctx.Array('d', [time.monotonic() if now is None else now] * size, lock=False)
        self._ready = ctx.Array('b', size, lock=False)
        self._prepared = ctx.Array('q', size, lock=False)
        self._claimed = ctx.Array('q', size, lock=False)
        self._members = ctx.Array('q', size, lock=False)
        self._periods = ctx.Array('d', size, lock=False)
        self._round = ctx.Value('q', 0, lock=False)
        self._epoch = ctx.Value('d', 0, lock=False)
        self._period = ctx.Value('d', 0, lock=False)
        self._delay = ctx.Value('d', 0, lock=False)
        self._round_delay = ctx.Value('d', 0, lock=False)
        self._pressure_round = ctx.Value('q', -1, lock=False)
        self._baseline = ctx.Value('d', 0, lock=False)

    @contextmanager
    def _guard(self, now):
        # Each open has its own file description, including after fork. flock
        # releases on process death; a multiprocessing.Lock does not. Never wait
        # for a paused holder on a camera thread.
        with open(self.lock_path, 'r+') as stream:
            try:
                fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                yield False
                return
            if self._owner.value:
                # A worker died mid-update. Invalidate all tickets/preparations
                # and restart from a future baseline rather than torn state.
                self._round.value += 1
                self._epoch.value = now
                self._period.value = max(self._periods[:]) or 1.0
                self._pressure_round.value = -1
                for index in range(len(self.profiles)):
                    self._ready[index] = self._prepared[index] = self._members[index] = 0
                    self._claimed[index] = self._round.value
                self._repairs.value += 1
            self._owner.value = os.getpid()
            try:
                yield True
            except BaseException:
                # Leave the owner marker: the next lock holder repairs state.
                raise
            else:
                self._owner.value = 0
            finally:
                fcntl.flock(stream, fcntl.LOCK_UN)

    def close(self):
        """Supervisor only, after every capture worker has joined."""
        try:
            os.unlink(self.lock_path)
        except FileNotFoundError:
            pass

    def _index(self, profile):
        return self.profiles.index(profile)

    def _reset(self, index, now, enabled):
        self._enabled[index] = enabled
        self._seen[index] = now
        self._ready[index] = self._prepared[index] = 0
        self._claimed[index] = self._round.value
        self._members[index] = 0

    def reset(self, profile, now=None):
        """Supervisor replaces a worker: discard its old readiness and ticket."""
        now = time.monotonic() if now is None else now
        with self._guard(now) as acquired:
            if not acquired:
                return False
            self._reset(self._index(profile), now, True)
            self._suspended[self._index(profile)] = 0
            return True

    def suspend(self, profile):
        index = self._index(profile)
        self._suspended[index] = 1
        with self._guard(time.monotonic()) as acquired:
            if not acquired:
                return True  # The published withdrawal is already authoritative.
            self._reset(index, 0, False)
            return True

    def _touch(self, index, now):
        if self._suspended[index] or not self._enabled[index] or now - self._seen[index] > self.lease_seconds:
            self._reset(index, now, True)
            self._suspended[index] = 0
        self._seen[index] = now

    def heartbeat(self, profile, now=None):
        """Busy cameras renew membership without declaring readiness."""
        now = time.monotonic() if now is None else now
        with self._guard(now) as acquired:
            if not acquired:
                return False
            index = self._index(profile)
            if self._suspended[index]:
                return False  # A late busy heartbeat cannot undo withdrawal.
            self._touch(index, now)
            self._ready[index] = 0
            return True

    def _ticket(self, index):
        self._claimed[index] = self._round.value
        self._ready[index] = 0
        return dict(action='start', round=self._round.value, epoch=self._epoch.value,
                    period=self._period.value, delay=self._round_delay.value,
                    repairs=self._repairs.value,
                    members=tuple(p for i, p in enumerate(self.profiles)
                                  if self._members[i] == self._round.value))

    def poll(self, profile, *, period, queue_depth, prepared_round=None, now=None):
        """Return wait, prepare(next round), or a single-use shared start ticket.

        Preparation is acknowledged only for its exact upcoming round. Hooks run
        outside the lock and before the grant, so one camera cannot start while
        another is still preparing. No subprocess, I/O or waiting holds the lock.
        """
        now = time.monotonic() if now is None else now
        if not math.isfinite(period) or period <= 0 or not math.isfinite(now):
            raise ValueError('Cadence time and period must be finite and positive')
        with self._guard(now) as acquired:
            if not acquired:
                return dict(action='wait')
            index = self._index(profile)
            self._touch(index, now)
            self._periods[index] = period
            if self._members[index] == self._round.value and self._claimed[index] < self._round.value:
                return self._ticket(index)
            self._ready[index] = 1
            upcoming = self._round.value + 1
            if prepared_round == upcoming:
                self._prepared[index] = upcoming
            active = [i for i in range(len(self.profiles))
                      if self._enabled[i] and not self._suspended[i]
                      and now - self._seen[i] <= self.lease_seconds]
            if any(not self._ready[i] or self._claimed[i] < self._round.value
                   for i in active):
                return dict(action='wait')

            # One queue decision per common cycle, with shared early release
            # when processing drains. Never choose per-camera delays.
            if self._pressure_round.value != upcoming:
                if queue_depth <= self.queue_min:
                    self._delay.value = 0
                elif queue_depth >= self.queue_max:
                    base_period = self._period.value or max(self._periods[i] for i in active)
                    self._delay.value = queue_depth / self.queue_max * base_period * self.backoff
                self._baseline.value = (self._epoch.value + self._period.value
                                        if self._round.value else now)
                self._pressure_round.value = upcoming
            elif queue_depth <= self.queue_min:
                self._delay.value = 0
            if now < self._baseline.value + self._delay.value:
                return dict(action='wait')
            if self._prepared[index] != upcoming:
                return dict(action='prepare', round=upcoming)
            if any(self._prepared[i] != upcoming for i in active):
                return dict(action='wait')

            self._round.value = upcoming
            self._epoch.value = now  # Actual release, never an overdue epoch.
            self._period.value = max(self._periods[i] for i in active)
            self._round_delay.value = self._delay.value
            self._pressure_round.value = -1
            for i in range(len(self.profiles)):
                self._members[i] = upcoming if i in active else 0
                self._ready[i] = self._prepared[i] = 0
                if i not in active:
                    self._claimed[i] = upcoming
            return self._ticket(index)
