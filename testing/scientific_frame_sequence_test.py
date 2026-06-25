import copy
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from indi_allsky.scientific_frame import SCIENTIFIC_FRAME_SEQUENCE_METADATA_VERSION
from indi_allsky.scientific_frame import ScientificFrame
from indi_allsky.scientific_frame import build_scientific_frame_sequence


def _frame(timestamp, camera_id=2, profile_id='asi678mc', source='/tmp/frame.fit'):
    return ScientificFrame(
        timestamp=timestamp,
        camera_uuid='camera-uuid-{0}'.format(camera_id),
        camera_id=camera_id,
        profile_id=profile_id,
        source_image_path=source,
        detector_image_path=source,
        detector_image_type='fits' if source else None,
        fits_path=source if source and source.endswith('.fit') else None,
        exposure=14.0,
        gain=220.0,
        binning=1,
    )


def test_build_sequence_from_ordered_frames():
    sequence = build_scientific_frame_sequence([
        _frame('2026-06-25T20:00:00+00:00', source='/tmp/one.fit'),
        _frame('2026-06-25T20:00:05+00:00', source='/tmp/two.fit'),
    ])

    assert sequence.frame_count == 2
    assert sequence.camera_id == 2
    assert sequence.profile_id == 'asi678mc'
    assert sequence.start_timestamp_utc == '2026-06-25T20:00:00+00:00'
    assert sequence.end_timestamp_utc == '2026-06-25T20:00:05+00:00'
    assert sequence.missing_source_count == 0
    assert sequence.metadata_version == SCIENTIFIC_FRAME_SEQUENCE_METADATA_VERSION


def test_build_sequence_sorts_unordered_frames():
    sequence = build_scientific_frame_sequence([
        _frame('2026-06-25T20:00:10+00:00', source='/tmp/three.fit'),
        _frame('2026-06-25T20:00:00+00:00', source='/tmp/one.fit'),
        _frame('2026-06-25T20:00:05+00:00', source='/tmp/two.fit'),
    ])

    assert [frame.timestamp for frame in sequence.frames] == [
        '2026-06-25T20:00:00+00:00',
        '2026-06-25T20:00:05+00:00',
        '2026-06-25T20:00:10+00:00',
    ]


def test_sequence_id_is_deterministic():
    frames = [
        _frame('2026-06-25T20:00:00+00:00', source='/tmp/one.fit'),
        _frame('2026-06-25T20:00:05+00:00', source='/tmp/two.fit'),
    ]

    first = build_scientific_frame_sequence(frames)
    second = build_scientific_frame_sequence(list(reversed(frames)))

    assert first.sequence_id == second.sequence_id


def test_missing_source_count():
    sequence = build_scientific_frame_sequence([
        _frame('2026-06-25T20:00:00+00:00', source='/tmp/one.fit'),
        _frame('2026-06-25T20:00:05+00:00', source=None),
    ])

    assert sequence.frame_count == 2
    assert sequence.missing_source_count == 1


def test_camera_mismatch_is_rejected():
    try:
        build_scientific_frame_sequence([
            _frame('2026-06-25T20:00:00+00:00', camera_id=1),
            _frame('2026-06-25T20:00:05+00:00', camera_id=2),
        ])
    except ValueError as e:
        assert 'camera_id' in str(e)
        return

    raise AssertionError('camera_id mismatch must be rejected')


def test_profile_mismatch_is_rejected():
    try:
        build_scientific_frame_sequence([
            _frame('2026-06-25T20:00:00+00:00', profile_id='asi678mc'),
            _frame('2026-06-25T20:00:05+00:00', profile_id='imx708-wide'),
        ])
    except ValueError as e:
        assert 'profile_id' in str(e)
        return

    raise AssertionError('profile_id mismatch must be rejected')


def test_input_frames_are_not_mutated():
    frame_dicts = [
        {
            'timestamp': '2026-06-25T20:00:00+00:00',
            'camera_id': 2,
            'profile_id': 'asi678mc',
            'fits_path': '/tmp/one.fit',
            'display_image_path': '/tmp/display.jpg',
        },
    ]
    original = copy.deepcopy(frame_dicts)

    build_scientific_frame_sequence(frame_dicts)

    assert frame_dicts == original


def test_sequence_serialization_preserves_fields():
    sequence = build_scientific_frame_sequence([
        _frame('2026-06-25T20:00:00+00:00', source='/tmp/one.fit'),
    ])
    data = sequence.to_dict()

    assert data['sequence_id'] == sequence.sequence_id
    assert data['frame_count'] == 1
    assert data['missing_source_count'] == 0
    assert data['metadata_version'] == SCIENTIFIC_FRAME_SEQUENCE_METADATA_VERSION
    assert data['frames'][0]['fits_path'] == '/tmp/one.fit'


def test_empty_input_is_rejected():
    try:
        build_scientific_frame_sequence([])
    except ValueError as e:
        assert 'at least one frame' in str(e)
        return

    raise AssertionError('empty sequence input must be rejected')


def test_display_path_is_not_promoted_to_source():
    sequence = build_scientific_frame_sequence([
        {
            'timestamp': '2026-06-25T20:00:00+00:00',
            'camera_id': 2,
            'profile_id': 'asi678mc',
            'display_image_path': '/tmp/display.jpg',
            'image_file_path': '/tmp/display.jpg',
        },
    ])

    assert sequence.frames[0].source_image_path is None
    assert sequence.frames[0].detector_image_path is None
    assert sequence.missing_source_count == 1


if __name__ == '__main__':
    test_build_sequence_from_ordered_frames()
    test_build_sequence_sorts_unordered_frames()
    test_sequence_id_is_deterministic()
    test_missing_source_count()
    test_camera_mismatch_is_rejected()
    test_profile_mismatch_is_rejected()
    test_input_frames_are_not_mutated()
    test_sequence_serialization_preserves_fields()
    test_empty_input_is_rejected()
    test_display_path_is_not_promoted_to_source()
    print('scientific frame sequence tests OK')
