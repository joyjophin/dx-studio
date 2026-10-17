"""dx_studio.text: HarfBuzz-shaped text (real kerning) drawn with cairo, plus kinetic per-glyph reveals."""
import os
from ._cairo import cairo
import uharfbuzz as hb
from functools import lru_cache
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import RecordingPen
from fontTools.pens.cairoPen import CairoPen
from .core import *

FONT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'fonts')
INK_DEFAULT = hexc('#211638')
FONTS = {  # key: (file in FONT_DIR, toy family name installed on the system, weight)
    'reg': ('DXSans-Regular', 'DXSans', cairo.FONT_WEIGHT_NORMAL),
    'med': ('DXSans-Medium', 'DXSans Medium', cairo.FONT_WEIGHT_NORMAL),
    'semi': ('DXSans-SemiBold', 'DXSans SemiBold', cairo.FONT_WEIGHT_NORMAL),
    'bold': ('DXSans-Bold', 'DXSans', cairo.FONT_WEIGHT_BOLD),
    'xb': ('DXSans-ExtraBold', 'DXSans ExtraBold', cairo.FONT_WEIGHT_NORMAL),
    'med_t': ('DXSansTab-Medium', 'DX Sans Tab Medium', cairo.FONT_WEIGHT_NORMAL),   # tabular figures
    'xb_t': ('DXSansTab-ExtraBold', 'DX Sans Tab ExtraBold', cairo.FONT_WEIGHT_NORMAL),
}
_hb = {}
def hbfont(w):
    if w not in _hb:
        path = os.path.join(FONT_DIR, f'{FONTS[w][0]}.ttf')
        face = hb.Face(hb.Blob.from_file_path(path)); _hb[w] = (hb.Font(face), face.upem)
    return _hb[w]

@lru_cache(8192)
def shape(s, w, size, track=0.0):
    font, upem = hbfont(w); buf = hb.Buffer(); buf.add_str(s); buf.guess_segment_properties()
    hb.shape(font, buf, {"kern": True, "liga": True, "calt": True})
    sc = size/upem; x = 0.0; gl = []
    for info, pos in zip(buf.glyph_infos, buf.glyph_positions):
        gl.append((info.codepoint, x+pos.x_offset*sc, -pos.y_offset*sc)); x += pos.x_advance*sc + track*size
    if gl: x -= track*size
    return tuple(gl), x

def tw(s, size, w='semi', track=0.0): return shape(s, w, size, track)[1] if s else 0.0     # empty strings measure 0 (used to raise)

@lru_cache(7)
def _outline_font(weight):
    font = TTFont(os.path.join(FONT_DIR, FONTS[weight][0]+'.ttf'))
    return font.getGlyphSet(), font.getGlyphOrder(), font['head'].unitsPerEm

@lru_cache(8192)
def _outline(weight, glyph):
    glyphs, names, upem = _outline_font(weight)
    pen = RecordingPen(); glyphs[names[glyph]].draw(pen)
    return pen

def _glyph(c, weight, glyph, x, y, size):
    _, _, upem = _outline_font(weight)
    c.save(); c.translate(x, y); c.scale(size/upem, -size/upem)
    _outline(weight, glyph).replay(CairoPen(_outline_font(weight)[0], c)); c.fill(); c.restore()

def text(c, s, x, y, size, w='semi', col=INK_DEFAULT, a=1.0, align='l', track=0.0, maxw=None):
    if a <= 0.003 or not s: return 0
    if maxw:
        while tw(s, size, w, track) > maxw and size > 20: size -= 1
    gl, wd = shape(s, w, size, track)
    if align == 'c': x -= wd/2
    elif align == 'r': x -= wd
    fam = FONTS[w]
    c.set_source_rgba(col[0], col[1], col[2], col[3]*a)
    for g, gx, gy in gl: _glyph(c, w, g, x+gx, y+gy, size)
    return wd

def ktext(c, s, x, y, size, w, col, t, t0, a=1.0, align='c', track=-0.02, stagger=0.022, dur=0.38, rise=26):
    if a <= 0.003 or t < t0: return 0
    gl, wd = shape(s, w, size, track)
    if align == 'c': x -= wd/2
    elif align == 'r': x -= wd
    fam = FONTS[w]
    for i, (g, gx, gy) in enumerate(gl):
        u = P(t, t0+i*stagger, t0+i*stagger+dur, lin)
        if u <= 0: continue
        c.set_source_rgba(col[0], col[1], col[2], col[3]*a*eo(u))
        _glyph(c, w, g, x+gx, y+gy+rise*(1-back_ease(u, 1.4)), size)
    return wd