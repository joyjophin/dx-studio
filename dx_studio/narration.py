"""Editable narration takes; imported sources stay inside the project."""
import math
import os
from pathlib import Path
import subprocess
import tempfile
import uuid

import soundfile as sf
from .paths import contained


def defaults(project):
    takes = []
    for index, line in enumerate(project.cfg.get('voice', [])):
        file = line.get('file', '')
        try: duration = sf.info(contained(project.path, file)).duration
        except (OSError, ValueError, RuntimeError): duration = line.get('dur') or max(.05, project.base_duration-line.get('start', 0))
        takes.append(dict(line, id=f'voice_{index}', name=line.get('name') or f'Take {index+1}',
                          start=line.get('start', 0), offset=0, duration=duration,
                          gain=line.get('gain', 1), duck=line.get('duck', 'normal'), muted=False))
    return takes


def validate(project, takes):
    if not isinstance(takes, list) or len(takes)>500: raise ValueError('Narration must contain at most 500 takes')
    ids = set()
    for take in takes:
        if not isinstance(take, dict): raise ValueError('Each narration take must be an object')
        identifier = take.get('id')
        if not isinstance(identifier, str) or not identifier or len(identifier)>100 or identifier in ids:
            raise ValueError('Narration takes need unique IDs')
        ids.add(identifier)
        if take.get('transcript') is not None:
            from .transcripts import validate as validate_transcript
            validate_transcript(take['transcript'])
        if not isinstance(take.get('file'), str): raise ValueError('Narration needs a source file path')
        contained(project.path, take['file'])
        if not isinstance(take.get('name'), str) or len(take['name'])>120: raise ValueError('Use a take name of at most 120 characters')
        for key, low, high in [('start',0,86400),('offset',0,86400),('duration',.001,86400),('gain',0,4)]:
            value = take.get(key)
            if isinstance(value,bool) or not isinstance(value,(int,float)) or not math.isfinite(value) or not low<=value<=high:
                raise ValueError(f'Narration {key} must be between {low} and {high}')
        if take.get('duck') not in ('normal','deep','none'): raise ValueError('Choose normal, deep or no music ducking')
        if not isinstance(take.get('muted'),bool): raise ValueError('Narration mute must be true or false')


def import_take(project, name, data, start=0):
    """Decode once to a unique 48 kHz WAV. No settings change until the user applies it."""
    if not data or len(data)>256*1024*1024: raise ValueError('Use an audio recording smaller than 256 MB')
    start = float(start)
    if not math.isfinite(start): raise ValueError('Choose a finite start time')
    assets = Path(contained(project.path, project.cfg.get('assets','assets')+'/narration'))
    assets.mkdir(parents=True,exist_ok=True)
    identifier = 'voice_'+uuid.uuid4().hex[:16]
    target = assets/(identifier+'.wav')
    with tempfile.TemporaryDirectory(prefix='.import-',dir=assets) as work:
        source = Path(work)/'recording'; source.write_bytes(data)
        decoded = Path(work)/'decoded.wav'
        try:
            subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-nostdin','-y','-i',str(source),
                            '-map','0:a:0','-t','86400','-vn','-ar','48000','-ac','1','-c:a','pcm_s24le',str(decoded)],
                           capture_output=True,check=True,timeout=120)
            info = sf.info(decoded)
            if not 0<info.duration<86400: raise ValueError('Choose a recording shorter than 24 hours')
            os.replace(decoded,target)
        except (subprocess.SubprocessError, RuntimeError) as error:
            raise ValueError('Could not read this recording. Choose a WAV, MP3, M4A, FLAC or other supported audio file.') from error
    return {'id':identifier,'name':Path(name).stem[:120] or 'Voice take',
            'file':target.relative_to(project.path).as_posix(),'start':max(0,min(start,project.base_duration-1/project.fps)),
            'offset':0,'duration':info.duration,'gain':1,'duck':'normal','muted':False}
