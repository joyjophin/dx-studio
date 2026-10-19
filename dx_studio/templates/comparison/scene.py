"""PROOF POINT: a responsive editorial comparison, with illustrative data."""
import json
from pathlib import Path
from dx_studio import *
CFG=json.loads(Path(__file__).with_name('project.json').read_text());W,H=CFG['width'],CFG['height'];END=CFG['duration']
RESPONSIVE_COMPOSITION=True
COMPOSITION_EXEMPT_LAYERS={'background'}
SCHEMA=[{'key':k,'type':'color','label':l,'default':v} for k,l,v in [('bg','Ivory','#F4F4EC'),('ink','Ink','#111711'),('accent','Citron','#D8FC71')]]+[
    {'key':k,'type':'text','label':l,'default':v,'at':at} for k,l,v,at in [
        ('label','Series label','THE DIFFERENCE IS IN THE DETAILS',1),('hook','Opening headline','Show the\nchange.',1),
        ('comparison','Comparison headline','Make it\nmeasurable.',4),('closing','Closing headline','Explain what\nchanged.',9),
        ('before','First label','Before',4),('after','Second label','After',4),('unit','Unit','points',4),
        ('note','Data credit','ILLUSTRATIVE DATA · REPLACE WITH YOUR OWN',4),('takeaway','Takeaway','Give the numbers a story.',9)]]+[
    {'key':k,'type':'number','label':l,'default':v,'min':0,'max':100,'step':1} for k,l,v in [('value_before','First value',32),('value_after','Second value',68)]]
CAPS=[]
def geometry(layout):
    global X,Y,CW,CH,CX,TX,TY,TS,ALIGN,GX,GY,GW,GH,CAP,VERT
    X,Y,r,b=layout['content'];CW,CH=r-X,b-Y;CX=(X+r)/2;VERT=CW/CH<1.2
    TX=CX if VERT else X;TY=Y+CH*(.20 if VERT else .40);TS=min(108,CW*(.13 if VERT else .062),CH*.13);ALIGN='c' if VERT else 'l'
    GX=X if VERT else X+CW*.53;GY=Y+CH*(.39 if VERT else .12);GW=CW if VERT else CW*.47;GH=CH*(.47 if VERT else .64)
    CAP=layout['captions']
from dx_studio.composition import layout_for
geometry(layout_for(W,H,CFG.get('composition',{}).get('presenter','none'),CFG.get('safe_area')))
def setup(p,project):
    global CAPS
    CAPS=project.captions;geometry(project.layout)
def bg(c,t,p):c.set_source_rgba(*p.bg);c.paint()
def label(c,t,p):text(c,p.label,CX if VERT else X,Y+25,17 if not VERT else 20,'med',p.ink,align=ALIGN,track=.10,maxw=CW)
def headline(c,t,p):
    value,start=(p.hook,0) if t<3 else (p.comparison,3) if t<8 else (p.closing,8)
    a=P(t,start,start+.35);dy=35*(1-a)
    for i,word in enumerate(value.split('\n')):text(c,word,TX,TY+TS*i*1.02+dy,TS,'semi',p.ink,a,align=ALIGN,track=-.055,maxw=CW if VERT else CW*.49)
def chart(c,t,p):
    rrect(c,GX,GY,GW,GH,16);fill(c,p.ink)
def row(c,t,p,index):
    y=GY+GH*(.26+.37*index);x=GX+GW*.08;w=GW*.84
    value=(p.value_before,p.value_after)[index];name=(p.before,p.after)[index];size=min(29,GW*.047)
    text(c,name,x,y,size,'med',p.bg,maxw=w*.6)
    text(c,f'{value:g}',x+w,y,size*1.6,'semi',p.bg,align='r',track=-.04)
    rrect(c,x,y+GH*.07,w,GH*.075,3);fill(c,p.bg,.1)
    u=P(t,.45+index*.22,1.25+index*.22)
    if value>0:rrect(c,x,y+GH*.07,w*value/100*u,GH*.075,3);fill(c,p.accent if index else p.bg)
    if index==1:text(c,p.unit,x,y+GH*.24,size*.72,'reg',p.bg,.6,maxw=w)
def first(c,t,p):row(c,t,p,0)
def second(c,t,p):row(c,t,p,1)
def note(c,t,p):text(c,p.note,GX,GY+GH+38,15 if not VERT else 18,'med',p.ink,.62,track=.04,maxw=GW)
def takeaway(c,t,p):
    if t<8:return
    y=Y+CH*.94;text(c,p.takeaway,CX,y,min(38,CW*.05),'reg',p.ink,P(t,8,8.4),align='c',track=-.025,maxw=CW)
def captions(c,t,p):
    if CAPS:
        x,y,r,b=CAP;draw_captions(c,t,CAPS,cx=(x+r)/2,cy=(y+b)/2,size=min(38,(b-y)*.32),backing=p.ink,highlight=p.accent,maxw=(r-x)*.94)
LAYERS=[Layer('background','Background',bg,(0,0,W,H),0,END,params=['bg']),
    Layer('label','Series label',label,lambda t:(X,Y,CW,45),0,END,params=['label']),
    Layer('headline','Headline',headline,lambda t:(X,TY-TS,CW if VERT else CW*.49,TS*2.2),0,END,params=['hook','comparison','closing','ink']),
    Layer('chart','Comparison card',chart,lambda t:(GX,GY,GW,GH),0,END,params=['ink']),
    Layer('before','First comparison',first,lambda t:(GX+GW*.06,GY+GH*.12,GW*.88,GH*.3),0,END,params=['before','value_before']),
    Layer('after','Second comparison',second,lambda t:(GX+GW*.06,GY+GH*.49,GW*.88,GH*.4),0,END,params=['after','value_after','unit','accent']),
    Layer('credit','Data credit',note,lambda t:(GX,GY+GH+15,GW,35),0,END,params=['note']),
    Layer('takeaway','Takeaway',takeaway,lambda t:(X,Y+CH*.89,CW,CH*.08),8,END,params=['takeaway']),
    Layer('captions','Captions',captions,lambda t:(CAP[0],CAP[1],CAP[2]-CAP[0],CAP[3]-CAP[1]),0,END,params=['__captions'])]
def draw(c,t,p):render_layers(c,t,p,LAYERS)
def cues(p):return [dict(sound='tap',at=.5,gain=.2,layer='before'),dict(sound='tap',at=.75,gain=.2,layer='after'),dict(sound='chime',at=8,gain=.15,layer='takeaway')]
