"""Application route composition, with an optional Classic frontend."""

from flask import Blueprint


def create_allsky_blueprint(*, enable_classic_ui=True):
    # Importing the Hybrid/shared handlers must never import Classic pages.
    from .views import register_hybrid_routes
    from .views import register_compatibility_routes

    bp_allsky = Blueprint(
        'indi_allsky', __name__, template_folder='templates',
        static_folder='static', url_prefix='/indi-allsky', static_url_path='static',
    )
    register_hybrid_routes(bp_allsky)
    register_compatibility_routes(bp_allsky)
    if enable_classic_ui:
        from .classic_views import register_classic_routes
        register_classic_routes(bp_allsky)
    return bp_allsky
