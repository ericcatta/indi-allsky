#!/usr/bin/env python3
"""Atomic FITS recipe publication and integrity across typed/compressed sources."""
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import numpy as np
from astropy.io import fits
from tempfile import TemporaryDirectory
from unittest.mock import patch
from indi_allsky.source_rendering import file_digest
from indi_allsky.fits_context import with_context,read_context
from indi_allsky.source_publication import scientific_digest, publish_source_recipe, read_source_recipe
with TemporaryDirectory() as folder:
 for dtype,shape in ((np.uint8,(3,16,24)),(np.uint16,(16,24)),(np.float32,(16,24))):
  for compressed in (False,True):
   path=Path(folder)/('test.fit.gz' if compressed else 'test.fit')
   pixels=np.arange(np.prod(shape),dtype=dtype).reshape(shape)
   hdus=fits.HDUList([fits.PrimaryHDU(pixels),fits.ImageHDU(np.arange(8),name='EXTRA')])
   ctx={'version':1,'camera_id':2,'exposure_time':'2026-01-01T00:00:00','complete_render_recipe':False}
   with_context(hdus,ctx).writeto(path,overwrite=True)
   original=path.read_bytes();stamp=path.stat().st_mtime_ns
   recipe={'version':1,'basis':{'version':1,'camera_id':2,'source_id':3,'exposure_date':ctx['exposure_time'],'source_sha256':file_digest(path)}}
   scientific=scientific_digest(path)
   with patch('os.replace',side_effect=OSError('fault injection')):
    try:publish_source_recipe(path,recipe)
    except OSError:pass
    else:raise AssertionError('Publication failure hidden')
   assert path.read_bytes()==original
   result=publish_source_recipe(path,recipe)
   assert scientific_digest(path)==scientific and path.stat().st_mtime_ns==stamp
   assert result['basis']['version']==2
   assert read_source_recipe(path)==result
   with fits.open(path) as restored:
    np.testing.assert_array_equal(restored[0].data,pixels)
    np.testing.assert_array_equal(restored['EXTRA'].data,np.arange(8))
    assert read_context(restored)['render_source']==result
   assert publish_source_recipe(path,result)==result
   stable=path.read_bytes()
   bad=dict(result,unexpected='x'*(1024*1024))
   try:publish_source_recipe(path,bad)
   except ValueError:pass
   else:raise AssertionError('Oversized context accepted')
   assert path.read_bytes()==stable
   link=Path(folder)/'symlink.fit';link.symlink_to(path)
   try:publish_source_recipe(link,result)
   except ValueError:pass
   else:raise AssertionError('Symlink publication accepted')
   link.unlink()
   assert path.read_bytes()==stable
   with fits.open(path) as changed:
    replacement=fits.HDUList([h.copy() for h in changed])
   replacement[0].data.flat[0]+=1
   replacement.writeto(path,overwrite=True)
   altered=path.read_bytes()
   try:publish_source_recipe(path,result)
   except ValueError:pass
   else:raise AssertionError('Changed scientific source accepted')
   assert path.read_bytes()==altered

print('Publication probe: typed science pixels/extra HDU/gzip preserved; context complete; failed replace preserves source: PASS')
