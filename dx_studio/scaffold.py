"""Project scaffolding with explicit layouts for portrait and landscape."""
import json
import shutil
from pathlib import Path
from .composition import PRESENTER_PRESETS

FORMATS = {"9:16": (1080,1920), "16:9": (1920,1080)}

def create(dest, template="explainer", format="9:16", name=None, brand=None, presenter="none"):
    dest = Path(dest).resolve()
    if dest.exists(): raise ValueError(f"Destination already exists: {dest}")
    source = Path(__file__).parent / "templates" / template
    if template not in {"explainer", "starter"}: raise ValueError("Unknown template")
    if format not in FORMATS: raise ValueError("Choose 9:16 or 16:9")
    if presenter not in PRESENTER_PRESETS: raise ValueError('Unknown presenter layout')
    palette = json.loads(Path(brand).read_text()) if brand else {}
    if not isinstance(palette, dict): raise ValueError("Brand file must be a JSON object")
    shutil.copytree(source, dest, ignore=shutil.ignore_patterns('__pycache__'))
    cfg = json.loads((dest/'project.json').read_text())
    cfg.update(width=FORMATS[format][0], height=FORMATS[format][1], name=name or dest.name)
    cfg['brand'] = palette
    cfg['composition'] = {'presenter': presenter}
    cfg['safe_area'] = ({'content':[130,170,950,1560], 'captions':[130,1370,950,1550]} if format == '9:16'
                        else {'content':[96,64,1824,1016], 'captions':[200,900,1720,1016]})
    (dest/'project.json').write_text(json.dumps(cfg, indent=2)+'\n')
    (dest/'assets'/'Avatars').mkdir(parents=True)
    (dest/'assets'/'README.md').write_text('Add your own licensed images, footage and stickers here. See the repository docs/ASSETS.md.\n')
    return dest
