"""dx_studio.draw: shapes, soft shadows, cards, checkmarks, glows, arrows, backgrounds, sparks."""
import math
from ._cairo import cairo
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from functools import lru_cache
from .core import *

KEEP = []          # keeps numpy buffers alive while cairo surfaces reference them
SHADOW_INK = (0x21, 0x16, 0x38)

def rrect(c, x, y, w, h, r):
    r = max(0, min(r, w/2, h/2)); c.new_sub_path()
    c.arc(x+w-r, y+r, r, -PI/2, 0); c.arc(x+w-r, y+h-r, r, 0, PI/2)
    c.arc(x+r, y+h-r, r, PI/2, PI); c.arc(x+r, y+r, r, PI, 1.5*PI); c.close_path()

def fill(c, col, a=1.0): c.set_source_rgba(col[0], col[1], col[2], col[3]*a); c.fill()

def fillp(c, col, a=1.0): c.set_source_rgba(col[0], col[1], col[2], col[3]*a); c.fill_preserve()

def stroke(c, col, wdt, a=1.0):
    c.set_source_rgba(col[0], col[1], col[2], col[3]*a); c.set_line_width(wdt); c.stroke()

@lru_cache(200)
def shadow_surf(w, h, r, blur, ink=SHADOW_INK):
    pad = int(blur*3); W2, H2 = w+2*pad, h+2*pad
    im = Image.new('L', (W2, H2), 0)
    ImageDraw.Draw(im).rounded_rectangle([pad, pad, pad+w, pad+h], radius=r, fill=255)
    im = im.filter(ImageFilter.GaussianBlur(blur)); a = np.asarray(im, dtype=np.float32)/255
    arr = np.zeros((H2, W2, 4), np.uint8)
    arr[..., 0] = (ink[2]*a).astype(np.uint8); arr[..., 1] = (ink[1]*a).astype(np.uint8)
    arr[..., 2] = (ink[0]*a).astype(np.uint8); arr[..., 3] = (255*a).astype(np.uint8)
    surf = cairo.ImageSurface.create_for_data(arr, cairo.FORMAT_ARGB32, W2, H2)
    KEEP.append(arr)
    return surf, pad

def shadow(c, x, y, w, h, r, a=1.0, strength=1.0):
    """two-layer soft drop shadow (ambient + contact), consistent light from above"""
    if a <= 0.01: return
    q = 6
    wq, hq = max(q, int(round(w/q))*q), max(q, int(round(h/q))*q); rq = int(min(r, wq/2, hq/2))
    for blur, dy, al in ((28, 20, 0.12), (7, 5, 0.07)):
        s, pad = shadow_surf(wq, hq, rq, blur)
        c.save(); c.translate(x-pad+(w-wq)/2, y-pad+dy+(h-hq)/2)
        c.set_source_surface(s, 0, 0); c.paint_with_alpha(al*a*strength); c.restore()

def card(c, x, y, w, h, r, a=1.0, col=WHITE, border=None, sh=1.0):
    """rounded card with soft shadow; border = colour or None"""
    shadow(c, x, y, w, h, r, a, sh)
    rrect(c, x, y, w, h, r); fillp(c, col, a)
    if border is not None: stroke(c, border, 1.5, a*0.9)
    else: c.new_path()

def check(c, cx, cy, r, frac, col=WHITE, a=1.0, wdt=None):
    if frac <= 0 or a <= 0: return
    p = [(cx-0.36*r, cy+0.02*r), (cx-0.1*r, cy+0.28*r), (cx+0.40*r, cy-0.27*r)]
    l1 = math.dist(p[0], p[1]); l2 = math.dist(p[1], p[2]); d = clamp(frac)*(l1+l2)
    c.move_to(*p[0])
    if d <= l1:
        u = d/l1; c.line_to(lerp(p[0][0], p[1][0], u), lerp(p[0][1], p[1][1], u))
    else:
        c.line_to(*p[1]); u = (d-l1)/l2; c.line_to(lerp(p[1][0], p[2][0], u), lerp(p[1][1], p[2][1], u))
    c.set_line_cap(cairo.LINE_CAP_ROUND); c.set_line_join(cairo.LINE_JOIN_ROUND)
    stroke(c, col, wdt or 0.17*r, a)

def star(c, cx, cy, ro, ri, rot=0.0):
    for i in range(10):
        ang = -PI/2 + rot + i*PI/5; rr = ro if i % 2 == 0 else ri
        (c.move_to if i == 0 else c.line_to)(cx+rr*math.cos(ang), cy+rr*math.sin(ang))
    c.close_path()

def glow(c, cx, cy, r0, r1, col, a):
    g = cairo.RadialGradient(cx, cy, r0, cx, cy, r1)
    g.add_color_stop_rgba(0, col[0], col[1], col[2], a); g.add_color_stop_rgba(1, col[0], col[1], col[2], 0)
    c.set_source(g); c.arc(cx, cy, r1, 0, 2*PI); c.fill()

def arrow_curve(c, pts, col, a, wdt=3.2, frac=1.0, head=True):
    """cubic bezier with arrow head at end; pts = p0,c1,c2,p1"""
    if a <= 0 or frac <= 0: return
    p0, c1, c2, p1 = pts
    def bz(u):
        return tuple((1-u)**3*p0[i]+3*(1-u)**2*u*c1[i]+3*(1-u)*u**2*c2[i]+u**3*p1[i] for i in range(2))
    n = 40; m = max(2, int(n*frac)); pts_ = [bz(k/n) for k in range(m+1)]
    c.move_to(*pts_[0])
    for q in pts_[1:]: c.line_to(*q)
    c.set_line_cap(cairo.LINE_CAP_ROUND); stroke(c, col, wdt, a)
    if head and frac > 0.9:
        e = pts_[-1]; b = pts_[-4]; ang = math.atan2(e[1]-b[1], e[0]-b[0]); L = 16
        for s in (-1, 1):
            c.move_to(*e); c.line_to(e[0]-L*math.cos(ang+s*0.5), e[1]-L*math.sin(ang+s*0.5))
        stroke(c, col, wdt, a)

def make_bg(top, bot, blobs, w=1080, h=1920):
    """vertical gradient with large soft colour blobs, pre-rendered once"""
    arr = np.zeros((h, w, 3), np.float32)
    yy = np.linspace(0, 1, h)[:, None, None]
    arr[:] = np.array(top)[None, None, :3]*(1-yy) + np.array(bot)[None, None, :3]*yy
    im = Image.fromarray((arr*255).astype(np.uint8), 'RGB').convert('RGBA')
    for (x, y, r, col, al) in blobs:
        mask = Image.new('L', (w, h), 0); ImageDraw.Draw(mask).ellipse([x-r, y-r, x+r, y+r], fill=int(al*255))
        mask = mask.filter(ImageFilter.GaussianBlur(120))
        solid = Image.new('RGBA', (w, h), tuple(int(v*255) for v in col[:3])+(255,)); solid.putalpha(mask)
        im = Image.alpha_composite(im, solid)
    a = np.asarray(im)[..., [2, 1, 0, 3]].copy()
    s = cairo.ImageSurface.create_for_data(a, cairo.FORMAT_ARGB32, w, h); KEEP.append(a); return s

def to_surface(im):
    """PIL RGBA -> premultiplied cairo ARGB32 surface"""
    a = np.asarray(im.convert('RGBA')).astype(np.float32)
    al = a[..., 3:4]/255.0
    out = np.zeros(a.shape, np.uint8)
    out[..., 0] = (a[..., 2]*al[..., 0]).astype(np.uint8); out[..., 1] = (a[..., 1]*al[..., 0]).astype(np.uint8)
    out[..., 2] = (a[..., 0]*al[..., 0]).astype(np.uint8); out[..., 3] = a[..., 3].astype(np.uint8)
    out = np.ascontiguousarray(out)
    s = cairo.ImageSurface.create_for_data(out, cairo.FORMAT_ARGB32, im.width, im.height); KEEP.append(out)
    return s

def sparks(c, cx, cy, t, t0, n=8, r0=30, r1=70, col=(0.47, 0.27, 0.92, 1), dur=0.45, wdt=4):
    """short radiating strokes: a restrained 'landed' accent"""
    if not (t0 <= t < t0+dur): return
    u = P(t, t0, t0+dur, eo)
    for i in range(n):
        ang = i*2*PI/n + 0.3
        a0 = lerp(r0, r1, u); a1 = a0 + lerp(18, 4, u)
        c.move_to(cx+a0*math.cos(ang), cy+a0*math.sin(ang)); c.line_to(cx+a1*math.cos(ang), cy+a1*math.sin(ang))
    c.set_line_cap(cairo.LINE_CAP_ROUND); stroke(c, col, wdt, 1-u)

class Motes:
    """quiet drifting background shapes (rings, dots, plus signs)"""
    def __init__(self, n=14, seed=3, w=1080, h=1920):
        rng = np.random.default_rng(seed)
        self.items = [(float(rng.uniform(40, w-40)), float(rng.uniform(0, h)), float(rng.uniform(5, 12)), int(rng.integers(0, 3)),
                       float(rng.uniform(8, 18)), float(rng.uniform(0, 6.28))) for _ in range(n)]
        self.h = h
    def draw(self, c, t, col, freeze_after=None):
        tt = min(t, freeze_after) if freeze_after else t
        for (x, y, r, kind, spd, ph) in self.items:
            yy = (y - spd*tt) % (self.h+40) - 20; xx = x + 14*math.sin(tt*0.4+ph)
            a = 0.30 + 0.12*math.sin(tt*0.9+ph)
            if kind == 0:
                c.arc(xx, yy, r, 0, 2*PI); stroke(c, col, 3, a)
            elif kind == 1:
                c.arc(xx, yy, r*0.6, 0, 2*PI); fill(c, col, a)
            else:
                c.move_to(xx-r, yy); c.line_to(xx+r, yy); c.move_to(xx, yy-r); c.line_to(xx, yy+r)
                c.set_line_cap(cairo.LINE_CAP_ROUND); stroke(c, col, 3, a)
