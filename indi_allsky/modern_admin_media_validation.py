"""Validate local media references before committing any record removals."""


class ModernAdminMediaValidation:
    # Model suffix, count label, removed-record label, require successful output.
    families = (
        ('Image', 'Images', 'image', False),
        ('FitsImage', 'FITS Images', 'FITS image', False),
        ('RawImage', 'RAW Images', 'RAW image', False),
        ('PanoramaImage', 'Panorama Images', 'panorama image', False),
        ('BadPixelMap', 'Bad pixel maps', 'bad pixel map', False),
        ('DarkFrame', 'Dark Frames', 'dark frame', False),
        ('Video', 'Timelapses', 'video', True),
        ('MiniVideo', 'Mini Timelapses', 'mini video', True),
        ('Keogram', 'Keograms', 'keogram', False),
        ('StarTrails', 'Star trails', 'star trail', True),
        ('StarTrailsVideo', 'Star trail timelapses', 'star trail timelapse', True),
        ('PanoramaVideo', 'Panorama timelapses', 'panorama timelapse', True),
        ('Thumbnail', 'Thumbnails', 'thumbnail', False),
    )

    def __init__(self, models, session):
        self.models = models
        self.session = session

    def run(self):
        messages, removals = [], []
        try:
            # Finish every filesystem check before scheduling any deletion.
            # Missing remote-only files are not evidence of an invalid record.
            for suffix, label, removed_label, successful in self.families:
                model = getattr(self.models, 'IndiAllSkyDb' + suffix + 'Table')
                query = model.query
                if suffix not in ('BadPixelMap', 'DarkFrame'):
                    query = query.filter(model.s3_key.is_(None))
                    query = query.filter((model.remote_url.is_(None)) | (model.remote_url == ''))
                if successful:
                    query = query.filter(model.success.is_(True))
                query = query.order_by(model.createDate.asc())
                messages.append('<p>{0}: {1:d}</p>'.format(label, query.count()))
                missing = [entry for entry in query if not entry.validateFile()]
                removals.append((removed_label, missing))
            for label, missing in removals:
                messages.append('<p>Removed {0:d} missing {1} entries</p>'.format(len(missing), label))
                for entry in missing:
                    self.session.delete(entry)
            self.session.commit()
        except Exception:
            self.session.rollback()
            raise
        return messages
