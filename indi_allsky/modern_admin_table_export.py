"""Bounded table exports with no filesystem, view or optional Excel dependency."""
import csv
import io
import json
from xml.etree import ElementTree as ET
from zipfile import ZipFile, ZIP_DEFLATED

MAX_PAYLOAD_BYTES = 8 * 1024 * 1024
MAX_CELLS = 200000


def parse_table_payload(value):
    if not isinstance(value, str) or len(value.encode('utf-8')) > MAX_PAYLOAD_BYTES:
        raise ValueError('Export is too large. Narrow the table filters and try again.')
    try:
        payload = json.loads(value)
    except (TypeError, ValueError):
        raise ValueError('Invalid table export.') from None
    if not isinstance(payload, dict):
        raise ValueError('Invalid table export.')
    header, rows = payload.get('header'), payload.get('body')
    if not isinstance(header, list) or not 1 <= len(header) <= 32 or not isinstance(rows, list):
        raise ValueError('Invalid table export.')
    if len(header) * (len(rows) + 1) > MAX_CELLS:
        raise ValueError('Export is too large. Narrow the table filters and try again.')
    if any(not isinstance(row, list) or len(row) != len(header) for row in rows):
        raise ValueError('Invalid table export.')
    if any(not isinstance(cell, str) or len(cell) > 32767 for row in [header, *rows] for cell in row):
        raise ValueError('Invalid table export cell.')
    return [header, *rows]


def export_table(rows, format_name):
    if format_name == 'csv':
        output = io.StringIO(newline='')
        # Prevent a CSV opened in a spreadsheet from executing cell formulas.
        csv.writer(output).writerows([
            ["'" + value if value.lstrip().startswith(('=', '+', '-', '@')) else value for value in row]
            for row in rows
        ])
        return output.getvalue().encode('utf-8-sig'), 'text/csv; charset=utf-8'
    if format_name != 'xlsx':
        raise ValueError('Unsupported export format.')
    ns = 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'
    root = ET.Element('worksheet', xmlns=ns)
    data = ET.SubElement(root, 'sheetData')
    for number, values in enumerate(rows, 1):
        row = ET.SubElement(data, 'row', r=str(number))
        for index, value in enumerate(values):
            # Maximum 32 columns: A..Z, AA..AF.
            column = chr(65 + index) if index < 26 else 'A' + chr(65 + index - 26)
            cell = ET.SubElement(row, 'c', r=column+str(number), t='inlineStr')
            text = ET.SubElement(ET.SubElement(cell, 'is'), 't', {'xml:space':'preserve'})
            # XML 1.0 cannot represent these control characters.
            text.text = ''.join(c for c in value if c in '\t\n\r' or 32 <= ord(c) <= 0xd7ff or 0xe000 <= ord(c) <= 0xfffd or 0x10000 <= ord(c) <= 0x10ffff)
    output = io.BytesIO()
    with ZipFile(output, 'w', ZIP_DEFLATED) as archive:
        archive.writestr('[Content_Types].xml', '''<?xml version="1.0" encoding="UTF-8"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/><Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/><Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/></Types>''')
        archive.writestr('_rels/.rels', '''<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/></Relationships>''')
        archive.writestr('xl/workbook.xml', '''<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><sheets><sheet name="Records" sheetId="1" r:id="rId1"/></sheets></workbook>''')
        archive.writestr('xl/_rels/workbook.xml.rels', '''<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/></Relationships>''')
        archive.writestr('xl/worksheets/sheet1.xml', ET.tostring(root, encoding='utf-8', xml_declaration=True))
    return output.getvalue(), 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
