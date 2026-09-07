#!/usr/bin/env python3
"""All four authenticated log exports with real gzip and disposable files."""
import gzip
from pathlib import Path
from unittest.mock import Mock, patch
from hybrid_runtime_fixture import isolated_app, login_client


def run():
    with isolated_app() as app:
        from indi_allsky.flask import views
        from indi_allsky.modern_admin_log_download import ModernAdminLogDownloadService, LogDownloadError
        root = Path(app.config['INDI_ALLSKY_IMAGE_FOLDER'])
        cases = [('download', views.LogDownloadView, 'indi-allsky_log', 'capture'),
                 ('webapp_download', views.LogWebappDownloadView, 'indi-allsky_webapp_log', 'webapp'),
                 ('syslog_download', views.LogSyslogDownloadView, 'indi-allsky_syslog_log', 'syslog'),
                 ('kern_download', views.LogKernDownloadView, 'indi-allsky_kern_log', 'kernel')]
        for name, cls, prefix, kind in cases:
            source = root / name
            content = (name.encode() + b'\n\xff\x00') * 300
            source.write_bytes(content)
            url = '/indi-allsky/log/' + name
            original_source = views.ModernAdminLogDetailView.log_policy.log_sources[kind]
            with patch.object(cls, 'log_path', str(source)), patch.dict(
                    views.ModernAdminLogDetailView.log_policy.log_sources,
                    {kind: dict(original_source, path=source)}):
                assert app.test_client().get(url).status_code == 302
                for uid in (1, 2):
                    client = login_client(app, uid)
                    response = client.get(url)
                    assert response.status_code == 200
                    assert response.mimetype == 'application/octet-stream'
                    assert prefix + '_' in response.headers['Content-Disposition']
                    assert 'attachment' in response.headers['Content-Disposition']
                    assert gzip.decompress(response.data) == content
                    assert gzip.decompress(client.get(url + '?lines=1').data) == content[-150:]
                    for invalid in ('0', '-1', 'oops'):
                        assert client.get(url + '?lines=' + invalid).status_code == 400
                    assert client.post(url).status_code in (400, 405)
                    detail = client.get('/indi-allsky/modern-admin/system/log/' + kind)
                    assert detail.status_code == 200
                    assert 'Open legacy' not in detail.text
                    assert f'href="{url}"' in detail.text and 'Download this log (.gz)' in detail.text
                source.write_bytes(b'')
                empty = client.get(url)
                assert empty.status_code == 200 and empty.text == 'Log file is empty'
                source.write_bytes(b'disposable permission test\n')
                source.chmod(0o000)
                try:
                    assert client.get(url).status_code == 403
                finally:
                    source.chmod(0o600)
                source.unlink()
                assert client.get(url).status_code == 404
                missing_detail = client.get('/indi-allsky/modern-admin/system/log/' + kind)
                assert missing_detail.status_code == 200 and 'Missing' in missing_detail.text
        assert client.get('/indi-allsky/modern-admin/system/log/unknown').status_code == 404

        service = ModernAdminLogDownloadService()
        for exc, status in ((PermissionError('private path'), 403), (OSError('private path'), 503)):
            source = Mock(); source.open.side_effect = exc
            try:
                service.prepare(source, None, 20000)
            except LogDownloadError as error:
                assert error.status == status and 'private path' not in str(error)
            else:
                raise AssertionError('Source failure ignored')
        source = root / 'large'
        content = b'a' * 3000001 + b'end'
        source.write_bytes(content)
        assert gzip.decompress(service.prepare(source, '999999999', 20000)) == content[-3000000:]
        assert gzip.decompress(service.prepare(source, None, 5000)) == content[-750000:]
        print('Four gzip downloads: exact source bytes, names, both roles, scope, invalid inputs, empty/missing/error sources and 3 MB bound: PASS')


if __name__ == '__main__':
    run()
