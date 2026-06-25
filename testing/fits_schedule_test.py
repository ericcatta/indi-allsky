import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from indi_allsky.fits_schedule import FitsSchedule


def test_first_fits_is_due_immediately_for_each_profile_camera():
    schedule = FitsSchedule()
    asi_key = schedule.key('asi678mc', 2)
    imx_key = schedule.key('imx708-wide', 1)

    assert schedule.is_due(asi_key, now=1000.0)
    assert schedule.is_due(imx_key, now=1000.0)


def test_two_profile_camera_keys_do_not_share_timer():
    schedule = FitsSchedule()
    asi_key = schedule.key('asi678mc', 2)
    imx_key = schedule.key('imx708-wide', 1)

    schedule.mark_written(asi_key, period=60, now=1000.0)

    assert not schedule.is_due(asi_key, now=1010.0)
    assert schedule.is_due(imx_key, now=1010.0)


def test_same_profile_camera_is_blocked_until_period_elapsed():
    schedule = FitsSchedule()
    key = schedule.key('asi678mc', 2)

    schedule.mark_written(key, period=60, now=1000.0)

    assert not schedule.is_due(key, now=1059.9)
    assert schedule.is_due(key, now=1060.0)


def test_zero_period_allows_every_frame():
    schedule = FitsSchedule()
    key = schedule.key('asi678mc', 2)

    schedule.mark_written(key, period=0, now=1000.0)

    assert schedule.is_due(key, now=1000.0)
    assert schedule.is_due(key, now=1000.1)


def test_invalid_period_falls_back_to_every_frame():
    schedule = FitsSchedule()
    key = schedule.key('asi678mc', 2)

    schedule.mark_written(key, period='bad-value', now=1000.0)

    assert schedule.is_due(key, now=1000.0)


if __name__ == '__main__':
    test_first_fits_is_due_immediately_for_each_profile_camera()
    test_two_profile_camera_keys_do_not_share_timer()
    test_same_profile_camera_is_blocked_until_period_elapsed()
    test_zero_period_allows_every_frame()
    test_invalid_period_falls_back_to_every_frame()
    print('fits schedule tests OK')
