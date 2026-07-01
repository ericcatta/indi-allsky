class ModernAdminNotificationReadService:
    def __init__(self, query, order_by_expression=None, id_field=None):
        self.query = query
        self.order_by_expression = order_by_expression
        self.id_field = id_field


    def list_notifications(self, limit=100):
        query = self.query
        if self.order_by_expression is not None:
            query = query.order_by(self.order_by_expression)
        if limit is not None:
            query = query.limit(limit)

        return query.all()


    def get_notification(self, notification_id):
        query = self.query
        if self.id_field is not None:
            query = query.filter(self.id_field == notification_id)

        return query.one()


    def build_notification_rows(self, notices):
        return [
            self.build_notification_row(notice)
            for notice in notices
        ]


    def build_notification_detail(self, notice):
        return self.build_notification_row(notice)


    def build_notification_row(self, notice):
        is_ack = bool(getattr(notice, 'ack', False))

        return {
            'id'          : getattr(notice, 'id', None),
            'category'    : self.format_notification_category(getattr(notice, 'category', None)),
            'item'        : getattr(notice, 'item', None) or 'Not set',
            'created'     : self.format_notification_datetime(getattr(notice, 'createDate', None)),
            'expires'     : self.format_notification_datetime(getattr(notice, 'expireDate', None)),
            'ack'         : 'Yes' if is_ack else 'No',
            'ack_tone'    : 'modern-admin-status-muted' if is_ack else 'modern-admin-status-warning',
            'notification': getattr(notice, 'notification', None),
        }


    def format_notification_datetime(self, value, default='Unknown'):
        if not value:
            return default
        if hasattr(value, 'strftime'):
            return value.strftime('%Y-%m-%d %H:%M:%S')
        return str(value)


    def format_notification_category(self, value):
        if value:
            return getattr(value, 'value', value)
        return 'Unknown'
