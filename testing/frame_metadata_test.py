import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from indi_allsky.frame_metadata import FrameMetadata
from indi_allsky.frame_metadata import FrameMetadataWriter
from indi_allsky.frame_metadata import default_frame_metadata_dir


def _metadata(frame_id=42, timestamp='2026-06-21T12:00:00+00:00'):
    return FrameMetadata(
        frame_id=frame_id,
        timestamp=timestamp,
        camera_id=2,
        profile_id='asi678mc',
        image_file_path='/var/lib/indi-allsky/images/ccd2.jpg',
        exposure_us=21686,
        gain=300.0,
        meter_value_raw=91.0,
        meter_value_smoothed=94.5,
        target_meter=95.0,
        meter_error=0.5,
        auto_exposure_action='hold',
        auto_gain_action='increase_gain',
        decision_reason='gain_increase_conditions_satisfied',
        capture_status='processed',
        error_message='',
        quality_score=0.0,
        quality_flags=[],
    )


def test_frame_metadata_fixed_jsonl_write():
    with tempfile.TemporaryDirectory() as tmpdir:
        metadata_path = Path(tmpdir).joinpath('frame_metadata.jsonl')
        writer = FrameMetadataWriter(metadata_path)

        writer.write(_metadata())
        rows = metadata_path.read_text(encoding='utf-8').splitlines()
        assert len(rows) == 1

        row = json.loads(rows[0])
        assert row['frame_id'] == 42
        assert row['camera_id'] == 2
        assert row['profile_id'] == 'asi678mc'
        assert row['exposure_us'] == 21686
        assert row['auto_gain_action'] == 'increase_gain'
        assert row['quality_flags'] == []


def test_frame_metadata_daily_filename_selection():
    with tempfile.TemporaryDirectory() as tmpdir:
        metadata_dir = Path(tmpdir).joinpath('frame_metadata')
        writer = FrameMetadataWriter(metadata_dir, rotate_daily=True)

        metadata_path = writer.write(_metadata(timestamp='2026-06-21T23:59:59+00:00'))

        assert metadata_dir.joinpath('2026-06-21.jsonl').exists()
        assert metadata_path == metadata_dir.joinpath('2026-06-21.jsonl')


def test_frame_metadata_default_daily_directory_case():
    with tempfile.TemporaryDirectory() as tmpdir:
        metadata_dir = default_frame_metadata_dir(tmpdir)
        writer = FrameMetadataWriter(metadata_dir, rotate_daily=True)

        metadata_path = writer.write(_metadata(timestamp='2026-06-21T12:00:00+00:00'))

        assert metadata_dir.is_dir()
        assert metadata_path == metadata_dir.joinpath('2026-06-21.jsonl')
        assert metadata_path.exists()


def test_frame_metadata_same_day_appends_to_same_file():
    with tempfile.TemporaryDirectory() as tmpdir:
        metadata_dir = Path(tmpdir).joinpath('frame_metadata')
        writer = FrameMetadataWriter(metadata_dir, rotate_daily=True)

        writer.write(_metadata(frame_id=1, timestamp='2026-06-21T01:00:00+00:00'))
        writer.write(_metadata(frame_id=2, timestamp='2026-06-21T23:00:00+00:00'))

        rows = metadata_dir.joinpath('2026-06-21.jsonl').read_text(encoding='utf-8').splitlines()
        assert len(rows) == 2
        assert json.loads(rows[0])['frame_id'] == 1
        assert json.loads(rows[1])['frame_id'] == 2


def test_frame_metadata_different_days_split_files():
    with tempfile.TemporaryDirectory() as tmpdir:
        metadata_dir = Path(tmpdir).joinpath('frame_metadata')
        writer = FrameMetadataWriter(metadata_dir, rotate_daily=True)

        writer.write(_metadata(frame_id=1, timestamp='2026-06-21T23:59:59+00:00'))
        writer.write(_metadata(frame_id=2, timestamp='2026-06-22T00:00:00+00:00'))

        assert metadata_dir.joinpath('2026-06-21.jsonl').exists()
        assert metadata_dir.joinpath('2026-06-22.jsonl').exists()
        assert len(metadata_dir.joinpath('2026-06-21.jsonl').read_text(encoding='utf-8').splitlines()) == 1
        assert len(metadata_dir.joinpath('2026-06-22.jsonl').read_text(encoding='utf-8').splitlines()) == 1


def test_frame_metadata_custom_path_stays_single_file_without_rotation():
    with tempfile.TemporaryDirectory() as tmpdir:
        metadata_path = Path(tmpdir).joinpath('custom_metadata.jsonl')
        writer = FrameMetadataWriter(metadata_path, rotate_daily=False)

        written_path = writer.write(_metadata(timestamp='2026-06-21T12:00:00+00:00'))

        assert written_path == metadata_path
        assert metadata_path.exists()


def test_frame_metadata_custom_path_rotates_when_enabled():
    with tempfile.TemporaryDirectory() as tmpdir:
        metadata_dir = Path(tmpdir).joinpath('custom_metadata')
        writer = FrameMetadataWriter(metadata_dir, rotate_daily=True)

        written_path = writer.write(_metadata(timestamp='2026-06-21T12:00:00+00:00'))

        assert written_path == metadata_dir.joinpath('2026-06-21.jsonl')
        assert written_path.exists()


def test_frame_metadata_daily_directory_auto_creation():
    with tempfile.TemporaryDirectory() as tmpdir:
        metadata_dir = Path(tmpdir).joinpath('missing', 'frame_metadata')
        writer = FrameMetadataWriter(metadata_dir, rotate_daily=True)

        writer.write(_metadata())

        assert metadata_dir.is_dir()
        assert metadata_dir.joinpath('2026-06-21.jsonl').exists()


if __name__ == '__main__':
    test_frame_metadata_fixed_jsonl_write()
    test_frame_metadata_daily_filename_selection()
    test_frame_metadata_default_daily_directory_case()
    test_frame_metadata_same_day_appends_to_same_file()
    test_frame_metadata_different_days_split_files()
    test_frame_metadata_custom_path_stays_single_file_without_rotation()
    test_frame_metadata_custom_path_rotates_when_enabled()
    test_frame_metadata_daily_directory_auto_creation()
    print('frame metadata tests OK')
