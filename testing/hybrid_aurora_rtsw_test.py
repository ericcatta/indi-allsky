#!/usr/bin/env python3
"""Operational-source selection and parity through unchanged scientific methods."""
from datetime import datetime, timedelta, timezone
from hybrid_runtime_fixture import isolated_app


def run():
    with isolated_app() as app:
        from indi_allsky.aurora import IndiAllskyAuroraUpdate
        from indi_allsky.aurora_rtsw import normalize_rtsw
        provider=IndiAllskyAuroraUpdate({})
        now=datetime.now(timezone.utc)
        for kind,fields,newfields,process in (
            ('mag',['bt','bz_gsm'],['bt','bz_gsm'],provider.processSolarWindMagData),
            ('wind',['density','speed','temperature'],['proton_density','proton_speed','proton_temperature'],provider.processSolarWindPlasmaData)):
            rows=[];legacy=[['time_tag',*fields]]
            for index,minutes in enumerate((30,10,5)):
                stamp=now-timedelta(minutes=minutes)
                values=[10+index,20+index,100000+index][:len(fields)]
                row={'time_tag':stamp.isoformat(),'active':True,'source':'operational','overall_quality':0,**dict(zip(newfields,values))}
                rows.append(row);legacy.append([stamp.strftime('%Y-%m-%d %H:%M:%S.%f'),*values])
            rows += [{**rows[-1],'active':False,newfields[0]:999999}, {**rows[-1],'overall_quality':1}, {**rows[-1],newfields[0]:None}, {**rows[-1],'time_tag':'invalid'}]
            converted=normalize_rtsw(list(reversed(rows)),kind)
            assert converted==legacy
            assert process(converted)==process(legacy)
            assert normalize_rtsw(legacy,kind) is legacy
            assert normalize_rtsw([rows[0],rows[0]],kind)==[['time_tag',*fields],legacy[1]]
            for bad in (None,[],[{'active':False}],[{**rows[0],newfields[0]:float('nan')}],[rows[0],{**rows[0],'source':'conflicting'}]):
                try:normalize_rtsw(bad,kind)
                except ValueError:pass
                else:raise AssertionError('Invalid or conflicting records accepted')
        print('RTSW: active/quality selection, timestamp normalization, duplicates/conflicts, absent values and unchanged 20-minute calculation parity: PASS')


if __name__=='__main__':run()
