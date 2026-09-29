"""Manual SQLite library compatibility probe; uses only a new synthetic database.

Run with the candidate library selected for this process, never a production DB.
The printed artifact path is retained for cross-version readback verification.
"""
import concurrent.futures
import hashlib
import json
import pathlib
import sqlite3
import tempfile
import threading
import time

root = pathlib.Path(tempfile.mkdtemp(prefix='hybrid-sqlite-probe-'))
path = root / 'probe.sqlite'
con = sqlite3.connect(path)
con.execute('pragma journal_mode=WAL')
con.execute('create table frames(camera integer, seq integer, payload text, primary key(camera,seq))')
con.commit()
stop = threading.Event()
ready = threading.Event()
checkpoints = []

def checkpoint():
    db = sqlite3.connect(path, timeout=5)
    try:
        db.execute('pragma synchronous=NORMAL')
        ready.set()
        while not stop.is_set():
            checkpoints.append(db.execute('pragma wal_checkpoint(PASSIVE)').fetchone())
            stop.wait(.005)
    finally:
        db.close()

def writer(camera):
    db = sqlite3.connect(path, timeout=5)
    try:
        db.execute('pragma synchronous=NORMAL')
        db.execute('pragma wal_autocheckpoint=0')
        for seq in range(200):
            db.execute('insert into frames values(?,?,?)',(camera,seq,str(camera)+':'+str(seq)+'x'*4096))
            db.commit()
    finally:
        db.close()

with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
    cp = pool.submit(checkpoint)
    assert ready.wait(5)
    try:
        futures = [pool.submit(writer, camera) for camera in (1,2)]
        for future in futures: future.result(timeout=60)
    finally:
        stop.set()
    cp.result(timeout=10)
assert con.execute('pragma integrity_check').fetchall() == [('ok',)]
rows = con.execute('select camera,seq,payload from frames order by camera,seq').fetchall()
assert len(rows) == 400
for camera, seq, payload in rows: assert payload == str(camera)+':'+str(seq)+'x'*4096
assert con.execute('pragma wal_checkpoint(TRUNCATE)').fetchone() == (0,0,0)
con.close()
result = {'version':sqlite3.sqlite_version,'database':str(path),'rows':400,'checkpoint_calls':len(checkpoints),'integrity':'ok','row_sha256':hashlib.sha256(json.dumps(rows).encode()).hexdigest(),'scope':'Synthetic database only. Concurrent writers/passive checkpoints and payload integrity; not exhaustive race reproduction or performance acceptance.'}
print(json.dumps(result))
