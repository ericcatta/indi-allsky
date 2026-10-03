"""Bounded FFmpeg input streaming: one encoded frame, no sequence on disk."""
import os
from pathlib import Path
import subprocess
from threading import Thread

from .exceptions import TimelapseException


def encode_stream(command, frames, output, env):
    """Drain stderr concurrently so a failed encoder cannot deadlock its writer."""
    output = Path(output)
    process = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL,
                               stderr=subprocess.PIPE, env=env, bufsize=0,
                               preexec_fn=lambda: os.nice(19))
    errors = bytearray()

    def drain():
        while True:
            chunk = process.stderr.read(4096)
            if not chunk:
                break
            errors.extend(chunk)
            del errors[:-65536]

    reader = Thread(target=drain, daemon=True)
    reader.start()
    try:
        count = 0
        for frame in frames:
            remaining = memoryview(frame)
            while remaining:
                written = process.stdin.write(remaining)
                if not written:
                    raise BrokenPipeError('FFmpeg input closed')
                remaining = remaining[written:]
            count += 1
        process.stdin.close()
        returncode = process.wait()
        reader.join()
        if not count or returncode:
            raise TimelapseException('FFmpeg failed (%s): %s' % (
                returncode, errors.decode(errors='replace')))
        output.chmod(0o644)
    except BaseException as error:
        if process.poll() is None:
            process.kill()
        process.wait()
        reader.join()
        output.unlink(missing_ok=True)
        if isinstance(error, BrokenPipeError):
            raise TimelapseException('FFmpeg input failed: %s' % errors.decode(errors='replace')) from error
        raise
    finally:
        process.stdin.close()
        process.stderr.close()
