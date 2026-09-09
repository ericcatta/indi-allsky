#!/usr/bin/env python3
"""Real SQLite/gzip round-trip; failed compression cannot prune good backups."""
import gzip
import re
from pathlib import Path
import sqlite3
import subprocess
from types import SimpleNamespace
from unittest.mock import patch
from hybrid_runtime_fixture import isolated_app, login_client


def run():
    with isolated_app(multi_camera=True) as app:
        from indi_allsky.backup import IndiAllskyDatabaseBackup
        from indi_allsky.exceptions import BackupFailure
        from indi_allsky.flask import db, models
        from indi_allsky.modern_admin_runtime_effects import ModernAdminTaskEnqueueEffectAdapter
        admin, ordinary, anonymous = login_client(app, 1), login_client(app, 2), app.test_client()
        def headers(client, path='/indi-allsky/modern-admin/account'):
            return {'X-CSRFToken': re.search(r'name="csrf_token"[^>]*value="([^"]+)"', client.get(path).text)[1]}
        auth, denied, anon = headers(admin), headers(ordinary), headers(anonymous, '/indi-allsky/login')
        endpoint = '/indi-allsky/ajax/system'
        payload = dict(CAMERA_ID=2, SERVICE_HIDDEN='system', COMMAND_HIDDEN='backup_db')
        with patch.object(ModernAdminTaskEnqueueEffectAdapter, 'enqueue_from_plan', side_effect=AssertionError('Unauthorized enqueue')) as effect:
            assert admin.post(endpoint, json=payload).status_code == 400
            assert ordinary.post(endpoint, json=payload, headers=denied).status_code == 400
            assert anonymous.post(endpoint, json=payload, headers=anon).status_code == 302
            effect.assert_not_called()
        response = admin.post(endpoint, json=payload, headers=auth)
        assert response.status_code == 200, response.text
        assert response.json == {'success-message': 'Submitted backup task'}
        ident = int(response.headers['X-Hybrid-Task-Id'])
        with app.app_context():
            task = db.session.get(models.IndiAllSkyDbTaskQueueTable, ident)
            assert task.data == {'action': 'backupDatabase', 'kwargs': {}}
            assert task.queue == models.TaskQueueQueue.VIDEO and task.state == models.TaskQueueState.MANUAL
            assert task.priority == 100
        assert admin.get('/indi-allsky/modern-admin/tasks/' + str(ident)).status_code == 200
        with patch.object(ModernAdminTaskEnqueueEffectAdapter, 'enqueue_from_plan', side_effect=RuntimeError('private failure')):
            response = admin.post(endpoint, json=payload, headers=auth)
            assert response.status_code == 503 and 'private failure' not in response.text
        for client, writable in ((admin, True), (ordinary, False)):
            page = client.get('/indi-allsky/modern-admin/system/info?camera_id=2&profile_id=test-profile-2')
            assert page.status_code == 200
            form = page.text.split('class="system-backup-form"', 1)[1].split('</form>', 1)[0]
            assert ('<fieldset disabled>' in form) != writable
            assert 'value="backup_db"' in form and 'all cameras' in form
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
