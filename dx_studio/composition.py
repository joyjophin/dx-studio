"""Shared presenter reservations and content/caption rectangles, in output pixels.

Rectangles are [left, top, right, bottom]. Guides never draw into exported frames.
Templates opt in to reflow by consuming Project.layout in setup().
"""
import math

PRESENTER_PRESETS = {
    'none': 'No presenter',
    'bottom-left': 'Bottom-left corner',
    'bottom-right': 'Bottom-right corner',
    'left-half': 'Left half',
    'right-half': 'Right half',
    'bottom-band': 'Bottom band (40%)',
}

def _rectangle(value, width, height, name):
    if not isinstance(value, (list,tuple)) or len(value) != 4:
        raise ValueError(f'{name} must be [left, top, right, bottom]')
    if any(isinstance(x,bool) or not isinstance(x,(int,float)) or not math.isfinite(x) for x in value):
        raise ValueError(f'{name} coordinates must be finite numbers')
    x0,y0,x1,y1=value
    if not (0 <= x0 < x1 <= width and 0 <= y0 < y1 <= height):
        raise ValueError(f'{name} must be a non-empty rectangle inside the video')
    return list(value)

def layout_for(width, height, preset='none', safe_area=None):
    if not isinstance(preset,str) or preset not in PRESENTER_PRESETS: raise ValueError(f'Unknown presenter layout: {preset!r}')
    vertical = height > width
    if safe_area is not None and not isinstance(safe_area,dict): raise ValueError("safe_area must be an object")
    safe_area = safe_area or {}
    # Keep the portrait graphics band centred while retaining its original width.
    portrait_margin=width*130/1080
    fallback = ([portrait_margin,height*.089,width-portrait_margin,height*.8125] if vertical else
                [width*.05,height*.06,width*.95,height*.94])
    available=_rectangle(safe_area.get('content',fallback),width,height,'Content safe area')
    gap=min(width,height)*.03
    presenter=None
    if preset in ('bottom-left','bottom-right'):
        pw,ph=width*.32,height*.34
        px=0 if preset=='bottom-left' else width-pw
        presenter=[px,height-ph,px+pw,height]
        # Use a full-width graphics band above the corner reservation, avoiding
        # both the presenter and their breathing room without clipping artwork.
        available[3]=min(available[3],presenter[1]-gap)
    elif preset in ('left-half','right-half'):
        if preset=='left-half':
            presenter=[0,0,width/2,height]
            available[0]=max(available[0],width/2+gap)
        else:
            presenter=[width/2,0,width,height]
            available[2]=min(available[2],width/2-gap)
    elif preset=='bottom-band':
        presenter=[0,height*.6,width,height]
        available[3]=min(available[3],presenter[1]-gap)
    if preset=='none' and safe_area.get('captions'):
        captions=_rectangle(safe_area['captions'],width,height,'Caption safe area')
        if not (available[0] <= captions[0] < captions[2] <= available[2] and
                available[1] < captions[1] < captions[3] <= available[3]):
            raise ValueError('Caption safe area must fit inside the content safe area')
    else:
        band=min(height*.10,(available[3]-available[1])*.17)
        captions=[available[0],available[3]-band,available[2],available[3]]
    content=[available[0],available[1],available[2],min(available[3],captions[1]-gap)]
    _rectangle(content,width,height,'Graphics area')
    return {'preset':preset, 'label':PRESENTER_PRESETS[preset],
            'content':content, 'captions':captions, 'presenter':presenter}


def presenter_collisions(project, times):
    """Selection boxes crossing the presenter zone; a guide for visual review."""
    reserved=project.layout['presenter']
    if reserved is None: return []
    exempt=set(getattr(project.scene,'COMPOSITION_EXEMPT_LAYERS',()))
    collisions=set()
    for t in times:
        for hit in project.hits(t):
            if hit['id'] in exempt: continue
            pts=hit['corners']
            box=[min(p[0] for p in pts),min(p[1] for p in pts),max(p[0] for p in pts),max(p[1] for p in pts)]
            if max(box[0],reserved[0]) < min(box[2],reserved[2]) and max(box[1],reserved[1]) < min(box[3],reserved[3]):
                collisions.add(hit['id'])
    return sorted(collisions)
