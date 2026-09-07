#!/usr/bin/env python3
"""Read public NOAA feeds, update only a disposable camera and record actual results."""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
from hybrid_runtime_fixture import isolated_app


def run(output):
    with isolated_app() as app:
        from indi_allsky.aurora import IndiAllskyAuroraUpdate
        from indi_allsky.flask import db
        from indi_allsky.flask.models import IndiAllSkyDbCameraTable
        with app.app_context():
            camera=db.session.get(IndiAllSkyDbCameraTable,1)
            provider=IndiAllskyAuroraUpdate({})
            result=provider.update(camera)
            evidence={'observed_at':datetime.now(timezone.utc).isoformat(),'scope':'Real public NOAA reads; isolated camera/database, not production metadata or scientific validation','result':result,
                'metadata':{key:value for key,value in camera.data.items() if key.startswith('AURORA_')},
                'solar_wind_urls':[provider.solar_wind_mag_json_url,provider.solar_wind_plasma_json_url]}
            output.write_text(json.dumps(evidence,indent=2)+'\n');print(json.dumps(evidence,indent=2),flush=True)
            assert not result['failed'],result


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path,required=True)
    run(parser.parse_args().output)
