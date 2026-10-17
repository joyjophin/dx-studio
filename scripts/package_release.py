"""Create source and agent-skill zips from the public source tree only."""
import argparse
import ast
import hashlib
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED

ROOT=Path(__file__).resolve().parents[1]
SKIP={'.git','.venv','__pycache__','.pytest_cache','.build','stills','dist','build','outputs','projects'}
def main():
    tree=ast.parse((ROOT/'dx_studio/__init__.py').read_text())
    version=next(ast.literal_eval(node.value) for node in tree.body if isinstance(node,ast.Assign) and any(isinstance(target,ast.Name) and target.id=='__version__' for target in node.targets))
    ap=argparse.ArgumentParser();ap.add_argument('--output');a=ap.parse_args()
    out=Path(a.output).resolve() if a.output else ROOT.parent/'release-artifacts'/version
    if out==ROOT or ROOT in out.parents:ap.error('Write release artifacts outside the repository')
    out.mkdir(parents=True,exist_ok=True)
    files=[p for p in sorted(ROOT.rglob('*')) if p.is_file() and not p.is_symlink()
           and not any(x in SKIP or x.endswith('.egg-info') for x in p.relative_to(ROOT).parts)
           and p.name!='.DS_Store' and not p.name.startswith('.env')]
    source=out/f'dx-studio-{version}-source.zip'
    skill=out/'dx-studio-video.zip'
    if any(path.exists() for path in [source,skill,out/'SHA256SUMS']):ap.error('Choose an empty output directory; existing release artifacts are never overwritten')
    for archive,prefix in [(source,'dx-studio'),(skill,'dx-studio-video')]:
        with ZipFile(archive,'w',ZIP_DEFLATED) as z:
            for p in files:z.write(p,str(Path(prefix)/p.relative_to(ROOT)))
        print(archive)
    sums=''.join(hashlib.sha256(p.read_bytes()).hexdigest()+'  '+p.name+'\n' for p in [source,skill])
    (out/'SHA256SUMS').write_text(sums)
if __name__=='__main__':main()
