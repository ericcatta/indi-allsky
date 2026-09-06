"""Hybrid notification commands; independent of Classic UI classes."""
from flask import current_app, jsonify, request
from flask_login import current_user, login_required
from sqlalchemy.orm.exc import NoResultFound

from . import db
from .base_views import BaseView
from .models import IndiAllSkyDbNotificationTable
from ..modern_admin_notifications import NotificationAcknowledgeDbAdapter, NotificationAcknowledgeService


class ModernAdminNotificationAcknowledgeView(BaseView):
    methods = ['POST']
    decorators = [login_required]

    def dispatch_request(self, notification_id):
        # Match the existing notification modal: any authenticated user may ack.
        # Notifications are system-wide; no camera/profile selection is implied.
        if not current_user.is_authenticated:
            return jsonify(message='Sign in to acknowledge notifications.'), 401
        payload = request.get_json(silent=True)
        if payload is not None and not isinstance(payload, dict):
            return jsonify(message='Expected a JSON object.'), 400
        adapter = NotificationAcknowledgeDbAdapter(
            notification_model=IndiAllSkyDbNotificationTable,
            no_result_exceptions=(NoResultFound,),
        )
        result = NotificationAcknowledgeService(adapter.lookup).acknowledge(
            notification_id, actor=current_user, payload=payload or {},
        )
        if not result.allowed:
            db.session.rollback()
        current_app.logger.info('Hybrid notification acknowledgement: actor=%s notification=%s status=%s',
                                current_user.id, notification_id, result.status)
        status = 200 if result.allowed else {
            'not_found': 404, 'invalid_id': 400,
        }.get(result.status, 500)
        return jsonify(result.to_dict()), status
