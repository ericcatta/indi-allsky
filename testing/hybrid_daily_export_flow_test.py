#!/usr/bin/env python3
"""HTTP export contents from rendered daily tables; not native download receipt."""
import csv
import io
import json
import re
from datetime import date
from html.parser import HTMLParser
from xml.etree import ElementTree as ET
from zipfile import ZipFile
from hybrid_runtime_fixture import isolated_app, login_client


class Table(HTMLParser):
    def __init__(self, html):
        super().__init__(); self.inside=False; self.cell=None; self.rows=[]; self.feed(html)
    def handle_starttag(self, tag, attrs):
        if tag=='table': self.inside=dict(attrs).get('id')=='file-space-table'
        if self.inside:
            if tag=='tr': self.row=[]
            if tag in ('td','th'): self.cell=[]
    def handle_data(self, text):
        if self.cell is not None: self.cell.append(text)
    def handle_endtag(self, tag):
        if self.inside:
            if tag in ('td','th') and self.cell is not None:
                self.row.append(''.join(self.cell).strip());self.cell=None
            if tag=='tr': self.rows.append(self.row)
        if tag=='table': self.inside=False


def decode(response, kind):
    assert response.status_code==200,response.text[:200]
    assert 'attachment;' in response.headers['Content-Disposition']
    assert 'hybrid-records.'+kind in response.headers['Content-Disposition']
    if kind=='csv':
        assert response.mimetype=='text/csv'
        return list(csv.reader(io.StringIO(response.data.decode('utf-8-sig'))))
    assert response.mimetype=='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    with ZipFile(io.BytesIO(response.data)) as archive:
        tree=ET.fromstring(archive.read('xl/worksheets/sheet1.xml'))
        ns={'s':'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
        assert not tree.findall('.//s:f',ns)
        return [[cell.find('s:is/s:t',ns).text or '' for cell in row]
                for row in tree.findall('s:sheetData/s:row',ns)]


def run():
    with isolated_app(multi_camera=True) as app:
        from indi_allsky.flask import db
        from indi_allsky.flask.models import IndiAllSkyDbImageTable as Image
        with app.app_context():
            for cid in (1,2):
                for night in (False,True):
                    db.session.add(Image(filename=f'export-{cid}-{night}',camera_id=cid,
                        dayDate=date(2026,9,12),night=night,exposure=1,gain=0,adu=.1,
                        fileSize=cid*1024*1024 if night else None))
            db.session.commit()
        url='/indi-allsky/modern-admin/operations/export'
        for uid in (1,2):
            client=login_client(app,uid)
            for cid in (1,2):
                page=client.get('/indi-allsky/modern-admin/storage/file-space-usage'
                                f'?camera_id={cid}&profile_id=test-profile-{cid}')
                assert page.status_code==200
                cfg=json.loads(re.search(r'id="hybrid-operations-table-config" type="application/json">(.*?)</script>',page.text,re.S)[1])
                table=Table(page.text).rows
                assert len(table)==3 and all(len(row)==14 for row in table)
                assert cfg['exportColumns']==list(range(14))
                assert any('size unknown' in cell for row in table for cell in row)
                for rows in (table[1:], [r for r in table[1:] if r[1]=='Night'], []):
                    data={'csrf_token':cfg['csrfToken'],'table':json.dumps({'header':table[0],'body':rows})}
                    for kind in ('csv','xlsx'):
                        response=client.post(url,data={**data,'format':kind})
                        assert decode(response,kind)==[table[0],*rows]
                assert client.get(url).status_code==405
                for data in ({'format':'csv','table':'{}'},
                             {'csrf_token':cfg['csrfToken'],'format':'pdf','table':json.dumps({'header':['A'],'body':[]})}):
                    response=client.post(url,data=data)
                    assert response.status_code==400 and 'attachment' not in response.headers.get('Content-Disposition','')
        anonymous=app.test_client()
        page=anonymous.get('/indi-allsky/login')
        token=re.search(r'name="csrf_token"[^>]*value="([^"]+)"',page.text)[1]
        response=anonymous.post(url,data={'csrf_token':token,'format':'csv',
                    'table':json.dumps({'header':['A'],'body':[['private']]})})
        assert response.status_code==302 and 'attachment' not in response.headers.get('Content-Disposition','')
        print('Daily exports PASS: rendered fourteen-column CSV/XLSX contents, both cameras/roles, full/filtered/empty payloads, unknown sizes, CSRF/authentication/method/format guards')


if __name__=='__main__': run()
