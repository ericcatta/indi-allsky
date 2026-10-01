#!/usr/bin/env python3
"""Camera Info remains usable before driver/lens metadata is populated."""
import re
from hybrid_runtime_fixture import isolated_app, login_client


def run():
    with isolated_app(multi_camera=True) as app:
        from indi_allsky.flask import db
        from indi_allsky.flask.models import IndiAllSkyDbCameraTable, IndiAllSkyDbConfigTable
        endpoint = '/indi-allsky/modern-admin/cameras/info'
        fields = ('width', 'height', 'pixelSize', 'lensFocalLength', 'lensFocalRatio',
                  'lensImageCircle', 'bits', 'minGain', 'maxGain', 'minExposure', 'maxExposure')
        with app.app_context():
            camera = db.session.get(IndiAllSkyDbCameraTable, 1)
            original = {key: getattr(camera, key) for key in fields}
        for uid in (1, 2):
            client = login_client(app, uid)
            for missing in (fields, ('lensFocalRatio',), ('pixelSize',), ('width',)):
                with app.app_context():
                    camera = db.session.get(IndiAllSkyDbCameraTable, 1)
                    for key, value in original.items():
                        setattr(camera, key, None if key in missing else value)
                    camera.cfa = 99999  # A newer/unknown driver CFA identifier.
                    db.session.commit()
                response = client.get(endpoint + '?camera_id=1&profile_id=test-profile-1')
                assert response.status_code == 200, response.status_code
                rows = dict(re.findall(r'<dt>(.*?)</dt><dd>(.*?)</dd>', response.text))
                assert rows['CFA'] == 'Unknown'
                assert rows['Gain'] == ('— - —' if 'minGain' in missing else '0.00 - 100.00')
                assert 'None' not in ''.join(rows.values())
                if 'pixelSize' in missing:
                    assert rows['Sensor Size'] == '— x —'
                    assert rows['Field of View'] == '— x —'
                elif missing == ('lensFocalRatio',):
                    assert rows['Sensor Size'] == '1.3mm x 1.0mm'
                    assert '—' not in rows['Field of View']
                elif missing == ('width',):
                    assert rows['Sensor Size'] == '— x 1.0mm'
                other = client.get(endpoint + '?camera_id=2&profile_id=test-profile-2')
                assert other.status_code == 200 and '1.3mm x 1.0mm' in other.text
            assert client.get(endpoint + '?camera_id=1&profile_id=test-profile-2').status_code == 400
        assert app.test_client().get(endpoint).status_code == 302
        with app.app_context():
            assert db.session.query(IndiAllSkyDbConfigTable).count() == 1
        print('Camera Info: missing and partial metadata, unknown CFA, true zero gain, both roles and camera isolation PASS')


if __name__ == '__main__':
    run()
