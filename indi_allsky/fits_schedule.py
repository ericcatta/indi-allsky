import time


class FitsSchedule:
    """Profile/camera aware FITS write scheduler.

    The scheduler only tracks when the next FITS write is due. It does not know
    anything about image processing, files, databases, or camera drivers.
    """

    def __init__(self):
        self.next_due_by_key = {}

    def key(self, profile_id, camera_id):
        profile_key = str(profile_id or 'default')
        camera_key = 'unknown' if camera_id is None else str(camera_id)
        return '{0:s}:{1:s}'.format(profile_key, camera_key)

    def is_due(self, key, now=None):
        now_time = time.time() if now is None else float(now)
        next_due = self.next_due_by_key.get(str(key))
        if next_due is None:
            return True
        return now_time >= float(next_due)

    def mark_written(self, key, period, now=None):
        now_time = time.time() if now is None else float(now)
        period_s = self._period_seconds(period)
        self.next_due_by_key[str(key)] = now_time + period_s
        return self.next_due_by_key[str(key)]

    def seconds_until_due(self, key, now=None):
        now_time = time.time() if now is None else float(now)
        next_due = self.next_due_by_key.get(str(key))
        if next_due is None:
            return 0.0
        return max(0.0, float(next_due) - now_time)

    def _period_seconds(self, period):
        try:
            return max(0.0, float(period))
        except (TypeError, ValueError):
            return 0.0
