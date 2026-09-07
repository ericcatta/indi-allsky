#!/usr/bin/env python3
"""Real SQLite/gzip round-trip; failed compression cannot prune good backups."""
import gzip
from pathlib import Path
import sqlite3
import subprocess
from types import SimpleNamespace
from unittest.mock import patch
from hybrid_runtime_fixture import isolated_app


def run():
    with isolated_app(multi_camera=True) as app:
        from indi_allsky.backup import IndiAllskyDatabaseBackup
        from indi_allsky.exceptions import BackupFailure
        with app.app_context():
            root=Path(app.config['INDI_ALLSKY_IMAGE_FOLDER'])/'backups';root.mkdir()
            backup=IndiAllskyDatabaseBackup({});backup.backup_folder_p=root
            unrelated=root/'user-data.sqlite';unrelated.write_bytes(b'preserve')
            with patch('indi_allsky.backup.psutil.disk_usage',return_value=SimpleNamespace(total=10**12,free=999*1024**2)):
                try:backup.db_backup()
                except BackupFailure:pass
                else:raise AssertionError('Full disk accepted because total capacity is large')
            with patch('indi_allsky.backup.psutil.disk_usage',return_value=SimpleNamespace(total=10**12,free=2*1024**3)):
                first=Path(backup.db_backup())
                assert first.is_file() and first.stat().st_mode & 0o777 == 0o640
                restored=root/'restore-check.db';restored.write_bytes(gzip.decompress(first.read_bytes()))
                with sqlite3.connect(restored) as db:
                    assert db.execute('PRAGMA integrity_check').fetchone()[0]=='ok'
                    assert db.execute('SELECT COUNT(*) FROM camera').fetchone()[0]==2
                for effect in (subprocess.CalledProcessError(1,['gzip']), OSError('gzip unavailable')):
                    with patch('indi_allsky.backup.subprocess.run',side_effect=effect):
                        try:backup.db_backup()
                        except BackupFailure:pass
                        else:raise AssertionError('Compression failure reported success')
                    assert first.exists() and not list(root.glob('.backup_*'))
                with patch('indi_allsky.backup.subprocess.run',return_value=SimpleNamespace(returncode=0)):
                    try:backup.db_backup()
                    except BackupFailure:pass
                    else:raise AssertionError('Missing compressed file reported success')
                backup.keep_backups=1
                second=Path(backup.db_backup())
                assert first!=second and second.exists() and not first.exists()
                assert unrelated.read_bytes()==b'preserve' and restored.exists()
                assert not list(root.glob('.backup_*'))
        print('Backup: real SQLite/gzip restore and integrity, free-space guard, failed/missing compression, cleanup and scoped retention: PASS')


if __name__=='__main__':run()
