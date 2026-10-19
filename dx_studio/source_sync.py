"""Detect external source/settings changes without executing or silently adopting them."""
import hashlib
import json
from pathlib import Path
from .paths import contained


def source_files(project,cfg):
    names={'project.json',cfg.get('scene','scene.py'),cfg.get('captions','captions.json')}
    names.update(p.name for p in Path(project.path).glob('*.py'))
    return names


def snapshot(project,values=None):
    cfg=json.loads((Path(project.path)/'project.json').read_text())
    if not isinstance(cfg,dict):raise ValueError('Project configuration must be an object')
    names=source_files(project,cfg)|{'settings.json'}
    result={}
    for name in sorted(names):
        path=Path(contained(project.path,name))
        result[name]={'kind':'source' if name!='settings.json' else 'settings',
                      'stamp':hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None}
    # Watch declared binary assets by metadata, not by hashing large footage on
    # every poll. Pending media imports are excluded until they have been saved.
    settings=Path(project.path)/'settings.json'
    saved=json.loads(settings.read_text()) if settings.is_file() else {}
    if not isinstance(saved,dict):raise ValueError('Saved settings must be an object')
    vals=saved
    refs=[];assets=contained(project.path,cfg.get('assets','assets'))
    refs.extend(contained(assets,it['file']) for it in vals.get('__media',[]) if it.get('file'))
    refs.extend(contained(project.path,it['file']) for it in vals.get('__voice',[]) if it.get('file'))
    refs.extend(contained(project.path,it['file']) for it in cfg.get('voice',[]) if it.get('file'))
    music=cfg.get('music')
    if isinstance(music,dict) and music.get('file'):refs.append(contained(project.path,music['file']))
    brand=vals.get('__brand_assets',{})
    refs.extend(contained(assets,file) for file in brand.get('fonts',{}).values())
    if brand.get('logo'):refs.append(contained(assets,brand['logo']))
    for file in refs:
        path=Path(file);name=path.relative_to(project.path).as_posix()
        stat=path.stat() if path.is_file() else None
        result[name]={'kind':'asset','stamp':[stat.st_mtime_ns,stat.st_size] if stat else None}
    return result


def digest(files):return hashlib.sha256(json.dumps(files,sort_keys=True).encode()).hexdigest()


def status(editor):
    try:
        files=snapshot(editor.pr,editor.saved)
        changed=sorted(name for name in files.keys()|editor.disk_files.keys() if files.get(name)!=editor.disk_files.get(name))
        return {'changed':bool(changed),'files':changed,'revision':digest(files)}
    except (OSError,ValueError,TypeError,KeyError,AttributeError) as error:
        return {'changed':True,'files':[],'revision':None,'error':str(error)}


def acknowledge_save(editor):
    current=snapshot(editor.pr,editor.saved)
    # Only our settings write and newly introduced references are acknowledged.
    # External asset replacements stay visible until a deliberate reload.
    editor.disk_files={name:(record if name=='settings.json' else editor.disk_files.get(name,record))
                       for name,record in current.items()}
