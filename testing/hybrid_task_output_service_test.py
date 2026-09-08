#!/usr/bin/env python3
"""Recorded outputs cannot escape the task camera, action or media root."""
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from indi_allsky.modern_admin_task_outputs import ModernAdminTaskOutputService


def run():
    with TemporaryDirectory() as directory:
        root = Path(directory)
        calls = []
        record = SimpleNamespace(id=7, camera_id=2, success=True)
        def lookup(*args):
            calls.append(args)
            return record
        service = ModernAdminTaskOutputService(root, lookup, lambda **kw: kw)
        task = SimpleNamespace(data={'action': 'generateVideo', 'kwargs': {'camera_id': 2},
                                     'profile_id': 'camera-two'}, state='SUCCESS',
                               result='Generated timelapse: '+str(root/'clip.mp4'))
        links = service.build_links(task)
        assert links == [{'label': 'Timelapse', 'url': {
            'kind': 'video', 'id': 7, 'camera_id': 2, 'profile_id': 'camera-two'}}]
        assert 'clip.mp4' in calls[-1][3]
        # A lookup adapter must not be able to return another camera or a failed asset.
        record.camera_id = 1
        assert service.build_links(task) == []
        record.camera_id = 2; record.success = False
        assert service.build_links(task) == []
        record.success = True
        for filename in ('../outside.mp4', '/outside.mp4', '\x00.mp4'):
            task.result = 'Generated timelapse: '+filename
            before = len(calls)
            assert service.build_links(task) == [] and len(calls) == before
        task.result = 'Generated timelapse: clip.mp4'
        task.state = 'FAILED'
        assert service.build_links(task) == []
        task.state = 'SUCCESS'
        task.data['generation_outcome'] = {'camera_id': 1, 'outputs': []}
        assert service.build_links(task) == [], 'Malformed receipt must not fall back to task text'
        task.data['action'] = 'generateKeogramStarTrails'
        row = {'kind': 'keogram', 'camera_id': 2, 'record_id': 7, 'status': 'generated'}
        task.data['generation_outcome'] = {'camera_id': 2, 'outputs': [row, dict(row)]}
        assert len(service.build_links(task)) == 1
        for change in ({'camera_id': 1}, {'record_id': True}, {'record_id': -1},
                       {'kind': 'video'}, {'status': 'skipped'}, {'status': 'failed'}):
            task.data['generation_outcome']['outputs'] = [dict(row, **change)]
            assert service.build_links(task) == []
        for data in (None, [], {'action': []}, {'action': 'generateVideo', 'camera_id': True}):
            task.data = data
            assert service.build_links(task) == []
    print('Task output resolution: camera/action isolation, path containment, receipts and legacy results: PASS')


if __name__ == '__main__':
    run()
