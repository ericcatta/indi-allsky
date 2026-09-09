#!/usr/bin/env python3
"""Verify worker metering uses the processor's camera-sized ROI with real pixels."""
import ast
import logging
from pathlib import Path
import sys
from types import SimpleNamespace

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from indi_allsky.auto_meter import measure_auto_exposure


def run():
    path = Path(__file__).resolve().parents[1] / 'indi_allsky/image.py'
    tree = ast.parse(path.read_text())
    cls = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == 'ImageWorker')
    method = next(n for n in cls.body if isinstance(n, ast.FunctionDef) and n.name == '_meter_auto_exposure')
    namespace = dict(measure_auto_exposure=measure_auto_exposure,
                     logger=logging.getLogger('metering-mask-test'))
    exec(compile(ast.Module(body=[method], type_ignores=[]), str(path), 'exec'), namespace)
    worker = SimpleNamespace(
        _auto_exposure_metering_mode=lambda: 'average',
        _update_auto_meter_state=lambda *args: {},
        _decide_auto_exposure_shadow=lambda *args: None,
        _decide_auto_gain_shadow=lambda *args: None,
    )
    cache = {}
    # Different camera sizes share binning; an obsolete entry must never win.
    cache[1] = np.ones((4, 8), dtype=np.uint8)
    for camera, height, width in ((1, 4, 8), (2, 6, 10), (1, 4, 8)):
        pixels = np.full((height, width), 240, dtype=np.uint8)
        pixels[1:3, 1:3] = 40
        mask = np.zeros_like(pixels)
        mask[1:3, 1:3] = 255
        cache[(1, width, height)] = mask
        worker.image_processor = SimpleNamespace(image=pixels, _adu_mask_dict=cache)
        result = namespace['_meter_auto_exposure'](worker, str(camera), camera, 1)
        assert result is not None
        assert result.measured_value == 40, result
        assert result.sample_count == 4
        assert result.excluded_pixels == pixels.size - 4
    # Missing masks retain the existing full-frame fallback, without reusing
    # an entry belonging to another shape or binning.
    for binning in (1, 2):
        pixels = np.full((3, 7), 80, dtype=np.uint8)
        worker.image_processor = SimpleNamespace(image=pixels, _adu_mask_dict=cache)
        result = namespace['_meter_auto_exposure'](worker, 'other', 3, binning)
        assert result.measured_value == 80 and result.sample_count == pixels.size
    print('Hybrid metering mask: PASS')


if __name__ == '__main__':
    run()
