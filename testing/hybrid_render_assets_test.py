#!/usr/bin/env python3
"""Lossless asset identity, atomic deduplication and constrained readers."""
import sys
import io
import zipfile
from unittest.mock import patch
from pathlib import Path
from tempfile import TemporaryDirectory
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from indi_allsky.render_assets import RenderAssetStore
with TemporaryDirectory() as root:
    store=RenderAssetStore(root)
    pixels=np.arange(48,dtype=np.uint8).reshape(4,4,3)
    alpha=np.arange(16,dtype=np.float64).reshape(4,4)/255
    key=store.put(pixels=pixels,alpha=alpha)
    assert key==store.put(alpha=alpha,pixels=pixels)
    assert len(list(Path(root).glob('*.npz')))==1
    saved=store.get(key)
    np.testing.assert_array_equal(saved['pixels'],pixels)
    np.testing.assert_array_equal(saved['alpha'],alpha)
    assert not list(Path(root).glob('*.part'))
    for invalid in ('../outside','a'*63,'/'+'a'*64):
        try:store.get(invalid)
        except ValueError:pass
        else:raise AssertionError('Invalid identity accepted')
    try:store.put(objects=np.array([{'x':1}],dtype=object))
    except ValueError:pass
    else:raise AssertionError('Object array accepted')
    path=Path(root)/(key+'.npz')
    np.savez_compressed(path,pixels=pixels+1,alpha=alpha)
    try:store.get(key)
    except ValueError:pass
    else:raise AssertionError('Corruption accepted')
    # A tiny ZIP can declare an enormous array: reject before allocation.
    header = io.BytesIO()
    np.lib.format.write_array_header_1_0(header, {
        'descr': '<f8', 'fortran_order': False, 'shape': (1024, 1024, 1024)})
    with zipfile.ZipFile(path, 'w') as archive:
        archive.writestr('pixels.npy', header.getvalue())
    with patch('numpy.load', side_effect=AssertionError('Unbounded allocation attempted')):
        try: store.get(key)
        except ValueError: pass
        else: raise AssertionError('Oversized declared array accepted')
print('Render assets: exact typed arrays, stable identity, deduplication, atomic cleanup, path/object/corruption rejection: PASS')
