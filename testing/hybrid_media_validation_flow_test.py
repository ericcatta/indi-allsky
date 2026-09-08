#!/usr/bin/env python3
"""Real isolated DB/files, legacy parity and deliberate remote-reference protection."""
from datetime import date, datetime, timedelta
import hashlib
from pathlib import Path
import re
from unittest.mock import patch
from hybrid_runtime_fixture import isolated_app, login_client


def run():
    with isolated_app() as app:
        from indi_allsky.flask import db, models
        from indi_allsky.flask.views import AjaxSystemInfoView
        from indi_allsky.modern_admin_media_validation import ModernAdminMediaValidation as Service
        from sqlalchemy import null, true, and_
        fixture = Path(__file__).parent / 'fixtures/legacy_validate_media_records.py'
        assert hashlib.sha256(fixture.read_bytes()).hexdigest() == '3cbcefbbab0ea9ce8feb1a77bd80a1a790e1d3729b994e467d7e3b34e80ee9a1'
        namespace = dict(vars(models), db=db, app=app, sa_null=null, sa_true=true, and_=and_)
        exec(compile(fixture.read_text(), str(fixture), 'exec'), namespace)
        kinds = {suffix: getattr(models, 'IndiAllSkyDb'+suffix+'Table') for suffix, *_ in Service.families}
        root = Path(app.config['INDI_ALLSKY_IMAGE_FOLDER'])
        def seed(remote=False):
            for suffix, model in kinds.items():
                model.query.delete()
                columns = set(model.__table__.columns.keys())
                for camera in (1, 2):
                    for case in (1, 2, 3, 4, 5):
                        if case == 3 and 's3_key' not in columns: continue
                        if case == 4 and (not remote or 'remote_url' not in columns): continue
                        if case == 5 and 'success' not in columns: continue
                        path = root / f'{suffix}-{camera}-{case}.dat'
                        if case == 1: path.write_bytes(b'preserve actual file bytes')
                        fields = dict(id=camera*10+case, filename=str(path), camera_id=camera,
                            dayDate=date(2026,1,1), createDate=datetime(2026,1,1)+timedelta(seconds=case),
                            exposure=1, gain=1, adu=1, bitdepth=16, night=True, success=case!=5,
                            targetDate=datetime(2026,1,1), startDate=datetime(2026,1,1), endDate=datetime(2026,1,1),
                            note='test', s3_key='stored' if case==3 else None,
                            remote_url='https://example.invalid/media' if case==4 else None)
                        db.session.add(model(**{k:v for k,v in fields.items() if k in columns}))
            db.session.commit()
        def remaining():
            return {suffix:[row.id for row in model.query.order_by(model.id)] for suffix,model in kinds.items()}
        with app.app_context():
            seed(); before_files={str(p):p.read_bytes() for p in root.iterdir() if p.is_file()}
            legacy_messages = namespace['validateDbEntries'](None)
            legacy_remaining = remaining()
            seed()
            assert Service(models,db.session).run() == legacy_messages
            assert remaining() == legacy_remaining
            assert {str(p):p.read_bytes() for p in root.iterdir() if p.is_file()} == before_files
            # Documented correction: valid remote references are preserved even
            # when no local file exists. S3 and failed output policy stay intact.
            seed(remote=True)
            Service(models,db.session).run()
            for suffix,model in kinds.items():
                if 'remote_url' in model.__table__.columns:
                    assert db.session.get(model,14) and db.session.get(model,24)
                assert not db.session.get(model,12) and not db.session.get(model,22)
            seed(remote=True); expected=remaining()
            with patch.object(models.IndiAllSkyDbBadPixelMapTable,'validateFile',side_effect=OSError('unreadable storage')):
                try: Service(models,db.session).run()
                except OSError: pass
                else: raise AssertionError('Filesystem failure swallowed')
            assert remaining() == expected
            with patch.object(db.session,'commit',side_effect=RuntimeError('database failure')):
                try: Service(models,db.session).run()
                except RuntimeError: pass
                else: raise AssertionError('Commit failure swallowed')
            assert remaining() == expected
        admin, ordinary, anonymous = login_client(app,1),login_client(app,2),app.test_client()
        def headers(client,page='/indi-allsky/modern-admin/account'):
            return {'X-CSRFToken':re.search(r'name="csrf_token"[^>]*value="([^"]+)"',client.get(page).text)[1]}
        auth,denied,anon=headers(admin),headers(ordinary),headers(anonymous,'/indi-allsky/login')
        payload=dict(CAMERA_ID=2,SERVICE_HIDDEN='system',COMMAND_HIDDEN='validate_db')
        url='/indi-allsky/ajax/system'
        with patch.object(AjaxSystemInfoView,'validateDbEntries',side_effect=AssertionError('Unexpected effect')) as effect:
            assert admin.post(url,json=payload).status_code == 400
            assert ordinary.post(url,json=payload,headers=denied).status_code == 400
            assert anonymous.post(url,json=payload,headers=anon).status_code == 302
            effect.assert_not_called()
        response=admin.post(url,json=payload,headers=auth)
        assert response.status_code==200 and 'Removed' in response.json['success-message']
        with app.app_context():
            for model in kinds.values():
                assert not db.session.get(model,12) and not db.session.get(model,22)
            seed(remote=True)
        with patch.object(models.IndiAllSkyDbBadPixelMapTable,'validateFile',side_effect=OSError('private path')):
            response=admin.post(url,json=payload,headers=auth)
            assert response.status_code==503 and 'private path' not in response.text
        for client,writable in ((admin,True),(ordinary,False)):
            response=client.get('/indi-allsky/modern-admin/system/info')
            assert response.status_code==200
            form=response.text.split('class="system-validation-form"',1)[1].split('</form>',1)[0]
            assert ('<fieldset disabled>' in form) != writable
            assert 'all cameras' in form and 'storage availability' in form
        print('Media validation: 13 families, legacy parity, both cameras, real file preservation, S3/remote/failed outputs, scan/commit rollback, roles/CSRF and UI: PASS')

if __name__=='__main__':run()
