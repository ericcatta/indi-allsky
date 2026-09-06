"""Synthetic task/notification records; only call inside isolated_app."""
from datetime import datetime, timedelta, timezone


def seed_operations(app):
    from indi_allsky.flask import db
    from indi_allsky.flask.models import (IndiAllSkyDbNotificationTable, NotificationCategory,
        IndiAllSkyDbTaskQueueTable, TaskQueueState, TaskQueueQueue)
    with app.app_context():
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        for number in range(1, 206):
            db.session.add(IndiAllSkyDbTaskQueueTable(id=number,
                createDate=now-timedelta(seconds=number), state=TaskQueueState.SUCCESS if number % 2 else TaskQueueState.FAILED,
                queue=TaskQueueQueue.VIDEO, data={'action':'generateVideo', 'kwargs':{
                    'camera_id':1 if number % 2 else 2, 'profile_id':'test-profile-'+str(1 if number % 2 else 2),
                    'token':'synthetic-secret-must-be-redacted'}}, result='Synthetic result '+str(number)))
        for number, ack in ((1,False),(2,False),(3,True)):
            db.session.add(IndiAllSkyDbNotificationTable(id=number, createDate=now-timedelta(seconds=number),
                expireDate=now+timedelta(hours=1), ack=ack, category=NotificationCategory.GENERAL,
                item='acceptance', notification='Synthetic notification '+str(number)))
        db.session.commit()
