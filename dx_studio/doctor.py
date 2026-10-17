"""Actionable dependency diagnostics; no installs or network requests."""
import importlib
import shutil
import sys

def doctor():
    ok=True
    print(f"Python {sys.version.split()[0]}")
    for module in ['dx_studio._cairo','uharfbuzz','fontTools','numpy','scipy','PIL','soundfile']:
        try: importlib.import_module(module); print(f"  OK {module}")
        except (ImportError,OSError,RuntimeError) as exc: print(f"  MISSING {module}: {exc}");ok=False
    for tool in ['ffmpeg','ffprobe']:
        found=shutil.which(tool)
        print(f"  {'OK' if found else 'MISSING'} {tool}: {found or 'install FFmpeg; see docs/INSTALL.md'}")
        ok=ok and bool(found)
    return 0 if ok else 1
