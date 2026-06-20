import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from indi_allsky.frame_metadata import FrameMetadata
from indi_allsky.frame_metadata import FrameMetadataWriter


def test_frame_metadata_jsonl_write():
    with tempfile.TemporaryDirectory() as tmpdir:
        metadata_path = Path(tmpdir).joinpath('frame_metadata.jsonl')
        writer = FrameMetadataWriter(metadata_path)
        metadata = FrameMetadata(
            frame_id=42,
            timestamp='2026-06-21T12:00:00+00:00',
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

        writer.write(metadata)
        rows = metadata_path.read_text(encoding='utf-8').splitlines()
        assert len(rows) == 1

        row = json.loads(rows[0])
        assert row['frame_id'] == 42
        assert row['camera_id'] == 2
        assert row['profile_id'] == 'asi678mc'
        assert row['exposure_us'] == 21686
        assert row['auto_gain_action'] == 'increase_gain'
        assert row['quality_flags'] == []


if __name__ == '__main__':
    test_frame_metadata_jsonl_write()
    print('frame metadata tests OK')
