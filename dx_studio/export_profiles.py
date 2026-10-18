"""Saved output profiles and output-clock ranges, independent of scene geometry."""
import math
from pathlib import Path
from .paths import contained


def resolve(project):
    opts=project.values.get('__export',{})
    profile=opts.get('profile','source');fps=opts.get('fps',0)
    if profile not in ('source','1080p','720p'):raise ValueError('Choose a source, 1080p or 720p export')
    if isinstance(fps,bool) or not isinstance(fps,int) or fps not in (0,12,24,25,30,60):raise ValueError('Choose a supported export frame rate')
    fps=fps or project.fps
    area=opts.get('range');a,b=area if isinstance(area,list) and len(area)==2 else (0,project.duration)
    if area is not None and (not isinstance(area,list) or len(area)!=2):raise ValueError('Export range needs start and end seconds')
    if any(isinstance(x,bool) or not isinstance(x,(int,float)) or not math.isfinite(x) for x in (a,b)) or not 0<=a<b<=project.duration+.000001 or b-a<1/fps-.000001:raise ValueError('Export range must fit the edited video and last at least one output frame')
    captions=opts.get('captions','burned')
    if captions not in ('burned','clean','sidecar'):raise ValueError('Choose burned, clean or sidecar captions')
    edge=project.width if project.width>=project.height else project.height
    target={'1080p':1920,'720p':1280}.get(profile,edge);scale=target/edge
    width=max(2,round(project.width*scale/2)*2);height=max(2,round(project.height*scale/2)*2)
    file=opts.get('file',project.cfg.get('output','output.mp4'))
    if not isinstance(file,str) or not file.lower().endswith('.mp4'):raise ValueError('Choose an MP4 filename inside the project')
    output=contained(project.path,file)
    return {'profile':profile,'width':width,'height':height,'fps':fps,'start':a,'end':b,'duration':b-a,'captions':captions,'output':output}


def sidecar(project,start,end):
    import html
    from .subtitles import output_cues,timestamp
    blocks=[]
    for cue in output_cues(project):
        a,b=max(start,cue['start']),min(end,cue['end'])
        if b<=a:continue
        text=html.escape(cue['text'],quote=False).replace('-->','—>')
        blocks.append(f'{len(blocks)+1}\n{timestamp(a-start,True)} --> {timestamp(b-start,True)}\n{text}')
    return '\n\n'.join(blocks)+'\n'
