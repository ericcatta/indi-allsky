#!/usr/bin/env python3
"""Two actual Flask processes restoring the same revision in a disposable SQLite DB."""
import multiprocessing
import time
from unittest.mock import patch
from hybrid_runtime_fixture import isolated_app, login_client
from hybrid_settings_flow_test import payload_from_page


def run():
    with isolated_app(multi_camera=True, file_database=True) as app:
        from indi_allsky.flask import db
        from indi_allsky.flask.models import IndiAllSkyDbConfigTable
        from indi_allsky.modern_admin_settings_runtime import ModernAdminSettingsRestoreService
        client = login_client(app, 1)
        _, token = payload_from_page(client.get('/indi-allsky/modern-admin/settings/full').text)
        context = multiprocessing.get_context('fork')
        barrier = context.Barrier(2)
        results = context.Queue()
        restore = ModernAdminSettingsRestoreService.restore_snapshot
        def delayed_restore(*args, **kwargs):
            time.sleep(1)  # Let the other process reach its revision check.
            return restore(*args, **kwargs)
        def request_restore():
            with app.app_context():
                db.session.remove()
                db.engine.dispose()
            barrier.wait(timeout=10)
            with patch.object(ModernAdminSettingsRestoreService, 'restore_snapshot', delayed_restore):
                response = client.post('/indi-allsky/modern-admin/config-restore/1/apply',
                    data={'CONFIRM_RESTORE':'yes', 'EXPECTED_CONFIG_ID':'1'},
                    headers={'X-CSRFToken':token})
            results.put(response.status_code)
        processes = [context.Process(target=request_restore) for _ in range(2)]
        try:
            for process in processes: process.start()
            for process in processes: process.join(timeout=20)
            assert all(not p.is_alive() and p.exitcode == 0 for p in processes)
            statuses = sorted(results.get(timeout=2) for _ in processes)
            assert statuses == [200,409], statuses
            with app.app_context():
                db.session.remove()
                assert IndiAllSkyDbConfigTable.query.count() == 2
                assert db.session.get(IndiAllSkyDbConfigTable, 1).note == 'Synthetic acceptance fixture'
            print('Concurrent Flask snapshot restore: one commit, one stale rejection, history retained: PASS')
        finally:
            for process in processes:
                if process.is_alive(): process.terminate(); process.join()


if __name__ == '__main__':
    run()
