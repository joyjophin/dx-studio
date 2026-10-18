"""Explanation blocks expand to editable text and shape layers, not screenshots."""
import copy
import csv
import io
import math
import uuid

KINDS={'comparison','steps','quote','bars','title','diagram'}


def prepare(project,values,config):
    kind=config.get('kind')
    if kind not in KINDS:raise ValueError('Choose comparison, steps, quote, bars, diagram or title')
    identifier=config.get('id') or uuid.uuid4().hex[:10]
    if not isinstance(identifier,str) or len(identifier)>80:raise ValueError('Invalid block ID')
    title=str(config.get('title','Your explanation'))[:500];body=str(config.get('body',''))[:5000]
    start=float(config.get('start',0));duration=float(config.get('duration',4))
    if not math.isfinite(start+duration) or not 0<=start<project.base_duration or duration<=0:raise ValueError('Choose a block range inside the scene')
    duration=min(duration,project.base_duration-start)
    x0,y0,x1,y1=project.layout['content'];w=x1-x0;h=y1-y0;items=[]
    ink=values.get('ink','#182126');accent=values.get('accent','#5056F4');surface=values.get('surface','#FFFFFF')
    def item(role,kind,box,**fields):
        items.append({'id':'media_block_'+identifier+'_'+role,'name':title+' · '+role,'kind':kind,'box':box,'t0':start,'dur':duration,'block_id':identifier,**fields})
    def text(role,value,x,y,width,size=42,color=None):item(role,'text',[x,y,width,size*2],text=str(value),weight='bold',size=size,color=color or ink,align='l',anim='rise',anim_dur=.4,track=0,line_height=1.15)
    def shape(role,x,y,width,height,color):item(role,'shape',[x,y,width,height],shape='rect',fill=color,stroke=None,radius=18,anim='fade',anim_dur=.3)
    shape('backplate',x0,y0,w,h,values.get('bg','#F5F3ED'))
    size=max(20,min(58,w*.065,h*.12));text('title',title,x0,y0,w,size,accent)
    lines=[line.strip() for line in body.splitlines() if line.strip()]
    top=y0+size*1.8;available=max(60,y1-top)
    if kind=='title':text('body',body,x0,top,w,size*.6)
    elif kind=='comparison':
        lines=(lines+['Before','After'])[:2];gap=w*.04;cw=(w-gap)/2
        for i,line in enumerate(lines):
            shape('card'+str(i),x0+i*(cw+gap),top,cw,available*.8,surface);text('side'+str(i),line,x0+i*(cw+gap)+cw*.06,top+available*.12,cw*.88,size*.65)
    elif kind=='steps':
        if not 2<=len(lines)<=6:raise ValueError('Enter 2–6 steps, one per line')
        step=available/len(lines)
        for i,line in enumerate(lines):text('step'+str(i),str(i+1)+'. '+line,x0,top+i*step,w,size*.65)
    elif kind=='diagram':
        if not 2<=len(lines)<=6:raise ValueError('Enter 2–6 diagram nodes, one per line')
        horizontal=w/available>1.4;count=len(lines);span=w if horizontal else available*.9;gap=span*.08;cell=(span-gap*(count-1))/count
        for i,line in enumerate(lines):
            nx=x0+i*(cell+gap) if horizontal else x0+w*.08;ny=top+available*.22 if horizontal else top+i*(cell+gap)
            nw=cell if horizontal else w*.84;nh=available*.42 if horizontal else cell
            shape('node'+str(i),nx,ny,nw,nh,surface);text('node_label'+str(i),line,nx+nw*.06,ny+nh*.18,nw*.88,min(size*.6,nh*.35,nw*.12))
            if i<count-1:
                box=[nx+nw+gap*.15,ny+nh*.5-8,gap*.7,16] if horizontal else [nx+nw*.5-8,ny+nh+gap*.15,16,gap*.7]
                item('connector'+str(i),'shape',box,shape='arrow',direction='right' if horizontal else 'down',fill=None,stroke=accent,stroke_w=max(2,size*.05),draw_on=.4)
    elif kind=='quote':
        text('quote','“'+body+'”',x0,top,w,size*.8);text('credit',config.get('credit',''),x0,y1-size,w,size*.45,accent)
    elif kind=='bars':
        rows=list(csv.reader(io.StringIO(body)))
        if not 1<=len(rows)<=8:raise ValueError('Enter 1–8 CSV rows: label,number')
        data=[]
        for row in rows:
            try:label,value=row[0],float(row[1])
            except (IndexError,ValueError) as error:raise ValueError('Each chart row needs a label and a number') from error
            if not math.isfinite(value):raise ValueError('Chart values must be finite')
            data.append((label,value))
        low=min(0,min(v for _,v in data));high=max(0,max(v for _,v in data));span=high-low or 1;left=x0+w*.28;chartw=w*.58;zero=left+(-low/span)*chartw;step=available/(len(data)+1)
        for i,(label,value) in enumerate(data):
            y=top+i*step;text('label'+str(i),label,x0,y,w*.26,size*.42);end=left+(value-low)/span*chartw
            shape('bar'+str(i),min(zero,end),y,max(1,abs(end-zero)),step*.5,accent);text('value'+str(i),f'{value:g}',left+chartw+w*.02,y,w*.12,size*.42)
        text('source',config.get('credit',''),x0,y1-size*.5,w,size*.3)
    new=copy.deepcopy(values);previous=next((b for b in values.get('__blocks',[]) if b['id']==identifier),None);timing_changed=previous is not None and (previous['start']!=start or previous['duration']!=duration);existing={item['id']:item for item in values['__media']};kept=[]
    for item in items:
        state=values['__layers'].get(item['id'],{})
        if state.get('locked') or 'layer:'+item['id'] in values.get('__protected',[]):kept.append(existing.get(item['id'],item))
        else:
            kept.append(item)
            if timing_changed and item['id'] in new['__layers']:new['__layers'][item['id']].update(start=start,end=start+duration)
    generated={item['id'] for item in kept}
    old=[item for item in new['__media'] if item.get('block_id')!=identifier or (item['id'] not in generated and (new['__layers'].get(item['id'],{}).get('locked') or 'layer:'+item['id'] in new.get('__protected',[])))]
    new['__media']=old+kept
    model=dict(config,id=identifier,title=title,body=body,start=start,duration=duration)
    new['__blocks']=[b for b in new.get('__blocks',[]) if b['id']!=identifier]+[model]
    return new
