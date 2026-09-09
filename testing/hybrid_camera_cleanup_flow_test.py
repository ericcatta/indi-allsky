#!/usr/bin/env python3
"""Legacy query parity and actual deletion across all supported media families."""
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import patch
from sqlalchemy.sql.expression import false as sa_false
from hybrid_runtime_fixture import isolated_app, login_client
from hybrid_account_input_test import csrf


def run():
    with isolated_app(multi_camera=True) as app:
        from indi_allsky.flask import db, models
        from indi_allsky.flask.base_views import BaseView
        from indi_allsky.modern_admin_camera_cleanup import ACTION_FAMILIES, build_cleanup_queries
        names = ('Image','FitsImage','RawImage','PanoramaImage','Video','MiniVideo','Keogram','StarTrails','StarTrailsVideo','PanoramaVideo')
        tables = {name:getattr(models,'IndiAllSkyDb'+name+'Table') for name in ('Camera',)+names}
        fixed = datetime(2026,1,2,12)
        class Clock:
            @staticmethod
            def now(): return fixed
        source = Path(__file__).parent/'fixtures/legacy_camera_cleanup_queries.py'
        namespace = {model.__name__:model for model in tables.values()}
        namespace.update(datetime=Clock,timedelta=timedelta,sa_false=sa_false,flush_media_batches=lambda queries,effect:queries)
        exec(compile(source.read_text(),str(source),'exec'),namespace)
        old = namespace['LegacyCleanup']();old._deleteAssets=None
        methods = dict(zip(ACTION_FAMILIES,('flushImages','flush16MinutesImages','flushTimelapses','flushDaytime')))
        root=Path(app.config['INDI_ALLSKY_IMAGE_FOLDER'])
        def seed():
            for name in names:
                model=tables[name];model.query.delete()
                for ident,camera,minutes,night in ((11,1,0,False),(21,2,20,True),(22,2,15,True),(23,2,16,False),(24,2,0,False),(25,2,17,False)):
                    path=root/(name+str(ident)+'.dat');path.write_bytes(b'cleanup fixture')
                    values=dict(id=ident,camera_id=camera,filename=str(path),dayDate=fixed.date(),createDate=fixed-timedelta(minutes=minutes),night=night,exposure=1,gain=1,adu=1,success=True,targetDate=fixed,startDate=fixed,endDate=fixed,note='test',data={})
                    db.session.add(model(**{k:v for k,v in values.items() if k in model.__table__.columns.keys()}))
            db.session.commit()
        admin,user=login_client(app,1),login_client(app,2)
        headers={'X-CSRFToken':csrf(admin,'/indi-allsky/modern-admin/account')}
        for command,method in methods.items():
            with app.app_context():
                seed()
                legacy=getattr(old,method)(2)
                actual=build_cleanup_queries(command,2,tables,fixed)
                def signature(queries):
                    return [(table.__tablename__,str(query.statement.compile(compile_kwargs={'literal_binds':True})),[r.id for r in query]) for query,table in queries]
                assert signature(actual)==signature(legacy),command
                expected={table.__tablename__:set(r.id for r in query) for query,table in actual}
            payload=dict(CAMERA_ID=2,SERVICE_HIDDEN='system',COMMAND_HIDDEN=command)
            for invalid in (0,-1,True,2.5,999999):
                rejected=admin.post('/indi-allsky/ajax/system',json=dict(payload,CAMERA_ID=invalid),headers=headers)
                assert rejected.status_code==400
            with patch('indi_allsky.flask.views.datetime',Clock):
                response=admin.post('/indi-allsky/ajax/system',json=payload,headers=headers)
            assert response.status_code==200,response.text
            assert response.json['success-message'].startswith(str(sum(map(len,expected.values())))+' ')
            with app.app_context():
                for name in names:
                    table=tables[name];deleted=expected.get(table.__tablename__,set())
                    assert {r.id for r in table.query}=={11,21,22,23,24,25}-deleted
                    for ident in (11,21,22,23,24,25):
                        path=root/(name+str(ident)+'.dat')
                        assert path.exists()==(ident not in deleted)
                        if path.exists():assert path.read_bytes()==b'cleanup fixture'
        for client,writable in ((admin,True),(user,False)):
            with patch.object(BaseView,'verify_admin_network',return_value=True):
                page=client.get('/indi-allsky/modern-admin/system/info?camera_id=2&profile_id=test-profile-2')
            assert page.status_code==200
            forms=page.text.split('class="system-cleanup-form"')[1:]
            assert len(forms)==4
            for form in forms:
                form=form.split('</form>',1)[0]
                assert ('<fieldset disabled>' in form)!=writable
                assert 'camera 2' in form and 'permanent deletion' in form
        with patch.object(BaseView,'verify_admin_network',return_value=False):
            page=admin.get('/indi-allsky/modern-admin/system/info?camera_id=2')
        for form in page.text.split('class="system-cleanup-form"')[1:]:assert '<fieldset disabled>' in form.split('</form>',1)[0]
        print('Cleanup: frozen legacy SQL/order/IDs, 10-family real file deletion, 16-minute boundary, day/night and camera isolation, invalid camera and UI gates: PASS')

if __name__=='__main__':run()
