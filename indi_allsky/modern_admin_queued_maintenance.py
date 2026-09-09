"""Hybrid planning for explicit reload and camera-scoped media expiration."""


RETENTION_FIELDS = {'IMAGE_EXPIRE_DAYS':10, 'IMAGE_RAW_EXPIRE_DAYS':10,
                    'IMAGE_FITS_EXPIRE_DAYS':10, 'TIMELAPSE_EXPIRE_DAYS':365}


def retention_policy_token(config):
    import hashlib
    import json
    values = {key:config.get(key, default) for key,default in RETENTION_FIELDS.items()}
    return hashlib.sha256(json.dumps(values, sort_keys=True).encode()).hexdigest()


class ModernAdminQueuedMaintenancePlanner:
    def plan(self, command, camera_id=None, retention_token=None):
        if command == 'hup':
            return dict(queue='MAIN', state='MANUAL', priority=100,
                        jobdata={'action':'reload'}, reload_status=True,
                        message='Job submitted')
        if command != 'expire_data':
            raise ValueError('Unsupported queued maintenance command')
        if isinstance(camera_id, bool) or not str(camera_id).isdigit() or int(camera_id) <= 0:
            raise ValueError('A valid camera ID is required')
        kwargs = {'camera_id':int(camera_id)}
        if retention_token is not None:
            if not isinstance(retention_token, str) or len(retention_token) != 64 or any(c not in '0123456789abcdef' for c in retention_token):
                raise ValueError('Invalid retention policy token')
            kwargs['retention_token'] = retention_token
        return dict(queue='VIDEO', state='MANUAL', priority=100,
                    jobdata={'action':'expireData', 'kwargs':kwargs},
                    reload_status=False, message='Submitted expire task')
