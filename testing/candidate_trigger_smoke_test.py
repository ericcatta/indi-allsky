#!/usr/bin/env python3
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from indi_allsky.event_candidate import EventCandidateAnalytics
from indi_allsky.event_candidate import EventCandidateWriter
from indi_allsky.event_candidate import EventTimelineAnalytics
from indi_allsky.event_candidate import EventTimelineWriter
from indi_allsky.event_candidate import build_event_timeline_segments
from indi_allsky.event_candidate import default_event_candidate_dir
from indi_allsky.event_candidate import default_event_timeline_dir
from indi_allsky.event_candidate import evaluate_candidate_triggers


SYNTHETIC_PREFIX = 'synthetic-trigger-smoke-v0'
DEFAULT_BASE_DIR = Path('/tmp/indi-allsky-candidate-trigger-smoke')


def _metadata(frame_id, camera_id, profile_id, timestamp, meter, quality, sky_condition='good', cloud_condition='mostly_clear', possible_condensation=False):
    return {
        'frame_id': frame_id,
        'timestamp': timestamp,
        'camera_id': camera_id,
        'profile_id': profile_id,
        'meter_value_raw': meter,
        'meter_value_smoothed': meter,
        'target_meter': 95.0,
        'meter_error': 95.0 - meter,
        'exposure_us': 1000000,
        'gain': 0.0,
        'capture_status': 'processed',
        'quality_score': quality,
        'quality_flags': [],
        'sky_condition': sky_condition,
        'cloud_condition': cloud_condition,
        'sky_trend': 'stable',
        'possible_condensation': possible_condensation,
    }


def build_synthetic_trigger_cases(date):
    return [
        {
            'name': 'normal',
            'previous': _metadata(1000, 1, 'asi_zenith', '{0:s}T22:00:00+00:00'.format(date), 95.0, 95.0),
            'current': _metadata(1001, 1, 'asi_zenith', '{0:s}T22:00:01+00:00'.format(date), 96.0, 94.0),
        },
        {
            'name': 'brightness_spike',
            'previous': _metadata(1010, 1, 'asi_zenith', '{0:s}T22:01:00+00:00'.format(date), 95.0, 95.0),
            'current': _metadata(1011, 1, 'asi_zenith', '{0:s}T22:01:01+00:00'.format(date), 185.0, 92.0),
        },
        {
            'name': 'quality_drop',
            'previous': _metadata(1020, 1, 'asi_zenith', '{0:s}T22:02:00+00:00'.format(date), 96.0, 95.0),
            'current': _metadata(1021, 1, 'asi_zenith', '{0:s}T22:02:01+00:00'.format(date), 90.0, 34.0),
        },
        {
            'name': 'condensation_onset',
            'previous': _metadata(2010, 2, 'imx708_south', '{0:s}T22:03:00+00:00'.format(date), 92.0, 90.0, possible_condensation=False),
            'current': _metadata(2011, 2, 'imx708_south', '{0:s}T22:03:01+00:00'.format(date), 92.0, 88.0, possible_condensation=True),
        },
        {
            'name': 'sky_condition_transition',
            'previous': _metadata(2020, 2, 'imx708_south', '{0:s}T22:04:00+00:00'.format(date), 93.0, 86.0, sky_condition='excellent', cloud_condition='clear'),
            'current': _metadata(2021, 2, 'imx708_south', '{0:s}T22:04:01+00:00'.format(date), 92.0, 80.0, sky_condition='poor', cloud_condition='cloudy'),
        },
    ]


def build_synthetic_trigger_candidates(date):
    candidates = []
    case_results = []
    for case in build_synthetic_trigger_cases(date):
        case_candidates = evaluate_candidate_triggers(case['current'], previous_metadata=case['previous'])
        for candidate in case_candidates:
            candidate.candidate_id = '{0:s}:{1:s}'.format(SYNTHETIC_PREFIX, candidate.candidate_id)
        candidates.extend(case_candidates)
        case_results.append((case['name'], [candidate.reasons[0] for candidate in case_candidates]))
    return candidates, case_results


def is_synthetic_row(row, id_field):
    if str(row.get(id_field, '')).startswith(SYNTHETIC_PREFIX):
        return True

    candidate_ids = row.get('candidate_ids')
    if isinstance(candidate_ids, list):
        return any(str(candidate_id).startswith(SYNTHETIC_PREFIX) for candidate_id in candidate_ids)

    return False


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

        if is_synthetic_row(row, id_field):
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


def print_summary(candidate_path, timeline_path, case_results, candidate_summary, timeline_summary):
    print('Candidate Trigger smoke test OK')
    print('candidate_file={0:s}'.format(str(candidate_path)))
    print('timeline_file={0:s}'.format(str(timeline_path)))
    for name, reasons in case_results:
        print('case_{0:s}={1:s}'.format(name, ','.join(reasons) if reasons else 'none'))
    print('total_event_candidates={0:d}'.format(candidate_summary['total_event_candidates']))
    print('event_candidates_by_camera={0:s}'.format(json.dumps(candidate_summary['event_candidates_by_camera'], sort_keys=True)))
    print('event_candidates_by_reason={0:s}'.format(json.dumps(candidate_summary['event_candidates_by_reason'], sort_keys=True)))
    print('total_timeline_segments={0:d}'.format(timeline_summary['total_timeline_segments']))
    print('timeline_segments_by_camera={0:s}'.format(json.dumps(timeline_summary['timeline_segments_by_camera'], sort_keys=True)))
    print('timeline_segments_by_reason={0:s}'.format(json.dumps(timeline_summary['timeline_segments_by_reason'], sort_keys=True)))


def main():
    parser = argparse.ArgumentParser(description='Write synthetic Candidate Trigger v0 JSONL data for manual dashboard smoke testing.')
    parser.add_argument('--date', default='2026-06-21', help='Synthetic metadata date / night id, default: 2026-06-21')
    parser.add_argument('--output-dir', help='Base directory containing event_candidates/ and event_timelines/. Default: /tmp/indi-allsky-candidate-trigger-smoke')
    parser.add_argument('--varlib', help='Use an indi-allsky VARLIB_FOLDER such as /var/lib/indi-allsky. Use this on Raspberry to populate the dashboard.')
    parser.add_argument('--cleanup', action='store_true', help='Remove only synthetic trigger smoke-test rows for the selected date and exit.')
    args = parser.parse_args()

    base_dir = resolve_base_dir(args)
    candidate_dir = default_event_candidate_dir(base_dir)
    timeline_dir = default_event_timeline_dir(base_dir)

    if args.cleanup:
        removed_candidates, removed_timelines = cleanup_synthetic(candidate_dir, timeline_dir, args.date)
        print('Removed synthetic trigger candidates: {0:d}'.format(removed_candidates))
        print('Removed synthetic trigger timelines: {0:d}'.format(removed_timelines))
        return 0

    cleanup_synthetic(candidate_dir, timeline_dir, args.date)

    candidates, case_results = build_synthetic_trigger_candidates(args.date)
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
    print_summary(candidate_path, timeline_path, case_results, candidate_summary, timeline_summary)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
