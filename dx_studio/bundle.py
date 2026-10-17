"""Portable source bundles that preserve the creator's saved edits."""
import json
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
from . import __version__
from .paths import contained

SKIP={'.build','stills','__pycache__','.git','.venv','node_modules','.pytest_cache'}

def pack(project, output):
    project=Path(project).resolve(); output=Path(output).resolve()
    cfg=json.loads((project/'project.json').read_text())
    video=Path(contained(project,cfg.get('output','output.mp4')))
    files=[]
    for f in sorted(project.rglob('*')):
        if f.is_symlink(): raise ValueError(f"Remove symlinks before sharing: {f.relative_to(project)}")
        rel=f.relative_to(project)
        if any(x in SKIP for x in rel.parts) or any(x.startswith('.') for x in rel.parts): continue
        if f.is_file() and f not in (output,video) and f.suffix not in {'.pyc','.zip','.onnx','.bin'}: files.append((f,Path('project')/rel))
    output.parent.mkdir(parents=True,exist_ok=True)
    engine=Path(__file__).parent
    with ZipFile(output,'w',ZIP_DEFLATED) as z:
        for f,rel in files: z.write(f,str(rel))
        for f in sorted(engine.rglob('*')):
            if f.is_file() and '__pycache__' not in f.parts and f.suffix != '.pyc': z.write(f,str(Path('engine/dx_studio')/f.relative_to(engine)))
        # Reuse installed distribution notices when available, or the source checkout.
        from importlib.metadata import distribution, PackageNotFoundError
        source=engine.parent
        try: dist=distribution('dx-studio')
        except PackageNotFoundError: dist=None
        for name in ['LICENSE','THIRD_PARTY_NOTICES.md']:
            f=source/name
            if f.exists(): z.write(f,'engine/'+name)
            elif dist:
                match=next((x for x in dist.files if str(x).endswith('/licenses/'+name)),None)
                if match: z.write(dist.locate_file(match),'engine/'+name)
                else: raise ValueError(f'Missing installed license notice: {name}')
            else: raise ValueError(f'Missing license notice: {name}')
        z.writestr('engine/pyproject.toml', f"""[build-system]
requires=["setuptools>=77"]
build-backend="setuptools.build_meta"
[project]
name="dx-studio"
version="{__version__}"
requires-python=">=3.10"
license="MIT"
license-files=["LICENSE", "THIRD_PARTY_NOTICES.md", "dx_studio/fonts/OFL.txt"]
dependencies=["cairocffi>=1.7,<2", "uharfbuzz>=0.39,<1", "fonttools>=4.50,<5", "numpy>=1.26,<3", "scipy>=1.12,<2", "Pillow>=10.3,<14", "soundfile>=0.12,<1"]
[project.scripts]
dx-studio="dx_studio.cli:main"
[tool.setuptools.packages.find]
include=["dx_studio*"]
[tool.setuptools.package-data]
dx_studio=["*.html","*.js","fonts/*.ttf","fonts/OFL.txt","templates/*/*.py","templates/*/*.json"]
""")
        z.writestr('OPEN-ME.md',f"""# DX Studio project

This bundle includes DX Studio {__version__}, source assets and settings.json (when saved).
Install Python 3.10+, Cairo and FFmpeg as described in the main project README.
Then, from this folder:

    python3 -m venv .venv
    # macOS/Linux: source .venv/bin/activate
    # Windows (WSL): follow Linux installation in the main repository.
    python -m pip install ./engine
    python -m dx_studio edit project

Project scenes are executable Python. Open only projects from people you trust.
""")
    return output
