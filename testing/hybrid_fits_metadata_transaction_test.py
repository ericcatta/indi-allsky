#!/usr/bin/env python3
"""Exercise FITS metadata retry against a file-backed SQLite writer conflict."""
import ast
from types import SimpleNamespace
from pathlib import Path
import sqlite3
import sys
from tempfile import TemporaryDirectory
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from sqlalchemy import Column, Integer, JSON, create_engine
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import declarative_base, sessionmaker
from indi_allsky.fits_registration import update_fits_metadata

Base = declarative_base()


class Fits(Base):
    __tablename__ = 'fits'
    id = Column(Integer, primary_key=True)
    fileSize = Column(Integer)
    data = Column(JSON)


with TemporaryDirectory() as directory:
    engine = create_engine('sqlite:///' + directory + '/test.sqlite',
                           connect_args={'timeout': 0})
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()
    session.add(Fits(id=1, fileSize=10, data={'old': True}))
    session.commit()
    writer = sqlite3.connect(directory + '/test.sqlite', timeout=0)
    writer.execute('BEGIN IMMEDIATE')
    writer.execute('UPDATE fits SET data=? WHERE id=1', ('{"concurrent":true}',))
    delays = []

    def release(delay):
        delays.append(delay)
        writer.commit()

    recipe = {'version': 1}
    with patch('indi_allsky.sqlite_transactions.time.sleep', release):
        entry = update_fits_metadata(session, Fits, 1, 20, recipe)
    assert delays == [0.1]
    assert entry.fileSize == 20
    assert entry.data == {'concurrent': True, 'render_source': recipe}

    session.rollback()
    writer.execute('BEGIN IMMEDIATE')
    writer.execute('UPDATE fits SET fileSize=fileSize WHERE id=1')
    with patch('indi_allsky.sqlite_transactions.time.sleep') as sleep:
        try:
            update_fits_metadata(session, Fits, 1, 30, None)
        except OperationalError:
            pass
        else:
            raise AssertionError('Persistent contention must propagate')
        assert sleep.call_count == 2
    writer.rollback()
    assert session.get(Fits, 1).fileSize == 20
    assert session.get(Fits, 1).data['render_source'] == recipe
    # Caller can continue using the session after failure.
    update_fits_metadata(session, Fits, 1, 40, None)
    assert session.get(Fits, 1).data == {'concurrent': True, 'render_source': None}
    with patch('indi_allsky.sqlite_transactions.time.sleep') as sleep:
        try:
            update_fits_metadata(session, Fits, 999, 40, recipe)
        except LookupError:
            pass
        else:
            raise AssertionError('Missing source record must not be fabricated')
        assert not sleep.called
    # Exercise the actual worker finalizer without loading camera drivers.
    tree = ast.parse((Path(__file__).resolve().parents[1] / 'indi_allsky/image.py').read_text())
    owner = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == 'ImageWorker')
    method = next(n for n in owner.body if isinstance(n, ast.FunctionDef) and n.name == '_finalize_fits_source')
    publications, uploads = [], []
    source = Path(directory) / 'source.fit'
    source.write_bytes(b'already published source')

    def publish(path, context):
        publications.append(str(path))
        return context

    namespace = {'__package__': 'indi_allsky', 'Path': Path,
                 'db': SimpleNamespace(session=session), 'publish_source_recipe': publish}
    exec(compile(ast.Module(body=[method], type_ignores=[]), 'image.py', 'exec'), namespace)
    finalize = namespace['_finalize_fits_source']
    worker = SimpleNamespace(
        _source_render_recipe=lambda *args: recipe,
        _miscUpload=SimpleNamespace(
            s3_upload_fits=lambda entry, metadata: uploads.append(('s3', entry.id, metadata)),
            upload_fits_image=lambda entry: uploads.append(('upload', entry.id))))
    result = {'db_id': 1, 'path': str(source), 'metadata': {'camera_id': 2}}
    session.rollback()
    writer.execute('BEGIN IMMEDIATE')
    delays.clear()
    with patch.dict(sys.modules, {'indi_allsky.flask.models': SimpleNamespace(IndiAllSkyDbFitsImageTable=Fits)}), \
            patch('indi_allsky.sqlite_transactions.time.sleep', release):
        assert finalize(worker, result, None, None, None) == recipe
    assert len(publications) == 1 and len(uploads) == 2 and delays == [.1]
    assert uploads[0][2]['fileSize'] == source.stat().st_size
    assert source.read_bytes() == b'already published source'
    recipe = {'version': 2}
    session.rollback()
    writer.execute('BEGIN IMMEDIATE')
    with patch.dict(sys.modules, {'indi_allsky.flask.models': SimpleNamespace(IndiAllSkyDbFitsImageTable=Fits)}), \
            patch('indi_allsky.sqlite_transactions.time.sleep'):
        try:
            finalize(worker, result, None, None, None)
        except OperationalError:
            pass
        else:
            raise AssertionError('Failed finalization must not queue uploads')
    writer.rollback()
    assert len(publications) == 2 and len(uploads) == 2
    session.close()
    writer.close()
    engine.dispose()
print('FITS metadata: real contention, concurrent metadata preserved, bounded failure and recovery PASS')
