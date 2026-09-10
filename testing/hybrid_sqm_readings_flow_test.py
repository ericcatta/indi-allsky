#!/usr/bin/env python3
"""SQM missing, zero, stale and camera-specific measurements without Classic."""
from datetime import datetime, timedelta
from unittest.mock import patch
from flask import template_rendered
from hybrid_runtime_fixture import isolated_app, login_client
from hybrid_generation_fixture import seed_generation


def run():
    with isolated_app(multi_camera=True) as app:
        from indi_allsky.flask import db, views
        from indi_allsky.flask.models import IndiAllSkyDbImageTable as Image, IndiAllSkyDbCameraTable as Camera
        seed_generation(app)
        client = login_client(app, 1)
        with app.app_context():
            for cid in (1, 2):
                db.session.get(Camera, cid).utc_offset = datetime.now().astimezone().utcoffset().total_seconds()
            db.session.query(Image).delete()
            db.session.commit()
        with patch.object(views.ModernAdminSqmView, 'get_astrometric_info', return_value={'moon_phase':37.5}):
            page = client.get('/indi-allsky/modern-admin/observatory/sqm?camera_id=1')
        assert page.status_code == 200
        assert 'No saved image' in page.text, 'Missing SQM readings are not explicitly reported'
        assert '37.5%' in page.text, 'Moon phase must come from astronomy, not absent image metadata'
        assert page.text.count('—') >= 8, 'Missing measurements must not become zero'
        seed_generation(app)
        contexts = []
        def capture_context(sender, template, context, **extra):
            contexts.append(context)
        template_rendered.connect(capture_context, app)
        for uid in (1, 2):
            client = login_client(app, uid)
            for cid in (1, 2):
                for minutes, value, expected_state in ((1, 0, 'current'), (1, None, 'current'),
                                                        (20, 12.5, 'stale'), (40, 12.5, 'stale'),
                                                        (-20, 99, 'missing')):
                    with app.app_context():
                        image = db.session.get(Image, cid)
                        image.createDate = datetime.now() - timedelta(minutes=minutes)
                        image.sqm = value
                        image.stars = None if value is None else int(value)
                        other = db.session.get(Image, 3-cid)
                        other.createDate = datetime.now() - timedelta(seconds=30)
                        other.sqm = 22.2
                        other.stars = 333
                        db.session.commit()
                    with patch.object(views.ModernAdminSqmView, 'get_astrometric_info', return_value={'moon_phase':37.5}):
                        page = client.get('/indi-allsky/modern-admin/observatory/sqm?camera_id=' + str(cid))
                    assert page.status_code == 200
                    context = contexts[-1]
                    assert context['modern_admin_sqm_reading_status']['state'] == expected_state
                    assert context['modern_admin_sqm'] == (None if minutes < 0 else value)
                    summary = context['modern_admin_sqm_summary']
                    assert summary.sqm_avg == (value if 0 < minutes < 30 else None)
                    assert '37.5%' in page.text
                    if value == 0:
                        assert '<h3>0.00</h3>' in page.text and '<h3>0</h3>' in page.text
                    if value is None or minutes < 0:
                        assert page.text.count('—') >= 8
        assert app.test_client().get('/indi-allsky/modern-admin/observatory/sqm').status_code == 302
        print('SQM: missing/null/zero/stale/future readings, both roles/cameras, 30-minute summary and astronomical moon phase: PASS')


if __name__ == '__main__':
    run()
