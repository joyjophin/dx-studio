"""dx_studio.timemap: ripple edits (insert time / delete time) as a mapping between
output time (what you watch) and scene time (what the scene code and all stored times use).

Edits are applied in order, each expressed in the output time of the moment it was made:
    {"op": "insert", "at": 12.0, "dur": 1.5}      hold the frame at 12.0 s for 1.5 s, pushing everything later
    {"op": "delete", "start": 20.0, "end": 22.0}  remove 20–22 s, pulling everything later earlier
"""

def out_time(s, edits):
    """scene time -> output time"""
    for e in edits:
        if e['op']=='reorder':
            cursor=0.0
            for a,b in e['ranges']:
                if a<=s<b:s=cursor+s-a;break
                cursor+=b-a
        elif e['op'] == 'insert':
            if s >= e['at']: s += e['dur']
        elif e['op'] == 'delete':
            a, b = e['start'], e['end']
            if s >= b: s -= (b - a)
            elif s > a: s = a
    return s

def scene_time(o, edits):
    """output time -> scene time"""
    for e in reversed(edits):
        if e['op']=='reorder':
            cursor=0.0
            for a,b in e['ranges']:
                if o<cursor+b-a:o=a+o-cursor;break
                cursor+=b-a
            else:o=e['ranges'][-1][1]
        elif e['op'] == 'insert':
            at, d = e['at'], e['dur']
            if o >= at + d: o -= d
            elif o >= at: o = at
        elif e['op'] == 'delete':
            if o >= e['start']: o += e['end'] - e['start']
    return o

def out_duration(base, edits):
    total=base
    for e in edits:
        if e['op']=='insert':total+=e['dur']
        elif e['op']=='delete':total-=e['end']-e['start']
    return total

def segments(base, edits, step=None):
    """list of (o0, o1, s0, s1, kind) covering the output timeline; kind is 'play' or 'hold'"""
    total = out_duration(base, edits)
    # breakpoints in output time where the mapping changes slope
    pts = {0.0, total}
    for i, e in enumerate(edits):
        prior = edits[:i]
        if e['op']=='reorder':
            cursor=0.0
            for a,b in e['ranges']:
                pts.add(_fwd(cursor,edits[i+1:]));cursor+=b-a
            continue
        if e['op'] == 'insert':
            a = e['at']; later = edits[i+1:]
            pts.add(_fwd(a, later)); pts.add(_fwd(a + e['dur'], later))
        else:
            pts.add(_fwd(e['start'], edits[i+1:]))
    pts = sorted(p for p in pts if 0 <= p <= total)
    out = []
    for o0, o1 in zip(pts, pts[1:]):
        if o1 - o0 < 1e-6: continue
        s0, s1 = scene_time(o0 + 1e-7, edits), scene_time(o1 - 1e-7, edits)
        out.append((o0, o1, s0, s1, 'hold' if abs(s1 - s0) < 1e-4 else 'play'))
    return out

def _fwd(o, later_edits):
    """position of an output time (at the moment of an edit) after the later edits are applied"""
    return out_time(o,later_edits)
