#!/usr/bin/env python3
"""Round-trip portable acquisition metadata without credentials or pixel changes."""
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace
from copy import deepcopy
import io
import json
import sys
import gzip
import numpy as np
from astropy.io import fits

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from indi_allsky.fits_context import capture_context, with_context, read_context, EXTENSION, MAX_BYTES

config = {
    'IMAGE_SAVE_FITS_PRE_DARK': True,
    'IMAGE_STRETCH': {'CLASSNAME': 'mode1_stddev_cutoff', 'MODE1_GAMMA': 3, 'UNKNOWN_SECRET': 'hidden'},
    'IMAGE_FLIP_V': True,
    'FILETRANSFER': {'PASSWORD': 'hidden'}, 'PASSWORD_KEY': 'hidden',
    'ADSB': {'URL': 'https://user:hidden@example.invalid'},
}
ref = SimpleNamespace(camera_id=2, camera_uuid='camera-2', exp_date=datetime(2026, 1, 1, 12, tzinfo=timezone.utc),
                      exposure=1.5, gain=np.float32(12.5), binning=2, calibrated=False)
context = capture_context(config, ref, profile_id='profile-2', night=True, moonmode=False)
assert context['stage'] == 'pre_calibration'
assert context['utc_offset_seconds'] == 0
assert 'hidden' not in json.dumps(context)
assert context['rendering_settings']['IMAGE_STRETCH'] == {'CLASSNAME': 'mode1_stddev_cutoff', 'MODE1_GAMMA': 3}
config['IMAGE_STRETCH']['MODE1_GAMMA'] = 99
assert context['rendering_settings']['IMAGE_STRETCH']['MODE1_GAMMA'] == 3
for dtype, shape in ((np.uint8, (3, 8, 16)), (np.uint16, (8, 16)), (np.float32, (8, 16))):
    pixels = np.arange(np.prod(shape), dtype=dtype).reshape(shape)
    source = fits.HDUList([fits.PrimaryHDU(pixels), fits.ImageHDU(np.ones((2, 2)), name='OTHER')])
    header = source[0].header.copy()
    for compressed in (False, True):
        output = with_context(source, context)
        buffer = io.BytesIO(); output.writeto(buffer)
        raw = buffer.getvalue()
        if compressed:
            raw = gzip.decompress(gzip.compress(raw))
        with fits.open(io.BytesIO(raw)) as restored:
            assert read_context(restored) == context
            np.testing.assert_array_equal(restored[0].data, pixels)
            np.testing.assert_array_equal(restored['OTHER'].data, source['OTHER'].data)
        assert len(source) == 2
        assert source[0].header == header
        np.testing.assert_array_equal(source[0].data, pixels)
    replacement = with_context(output, dict(context, profile_id='replacement'))
    assert len(replacement) == 3
    assert read_context(replacement)['profile_id'] == 'replacement'
    assert read_context(output)['profile_id'] == 'profile-2'

assert read_context(fits.HDUList([fits.PrimaryHDU()])) is None
for mutate in (
    lambda h: h.append(h[-1].copy()),
    lambda h: h[-1].header.__setitem__('CTXVER', 999),
    lambda h: h[-1].header.__setitem__('NAXIS1', MAX_BYTES + 1),
    lambda h: h[-1].__setattr__('data', np.frombuffer(b'{bad json', dtype=np.uint8).copy()),
    lambda h: h[-1].__setattr__('data', np.frombuffer(b'{"version":1,"gain":NaN}', dtype=np.uint8).copy()),
):
    hdus = with_context(fits.HDUList([fits.PrimaryHDU()]), context)
    mutate(hdus)
    try:
        read_context(hdus)
    except ValueError:
        pass
    else:
        raise AssertionError('Malformed context accepted')
try:
    with_context(fits.HDUList([fits.PrimaryHDU()]), {'version': 1, 'value': 'x' * MAX_BYTES})
except ValueError:
    pass
else:
    raise AssertionError('Oversized context accepted')
print('FITS context: capture identity/phase, whitelist, immutable snapshot, mono/RGB typed pixels, gzip, other extensions and malformed/oversized input: PASS')
