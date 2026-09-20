#!/usr/bin/env python3
"""Every registered Hybrid entry requires login, independently of public flags."""
import argparse
from urllib.parse import urlsplit
from unittest.mock import patch

from hybrid_authenticated_flow_test import FormFields
from hybrid_runtime_fixture import isolated_app


def run(runtime_config):
    with isolated_app(runtime_config, multi_camera=True) as app:
        from werkzeug.routing import IntegerConverter, FloatConverter
        routes = [r for r in app.url_map.iter_rules() if r.rule == '/indi-allsky/modern-admin' or r.rule.startswith('/indi-allsky/modern-admin/')]
        assert len(routes) >= 100, 'Hybrid route coverage unexpectedly shrank'
        checked = []
        for all_views in (False, True):
            for media_views in (False, True):
                app.config.update(INDI_ALLSKY_AUTH_ALL_VIEWS=all_views,
                                  INDI_ALLSKY_AUTH_MEDIA_VIEWS=media_views)
                client = app.test_client()
                token = FormFields(client.get('/indi-allsky/login').text).fields['csrf_token']
                with patch('subprocess.Popen', side_effect=AssertionError('Anonymous Hybrid request ran a process')), \
                     patch('dbus.SystemBus', side_effect=AssertionError('Anonymous request reached hardware')), \
                     patch('dbus.SessionBus', side_effect=AssertionError('Anonymous request reached services')):
                    for rule in routes:
                        values = {name: (1 if isinstance(converter, (IntegerConverter, FloatConverter)) else 'image')
                                  for name, converter in rule._converters.items()}
                        path = app.url_map.bind('localhost').build(rule.endpoint, values)
                        for method in sorted(rule.methods - {'HEAD', 'OPTIONS'}):
                            response = client.open(path, method=method, json={}, headers={'X-CSRFToken': token})
                            hops = 0
                            while response.status_code in (301, 302, 303, 307, 308):
                                target = urlsplit(response.location)
                                assert not target.netloc and not target.scheme, (path, response.location)
                                if target.path == '/indi-allsky/login':
                                    break
                                hops += 1
                                assert hops <= 5, (path, 'redirect loop')
                                response = client.get(response.location)
                            else:
                                # The capture action deliberately has no GET operation.
                                assert (method == 'GET' and path == '/indi-allsky/modern-admin/capture/service'
                                        and response.status_code == 405), (path, method, response.status_code)
                            checked.append((all_views, media_views, rule.endpoint, method))
        print(f'Private Hybrid UI: {len(routes)} routes, {len(checked)} anonymous requests with valid CSRF across all public-auth flag combinations PASS')
        print('This verifies authentication gates, not authenticated effects or public media/API policy.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--runtime-config', default='/etc/indi-allsky/flask.json')
    run(parser.parse_args().runtime_config)
