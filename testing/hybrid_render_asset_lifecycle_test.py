#!/usr/bin/env python3
"""Actual collection, accounting, lock contention and complete reference scans."""
from datetime import datetime
import os
from pathlib import Path
import tempfile
from hybrid_runtime_fixture import isolated_app

with isolated_app(multi_camera=True) as app, app.app_context():
    import numpy as np
    from astropy.io import fits
    from indi_allsky.flask import db, models
    from indi_allsky.render_assets import RenderAssetStore
    from indi_allsky.render_asset_lifecycle import (
        archive_asset_lock, archive_references, asset_usage, collect_assets)
    root=Path(app.config['INDI_ALLSKY_IMAGE_FOLDER'])
    asset_root=root/'.render-assets'
    store=RenderAssetStore(asset_root)
    live=store.put(pixels=np.zeros((4,4),dtype=np.uint8))
    dead=store.put(pixels=np.ones((4,4),dtype=np.uint8))
    young=store.put(pixels=np.full((4,4),2,dtype=np.uint8))
    paths={key:asset_root/(key+'.npz') for key in (live,dead,young)}
    now=1000000
    for key in (live,dead): os.utime(paths[key],(now-100000,now-100000))
    os.utime(paths[young],(now,now))
    unknown=asset_root/'notes.txt';unknown.write_text('Keep unrelated files')
    outside=root/'outside';outside.write_text('Keep symlink target')
    link=asset_root/('f'*64+'.npz');link.symlink_to(outside)
    when=datetime.now()
    image=models.IndiAllSkyDbImageTable(filename=str(root/'display.jpg'),camera_id=1,
        createDate=when,dayDate=when.date(),exposure=1,gain=0,adu=1,night=True,
        data={'render_presentation':{'nested':[{'asset':live}]}})
    db.session.add(image);db.session.commit()
    references=lambda:archive_references(db.session,models)
    assert live in set(references())
    total,recent=asset_usage(asset_root,since=now-1)
    assert total==sum(p.stat().st_size for p in paths.values())
    assert recent==paths[young].stat().st_size
    with archive_asset_lock(asset_root):
        result=collect_assets(asset_root,references,now=now)
        assert result['status']=='busy' and paths[dead].exists()
    def broken_scan():
        yield live
        raise OSError('Synthetic incomplete database scan')
    try: collect_assets(asset_root,broken_scan,now=now)
    except OSError: pass
    else: raise AssertionError('Incomplete reference scan accepted')
    assert all(path.exists() for path in paths.values())
    abandoned=asset_root/'.hybrid-asset-crashed.part'
    abandoned.write_bytes(b'partial archive write')
    os.utime(abandoned,(now-100000,now-100000))
    result=collect_assets(asset_root,references,now=now)
    assert result['deleted']==2 and result['bytes']>0 and not abandoned.exists()
    assert paths[live].exists() and paths[young].exists() and not paths[dead].exists()
    assert unknown.exists() and link.is_symlink() and outside.read_text()=='Keep symlink target'
    # A scientific record alone protects the asset after its display row is gone.
    source=root/'archived.fit';fits.PrimaryHDU(np.ones((4,4),np.uint16)).writeto(source)
    scientific=models.IndiAllSkyDbFitsImageTable(filename=str(source),camera_id=2,
        createDate=when,dayDate=when.date(),exposure=1,gain=0,night=True,
        data={'render_source':{'basis':{'prepared_asset':live}}})
    db.session.add(scientific);db.session.delete(image);db.session.commit()
    assert collect_assets(asset_root,references,now=now)['deleted']==0
    db.session.delete(scientific);db.session.commit()
    assert collect_assets(asset_root,references,now=now)['deleted']==1
    assert not paths[live].exists() and paths[young].exists()
    # A missing/corrupt imported FITS cannot silently produce a partial live set.
    scientific=models.IndiAllSkyDbFitsImageTable(filename=str(source),camera_id=2,
        createDate=when,dayDate=when.date(),exposure=1,gain=0,night=True,data={})
    db.session.add(scientific);db.session.commit()
    assert list(references())==[]  # Historical FITS without rendering context.
    source.write_bytes(b'corrupt FITS fixture')
    try: collect_assets(asset_root,references,now=now+200000)
    except (OSError,ValueError): pass
    else: raise AssertionError('Unreadable source permitted reclamation')
    assert paths[young].exists()
print('Rendering assets: reference traversal, FITS-only references, complete scans, active lease, grace period, exact accounting, symlink isolation PASS')
