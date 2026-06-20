import sys
import tempfile
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from indi_allsky.auto_gain_runtime_state import AutoGainRuntimeStateStore


def test_restore_recent_gain():
    with tempfile.TemporaryDirectory() as tmpdir:
        state_path = Path(tmpdir).joinpath('auto_gain_runtime_state.json')
        store = AutoGainRuntimeStateStore(state_path, max_age_seconds=3600)
        store.save_gain(
            profile_id='asi678mc',
            camera_id=2,
            mode='moonmode',
            gain=300.0,
            gain_min=0.0,
            gain_max=300.0,
        )

        restored = store.restore_gain(
            profile_id='asi678mc',
            camera_id=2,
            mode='moonmode',
            configured_gain=100.0,
            gain_min=0.0,
            gain_max=300.0,
        )
        assert restored.restored is True
        assert restored.reason == 'restored'
        assert restored.gain == 300.0


def test_restore_clamps_to_current_limits():
    with tempfile.TemporaryDirectory() as tmpdir:
        state_path = Path(tmpdir).joinpath('auto_gain_runtime_state.json')
        store = AutoGainRuntimeStateStore(state_path, max_age_seconds=3600)
        store.save_gain(
            profile_id='asi678mc',
            camera_id=2,
            mode='moonmode',
            gain=300.0,
            gain_min=0.0,
            gain_max=300.0,
        )

        restored = store.restore_gain(
            profile_id='asi678mc',
            camera_id=2,
            mode='moonmode',
            configured_gain=100.0,
            gain_min=0.0,
            gain_max=220.0,
        )
        assert restored.restored is True
        assert restored.reason == 'clamped'
        assert restored.gain == 220.0


def test_expired_gain_is_not_restored():
    with tempfile.TemporaryDirectory() as tmpdir:
        state_path = Path(tmpdir).joinpath('auto_gain_runtime_state.json')
        store = AutoGainRuntimeStateStore(state_path, max_age_seconds=0.001)
        store.save_gain(
            profile_id='asi678mc',
            camera_id=2,
            mode='moonmode',
            gain=300.0,
        )
        time.sleep(0.01)

        restored = store.restore_gain(
            profile_id='asi678mc',
            camera_id=2,
            mode='moonmode',
            configured_gain=100.0,
            gain_min=0.0,
            gain_max=300.0,
        )
        assert restored.restored is False
        assert restored.reason == 'expired'
        assert restored.gain == 100.0


def test_profile_changed_is_not_restored():
    with tempfile.TemporaryDirectory() as tmpdir:
        state_path = Path(tmpdir).joinpath('auto_gain_runtime_state.json')
        store = AutoGainRuntimeStateStore(state_path, max_age_seconds=3600)
        store.save_gain(
            profile_id='old-profile',
            camera_id=2,
            mode='moonmode',
            gain=300.0,
        )

        restored = store.restore_gain(
            profile_id='asi678mc',
            camera_id=2,
            mode='moonmode',
            configured_gain=100.0,
            gain_min=0.0,
            gain_max=300.0,
        )
        assert restored.restored is False
        assert restored.reason == 'profile_changed'
        assert restored.gain == 100.0


if __name__ == '__main__':
    test_restore_recent_gain()
    test_restore_clamps_to_current_limits()
    test_expired_gain_is_not_restored()
    test_profile_changed_is_not_restored()
    print('auto gain runtime state tests OK')
