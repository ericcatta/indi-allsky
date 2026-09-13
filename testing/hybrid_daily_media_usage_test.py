#!/usr/bin/env python3
"""Complete daily accounting, unknown sizes and one-count thumbnail attribution."""
from datetime import date, datetime
from unittest.mock import patch
from sqlalchemy import event
from sqlalchemy.exc import SQLAlchemyError
from hybrid_runtime_fixture import isolated_app, login_client


def run():
    with isolated_app(multi_camera=True) as app:
        from indi_allsky.flask import db, overview_queries as q
        from indi_allsky.flask.models import IndiAllSkyDbThumbnailTable as Thumb
        with app.app_context():
            for cid in (1, 2):
                for index, (_, model) in enumerate(q.DAILY_MODELS):
                    fields = dict(filename=f'{cid}-{index}', camera_id=cid, fileSize=100*cid,
                                  dayDate=date(2026, 9, 12), night=True, thumbnail_uuid=f'shared-{cid}')
                    candidates = dict(exposure=.5, gain=1, adu=.1, note='Synthetic daily accounting',
                                      targetDate=datetime.now(), startDate=datetime.now(), endDate=datetime.now())
                    fields.update({k:v for k,v in candidates.items() if k in model.__table__.columns})
                    db.session.add(model(**fields))
                db.session.add(Thumb(filename=f'thumb-{cid}', uuid=f'shared-{cid}', camera_id=cid, fileSize=55))
            db.session.add(Thumb(filename='orphan',uuid='orphan',camera_id=1,fileSize=None))
            db.session.commit()
            calls=[]
            def record(*args): calls.append(args[2])
            event.listen(db.engine,'before_cursor_execute',record)
            try:
                result=q.daily_media_usage(1)
                assert len(calls)==2, len(calls)
            finally: event.remove(db.engine,'before_cursor_execute',record)
            group=result['2026-09-12']['Night']
            assert group['tod_fileSize']==1055 and group['tod_count']==11, group
            assert all(group[label]['count']==1 for label in q.DAILY_LABELS)
            assert result['Unassigned']['Unknown']['tod_unknown']==1
            assert result['Unassigned']['Unknown']['tod_count']==1
            assert q.daily_media_usage(2)['2026-09-12']['Night']['tod_fileSize']==2055
            image=q.DAILY_MODELS[0][1].query.filter_by(camera_id=1).one()
            image.fileSize=None
            image.night=False  # shared thumbnail references now disagree on period
            db.session.commit()
            result=q.daily_media_usage(1)
            assert result['2026-09-12']['Day']['Images']==dict(fileSize=0,count=1,unknown=1)
            assert result['Unassigned']['Unknown']['Thumbnails']==dict(fileSize=55,count=2,unknown=1)
            image.night=True; image.dayDate=date(2026,9,11)
            db.session.commit()
            assert q.daily_media_usage(1)['Unassigned']['Unknown']['Thumbnails']['count']==2
            image.thumbnail_uuid='shared-2'  # cross-camera reference cannot steal thumbnail
            db.session.commit()
            assert q.daily_media_usage(2)['2026-09-12']['Night']['Thumbnails']['count']==1
            assert q.daily_media_usage(999)=={}
        for uid in (1,2):
            client=login_client(app,uid)
            path='/indi-allsky/modern-admin/storage/file-space-usage?camera_id=1&profile_id=test-profile-1'
            page=client.get(path)
            assert page.status_code==200
            for label in q.DAILY_LABELS: assert '<th>'+label+'</th>' in page.text, label
            assert 'size unknown' in page.text and 'Unassigned' in page.text
            with patch.object(q,'daily_media_usage',side_effect=SQLAlchemyError('synthetic daily read failure')):
                page=client.get(path)
                assert page.status_code==200 and 'Daily media usage could not be read' in page.text
                assert 'No file usage rows' not in page.text
                assert 'hybrid-operations-table-config' not in page.text
                assert 'operations-table.js' not in page.text
            assert client.get(path).status_code==200
        print('Daily usage PASS: all eleven families, shared/orphan/ambiguous/cross-camera thumbnails, unknown sizes, two queries, both roles and read recovery')


if __name__=='__main__': run()
