#!/usr/bin/env python3
"""Verify subsecond normalization with the installed psutil implementation."""
from pathlib import Path
import sys
from unittest.mock import patch

import psutil

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from indi_allsky.modern_admin_system_tools import ModernAdminCpuUsageProvider


def run():
    sample_type = type(psutil.cpu_times())
    before = sample_type(*([0.0] * len(sample_type._fields)))
    provider = ModernAdminCpuUsageProvider(psutil.cpu_percent)
    cases = [({'user': .1, 'idle': .3}, 25.0),
             ({'idle': .4}, 0.0),
             ({'system': .4}, 100.0),
             ({'iowait': .1, 'idle': .3}, 0.0)]
    for changes, expected in cases:
        after = before._replace(**changes)
        # Real psutil calculation; only kernel counters and waiting are replaced.
        with patch.object(psutil, 'cpu_times', side_effect=[before, after]) as read:
            with patch.object(psutil.time, 'sleep') as wait:
                assert provider.read() == expected
                assert read.call_count == 2
                wait.assert_called_once_with(0.1)
    print('Hybrid CPU subsecond sampling: PASS (psutil %s)' % psutil.__version__)


if __name__ == '__main__':
    run()
