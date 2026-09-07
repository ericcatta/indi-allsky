#!/usr/bin/env python3
"""Synthetic orbital elements exercise actual PyEphem and Flask; no live orbit claims."""
from datetime import datetime, timezone
from unittest.mock import patch
from hybrid_runtime_fixture import isolated_app, login_client


class FixedClock(datetime):
    @classmethod
    def now(cls, tz=None):
        value = cls(2026, 9, 7, 7, 0, tzinfo=timezone.utc)
        return value.astimezone(tz) if tz else value.replace(tzinfo=None)


def checksum(line):
    assert len(line) == 68, (len(line), line)
    return line + str(sum(int(c) if c.isdigit() else 1 if c == '-' else 0 for c in line) % 10)


def run():
    with isolated_app(multi_camera=True) as app:
        from indi_allsky.flask import db
        from indi_allsky.flask.models import IndiAllSkyDbTleDataTable, IndiAllSkyDbCameraTable
        from indi_allsky import constants
        # Deliberately synthetic ISS-like geometry at a fixed epoch, not published TLEs.
        line1 = checksum('1 25544U 98067A   26250.00000000  .00010000  00000-0  18000-3 0  999')
        line2 = checksum('2 25544  51.6400 100.0000 0005000  20.0000 340.0000 15.5000000040000')
        with app.app_context():
            for i in range(20):
                db.session.add(IndiAllSkyDbTleDataTable(title='SYNTHETIC-'+str(i), line1=line1, line2=line2, group=constants.SATELLITE_VISUAL))
            db.session.add(IndiAllSkyDbTleDataTable(title='INVALID-TLE', line1='invalid', line2='invalid', group=constants.SATELLITE_VISUAL))
            db.session.add(IndiAllSkyDbTleDataTable(title='EXPIRED-TLE', line1=checksum(line1[:18]+'00250.00000000'+line1[32:68]), line2=line2, group=constants.SATELLITE_VISUAL))
            db.session.add(IndiAllSkyDbTleDataTable(title='OTHER-GROUP', line1=line1, line2=line2, group=-1))
            camera = db.session.get(IndiAllSkyDbCameraTable, 2)
            camera.latitude = -33.0
            camera.longitude = 151.0
            db.session.commit()
        positions = {}
        with patch('indi_allsky.flask.views.datetime', FixedClock):
            for uid in (1, 2):
                client = login_client(app, uid)
                for cid in (1, 2):
                    response = client.get('/indi-allsky/ajax/astropanel', query_string={'camera_id':cid})
                    assert response.status_code == 200, response.text[:500]
                    rows = response.json['satellite_list']
                    errors = response.json['satellite_errors']
                    assert {error['name'] for error in errors} == {'INVALID-TLE', 'EXPIRED-TLE'}, errors
                    assert any('date' in error['reason'] for error in errors)
                    assert len(rows) == 20, rows
                    assert all(row['name'].startswith('SYNTHETIC-') for row in rows)
                    assert [row['alt'] for row in rows] == sorted((row['alt'] for row in rows), reverse=True)
                    for row in rows:
                        assert isinstance(row['eclipsed'], bool)
                        assert isinstance(row['elevation'], int) and row['elevation'] > 0
                        for key in ('rise', 'transit', 'set', 'duration'):
                            assert isinstance(row[key], list) and len(row[key]) == 1, row
                    positions[cid] = (rows[0]['alt'], rows[0]['az'])
        assert positions[1] != positions[2], positions
        print('Satellites: real TLE propagation/pass calculation, 20 rows, malformed entry skipped, group filter, camera coordinates and both roles: PASS')


if __name__ == '__main__':
    run()
