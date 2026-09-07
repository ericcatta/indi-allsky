#!/usr/bin/env python3
"""Real ephemeris response and Hybrid detail contract, without Classic imports."""
import re
from hybrid_runtime_fixture import isolated_app, login_client


def run():
    with isolated_app(multi_camera=True) as app:
        for uid in (1, 2):
            client = login_client(app, uid)
            for cid in (1, 2):
                page = client.get('/indi-allsky/modern-admin/observatory/astropanel', query_string={'camera_id':cid})
                assert page.status_code == 200
                assert 'modern_admin/astropanel.js' in page.text
                assert 'id="astropanel-refresh"' in page.text
                response = client.get('/indi-allsky/ajax/astropanel', query_string={'camera_id':cid})
                assert response.status_code == 200, response.text[:500]
                data = response.json
                for key in re.findall('data-astro-field="([^"]+)"', page.text):
                    assert key in data and isinstance(data[key], (int, float, str)), key
                assert data['satellite_list'] == []
                assert isinstance(data['polaris_hour_angle'], (int,float))
                for planet in ('mercury','venus','mars','jupiter','saturn','uranus','neptune'):
                    for suffix in ('rise','transit','set','alt','az'):
                        assert planet+'_'+suffix in data
        assert app.test_client().get('/indi-allsky/modern-admin/observatory/astropanel').status_code == 302
        print('Astropanel: actual ephemerides, all new detail fields, both cameras/roles, no satellites and Classic disabled: PASS')


if __name__ == '__main__':
    run()
