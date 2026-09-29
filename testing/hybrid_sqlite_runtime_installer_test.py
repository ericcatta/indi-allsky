"""Installer ownership/failure checks; real loader acceptance is a separate Pi probe."""
import hashlib
import importlib.util
from pathlib import Path
import tempfile
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('installer', Path(__file__).resolve().parents[1] / 'misc/hybrid_sqlite_runtime.py')
installer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(installer)


def main():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        prefix = root/'venv'
        prefix.mkdir()
        (prefix/'pyvenv.cfg').write_text('home = /test\n')
        site = prefix/'lib/site-packages'
        site.mkdir(parents=True)
        library = root/'verified.so'
        library.write_bytes(b'synthetic library; not loaded by this unit test')
        sha = hashlib.sha256(library.read_bytes()).hexdigest()
        try: installer.install(prefix,library,'wrong')
        except ValueError: pass
        else: raise AssertionError('Wrong checksum accepted')
        with patch.object(installer.subprocess,'check_output',side_effect=[str(site),'3.51.3']):
            state = installer.install(prefix,library,sha)
        original = {str(p):p.read_bytes() for p in prefix.rglob('*') if p.is_file()}
        with patch.object(installer.subprocess,'check_output',return_value=str(site)):
            try: installer.install(prefix,library,sha)
            except FileExistsError: pass
            else: raise AssertionError('Managed files overwritten')
        assert original == {str(p):p.read_bytes() for p in prefix.rglob('*') if p.is_file()}
        pth = Path(state['pth'])
        pth.write_text('user changed bootstrap\n')
        try: installer.remove(prefix)
        except ValueError: pass
        else: raise AssertionError('Changed bootstrap deleted')
        pth.write_text('import _hybrid_sqlite_runtime\n')
        installer.remove(prefix)
        assert not pth.exists()
        assert all(not Path(p).exists() for p in state['files'])
        with patch.object(installer.subprocess,'check_output',side_effect=[str(site),'3.46.1']):
            try: installer.install(prefix,library,sha)
            except RuntimeError: pass
            else: raise AssertionError('Wrong loaded version accepted')
        assert not pth.exists()  # failed activation cannot break future launches
        installer.remove(prefix)
        with patch.object(installer.subprocess,'check_output',return_value=str(root)):
            try: installer.install(prefix,library,sha)
            except ValueError: pass
            else: raise AssertionError('Outside virtualenv accepted')
    print('PASS checksum, ownership, activation failure, rollback and path guards')


if __name__ == '__main__':
    main()
