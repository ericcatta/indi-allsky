#!/usr/bin/env python3
"""Real SQLite BUSY/BUSY_SNAPSHOT retries emit bounded metadata only."""
from pathlib import Path
import sqlite3
import tempfile
from unittest.mock import patch

from sqlalchemy import Column, create_engine, Integer, select
from sqlalchemy.orm import declarative_base, Session

from indi_allsky.sqlite_transactions import insert_with_retry


Base = declarative_base()


class Row(Base):
    __tablename__ = 'row'
    id = Column(Integer, primary_key=True)
    value = Column(Integer, nullable=False)


with tempfile.TemporaryDirectory(prefix='hybrid-sqlite-retry-') as folder:
    database = str(Path(folder) / 'retry.sqlite')
    engine = create_engine('sqlite:///' + database, connect_args={'timeout': 0})
    Base.metadata.create_all(engine)
    with engine.begin() as connection:
        connection.exec_driver_sql('PRAGMA journal_mode=WAL')
        connection.execute(Row.__table__.insert(), {'id': 1, 'value': 1})

    # A separate immediate writer produces SQLITE_BUSY. Release it only after
    # the first bounded diagnostic so the replay succeeds.
    session = Session(engine)
    writer = sqlite3.connect(database, timeout=0)
    writer.execute('BEGIN IMMEDIATE')
    writer.execute('UPDATE row SET value=2 WHERE id=1')
    with patch('indi_allsky.sqlite_transactions.time.sleep', side_effect=lambda delay: writer.commit()), \
            patch('indi_allsky.sqlite_transactions.logger.warning') as warning:
        insert_with_retry(session, Row, {'id': 2, 'value': 2})
    assert warning.call_count == 1
    args = warning.call_args.args
    assert args[1] == 1 and args[4] == sqlite3.SQLITE_BUSY and args[5] == sqlite3.SQLITE_BUSY
    writer.close()
    session.close()

    # A stale WAL read snapshot upgraded after another writer commits produces
    # SQLITE_BUSY_SNAPSHOT. Rollback must replay on a fresh snapshot, while the
    # diagnostic exposes extended and base codes without SQL parameters.
    session = Session(engine)
    session.connection().exec_driver_sql('BEGIN')
    assert session.execute(select(Row.value).where(Row.id == 1)).scalar_one() == 2
    writer = sqlite3.connect(database, timeout=0)
    writer.execute('PRAGMA journal_mode=WAL')
    writer.execute('UPDATE row SET value=3 WHERE id=1')
    writer.commit()
    with patch('indi_allsky.sqlite_transactions.time.sleep'), \
            patch('indi_allsky.sqlite_transactions.logger.warning') as warning:
        insert_with_retry(session, Row, {'id': 3, 'value': 3})
    assert warning.call_count == 1
    args = warning.call_args.args
    assert args[1] == 1 and args[4] == sqlite3.SQLITE_BUSY_SNAPSHOT and args[5] == sqlite3.SQLITE_BUSY
    assert 'INSERT' not in args[0] and 'parameters' not in args[0]
    writer.close()
    session.close()
    engine.dispose()

print('SQLite retry diagnostics: real BUSY and BUSY_SNAPSHOT metadata with bounded recovery PASS')
