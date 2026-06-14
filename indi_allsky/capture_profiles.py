from dataclasses import asdict
from dataclasses import dataclass
from typing import Any
from typing import Dict
from typing import List
from typing import Mapping


@dataclass(frozen=True)
class CaptureProfile:
    """Normalized read-only description of one camera capture target.

    This is intentionally a passive data object for the first multi-camera
    refactor step. Runtime workers still use the legacy flat config directly.
    """

    profile_id: str
    enabled: bool
    primary: bool
    camera_interface: str
    indi_server: str
    indi_port: int
    indi_camera_name: str
    libcamera_camera_id: int

    def as_dict(self) -> Dict[str, Any]:
        return asdict(self)


def derive_capture_profiles(config: Mapping[str, Any]) -> List[CaptureProfile]:
    """Derive capture profiles from the current single-camera config.

    The first version deliberately returns exactly one default profile. It does
    not mutate the config and does not enable multi-camera runtime behavior.
    """

    libcamera_config = config.get('LIBCAMERA') or {}

    try:
        indi_port = int(config.get('INDI_PORT', 7624))
    except (TypeError, ValueError):
        indi_port = 7624

    try:
        libcamera_camera_id = int(libcamera_config.get('CAMERA_ID', 0))
    except (TypeError, ValueError):
        libcamera_camera_id = 0

    return [
        CaptureProfile(
            profile_id='default',
            enabled=True,
            primary=True,
            camera_interface=str(config.get('CAMERA_INTERFACE', 'indi') or 'indi'),
            indi_server=str(config.get('INDI_SERVER', 'localhost') or 'localhost'),
            indi_port=indi_port,
            indi_camera_name=str(config.get('INDI_CAMERA_NAME', '') or ''),
            libcamera_camera_id=libcamera_camera_id,
        ),
    ]
