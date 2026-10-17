"""Local recent-project index. Reading the library never executes scene code."""
import hashlib
import json
import os
from pathlib import Path
import re
import threading
from datetime import datetime, timezone

from .history import atomic_json


def project_id(path):
    return hashlib.sha256(str(Path(path).resolve()).encode()).hexdigest()[:24]


class ProjectLibrary:
    def __init__(self, path=None):
        if path is None:
            path = os.environ.get('DX_STUDIO_LIBRARY')
        if path is None:
            base = Path(os.environ.get('APPDATA', Path.home()/'.config'))
            path = base/'dx-studio'/'library.json'
        self.path = Path(path).expanduser().resolve()
        self.lock = threading.RLock()

    def read(self):
        if not self.path.exists(): return []
        data = json.loads(self.path.read_text(encoding='utf-8'))
        if data.get('format_version') != 1: raise ValueError('Unsupported project library format')
        return data.get('projects', [])

    def remember(self, folder):
        folder = Path(folder).expanduser().resolve()
        cfg = json.loads((folder/'project.json').read_text(encoding='utf-8'))
        record = {'id':project_id(folder), 'path':str(folder), 'name':cfg.get('name',folder.name),
                  'width':cfg.get('width',1080), 'height':cfg.get('height',1920),
                  'last_opened':datetime.now(timezone.utc).isoformat()}
        with self.lock:
            records = [p for p in self.read() if p['id'] != record['id']]
            self.path.parent.mkdir(parents=True, exist_ok=True)
            atomic_json(self.path, {'format_version':1,'projects':[record]+records[:49]})
        return record

    def list(self):
        with self.lock:
            return [dict(p, missing=not (Path(p['path'])/'project.json').is_file()) for p in self.read()]

    def find(self, identifier):
        if not re.fullmatch(r'[a-f0-9]{24}', identifier): raise ValueError('Unknown project')
        record = next((p for p in self.read() if p['id'] == identifier), None)
        if record is None: raise ValueError('Project is no longer in recents. Open its folder again.')
        return record

    def forget(self, identifier):
        with self.lock:
            records = [p for p in self.read() if p['id'] != identifier]
            self.path.parent.mkdir(parents=True, exist_ok=True)
            atomic_json(self.path, {'format_version':1,'projects':records})


class Workspace:
    def __init__(self, library=None):
        self.library = library or ProjectLibrary()
        self.editors = {}
        self.lock = threading.RLock()

    def open(self, path):
        from .editor import Editor
        folder = Path(path).expanduser().resolve()
        identifier = project_id(folder)
        with self.lock:
            if identifier not in self.editors:
                self.editors[identifier] = Editor(folder)
                self.editors[identifier].lock = self.lock
                if self.editors[identifier].has_audio() and not Path(self.editors[identifier].audio_path).exists(): self.editors[identifier].regen_audio()
            self.library.remember(folder)
            return self.editors[identifier]

    def editor(self, identifier):
        return self.open(self.library.find(identifier)['path']) if identifier not in self.editors else self.editors[identifier]

    def create(self, body):
        from .scaffold import create
        name = str(body.get('name','')).strip()
        if not name or len(name)>120: raise ValueError('Enter a project name of up to 120 characters')
        slug = re.sub(r'[^\w-]+','-',name,flags=re.UNICODE).strip('-')[:80]
        if not slug: raise ValueError('Use letters or numbers in the project name')
        parent = Path(body.get('folder') or Path.home()/'DX Studio Projects').expanduser().resolve()
        folder = create(parent/slug, template=body.get('template','explainer'), format=body.get('format','16:9'),
                        name=name,presenter=body.get('presenter','none'))
        return self.open(folder)

    def thumbnail(self, identifier):
        cache = self.library.path.parent/'thumbnails'/(identifier+'.jpg')
        editor = self.editors.get(identifier)
        if editor is not None:
            data = editor.frame(min(1,editor.pr.duration/2), min(.3,320/editor.pr.width))
            cache.parent.mkdir(parents=True, exist_ok=True)
            cache.write_bytes(data)
            return data
        if cache.is_file(): return cache.read_bytes()
        return None
