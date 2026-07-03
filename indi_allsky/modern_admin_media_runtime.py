from pathlib import Path


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
