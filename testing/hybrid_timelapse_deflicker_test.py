#!/usr/bin/env python3
"""Encode/decode real timelapses; measure smoothing and preserve originals."""
import hashlib
import os
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory

import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from indi_allsky.timelapse import TimelapseGenerator


def run():
    with TemporaryDirectory(prefix='hybrid-deflicker-') as folder:
        root = Path(folder)
        sources = []
        for i in range(30):
            path = root / ('source-%03d.png' % i)
            Image.new('RGB', (64, 48), (118 if i % 2 else 102,) * 3).save(path)
            os.utime(path, (1000 + i, 1000 + i))
            sources.append(path)
        before = [hashlib.sha256(p.read_bytes()).hexdigest() for p in sources]
        results = {}
        # Missing DEFLICKER key must mean on, including old saved configs.
        for mode, section in (('off', {'DEFLICKER': False}), ('on', {})):
            config = {'IMAGE_FILE_TYPE': 'png', 'TIMELAPSE': section}
            generator = TimelapseGenerator(config)
            generator.vf_scale = '32:24'
            generator.ffmpeg_extra_options = '-threads 1 -filter_threads 1 -preset ultrafast -crf 0'
            video = root / (mode + '.mp4')
            try:
                generator.generate(video, sources)
                decoded = subprocess.run([
                    'ffmpeg', '-v', 'error', '-threads', '1', '-i', str(video),
                    '-f', 'rawvideo', '-pix_fmt', 'gray', 'pipe:1'],
                    capture_output=True, check=True, timeout=30)
                frames = np.frombuffer(decoded.stdout, dtype=np.uint8).reshape(-1, 24, 32)
                assert len(frames) == 30, frames.shape
                results[mode] = frames.mean(axis=(1, 2))
            finally:
                generator.pre_processor.temp_seqfolder.cleanup()
        off = float(np.sqrt(np.mean(np.diff(results['off']) ** 2)))
        on = float(np.sqrt(np.mean(np.diff(results['on']) ** 2)))
        assert off > 10 and on < off * .35, (off, on)
        assert before == [hashlib.sha256(p.read_bytes()).hexdigest() for p in sources]
        print('Deflicker real encoding: PASS; adjacent RMS off=%.3f on=%.3f' % (off, on))


if __name__ == '__main__':
    run()
