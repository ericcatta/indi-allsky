from dataclasses import dataclass
from typing import Any
from typing import Dict


@dataclass
class CameraSharedState:
    """Adapter around shared multiprocessing arrays for one camera.

    MULTI_CAMERA_PREP: this keeps the existing arrays authoritative while
    giving future workers one per-camera state object to pass around.
    """

    profile_id: str
    position_av: Any
    exposure_av: Any
    gain_av: Any
    binning_av: Any
    sensors_temp_av: Any
    sensors_user_av: Any
    night_av: Any
    astro_av: Any
    hybrid_av: Any = None

    def summary(self) -> Dict[str, str]:
        return {
            'profile_id': self.profile_id,
            'position_av': type(self.position_av).__name__,
            'exposure_av': type(self.exposure_av).__name__,
            'gain_av': type(self.gain_av).__name__,
            'binning_av': type(self.binning_av).__name__,
            'sensors_temp_av': type(self.sensors_temp_av).__name__,
            'sensors_user_av': type(self.sensors_user_av).__name__,
            'night_av': type(self.night_av).__name__,
            'astro_av': type(self.astro_av).__name__,
            'hybrid_av': type(self.hybrid_av).__name__,
        }
