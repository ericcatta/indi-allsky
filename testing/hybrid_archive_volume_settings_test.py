#!/usr/bin/env python3
"""Admin can recover disk protection while archive is offline."""
from pathlib import Path
import re
from unittest.mock import patch
from hybrid_runtime_fixture import isolated_app, login_client

with isolated_app(multi_camera=True) as app:
    from indi_allsky.flask.models import IndiAllSkyDbConfigTable as Config
    url='/indi-allsky/modern-admin/settings/storage-protection?camera_id=2'
    admin=login_client(app,1)
    def form(client):
        page=client.get(url)
        assert page.status_code==200, page.text
        return {key:re.search(r'name="'+key+r'" value="([^"]+)"',page.text)[1] for key in ('csrf_token','revision')}
    device=Path(app.config['INDI_ALLSKY_IMAGE_FOLDER']).stat().st_dev
    with patch('indi_allsky.flask.storage_settings.current_volume_uuid',return_value='test-volume'), patch('indi_allsky.archive_volume.device_identity',return_value=device):
        data=dict(form(admin),operation='volume',volume_required='on')
        assert admin.post(url,data=data).status_code==303
        assert admin.post(url,data=data).status_code==409
    with app.app_context():
        assert Config.query.order_by(Config.id.desc()).first().data['ARCHIVE_VOLUME']['UUID']=='test-volume'
    with patch('indi_allsky.archive_volume.device_identity',side_effect=FileNotFoundError):
        page=admin.get(url)
        assert page.status_code==200, page.text
        assert 'unavailable' in page.text.lower()
        # A valid authenticated Sync request cannot publish to the underlying disk.
        import io
        from indi_allsky.flask.syncapi_views import SyncApiBaseView
        with patch.object(SyncApiBaseView, 'authorize'), patch.object(SyncApiBaseView, 'post') as publish:
            response=app.test_client().post('/indi-allsky/sync/v1/image',
                data={'metadata':(io.BytesIO(b'{}'),'metadata.json')})
            assert response.status_code==503, response.text
            publish.assert_not_called()

        from indi_allsky.archive_volume import ArchiveUnavailable
        from indi_allsky.flask.models import IndiAllSkyDbThumbnailTable
        probe=Path(app.config['INDI_ALLSKY_IMAGE_FOLDER']) / 'volume-probe.fits'
        probe.write_bytes(b'unchanged-source')
        with app.app_context():
            entry=IndiAllSkyDbThumbnailTable(filename=probe.name)
            for operation in (entry.getFilesystemPath, entry.validateFile, entry.deleteFile):
                try: operation()
                except ArchiveUnavailable: pass
                else: raise AssertionError('Offline media access accepted')
        assert probe.read_bytes()==b'unchanged-source'
        probe.unlink()

        reader=login_client(app,2)
        assert reader.post(url,data=dict(form(reader),operation='volume')).status_code==403
        assert admin.post(url,data={'operation':'volume'}).status_code==400
        assert admin.post(url,data=dict(form(admin),operation='volume')).status_code==303
    with app.app_context():
        assert Config.query.order_by(Config.id.desc()).first().data['ARCHIVE_VOLUME'] is None
print('Archive volume Settings: pin, stale revision, offline recovery, roles and CSRF PASS')
