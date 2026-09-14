#!/usr/bin/env python3
"""Rehearse frontend removal in a disposable copy, never in the real checkout.

This proves the listed automatic flows run without Classic files. It does not
replace native browser, hardware acceptance or the final production removal.
"""
import argparse
import json
import os
import time
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


def run(*, all_flows=False, oauth_python=None, report_path=None):
    flows = tuple(sorted(p.name for p in (ROOT / "testing").glob("hybrid_*_flow_test.py"))) if all_flows else FLOWS
    assert flows and set(FLOWS) <= set(flows)
    results = []
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
        # Keep the interpreter's dependency configuration (the OAuth venv also
        # uses user-site dependencies). Application origins are checked above.
        env = {**os.environ, 'PYTHONPATH': str(stage),
               'PYTHONDONTWRITEBYTECODE': '1'}
        print('PHYSICAL REMOVAL', removed, flush=True)
        for flow in flows:
            python = str(oauth_python or sys.executable) if flow == 'hybrid_youtube_flow_test.py' else sys.executable
            started = time.monotonic()
            try:
                result = subprocess.run([python, '-c', bootstrap, str(stage), flow],
                                        cwd=stage, env=env, capture_output=True, text=True, timeout=90)
                code = result.returncode
                if code:
                    print(result.stdout, result.stderr, flush=True)
            except subprocess.TimeoutExpired:
                code = -1
                print('Flow exceeded 90 seconds:', flow, flush=True)
            results.append({'flow': flow, 'exit_code': code, 'seconds': round(time.monotonic()-started, 2)})
            if report_path:
                report_path.write_text(json.dumps({'mode': 'all-flows' if all_flows else 'core',
                    'removed': removed, 'results': results, 'status': 'running'}, indent=2) + '\n')
            print('CLASSIC ABSENT', 'PASS' if code == 0 else 'FAIL', flow, flush=True)
        assert not classic.exists()
    passed = all(result['exit_code'] == 0 for result in results)
    if report_path:
        report_path.write_text(json.dumps({'mode': 'all-flows' if all_flows else 'core',
            'removed': removed, 'results': results, 'status': 'passed' if passed else 'failed',
            'temporary_copy_removed': not stage.exists()}, indent=2) + '\n')
    assert passed, 'Classic-absent integration failures; inspect listed results'
    print('Classic absence rehearsal PASS:', len(results), 'flows; disposable tree removed; original checkout untouched', flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--all-flows', action='store_true', help='Discover every hybrid_*_flow_test.py instead of the twelve core flows')
    parser.add_argument('--oauth-python', type=Path, help='Interpreter with optional Google OAuth dependencies for its integration test')
    parser.add_argument('--report', type=Path, help='Write per-flow outcomes outside the disposable tree')
    args = parser.parse_args()
    run(all_flows=args.all_flows, oauth_python=args.oauth_python, report_path=args.report)
