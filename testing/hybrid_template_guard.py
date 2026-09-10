"""Make Classic templates unavailable during real Hybrid acceptance flows."""
from jinja2 import BaseLoader


class HybridTemplateLoader(BaseLoader):
    def __init__(self, delegate):
        self.delegate = delegate
        self.loaded = set()

    def get_source(self, environment, template):
        # Login is a standalone shared authentication page, not a Classic shell.
        allowed = (template == 'login.html' or
                   template.startswith(('modern_admin/', 'shared/')))
        assert allowed and '..' not in template.split('/'), \
            'Hybrid requested a Classic or unclassified template: ' + template
        source = self.delegate.get_source(environment, template)
        self.loaded.add(template)
        return source


def protect_templates(app):
    app.jinja_env.cache.clear()
    guard = HybridTemplateLoader(app.jinja_env.loader)
    app.jinja_env.loader = guard
    return guard
