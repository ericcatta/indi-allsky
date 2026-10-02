#!/usr/bin/env python3
"""Capture/replay label pixels despite changed live templates/styles and sensors."""
from copy import deepcopy
from datetime import datetime
from multiprocessing import Array
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch
import json
import numpy as np
from hybrid_runtime_fixture import isolated_app

with isolated_app() as app, app.app_context():
    from indi_allsky import processing
    from indi_allsky.config import IndiAllSkyConfigBase
    from indi_allsky.image_labels import snapshot_label, render_saved_label
    ImageProcessor = processing.ImageProcessor
    Legacy = type('LegacyLabelProcessor', (ImageProcessor,), {})
    captured = json.loads((Path(__file__).parent / 'fixtures/image_label_legacy.json').read_text())
    for name, code in captured['methods'].items():
        namespace = vars(processing).copy()
        # Source segments include method indentation after the first line.
        lines = code.splitlines()
        code = '\n'.join([lines[0]] + [line[4:] if line.startswith('    ') else line for line in lines[1:]])
        exec(compile(code, '<frozen-label-baseline>', 'exec'), namespace)
        setattr(Legacy, name, namespace[name])

    def processor(cls, system, focus=False):
        config = deepcopy(IndiAllSkyConfigBase().base_config)
        config['IMAGE_LABEL_SYSTEM'] = system
        config['FOCUS_MODE'] = focus
        p = cls(config, Array('f',[46,8,200]), Array('f',[0]), Array('i',[1]),
                Array('f',[0]*60), Array('f',[0]*110), Array('i',[1,0]), Array('f',[0]*3))
        p.image_list = [SimpleNamespace(exp_date=datetime(2020,1,1,12,34,56))]
        p.image = np.zeros((300,640,3), dtype=np.uint8)
        p.get_image_label = Mock(return_value='2020-01-01 12:34:56\nExposure 2.0 Gain 0\nTemp -5.0 Stars 42')
        return p

    for system in ('opencv','pillow'):
        original = processor(Legacy, system)
        original.label_image()
        p = processor(ImageProcessor, system)
        p.label_image()
        np.testing.assert_array_equal(p.image, original.image)
        expected = p.image.copy()
        snapshot = snapshot_label(p)
        snapshot_before = deepcopy(snapshot)
        assert snapshot['text'] == p.get_image_label.return_value
        # A later preview must not query live text or reuse current style.
        p.config['TEXT_PROPERTIES']['FONT_X'] = 200
        p.config['TEXT_PROPERTIES']['FONT_COLOR'][0] = 0
        p.config['IMAGE_LABEL_SYSTEM'] = 'off'
        p.get_image_label = Mock(side_effect=AssertionError('Live label evaluated during replay'))
        current = p.config
        p.image = np.zeros_like(expected)
        render_saved_label(p, snapshot)
        np.testing.assert_array_equal(p.image, expected)
        assert p.config is current
        assert snapshot == snapshot_before
        # Empty captured text is different from missing text.
        empty = dict(snapshot, text='')
        p.image = np.zeros_like(expected)
        render_saved_label(p, empty)
        assert not p.image.any()
        with patch.object(p, 'label_image', side_effect=RuntimeError('encoder failure')):
            try: render_saved_label(p, snapshot)
            except RuntimeError: pass
            else: raise AssertionError('Failure swallowed')
        assert p.config is current
        p.config['IMAGE_LABEL_SYSTEM'] = 'off'
        p.label_image()
        assert p.last_label_text is None
        disabled = snapshot_label(p)
        assert disabled['mode'] == 'off' and disabled['text'] is None
        p.image = np.zeros_like(expected)
        render_saved_label(p, disabled)
        assert not p.image.any()
        # Focus OpenCV previously raised AttributeError for uninitialized image_xy.
        focus = processor(ImageProcessor, system, True)
        focus.get_image_label = Mock(side_effect=AssertionError('Focus evaluated template'))
        focus.label_image()
        assert focus.image.any()
        focus_expected = focus.image.copy()
        focus_saved = snapshot_label(focus)
        assert focus_saved['mode'] == 'focus' and focus_saved['text'] is None
        focus.image = np.zeros_like(focus_expected)
        render_saved_label(focus, focus_saved)
        np.testing.assert_array_equal(focus.image, focus_expected)

    for invalid in ({'version':99}, {'version':1,'mode':'text','text':None},
                    {'version':1,'mode':'text','text':'x','style':{}}):
        p = processor(ImageProcessor, 'pillow')
        before = p.config
        try: render_saved_label(p, invalid)
        except ValueError: pass
        else: raise AssertionError('Incomplete label accepted')
        assert p.config is before
print('Labels: frozen capture pixel parity, saved text/styles replay, no live reads, empty/off/focus states, failure restoration and invalid snapshots: PASS')
