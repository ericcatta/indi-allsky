#!/usr/bin/env python3
"""Installer preflight: validate a pinned archive before changing storage paths."""
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from indi_allsky.archive_volume import verify_archive


def main():
    try:
        with open(sys.argv[1]) as stream:
            config = json.load(stream)
        verify_archive(config['IMAGE_FOLDER'], config.get('ARCHIVE_VOLUME'), writable=True)
    except (OSError, ValueError, KeyError) as error:
        print('Archive preflight failed: {}'.format(error), file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
