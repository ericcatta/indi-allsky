#!/usr/bin/env python3
"""Encode/decode source-stream videos, including wrap, ordering and failures."""
from datetime import datetime
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest.mock import patch

import cv2
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from indi_allsky.timelapse import TimelapseGenerator
from indi_allsky.timelapse_stream import encode_stream
from indi_allsky.generation_frames import read_generation_frame


frozen=json.loads((Path(__file__).parent/'fixtures/source_timelapse_wrap_legacy.json').read_text())
assert hashlib.sha256(frozen['source'].encode()).hexdigest()==frozen['sha256']
namespace={'__name__':'indi_allsky.timelapse_preprocessor.frozen',
           '__package__':'indi_allsky.timelapse_preprocessor'}
exec(compile(frozen['source'],'frozen-wrap.py','exec'),namespace)
FrozenWrap=namespace['PreProcessorWrapKeogram']


def decoded(path):
    result = subprocess.run(['ffmpeg', '-v', 'error', '-threads', '1', '-i', str(path),
        '-f', 'rawvideo', '-pix_fmt', 'bgr24', 'pipe:1'], capture_output=True, check=True, timeout=30)
    return np.frombuffer(result.stdout, np.uint8).reshape(-1, 48, 64, 3)


with TemporaryDirectory(prefix='hybrid-stream-') as directory:
    root = Path(directory)
    paths = []
    entries = []
    for i in range(12):
        path = root / ('frame-%02d.png' % i)
        pixels = np.full((48,64,3), 45+i*11, np.uint8)
        pixels[:,i:i+3] = (220,20,80)
        assert cv2.imwrite(str(path),pixels)
        os.utime(path,(1000+i,1000+i));paths.append(path)
        missing = root / ('missing-%02d.jpg' % i)
        entries.append(SimpleNamespace(id=i+1, camera_id=1, createDate=datetime.fromtimestamp(1000+i),
            data={'render_source':{}}, getFilesystemPath=lambda path=missing:path))
    before = [hashlib.sha256(p.read_bytes()).hexdigest() for p in paths]
    kg = root/'keogram.png';assert cv2.imwrite(str(kg),np.full((8,24,3),120,np.uint8))
    for kind in ('standard','wrap_keogram'):
        for enabled in (False,True):
            config = {'IMAGE_FILE_TYPE':'png','IMAGE_FOLDER':str(root),'IMAGE_FILE_COMPRESSION':{'jpg':95,'png':3},
                      'TIMELAPSE':{'DEFLICKER':enabled,'IMAGE_CIRCLE':40,'KEOGRAM_RATIO':0.15}}
            legacy = TimelapseGenerator(config,skip_frames=2,pre_processor_class=kind)
            if kind=='wrap_keogram':
                legacy.pre_processor.temp_seqfolder.cleanup()
                legacy._pre_processor=FrozenWrap(config)
            stream = TimelapseGenerator(config,skip_frames=2,pre_processor_class=kind)
            for generator in (legacy,stream):
                generator.pre_processor.keogram=kg
                generator.pre_processor.pre_scale=75
                generator.vf_scale='64:48'
                generator.ffmpeg_extra_options='-threads 1 -filter_threads 1 -preset ultrafast -crf 0'
            a=root/(kind+str(enabled)+'-legacy.mp4');b=root/(kind+str(enabled)+'-stream.mp4')
            legacy.generate(a,paths)
            seen=[]
            def reader(entry,*args):
                seen.append(entry.id)
                return paths[entry.id-1],cv2.imread(str(paths[entry.id-1])),entry.createDate.timestamp()
            with patch('indi_allsky.generation_frames.read_generation_frame',side_effect=reader):
                stream.generate_entries(b,list(reversed(entries)),root,None)
            assert seen==list(range(3,13)), seen
            np.testing.assert_array_equal(decoded(a),decoded(b))
            assert len(decoded(b))==10
            assert not list(stream.pre_processor.seqfolder.iterdir()), 'Stream must not stage the sequence'
            # Mixed archives and all-JPEG/PNG archives retain complete frame lists.
            mixed=[]
            for index,entry in enumerate(entries):
                mixed.append(SimpleNamespace(**{**vars(entry),
                    'getFilesystemPath':(lambda path=paths[index]:path)}))
            ordinary=TimelapseGenerator(config,skip_frames=2,pre_processor_class=kind)
            ordinary.pre_processor.keogram=kg;ordinary.pre_processor.pre_scale=75
            ordinary.vf_scale=stream.vf_scale;ordinary.ffmpeg_extra_options=stream.ffmpeg_extra_options
            c=root/'ordinary.mp4';ordinary.generate_entries(c,list(reversed(mixed)),root,None)
            np.testing.assert_array_equal(decoded(a),decoded(c))
            ordinary.pre_processor.temp_seqfolder.cleanup()
            mixed[4]=entries[4]
            def mixed_reader(entry,*args):
                if Path(entry.getFilesystemPath()).exists():
                    return read_generation_frame(entry,*args)
                return reader(entry,*args)
            with patch('indi_allsky.generation_frames.read_generation_frame',side_effect=mixed_reader):
                stream.generate_entries(b,list(reversed(mixed)),root,None)
            np.testing.assert_array_equal(decoded(a),decoded(b))
            legacy.pre_processor.temp_seqfolder.cleanup();stream.pre_processor.temp_seqfolder.cleanup()
    assert before==[hashlib.sha256(p.read_bytes()).hexdigest() for p in paths]

    # Encoder failure and a missing middle source both reap the child and remove
    # the incomplete output. A future retry must not mistake it for a valid video.
    generator=TimelapseGenerator(config)
    generator.ffmpeg_extra_options='-threads 1 -filter_threads 1 -preset ultrafast'
    children=[];popen=subprocess.Popen
    def tracked(*args,**kwargs):
        child=popen(*args,**kwargs);children.append(child);return child
    def failing_reader(entry,*args):
        if entry.id==3:raise FileNotFoundError('Scientific frame unavailable')
        return paths[entry.id-1],cv2.imread(str(paths[entry.id-1])),entry.createDate.timestamp()
    broken=root/'partial.mp4'
    with patch('indi_allsky.timelapse_stream.subprocess.Popen',side_effect=tracked), patch(
            'indi_allsky.generation_frames.read_generation_frame',side_effect=failing_reader):
        try:generator.generate_entries(broken,entries,root,None)
        except FileNotFoundError:pass
        else:raise AssertionError('Missing source accepted')
    assert not broken.exists() and all(child.poll() is not None for child in children)
    generator.codec='not_a_real_encoder'
    with patch('indi_allsky.generation_frames.read_generation_frame',side_effect=reader):
        try:generator.generate_entries(broken,entries,root,None)
        except (BrokenPipeError,RuntimeError):pass
        except Exception as error:
            from indi_allsky.exceptions import TimelapseException
            assert isinstance(error,TimelapseException),repr(error)
        else:raise AssertionError('Invalid encoder accepted')
    assert not broken.exists()
    # stderr larger than a pipe buffer cannot block frame delivery.
    output=root/'drain.bin'
    command=[sys.executable,'-c',
        'import sys,pathlib;sys.stderr.buffer.write(b"x"*200000);sys.stderr.flush();pathlib.Path(sys.argv[1]).write_bytes(sys.stdin.buffer.read())',str(output)]
    encode_stream(command,iter([b'a'*100000,b'b'*100000]),output,{})
    assert output.read_bytes()==b'a'*100000+b'b'*100000
print('Source streaming: real video parity, wrap, deflicker, order/skip, no sequence, child cleanup and stderr backpressure: PASS')
