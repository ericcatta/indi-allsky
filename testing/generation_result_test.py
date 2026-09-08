#!/usr/bin/env python3
"""Task receipts distinguish generated, skipped, disabled and failed outputs."""
from pathlib import Path
import ast
import hashlib
import sys
import tempfile
from types import SimpleNamespace
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from indi_allsky.generation_result import finish_keogram_task


class Task:
    def __init__(self):self.data={'action':'generateKeogramStarTrails','kwargs':{'camera_id':2},'profile_id':'p2'}
    def setSuccess(self,message):self.state='SUCCESS';self.result=message
    def setFailed(self,message):self.state='FAILED';self.result=message


def run():
    # Captured from 3b172949: only replace the final generic task receipt.
    source=(Path(__file__).resolve().parents[1]/'indi_allsky/video.py').read_text()
    method=next(n for n in ast.walk(ast.parse(source)) if isinstance(n,ast.FunctionDef) and n.name=='generateKeogramStarTrails')
    assert isinstance(method.body[-2],ast.ImportFrom) and method.body[-2].module=='generation_result'
    assert isinstance(method.body[-1],ast.Expr) and method.body[-1].value.func.id=='finish_keogram_task'
    method.body=method.body[:-2]
    # Normalize only the verified no-eligible-frame gate, retaining the original
    # fingerprint for all scientific selection, processing and upload logic.
    additions=ast.parse("startrail_video_entry = None\nif startrail_entry is not None:\n    startrail_entry.frames = stg.trail_count").body
    for addition in additions:
        matches=[node for node in method.body if ast.dump(node,include_attributes=False)==ast.dump(addition,include_attributes=False)]
        assert len(matches)==1
        method.body.remove(matches[0])
    gates=0
    for node in method.body:
        if isinstance(node,ast.If) and isinstance(node.test,ast.BoolOp):
            condition=node.test.values[-1]
            if ast.dump(condition,include_attributes=False)==ast.dump(ast.parse('stg.trail_count > 0',mode='eval').body,include_attributes=False):
                assert isinstance(node.test.op,ast.And)
                node.test.values.pop()
                if len(node.test.values)==1:node.test=node.test.values[0]
                gates+=1
    assert gates==2
    assert hashlib.sha256(ast.dump(method,include_attributes=False).encode()).hexdigest()=='ee2e28ea1bb9fd38ccb542adcf939bfcb9572939b1179e60cf3955eece0878ba'
    with tempfile.TemporaryDirectory() as folder:
        paths=[Path(folder)/str(i) for i in range(3)]
        for path in paths:path.write_bytes(b'generated fixture')
        def finish(**kwargs):
            entries=[SimpleNamespace(id=i+1,success=True) for i in range(3)]
            task=Task();args=dict(camera_id=2,night=True,keogram=(entries[0],paths[0]),startrail=(entries[1],paths[1]),video=(entries[2],paths[2]),frames=300,min_frames=250,video_enabled=True)
            args.update(kwargs);outcome=finish_keogram_task(task,**args)
            assert task.data['profile_id']=='p2' and task.data['kwargs']=={'camera_id':2}
            assert task.data['generation_outcome']==outcome and len(task.result)<=255
            assert all(r['camera_id']==2 for r in outcome['outputs'])
            return task,outcome,entries
        task,outcome,_=finish();assert task.state=='SUCCESS' and outcome['status']=='complete'
        task,outcome,_=finish(frames=59,video=(None,paths[2]));assert task.state=='SUCCESS' and outcome['status']=='partial'
        assert '59/250 eligible frames' in task.result and outcome['outputs'][2]['status']=='skipped'
        task,outcome,_=finish(video_enabled=False,video=(None,paths[2]),frames=0)
        assert outcome['status']=='complete' and outcome['outputs'][2]['status']=='not_requested'
        task,outcome,_=finish(night=False,video=(None,paths[2]),startrail=(None,paths[1]))
        assert outcome['status']=='complete' and 'Startrail' not in task.result
        task,outcome,entries=finish(startrail_frames=0,frames=0)
        assert task.state=='SUCCESS' and outcome['status']=='partial'
        assert outcome['outputs'][1]['reason']=='No eligible frames' and not entries[1].success
        assert 'Startrail: skipped (0/1 eligible frames)' in task.result
        task,outcome,_=finish(startrail_frames=0,frames=0,video_enabled=False)
        assert outcome['status']=='partial' and outcome['outputs'][2]['status']=='not_requested'
        paths[2].write_bytes(b'')
        task,outcome,entries=finish();assert task.state=='FAILED' and not entries[2].success
        assert outcome['outputs'][0]['status']=='generated' and outcome['outputs'][2]['status']=='failed'
        paths[0].unlink();paths[1].unlink()
        task,outcome,_=finish();assert task.state=='FAILED' and outcome['status']=='failed'
        task,outcome,_=finish(night=False,keogram=(None,paths[0]));assert task.state=='FAILED'
        print('Generation receipt: complete/partial/disabled/daytime/failed, actual files, missing/empty output, camera/profile and bounded message: PASS')

if __name__=='__main__':run()
