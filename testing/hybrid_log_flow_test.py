#!/usr/bin/env python3
"""Rendered log CSRF header, actual reader and authenticated response contract."""
import json
from pathlib import Path
import re
from unittest.mock import patch
from hybrid_runtime_fixture import isolated_app, login_client


def run():
    with isolated_app() as app:
        root = Path(app.config['INDI_ALLSKY_IMAGE_FOLDER'])
        logfile = root / 'synthetic.log'
        logfile.write_text('Header\nCamera 1 ready\nCamera 2 ready\nUpload done\n')

        def path(value, *parts):
            if str(value) == '/var/log/indi-allsky/indi-allsky.log' and not parts:
                return logfile
            return Path(value, *parts)

        with patch('indi_allsky.flask.views.Path', side_effect=path):
            for uid in (1, 2):
                client = login_client(app, uid)
                page = client.get('/indi-allsky/modern-admin/system/log')
                assert page.status_code == 200
                token = json.loads(re.search(r"'X-CSRFToken': (\"[^\"]+\")", page.text)[1])
                endpoint = '/indi-allsky/js/log'
                payload = {'lines': '25', 'filter': ''}
                assert client.post(endpoint, json=payload).status_code == 400
                response = client.post(endpoint, json=payload, headers={'X-CSRFToken': token})
                assert response.status_code == 200 and response.json['log'] == 'Upload done\nCamera 2 ready\nCamera 1 ready\nHeader\n'
                limited = client.post(endpoint, json={'lines': 1}, headers={'X-CSRFToken': token})
                assert limited.json['log'] == 'Upload done\n'
                for bad in ([], {'lines': 0}, {'lines': 'invalid'}, {'filter': '\\'}):
                    rejected = client.post(endpoint, json=bad, headers={'X-CSRFToken': token})
                    assert rejected.status_code == 200 and rejected.json['log'].startswith('ERROR:')
                payload['filter'] = 'Camera 2'
                response = client.post(endpoint, json=payload, headers={'X-CSRFToken': token})
                assert response.json['log'] == 'Camera 2 ready\n'
                payload['filter'] = 'unmatched'
                assert client.post(endpoint, json=payload, headers={'X-CSRFToken': token}).json['log'] == '[No matching lines]'
            logfile.unlink()
            assert client.post(endpoint, json=payload, headers={'X-CSRFToken': token}).json['log'] == 'ERROR: Log file missing'
        assert app.test_client().get('/indi-allsky/modern-admin/system/log').status_code == 302
        print('Log: rendered CSRF, both roles, real reader/filter, absent source and anonymous redirect: PASS')


if __name__ == '__main__':
    run()
