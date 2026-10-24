#!/usr/bin/env python3
"""Compatibility and deterministic edge cases for adaptive MTF v2."""
import hashlib
from pathlib import Path

import numpy as np

from indi_allsky.stretch.mode3_adaptive_mtf import IndiAllSky_Mode3_Adaptive_MTF_Stretch


def config(version=None, midtones=0.30):
    stretch = {
        'CLASSNAME': 'mode3_adaptive_mtf',
        'MODE3_BLACK_CLIP': -2.8,
        'MODE3_SHADOWS': 0.0,
        'MODE3_MIDTONES': midtones,
        'MODE3_HIGHLIGHTS': 1.0,
        'DAYTIME': True,
        'MOONMODE': False,
        'SPLIT': False,
    }
    if version is not None:
        stretch['MODE3_ALGORITHM_VERSION'] = version
    return {'IMAGE_STRETCH': stretch}


legacy_gray = np.arange(64 * 96, dtype=np.uint16).reshape(64, 96) % 4096
legacy_color = ((np.arange(64 * 96 * 3, dtype=np.uint16).reshape(64, 96, 3) * 17 + 23) % 4096)
legacy = IndiAllSky_Mode3_Adaptive_MTF_Stretch(config(None, midtones=0.25))
assert legacy.algorithm_version == 1
assert hashlib.sha256(legacy.stretch(legacy_gray, 12, 1).tobytes()).hexdigest() == \
    '635669106e68b60daeeef3e3796846483721b04940ae9467e59c012893d4420f'
assert hashlib.sha256(legacy.stretch(legacy_color, 12, 1).tobytes()).hexdigest() == \
    'c1c81bbb1e546e11d9586d145c75caf86bbe0561d0ec6be7bbbedbbbdc4aa9e5'

v2 = IndiAllSky_Mode3_Adaptive_MTF_Stretch(config(2))
for flat in (
    np.zeros((32, 48), dtype=np.uint16),
    np.full((32, 48), 701, dtype=np.uint16),
    np.zeros((32, 48, 3), dtype=np.uint16),
    np.full((32, 48, 3), 701, dtype=np.uint16),
):
    np.testing.assert_array_equal(v2.stretch(flat, 12, 1), flat)

for source in (legacy_gray, legacy_color):
    output = v2.stretch(source, 12, 1)
    assert output.shape == source.shape and output.dtype == source.dtype
    assert np.isfinite(output).all()
    assert output.min() == 0 and output.max() == 4095
    # A lookup-table transform must preserve input ordering and channel equality.
    order = np.argsort(source, axis=None)
    ordered_output = output.reshape(-1)[order]
    assert np.all(ordered_output[1:] >= ordered_output[:-1])

# The algorithm choice is part of the frozen render settings. Reconstructing
# from that snapshot ignores later live configuration and reproduces its pixels.
source = ((np.arange(80 * 120 * 3, dtype=np.uint16).reshape(80, 120, 3) * 11 + 7) % 4096)
live_config = config(2)
expected = IndiAllSky_Mode3_Adaptive_MTF_Stretch(live_config).stretch(source, 12, 1)
frozen = {'IMAGE_STRETCH': dict(live_config['IMAGE_STRETCH'])}
assert frozen['IMAGE_STRETCH']['MODE3_ALGORITHM_VERSION'] == 2
source_rendering = (Path(__file__).parents[1] / 'indi_allsky' / 'source_rendering.py').read_text()
assert "'MODE3_ALGORITHM_VERSION'" in source_rendering
assert "'algorithm_version'" in source_rendering
live_config['IMAGE_STRETCH']['MODE3_ALGORITHM_VERSION'] = 1
live_config['IMAGE_STRETCH']['MODE3_MIDTONES'] = 0.8
replayed = IndiAllSky_Mode3_Adaptive_MTF_Stretch(frozen).stretch(source, 12, 1)
np.testing.assert_array_equal(replayed, expected)

# The configured target is monotone: a higher target brightens the same frame.
low = IndiAllSky_Mode3_Adaptive_MTF_Stretch(config(2, midtones=0.25)).stretch(source, 12, 1)
high = IndiAllSky_Mode3_Adaptive_MTF_Stretch(config(2, midtones=0.30)).stretch(source, 12, 1)
assert float(np.median(high)) > float(np.median(low))

print('Adaptive MTF v2 compatibility, degenerates and frozen settings: PASS')
