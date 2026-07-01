import json
from datetime import timedelta


class ModernAdminTaskReadService:
    sensitive_payload_keys = (
        'password',
        'passwd',
        'token',
        'secret',
        'credential',
        'authorization',
        'auth_header',
        'api_key',
        'access_key',
        'private_key',
    )

    def __init__(self, query, now, filter_expression=None, order_by_expression=None, id_field=None):
        self.query = query
        self.now = now
        self.filter_expression = filter_expression
        self.order_by_expression = order_by_expression
        self.id_field = id_field


    def list_tasks(self):
        query = self.query
        if self.filter_expression is not None:
            query = query.filter(self.filter_expression)
        if self.order_by_expression is not None:
            query = query.order_by(self.order_by_expression)

        return [
            self.build_task_entry(task)
            for task in query
        ]


    def get_task(self, task_id):
        query = self.query
        if self.id_field is not None:
            query = query.filter(self.id_field == task_id)

        return query.one()


    def build_task_entry(self, task):
        task_data = task.data if isinstance(getattr(task, 'data', None), dict) else {}

        return {
            'id'         : getattr(task, 'id', None),
            'createDate' : getattr(task, 'createDate', None),
            'updateDate' : getattr(task, 'updateDate', None),
            'queue'      : self.enum_name(getattr(task, 'queue', None)),
            'state'      : self.enum_name(getattr(task, 'state', None)),
            'action'     : self.get_task_data_value(task_data, 'action', 'MISSING'),
            'camera_id'  : self.get_task_data_value(task_data, 'camera_id'),
            'profile_id' : self.get_task_data_value(task_data, 'profile_id'),
            'message'    : self.get_task_data_value(task_data, 'message') or self.get_task_data_value(task_data, 'error'),
            'result'     : getattr(task, 'result', None),
        }


    def build_queue_rows(self, task_list, details_url_builder, display_limit=200):
        task_rows = list()

        for task in task_list[:display_limit]:
            created_date = task.get('createDate')
            message = task.get('message') or task.get('result') or ''
            task_id = task.get('id')
            task_rows.append({
                'id'         : task_id,
                'details_url': details_url_builder(task_id),
                'created'    : self.format_task_datetime(created_date),
                'age'        : self.format_task_age(created_date),
                'updated'    : self.format_task_datetime(task.get('updateDate'), default='Not tracked'),
                'queue'      : task.get('queue') or 'Unknown',
                'action'     : task.get('action') or 'Unknown',
                'state'      : task.get('state') or 'Unknown',
                'state_tone' : self.get_task_state_tone(task.get('state')),
                'camera_id'  : task.get('camera_id') or 'Any',
                'profile_id' : task.get('profile_id') or 'Any',
                'message'    : message or 'No message',
            })

        return task_rows


    def build_task_detail(self, task):
        task_data = task.data if isinstance(getattr(task, 'data', None), dict) else {}
        payload_text = self.format_task_payload(self.redact_task_payload(getattr(task, 'data', None)))
        queue = getattr(task, 'queue', None)
        state = getattr(task, 'state', None)
        state_name = self.enum_name(state)

        return {
            'id'           : getattr(task, 'id', None),
            'queue'        : self.enum_name(queue),
            'queue_value'  : self.enum_value(queue),
            'state'        : state_name,
            'state_value'  : self.enum_value(state),
            'state_tone'   : self.get_task_state_tone(state_name),
            'action'       : self.get_task_data_value(task_data, 'action', 'MISSING'),
            'created'      : self.format_task_datetime(getattr(task, 'createDate', None)),
            'updated'      : self.format_task_datetime(getattr(task, 'updateDate', None), default='Not tracked'),
            'priority'     : getattr(task, 'priority', None) if getattr(task, 'priority', None) is not None else 'Not set',
            'camera_id'    : self.get_task_data_value(task_data, 'camera_id') or 'Any',
            'profile_id'   : self.get_task_data_value(task_data, 'profile_id') or 'Any',
            'message'      : self.get_task_data_value(task_data, 'message') or self.get_task_data_value(task_data, 'error') or 'No message',
            'result'       : getattr(task, 'result', None) or 'No result',
            'payload_text' : payload_text,
            'has_payload'  : payload_text != '',
        }


    def get_task_data_value(self, task_data, key, default=''):
        if not isinstance(task_data, dict):
            return default

        value = task_data.get(key)
        if value not in (None, ''):
            return value

        task_kwargs = task_data.get('kwargs')
        if isinstance(task_kwargs, dict):
            value = task_kwargs.get(key)
            if value not in (None, ''):
                return value

        return default


    def format_task_datetime(self, value, default='Unknown'):
        if not value:
            return default
        if hasattr(value, 'strftime'):
            return value.strftime('%Y-%m-%d %H:%M:%S')
        return str(value)


    def format_task_age(self, value):
        if not value:
            return 'Unknown age'

        try:
            age_s = max(0, int((self.now - value).total_seconds()))
        except TypeError:
            return 'Unknown age'

        if age_s < 60:
            return '{0:d}s ago'.format(age_s)
        if age_s < 3600:
            return '{0:d}m ago'.format(int(age_s / 60))
        if age_s < 86400:
            return '{0:d}h ago'.format(int(age_s / 3600))
        return '{0:d}d ago'.format(int(age_s / 86400))


    def get_task_state_tone(self, state):
        state_name = str(state or '').upper()
        if state_name == 'SUCCESS':
            return 'modern-admin-status-good'
        if state_name == 'FAILED':
            return 'modern-admin-status-warning'
        if state_name in ('QUEUED', 'RUNNING'):
            return 'modern-admin-status-neutral'
        return 'modern-admin-status-muted'


    def get_task_filter_values(self, task_rows, key):
        values = {str(row.get(key) or 'Unknown') for row in task_rows}
        return sorted(values)


    def get_recent_task_count(self, task_list):
        recent_cutoff = self.now - timedelta(hours=1)
        recent_count = 0
        for task in task_list:
            create_date = task.get('createDate')
            if create_date and create_date >= recent_cutoff:
                recent_count += 1
        return recent_count


    def redact_task_payload(self, value):
        if isinstance(value, dict):
            redacted = {}
            for key, item in value.items():
                if self.is_sensitive_payload_key(key):
                    redacted[key] = '<redacted>'
                else:
                    redacted[key] = self.redact_task_payload(item)
            return redacted

        if isinstance(value, list):
            return [self.redact_task_payload(item) for item in value]

        return value


    def is_sensitive_payload_key(self, key):
        key_str = str(key).lower()
        return any(sensitive_key in key_str for sensitive_key in self.sensitive_payload_keys)


    def format_task_payload(self, value):
        if value in (None, ''):
            return ''

        try:
            return json.dumps(value, indent=2, sort_keys=True, default=str)
        except TypeError:
            return str(value)


    def enum_name(self, value):
        return value.name if value else 'Unknown'


    def enum_value(self, value):
        return value.value if value else 'Unknown'
