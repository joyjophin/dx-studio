"""dx_studio.project: load a project folder (project.json + scene.py), its editable parameters and its render."""
import copy, importlib.util, json, os, sys, math
from .paths import contained
from .composition import layout_for, PRESENTER_PRESETS
from ._cairo import cairo
from .core import hexc
from . import stickers, captions as _captions
from .schema import normalize, Params, migrate_settings

class Project:
    def __init__(self, path):
        self.path = os.path.abspath(path)
        self.cfg = json.load(open(os.path.join(self.path, 'project.json')))
        if self.cfg.get('format_version', 1) != 1:
            raise ValueError('Unsupported format_version; this release supports version 1')
        for key, default in [('width',1080), ('height',1920), ('fps',30)]:
            v = self.cfg.get(key, default)
            if isinstance(v, bool) or not isinstance(v, int) or v <= 0 or v > (120 if key == 'fps' else 8192):
                raise ValueError(f'{key} must be a positive integer within the supported range')
            if key != 'fps' and v % 2: raise ValueError(f'{key} must be even for H.264 export')
        duration = self.cfg.get('duration', 10)
        if isinstance(duration, bool) or not isinstance(duration, (int,float)) or not math.isfinite(duration) or duration < 1/self.cfg.get('fps',30):
            raise ValueError('duration must be finite and at least one frame')
        for key, default in [('scene','scene.py'), ('assets','assets'), ('captions','captions.json'), ('output','output.mp4')]:
            contained(self.path, self.cfg.get(key, default))
        for line in self.cfg.get('voice', []):
            if line.get('file'): contained(self.path, line['file'])
        if isinstance(self.cfg.get('music'), dict) and self.cfg['music'].get('file'):
            contained(self.path, self.cfg['music']['file'])
        self.name = self.cfg.get('name', os.path.basename(self.path))
        self.width, self.height = self.cfg.get('width', 1080), self.cfg.get('height', 1920)
        self.fps, self.duration = self.cfg.get('fps', 30), float(self.cfg.get('duration', 10))
        composition = self.cfg.get('composition', {})
        if not isinstance(composition, dict): raise ValueError('composition must be an object')
        preset = composition.get('presenter', 'none')
        layout_for(self.width,self.height,preset,self.cfg.get('safe_area'))
        self.base_duration = self.duration          # scene time; self.duration becomes the output length after ripple edits
        self.edits = []
        self.output = os.path.join(self.path, self.cfg.get('output', 'output.mp4'))
        stickers.set_asset_dir(os.path.join(self.path, self.cfg.get('assets', 'assets')))
        stickers.FREEZE_AFTER = self.duration - self.cfg.get('final_hold', 0.8)
        cap_file = os.path.join(self.path, self.cfg.get('captions', 'captions.json'))
        self.has_captions = os.path.exists(cap_file) or 'captions' in self.cfg
        base_caps = json.load(open(cap_file)) if os.path.exists(cap_file) else []
        self.captions = _captions.prepare(copy.deepcopy(base_caps))
        from .media import MediaLibrary
        self.media = MediaLibrary(self); self.media_layers = []
        spec = importlib.util.spec_from_file_location(f'mkscene_{abs(hash(self.path))}', os.path.join(self.path, self.cfg.get('scene', 'scene.py')))
        self.scene = importlib.util.module_from_spec(spec); sys.modules[spec.name] = self.scene
        sys.path.insert(0, self.path)
        try: spec.loader.exec_module(self.scene)
        finally: sys.path.remove(self.path)
        schema = copy.deepcopy(getattr(self.scene, 'SCHEMA', []))
        brand = self.cfg.get('brand', {})
        for entry in schema:
            if entry['key'] in brand: entry['default'] = brand[entry['key']]

        self.composition_supported = bool(getattr(self.scene, 'RESPONSIVE_COMPOSITION', False))
        schema.append({'key':'__composition', 'type':'choice', 'label':'Presenter space',
                       'panel':'Composition', 'group':'Layout', 'default':preset,
                       'options':list(PRESENTER_PRESETS), 'option_labels':PRESENTER_PRESETS,
                       'help':'Reserve this area for your talking head. Graphics and captions use the remaining space in responsive scenes.'})
        self.layers = list(getattr(self.scene, 'LAYERS', []))
        if self.layers:
            from . import layers as _L
            self.layer_meta = _L.meta_for(self.layers, self.duration)
            schema.insert(0, {'key': '__layers', 'type': 'layers', 'label': 'Layers', 'panel': 'Layers',
                              'default': _L.defaults_for(self.layers, self.duration)})
        else: self.layer_meta = []
        self.scene_layer_meta = list(self.layer_meta)
        if self.has_captions:
            schema.append({'key': '__captions', 'type': 'captions', 'label': 'Captions', 'panel': 'Captions',
                           'default': [{'start': c['start'], 'end': c['show_end'], 'text': c['text'], 'hl': c.get('hl')} for c in base_caps]})
        schema.append({'key': '__media', 'type': 'media', 'label': 'Media', 'panel': 'Layers', 'default': []})
        schema.append({'key': '__timeline', 'type': 'timeline', 'label': 'Ripple edits', 'panel': 'Layers', 'default': []})
        if not self.layers:
            schema.insert(0, {'key': '__layers', 'type': 'layers', 'label': 'Layers', 'panel': 'Layers', 'default': {}})
        from .narration import defaults as voice_defaults
        schema.append({'key':'__voice','type':'narration','label':'Narration','panel':'Narration','default':voice_defaults(self)})
        self.schema = normalize(schema)
        self.defaults = {e['key']: copy.deepcopy(e['default']) for e in self.schema}
        self.values = self.load_settings()
        self.apply(self.values)

    # ---- settings
    @property
    def settings_path(self): return os.path.join(self.path, 'settings.json')
    def load_settings(self):
        user = json.load(open(self.settings_path)) if os.path.exists(self.settings_path) else {}
        return self.values_from_settings(user)
    def values_from_settings(self, user):
        vals = copy.deepcopy(self.defaults)
        user = migrate_settings(copy.deepcopy(user), self.schema)
        for k, v in user.items():
            if k not in vals: continue
            if k == '__layers':                       # merge per layer so new layers keep their defaults
                for lid, st in v.items():
                    if lid in vals[k]: vals[k][lid].update(st)
                    else: vals[k][lid] = dict(st)           # media layers: completed in apply()
            else: vals[k] = v
        return vals
    def settings_diff(self, values=None):
        values = self.values if values is None else values
        changed = {k: v for k, v in values.items() if v != self.defaults.get(k) and k != '__layers'}
        if '__layers' in values:
            lc = {lid: {f: x for f, x in st.items() if x != self.defaults['__layers'].get(lid, {}).get(f)}
                  for lid, st in values['__layers'].items()}
            lc = {lid: st for lid, st in lc.items() if st}
            if lc: changed['__layers'] = lc
        return changed
    def save_settings(self, values=None):
        from .history import atomic_json
        atomic_json(self.settings_path, self.settings_diff(values))
    def apply(self, values):
        from . import layers as _L
        from .narration import validate as validate_voice
        validate_voice(self, values.get('__voice', []))
        layout = layout_for(self.width,self.height,values.get('__composition','none'),self.cfg.get('safe_area'))
        self.layout = layout
        self.values = values
        items = values.get('__media', [])
        self.media_layers = self.media.layers_for(items)
        ids = {it['id'] for it in items}
        from .timemap import out_duration
        self.edits = list(values.get('__timeline', []))
        self.duration = out_duration(self.base_duration, self.edits)
        for L in self.media_layers:                      # every media layer has a default state and a full state
            d = _L.default_state(L, self.base_duration)
            self.defaults['__layers'][L.id] = d
            cur = values['__layers'].get(L.id, {})
            values['__layers'][L.id] = {**d, **cur}
        for lid in [k for k in values['__layers'] if k.startswith('media_') and k not in ids]: values['__layers'].pop(lid)
        for lid in [k for k in self.defaults['__layers'] if k.startswith('media_') and k not in ids]: self.defaults['__layers'].pop(lid)
        self.layer_meta = self.scene_layer_meta + _L.meta_for(self.media_layers, self.base_duration)
        self.layer_meta = [dict(m, label=str(values['__layers'].get(m['id'], {}).get('label') or m['label'])[:120]) for m in self.layer_meta]
        if self.has_captions:
            self.captions = _captions.prepare([{'start': c['start'], 'show_end': c['end'], 'end': c['end'], 'text': c['text'], 'hl': c.get('hl') or None}
                                                for c in sorted(values.get('__captions', []), key=lambda c: c['start']) if c.get('text', '').strip()])
        self.params = Params(self.schema, values)
        if hasattr(self.scene, 'setup'): self.scene.setup(self.params, self)

    def voices(self):
        return self.values.get('__voice', [])

    # ---- output
    def hits(self, t):
        from .layers import measure_layers
        return measure_layers(self.scene_t(t), self.params, self.layers + self.media_layers, self.width, self.height)
    def scene_t(self, t):
        """output time -> scene time (identity unless ripple edits exist)"""
        from .timemap import scene_time
        s = scene_time(t, self.edits) if self.edits else t
        return max(0.0, min(self.base_duration-1e-3, s))
    def cues(self):
        """sound cues; a cue with "layer": id follows that layer when it is moved, and goes silent when it is hidden"""
        if not hasattr(self.scene, 'cues'): return []
        out = []
        st = self.values.get('__layers', {}); dflt = self.defaults.get('__layers', {})
        for cue in self.scene.cues(self.params):
            cue = dict(cue); lid = cue.pop('layer', None)
            if lid and lid in st:
                chain = [lid] + self._ancestors(lid)
                if not all(st[x].get('visible', True) for x in chain): continue
                cue['at'] += sum(st[x]['start'] - dflt[x]['start'] for x in chain)
            out.append(cue)
        return out
    def _ancestors(self, lid):
        parent = {m['id']: m['parent'] for m in self.layer_meta}; out = []
        while parent.get(lid): lid = parent[lid]; out.append(lid)
        return out
    def render(self, t, scale=1.0):
        if not math.isfinite(t) or not math.isfinite(scale) or not 0.02 <= scale <= 2:
            raise ValueError('Time must be finite and render scale must be between 0.02 and 2')
        stickers.set_asset_dir(os.path.join(self.path, self.cfg.get('assets', 'assets')))
        stickers.FREEZE_AFTER = self.base_duration - self.cfg.get('final_hold', 0.8)
        w, h = int(round(self.width*scale)), int(round(self.height*scale))
        surf = cairo.ImageSurface(cairo.FORMAT_RGB24, w, h); c = cairo.Context(surf)
        c.set_antialias(cairo.ANTIALIAS_BEST)
        fo = cairo.FontOptions(); fo.set_antialias(cairo.ANTIALIAS_GRAY); fo.set_hint_style(cairo.HINT_STYLE_NONE); fo.set_hint_metrics(cairo.HINT_METRICS_OFF)
        c.set_font_options(fo)
        if scale != 1.0: c.scale(scale, scale)
        tt = self.scene_t(t)
        self.scene.draw(c, tt, self.params)
        if self.media_layers:
            from .layers import render_layers
            render_layers(c, tt, self.params, self.media_layers)       # user media sits on top of the scene
        surf.flush(); return surf
