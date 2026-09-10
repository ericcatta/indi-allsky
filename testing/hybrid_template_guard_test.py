#!/usr/bin/env python3
"""The guard rejects direct, inherited and fallback Classic templates."""
from jinja2 import DictLoader, Environment
from hybrid_template_guard import HybridTemplateLoader


def run():
    source = DictLoader({
        'base.html': 'Classic',
        'modern_admin/good.html': "{% extends 'shared/document.html' %}",
        'shared/document.html': 'Hybrid',
        'login.html': 'Login',
        'modern_admin/bad.html': "{% extends 'base.html' %}",
        'modern_admin/fallback.html': "{% include ['base.html', 'shared/document.html'] ignore missing %}",
    })
    loader = HybridTemplateLoader(source)
    env = Environment(loader=loader)
    assert env.get_template('modern_admin/good.html').render() == 'Hybrid'
    assert env.get_template('login.html').render() == 'Login'
    for name in ('base.html', 'modern_admin/bad.html',
                 'modern_admin/fallback.html', 'modern_admin/../base.html'):
        try:
            env.get_template(name).render()
        except AssertionError as error:
            assert 'Classic or unclassified template' in str(error)
        else:
            raise AssertionError('Classic template was accepted: ' + name)
    assert 'base.html' not in loader.loaded
    print('Hybrid template guard: direct, inherited and fallback Classic loads rejected: PASS')


if __name__ == '__main__':
    run()
