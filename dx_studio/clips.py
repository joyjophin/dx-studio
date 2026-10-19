"""Non-destructive clip operations. Return staged values for normal undo/save."""
import copy
import uuid
from .creator import finite


def prepare(project, values, identifier, operation, at=None, start=None, end=None):
    new = copy.deepcopy(values)
    item = next((item for item in new.get('__media', []) if item['id'] == identifier), None)
    if not item or item['kind'] not in ('video', 'gif', 'image'):
        raise ValueError('Select an imported image, GIF or video clip')
    state = new['__layers'][identifier]
    if state.get('locked'): raise ValueError('Unlock this clip before editing it')
    a, b = state['start'], state['end']
    frame = 1 / project.fps
    if operation == 'split':
        if not finite(at, a + frame, b - frame):
            raise ValueError('Place the playhead inside the clip, at least one frame from either edge')
        cut = float(at) - a
        right = copy.deepcopy(item)
        right['id'] = 'media_' + uuid.uuid4().hex[:10]
        right['name'] = item.get('name', 'Clip') + ' · split'
        right.update(t0=float(at), dur=b-float(at), source_offset=float(item.get('source_offset', 0))+cut)
        right['audio_fade_in']=False
        right_state = copy.deepcopy(state)
        right_state.update(start=float(at), label=str(state.get('label') or right['name']),
                           enter_offset=state.get('enter_offset', 0)+cut)
        for key in right_state.get('keys', []): key['t'] -= cut
        state.update(end=float(at), end_exclusive=True, exit_offset=state.get('exit_offset', 0)+b-float(at))
        item.update(t0=a, dur=float(at)-a)
        item['audio_fade_out']=False
        new['__media'].insert(new['__media'].index(item)+1, right)
        new['__layers'][right['id']] = right_state
        for group in new.get('__groups', []):
            if identifier in group['layers']: group['layers'].append(right['id'])
        selected = right['id']
    elif operation == 'trim':
        if not finite(start, a, b-frame) or not finite(end, float(start)+frame, b):
            raise ValueError('Trim edges must stay inside the current clip and leave at least one frame')
        delta = float(start)-a
        item.update(t0=float(start), dur=float(end)-float(start),
                    source_offset=float(item.get('source_offset', 0))+delta)
        state.update(start=float(start), end=float(end), enter_offset=state.get('enter_offset', 0)+delta,
                     exit_offset=state.get('exit_offset', 0)+b-float(end))
        for key in state.get('keys', []): key['t'] -= delta
        selected = identifier
    else: raise ValueError('Choose trim or split')
    return {'values': new, 'selected': selected}
