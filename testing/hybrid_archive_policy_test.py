#!/usr/bin/env python3
"""Archive choices, explicit activation, real settings persistence and auth."""
from copy import deepcopy
import re
from hybrid_runtime_fixture import isolated_app, login_client

with isolated_app(multi_camera=True) as app:
    from indi_allsky.archive_policy import ArchivePolicy, DEFAULTS, validate_archive_config
    from indi_allsky.flask.models import IndiAllSkyDbConfigTable as Config
    assert ArchivePolicy.from_config({},True).mode=='legacy'
    for night in (False,True):
        for mode in ('legacy','processed','fits','both'):
            config={'IMAGE_ARCHIVE':{'NIGHT':mode,'DAY':mode},'IMAGE_SAVE_FITS':True,'IMAGE_EXPORT_RAW':True}
            policy=ArchivePolicy.from_config(config,night)
            for secondary in (False,True):
                assert policy.save_fits(config,secondary)==(mode in ('fits','both') or (mode=='legacy' and not secondary))
                assert policy.save_raw(config,secondary)==(mode=='legacy' and not secondary)
            if policy.every_frame:
                assert not policy.save_fits(dict(config,FOCUS_MODE=True),False)
    for invalid in (None,{}, {'NIGHT':'fits'}, {'NIGHT':'raw','DAY':'processed'}, {'NIGHT':'fits','DAY':True}):
        try: validate_archive_config(invalid)
        except ValueError: pass
        else: raise AssertionError('Invalid archive settings accepted')
    url='/indi-allsky/modern-admin/settings/storage-protection?camera_id=2&profile_id=test-profile-2'
    admin=login_client(app,1)
    page=admin.get(url)
    assert page.status_code==200 and 'Save archive formats' in page.text
    assert 'current archive still uses' in page.text
    with app.app_context():
        previous=deepcopy(Config.query.order_by(Config.id.desc()).first().data)
    def form(client):
        html=client.get(url).text
        return {key:re.search(r'name="'+key+r'" value="([^"]+)"',html)[1] for key in ('csrf_token','revision')}
    data=dict(form(admin),operation='archive',archive_night='invalid',archive_day='processed',archive_compressed='on')
    assert admin.post(url,data=data).status_code==400
    data['archive_night']='fits'
    response=admin.post(url,data=data)
    assert response.status_code==303 and 'camera_id=2' in response.location and 'profile_id=test-profile-2' in response.location
    with app.app_context():
        saved=Config.query.order_by(Config.id.desc()).first().data
        assert saved['IMAGE_ARCHIVE']==DEFAULTS and saved['IMAGE_SAVE_FITS_COMPRESSED'] is True
        for key,value in previous.items():
            if key!='IMAGE_SAVE_FITS_COMPRESSED': assert saved[key]==value,key
    assert admin.post(url,data=data).status_code==409
    reader=login_client(app,2)
    assert reader.post(url,data=dict(form(reader),operation='archive',archive_night='fits',archive_day='both')).status_code==403
    assert app.test_client().get(url).status_code==302
    assert admin.post(url,data={'operation':'archive','archive_night':'fits','archive_day':'processed'}).status_code==400
print('Archive policy: independent day/night formats, every-frame secondary FITS, legacy/raw preservation, Settings/CSRF/roles/revisions PASS')
