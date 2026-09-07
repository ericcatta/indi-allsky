#!/usr/bin/env python3
"""Aurora presentation with real Flask and user numeric format contracts."""
from copy import deepcopy
import time
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from hybrid_runtime_fixture import isolated_app, login_client


def run():
    from indi_allsky.modern_admin_aurora_status import build_aurora_status, FIELDS
    now = time.time()
    source = {key: 0 for _, key, _ in FIELDS.values()}
    source.update(AURORA_DATA_TS=now, KPINDEX_CURRENT=6, KPINDEX_COEF=2)
    before = deepcopy(source)
    current = build_aurora_status(source, now)
    assert source == before
    assert current['aurora_data_status'] == '' and 'HIGH' in current['kpindex_rating']
    assert current['kpindex_trend'] == '&nearr;' and current['ovation_max'] == 0
    missing = build_aurora_status({'unrelated': 'present'}, now)
    assert missing['aurora_data_status'] == 'No data'
    assert '{kpindex:0.2f}/{ovation_max:d}/{aurora_mag_bt:+0.1f}'.format(**missing) == '—/—/—'
    assert not missing['kpindex_rating'] and not missing['kpindex_trend']
    for value in (None, 'bad', float('nan'), float('inf'), [], {}, True):
        bad = build_aurora_status({**source, 'KPINDEX_CURRENT': value}, now)
        assert str(bad['kpindex']) == '—' and bad['kpindex_status'] == 'No data'
    for value in (None, 'bad', 0, now + 100):
        assert build_aurora_status({**source, 'AURORA_DATA_TS': value}, now)['kpindex_status'] == '[age unknown]'
    old = build_aurora_status({**source, 'AURORA_DATA_TS': now - 21601}, now)
    assert old['aurora_data_status'] == '[old]' and not old['kpindex_rating']
    assert build_aurora_status({**source, 'AURORA_DATA_TS': now - 21600}, now)['aurora_data_status'] == ''
    components = {name: {'state': 'available', 'last_success': now} for name, _, _ in FIELDS.values()}
    components['mag'] = {'state': 'unavailable', 'last_success': now - 30000}
    partial = {**source, 'AURORA_COMPONENT_STATUS': components}
    result = build_aurora_status(partial, now)
    assert 'mag [update failed]' in result['aurora_data_status']
    assert result['aurora_mag_bt'] == 0 and 'HIGH' in result['kpindex_rating']
    components['kpindex'] = {'state': 'available', 'last_success': now - 30000}
    result = build_aurora_status(partial, now)
    assert result['kpindex_status'] == '[old]' and not result['kpindex_rating']
    # A refreshed global timestamp cannot make an old individual feed current.
    with isolated_app(multi_camera=True) as app:
        from indi_allsky.flask import db
        from indi_allsky.flask.models import IndiAllSkyDbCameraTable
        from indi_allsky.flask.base_views import BaseView
        with app.app_context():
            view = object.__new__(BaseView)
            view.camera_data = {}
            view.indi_allsky_config = {'WEB_STATUS_TEMPLATE': '{kpindex:0.2f} {ovation_max:d} {aurora_data_status:s}'}
            assert view.get_status_text(view.get_aurora_info()) == '<div>— — No data</div>'
            for cid, data in ((1, source), (2, partial)):
                db.session.get(IndiAllSkyDbCameraTable, cid).data = data
            db.session.commit()
        for uid in (1, 2):
            client = login_client(app, uid)
            for cid in (1, 2):
                response = client.get('/indi-allsky/modern-admin/now', query_string={'camera_id': cid})
                assert response.status_code == 200 and 'TEMPLATE ERROR' not in response.text
                status = client.get('/indi-allsky/ajax/status_update', query_string={'camera_id': cid})
                assert status.status_code == 200, status.text
                text = status.json['status_text']
                assert 'TEMPLATE ERROR' not in text
                assert ('mag [update failed]' in text) == (cid == 2)
        print('Aurora status: missing/zero/invalid/stale/failed feeds, numeric formats, camera isolation and Classic-free Flask: PASS')


if __name__ == '__main__':
    run()
