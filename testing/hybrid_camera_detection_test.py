#!/usr/bin/env python3
"""Device capabilities, never USB hints or names, determine camera eligibility."""
import ast
from collections import OrderedDict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def run():
    tree = ast.parse((ROOT / 'indi_allsky/flask/views.py').read_text())
    view = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == 'ModernAdminIndiCameraDetectView')
    method = next(n for n in view.body if isinstance(n, ast.FunctionDef) and n.name == 'parse_indi_getprop_devices')
    annotation = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'annotate_modern_admin_detected_cameras')
    namespace = dict(OrderedDict=OrderedDict, get_modern_admin_configured_camera_matches=lambda: [],
                     normalize_modern_admin_camera_name=lambda value: str(value or '').strip().lower())
    exec(compile(ast.Module(body=[method, annotation], type_ignores=[]), '<actual detection functions>', 'exec'), namespace)
    parse = lambda text: namespace['parse_indi_getprop_devices'](None, text, driver_hint='indi_asi_ccd')
    rows = parse('''Telescope Simulator.DRIVER_INFO.DRIVER_EXEC=indi_simulator_telescope
Telescope Simulator.DRIVER_INFO.DRIVER_INTERFACE=5
ZWO CCD ASI678MC.DRIVER_INFO.DRIVER_EXEC=indi_asi_ccd
ZWO CCD ASI678MC.DRIVER_INFO.DRIVER_INTERFACE=6
ZWO CCD ASI678MC.CCD_EXPOSURE.CCD_EXPOSURE_VALUE=0
Disconnected camera.DRIVER_INFO.DRIVER_INTERFACE=2
ZWO ASI focuser.DRIVER_INFO.DRIVER_INTERFACE=8
Unknown.DRIVER_INFO.DRIVER_INTERFACE=invalid
Legacy.camera.CCD_EXPOSURE.CCD_EXPOSURE_VALUE=0
# ignored.CCD_INFO.VALUE=1
bad=1
''')
    by_name = {row['name']: row for row in rows}
    assert len(rows) == 6
    for name in ('ZWO CCD ASI678MC', 'Disconnected camera', 'Legacy.camera'):
        assert by_name[name]['selectable'] and by_name[name]['candidate']
    for name in ('Telescope Simulator', 'ZWO ASI focuser', 'Unknown'):
        assert not by_name[name]['selectable'] and not by_name[name]['candidate']
    assert by_name['Telescope Simulator']['driver'] == 'indi_simulator_telescope'
    assert by_name['ZWO ASI focuser']['driver'] == ''
    assert by_name['Legacy.camera']['device_id'] == 'indi:indi_asi_ccd:Legacy.camera'
    assert [r['candidate'] for r in rows] == [True, True, True, False, False, False]
    # An explicit non-camera interface wins over camera-like names/properties.
    assert not parse('ASI.CCD_FRAME.X=0\nASI.DRIVER_INFO.DRIVER_INTERFACE=4')[0]['selectable']
    assert parse('Other.DRIVER_INFO.DRIVER_EXEC=indi_gphoto_ccd\nOther.CCD_INFO.CCD_MAX_X=100')[0]['driver'] == 'indi_gphoto_ccd'
    many = '\n'.join('Device.PROP.VALUE%d=x' % i for i in range(20)) + '\nDevice.DRIVER_INFO.DRIVER_INTERFACE=2'
    assert len(parse(many)[0]['properties']) == 8 and parse(many)[0]['selectable']
    annotated = namespace['annotate_modern_admin_detected_cameras'](rows, {}, None)
    telescope = next(r for r in annotated if r['name'] == 'Telescope Simulator')
    assert telescope['status'] == 'Not a camera' and telescope['action_label'] == '' and not telescope['selectable']
    assert next(r for r in annotated if r['name'] == 'ZWO CCD ASI678MC')['action_label'] == 'Add camera'
    print('INDI discovery: capabilities, disconnected/legacy CCD, real drivers, misleading names, bounded preview and annotation PASS')

if __name__ == '__main__':
    run()
