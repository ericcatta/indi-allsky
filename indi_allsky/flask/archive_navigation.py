"""Return from media details to a local, filtered Hybrid archive page."""
from urllib.parse import parse_qsl, urlsplit
from flask import url_for

_ARCHIVE_ENDPOINTS = (
    'indi_allsky.modern_admin_library_view',
    'indi_allsky.modern_admin_media_archive_view',
)
_QUERY_KEYS = frozenset(('kind', 'camera_id', 'profile_id', 'start', 'end',
                         'search', 'period', 'uploaded', 'sort', 'cursor', 'direction'))


def archive_return_url(value):
    """Rebuild only recognized local archive links; never trust a return URL."""
    if not isinstance(value, str) or len(value) > 4096:
        return None
    if any(ord(char) < 32 for char in value) or '\\' in value:
        return None
    try:
        parts = urlsplit(value)
        if parts.scheme or parts.netloc or parts.fragment:
            return None
        endpoint = next((name for name in _ARCHIVE_ENDPOINTS
                         if parts.path == url_for(name)), None)
        if not endpoint:
            return None
        pairs = parse_qsl(parts.query, keep_blank_values=True, max_num_fields=12)
        values = dict(pairs)
        if len(values) != len(pairs) or not set(values) <= _QUERY_KEYS:
            return None
        return url_for(endpoint, **values)
    except ValueError:
        return None
