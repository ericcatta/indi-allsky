"""Read-only, explicitly scoped queries for Storage and Uploads summaries."""
from sqlalchemy import Integer, case, cast, func, literal, select, union_all
from . import db
from .models import (
    IndiAllSkyDbImageTable, IndiAllSkyDbPanoramaImageTable,
    IndiAllSkyDbFitsImageTable, IndiAllSkyDbRawImageTable,
    IndiAllSkyDbVideoTable, IndiAllSkyDbMiniVideoTable,
    IndiAllSkyDbKeogramTable, IndiAllSkyDbStarTrailsTable,
    IndiAllSkyDbStarTrailsVideoTable, IndiAllSkyDbPanoramaVideoTable,
    IndiAllSkyDbThumbnailTable, IndiAllSkyDbTaskQueueTable, TaskQueueQueue,
)

MEDIA_MODELS = (
    ('Images', IndiAllSkyDbImageTable), ('Panoramas', IndiAllSkyDbPanoramaImageTable),
    ('FITS', IndiAllSkyDbFitsImageTable), ('RAW', IndiAllSkyDbRawImageTable),
    ('Timelapses', IndiAllSkyDbVideoTable), ('Mini Timelapses', IndiAllSkyDbMiniVideoTable),
    ('Keograms', IndiAllSkyDbKeogramTable), ('Startrails', IndiAllSkyDbStarTrailsTable),
    ('Startrail Videos', IndiAllSkyDbStarTrailsVideoTable),
    ('Panorama Videos', IndiAllSkyDbPanoramaVideoTable),
    ('Thumbnails', IndiAllSkyDbThumbnailTable),
)


def media_counts(camera_id):
    statements = [select(literal(label).label('label'), func.count(model.id).label('count'))
                  .where(model.camera_id == camera_id) for label, model in MEDIA_MODELS]
    counts = dict(db.session.execute(union_all(*statements)).all())
    return [{'label': label, 'count': counts[label]} for label, _ in MEDIA_MODELS]


def upload_state_counts():
    rows = db.session.execute(select(IndiAllSkyDbTaskQueueTable.state,
                                    func.count(IndiAllSkyDbTaskQueueTable.id))
                              .where(IndiAllSkyDbTaskQueueTable.queue == TaskQueueQueue.UPLOAD)
                              .group_by(IndiAllSkyDbTaskQueueTable.state)).all()
    return {state.value: count for state, count in rows}


DAILY_MODELS = tuple(({'RAW': 'Raw Images', 'Startrails': 'Star Trails',
                      'Startrail Videos': 'Star Trail Timelapses',
                      'Panorama Videos': 'Panorama Timelapses'}.get(label, label), model)
                     for label, model in MEDIA_MODELS[:-1])
DAILY_LABELS = tuple(label for label, _ in DAILY_MODELS) + ('Thumbnails',)


def daily_media_usage(camera_id):
    """Recorded bytes, not filesystem allocation; unknown sizes remain visible.

    Attribute thumbnails only when all same-camera media references agree on
    capture day/period. Shared thumbnails count once; orphan/ambiguous ones
    remain in an explicit unassigned bucket, without inventing a capture date.
    """
    statements = [select(literal(label).label('label'), model.dayDate.label('day'),
                         model.night.label('night'), func.sum(model.fileSize).label('size'),
                         func.count(model.id).label('count'),
                         (func.count(model.id) - func.count(model.fileSize)).label('unknown'))
                  .where(model.camera_id == camera_id).group_by(model.dayDate, model.night)
                  for label, model in DAILY_MODELS]
    rows = list(db.session.execute(union_all(*statements)))
    references = union_all(*[
        select(model.thumbnail_uuid.label('uuid'), model.dayDate.label('day'),
               cast(model.night, Integer).label('night'))
        .where(model.camera_id == camera_id, model.thumbnail_uuid.isnot(None))
        for _, model in DAILY_MODELS]).subquery()
    ownership = (select(references.c.uuid,
                       func.min(references.c.day).label('day'),
                       func.min(references.c.night).label('night'),
                       func.max(references.c.day).label('last_day'),
                       func.max(references.c.night).label('last_night'))
                 .group_by(references.c.uuid).subquery())
    consistent = (ownership.c.day == ownership.c.last_day) & (ownership.c.night == ownership.c.last_night)
    day = case((consistent, ownership.c.day), else_=None)
    night = case((consistent, ownership.c.night), else_=None)
    thumb = IndiAllSkyDbThumbnailTable
    rows.extend(db.session.execute(
        select(literal('Thumbnails'), day, night, func.sum(thumb.fileSize),
               func.count(thumb.id), func.count(thumb.id) - func.count(thumb.fileSize))
        .outerjoin(ownership, ownership.c.uuid == thumb.uuid)
        .where(thumb.camera_id == camera_id).group_by(day, night)))
    result = {}
    for label, day, night, size, count, unknown in rows:
        day_key = str(day) if day is not None else 'Unassigned'
        period = ('Night' if night else 'Day') if night is not None else 'Unknown'
        group = result.setdefault(day_key, {}).setdefault(period, {
            **{key: {'fileSize': 0, 'count': 0, 'unknown': 0} for key in DAILY_LABELS},
            'tod_fileSize': 0, 'tod_count': 0, 'tod_unknown': 0,
        })
        group[label] = {'fileSize': size or 0, 'count': count, 'unknown': unknown}
        group['tod_fileSize'] += size or 0
        group['tod_count'] += count
        group['tod_unknown'] += unknown
    return dict(sorted(result.items(), reverse=True))
