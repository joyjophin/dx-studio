"""Portable source bundles that preserve the creator's saved edits."""
import json
import hashlib
import os
import tempfile
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
from . import __version__
from .paths import contained

SKIP={'.build','stills','__pycache__','.git','.venv','node_modules','.pytest_cache'}

def pack(project, output, include_history=False):
    """Publish a complete bundle atomically; a previous bundle is never replaced."""
    output=Path(output).resolve()
    if output.exists():raise ValueError('Bundle already exists. Choose a new ZIP filename.')
    output.parent.mkdir(parents=True,exist_ok=True)
    fd,temp=tempfile.mkstemp(prefix='.dx-bundle-',suffix='.zip',dir=output.parent);os.close(fd)
    try:
        _write(project,temp,exclude=output,include_history=include_history)
        verify(temp)
        os.link(temp,output)
    finally:Path(temp).unlink(missing_ok=True)
    return output


def _write(project, output, exclude=None, include_history=False):
    project=Path(project).resolve(); output=Path(output).resolve()
    cfg=json.loads((project/'project.json').read_text())
    video=Path(contained(project,cfg.get('output','output.mp4')))
    selected=None
    settings=project/'settings.json'
    if settings.is_file():
        filename=json.loads(settings.read_text()).get('__export',{}).get('file')
        if filename:selected=Path(contained(project,filename))
    files=[]
    for f in sorted(project.rglob('*')):
        if f.is_symlink(): raise ValueError(f"Remove symlinks before sharing: {f.relative_to(project)}")
        rel=f.relative_to(project)
        if any(x in SKIP for x in rel.parts) or any(x.startswith('.') for x in rel.parts): continue
        if f.is_file() and f not in (output,exclude,video,selected) and f.suffix not in {'.pyc','.zip','.onnx','.bin','.lock'}: files.append((f,Path('project')/rel))
    # Check known source references without importing or executing scene.py.
    saved=json.loads(settings.read_text()) if settings.is_file() else {}
    assets=Path(contained(project,cfg.get('assets','assets')))
    refs=[Path(contained(assets,it['file'])) for it in saved.get('__media',[]) if it.get('file')]
    refs.extend(Path(contained(project,take['file'])) for take in [*cfg.get('voice',[]),*saved.get('__voice',[])] if take.get('file'))
    if isinstance(cfg.get('music'),dict) and cfg['music'].get('file'):refs.append(Path(contained(project,cfg['music']['file'])))
    brand=saved.get('__brand_assets',{})
    refs.extend(Path(contained(assets,file)) for file in brand.get('fonts',{}).values())
    if brand.get('logo'):refs.append(Path(contained(assets,brand['logo'])))
    included={f for f,_ in files}
    for source in refs:
        if source not in included:raise ValueError('Bundle source is missing or excluded: '+str(source.relative_to(project))+'. Restore it, or remove the reference before sharing.')
    output.parent.mkdir(parents=True,exist_ok=True)
    engine=Path(__file__).parent
    with ZipFile(output,'w',ZIP_DEFLATED) as z:
        for f,rel in files: z.write(f,str(rel))
        from .history import SettingsHistory
        history=SettingsHistory(project)
        for record in history.list() if include_history else []:
            identifier=record['id']
            z.writestr('project/.dx-studio/versions/'+identifier+'.json',json.dumps(history.get(identifier),ensure_ascii=False))
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
dx_studio=["*.html","*.js","*.css","fonts/*.ttf","fonts/OFL.txt","templates/*/*.py","templates/*/*.json","templates/*/assets/*.flac","template_previews/*.jpg"]
""")
        z.writestr('OPEN-ME.md',f"""# DX Studio project

This bundle includes DX Studio {__version__}, source assets and settings.json (when saved).
Install Python 3.10+, Cairo and FFmpeg as described in the main project README.
Then, from this folder:

    python3 -m venv .venv
    source .venv/bin/activate
    python -m pip install ./engine
    python -m dx_studio doctor
    python -m dx_studio edit project

Project scenes are executable Python. Open only projects from people you trust.
Before installing or opening, verify the archive with an existing DX Studio:

    python -m dx_studio verify-bundle your-project.zip

Verification checks hashes and paths; it does not certify that scene code is safe.
Named settings versions: {'included' if include_history else 'excluded (the current saved edits are included)'}.
Keep the original project as your full backup.
Use the included engine to reproduce this project; upgrade a copy when changing versions.
""")
        records={}
        for info in z.infolist():
            digest=hashlib.sha256()
            with z.open(info.filename) as stream:
                while data:=stream.read(1024*1024):digest.update(data)
            records[info.filename]=digest.hexdigest()
        z.writestr('DX-BUNDLE.json',json.dumps({'format_version':1,'engine_version':__version__,'project_format':cfg.get('format_version',1),'files':records},indent=2))
    return output


def verify(path):
    """Integrity inspection only: no extraction, imports or scene execution."""
    from pathlib import PurePosixPath
    with ZipFile(path) as archive:
        infos=archive.infolist();names=[i.filename for i in infos]
        if len(names)!=len(set(names)):raise ValueError('Bundle contains duplicate paths')
        for info in infos:
            name=PurePosixPath(info.filename)
            if name.is_absolute() or '..' in name.parts or '\\' in info.filename or (info.external_attr>>16)&0o170000==0o120000:raise ValueError('Bundle contains unsafe paths')
        if 'DX-BUNDLE.json' not in names:raise ValueError('This archive has no DX bundle manifest; use its original engine and review its source before opening.')
        if archive.getinfo('DX-BUNDLE.json').file_size>4*1024*1024:raise ValueError('Bundle manifest is too large')
        manifest=json.loads(archive.read('DX-BUNDLE.json'))
        records=manifest.get('files',{})
        if manifest.get('format_version')!=1 or not isinstance(records,dict):raise ValueError('Unsupported bundle manifest')
        if set(records)!=(set(names)-{'DX-BUNDLE.json'}):raise ValueError('Bundle file list differs from its manifest')
        for name,expected in records.items():
            digest=hashlib.sha256()
            with archive.open(name) as stream:
                while data:=stream.read(1024*1024):digest.update(data)
            if digest.hexdigest()!=expected:raise ValueError('Bundle integrity check failed: '+name)
    return {'ok':True,'engine_version':manifest.get('engine_version'),'files':len(records)}
