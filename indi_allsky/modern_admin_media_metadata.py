from pathlib import Path


class ModernAdminStartrailVideoMetadataService:
    def __init__(
        self,
        query,
        camera_relation=None,
        camera_id_field=None,
        camera_id=None,
        order_by_expression=None,
    ):
        self.query = query
        self.camera_relation = camera_relation
        self.camera_id_field = camera_id_field
        self.camera_id = camera_id
        self.order_by_expression = order_by_expression


    def list_entries(self, limit=100):
        query = self.query
        if self.camera_relation is not None:
            query = query.join(self.camera_relation)
        if self.camera_id_field is not None and self.camera_id is not None:
            query = query.filter(self.camera_id_field == self.camera_id)
        if self.order_by_expression is not None:
            query = query.order_by(self.order_by_expression)
        if limit is not None:
            query = query.limit(limit)

        return query.all()


    def build_rows(self, entries):
        return [
            self.build_row(entry)
            for entry in entries
        ]


    def build_row(self, entry):
        return {
            'id'         : entry.id,
            'created'    : self.format_datetime(entry.createDate),
            'day_date'   : entry.dayDate if entry.dayDate else 'Unknown',
            'camera_id'  : entry.camera_id,
            'filename'   : self.format_filename(entry.filename),
            'dimensions' : self.format_dimensions(entry.width, entry.height),
            'frames'     : entry.frames if entry.frames is not None else 'Unknown',
            'framerate'  : self.format_number(entry.framerate, suffix=' fps'),
            'file_size'  : self.format_media_size(entry.fileSize) if entry.fileSize else 'Unknown',
            'timeofday'  : 'Night' if entry.night else 'Day',
            'uploaded'   : self.format_bool(entry.uploaded),
            'success'    : self.format_bool(entry.success),
            'source'     : self.format_source(entry),
            'sync_id'    : entry.sync_id if entry.sync_id is not None else 'N/A',
            'metadata'   : self.format_data_summary(entry.data),
        }


    def format_datetime(self, value, default='Unknown'):
        if not value:
            return default
        if hasattr(value, 'strftime'):
            return value.strftime('%Y-%m-%d %H:%M:%S')
        return str(value)


    def format_filename(self, value):
        if not value:
            return 'Unknown'
        return Path(str(value)).name


    def format_dimensions(self, width, height):
        if width and height:
            return '{0:d} x {1:d}'.format(int(width), int(height))
        return 'Unknown'


    def format_number(self, value, suffix=''):
        if value is None:
            return 'Unknown'
        try:
            number = '{0:.3f}'.format(float(value)).rstrip('0').rstrip('.')
            return '{0:s}{1:s}'.format(number, suffix)
        except (TypeError, ValueError):
            return str(value)


    def format_media_size(self, value):
        if value is None:
            return 'Unknown'

        try:
            size = float(value)
        except (TypeError, ValueError):
            return str(value)

        units = ('B', 'KB', 'MB', 'GB', 'TB')
        unit_index = 0
        while size >= 1024.0 and unit_index < len(units) - 1:
            size /= 1024.0
            unit_index += 1

        if unit_index == 0:
            return '{0:d} {1:s}'.format(int(size), units[unit_index])
        return '{0:.1f} {1:s}'.format(size, units[unit_index])


    def format_bool(self, value):
        return 'Yes' if bool(value) else 'No'


    def format_source(self, entry):
        if entry.remote_url:
            return 'Remote URL recorded'
        if entry.s3_key:
            return 'S3 key recorded'
        return 'Local DB entry'


    def format_data_summary(self, value):
        if isinstance(value, dict):
            return 'Keys: {0:d}'.format(len(value))
        if value is None:
            return 'No metadata payload'
        return 'Non-dict metadata payload'


class ModernAdminKeogramMetadataService(ModernAdminStartrailVideoMetadataService):
    def build_row(self, entry):
        return {
            'id'         : entry.id,
            'created'    : self.format_datetime(entry.createDate),
            'day_date'   : entry.dayDate if entry.dayDate else 'Unknown',
            'camera_id'  : entry.camera_id,
            'filename'   : self.format_filename(entry.filename),
            'dimensions' : self.format_dimensions(entry.width, entry.height),
            'frames'     : entry.frames if entry.frames is not None else 'Unknown',
            'file_size'  : self.format_media_size(entry.fileSize) if entry.fileSize else 'Unknown',
            'timeofday'  : 'Night' if entry.night else 'Day',
            'uploaded'   : self.format_bool(entry.uploaded),
            'success'    : self.format_bool(entry.success),
            'source'     : self.format_source(entry),
            'sync_id'    : entry.sync_id if entry.sync_id is not None else 'N/A',
            'metadata'   : self.format_data_summary(entry.data),
        }
