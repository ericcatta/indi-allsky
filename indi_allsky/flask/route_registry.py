"""Application route composition for Hybrid and shared/public compatibility."""

from flask import Blueprint


def create_allsky_blueprint():
    # Importing the Hybrid/shared handlers must never import Classic pages.
    from .views import register_hybrid_routes
    from .views import register_compatibility_routes

    bp_allsky = Blueprint(
        'indi_allsky', __name__, template_folder='templates',
        static_folder='static', url_prefix='/indi-allsky', static_url_path='static',
    )
    register_hybrid_routes(bp_allsky)
    register_compatibility_routes(bp_allsky)
    from .navigation_redirects import register_navigation_redirects
    register_navigation_redirects(bp_allsky)
    return bp_allsky
