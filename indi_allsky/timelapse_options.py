"""Shared timelapse display-processing policy; original frames are untouched."""


def deflicker_options(config):
    options = config.get('TIMELAPSE') or {}
    enabled = options.get('DEFLICKER', True)
    if not isinstance(enabled, bool):
        raise ValueError('Timelapse deflicker must be enabled or disabled.')
    window = options.get('DEFLICKER_WINDOW', 5)
    if isinstance(window, bool) or window not in (3, 5, 9):
        raise ValueError('Choose a deflicker window of 3, 5 or 9 frames.')
    return enabled, int(window)


def video_filter_arguments(config, scale, extra_options):
    enabled, window = deflicker_options(config)
    # Preserve the existing extra-options tokenization and FFmpeg's last -vf
    # precedence. Add deflicker to that effective chain, not a second -vf.
    extra = extra_options.split(' ') if extra_options else []
    if not enabled:
        return (['-vf', 'scale=' + scale] if scale else []) + extra
    chain = 'scale=' + scale if scale else ''
    remaining = []
    i = 0
    while i < len(extra):
        if extra[i] in ('-vf', '-filter:v', '-filter:v:0'):
            if i + 1 == len(extra):
                raise ValueError('The video filter option is missing its value.')
            chain = extra[i + 1]
            i += 2
        else:
            remaining.append(extra[i])
            i += 1
    filters = 'deflicker=size={}:mode=am'.format(window)
    if chain:
        filters += ',' + chain
    return ['-vf', filters] + remaining
