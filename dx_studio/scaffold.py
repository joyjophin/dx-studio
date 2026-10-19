"""Project scaffolding: real templates, a blank canvas and explicit constraints."""
import json
import math
import shutil
from pathlib import Path
from .composition import PRESENTER_PRESETS

FORMATS = {'9:16': (1080,1920), '16:9': (1920,1080)}
TEMPLATES = ('explainer', 'starter', 'showcase', 'comparison', 'blank')
CATALOG = [
    {'id':'showcase','name':'Make it click','description':'Sculptural motion, bold type and layered posters. Original music included.','duration':10,'thumbnail':'showcase.jpg'},
    {'id':'comparison','name':'Proof point','description':'A clean visual comparison. Replace the illustrative numbers and tell your story.','duration':12,'thumbnail':'comparison.jpg'},
]

def create(dest, template='explainer', format='9:16', name=None, brand=None, presenter='none', duration=None, width=None, height=None):
    dest=Path(dest).resolve()
    if dest.exists():raise ValueError(f'Destination already exists: {dest}')
    if template not in TEMPLATES:raise ValueError('Unknown template')
    if format not in FORMATS:raise ValueError('Choose 9:16 or 16:9')
    if presenter not in PRESENTER_PRESETS:raise ValueError('Unknown presenter layout')
    if (width is None)!=(height is None):raise ValueError('Set both width and height')
    w,h=FORMATS[format] if width is None else (width,height)
    if any(isinstance(n,bool) or not isinstance(n,int) or not 64<=n<=8192 or n%2 for n in (w,h)):
        raise ValueError('Canvas dimensions must be even whole numbers between 64 and 8192')
    if duration is not None and (isinstance(duration,bool) or not isinstance(duration,(float,int)) or not math.isfinite(duration) or not 1<=duration<=3600):
        raise ValueError('Choose a duration between 1 and 3600 seconds')
    palette=json.loads(Path(brand).read_text()) if brand else {}
    if not isinstance(palette,dict):raise ValueError('Brand file must be a JSON object')
    source=Path(__file__).parent/'templates'/template
    cfg=json.loads((source/'project.json').read_text())
    cfg.update(width=w,height=h,name=name or dest.name,brand=palette,composition={'presenter':presenter})
    if duration is not None:
        cfg['duration']=duration
        # A blank scene has one user-defined time range. Authored templates keep
        # their choreography; the UI does not offer arbitrary template duration.
        if template in ('blank','starter'):cfg['chapters']=[[0,duration,'Scene 1']]
    cfg['safe_area']=({'content':[w*130/1080,h*170/1920,w*950/1080,h*1560/1920],
                       'captions':[w*130/1080,h*1370/1920,w*950/1080,h*1550/1920]} if h>w else
                      {'content':[w*.05,h*64/1080,w*.95,h*1016/1080],
                       'captions':[w*200/1920,h*900/1080,w*1720/1920,h*1016/1080]})
    shutil.copytree(source,dest,ignore=shutil.ignore_patterns('__pycache__'))
    (dest/'project.json').write_text(json.dumps(cfg,indent=2)+'\n')
    (dest/'assets'/'Avatars').mkdir(parents=True,exist_ok=True)
    (dest/'assets'/'README.md').write_text('Add your own licensed images, footage and stickers here. See the repository docs/ASSETS.md.\n')
    return dest
