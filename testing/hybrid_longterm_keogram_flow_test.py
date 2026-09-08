#!/usr/bin/env python3
"""Real long-term sample query, generator, JPEG/cache and Hybrid request flow."""
import base64
from datetime import datetime,timedelta
import io,json,re,hashlib,html
from urllib.parse import urljoin
from pathlib import Path
from unittest.mock import patch
from hybrid_runtime_fixture import isolated_app,login_client


def run():
    with isolated_app(multi_camera=True) as app:
        from PIL import Image
        from indi_allsky.flask import db
        from indi_allsky.flask.models import IndiAllSkyDbLongTermKeogramTable as Sample
        from indi_allsky.longterm_keogram_cache import write_longterm_keogram_cache
        clients=[login_client(app,1),login_client(app,2)]
        root=Path(app.config['INDI_ALLSKY_IMAGE_FOLDER']);url='/indi-allsky/js/longtermkeogram'
        base={'CAMERA_ID':'1','END_SELECT':'today','DAYS_SELECT':'30','PIXELS_SELECT':'5','ALIGNMENT_SELECT':'120','OFFSET_SELECT':'0','REVERSE':False,'LABEL':False}
        page=clients[0].get('/indi-allsky/modern-admin/observatory/long-term-keogram?camera_id=1')
        assert page.status_code==200 and 'longterm-form' in page.text and 'remains unavailable' not in page.text
        token=re.search(r'name="csrf_token"[^>]*value="([^"]+)"',page.text)[1]
        headers={'X-CSRFToken':token}
        anonymous=app.test_client()
        login=anonymous.get('/indi-allsky/login')
        anonymous_token=re.search(r'name="csrf_token"[^>]*value="([^"]+)"',login.text)[1]
        denied=anonymous.post(url,json=base,headers={'X-CSRFToken':anonymous_token})
        assert denied.status_code==302 and '/login' in denied.location
        for invalid_camera in ('bad','0','999'):
            assert clients[0].post(url,json=dict(base,CAMERA_ID=invalid_camera),headers=headers).status_code==400
        assert clients[0].post(url,json=base).status_code==400
        empty=clients[0].post(url,json=dict(base,DAYS_SELECT='42'),headers=headers)
        assert empty.status_code==400 and 'No long-term samples' in empty.json['failure-message']
        assert not list(root.glob('ccd_*'))
        with app.app_context():
            instant=datetime.now().replace(hour=16,minute=0,second=0,microsecond=0)-timedelta(days=1)
            for cid in (1,2):
                for index in range(120):
                    channels={color+str(line):value for line in range(1,6) for color,value in [('r',80*cid),('g',30),('b',20)]}
                    db.session.add(Sample(camera_id=cid,ts=int(instant.timestamp())+index*120,**channels))
            db.session.commit()
        for query, expected in (('camera_id=bad',400),('camera_id=999',404),
                                ('camera_id=1&profile_id=test-profile-2',400),
                                ('profile_id=missing',400)):
            assert clients[0].get('/indi-allsky/modern-admin/observatory/long-term-keogram?'+query).status_code==expected
        profile_page=clients[0].get('/indi-allsky/modern-admin/observatory/long-term-keogram?profile_id=test-profile-2')
        assert re.search(r'name="CAMERA_ID"[^>]*value="2"',profile_page.text)
        results=[]
        for cid,client in enumerate(clients,1):
            page=client.get('/indi-allsky/modern-admin/observatory/long-term-keogram?camera_id='+str(cid))
            assert re.search(r'name="CAMERA_ID"[^>]*value="'+str(cid)+'"',page.text), (cid,page.status_code)
            token=re.search(r'name="csrf_token"[^>]*value="([^"]+)"',page.text)[1];headers={'X-CSRFToken':token}
            with patch('indi_allsky.flask.create_app',return_value=app):
                response=client.post(url,json=dict(base,CAMERA_ID=str(cid),DAYS_SELECT='42'),headers=headers)
            assert response.status_code==200 and not response.json['failure-message'],response.text
            content=base64.b64decode(response.json['image_b64'][0]);cached=root/f'ccd_test-camera-{cid}'/'longterm_keogram.jpg'
            assert cached.read_bytes()==content
            with Image.open(io.BytesIO(content)) as image:
                image.load();assert image.width==720 and image.height>=5
                red=max(image.convert('RGB').tobytes()[::3]);assert abs(red-80*cid)<25,(cid,red)
            page=client.get('/indi-allsky/modern-admin/observatory/long-term-keogram?camera_id='+str(cid))
            assert f'ccd_test-camera-{cid}' in page.text and 'Download JPEG' in page.text, (cid,page.status_code,page.text[-3000:])
            src=html.unescape(re.search(r'id="longterm-image"[^>]*src="([^"]+)"',page.text)[1])
            download=client.get(urljoin(page.request.path,src))
            assert download.status_code==200 and download.data==content,(src,download.status_code)
            before=cached.read_bytes()
            no_period=client.post(url,json=dict(base,CAMERA_ID=str(cid),END_SELECT='lastyear'),headers=headers)
            assert no_period.status_code==400 and cached.read_bytes()==before
            invalid=client.post(url,json=dict(base,CAMERA_ID=str(cid),DAYS_SELECT='bad'),headers=headers)
            assert invalid.status_code==400 and cached.read_bytes()==before
            with patch('indi_allsky.longterm_keogram_cache.os.replace',side_effect=OSError('fixture disk failure')):
                failed=client.post(url,json=dict(base,CAMERA_ID=str(cid)),headers=headers)
            assert failed.json['failure-message'] and cached.read_bytes()==before
            assert not list(cached.parent.glob('.longterm-*'))
            results.append({'camera_id':cid,'bytes':len(content),'sha256':hashlib.sha256(content).hexdigest(),'cached_preview':True,'failed_write_preserves_cache':True})
        try:write_longterm_keogram_cache(root,'../../../escape',b'bad')
        except ValueError:pass
        else:raise AssertionError('Escaping camera cache path accepted')
        print(json.dumps({'scope':'Classic-disabled isolated Flask, real DB samples/generator/JPEG/cache; no live data','results':results,'empty_all_available':'explicit no-data response','csrf':'enforced'},indent=2))

if __name__=='__main__':run()
