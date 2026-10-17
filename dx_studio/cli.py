"""dx_studio command line.

    python3 -m dx_studio still  <project> 3.9 16.5 42.6   stills -> <project>/stills/
    python3 -m dx_studio build  <project>                 full MP4 (audio mix, master, frames, mux)
    python3 -m dx_studio audio  <project>                 just the audio mix (for previews)
    python3 -m dx_studio check  <project>                 validate project.json + schema + a test frame
    python3 -m dx_studio edit   <project>                 open the visual editor
    python3 -m dx_studio sounds                           list the built-in sound effects
"""
import os, subprocess, sys, time
from PIL import Image

def _project(path):
    from .project import Project
    return Project(path)

def cmd_still(path, times):
    pr = _project(path); os.makedirs(os.path.join(pr.path, 'stills'), exist_ok=True)
    files = []
    for t in times:
        f = os.path.join(pr.path, 'stills', f'f_{t:05.2f}.png'); pr.render(t).write_to_png(f); files.append(f)
    if len(files) > 1:
        ims = [Image.open(f) for f in files]; w = 360; h = int(w*pr.height/pr.width)
        sheet = Image.new('RGB', (w*len(ims), h), 'white')
        for i, im in enumerate(ims): sheet.paste(im.convert('RGB').resize((w, h)), (i*w, 0))
        sheet.save(os.path.join(pr.path, 'stills', 'sheet.png')); files.append(os.path.join(pr.path, 'stills', 'sheet.png'))
    print('\n'.join(files))

def render_video(pr, out, progress=None):
    n = int(round(pr.duration*pr.fps))
    p = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'bgra', '-s', f'{pr.width}x{pr.height}',
                          '-r', str(pr.fps), '-i', '-', '-c:v', 'libx264', '-preset', 'medium', '-crf', '17', '-pix_fmt', 'yuv420p',
                          '-tune', 'animation', out], stdin=subprocess.PIPE)
    try:
        for i in range(n):
            s = pr.render(i/pr.fps); p.stdin.write(bytes(s.get_data()))
            if i % 150 == 0:
                print(f'frame {i}', flush=True)
                if progress: progress(i/n)
    except BaseException:
        p.stdin.close(); p.terminate(); p.wait(); raise
    p.stdin.close(); p.wait()
    if p.returncode: raise RuntimeError('ffmpeg failed while encoding frames')

def cmd_audio(path, pr=None):
    from . import audio
    pr = pr or _project(path)
    raw = os.path.join(pr.path, '.build', 'mix_raw.wav'); os.makedirs(os.path.dirname(raw), exist_ok=True)
    audio.build_mix(pr, raw); print('audio mix ->', raw); return raw

def cmd_build(path):
    from . import audio
    t0 = time.time(); pr = _project(path)
    from .preflight import require_ready
    require_ready(pr)
    bdir = os.path.join(pr.path, '.build'); os.makedirs(bdir, exist_ok=True)
    print('mixing audio…', flush=True)
    raw = cmd_audio(path, pr)
    mx = pr.cfg.get('mix', {})
    lufs, peak = audio.master(raw, os.path.join(bdir, 'master.wav'), mx.get('loudness', -14.0), mx.get('peak', -1.2))
    print(f'mastered: {lufs:.1f} LUFS, peak {peak:.1f} dBFS', flush=True)
    vid = os.path.join(bdir, 'video.mp4'); render_video(pr, vid); print('done', flush=True)
    subprocess.run(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-y', '-i', vid, '-i', os.path.join(bdir, 'master.wav'),
                    '-map', '0:v', '-map', '1:a', '-c:v', 'copy', '-c:a', 'aac', '-b:a', '256k', '-ar', '48000',
                    '-t', str(pr.duration), '-movflags', '+faststart', pr.output], check=True)
    print(f'Done -> {pr.output}  ({time.time()-t0:.0f} s)')

def cmd_check(path):
    pr = _project(path)
    from .preflight import require_ready
    report = require_ready(pr)
    for finding in report['findings']: print('warning:',finding['message'])
    kinds = {}
    for e in pr.schema: kinds[e['type']] = kinds.get(e['type'], 0)+1
    print(f"{pr.name}: {pr.width}x{pr.height} @ {pr.fps} fps, {pr.duration:.1f} s")
    print('parameters:', ', '.join(f'{v} {k}' for k, v in sorted(kinds.items())))
    print('captions:', len(pr.captions), '· voice lines:', len(pr.cfg.get('voice', [])), '· sound cues:', len(pr.cues()))
    t0 = time.time(); pr.render(pr.duration/2); print(f'test frame OK ({(time.time()-t0)*1000:.0f} ms)')

def cmd_sounds():
    from .audio import SOUND_HELP
    for k, v in SOUND_HELP.items(): print(f'{k:10s} {v}')

def main(argv=None):
    import argparse
    ap=argparse.ArgumentParser(prog='dx-studio', description='DX Studio: explainer videos that stay editable.')
    ap.add_argument('--version',action='version',version='DX Studio 0.1.0')
    sub=ap.add_subparsers(dest='command',required=True)
    sub.add_parser('doctor',help='Check local dependencies')
    sub.add_parser('sounds',help='List built-in sound effects')
    new=sub.add_parser('init',help='Create an editable project')
    new.add_argument('dest');new.add_argument('--format',choices=['9:16','16:9'],default='9:16')
    new.add_argument('--template',choices=['explainer','starter'],default='explainer');new.add_argument('--name');new.add_argument('--brand')
    from .composition import PRESENTER_PRESETS
    new.add_argument('--presenter',choices=list(PRESENTER_PRESETS),default='none',help='Reserve space for a talking head')
    for command in ['check','audio','build','edit','still','pack']:
        p=sub.add_parser(command);p.add_argument('project', **({'nargs':'?'} if command=='edit' else {}))
        if command=='still': p.add_argument('times',type=float,nargs='*',default=[0.0])
        if command=='edit': p.add_argument('--port',type=int,default=8765);p.add_argument('--no-browser',action='store_true')
        if command=='pack': p.add_argument('--output',required=True)
    args=ap.parse_args(argv)
    try:
        if args.command=='doctor':
            from .doctor import doctor
            return doctor()
        if args.command=='init':
            from .scaffold import create
            print(create(args.dest,args.template,args.format,args.name,args.brand,args.presenter));return 0
        if args.command=='pack':
            from .bundle import pack
            print(pack(args.project,args.output));return 0
        if args.command=='sounds': cmd_sounds();return 0
        if args.command=='edit':
            from .editor import serve
            serve(args.project,port=args.port,open_browser=not args.no_browser);return 0
        if args.command=='still': cmd_still(args.project,args.times or [0.0]);return 0
        {'check':cmd_check,'audio':cmd_audio,'build':cmd_build}[args.command](args.project)
        return 0
    except (ValueError,FileNotFoundError,RuntimeError) as exc:
        ap.exit(1,f'Error: {exc}\n')
