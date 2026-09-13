#!/usr/bin/env python3
"""Storage scope, complete counts, upload-only backlog and honest read failures."""
from datetime import date, datetime
from urllib.parse import urlsplit, parse_qs
from html.parser import HTMLParser
from unittest.mock import patch, Mock
from types import SimpleNamespace
from sqlalchemy import event
from sqlalchemy.exc import SQLAlchemyError
from flask import template_rendered
from hybrid_runtime_fixture import isolated_app, login_client


class Links(HTMLParser):
    def __init__(self, text):
        super().__init__(); self.links = []; self.feed(text)
    def handle_starttag(self, tag, attrs):
        if tag == 'a': self.links.append(dict(attrs).get('href', ''))


def run():
    with isolated_app(multi_camera=True) as app:
        from indi_allsky.flask import db, views, overview_queries as queries
        from indi_allsky.flask.models import IndiAllSkyDbTaskQueueTable as Task, TaskQueueQueue as Queue, TaskQueueState as State
        with app.app_context():
            for label, model in queries.MEDIA_MODELS:
                for cid in (1, 2):
                    for index in range(cid):
                        fields = {'filename': '%s-%s-%s' % (model.__tablename__, cid, index), 'camera_id': cid}
                        candidates = dict(dayDate=date.today(), exposure=.5, gain=1, adu=.1, note='Synthetic overview',
                                          targetDate=datetime.now(), startDate=datetime.now(), endDate=datetime.now())
                        fields.update({k:v for k,v in candidates.items() if k in model.__table__.columns})
                        db.session.add(model(**fields))
            for state in State:
                db.session.add(Task(queue=Queue.UPLOAD, state=state, data={}))
                for _ in range(3): db.session.add(Task(queue=Queue.VIDEO, state=state, data={}))
            db.session.commit()
            calls=[]
            def record(*args): calls.append(args[2])
            event.listen(db.engine, 'before_cursor_execute', record)
            try:
                # Measure the previous Storage and Uploads query round trips.
                for _, model in queries.MEDIA_MODELS[:3] + (queries.MEDIA_MODELS[4],):
                    model.query.filter_by(camera_id=1).count()
                assert len(calls)==4
                calls.clear()
                for state in State: Task.query.filter_by(state=state).count()
                assert len(calls)==len(State)
                calls.clear()
                assert queries.media_counts(1)==[{'label':label,'count':1} for label,_ in queries.MEDIA_MODELS]
                assert len(calls)==1
                calls.clear()
                assert queries.upload_state_counts()=={state.value:1 for state in State}
                assert len(calls)==1
            finally: event.remove(db.engine,'before_cursor_execute',record)
        contexts=[]
        def rendered(sender,template,context,**extra): contexts.append(context)
        template_rendered.connect(rendered,app)
        for uid in (1,2):
            client=login_client(app,uid)
            for cid in (1,2):
                page=client.get('/indi-allsky/modern-admin/storage?camera_id=%s&profile_id=test-profile-%s'%(cid,cid))
                assert page.status_code==200,page.text[:300]
                assert int(contexts[-1]['camera_id'])==cid
                assert sum(r['count'] for r in contexts[-1]['modern_admin_storage_counts'])==11*cid
                for link in Links(page.text.split('aria-labelledby="storage-pages-title"',1)[1].split('</section>',1)[0]).links:
                    if urlsplit(link).path.endswith(('/storage/file-space-usage','/media/images','/tools/process-fits')):
                        assert parse_qs(urlsplit(link).query)=={'camera_id':[str(cid)],'profile_id':['test-profile-'+str(cid)]},link
                assert 'Storage Protection' in page.text and 'Thumbnails' in page.text and 'RAW' in page.text
            for query in ('camera_id=bad','camera_id=1&profile_id=test-profile-2','profile_id=missing'):
                assert client.get('/indi-allsky/modern-admin/storage?'+query).status_code==400
            page=client.get('/indi-allsky/modern-admin/uploads')
            assert page.status_code==200,page.text[:300]
            assert all(row['count']==1 for row in contexts[-1]['modern_admin_upload_tasks'])
            assert 'No recent upload notifications.' in page.text and 'across all cameras' in page.text
            for helper,page_path,message in (
                ('media_counts','storage','Media inventory could not be read'),
                ('upload_state_counts','uploads','Upload queue could not be read'),
            ):
                with patch.object(queries,helper,side_effect=SQLAlchemyError('synthetic read failure')):
                    response=client.get('/indi-allsky/modern-admin/'+page_path)
                    assert response.status_code==200 and message in response.text
                assert client.get('/indi-allsky/modern-admin/'+page_path).status_code==200
            with patch.object(views.ModernAdminUploadsView,'get_upload_notifications',return_value=None):
                response=client.get('/indi-allsky/modern-admin/uploads')
                assert 'Upload notifications could not be read' in response.text
                assert 'No recent upload notifications.' not in response.text
        with app.app_context():
            query=Mock();query.filter.side_effect=SQLAlchemyError('synthetic notification failure')
            with patch.object(views,'IndiAllSkyDbNotificationTable',SimpleNamespace(query=query, category=views.IndiAllSkyDbNotificationTable.category)):
                assert views.ModernAdminUploadsView.get_upload_notifications(None) is None
        print('Overview PASS: eleven media families, two cameras/roles, scoped links, upload-only counts, read failures; SQL round trips Storage 4->1 and Uploads 6->1')


if __name__=='__main__': run()
