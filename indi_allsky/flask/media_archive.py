"""Hybrid archive query, cursor navigation and per-record media access."""
from datetime import date, datetime
from pathlib import Path
from urllib.parse import urlsplit
from flask import abort, url_for
from sqlalchemy import and_, or_
from .source_media_views import MEDIA_DOWNLOAD_MODELS, local_source_allowed
from ..modern_admin_media_runtime import ModernAdminMediaUrlNormalizer

KINDS = {
    'image': 'Images', 'video': 'Timelapses', 'mini-video': 'Mini timelapses',
    'keogram': 'Keograms', 'startrail': 'Startrails', 'startrail-video': 'Startrail videos',
    'panorama': 'Panorama images', 'panorama-video': 'Panorama videos', 'fits': 'FITS', 'raw': 'RAW',
}
PAGE_SIZE = 48


def archive_parameters(args):
    kind = args.get('kind', 'image')
    if kind not in KINDS:
        abort(400, description='Choose a supported media type.')
    values = {'kind': kind, 'search': args.get('search', '').strip(),
              'period': args.get('period', ''), 'uploaded': args.get('uploaded', ''),
              'sort': args.get('sort', 'newest'), 'start': args.get('start', ''), 'end': args.get('end', '')}
    if len(values['search']) > 255 or values['period'] not in ('', 'day', 'night') or values['uploaded'] not in ('', 'yes', 'no') or values['sort'] not in ('newest', 'oldest'):
        abort(400, description='Invalid archive filters.')
    for key in ('start', 'end'):
        if values[key]:
            try:
                values[key] = date.fromisoformat(values[key]).isoformat()
            except ValueError:
                abort(400, description='Use a valid YYYY-MM-DD capture date.')
    if values['start'] and values['end'] and values['start'] > values['end']:
        abort(400, description='Start date must be on or before end date.')
    cursor = args.get('cursor', '')
    direction = args.get('direction', 'next')
    if direction not in ('next', 'previous'):
        abort(400, description='Invalid archive navigation direction.')
    anchor = None
    if cursor:
        try:
            timestamp, identifier = cursor.split('|')
            anchor = (datetime.fromisoformat(timestamp), int(identifier))
            if anchor[0].tzinfo is not None or not 0 < anchor[1] <= 2**63 - 1:
                raise ValueError()
        except (ValueError, TypeError):
            abort(400, description='Invalid archive cursor. Apply filters to restart navigation.')
    return values, anchor, direction


class ModernAdminMediaArchive:
    def __init__(self, kind, camera_id, verify_admin_network):
        self.kind = kind
        self.model = MEDIA_DOWNLOAD_MODELS[kind]
        self.camera_id = camera_id
        self.verify_admin_network = verify_admin_network
        self.normalizer = ModernAdminMediaUrlNormalizer(
            images_folder_url_builder=lambda path: url_for('indi_allsky.images_folder', path=path))

    def query(self, values):
        model = self.model
        query = model.query
        if self.camera_id is not None:
            query = query.filter(model.camera_id == self.camera_id)
        if values['search']:
            query = query.filter(model.filename.contains(values['search'], autoescape=True))
        if values['period']:
            query = query.filter(model.night.is_(values['period'] == 'night'))
        if values['uploaded']:
            query = query.filter(model.uploaded.is_(values['uploaded'] == 'yes'))
        if values['start']:
            query = query.filter(model.dayDate >= date.fromisoformat(values['start']))
        if values['end']:
            query = query.filter(model.dayDate <= date.fromisoformat(values['end']))
        return query

    def load(self, values, anchor=None, direction='next'):
        model = self.model
        query = self.query(values)
        descending = values['sort'] == 'newest'
        if direction == 'previous':
            descending = not descending
        if anchor:
            timestamp, identifier = anchor
            compare_date = model.createDate < timestamp if descending else model.createDate > timestamp
            compare_id = model.id < identifier if descending else model.id > identifier
            query = query.filter(or_(compare_date, and_(model.createDate == timestamp, compare_id)))
        order = (model.createDate.desc(), model.id.desc()) if descending else (model.createDate.asc(), model.id.asc())
        entries = query.order_by(*order).limit(PAGE_SIZE + 1).all()
        more = len(entries) > PAGE_SIZE
        entries = entries[:PAGE_SIZE]
        if direction == 'previous':
            entries.reverse()
        return {
            'items': [self.item(entry) for entry in entries],
            'previous': self.cursor(entries[0]) if entries and (more if direction == 'previous' else anchor is not None) else None,
            'next': self.cursor(entries[-1]) if entries and (anchor is not None if direction == 'previous' else more) else None,
        }

    @staticmethod
    def cursor(entry):
        return entry.createDate.isoformat() + '|' + str(entry.id)

    def item(self, entry):
        local = local_source_allowed(entry.camera, self.verify_admin_network)
        media_url = None
        if local or entry.remote_url or entry.s3_key:
            try:
                candidate = self.normalizer.normalize_media_url(entry.getUrl(s3_prefix=entry.camera.s3_prefix, local=local))
                parts = urlsplit(candidate)
                if parts.scheme in ('http', 'https') and parts.netloc or not parts.scheme and candidate.startswith('/') and not candidate.startswith('//'):
                    media_url = candidate
            except (ValueError, TypeError, OSError):
                pass
        video = 'video' in self.kind
        preview = media_url
        if self.kind == 'fits':
            preview = url_for('indi_allsky.fits2jpeg_view', id=entry.id) if local else None
        elif not video and Path(entry.filename).suffix.lower() not in ('.jpg', '.jpeg', '.png', '.webp', '.gif', '.avif'):
            preview = None
        return {'id': entry.id, 'camera_id': entry.camera_id, 'filename': Path(entry.filename).name,
            'created': entry.createDate, 'day_date': entry.dayDate, 'night': entry.night,
            'uploaded': entry.uploaded, 'excluded': getattr(entry, 'exclude', False),
            'success': getattr(entry, 'success', None), 'note': getattr(entry, 'note', ''),
            'width': entry.width, 'height': entry.height, 'frames': getattr(entry, 'frames', None),
            'preview_url': preview, 'video': video,
            'download_url': url_for('indi_allsky.modern_admin_source_download_view', kind=self.kind,
                camera_id=entry.camera_id, media_id=entry.id)}
