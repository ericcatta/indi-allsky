"""Read-only capture-cycle summaries from persisted per-camera records."""
from sqlalchemy import func


def camera_cycle(camera, image_model, source_models, output_models):
    candidates = []
    for model in (image_model, *(model for _, model in source_models)):
        record = model.query.filter(model.camera_id == camera.id).order_by(
            model.createDate.desc(), model.id.desc()).first()
        if record is not None:
            candidates.append(record)
    latest = max(candidates, key=lambda record: record.createDate) if candidates else None
    result = {'camera_id': camera.id, 'camera_name': camera.friendlyName or camera.name,
              'status': 'empty', 'day_date': None, 'latest': None,
              'phases': [], 'sources': [], 'outputs': []}
    if latest is None:
        return result
    result.update(status='available', day_date=latest.dayDate, latest=latest.createDate)
    def cycle_query(model):
        return model.query.filter(model.camera_id == camera.id, model.dayDate == latest.dayDate)
    rows = cycle_query(image_model).with_entities(
        image_model.night, func.count(image_model.id), func.min(image_model.createDate),
        func.max(image_model.createDate)).group_by(image_model.night).all()
    result['phases'] = [{'label': 'Night' if night else 'Day', 'count': count,
                         'first': first, 'last': last} for night, count, first, last in rows]
    for label, model in source_models:
        result['sources'].append({'label': label, 'count': cycle_query(model).count()})
    for label, model in output_models:
        total, successful = cycle_query(model).with_entities(
            func.count(model.id), func.count(model.id).filter(model.success.is_(True))).one()
        result['outputs'].append({'label': label, 'count': total, 'successful': successful})
    return result
