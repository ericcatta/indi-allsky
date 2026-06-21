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


    def get_nightly_summary(self, date=None):
        summary_date = self._latest_day() if date is None else str(date)
        frames = self.load_day(summary_date) if summary_date else []
        camera_ids = sorted(set(self._string_value(frame.get('camera_id')) for frame in frames if self._string_value(frame.get('camera_id'))))
        return {
            'date': summary_date,
            'cameras': [
                self._nightly_camera_summary(camera_id, [
                    frame for frame in frames
                    if self._string_value(frame.get('camera_id')) == camera_id
                ])
                for camera_id in camera_ids
            ],
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


    def _nightly_camera_summary(self, camera_id, frames):
        summary = self._summary(frames)
        total = len(frames)
        quality_flags = Counter()
        decision_reasons = Counter()
        nominal_count = 0
        low_meter_count = 0
        high_meter_count = 0
        exposure_max_count = 0
        gain_max_count = 0
        capture_error_count = 0
        profile_ids = Counter(self._string_value(frame.get('profile_id')) for frame in frames if self._string_value(frame.get('profile_id')))

        for frame in frames:
            flags = self._quality_flags(frame.get('quality_flags'))
            quality_flags.update(flags)
            reason = self._string_value(frame.get('decision_reason'))
            if reason:
                decision_reasons.update([reason])

            quality_score = self._optional_float(frame.get('quality_score'))
            if 'nominal' in flags or (quality_score is not None and quality_score >= 90.0):
                nominal_count += 1

            meter = self._optional_float(frame.get('meter_value_smoothed'))
            target = self._optional_float(frame.get('target_meter'))
            if 'meter_near_black' in flags or (meter is not None and target is not None and meter < (target - 20.0)):
                low_meter_count += 1
            if 'meter_saturated_high' in flags or (meter is not None and target is not None and meter > (target + 20.0)):
                high_meter_count += 1

            if 'exposure_and_gain_already_max' in reason or ('exposure' in reason and 'max' in reason):
                exposure_max_count += 1
            if 'gain_already_max' in reason or ('gain' in reason and 'max' in reason):
                gain_max_count += 1

            capture_status = self._string_value(frame.get('capture_status')).lower()
            if capture_status and capture_status != 'processed':
                capture_error_count += 1
            elif self._string_value(frame.get('error_message')):
                capture_error_count += 1
            elif 'capture_error' in flags or 'capture_not_processed' in flags:
                capture_error_count += 1

        summary.update({
            'camera_id': camera_id,
            'profile_id': profile_ids.most_common(1)[0][0] if profile_ids else '',
            'most_common_quality_flags': self._counter_rows(quality_flags),
            'most_common_decision_reasons': self._counter_rows(decision_reasons),
            'percentages': {
                'nominal_quality': self._percentage(nominal_count, total),
                'low_meter': self._percentage(low_meter_count, total),
                'high_meter': self._percentage(high_meter_count, total),
                'exposure_max': self._percentage(exposure_max_count, total),
                'gain_max': self._percentage(gain_max_count, total),
                'capture_errors': self._percentage(capture_error_count, total),
            },
        })
        return summary


    def _latest_day(self):
        metadata_paths = sorted(self.metadata_dir.glob('*.jsonl'))
        if not metadata_paths:
            return None
        return metadata_paths[-1].stem


    def _quality_flags(self, flags):
        if isinstance(flags, list):
            return [self._string_value(flag) for flag in flags if self._string_value(flag)]
        flag_value = self._string_value(flags)
        if not flag_value:
            return []
        return [flag_value]


    def _counter_rows(self, counter, limit=5):
        return [
            {
                'label': label,
                'count': count,
            }
            for label, count in counter.most_common(limit)
        ]


    def _percentage(self, count, total):
        if not total:
            return 0.0
        return (float(count) / float(total)) * 100.0


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
