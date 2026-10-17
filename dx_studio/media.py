"""dx_studio.media: user-added PNG / JPG / WEBP / GIF / MP4 overlays. Each item becomes a real layer
(select, move, scale, rotate, fade, keyframe, retime, entrance/exit) drawn above the scene.

Items live in settings under "__media":
    {"id": "media_ab12", "name": "logo.png", "file": "Media/logo.png", "kind": "image" | "gif" | "video",
     "box": [x, y, w, h], "t0": 3.0, "dur": 3.0, "loop": true, "muted": false, "volume": 1.0, "radius": 0}
File paths are relative to the project's assets folder. Videos are decoded once into .build/media/<id>/.
"""
import os, json, subprocess, shutil, uuid, hashlib, io
from pathlib import Path
from collections import OrderedDict
from ._cairo import cairo
from PIL import Image
from .draw import to_surface, rrect, fill, stroke, shadow
from .core import hexc, clamp, P, eo, lerp, back_ease
from .text import tw, text, ktext
import math
from .layers import Layer
from .paths import contained

IMAGE_EXT = {'.png', '.jpg', '.jpeg', '.webp'}
GIF_EXT = {'.gif'}
VIDEO_EXT = {'.mp4', '.mov', '.m4v', '.webm'}
ALL_EXT = IMAGE_EXT | GIF_EXT | VIDEO_EXT

def kind_of(name):
    e = os.path.splitext(name)[1].lower()
    return 'image' if e in IMAGE_EXT else 'gif' if e in GIF_EXT else 'video' if e in VIDEO_EXT else None

class MediaLibrary:
    def __init__(self, project):
        self.pr = project
        self.assets = os.path.join(project.path, project.cfg.get('assets', 'assets'))
        self.cache_dir = os.path.join(project.path, '.build', 'media')
        self._img, self._gif, self._frames = {}, {}, OrderedDict()
        self._info, self._thumbnails = {}, {}

    # ---- import
    def import_file(self, filename, data, t, center=None):
        kind = kind_of(filename)
        if not kind: raise ValueError(f'Unsupported file type: {filename}. Use PNG, JPG, WEBP, GIF or MP4.')
        os.makedirs(os.path.join(self.assets, 'Media'), exist_ok=True)
        base, ext = os.path.splitext(os.path.basename(filename)); name = base+ext; k = 1
        while os.path.exists(os.path.join(self.assets, 'Media', name)): k += 1; name = f'{base}-{k}{ext}'
        path = contained(self.assets, 'Media/'+name)
        open(path, 'wb').write(data)
        try:
            return self.item_for('Media/'+name, t, center)
        except Exception:
            os.unlink(path)
            raise

    def inspect(self, file):
        path = contained(self.assets, file)
        kind = kind_of(file)
        if not kind: raise ValueError('Use PNG, JPG, WEBP, GIF, MP4, MOV, M4V or WEBM')
        stat = os.stat(path)
        if not os.path.isfile(path): raise ValueError('Choose a media file')
        key = (path, stat.st_size, stat.st_mtime_ns)
        if key in self._info: return dict(self._info[key], file=str(Path(file).as_posix()), name=Path(file).name)
        if kind == 'video':
            w, h, duration, has_audio = probe_video(path)
        else:
            with Image.open(path) as im:
                w, h = im.size
                duration = None
                if kind == 'gif':
                    duration = 0
                    for i in range(getattr(im, 'n_frames', 1)):
                        im.seek(i); duration += (im.info.get('duration') or 100)/1000
                else: im.verify()
            has_audio = False
        result = {'file':str(Path(file).as_posix()), 'name':Path(file).name, 'kind':kind,
                  'width':w, 'height':h, 'duration':duration, 'has_audio':has_audio, 'bytes':stat.st_size}
        self._info[key] = result
        return dict(result)

    def item_for(self, file, t, center=None):
        info = self.inspect(file)
        W, H, D = self.pr.width, self.pr.height, self.pr.base_duration
        w, h, kind = info['width'], info['height'], info['kind']
        area = self.pr.layout.get('content',[0,0,W,H])
        aw,ah=area[2]-area[0],area[3]-area[1]
        scale = min(1.0, (aw*.8)/w, (ah*.5)/h)
        bw, bh = max(1,round(w*scale)), max(1,round(h*scale))
        cx, cy = center if center else ((area[0]+area[2])/2,(area[1]+area[3])/2)
        t0 = max(0.0, min(D-.5, float(t)))
        duration = info['duration'] or 3.0
        return {'id':'media_'+uuid.uuid4().hex[:10], 'name':info['name'], 'file':info['file'], 'kind':kind,
                'box':[round(cx-bw/2),round(cy-bh/2),bw,bh], 't0':round(t0,2),
                'dur':round(min(duration,D-t0),2), 'loop':kind!='video', 'muted':False,
                'volume':1.0, 'radius':28 if kind=='video' else 0, 'has_audio':info['has_audio']}

    def catalog(self, include_unused=True):
        used = {}
        for item in self.pr.values.get('__media', []):
            if item.get('file'): used.setdefault(item['file'], []).append(item['id'])
        files = set(used)
        root = Path(self.assets)
        if include_unused and root.exists():
            for path in root.rglob('*'):
                if len(files)>=1000: break
                if path.is_file() and kind_of(path.name): files.add(path.relative_to(root).as_posix())
        records = []
        for file in sorted(files):
            record = {'file':file,'name':Path(file).name,'kind':kind_of(file),'used_by':used.get(file,[])}
            try: record.update(self.inspect(file), status='ready')
            except FileNotFoundError: record.update(status='missing',error='File is missing. Relink or replace it.')
            except (OSError,ValueError,subprocess.SubprocessError) as error: record.update(status='unreadable',error=str(error))
            records.append(record)
        return records

    def thumbnail(self, file):
        info = self.inspect(file)
        key = self.source_key({'file':file})
        if key in self._thumbnails: return self._thumbnails[key]
        if info['kind']=='video':
            result = subprocess.run(['ffmpeg','-v','error','-i',contained(self.assets,file),'-frames:v','1',
                                     '-vf','scale=320:-2','-f','image2pipe','-vcodec','mjpeg','-'],capture_output=True,check=True)
            self._thumbnails[key] = result.stdout
            return result.stdout
        with Image.open(contained(self.assets,file)) as im:
            im=im.convert('RGB'); im.thumbnail((320,180)); output=io.BytesIO(); im.save(output,'JPEG'); self._thumbnails[key]=output.getvalue(); return output.getvalue()

    def source_key(self, item):
        path = self.path(item); stat=os.stat(path)
        return path, stat.st_size, stat.st_mtime_ns

    # ---- decoding / caching
    def path(self, item): return contained(self.assets, item['file'])
    def image(self, item):
        p = self.source_key(item)
        if p not in self._img:
            im = Image.open(p[0]).convert('RGBA'); im.thumbnail((2000, 2000)); self._img[p] = (to_surface(im), im.width, im.height)
        return self._img[p]
    def gif_frames(self, item):
        p = self.source_key(item)
        if p not in self._gif:
            im = Image.open(p[0]); frames = []; acc = 0.0
            for i in range(getattr(im, 'n_frames', 1)):
                im.seek(i); fr = im.convert('RGBA'); fr.thumbnail((1400, 1400))
                acc += (im.info.get('duration') or 100)/1000; frames.append((to_surface(fr), acc, fr.width, fr.height))
            self._gif[p] = frames
        return self._gif[p]
    def cache_key(self, item): return hashlib.sha256(repr((self.source_key(item),self.pr.fps)).encode()).hexdigest()[:24]
    def frames_dir(self, item): return contained(self.cache_dir, self.cache_key(item))
    def decode_video(self, item):
        d = self.frames_dir(item)
        if os.path.isfile(os.path.join(d,'.complete')): return d
        os.makedirs(d, exist_ok=True)
        for stale in Path(d).glob('f_*.jpg'): stale.unlink()
        subprocess.run(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-y', '-i', self.path(item),
                        '-vf', f"fps={self.pr.fps},scale='min(1080,iw)':-2", '-q:v', '3', os.path.join(d, 'f_%05d.jpg')], check=True)
        Path(d,'.complete').touch()
        return d
    def video_frame(self, item, lt):
        d = self.decode_video(item)
        n = len([f for f in os.listdir(d) if f.endswith('.jpg')]) if (d, 'n') not in self._frames else self._frames[(d, 'n')]
        self._frames[(d, 'n')] = n
        if n == 0: return None
        i = int(lt*self.pr.fps)
        i = i % n if item.get('loop') else min(max(i, 0), n-1)
        key = (d, i)
        if key not in self._frames:
            im = Image.open(os.path.join(d, f'f_{i+1:05d}.jpg')).convert('RGBA')
            self._frames[key] = (to_surface(im), im.width, im.height)
            while len(self._frames) > 90: self._frames.popitem(last=False)
        else: self._frames.move_to_end(key)
        return self._frames[key]
    def audio_wav(self, item):
        """the video's own audio as a mono 48 kHz wav (cached); None if it has no audio"""
        if item.get('kind') != 'video' or not item.get('has_audio'): return None
        out = contained(self.cache_dir, self.cache_key(item)+'.wav')
        if not os.path.exists(out):
            os.makedirs(self.cache_dir, exist_ok=True)
            r = subprocess.run(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-y', '-i', self.path(item), '-vn', '-ac', '1', '-ar', '48000', out])
            if r.returncode: return None
        return out

    # ---- drawing
    def draw(self, c, item, lt):
        try: self._draw(c, item, lt)
        except (OSError, ValueError, subprocess.SubprocessError):
            x,y,w,h=item['box']
            c.save(); rrect(c,x,y,w,h,12); fill(c,hexc('#FBE8EF'))
            text(c,'Media unavailable',x+w/2,y+h/2,min(28,max(10,w/12)),'bold',hexc('#97385B'),1,'c'); c.restore()

    def _draw(self, c, item, lt):
        x, y, w, h = item['box']
        k = item['kind']
        if k == 'image': surf, iw, ih = self.image(item)
        elif k == 'gif':
            frames = self.gif_frames(item); total = frames[-1][1]
            tt = (lt % total) if item.get('loop', True) else min(lt, total-1e-3)
            surf, iw, ih = next(((s, fw, fh) for s, te, fw, fh in frames if tt < te), (frames[-1][0], frames[-1][2], frames[-1][3]))
        else:
            fr = self.video_frame(item, lt)
            if fr is None: return
            surf, iw, ih = fr
        c.save()
        r = float(item.get('radius', 0) or 0)
        if r > 0: rrect(c, x, y, w, h, r); c.clip()
        c.translate(x, y); c.scale(w/iw, h/ih)
        c.set_source_surface(surf, 0, 0); c.get_source().set_filter(cairo.FILTER_GOOD); c.paint()
        c.restore()

    def layers_for(self, items):
        out = []
        for it in items:
            k = it['kind']
            if k == 'text':
                def draw_it(c, t, p, it=it): draw_text_el(c, it, t - it['t0'])
                box = (lambda t, it=it: text_box(it)); label = 'Text: ' + (it.get('text', '').split('\n')[0][:26] or '…'); grp = 'Text & shapes'; hlp = 'Text element'
            elif k == 'shape':
                def draw_it(c, t, p, it=it): draw_shape_el(c, it, t - it['t0'])
                box = tuple(it['box']); label = 'Shape: ' + it.get('shape', 'rect'); grp = 'Text & shapes'; hlp = 'Shape element'
            else:
                def draw_it(c, t, p, it=it): self.draw(c, it, t - it['t0'])
                box = tuple(it['box']); label = it.get('name', it['id']); grp = 'Media'; hlp = f"{k.upper()} · {it['file']}"
            out.append(Layer(it['id'], label, draw_it, box, it['t0'], it['t0']+it['dur'], grp, help=hlp))
        return out

def probe_video(path):
    r = subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'stream=codec_type,width,height:format=duration', '-of', 'json', path],
                       capture_output=True, text=True)
    info = json.loads(r.stdout or '{}'); w = h = None; has_audio = False
    for s in info.get('streams', []):
        if s.get('codec_type') == 'video' and w is None: w, h = s.get('width'), s.get('height')
        if s.get('codec_type') == 'audio': has_audio = True
    dur = float(info.get('format', {}).get('duration', 3.0) or 3.0)
    if not w: raise ValueError('Could not read that video file.')
    return w, h, dur, has_audio


# ------------------------------------------------------------------ text elements
TEXT_DEFAULTS = {'text': 'New text', 'weight': 'xb', 'size': 72, 'color': '#211638', 'align': 'c', 'line_height': 1.15,
                 'bg': 'none', 'bg_color': '#FFFFFF', 'pad': 24, 'radius': 24, 'anim': 'rise', 'anim_dur': 0.8, 'track': -0.02}
def _wrap(it):
    size = float(it.get('size', 72)); w = it.get('weight', 'xb'); tr = float(it.get('track', -0.02)) if w in ('xb', 'xb_t', 'bold') else 0.0
    maxw = max(40, it['box'][2] - 2*float(it.get('pad', 24) if it.get('bg', 'none') != 'none' else 0))
    lines = []
    for para in str(it.get('text', '')).split('\n'):
        words = para.split(' '); cur = ''
        for wd in words:
            trial = (cur + ' ' + wd) if cur else wd
            if cur and tw(trial, size, w, tr) > maxw: lines.append(cur); cur = wd
            else: cur = trial
        lines.append(cur)
    return lines, size, w, tr
def text_box(it):
    lines, size, w, tr = _wrap(it)
    pad = float(it.get('pad', 24)) if it.get('bg', 'none') != 'none' else 0
    h = len(lines)*size*float(it.get('line_height', 1.15)) + 2*pad
    return (it['box'][0], it['box'][1], it['box'][2], h)
def draw_text_el(c, it, ts):
    lines, size, w, tr = _wrap(it)
    x, y, bw, bh = text_box(it); col = hexc(it.get('color', '#211638'))
    bg = it.get('bg', 'none'); pad = float(it.get('pad', 24)) if bg != 'none' else 0
    lh = size*float(it.get('line_height', 1.15)); align = it.get('align', 'c')
    anim = it.get('anim', 'none'); ad = max(0.05, float(it.get('anim_dur', 0.8)))
    widths = [tw(l, size, w, tr) for l in lines]
    if bg != 'none':
        if bg == 'pill':
            ww = max(widths or [0]) + 2*pad
            bx = x if align == 'l' else x + bw - ww if align == 'r' else x + (bw-ww)/2
            rrect(c, bx, y, ww, bh, min(bh/2, float(it.get('radius', 24)) if len(lines) > 1 else bh/2))
        else:
            shadow(c, x, y, bw, bh, float(it.get('radius', 24)), 1.0, 0.8)
            rrect(c, x, y, bw, bh, float(it.get('radius', 24)))
        fill(c, hexc(it.get('bg_color', '#FFFFFF')), P(ts, 0, 0.25) if anim != 'none' else 1.0)
    ax = x + pad if align == 'l' else x + bw - pad if align == 'r' else x + bw/2
    total = sum(len(l) for l in lines) or 1; nwords = sum(len(l.split()) for l in lines) or 1; seen_c = seen_w = 0
    for i, line in enumerate(lines):
        by = y + pad + i*lh + lh/2 + size*0.36
        if anim == 'rise':
            ktext(c, line, ax, by, size, w, col, ts, i*0.12, 1.0, align=align, track=tr, stagger=min(0.03, ad/max(1, len(line))), dur=0.4, rise=size*0.35)
        elif anim == 'type':
            n = int(round(clamp(ts/ad)*total)) - seen_c
            if n > 0: text(c, line[:n], ax - (widths[i] if align == 'r' else widths[i]/2 if align == 'c' else 0), by, size, w, col, 1.0, 'l', tr)
        elif anim == 'words':
            words = line.split(' '); xx = ax - (widths[i] if align == 'r' else widths[i]/2 if align == 'c' else 0); sp = tw(' ', size, w, tr)
            for j, wd in enumerate(words):
                k = seen_w + j; t0 = k*ad/nwords; u = P(ts, t0, t0+0.3)
                if u > 0: text(c, wd, xx, by + (1-u)*size*0.25, size, w, col, u, 'l', tr)
                xx += tw(wd, size, w, tr) + sp
        else:
            text(c, line, ax, by, size, w, col, 1.0, align, tr)
        seen_c += len(line); seen_w += len(line.split())

# ------------------------------------------------------------------ shape elements
SHAPE_DEFAULTS = {'shape': 'rect', 'fill': '#FFFFFF', 'stroke': '#DDD3EC', 'stroke_w': 3, 'radius': 28, 'shadow': True, 'draw_on': 0.6}
def draw_shape_el(c, it, ts):
    x, y, w, h = it['box']; kind = it.get('shape', 'rect')
    fc = it.get('fill'); sc = it.get('stroke'); sw = float(it.get('stroke_w', 3))
    don = float(it.get('draw_on', 0) or 0); u = clamp(ts/don) if don > 0 else 1.0; u = eo(u) if don > 0 else 1.0
    if kind in ('rect', 'circle'):
        if it.get('shadow') and fc: shadow(c, x, y, w, h, min(w, h)/2 if kind == 'circle' else float(it.get('radius', 28)), 1.0, 1.0)
        if kind == 'rect': rrect(c, x, y, w, h, float(it.get('radius', 28)))
        else:
            c.save(); c.translate(x+w/2, y+h/2); c.scale(w/2, h/2); c.arc(0, 0, 1, 0, 2*math.pi); c.restore()
        if fc: c.set_source_rgba(*hexc(fc)); c.fill_preserve() if sc else c.fill()
        if sc and sw > 0: c.set_source_rgba(*hexc(sc)); c.set_line_width(sw); c.stroke()
        c.new_path(); return
    if kind == 'marker':
        col = hexc(fc or '#BCA4F5'); rrect(c, x, y, max(1, w*u), h, min(h/2, float(it.get('radius', 28)))); c.set_source_rgba(col[0], col[1], col[2], 0.45); c.fill(); return
    # line / arrow along the box's horizontal centre (rotate the layer to angle it)
    col = hexc(sc or '#7846EB'); y0 = y + h/2; x1 = x + w*u
    c.set_line_cap(cairo.LINE_CAP_ROUND); c.set_line_join(cairo.LINE_JOIN_ROUND)
    c.move_to(x, y0); c.line_to(x1, y0); c.set_source_rgba(*col); c.set_line_width(max(1, sw)); c.stroke()
    if kind == 'arrow' and u > 0.6:
        hs = max(16, sw*3.2)*clamp((u-0.6)/0.4)
        c.move_to(x1-hs, y0-hs*0.8); c.line_to(x1, y0); c.line_to(x1-hs, y0+hs*0.8); c.stroke()
