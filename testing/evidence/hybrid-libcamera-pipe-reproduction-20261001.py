import ast, json, subprocess, sys, tempfile
from pathlib import Path
from types import SimpleNamespace
source = Path('indi_allsky/camera/libcamera.py')
tree = ast.parse(source.read_text())
block = next(n for n in ast.walk(tree) if isinstance(n, ast.If) and isinstance(n.test, ast.Name) and n.test.id == 'images_only' and any(isinstance(v, ast.Attribute) and v.attr == 'TemporaryFile' for v in ast.walk(n)))
program = compile(ast.Module(body=[block], type_ignores=[]), str(source), 'exec')
results=[]
for mode in (False, True):
    client=SimpleNamespace(libcamera_output_f=None)
    ns={'self': client, 'images_only':mode, 'tempfile':tempfile, 'subprocess':subprocess}
    exec(program, ns)
    child=subprocess.Popen([sys.executable,'-c','import sys; sys.stdout.buffer.write(b"x" * (4 * 1024 * 1024)); sys.stdout.flush()'], stdout=ns['libcamera_stdout'], stderr=subprocess.STDOUT)
    try:
        child.wait(timeout=2)
        result={'images_only':mode,'completed':True,'returncode':child.returncode}
    except subprocess.TimeoutExpired:
        result={'images_only':mode,'completed':False,'reason':'Unread output pipe prevents child completion'}
    finally:
        if child.poll() is None:
            child.kill()
        child.wait()
        if child.stdout:
            child.stdout.close()
        if client.libcamera_output_f:
            client.libcamera_output_f.close()
    results.append(result)
print(json.dumps(results,indent=2))
assert results[0]['completed'] is False and results[1]['completed'] is True
