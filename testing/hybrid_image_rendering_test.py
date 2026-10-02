#!/usr/bin/env python3
"""Parity against captured worker statements, including partial failures/order."""
import ast
import hashlib
import itertools
import json
from pathlib import Path
import sys
import textwrap
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from indi_allsky import constants
from indi_allsky import image_rendering

FIXTURE = json.loads((ROOT / 'testing/fixtures/image_rendering_legacy.json').read_text())


def legacy(name, processor, config, night_av):
    exec(compile(textwrap.dedent(FIXTURE['blocks'][name]), '<capture-baseline>', 'exec'),
         {'self': SimpleNamespace(image_processor=processor, config=config, night_av=night_av),
          'i_ref': SimpleNamespace(binning=2), 'constants': constants})


def shared(name, processor, config, night_av):
    fn = getattr(image_rendering, name)
    return fn(processor, 2) if name == 'render_presentation' else fn(processor, config, night_av)


class Trace:
    def __init__(self, fail=None):
        self.calls, self.fail = [], fail

    def __getattr__(self, name):
        def call(*args):
            self.calls.append((name, args))
            if name == self.fail:
                raise ValueError('render failure', name)
        return call


def result(fn, name, config, night, fail):
    processor = Trace(fail)
    try:
        value = fn(name, processor, config, [night, 0])
        return value, processor.calls, None
    except Exception as error:
        return None, processor.calls, (type(error), error.args)


def run():
    # Restore delegation sites to frozen statements; every other worker statement
    # and its position must remain identical to the pre-extraction implementation.
    tree = ast.parse((ROOT / 'indi_allsky/image.py').read_text())
    method = next(n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name == 'processImage')
    found = []
    class Restore(ast.NodeTransformer):
        def visit_Expr(self, node):
            if isinstance(node.value, ast.Call) and isinstance(node.value.func, ast.Name) and node.value.func.id in FIXTURE['blocks']:
                name = node.value.func.id
                expected = (f'{name}(self.image_processor, i_ref.binning)' if name == 'render_presentation'
                            else f'{name}(self.image_processor, self.config, self.night_av)')
                assert ast.dump(node) == ast.dump(ast.parse(expected).body[0])
                found.append(name)
                return ast.parse(textwrap.dedent(FIXTURE['blocks'][name])).body
            return self.generic_visit(node)
    method = Restore().visit(method)
    assert found == list(FIXTURE['blocks'])
    assert hashlib.sha256(ast.dump(method, include_attributes=False).encode()).hexdigest() == FIXTURE['processImage_ast_sha256']
    for night, high_depth, day_contrast, night_contrast in itertools.product((False, True), repeat=4):
        config = dict(CONTRAST_ENHANCE_16BIT=high_depth, DAYTIME_CONTRAST_ENHANCE=day_contrast,
                      NIGHT_CONTRAST_ENHANCE=night_contrast)
        for name in FIXTURE['blocks']:
            methods = [call[0] for call in result(legacy, name, config, night, None)[1]]
            for fail in (None, *methods):
                assert result(shared, name, config, night, fail) == result(legacy, name, config, night, fail)
            for missing in config:
                incomplete = dict(config); del incomplete[missing]
                assert result(shared, name, incomplete, night, None) == result(legacy, name, incomplete, night, None)
    print('Shared rendering: entire worker AST parity, stage order, day/night, CLAHE paths and partial failures: PASS')

if __name__ == '__main__':
    run()
