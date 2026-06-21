#!/usr/bin/env python3
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from indi_allsky.event_candidate import EventCandidate
from indi_allsky.event_candidate import EventCandidateAnalytics
from indi_allsky.event_candidate import EventCandidateWriter
from indi_allsky.event_candidate import EventTimelineAnalytics
from indi_allsky.event_candidate import EventTimelineWriter
from indi_allsky.event_candidate import build_event_timeline_segments
from indi_allsky.event_candidate import default_event_candidate_dir
from indi_allsky.event_candidate import default_event_timeline_dir


SYNTHETIC_PREFIX = 'synthetic-smoke-v0'
DEFAULT_BASE_DIR = Path('/tmp/indi-allsky-event-foundation-smoke')


def _candidate(candidate_id, camera_id, profile_id, frame_id, timestamp, score, reasons, meter, quality_score):
    return EventCandidate(
        candidate_id='{0:s}:{1:s}'.format(SYNTHETIC_PREFIX, candidate_id),
        camera_id=camera_id,
        profile_id=profile_id,
        frame_id=frame_id,
        timestamp_utc=timestamp,
        night_id=timestamp[:10],
        candidate_score=score,
        reasons=reasons,
        source_metrics={
            'meter_value_raw': meter,
            'meter_value_smoothed': meter,
            'target_meter': 95.0,
            'meter_error': 95.0 - meter,
            'exposure_us': 14000000 if camera_id == 1 else 25000,
            'gain': 16.0 if camera_id == 1 else 300.0,
            'capture_status': 'processed',
        },
        quality_context={
            'quality_score': quality_score,
            'quality_flags': reasons,
        },
        environment_context={
            'sky_condition': 'usable' if quality_score >= 60.0 else 'poor',
            'cloud_condition': 'partly_cloudy' if quality_score >= 60.0 else 'cloudy',
            'sky_trend': 'stable',
            'possible_condensation': False,
        },
    )


def build_synthetic_candidates(date):
    return [
        _candidate('asi-001', 2, 'asi_zenith', 9001, '{0:s}T22:00:00+00:00'.format(date), 24.0, ['synthetic_brightness_spike'], 240.0, 55.0),
        _candidate('asi-002', 2, 'asi_zenith', 9002, '{0:s}T22:00:01+00:00'.format(date), 30.0, ['synthetic_brightness_spike'], 245.0, 50.0),
        _candidate('asi-003', 2, 'asi_zenith', 9003, '{0:s}T22:00:08+00:00'.format(date), 18.0, ['synthetic_quality_drop'], 80.0, 42.0),
        _candidate('imx-001', 1, 'imx708_south', 9101, '{0:s}T22:01:00+00:00'.format(date), 12.0, ['synthetic_quality_drop'], 70.0, 62.0),
        _candidate('imx-002', 1, 'imx708_south', 9102, '{0:s}T22:01:01+00:00'.format(date), 16.0, ['synthetic_quality_drop'], 72.0, 65.0),
    ]


def remove_synthetic_rows(jsonl_path, id_field):
    if not jsonl_path.exists():
        return 0

    kept_lines = []
    removed = 0
    for line in jsonl_path.read_text(encoding='utf-8').splitlines():
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except ValueError:
            kept_lines.append(line)
            continue

        if str(row.get(id_field, '')).startswith(SYNTHETIC_PREFIX):
            removed += 1
            continue
        kept_lines.append(line)

    if kept_lines:
        jsonl_path.write_text('{0:s}\n'.format('\n'.join(kept_lines)), encoding='utf-8')
    else:
        jsonl_path.unlink()

    return removed


def cleanup_synthetic(candidate_dir, timeline_dir, date):
    candidate_path = candidate_dir.joinpath('{0:s}.jsonl'.format(date))
    timeline_path = timeline_dir.joinpath('{0:s}.jsonl'.format(date))
    removed_candidates = remove_synthetic_rows(candidate_path, 'candidate_id')
    removed_timelines = remove_synthetic_rows(timeline_path, 'timeline_id')
    return removed_candidates, removed_timelines


def resolve_base_dir(args):
    if args.varlib:
        return Path(args.varlib)
    if args.output_dir:
        return Path(args.output_dir)
    return DEFAULT_BASE_DIR


def print_summary(candidate_path, timeline_path, candidate_summary, timeline_summary):
    print('Event Foundation smoke test OK')
    print('candidate_file={0:s}'.format(str(candidate_path)))
    print('timeline_file={0:s}'.format(str(timeline_path)))
    print('total_event_candidates={0:d}'.format(candidate_summary['total_event_candidates']))
    print('event_candidates_by_camera={0:s}'.format(json.dumps(candidate_summary['event_candidates_by_camera'], sort_keys=True)))
    print('event_candidates_by_reason={0:s}'.format(json.dumps(candidate_summary['event_candidates_by_reason'], sort_keys=True)))
    print('average_candidate_score={0}'.format(candidate_summary['average_candidate_score']))
    print('max_candidate_score={0}'.format(candidate_summary['max_candidate_score']))
    print('total_timeline_segments={0:d}'.format(timeline_summary['total_timeline_segments']))
    print('timeline_segments_by_camera={0:s}'.format(json.dumps(timeline_summary['timeline_segments_by_camera'], sort_keys=True)))
    print('timeline_segments_by_reason={0:s}'.format(json.dumps(timeline_summary['timeline_segments_by_reason'], sort_keys=True)))
    print('average_segment_duration_seconds={0}'.format(timeline_summary['average_segment_duration_seconds']))
    print('max_segment_duration_seconds={0}'.format(timeline_summary['max_segment_duration_seconds']))
    print('average_candidates_per_segment={0}'.format(timeline_summary['average_candidates_per_segment']))
    print('max_candidates_per_segment={0}'.format(timeline_summary['max_candidates_per_segment']))


def main():
    parser = argparse.ArgumentParser(description='Write synthetic Event Foundation v0 JSONL data for manual dashboard smoke testing.')
    parser.add_argument('--date', default='2026-06-21', help='Synthetic metadata date / night id, default: 2026-06-21')
    parser.add_argument('--output-dir', help='Base directory containing event_candidates/ and event_timelines/. Default: /tmp/indi-allsky-event-foundation-smoke')
    parser.add_argument('--varlib', help='Use an indi-allsky VARLIB_FOLDER such as /var/lib/indi-allsky. Use this on Raspberry to populate the dashboard.')
    parser.add_argument('--cleanup', action='store_true', help='Remove only synthetic smoke-test rows for the selected date and exit.')
    args = parser.parse_args()

    base_dir = resolve_base_dir(args)
    candidate_dir = default_event_candidate_dir(base_dir)
    timeline_dir = default_event_timeline_dir(base_dir)

    if args.cleanup:
        removed_candidates, removed_timelines = cleanup_synthetic(candidate_dir, timeline_dir, args.date)
        print('Removed synthetic candidates: {0:d}'.format(removed_candidates))
        print('Removed synthetic timelines: {0:d}'.format(removed_timelines))
        return 0

    cleanup_synthetic(candidate_dir, timeline_dir, args.date)

    candidates = build_synthetic_candidates(args.date)
    candidate_writer = EventCandidateWriter(candidate_dir)
    candidate_path = None
    for candidate in candidates:
        candidate_path = candidate_writer.write(candidate)

    segments = build_event_timeline_segments(candidates)
    timeline_writer = EventTimelineWriter(timeline_dir)
    timeline_path = None
    for segment in segments:
        timeline_path = timeline_writer.write(segment)

    candidate_summary = EventCandidateAnalytics(candidate_dir).get_nightly_event_summary(args.date)
    timeline_summary = EventTimelineAnalytics(timeline_dir).get_nightly_timeline_summary(args.date)
    print_summary(candidate_path, timeline_path, candidate_summary, timeline_summary)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
