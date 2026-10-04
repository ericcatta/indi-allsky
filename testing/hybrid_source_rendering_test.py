#!/usr/bin/env python3
"""Full FITS-to-display replay, including unusual source/stack contexts."""
from copy import deepcopy
from datetime import datetime
from multiprocessing import Array
from pathlib import Path
from unittest.mock import patch
import hashlib
import json
import numpy as np
from astropy.io import fits
from hybrid_runtime_fixture import isolated_app, login_client

with isolated_app(multi_camera=True) as app:
    with app.app_context():
        from indi_allsky.config import IndiAllSkyConfigBase
        from indi_allsky.processing import ImageProcessor
        from indi_allsky.flask.models import IndiAllSkyDbCameraTable
        from indi_allsky.source_rendering import snapshot_source_basis, snapshot_source_recipe, render_source
        from indi_allsky.image_awb import apply_rgb_gains
        from indi_allsky.image_rendering import render_tone, render_geometry_and_color, render_presentation
        from indi_allsky.image_presentation import snapshot_presentation
        from indi_allsky.render_assets import RenderAssetStore
        root = Path(app.config['INDI_ALLSKY_IMAGE_FOLDER'])
        assets = RenderAssetStore(root/'.render-assets')
        # Includes uint8 RGB and 16-bit CFA, calibrated/pre-dark and actual stack data.
        for cid, dtype, channels, maximum in ((1,np.uint8,3,255),(2,np.uint16,1,4095),(2,np.float32,1,4095)):
            camera = IndiAllSkyDbCameraTable.query.filter_by(id=cid).one()
            for mode in ('direct','pre_calibration','stack','focus'):
                for night in (False,True):
                    for stretch in ('mode1_stddev_cutoff','mode2_mtf','mode2_mtf_x2','mode3_adaptive_mtf'):
                        c = deepcopy(IndiAllSkyConfigBase().base_config)
                        c.update(IMAGE_FOLDER=str(root),IMAGE_LABEL_SYSTEM='opencv',
                            FOCUS_MODE=mode=='focus',IMAGE_SAVE_FITS_PRE_DARK=mode=='pre_calibration',
                            IMAGE_STACK_COUNT=2 if mode=='stack' else 1, IMAGE_STACK_DAY=True,
                            IMAGE_STACK_ALIGN=False,IMAGE_STACK_METHOD='average',
                            USE_NIGHT_COLOR=False,IMAGE_ROTATE='ROTATE_90_CLOCKWISE',
                            IMAGE_SCALE=80,CCD_BIT_DEPTH=8 if dtype==np.uint8 else 12,
                            GAMMA_CORRECTION=1.2,GAMMA_CORRECTION_DAY=0.9,
                            SCNR_ALGORITHM='average_neutral', SCNR_ALGORITHM_DAY='',
                            IMAGE_DENOISE='gaussian_blur',IMAGE_DENOISE_DAY='gaussian_blur',
                            CONTRAST_ENHANCE_16BIT=night,DAYTIME_CONTRAST_ENHANCE=True,
                            NIGHT_CONTRAST_ENHANCE=True,DETECT_DRAW=True,
                            CFA_PATTERN='RGGB' if channels==1 else '',
                            FILETRANSFER={'PASSWORD':'never-archive-this-secret'})
                        c['ORB_PROPERTIES']['MODE']='off'
                        for key in ('MOON_OVERLAY','LIGHTGRAPH_OVERLAY','IMAGE_OVERLAY','CARDINAL_DIRS'):
                            c[key]['ENABLE']=False
                        c['IMAGE_STRETCH'].update(CLASSNAME=stretch,DAYTIME=True,MOONMODE=True,
                            MODE3_MIDTONES=0.33,MODE3_BLACK_CLIP=-2.0)
                        c['IMAGE_CIRCLE_MASK'].update(ENABLE=True,DIAMETER=110,BLUR=3)
                        c['IMAGE_BORDER'].update(TOP=2,BOTTOM=3,LEFT=4,RIGHT=5)
                        p=ImageProcessor(c,Array('f',[46,8,200,0,0]),Array('f',[0]),Array('i',[1]),
                            Array('f',[0]*60),Array('f',[0]*110),Array('i',[int(night),0]),Array('f',[0]*3))
                        p.post_init(detection_mask={1:np.full((128,192),255,np.uint8)})
                        p._ia_denoise.star_mask_time_override=night
                        source=root/f'source-{cid}.fit'
                        shape=(3,128,192) if channels==3 else (128,192)
                        for frame in range(2 if mode=='stack' else 1):
                            data=(np.arange(np.prod(shape)).reshape(shape)*13%(maximum-40)+20+frame).astype(dtype)
                            fits.PrimaryHDU(data).writeto(source,overwrite=True)
                            ref=p.add(source,1.0,0.0,1,datetime(2020,1,1,12,0,frame),0.0,camera)
                            if mode=='pre_calibration':
                                # Saved FITS retains these raw values; actual calibration
                                # result is distinct and must be preserved separately.
                                ref.hdulist[0].data=np.maximum(ref.hdulist[0].data.astype(np.int32)-10,0).astype(dtype)
                            p.debayer()
                        p.stack()
                        if mode=='direct' and night:
                            # A running processor can carry LUTs from previous
                            # frames. Replay must preserve those effective tables.
                            p._gamma_lut=np.arange(256,dtype=np.uint8)
                            c['WBB_MTF_MIDTONES']=0.6
                            p._wbb_mtf_lut=np.arange(256,dtype=np.uint8)
                            if hasattr(p._stretch_o,'_mtf_lut'):
                                p._stretch_o._mtf_lut=np.arange(1<<p.max_bit_depth,
                                    dtype=np.uint8 if p.max_bit_depth==8 else np.uint16)
                        original=source.read_bytes()
                        basis=snapshot_source_basis(p,{'path':str(source),'db_id':cid},assets)
                        assert bool(basis['prepared_asset'])==(mode in ('pre_calibration','stack'))
                        p.render_awb_gains=[1.03,0.94]
                        if p.image.ndim==3:
                            p.image=apply_rgb_gains(p.image,*p.render_awb_gains)
                        else:
                            p.render_awb_gains=None
                        p.libcamera_raw=True
                        basis['libcamera_raw']=True
                        ccm=[[1.01,0,0],[0,0.98,0],[0,0,1.02]] if p.image.ndim==3 else None
                        if ccm:p.apply_color_correction_matrix(ccm)
                        render_tone(p,c,p.night_av)
                        ref.lines=[[[20,20,60,50]]];ref.stars=[[80,70]]
                        if not p.focus_mode:
                            p._lineDetect._drawLines(p.image,ref.lines)
                            p._stars_detect._drawCircles(p.image,ref.stars)
                            p.drawDetections()
                        render_geometry_and_color(p,c,p.night_av);p.colormap();p.apply_image_circle_mask(1)
                        render_presentation(p,1)
                        presentation=snapshot_presentation(p,1,assets)
                        p.label_image(label_text='Saved exposure')
                        recipe=snapshot_source_recipe(p,basis,presentation,assets,ccm=ccm)
                        assert 'never-archive' not in json.dumps(recipe)
                        c['GAMMA_CORRECTION']=2.0 # replay must not use current settings
                        with patch('indi_allsky.processing.ImageProcessor.calibrate',side_effect=AssertionError('Live calibration')), \
                             patch('indi_allsky.processing.ImageProcessor.update_astrometric_data',side_effect=AssertionError('Live astronomy')):
                            output=render_source(source,recipe,assets,camera_id=cid,source_id=cid)
                        np.testing.assert_array_equal(output,p.image)
                        assert source.read_bytes()==original
        # Regression: valid 12-bit input may gain luminance in denoise. Its
        # intermediate output must remain in the 4096-entry stretch LUT domain.
        p.focus_mode=False
        p.max_bit_depth=12
        p.image=np.full((8,8,3),4090,np.uint16)
        bounded=p._denoise(lambda image: np.full_like(image,4200))
        assert bounded.dtype==np.uint16 and bounded.max()==4095
        np.testing.assert_array_equal(p._denoise(lambda image:image.copy()),p.image)
        # Identity/content guards protect all source readers, even checkpoint recipes.
        for camera_id,source_id in ((999,cid),(cid,999)):
            try:render_source(source,recipe,assets,camera_id=camera_id,source_id=source_id)
            except ValueError:pass
            else:raise AssertionError('Wrong source identity accepted')
        source.write_bytes(original+b'changed')
        try:render_source(source,recipe,assets,camera_id=cid,source_id=cid)
        except ValueError:pass
        else:raise AssertionError('Modified source accepted')
        source.write_bytes(original)
        # Gzip is a storage representation of the same scientific exposure.
        import gzip
        compressed=source.with_suffix('.fit.gz')
        compressed.write_bytes(gzip.compress(original))
        compressed_recipe=deepcopy(recipe)
        from indi_allsky.source_rendering import file_digest
        compressed_recipe['basis']['source_sha256']=file_digest(compressed)
        np.testing.assert_array_equal(
            render_source(compressed,compressed_recipe,assets,camera_id=cid,source_id=cid),
            render_source(source,recipe,assets,camera_id=cid,source_id=cid))
        # Exercise the actual authenticated preview route with no archived JPEG.
        from indi_allsky.flask import db
        from indi_allsky.flask.models import IndiAllSkyDbFitsImageTable, IndiAllSkyDbImageTable
        import cv2
        when=datetime.fromisoformat(recipe['basis']['exposure_date'])
        entry=IndiAllSkyDbFitsImageTable(id=cid,camera_id=cid,filename=str(source),
            createDate=when,dayDate=when.date(),exposure=1,gain=0,night=night)
        image_entry=IndiAllSkyDbImageTable(camera_id=cid,filename=str(root/'missing-jpeg.jpg'),
            createDate=when,dayDate=when.date(),exposure=1,gain=0,adu=0,night=night,
            data={'render_source':recipe})
        db.session.add_all([entry,image_entry]);db.session.commit()
        expected=render_source(source,recipe,assets,camera_id=cid,source_id=cid)
        ok,jpeg=cv2.imencode('.jpg',expected,[cv2.IMWRITE_JPEG_QUALITY,recipe['jpeg_quality']]);assert ok
        # The generated-image consumers use the same display bytes with no
        # permanent JPEG and no cache-path lease or cache-mtime dependency.
        from indi_allsky.generation_frames import read_generation_frame
        from indi_allsky.preview_cache import PreviewCache
        from indi_allsky.keogram import KeogramGenerator
        from indi_allsky.starTrails import StarTrailGenerator
        import simplejpeg
        import os
        cache=PreviewCache(root/'.render-cache')
        generators=[]
        generation_config=deepcopy(p.config)
        generation_config['IMAGE_FOLDER']=str(root)
        generation_config['STARTRAILS_TIMELAPSE']=True
        for _ in range(2):
            kg=KeogramGenerator(generation_config)
            st=StarTrailGenerator(generation_config,mask={1:np.full(expected.shape[:2],255,np.uint8)})
            st.sun_alt_threshold=91;st.max_adu=256;st.pixel_cutoff_threshold=101
            generators.append((kg,st))
        reference=root/'reference.jpg';reference.write_bytes(jpeg.tobytes())
        os.utime(reference,(when.timestamp(),when.timestamp()))
        for _ in range(2):
            cache.clear()
            source_path,pixels,stamp=read_generation_frame(image_entry,root,lambda source_id:entry)
            assert stamp==when.timestamp() and source_path==source
            np.testing.assert_array_equal(pixels,simplejpeg.decode_jpeg(jpeg.tobytes(),colorspace='BGR'))
            generators[0][0].processImage(pixels,stamp)
            generators[0][1].processImage(source_path,pixels,1,adu=0,star_count=100,exposure_timestamp=stamp)
            reference_pixels=simplejpeg.decode_jpeg(reference.read_bytes(),colorspace='BGR')
            generators[1][0].processImage(reference_pixels,reference.stat().st_mtime)
            generators[1][1].processImage(reference,reference_pixels,1,adu=0,star_count=100)
        np.testing.assert_array_equal(generators[0][0]._keogram_data,generators[1][0]._keogram_data)
        assert generators[0][0]._timestamps==generators[1][0]._timestamps
        np.testing.assert_array_equal(generators[0][1].trail_image,generators[1][1].trail_image)
        assert generators[0][1].trail_count==generators[1][1].trail_count==2
        for left,right in zip(generators[0][1]._timelapse_frame_list,generators[1][1]._timelapse_frame_list):
            assert left.read_bytes()==right.read_bytes()
            assert left.stat().st_mtime==right.stat().st_mtime==when.timestamp()
        assert source.read_bytes()==original
        # Real FITS -> saved rendering -> streaming FFmpeg, with no archived JPEG.
        from indi_allsky.timelapse import TimelapseGenerator
        import subprocess
        video_config=deepcopy(generation_config)
        video_config['IMAGE_FILE_TYPE']='png'
        video_config['TIMELAPSE']['DEFLICKER']=False
        png_reference=root/'display-reference.png'
        assert cv2.imwrite(str(png_reference),pixels)
        os.utime(png_reference,(when.timestamp(),when.timestamp()))
        videos=[]
        for source_input in (False,True):
            generator=TimelapseGenerator(video_config)
            generator.vf_scale='64:48'
            generator.ffmpeg_extra_options='-threads 1 -filter_threads 1 -preset ultrafast -crf 0'
            video=root/('source-stream.mp4' if source_input else 'display-stream.mp4')
            cache.clear()
            if source_input:
                generator.generate_entries(video,[image_entry],root,lambda source_id:entry)
                assert not list(generator.pre_processor.seqfolder.iterdir())
            else:
                generator.generate(video,[png_reference])
            videos.append(subprocess.run(['ffmpeg','-v','error','-threads','1','-i',str(video),
                '-f','rawvideo','-pix_fmt','bgr24','pipe:1'],capture_output=True,check=True,timeout=30).stdout)
            generator.pre_processor.temp_seqfolder.cleanup()
        assert videos[0]==videos[1] and len(videos[0])==64*48*3
        assert source.read_bytes()==original
        for attribute,wrong in (('camera_id',999),('createDate',datetime(2001,1,1))):
            from types import SimpleNamespace
            invalid=SimpleNamespace(id=entry.id,camera_id=entry.camera_id,createDate=entry.createDate)
            setattr(invalid,attribute,wrong)
            try:read_generation_frame(image_entry,root,lambda source_id:invalid)
            except ValueError:pass
            else:raise AssertionError('Wrong generation exposure accepted')
        cache.clear()
        source.rename(source.with_suffix('.hidden'))
        try:read_generation_frame(image_entry,root,lambda source_id:entry)
        except FileNotFoundError:pass
        else:raise AssertionError('Missing scientific source silently skipped')
        source.with_suffix('.hidden').rename(source)
        image_id=image_entry.id
    url='/indi-allsky/fits2jpeg?id='+str(cid)
    assert app.test_client().get(url).status_code in (302,401)
    from indi_allsky.preview_cache import PreviewCache
    preview_cache=PreviewCache(root/'.render-cache')
    for uid in (1,2):
        client=login_client(app,uid)
        if uid==2:
            with patch('indi_allsky.source_preview.render_source',side_effect=AssertionError('Cache hit should not render')):
                response=client.get(url)
        else:
            response=client.get(url)
        assert response.status_code==200, response.text[:500]
        assert response.data==jpeg.tobytes() and response.cache_control.private
    preview_cache.clear()
    assert client.get(url).data==jpeg.tobytes(), 'Evicted preview must regenerate without archived JPEG'
    assert source.read_bytes()==original
    preview_cache.clear()
    asset_path=assets.root/(recipe['presentation']['config']['font']+'.npz')
    preserved_asset=asset_path.read_bytes()
    asset_path.write_bytes(b'broken archive')
    assert client.get(url).status_code==422
    asset_path.write_bytes(preserved_asset)
    broken=deepcopy(recipe);broken['basis']['camera_id']=999
    with app.app_context():
        image_entry=db.session.get(IndiAllSkyDbImageTable,image_id)
        image_entry.data={'render_source':broken};db.session.commit()
    assert client.get(url).status_code==422
    download=client.get(f'/indi-allsky/modern-admin/media/fits/{cid}/{cid}/download')
    assert download.status_code==200 and download.data==original
    with app.app_context():
        image_entry=db.session.get(IndiAllSkyDbImageTable,image_id)
        image_entry.data={'render_source':recipe};db.session.commit()
        duplicate=IndiAllSkyDbImageTable(camera_id=cid,filename=str(root/'ambiguous.jpg'),
            createDate=when,dayDate=when.date(),exposure=1,gain=0,adu=0,night=night)
        db.session.add(duplicate);db.session.commit()
    assert client.get(url).status_code==422
    # A completed FITS carries its recipe even without the Image JSON copy.
    from indi_allsky.source_publication import read_source_recipe, scientific_digest
    from indi_allsky.image import ImageWorker
    from types import SimpleNamespace
    import io
    with app.app_context():
        db.session.delete(duplicate);db.session.commit()
        calls=[]
        def uploaded(fits_entry, metadata):
            published=read_source_recipe(source)
            assert published['basis']['version']==2
            assert metadata['fileSize']==source.stat().st_size==fits_entry.fileSize
            assert metadata['data']['render_source']==published
            calls.append('s3')
        worker=SimpleNamespace(_source_render_recipe=lambda *args:recipe,
            _miscUpload=SimpleNamespace(s3_upload_fits=uploaded,
                upload_fits_image=lambda entry:calls.append('upload')))
        result={'path':str(source),'db_id':cid,'metadata':{'fileSize':len(original)}}
        science=scientific_digest(source)
        published=ImageWorker._finalize_fits_source(worker,result,None,None,None)
        assert calls==['s3','upload']
        assert scientific_digest(source)==science
        image_entry=db.session.get(IndiAllSkyDbImageTable,image_id)
        image_entry.data={'source_fits_id':cid};db.session.commit()
        with fits.open(source) as stored, fits.open(io.BytesIO(original)) as previous:
            np.testing.assert_array_equal(stored[0].data,previous[0].data)
        preview_cache.clear()
        frame=read_generation_frame(image_entry,root,lambda source_id:db.session.get(IndiAllSkyDbFitsImageTable,source_id))
        np.testing.assert_array_equal(frame[1],simplejpeg.decode_jpeg(jpeg.tobytes(),colorspace='BGR'))
        stable=source.read_bytes()
        assert published==read_source_recipe(source)
    preview_cache.clear()
    assert client.get(url).data==jpeg.tobytes()
    assert source.read_bytes()==stable
    # Source-only display records serve Library/Loop and existing public URLs.
    with app.app_context():
        image_entry=db.session.get(IndiAllSkyDbImageTable,image_id)
        image_entry.data={'source_fits_id':cid,'storage_format':'fits'}
        image_entry.fileSize=0;db.session.commit()
        assert image_entry.validateFile()
        assert not image_entry.getFilesystemPath().exists(), 'Validation must not render a file'
        display_url=str(image_entry.getUrl())
        assert display_url==f'/indi-allsky/media/image/{cid}/{image_id}/original'
        from indi_allsky.modern_admin_media_runtime import ModernAdminMediaUrlNormalizer
        normalizer=ModernAdminMediaUrlNormalizer()
        assert normalizer.normalize_safe_local_image_url(display_url)==display_url
        assert normalizer.normalize_safe_local_image_url(display_url+'/../private') is None
        assert normalizer.normalize_safe_local_image_url(display_url+'?target=https://example.invalid') is None
    for uid in (1,2):
        reader=login_client(app,uid)
        response=reader.get(display_url)
        assert response.status_code==200 and response.data==jpeg.tobytes()
        assert response.mimetype=='image/jpeg' and 'attachment' not in response.headers['Content-Disposition']
        assert reader.get(display_url,headers={'If-None-Match':response.headers['ETag']}).status_code==304
        assert reader.get(display_url,headers={'Range':'bytes=0-15'}).data==jpeg.tobytes()[:16]
        for download_url in (display_url+'?download=1',f'/indi-allsky/modern-admin/media/image/{cid}/{image_id}/download'):
            response=reader.get(download_url)
            assert response.status_code==200 and response.data==jpeg.tobytes()
            assert response.mimetype=='image/jpeg' and 'attachment' in response.headers['Content-Disposition']
        library=reader.get('/indi-allsky/modern-admin/library',query_string={'kind':'image','camera_id':cid})
        assert library.status_code==200 and display_url in library.text
        now=reader.get('/indi-allsky/modern-admin/now',query_string={'camera_id':cid})
        assert now.status_code==200 and f'src="{display_url}"' in now.text
        detail=reader.get(f'/indi-allsky/modern-admin/media/images/{image_id}',query_string={'camera_id':cid})
        assert detail.status_code==200 and display_url in detail.text
        loop=reader.get('/indi-allsky/js/loop',query_string={'camera_id':cid,'timestamp':int(when.timestamp())})
        assert loop.status_code==200 and any(item['url']==display_url for item in loop.json['image_list'])
        viewer=reader.get('/indi-allsky/view_image',query_string={'id':image_id,'camera_id':cid})
        assert viewer.status_code==200 and 'Download JPEG with overlay' in viewer.text
        assert reader.get(f'/indi-allsky/media/image/{3-cid}/{image_id}/original').status_code==404
    anonymous=app.test_client()
    app.config.update(INDI_ALLSKY_AUTH_ALL_VIEWS=False,INDI_ALLSKY_AUTH_MEDIA_VIEWS=False)
    assert anonymous.get(display_url).data==jpeg.tobytes()
    assert anonymous.get(f'/indi-allsky/modern-admin/media/fits/{cid}/{cid}/download').status_code in (302,401)
    app.config['INDI_ALLSKY_AUTH_MEDIA_VIEWS']=True
    assert anonymous.get(display_url).status_code in (302,401)
    with app.app_context():
        camera=db.session.get(IndiAllSkyDbCameraTable,cid)
        camera.web_nonlocal_images=True;camera.web_local_images_admin=False;db.session.commit()
    assert reader.get(display_url).status_code==404
    with app.app_context():
        camera.web_nonlocal_images=False;db.session.commit()
        fits_entry=db.session.get(IndiAllSkyDbFitsImageTable,cid)
        fits_entry.camera_id=3-cid;db.session.commit()
        assert not db.session.get(IndiAllSkyDbImageTable,image_id).validateFile()
    assert reader.get(display_url).status_code==404
    with app.app_context():
        fits_entry=db.session.get(IndiAllSkyDbFitsImageTable,cid)
        fits_entry.camera_id=cid;db.session.commit()
    assert source.read_bytes()==stable, 'All display/download requests preserve the FITS'
    with app.app_context():
        from source_upload_checks import check_source_upload
        check_source_upload(db.session.get(IndiAllSkyDbImageTable,image_id), source, root, expected)
        from indi_allsky.archive_policy import retain_scientific_only
        from indi_allsky.flask import models
        item=db.session.get(IndiAllSkyDbImageTable,image_id)
        item.data={'source_fits_id':cid,'render_source':published}
        display=item.getFilesystemPath();display.write_bytes(jpeg.tobytes())
        item.fileSize=display.stat().st_size;db.session.commit()
        assert not retain_scientific_only(item,None,None,db.session,models) and display.exists()
        with patch.object(Path,'unlink',side_effect=OSError('synthetic filesystem error')):
            assert not retain_scientific_only(item,{'db_id':cid},published,db.session,models)
        assert display.exists() and item.data.get('storage_format') is None
        assert retain_scientific_only(item,{'db_id':cid},published,db.session,models)
        assert not display.exists() and item.fileSize==0 and item.validateFile()
        assert source.read_bytes()==stable
        from indi_allsky.miscUpload import miscUpload
        tasks=[]
        upload=SimpleNamespace(config={'MQTTPUBLISH':{'ENABLE':True}},_queue_upload_task=tasks.append)
        miscUpload.mqtt_publish_image(upload,display,'latest',{'exposure':1},image_entry=item)
        assert len(tasks)==1 and tasks[0].data['id']==item.id
        assert tasks[0].data['model']==type(item).__name__ and 'local_file' not in tasks[0].data
        from indi_allsky.source_upload import source_upload_file
        with source_upload_file(item,root,{'exposure':1}) as (_,metadata):
            assert metadata=={'exposure':1}
        # Preserve the actual capture EXIF through FITS context and reconstruction.
        import piexif
        from indi_allsky.source_preview import source_display_bytes
        exif=piexif.dump({'0th':{piexif.ImageIFD.Model:b'Archive fixture'},
                         'Exif':{piexif.ExifIFD.ExposureTime:(1,2)}, 'GPS':{}})
        worker._source_render_recipe=lambda *args:published
        before_science=scientific_digest(source)
        with_exif=ImageWorker._finalize_fits_source(worker,result,None,None,None,
                                                  upload=False,jpeg_exif=exif)
        assert read_source_recipe(source)['export_exif']==exif.hex()
        assert scientific_digest(source)==before_science
        from PIL import Image
        for extension in ('jpg','webp'):
            encoded=source_display_bytes(source,with_exif,camera_id=cid,source_id=cid,
                                         media_root=root,file_type=extension)
            decoded=piexif.load(encoded)
            assert decoded['0th'][piexif.ImageIFD.Model]==b'Archive fixture'
            assert decoded['Exif'][piexif.ExifIFD.ExposureTime]==(1,2) and decoded['GPS']=={}
            if extension=='jpg':
                np.testing.assert_array_equal(simplejpeg.decode_jpeg(encoded,colorspace='BGR'),
                                              simplejpeg.decode_jpeg(jpeg.tobytes(),colorspace='BGR'))


print('Full source replay: exact display pixels, original FITS unchanged, calibrated/raw/stack/focus, two cameras, day/night, all stretch modes, AWB/CCM, masks and saved labels: PASS')
