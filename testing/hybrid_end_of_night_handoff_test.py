#!/usr/bin/env python3
"""Real transaction/dispatch failure cases without any external upload."""
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock,patch
from hybrid_runtime_fixture import isolated_app


def run():
    with isolated_app(multi_camera=True) as app:
        from indi_allsky.flask import db
        from indi_allsky.flask.models import IndiAllSkyDbTaskQueueTable as Task, TaskQueueQueue as Queue, TaskQueueState as State
        from indi_allsky.end_of_night import handoff_end_of_night_upload as handoff
        with app.app_context():
            root=Path(app.config['INDI_ALLSKY_IMAGE_FOLDER'])
            def objects(label):
                file=root/label;file.write_text('{}')
                parent=Task(queue=Queue.VIDEO,state=State.RUNNING,data={'profile_id':'test-profile-2','kwargs':{'camera_id':2}})
                db.session.add(parent);db.session.commit()
                child=Task(queue=Queue.UPLOAD,state=State.QUEUED,data={'local_file':str(file),'camera_id':2,'profile_id':'test-profile-2'})
                return parent,child,file
            for committed in (False,True):
                parent,child,file=objects('persist-'+str(committed));parent_id=parent.id
                def commit():
                    if committed:db.session.commit()
                    raise RuntimeError('lost persistence acknowledgement')
                adapter=SimpleNamespace(add=db.session.add,flush=db.session.flush,commit=commit,rollback=db.session.rollback)
                dispatch=Mock()
                assert handoff(parent,child,session=adapter,dispatch=dispatch,camera_id=2) is False
                dispatch.assert_not_called();db.session.expire_all()
                saved=db.session.get(Task,parent_id)
                assert saved.state==State.FAILED and saved.data['end_of_night_upload']['status']=='persistence_uncertain'
                candidate=saved.data['end_of_night_upload']['candidate_task_id']
                assert (db.session.get(Task,candidate) is not None)==committed
                assert file.exists()
            parent,child,file=objects('dispatch');parent_id=parent.id
            def uncertain(child,**kwargs):
                # Simulate a worker consuming the request before caller sees failure.
                child.setSuccess('Delivered by simulated consumer')
                raise RuntimeError('queue acknowledgement lost')
            assert handoff(parent,child,session=db.session,dispatch=uncertain,camera_id=2) is False
            child_id=child.id;db.session.expire_all()
            assert db.session.get(Task,child_id).state==State.SUCCESS
            saved=db.session.get(Task,parent_id)
            assert saved.state==State.FAILED and saved.data['end_of_night_upload']['task_id']==child_id
            assert saved.data['end_of_night_upload']['status']=='dispatch_uncertain' and file.exists()
            parent,child,file=objects('success');parent_id=parent.id
            def dispatch(child,**kwargs):
                assert kwargs=={'camera_id':2}
                db.session.expire_all()
                assert db.session.get(Task,parent_id).data['end_of_night_upload']['task_id']==child.id
                assert db.session.get(Task,child.id).state==State.QUEUED
            assert handoff(parent,child,session=db.session,dispatch=dispatch,camera_id=2)
            db.session.expire_all();saved=db.session.get(Task,parent_id)
            assert saved.state==State.SUCCESS and saved.data['profile_id']=='test-profile-2'
            assert saved.data['end_of_night_upload']['status']=='queued' and file.exists()
            parent,child,file=objects('completion-write-failure');parent_id=parent.id
            real_commit=db.session.commit
            count=0
            def commit_once():
                nonlocal count
                count+=1
                if count==1:return real_commit()
                raise RuntimeError('completion commit failed')
            dispatch=Mock()
            with patch.object(db.session,'commit',side_effect=commit_once):
                assert handoff(parent,child,session=db.session,dispatch=dispatch,camera_id=2) is False
            dispatch.assert_called_once();db.session.expire_all()
            saved=db.session.get(Task,parent_id)
            assert saved.data['end_of_night_upload']['status']=='prepared'
            assert saved.data['end_of_night_upload']['task_id']==child.id
            assert db.session.get(Task,child.id).state==State.QUEUED and file.exists()
        print('EndOfNight handoff: atomic receipt, failed/lost commit, uncertain dispatch/completion, preserved consumed child and retained files: PASS')

if __name__=='__main__':run()
