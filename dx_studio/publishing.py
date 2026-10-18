"""Publish a completed video and optional caption sidecar with rollback on failure."""
import os
from pathlib import Path
import uuid
from .paths import file_lock


def publish(video,destination,sidecar=None):
    destination=Path(destination);destination.parent.mkdir(parents=True,exist_ok=True)
    captions=destination.with_suffix('.srt');backup=captions.with_name('.'+captions.name+'.'+uuid.uuid4().hex+'.backup')
    moved=False;installed=False
    with file_lock(str(destination)+'.publish.lock'):
        try:
            if sidecar:
                if captions.exists():os.replace(captions,backup);moved=True
                os.replace(sidecar,captions);installed=True
            os.replace(video,destination)
        except BaseException:
            if installed and captions.exists():captions.unlink()
            if moved:os.replace(backup,captions)
            raise
        finally:
            if backup.exists():backup.unlink()
