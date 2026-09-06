"""Real Flask fixture: synthetic identities/config, temporary media and memory DB."""
from contextlib import contextmanager
from copy import deepcopy
from datetime import datetime, timezone
import importlib.abc
import json
import os
from pathlib import Path
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
PASSWORD = 'Hybrid-Acceptance-2026!'

class ForbidClassicImport(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname == 'indi_allsky.flask.classic_views':
            raise AssertionError('Hybrid imported Classic views')

@contextmanager
def isolated_app(runtime_config='/etc/indi-allsky/flask.json', *, multi_camera=False):
    sys.path.insert(0, str(ROOT))
    assert 'indi_allsky.flask' not in sys.modules, 'Run this fixture in a fresh process'
    guard = ForbidClassicImport()
    sys.meta_path.insert(0, guard)
    previous = os.environ.get('INDI_ALLSKY_FLASK_CONFIG')
    with tempfile.TemporaryDirectory(prefix='hybrid-acceptance-') as directory:
        from cryptography.fernet import Fernet
        config = json.loads(Path(runtime_config).read_text())
        config.update(HYBRID_ENABLE_CLASSIC_UI=False, SQLALCHEMY_DATABASE_URI='sqlite://',
                      SQLALCHEMY_ENGINE_OPTIONS={}, SQLALCHEMY_BINDS={}, TESTING=True,
                      LOGIN_DISABLED=False, WTF_CSRF_ENABLED=True,
                      SECRET_KEY='isolated-acceptance-session-key', PASSWORD_KEY=Fernet.generate_key().decode(),
                      INDI_ALLSKY_IMAGE_FOLDER=directory)
        path = Path(directory) / 'flask.json'
        path.write_text(json.dumps(config))
        os.environ['INDI_ALLSKY_FLASK_CONFIG'] = str(path)
        try:
            from indi_allsky.flask import create_app, db
            from indi_allsky.flask.models import IndiAllSkyDbConfigTable, IndiAllSkyDbUserTable, IndiAllSkyDbCameraTable
            from indi_allsky.config import IndiAllSkyConfigBase
            from indi_allsky.version import __config_level__
            from passlib.hash import argon2
            app = create_app()
            app.logger.setLevel('CRITICAL')
            with app.app_context():
                db.create_all()
                for uid, admin in ((1, True), (2, False)):
                    db.session.add(IndiAllSkyDbUserTable(id=uid, username='test-user-'+str(uid),
                        password=argon2.hash(PASSWORD), email='test@example.invalid', name='Test User', admin=admin))
                settings = deepcopy(IndiAllSkyConfigBase().base_config)
                settings.update(IMAGE_FOLDER=directory, WEB_EXTRA_TEXT='', IMAGE_EXPORT_FOLDER=directory)
                if multi_camera:
                    settings['MULTI_CAMERA'] = {'profiles': [
                        {'profile_id':'test-profile-'+str(cid), 'enabled':True, 'primary':cid==1,
                         'camera_interface':'indi', 'db_camera_id':cid, 'indi_camera_name':'Test Camera '+str(cid),
                         'exposure_max':10.0+cid, 'gain_night':40.0+cid,
                         'outputs':{'images':True, 'timelapse':True}, 'test_extension':{'preserve':cid}}
                        for cid in (1,2)]}
                db.session.add(IndiAllSkyDbConfigTable(id=1, level=__config_level__, data=settings,
                    note='Synthetic acceptance fixture', user_id=1))
                for cid in (1, 2):
                    db.session.add(IndiAllSkyDbCameraTable(id=cid, uuid='test-camera-'+str(cid),
                        name='Test Camera '+str(cid), friendlyName='Test Camera '+str(cid),
                        connectDate=datetime.now(timezone.utc).replace(tzinfo=None),
                        latitude=46.0, longitude=8.0, elevation=200, nightSunAlt=-6.0,
                        width=640, height=480, bits=16, pixelSize=2.0,
                        minGain=0, maxGain=100, minExposure=0.001, maxExposure=120,
                        minBinning=1, maxBinning=4, lensFocalLength=2.5, lensFocalRatio=2.0,
                        lensImageCircle=480, alt=90, az=0, owner='', location='Test site',
                        s3_prefix='', data={}, local=True))
                db.session.commit()
            yield app
            with app.app_context():
                db.session.remove()
                db.engine.dispose()
        finally:
            if previous is None:
                os.environ.pop('INDI_ALLSKY_FLASK_CONFIG', None)
            else:
                os.environ['INDI_ALLSKY_FLASK_CONFIG'] = previous
            sys.meta_path.remove(guard)

def login_client(app, user_id):
    """Use real login so strong session protection is exercised, not bypassed."""
    from html.parser import HTMLParser
    class Token(HTMLParser):
        value = None
        def handle_starttag(self, tag, attrs):
            attrs = dict(attrs)
            if tag == 'input' and attrs.get('name') == 'csrf_token':
                self.value = attrs['value']
    client = app.test_client()
    parser = Token()
    parser.feed(client.get('/indi-allsky/login').text)
    assert parser.value
    result = client.post('/indi-allsky/login', headers={'X-CSRFToken':parser.value}, json={
        'USERNAME':'test-user-'+str(user_id), 'PASSWORD':PASSWORD, 'NEXT':''})
    assert result.status_code == 200
    return client
