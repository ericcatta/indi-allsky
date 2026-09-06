#!/usr/bin/env python3
"""Hybrid simulator controls render without Classic and never save config."""
import argparse
from pathlib import Path
import re
from hybrid_runtime_fixture import isolated_app, login_client


def run(runtime_config):
    with isolated_app(runtime_config,multi_camera=True) as app:
        from indi_allsky.flask import db
        from indi_allsky.flask.models import IndiAllSkyDbConfigTable, IndiAllSkyDbTaskQueueTable
        from indi_allsky.flask.forms import IndiAllskyCameraSimulatorForm
        data=(Path(__file__).resolve().parents[1]/'indi_allsky/flask/static/modern_admin/camera-simulator-data.js').read_text()
        catalog=set(re.findall(r"^    '([^']+)'\s*:",data,re.M))
        for choices in (IndiAllskyCameraSimulatorForm.LENS_SELECT_choices,IndiAllskyCameraSimulatorForm.SENSOR_SELECT_choices):
            for group in choices.values():
                for value,_label in group: assert value in catalog, value
        route='/indi-allsky/modern-admin/tools/camera-simulator'
        for uid in (1,2):
            client=login_client(app,uid)
            for sensor in ('imx708','imx678'):
                page=client.get(route+'?camera_id=2&profile_id=test-profile-2&sensor='+sensor+'&offset_x=1&offset_y=-25')
                assert page.status_code==200
                assert 'id="image-circle-canvas"' in page.text and 'Copy simulation link' in page.text
                assert 'disabled' not in page.text.split('<form id="hybrid-camera-simulator">')[1].split('</form>')[0]
                assert 'readonly' not in page.text.split('<form id="hybrid-camera-simulator">')[1].split('</form>')[0]
                assert 'value="1"' in page.text and 'value="-25"' in page.text
            for query in ('offset_x=invalid','offset_y=1.25','sensor=not-supported','lens=not-supported'):
                assert client.get(route+'?'+query).status_code==400
            assert client.post(route,json={}).status_code in (400,405)
        with app.app_context():
            assert IndiAllSkyDbConfigTable.query.count()==1
            assert IndiAllSkyDbTaskQueueTable.query.count()==0
        print('Hybrid simulator controls, supported catalog, invalid inputs and no persistence/effects: PASS')

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--runtime-config',default='/etc/indi-allsky/flask.json')
    run(parser.parse_args().runtime_config)
