#!/usr/bin/env python3
"""Exercise report completion/failure with real child processes and temp files."""
import contextlib
import io
import json
from pathlib import Path
import sys
import tempfile
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent))
import run_hybrid_regression as runner


def run():
    for scenario in ('passed', 'failed', 'source_changed', 'interrupted'):
        with tempfile.TemporaryDirectory() as folder:
            base = Path(folder)
            root = base / 'source'
            (root / 'indi_allsky').mkdir(parents=True)
            (root / 'testing').mkdir()
            source = root / 'indi_allsky/module.py'
            source.write_text('value = 1\n')
            command = 'print("child ran")'
            if scenario == 'failed':
                command += '; raise SystemExit(7)'
            elif scenario == 'source_changed':
                command += '; from pathlib import Path; Path("indi_allsky/module.py").write_text("value = 2")'
            cases = [{'case': 'child', 'command': [sys.executable, '-c', command]}]
            argv = ['runner', '--root', str(root), '--output', str(base / 'results')]
            with patch.object(sys, 'argv', argv), patch.object(runner, 'discover', return_value=cases), contextlib.redirect_stdout(io.StringIO()):
                if scenario == 'interrupted':
                    with patch.object(runner.subprocess, 'run', side_effect=KeyboardInterrupt):
                        code = runner.main()
                else:
                    code = runner.main()
            report = json.loads((base / 'results/results.json').read_text())
            assert report['status'] == scenario, report
            assert (code == 0) == (scenario == 'passed')
            assert report['planned'] == cases
            if scenario != 'interrupted':
                assert len(report['results']) == 1
                assert 'child ran' in Path(report['results'][0]['log']).read_text()
                assert report['results'][0]['exit_code'] == (7 if scenario == 'failed' else 0)
            # A repeated invocation cannot replace prior evidence.
            saved = (base / 'results/results.json').read_bytes()
            with patch.object(sys, 'argv', argv), patch.object(runner, 'discover', return_value=cases):
                try:
                    runner.main()
                except FileExistsError:
                    pass
                else:
                    raise AssertionError('Existing evidence overwritten')
            assert (base / 'results/results.json').read_bytes() == saved
    print('Hybrid regression runner checks passed')


if __name__ == '__main__':
    run()
