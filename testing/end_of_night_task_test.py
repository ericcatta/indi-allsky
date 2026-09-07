#!/usr/bin/env python3
"""Exercise the actual worker method's terminal gates without loading drivers."""
import ast
import logging
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock


def worker_method():
    source=(Path(__file__).resolve().parents[1]/'indi_allsky/video.py').read_text()
    method=next(n for n in ast.walk(ast.parse(source)) if isinstance(n,ast.FunctionDef) and n.name=='uploadAllskyEndOfNight')
    model=Mock();model.id=1;model.query.filter.return_value.one.return_value=SimpleNamespace(id=2)
    namespace={'IndiAllSkyDbCameraTable':model,'logger':logging.getLogger('test')}
    exec(compile(ast.fix_missing_locations(ast.Module(body=[method],type_ignores=[])),'video.py','exec'),namespace)
    return namespace['uploadAllskyEndOfNight']


def run():
    method=worker_method()
    for night,config,success,message in (
        (False,{},True,'daytime request'),
        (True,{},True,'disabled in configuration'),
        (True,{'FILETRANSFER':{'UPLOAD_ENDOFNIGHT':True}},False,'folder not configured'),
    ):
        worker=SimpleNamespace(config=config);task=Mock()
        method(worker,task,night=night,camera_id=2)
        task.setRunning.assert_called_once_with()
        expected=task.setSuccess if success else task.setFailed
        expected.assert_called_once();assert message in expected.call_args.args[0]
        (task.setFailed if success else task.setSuccess).assert_not_called()
    print('EndOfNight worker gates: daytime and disabled are terminal skips, missing destination remains failure: PASS')

if __name__=='__main__':run()
