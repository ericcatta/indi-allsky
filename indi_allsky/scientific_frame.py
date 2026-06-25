from dataclasses import asdict
from dataclasses import dataclass


SCIENTIFIC_FRAME_METADATA_VERSION = 'scientific_frame_v1'


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
