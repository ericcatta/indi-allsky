"""Admission for handlers whose existing JSON contract requires an object."""
from functools import wraps

from flask import jsonify, request


def json_object_required(error_key='form_global'):
    def decorate(handler):
        @wraps(handler)
        def checked(*args, **kwargs):
            if not isinstance(request.get_json(silent=True), dict):
                return jsonify({error_key: ['Request must be a JSON object.']}), 400
            return handler(*args, **kwargs)
        return checked
    return decorate
