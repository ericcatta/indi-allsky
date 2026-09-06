#!/usr/bin/env python3
"""Now renders runtime evidence and useful links, never prototype panels."""
import html
import re
from unittest.mock import patch
from hybrid_runtime_fixture import isolated_app, login_client
from hybrid_generation_fixture import seed_generation
from hybrid_generated_media_fixture import seed_generated_media


def run():
    with isolated_app(multi_camera=True) as app:
        seed_generation(app);seed_generated_media(app)
        from indi_allsky.flask.views import ModernAdminNowView
        endpoint='/indi-allsky/modern-admin/now'
        for uid in (1,2):
            client=login_client(app,uid)
            response=client.get(endpoint)
            assert response.status_code==200,response.text[:500]
            assert 'Snapshot at page load' in response.text
            assert response.text.count('>Browse camera images</a>')==2
            assert 'now-frame-error' in response.text
            for removed in ('Placeholder answers','Static briefing','placeholder-only','now-outputs-title','now-health-title','now-questions-title'):
                assert removed not in response.text,removed
            for label in ('Browse camera images','Browse these outputs','Inspect FITS sources','Inspect RAW sources'):
                matches=re.findall(r'href="([^"]+)"\s*>'+label+'</a>',response.text)
                assert matches,label
                for target in matches:
                    page=client.get(html.unescape(target))
                    assert page.status_code==200,page.text[:500]
            with patch.object(ModernAdminNowView,'get_latest_camera_frames_provider',return_value=None):
                missing=client.get(endpoint)
                assert missing.status_code==200 and 'No camera frame metadata is available.' in missing.text
                assert '>Browse camera images</a>' not in missing.text
        assert app.test_client().get(endpoint).status_code==302
        print('Now: real camera/source/output links, both roles, no prototype panels or fake camera slots, provider fallback and authentication: PASS')


if __name__=='__main__':run()
