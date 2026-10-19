"""Reproduce MAKE IT CLICK: two editable projects, original score and gallery.

python scripts/render_showcase.py              # create projects + review stills
python scripts/render_showcase.py --build      # also render both 10 s masters
python scripts/render_showcase.py --gallery    # write README artwork / GIFs

No models, network requests, stock artwork or installed system fonts required.
"""
import argparse
import copy
import json
import math
import shutil
import subprocess
from pathlib import Path
import numpy as np
import soundfile as sf
from PIL import Image
from dx_studio.project import Project
from dx_studio.cli import cmd_build, cmd_still

ROOT=Path(__file__).resolve().parents[1]
SR=48000


def score(destination):
    """An original restrained electronic ident, D minor/add9, 120 BPM.

    Round bass, damped glass partials, filtered noise breaths and a final chord.
    The fixed seed, analytic envelopes and short delay give reproducible audio.
    No samples; the scene's separately linked cues supply the tactile clicks.
    """
    rng=np.random.default_rng(31);out=np.zeros(SR*10,dtype=np.float64)
    def put(at,signal,gain=1):
        k=int(at*SR);n=min(len(signal),len(out)-k)
        if n>0:out[k:k+n]+=signal[:n]*gain
    def note(midi,duration=1.2,kind='glass'):
        t=np.arange(int(duration*SR))/SR;f=440*2**((midi-69)/12)
        attack=1-np.exp(-t*(85 if kind=='glass' else 35))
        if kind=='glass':
            x=sum(g*np.sin(math.tau*f*r*t)*np.exp(-t*d) for r,g,d in [(1,1,3.8),(2,.25,6),(3.01,.09,9)])
        else:
            x=np.sin(math.tau*f*t)*np.exp(-t*2.8)+.15*np.sin(math.tau*f*2*t)*np.exp(-t*5)
        tail=np.minimum(1,(duration-t)/.06)
        return x*attack*tail
    for at,m in [(0,38),(1,38),(2.25,46),(3.25,41),(4.5,38),(5.5,38),(6.5,41),(7.5,38)]:put(at,note(m,1.25,'bass'),.19)
    for at,m,g in [(0,74,.10),(.5,81,.07),(1.25,77,.09),(2.25,74,.13),(2.75,81,.09),(3.25,86,.08),(3.75,81,.06),(4.5,77,.10),(5,74,.07),(5.5,81,.09),(6.25,77,.07),(6.75,86,.06)]:
        sig=note(m,1.35);put(at,sig,g);put(at+.19,sig,g*.17);put(at+.38,sig,g*.08)
    # A soft downbeat under every major change; no aggressive trailer hits.
    for at in (0,2.25,4.5,7.5):
        t=np.arange(int(.55*SR))/SR
        phase=math.tau*(48*t+50*(1-np.exp(-t*20))/20)
        put(at,np.sin(phase)*(1-np.exp(-t*200))*np.exp(-t*13),.25)
    for at in (1.95,4.15,7.2):
        t=np.arange(int(.4*SR))/SR;noise=rng.normal(0,1,len(t))
        smooth=np.convolve(noise,np.ones(17)/17,mode='same')
        env=np.sin(math.pi*t/.4)**2
        put(at,smooth*env,.055)
    for midi,g in [(50,.09),(62,.065),(69,.06),(74,.06),(76,.04),(81,.035)]:
        t=np.arange(int(2.5*SR))/SR;f=440*2**((midi-69)/12)
        put(7.5,np.sin(math.tau*f*t)*(1-np.exp(-t*12))*np.exp(-t*1.9),g)
    out*=np.minimum(1,np.arange(len(out))/480)
    out[-12000:]*=np.linspace(1,0,12000)**2
    destination.parent.mkdir(parents=True,exist_ok=True)
    sf.write(destination,out,SR,format='FLAC',subtype='PCM_24')


def create(output,aspect):
    name='landscape' if aspect=='16:9' else 'portrait'
    folder=output/name;folder.mkdir(parents=True,exist_ok=True)
    # Never overwrite an already edited project: keep reproducible sources in
    # separate folders, and require an explicit new output path for another cut.
    if (folder/'settings.json').exists() and json.loads((folder/'settings.json').read_text()):
        raise SystemExit(f'{folder} has saved edits. Choose --output elsewhere to preserve them.')
    shutil.copy2(ROOT/'examples/showcase/scene.py',folder/'scene.py')
    width,height=(1920,1080) if aspect=='16:9' else (1080,1920)
    cfg = {
        'format_version': 1,
        'name': f'Make it click / {aspect}',
        'description': 'An original ten-second DX Studio motion study. Every word, plane and curve remains editable.',
        'width': width, 'height': height, 'fps': 30,
        'duration': 10, 'final_hold': 1.1,
        'scene': 'scene.py', 'assets': 'assets',
        'output': f'dx-studio-{name}.mp4',
        'composition': {'presenter': 'none'},
        'safe_area': {
            'content': [96,64,1824,1016] if aspect=='16:9' else [130,170,950,1560],
            'captions': [200,900,1720,1016] if aspect=='16:9' else [130,1370,950,1550],
        },
        'chapters': [[0,2.25,'Complex.'], [2.25,4.5,'Clear.'],
                     [4.5,7.6,'Yours.'], [7.6,10,'DX Studio']],
        'voice': [],
        'music': {'file': 'assets/make-it-click.flac', 'level': .72, 'end_fade_at': 9.65},
        'mix': {'loudness': -14, 'peak': -1.2},
    }
    (folder/'project.json').write_text(json.dumps(cfg,indent=2)+'\n')
    score(folder/'assets/make-it-click.flac')
    (folder/'OPEN-ME.md').write_text('# Make it click\n\nOriginal 10-second editable motion study. Code, visuals and synthesised audio: MIT.\nNo external artwork or private assets. Bundled DX Sans typography: SIL OFL 1.1.\n\nInstall DX Studio, then run `python -m dx_studio edit .` from this folder.\nSelect Text for the words; Design for the palette; Layers for the sculpture, cards and tracks.\nThe score is a replaceable source asset. Save edits before packing a handoff.\n')
    return Project(folder)


def gallery(output,dest):
    dest.mkdir(parents=True,exist_ok=True)
    land=Project(output/'landscape');port=Project(output/'portrait')
    for name,project in [('landscape',land),('portrait',port)]:
        for label,t in [('complex',1.35),('clear',3.45),('yours',6.35),('signature',9)]:
            project.render(t).write_to_png(str(dest/f'showcase-{name}-{label}.png'))
        # A real motion loop, not a sequence of still slide changes.
        movie=output/name/f'dx-studio-{name}.mp4'
        if movie.exists():
            width=960 if name=='landscape' else 432
            subprocess.run(['ffmpeg','-y','-v','error','-ss','0.45','-i',str(movie),'-filter_complex',f'fps=15,scale={width}:-1:flags=lanczos,split[a][b];[a]palettegen=stats_mode=diff:reserve_transparent=0[p];[b][p]paletteuse=dither=bayer:bayer_scale=4:diff_mode=rectangle','-loop','0',str(dest/f'showcase-{name}.gif')],check=True)
    # Contact sheet is for review. Public format comparison uses uncropped masters.
    im=Image.new('RGB',(1800,1170),'#E9EAE3')
    wide=Image.open(dest/'showcase-landscape-yours.png').convert('RGB').resize((1280,720),Image.Resampling.LANCZOS)
    tall=Image.open(dest/'showcase-portrait-yours.png').convert('RGB').resize((486,864),Image.Resampling.LANCZOS)
    im.paste(wide,(0,224));im.paste(tall,(1314,145))
    # Draw labels with the same bundled type; do not depend on host fonts.
    from dx_studio import cairo,text,hexc
    surface=cairo.ImageSurface(cairo.FORMAT_ARGB32,1800,1170);c=cairo.Context(surface)
    from dx_studio.draw import to_surface
    c.set_source_surface(to_surface(im),0,0);c.paint()
    text(c,'ONE STORY. TWO COMPOSITIONS.',54,86,27,'semi',hexc('#111711'),track=.08)
    text(c,'1920 × 1080  /  16:9',54,1049,25,'med',hexc('#111711'))
    text(c,'1080 × 1920  /  9:16',1314,1049,25,'med',hexc('#111711'))
    text(c,'Native layouts. Editable source. Original sound.',54,1125,24,'reg',hexc('#455040'))
    surface.write_to_png(str(dest/'showcase-formats.png'))
    # A compact four-beat proof sheet supports the production notes.
    sheet=Image.new('RGB',(1920,1080),'#111711')
    for i,label in enumerate(('complex','clear','yours','signature')):
        frame=Image.open(dest/f'showcase-landscape-{label}.png').convert('RGB').resize((960,540),Image.Resampling.LANCZOS)
        sheet.paste(frame,((i%2)*960,(i//2)*540))
    sheet.save(dest/'showcase-storyboard.jpg',quality=94)
    # A social preview is another real source-parameter variant of the film.
    saved=copy.deepcopy(land.values)
    values=copy.deepcopy(saved);values['hook']='DX Studio';values['hook_body']='Make the story. Keep the layers.'
    land.apply(values)
    poster=output/'social-native.png';land.render(1.35).write_to_png(str(poster))
    image=Image.open(poster).convert('RGB').resize((1280,720),Image.Resampling.LANCZOS)
    image.crop((0,40,1280,680)).save(dest/'showcase-social.png')
    land.apply(saved)



def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--output',type=Path,default=ROOT/'outputs/showcase')
    ap.add_argument('--build',action='store_true')
    ap.add_argument('--gallery',action='store_true')
    ap.add_argument('--gallery-output',type=Path,default=ROOT/'docs/images')
    ap.add_argument('--stills',action='store_true',help='Render each beat and transition for review')
    args=ap.parse_args()
    if args.gallery and not args.build and not args.stills and (args.output/'landscape/project.json').exists():
        gallery(args.output,args.gallery_output);return
    for aspect in ('16:9','9:16'):
        project=create(args.output,aspect)
        if args.stills or not args.build:cmd_still(project.path,[.5,1.35,2.2,2.65,3.45,4.55,5.2,6.35,7.7,8.35,9])
        if args.build:cmd_build(project.path)
    if args.gallery:gallery(args.output,args.gallery_output)
    print(args.output)

if __name__=='__main__':main()
