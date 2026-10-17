"""dx_studio.layers: scenes built from named layers the editor can select, move, scale, rotate, fade,
retime, hide and keyframe.

    LAYERS = [
        Layer('title', 'Title', draw=draw_title, box=(140, 430, 800, 120), start=0.4, end=5.0, group='Opening', params=['title']),
        Layer('card', 'Card', draw=draw_card, box=(160, 700, 760, 420), start=1.2, group='Opening',
              children=[Layer('check', 'Checkmark', draw=draw_check, box=(450, 820, 180, 180), start=1.6)]),
    ]
    def draw(c, t, p):
        ...background...
        render_layers(c, t, p, LAYERS)

A layer's draw(c, t, p) receives the timeline time *shifted by however far the user moved the layer*,
so a scene can keep using absolute times and still have its whole animation follow the layer bar.
Coordinates are the frame's (or the parent's space for children). `box` is (x, y, w, h), or a function
of t returning one, and defines both the selection outline and the pivot for scale/rotation.
Optional: motion(c, t) = the layer's built-in movement (applied before the user's transform, inherited
by children); child_ctx(c, t) = clip/translate applied before drawing children; alive(t) = whether the
element is actually visible at t (used for click-selection; defaults to the layer's time window).
"""
import math, copy
from ._cairo import cairo
from .core import clamp, lerp, eo, eio, ei, back_ease

TRANSFORM_KEYS = ('x', 'y', 'scale', 'rotation', 'opacity')
PRESETS = ['none', 'fade', 'pop', 'zoom', 'slide-up', 'slide-down', 'slide-left', 'slide-right']
EASES = {'ease': eio, 'ease-out': eo, 'ease-in': ei, 'linear': lambda u: clamp(u), 'back': lambda u: back_ease(u, 1.6), 'hold': lambda u: 0.0 if u < 1 else 1.0}

class Layer:
    def __init__(self, id, label=None, draw=None, box=None, start=0.0, end=None, group='Layers', params=(), motion=None,
                 children=(), child_ctx=None, alive=None, locked=False, help=None):
        self.id, self.label, self.draw, self.box = id, label or id, draw, box
        self.start, self.end, self.group, self.params = float(start), end, group, list(params)
        self.motion, self.children, self.child_ctx, self.alive = motion, list(children), child_ctx, alive
        self.locked, self.help = locked, help

def walk(layers, parent=None, depth=0):
    for L in layers:
        yield L, parent, depth
        yield from walk(L.children, L, depth+1)

def default_state(L, duration):
    return {'start': L.start, 'end': float(L.end if L.end is not None else duration), 'visible': True,
            'x': 0.0, 'y': 0.0, 'scale': 1.0, 'rotation': 0.0, 'opacity': 1.0,
            'enter': 'none', 'enter_dur': 0.4, 'exit': 'none', 'exit_dur': 0.3, 'keys': []}

def defaults_for(layers, duration):
    return {L.id: default_state(L, duration) for L, _, _ in walk(layers)}

def meta_for(layers, duration):
    return [{'id': L.id, 'label': L.label, 'group': L.group, 'parent': P.id if P else None, 'depth': d,
             'params': L.params, 'locked': L.locked, 'help': L.help,
             'default_start': L.start, 'default_end': float(L.end if L.end is not None else duration)} for L, P, d in walk(layers)]

# ------------------------------------------------------------------ transform evaluation
def transform_at(st, rt):
    """user transform at layer-relative time rt: keyframes if any, else the static values"""
    keys = st.get('keys') or []
    if not keys: return {k: float(st.get(k, 1.0 if k in ('scale', 'opacity') else 0.0)) for k in TRANSFORM_KEYS}
    keys = sorted(keys, key=lambda k: k['t'])
    if rt <= keys[0]['t']: return {k: float(keys[0][k]) for k in TRANSFORM_KEYS}
    if rt >= keys[-1]['t']: return {k: float(keys[-1][k]) for k in TRANSFORM_KEYS}
    for a, b in zip(keys, keys[1:]):
        if a['t'] <= rt <= b['t']:
            u = (rt-a['t'])/max(1e-6, b['t']-a['t']); e = EASES.get(b.get('ease', 'ease'), eio)(u)
            return {k: lerp(float(a[k]), float(b[k]), e) for k in TRANSFORM_KEYS}

def preset_factor(kind, u):
    """u: 0 = fully out, 1 = fully in. returns (dx, dy, scale, alpha)"""
    if kind == 'none' or u >= 1: return 0.0, 0.0, 1.0, 1.0
    e = eo(u)
    if kind == 'fade': return 0.0, 0.0, 1.0, e
    if kind == 'pop': return 0.0, 0.0, lerp(0.6, 1.0, back_ease(u, 1.8)), clamp(u*2.5)
    if kind == 'zoom': return 0.0, 0.0, lerp(0.85, 1.0, e), e
    d = 140*(1-e)
    return {'slide-up': (0, d), 'slide-down': (0, -d), 'slide-left': (d, 0), 'slide-right': (-d, 0)}[kind] + (1.0, e)

def _box(L, lt):
    b = L.box(lt) if callable(L.box) else L.box
    return b

def _window(st, t):
    ex = st.get('exit', 'none') != 'none'
    return st['start'] <= t <= st['end'] + (0 if not ex else 0)

def _apply(c, L, st, t, measure=False):
    """apply motion + user transform + presets; returns (alpha, layer time)"""
    shift = st['start'] - L.start; lt = t - shift
    if L.motion: L.motion(c, lt)
    tr = transform_at(st, t - st['start'])
    en_u = (t-st['start'])/max(1e-6, st.get('enter_dur', 0.4)) if st.get('enter', 'none') != 'none' else 1.0
    ex_u = (st['end']-t)/max(1e-6, st.get('exit_dur', 0.3)) if st.get('exit', 'none') != 'none' else 1.0
    edx, edy, es, ea = preset_factor(st.get('enter', 'none'), clamp(en_u))
    xdx, xdy, xs, xa = preset_factor(st.get('exit', 'none'), clamp(ex_u))
    b = _box(L, lt)
    ax, ay = (b[0]+b[2]/2, b[1]+b[3]/2) if b else (0.0, 0.0)
    dx, dy = tr['x']+edx-xdx, tr['y']+edy-xdy
    s = tr['scale']*es*xs; rot = tr['rotation']
    if dx or dy or s != 1 or rot:
        c.translate(ax+dx, ay+dy)
        if rot: c.rotate(math.radians(rot))
        if s != 1: c.scale(s, s)
        c.translate(-ax, -ay)
    return tr['opacity']*ea*xa, lt

def ordered(layers, state):
    """siblings sorted by their editable 'order' (bring forward / send backward), then declaration order"""
    return [L for _, L in sorted(enumerate(layers), key=lambda iL: (state.get(iL[1].id, {}).get('order', iL[0]), iL[0]))]

def render_layers(c, t, p, layers, _state=None):
    state = _state if _state is not None else p.raw('__layers')
    for L in ordered(layers, state):
        st = state.get(L.id)
        if st is None or not st.get('visible', True) or not _window(st, t): continue
        c.save()
        alpha, lt = _apply(c, L, st, t)
        if alpha <= 0.002: c.restore(); continue
        grouped = alpha < 0.999
        if grouped: c.push_group()
        if L.draw: L.draw(c, lt, p)
        if L.children:
            c.save()
            if L.child_ctx: L.child_ctx(c, lt)
            render_layers(c, lt, p, L.children, state)
            c.restore()
        if grouped: c.pop_group_to_source(); c.paint_with_alpha(alpha)
        c.restore()

def measure_layers(t, p, layers, width, height, _state=None, _c=None, out=None):
    """device-space outlines of the layers present at t (top-most last), for click-selection and handles"""
    if _c is None:
        _c = cairo.Context(cairo.ImageSurface(cairo.FORMAT_A8, 1, 1)); out = []
    state = _state if _state is not None else p.raw('__layers')
    for L in ordered(layers, state):
        st = state.get(L.id)
        if st is None or not st.get('visible', True) or not _window(st, t): continue
        _c.save()
        shift = st['start'] - L.start; lt = t - shift
        base = _c.get_matrix()
        alpha, lt = _apply(_c, L, st, t)
        if alpha <= 0.002:
            _c.restore(); continue
        b = _box(L, lt)
        present = st.get('visible', True) and (L.alive(lt) if L.alive else True)
        if b and present and not L.locked:
            pts = [_c.user_to_device(x, y) for x, y in ((b[0], b[1]), (b[0]+b[2], b[1]), (b[0]+b[2], b[1]+b[3]), (b[0], b[1]+b[3]))]
            ctr = _c.user_to_device(b[0]+b[2]/2, b[1]+b[3]/2)
            out.append({'id': L.id, 'corners': [list(q) for q in pts], 'center': list(ctr),
                        'base': [base.xx, base.yx, base.xy, base.yy]})
        if L.children and st.get('visible', True):
            _c.save()
            if L.child_ctx: L.child_ctx(_c, lt)
            measure_layers(lt, p, L.children, width, height, state, _c, out)
            _c.restore()
        _c.restore()
    return out

def _apply_user_only(c, L, st, t, lt):
    tr = transform_at(st, t - st['start'])
    b = _box(L, lt)
    ax, ay = (b[0]+b[2]/2, b[1]+b[3]/2) if b else (0.0, 0.0)
    c.translate(ax+tr['x'], ay+tr['y'])
    if tr['rotation']: c.rotate(math.radians(tr['rotation']))
    if tr['scale'] != 1: c.scale(tr['scale'], tr['scale'])
    c.translate(-ax, -ay)
    return tr['opacity'], lt
