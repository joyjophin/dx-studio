"""dx_studio.stickers: PNG character stickers (pop-in, idle bob, pop-out) and recoloured GIF stickers."""
import math, os
from ._cairo import cairo
from PIL import Image, ImageFilter
from .core import *
from .draw import to_surface as _to_surface

ASSET_DIR = None   # set by the project loader to the project's asset folder
FREEZE_AFTER = None  # set to (duration - hold) so idle motion stops for the final hold

def set_asset_dir(path):
    global ASSET_DIR
    if ASSET_DIR != path:
        ASSET_DIR = path; _AV.clear(); _GIF.clear()

def sticker_path(name):
    """name without extension, looked up in <assets>/Avatars/"""
    from .paths import contained
    return contained(os.path.join(ASSET_DIR, 'Avatars'), name+'.png')

_AV = {}
def avatar_surf(name, size, mirror=False):
    """returns (sticker, shadow, w, h); size = target width for face/half, height for body"""
    size = int(round(size)); mirror = bool(mirror)
    key = (name, size, mirror)
    if key not in _AV:
        im = Image.open(sticker_path(name)).convert('RGBA')
        bb = im.getchannel('A').point(lambda v: 255 if v > 8 else 0).getbbox(); im = im.crop(bb)
        if name.startswith('body'): h = size; w = int(im.width*size/im.height)
        else: w = size; h = int(im.height*size/im.width)
        im = im.resize((w, h), Image.LANCZOS)
        if mirror: im = im.transpose(Image.FLIP_LEFT_RIGHT)
        pad = 40
        sh = Image.new('L', (w+2*pad, h+2*pad), 0); sh.paste(im.getchannel('A'), (pad, pad))
        sh = sh.filter(ImageFilter.GaussianBlur(14))
        shimg = Image.new('RGBA', sh.size, (0x21, 0x16, 0x38, 255)); shimg.putalpha(sh)
        _AV[key] = (_to_surface(im), _to_surface(shimg), w, h, pad)
    return _AV[key]

def draw_avatar(c, name, cx, cy, size, t, t_in, t_out, mirror=False, bob=True, a=1.0, rot=0.0):
    """pop-in (overshoot), gentle idle bob, pop-out. (cx, cy) = sticker centre"""
    if t < t_in or t > t_out+0.3: return
    surf, shs, w, h, pad = avatar_surf(name, size, mirror)
    u = P(t, t_in, t_in+0.45, lin); sc = lerp(0.55, 1.0, back_ease(u)); al = P(t, t_in, t_in+0.18, lin)
    v = P(t, t_out, t_out+0.25, ei); sc *= lerp(1, 0.7, v); al *= 1-v
    tb = min(t, FREEZE_AFTER) if FREEZE_AFTER else t
    dy = -6*math.sin((tb-t_in)*2*PI/2.8) if bob else 0
    al *= a
    if al <= 0.01: return
    c.save(); c.translate(cx, cy+dy); c.rotate(rot*(1-back_ease(u)) if rot else 0); c.scale(sc, sc)
    c.set_source_surface(shs, -w/2-pad, -h/2-pad+12); c.paint_with_alpha(0.16*al*1.6)
    c.set_source_surface(surf, -w/2, -h/2); c.get_source().set_filter(cairo.FILTER_GOOD); c.paint_with_alpha(al)
    c.restore()

def draw_walker(c, t, t0, t1, x0, x1, ybottom, height=340, mirror=False, name='walking'):
    if not (t0 <= t <= t1): return
    surf, shs, w, h, pad = avatar_surf(name, height, mirror)
    u = P(t, t0, t1, lin); x = lerp(x0, x1, u)
    step = abs(math.sin((t-t0)*PI*3.4)); y = ybottom - h/2 - 10*step
    c.save(); c.translate(x, y); c.rotate(0.03*math.sin((t-t0)*PI*3.4))
    c.set_source_surface(shs, -w/2-pad, -h/2-pad+12); c.paint_with_alpha(0.22)
    c.set_source_surface(surf, -w/2, -h/2); c.paint()
    c.restore()

_GIF = {}
def gif_frames(name, w, h, color=(0.47, 0.27, 0.92, 1)):
    """recolour a sticker GIF's strokes to a palette colour; returns [(surface, t_end)]"""
    key = (name, w, h, color)
    if key not in _GIF:
        im = Image.open(os.path.join(ASSET_DIR, 'GIFs', name+'.gif')); frames = []; tacc = 0
        for i in range(im.n_frames):
            im.seek(i); fr = im.convert('RGBA'); al = fr.getchannel('A')
            al = al.resize((w, h), Image.LANCZOS).filter(ImageFilter.GaussianBlur(0.8))
            col = Image.new('RGBA', (w, h), tuple(int(v*255) for v in color[:3])+(255,)); col.putalpha(al)
            tacc += (im.info.get('duration') or 40)/1000.0
            frames.append((_to_surface(col), tacc))
        _GIF[key] = frames
    return _GIF[key]

def draw_gif(c, name, x, y, w, h, t, t0, t1, speed=1.0, color=(0.47, 0.27, 0.92, 1), a=1.0):
    """plays once, holds the final frame, fades out at t1"""
    if t < t0 or t > t1+0.25: return
    frames = gif_frames(name, int(w), int(h), color)
    el = (t-t0)*speed; fr = frames[-1][0]
    for s_, te in frames:
        if el < te: fr = s_; break
    al = a*(1-P(t, t1, t1+0.25, lin))
    c.set_source_surface(fr, x, y); c.paint_with_alpha(al)