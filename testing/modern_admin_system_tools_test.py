#!/usr/bin/env python3

import inspect
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from indi_allsky.modern_admin_system_tools import LOG_DETAIL_DEFAULT_LINES
from indi_allsky.modern_admin_system_tools import LOG_DETAIL_LINE_SIZE
from indi_allsky.modern_admin_system_tools import LOG_DETAIL_MAX_LINES
from indi_allsky.modern_admin_system_tools import ModernAdminLogDisplayPolicy


def test_log_display_policy_preserves_line_limits():
    policy = ModernAdminLogDisplayPolicy()

    assert LOG_DETAIL_DEFAULT_LINES == 200
    assert LOG_DETAIL_MAX_LINES == 500
    assert LOG_DETAIL_LINE_SIZE == 180
    assert policy.normalize_line_limit(None) == 200
    assert policy.normalize_line_limit('not-a-number') == 200
    assert policy.normalize_line_limit(0) == 200
    assert policy.normalize_line_limit(-1) == 200
    assert policy.normalize_line_limit(25) == 25
    assert policy.normalize_line_limit(999) == 500
    assert policy.read_bytes_for_limit(25) == 4500


def test_log_display_policy_preserves_source_rows():
    policy = ModernAdminLogDisplayPolicy()

    assert policy.is_known_log('capture') is True
    assert policy.is_known_log('missing') is False
    assert policy.get_log_source('capture')['label'] == 'Capture Log'

    rows = policy.build_source_rows('webapp')

    assert rows == [
        {'name': 'capture', 'label': 'Capture Log', 'active': False},
        {'name': 'webapp', 'label': 'Webapp Log', 'active': True},
        {'name': 'syslog', 'label': 'OS System Log', 'active': False},
        {'name': 'kernel', 'label': 'Kernel Log', 'active': False},
    ]


def test_log_display_policy_redacts_sensitive_lines():
    policy = ModernAdminLogDisplayPolicy()

    line = 'password=alpha token:beta api_key=gamma secret:delta ok'
    redacted = policy.redact_log_line(line)

    assert 'alpha' not in redacted
    assert 'beta' not in redacted
    assert 'gamma' not in redacted
    assert 'delta' not in redacted
    assert redacted == 'password=[REDACTED] token:[REDACTED] api_key=[REDACTED] secret:[REDACTED] ok'


def test_log_display_policy_formats_file_size():
    policy = ModernAdminLogDisplayPolicy()

    assert policy.format_file_size(None) == 'Unknown'
    assert policy.format_file_size(0) == '0 B'
    assert policy.format_file_size(1023) == '1023 B'
    assert policy.format_file_size(1024) == '1.0 KB'
    assert policy.format_file_size(1024 * 1024) == '1.0 MB'
    assert policy.format_file_size('unknown') == 'unknown'


def test_modern_log_detail_view_uses_system_tool_policy():
    source = (REPO_ROOT / 'indi_allsky' / 'flask' / 'views.py').read_text()
    start = source.index('class ModernAdminLogDetailView')
    end = source.index('class ModernAdminMaskView', start)
    source = source[start:end]

    assert 'ModernAdminLogDisplayPolicy' in source
    assert "Path('/var/log/indi-allsky/indi-allsky.log')" not in source
    assert "re.compile(r'(?i)(password" not in source
    assert 'line_limit * self.line_size' not in source


def test_system_tools_module_has_no_flask_db_or_file_read_dependency():
    import indi_allsky.modern_admin_system_tools as module

    source = inspect.getsource(module)

    assert 'flask' not in source.lower()
    assert 'db.session' not in source
    assert 'request' not in source
    assert 'io.open' not in source


def run_tests():
    test_log_display_policy_preserves_line_limits()
    test_log_display_policy_preserves_source_rows()
    test_log_display_policy_redacts_sensitive_lines()
    test_log_display_policy_formats_file_size()
    test_modern_log_detail_view_uses_system_tool_policy()
    test_system_tools_module_has_no_flask_db_or_file_read_dependency()
    print('Modern admin system tools checks passed')


if __name__ == '__main__':
    run_tests()
