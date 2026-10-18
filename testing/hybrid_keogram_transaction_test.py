#!/usr/bin/env python3
"""Actual miscDb sample conversion and insertion under a real SQLite lock."""
import ast
from datetime import datetime, timezone
from pathlib import Path
import sqlite3
import sys
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from sqlalchemy import Column, Integer, create_engine
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import declarative_base, sessionmaker

root = Path(__file__).resolve().parents[1]
tree = ast.parse((root / 'indi_allsky/flask/miscDb.py').read_text())
owner = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == 'miscDb')
method = next(n for n in owner.body if isinstance(n, ast.FunctionDef) and n.name == 'add_long_term_keogram_data')
Base = declarative_base()
attrs = {'__tablename__': 'samples', 'id': Column(Integer, primary_key=True),
         'ts': Column(Integer), 'camera_id': Column(Integer)}
attrs.update({color + str(i): Column(Integer) for i in range(1, 6) for color in 'rgb'})
Sample = type('Sample', (Base,), attrs)

with TemporaryDirectory() as folder:
    engine = create_engine('sqlite:///' + folder + '/db.sqlite', connect_args={'timeout': 0})
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()
    scope = {'__package__': 'indi_allsky.flask', 'db': SimpleNamespace(session=session),
             'IndiAllSkyDbLongTermKeogramTable': Sample}
    exec(compile(ast.Module(body=[method], type_ignores=[]), 'miscDb.py', 'exec'), scope)
    add = scope['add_long_term_keogram_data']
    writer = sqlite3.connect(folder + '/db.sqlite', timeout=0)
    writer.execute('BEGIN IMMEDIATE')
    pixels = [(i + .9, i + 1.9, i + 2.9) for i in range(5)]
    delays = []

    def release(delay):
        delays.append(delay)
        writer.commit()

    stamp = datetime(2026, 10, 10, tzinfo=timezone.utc)
    with patch('indi_allsky.sqlite_transactions.time.sleep', release):
        entry = add(None, stamp, 2, pixels)
    assert delays == [.1]
    assert session.query(Sample).count() == 1
    assert (entry.ts, entry.camera_id) == (int(stamp.timestamp()), 2)
    for i, rgb in enumerate(pixels, 1):
        assert tuple(getattr(entry, color + str(i)) for color in 'rgb') == tuple(map(int, rgb))
    session.rollback()
    writer.execute('BEGIN IMMEDIATE')
    with patch('indi_allsky.sqlite_transactions.time.sleep') as sleep:
        try:
            add(None, stamp.timestamp() + 1, 1, pixels)
        except OperationalError:
            pass
        else:
            raise AssertionError('Persistent lock must reach existing worker error handling')
        assert sleep.call_count == 2
    writer.rollback()
    assert session.query(Sample).count() == 1
    recovered = add(None, stamp.timestamp() + 2, 1, pixels)
    assert recovered.camera_id == 1 and session.query(Sample).count() == 2
    session.close()
    writer.close()
    engine.dispose()
print('Keogram: actual conversion, one insert after contention, bounded failure and camera isolation PASS')
