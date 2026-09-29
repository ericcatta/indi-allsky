"""Publish a complete replaceable status snapshot for external readers."""
import json
import os
from pathlib import Path
import tempfile


def publish_status_json(target, status):
    target = Path(target)
    # Serialize before touching the filesystem, including on invalid metadata.
    content = json.dumps(status, indent=4, ensure_ascii=False)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(
                mode='w', encoding='utf-8', dir=target.parent,
                prefix='.indi-status-', delete=False) as stream:
            temporary = Path(stream.name)
            stream.write(content)
        temporary.chmod(0o644)
        # Same-directory replacement prevents readers from seeing truncation.
        # This regenerable snapshot retains the previous non-fsync semantics.
        os.replace(temporary, target)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
