import json
import logging
from dataclasses import asdict
from dataclasses import dataclass
from pathlib import Path


logger = logging.getLogger('indi_allsky')


@dataclass
class FrameMetadata:
    frame_id: int
    timestamp: str
    camera_id: int
    profile_id: str
    image_file_path: str
    exposure_us: int
    gain: float
    meter_value_raw: float
    meter_value_smoothed: float
    target_meter: float
    meter_error: float
    auto_exposure_action: str
    auto_gain_action: str
    decision_reason: str
    capture_status: str
    error_message: str
    quality_score: float
    quality_flags: list

    def to_dict(self):
        return asdict(self)


class FrameMetadataWriter:
    """Append-only JSONL persistence for frame analytics metadata."""

    def __init__(self, metadata_path):
        self.metadata_path = Path(metadata_path)


    def write(self, metadata):
        self.metadata_path.parent.mkdir(parents=True, exist_ok=True)
        with self.metadata_path.open('a', encoding='utf-8') as f_metadata:
            json.dump(metadata.to_dict(), f_metadata, sort_keys=True, separators=(',', ':'))
            f_metadata.write('\n')


def default_frame_metadata_path(varlib_folder):
    return Path(varlib_folder).joinpath('frame_metadata.jsonl')
