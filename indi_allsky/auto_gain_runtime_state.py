import json
import logging
import time
from dataclasses import dataclass
from pathlib import Path


logger = logging.getLogger('indi_allsky')


@dataclass(frozen=True)
class AutoGainRestoreResult:
    gain: float
    reason: str
    restored: bool
    stored_gain: float = None


class AutoGainRuntimeStateStore:
    """Small JSON state store for adaptive Auto Gain values.

    This is intentionally separate from the config database: it is runtime
    state used to seed GAIN_NEXT after service restarts.
    """

    def __init__(self, state_path, max_age_seconds=86400):
        self.state_path = Path(state_path)
        self.max_age_seconds = float(max_age_seconds)


    def save_gain(self, *, profile_id, camera_id, mode, gain, gain_min=None, gain_max=None):
        state = self._load_state()
        records = state.setdefault('records', {})
        records[self._key(profile_id, camera_id, mode)] = {
            'profile_id' : str(profile_id),
            'camera_id'  : str(camera_id),
            'mode'       : str(mode),
            'gain'       : float(gain),
            'gain_min'   : self._optional_float(gain_min),
            'gain_max'   : self._optional_float(gain_max),
            'timestamp'  : time.time(),
        }
        self._write_state(state)


    def restore_gain(self, *, profile_id, camera_id, mode, configured_gain, gain_min, gain_max):
        configured_gain = float(configured_gain)
        gain_min = float(gain_min)
        gain_max = float(gain_max)
        if gain_min > gain_max:
            gain_min, gain_max = gain_max, gain_min

        state = self._load_state()
        records = state.get('records') or {}
        record = records.get(self._key(profile_id, camera_id, mode))
        if not record:
            if self._has_camera_record(records, camera_id):
                return AutoGainRestoreResult(configured_gain, 'profile_changed', False)
            return AutoGainRestoreResult(configured_gain, 'missing', False)

        try:
            stored_gain = float(record.get('gain'))
            timestamp = float(record.get('timestamp'))
        except (TypeError, ValueError):
            return AutoGainRestoreResult(configured_gain, 'missing', False)

        if self.max_age_seconds > 0 and (time.time() - timestamp) > self.max_age_seconds:
            return AutoGainRestoreResult(configured_gain, 'expired', False, stored_gain=stored_gain)

        restored_gain = self._clamp(stored_gain, gain_min, gain_max)
        if restored_gain != stored_gain:
            return AutoGainRestoreResult(restored_gain, 'clamped', True, stored_gain=stored_gain)

        return AutoGainRestoreResult(restored_gain, 'restored', True, stored_gain=stored_gain)


    def _load_state(self):
        try:
            with self.state_path.open('r', encoding='utf-8') as f_state:
                state = json.load(f_state)
        except FileNotFoundError:
            return {'version': 1, 'records': {}}
        except json.JSONDecodeError as e:
            logger.warning('[AUTO_GAIN_RESTORE] state file decode failed path=%s reason=%s', self.state_path, str(e))
            return {'version': 1, 'records': {}}
        except OSError as e:
            logger.warning('[AUTO_GAIN_RESTORE] state file read failed path=%s reason=%s', self.state_path, str(e))
            return {'version': 1, 'records': {}}

        if not isinstance(state, dict):
            return {'version': 1, 'records': {}}
        if not isinstance(state.get('records'), dict):
            state['records'] = {}
        state.setdefault('version', 1)
        return state


    def _write_state(self, state):
        self.state_path.parent.mkdir(parents=True, exist_ok=True)
        tmp_path = self.state_path.with_suffix(self.state_path.suffix + '.tmp')
        with tmp_path.open('w', encoding='utf-8') as f_state:
            json.dump(state, f_state, sort_keys=True, separators=(',', ':'))
            f_state.write('\n')
        tmp_path.replace(self.state_path)


    def _has_camera_record(self, records, camera_id):
        camera_id_str = str(camera_id)
        for record in records.values():
            if isinstance(record, dict) and str(record.get('camera_id')) == camera_id_str:
                return True
        return False


    def _key(self, profile_id, camera_id, mode):
        return '{0:s}:{1:s}:{2:s}'.format(str(profile_id), str(camera_id), str(mode))


    def _clamp(self, value, minimum, maximum):
        return max(minimum, min(maximum, float(value)))


    def _optional_float(self, value):
        try:
            return float(value)
        except (TypeError, ValueError):
            return None


def default_auto_gain_runtime_state_path(varlib_folder):
    return Path(varlib_folder).joinpath('auto_gain_runtime_state.json')
