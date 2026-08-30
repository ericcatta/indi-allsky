from pathlib import Path


class ModernAdminMediaListQueryPlan:
    """Read-only query intent for Modern/Admin media list pages."""

    def __init__(
        self,
        selected_camera_id=None,
        limit=24,
        join_camera=True,
        order_latest=True,
    ):
        self.selected_camera_id = selected_camera_id
        self.limit = limit
        self.join_camera = bool(join_camera)
        self.order_latest = bool(order_latest)


    def to_dict(self):
        return {
            'selected_camera_id': self.selected_camera_id,
            'limit'             : self.limit,
            'join_camera'       : self.join_camera,
            'order_latest'      : self.order_latest,
        }


class ModernAdminMediaListQueryPlanner:
    """Hybrid-owned planning boundary; the caller still executes the query."""

    def build_plan(self, selected_camera_id=None, limit=24):
        return ModernAdminMediaListQueryPlan(
            selected_camera_id=self.normalize_camera_id(selected_camera_id),
            limit=self.normalize_limit(limit),
            join_camera=True,
            order_latest=True,
        )


    def normalize_camera_id(self, value):
        if value in (None, ''):
            return None

        try:
            camera_id = int(value)
        except (TypeError, ValueError):
            return None

        if camera_id <= 0:
            return None

        return camera_id


    def normalize_limit(self, value):
        if value is None:
            return 24

        try:
            return int(value)
        except (TypeError, ValueError):
            return 24


class ModernAdminMediaUrlNormalizer:
    """Hybrid-owned URL shaping for Modern/Admin media surfaces."""

    def __init__(self, images_folder_url_builder=None):
        self.images_folder_url_builder = images_folder_url_builder


    def normalize_media_url(self, media_url):
        if not media_url:
            return None

        media_url_str = str(media_url)
        if media_url_str.startswith(('http://', 'https://', '/')):
            return media_url_str

        media_url_p = Path(media_url_str)
        if media_url_p.parts and media_url_p.parts[0] == 'images':
            if not self.images_folder_url_builder:
                return media_url_str
            return self.images_folder_url_builder(str(Path(*media_url_p.parts[1:])))

        return media_url_str


    def normalize_safe_local_image_url(self, media_url):
        normalized_url = self.normalize_media_url(media_url)
        if not normalized_url:
            return None

        normalized_url = str(normalized_url)
        if not self.is_safe_local_image_route(normalized_url):
            return None

        return normalized_url


    def is_safe_local_image_route(self, value):
        if not value:
            return False

        value = str(value)
        value_lower = value.lower()
        if not value.startswith('/'):
            return False

        if '/images/' not in value:
            return False

        if any(token in value_lower for token in ('..', '\\', '://', 'file:', '\x00')):
            return False

        return True


class ModernAdminMediaAccessAdapter:
    """Hybrid compatibility adapter for existing media URL resolution."""

    def __init__(
        self,
        url_normalizer,
        s3_prefix='',
        logger=None,
        error_message='Error determining modern admin media URL: {0:s}',
    ):
        self.url_normalizer = url_normalizer
        self.s3_prefix = s3_prefix
        self.logger = logger
        self.error_message = error_message


    def resolve_media_url(self, media_entry, local=True):
        try:
            media_url = media_entry.getUrl(s3_prefix=self.s3_prefix, local=local)
        except Exception as e:
            self.log_error(self.error_message, e)
            return None

        return self.url_normalizer.normalize_media_url(media_url)


    def resolve_existing_media_url(self, media_url):
        return self.url_normalizer.normalize_media_url(media_url)


    def resolve_filesystem_path(self, media_entry):
        return media_entry.getFilesystemPath()


    def resolve_media_file_size(self, media_entry, default=0):
        try:
            return self.resolve_filesystem_path(media_entry).stat().st_size
        except Exception:
            return default


    def read_fits_preview_metadata(self, filename_p, fits_opener):
        hdulist = fits_opener(filename_p)
        header = hdulist[0].header
        sensor_temp = float(header.get('CCD-TEMP', 0))
        metadata = {
            'exposure'    : float(header.get('EXPTIME', 0)),
            'gain'        : float(header.get('GAIN', 0)),
            'binning'     : int(header.get('XBINNING', 1)),
            'sensor_temp' : sensor_temp,
        }
        hdulist.close()
        return metadata


    def log_error(self, message, *args):
        if self.logger is None:
            return

        try:
            self.logger.error(message, *args)
        except Exception:
            pass


class ModernAdminMediaServeAdapter:
    """Hybrid compatibility adapter for existing media file serving."""

    def __init__(self, image_folder, sender):
        self.image_folder = image_folder
        self.sender = sender


    def serve_image_folder_path(self, path):
        return self.sender(self.image_folder, path)


class ModernAdminPreviewMetadataLookupService:
    """Metadata-only thumbnail/preview lookup for Modern/Admin media surfaces."""

    def __init__(
        self,
        thumbnail_query,
        thumbnail_uuid_field,
        url_normalizer,
        s3_prefix='',
        logger=None,
    ):
        self.thumbnail_query = thumbnail_query
        self.thumbnail_uuid_field = thumbnail_uuid_field
        self.url_normalizer = url_normalizer
        self.s3_prefix = s3_prefix
        self.logger = logger


    def get_preview_url(self, media_entry, media_url=None, local=True):
        fallback_url = media_url
        thumbnail_uuid = getattr(media_entry, 'thumbnail_uuid', None)
        if not thumbnail_uuid:
            return fallback_url

        thumbnail_entry = self.get_thumbnail_entry(thumbnail_uuid)
        if thumbnail_entry is None:
            return fallback_url

        if not local and not self.has_remote_media(thumbnail_entry):
            return fallback_url

        try:
            thumbnail_url = thumbnail_entry.getUrl(s3_prefix=self.s3_prefix, local=local)
        except Exception as e:
            self.log_error('Error determining modern admin thumbnail URL: {0:s}', e)
            return fallback_url

        normalized_url = self.url_normalizer.normalize_media_url(thumbnail_url)
        return normalized_url if normalized_url is not None else fallback_url


    def get_thumbnail_entry(self, thumbnail_uuid):
        try:
            return self.thumbnail_query\
                .filter(self.thumbnail_uuid_field == thumbnail_uuid)\
                .one()
        except Exception:
            return None


    def has_remote_media(self, thumbnail_entry):
        return bool(
            getattr(thumbnail_entry, 'remote_url', None)
            or getattr(thumbnail_entry, 's3_key', None)
        )


    def log_error(self, message, *args):
        if self.logger is None:
            return

        try:
            self.logger.error(message, *args)
        except Exception:
            pass


class ModernAdminMediaItemSerializer:
    """Serialize one media DB row into the existing Modern/Admin view item shape."""

    def __init__(
        self,
        media_url_provider,
        preview_url_provider,
        clock,
    ):
        self.media_url_provider = media_url_provider
        self.preview_url_provider = preview_url_provider
        self.clock = clock


    def serialize(self, media_entry):
        create_date = getattr(media_entry, 'createDate', None)
        day_date = getattr(media_entry, 'dayDate', None)
        file_size = getattr(media_entry, 'fileSize', None)
        width = getattr(media_entry, 'width', None)
        height = getattr(media_entry, 'height', None)
        frames = getattr(media_entry, 'frames', None)
        media_url = self.media_url_provider(media_entry)
        preview_url = self.preview_url_provider(media_entry, media_url=media_url)

        return {
            'id'          : getattr(media_entry, 'id', None),
            'camera_id'   : getattr(media_entry, 'camera_id', None),
            'title'       : self.format_media_title(media_entry),
            'url'         : media_url,
            'preview_url' : preview_url,
            'filename'    : self.format_filename(getattr(media_entry, 'filename', None)),
            'created'     : self.format_datetime(create_date, default='Unknown date'),
            'day_date'    : self.format_date(day_date, default='Unknown day'),
            'age'         : self.format_media_age(create_date) if create_date else 'Unknown age',
            'timeofday'   : self.format_media_timeofday(media_entry),
            'size'        : self.format_media_size(file_size) if file_size else 'Unknown size',
            'dimensions'  : self.format_dimensions(width, height),
            'frames'      : '{0:d} frames'.format(frames) if frames else None,
            'success'     : getattr(media_entry, 'success', None),
        }


    def format_media_title(self, media_entry):
        create_date = getattr(media_entry, 'createDate', None)
        if create_date:
            return self.format_datetime(create_date, format_text='%b %d, %H:%M')

        day_date = getattr(media_entry, 'dayDate', None)
        if day_date:
            return self.format_date(day_date)

        return self.format_filename(getattr(media_entry, 'filename', None))


    def format_media_timeofday(self, media_entry):
        if not hasattr(media_entry, 'night'):
            return 'Captured'

        if media_entry.night:
            return 'Night'

        return 'Day'


    def format_media_age(self, create_date):
        age_s = max(0, int((self.clock() - create_date).total_seconds()))

        if age_s < 60:
            return '{0:d}s ago'.format(age_s)
        elif age_s < 3600:
            return '{0:d}m ago'.format(int(age_s / 60))

        return '{0:d}h ago'.format(int(age_s / 3600))


    def format_media_size(self, size_b):
        size = float(size_b)
        for unit in ('B', 'KB', 'MB', 'GB'):
            if size < 1024.0:
                return '{0:0.1f} {1:s}'.format(size, unit)
            size /= 1024.0

        return '{0:0.1f} TB'.format(size)


    def format_datetime(self, value, default='Unknown', format_text='%Y-%m-%d %H:%M:%S'):
        if not value:
            return default
        if hasattr(value, 'strftime'):
            return value.strftime(format_text)
        return str(value)


    def format_date(self, value, default='Unknown'):
        if not value:
            return default
        if hasattr(value, 'strftime'):
            return value.strftime('%Y-%m-%d')
        return str(value)


    def format_filename(self, value):
        if not value:
            return 'Unknown'
        return Path(str(value)).name


    def format_dimensions(self, width, height):
        if width and height:
            return '{0:d} x {1:d}'.format(int(width), int(height))
        return 'Unknown dimensions'


class ModernAdminLatestCameraFramesRepository:
    """Bounded runtime source for the two latest Product UI camera images."""

    def __init__(
        self,
        camera_query,
        image_query,
        camera_id_field,
        image_order_by_expression,
        camera_visible_expression=None,
        camera_order_by_expression=None,
        fallback_camera=None,
        clock=None,
        s3_prefix='',
        images_folder_url_builder=None,
        logger=None,
    ):
        self.camera_query = camera_query
        self.image_query = image_query
        self.camera_id_field = camera_id_field
        self.image_order_by_expression = image_order_by_expression
        self.camera_visible_expression = camera_visible_expression
        self.camera_order_by_expression = camera_order_by_expression
        self.fallback_camera = fallback_camera
        self.clock = clock
        self.s3_prefix = s3_prefix
        self.url_normalizer = ModernAdminMediaUrlNormalizer(
            images_folder_url_builder=images_folder_url_builder,
        )
        self.logger = logger


    def get_latest_camera_frames(self):
        frames = []
        for camera in self.get_camera_rows():
            frames.append(self.get_frame_for_camera(camera))

        return frames


    def get_camera_rows(self):
        try:
            query = self.camera_query
            if self.camera_visible_expression is not None:
                query = query.filter(self.camera_visible_expression)
            if self.camera_order_by_expression is not None:
                query = query.order_by(self.camera_order_by_expression)
            camera_rows = query.limit(2).all()
        except Exception as e:
            self.log_error('Error loading Now camera frame rows: {0:s}', e)
            camera_rows = list()

        if camera_rows:
            return camera_rows[:2]

        return [self.fallback_camera] if self.fallback_camera is not None else []


    def get_frame_for_camera(self, camera):
        camera_id = getattr(camera, 'id', None)
        camera_label = str(
            getattr(camera, 'friendlyName', None)
            or getattr(camera, 'name', None)
            or 'Camera {0}'.format(camera_id or 'unknown')
        )

        if not camera_id:
            return self.empty_frame(camera_id, camera_label, 'Camera context unavailable.')

        try:
            image_entry = self.image_query\
                .filter(self.camera_id_field == camera_id)\
                .order_by(self.image_order_by_expression)\
                .limit(1)\
                .first()
        except Exception as e:
            self.log_error('Error loading Now latest image for camera {0}: {1:s}', camera_id, e)
            return self.empty_frame(camera_id, camera_label, 'Latest image metadata unavailable.')

        if not image_entry:
            return self.empty_frame(camera_id, camera_label, 'No latest image metadata available.')

        safe_image_url = self.safe_image_url(image_entry)
        created_at = getattr(image_entry, 'createDate', None)

        return {
            'camera_id': camera_id,
            'camera_label': camera_label,
            'timestamp': self.timestamp_label(created_at),
            'age_label': self.age_label(created_at),
            'image_available': bool(safe_image_url),
            'safe_image_url': safe_image_url,
            'source_status': 'Existing image route available.' if safe_image_url else 'No safe image route available.',
            'note': 'Latest frame shown from existing image URL metadata; no filesystem scan is performed by Now.',
        }


    def empty_frame(self, camera_id, camera_label, note):
        return {
            'camera_id': camera_id,
            'camera_label': camera_label,
            'timestamp': 'No latest frame available',
            'age_label': 'Not evaluated yet',
            'image_available': False,
            'safe_image_url': None,
            'source_status': note,
            'note': note,
        }


    def safe_image_url(self, image_entry):
        try:
            image_url = image_entry.getUrl(s3_prefix=self.s3_prefix, local=True)
        except Exception as e:
            self.log_error('Error determining Now camera image URL: {0:s}', e)
            return None

        return self.url_normalizer.normalize_safe_local_image_url(image_url)


    def timestamp_label(self, value):
        if hasattr(value, 'strftime'):
            return value.strftime('%Y-%m-%d %H:%M:%S')

        return 'No timestamp available'


    def age_label(self, value):
        if not hasattr(value, 'strftime'):
            return 'Not evaluated yet'

        try:
            age_seconds = int((self.clock() - value).total_seconds())
        except Exception:
            return 'Not evaluated yet'

        if age_seconds < 0:
            return 'Not evaluated yet'

        if age_seconds < 60:
            return '{0:d} seconds ago'.format(age_seconds)

        age_minutes = int(age_seconds / 60)
        if age_minutes < 60:
            return '{0:d} minutes ago'.format(age_minutes)

        return '{0:d} hours ago'.format(int(age_minutes / 60))


    def log_error(self, message, *args):
        if self.logger is None:
            return

        try:
            self.logger.error(message, *args)
        except Exception:
            pass
