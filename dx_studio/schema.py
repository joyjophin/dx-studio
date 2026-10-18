"""dx_studio.schema: the editable-parameter contract between a scene and the editor.

A scene declares SCHEMA = [ {param}, ... ].  Every param has:
    key      unique name (used in settings.json and in the scene as p.key / p['key'])
    type     time | number | color | text | bool | choice | point | sticker | clips
    label    human label shown in the editor
    default  value used when the user hasn't changed it
optional:
    group    sub-heading inside a panel                       (default "General")
    panel    which editor tab                                  (default chosen by type)
    at       seconds: where to jump when the field is focused  (text / color / number / point)
    help     one-line hint shown under the field
    number:  min, max, step, unit          choice: options [..]
    point:   auto_label (text shown when the value is null = "let the scene decide")
    clips:   fields [ {key, type, label, ...} ]   every clip also has start / end (seconds)
             label_field (field whose value names the block on the timeline, e.g. "pose")
             lane_label (timeline lane name)
Values in settings.json are plain JSON: time/number -> float, color -> "#RRGGBB", point -> [x, y] or null.
"""
import copy
from .core import hexc

TYPES = {'time', 'number', 'color', 'text', 'bool', 'choice', 'point', 'sticker', 'clips', 'layers', 'captions', 'media', 'timeline', 'narration', 'audio_mix'}
DEFAULT_PANEL = {'time': 'Timing', 'color': 'Colours', 'text': 'Text', 'clips': None,
                 'number': 'Settings', 'bool': 'Settings', 'choice': 'Settings', 'point': 'Settings', 'sticker': 'Settings', 'layers': 'Layers', 'captions': 'Captions', 'media': 'Layers', 'timeline': 'Layers', 'narration': 'Narration', 'audio_mix': 'Audio'}

def normalize(schema):
    out, seen = [], set()
    for e in schema:
        e = dict(e)
        if e.get('type') not in TYPES: raise ValueError(f"param {e.get('key')}: unknown type {e.get('type')!r}")
        if 'key' not in e or 'default' not in e: raise ValueError(f"param needs key and default: {e}")
        if e['key'] in seen: raise ValueError(f"duplicate param key {e['key']}")
        seen.add(e['key'])
        e.setdefault('label', e['key']); e.setdefault('group', 'General')
        e.setdefault('panel', DEFAULT_PANEL[e['type']] or e['label'])
        if e['type'] == 'clips':
            e.setdefault('fields', []); e.setdefault('label_field', None); e.setdefault('lane_label', e['label'])
        out.append(e)
    return out

class Clip(dict):
    """one timeline clip: attribute access (clip.start, clip.pose, clip.pos)"""
    def __getattr__(self, k):
        try: return self[k]
        except KeyError: raise AttributeError(k)

def _conv(ptype, v, fields=None):
    if v is None: return None
    if ptype == 'color': return hexc(v)
    if ptype in ('time', 'number'): return float(v)
    if ptype == 'bool': return bool(v)
    if ptype == 'point': return (float(v[0]), float(v[1]))
    if ptype == 'clips':
        fmap = {f['key']: f['type'] for f in (fields or [])}
        return [Clip({k: _conv(fmap.get(k, 'time' if k in ('start', 'end') else None), x) for k, x in item.items()}) for item in v]
    return v

class Params:
    """typed, read-only view of the current values for a scene: p.accent -> (r,g,b,a), p.t_stamp -> 16.46"""
    def __init__(self, schema, values):
        object.__setattr__(self, '_s', {e['key']: e for e in schema})
        object.__setattr__(self, '_v', values)
        object.__setattr__(self, '_c', {})
    def __getitem__(self, k):
        c = self._c
        if k not in c:
            e = self._s[k]; c[k] = _conv(e['type'], self._v[k], e.get('fields'))
        return c[k]
    def __getattr__(self, k):
        if k.startswith('_'): raise AttributeError(k)
        try: return self[k]
        except KeyError: raise AttributeError(f"no parameter named {k!r}")
    def raw(self, k): return self._v[k]
    def keys(self): return self._s.keys()

def migrate_settings(user, schema):
    """accepts the flat format, and the older nested one ({colors, text, timing, characters})"""
    if not any(k in user for k in ('colors', 'text', 'timing')): return user
    flat = {}
    for sect in ('colors', 'text', 'timing'): flat.update(user.get(sect, {}))
    if 'characters' in user:
        chars = []
        for b in user['characters']:
            b = copy.deepcopy(b); x, y = b.pop('x', None), b.pop('y', None)
            b['pos'] = [x, y] if x is not None and y is not None else None
            b.setdefault('mirror', False); chars.append(b)
        flat['characters'] = chars
    return flat
