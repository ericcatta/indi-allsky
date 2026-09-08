"""Resolve recorded generation results to camera-scoped Hybrid output pages."""
from pathlib import Path


ACTION_OUTPUTS = {
    'generateVideo': {'video': 'Timelapse'},
    'generateMiniVideo': {'mini-video': 'Mini timelapse'},
    'generatePanoramaVideo': {'panorama-video': 'Panorama video'},
    'generateKeogramStarTrails': {
        'keogram': 'Keogram', 'startrail': 'Startrail', 'startrail-video': 'Startrail video',
    },
}


def positive_id(value):
    if type(value) is int:
        return value if 0 < value < 2**63 else None
    if isinstance(value, str) and value.isascii() and value.isdigit() and len(value) < 20:
        return positive_id(int(value))
    return None


class ModernAdminTaskOutputService:
    def __init__(self, media_root, lookup, url_builder):
        self.media_root = Path(media_root).resolve()
        self.lookup = lookup
        self.url_builder = url_builder

    def build_links(self, task):
        data = task.data if isinstance(task.data, dict) else {}
        kwargs = data.get('kwargs') if isinstance(data.get('kwargs'), dict) else {}
        action = data.get('action')
        allowed = ACTION_OUTPUTS.get(action, {}) if isinstance(action, str) else {}
        camera_id = positive_id(data.get('camera_id') or kwargs.get('camera_id'))
        if not camera_id or not allowed:
            return []
        profile_id = data.get('profile_id') or kwargs.get('profile_id') or ''
        if not isinstance(profile_id, str):
            profile_id = ''
        candidates = []
        outcome = data.get('generation_outcome')
        if isinstance(outcome, dict) and positive_id(outcome.get('camera_id')) == camera_id:
            outputs = outcome.get('outputs')
            for row in outputs[:16] if isinstance(outputs, list) else ():
                if not isinstance(row, dict):
                    continue
                kind, record_id = row.get('kind'), positive_id(row.get('record_id'))
                if (isinstance(kind, str) and kind in allowed and record_id
                        and row.get('status') == 'generated'
                        and positive_id(row.get('camera_id')) == camera_id):
                    candidates.append((kind, record_id, None))
        # Historical video tasks have no structured receipt. Resolve their exact
        # recorded filename in the database; never turn task text into a file URL.
        elif outcome is None and len(allowed) == 1 and getattr(task.state, 'name', task.state) == 'SUCCESS':
            result = task.result
            prefix = 'Generated timelapse: '
            if isinstance(result, str) and result.startswith(prefix):
                try:
                    original = result[len(prefix):]
                    path = Path(original)
                    resolved = (path if path.is_absolute() else self.media_root / path).resolve()
                    relative = resolved.relative_to(self.media_root)
                    candidates.append((next(iter(allowed)), None, (original, str(resolved), str(relative))))
                except (OSError, ValueError, RuntimeError):
                    pass
        links, seen = [], set()
        for kind, record_id, filenames in candidates:
            entry = self.lookup(kind, camera_id, record_id, filenames)
            if entry is None or entry.camera_id != camera_id or not entry.success:
                continue
            key = (kind, entry.id)
            if key in seen:
                continue
            seen.add(key)
            links.append({'label': allowed[kind], 'url': self.url_builder(
                kind=kind, id=entry.id, camera_id=camera_id, profile_id=profile_id)})
        return links
