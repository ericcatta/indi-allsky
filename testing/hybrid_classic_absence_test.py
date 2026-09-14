#!/usr/bin/env python3
"""Rehearse frontend removal in a disposable copy, never in the real checkout.

This proves the listed automatic flows run without Classic files. It does not
replace native browser, hardware acceptance or the final production removal.
"""
import os
from pathlib import Path
import shutil
import subprocess
import sys
from tempfile import TemporaryDirectory
from hybrid_asset_guard import SHARED_FILES

ROOT = Path(__file__).resolve().parents[1]
FLOWS = (
    'hybrid_authenticated_flow_test.py',
    'hybrid_settings_flow_test.py',
    'hybrid_operations_flow_test.py',
    'hybrid_gallery_isolation_flow_test.py',
    'hybrid_generated_media_flow_test.py',
    'hybrid_public_media_flow_test.py',
    'hybrid_camera_management_flow_test.py',
    'hybrid_fits_processing_flow_test.py',
    'hybrid_geometry_flow_test.py',
    'hybrid_queued_maintenance_flow_test.py',
    'hybrid_system_units_flow_test.py',
    'hybrid_astropanel_flow_test.py',
)


def run():
    with TemporaryDirectory(prefix='hybrid-without-classic-') as directory:
        stage = Path(directory)
        ignore = shutil.ignore_patterns('__pycache__', '*.pyc', 'evidence')
        for name in ('indi_allsky', 'testing'):
            shutil.copytree(ROOT / name, stage / name, ignore=ignore)
        flask = stage / 'indi_allsky/flask'
        classic = flask / 'classic_views.py'
        assert classic.is_file(), 'Expected optional frontend module before rehearsal'
        classic.unlink()
        removed = {'modules': 1, 'templates': 0, 'assets': 0}
        for path in (flask / 'templates').rglob('*'):
            if not path.is_file():
                continue
            name = path.relative_to(flask / 'templates').as_posix()
            if name != 'login.html' and not name.startswith(('modern_admin/', 'shared/')):
                path.unlink(); removed['templates'] += 1
        for path in (flask / 'static').rglob('*'):
            if not path.is_file():
                continue
            name = path.relative_to(flask / 'static').as_posix()
            if name not in SHARED_FILES and not name.startswith(('modern_admin/', 'virtualsky/')):
                path.unlink(); removed['assets'] += 1
        assert removed['templates'] > 0 and removed['assets'] > 0
        assert not classic.exists() and not (flask / 'templates/base.html').exists()
        # Every child imports its copied fixtures/package. Prevent an installed
        # or editable source checkout from silently supplying the missing files.
        bootstrap = '''
import runpy,sys
from pathlib import Path
root=Path(sys.argv[1]).resolve()
flow=root/'testing'/sys.argv[2]
sys.path[:0]=[str(root/'testing'),str(root)]
sys.argv=[str(flow)]
runpy.run_path(str(flow),run_name='__main__')
for name,module in list(sys.modules.items()):
    if name=='indi_allsky' or name.startswith('indi_allsky.'):
        filename=getattr(module,'__file__',None)
        if filename:
            assert Path(filename).resolve().is_relative_to(root), name
assert 'indi_allsky.flask.classic_views' not in sys.modules
'''
        env = {**os.environ, 'PYTHONPATH': str(stage), 'PYTHONNOUSERSITE': '1',
               'PYTHONDONTWRITEBYTECODE': '1'}
        print('PHYSICAL REMOVAL', removed, flush=True)
        for flow in FLOWS:
            result = subprocess.run([sys.executable, '-c', bootstrap, str(stage), flow],
                                    cwd=stage, env=env, capture_output=True, text=True, timeout=90)
            if result.returncode:
                print(result.stdout, result.stderr, flush=True)
                raise AssertionError('Classic-absent flow failed: ' + flow)
            print('CLASSIC ABSENT PASS', flow, flush=True)
        assert not classic.exists()
    print('Classic absence rehearsal PASS: disposable tree removed; original checkout untouched', flush=True)


if __name__ == '__main__':
    run()
