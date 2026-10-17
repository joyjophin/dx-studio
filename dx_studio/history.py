"""Durable editable-setting snapshots, independent of scene execution.

Versions contain settings, not copies of scene code or source media. The settings
file remains the public handoff used by the CLI and portable project bundles.
"""
import contextlib
import hashlib
import json
import os
from pathlib import Path
import re
import tempfile
import time
from datetime import datetime, timezone
from uuid import uuid4

from .paths import contained


def atomic_json(path, value):
    path = Path(path)
    data = json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False)
    fd, temporary = tempfile.mkstemp(dir=path.parent, prefix='.dx-write-', suffix='.tmp')
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
        # A directory sync makes the replacement durable on supported POSIX filesystems.
        if os.name != 'nt':
            directory = os.open(path.parent, os.O_RDONLY)
            try: os.fsync(directory)
            finally: os.close(directory)
    finally:
        if os.path.exists(temporary): os.unlink(temporary)


class SaveConflict(Exception):
    """Another writer changed settings since the client last acknowledged them."""


class SettingsHistory:
    AUTO_INTERVAL = 60
    AUTO_LIMIT = 30

    def __init__(self, project):
        self.project = Path(project).resolve()
        self.settings = Path(contained(self.project, 'settings.json'))
        self.root = Path(contained(self.project, '.dx-studio'))
        self.directory = Path(contained(self.project, '.dx-studio/versions'))

    @contextlib.contextmanager
    def writing(self):
        self.directory.mkdir(parents=True, exist_ok=True)
        with open(contained(self.project, '.dx-studio/write.lock'), 'a+b') as lock:
            if os.name == 'nt':
                import msvcrt
                lock.seek(0, os.SEEK_END)
                if not lock.tell(): lock.write(b'\0'); lock.flush()
                lock.seek(0)
                msvcrt.locking(lock.fileno(), msvcrt.LK_LOCK, 1)
            else:
                import fcntl
                fcntl.flock(lock, fcntl.LOCK_EX)
            try: yield
            finally:
                if os.name == 'nt':
                    lock.seek(0); msvcrt.locking(lock.fileno(), msvcrt.LK_UNLCK, 1)
                else: fcntl.flock(lock, fcntl.LOCK_UN)

    def revision(self):
        return hashlib.sha256(self.settings.read_bytes() if self.settings.exists() else b'').hexdigest()

    def read_settings(self):
        return json.loads(self.settings.read_text(encoding='utf-8')) if self.settings.exists() else {}

    def check(self, expected):
        if expected is not None and expected != self.revision():
            raise SaveConflict('This project was saved in another window or application. Your draft is kept in this browser. Reload the saved project before continuing.')

    def list(self):
        if not self.directory.exists(): return []
        records = []
        for path in self.directory.glob('*.json'):
            try:
                record = self.get(path.stem)
                records.append({k: record[k] for k in ('id', 'name', 'kind', 'created_at', 'source_revision')})
            except (ValueError, OSError, KeyError, json.JSONDecodeError):
                continue  # One damaged snapshot must not hide all other versions.
        return sorted(records, key=lambda record: (record['created_at'], record['id']), reverse=True)

    def get(self, version_id):
        if not isinstance(version_id, str) or not re.fullmatch(r'[a-f0-9]{32}', version_id):
            raise ValueError('Invalid version ID')
        path = Path(contained(self.project, f'.dx-studio/versions/{version_id}.json'))
        if not path.exists(): raise ValueError('Version not found')
        record = json.loads(path.read_text(encoding='utf-8'))
        if not isinstance(record, dict) or record.get('format_version') != 1 or record.get('id') != version_id or not isinstance(record.get('settings'), dict):
            raise ValueError('Unsupported or damaged version')
        if any(not isinstance(record.get(key), str) for key in ('name', 'kind', 'created_at', 'source_revision')):
            raise ValueError('Damaged version metadata')
        if datetime.fromisoformat(record['created_at']).tzinfo is None:
            raise ValueError('Version timestamp must include its timezone')
        return record

    def snapshot(self, settings, source_revision, name, kind='named'):
        if not isinstance(name, str) or not name.strip() or len(name.strip()) > 120:
            raise ValueError('Give this version a name between 1 and 120 characters')
        record = {'format_version': 1, 'id': uuid4().hex, 'name': name.strip(), 'kind': kind,
                  'created_at': datetime.now(timezone.utc).isoformat(),
                  'source_revision': source_revision, 'settings': settings}
        atomic_json(self.directory / (record['id'] + '.json'), record)
        return record

    def before_save(self, source_revision):
        versions = self.list()
        if not versions:
            self.snapshot(self.read_settings(), source_revision, 'Before the first autosave', 'initial')
            return
        automatic = [v for v in versions if v['kind'] in ('automatic', 'initial')]
        if not automatic or time.time() - datetime.fromisoformat(automatic[0]['created_at']).timestamp() >= self.AUTO_INTERVAL:
            self.snapshot(self.read_settings(), source_revision, 'Automatic backup', 'automatic')
            # Named versions and the initial version are never automatically removed.
            for version in [v for v in self.list() if v['kind'] == 'automatic'][self.AUTO_LIMIT:]:
                Path(contained(self.project, f".dx-studio/versions/{version['id']}.json")).unlink()
