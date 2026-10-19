"""Shared contracts for the creator workflow; all additions are ordinary saved values."""
import math
from .composition import PRESENTER_PRESETS
from .paths import contained


def scene_defaults(project):
    labels={float(a):str(label)[:120] for a,b,label in project.cfg.get('chapters',[]) if 0<=a<project.base_duration}
    bounds=sorted({0.0,project.base_duration,*labels})
    return [{'id':f'scene_{i}','name':labels.get(a,f'Scene {i+1}'),'start':a,'end':b,'script':'','visual':'','source':''} for i,(a,b) in enumerate(zip(bounds,bounds[1:]))]


def defaults(project):
    return [('__groups','Layers',[]),('__story','Storyboard',scene_defaults(project)),('__anchors','Transcript',[]),('__protected','Revisions',[]),
            ('__presenter','Presenter',{'media_id':None,'scenes':{}}),
            ('__brand_assets','Brand',{'fonts':{},'logo':None,'credits':{}}),('__blocks','Blocks',[]),
            ('__export','Export',{'profile':'source','fps':0,'range':None,'captions':'burned','file':project.cfg.get('output','output.mp4')}),
            ('__quality_ignores','Export',[])]


def finite(value,low,high):return not isinstance(value,bool) and isinstance(value,(int,float)) and math.isfinite(value) and low<=value<=high


def validate(project,values):
    groups=values.get('__groups',[])
    if not isinstance(groups,list) or len(groups)>200:raise ValueError('Use at most 200 selection groups')
    group_ids=set();members=set()
    for group in groups:
        if not isinstance(group,dict) or not isinstance(group.get('id'),str) or group['id'] in group_ids or not isinstance(group.get('name'),str) or not 1<=len(group['name'])<=120:raise ValueError('Selection groups need unique IDs and a name')
        ids=group.get('layers')
        if not isinstance(ids,list) or not 1<=len(ids)<=2000 or any(not isinstance(id,str) for id in ids) or len(set(ids))!=len(ids) or members.intersection(ids):raise ValueError('A layer can belong to one selection group')
        group_ids.add(group['id']);members.update(ids)
    scenes=values.get('__story',[])
    if not isinstance(scenes,list) or len(scenes)>100:raise ValueError('Use at most 100 storyboard scenes')
    ids=set()
    for scene in scenes:
        if not isinstance(scene,dict) or not isinstance(scene.get('id'),str) or scene['id'] in ids:raise ValueError('Scene IDs must be unique')
        ids.add(scene['id'])
        if not finite(scene.get('start'),0,project.base_duration) or not finite(scene.get('end'),0,project.base_duration) or scene['end']<=scene['start']:raise ValueError('Scene ranges must fit the original timeline')
        for key in ('name','script','visual','source'):
            if not isinstance(scene.get(key,''),str) or len(scene.get(key,''))>20000:raise ValueError('Scene notes are too long')
    for key in ('__anchors','__protected','__blocks','__quality_ignores'):
        if not isinstance(values.get(key,[]),list) or len(values.get(key,[]))>2000:raise ValueError(key+' must be a bounded list')
    if any(not isinstance(key,str) or len(key)>200 for key in values.get('__protected',[])):raise ValueError('Invalid protected field')
    for anchor in values.get('__anchors',[]):
        if not isinstance(anchor,dict) or not all(isinstance(anchor.get(key),str) for key in ('voice_id','word_id','layer_id','text')) or not finite(anchor.get('offset',0),-86400,86400):raise ValueError('Invalid word anchor')
    block_ids=set()
    from .blocks import KINDS
    for block in values.get('__blocks',[]):
        if not isinstance(block,dict) or not isinstance(block.get('id'),str) or block['id'] in block_ids or block.get('kind') not in KINDS or not finite(block.get('start'),0,project.base_duration) or not finite(block.get('duration'),.00001,project.base_duration) or not isinstance(block.get('title'),str) or not isinstance(block.get('body'),str):raise ValueError('Invalid explanation block')
        block_ids.add(block['id'])
    if any(not isinstance(key,str) or len(key)>2000 for key in values.get('__quality_ignores',[])):raise ValueError('Invalid quality warning dismissal')
    presenter=values.get('__presenter',{})
    if not isinstance(presenter,dict) or not isinstance(presenter.get('scenes',{}),dict):raise ValueError('Invalid presenter settings')
    for key,preset in presenter.get('scenes',{}).items():
        if key not in ids or preset not in PRESENTER_PRESETS:raise ValueError('Choose a valid scene presenter layout')
    brand=values.get('__brand_assets',{})
    if not isinstance(brand,dict) or not isinstance(brand.get('fonts',{}),dict) or not isinstance(brand.get('credits',{}),dict):raise ValueError('Invalid brand assets')
    for role,file in brand.get('fonts',{}).items():
        if not isinstance(file,str):raise ValueError('Font paths must be strings')
        if role not in ('reg','med','semi','bold','xb','med_t','xb_t'):raise ValueError('Unknown font role')
        contained(project.media.assets,file)
    if brand.get('logo'):
        if not isinstance(brand['logo'],str):raise ValueError('Logo path must be a string')
        contained(project.media.assets,brand['logo'])
    if any(not isinstance(note,str) or len(note)>20000 for note in brand.get('credits',{}).values()):raise ValueError('Brand credit notes are too long')
    for item in values.get('__media',[]):
        if item.get('fit','stretch') not in ('stretch','cover','contain'):raise ValueError('Choose cover, contain or stretch for media fit')
        if not finite(item.get('source_offset',0),0,86400):raise ValueError('Media source trim must be nonnegative')
        for field in ('crop_x','crop_y'):
            if field in item and not finite(item[field],0,1):raise ValueError('Crop focus must be between 0 and 1')
        if not isinstance(item.get('box'),list) or len(item['box'])!=4 or any(not finite(n,-1000000,1000000) for n in item['box']) or min(item['box'][2:])<=0:raise ValueError('Media boxes need finite coordinates and positive sizes')
    for state in values.get('__layers',{}).values():
        from .motion import validate_curve
        if not isinstance(state.get('keys',[]),list) or len(state.get('keys',[]))>2000:raise ValueError('Use at most 2,000 layer keyframes')
        if not finite(state.get('enter_delay',0),0,86400):raise ValueError('Entrance delay must be nonnegative and finite')
        if any(not finite(state.get(key,0),0,86400) for key in ('enter_offset','exit_offset')):raise ValueError('Clip animation offsets must be nonnegative and finite')
        for keyframe in state.get('keys',[]):
            if not isinstance(keyframe,dict):raise ValueError('Invalid layer keyframe')
            if keyframe.get('ease')=='custom':validate_curve(keyframe.get('bezier'))
        for key in ('start','end','x','y','scale','rotation','opacity'):
            if key in state and not finite(state[key],-1000000,1000000):raise ValueError('Layer values must be finite numbers')
    from .core import hexc
    for entry in project.schema:
        value=values.get(entry['key'])
        if entry['type']=='color':
            try:hexc(value)
            except Exception as error:raise ValueError('Use a valid hex colour for '+entry['label']) from error
        if entry['type'] in ('number','time') and not finite(value,-1000000,1000000):raise ValueError('Use a finite number for '+entry['label'])
    for edit in values.get('__timeline',[]):
        if edit.get('op')=='reorder':
            ranges=edit.get('ranges',[])
            if not ranges or len(ranges)>100 or any(not isinstance(r,list) or len(r)!=2 or not finite(r[0],0,project.base_duration) or not finite(r[1],0,project.base_duration) or r[1]<=r[0] for r in ranges):raise ValueError('Invalid scene order')
            ordered=sorted(ranges)
            if abs(ordered[0][0])>1e-6 or abs(ordered[-1][1]-project.base_duration)>1e-6 or any(abs(a[1]-b[0])>1e-6 for a,b in zip(ordered,ordered[1:])):raise ValueError('Scene order must contain the complete original timeline once')
            if edit is not values['__timeline'][0]:raise ValueError('Scene order must precede ripple edits')


def reorder(values,ids):
    if len(ids)!=len(values['__story']) or set(ids)!={scene['id'] for scene in values['__story']}:raise ValueError('Choose each scene exactly once')
    if any(edit['op']!='reorder' for edit in values['__timeline']):raise ValueError('Reorder scenes before adding ripple cuts or holds. Restore those edits first if you need a new order.')
    by_id={s['id']:s for s in values['__story']};values['__story']=[by_id[key] for key in ids]
    values['__timeline']=[{'op':'reorder','ranges':[[s['start'],s['end']] for s in values['__story']]}]
    return values


def layout_at(project,t):
    from .composition import layout_for
    schedule=project.values.get('__presenter',{}).get('scenes',{})
    scene=next((s for s in project.values.get('__story',[]) if s['start']<=t<s['end']),None)
    preset=schedule.get(scene['id']) if scene else None
    return layout_for(project.width,project.height,preset or project.values.get('__composition','none'),project.cfg.get('safe_area'))
