"""Bounded application-log reading for the Hybrid operational viewer."""
import os
import re


class ModernAdminLogReader:
    MAX_LINES = 5000
    MAX_BYTES = 750000
    CHUNK_BYTES = 8192

    def read(self, path, payload):
        if not isinstance(payload, dict):
            return 'ERROR: Invalid log request'
        try:
            limit = min(int(payload.get('lines', 500)), self.MAX_LINES)
        except (ValueError, TypeError, OverflowError):
            return 'ERROR: Invalid log line count'
        if limit < 1:
            return 'ERROR: Invalid log line count'
        filter_text = str(payload.get('filter', ''))[:30]
        if not re.fullmatch(r'[a-zA-Z0-9_\.\-\\ ]*', filter_text):
            return 'ERROR: Log filter has illegal characters'
        try:
            pattern = re.compile(filter_text, re.IGNORECASE) if filter_text else None
        except re.error:
            return 'ERROR: Invalid log filter expression'

        try:
            with path.open('rb') as stream:
                stream.seek(0, os.SEEK_END)
                position = stream.tell()
                chunks, total, newlines = [], 0, 0
                # Read backward until enough complete lines are available. File
                # size and bytes come from the same open handle, even on rename.
                while position > 0 and total < self.MAX_BYTES and newlines <= limit:
                    count = min(position, self.CHUNK_BYTES, self.MAX_BYTES - total)
                    position -= count
                    stream.seek(position)
                    chunk = stream.read(count)
                    chunks.append(chunk)
                    total += count
                    newlines += chunk.count(b'\n')
                data = b''.join(reversed(chunks))
        except FileNotFoundError:
            return 'ERROR: Log file missing'
        except PermissionError:
            return 'ERROR: Log file access denied'
        except OSError:
            return 'ERROR: Log file could not be read'

        truncated = position > 0
        if truncated:
            # The first fragment may start in the middle of a UTF-8 character
            # or line. Complete older lines are excluded by the final limit.
            _, separator, data = data.partition(b'\n')
            if not separator:
                return '[No complete log lines within read limit]'
        if not data:
            return '[No complete log lines within read limit]' if truncated else '[indi-allsky log empty]'
        lines = data.decode('utf-8', errors='replace').splitlines()[-limit:]
        lines.reverse()
        if pattern:
            lines = [line for line in lines if pattern.search(line)]
        if not lines:
            return '[No matching lines]'
        return '\n'.join(lines) + ('\n' if data.endswith((b'\n', b'\r')) else '')
