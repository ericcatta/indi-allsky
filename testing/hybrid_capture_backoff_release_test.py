#!/usr/bin/env python3
"""A drained multi-camera queue releases obsolete delay at a ready camera."""
import ast
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

SOURCE = Path(__file__).resolve().parents[1] / 'indi_allsky/capture.py'


def run():
    tree = ast.parse(SOURCE.read_text())
    release = next(n for n in ast.walk(tree) if isinstance(n, ast.If)
                   and any(isinstance(c, ast.Name) and c.id == 'baseline_frame_time'
                           for c in ast.walk(n))
                   and 'MULTI_CAMERA_CAPTURE_ENABLE' in ast.unparse(n.test))
    container = next(n for n in ast.walk(tree) if hasattr(n, 'body')
                     and isinstance(n.body, list) and release in n.body)
    index = container.body.index(release)
    start = container.body[index + 1]
    assert ast.unparse(start.test) == 'now_time >= next_frame_time'
    # Run the actual scheduling predicate after the actual release branch.
    # The exposure body is represented by one record to avoid camera hardware.
    record = ast.parse('started.append(now_time)').body
    predicate = ast.If(test=start.test, body=record, orelse=[])
    ast.fix_missing_locations(predicate)
    program = compile(ast.Module(body=[release, predicate], type_ignores=[]), str(SOURCE), 'exec')

    def scenario(now, depth, *, multi=True, focus=False, deadline=182.5):
        worker = SimpleNamespace(config={'MULTI_CAMERA_CAPTURE_ENABLE': multi},
                                 focus_mode=focus, add_period_delay=37.5,
                                 image_queue_min=1,
                                 image_q=SimpleNamespace(qsize=lambda: depth))
        state = dict(self=worker, frame_start_time=100.,
                     exposure_period_info={'effective': 45.},
                     next_frame_time=deadline, now_time=now, logger=Mock(), started=[])
        exec(program, state)
        return worker, state

    worker, state = scenario(144, 0)
    assert worker.add_period_delay == 0 and state['next_frame_time'] == 145
    assert state['started'] == []  # Never start before the baseline period.
    worker, state = scenario(145, 1)
    assert state['started'] == [145] and worker.add_period_delay == 0
    worker, state = scenario(160, 0)
    assert state['started'] == [160] and state['next_frame_time'] == 145
    # The actual existing start branch schedules from the new start, so an
    # overdue release does not create a catch-up burst against the old epoch.
    assignments = [n for n in ast.walk(start) if isinstance(n, ast.Assign)
                   and any(isinstance(t, ast.Name) and t.id == 'next_frame_time' for t in n.targets)]
    normal = next(n for n in assignments if 'exposure_period_info' in ast.unparse(n.value))
    state['frame_start_time'] = 160.
    exec(compile(ast.Module(body=[normal], type_ignores=[]), str(SOURCE), 'exec'), state)
    assert state['next_frame_time'] == 205

    for depth in (2, 3, 5):
        worker, state = scenario(160, depth)
        assert worker.add_period_delay == 37.5 and state['next_frame_time'] == 182.5
        assert state['started'] == []
    for options in ({'multi': False}, {'focus': True},
                    {'deadline': 100.},  # SQM explicitly schedules immediately.
                    {'deadline': 190.}):  # A clock-reset deadline stays explicit.
        worker, state = scenario(144, 0, **options)
        assert worker.add_period_delay == 37.5
        assert state['next_frame_time'] == options.get('deadline', 182.5)

    # This release executes only in the camera-ready portion of the real loop.
    before = container.body[:index]
    busy = next(n for n in before if isinstance(n, ast.If)
                and ast.unparse(n.test) == 'not camera_ready')
    assert isinstance(busy.body[-1], ast.Continue)
    print('Capture backoff: drained ready queue, baseline period, retained pressure, SQM/focus isolation and no catch-up burst passed')


if __name__ == '__main__':
    run()
