"""Teaching kit for 16:9 "N mistakes / N tips" explainers. The proven pieces of "11 UI Mistakes Beginners Make" (6:47).

Copy next to scene.py:  `from dx_studio import *` then `from teaching16x9 import *`, and call `set_image_dir(...)` in setup().
Optional drawing helpers for custom scenes; adapt tokens and geometry to your project.

  tokens            INK / TXT2 / TXT3 / LINE / FILL / SURF / BRAND* / GOOD / BAD / WARN / PAGE / REDLINE (override after import)
  images            set_image_dir, img, draw_img (cover-fit with a focal point and rounded corners)
  text              T (text with sane defaults), hair (1 px line)
  icons             icon(name, ...): a 24 px grid, 2 px strokes, round caps; icon_off(style, ...) draws deliberately mismatched styles
  devices           phone (iPhone frame, 393 x 852 pt at 1:1, status bar, Dynamic Island, home bar), browser (traffic lights + URL)
  components        button (primary / secondary / ghost x default / hover / pressed / disabled), input_field (label, hint, focus, error, caret)
  annotations       ring, redline_v (Figma-style spacing measurement), callout (big stat + context + source),
                    finger (fingertip contact), cursor_arrow, spinner, wobble_rect + arrow (sketchy -> clean flows)
  truth tools       lum / contrast (real WCAG ratios), meter (pass/fail ratio pill), cvd (Machado 2009 deuteranopia + grayscale)
  structure         segment timing from project.json "segments" + title_card (the chapter card that sits in the gap before each item)
"""
import math, os
from dx_studio import cairo
import numpy as np
from PIL import Image
from dx_studio import *

W, H, CX, CY = 1920, 1080, 960, 540
def hx(s): return hexc(s)
INK, TXT2, TXT3 = hx('#0F172A'), hx('#475569'), hx('#64748B')
LINE, FILL, SURF = hx('#E2E8F0'), hx('#F1F5F9'), WHITE
BRAND, BRAND_D, BRAND_L = hx('#4F46E5'), hx('#4338CA'), hx('#EEF2FF')
GOOD, BAD, WARN = hx('#16A34A'), hx('#DC2626'), hx('#D97706')
PAGE = hx('#F4F4F7')
REDLINE = hx('#F24E1E')

# ---------------------------------------------------------------- images
IMG_DIR = [None]
IMGS = {}
def set_image_dir(path): IMG_DIR[0] = path
def img(name):
    if name not in IMGS: IMGS[name] = to_surface(Image.open(os.path.join(IMG_DIR[0], f'{name}.png')))
    return IMGS[name][0]
def draw_img(c, name, x, y, w, h, r=0, a=1.0, fx=0.5, fy=0.5, zoom=1.0):
    """cover-fit an image into (x, y, w, h) with rounded corners; fx/fy = focal point"""
    s = img(name); sw, sh = s.get_width(), s.get_height(); k = max(w/sw, h/sh)*zoom
    c.save(); rrect(c, x, y, w, h, r) if r else c.rectangle(x, y, w, h); c.clip()
    c.translate(x + w/2 - (fx - 0.5)*(sw*k - w), y + h/2 - (fy - 0.5)*(sh*k - h)); c.scale(k, k); c.translate(-sw/2, -sh/2)
    c.set_source_surface(s, 0, 0); c.get_source().set_filter(cairo.FILTER_GOOD); c.paint_with_alpha(a); c.restore()

def lum(col):
    def ch(v): return v/12.92 if v <= 0.04045 else ((v + 0.055)/1.055)**2.4
    r, g, b = col[:3]; return 0.2126*ch(r) + 0.7152*ch(g) + 0.0722*ch(b)

def contrast(a, b):
    la, lb = sorted((lum(a), lum(b)), reverse=True); return (la + 0.05)/(lb + 0.05)

def to_surface(im):
    im = im.convert('RGBA'); r, g, b, a = im.split(); data = bytearray(Image.merge('RGBA', (b, g, r, a)).tobytes())
    return cairo.ImageSurface.create_for_data(data, cairo.FORMAT_ARGB32, im.width, im.height, im.width*4), data

def T(c, s, x, y, size, w='med', col=INK, a=1.0, align='l', track=0.0, maxw=None):
    if not s or a <= 0: return 0
    return text(c, s, x, y, size, w, col, a, align, track=track, maxw=maxw)

def hair(c, x0, y0, x1, y1, col, a=1.0, w=1.0):
    c.move_to(x0, y0); c.line_to(x1, y1); stroke(c, col, w, a)

def _ic_begin(c, cx, cy, size):
    c.save(); c.translate(cx, cy); k = size/24; c.scale(k, k); c.set_line_cap(cairo.LINE_CAP_ROUND); c.set_line_join(cairo.LINE_JOIN_ROUND)

def icon(c, name, cx, cy, size, col, a=1.0, sw=2.0, filled=False):
    """consistent outline icon set; `sw` in icon units (24 grid)"""
    _ic_begin(c, cx, cy, size)
    def st(): stroke(c, col, sw, a)
    if name == 'home':
        c.move_to(-9, -1.5); c.line_to(0, -9.5); c.line_to(9, -1.5); c.line_to(9, 8); c.curve_to(9, 8.8, 8.5, 9, 8, 9)
        c.line_to(3, 9); c.line_to(3, 3); c.line_to(-3, 3); c.line_to(-3, 9); c.line_to(-8, 9); c.curve_to(-8.5, 9, -9, 8.8, -9, 8); c.close_path()
        fill(c, col, a) if filled else st()
    elif name == 'search':
        c.arc(-1.5, -1.5, 7, 0, 2*PI); st(); c.move_to(3.8, 3.8); c.line_to(9, 9); st()
    elif name == 'heart':
        c.move_to(0, 8.5); c.curve_to(-6, 4.5, -10, 1, -10, -3); c.curve_to(-10, -7, -7, -9.5, -4.2, -9.5); c.curve_to(-2.2, -9.5, -0.8, -8.5, 0, -7)
        c.curve_to(0.8, -8.5, 2.2, -9.5, 4.2, -9.5); c.curve_to(7, -9.5, 10, -7, 10, -3); c.curve_to(10, 1, 6, 4.5, 0, 8.5); c.close_path()
        fill(c, col, a) if filled else st()
    elif name == 'bookmark':
        c.move_to(-6, -9); c.line_to(6, -9); c.line_to(6, 9.5); c.line_to(0, 5); c.line_to(-6, 9.5); c.close_path(); fill(c, col, a) if filled else st()
    elif name == 'bell':
        c.move_to(-7, 5); c.line_to(-7, -2); c.curve_to(-7, -6.5, -4, -9, 0, -9); c.curve_to(4, -9, 7, -6.5, 7, -2); c.line_to(7, 5); c.line_to(8.5, 6.5)
        c.line_to(-8.5, 6.5); c.close_path(); fill(c, col, a) if filled else st()
        c.move_to(-2.5, 9.5); c.curve_to(-1.5, 10.8, 1.5, 10.8, 2.5, 9.5); st()
    elif name == 'user':
        c.arc(0, -4, 4.5, 0, 2*PI); fill(c, col, a) if filled else st()
        c.move_to(-8, 9); c.curve_to(-8, 4.5, -4.5, 2, 0, 2); c.curve_to(4.5, 2, 8, 4.5, 8, 9); fill(c, col, a) if filled else st()
    elif name == 'share':
        c.move_to(0, 3); c.line_to(0, -9); st(); c.move_to(-4, -5); c.line_to(0, -9); c.line_to(4, -5); st()
        c.move_to(-3.5, -2); c.line_to(-6.5, -2); c.line_to(-6.5, 9); c.line_to(6.5, 9); c.line_to(6.5, -2); c.line_to(3.5, -2); st()
    elif name == 'more':
        for d in (-7, 0, 7): c.arc(d, 0, 1.6, 0, 2*PI); fill(c, col, a)
    elif name == 'check':
        c.move_to(-7, 0.5); c.line_to(-2.5, 5); c.line_to(7.5, -5); st()
    elif name == 'x':
        c.move_to(-6, -6); c.line_to(6, 6); c.move_to(6, -6); c.line_to(-6, 6); st()
    elif name == 'clock':
        c.arc(0, 0, 9, 0, 2*PI); st(); c.move_to(0, -5); c.line_to(0, 0); c.line_to(3.5, 2.5); st()
    elif name == 'alert':
        c.move_to(0, -9); c.line_to(9.5, 8); c.line_to(-9.5, 8); c.close_path(); st(); c.move_to(0, -2.5); c.line_to(0, 2); st(); c.arc(0, 5, 1.1, 0, 2*PI); fill(c, col, a)
    elif name == 'pin':
        c.move_to(0, 10); c.curve_to(-5, 4, -8, 0, -8, -3); c.curve_to(-8, -7.5, -4.4, -10, 0, -10); c.curve_to(4.4, -10, 8, -7.5, 8, -3)
        c.curve_to(8, 0, 5, 4, 0, 10); c.close_path(); st(); c.arc(0, -3, 2.8, 0, 2*PI); st()
    elif name == 'star':
        pts = [(math.cos(-PI/2 + k*PI/5)*(9.5 if k % 2 == 0 else 4.2), math.sin(-PI/2 + k*PI/5)*(9.5 if k % 2 == 0 else 4.2)) for k in range(10)]
        c.move_to(*pts[0]); [c.line_to(*q) for q in pts[1:]]; c.close_path(); fill(c, col, a) if filled else st()
    elif name == 'calendar':
        rrect(c, -8.5, -7, 17, 16, 2.5); st(); c.move_to(-8.5, -2); c.line_to(8.5, -2); st()
        c.move_to(-4, -9.5); c.line_to(-4, -5); c.move_to(4, -9.5); c.line_to(4, -5); st()
    elif name == 'plus':
        c.move_to(0, -7); c.line_to(0, 7); c.move_to(-7, 0); c.line_to(7, 0); st()
    elif name == 'arrow':
        c.move_to(-7, 0); c.line_to(7, 0); st(); c.move_to(2, -5); c.line_to(7, 0); c.line_to(2, 5); st()
    elif name == 'chev':
        c.move_to(-2.5, -6); c.line_to(3.5, 0); c.line_to(-2.5, 6); st()
    elif name == 'filter':
        for y, x in ((-6, 3), (0, -3), (6, 4)):
            c.move_to(-9, y); c.line_to(9, y); st(); c.arc(x, y, 2.4, 0, 2*PI); fill(c, WHITE, a); c.arc(x, y, 2.4, 0, 2*PI); st()
    elif name == 'plane':
        c.move_to(-1.5, -9); c.curve_to(-1.5, -10.5, 1.5, -10.5, 1.5, -9); c.line_to(1.5, -2.5); c.line_to(9, 2); c.line_to(9, 4.5); c.line_to(1.5, 2.2)
        c.line_to(1.5, 6.5); c.line_to(4, 8.5); c.line_to(4, 10); c.line_to(0, 9); c.line_to(-4, 10); c.line_to(-4, 8.5); c.line_to(-1.5, 6.5)
        c.line_to(-1.5, 2.2); c.line_to(-9, 4.5); c.line_to(-9, 2); c.line_to(-1.5, -2.5); c.close_path(); fill(c, col, a) if filled else st()
    elif name == 'download':
        c.move_to(0, -9); c.line_to(0, 4); st(); c.move_to(-5, -1); c.line_to(0, 4); c.line_to(5, -1); st(); c.move_to(-8, 9); c.line_to(8, 9); st()
    elif name == 'eyeoff':
        c.move_to(-9, 0); c.curve_to(-6, -6, 6, -6, 9, 0); c.curve_to(6, 6, -6, 6, -9, 0); st(); c.arc(0, 0, 3, 0, 2*PI); st(); c.move_to(-8, 8); c.line_to(8, -8); st()
    elif name == 'speaker':
        c.move_to(-9, -3); c.line_to(-5, -3); c.line_to(1, -8); c.line_to(1, 8); c.line_to(-5, 3); c.line_to(-9, 3); c.close_path(); st()
        c.move_to(5, -5); c.line_to(10, 5); c.move_to(10, -5); c.line_to(5, 5); st()
    elif name == 'sun':
        c.arc(0, 0, 4.5, 0, 2*PI); st()
        for k in range(8):
            ang = k*PI/4; c.move_to(math.cos(ang)*7.5, math.sin(ang)*7.5); c.line_to(math.cos(ang)*10, math.sin(ang)*10); st()
    c.restore()

def icon_off(c, style, name, cx, cy, size, col, a=1.0):
    """deliberately mismatched icons for the 'mismatched icons' mistake"""
    if style == 'filled_big': icon(c, name, cx, cy, size*1.25, col, a, 2.0, filled=True)
    elif style == 'thin': icon(c, name, cx, cy, size*1.1, col, a, 1.0)
    elif style == 'thick': icon(c, name, cx, cy, size*0.9, col, a, 3.4)
    elif style == 'square':
        _ic_begin(c, cx, cy, size*1.05); c.set_line_cap(cairo.LINE_CAP_BUTT); c.set_line_join(cairo.LINE_JOIN_MITER)
        c.rectangle(-4.5, -9, 9, 9); stroke(c, col, 2.6, a); c.move_to(-9, 9); c.line_to(-9, 3); c.line_to(9, 3); c.line_to(9, 9); stroke(c, col, 2.6, a); c.restore()
    else: icon(c, name, cx, cy, size, col, a)

PH_W, PH_H, PH_R = 393.0, 852.0, 55.0

def phone(c, x, y, s, content, a=1.0, dark_status=False, t=0.0):
    """iPhone-style frame; `content(c)` draws in screen points (393 x 852)"""
    c.save(); c.translate(x, y); c.scale(s, s)
    shadow(c, -12, -12, PH_W + 24, PH_H + 24, PH_R + 12, 1.1*a, 1.4)
    rrect(c, -12, -12, PH_W + 24, PH_H + 24, PH_R + 12); fill(c, hx('#1B1B1F'), a)
    rrect(c, -10, -10, PH_W + 20, PH_H + 20, PH_R + 10); stroke(c, hx('#3A3A40'), 1.5, a)
    c.save(); rrect(c, 0, 0, PH_W, PH_H, PH_R); c.clip()
    c.rectangle(0, 0, PH_W, PH_H); fill(c, SURF, a)
    content(c)
    sc = WHITE if dark_status else INK
    T(c, '9:41', 51, 38, 17, 'semi', sc, a, align='c')
    for k in range(4): rrect(c, 290 + k*5, 33 - k*2.4, 3, 4 + k*2.4, 1); fill(c, sc, a)
    for r in (6.5, 10.5):
        c.new_sub_path(); c.arc(322, 39, r, -PI*0.78, -PI*0.22); c.set_line_cap(cairo.LINE_CAP_ROUND); stroke(c, sc, 2.2, a)
    c.arc(322, 38.2, 1.9, 0, 2*PI); fill(c, sc, a)
    rrect(c, 338, 26, 25, 13, 4); stroke(c, sc, 1.2, a*0.5); rrect(c, 340, 28, 21, 9, 2.5); fill(c, sc, a); rrect(c, 364.5, 30, 1.8, 5, 0.9); fill(c, sc, a*0.5)
    rrect(c, PH_W/2 - 63, 11, 126, 37, 18.5); fill(c, (0, 0, 0, 1), a)
    rrect(c, PH_W/2 - 67, PH_H - 13, 134, 5, 2.5); fill(c, sc, a*0.85)
    c.restore(); c.restore()

def browser(c, x, y, w, h, content, a=1.0, url='wander.app/bookings'):
    shadow(c, x, y, w, h, 14, 1.0*a, 1.3)
    rrect(c, x, y, w, h, 14); fill(c, SURF, a)
    c.save(); rrect(c, x, y, w, h, 14); c.clip()
    c.rectangle(x, y, w, 44); fill(c, hx('#F8FAFC'), a); hair(c, x, y + 44.5, x + w, y + 44.5, LINE, a)
    for k, col in enumerate(('#FF5F57', '#FEBC2E', '#28C840')): c.arc(x + 22 + k*20, y + 22, 6, 0, 2*PI); fill(c, hx(col), a)
    uw = min(520, w*0.4); rrect(c, x + w/2 - uw/2, y + 10, uw, 24, 8); fill(c, hx('#EEF1F5'), a)
    T(c, url, x + w/2, y + 27, 13, 'med', TXT3, a, align='c')
    c.save(); c.translate(x, y + 45); content(c); c.restore()
    c.restore()
    rrect(c, x + 0.5, y + 0.5, w - 1, h - 1, 13.5); stroke(c, hx('#D8DDE6'), 1, a)

def button(c, x, y, w, h, label, p=None, kind='primary', a=1.0, r=12, size=16, weight='semi', col=None, icon_name=None, state='default', shadow_=False, upper=False):
    base = col or BRAND
    if kind == 'primary':
        f = {'hover': mixc(base, (0, 0, 0, 1), 0.08), 'pressed': mixc(base, (0, 0, 0, 1), 0.18), 'disabled': mixc(base, WHITE, 0.62)}.get(state, base)
        if shadow_: shadow(c, x, y + 4, w, h, r, 0.9*a, 1.0)
        rrect(c, x, y, w, h, r); fill(c, f, a); tc = WHITE
    elif kind == 'secondary':
        f = {'hover': FILL, 'pressed': hx('#E2E8F0')}.get(state, SURF)
        rrect(c, x, y, w, h, r); fill(c, f, a); rrect(c, x + 0.5, y + 0.5, w - 1, h - 1, r - 0.5); stroke(c, hx('#CBD5E1'), 1, a)
        tc = INK if state != 'disabled' else hx('#94A3B8')
    else:  # ghost
        if state in ('hover', 'pressed'): rrect(c, x, y, w, h, r); fill(c, BRAND_L if state == 'hover' else hx('#E0E7FF'), a)
        tc = base if state != 'disabled' else hx('#A5B4FC')
    lab = label.upper() if upper else label
    if not lab: return
    tr = 0.06 if upper else 0.0
    lw = tw(lab, size, weight, tr); iw = 26 if icon_name else 0
    x0 = x + w/2 - (lw + iw)/2
    if icon_name: icon(c, icon_name, x0 + 9, y + h/2, 18, tc, a)
    T(c, lab, x0 + iw, y + h/2 + size*0.36, size, weight, tc, a, track=tr)

def input_field(c, x, y, w, p=None, label=None, value='', placeholder='', hint=None, a=1.0, state='default', h=48, border=None, ph_col=None, caret=False):
    yy = y
    if label: T(c, label, x, yy + 14, 14, 'semi', INK, a); yy += 22
    bc = border or {'focus': BRAND, 'error': BAD}.get(state, hx('#CBD5E1'))
    rrect(c, x, yy, w, h, 12); fill(c, SURF, a)
    rrect(c, x + 0.5, yy + 0.5, w - 1, h - 1, 11.5); stroke(c, bc, 2 if state in ('focus', 'error') else 1, a)
    if state == 'focus': rrect(c, x - 3, yy - 3, w + 6, h + 6, 15); stroke(c, BRAND, 3, 0.18*a)
    if value: T(c, value, x + 16, yy + h/2 + 6, 16, 'reg', INK, a)
    elif placeholder: T(c, placeholder, x + 16, yy + h/2 + 6, 16, 'reg', ph_col or hx('#94A3B8'), a)
    if caret:
        cx = x + 16 + (tw(value, 16, 'reg') + 1 if value else 0); hair(c, cx, yy + 14, cx, yy + h - 14, BRAND, a, 1.6)
    yy += h
    if hint: T(c, hint, x, yy + 20, 13, 'med', BAD if state == 'error' else TXT3, a); yy += 26
    return yy

def ring(c, x, y, w, h, col, a=1.0, r=14, lw=4, pad=8):
    if a <= 0: return
    rrect(c, x - pad, y - pad, w + 2*pad, h + 2*pad, r + pad); stroke(c, col, lw, a)

def redline_v(c, x, y0, y1, label, a=1.0, col=REDLINE):
    """Figma-style vertical spacing measurement"""
    if a <= 0 or y1 - y0 < 1: return
    hair(c, x, y0, x, y1, col, a, 2); hair(c, x - 7, y0, x + 7, y0, col, a, 2); hair(c, x - 7, y1, x + 7, y1, col, a, 2)
    w = tw(label, 18, 'bold') + 16; rrect(c, x + 12, (y0 + y1)/2 - 14, w, 28, 6); fill(c, col, a)
    T(c, label, x + 12 + w/2, (y0 + y1)/2 + 6.5, 18, 'bold', WHITE, a, align='c')

def callout(c, x, y, big, small, p, a=1.0, col=None, size=84, align='l', src=None):
    """a typographic stat: big number + one line of context (+ optional source)"""
    if a <= 0: return
    T(c, big, x, y, size, 'xb', col or INK, a, align=align, track=-0.02)
    if small: T(c, small, x, y + size*0.62, 28, 'semi', TXT2, a, align=align)
    if src: T(c, src, x, y + size*0.62 + 40, 20, 'med', TXT3, a, align=align)

def finger(c, x, y, a=1.0, down=0.0, s=1.0):
    """a fingertip contact: soft translucent disc + pressed ring"""
    if a <= 0: return
    r = 26*s*(1 - 0.08*down)
    c.arc(x, y, r + 10, 0, 2*PI); fill(c, (0, 0, 0, 1), 0.06*a)
    c.arc(x, y, r, 0, 2*PI); fill(c, hx('#FFD9C7'), 0.78*a); c.arc(x, y, r, 0, 2*PI); stroke(c, hx('#E7A98C'), 2, 0.9*a)
    if down > 0: c.arc(x, y, r + 14*down, 0, 2*PI); stroke(c, BRAND, 4, 0.5*a*down)

def cursor_arrow(c, x, y, a=1.0, s=1.6):
    c.save(); c.translate(x, y); c.scale(s, s)
    c.move_to(0, 0); c.line_to(0, 17); c.line_to(4.2, 13.2); c.line_to(7, 19.6); c.line_to(9.6, 18.4); c.line_to(6.9, 12.2); c.line_to(12.3, 12.2); c.close_path()
    c.set_line_join(cairo.LINE_JOIN_ROUND); fillp(c, (0.06, 0.06, 0.07, 1), a); stroke(c, WHITE, 1.5, a); c.restore()

def spinner(c, cx, cy, r, t, col, a=1.0, w=3):
    c.arc(cx, cy, r, 0, 2*PI); stroke(c, col, w, 0.25*a)
    s0 = t*6.0; c.arc(cx, cy, r, s0, s0 + 1.6); c.set_line_cap(cairo.LINE_CAP_ROUND); stroke(c, col, w, a)

def page_bg(c, a=1.0, col=None):
    c.rectangle(0, 0, W, H); fill(c, col or PAGE, a)

def wobble_rect(c, x, y, w, h, seed):
    pts = []
    for k in range(40):
        u = k/40; per = 2*(w + h); d = u*per
        if d < w: px_, py_ = x + d, y
        elif d < w + h: px_, py_ = x + w, y + d - w
        elif d < 2*w + h: px_, py_ = x + w - (d - w - h), y + h
        else: px_, py_ = x, y + h - (d - 2*w - h)
        j = 1.6*math.sin(seed*3.1 + k*1.7) + 0.9*math.sin(seed + k*0.55)
        pts.append((px_ + j, py_ + j*0.6))
    c.move_to(*pts[0]); [c.line_to(*q) for q in pts[1:]]; c.close_path()

def arrow(c, x0, y0, x1, y1, u, col, a, sketch=0.0, w=3):
    if u <= 0 or a <= 0: return
    ex, ey = lerp(x0, x1, u), lerp(y0, y1, u)
    if sketch > 0.5:
        mx, my = (x0 + ex)/2 + 2*math.sin(x0), (y0 + ey)/2 + 2*math.cos(y0); c.move_to(x0, y0); c.curve_to(mx, my, mx, my, ex, ey)
    else: c.move_to(x0, y0); c.line_to(ex, ey)
    c.set_line_cap(cairo.LINE_CAP_ROUND); stroke(c, col, w, a)
    if u > 0.9:
        ang = math.atan2(y1 - y0, x1 - x0); hl = 13
        c.move_to(ex - hl*math.cos(ang - 0.45), ey - hl*math.sin(ang - 0.45)); c.line_to(ex, ey); c.line_to(ex - hl*math.cos(ang + 0.45), ey - hl*math.sin(ang + 0.45))
        c.set_line_join(cairo.LINE_JOIN_ROUND); stroke(c, col, w, a*P(u, 0.9, 1.0, lin))

def meter(c, x, y, label, need, fg, bg, p, a, big=True):
    r = contrast(fg, bg); ok = r >= need
    T(c, label, x, y, 30, 'bold', INK, a)
    T(c, f"needs {need:g} : 1", x, y + 38, 22, 'med', TXT3, a)
    w = tw(f"{r:.1f} : 1", 30, 'xb') + 44
    rrect(c, x + 520 - w, y - 34, w, 52, 26); fill(c, GOOD if ok else BAD, a)
    T(c, f"{r:.1f} : 1", x + 520 - w/2, y + 3, 30, 'xb', WHITE, a, align='c')

MACH = ((0.367322, 0.860646, -0.227968), (0.280085, 0.672501, 0.047413), (-0.011820, 0.042940, 0.968881))

def _lin(v): return v/12.92 if v <= 0.04045 else ((v + 0.055)/1.055)**2.4

def _gam(v): v = min(1, max(0, v)); return v*12.92 if v <= 0.0031308 else 1.055*v**(1/2.4) - 0.055

def cvd(col, deut=0.0, gray=0.0):
    if deut <= 0 and gray <= 0: return col
    r, g, b = (_lin(v) for v in col[:3])
    if deut > 0:
        rs = [sum(MACH[j][q]*(r, g, b)[q] for q in range(3)) for j in range(3)]; r, g, b = (lerp(o, s_, deut) for o, s_ in zip((r, g, b), rs))
    if gray > 0:
        y_ = 0.2126*r + 0.7152*g + 0.0722*b; r, g, b = (lerp(o, y_, gray) for o in (r, g, b))
    return (_gam(r), _gam(g), _gam(b), col[3] if len(col) > 3 else 1.0)


# ---------------------------------------------------------------- structure: segments + title cards
# project.json: "segments": [{"title": null, "first": 0, "n": 3}, {"title": "Random spacing", "first": 3, "n": 4}, ...]
# "first" = the segment's first voice line; give that line "pause_before": 2.2 so the title card has its gap.
def seg_helpers(VT, segs, end):
    L = [VT.start(i) for i in range(len(VT.lines))]
    def seg_line(k, j=0): return segs[k]['first'] + j
    def seg_start(k): return L[segs[k]['first']]
    def seg_window(k):
        a = (seg_start(k) - 0.7) if segs[k]['title'] else (0.0 if k == 0 else seg_start(k) - 0.6)
        b = (seg_start(k + 1) - 1.5) if k + 1 < len(segs) else end
        return a, b
    def seg_alpha(t, k):
        a, b = seg_window(k)
        return P(t, a, a + 0.35, lin)*(1 - P(t, b - 0.35, b, lin)) if k + 1 < len(segs) else P(t, a, a + 0.35, lin)
    return seg_line, seg_start, seg_window, seg_alpha

TITLE_GLOWS = ((BRAND, 0.25, 0.8, 620), (hx('#06B6D4'), 0.82, 0.25, 520), (hx('#EC4899'), 0.7, 0.95, 420))
def title_card(c, t, t0, title, bg=None, glows=TITLE_GLOWS, size=96):
    """the chapter card: near-black, slowly drifting colour glows, the item's name built big. It fades in 2.1 s before the
    segment's first line (inside the 2.2 s pause) and out 1–1.5 s after it. No numbers, no 'Mistake 3' pills."""
    a = P(t, t0 - 2.1, t0 - 1.75, lin)*(1 - P(t, t0 + 1.0, t0 + 1.5, lin))
    if a <= 0: return
    c.rectangle(0, 0, W, H); fill(c, bg or hx('#0B0B14'), a)
    for j, (col, ox, oy, r) in enumerate(glows):
        x = W*ox + 60*math.sin(t*0.6 + j); y = H*oy + 40*math.cos(t*0.5 + j*2)
        g = cairo.RadialGradient(x, y, 0, x, y, r); g.add_color_stop_rgba(0, col[0], col[1], col[2], 0.55*a); g.add_color_stop_rgba(1, col[0], col[1], col[2], 0)
        c.rectangle(0, 0, W, H); c.set_source(g); c.fill()
    ktext(c, title, 160, 590, size, 'xb', WHITE, t, t0 - 1.8, a, align='l', track=-0.03)

def wipe_reveal(c, u, w, h, draw_bad, draw_good, col=None):
    """bad -> fixed: the fixed version wipes in left to right behind a thin accent line (used on the intro phone)"""
    draw_bad(c)
    if u > 0:
        c.save(); c.rectangle(0, 0, w*u, h); c.clip(); draw_good(c); c.restore()
        if u < 1: hair(c, w*u, 0, w*u, h, col or BRAND, 1.0, 3)
