"""Saved bus balance and export mastering settings, separate from preview monitoring."""
import math

TRACKS = ('voice','music','effects','footage')


def defaults(cfg):
    mix = cfg.get('mix', {})
    return {**{key:1.0 for key in TRACKS}, **{key+'_muted':False for key in TRACKS},
            'loudness':mix.get('loudness',-14.0),'peak':mix.get('peak',-1.2)}


def settings(project):
    return {**defaults(project.cfg), **getattr(project,'values',{}).get('__mix',{})}


def level(mix, track):
    return 0.0 if mix.get(track+'_muted') else mix.get(track,1.0)


def validate(mix):
    if not isinstance(mix,dict): raise ValueError('Audio mix must be an object')
    for key,low,high in [(key,0,2) for key in TRACKS]+[('loudness',-60,-5),('peak',-12,-.1)]:
        value=mix.get(key)
        if isinstance(value,bool) or not isinstance(value,(int,float)) or not math.isfinite(value) or not low<=value<=high:
            raise ValueError(f'Audio mix {key} must be between {low} and {high}')
    for key in TRACKS:
        if not isinstance(mix.get(key+'_muted'),bool): raise ValueError('Audio mix mute must be true or false')
