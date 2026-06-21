import json
from collections import Counter
from datetime import datetime
from datetime import timedelta
from datetime import timezone
from pathlib import Path


class FrameMetadataAnalytics:
    """Lightweight reader/summary layer for daily frame metadata JSONL files."""

    def __init__(self, metadata_dir):
        self.metadata_dir = Path(metadata_dir)


    def load_day(self, date):
        metadata_path = self._day_path(date)
        if not metadata_path.exists():
            return []

        rows = []
        with metadata_path.open('r', encoding='utf-8') as f_metadata:
            for line in f_metadata:
                line = line.strip()
                if not line:
                    continue
                rows.append(json.loads(line))

        return rows


    def get_latest_frames(self, limit=100):
        limit = max(0, int(limit))
        if limit == 0:
            return []

        frames = []
        for metadata_path in sorted(self.metadata_dir.glob('*.jsonl'), reverse=True):
            frames.extend(reversed(self._load_file(metadata_path)))
            if len(frames) >= limit:
                break

        return frames[:limit]


    def get_recent_frames(self, hours=24, now=None):
        now_dt = now or datetime.now(timezone.utc)
        cutoff = now_dt - timedelta(hours=float(hours))
        frames = []
        for frame in self._iter_frames():
            timestamp = self._parse_timestamp(frame.get('timestamp'))
            if timestamp is not None and timestamp >= cutoff:
                frames.append(frame)

        return sorted(frames, key=lambda frame: self._string_value(frame.get('timestamp')))


    def get_camera_summary(self, camera_id):
        camera_id_str = str(camera_id)
        frames = [
            frame for frame in self._iter_frames()
            if str(frame.get('camera_id')) == camera_id_str
        ]
        return self._summary(frames)


    def get_decision_statistics(self, camera_id=None):
        if camera_id is None:
            frames = list(self._iter_frames())
        else:
            camera_id_str = str(camera_id)
            frames = [
                frame for frame in self._iter_frames()
                if str(frame.get('camera_id')) == camera_id_str
            ]

        return {
            'auto_exposure_action': dict(Counter(self._string_value(frame.get('auto_exposure_action')) for frame in frames)),
            'auto_gain_action': dict(Counter(self._string_value(frame.get('auto_gain_action')) for frame in frames)),
            'decision_reason': dict(Counter(self._string_value(frame.get('decision_reason')) for frame in frames)),
        }


    def _iter_frames(self):
        for metadata_path in sorted(self.metadata_dir.glob('*.jsonl')):
            yield from self._load_file(metadata_path)


    def _load_file(self, metadata_path):
        rows = []
        with metadata_path.open('r', encoding='utf-8') as f_metadata:
            for line in f_metadata:
                line = line.strip()
                if not line:
                    continue
                rows.append(json.loads(line))
        return rows


    def _summary(self, frames):
        timestamps = [self._string_value(frame.get('timestamp')) for frame in frames if frame.get('timestamp')]
        exposures = [value for value in (self._optional_float(frame.get('exposure_us')) for frame in frames) if value is not None]
        gains = [value for value in (self._optional_float(frame.get('gain')) for frame in frames) if value is not None]
        meters = [value for value in (self._optional_float(frame.get('meter_value_smoothed')) for frame in frames) if value is not None]
        quality_scores = [value for value in (self._optional_float(frame.get('quality_score')) for frame in frames) if value is not None]

        return {
            'frame_count': len(frames),
            'first_timestamp': min(timestamps) if timestamps else None,
            'last_timestamp': max(timestamps) if timestamps else None,
            'average_exposure': self._average(exposures),
            'minimum_exposure': min(exposures) if exposures else None,
            'maximum_exposure': max(exposures) if exposures else None,
            'average_gain': self._average(gains),
            'minimum_gain': min(gains) if gains else None,
            'maximum_gain': max(gains) if gains else None,
            'average_meter_value': self._average(meters),
            'minimum_meter_value': min(meters) if meters else None,
            'maximum_meter_value': max(meters) if meters else None,
            'average_quality_score': self._average(quality_scores),
            'minimum_quality_score': min(quality_scores) if quality_scores else None,
            'maximum_quality_score': max(quality_scores) if quality_scores else None,
        }


    def _day_path(self, date):
        return self.metadata_dir.joinpath('{0:s}.jsonl'.format(str(date)))


    def _optional_float(self, value):
        try:
            return float(value)
        except (TypeError, ValueError):
            return None


    def _average(self, values):
        if not values:
            return None
        return sum(values) / len(values)


    def _string_value(self, value):
        if value is None:
            return ''
        return str(value)


    def _parse_timestamp(self, timestamp):
        timestamp_str = self._string_value(timestamp).strip()
        if not timestamp_str:
            return None
        if timestamp_str.endswith('Z'):
            timestamp_str = '{0:s}+00:00'.format(timestamp_str[:-1])

        try:
            timestamp_dt = datetime.fromisoformat(timestamp_str)
        except ValueError:
            return None

        if timestamp_dt.tzinfo is None:
            return timestamp_dt.replace(tzinfo=timezone.utc)

        return timestamp_dt.astimezone(timezone.utc)
