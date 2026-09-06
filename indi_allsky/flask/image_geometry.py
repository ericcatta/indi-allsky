"""Validated, unsaved geometry drafts shared by the helper and Settings."""
from flask import abort

GEOMETRY_FIELDS = {
    'helper_diameter': ('lens_image_circle', 'LENS_IMAGE_CIRCLE'),
    'helper_offset_x': ('lens_offset_x', 'LENS_OFFSET_X'),
    'helper_offset_y': ('lens_offset_y', 'LENS_OFFSET_Y'),
}


def geometry_draft(args):
    if not any(key in args for key in GEOMETRY_FIELDS):
        return {}
    draft = {}
    for key in GEOMETRY_FIELDS:
        try:
            value = int(args[key])
            if abs(value) > 100000 or key == 'helper_diameter' and value < 1:
                raise ValueError()
        except (KeyError, ValueError, TypeError):
            abort(400, description='Geometry draft requires a positive diameter and whole-pixel offsets between -100000 and 100000.')
        draft[key] = value
    return draft
