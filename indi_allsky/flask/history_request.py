"""Validated query controls shared by history pages and their JSON providers."""
from datetime import datetime, timedelta
from flask import abort, request


def query_integer(name, default=None, *, minimum=0, maximum=None):
    raw = request.args.get(name, default)
    if raw is None:
        abort(400, description=f'{name} is required.')
    try:
        value = int(raw)
    except (TypeError, ValueError, OverflowError):
        abort(400, description=f'{name} must be an integer.')
    if minimum is not None and value < minimum:
        abort(400, description=f'{name} must be at least {minimum}.')
    if maximum is not None and value > maximum:
        abort(400, description=f'{name} must be at most {maximum}.')
    return value


def history_timestamp():
    value = query_integer('timestamp', 0, minimum=None)
    if value:
        try:
            moment = datetime.fromtimestamp(value)
            # History can look back seven days and apply a camera time offset.
            # Leave room for that arithmetic and the JSON provider's 3s jitter.
            moment - timedelta(days=8)
            moment + timedelta(days=1)
        except (ValueError, OverflowError, OSError):
            abort(400, description='timestamp is outside the supported history range.')
    return value
