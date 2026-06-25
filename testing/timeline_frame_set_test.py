import copy
import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from indi_allsky.timeline_frame_set import TIMELINE_FRAME_SET_SCHEMA_VERSION
from indi_allsky.timeline_frame_set import TimelineFrameSet
from indi_allsky.timeline_frame_set import build_timeline_frame_set


def _timeline(candidate_ids=None):
    return {
        'timeline_id': 'timeline-1',
        'camera_id': 2,
        'profile_id': 'asi678mc',
        'night_id': '2026-06-25',
        'start_timestamp_utc': '2026-06-25T20:00:00+00:00',
        'end_timestamp_utc': '2026-06-25T20:00:05+00:00',
        'candidate_ids': candidate_ids or ['candidate-1', 'candidate-2'],
    }


def _candidate(candidate_id, frame_id, timestamp):
    return {
        'candidate_id': candidate_id,
        'camera_id': 2,
        'profile_id': 'asi678mc',
        'frame_id': frame_id,
        'timestamp_utc': timestamp,
        'night_id': '2026-06-25',
    }


def _frame_metadata(frame_id, timestamp, fits_path=None, raw_path=None, display_path=None):
    return {
        'frame_id': frame_id,
        'timestamp': timestamp,
        'camera_id': 2,
        'profile_id': 'asi678mc',
        'camera_uuid': 'camera-uuid',
        'image_file_path': display_path or '/tmp/display-{0}.jpg'.format(frame_id),
        'display_image_path': display_path or '/tmp/display-{0}.jpg'.format(frame_id),
        'fits_path': fits_path,
        'raw_path': raw_path,
        'detector_image_type': 'fits' if fits_path else ('tif' if raw_path else None),
        'exposure_us': 21686,
        'gain': 300.0,
    }


def _write_jsonl(path, rows, malformed=False):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w', encoding='utf-8') as f_jsonl:
        for row in rows:
            json.dump(row, f_jsonl, sort_keys=True, separators=(',', ':'))
            f_jsonl.write('\n')
        if malformed:
            f_jsonl.write('{bad json\n')


def test_resolves_simple_timeline_to_frame_set():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_p = Path(tmpdir)
        candidate_path = tmpdir_p.joinpath('event_candidates.jsonl')
        metadata_path = tmpdir_p.joinpath('frame_metadata.jsonl')
        _write_jsonl(candidate_path, [
            _candidate('candidate-1', 1, '2026-06-25T20:00:00+00:00'),
            _candidate('candidate-2', 2, '2026-06-25T20:00:05+00:00'),
        ])
        _write_jsonl(metadata_path, [
            _frame_metadata(1, '2026-06-25T20:00:00+00:00', fits_path='/tmp/one.fit'),
            _frame_metadata(2, '2026-06-25T20:00:05+00:00', raw_path='/tmp/two.tif'),
        ])

        frame_set = build_timeline_frame_set(_timeline(), candidate_path, frame_metadata_path=metadata_path)

        assert isinstance(frame_set, TimelineFrameSet)
        assert frame_set.schema_version == TIMELINE_FRAME_SET_SCHEMA_VERSION
        assert frame_set.timeline_id == 'timeline-1'
        assert frame_set.resolved_candidate_ids == ['candidate-1', 'candidate-2']
        assert frame_set.sequence.frame_count == 2
        assert frame_set.sequence.frames[0].fits_path == '/tmp/one.fit'
        assert frame_set.sequence.frames[1].raw_path == '/tmp/two.tif'


def test_ordered_frames_by_timestamp():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_p = Path(tmpdir)
        candidate_path = tmpdir_p.joinpath('event_candidates.jsonl')
        metadata_path = tmpdir_p.joinpath('frame_metadata.jsonl')
        _write_jsonl(candidate_path, [
            _candidate('candidate-1', 1, '2026-06-25T20:00:10+00:00'),
            _candidate('candidate-2', 2, '2026-06-25T20:00:00+00:00'),
        ])
        _write_jsonl(metadata_path, [
            _frame_metadata(1, '2026-06-25T20:00:10+00:00', fits_path='/tmp/late.fit'),
            _frame_metadata(2, '2026-06-25T20:00:00+00:00', fits_path='/tmp/early.fit'),
        ])

        frame_set = build_timeline_frame_set(_timeline(), candidate_path, frame_metadata_path=metadata_path)

        assert [frame.timestamp for frame in frame_set.sequence.frames] == [
            '2026-06-25T20:00:00+00:00',
            '2026-06-25T20:00:10+00:00',
        ]


def test_missing_candidate_is_reported():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_p = Path(tmpdir)
        candidate_path = tmpdir_p.joinpath('event_candidates.jsonl')
        metadata_path = tmpdir_p.joinpath('frame_metadata.jsonl')
        _write_jsonl(candidate_path, [_candidate('candidate-1', 1, '2026-06-25T20:00:00+00:00')])
        _write_jsonl(metadata_path, [_frame_metadata(1, '2026-06-25T20:00:00+00:00', fits_path='/tmp/one.fit')])

        frame_set = build_timeline_frame_set(_timeline(), candidate_path, frame_metadata_path=metadata_path)

        assert frame_set.resolved_candidate_ids == ['candidate-1']
        assert frame_set.missing_candidate_ids == ['candidate-2']
        assert frame_set.sequence.frame_count == 1


def test_missing_frame_metadata_is_reported():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_p = Path(tmpdir)
        candidate_path = tmpdir_p.joinpath('event_candidates.jsonl')
        metadata_path = tmpdir_p.joinpath('frame_metadata.jsonl')
        _write_jsonl(candidate_path, [_candidate('candidate-1', 1, '2026-06-25T20:00:00+00:00')])
        _write_jsonl(metadata_path, [])

        frame_set = build_timeline_frame_set(_timeline(['candidate-1']), candidate_path, frame_metadata_path=metadata_path)

        assert frame_set.resolved_candidate_ids == ['candidate-1']
        assert frame_set.missing_frame_metadata_ids == ['1']
        assert frame_set.sequence.frame_count == 0


def test_malformed_candidate_jsonl_skipped():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_p = Path(tmpdir)
        candidate_path = tmpdir_p.joinpath('event_candidates.jsonl')
        metadata_path = tmpdir_p.joinpath('frame_metadata.jsonl')
        _write_jsonl(candidate_path, [_candidate('candidate-1', 1, '2026-06-25T20:00:00+00:00')], malformed=True)
        _write_jsonl(metadata_path, [_frame_metadata(1, '2026-06-25T20:00:00+00:00', fits_path='/tmp/one.fit')])

        frame_set = build_timeline_frame_set(_timeline(['candidate-1']), candidate_path, frame_metadata_path=metadata_path)

        assert frame_set.sequence.frame_count == 1


def test_malformed_frame_metadata_jsonl_skipped():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_p = Path(tmpdir)
        candidate_path = tmpdir_p.joinpath('event_candidates.jsonl')
        metadata_path = tmpdir_p.joinpath('frame_metadata.jsonl')
        _write_jsonl(candidate_path, [_candidate('candidate-1', 1, '2026-06-25T20:00:00+00:00')])
        _write_jsonl(metadata_path, [_frame_metadata(1, '2026-06-25T20:00:00+00:00', fits_path='/tmp/one.fit')], malformed=True)

        frame_set = build_timeline_frame_set(_timeline(['candidate-1']), candidate_path, frame_metadata_path=metadata_path)

        assert frame_set.sequence.frame_count == 1


def test_display_images_are_not_promoted_to_source():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_p = Path(tmpdir)
        candidate_path = tmpdir_p.joinpath('event_candidates.jsonl')
        metadata_path = tmpdir_p.joinpath('frame_metadata.jsonl')
        _write_jsonl(candidate_path, [_candidate('candidate-1', 1, '2026-06-25T20:00:00+00:00')])
        _write_jsonl(metadata_path, [_frame_metadata(1, '2026-06-25T20:00:00+00:00', display_path='/tmp/display.jpg')])

        frame_set = build_timeline_frame_set(_timeline(['candidate-1']), candidate_path, frame_metadata_path=metadata_path)

        assert frame_set.sequence.frame_count == 1
        assert frame_set.sequence.frames[0].source_image_path is None
        assert frame_set.sequence.frames[0].detector_image_path is None
        assert frame_set.sequence.missing_source_count == 1


def test_no_image_files_are_read():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_p = Path(tmpdir)
        candidate_path = tmpdir_p.joinpath('event_candidates.jsonl')
        metadata_path = tmpdir_p.joinpath('frame_metadata.jsonl')
        missing_fits = tmpdir_p.joinpath('does-not-exist.fit')
        _write_jsonl(candidate_path, [_candidate('candidate-1', 1, '2026-06-25T20:00:00+00:00')])
        _write_jsonl(metadata_path, [_frame_metadata(1, '2026-06-25T20:00:00+00:00', fits_path=str(missing_fits))])

        frame_set = build_timeline_frame_set(_timeline(['candidate-1']), candidate_path, frame_metadata_path=metadata_path)

        assert frame_set.sequence.frame_count == 1
        assert frame_set.sequence.frames[0].fits_path == str(missing_fits)


def test_empty_no_resolved_frames_returns_diagnostic_empty_sequence():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_p = Path(tmpdir)
        candidate_path = tmpdir_p.joinpath('missing_candidates.jsonl')

        frame_set = build_timeline_frame_set(_timeline(), candidate_path)

        assert frame_set.missing_candidate_ids == ['candidate-1', 'candidate-2']
        assert frame_set.sequence.frame_count == 0
        assert frame_set.sequence.frames == ()


def test_frame_metadata_dir_date_inference():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_p = Path(tmpdir)
        candidate_path = tmpdir_p.joinpath('event_candidates.jsonl')
        metadata_dir = tmpdir_p.joinpath('frame_metadata')
        metadata_path = metadata_dir.joinpath('2026-06-25.jsonl')
        _write_jsonl(candidate_path, [_candidate('candidate-1', 1, '2026-06-25T20:00:00+00:00')])
        _write_jsonl(metadata_path, [_frame_metadata(1, '2026-06-25T20:00:00+00:00', fits_path='/tmp/one.fit')])

        frame_set = build_timeline_frame_set(_timeline(['candidate-1']), candidate_path, frame_metadata_dir=metadata_dir)

        assert frame_set.sequence.frame_count == 1
        assert frame_set.sequence.frames[0].fits_path == '/tmp/one.fit'


def test_input_timeline_is_not_mutated():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_p = Path(tmpdir)
        candidate_path = tmpdir_p.joinpath('missing_candidates.jsonl')
        timeline = _timeline()
        original = copy.deepcopy(timeline)

        build_timeline_frame_set(timeline, candidate_path)

        assert timeline == original


def test_serialization_preserves_diagnostics():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_p = Path(tmpdir)
        candidate_path = tmpdir_p.joinpath('missing_candidates.jsonl')

        frame_set = build_timeline_frame_set(_timeline(), candidate_path)
        data = frame_set.to_dict()

        assert data['schema_version'] == TIMELINE_FRAME_SET_SCHEMA_VERSION
        assert data['timeline_id'] == 'timeline-1'
        assert data['missing_candidate_ids'] == ['candidate-1', 'candidate-2']
        assert data['sequence']['frame_count'] == 0


if __name__ == '__main__':
    test_resolves_simple_timeline_to_frame_set()
    test_ordered_frames_by_timestamp()
    test_missing_candidate_is_reported()
    test_missing_frame_metadata_is_reported()
    test_malformed_candidate_jsonl_skipped()
    test_malformed_frame_metadata_jsonl_skipped()
    test_display_images_are_not_promoted_to_source()
    test_no_image_files_are_read()
    test_empty_no_resolved_frames_returns_diagnostic_empty_sequence()
    test_frame_metadata_dir_date_inference()
    test_input_timeline_is_not_mutated()
    test_serialization_preserves_diagnostics()
    print('timeline frame set tests OK')
