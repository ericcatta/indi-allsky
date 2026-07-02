import re
from pathlib import Path


LOG_DETAIL_MAX_LINES = 500
LOG_DETAIL_DEFAULT_LINES = 200
LOG_DETAIL_LINE_SIZE = 180

LOG_DETAIL_SOURCES = {
    'capture': {
        'label'       : 'Capture Log',
        'path'        : Path('/var/log/indi-allsky/indi-allsky.log'),
        'classic_url' : 'indi_allsky.log_view',
    },
    'webapp': {
        'label'       : 'Webapp Log',
        'path'        : Path('/var/log/indi-allsky/webapp-indi-allsky.log'),
        'classic_url' : 'indi_allsky.log_view',
    },
    'syslog': {
        'label'       : 'OS System Log',
        'path'        : Path('/var/log/syslog'),
        'classic_url' : 'indi_allsky.log_view',
    },
    'kernel': {
        'label'       : 'Kernel Log',
        'path'        : Path('/var/log/kern.log'),
        'classic_url' : 'indi_allsky.log_view',
    },
}

LOG_DETAIL_SENSITIVE_PATTERNS = (
    r'(?i)(password\s*[:=]\s*)(\S+)',
    r'(?i)(token\s*[:=]\s*)(\S+)',
    r'(?i)(api[_-]?key\s*[:=]\s*)(\S+)',
    r'(?i)(secret\s*[:=]\s*)(\S+)',
)


class ModernAdminLogDisplayPolicy:
    def __init__(
        self,
        max_detail_lines=LOG_DETAIL_MAX_LINES,
        default_detail_lines=LOG_DETAIL_DEFAULT_LINES,
        line_size=LOG_DETAIL_LINE_SIZE,
        log_sources=None,
        sensitive_patterns=None,
    ):
        self.max_detail_lines = max_detail_lines
        self.default_detail_lines = default_detail_lines
        self.line_size = line_size
        self.log_sources = log_sources or LOG_DETAIL_SOURCES
        self.sensitive_line_regexes = tuple(
            re.compile(pattern) if isinstance(pattern, str) else pattern
            for pattern in (sensitive_patterns or LOG_DETAIL_SENSITIVE_PATTERNS)
        )


    def is_known_log(self, log_name):
        return log_name in self.log_sources


    def get_log_source(self, log_name):
        return self.log_sources[log_name]


    def normalize_line_limit(self, line_limit):
        try:
            normalized_limit = int(line_limit)
        except (TypeError, ValueError):
            return self.default_detail_lines

        if normalized_limit <= 0:
            return self.default_detail_lines

        return min(normalized_limit, self.max_detail_lines)


    def read_bytes_for_limit(self, line_limit):
        return line_limit * self.line_size


    def build_source_rows(self, active_log_name):
        return [
            {
                'name'   : source_name,
                'label'  : source['label'],
                'active' : source_name == active_log_name,
            }
            for source_name, source in self.log_sources.items()
        ]


    def redact_log_line(self, line):
        redacted_line = line
        for sensitive_regex in self.sensitive_line_regexes:
            redacted_line = sensitive_regex.sub(r'\1[REDACTED]', redacted_line)

        return redacted_line


    def format_file_size(self, value):
        if value is None:
            return 'Unknown'

        try:
            size = float(value)
        except (TypeError, ValueError):
            return str(value)

        units = ('B', 'KB', 'MB', 'GB', 'TB')
        unit_index = 0
        while size >= 1024.0 and unit_index < len(units) - 1:
            size /= 1024.0
            unit_index += 1

        if unit_index == 0:
            return '{0:d} {1:s}'.format(int(size), units[unit_index])
        return '{0:.1f} {1:s}'.format(size, units[unit_index])
