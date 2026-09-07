"""Bounded binary log exports; no decoding or modification of source bytes."""
import gzip
import os


class LogDownloadError(Exception):
    def __init__(self, message, status):
        super().__init__(message)
        self.status = status


class ModernAdminLogDownloadService:
    MAX_LINES = 20000
    BYTES_PER_LINE = 150

    def prepare(self, path, requested_lines, default_lines):
        try:
            lines = int(default_lines if requested_lines is None else requested_lines)
        except (TypeError, ValueError, OverflowError):
            raise LogDownloadError('Invalid log line count', 400)
        if lines < 1:
            raise LogDownloadError('Invalid log line count', 400)
        # Preserve the historical byte-window meaning of download "lines".
        read_bytes = min(lines, self.MAX_LINES) * self.BYTES_PER_LINE
        try:
            with path.open('rb') as stream:
                stream.seek(0, os.SEEK_END)
                size = stream.tell()
                stream.seek(max(size - read_bytes, 0))
                data = stream.read(read_bytes)
        except FileNotFoundError:
            raise LogDownloadError('Log file does not exist', 404)
        except PermissionError:
            raise LogDownloadError('Log file access denied', 403)
        except OSError:
            raise LogDownloadError('Log file could not be read', 503)
        if not data:
            raise LogDownloadError('Log file is empty', 200)
        return gzip.compress(data)
