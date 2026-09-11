#!/usr/bin/env python3
"""Offline parity for the original Full Config read-form expressions."""
import ast
import copy
import hashlib
import importlib.util
from pathlib import Path
import sys
from types import SimpleNamespace

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from indi_allsky.modern_admin_full_config_form import build_full_config_form_defaults
FIXTURE=ROOT/'testing/fixtures/full_config_form_before_hybrid.py'


class TracedConfig(dict):
    def __init__(self,values,trace,path=()):
        super().__init__(values);self.trace=trace;self.path=path
    def get(self,key,default=None):
        self.trace.append(self.path+(key,))
        value=super().get(key,default)
        return TracedConfig(value,self.trace,self.path+(key,)) if isinstance(value,dict) else value


def run():
    assert hashlib.sha256(FIXTURE.read_bytes()).hexdigest()=='b27ed1185dce972fa5e1bc629d2cbdf954db58bd03cf2dd67871925b10dac349'
    spec=importlib.util.spec_from_file_location('form_baseline',FIXTURE)
    baseline=importlib.util.module_from_spec(spec);spec.loader.exec_module(baseline)
    old=lambda config:baseline.legacy_form_defaults(SimpleNamespace(indi_allsky_config=config))
    def execute(fn,payload):
        trace=[];config=TracedConfig(copy.deepcopy(payload),trace);before=copy.deepcopy(dict(config))
        try:result=('ok',fn(config))
        except Exception as error:result=('error',type(error),error.args)
        assert dict(config)==before,'Input configuration mutated'
        return result,trace
    checks=0
    def compare(payload):
        nonlocal checks
        assert execute(old,payload)==execute(build_full_config_form_defaults,payload)
        checks+=1
    compare({})
    defaults=build_full_config_form_defaults({})
    assert len(defaults)==684
    assert defaults==old({})
    assert list(defaults)==list(old({})), 'Form field order changed'
    assert defaults is not build_full_config_form_defaults({})
    tree=ast.parse(FIXTURE.read_text())
    def config_path(node):
        if isinstance(node,ast.Attribute) and isinstance(node.value,ast.Name) and node.value.id=='self' and node.attr=='indi_allsky_config':return ()
        if isinstance(node,ast.Call) and isinstance(node.func,ast.Attribute) and node.func.attr=='get' and node.args and isinstance(node.args[0],ast.Constant):
            parent=config_path(node.func.value)
            if parent is not None:return parent+(node.args[0].value,)
        return None
    paths={path for node in ast.walk(tree) if (path:=config_path(node))}
    for path in sorted(paths):
        for value in (None,False,True,0,1,1.75,'3.25','invalid',[],{}):
            payload={};container=payload
            for key in path[:-1]:container=container.setdefault(key,{})
            container[path[-1]]=value
            compare(payload)
    # Explicit values exercise aliases, stringification and rounding together.
    populated={}
    for path in sorted(paths,key=len,reverse=True):
        container=populated
        for key in path[:-1]:container=container.setdefault(key,{})
        container.setdefault(path[-1],1)
    compare(populated)
    view_tree=ast.parse((ROOT/'indi_allsky/flask/settings_form_view.py').read_text())
    view=next(n for n in view_tree.body if isinstance(n,ast.ClassDef) and n.name=='HybridSettingsFormView')
    method=next(n for n in view.body if isinstance(n,ast.FunctionDef) and n.name=='get_context')
    assignment=next(n for n in method.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='form_data' for t in n.targets))
    assert ast.unparse(assignment.value)=='build_full_config_form_defaults(self.indi_allsky_config)'
    module_tree=ast.parse((ROOT/'indi_allsky/modern_admin_full_config_form.py').read_text())
    assert [ast.unparse(n) for n in ast.walk(module_tree) if isinstance(n,(ast.Import,ast.ImportFrom))]==['import json']
    print('Full Config read form: 684 fields;',checks,'parity cases; defaults, order, exceptions, access order and input preservation: PASS')


def test_display_and_encoded_fields():
    from indi_allsky.modern_admin_full_config_form import apply_full_config_form_display_fields, apply_full_config_form_encoded_fields
    fixture=ROOT/'testing/fixtures/full_config_form_details_before_hybrid.py'
    assert hashlib.sha256(fixture.read_bytes()).hexdigest()=='3097c0740730a77356dd578ef183d5dda5735fd23d42ccf3f926bdd037736ce8'
    spec=importlib.util.spec_from_file_location('details_baseline',fixture)
    baseline=importlib.util.module_from_spec(spec);spec.loader.exec_module(baseline)
    pairs=[(baseline.legacy_apply_full_config_form_display_fields,apply_full_config_form_display_fields),
           (baseline.legacy_apply_full_config_form_encoded_fields,apply_full_config_form_encoded_fields)]
    cases=[{}, {'ADU_ROI':[1,2,3,4],'SQM_ROI':[5,6,7,8],'IMAGE_CROP_ROI':[9,10,11,12],
                'YOUTUBE':{'TAGS':['first','second']},'FITSHEADERS':[['observer','Example'],['site','Test']] }]
    for key in ('ADU_ROI','SQM_ROI','IMAGE_CROP_ROI','FITSHEADERS','INDI_CONFIG_DEFAULTS','INDI_CONFIG_DAY'):
        for value in (None,True,False,1,1.25,'abcd',[],[1],[1,2,3,4],{}, {0:[1,2]},set([1])):
            cases.append({key:value})
    for section,field in [('TEXT_PROPERTIES','FONT_COLOR'),('CARDINAL_DIRS','FONT_COLOR'),
                          ('ORB_PROPERTIES','SUN_COLOR'),('ORB_PROPERTIES','MOON_COLOR'),('IMAGE_BORDER','COLOR'),
                          *[('LIGHTGRAPH_OVERLAY',key) for key in ('DAY_COLOR','DUSK_COLOR','NIGHT_COLOR','MOONMODE_COLOR','HOUR_COLOR','BORDER_COLOR','NOW_COLOR','FONT_COLOR')],
                          ('YOUTUBE','TAGS'),('FILETRANSFER','LIBCURL_OPTIONS')]:
        for value in (None,False,4,'abc',[],[1,'2',3],{},set([1])):cases.append({section:{field:value}})
        cases.append({section:None})
    cases.extend({'FITSHEADERS':value} for value in ([['key']], [['key','value'],[]], [[],['other']], [['x',None]]*6))
    for payload in cases:
        for old,new in pairs:
            outcomes=[]
            for fn,legacy in ((old,True),(new,False)):
                trace=[];config=TracedConfig(copy.deepcopy(payload),trace)
                foreign={'keep':['value']};data={'foreign':foreign,'ADU_ROI_X1':99}
                try:
                    returned=fn(SimpleNamespace(indi_allsky_config=config) if legacy else config,data)
                    assert returned is data
                    outcome=('ok',)
                except Exception as error:outcome=('error',type(error),error.args)
                assert data['foreign'] is foreign
                assert dict(config)==payload
                outcomes.append((outcome,data,trace))
            assert outcomes[0]==outcomes[1],payload
    view=next(n for n in ast.parse((ROOT/'indi_allsky/flask/settings_form_view.py').read_text()).body if isinstance(n,ast.ClassDef) and n.name=='HybridSettingsFormView')
    method = next(n for n in view.body if isinstance(n, ast.FunctionDef))
    # Frozen caad7bb2 ConfigView method, with only its class name normalized.
    assert hashlib.sha256(ast.dump(method, include_attributes=False).encode()).hexdigest() == '94d03b1a04c133a4e89f32ff8a466c20f69aa7ac04276d6cd02e129346029963'
    imports = [n.module for n in ast.walk(ast.parse((ROOT/'indi_allsky/flask/settings_form_view.py').read_text())) if isinstance(n, ast.ImportFrom)]
    assert 'views' not in imports and 'classic_views' not in imports
    shared = ast.parse((ROOT/'indi_allsky/flask/views.py').read_text())
    assert not any(isinstance(n, ast.ClassDef) and n.name == 'ConfigView' for n in shared.body)
    inventory = next(n for n in shared.body if isinstance(n, ast.ClassDef) and n.name == 'ModernAdminSettingsInventoryView')
    assert [ast.unparse(n) for n in inventory.bases] == ['ModernAdminContextMixin', 'HybridSettingsFormView']
    classic = ast.parse((ROOT/'indi_allsky/flask/classic_views.py').read_text())
    compatibility = next(n for n in classic.body if isinstance(n, ast.ClassDef) and n.name == 'ConfigView')
    assert [ast.unparse(n) for n in compatibility.bases] == ['HybridSettingsFormView']
    text=ast.unparse(view)
    assert text.index('build_full_config_form_defaults(')<text.index('apply_full_config_form_display_fields(')<text.index("url_for('indi_allsky.youtube_oauth2callback_view'")<text.index('apply_full_config_form_encoded_fields(')<text.index('psutil.net_if_addrs(')
    assert 'ADU_ROI_X1' not in text and 'FITSHEADERS__0__KEY' not in text
    print('Read-form display/encoding:',len(cases)*2,'parity cases; partial mutations, exceptions, identity and adapter order: PASS')


if __name__=='__main__':
    run()
    test_display_and_encoded_fields()
