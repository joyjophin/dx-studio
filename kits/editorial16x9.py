"""Editorial layer for 16:9 product explainers (from the "Design a Better Dashboard With AI" episode).

Copy next to scene.py and `from editorial16x9 import *` after `from dx_studio import *`.
The product UI is drawn once, at its native size (e.g. 1440 x 810), by your own component functions that read a
state dict. Everything here sits on top of it, in screen px:

  CAM / cam_at / stage   a camera over the native UI (log-scale zoom, holds still between moves)
  geometry helpers       text_box / union / center: build rects from the SAME constants the UI draws with
  ring_ui                a highlight that hugs a rect (pad and radius in UI units; pad=(px, py) for narrow numerals)
  connector / callout    rounded elbow connectors (one corner, draws on, dot at the target); smart anchoring
  floating_label         branch names, "Preview", the honest "Example first draft" stamp: a card with a coloured dot
  note / veil / banner   readable editorial text on its own card; a soft side veil behind side lists; a question banner
  chapter_moment         dim -> big title + progress meter + underline -> docks top-left as a floating card
  cursor helpers         pointer, eased track, click ripples, drawer open/close progress (240 ms ease-out)
Set STYLE colours to the episode's palette before drawing.
"""
import math
from dx_studio import cairo
from dx_studio import *

W, H, CX, CY = 1920, 1080, 960, 540
STYLE = dict(ink=hexc('#101827'), acc=hexc('#2448B5'), surf=hexc('#FFFFFF'), stage=hexc('#E7EAEF'), muted=hexc('#526174'),
             amber=hexc('#D9860A'), err=hexc('#B42318'), border=hexc('#D9DFE7'))

def _box(c, x, y, w, h, r, col, a=1.0): rrect(c, x, y, w, h, r); fill(c, col, a)
def ED(c, s, x, y, size, w='semi', col=None, a=1.0, align='l'):
    if a > 0 and s: text(c, s, x, y, size, w, col or STYLE['ink'], a, align)

# ---------------------------------------------------------------- camera over the native UI
def CAM(cx, cy, s, sx=CX, sy=CY): return (cx, cy, s, sx, sy)
def scr(cam, x, y):
    cx, cy, s, sx, sy = cam; return sx + (x - cx)*s, sy + (y - cy)*s
def cam_at(keys, t):
    """keys: [(t, CAM(...), move_dur), ...]: each move ends on its key time; the camera holds still in between"""
    cam = keys[0][1]
    for (t0, c0, _d), (t1, c1, d1) in zip(keys, keys[1:]):
        if t >= t1: cam = c1; continue
        st_ = t1 - d1
        if t <= st_: cam = c0; break
        u = eio(clamp((t - st_)/max(d1, 0.01)))
        s = math.exp(lerp(math.log(c0[2]), math.log(c1[2]), u))
        cam = (lerp(c0[0], c1[0], u), lerp(c0[1], c1[1], u), s, lerp(c0[3], c1[3], u), lerp(c0[4], c1[4], u)); break
    return cam
def stage(c, cam, draw_fn, uiw, uih, a=1.0, radius=16):
    """the app window: shadow, rounded clip, your UI drawn in native coordinates"""
    if a <= 0: return
    cx, cy, s, sx, sy = cam
    c.save(); c.translate(sx, sy); c.scale(s, s); c.translate(-cx, -cy)
    shadow(c, 0, 0, uiw, uih, radius, 1.1*a, 1.5)
    c.save(); rrect(c, 0, 0, uiw, uih, radius); c.clip(); draw_fn(c); c.restore()
    c.restore()
    if a < 1:
        x0, y0 = scr(cam, 0, 0); x1, y1 = scr(cam, uiw, uih)
        rrect(c, x0, y0, x1 - x0, y1 - y0, radius*s); fill(c, STYLE['stage'], 1 - a)

# ---------------------------------------------------------------- geometry helpers (UI units)
def text_box(s, x, y, size, w='reg', align='l'):
    """the box of a string drawn at baseline (x, y): use it so rings hug real text"""
    tw_ = tw(s, size, w); x0 = x if align == 'l' else (x - tw_ if align == 'r' else x - tw_/2)
    return (x0, y - size*0.74, tw_, size*0.96)
def union(*rs):
    x0 = min(r[0] for r in rs); y0 = min(r[1] for r in rs); x1 = max(r[0] + r[2] for r in rs); y1 = max(r[1] + r[3] for r in rs)
    return (x0, y0, x1 - x0, y1 - y0)
def center(r): return (r[0] + r[2]/2, r[1] + r[3]/2)

# ---------------------------------------------------------------- highlights and connectors
def ring_ui(c, cam, rect, a, col=None, pad=6, r=8, lw=3.0):
    """a ring that draws itself around a UI rect; pad / r in UI units; pad=(px, py) gives narrow numerals side room"""
    if a <= 0 or rect is None: return
    col = col or STYLE['acc']
    x, y, w, h = rect; s = cam[2]
    px, py = pad if isinstance(pad, tuple) else (pad, pad)
    x0, y0 = scr(cam, x - px, y - py); x1, y1 = scr(cam, x + w + px, y + h + py)
    rr = min((r + min(px, py))*s, (y1 - y0)/2, (x1 - x0)/2)
    u = eo(clamp(a*1.6)); per = 2*((x1 - x0) + (y1 - y0)); al = min(1.0, a*1.4)
    for width, alpha in ((lw*4.2, 0.13), (lw, 1.0)):
        c.save(); c.set_dash([per*u, per]); rrect(c, x0, y0, x1 - x0, y1 - y0, rr)
        c.set_line_width(width); c.set_source_rgba(col[0], col[1], col[2], alpha*al); c.stroke(); c.restore()
def elbow_path(c, x0, y0, x1, y1, r=28, first='h'):
    """horizontal-then-vertical (first='h') or vertical-then-horizontal path with one rounded corner; returns length"""
    dx, dy = x1 - x0, y1 - y0
    if abs(dy) < 3 or abs(dx) < 3:
        c.move_to(x0, y0); c.line_to(x1, y1); return math.hypot(dx, dy)
    sx, sy = (1 if dx > 0 else -1), (1 if dy > 0 else -1)
    rr = min(r, abs(dx)/2, abs(dy)/2)
    c.move_to(x0, y0)
    if first == 'h':
        c.line_to(x1 - sx*rr, y0); c.curve_to(x1 - sx*rr*0.45, y0, x1, y0 + sy*rr*0.45, x1, y0 + sy*rr); c.line_to(x1, y1)
    else:
        c.line_to(x0, y1 - sy*rr); c.curve_to(x0, y1 - sy*rr*0.45, x0 + sx*rr*0.45, y1, x0 + sx*rr, y1); c.line_to(x1, y1)
    return abs(dx) + abs(dy) - (2 - PI/2)*rr
def connector(c, x0, y0, x1, y1, a, col=None, r=30, lw=3.2, first='h', dot=True):
    if a <= 0: return
    col = col or STYLE['acc']; u = eo(clamp(a*1.5)); al = min(1.0, a*1.4)
    c.new_path(); L_ = elbow_path(c, x0, y0, x1, y1, r, first); c.new_path()
    for width, alpha in ((lw*3.6, 0.12), (lw, 1.0)):
        c.save(); elbow_path(c, x0, y0, x1, y1, r, first); c.set_dash([L_*u, L_ + 10])
        c.set_line_cap(cairo.LINE_CAP_ROUND); c.set_line_join(cairo.LINE_JOIN_ROUND)
        c.set_line_width(width); c.set_source_rgba(col[0], col[1], col[2], alpha*al); c.stroke(); c.restore()
    if dot and u > 0.92:
        da = al*P(u, 0.92, 1.0, lin)
        c.arc(x1, y1, 8.5, 0, 2*PI); fill(c, WHITE, da); c.arc(x1, y1, 5.5, 0, 2*PI); fill(c, col, da)
def callout(c, cam, ux, uy, label, a, lx, ly, col=None, size=30, align='l', anchor='side'):
    """a label card at screen (lx, ly) pointing at UI point (ux, uy).
    anchor='side': leave from the edge facing the target; a target under/over the label gets a straight drop instead
    (never route back across the label). anchor='bottom': leave from the bottom, vertical first."""
    if a <= 0: return
    col = col or STYLE['acc']; px, py = scr(cam, ux, uy)
    w = tw(label, size, 'semi') + 40; h = size + 28; bx = lx if align == 'l' else lx - w
    shadow(c, bx, ly, w, h, 14, 0.55*a, 1.0); _box(c, bx, ly, w, h, 14, STYLE['surf'], a)
    c.arc(bx + 20, ly + h/2, 5, 0, 2*PI); fill(c, col, a)
    ED(c, label, bx + 34, ly + h/2 + size*0.36, size, 'semi', STYLE['ink'], a)
    if anchor == 'bottom': connector(c, bx + w*0.5, ly + h, px, py, a, col, first='v')
    elif bx + 24 <= px <= bx + w - 24: connector(c, px, ly + h if py > ly + h else ly, px, py, a, col)
    else: connector(c, bx + w if px > bx + w else bx, ly + h/2, px, py, a, col)
def floating_label(c, s, x, y, a, dot=None, size=22, align='l'):
    if a <= 0 or not s: return
    dot = dot or STYLE['acc']; w = tw(s, size, 'semi') + 58; h = size + 26; x0 = x if align == 'l' else x - w
    shadow(c, x0, y, w, h, 14, 0.5*a, 1.0); _box(c, x0, y, w, h, 14, STYLE['surf'], a)
    c.arc(x0 + 24, y + h/2, 5.5, 0, 2*PI); fill(c, dot, a)
    ED(c, s, x0 + 40, y + h/2 + size*0.36, size, 'semi', STYLE['ink'], a)
def note(c, s, x, y, size, w='semi', col=None, a=1.0, align='l'):
    """editorial text on its own card, so it reads over any UI (never put bare text on a busy zoomed screen)"""
    if a <= 0 or not s: return
    tw_ = tw(s, size, w); px, py = 26, 18
    x0 = x - px if align == 'l' else (x - tw_/2 - px if align == 'c' else x - tw_ - px)
    shadow(c, x0, y - size - py + 6, tw_ + 2*px, size + 2*py, 14, 0.5*a, 1.0); _box(c, x0, y - size - py + 6, tw_ + 2*px, size + 2*py, 14, STYLE['surf'], a)
    ED(c, s, x, y, size, w, col, a, align)
def veil(c, a, w=700):
    """a soft stage-coloured veil on the left, so side cards separate from a zoomed UI"""
    if a <= 0: return
    st = STYLE['stage']; g = cairo.LinearGradient(0, 0, w, 0)
    g.add_color_stop_rgba(0, st[0], st[1], st[2], 0.92*a); g.add_color_stop_rgba(0.75, st[0], st[1], st[2], 0.75*a); g.add_color_stop_rgba(1, st[0], st[1], st[2], 0)
    c.rectangle(0, 0, w, H); c.set_source(g); c.fill()
def banner(c, s, a, y=70, size=40):
    if a <= 0: return
    w = tw(s, size, 'semi') + 64; x = CX - w/2
    shadow(c, x, y - size - 10, w, size + 40, 18, 0.6*a, 1.1); _box(c, x, y - size - 10, w, size + 40, 18, STYLE['surf'], a)
    ED(c, s, CX, y + 10, size, 'semi', STYLE['ink'], a, align='c')

# ---------------------------------------------------------------- chapter moment (replaces "pipe + text" titles)
def chapter_moment(c, t, t_voice, title, index, total, dock_after=1.15, hold=4.4, x=160, y=560):
    """t_voice: when the chapter's narration starts. Starts 0.55 s before it in the gap, docks after `dock_after` s."""
    t0 = t_voice - 0.55; t_dock = t_voice + dock_after; t_out = t_voice + hold
    if not (t0 <= t <= t_out + 0.4): return
    dim = P(t, t0, t0 + 0.35, eio)*(1 - P(t, t_dock, t_dock + 0.45, eio))
    if dim > 0: c.rectangle(0, 0, W, H); fill(c, STYLE['stage'], 0.86*dim)
    u = eio(P(t, t_dock, t_dock + 0.45, lin)); a = 1 - P(t, t_out, t_out + 0.4, lin)
    big, small = 76, 28; k = lerp(1.0, small/big, u); bx, by = lerp(x, 136, u), lerp(y, 66, u)
    if u > 0:
        cw = tw(title, small, 'semi') + 70; ca = a*P(u, 0.35, 1.0, lin)
        shadow(c, 96, 28, cw, 56, 16, 0.55*ca, 1.0); _box(c, 96, 28, cw, 56, 16, STYLE['surf'], ca)
        c.arc(118, 56, 5.5, 0, 2*PI); fill(c, STYLE['acc'], ca)
    ma = a*(1 - P(u, 0.0, 0.5, lin))
    if ma > 0:                       # progress meter: segments, no numbers
        for j in range(total):
            seg = 1.0 if j < index - 1 else (P(t, t0 + 0.15, t0 + 0.55, eo) if j == index - 1 else 0.0)
            _box(c, x + j*44, y - 122, 36, 6, 3, STYLE['border'], ma)
            if seg > 0: _box(c, x + j*44, y - 122, 36*seg, 6, 3, STYLE['acc'], ma)
    c.save(); c.translate(bx, by); c.scale(k, k)
    ktext(c, title, 0, 0, big, 'semi', STYLE['ink'], t, t0 + 0.1, a, align='l', track=-0.02)
    c.restore()
    la = a*(1 - P(u, 0.0, 0.4, lin))*P(t, t0 + 0.35, t0 + 0.75, eo)
    if la > 0: _box(c, x, y + 40, 140*la, 6, 3, STYLE['acc'], min(1, la*1.2))

# ---------------------------------------------------------------- cursor, windows, drawers
def pointer(c, x, y, a=1.0, down=False, s=1.5):
    if a <= 0: return
    s = s*(0.92 if down else 1.0)
    c.save(); c.translate(x, y); c.scale(s, s)
    c.move_to(0, 0); c.line_to(0, 17); c.line_to(4.2, 13.2); c.line_to(7, 19.6); c.line_to(9.6, 18.4); c.line_to(6.9, 12.2); c.line_to(12.3, 12.2); c.close_path()
    c.set_line_join(cairo.LINE_JOIN_ROUND); fillp(c, (0.06, 0.06, 0.07, 1), a); stroke(c, WHITE, 1.4, a); c.restore()
def cursor_track(keys, t, move=0.45):
    """keys: [(t, ux, uy), ...]: each move takes `move` s and ends on its key; the cursor only moves to interact"""
    x, y = keys[0][1], keys[0][2]
    for (t0, x0, y0), (t1, x1, y1) in zip(keys, keys[1:]):
        if t >= t1: x, y = x1, y1; continue
        u = eio(clamp((t - (t1 - move))/move)); x, y = lerp(x0, x1, u), lerp(y0, y1, u); break
    return x, y
def draw_cursor(c, cam, keys, clicks, t, a):
    if a <= 0: return
    ux, uy = cursor_track(keys, t); px, py = scr(cam, ux, uy)
    down = any(0 <= t - tc < 0.12 for tc in clicks)
    for tc in clicks:
        u = (t - tc)/0.45
        if 0 <= u <= 1: c.arc(px, py, 10 + 34*eo(u), 0, 2*PI); stroke(c, STYLE['acc'], 3*(1 - u) + 0.5, 0.8*(1 - u))
    pointer(c, px, py, a, down, 1.25 + 0.25*min(1.5, cam[2]))
def opening(t, t_open, t_close=None, d=0.24):
    """drawer open progress: 240 ms ease-out (apply eo() when drawing), 200 ms close"""
    u = clamp((t - t_open)/d) if t >= t_open else 0.0
    if t_close is not None and t >= t_close: u = 1 - clamp((t - t_close)/0.2)
    return u
def win(t, t0, t1, fi=0.2, fo=0.2): return P(t, t0, t0 + fi, lin)*(1 - P(t, t1 - fo, t1, lin)) if t1 > t0 else 0.0
