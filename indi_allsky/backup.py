
import time
from datetime import datetime
from pathlib import Path
import subprocess
import psutil
import sqlite3
import tempfile
import os
import logging

from .flask import db
from .flask.miscDb import miscDb

from .exceptions import BackupFailure


logger = logging.getLogger('indi_allsky')


class IndiAllskyDatabaseBackup(object):

    # maintain at least this many backups
    keep_backups = 7


    def __init__(self, config, skip_frames=0):
        self.config = config

        self._miscDb = miscDb(self.config)

        varlib_folder = self.config.get('VARLIB_FOLDER', '/var/lib/indi-allsky')
        self.varlib_folder_p = Path(varlib_folder)

        # DB folder is managed separately from varlib
        db_folder = Path('/var/lib/indi-allsky')
        self.backup_folder_p = db_folder.joinpath('backup')


    def db_backup(self):
        self.checkAvailableSpace()


        now_time = time.time()

        # immediately set timestamp so if it fails, it will not run immediately again
        self._miscDb.setState('BACKUP_DB_TS', int(now_time))


        now = datetime.now()
        final = self.backup_folder_p / ('backup_indi-allsky_{0:%Y%m%d_%H%M%S_%f}.sqlite.gz'.format(now))
        temporary = None
        compressed = None
        try:
            with tempfile.NamedTemporaryFile(prefix='.backup_indi-allsky_', suffix='.sqlite',
                                             dir=self.backup_folder_p, delete=False) as stream:
                temporary = Path(stream.name)
            compressed = Path(str(temporary) + '.gz')
            backup_conn = sqlite3.connect(str(temporary))
            try:
                raw_connection = db.engine.raw_connection()
                try:
                    raw_connection.backup(backup_conn)
                finally:
                    raw_connection.close()
            finally:
                backup_conn.close()
            temporary.chmod(0o640)
            subprocess.run(('/usr/bin/gzip', str(temporary)), check=True,
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            if not compressed.is_file() or compressed.stat().st_size == 0:
                raise BackupFailure('Backup compression produced no file')
            os.replace(compressed, final)
        except (OSError, sqlite3.Error, subprocess.CalledProcessError) as error:
            logger.error('Database backup failed: %s', error)
            raise BackupFailure('Database backup or compression failed') from error
        finally:
            for partial in (temporary, compressed):
                if partial is not None:
                    partial.unlink(missing_ok=True)

        self.expireBackups()
        return str(final)


    def expireBackups(self):
        backup_list = [path for path in self.backup_folder_p.iterdir()
                       if path.is_file() and not path.is_symlink()
                       and path.name.startswith('backup_indi-allsky_')
                       and path.name.endswith(('.sqlite.gz', '.sqlite'))]

        backup_list_ordered = sorted(backup_list, key=lambda p: p.stat().st_mtime, reverse=True)


        remove_backups = backup_list_ordered[self.keep_backups:]


        for b in remove_backups:
            logger.warning('Remove backup: %s', b)
            b.unlink()


    def checkAvailableSpace(self):
        try:
            free_bytes = psutil.disk_usage(str(self.backup_folder_p)).free
        except OSError as error:
            raise BackupFailure('Cannot determine available backup space') from error
        if free_bytes < 1000 * 1024 * 1024:
            raise BackupFailure('Not enough available space on backup filesystem')

