"""Tools for videos built on supplied footage (release videos, screen recordings). Measure, don't estimate.

    python3 scripts/footage.py frames VIDEO OUTDIR             # every frame as OUTDIR/0001.jpg (q2) for the scene to read
    python3 scripts/footage.py cuts VIDEO [--fps 12] [--thr 6]  # the source's own cuts / zooms (frame-difference peaks)
    python3 scripts/footage.py sheet VIDEO OUT.png [--start 0] [--end D] [--step 1] [--cols 3]
                                                                # gridded contact sheet (10 % grid, timestamps) to map the story
    python3 scripts/footage.py grid VIDEO T OUT.png [--box x0,y0,x1,y1] [--step 50] [--scale 1.0]
                                                                # one frame (or a crop) with a grid labelled in SOURCE px:
                                                                # read element coordinates for rings / camera keys from this
    python3 scripts/footage.py reveal VIDEO T0 DUR x0,y0,x1,y1 [--thr 225]
                                                                # times new bright glyphs appear in a box (typing / text reveals)

Look at `grid` output with the image viewer at full size: composite sheets are downscaled for display and are easy to
misread. Coordinates you read become constants in the scene (camera keys, ring rects, click points).
"""
import argparse, json, os, subprocess, sys
import numpy as np
from PIL import Image, ImageDraw

def probe(video):
    out = subprocess.run(['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_entries', 'stream=width,height,r_frame_rate:format=duration',
                          '-of', 'json', video], capture_output=True, text=True).stdout
    d = json.loads(out); st = d['streams'][0]; num, den = st['r_frame_rate'].split('/')
    return int(st['width']), int(st['height']), float(num)/float(den), float(d['format']['duration'])

def frame(video, t):
    tmp = f'/tmp/_ft_{os.getpid()}.png'
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-ss', str(t), '-i', video, '-frames:v', '1', tmp], check=True)
    im = Image.open(tmp).convert('RGB'); os.remove(tmp); return im

def cmd_frames(a):
    os.makedirs(a.outdir, exist_ok=True)
    subprocess.run(['ffmpeg', '-v', 'error', '-i', a.video, '-q:v', '2', os.path.join(a.outdir, '%04d.jpg')], check=True)
    w, h, fps, dur = probe(a.video); n = len([f for f in os.listdir(a.outdir) if f.endswith('.jpg')])
    print(f'{n} frames · {w}x{h} · {fps:.3f} fps · {dur:.2f}s  (frame i is at t = (i-1)/fps; file names start at 0001)')

def cmd_cuts(a):
    raw = f'/tmp/_cuts_{os.getpid()}.gray'
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', a.video, '-vf', f'fps={a.fps},scale=192:108,format=gray', '-f', 'rawvideo', raw], check=True)
    g = np.fromfile(raw, dtype=np.uint8).reshape(-1, 108, 192).astype(float); os.remove(raw)
    d = np.abs(np.diff(g, axis=0)).mean(axis=(1, 2))
    hits = [((i + 1)/a.fps, v) for i, v in enumerate(d) if v > a.thr]
    groups = []
    for t, v in hits:
        if groups and t - groups[-1][1] <= 1.5/a.fps: groups[-1][1] = t; groups[-1][2] = max(groups[-1][2], v)
        else: groups.append([t, t, v])
    for t0, t1, v in groups:
        kind = 'cut' if t1 - t0 < 0.1 else 'transition'
        print(f'{t0:7.2f}–{t1:6.2f}s  {kind:10s} peak {v:5.1f}')

def gridded(im, step_frac=0.1, label=None):
    d = ImageDraw.Draw(im); w, h = im.size
    for k in range(1, int(1/step_frac)):
        d.line([(w*k*step_frac, 0), (w*k*step_frac, h)], fill=(255, 0, 0), width=1); d.line([(0, h*k*step_frac), (w, h*k*step_frac)], fill=(255, 0, 0), width=1)
    if label: d.rectangle([0, 0, 52, 16], fill=(0, 0, 0)); d.text((4, 2), label, fill=(255, 255, 0))
    return im

def cmd_sheet(a):
    w, h, fps, dur = probe(a.video); end = a.end or dur
    ts = list(np.arange(a.start, end, a.step)); ims = []
    for t in ts:
        im = frame(a.video, t).resize((480, int(480*h/w))); ims.append(gridded(im, 0.1, f'{t:.2f}'))
    tw_, th_ = ims[0].size; rows = (len(ims) + a.cols - 1)//a.cols
    sheet = Image.new('RGB', (tw_*a.cols, th_*rows), 'white')
    for i, im in enumerate(ims): sheet.paste(im, ((i % a.cols)*tw_, (i//a.cols)*th_))
    sheet.save(a.out); print(f'{len(ims)} frames → {a.out} (grid lines every 10 % of the source frame)')

def cmd_grid(a):
    im = frame(a.video, a.t); W, H = im.size
    x0, y0, x1, y1 = map(int, a.box.split(',')) if a.box else (0, 0, W, H)
    im = im.crop((x0, y0, x1, y1)); d = ImageDraw.Draw(im)
    for x in range((x0//a.step + 1)*a.step, x1, a.step):
        major = x % (a.step*2) == 0
        d.line([(x - x0, 0), (x - x0, im.height)], fill=(255, 0, 0) if major else (255, 170, 170), width=1)
        if major: d.text((x - x0 + 3, 3), str(x), fill=(0, 0, 255))
    for y in range((y0//a.step + 1)*a.step, y1, a.step):
        major = y % (a.step*2) == 0
        d.line([(0, y - y0), (im.width, y - y0)], fill=(255, 0, 0) if major else (255, 170, 170), width=1)
        if major: d.text((3, y - y0 + 3), str(y), fill=(0, 0, 255))
    if a.scale != 1.0: im = im.resize((int(im.width*a.scale), int(im.height*a.scale)))
    im.save(a.out); print(f'{a.out}: source px {x0},{y0} → {x1},{y1}; labels every {a.step*2} px')

def cmd_reveal(a):
    x0, y0, x1, y1 = map(int, a.box.split(',')); w, h = x1 - x0, y1 - y0
    _, _, fps, _ = probe(a.video); raw = f'/tmp/_rv_{os.getpid()}.gray'
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-ss', str(a.t0), '-t', str(a.dur), '-i', a.video, '-vf', f'crop={w}:{h}:{x0}:{y0},format=gray',
                    '-f', 'rawvideo', raw], check=True)
    g = np.fromfile(raw, dtype=np.uint8).reshape(-1, h, w); os.remove(raw)
    cnt = (g > a.thr).sum(axis=(1, 2)).astype(float); d = np.diff(cnt)
    thr = max(150, np.percentile(d[d > 0], 70)) if (d > 0).any() else 150
    ev = []
    for i, v in enumerate(d):
        tt = round(a.t0 + (i + 1)/fps, 3)
        if v > thr and (not ev or tt - ev[-1] > 0.04): ev.append(tt)
    print(json.dumps(ev))

def main():
    ap = argparse.ArgumentParser(); sp = ap.add_subparsers(dest='cmd', required=True)
    p = sp.add_parser('frames'); p.add_argument('video'); p.add_argument('outdir'); p.set_defaults(fn=cmd_frames)
    p = sp.add_parser('cuts'); p.add_argument('video'); p.add_argument('--fps', type=float, default=12); p.add_argument('--thr', type=float, default=6); p.set_defaults(fn=cmd_cuts)
    p = sp.add_parser('sheet'); p.add_argument('video'); p.add_argument('out'); p.add_argument('--start', type=float, default=0.0)
    p.add_argument('--end', type=float, default=None); p.add_argument('--step', type=float, default=1.0); p.add_argument('--cols', type=int, default=3); p.set_defaults(fn=cmd_sheet)
    p = sp.add_parser('grid'); p.add_argument('video'); p.add_argument('t', type=float); p.add_argument('out'); p.add_argument('--box', default=None)
    p.add_argument('--step', type=int, default=50); p.add_argument('--scale', type=float, default=1.0); p.set_defaults(fn=cmd_grid)
    p = sp.add_parser('reveal'); p.add_argument('video'); p.add_argument('t0', type=float); p.add_argument('dur', type=float); p.add_argument('box')
    p.add_argument('--thr', type=float, default=225); p.set_defaults(fn=cmd_reveal)
    a = ap.parse_args(); a.fn(a)

if __name__ == '__main__':
    main()
