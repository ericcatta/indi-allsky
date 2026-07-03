#!/usr/bin/env python3

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
CAPTURE_SOURCE = REPO_ROOT / 'indi_allsky' / 'capture.py'


def _capture_source():
    return CAPTURE_SOURCE.read_text()


def _method_source(source, method_name, next_method_name):
    method_start = source.index('    def {0:s}'.format(method_name))
    method_end = source.index('    def {0:s}'.format(next_method_name), method_start)
    return source[method_start:method_end]


def test_exposure_timeout_plan_is_profile_config_and_exposure_aware():
    source = _capture_source()
    method = _method_source(source, '_exposure_timeout_plan', '_next_exposure_timeout_check')

    assert "self.config.get('CCD_EXPOSURE_TIMEOUT', 330)" in method
    assert 'requested_exposure + 30.0' in method
    assert 'max(configured_timeout, exposure_floor)' in method
    assert "'floor_applied'" in method


def test_timeout_check_does_not_wait_another_full_timeout_while_exposure_is_busy():
    source = _capture_source()
    method = _method_source(source, '_next_exposure_timeout_check', '_log_exposure_timeout_plan')

    assert 'if not waiting_for_frame:' in method
    assert "return now_time + timeout_plan['effective']" in method
    assert 'remaining_s = timeout_plan' in method
    assert 'min(max(remaining_s, 1.0), 30.0)' in method


def test_capture_loop_aligns_timeout_check_to_exposure_start():
    source = _capture_source()

    start_marker = 'if now_time >= next_frame_time:'
    start_index = source.index(start_marker)
    start_branch = source[start_index:source.index("logger.info('Total time since last exposure", start_index)]

    assert 'exposure_timeout_plan = self._exposure_timeout_plan(self.exposure_av[constants.EXPOSURE_NEXT])' in start_branch
    assert 'next_check_exposure_state = frame_start_time + exposure_timeout_plan' in start_branch
    assert "self._log_exposure_timeout_plan(exposure_timeout_plan, 'start')" in start_branch


def test_capture_loop_aborts_only_while_waiting_for_frame_after_effective_timeout():
    source = _capture_source()
    check_index = source.index('if next_check_exposure_state < loop_start_time:')
    check_branch = source[check_index:source.index('# Loop to run for 11 seconds', check_index)]

    assert 'waiting_for_frame' in check_branch
    assert "camera_last_ready_s >= exposure_timeout_plan['effective']" in check_branch
    assert "self._log_exposure_timeout_plan(exposure_timeout_plan, 'abort')" in check_branch
    assert 'self.indiclient.abortCcdExposure()' in check_branch


if __name__ == '__main__':
    test_exposure_timeout_plan_is_profile_config_and_exposure_aware()
    test_timeout_check_does_not_wait_another_full_timeout_while_exposure_is_busy()
    test_capture_loop_aligns_timeout_check_to_exposure_start()
    test_capture_loop_aborts_only_while_waiting_for_frame_after_effective_timeout()
    print('Capture timeout policy tests passed')
