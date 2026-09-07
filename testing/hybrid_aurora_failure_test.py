#!/usr/bin/env python3
"""Provider failures retain prior readings and produce explicit partial outcomes."""
from unittest.mock import patch
from types import SimpleNamespace
from hybrid_runtime_fixture import isolated_app


def run():
    with isolated_app(multi_camera=True) as app:
        from indi_allsky.aurora import IndiAllskyAuroraUpdate, AuroraDataUpdateFailure
        from indi_allsky.flask import db
        from indi_allsky.flask.models import IndiAllSkyDbCameraTable
        with app.app_context():
            camera=db.session.get(IndiAllSkyDbCameraTable,2)
            camera.data={'AURORA_DATA_TS':123,'AURORA_MAG_BT':4,'unrelated':'preserve'};db.session.commit()
            provider=IndiAllskyAuroraUpdate({})
            with patch('indi_allsky.aurora.requests.get',return_value=SimpleNamespace(status_code=404)):
                for method in (provider.download_json,provider.download_txt):
                    try:method('https://example.invalid/test')
                    except AuroraDataUpdateFailure:pass
                    else:raise AssertionError('HTTP failure returned absent data as success')
                result=provider.update(camera)
            assert result['updated']==[] and len(result['failed'])==5
            assert camera.data['AURORA_DATA_TS']==123 and camera.data['AURORA_MAG_BT']==4
            assert camera.data['unrelated']=='preserve'
            assert all(value['state']=='unavailable' for value in camera.data['AURORA_COMPONENT_STATUS'].values())
            def bad_ovation(data, *args):
                data['AURORA_MAG_BT']=999
                raise TypeError('malformed data')
            def kp(data):data['AURORA_KPINDEX_CURRENT']=3
            with patch.object(provider,'update_ovation',side_effect=bad_ovation),patch.object(provider,'update_kpindex',side_effect=kp),patch.object(provider,'update_solar_wind_mag_data',side_effect=AuroraDataUpdateFailure),patch.object(provider,'update_solar_wind_plasma_data',side_effect=AuroraDataUpdateFailure),patch.object(provider,'update_hemi_power_data',side_effect=AuroraDataUpdateFailure):
                result=provider.update(camera)
            assert result['updated']==['kpindex'] and len(result['failed'])==4
            assert camera.data['AURORA_COMPONENT_STATUS']['kpindex']['state']=='available'
            assert camera.data['AURORA_KPINDEX_CURRENT']==3 and camera.data['AURORA_MAG_BT']==4
        print('Aurora: HTTP failure, missing/malformed components, partial success, retained readings and per-source status: PASS')


if __name__=='__main__':run()
