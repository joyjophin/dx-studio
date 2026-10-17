"""Resolve data paths inside a project, including symlink containment."""
from pathlib import Path

def contained(root, value):
    root = Path(root).resolve()
    path = (root / value).resolve()
    if path != root and root not in path.parents:
        raise ValueError(f"Path must stay inside {root.name}: {value}")
    return str(path)


import contextlib
import os


@contextlib.contextmanager
def file_lock(path):
    """Serialize writers across processes; readers see only completed cache files."""
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    with open(path,'a+b') as lock:
        if os.name=='nt':
            import msvcrt
            lock.seek(0,os.SEEK_END)
            if not lock.tell():lock.write(b'\0');lock.flush()
            lock.seek(0);msvcrt.locking(lock.fileno(),msvcrt.LK_LOCK,1)
        else:
            import fcntl
            fcntl.flock(lock,fcntl.LOCK_EX)
        try:yield
        finally:
            if os.name=='nt':lock.seek(0);msvcrt.locking(lock.fileno(),msvcrt.LK_UNLCK,1)
            else:fcntl.flock(lock,fcntl.LOCK_UN)
