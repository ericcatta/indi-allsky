#!/usr/bin/env python3
"""Real ADU rows, camera selection and table controls with Classic blocked."""
from datetime import datetime, timedelta
import csv
import html
import io
import json
import re
from hybrid_runtime_fixture import isolated_app, login_client
from hybrid_generation_fixture import seed_generation


def run():
    with isolated_app(multi_camera=True) as app:
        seed_generation(app)
        from indi_allsky.flask import db
        from indi_allsky.flask.models import IndiAllSkyDbImageTable, IndiAllSkyDbConfigTable
        with app.app_context():
            for cid in (1, 2):
                row = db.session.get(IndiAllSkyDbImageTable, cid)
                row.createDate = (datetime.now() - timedelta(days=2)).replace(hour=23, minute=0, second=0)
                row.createDate_hour = 23
                row.adu = 12.34 if cid == 1 else 87.65
                row.sqm = None if cid == 1 else 19.5
                row.stars = None if cid == 1 else 234
            db.session.commit()
        endpoint = '/indi-allsky/modern-admin/cameras/adu-history'
        for uid in (1, 2):
            client = login_client(app, uid)
            for cid in (1, 2):
                page = client.get(endpoint + '?camera_id=' + str(cid))
                assert page.status_code == 200, page.text[:500]
                rows = re.findall(r'<tr data-search=.*?</tr>', page.text, re.S)
                assert len(rows) == 1, rows
                assert ('12.34' if cid == 1 else '87.65') in rows[0]
                assert ('87.65' if cid == 1 else '12.34') not in rows[0]
                if cid == 1:
                    assert rows[0].count('—') == 2
                config = json.loads(re.search(r'id="hybrid-operations-table-config" type="application/json">(.*?)</script>', page.text, re.S)[1])
                assert config['order'] == [[0, 'desc']]
                assert config['exportColumns'] == list(range(6)) and config['columnDefs'] == []
                assert 'id="adu-history-search"' in page.text
                assert config['csrfToken'] and config['exportUrl'].endswith('/operations/export')
                cells = [html.unescape(value) for value in re.findall(r'<td>(.*?)</td>', rows[0])]
                headers = ['Date', 'Count', 'Exposure Avg', 'ADU Avg', 'jSQM Avg', 'Stars Avg']
                exported = client.post(config['exportUrl'], data={
                    'csrf_token': config['csrfToken'], 'format': 'csv',
                    'table': json.dumps({'header': headers, 'body': [cells]}),
                })
                assert exported.status_code == 200 and 'attachment' in exported.headers['Content-Disposition']
                assert list(csv.reader(io.StringIO(exported.data.decode('utf-8-sig')))) == [headers, cells]
            profile = client.get(endpoint + '?profile_id=test-profile-1')
            assert profile.status_code == 200 and '<td>12.34</td>' in profile.text
            for query in ('camera_id=bad','camera_id=1&profile_id=test-profile-2','profile_id=missing'):
                assert client.get(endpoint + '?' + query).status_code == 400
        assert app.test_client().get(endpoint).status_code == 302
        with app.app_context():
            assert db.session.query(IndiAllSkyDbConfigTable).count() == 1
            assert db.session.query(IndiAllSkyDbImageTable).count() == 2
        print('ADU history: camera/profile isolation, nullable metrics, table controls and unchanged data: PASS')


if __name__ == '__main__':
    run()
