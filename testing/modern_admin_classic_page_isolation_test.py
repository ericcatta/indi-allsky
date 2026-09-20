#!/usr/bin/env python3
"""Classic-only page definitions must not be loaded through shared views."""
import ast
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
# Complete class ASTs captured before isolation at f85027a2.
FINGERPRINTS = {'RealtimeKeogramView': 'd92f8df33ad80cf30c79c2633f9857b1ebf0782e936a295462d214810705ec64', 'MaskView': '5c8f77d0250e5e542d7b5526caf3be7194731f96b4e47acb049923d78ec73be5', 'ImageLagView': '9388708d20e33db70c505914029f59921904cad83d575ebbd678fcf1476e1ba3', 'RollingAduView': '92f2229bf915f3c3fe79a6d94b7b268a5d0199221f40ebb64a7e1f78c2e80798', 'ImageLoopImgView': '71dfa7ef4f3eb4b4d511da93c319961d99fd3fa87c78b93bf009a23ac12aec32', 'TimelapseGeneratorView': '533960839d051760489209283a77f2e686490b813ae325b613333a6bd85c8a1e', 'FocusView': 'a663627f55e82e71bdcf00156a68983cdcfd37490188b4bdb4836226b3c1bd9a', 'ManualGpioView': '75cf66edb983492fe06dc9ee73c027569694f60be1f69c2c5becf06f17a37342', 'ImageProcessingView': '1cbc9b4b551ba1c09db201322df6799ec8eee417b1a03eabdf7cc3469b6ba461', 'CameraLensView': '6a2ca10488d3e6f6850182a7077b0dc1b86a5eff5f2ae1f84c9b5ddab7a5de51', 'CameraSimulatorView': '223c20334c2b26be9e93e5e0da24f8683ad3643bd015bb37b568dccf6a5eb0d8', 'FileSpaceUsageView': '15995f6fd4aa24155338f277528df2ece0cceb3bfc6d3ef53eabab24d06b0127', 'NetworkManagerView': '689746138231cb1cbac84706db7d085ec4c4f83b9a7c575fb1e7096ad59cfbf6', 'DriveManagerView': '19a108f27bcf23031d60f981afeeb50cac7855a329570e71ba3f89724d763242', 'ImageCircleHelperView': 'a730dd96b2972ae3d7b74acd7385f48cc22cf50b9ff4dbb7ac0e4cbc3b528630'}


def run():
    shared = ast.parse((ROOT/'indi_allsky/flask/views.py').read_text())
    assert not (ROOT/'indi_allsky/flask/classic_views.py').exists()
    classes = json.loads((ROOT/'testing/classic_frontend_contract.json').read_text())['classes']
    for name, fingerprint in FINGERPRINTS.items():
        assert classes[name] == fingerprint, name
    assert not any(isinstance(n, ast.Name) and n.id in classes
                   or isinstance(n, ast.ClassDef) and n.name in classes
                   or isinstance(n, ast.alias) and n.name in classes
                   for n in ast.walk(shared))
    for path in (ROOT/'indi_allsky/flask').glob('*.py'):
        assert not any(isinstance(n, ast.ImportFrom) and n.module == 'classic_views'
                       for n in ast.walk(ast.parse(path.read_text()))), path
    print('Classic frontend absent: retired fingerprints retained and view names cannot reappear in shared handlers PASS')


if __name__ == '__main__':
    run()
