#!/usr/bin/env python3
"""Storage threshold hysteresis, recent-image retention and honest estimates."""
from datetime import datetime, timedelta
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from indi_allsky.storage_pressure import GIB, StoragePressureOptions, retention_estimate


def run():
    options = StoragePressureOptions.from_config({})
    assert options.enabled and options.keep_days == 3
    assert options.needs_cleanup(5*GIB-1) and not options.needs_cleanup(5*GIB)
    assert options.target_free_gib == 8
    assert not StoragePressureOptions(enabled=False).needs_cleanup(0)
    now = datetime(2026, 9, 13, 12)
    assert options.cutoff(now) == now-timedelta(days=3)
    for values in (None, [], {'MIN_FREE_GIB':None}, {'MIN_FREE_GIB':True}, {'ENABLE':'false'}, {'MIN_FREE_GIB':0}, {'TARGET_FREE_GIB':4},
                   {'TARGET_FREE_GIB':float('nan')}, {'KEEP_DAYS':0}, {'KEEP_DAYS':True}):
        try: StoragePressureOptions.from_config({'STORAGE_PRESSURE':values})
        except ValueError: pass
        else: raise AssertionError(values)
    args = dict(free_bytes=9*GIB, stored_image_bytes=12*GIB, observed_bytes=2*GIB,
                observed_seconds=86400, samples=100, options=options)
    result = retention_estimate(**args)
    assert result['seconds_to_threshold'] == 2*86400
    assert result['retained_seconds'] == 8*86400
    for override in ({'observed_bytes':0}, {'samples':1}, {'observed_seconds':300}, {'observed_bytes':float('nan')}, {'free_bytes':-1}):
        result = retention_estimate(**dict(args, **override))
        assert result['status'] == 'insufficient_data' and result['retained_seconds'] is None
    assert retention_estimate(**dict(args, free_bytes=2*GIB))['seconds_to_threshold'] == 0
    from types import SimpleNamespace
    from indi_allsky.storage_pressure import reclaim_old_images
    items = [SimpleNamespace(created=now-timedelta(days=n)) for n in (5,4,3,2)]
    deleted = []
    space = [4*GIB]
    def delete(item):
        deleted.append(item)
        space[0] += 2*GIB
    result = reclaim_old_images(options=options, now=now, free_bytes=lambda:space[0],
                                candidates=lambda cutoff:iter(items), delete=delete)
    assert result['status'] == 'recovered' and deleted == items[:2]
    deleted.clear();space[0] = 4*GIB
    result = reclaim_old_images(options=options, now=now, free_bytes=lambda:space[0],
                                candidates=lambda cutoff:iter(items[2:]), delete=delete)
    assert result['status'] == 'insufficient_old_images' and not deleted
    result = reclaim_old_images(options=options, now=now, free_bytes=lambda:space[0],
                                candidates=lambda cutoff:iter(items), delete=delete, max_files=1)
    assert result['status'] == 'more_work' and result['deleted'] == 1
    # A bounded batch may cross 5 GiB before reaching 8 GiB. Continue the same
    # recovery, but never initiate an unrelated cleanup above the trigger.
    space[0] = 6*GIB
    result = reclaim_old_images(options=options, now=now, free_bytes=lambda:space[0],
                                candidates=lambda cutoff:iter(items), delete=delete)
    assert result['status'] == 'not_needed'
    result = reclaim_old_images(options=options, now=now, free_bytes=lambda:space[0],
                                candidates=lambda cutoff:iter(items), delete=delete, continuing=True)
    assert result['status'] == 'recovered' and result['deleted'] == 1
    print('Storage pressure policy and observed retention estimates PASS')


if __name__ == '__main__':
    run()
