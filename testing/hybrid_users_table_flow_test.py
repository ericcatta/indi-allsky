#!/usr/bin/env python3
"""Hybrid users table, detail navigation and safe exports with Classic disabled."""
import csv
from copy import deepcopy
from datetime import datetime, timedelta
from html.parser import HTMLParser
import io
import json
import re
from xml.etree import ElementTree as ET
from zipfile import ZipFile
from hybrid_runtime_fixture import isolated_app, login_client


class UserTable(HTMLParser):
    def __init__(self, text):
        super().__init__()
        self.in_table = False
        self.cell = None
        self.rows = []
        self.headers = []
        self.record = None
        self.feed(text)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'table' and attrs.get('id') == 'modern-users-table':
            self.in_table = True
        if not self.in_table:
            return
        if tag == 'tr':
            self.record = {'attrs': attrs, 'cells': [], 'links': []}
        if tag in ('td', 'th'):
            self.cell = ''
        if tag == 'a':
            self.record['links'].append(attrs['href'])

    def handle_data(self, text):
        if self.cell is not None:
            self.cell += text

    def handle_endtag(self, tag):
        if not self.in_table:
            return
        if tag in ('td', 'th'):
            self.record['cells'].append(self.cell.strip())
            self.cell = None
        if tag == 'tr':
            if 'data-search' in self.record['attrs']:
                self.rows.append(self.record)
            elif not self.headers:
                self.headers = self.record['cells']
        if tag == 'table':
            self.in_table = False


def run():
    with isolated_app(multi_camera=True) as app:
        from indi_allsky.flask import db
        from indi_allsky.flask.models import IndiAllSkyDbUserTable as User
        with app.app_context():
            password = db.session.get(User, 1).password
            for uid in range(3, 29):
                name = {3: '=1+1', 4: 'Éric 星空', 5: '<script>example</script>'}.get(uid, 'User ' + str(uid))
                db.session.add(User(id=uid, username='fixture-user-' + str(uid), password=password,
                    name=name, email='private-mail@example.invalid', apikey='private-key-sentinel',
                    loginIp='private-ip-sentinel', data={'private': 'private-json-sentinel'},
                    active=uid % 2 == 0, staff=uid % 3 == 0, admin=uid % 7 == 0,
                    createDate=datetime(2020, 1, 1) + timedelta(days=uid)))
            db.session.commit()
            # Login itself may update login timestamps. Account content and roles
            # must stay unchanged throughout read/export navigation.
            fields=('id','username','name','password','email','apikey','active','staff','admin','data')
            def snapshot():
                return [{key:deepcopy(getattr(u,key)) for key in fields} for u in User.query.order_by(User.id)]
            before=snapshot()
        results=[]
        for uid in (1, 2):
            client=login_client(app, uid)
            for camera in (1, 2):
                response=client.get('/indi-allsky/modern-admin/users',query_string={'camera_id':camera})
                assert response.status_code==200
                assert 'Legacy fallback' not in response.text and 'User management fallbacks' not in response.text
                assert '28 accounts' in response.text and 'My Account' in response.text
                table=UserTable(response.text)
                assert len(table.rows)==28 and len(table.headers)==9
                assert '<script>example</script>' not in response.text
                for secret in ('private-mail@example.invalid','private-key-sentinel','private-ip-sentinel','private-json-sentinel',password):
                    assert secret not in response.text
                assert len({tuple(r['cells']) for r in table.rows})==28
                for row in (table.rows[0], table.rows[-1]):
                    assert len(row['cells'])==9 and len(row['links'])==1
                    detail=client.get(row['links'][0])
                    assert detail.status_code==200 and row['cells'][2] in detail.text
                    assert ('Not retrievable.' in detail.text)==(uid==1)
                config=json.loads(re.search(r'id="hybrid-operations-table-config">(.*?)</script>',response.text,re.S)[1])
                assert config['table']=='modern-users-table' and config['rowAttribute']=='data-search'
                assert len(config['filters'])==4
                assert {f['attribute'] for f in config['filters']}=={'search','active','staff','admin'}
                assert 'operations-table.js' in response.text and 'DataTables/datatables.min.js' in response.text
                # Match one actual combination of the rendered table filters.
                selected=[r['cells'][:-1] for r in table.rows if r['attrs']['data-active']=='no' and r['attrs']['data-staff']=='yes']
                assert selected and any(r[3]=='=1+1' for r in selected)
                data={'table':json.dumps({'header':table.headers[:-1],'body':selected}), 'csrf_token':config['csrfToken']}
                for fmt in ('csv','xlsx'):
                    exported=client.post(config['exportUrl'],data=dict(data,format=fmt))
                    assert exported.status_code==200 and 'attachment' in exported.headers['Content-Disposition']
                    if fmt=='csv':
                        rows=list(csv.reader(io.StringIO(exported.data.decode('utf-8-sig'))))
                        expected=[table.headers[:-1]]+[["'"+cell if cell.startswith('=') else cell for cell in row] for row in selected]
                        assert rows==expected
                    else:
                        with ZipFile(io.BytesIO(exported.data)) as archive:
                            root=ET.fromstring(archive.read('xl/worksheets/sheet1.xml'))
                            ns={'s':'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
                            assert not root.findall('.//s:f',ns)
                            assert [n.text or '' for n in root.findall('.//s:t',ns)]==[c for row in [table.headers[:-1]]+selected for c in row]
                assert client.post(config['exportUrl'],data={'format':'csv','table':data['table']}).status_code==400
                assert client.get('/indi-allsky/modern-admin/users/99999').status_code==404
                assert client.get('/indi-allsky/modern-admin/account').status_code==200
                results.append({'user_id':uid,'camera_id':camera,'visible_records':28,'exported_filtered_records':len(selected)})
        anonymous=app.test_client()
        assert anonymous.get('/indi-allsky/modern-admin/users').status_code==302
        assert anonymous.get('/indi-allsky/modern-admin/users/1').status_code==302
        login=anonymous.get('/indi-allsky/login')
        token=re.search(r'name="csrf_token"[^>]*value="([^"]+)"',login.text)[1]
        assert anonymous.post(config['exportUrl'],data=dict(data,format='csv',csrf_token=token)).status_code==302
        with app.app_context():
            assert snapshot()==before
        print(json.dumps({'scope':'Classic-disabled isolated Flask; synthetic users only', 'results':results,
                          'exports':'Actual rendered cells, filtered CSV/XLSX values verified; formula-safe',
                          'privacy':'Private fields and password hash excluded', 'mutations':'No account content or role changes',
                          'native_browser':'Not covered by this test'},indent=2))


if __name__=='__main__':
    run()
