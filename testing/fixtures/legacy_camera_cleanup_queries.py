"""Frozen pre-extraction query/effect ordering for parity tests."""
class LegacyCleanup:
    def flushImages(self, camera_id):
        ### Images
        image_query = IndiAllSkyDbImageTable.query\
            .join(IndiAllSkyDbImageTable.camera)\
            .filter(IndiAllSkyDbCameraTable.id == camera_id)\
            .order_by(IndiAllSkyDbImageTable.createDate.asc())


        ### FITS Images
        fits_image_query = IndiAllSkyDbFitsImageTable.query\
            .join(IndiAllSkyDbFitsImageTable.camera)\
            .filter(IndiAllSkyDbCameraTable.id == camera_id)\
            .order_by(IndiAllSkyDbFitsImageTable.createDate.asc())


        ### RAW Images
        raw_image_query = IndiAllSkyDbRawImageTable.query\
            .join(IndiAllSkyDbRawImageTable.camera)\
            .filter(IndiAllSkyDbCameraTable.id == camera_id)\
            .order_by(IndiAllSkyDbRawImageTable.createDate.asc())


        ### Panorama Images
        panorama_image_query = IndiAllSkyDbPanoramaImageTable.query\
            .join(IndiAllSkyDbPanoramaImageTable.camera)\
            .filter(IndiAllSkyDbCameraTable.id == camera_id)\
            .order_by(IndiAllSkyDbPanoramaImageTable.createDate.asc())


        ### Getting IDs first then deleting each file is faster than deleting all files with
        ### thumbnails with a single query.  Deleting associated thumbnails causes sqlalchemy
        ### to recache after every delete which cause a 1-5 second lag for each delete


        asset_lists = [
            (image_query, IndiAllSkyDbImageTable),
            (fits_image_query, IndiAllSkyDbFitsImageTable),
            (raw_image_query, IndiAllSkyDbRawImageTable),
            (panorama_image_query, IndiAllSkyDbPanoramaImageTable),
        ]


        return flush_media_batches(asset_lists, self._deleteAssets)


    def flush16MinutesImages(self, camera_id):
        now = datetime.now()
        now_minus_x_minutes = now - timedelta(minutes=16)

        ### Images
        image_query_16 = IndiAllSkyDbImageTable.query\
            .join(IndiAllSkyDbImageTable.camera)\
            .filter(IndiAllSkyDbCameraTable.id == camera_id)\
            .filter(IndiAllSkyDbImageTable.createDate >= now_minus_x_minutes)\
            .order_by(IndiAllSkyDbImageTable.createDate.asc())


        ### Getting IDs first then deleting each file is faster than deleting all files with
        ### thumbnails with a single query.  Deleting associated thumbnails causes sqlalchemy
        ### to recache after every delete which cause a 1-5 second lag for each delete


        asset_lists = [
            (image_query_16, IndiAllSkyDbImageTable),
        ]


        return flush_media_batches(asset_lists, self._deleteAssets)


    def flushTimelapses(self, camera_id):
        video_query = IndiAllSkyDbVideoTable.query\
            .join(IndiAllSkyDbVideoTable.camera)\
            .filter(IndiAllSkyDbCameraTable.id == camera_id)\
            .order_by(IndiAllSkyDbVideoTable.createDate.asc())

        mini_video_query = IndiAllSkyDbMiniVideoTable.query\
            .join(IndiAllSkyDbMiniVideoTable.camera)\
            .filter(IndiAllSkyDbCameraTable.id == camera_id)\
            .order_by(IndiAllSkyDbMiniVideoTable.createDate.asc())

        keogram_query = IndiAllSkyDbKeogramTable.query\
            .join(IndiAllSkyDbKeogramTable.camera)\
            .filter(IndiAllSkyDbCameraTable.id == camera_id)\
            .order_by(IndiAllSkyDbKeogramTable.createDate.asc())

        startrail_query = IndiAllSkyDbStarTrailsTable.query\
            .join(IndiAllSkyDbStarTrailsTable.camera)\
            .filter(IndiAllSkyDbCameraTable.id == camera_id)\
            .order_by(IndiAllSkyDbStarTrailsTable.createDate.asc())

        startrail_video_query = IndiAllSkyDbStarTrailsVideoTable.query\
            .join(IndiAllSkyDbStarTrailsVideoTable.camera)\
            .filter(IndiAllSkyDbCameraTable.id == camera_id)\
            .order_by(IndiAllSkyDbStarTrailsVideoTable.createDate.asc())

        panorama_video_query = IndiAllSkyDbPanoramaVideoTable.query\
            .join(IndiAllSkyDbPanoramaVideoTable.camera)\
            .filter(IndiAllSkyDbCameraTable.id == camera_id)\
            .order_by(IndiAllSkyDbPanoramaVideoTable.createDate.asc())


        ### Getting IDs first then deleting each file is faster than deleting all files with
        ### thumbnails with a single query.  Deleting associated thumbnails causes sqlalchemy
        ### to recache after every delete which cause a 1-5 second lag for each delete


        asset_lists = [
            (video_query, IndiAllSkyDbVideoTable),
            (mini_video_query, IndiAllSkyDbMiniVideoTable),
            (keogram_query, IndiAllSkyDbKeogramTable),
            (startrail_query, IndiAllSkyDbStarTrailsTable),
            (startrail_video_query, IndiAllSkyDbStarTrailsVideoTable),
            (panorama_video_query, IndiAllSkyDbPanoramaVideoTable),
        ]


        return flush_media_batches(asset_lists, self._deleteAssets)


    def flushDaytime(self, camera_id):
        ### Images
        image_query = IndiAllSkyDbImageTable.query\
            .join(IndiAllSkyDbImageTable.camera)\
            .filter(IndiAllSkyDbCameraTable.id == camera_id)\
            .filter(IndiAllSkyDbImageTable.night == sa_false())\
            .order_by(IndiAllSkyDbImageTable.createDate.asc())


        ### FITS Images
        fits_image_query = IndiAllSkyDbFitsImageTable.query\
            .join(IndiAllSkyDbFitsImageTable.camera)\
            .filter(IndiAllSkyDbCameraTable.id == camera_id)\
            .filter(IndiAllSkyDbFitsImageTable.night == sa_false())\
            .order_by(IndiAllSkyDbFitsImageTable.createDate.asc())


        ### RAW Images
        raw_image_query = IndiAllSkyDbRawImageTable.query\
            .join(IndiAllSkyDbRawImageTable.camera)\
            .filter(IndiAllSkyDbCameraTable.id == camera_id)\
            .filter(IndiAllSkyDbRawImageTable.night == sa_false())\
            .order_by(IndiAllSkyDbRawImageTable.createDate.asc())


        ### Panorama Images
        panorama_image_query = IndiAllSkyDbPanoramaImageTable.query\
            .join(IndiAllSkyDbPanoramaImageTable.camera)\
            .filter(IndiAllSkyDbCameraTable.id == camera_id)\
            .filter(IndiAllSkyDbPanoramaImageTable.night == sa_false())\
            .order_by(IndiAllSkyDbPanoramaImageTable.createDate.asc())


        ### Timelapses
        video_query = IndiAllSkyDbVideoTable.query\
            .join(IndiAllSkyDbVideoTable.camera)\
            .filter(IndiAllSkyDbCameraTable.id == camera_id)\
            .filter(IndiAllSkyDbVideoTable.night == sa_false())\
            .order_by(IndiAllSkyDbVideoTable.createDate.asc())

        ### Not flushing daytime mini timelapses

        ### Keograms
        keogram_query = IndiAllSkyDbKeogramTable.query\
            .join(IndiAllSkyDbKeogramTable.camera)\
            .filter(IndiAllSkyDbCameraTable.id == camera_id)\
            .filter(IndiAllSkyDbKeogramTable.night == sa_false())\
            .order_by(IndiAllSkyDbKeogramTable.createDate.asc())


        ### Panorama Videos
        panorama_video_query = IndiAllSkyDbPanoramaVideoTable.query\
            .join(IndiAllSkyDbPanoramaVideoTable.camera)\
            .filter(IndiAllSkyDbCameraTable.id == camera_id)\
            .filter(IndiAllSkyDbPanoramaVideoTable.night == sa_false())\
            .order_by(IndiAllSkyDbPanoramaVideoTable.createDate.asc())

        ## no startrails
        ## no startrail videos


        ### Getting IDs first then deleting each file is faster than deleting all files with
        ### thumbnails with a single query.  Deleting associated thumbnails causes sqlalchemy
        ### to recache after every delete which cause a 1-5 second lag for each delete


        asset_lists = [
            (image_query, IndiAllSkyDbImageTable),
            (fits_image_query, IndiAllSkyDbFitsImageTable),
            (raw_image_query, IndiAllSkyDbRawImageTable),
            (panorama_image_query, IndiAllSkyDbPanoramaImageTable),
            (video_query, IndiAllSkyDbVideoTable),
            (keogram_query, IndiAllSkyDbKeogramTable),
            (panorama_video_query, IndiAllSkyDbPanoramaVideoTable),
        ]


        return flush_media_batches(asset_lists, self._deleteAssets)


