#!/usr/bin/env python3
import csv
import importlib.util
import io
import json
from pathlib import Path
from xml.etree import ElementTree as ET
from zipfile import ZipFile

path=Path(__file__).resolve().parents[1]/'indi_allsky/modern_admin_table_export.py'
spec=importlib.util.spec_from_file_location('table_export',path)
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
rows=module.parse_table_payload(json.dumps({'header':['ID','Text'],'body':[['205','line\nquoted "é"'],['206','=SUM(A1)'],['207','  @formula']]}))
content,mime=module.export_table(rows,'csv')
parsed=list(csv.reader(io.StringIO(content.decode('utf-8-sig'))))
assert parsed[1]==rows[1]
assert parsed[2][1]=="'=SUM(A1)" and parsed[3][1]=="'  @formula"
content,mime=module.export_table(rows,'xlsx')
with ZipFile(io.BytesIO(content)) as archive:
    for name in archive.namelist(): ET.fromstring(archive.read(name))
    root=ET.fromstring(archive.read('xl/worksheets/sheet1.xml'))
    ns={'s':'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
    assert [text.text for text in root.findall('.//s:t',ns)]==[cell for row in rows for cell in row]
    assert not root.findall('.//s:f',ns), 'Excel values must never become formulas'
for invalid in ('null','{}','[]','invalid',json.dumps({'header':['A'],'body':[['A','B']]}),json.dumps({'header':['A'],'body':[[42]]})):
    try: module.parse_table_payload(invalid)
    except ValueError: pass
    else: raise AssertionError(invalid)
try: module.parse_table_payload(' '*(module.MAX_PAYLOAD_BYTES+1))
except ValueError: pass
else: raise AssertionError('Oversize export accepted')
print('Hybrid CSV/XLSX export content, shape, bounds and formula safety: PASS')
