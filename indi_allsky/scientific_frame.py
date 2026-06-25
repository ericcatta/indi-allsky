from dataclasses import asdict
from dataclasses import dataclass
from datetime import datetime
from datetime import timezone
import hashlib


SCIENTIFIC_FRAME_METADATA_VERSION = 'scientific_frame_v1'
SCIENTIFIC_FRAME_SEQUENCE_METADATA_VERSION = 'scientific_frame_sequence_v1'


@dataclass(frozen=True)
class ScientificFrame:
    """Immutable contract for the scientific acquisition behind a capture.

    A ScientificFrame represents the non-display scientific frame associated
    with an exposure.  It is intentionally independent from display rendering,
    overlays, JPEG generation, dashboards, thumbnails, and future detector
    implementations.  It may point to FITS or RAW assets when available, but it
    does not create, transform, or validate those files.
    """

    timestamp: str = None
    camera_uuid: str = None
    camera_id: int = None
    profile_id: str = None
    source_image_path: str = None
    detector_image_path: str = None
    detector_image_type: str = None
    fits_path: str = None
    raw_path: str = None
    bit_depth: int = None
    width: int = None
    height: int = None
    exposure: float = None
    gain: float = None
    binning: int = None
    is_lossless: bool = None
    is_calibrated: bool = None
    metadata_version: str = SCIENTIFIC_FRAME_METADATA_VERSION

    @classmethod
    def from_frame_metadata(cls, metadata):
        """Build a contract object from a FrameMetadata-like dict/object.

        This helper is offline/contract-only.  It accepts dictionaries or
        objects exposing attributes and deliberately does not inspect files,
        query databases, or alter runtime behavior.
        """

        def get_value(name, default=None):
            if isinstance(metadata, dict):
                return metadata.get(name, default)
            return getattr(metadata, name, default)

        detector_image_type = get_value('detector_image_type')
        fits_path = get_value('fits_path')
        raw_path = get_value('raw_path')
        exposure = get_value('exposure')
        if exposure is None:
            exposure_us = get_value('exposure_us')
            if exposure_us is not None:
                exposure = float(exposure_us) / 1000000.0

        return cls(
            timestamp=get_value('timestamp'),
            camera_uuid=get_value('camera_uuid'),
            camera_id=get_value('camera_id'),
            profile_id=get_value('profile_id'),
            source_image_path=get_value('source_image_path') or fits_path or raw_path,
            detector_image_path=get_value('detector_image_path') or fits_path or raw_path,
            detector_image_type=detector_image_type,
            fits_path=fits_path,
            raw_path=raw_path,
            bit_depth=get_value('bit_depth'),
            width=get_value('width'),
            height=get_value('height'),
            exposure=exposure,
            gain=get_value('gain'),
            binning=get_value('binning'),
            is_lossless=get_value('is_lossless'),
            is_calibrated=get_value('is_calibrated'),
            metadata_version=get_value('metadata_version', SCIENTIFIC_FRAME_METADATA_VERSION),
        )

    def to_dict(self):
        return asdict(self)


@dataclass(frozen=True)
class ScientificFrameSequence:
    """Detector-neutral ordered sequence of scientific frames.

    A ScientificFrameSequence is raw-first and detector-agnostic.  It represents
    frames from one camera/profile only, preserves timestamp ordering, and does
    not read files, query databases, load pixels, apply masks, or promote
    display images to scientific inputs.
    """

    sequence_id: str
    camera_id: int
    camera_uuid: str
    profile_id: str
    start_timestamp_utc: str
    end_timestamp_utc: str
    frames: tuple
    frame_count: int
    missing_source_count: int
    source_policy: str = 'fits_first_raw_fallback'
    metadata_version: str = SCIENTIFIC_FRAME_SEQUENCE_METADATA_VERSION
    created_at: str = None

    def __post_init__(self):
        object.__setattr__(self, 'frames', tuple(self.frames))
        object.__setattr__(self, 'frame_count', int(self.frame_count))
        object.__setattr__(self, 'missing_source_count', int(self.missing_source_count))
        if self.created_at is None:
            object.__setattr__(self, 'created_at', _utc_now())

    def to_dict(self):
        data = asdict(self)
        data['frames'] = [
            frame.to_dict() if hasattr(frame, 'to_dict') else dict(frame)
            for frame in self.frames
        ]
        return data


def build_scientific_frame_sequence(frames, source_policy='fits_first_raw_fallback'):
    """Build an ordered ScientificFrameSequence from frame contracts/dicts.

    Empty input and mixed camera/profile sequences are rejected.  This keeps the
    contract conservative until explicit cross-camera/cross-profile sequence
    support is designed.
    """

    scientific_frames = [
        frame if isinstance(frame, ScientificFrame) else ScientificFrame.from_frame_metadata(frame)
        for frame in frames
    ]

    if not scientific_frames:
        raise ValueError('ScientificFrameSequence requires at least one frame')

    for frame in scientific_frames:
        if not frame.timestamp:
            raise ValueError('ScientificFrameSequence frames require timestamp')

    ordered_frames = tuple(sorted(scientific_frames, key=lambda frame: _timestamp_sort_key(frame.timestamp)))
    first_frame = ordered_frames[0]
    camera_id = first_frame.camera_id
    camera_uuid = first_frame.camera_uuid
    profile_id = first_frame.profile_id

    for frame in ordered_frames:
        if frame.camera_id != camera_id:
            raise ValueError('ScientificFrameSequence requires one camera_id')
        if frame.profile_id != profile_id:
            raise ValueError('ScientificFrameSequence requires one profile_id')

    missing_source_count = sum(
        1
        for frame in ordered_frames
        if not frame.source_image_path and not frame.detector_image_path
    )

    sequence_id = _build_scientific_frame_sequence_id(
        ordered_frames,
        source_policy,
    )

    return ScientificFrameSequence(
        sequence_id=sequence_id,
        camera_id=camera_id,
        camera_uuid=camera_uuid,
        profile_id=profile_id,
        start_timestamp_utc=ordered_frames[0].timestamp,
        end_timestamp_utc=ordered_frames[-1].timestamp,
        frames=ordered_frames,
        frame_count=len(ordered_frames),
        missing_source_count=missing_source_count,
        source_policy=source_policy,
    )


def _build_scientific_frame_sequence_id(frames, source_policy):
    identity_parts = [str(source_policy)]
    for frame in frames:
        identity_parts.extend((
            str(frame.timestamp),
            str(frame.camera_id),
            str(frame.camera_uuid),
            str(frame.profile_id),
            str(frame.detector_image_path or frame.source_image_path or ''),
        ))

    digest = hashlib.sha256('|'.join(identity_parts).encode('utf-8')).hexdigest()[:24]
    return 'scientific-sequence-{0:s}'.format(digest)


def _timestamp_sort_key(timestamp):
    timestamp_str = str(timestamp)
    if timestamp_str.endswith('Z'):
        timestamp_str = '{0:s}+00:00'.format(timestamp_str[:-1])
    return timestamp_str


def _utc_now():
    return datetime.now(tz=timezone.utc).isoformat()
