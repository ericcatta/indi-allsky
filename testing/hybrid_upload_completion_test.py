#!/usr/bin/env python3
"""Upload remains protected until post-transfer metadata and cleanup finish."""
import ast
from pathlib import Path
from types import SimpleNamespace
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from indi_allsky import constants


def run():
    path = Path(__file__).resolve().parents[1]/'indi_allsky/uploader.py'
    tree = ast.parse(path.read_text())
    method = next(n for n in ast.walk(tree) if isinstance(n,ast.FunctionDef) and n.name=='processUpload')
    # Execute the actual complete finalization block, after network transfer.
    first = next(i for i,n in enumerate(method.body) if isinstance(n,ast.If)
                 and ast.unparse(n.test)=='entry and action == constants.TRANSFER_UPLOAD')
    body = method.body[first:]
    successes = [n for n in ast.walk(method) if isinstance(n,ast.Call)
                 and ast.unparse(n.func)=='task.setSuccess']
    assert len(successes)==1 and successes[0].lineno >= body[0].lineno
    code = compile(ast.fix_missing_locations(ast.Module(body=body,type_ignores=[])),str(path),'exec')
    for action in (constants.TRANSFER_UPLOAD, constants.TRANSFER_S3, constants.TRANSFER_SYNC_V1, constants.TRANSFER_YOUTUBE):
        for fail in (False,True):
            events=[]
            task=SimpleNamespace(state='RUNNING')
            def effect(name):
                assert task.state=='RUNNING', (name,events)
                events.append(name)
            def commit():
                effect('commit')
                if fail: raise RuntimeError('synthetic persistence failure')
            def success(message):
                effect('success');task.state='SUCCESS'
            task.setSuccess=success
            entry=SimpleNamespace(uploaded=False,data={})
            worker=SimpleNamespace(_syncapi=lambda *a:effect('sync handoff'),cleanup=lambda *a,**k:effect('cleanup'))
            namespace=dict(entry=entry,task=task,self=worker,action=action,constants=constants,
                           db=SimpleNamespace(session=SimpleNamespace(commit=commit)),s3_key='test-key',
                           metadata={},response={'id':123},local_file_p=Path('/unused-fixture'),remove_local=False)
            try: exec(code,namespace)
            except RuntimeError:
                assert fail and task.state=='RUNNING' and 'success' not in events
            else:
                assert not fail and task.state=='SUCCESS' and events[-2:]==['cleanup','success']
                if action==constants.TRANSFER_S3: assert 'sync handoff' in events
    print('Upload finalization: pending protection through metadata/child handoff/cleanup, no false success on persistence failure PASS')


if __name__=='__main__':run()
