# Frozen before Hybrid validation extraction, baseline d4ba173d.
def validateDbEntries(self):
    message_list = list()

    ### Images
    image_entries = IndiAllSkyDbImageTable.query\
        .filter(IndiAllSkyDbImageTable.s3_key == sa_null())\
        .order_by(IndiAllSkyDbImageTable.createDate.asc())


    image_entries_count = image_entries.count()
    message_list.append('<p>Images: {0:d}</p>'.format(image_entries_count))

    app.logger.info('Searching %d images...', image_entries_count)
    image_notfound_list = list()
    for i in image_entries:
        if not i.validateFile():
            #logger.warning('Entry not found on filesystem: %s', i.filename)
            image_notfound_list.append(i)


    ### FITS Images
    fits_image_entries = IndiAllSkyDbFitsImageTable.query\
        .filter(IndiAllSkyDbFitsImageTable.s3_key == sa_null())\
        .order_by(IndiAllSkyDbFitsImageTable.createDate.asc())


    fits_image_entries_count = fits_image_entries.count()
    message_list.append('<p>FITS Images: {0:d}</p>'.format(fits_image_entries_count))

    app.logger.info('Searching %d fits images...', fits_image_entries_count)
    fits_image_notfound_list = list()
    for i in fits_image_entries:
        if not i.validateFile():
            #logger.warning('Entry not found on filesystem: %s', i.filename)
            fits_image_notfound_list.append(i)


    ### Raw Images
    raw_image_entries = IndiAllSkyDbRawImageTable.query\
        .filter(IndiAllSkyDbRawImageTable.s3_key == sa_null())\
        .order_by(IndiAllSkyDbRawImageTable.createDate.asc())


    raw_image_entries_count = raw_image_entries.count()
    message_list.append('<p>RAW Images: {0:d}</p>'.format(raw_image_entries_count))

    app.logger.info('Searching %d raw images...', raw_image_entries_count)
    raw_image_notfound_list = list()
    for i in raw_image_entries:
        if not i.validateFile():
            #logger.warning('Entry not found on filesystem: %s', i.filename)
            raw_image_notfound_list.append(i)


    ### Panorama Images
    panorama_image_entries = IndiAllSkyDbPanoramaImageTable.query\
        .filter(IndiAllSkyDbPanoramaImageTable.s3_key == sa_null())\
        .order_by(IndiAllSkyDbPanoramaImageTable.createDate.asc())


    panorama_image_entries_count = panorama_image_entries.count()
    message_list.append('<p>Panorama Images: {0:d}</p>'.format(panorama_image_entries_count))

    app.logger.info('Searching %d panorama images...', panorama_image_entries_count)
    panorama_image_notfound_list = list()
    for i in panorama_image_entries:
        if not i.validateFile():
            #logger.warning('Entry not found on filesystem: %s', i.filename)
            panorama_image_notfound_list.append(i)


    ### Bad Pixel Maps
    badpixelmap_entries = IndiAllSkyDbBadPixelMapTable.query\
        .order_by(IndiAllSkyDbBadPixelMapTable.createDate.asc())
    # fixme - need deal with non-local installs


    badpixelmap_entries_count = badpixelmap_entries.count()
    message_list.append('<p>Bad pixel maps: {0:d}</p>'.format(badpixelmap_entries_count))

    app.logger.info('Searching %d bad pixel maps...', badpixelmap_entries_count)
    badpixelmap_notfound_list = list()
    for b in badpixelmap_entries:
        if not b.validateFile():
            #logger.warning('Entry not found on filesystem: %s', b.filename)
            badpixelmap_notfound_list.append(b)


    ### Dark frames
    darkframe_entries = IndiAllSkyDbDarkFrameTable.query\
        .order_by(IndiAllSkyDbDarkFrameTable.createDate.asc())
    # fixme - need deal with non-local installs


    darkframe_entries_count = darkframe_entries.count()
    message_list.append('<p>Dark Frames: {0:d}</p>'.format(darkframe_entries_count))

    app.logger.info('Searching %d dark frames...', darkframe_entries_count)
    darkframe_notfound_list = list()
    for d in darkframe_entries:
        if not d.validateFile():
            #logger.warning('Entry not found on filesystem: %s', d.filename)
            darkframe_notfound_list.append(d)


    ### Videos
    video_entries = IndiAllSkyDbVideoTable.query\
        .filter(
            and_(
                IndiAllSkyDbVideoTable.success == sa_true(),
                IndiAllSkyDbVideoTable.s3_key == sa_null(),
            )
        )\
        .order_by(IndiAllSkyDbVideoTable.createDate.asc())

    video_entries_count = video_entries.count()
    message_list.append('<p>Timelapses: {0:d}</p>'.format(video_entries_count))

    app.logger.info('Searching %d videos...', video_entries_count)
    video_notfound_list = list()
    for v in video_entries:
        if not v.validateFile():
            #logger.warning('Entry not found on filesystem: %s', v.filename)
            video_notfound_list.append(v)


    ### Mini Videos
    mini_video_entries = IndiAllSkyDbMiniVideoTable.query\
        .filter(
            and_(
                IndiAllSkyDbMiniVideoTable.success == sa_true(),
                IndiAllSkyDbMiniVideoTable.s3_key == sa_null(),
            )
        )\
        .order_by(IndiAllSkyDbMiniVideoTable.createDate.asc())

    mini_video_entries_count = mini_video_entries.count()
    message_list.append('<p>Mini Timelapses: {0:d}</p>'.format(mini_video_entries_count))

    app.logger.info('Searching %d mini videos...', mini_video_entries_count)
    mini_video_notfound_list = list()
    for m in mini_video_entries:
        if not m.validateFile():
            #logger.warning('Entry not found on filesystem: %s', m.filename)
            mini_video_notfound_list.append(m)


    ### Keograms
    keogram_entries = IndiAllSkyDbKeogramTable.query\
        .filter(IndiAllSkyDbKeogramTable.s3_key == sa_null())\
        .order_by(IndiAllSkyDbKeogramTable.createDate.asc())

    keogram_entries_count = keogram_entries.count()
    message_list.append('<p>Keograms: {0:d}</p>'.format(keogram_entries_count))

    app.logger.info('Searching %d keograms...', keogram_entries_count)
    keogram_notfound_list = list()
    for k in keogram_entries:
        if not k.validateFile():
            #logger.warning('Entry not found on filesystem: %s', k.filename)
            keogram_notfound_list.append(k)


    ### Startrails
    startrail_entries = IndiAllSkyDbStarTrailsTable.query\
        .filter(
            and_(
                IndiAllSkyDbStarTrailsTable.success == sa_true(),
                IndiAllSkyDbStarTrailsTable.s3_key == sa_null(),
            )
        )\
        .order_by(IndiAllSkyDbStarTrailsTable.createDate.asc())

    startrail_entries_count = startrail_entries.count()
    message_list.append('<p>Star trails: {0:d}</p>'.format(startrail_entries_count))

    app.logger.info('Searching %d star trails...', startrail_entries_count)
    startrail_notfound_list = list()
    for s in startrail_entries:
        if not s.validateFile():
            #logger.warning('Entry not found on filesystem: %s', s.filename)
            startrail_notfound_list.append(s)


    ### Startrail videos
    startrail_video_entries = IndiAllSkyDbStarTrailsVideoTable.query\
        .filter(
            and_(
                IndiAllSkyDbStarTrailsVideoTable.success == sa_true(),
                IndiAllSkyDbStarTrailsVideoTable.s3_key == sa_null(),
            )
        )\
        .order_by(IndiAllSkyDbStarTrailsVideoTable.createDate.asc())

    startrail_video_entries_count = startrail_video_entries.count()
    message_list.append('<p>Star trail timelapses: {0:d}</p>'.format(startrail_video_entries_count))

    app.logger.info('Searching %d star trail timelapses...', startrail_video_entries_count)
    startrail_video_notfound_list = list()
    for s in startrail_video_entries:
        if not s.validateFile():
            #logger.warning('Entry not found on filesystem: %s', s.filename)
            startrail_video_notfound_list.append(s)


    ### Panorama videos
    panorama_video_entries = IndiAllSkyDbPanoramaVideoTable.query\
        .filter(
            and_(
                IndiAllSkyDbPanoramaVideoTable.success == sa_true(),
                IndiAllSkyDbPanoramaVideoTable.s3_key == sa_null(),
            )
        )\
        .order_by(IndiAllSkyDbPanoramaVideoTable.createDate.asc())

    panorama_video_entries_count = panorama_video_entries.count()
    message_list.append('<p>Panorama timelapses: {0:d}</p>'.format(panorama_video_entries_count))

    app.logger.info('Searching %d panorama timelapses...', panorama_video_entries_count)
    panorama_video_notfound_list = list()
    for p in panorama_video_entries:
        if not p.validateFile():
            #logger.warning('Entry not found on filesystem: %s', p.filename)
            panorama_video_notfound_list.append(p)


    ### Thumbnails
    thumbnail_entries = IndiAllSkyDbThumbnailTable.query\
        .filter(IndiAllSkyDbThumbnailTable.s3_key == sa_null())\
        .order_by(IndiAllSkyDbThumbnailTable.createDate.asc())

    thumbnail_entries_count = thumbnail_entries.count()
    message_list.append('<p>Thumbnails: {0:d}</p>'.format(thumbnail_entries_count))

    app.logger.info('Searching %d thumbnails...', thumbnail_entries_count)
    thumbnail_notfound_list = list()
    for t in thumbnail_entries:
        if not t.validateFile():
            #logger.warning('Entry not found on filesystem: %s', t.filename)
            thumbnail_notfound_list.append(t)



    app.logger.warning('Images not found: %d', len(image_notfound_list))
    app.logger.warning('FITS Images not found: %d', len(fits_image_notfound_list))
    app.logger.warning('RAW Images not found: %d', len(raw_image_notfound_list))
    app.logger.warning('Panorama Images not found: %d', len(panorama_image_notfound_list))
    app.logger.warning('Bad pixel maps not found: %d', len(badpixelmap_notfound_list))
    app.logger.warning('Dark frames not found: %d', len(darkframe_notfound_list))
    app.logger.warning('Videos not found: %d', len(video_notfound_list))
    app.logger.warning('Mini Videos not found: %d', len(mini_video_notfound_list))
    app.logger.warning('Keograms not found: %d', len(keogram_notfound_list))
    app.logger.warning('Star trails not found: %d', len(startrail_notfound_list))
    app.logger.warning('Star trail timelapses not found: %d', len(startrail_video_notfound_list))
    app.logger.warning('Panorama timelapses not found: %d', len(panorama_video_notfound_list))
    app.logger.warning('Thumbnails not found: %d', len(thumbnail_notfound_list))


    ### DELETE ###
    message_list.append('<p>Removed {0:d} missing image entries</p>'.format(len(image_notfound_list)))
    [db.session.delete(i) for i in image_notfound_list]


    message_list.append('<p>Removed {0:d} missing FITS image entries</p>'.format(len(fits_image_notfound_list)))
    [db.session.delete(i) for i in fits_image_notfound_list]


    message_list.append('<p>Removed {0:d} missing RAW image entries</p>'.format(len(raw_image_notfound_list)))
    [db.session.delete(i) for i in raw_image_notfound_list]


    message_list.append('<p>Removed {0:d} missing panorama image entries</p>'.format(len(panorama_image_notfound_list)))
    [db.session.delete(i) for i in panorama_image_notfound_list]


    message_list.append('<p>Removed {0:d} missing bad pixel map entries</p>'.format(len(badpixelmap_notfound_list)))
    [db.session.delete(b) for b in badpixelmap_notfound_list]


    message_list.append('<p>Removed {0:d} missing dark frame entries</p>'.format(len(darkframe_notfound_list)))
    [db.session.delete(d) for d in darkframe_notfound_list]


    message_list.append('<p>Removed {0:d} missing video entries</p>'.format(len(video_notfound_list)))
    [db.session.delete(v) for v in video_notfound_list]


    message_list.append('<p>Removed {0:d} missing mini video entries</p>'.format(len(mini_video_notfound_list)))
    [db.session.delete(m) for m in mini_video_notfound_list]


    message_list.append('<p>Removed {0:d} missing keogram entries</p>'.format(len(keogram_notfound_list)))
    [db.session.delete(k) for k in keogram_notfound_list]


    message_list.append('<p>Removed {0:d} missing star trail entries</p>'.format(len(startrail_notfound_list)))
    [db.session.delete(s) for s in startrail_notfound_list]


    message_list.append('<p>Removed {0:d} missing star trail timelapse entries</p>'.format(len(startrail_video_notfound_list)))
    [db.session.delete(sv) for sv in startrail_video_notfound_list]


    message_list.append('<p>Removed {0:d} missing panorama timelapse entries</p>'.format(len(panorama_video_notfound_list)))
    [db.session.delete(p) for p in panorama_video_notfound_list]


    message_list.append('<p>Removed {0:d} missing thumbnail entries</p>'.format(len(thumbnail_notfound_list)))
    [db.session.delete(t) for t in thumbnail_notfound_list]


    # finalize transaction
    db.session.commit()

    return message_list
