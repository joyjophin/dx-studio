"""Review missing project sources against a folder; never overwrite an existing file."""
import os
from pathlib import Path
import shutil
import tempfile
from .paths import contained


def references(project):
    refs={}
    def add(root,file,kind):
        if file: refs[contained(root,file)]=kind
    for item in project.values.get('__media',[]): add(project.media.assets,item.get('file'),'media')
    for take in project.voices(): add(project.path,take.get('file'),'audio')
    for take in project.cfg.get('voice',[]): add(project.path,take.get('file'),'audio')
    music=project.cfg.get('music')
    if isinstance(music,dict): add(project.path,music.get('file'),'audio')
    assets=project.values.get('__brand_assets',{})
    for file in assets.get('fonts',{}).values(): add(project.media.assets,file,'font')
    add(project.media.assets,assets.get('logo'),'media')
    return refs


def validate_source(path,kind):
    if kind=='audio':
        import soundfile as sf
        sf.info(path)
    elif kind=='font':
        from fontTools.ttLib import TTFont
        font=TTFont(path);font.getGlyphSet();font.close()
    else:
        from .media import kind_of,probe_video
        if kind_of(path.name)=='video': probe_video(str(path))
        elif kind_of(path.name):
            from PIL import Image
            with Image.open(path) as image: image.verify()
        else: raise ValueError('Unsupported media type')


def plan(project,folder):
    root=Path(folder).expanduser().resolve()
    if not root.is_dir(): raise ValueError('Choose a folder containing your original media')
    by_name={};count=0;limited=False
    for base,dirs,files in os.walk(root,followlinks=False):
        dirs[:]=sorted(d for d in dirs if not d.startswith('.') and not Path(base,d).is_symlink())
        for name in sorted(files):
            count+=1
            if count>10000: limited=True;break
            path=Path(base,name)
            if path.is_symlink() or not path.is_file(): continue
            by_name.setdefault(name.casefold(),[]).append(path)
        if limited: break
    records=[]
    for filename,kind in references(project).items():
        target=Path(filename)
        if target.exists(): continue
        relative=target.relative_to(project.path).as_posix()
        candidates=by_name.get(target.name.casefold(),[])
        def score(path):
            n=0
            for a,b in zip(reversed(target.parts),reversed(path.parts)):
                if a.casefold()!=b.casefold():break
                n+=1
            return n
        best=max((score(p) for p in candidates),default=0)
        candidates=[p for p in candidates if score(p)==best]
        record={'target':relative,'kind':kind,'status':'missing','source':None}
        if len(candidates)>1: record.update(status='ambiguous',message='Several matching files. Use individual relinking or choose a more specific folder.')
        elif candidates:
            source=candidates[0]
            try:
                validate_source(source,kind);stat=source.stat()
                # Nanosecond timestamps exceed JavaScript's exact integer range.
                record.update(status='ready',source=str(source),bytes=stat.st_size,mtime_ns=str(stat.st_mtime_ns))
            except Exception:record.update(status='invalid',message='The matching file could not be read as '+kind+'.')
        records.append(record)
    return {'folder':str(root),'files':records,'limited':limited}


def restore(project,folder,selected):
    if not isinstance(selected,list) or len(selected)>2000: raise ValueError('Choose files from the relink review')
    current=plan(project,folder)
    ready={r['target']:r for r in current['files'] if r['status']=='ready'}
    requested=[]
    for record in selected:
        match=ready.get(record.get('target'))
        if not match or any(match.get(k)!=record.get(k) for k in ('source','bytes','mtime_ns')):
            raise ValueError('Media changed since the review. Scan the folder again before copying.')
        requested.append(match)
    restored=[]
    for record in requested:
        source=Path(record['source']);destination=Path(contained(project.path,record['target']))
        destination.parent.mkdir(parents=True,exist_ok=True)
        fd,temp=tempfile.mkstemp(prefix='.dx-relink-',dir=destination.parent)
        try:
            with os.fdopen(fd,'wb') as out,source.open('rb') as stream:
                shutil.copyfileobj(stream,out);out.flush();os.fsync(out.fileno())
            # Hard-link publication is atomic and fails if the destination exists.
            os.link(temp,destination)
            restored.append(record['target'])
        except FileExistsError: pass
        finally:Path(temp).unlink(missing_ok=True)
    return {'restored':restored,'remaining':plan(project,folder)['files']}
