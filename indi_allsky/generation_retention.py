"""Map pending generation work to conservative media retention scopes."""
from dataclasses import dataclass
from datetime import datetime, timedelta

from .media_task_guard import GENERATION_ACTIONS


@dataclass(frozen=True)
class GenerationScope:
    camera_id: int
    day: object = None
    night: object = None
    start: object = None
    end: object = None

    def protects(self, entry):
        if entry.camera_id != self.camera_id:
            return False
        if self.start is not None:
            # Generated assets can be reused/overwritten by the worker. Keep
            # those for this camera; image inputs use the exact inclusive range.
            if type(entry).__name__ not in (
                    'IndiAllSkyDbImageTable', 'IndiAllSkyDbFitsImageTable',
                    'IndiAllSkyDbRawImageTable', 'IndiAllSkyDbPanoramaImageTable'):
                return True
            return self.start <= entry.createDate <= self.end
        return entry.dayDate == self.day and bool(entry.night) == self.night


def generation_scope(data, lookup_image):
    """None means unknown scope: retain the global guard, never guess.

    The camera/date/night filters mirror VideoWorker's input queries. Mini
    videos intentionally do not filter night or dayDate: their range can cross
    both boundaries. Invalid or incomplete tasks retain everything.
    """
    if not isinstance(data, dict) or data.get('action') not in GENERATION_ACTIONS:
        return None
    kwargs = data.get('kwargs')
    if not isinstance(kwargs, dict):
        return None
    camera = kwargs.get('camera_id')
    if type(camera) is not int or camera <= 0:
        return None
    if data['action'] == 'generateMiniVideo':
        identity = kwargs.get('image_id')
        if type(identity) is not int or identity <= 0:
            return None
        anchor = lookup_image(identity)
        if anchor is None or anchor.camera_id != camera:
            return None
        try:
            pre = int(kwargs['pre_seconds'])
            post = int(kwargs['post_seconds'])
            if pre < 0 or post < 0:
                return None
            start = anchor.createDate - timedelta(seconds=pre)
            end = anchor.createDate + timedelta(seconds=post)
        except (KeyError, ValueError, TypeError, OverflowError):
            return None
        return GenerationScope(camera, start=start, end=end)
    if type(kwargs.get('night')) not in (bool, int) or kwargs['night'] not in (0, 1):
        return None
    try:
        day = datetime.strptime(kwargs['timespec'], '%Y%m%d').date()
    except (KeyError, ValueError, TypeError):
        return None
    return GenerationScope(camera, day=day, night=bool(kwargs['night']))
