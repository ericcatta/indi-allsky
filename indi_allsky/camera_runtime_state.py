from dataclasses import asdict
from dataclasses import dataclass
from typing import Any
from typing import Dict
from typing import Optional


@dataclass
class CameraRuntimeState:
    """Mutable mirror of one camera worker's runtime state.

    MULTI_CAMERA_PREP: this is intentionally passive for now. Existing shared
    arrays and worker-local variables remain the source of behavior.
    """

    camera_id: Optional[int] = None
    camera_name: str = ''
    camera_server: str = ''
    connected: bool = False
    ready: bool = False
    busy: bool = False
    current_exposure: Optional[float] = None
    current_gain: Optional[float] = None
    current_binning: Optional[int] = None
    current_temperature: Optional[float] = None
    last_frame_ts: Optional[float] = None
    last_image_id: Optional[int] = None

    def as_dict(self) -> Dict[str, Any]:
        return asdict(self)
