"""Portable relative motion styles; preparing an application never saves a project."""
import copy
import json
import math
from pathlib import Path
import uuid
from .history import atomic_json
from .paths import file_lock


def finite(value, low, high):
    return not isinstance(value, bool) and isinstance(value, (int, float)) and math.isfinite(value) and low <= value <= high


def validate_curve(points):
    if not isinstance(points, (list, tuple)) or len(points) != 4 or not all(finite(v, 0 if i in (0, 2) else -2, 1 if i in (0, 2) else 3) for i, v in enumerate(points)):
        raise ValueError('Bezier controls need x in 0–1 and y in −2–3')
    return list(points)


def bezier(u, points):
    x1, y1, x2, y2 = validate_curve(points)
    if u <= 0: return 0.0
    if u >= 1: return 1.0
    def cubic(t, a, b): return 3*(1-t)**2*t*a + 3*(1-t)*t*t*b + t**3
    low, high = 0.0, 1.0
    for _ in range(32):
        mid = (low+high)/2
        if cubic(mid, x1, x2) < u: low = mid
        else: high = mid
    return cubic((low+high)/2, y1, y2)


def validate_style(style):
    from .layers import PRESETS, EASES, TRANSFORM_KEYS
    if not isinstance(style, dict) or style.get('format_version') != 1: raise ValueError('Use a DX motion style with format_version 1')
    name = style.get('name')
    if not isinstance(name, str) or not name.strip() or len(name) > 80: raise ValueError('Use a motion name of up to 80 characters')
    keys = style.get('keys', [])
    if not isinstance(keys, list) or len(keys) > 2000: raise ValueError('Use at most 2,000 motion keys')
    clean = {'format_version':1, 'name':name.strip(), 'keys':[], 'duration':style.get('duration', .6)}
    if not finite(clean['duration'], .01, 86400): raise ValueError('Motion duration must be positive and finite')
    previous = -1
    for key in keys:
        if not isinstance(key, dict) or not finite(key.get('t'), 0, 1) or key['t'] <= previous: raise ValueError('Motion keys need increasing normalized times in 0–1')
        if any(not finite(key.get(field), -1000000, 1000000) for field in TRANSFORM_KEYS): raise ValueError('Motion transforms must be finite')
        if key['scale'] <= 0 or key['opacity'] < 0: raise ValueError('Use positive relative scale and nonnegative opacity')
        ease = key.get('ease', 'ease')
        if ease not in {*EASES, 'custom'}: raise ValueError('Unknown motion easing')
        out = {field:key[field] for field in ('t', *TRANSFORM_KEYS)}; out['ease'] = ease
        if ease == 'custom': out['bezier'] = validate_curve(key.get('bezier'))
        clean['keys'].append(out); previous = key['t']
    for which in ('enter', 'exit'):
        clean[which] = style.get(which, 'none'); clean[which+'_fraction'] = style.get(which+'_fraction', .5)
        if clean[which] not in PRESETS or not finite(clean[which+'_fraction'], .001, 1): raise ValueError('Invalid motion entrance/exit')
    if not keys and clean['enter'] == clean['exit'] == 'none': raise ValueError('Add keyframes or an entrance/exit before saving a motion style')
    return clean


def capture(name, state):
    from .layers import TRANSFORM_KEYS
    for key in state.get('keys',[]):
        if not isinstance(key,dict) or not finite(key.get('t'),-86400,86400) or any(not finite(key.get(field),-1000000,1000000) for field in TRANSFORM_KEYS):raise ValueError('Capture needs complete, finite keyframes')
    keys = sorted(state.get('keys', []), key=lambda k:k['t'])
    if len(keys) == 1: raise ValueError('Add a second keyframe before saving keyframed motion')
    duration = keys[-1]['t']-keys[0]['t'] if keys else state['end']-state['start']
    if duration <= 0: raise ValueError('Motion needs a positive duration')
    base = {k:state.get(k, 1 if k in ('scale', 'opacity') else 0) for k in TRANSFORM_KEYS}
    if base['scale'] <= 0 or base['opacity'] <= 0: raise ValueError('Use positive static scale and opacity before capturing motion')
    out = []
    for key in keys:
        item = {'t':(key['t']-keys[0]['t'])/duration, 'ease':key.get('ease', 'ease')}
        for field in TRANSFORM_KEYS: item[field] = key[field]/base[field] if field in ('scale','opacity') else key[field]-base[field]
        if item['ease'] == 'custom': item['bezier'] = key['bezier']
        out.append(item)
    return validate_style({'format_version':1, 'name':name, 'duration':duration, 'keys':out,
        **{which:state.get(which, 'none') for which in ('enter','exit')},
        **{which+'_fraction':max(.001,min(1,state.get(which+'_dur',.3)/duration)) for which in ('enter','exit')}})


def prepare(project, values, style, ids, duration, stagger=0, calm=False):
    """New keyframes relative to each target's static transform, without moving its window."""
    from .layers import TRANSFORM_KEYS
    style = validate_style(style)
    if not finite(duration,.01,86400) or not finite(stagger,0,60) or not isinstance(calm,bool): raise ValueError('Use a positive duration and a nonnegative stagger up to 60 seconds')
    states = values['__layers']; known = {m['id'] for m in project.layer_meta}
    if not isinstance(ids,list) or not 1 <= len(ids) <= 200 or any(not isinstance(i,str) or i not in known for i in ids) or len(ids)!=len(set(ids)): raise ValueError('Choose 1–200 existing layers')
    roots = [i for i in ids if not any(p in ids for p in project._ancestors(i))]
    unlocked = [i for i in roots if not any(states.get(p,{}).get('locked') for p in [i,*project._ancestors(i)])]
    patches = {}
    for index, identifier in enumerate(unlocked):
        state = copy.deepcopy(states[identifier]); delay = index*stagger
        if duration+delay > state['end']-state['start']+1e-6: raise ValueError('Motion and stagger must fit each selected layer; shorten the motion or extend the layer first')
        base = {k:state.get(k,1 if k in ('scale','opacity') else 0) for k in TRANSFORM_KEYS}
        if base['scale'] <= 0: raise ValueError('Use positive static layer scale before applying motion')
        state['keys'] = []
        for key in style['keys']:
            item = {'t':delay+key['t']*duration,'ease':key['ease']}
            for field in TRANSFORM_KEYS:
                relative = (1 if field=='scale' else 0) if calm and field!='opacity' else key[field]
                item[field] = base[field]*relative if field in ('scale','opacity') else base[field]+relative
            if item['ease']=='custom': item['bezier']=key['bezier']
            state['keys'].append(item)
        for which in ('enter','exit'):
            kind = style[which]
            state[which] = 'fade' if calm and kind!='none' else kind
            state[which+'_dur'] = duration*style[which+'_fraction']
        state['enter_delay'] = delay
        patches[identifier] = state
    candidate=copy.deepcopy(values);candidate['__layers'].update(patches);project.apply(candidate)
    return {'states':patches,'skipped':[i for i in roots if i not in unlocked]}


def builtin(identifier, name, **start):
    initial = dict(t=0,x=0,y=0,scale=1,rotation=0,opacity=0,ease='linear'); initial.update(start)
    end = dict(t=1,x=0,y=0,scale=1,rotation=0,opacity=1,ease='ease-out')
    if identifier=='pop': end['ease']='back'
    return dict(id=identifier,builtin=True,**validate_style({'format_version':1,'name':name,'duration':.6,'keys':[initial,end]}))


BUILTINS = [builtin('rise','Gentle rise',y=48),builtin('slide','Editorial slide',x=-80),
            builtin('zoom','Soft zoom',scale=.92),builtin('pop','Pop emphasis',scale=.82),builtin('fade','Calm fade')]


class MotionLibrary:
    def __init__(self, path): self.path=Path(path)
    def read(self):
        if not self.path.exists(): return []
        data=json.loads(self.path.read_text())
        if data.get('format_version')!=1: raise ValueError('Unsupported motion library format')
        return data['styles']
    def list(self): return copy.deepcopy(BUILTINS+self.read())
    def get(self, identifier):
        item=next((item for item in self.list() if item['id']==identifier),None)
        if item is None: raise ValueError('Unknown motion style')
        return item
    def save(self, style):
        clean=validate_style(style)
        with file_lock(self.path.with_suffix('.lock')):
            records=self.read()
            if len(records)>=100: raise ValueError('The local library holds up to 100 motion styles')
            if any(item['name'].casefold()==clean['name'].casefold() for item in BUILTINS+records): raise ValueError('Choose a unique motion name')
            clean['id']=uuid.uuid4().hex[:16]
            atomic_json(self.path,{'format_version':1,'styles':records+[clean]})
        return clean
    def delete(self, identifier):
        if any(item['id']==identifier for item in BUILTINS): raise ValueError('Included styles cannot be removed')
        with file_lock(self.path.with_suffix('.lock')):
            records=self.read()
            if not any(item['id']==identifier for item in records): raise ValueError('Unknown motion style')
            atomic_json(self.path,{'format_version':1,'styles':[item for item in records if item['id']!=identifier]})
