"""dx_studio command line.

    python3 -m dx_studio still  <project> 3.9 16.5 42.6   stills -> <project>/stills/
    python3 -m dx_studio build  <project>                 full MP4 (audio mix, master, frames, mux)
    python3 -m dx_studio audio  <project>                 just the audio mix (for previews)
    python3 -m dx_studio check  <project>                 validate project.json + schema + a test frame
    python3 -m dx_studio edit   <project>                 open the visual editor
    python3 -m dx_studio sounds                           list the built-in sound effects
"""
import os, subprocess, sys, time, tempfile
from pathlib import Path

def _project(path):
    from .project import Project
    return Project(path)

def cmd_still(path, times):
    from PIL import Image
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
    from .export_profiles import resolve
    opts=resolve(pr);n=max(1,int(round(opts['duration']*opts['fps'])))
    p = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'bgra', '-s', f'{pr.width}x{pr.height}',
                          '-r', str(opts['fps']), '-i', '-', '-vf', f"scale={opts['width']}:{opts['height']}", '-c:v', 'libx264', '-preset', 'medium', '-crf', '17', '-pix_fmt', 'yuv420p',
                          '-tune', 'animation', out], stdin=subprocess.PIPE)
    try:
        for i in range(n):
            s = pr.render(opts['start']+i/opts['fps']); p.stdin.write(bytes(s.get_data()))
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

def cmd_build(path, output=None, settings=None):
    from . import audio
    t0 = time.time(); pr = _project(path)
    from .paths import contained
    if settings:
        import json
        with open(contained(pr.path,settings),encoding='utf-8') as stream: snapshot=json.load(stream)
        if not isinstance(snapshot,dict):raise ValueError('Settings snapshot must be an object')
        pr.apply(pr.values_from_settings(snapshot))
    from .preflight import require_ready
    require_ready(pr)
    from .export_profiles import resolve as export_options,sidecar as caption_sidecar
    opts=export_options(pr)
    sidecar_text=caption_sidecar(pr,opts['start'],opts['end']) if opts['captions']=='sidecar' else None
    destination=contained(pr.path,output) if output else pr.output
    if not destination.lower().endswith('.mp4'):raise ValueError('Export to an .mp4 file')
    sources={pr.media.path(item) for item in pr.values.get('__media',[]) if item.get('file')}
    sources.update(contained(pr.path,line['file']) for line in pr.voices() if line.get('file'))
    music=pr.cfg.get('music')
    if isinstance(music,dict) and music.get('file'):sources.add(contained(pr.path,music['file']))
    if str(Path(destination).resolve()) in sources:raise ValueError('The export path is used by a source asset. Choose a separate MP4 path.')
    os.makedirs(os.path.dirname(destination),exist_ok=True)
    bdir = os.path.join(pr.path, '.build'); os.makedirs(bdir, exist_ok=True)
    # Each job owns its intermediates; a failed/cancelled build keeps the previous MP4.
    with tempfile.TemporaryDirectory(prefix='export-',dir=bdir) as work:
        print('mixing audio…', flush=True)
        raw=audio.build_mix(pr,os.path.join(work,'mix.wav'))
        if opts['start']>0 or opts['end']<pr.duration:
            clipped=os.path.join(work,'range.wav')
            subprocess.run(['ffmpeg','-v','error','-y','-ss',str(opts['start']),'-i',raw,'-t',str(opts['duration']),'-c:a','pcm_f32le',clipped],check=True);raw=clipped
        from .mix_controls import settings as mix_settings
        mx=mix_settings(pr)
        mastered=os.path.join(work,'master.wav')
        lufs,peak=audio.master(raw,mastered,mx.get('loudness',-14.0),mx.get('peak',-1.2))
        print(f'mastered: {lufs:.1f} LUFS, peak {peak:.1f} dBFS',flush=True)
        if opts['captions']!='burned':
            pr.values['__captions']=[];pr.apply(pr.values)
        vid=os.path.join(work,'video.mp4');render_video(pr,vid);print('muxing…',flush=True)
        final=os.path.join(work,'complete.mp4')
        subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-y','-i',vid,'-i',mastered,
                        '-map','0:v','-map','1:a','-c:v','copy','-c:a','aac','-b:a','256k','-ar','48000',
                        '-t',str(opts['duration']),'-movflags','+faststart',final],check=True)
        captions=None
        if sidecar_text is not None:
            captions=os.path.join(work,'captions.srt');Path(captions).write_text(sidecar_text,encoding='utf-8')
        from .export_validation import verify
        verify(final,opts)
        print('MP4 verified: dimensions, frame rate, duration and audio/video streams',flush=True)
        from .publishing import publish
        publish(final,destination,captions)
    print(f'Done -> {destination}  ({time.time()-t0:.0f} s)')

def cmd_check(path):
    pr = _project(path)
    from .preflight import require_ready
    report = require_ready(pr)
    for finding in report['findings']: print('warning:',finding['message'])
    kinds = {}
    for e in pr.schema: kinds[e['type']] = kinds.get(e['type'], 0)+1
    print(f"{pr.name}: {pr.width}x{pr.height} @ {pr.fps} fps, {pr.duration:.1f} s")
    print('parameters:', ', '.join(f'{v} {k}' for k, v in sorted(kinds.items())))
    print('captions:', len(pr.captions), '· voice lines:', len(pr.voices()), '· sound cues:', len(pr.cues()))
    t0 = time.time(); pr.render(pr.duration/2); print(f'test frame OK ({(time.time()-t0)*1000:.0f} ms)')

def cmd_sounds():
    from .audio import SOUND_HELP
    for k, v in SOUND_HELP.items(): print(f'{k:10s} {v}')

def main(argv=None):
    import argparse
    ap=argparse.ArgumentParser(prog='dx-studio', description='DX Studio: explainer videos that stay editable.')
    from . import __version__
    ap.add_argument('--version',action='version',version='DX Studio '+__version__)
    sub=ap.add_subparsers(dest='command',required=True)
    diagnostic=sub.add_parser('doctor',help='Check local dependencies');diagnostic.add_argument('--json',action='store_true',help='Print a shareable report without project contents or file paths')
    verify=sub.add_parser('verify-bundle',help='Check portable ZIP integrity without executing scenes');verify.add_argument('archive')
    sub.add_parser('sounds',help='List built-in sound effects')
    new=sub.add_parser('init',help='Create an editable project')
    new.add_argument('dest');new.add_argument('--format',choices=['9:16','16:9'],default='9:16')
    new.add_argument('--template',choices=['explainer','starter'],default='explainer');new.add_argument('--name');new.add_argument('--brand')
    from .composition import PRESENTER_PRESETS
    new.add_argument('--presenter',choices=list(PRESENTER_PRESETS),default='none',help='Reserve space for a talking head')
    for command in ['check','audio','build','edit','still','pack','captions']:
        p=sub.add_parser(command);p.add_argument('project', **({'nargs':'?'} if command=='edit' else {}))
        if command=='still': p.add_argument('times',type=float,nargs='*',default=[0.0])
        if command=='edit': p.add_argument('--port',type=int,default=8765);p.add_argument('--no-browser',action='store_true')
        if command=='build':p.add_argument('--output',help='Output path inside the project');p.add_argument('--settings',help='Settings snapshot inside the project')
        if command=='captions':p.add_argument('--format',choices=['srt','vtt'],default='srt');p.add_argument('--output')
        if command=='pack': p.add_argument('--output',required=True);p.add_argument('--include-history',action='store_true',help='Include older settings versions in a backup; review before sharing')
    args=ap.parse_args(argv)
    try:
        if args.command=='doctor':
            from .doctor import doctor
            return doctor(args.json)
        if args.command=='verify-bundle':
            from .bundle import verify
            result=verify(args.archive);print(f"Bundle verified: {result['files']} files · matching engine {result['engine_version']}");return 0
        if args.command=='init':
            from .scaffold import create
            print(create(args.dest,args.template,args.format,args.name,args.brand,args.presenter));return 0
        if args.command=='pack':
            from .bundle import pack
            print(pack(args.project,args.output,args.include_history));return 0
        if args.command=='captions':
            from .subtitles import export
            from pathlib import Path
            text=export(_project(args.project),args.format)
            if args.output:Path(args.output).write_text(text,encoding='utf-8')
            else:print(text,end='')
            return 0
        if args.command=='sounds': cmd_sounds();return 0
        if args.command=='edit':
            from .editor import serve
            serve(args.project,port=args.port,open_browser=not args.no_browser);return 0
        if args.command=='still': cmd_still(args.project,args.times or [0.0]);return 0
        if args.command=='build':cmd_build(args.project,args.output,args.settings);return 0
        {'check':cmd_check,'audio':cmd_audio}[args.command](args.project)
        return 0
    except (ValueError,OSError,RuntimeError,subprocess.SubprocessError) as exc:
        ap.exit(1,f'Error: {exc}\n')
