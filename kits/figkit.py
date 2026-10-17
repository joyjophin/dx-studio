"""figkit: the shared Figma UI3 kit for the 9:16 interactive-component Shorts (toggle, checkbox, tabs, accordion, tooltip).

Same look as the button / input / dropdown Shorts: a light Figma window in real Figma px inside a rounded screen card,
a camera that zooms to whatever is being edited, and cursor / keycaps / fact cards in screen px on top.
A scene sets KIT[...] (camera keys, cursor keys, clicks, presses, heads) in setup() and composes these pieces.
"""
import math
from dx_studio import cairo
from dx_studio import *
from dx_studio.draw import card as _card

W, H, CX = 1080, 1920, 540
SX, SY, SW, SH, SR = 50, 366, 980, 1150, 34
WS = 1.8
WW, WH = SW/WS, SH/WS
PW = 240; PX0 = WW - PW
TOP_H, TAB_H = 48, 40; BODY0 = TOP_H + TAB_H
KY = 1250
KIT = dict(cam=[(0.0, 0.0, (WW/2, WH/2, WW))], cur=[(0.0, 200, 300)], clicks=[], presses=[], hide=[], heads=[], hstart=[], hend=[], L=[], end=60.0,
           proto_tab=1e9, present_hot=1e9, tool=lambda t: 0)

UI = dict(design='Design', proto='Prototype', share='Share', zoom='100%', position='Position', layout='Layout', autolayout='Auto layout',
          appearance='Appearance', fill='Fill', stroke='Stroke', effects='Effects', export='Export', props='Properties',
          page='Page', variables='Variables', styles='Styles', typo='Typography', inter='Inter', interactions='Interactions',
          scroll='Scroll behavior', scrollv='Scroll with parent', interaction='Interaction', animation='Animation', drafts='Drafts',
          variant='Variant', boolean='Boolean', swap='Instance swap', text_prop='Text', hug='Hug', fixed='Fixed', fill_c='Fill', inside='Inside')

# ================================================================= params shared by every video
def kit_schema(file_name, at=2.0):
    C = lambda k, lab, grp, d: {"key": k, "type": "color", "label": lab, "group": grp, "default": d}
    return [C("bg", "Background", "Palette", "#F3F0FF"), C("ink", "Headline text", "Palette", "#17122B"), C("accent", "Accent", "Palette", "#6C4DFF"),
            C("soft", "Soft accent", "Palette", "#C7B8FF"), C("annot", "Annotations", "Palette", "#FF4F6D"), C("capback", "Captions backing", "Palette", "#17122B"),
            C("f_canvas", "Canvas", "Figma UI", "#F5F5F5"), C("f_panel", "Panels", "Figma UI", "#FFFFFF"), C("f_text", "UI text", "Figma UI", "#1E1E1E"),
            C("f_muted", "UI secondary text", "Figma UI", "#7A7A7A"), C("f_field", "Input fields", "Figma UI", "#F5F5F5"), C("f_line", "Dividers", "Figma UI", "#E6E6E6"),
            C("f_blue", "Selection blue", "Figma UI", "#0D99FF"), C("f_purple", "Component purple", "Figma UI", "#9747FF"), C("f_menu", "Menus", "Figma UI", "#1E1E1E"),
            C("f_present", "Present background", "Figma UI", "#1E1E1E"),
            {"key": "file_name", "type": "text", "label": "File name", "group": "Canvas", "default": file_name, "at": at}]
def sticker_schema(defaults):
    return [{"key": "stickers", "type": "clips", "label": "Stickers", "panel": "Stickers", "lane_label": "Stickers", "label_field": "pose",
             "help": "Joy's reactions. Leave position on auto for the top-right spot beside the headline.",
             "fields": [{"key": "pose", "type": "sticker", "label": "Sticker"},
                        {"key": "size", "type": "number", "label": "Size", "min": 120, "max": 460, "step": 5, "unit": "px"},
                        {"key": "pos", "type": "point", "label": "Position", "auto_label": "top right"},
                        {"key": "mirror", "type": "bool", "label": "Mirror"}],
             "default": defaults}]
def head_schema(heads):
    out = []
    for i, (chip, title) in enumerate(heads):
        at = KIT['hstart'][i] + 0.6 if KIT['hstart'] else 1.0
        out += [{"key": f"chip{i}", "type": "text", "label": f"Beat {i} chip", "group": "Headlines", "default": chip, "at": at},
                {"key": f"title{i}", "type": "text", "label": f"Beat {i} title", "group": "Headlines", "default": title, "at": at}]
    return out

# ================================================================= camera (Figma px window -> screen)
def cam(t):
    K = KIT['cam']; cx, cy, vw = K[0][2]
    for t0, d, (nx, ny, nw) in K[1:]:
        if t < t0: break
        u = P(t, t0, t0 + d, eio)
        cx, cy, vw = lerp(cx, nx, u), lerp(cy, ny, u), vw*(nw/vw)**u
    return cx, cy, vw
def to_screen(t, x, y):
    cx, cy, vw = cam(t); s = SW/vw; vh = vw*SH/SW
    return SX + (x - (cx - vw/2))*s, SY + (y - (cy - vh/2))*s
def camera_motion(c, t):
    cx, cy, vw = cam(t); s = SW/vw; vh = vw*SH/SW
    c.translate(SX, SY); c.scale(s, s); c.translate(-(cx - vw/2), -(cy - vh/2))
V_ALL = (WW/2, WH/2, WW)

# ================================================================= primitives (Figma px)
def ui(c, s, x, y, p, size=11, w='med', col=None, a=1.0, align='l', maxw=None):
    return text(c, s, x, y, size, w, col or p.f_text, a, align, maxw=maxw)
def chevron(c, x, y, col, s=3.2, a=1.0, wdt=1.0):
    c.move_to(x-s, y-s*0.5); c.line_to(x, y+s*0.5); c.line_to(x+s, y-s*0.5); stroke(c, col, wdt, a)
def plus_icon(c, cx, cy, col, s=4.5, a=1.0, wdt=1.0):
    c.move_to(cx-s, cy); c.line_to(cx+s, cy); c.move_to(cx, cy-s); c.line_to(cx, cy+s); stroke(c, col, wdt, a)
def minus_icon(c, cx, cy, col, s=4.5, a=1.0): c.move_to(cx-s, cy); c.line_to(cx+s, cy); stroke(c, col, 1.0, a)
def diamond(c, cx, cy, r):
    c.move_to(cx, cy-r); c.line_to(cx+r, cy); c.line_to(cx, cy+r); c.line_to(cx-r, cy); c.close_path()
def comp_icon(c, cx, cy, col, s=1.0, a=1.0):
    for dx, dy in ((0, -3.2), (3.2, 0), (0, 3.2), (-3.2, 0)): diamond(c, cx+dx*s, cy+dy*s, 1.9*s); fill(c, col, a)
def inst_icon(c, cx, cy, col, s=1.0, a=1.0): diamond(c, cx, cy, 4.6*s); stroke(c, col, 1.2*s, a)
def var_icon(c, cx, cy, col, a=1.0):
    diamond(c, cx, cy, 4.8); stroke(c, col, 1.0, a); c.move_to(cx-4.8, cy); c.line_to(cx+4.8, cy); stroke(c, col, 1.0, a)
def eye_icon(c, cx, cy, col, a=1.0, closed=False):
    if closed:
        c.move_to(cx-5.5, cy-1); c.curve_to(cx-2, cy+3, cx+2, cy+3, cx+5.5, cy-1); stroke(c, col, 1.0, a)
        for dx in (-3.5, 0, 3.5): c.move_to(cx+dx, cy+2); c.line_to(cx+dx*1.15, cy+4); stroke(c, col, 1.0, a)
        return
    c.save(); c.translate(cx, cy); c.scale(1, 0.55); c.arc(0, 0, 5.5, 0, 2*PI); c.restore(); stroke(c, col, 1.0, a)
    c.arc(cx, cy, 1.6, 0, 2*PI); fill(c, col, a)
def bolt(c, cx, cy, col, a=1.0):
    c.move_to(cx+1.5, cy-5); c.line_to(cx-3, cy+1); c.line_to(cx, cy+1); c.line_to(cx-1.5, cy+5); c.line_to(cx+3, cy-1)
    c.line_to(cx, cy-1); c.close_path(); fill(c, col, a)
def frame_icon(c, cx, cy, col, a=1.0):
    for d in (-2.5, 2.5): c.move_to(cx+d, cy-5); c.line_to(cx+d, cy+5); c.move_to(cx-5, cy+d); c.line_to(cx+5, cy+d)
    stroke(c, col, 1.0, a)
def toggle_glyph(c, x, y, on, p, a=1.0):
    rrect(c, x, y, 24, 14, 7); fill(c, p.f_blue if on else p.f_line, a)
    c.arc(x + (17 if on else 7), y + 7, 5, 0, 2*PI); fill(c, WHITE, a)
def field(c, x, y, w, p, icon=None, value='', focus=0.0, h=24, a=1.0, chev=False, vcol=None, suffix=None):
    rrect(c, x, y, w, h, 5); fill(c, p.f_field, a)
    if focus > 0:
        rrect(c, x, y, w, h, 5); fill(c, WHITE, a*focus); rrect(c, x+0.5, y+0.5, w-1, h-1, 4.5); stroke(c, p.f_blue, 1.0, a*focus)
    tx = x + 8
    if icon:
        if callable(icon): icon(c, x+11, y+h/2); tx = x + 22
        else: ui(c, icon, x+8, y+h/2+4, p, 11, 'med', p.f_muted, a); tx = x + 22
    ui(c, value, tx, y+h/2+4, p, 11, 'med', vcol or p.f_text, a, maxw=w-(tx-x)-(24 if chev else 8))
    if suffix: ui(c, suffix, x+w-(20 if chev else 8), y+h/2+4, p, 10, 'med', p.f_muted, a, align='r')
    if chev: chevron(c, x+w-10, y+h/2, p.f_muted, 2.6, a)
def divider(c, y, p, a=1.0): c.move_to(PX0, y+0.5); c.line_to(PX0+PW, y+0.5); stroke(c, p.f_line, 1.0, a)
def sec_title(c, y, title, p, plus=True, extra=0, a=1.0, hot=0.0):
    if hot > 0: rrect(c, PX0+PW-30, y+6, 20, 20, 4); fill(c, p.f_field, hot*a)
    ui(c, title, PX0+16, y+21, p, 11, 'semi', p.f_text, a)
    if plus: plus_icon(c, PX0+PW-20, y+16, p.f_text, 4.2, a)
    for i in range(extra):
        x = PX0+PW-(44 if plus else 20)-i*22; rrect(c, x-5, y+11, 10, 10, 2); stroke(c, p.f_muted, 1.0, a*0.9)
def sel_box(c, x, y, w, h, col, pill=None, handles=True, a=1.0):
    if a <= 0: return
    c.rectangle(x, y, w, h); stroke(c, col, 1.0, a)
    if handles:
        for hx, hy in ((x, y), (x+w, y), (x, y+h), (x+w, y+h)):
            c.rectangle(hx-2.6, hy-2.6, 5.2, 5.2); fill(c, WHITE, a); c.rectangle(hx-2.6, hy-2.6, 5.2, 5.2); stroke(c, col, 1.0, a)
    if pill:
        pw = tw(pill, 9, 'semi') + 10; px = x + w/2 - pw/2; py = y + h + 6
        rrect(c, px, py, pw, 14, 3); fill(c, col, a); text(c, pill, px+5, py+10.2, 9, 'semi', WHITE, a)
def set_frame(c, x, y, w, h, name, p, a=1.0):
    """a component set: purple dashed border with its name above"""
    if a <= 0: return
    rrect(c, x, y, w, h, 5); c.save(); c.set_dash([4, 3]); stroke(c, p.f_purple, 1.0, a); c.restore()
    comp_icon(c, x+5, y-8, p.f_purple, 0.75, a); text(c, name, x+12, y-4.5, 9, 'semi', p.f_purple, a)
def var_label(c, x, y, s, p, a=1.0): text(c, s, x, y-4, 8, 'semi', p.f_purple, a)
def comp_label(c, x, y, s, p, a=1.0):
    comp_icon(c, x+4, y-7.5, p.f_purple, 0.7, a); text(c, s, x+11, y-4, 8.5, 'semi', p.f_purple, a)
def noodle(c, x0, y0, x1, y1, u, p, live=None, side=1):
    """a prototype connection: from the right edge of the source to the destination (drawn on by u)"""
    if u <= 0: return
    ex, ey = live if (live and u < 1) else (x1, y1)
    bulge = side*(22 + 0.2*abs(ey - y0))
    c.move_to(x0, y0); c.curve_to(x0+bulge, y0, ex+bulge, ey, ex+2*side, ey); stroke(c, p.f_blue, 1.4)
    c.arc(x0, y0, 3, 0, 2*PI); fill(c, p.f_blue)
    c.move_to(ex+1*side, ey); c.line_to(ex+7*side, ey-4); c.line_to(ex+7*side, ey+4); c.close_path(); fill(c, p.f_blue)
def annot_below(c, cx, y, s, p, a=1.0, size=9):
    """a red annotation pill under a point, with a small arrow up"""
    if a <= 0: return
    w = tw(s, size, 'bold') + size*1.4; h = size*1.8
    c.move_to(cx-4, y); c.line_to(cx+4, y); c.line_to(cx, y-5); c.close_path(); fill(c, p.annot, a)
    rrect(c, cx-w/2, y, w, h, h/2); fill(c, p.annot, a); text(c, s, cx, y+h*0.68, size, 'bold', WHITE, a, align='c')
def annot_tag(c, x, y, s, p, a=1.0, size=9):
    """a red annotation tag pointing left at (x, y)"""
    if a <= 0: return
    w = tw(s, size, 'bold') + 12
    c.move_to(x-5, y); c.line_to(x+1, y-4); c.line_to(x+1, y+4); c.close_path(); fill(c, p.annot, a)
    rrect(c, x+1, y-8, w, 16, 8); fill(c, p.annot, a); text(c, s, x+7, y+3.3, size, 'bold', WHITE, a)

# ================================================================= chrome
def el_canvas(c, t, p): c.rectangle(0, 0, PX0, WH); fill(c, p.f_canvas)
def canvas_ctx(c, t): c.rectangle(0, 0, PX0, WH); c.clip()
def el_filepill(c, t, p):
    x, y, w, h = 10, 10, 168, 40
    shadow(c, x, y, w, h, 10, 0.5); rrect(c, x, y, w, h, 10); fill(c, p.f_panel)
    rrect(c, x+8, y+8, 24, 24, 6); fill(c, p.f_field)
    for i in range(3): c.move_to(x+14, y+15+i*5); c.line_to(x+26, y+15+i*5); stroke(c, p.f_text, 1.1)
    ui(c, p.file_name, x+40, y+18, p, 11, 'semi', p.f_text, maxw=100)
    ui(c, UI['drafts'], x+40, y+31, p, 9.5, 'med', p.f_muted)
    rrect(c, x+w-26, y+13, 14, 14, 3); stroke(c, p.f_muted, 1.0); c.move_to(x+w-21, y+13); c.line_to(x+w-21, y+27); stroke(c, p.f_muted, 1.0)
TB_W, TB_H = 288.0, 44.0
def tb_rect(): return (PX0 - TB_W)/2, WH - 12 - TB_H, TB_W, TB_H
def el_toolbar(c, t, p):
    x, y, w, h = tb_rect()
    shadow(c, x, y, w, h, 12, 0.6); rrect(c, x, y, w, h, 12); fill(c, p.f_panel)
    active = KIT['tool'](t)
    for i in range(6):
        bx = x + 8 + i*34; by = y + 6
        if i == active: rrect(c, bx, by, 32, 32, 7); fill(c, p.f_blue)
        col = WHITE if i == active else p.f_text; cx, cy = bx + 16, by + 16
        if i == 0: c.move_to(cx-4, cy-7); c.line_to(cx+6, cy+1); c.line_to(cx+1, cy+2); c.line_to(cx-1, cy+7); c.close_path(); fill(c, col)
        elif i == 1:
            for d in (-3, 3): c.move_to(cx+d, cy-7); c.line_to(cx+d, cy+7); c.move_to(cx-7, cy+d); c.line_to(cx+7, cy+d)
            stroke(c, col, 1.1)
        elif i == 2: c.rectangle(cx-6, cy-6, 12, 12); stroke(c, col, 1.1)
        elif i == 3:
            c.move_to(cx, cy-7); c.line_to(cx+6, cy+2); c.line_to(cx, cy+7); c.line_to(cx-6, cy+2); c.close_path(); stroke(c, col, 1.1)
            c.arc(cx, cy+1, 1.4, 0, 2*PI); fill(c, col)
        elif i == 4: text(c, 'T', cx-4.2, cy+5.2, 15, 'reg', col)
        elif i == 5: c.arc(cx, cy-1, 6.5, 0.6*PI, 2.35*PI); c.line_to(cx-6.4, cy+6.4); c.close_path(); stroke(c, col, 1.1)
    dx = x + 8 + 6*34 + 4; c.move_to(dx, y+12); c.line_to(dx, y+h-12); stroke(c, p.f_line, 1.0)
    star(c, dx+20, y+h/2, 7, 2.4); fill(c, p.f_text)
    rrect(c, dx+36, y+15, 22, 14, 7); fill(c, p.f_field); c.arc(dx+43, y+22, 5, 0, 2*PI); fill(c, p.f_muted)
def el_panel_top(c, t, p):
    c.rectangle(PX0, 0, PW, WH); fill(c, p.f_panel)
    c.move_to(PX0+0.5, 0); c.line_to(PX0+0.5, WH); stroke(c, p.f_line, 1.0)
    c.arc(PX0+26, 24, 11, 0, 2*PI); fill(c, mixc(p.accent, WHITE, 0.15)); text(c, 'J', PX0+22.4, 28, 11, 'bold', WHITE)
    hx = PX0 + PW - 94; tp = KIT['present_hot']; hot = window(t, tp-0.35, tp-0.15, tp+0.2, tp+0.4)
    if hot > 0: rrect(c, hx-12, 12, 34, 24, 5); fill(c, p.f_field, hot)
    c.move_to(hx-4, 18); c.line_to(hx+5, 24); c.line_to(hx-4, 30); c.close_path(); stroke(c, p.f_text, 1.1)
    chevron(c, hx+14, 24, p.f_text, 2.4)
    rrect(c, PX0+PW-16-56, 12, 56, 24, 5); fill(c, p.f_blue); text(c, UI['share'], PX0+PW-44, 28, 11, 'semi', WHITE, align='c')
    proto = t >= KIT['proto_tab']; x = PX0 + 8
    for i, lab in enumerate((UI['design'], UI['proto'])):
        wtab = tw(lab, 11, 'semi') + 16; on = (i == 1) == proto
        if on: rrect(c, x, 56, wtab, 24, 5); fill(c, p.f_field)
        ui(c, lab, x+8, 72, p, 11, 'semi', p.f_text if on else p.f_muted); x += wtab + 8
    ui(c, UI['zoom'], PX0+PW-26, 72, p, 11, 'med', p.f_text, align='r'); chevron(c, PX0+PW-16, 68, p.f_text, 2.4)
    divider(c, BODY0, p)
def proto_tab_pos(): return PX0 + 16 + tw(UI['design'], 11, 'semi') + 24 + tw(UI['proto'], 11, 'semi')/2, 70
def present_btn_pos(): return PX0 + PW - 94, 24
def el_screen(c, t, p):
    shadow(c, SX, SY, SW, SH, SR, 1.0, 1.4); rrect(c, SX, SY, SW, SH, SR); fill(c, p.f_canvas)
def screen_ctx(c, t): rrect(c, SX, SY, SW, SH, SR); c.clip()

# ================================================================= right panel: data-driven sections
SEC_H = dict(type=40, position=62, layout=62, autolayout=158, appearance=62, fill=62, fill_none=40, stroke=104, stroke_none=40, effects=40,
             props=40, page=62, variables=40, styles=40, export=40, scroll=62, typo=94, text_content=40)
def sec_height(s):
    k = s[0]
    if k == 'interactions': return 40 + 32*len(s[1])
    if k == 'props_set': return 40 + 34*len(s[1])
    if k in ('props_var', 'props_inst'): return 40 + 32*len(s[1])
    return SEC_H[k]
def sec_y(secs, name, nth=0):
    y = BODY0; n = 0
    for s in secs:
        if s[0] == name:
            if n == nth: return y
            n += 1
        y += sec_height(s)
    return y
def draw_section(c, s, y, t, p):
    k = s[0]; x0 = PX0 + 16; half = 100; x1 = PX0 + 124
    if k == 'type':
        name, kind = s[1], s[2]; purple = kind in ('comp', 'set', 'variant', 'inst')
        col = p.f_purple if purple else p.f_text; tx = x0 + 14
        if kind == 'frame': frame_icon(c, x0+4, y+20, p.f_text)
        elif kind == 'inst': inst_icon(c, x0+4, y+20, p.f_purple, 0.9)
        elif kind in ('comp', 'set', 'variant'): comp_icon(c, x0+4, y+20, p.f_purple, 0.9)
        elif kind == 'rect': c.rectangle(x0, y+16, 8, 8); stroke(c, p.f_text, 1.0)
        elif kind == 'ellipse': c.arc(x0+4, y+20, 4.5, 0, 2*PI); stroke(c, p.f_text, 1.0)
        elif kind == 'text': text(c, 'T', x0, y+24.5, 11, 'med', p.f_text)
        ui(c, name, tx, y+24, p, 11, 'semi', col, maxw=150); chevron(c, tx + min(150, tw(name, 11, 'semi')) + 8, y+20, p.f_muted, 2.4)
        for i in range(2): rrect(c, PX0+PW-26-i*22, y+14, 12, 12, 2); stroke(c, p.f_muted, 1.0, 0.8)
    elif k == 'position':
        sec_title(c, y, UI['position'], p, plus=False)
        field(c, x0, y+30, half, p, 'X', str(s[1])); field(c, x1, y+30, half, p, 'Y', str(s[2]), focus=s[4] if len(s) > 4 else 0.0)
        if len(s) > 3 and s[3] is not None:      # absolute-position toggle highlighted
            hot = s[3]; bx = PX0+PW-30
            rrect(c, bx-2, y+6, 20, 20, 4); fill(c, mixc(p.f_field, p.f_blue, 0.25*hot) if hot else p.f_field)
            c.rectangle(bx+3, y+11, 10, 10); stroke(c, p.f_blue if hot > 0.5 else p.f_muted, 1.0); c.rectangle(bx+6, y+14, 4, 4); fill(c, p.f_blue if hot > 0.5 else p.f_muted)
    elif k == 'layout':
        sec_title(c, y, UI['layout'], p, plus=False)
        field(c, x0, y+30, half, p, 'W', str(s[1])); field(c, x1, y+30, half, p, 'H', str(s[2]))
    elif k == 'autolayout':
        d = s[1]; hot = d.get('hot', {})
        sec_title(c, y, UI['autolayout'], p, plus=False, extra=2)
        field(c, x0, y+30, half, p, 'W', str(d.get('w', '')), suffix=d.get('wmode', UI['hug']), chev=True, focus=hot.get('w', 0))
        field(c, x1, y+30, half, p, 'H', str(d.get('h', '')), suffix=d.get('hmode', UI['hug']), chev=True, focus=hot.get('h', 0))
        rrect(c, x0, y+62, 72, 24, 5); fill(c, p.f_field)
        hz = d.get('dir', 'h') == 'h'; rrect(c, x0+(25 if hz else 1), y+64, 22, 20, 4); fill(c, WHITE)
        for j, (ax, ay) in enumerate(((x0+12, y+74), (x0+36, y+74), (x0+60, y+74))):
            if j == 0: c.move_to(ax, ay-5); c.line_to(ax, ay+5); c.move_to(ax-3, ay+2); c.line_to(ax, ay+5); c.line_to(ax+3, ay+2)
            elif j == 1: c.move_to(ax-5, ay); c.line_to(ax+5, ay); c.move_to(ax+2, ay-3); c.line_to(ax+5, ay); c.line_to(ax+2, ay+3)
            else: c.move_to(ax-5, ay-3); c.line_to(ax+2, ay-3); c.arc(ax+2, ay, 3, -PI/2, PI/2); c.line_to(ax-3, ay+3)
            stroke(c, p.f_text if (j == 1) == hz else p.f_muted, 1.1)
        def gap_ic(c, cx, cy):
            for dd in (-3.5, 3.5): c.move_to(cx+dd, cy-4); c.line_to(cx+dd, cy+4)
            stroke(c, p.f_muted, 1.0)
        field(c, x0, y+94, half, p, gap_ic, str(d.get('gap', '10')), focus=hot.get('gap', 0), chev=d.get('gap') == 'Auto')
        # alignment grid (UI3): 3 x 3 dots, the active cell drawn as bars
        gx, gy, gw, gh = x1, y+62, half, 56
        rrect(c, gx, gy, gw, gh, 5); fill(c, p.f_field)
        if hot.get('align', 0) > 0: rrect(c, gx+0.5, gy+0.5, gw-1, gh-1, 4.5); stroke(c, p.f_blue, 1.0, hot['align'])
        al = d.get('align', (0, 1))           # (col, row)
        for r in range(3):
            for cc in range(3):
                px_, py_ = gx + 22 + cc*28, gy + 10 + r*18
                if (cc, r) == tuple(al):
                    if hz:
                        for j, hh in enumerate((8, 12, 6)): rrect(c, px_-5+j*4, py_-hh/2, 2.4, hh, 1.2); fill(c, p.f_blue)
                    else:
                        for j, ww in enumerate((8, 12, 6)): rrect(c, px_-ww/2, py_-5+j*4, ww, 2.4, 1.2); fill(c, p.f_blue)
                else:
                    c.arc(px_, py_, 1.3, 0, 2*PI); fill(c, p.f_muted, 0.8)
        def padh(c, cx, cy):
            c.move_to(cx-4.5, cy-4.5); c.line_to(cx-4.5, cy+4.5); c.move_to(cx+4.5, cy-4.5); c.line_to(cx+4.5, cy+4.5); stroke(c, p.f_muted, 1.0)
            c.rectangle(cx-2, cy-2.5, 4, 5); stroke(c, p.f_muted, 0.9)
        def padv(c, cx, cy):
            c.move_to(cx-4.5, cy-4.5); c.line_to(cx+4.5, cy-4.5); c.move_to(cx-4.5, cy+4.5); c.line_to(cx+4.5, cy+4.5); stroke(c, p.f_muted, 1.0)
            c.rectangle(cx-2.5, cy-2, 5, 4); stroke(c, p.f_muted, 0.9)
        field(c, x0, y+126, half, p, padh, str(d.get('padh', '0')), focus=hot.get('pad', 0))
        field(c, x1, y+126, half, p, padv, str(d.get('padv', '0')), focus=hot.get('pad', 0))
    elif k == 'appearance':
        hot = s[3] if len(s) > 3 else 0.0; hop = s[4] if len(s) > 4 else 0.0
        ui(c, UI['appearance'], PX0+16, y+21, p, 11, 'semi', p.f_text)
        hid = s[5] if len(s) > 5 else 0.0
        if hid > 0: rrect(c, PX0+PW-50, y+6, 20, 20, 4); fill(c, mixc(p.f_field, p.f_blue, 0.25), hid)
        eye_icon(c, PX0+PW-40, y+16, p.f_blue if hid > 0.5 else p.f_text, closed=hid > 0.5); rrect(c, PX0+PW-25, y+11, 10, 10, 2); stroke(c, p.f_muted, 1.0, 0.9)
        def op_ic(c, cx, cy):
            c.rectangle(cx-4.5, cy-4.5, 9, 9); stroke(c, p.f_muted, 1.0); c.rectangle(cx-4.5, cy-4.5, 4.5, 4.5); c.rectangle(cx, cy, 4.5, 4.5); fill(c, p.f_muted)
        def rad_ic(c, cx, cy):
            c.move_to(cx-4.5, cy+4.5); c.line_to(cx-4.5, cy); c.arc(cx, cy, 4.5, PI, 1.5*PI); c.line_to(cx+4.5, cy-4.5); stroke(c, p.f_muted, 1.1)
        field(c, x0, y+30, half, p, op_ic, str(s[1]), focus=hop); field(c, x1, y+30, half, p, rad_ic, str(s[2]), focus=hot)
    elif k == 'fill':
        hx_, col = s[1], s[2]; hot = s[3] if len(s) > 3 else 0.0
        sec_title(c, y, UI['fill'], p, extra=1)
        def sw(c, cx, cy):
            rrect(c, cx-5, cy-5, 10, 10, 2); fill(c, col); rrect(c, cx-5, cy-5, 10, 10, 2); stroke(c, p.f_line, 0.8)
        field(c, x0, y+30, 172, p, sw, hx_, suffix='100%', focus=hot)
        eye_icon(c, PX0+PW-40, y+42, p.f_muted); minus_icon(c, PX0+PW-20, y+42, p.f_muted, 4)
    elif k == 'fill_none': sec_title(c, y, UI['fill'], p, extra=1, hot=s[1] if len(s) > 1 else 0)
    elif k == 'stroke':
        hx_, col, wt_ = s[1], s[2], s[3]; hot = s[4] if len(s) > 4 else 0.0
        sec_title(c, y, UI['stroke'], p, extra=1)
        def sw(c, cx, cy):
            rrect(c, cx-5, cy-5, 10, 10, 2); fill(c, col); rrect(c, cx-5, cy-5, 10, 10, 2); stroke(c, p.f_line, 0.8)
        field(c, x0, y+30, 172, p, sw, hx_, suffix='100%', focus=hot)
        eye_icon(c, PX0+PW-40, y+42, p.f_muted); minus_icon(c, PX0+PW-20, y+42, p.f_muted, 4)
        def wtic(c, cx, cy):
            for i, w_ in enumerate((0.8, 1.4, 2.0)): c.move_to(cx-4.5, cy-3+i*3); c.line_to(cx+4.5, cy-3+i*3); stroke(c, p.f_muted, w_*0.6)
        field(c, x0, y+62, half, p, None, UI['inside'], chev=True); field(c, x1, y+62, half, p, wtic, str(wt_), focus=hot)
    elif k == 'stroke_none': sec_title(c, y, UI['stroke'], p, extra=0, hot=s[1] if len(s) > 1 else 0)
    elif k in ('effects', 'export', 'variables', 'styles'): sec_title(c, y, UI[k], p, plus=k in ('effects', 'export'))
    elif k == 'page':
        sec_title(c, y, UI['page'], p, plus=False)
        def sw(c, cx, cy):
            rrect(c, cx-5, cy-5, 10, 10, 2); fill(c, p.f_canvas); rrect(c, cx-5, cy-5, 10, 10, 2); stroke(c, p.f_line, 0.8)
        field(c, x0, y+30, 172, p, sw, hex_of(p.f_canvas)[1:].upper(), suffix='100%')
    elif k == 'typo':
        sec_title(c, y, UI['typo'], p, plus=False, extra=1)
        field(c, x0, y+30, 208, p, None, UI['inter'], chev=True)
        field(c, x0, y+62, half, p, None, s[1], chev=True); field(c, x1, y+62, half, p, None, str(s[2]), chev=True)
    elif k == 'props':
        sec_title(c, y, UI['props'], p, hot=s[1] if len(s) > 1 else 0)
    elif k == 'props_set':
        sec_title(c, y, UI['props'], p)
        for j, (kind, name, vals, foc) in enumerate(s[1]):
            ry = y + 32 + j*34
            if kind == 'variant': var_icon(c, x0+5, ry+12, p.f_text)
            elif kind == 'text': text(c, 'T', x0+1, ry+16, 11, 'med', p.f_text)
            elif kind == 'bool': rrect(c, x0, ry+8, 10, 7, 3.5); stroke(c, p.f_text, 1.0)
            ui(c, name, x0+16, ry+16, p, 11, 'med', p.f_text, maxw=196)
            ui(c, vals, x0+16, ry+31, p, 10, 'med', p.f_muted, maxw=196)
            if foc > 0: rrect(c, x0-4, ry, 216, 38, 5); stroke(c, p.f_blue, 1.0, foc)
    elif k == 'props_var':
        sec_title(c, y, UI['props'], p, plus=False)
        for j, (name, val) in enumerate(s[1]):
            ry = y + 30 + j*32
            var_icon(c, x0+5, ry+12, p.f_text); ui(c, name, x0+16, ry+16, p, 11, 'med', p.f_muted)
            field(c, x1-10, ry, 110, p, None, val, chev=True)
    elif k == 'props_inst':
        sec_title(c, y, UI['props'], p, plus=False)
        for j, (kind, name, val) in enumerate(s[1]):
            ry = y + 30 + j*32
            ui(c, name, x0, ry+16, p, 11, 'med', p.f_muted)
            if kind == 'toggle': toggle_glyph(c, x1-10, ry+5, bool(val), p)
            elif kind == 'text': field(c, x1-10, ry, 110, p, None, val)
            else: field(c, x1-10, ry, 110, p, None, val, chev=True)
    elif k == 'interactions':
        sec_title(c, y, UI['interactions'], p)
        for j, (trig, dest) in enumerate(s[1]):
            ry = y + 32 + j*32
            field(c, x0, ry, 208, p, lambda c, cx, cy: bolt(c, cx, cy, p.f_text), trig)
            ui(c, '→ ' + dest, x0+200, ry+16, p, 10, 'med', p.f_muted, align='r')
    elif k == 'scroll':
        sec_title(c, y, UI['scroll'], p, plus=False)
        field(c, x0, y+30, 208, p, None, UI['scrollv'], chev=True)
    elif k == 'text_content':
        sec_title(c, y, 'Text', p, plus=False)
    divider(c, y + sec_height(s), p)
def draw_panel(c, t, p, secs):
    y = BODY0
    for s in secs: draw_section(c, s, y, t, p); y += sec_height(s)

# ================================================================= property-type menu and the interaction popover
MENU_W, MENU_ITEM = 150.0, 26.0
def prop_menu(c, t, p, mx, my, t_open, t_close, t_pick, pick=0):
    a = P(t, t_open+0.02, t_open+0.14, lin)*(1-P(t, t_close+0.08, t_close+0.2, lin))
    if a <= 0: return
    items = (UI['variant'], UI['boolean'], UI['swap'], UI['text_prop']); mh = 16 + MENU_ITEM*len(items)
    shadow(c, mx, my, MENU_W, mh, 8, a); rrect(c, mx, my, MENU_W, mh, 8); fill(c, p.f_menu, a)
    for i, s in enumerate(items):
        iy = my + 8 + i*MENU_ITEM
        if i == pick and t >= t_pick - 0.12: rrect(c, mx+6, iy, MENU_W-12, MENU_ITEM, 5); fill(c, p.f_blue, a)
        text(c, s, mx+30, iy+17, 11, 'med', WHITE, a)
        icx = mx + 18; icy = iy + 13
        if i == 0: var_icon(c, icx, icy, WHITE, a)
        elif i == 1: rrect(c, icx-5, icy-3.5, 10, 7, 3.5); stroke(c, WHITE, 1.0, a)
        elif i == 2: inst_icon(c, icx, icy, WHITE, 0.9, a)
        else: text(c, 'T', icx-3.5, icy+4.5, 11, 'med', WHITE, a)
POP_X, POP_Y, POP_W, POP_H = PX0 - 8 - 240, 62.0, 240.0, 300.0
def pop_rows():
    y = POP_Y
    return dict(trigger=y+58, action=y+92, dest=y+126, anim=y+188, ease=y+222, curve=y+254, close=(POP_X+POP_W-18, y+22))
def popover(c, t, p, cfg):
    """cfg: t_open, t_close, trigger, trig_hot, action, prop, dest, anim, anim_hot, ease, dur, ease_hot, from_instant"""
    t_open, t_close = cfg['t_open'], cfg['t_close']
    a = P(t, t_open, t_open+0.15, lin)*(1-P(t, t_close, t_close+0.15, lin))
    if a <= 0: return
    x, y, w, h = POP_X, POP_Y, POP_W, POP_H; r = pop_rows()
    c.save(); u = P(t, t_open, t_open+0.22, eo); s = lerp(0.96, 1, u); c.translate(x+w, y); c.scale(s, s); c.translate(-(x+w), -y)
    shadow(c, x, y, w, h, 10, a*1.2); rrect(c, x, y, w, h, 10); fill(c, p.f_panel, a); rrect(c, x+0.5, y+0.5, w-1, h-1, 9.5); stroke(c, p.f_line, 1.0, a)
    ui(c, UI['interaction'], x+16, y+26, p, 11, 'semi', p.f_text, a)
    cx_, cy_ = r['close']
    for d in (-1, 1): c.move_to(cx_-4, cy_-4*d); c.line_to(cx_+4, cy_+4*d)
    stroke(c, p.f_text, 1.1, a)
    def flash(tt): return window(t, tt-0.1, tt, tt+0.45, tt+0.6) if tt else 0
    trig = cfg['trigger'] if t >= cfg.get('trig_switch', -1) else cfg.get('trigger0', cfg['trigger'])
    field(c, x+16, r['trigger']-12, w-32, p, None, trig, focus=flash(cfg.get('trig_hot')), chev=True, a=a)
    field(c, x+16, r['action']-12, w-32, p, None, cfg.get('action', 'Change to'), focus=flash(cfg.get('act_hot')), chev=True, a=a)
    ui(c, cfg['prop'], x+20, r['dest']+4, p, 11, 'med', p.f_muted, a, maxw=72)
    field(c, x+96, r['dest']-12, w-112, p, None, cfg['dest'], chev=True, a=a, focus=flash(cfg.get('dest_hot')))
    c.move_to(x, r['dest']+24.5); c.line_to(x+w, r['dest']+24.5); stroke(c, p.f_line, 1.0, a)
    ui(c, UI['animation'], x+16, r['anim']-22, p, 11, 'semi', p.f_text, a)
    ah = cfg.get('anim_hot'); smart = (ah is None) or t >= ah + 0.05
    field(c, x+16, r['anim']-6, w-32, p, None, cfg.get('anim', 'Smart animate') if smart else 'Instant', focus=flash(ah), chev=True, a=a)
    ea = a*(P(t, ah+0.05, ah+0.3, lin) if ah else 1.0)
    if ea > 0:
        fe = flash(cfg.get('ease_hot'))
        field(c, x+16, r['ease']-6, 124, p, None, cfg.get('ease', 'Ease out'), chev=True, a=ea, focus=fe)
        field(c, x+148, r['ease']-6, w-164, p, None, cfg.get('dur', '200ms'), a=ea, focus=fe)
        gx, gy, gw, gh = x+16, r['curve']+2, w-32, 34
        rrect(c, gx, gy, gw, gh, 5); fill(c, p.f_field, ea)
        c.move_to(gx+10, gy+gh-6); c.curve_to(gx+10+gw*0.1, gy+6, gx+gw*0.45, gy+6, gx+gw-10, gy+6); stroke(c, p.f_blue, 1.4, ea)
    c.restore()

# ================================================================= present mode
def present_rect(fw, fh, s): w, h = fw*s, fh*s; return WW/2 - w/2, 40 + (WH-40)/2 - h/2 + 4, w, h
def present(c, t, p, t0, title, fw, fh, s, draw_fn):
    a = P(t, t0+0.2, t0+0.5, lin)
    if a <= 0: return
    c.rectangle(0, 0, WW, WH); fill(c, p.f_present, a)
    c.rectangle(0, 0, WW, 40); fill(c, mixc(p.f_present, WHITE, 0.07), a)
    text(c, title, WW/2, 25, 11, 'semi', WHITE, a, align='c')
    rrect(c, WW-92, 9, 80, 22, 5); fill(c, p.f_blue, a); text(c, UI['share'], WW-52, 24, 10.5, 'semi', WHITE, a, align='c')
    x, y, w, h = present_rect(fw, fh, s)
    c.save(); u = P(t, t0+0.2, t0+0.6, eo); k = lerp(0.9, 1, u)
    c.translate(WW/2, y+h/2); c.scale(k, k); c.translate(-WW/2, -(y+h/2))
    c.translate(x, y); c.scale(s, s)
    c.rectangle(0, 0, fw, fh); fill(c, WHITE, a)
    draw_fn(c, a)
    c.restore()

# ================================================================= screen-space pieces
def keycap(c, keys, cx, cy, label, sub, t, t0, t1, p):
    a = P(t, t0, t0+0.15, lin)*(1-P(t, t1, t1+0.2, lin))
    if a <= 0: return
    u = back_ease(P(t, t0, t0+0.35, lin), 1.6); kw = [max(100, tw(k, 52, 'semi')+60) for k in keys]
    plus_w = 46; total = sum(kw) + plus_w*(len(keys)-1)
    c.save(); c.translate(cx, cy); s = lerp(0.7, 1, u); c.scale(s, s); c.translate(-cx, -cy)
    x = cx - total/2; y = cy - 56
    press = window(t, t0+0.25, t0+0.3, t0+0.42, t0+0.5)
    for i, k in enumerate(keys):
        dy = 6*press
        rrect(c, x, y+12, kw[i], 100, 22); fill(c, mixc(p.soft, p.accent, 0.35), a)
        _card(c, x, y+dy, kw[i], 100, 22, a, WHITE, mixc(p.soft, WHITE, 0.3))
        text(c, k, x+kw[i]/2, y+dy+68, 52, 'semi', p.ink, a, align='c')
        x += kw[i]
        if i < len(keys)-1: text(c, '+', x+plus_w/2, y+70, 44, 'bold', p.accent, a, align='c'); x += plus_w
    if label:
        lw = tw(label, 36, 'bold') + 48; rrect(c, cx-lw/2, cy+76, lw, 62, 31); fill(c, p.ink, a*0.94)
        text(c, label, cx, cy+119, 36, 'bold', WHITE, a, align='c')
    if sub:
        sw_ = tw(sub, 30, 'semi') + 36; rrect(c, cx-sw_/2, cy+150, sw_, 50, 25); fill(c, WHITE, a*0.92)
        text(c, sub, cx, cy+185, 30, 'semi', p.ink, a, align='c')
    c.restore()
def el_head(i):
    def draw(c, t, p):
        a0, a1 = KIT['hstart'][i], KIT['hend'][i]; END = KIT['end']
        a = (P(t, a0, a0+0.25, lin) if a0 > 0 else 1.0)*((1-P(t, a1-0.2, a1, lin)) if a1 < END else 1.0)
        if a <= 0: return
        chip = getattr(p, f'chip{i}'); title = getattr(p, f'title{i}')
        u = P(t, a0, a0+0.35, eo) if a0 > 0 else 1.0
        if chip.strip():
            cw = tw(chip, 26, 'bold', 0.06) + 36
            rrect(c, 80, 150 + 12*(1-u), cw, 46, 23); fill(c, p.accent, a*u)
            text(c, chip, 98, 182 + 12*(1-u), 26, 'bold', WHITE, a*u, track=0.06)
        size = 76
        while tw(title, size, 'xb', -0.02) > 640 and size > 50: size -= 2
        ktext(c, title, 80, 302, size, 'xb', p.ink, t, a0 + (0.08 if a0 > 0 else -1), a, align='l')
    return draw
PB_X, PB_Y, PB_W, PB_H = 60, 100, 960, 22
def el_progress(c, t, p):
    r = PB_H/2
    rrect(c, PB_X, PB_Y, PB_W, PB_H, r); fill(c, mixc(p.soft, WHITE, 0.45))
    f = clamp(t/KIT['end'])
    if f > 0:
        w = max(PB_H, PB_W*f); rrect(c, PB_X, PB_Y, w, PB_H, r); fill(c, p.accent)
        c.arc(PB_X + w - r, PB_Y + r, r*0.42, 0, 2*PI); fill(c, WHITE, 0.9)
FC_X, FC_W, FC_H = 80, 920, 206
def fc_y(): return SY + SH - 30 - FC_H
def fact_card(c, t, p, k, big, line, icon_fn):
    L, HEND = KIT['L'], KIT['hend']
    a = P(t, L[k]+0.1, L[k]+0.4, lin)*(1-P(t, HEND[k]-0.25, HEND[k], lin))
    if a <= 0: return
    u = P(t, L[k]+0.1, L[k]+0.55, back_ease); y = fc_y() + 60*(1-u)
    _card(c, FC_X, y, FC_W, FC_H, 40, a, p.accent, None, 1.2)
    c.arc(FC_X+118, y+FC_H/2, 78, 0, 2*PI); fill(c, WHITE, 0.14*a)
    icon_fn(c, FC_X+118, y+FC_H/2, a, t)
    size = 60
    while tw(big, size, 'xb') > FC_W - 280 and size > 40: size -= 2
    text(c, big, FC_X+232, y+96, size, 'xb', WHITE, a)
    text(c, line, FC_X+234, y+148, 30, 'semi', mixc(WHITE, p.soft, 0.25), a, maxw=FC_W-270)
def cursor_pos(t):
    k = KIT['cur']
    if t <= k[0][0]: return k[0][1], k[0][2]
    for a, b in zip(k, k[1:]):
        if a[0] <= t <= b[0]:
            u = P(t, a[0], b[0], eio); return lerp(a[1], b[1], u), lerp(a[2], b[2], u)
    return k[-1][1], k[-1][2]
def cursor_alpha(t):
    a = 1.0
    for t0, t1 in KIT['hide']: a = min(a, 1 - window(t, t0, t0+0.12, t1-0.12, t1))
    return a
def el_cursor(c, t, p):
    a = cursor_alpha(t)
    if a <= 0: return
    x, y = cursor_pos(t); X, Y = to_screen(t, x, y)
    for tc in KIT['clicks']:
        if tc <= t < tc + 0.4:
            u = P(t, tc, tc+0.4, eo); c.arc(X, Y, 14+30*u, 0, 2*PI); stroke(c, p.accent, 5*(1-u)+1, (1-u)*0.8*a)
    down = any(tc <= t < tc+0.12 for tc in KIT['clicks']) or any(t0 <= t < t1 for t0, t1 in KIT['presses'])
    s = 2.0*(0.9 if down else 1.0)
    c.save(); c.translate(X, Y); c.scale(s, s)
    c.move_to(0, 0); c.line_to(0, 17); c.line_to(4.2, 13.2); c.line_to(7, 19.6); c.line_to(9.6, 18.4); c.line_to(6.9, 12.2); c.line_to(12.3, 12.2); c.close_path()
    c.set_line_join(cairo.LINE_JOIN_ROUND); fillp(c, (0.06, 0.06, 0.07, 1), a); stroke(c, WHITE, 1.5, a)
    c.restore()
def cursor_box(t):
    X, Y = to_screen(t, *cursor_pos(t)); return (X-6, Y-6, 34, 46)
def draw_stickers_captions(c, t, p, caps):
    for k in p.stickers:
        x, y = k.pos if k.pos else (822, 240)
        draw_avatar(c, k.pose, x, y, k.size, t, k.start, k.end, mirror=k.mirror)
    draw_captions(c, t, caps, cx=CX, cy=1592, backing=p.capback, edge=p.soft, color=WHITE, highlight=p.soft)
