"""Resolve data paths inside a project, including symlink containment."""
from pathlib import Path

def contained(root, value):
    root = Path(root).resolve()
    path = (root / value).resolve()
    if path != root and root not in path.parents:
        raise ValueError(f"Path must stay inside {root.name}: {value}")
    return str(path)
