"""Read-only, explicitly scoped queries for Storage and Uploads summaries."""
from sqlalchemy import func, literal, select, union_all
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
