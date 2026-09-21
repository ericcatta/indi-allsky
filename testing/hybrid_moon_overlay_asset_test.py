#!/usr/bin/env python3
"""Cold image workers load the retained scientific overlay without Classic assets."""
import hashlib
from pathlib import Path
import sys
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from indi_allsky.overlay.moonOverlay import IndiAllSkyMoonOverlay
from run_hybrid_regression import source_hashes


def run():
    asset = ROOT / 'indi_allsky/overlay/assets/moon_rot.png'
    assert hashlib.sha256(asset.read_bytes()).hexdigest() == '856ba0960823bb52177fbfde1502db01f474d693fb2a0e40fdd1ff1966a2feed'
    assert str(asset.relative_to(ROOT)) in source_hashes(ROOT)
    for cycle, phase in ((12, 20), (38, 80), (62, 80), (88, 20)):
        overlay = IndiAllSkyMoonOverlay({'MOON_OVERLAY': {'X': 20, 'Y': 20, 'SCALE': .5}})
        assert overlay.moon_orig is None and overlay.moon_file == asset
        frame = np.zeros((1080, 1920, 3), dtype=np.uint8)
        overlay.apply(frame, cycle, phase)
        assert overlay.moon_orig is not None and overlay.moon_orig.shape[2] == 4
        assert np.count_nonzero(frame) > 0
        assert not np.any(frame[:20]) and not np.any(frame[:, :20])
        second = np.zeros_like(frame)
        overlay.apply(second, cycle, phase)
        assert np.array_equal(frame, second), 'Cold and cached render differ'
    assert 'indi_allsky.flask.classic_views' not in sys.modules
    print('Moon overlay: retained asset fingerprint, manifest inclusion, four cold/cached phases without Classic PASS')


if __name__ == '__main__':
    run()
