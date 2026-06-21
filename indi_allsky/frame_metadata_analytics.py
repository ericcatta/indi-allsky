import json
from collections import Counter
from datetime import datetime
from datetime import timedelta
from datetime import timezone
from pathlib import Path


class FrameMetadataAnalytics:
    """Lightweight reader/summary layer for daily frame metadata JSONL files."""

    REQUIRED_METADATA_FIELDS = (
        'frame_id',
        'timestamp',
        'camera_id',
        'profile_id',
        'exposure_us',
        'gain',
        'meter_value_raw',
        'meter_value_smoothed',
        'target_meter',
        'capture_status',
        'quality_score',
        'quality_flags',
    )
    LEGACY_OPTIONAL_FIELDS = ('quality_score', 'quality_flags')

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


    def get_metadata_health_report(self, date=None):
        frames = self.load_day(date) if date is not None else list(self._iter_frames())
        total_frames = len(frames)
        missing_field_counts = Counter()
        invalid_value_counts = Counter()
        valid_frames = 0
        quality_frames = 0
        present_field_total = 0
        required_field_total = total_frames * len(self.REQUIRED_METADATA_FIELDS)

        for frame in frames:
            frame_valid = True

            for field in self.REQUIRED_METADATA_FIELDS:
                if field in frame and frame.get(field) is not None:
                    present_field_total += 1
                    continue

                missing_field_counts.update([field])
                if field not in self.LEGACY_OPTIONAL_FIELDS:
                    frame_valid = False

            if self._parse_timestamp(frame.get('timestamp')) is None:
                invalid_value_counts.update(['timestamp'])
                frame_valid = False

            if not self._string_value(frame.get('camera_id')):
                invalid_value_counts.update(['camera_id'])
                frame_valid = False

            if not self._string_value(frame.get('profile_id')):
                invalid_value_counts.update(['profile_id'])
                frame_valid = False

            exposure = self._optional_float(frame.get('exposure_us'))
            if exposure is None or exposure < 0.0:
                invalid_value_counts.update(['exposure_us'])
                frame_valid = False

            gain = self._optional_float(frame.get('gain'))
            if gain is None or gain < 0.0:
                invalid_value_counts.update(['gain'])
                frame_valid = False

            quality_score = self._optional_float(frame.get('quality_score'))
            quality_flags = frame.get('quality_flags')
            has_quality_score = quality_score is not None
            has_quality_flags = isinstance(quality_flags, list)
            if has_quality_score and (quality_score < 0.0 or quality_score > 100.0):
                invalid_value_counts.update(['quality_score'])
                frame_valid = False
            if frame.get('quality_flags') is not None and not isinstance(quality_flags, list):
                invalid_value_counts.update(['quality_flags'])
                frame_valid = False
            if has_quality_score and has_quality_flags:
                quality_frames += 1

            if frame_valid:
                valid_frames += 1

        invalid_frames = total_frames - valid_frames
        return {
            'total_frames_checked': total_frames,
            'valid_frames': valid_frames,
            'invalid_frames': invalid_frames,
            'missing_field_counts': dict(missing_field_counts),
            'invalid_value_counts': dict(invalid_value_counts),
            'quality_coverage_percentage': self._percentage(quality_frames, total_frames),
            'metadata_completeness_percentage': self._percentage(present_field_total, required_field_total),
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
        sorted_frames = self._frames_sorted_by_timestamp(frames)
        missing_frames = self._missing_frame_summary(sorted_frames)
        anomaly_events = Counter()
        best_frame = self._quality_extreme_frame(frames, reverse=True)
        worst_frame = self._quality_extreme_frame(frames, reverse=False)
        night_trend = self._night_trend(sorted_frames)

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
                anomaly_events.update(['low_meter'])
            if 'meter_saturated_high' in flags or (meter is not None and target is not None and meter > (target + 20.0)):
                high_meter_count += 1
                anomaly_events.update(['high_meter'])

            if 'exposure_and_gain_already_max' in reason or ('exposure' in reason and 'max' in reason):
                exposure_max_count += 1
                anomaly_events.update(['exposure_max'])
            if 'gain_already_max' in reason or ('gain' in reason and 'max' in reason):
                gain_max_count += 1
                anomaly_events.update(['gain_max'])

            capture_status = self._string_value(frame.get('capture_status')).lower()
            if capture_status and capture_status != 'processed':
                capture_error_count += 1
                anomaly_events.update(['capture_error'])
            elif self._string_value(frame.get('error_message')):
                capture_error_count += 1
                anomaly_events.update(['capture_error'])
            elif 'capture_error' in flags or 'capture_not_processed' in flags:
                capture_error_count += 1
                anomaly_events.update(['capture_error'])

            quality_score = self._optional_float(frame.get('quality_score'))
            if quality_score is not None and quality_score < 50.0:
                anomaly_events.update(['low_quality'])

        summary.update({
            'camera_id': camera_id,
            'profile_id': profile_ids.most_common(1)[0][0] if profile_ids else '',
            'missing_frames': missing_frames,
            'anomaly_events': {
                'count': sum(anomaly_events.values()),
                'most_common': self._counter_rows(anomaly_events),
            },
            'best_frame': self._frame_reference(best_frame),
            'worst_frame': self._frame_reference(worst_frame),
            'night_trend': night_trend,
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


    def _frames_sorted_by_timestamp(self, frames):
        timestamped_frames = []
        for frame in frames:
            timestamp = self._parse_timestamp(frame.get('timestamp'))
            if timestamp is not None:
                timestamped_frames.append((timestamp, frame))
        return [frame for timestamp, frame in sorted(timestamped_frames, key=lambda item: item[0])]


    def _missing_frame_summary(self, frames):
        timestamps = [self._parse_timestamp(frame.get('timestamp')) for frame in frames]
        timestamps = [timestamp for timestamp in timestamps if timestamp is not None]
        if len(timestamps) < 2:
            return {
                'count': 0,
                'percent': 0.0,
                'expected_interval_seconds': None,
                'threshold_seconds': None,
            }

        intervals = [
            (timestamps[index] - timestamps[index - 1]).total_seconds()
            for index in range(1, len(timestamps))
            if (timestamps[index] - timestamps[index - 1]).total_seconds() > 0
        ]
        if not intervals:
            return {
                'count': 0,
                'percent': 0.0,
                'expected_interval_seconds': None,
                'threshold_seconds': None,
            }

        expected_interval = self._median(intervals)
        threshold = expected_interval * 2.0
        missing_count = 0
        for interval in intervals:
            if interval > threshold:
                missing_count += max(1, int(round(interval / expected_interval)) - 1)

        total_expected = len(timestamps) + missing_count
        return {
            'count': missing_count,
            'percent': self._percentage(missing_count, total_expected),
            'expected_interval_seconds': expected_interval,
            'threshold_seconds': threshold,
        }


    def _quality_extreme_frame(self, frames, reverse=False):
        scored_frames = [
            (self._optional_float(frame.get('quality_score')), frame)
            for frame in frames
            if self._optional_float(frame.get('quality_score')) is not None
        ]
        if not scored_frames:
            return None
        return sorted(scored_frames, key=lambda item: item[0], reverse=reverse)[0][1]


    def _frame_reference(self, frame):
        if frame is None:
            return {
                'timestamp': None,
                'quality_score': None,
                'image_file_path': None,
                'frame_id': None,
            }
        return {
            'timestamp': self._string_value(frame.get('timestamp')) or None,
            'quality_score': self._optional_float(frame.get('quality_score')),
            'image_file_path': self._string_value(frame.get('image_file_path')) or None,
            'frame_id': frame.get('frame_id'),
        }


    def _night_trend(self, frames):
        return {
            'quality': self._metric_trend(frames, 'quality_score'),
            'meter': self._metric_trend(frames, 'meter_value_smoothed'),
            'exposure': self._metric_trend(frames, 'exposure_us'),
            'gain': self._metric_trend(frames, 'gain'),
        }


    def _metric_trend(self, frames, key):
        values = [self._optional_float(frame.get(key)) for frame in frames]
        values = [value for value in values if value is not None]
        if len(values) < 2:
            return {
                'direction': 'unknown',
                'delta': None,
                'first_average': None,
                'last_average': None,
            }

        midpoint = max(1, int(len(values) / 2))
        first_values = values[:midpoint]
        last_values = values[midpoint:] or values[midpoint - 1:]
        first_average = self._average(first_values)
        last_average = self._average(last_values)
        delta = last_average - first_average
        tolerance = max(abs(first_average) * 0.05, 0.5)
        if delta > tolerance:
            direction = 'up'
        elif delta < (tolerance * -1):
            direction = 'down'
        else:
            direction = 'stable'

        return {
            'direction': direction,
            'delta': delta,
            'first_average': first_average,
            'last_average': last_average,
        }


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


    def _median(self, values):
        if not values:
            return None
        values_sorted = sorted(values)
        midpoint = int(len(values_sorted) / 2)
        if len(values_sorted) % 2:
            return values_sorted[midpoint]
        return (values_sorted[midpoint - 1] + values_sorted[midpoint]) / 2.0


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
