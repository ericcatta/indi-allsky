#!/usr/bin/env python3
"""Actual bounded file reads and regressions for lost/excess log lines."""
import ast
import io
from pathlib import Path
import sys
import tempfile
from unittest.mock import Mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from indi_allsky.modern_admin_log_reader import ModernAdminLogReader


def run():
    reader = ModernAdminLogReader()
    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / 'app.log'
        path.write_text('only line\n')
        assert reader.read(path, {}) == 'only line\n'
        path.write_text('first\nlast')
        assert reader.read(path, {}) == 'last\nfirst'
        path.write_text(''.join(f'line {i:04d}\n' for i in range(1000)))
        for limit in (25, 100, 500, 1000, 2000, 5000):
            assert reader.read(path, {'lines': limit}).splitlines() == [
                f'line {i:04d}' for i in range(999, 999 - min(limit, 1000), -1)]
        assert reader.read(path, {'lines': 25, 'filter': 'LiNe 0999'}) == 'line 0999\n'
        assert reader.read(path, {'lines': 25, 'filter': 'line 0000'}) == '[No matching lines]'
        assert reader.read(path, {'filter': r'line 099\d'}).count('\n') == 10
        for payload in (None, [], {'lines': 0}, {'lines': -1}, {'lines': 'bad'}, {'lines': None}, {'lines': float('inf')}, {'filter': '['}, {'filter': '\\'}, {'filter': r'\1'}):
            assert reader.read(path, payload).startswith('ERROR:'), payload
        path.write_bytes(b'first\r\nsecond\r\n')
        assert reader.read(path, {}) == 'second\nfirst\n'
        path.write_bytes(b'first\ninvalid \xff\nlast \xe2\x82\xac\n')
        assert reader.read(path, {'lines': 2}) == 'last €\ninvalid �\n'
        path.write_bytes(b'')
        assert reader.read(path, {}) == '[indi-allsky log empty]'
        path.unlink()
        assert reader.read(path, {}) == 'ERROR: Log file missing'
        for error, message in ((PermissionError(), 'access denied'), (OSError(), 'could not be read')):
            denied = Mock()
            denied.open.side_effect = error
            assert message in reader.read(denied, {})

        # Instrument real byte handling to prove the I/O bound, including a
        # pathological single line and a file much larger than the window.
        class MeasuredFile(io.BytesIO):
            def __init__(self, data):
                super().__init__(data)
                self.bytes_read = 0

            def read(self, count=-1):
                assert 0 <= count <= reader.CHUNK_BYTES
                data = super().read(count)
                self.bytes_read += len(data)
                return data

        for data, expected in ((b'x' * (reader.MAX_BYTES + 1), '[No complete log lines within read limit]'),
                               (b'x' * (reader.MAX_BYTES + 1) + b'\nlatest\n', 'latest\n')):
            stream = MeasuredFile(data)
            source = Mock()
            source.open.return_value = stream
            assert reader.read(source, {'lines': 5000}) == expected
            assert stream.bytes_read <= reader.MAX_BYTES
        stream = MeasuredFile(b'line\n' * 1000000)
        source = Mock()
        source.open.return_value = stream
        assert len(reader.read(source, {'lines': 25}).splitlines()) == 25
        assert stream.bytes_read == reader.CHUNK_BYTES
        stream = MeasuredFile(b'line\n' * 1000000)
        source.open.return_value = stream
        assert len(reader.read(source, {'lines': 999999}).splitlines()) == reader.MAX_LINES

    tree = ast.parse((ROOT / 'indi_allsky/flask/views.py').read_text())
    cls = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == 'JsonLogView')
    text = ast.unparse(cls)
    assert 'ModernAdminLogReader().read(' in text and 'readlines(' not in text
    assert "methods = ['POST']" in text and 'decorators = [login_required]' in text
    print('Log reader: exact tail, first/unterminated/UTF-8 lines, filtering, errors, 8192-byte short tail and 750000-byte hard bound: PASS')


if __name__ == '__main__':
    run()
