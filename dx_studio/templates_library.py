"""Local reusable selections with copied asset dependencies and portable JSON export."""
import base64
import copy
import json
import math
import binascii
from pathlib import Path
import uuid
from .history import atomic_json
from .paths import contained,file_lock


def validate_template(data):
    from .creator import finite
    if not isinstance(data,dict) or data.get('format_version')!=1:raise ValueError('Use a DX template with format_version 1')
    if not isinstance(data.get('name'),str) or not data['name'].strip() or len(data['name'])>120:raise ValueError('Use a template name of up to 120 characters')
    items,states,files=data.get('items'),data.get('states'),data.get('files')
    if not isinstance(items,list) or not 1<=len(items)<=200 or not isinstance(states,dict) or not isinstance(files,dict):raise ValueError('A template needs 1–200 editable items, states and asset files')
    if len(files)>200 or len(json.dumps(data,allow_nan=False))>30*1024*1024:raise ValueError('Template is too large')
    total=0
    for file,encoded in files.items():
        if not isinstance(file,str) or not isinstance(encoded,str):raise ValueError('Invalid template asset')
        contained('/tmp/dx-template-validation',file)
        try:blob=base64.b64decode(encoded,validate=True)
        except (ValueError,binascii.Error) as error:raise ValueError('Template assets must be valid base64') from error
        total+=len(blob)
        if total>20*1024*1024:raise ValueError('Template assets exceed 20 MB')
    seen=set()
    for item in items:
        if not isinstance(item,dict) or not isinstance(item.get('id'),str) or not item['id'].startswith('media_') or item['id'] in seen:raise ValueError('Template items need unique media IDs')
        seen.add(item['id'])
        if item.get('kind') not in ('text','shape','image','gif','video'):raise ValueError('Unknown template item type')
        if item.get('kind') in ('image','gif','video') and item.get('file') not in files:raise ValueError('A template asset is missing')
        box=item.get('box')
        if not isinstance(box,list) or len(box)!=4 or any(not finite(n,-1000000,1000000) for n in box) or min(box[2:])<=0:raise ValueError('Invalid template geometry')
        if not finite(item.get('t0'),-86400,86400) or not finite(item.get('dur'),.00001,86400):raise ValueError('Invalid template timing')
        if item.get('kind')=='text' and (not isinstance(item.get('text'),str) or len(item['text'])>20000):raise ValueError('Invalid template text')
        state=states.get(item['id'])
        if not isinstance(state,dict) or not finite(state.get('start'),0,86400) or not finite(state.get('end'),0,86400) or state['end']<=state['start']:raise ValueError('Invalid template layer range')
        if not isinstance(state.get('keys',[]),list) or len(state.get('keys',[]))>2000:raise ValueError('Too many template keyframes')
        for transform in [state]+state.get('keys',[]):
            if not isinstance(transform,dict) or any(key in transform and not finite(transform[key],-1000000,1000000) for key in ('t','x','y','scale','rotation','opacity')):raise ValueError('Invalid template transform')
            if transform.get('ease')=='custom':
                from .motion import validate_curve
                validate_curve(transform.get('bezier'))
    content=data.get('content',[0,0,1920,1080])
    if not isinstance(content,list) or len(content)!=4 or any(not finite(n,-1000000,1000000) for n in content) or content[2]<=content[0] or content[3]<=content[1]:raise ValueError('Invalid template content bounds')
    brand=data.get('brand')
    if not isinstance(brand,dict) or not isinstance(brand.get('fonts',{}),dict) or not isinstance(brand.get('credits',{}),dict):raise ValueError('Invalid template brand')
    if any(role not in ('reg','med','semi','bold','xb','med_t','xb_t') or file not in files for role,file in brand.get('fonts',{}).items()) or (brand.get('logo') and brand['logo'] not in files):raise ValueError('Missing brand dependencies')
    if any(not isinstance(note,str) or len(note)>20000 for note in brand.get('credits',{}).values()):raise ValueError('Invalid template credits')
    blocks=data.get('blocks',[])
    if not isinstance(blocks,list) or len(blocks)>200:raise ValueError('Too many template blocks')
    ids=set()
    from .blocks import KINDS
    for block in blocks:
        if not isinstance(block,dict) or not isinstance(block.get('id'),str) or block['id'] in ids or block.get('kind') not in KINDS or not isinstance(block.get('title'),str) or not isinstance(block.get('body'),str) or not finite(block.get('start'),0,86400) or not finite(block.get('duration'),.00001,86400):raise ValueError('Invalid template block')
        ids.add(block['id'])
    return data


class TemplateLibrary:
    def __init__(self,root):self.root=Path(root)
    def list(self):
        if not self.root.exists():return []
        return [{'id':p.stem,'name':json.loads(p.read_text())['name']} for p in sorted(self.root.glob('*.json'))]
    def get(self,identifier):
        if not isinstance(identifier,str) or len(identifier)!=32 or any(c not in '0123456789abcdef' for c in identifier):raise ValueError('Unknown template')
        return json.loads(Path(contained(self.root,identifier+'.json')).read_text())
    def capture(self,project,values,ids,name):
        items=[copy.deepcopy(item) for item in values['__media'] if item['id'] in ids]
        if not items:raise ValueError('Select editable text, shapes, blocks or imported media layers first')
        states={item['id']:copy.deepcopy(values['__layers'][item['id']]) for item in items}
        start=min(state['start'] for state in states.values())
        selected={item['id'] for item in items}
        complete={item.get('block_id') for item in items if item.get('block_id') and all(other['id'] in selected for other in values['__media'] if other.get('block_id')==item.get('block_id'))}
        blocks=[]
        for block in values.get('__blocks',[]):
            if block['id'] in complete:
                model=copy.deepcopy(block);members=[states[item['id']] for item in items if item.get('block_id')==block['id']];model['start']=min(st['start'] for st in members)-start;model['duration']=max(st['end'] for st in members)-start-model['start'];blocks.append(model)
        for item in items:
            if item.get('block_id') not in complete:item.pop('block_id',None)
            if item.get('presenter'):item['presenter']=False
            item['t0']-=start;state=states[item['id']];state['start']-=start;state['end']-=start;state['locked']=False
        from .brands import capture
        assets=copy.deepcopy(values['__brand_assets']);files={item['file'] for item in items if item.get('file')}
        files.update(assets['fonts'].values())
        if assets.get('logo'):files.add(assets['logo'])
        blobs={};total=0
        for file in files:
            path=Path(contained(project.media.assets,file));total+=path.stat().st_size
            if total>20*1024*1024:raise ValueError('A reusable template can include up to 20 MB of media/font assets')
            blobs[file]=base64.b64encode(path.read_bytes()).decode()
        return self.save({'format_version':1,'name':name,'items':items,'states':states,'brand':assets,'tokens':capture('Template',project.schema,values)['tokens'],'files':blobs,'blocks':blocks,'content':project.layout['content']})
    def save(self,data):
        validate_template(data)
        identifier=uuid.uuid4().hex;self.root.mkdir(parents=True,exist_ok=True)
        with file_lock(self.root/'.lock'):
            if len(list(self.root.glob('*.json')))>=100:raise ValueError('The local library contains 100 templates')
            atomic_json(self.root/(identifier+'.json'),data)
        return {'id':identifier,'name':data['name']}
    def apply(self,project,values,identifier,start,brand=False):
        data=validate_template(self.get(identifier));new=copy.deepcopy(values);mapping={}
        if not 0<=start<project.base_duration:raise ValueError('Choose a playhead inside the original scene')
        for file,encoded in data['files'].items():
            contained(project.media.assets,file);blob=base64.b64decode(encoded,validate=True)
            if len(blob)>20*1024*1024:raise ValueError('Template asset is too large')
            target='Templates/'+uuid.uuid4().hex+Path(file).suffix.lower();dest=Path(contained(project.media.assets,target));dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(blob);mapping[file]=target
        block_ids={block['id']:uuid.uuid4().hex[:10] for block in data.get('blocks',[])}
        old=data.get('content',[0,0,project.width,project.height]);area=project.layout['content'];scale=min((area[2]-area[0])/max(1,old[2]-old[0]),(area[3]-area[1])/max(1,old[3]-old[1]));oldcx=(old[0]+old[2])/2;oldcy=(old[1]+old[3])/2;cx=(area[0]+area[2])/2;cy=(area[1]+area[3])/2
        for source in data['items']:
            item=copy.deepcopy(source);oldid=item['id'];item['id']='media_'+uuid.uuid4().hex[:12];item['t0']+=start
            if item.get('block_id') in block_ids:
                oldblock=item['block_id'];role=oldid.removeprefix('media_block_'+oldblock+'_');item['block_id']=block_ids[oldblock];item['id']='media_block_'+item['block_id']+'_'+role
            x,y,w,h=item['box'];item['box']=[cx+(x-oldcx)*scale,cy+(y-oldcy)*scale,w*scale,h*scale]
            for field in ('size','pad','radius','stroke_w'):
                if isinstance(item.get(field),(int,float)):item[field]*=scale
            if item.get('file'):item['file']=mapping[item['file']]
            state=copy.deepcopy(data['states'][oldid]);state['start']+=start;state['end']=min(project.base_duration,state['end']+start)
            for transform in [state]+state.get('keys',[]):
                for field in ('x','y'):transform[field]=transform.get(field,0)*scale
            if state['start']>=project.base_duration:continue
            new['__media'].append(item);new['__layers'][item['id']]=state
        for block in data.get('blocks',[]):
            model=copy.deepcopy(block);model['id']=block_ids[block['id']];model['start']+=start;model['duration']=min(model['duration'],project.base_duration-model['start'])
            if model['duration']>0:new['__blocks'].append(model)
        for file,note in data['brand'].get('credits',{}).items():
            if file in mapping:new['__brand_assets']['credits'][mapping[file]]=note
        if brand:
            from .brands import resolve
            new.update(resolve({'tokens':data.get('tokens',[])},project.schema)['values'])
            kit=copy.deepcopy(data['brand']);kit['fonts']={r:mapping[f] for r,f in kit['fonts'].items()};kit['logo']=mapping.get(kit.get('logo'));kit['credits']={mapping.get(f,f):note for f,note in kit.get('credits',{}).items()};new['__brand_assets']=kit
        return new
