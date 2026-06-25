import json
import logging
from dataclasses import asdict
from dataclasses import dataclass
from datetime import datetime
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
    display_image_path: str = None
    source_image_path: str = None
    detector_image_path: str = None
    detector_image_type: str = None
    fits_path: str = None
    raw_path: str = None
    thumbnail_path: str = None
    overlay_applied: bool = False
    stretch_applied: bool = False
    rendering_profile: str = 'indi-allsky-display-v1'

    def __post_init__(self):
        if self.display_image_path is None:
            self.display_image_path = self.image_file_path

    def to_dict(self):
        return asdict(self)


class FrameMetadataWriter:
    """Append-only JSONL persistence for frame analytics metadata."""

    def __init__(self, metadata_path, rotate_daily=False):
        self.metadata_path = Path(metadata_path)
        self.rotate_daily = bool(rotate_daily)


    def write(self, metadata):
        metadata_path = self._metadata_path_for(metadata)
        metadata_path.parent.mkdir(parents=True, exist_ok=True)
        with metadata_path.open('a', encoding='utf-8') as f_metadata:
            json.dump(metadata.to_dict(), f_metadata, sort_keys=True, separators=(',', ':'))
            f_metadata.write('\n')
        return metadata_path


    def _metadata_path_for(self, metadata):
        if not self.rotate_daily:
            return self.metadata_path

        return self.metadata_path.joinpath('{0:s}.jsonl'.format(self._date_from_timestamp(metadata.timestamp)))


    def _date_from_timestamp(self, timestamp):
        timestamp_str = str(timestamp or '').strip()
        if timestamp_str.endswith('Z'):
            timestamp_str = '{0:s}+00:00'.format(timestamp_str[:-1])

        try:
            return datetime.fromisoformat(timestamp_str).date().isoformat()
        except ValueError:
            if len(timestamp_str) >= 10:
                return datetime.fromisoformat(timestamp_str[:10]).date().isoformat()
            raise


def default_frame_metadata_path(varlib_folder):
    return Path(varlib_folder).joinpath('frame_metadata.jsonl')


def default_frame_metadata_dir(varlib_folder):
    return Path(varlib_folder).joinpath('frame_metadata')
