#!/usr/bin/env python3
"""Preserve form defaults, parser assignments and scientific stage calls."""
import ast
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
BASELINE=json.loads((ROOT/'testing/fixtures/hybrid_fits_processing_parity.json').read_text())
FLASK=ROOT/'indi_allsky/flask'


def digest(body):
    return hashlib.sha256(ast.dump(ast.Module(body=body,type_ignores=[]),include_attributes=False).encode()).hexdigest()


def run():
    tree=ast.parse((FLASK/'image_processing_form.py').read_text())
    form=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='processing_form')
    assert isinstance(form.body[-1],ast.Return)
    assert digest(form.body[:-1])==BASELINE['form_ast_sha256']
    tree=ast.parse((FLASK/'image_processing_config.py').read_text())
    fields=next(n for n in tree.body if isinstance(n,ast.Assign) and n.targets[0].id=='REQUIRED_FIELDS')
    assert list(ast.literal_eval(fields.value))==BASELINE['required_fields']
    parser=next(n for n in tree.body if isinstance(n,ast.FunctionDef))
    assert ast.unparse(parser.body[0])=='p_config = deepcopy(config)'
    parser.body[0].value=ast.parse('config.copy()',mode='eval').body
    assert digest(parser.body[:-1])==BASELINE['config_ast_sha256']
    tree=ast.parse((FLASK/'image_processing_pipeline.py').read_text())
    calls=[ast.unparse(n) for n in sorted(ast.walk(tree),key=lambda n:(getattr(n,'lineno',0),getattr(n,'col_offset',0)))
           if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and isinstance(n.func.value,ast.Name) and n.func.value.id=='image_processor']
    assert calls==BASELINE['scientific_calls']
    source=(FLASK/'views.py').read_text()
    native=source[source.index('class ModernAdminImageProcessingView'):source.index('class ModernAdminImageCircleHelperView')]
    assert 'ModernAdminMediaBrowseView, TemplateView' in native
    assert 'ImageProcessingView)' not in native
    assert 'from .image_processing_views import JsonImageProcessingView' in source
    print('FITS preview parity: original defaults, 144-field parser and 46 scientific calls retained; native view independent: PASS')

if __name__=='__main__':run()
