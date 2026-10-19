"""Create source and agent-skill zips from the public source tree only."""
import argparse
import ast
import hashlib
import re
import shutil
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED

ROOT=Path(__file__).resolve().parents[1]
SKIP={'.git','.venv','.codex','.agents','.aws','.ssh','__pycache__','.pytest_cache','.build','stills','dist','build','outputs','projects'}
def main():
    tree=ast.parse((ROOT/'dx_studio/__init__.py').read_text())
    version=next(ast.literal_eval(node.value) for node in tree.body if isinstance(node,ast.Assign) and any(isinstance(target,ast.Name) and target.id=='__version__' for target in node.targets))
    ap=argparse.ArgumentParser();ap.add_argument('--output');ap.add_argument('--distributions',help='Include matching wheel/sdist in the release checksums');a=ap.parse_args()
    declared=re.search(r'^version\s*=\s*"([^"]+)"',(ROOT/'pyproject.toml').read_text(),re.M)
    if not declared or declared[1]!=version:ap.error('Package and engine versions must match')
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
    artifacts=[source,skill]
    if a.distributions:
        distributions=[p for p in sorted(Path(a.distributions).glob('*')) if p.is_file() and ((p.name.endswith('.whl') and ('-'+version+'-') in p.name) or p.name.endswith('-'+version+'.tar.gz'))]
        if len(distributions)!=2:ap.error('Provide exactly one matching wheel and source distribution')
        for path in distributions:
            target=out/path.name
            if target.exists():ap.error('Release artifacts already exist')
            shutil.copy2(path,target);artifacts.append(target)
    sums=''.join(hashlib.sha256(p.read_bytes()).hexdigest()+'  '+p.name+'\n' for p in artifacts)
    (out/'SHA256SUMS').write_text(sums)
if __name__=='__main__':main()
