#!/usr/bin/env python3
"""Source-only archive dependencies survive ordinary and pressure cleanup."""
from datetime import datetime, timedelta
from pathlib import Path
from types import SimpleNamespace
from hybrid_runtime_fixture import isolated_app


with isolated_app(multi_camera=True) as app, app.app_context():
    from indi_allsky.flask import db, models
    from indi_allsky.source_retention import source_dependents
    from indi_allsky.storage_pressure import GIB
    from indi_allsky.storage_pressure_runtime import StoragePressureRuntime
    root = Path(app.config['INDI_ALLSKY_IMAGE_FOLDER'])
    now = datetime.now()
    Image, Fits = models.IndiAllSkyDbImageTable, models.IndiAllSkyDbFitsImageTable
    def pair(identity, camera, days, source_only=True):
        when = now-timedelta(days=days)
        path = root/f'source-{identity}.fit'
        path.write_bytes(b'scientific fixture')
        source = Fits(id=identity,filename=str(path),camera_id=camera,createDate=when,
                      dayDate=when.date(),night=True,exposure=1,gain=0)
        display = root/f'image-{identity}.jpg'
        if not source_only:
            display.write_bytes(b'legacy display')
        image = Image(id=identity,filename=str(display),camera_id=camera,createDate=when,
                      dayDate=when.date(),night=True,exposure=1,gain=0,adu=1,
                      data={'storage_format':'fits','source_fits_id':identity} if source_only else {})
        db.session.add_all([source,image]);db.session.commit()
        return image, source, path
    image, source, path = pair(100,1,5)
    other_image, other_source, other_path = pair(101,2,1)
    runtime = StoragePressureRuntime({},db.session,models,root,
                                    disk_usage=lambda path:SimpleNamespace(free=4*GIB))
    for delete in (source.deleteFile, source.deleteAsset):
        try: delete()
        except OSError: pass
        else: raise AssertionError('Live scientific dependency was deleted')
        assert path.read_bytes()==b'scientific fixture'
    Task, State = models.IndiAllSkyDbTaskQueueTable, models.TaskQueueState
    task = Task(queue=models.TaskQueueQueue.UPLOAD,state=State.QUEUED,
                data={'action':'upload','model':Image.__name__,'id':image.id})
    db.session.add(task);db.session.commit()
    assert runtime.run(now)['deleted']==0
    # A transfer of the original also protects its display record.
    task.data={'action':'upload','model':Fits.__name__,'id':source.id};db.session.commit()
    assert runtime.run(now)['deleted']==0
    task.data={'action':'upload','local_file':str(path)};db.session.commit()
    assert runtime.run(now)['deleted']==0
    task.setSuccess('fixture transfer finished')
    candidates=list(runtime.candidates(runtime.options.cutoff(now)))
    assert len(candidates)==1 and candidates[0].table is Image
    # A new transfer after selection is checked again before any mutation.
    task.state=State.RUNNING;task.data={'action':'upload','model':Fits.__name__,'id':source.id};db.session.commit()
    try: runtime.delete(candidates[0])
    except RuntimeError: db.session.rollback()
    else: raise AssertionError('Selected dependency deleted during transfer')
    task.setSuccess('fixture transfer finished')
    # Two bounded passes may be necessary: remove the display record first,
    # then its source becomes eligible under the existing FITS retention policy.
    first=runtime.run(now)
    second=runtime.run(now)
    assert first['deleted']+second['deleted']==2
    assert db.session.get(Image,100) is None and db.session.get(Fits,100) is None
    assert not path.exists() and other_path.exists()
    assert db.session.get(Image,101) is not None and db.session.get(Fits,101) is not None
    # Historical dual-format acquisitions retain independent cleanup semantics.
    legacy, legacy_source, legacy_path=pair(102,1,5,False)
    legacy_source.deleteAsset()
    assert not legacy_path.exists() and legacy.getFilesystemPath().exists()
    # Wrong camera/exposure cannot make an unrelated source dependent.
    unrelated=Fits(id=103,filename=str(root/'unrelated.fit'),camera_id=1,
                   createDate=other_source.createDate,dayDate=now.date(),night=True,exposure=1,gain=0)
    db.session.add(unrelated);db.session.commit()
    assert source_dependents(unrelated,db.session,models)==[]
    # Broken source references are kept for explicit repair, not purged blindly.
    other_image.data={'storage_format':'fits','source_fits_id':True};db.session.commit()
    assert source_dependents(other_source,db.session,models)==[other_image]
print('Source retention: original protection, pending upload scope, post-selection race, bounded cleanup, two cameras and legacy parity PASS')
