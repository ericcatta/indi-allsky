#!/usr/bin/env python3
"""Actual queue receipts and expiration effects confined to synthetic DB/files."""
import ast
from datetime import date, datetime, timedelta
import logging
from pathlib import Path
import re
from unittest.mock import patch
from hybrid_runtime_fixture import isolated_app, login_client


def run():
    with isolated_app(multi_camera=True) as app:
        from indi_allsky.flask import db, models
        from indi_allsky.flask.views import AjaxSystemInfoView
        from indi_allsky.modern_admin_runtime_effects import ModernAdminTaskEnqueueEffectAdapter
        from indi_allsky.modern_admin_queued_maintenance import ModernAdminQueuedMaintenancePlanner, retention_policy_token
        from indi_allsky.modern_admin_media_cleanup import MediaCleanupIncomplete, flush_media_batches, prune_empty_camera_directories
        Task, State, Queue = models.IndiAllSkyDbTaskQueueTable, models.TaskQueueState, models.TaskQueueQueue
        planner=ModernAdminQueuedMaintenancePlanner()
        for value in (None,True,False,0,-1,1.5,'bad','2.5'):
            try: planner.plan('expire_data',value)
            except ValueError: pass
            else: raise AssertionError(value)
        assert planner.plan('expire_data','2')['jobdata']=={'action':'expireData','kwargs':{'camera_id':2}}
        try: planner.plan('arbitrary',2)
        except ValueError: pass
        else: raise AssertionError('Unknown command accepted')
        admin,user,anonymous=login_client(app,1),login_client(app,2),app.test_client()
        def headers(client,page='/indi-allsky/modern-admin/account'):
            return {'X-CSRFToken':re.search(r'name="csrf_token"[^>]*value="([^"]+)"',client.get(page).text)[1]}
        auth,denied,anon=headers(admin),headers(user),headers(anonymous,'/indi-allsky/login')
        endpoint='/indi-allsky/ajax/system'
        for command,unit in [('hup',app.config['ALLSKY_SERVICE_NAME']),('expire_data','system')]:
            payload=dict(CAMERA_ID=2,SERVICE_HIDDEN=unit,COMMAND_HIDDEN=command)
            with patch.object(AjaxSystemInfoView,'queue_maintenance_command',side_effect=AssertionError('Unexpected effect')) as effect:
                assert admin.post(endpoint,json=payload).status_code==400
                assert user.post(endpoint,json=payload,headers=denied).status_code==400
                assert anonymous.post(endpoint,json=payload,headers=anon).status_code==302
                effect.assert_not_called()
            for invalid in ('bad', [], 999999):
                if command == 'hup' and invalid == 999999: continue
                rejected=admin.post(endpoint,json=dict(payload,CAMERA_ID=invalid),headers=auth)
                assert rejected.status_code==400,rejected.text
            response=admin.post(endpoint,json=payload,headers=auth)
            assert response.status_code==200,response.text
            ident=int(response.headers['X-Hybrid-Task-Id'])
            plan=planner.plan(command,2)
            assert response.json=={'success-message':plan['message']}
            with app.app_context():
                task=db.session.get(Task,ident)
                assert task.data==plan['jobdata'] and task.queue==Queue[plan['queue']]
                assert task.state==State.MANUAL and task.priority==100
            assert admin.get('/indi-allsky/modern-admin/tasks/'+str(ident)).status_code==200
            if command == 'expire_data':
                stale=admin.post(endpoint,json=dict(payload,RETENTION_TOKEN='0'*64),headers=auth)
                assert stale.status_code==409
                with app.app_context(): token=retention_policy_token(db.session.get(models.IndiAllSkyDbConfigTable,1).data)
                guarded=admin.post(endpoint,json=dict(payload,RETENTION_TOKEN=token),headers=auth)
                assert guarded.status_code==200
                with app.app_context():
                    guarded_task=db.session.get(Task,int(guarded.headers['X-Hybrid-Task-Id']))
                    assert guarded_task.data['kwargs']['retention_token']==token
            with patch.object(ModernAdminTaskEnqueueEffectAdapter,'enqueue_from_plan',side_effect=RuntimeError('private queue failure')):
                response=admin.post(endpoint,json=payload,headers=auth)
                assert response.status_code==503 and 'private queue' not in response.text
        for client,writable in ((admin,True),(user,False)):
            response=client.get('/indi-allsky/modern-admin/system/info?camera_id=2&profile_id=test-profile-2')
            assert response.status_code==200
            for kind in ('reload','expire'):
                form=response.text.split('class="system-'+kind+'-form"',1)[1].split('</form>',1)[0]
                assert ('<fieldset disabled>' in form) != writable
            assert 'retention' in response.text and 'camera 2' in response.text

        assert admin.get('/indi-allsky/modern-admin/system/info?camera_id=1&profile_id=test-profile-2').status_code==400
        assert admin.get('/indi-allsky/modern-admin/system/info?camera_id=999999').status_code==404
        assert 'camera 2' in admin.get('/indi-allsky/modern-admin/system/info?profile_id=test-profile-2').text

        # Execute the production worker methods with real isolated models/files.
        tree=ast.parse((Path(__file__).resolve().parents[1]/'indi_allsky/video.py').read_text())
        names={'expireData','_deleteAssets'}
        cls=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='VideoWorker')
        nodes=[n for n in cls.body if isinstance(n,ast.FunctionDef) and n.name in names]
        namespace=dict(vars(models),db=db,datetime=datetime,timedelta=timedelta,
                       logger=logging.getLogger('expiry-test'),MediaCleanupIncomplete=MediaCleanupIncomplete,
                       flush_media_batches=flush_media_batches,prune_empty_camera_directories=prune_empty_camera_directories,retention_policy_token=retention_policy_token)
        exec(compile(ast.Module(body=nodes,type_ignores=[]),'actual-worker','exec'),namespace)
        Worker=type('Worker',(),{name:namespace[name] for name in names});worker=Worker()
        worker.image_dir=Path(app.config['INDI_ALLSKY_IMAGE_FOLDER'])
        worker.config=dict(IMAGE_EXPIRE_DAYS=10,IMAGE_RAW_EXPIRE_DAYS=20,IMAGE_FITS_EXPIRE_DAYS=30,TIMELAPSE_EXPIRE_DAYS=40)
        family_days={'Image':10,'PanoramaImage':10,'RawImage':20,'FitsImage':30,'Video':40,'MiniVideo':40,'Keogram':40,'StarTrails':40,'StarTrailsVideo':40,'PanoramaVideo':40}
        families={name:getattr(models,'IndiAllSkyDb'+name+'Table') for name in family_days}
        def seed():
            for name,model in families.items():
                model.query.delete()
                for ident,camera,age in ((11,1,family_days[name]+1),(21,2,family_days[name]+1),(22,2,family_days[name]),(23,2,0),(24,2,family_days[name]+2)):
                    folder=worker.image_dir/('ccd_test-camera-'+str(camera));folder.mkdir(exist_ok=True)
                    path=folder/(name+'-'+str(ident)+'.dat');path.write_bytes(b'dedicated expiration fixture')
                    values=dict(id=ident,camera_id=camera,filename=str(path),dayDate=date.today()-timedelta(days=age),
                                createDate=datetime.now()-timedelta(days=age),night=True,exposure=1,gain=1,adu=1,
                                success=True,targetDate=datetime.now(),startDate=datetime.now(),endDate=datetime.now(),note='test')
                    columns=set(model.__table__.columns.keys())
                    db.session.add(model(**{k:v for k,v in values.items() if k in columns}))
            db.session.commit()
        def task():
            value=Task(queue=Queue.VIDEO,state=State.QUEUED,data={'action':'expireData','kwargs':{'camera_id':2}})
            db.session.add(value);db.session.commit();return value
        with app.app_context():
            seed()
            mismatch=task();worker.expireData(mismatch,camera_id=2,retention_token='0'*64)
            assert mismatch.state==State.FAILED
            for model in families.values(): assert model.query.count()==5
            for camera in (1,2): (worker.image_dir/f'ccd_test-camera-{camera}'/'empty').mkdir(exist_ok=True)
            outside=worker.image_dir/'outside';outside.mkdir();(outside/'empty').mkdir()
            link=worker.image_dir/'ccd_test-camera-2'/'external-link';link.symlink_to(outside,target_is_directory=True)
            value=task();worker.expireData(value,camera_id=2,retention_token=retention_policy_token(worker.config))
            assert value.state==State.SUCCESS and value.result=='Expired 20 assets'
            for name,model in families.items():
                for removed in (21,24): assert not (worker.image_dir/'ccd_test-camera-2'/(name+'-'+str(removed)+'.dat')).exists()
                assert [v.id for v in model.query.order_by(model.id)]==[11,22,23]
                for entry in model.query: assert Path(entry.filename).read_bytes()==b'dedicated expiration fixture'
            assert (worker.image_dir/'ccd_test-camera-1'/'empty').exists()
            assert not (worker.image_dir/'ccd_test-camera-2'/'empty').exists()
            assert (outside/'empty').exists() and link.is_symlink()
            empty=task();worker.expireData(empty,camera_id=2);assert empty.result=='Expired 0 assets'
            seed();Image=models.IndiAllSkyDbImageTable;original=Image.deleteAsset;attempts=[]
            def remove(entry):
                attempts.append(entry.id)
                if entry.id==21:
                    if attempts.count(21)>1: raise AssertionError('Infinite failed-batch retry')
                    raise PermissionError('Synthetic protected file')
                return original(entry)
            failed=task()
            with patch.object(Image,'deleteAsset',remove): worker.expireData(failed,camera_id=2)
            assert failed.state==State.FAILED and sorted(attempts)==[21,24]
            assert failed.data['cleanup_result']=={'camera_id':2,'deleted_count':1,'failed_count':1}
            assert db.session.get(Image,21) and db.session.get(Image,11) and not db.session.get(Image,24)
            retry=task();worker.expireData(retry,camera_id=2);assert retry.state==State.SUCCESS and retry.result=='Expired 19 assets'
            seed();directory_failure=task()
            namespace['prune_empty_camera_directories']=lambda *args:1
            worker.expireData(directory_failure,camera_id=2)
            assert directory_failure.state==State.FAILED and directory_failure.data['cleanup_result']['directory_errors']==1
            failed_id=failed.id
        for metadata in (None, [], 'invalid', {'camera_sqm_raw_mag':18.5}):
            with app.app_context():
                latest=models.IndiAllSkyDbImageTable.query.filter_by(camera_id=2).order_by(models.IndiAllSkyDbImageTable.createDate.desc()).first()
                latest.data=metadata;db.session.commit()
            page=admin.get('/indi-allsky/modern-admin/tasks/'+str(failed_id))
            assert page.status_code==200 and 'Cleanup stopped' in page.text

        print('Queued maintenance: roles/CSRF, exact plans/receipts, queue failures, UI gates; actual expiration of 10 families, date boundaries, camera isolation, symlinks, partial failure, retry and directory errors: PASS')

if __name__=='__main__':run()
