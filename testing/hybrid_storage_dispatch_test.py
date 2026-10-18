#!/usr/bin/env python3
"""Cleanup dispatch remains available while the video consumer is busy."""
import ast
import logging
import queue
from pathlib import Path
from queue import Queue
from types import SimpleNamespace, ModuleType
from unittest.mock import patch


def run():
    path=Path(__file__).resolve().parents[1]/'indi_allsky/allsky.py'
    tree=ast.parse(path.read_text())
    wanted={'_queue_video_task','_startStorageWorker','_stopStorageWorker'}
    methods=[n for n in ast.walk(tree) if isinstance(n,ast.FunctionDef) and n.name in wanted]
    class App:
        def app_context(self):
            class Context:
                def __enter__(self): return self
                def __exit__(self,*args): return False
            return Context()
    scope={'__package__':'indi_allsky','logger':logging.getLogger('test'),
        'queue':queue,'app':App()}
    rollbacks=[]
    scope['db']=SimpleNamespace(session=SimpleNamespace(rollback=lambda:rollbacks.append('rollback')))
    exec(compile(ast.fix_missing_locations(ast.Module(body=methods,type_ignores=[])),str(path),'exec'),scope)
    storage=Queue(); video=Queue()
    supervisor=SimpleNamespace(storage_q=storage,video_q=video,storage_worker=None,
        storage_worker_idx=0,storage_error_q=Queue(),config={},upload_q=Queue(),
        night_av=[],binning_av=[],_terminate=False)
    # Video work already pending; cleanup must bypass that queue entirely.
    video.put({'task_id':100})
    scope['_queue_video_task'](supervisor,SimpleNamespace(id=101,data={'action':'storagePressureCleanup'}))
    assert storage.get_nowait()=={'task_id':101}
    assert video.get_nowait()=={'task_id':100} and video.empty()
    events=[]; workers=[]; recoveries=[]
    class Worker:
        def __init__(self,*args):
            assert args[3] is storage
            self.index=args[0]
            self.alive=False
            workers.append(self)
        def is_alive(self): return self.alive
        def start(self): self.alive=True;events.append(('start',self.index))
        def join(self):
            assert storage.get_nowait()=={'stop':True}
            self.alive=False;events.append(('join',self.index))
    module=ModuleType('indi_allsky.storage_worker')
    module.StorageWorker=Worker
    recovery_failures=[RuntimeError('database is locked')]
    def recover():
        recoveries.append('recover')
        if recovery_failures:
            raise recovery_failures.pop()
    module.recover_interrupted_cleanup=recover
    with patch.dict('sys.modules',{'indi_allsky.storage_worker':module}):
        # Starting an already-live worker must not create a second consumer.
        scope['_startStorageWorker'](supervisor)
        scope['_startStorageWorker'](supervisor)
        assert events==[('start',1)] and len(workers)==1

        # An unexpectedly dead consumer is recovered before its replacement.
        workers[-1].alive=False
        scope['_startStorageWorker'](supervisor)
        assert recoveries==['recover']
        assert rollbacks==['rollback']
        assert events==[('start',1)] and len(workers)==1
        assert supervisor.storage_worker is workers[0]
        scope['_startStorageWorker'](supervisor)
        assert recoveries==['recover','recover']
        assert events==[('start',1),('start',2)] and len(workers)==2
        scope['_startStorageWorker'](supervisor)
        assert events==[('start',1),('start',2)] and len(workers)==2

        # A graceful stop queues the sentinel, joins, and permits a clean restart.
        scope['_stopStorageWorker'](supervisor)
        assert events==[('start',1),('start',2),('join',2)]
        scope['_startStorageWorker'](supervisor)
        assert recoveries==['recover','recover','recover']
        assert events==[('start',1),('start',2),('join',2),('start',3)]
        assert len(workers)==3 and supervisor.storage_worker is workers[-1]
        scope['_startStorageWorker'](supervisor)
        assert len(workers)==3
    print('Dedicated storage dispatch and worker lifecycle PASS')


if __name__=='__main__': run()
