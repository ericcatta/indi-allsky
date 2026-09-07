#!/usr/bin/env python3
"""Only fully written metadata files may be passed to the upload queue."""
from datetime import datetime,timezone
import json
from pathlib import Path
import sys,tempfile
from unittest.mock import Mock,patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from indi_allsky.end_of_night import prepare_end_of_night_payload as prepare


def run():
    now=datetime(2026,9,7,6,30,tzinfo=timezone.utc)
    with tempfile.TemporaryDirectory() as folder:
        root=Path(folder);foreign=root/'keep.jpg';foreign.write_bytes(b'user media')
        factory=lambda **kwargs:tempfile.NamedTemporaryFile(dir=root,**kwargs)
        args=dict(remote_folder='test/{camera_uuid}/{timestamp:%Y%m%d}/{ts:%H%M}',camera_uuid='camera-2',now=now,temp_factory=factory)
        data={'sunrise':'2026-09-07T06:00:00+00:00','sunset':'2026-09-07T19:00:00+00:00','streamDaytime':True}
        local,remote=prepare(data,**args)
        assert str(remote)=='test/camera-2/20260907/0630/data.json'
        assert local.read_text()==json.dumps(data,indent=4,ensure_ascii=False)
        assert local.stat().st_mode & 0o077==0
        local.unlink()
        spy=Mock(side_effect=factory)
        for invalid in ('{unknown}','{0}','{','{timestamp:bad{format}'):
            try:prepare(data,**dict(args,remote_folder=invalid,temp_factory=spy))
            except (KeyError,ValueError,IndexError):pass
            else:raise AssertionError(invalid)
        spy.assert_not_called()
        for failure in (TypeError('serialize failure'),OSError('disk full')):
            def fail_dump(value,stream,**kwargs):stream.write('partial');raise failure
            with patch('indi_allsky.end_of_night.json.dump',side_effect=fail_dump):
                try:prepare(data,**args)
                except type(failure):pass
                else:raise AssertionError('Write failure swallowed')
            assert list(root.iterdir())==[foreign]
        with patch('indi_allsky.end_of_night.json.dump',side_effect=KeyboardInterrupt):
            try:prepare(data,**args)
            except KeyboardInterrupt:pass
        assert list(root.iterdir())==[foreign] and foreign.read_bytes()==b'user media'
    print('EndOfNight payload: formatting before allocation, exact JSON/path, private file mode, partial-write/interruption cleanup, unrelated file preservation: PASS')

if __name__=='__main__':run()
