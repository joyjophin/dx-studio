"""Bounded-memory waveform peaks for the editor's final-timeline preview mix."""
import hashlib
import math
from pathlib import Path
import json
import numpy as np
import soundfile as sf
from .history import atomic_json


def peaks(path, bins=1800):
    bins=max(16,min(4096,int(bins)))
    with sf.SoundFile(path) as source:
        frames,rate=source.frames,source.samplerate
        step=max(1,math.ceil(frames/bins)); values=[]
        for _ in range(math.ceil(frames/step)):
            data=source.read(step,dtype='float32',always_2d=True)
            values.append(round(float(np.max(np.abs(np.nan_to_num(data,nan=0,posinf=0,neginf=0)))) if data.size else 0,4))
    return {'duration':frames/rate,'sample_rate':rate,'peaks':values,'step':step/rate}


def cached_peaks(path):
    path=Path(path)
    if not path.is_file(): return {'ready':False,'message':'Preview audio is not ready yet.'}
    stat=path.stat();key=hashlib.sha256(f'{path.resolve()}:{stat.st_size}:{stat.st_mtime_ns}:v1'.encode()).hexdigest()[:24]
    cache=path.parent/'waveforms'/(key+'.json')
    try:
        if cache.is_file(): return dict(json.loads(cache.read_text()),ready=True,key=key)
    except (OSError,ValueError): pass
    result=peaks(path)
    cache.parent.mkdir(parents=True,exist_ok=True);atomic_json(cache,result)
    # Peaks are disposable; keep a bounded number of versions per project.
    for stale in sorted(cache.parent.glob('*.json'),key=lambda file:file.stat().st_mtime_ns,reverse=True)[8:]:
        try:stale.unlink()
        except FileNotFoundError:pass
    return dict(result,ready=True,key=key)
