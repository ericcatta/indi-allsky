"""Capture and replay the exact formatted text painted on a frame."""
from copy import deepcopy

STYLE_KEYS = (
    'FONT_FACE', 'FONT_AA', 'FONT_SCALE', 'FONT_THICKNESS', 'FONT_OUTLINE',
    'FONT_HEIGHT', 'FONT_X', 'FONT_Y', 'FONT_COLOR', 'PIL_FONT_FILE',
    'PIL_FONT_CUSTOM', 'PIL_FONT_SIZE',
)


def snapshot_label(processor):
    system = processor.config.get('IMAGE_LABEL_SYSTEM', 'pillow')
    mode = 'off' if system not in ('opencv', 'pillow') else ('focus' if processor.focus_mode else 'text')
    return {
        'version': 1, 'mode': mode, 'system': system,
        'text': processor.last_label_text if mode == 'text' else None,
        'style': {key: deepcopy(processor.config['TEXT_PROPERTIES'][key])
                  for key in STYLE_KEYS if key in processor.config['TEXT_PROPERTIES']},
    }


def render_saved_label(processor, snapshot):
    """Use saved text/styles, never reevaluate weather, hooks or the live template.

    The prepared processor still needs the original exposure time for focus labels
    and the referenced font asset. This is label replay, not full frame replay.
    """
    if snapshot.get('version') != 1 or snapshot.get('mode') not in ('text', 'focus', 'off'):
        raise ValueError('Unsupported saved label')
    if snapshot['mode'] == 'text' and not isinstance(snapshot.get('text'), str):
        raise ValueError('Saved label text is unavailable')
    original_config, original_focus = processor.config, processor.focus_mode
    style = snapshot.get('style')
    if not isinstance(style, dict) or not set(STYLE_KEYS).issubset(style):
        raise ValueError('Saved label style is incomplete')
    system = snapshot.get('system')
    if snapshot['mode'] != 'off' and system not in ('opencv', 'pillow'):
        raise ValueError('Unsupported saved label renderer')
    try:
        processor.config = dict(original_config, TEXT_PROPERTIES=deepcopy(style),
                                IMAGE_LABEL_SYSTEM='off' if snapshot['mode'] == 'off' else system)
        processor.focus_mode = snapshot['mode'] == 'focus'
        processor.label_image(label_text=snapshot.get('text'))
    finally:
        processor.config, processor.focus_mode = original_config, original_focus
