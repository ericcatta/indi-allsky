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
    archive_rules = json.loads((ROOT / 'testing/fixtures/archive_policy_hooks.json').read_text())
    replacements = {ast.dump(ast.parse(row['new']).body[0]): ast.parse(row['old']).body for row in archive_rules}
    counts = {key:0 for key in replacements}
    class RestoreArchive(ast.NodeTransformer):
        def visit(self, node):
            key = ast.dump(node)
            if key in replacements:
                counts[key] += 1
                return replacements[key]
            return super().visit(node)
        def visit_If(self, node):
            gates = {
                'archive_policy.save_fits(self.config, images_only)': "not images_only and self.config.get('IMAGE_SAVE_FITS')",
                'archive_policy.save_raw(self.config, images_only)': "not images_only and self.config.get('IMAGE_EXPORT_RAW')",
            }
            old = gates.get(ast.unparse(node.test))
            if old:
                node.test = ast.parse(old, mode='eval').body
            return self.generic_visit(node)
    method = RestoreArchive().visit(method)
    assert sorted(counts.values()) == [1,1,1,1,1,2], counts
    found = []
    class Restore(ast.NodeTransformer):
        def visit_Dict(self, node):
            for i, key in reversed(list(enumerate(node.keys))):
                if isinstance(key, ast.Constant) and key.value in ('render_label', 'render_presentation', 'render_source', 'source_fits_id'):
                    expected = {'render_label':'snapshot_label(self.image_processor)', 'render_presentation':'presentation_record',
                                'render_source':'source_recipe', 'source_fits_id':"fits_result['db_id'] if fits_result else None"}[key.value]
                    assert ast.dump(node.values[i]) == ast.dump(ast.parse(expected, mode='eval').body)
                    node.keys.pop(i); node.values.pop(i)
            return self.generic_visit(node)
        def visit_Expr(self, node):
            if isinstance(node.value, ast.Call) and isinstance(node.value.func, ast.Name) and node.value.func.id in FIXTURE['blocks']:
                name = node.value.func.id
                expected = (f'{name}(self.image_processor, i_ref.binning)' if name == 'render_presentation'
                            else f'{name}(self.image_processor, self.config, self.night_av)')
                assert ast.dump(node) == ast.dump(ast.parse(expected).body[0])
                found.append(name)
                return ast.parse(textwrap.dedent(FIXTURE['blocks'][name])).body
            return self.generic_visit(node)
    context_source = (ROOT / 'indi_allsky/image.py').read_text()
    start = context_source.index('        presentation_record = None\n')
    end = context_source.index('\n        if images_only_diag:', start)
    context_body = ast.parse(textwrap.dedent(context_source[start:end])).body
    # Pin the entire exception boundary, condition and asset destination.
    assert hashlib.sha256(ast.dump(ast.Module(body=context_body, type_ignores=[])).encode()).hexdigest() == '5d045234e2af91fc3a35158fd048890c538fd3a89632f812c60f4c5ffbfac0f2'
    indices = [i for i,n in enumerate(method.body) if isinstance(n,ast.Assign)
               and isinstance(n.targets[0],ast.Name) and n.targets[0].id == 'presentation_record']
    assert len(indices) == 1
    index = indices[0]
    assert ast.dump(ast.Module(body=method.body[index:index+2],type_ignores=[])) == ast.dump(ast.Module(body=context_body,type_ignores=[]))
    del method.body[index:index+2]
    start = context_source.index('        source_basis = None\n')
    end = context_source.index('\n\n        image_height, image_width', start)
    basis_body = ast.parse(textwrap.dedent(context_source[start:end])).body
    assert hashlib.sha256(ast.dump(ast.Module(body=basis_body,type_ignores=[])).encode()).hexdigest() == 'c16387007811621b80999370822d44e01fd0058cc6afe02d79e6ef33759206a6'
    indices = [i for i,n in enumerate(method.body) if isinstance(n,ast.Assign)
               and isinstance(n.targets[0],ast.Name) and n.targets[0].id == 'source_basis']
    assert len(indices) == 1
    index = indices[0]
    assert ast.dump(ast.Module(body=method.body[index:index+2],type_ignores=[])) == ast.dump(ast.Module(body=basis_body,type_ignores=[]))
    del method.body[index:index+2]
    finalizers=[n for n in method.body if isinstance(n,ast.Assign) and isinstance(n.targets[0],ast.Name) and n.targets[0].id=='source_recipe']
    assert len(finalizers)==1
    assert ast.dump(finalizers[0])==ast.dump(ast.parse('source_recipe = self._finalize_fits_source(fits_result, source_basis, presentation_record, libcamera_ccm)').body[0])
    method.body.remove(finalizers[0])
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
