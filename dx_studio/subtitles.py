"""Plain-text SRT/WebVTT interchange with explicit scene/output timeline mapping."""
import html
import math
import re
from .timemap import scene_time, segments

STAMP = r'(?:\d{1,3}:)?\d{2}:\d{2}[.,]\d{3}'
TIMING = re.compile(r'^('+STAMP+r')\s*-->\s*('+STAMP+r')(?:\s+.*)?$')


def seconds(stamp):
    parts=stamp.replace(',','.').split(':')
    if float(parts[-1])>=60 or int(parts[-2])>=60: raise ValueError('Invalid subtitle timestamp: '+stamp)
    return sum(float(part)*60**index for index,part in enumerate(reversed(parts)))


def parse(text):
    if not isinstance(text,str) or len(text)>1000000: raise ValueError('Use a subtitle file smaller than 1 MB')
    text=text.lstrip('\ufeff').replace('\r\n','\n').replace('\r','\n').strip()
    cues=[]
    for block in re.split(r'\n\s*\n',text):
        lines=block.strip().splitlines()
        if not lines or lines[0].startswith(('WEBVTT','NOTE','STYLE','REGION')):continue
        index=next((i for i,line in enumerate(lines[:2]) if '-->' in line),None)
        if index is None: raise ValueError('Expected SRT or WebVTT cue timestamps')
        match=TIMING.match(lines[index].strip())
        if not match:raise ValueError('Invalid subtitle timing: '+lines[index])
        start,end=map(seconds,match.groups())
        if end<=start:raise ValueError('A subtitle must end after it starts')
        content=' '.join(lines[index+1:])
        content=html.unescape(re.sub(r'<[^>]*>','',content)).strip()
        if content:cues.append({'start':start,'end':end,'text':content,'hl':None})
        if len(cues)>2000:raise ValueError('Import at most 2,000 subtitle cues at a time')
    if not cues:raise ValueError('No subtitle cues found')
    return sorted(cues,key=lambda cue:cue['start'])


def prepare_import(text, project, timing='output'):
    if timing not in ('scene','output'):raise ValueError('Choose scene or output timing')
    cues=parse(text);out=[];clipped=skipped=0
    limit=project.duration if timing=='output' else project.base_duration
    for cue in cues:
        start,end=cue['start'],cue['end']
        if start>=limit:skipped+=1;continue
        if end>limit:end=limit;clipped+=1
        if timing=='output':start,end=scene_time(start,project.edits),scene_time(end,project.edits)
        if end-start<.001:skipped+=1;continue
        out.append(dict(cue,start=round(start,3),end=round(end,3)))
    warnings=[]
    if clipped:warnings.append(f'{clipped} cues shortened at the end of the project.')
    if skipped:warnings.append(f'{skipped} cues outside the project or wholly inside a held frame were skipped.')
    if not out:raise ValueError('No cues fit this project. Check the timing choice and video length.')
    return {'cues':out,'warnings':warnings}


def output_cues(project):
    out=[]
    spans=segments(project.base_duration,project.edits)
    for cap in sorted(project.values.get('__captions',[]),key=lambda cue:cue['start']):
        intervals=[]
        for o0,o1,s0,s1,kind in spans:
            if kind=='hold':
                if cap['start']<=s0<cap['end']:intervals.append((o0,o1))
            else:
                low,high=max(cap['start'],s0),min(cap['end'],s1)
                if high>low:intervals.append((o0+low-s0,min(o1,o0+high-s0)))
        merged=[]
        for start,end in intervals:
            start,end=round(start,3),round(end,3)
            if end<=start:continue
            if merged and start<=merged[-1][1]+.002:merged[-1]=(merged[-1][0],end)
            else:merged.append((start,end))
        out.extend({'start':a,'end':b,'text':cap['text']} for a,b in merged if cap.get('text','').strip())
    return sorted(out,key=lambda cue:cue['start'])


def timestamp(value,comma=False):
    total=max(0,round(value*1000));hours,total=divmod(total,3600000);minutes,total=divmod(total,60000);seconds,millis=divmod(total,1000)
    return f'{hours:02}:{minutes:02}:{seconds:02}{"," if comma else "."}{millis:03}'


def export(project,format='srt'):
    if format not in ('srt','vtt'):raise ValueError('Choose SRT or VTT')
    blocks=[]
    for index,cue in enumerate(output_cues(project),1):
        # Escape markup so literal caption text does not turn into subtitle styling.
        text=html.escape(cue['text'],quote=False).replace('-->','—>')
        timing=f'{timestamp(cue["start"],format=="srt")} --> {timestamp(cue["end"],format=="srt")}'
        blocks.append((str(index)+'\n' if format=='srt' else '')+timing+'\n'+text)
    return ('WEBVTT\n\n' if format=='vtt' else '')+'\n\n'.join(blocks)+'\n'


def findings(project):
    issues=[];previous_end=0
    for index,cue in enumerate(sorted(project.values.get('__captions',[]),key=lambda c:c['start'])):
        start,end=cue['start'],cue['end'];reasons=[];invalid=False
        if not all(isinstance(x,(int,float)) and math.isfinite(x) for x in (start,end)) or start<0 or end<=start or end>project.base_duration+.001:
            reasons.append('Timing must stay inside the scene and end after it starts');invalid=True
        elif len(cue.get('text','').strip())/(end-start)>20:reasons.append('Dense text: over 20 characters per second')
        if start<previous_end:reasons.append('Overlaps another caption')
        if cue.get('hl') and cue['hl'] not in cue.get('text',''):reasons.append('Highlight does not match the caption')
        if not cue.get('text','').strip():reasons.append('Empty caption')
        if reasons:issues.append({'severity':'error' if invalid else 'warning','kind':'caption','layers':[],
                                 'caption':index,'at':start,'message':f'Caption {index+1}: '+ '; '.join(reasons),
                                 'fix':'Review its text and timing in Captions.'})
        previous_end=max(previous_end,end)
    return issues
