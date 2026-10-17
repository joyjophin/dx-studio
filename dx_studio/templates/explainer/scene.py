"""An editable, responsive explainer. No downloads, voice model or private assets.

The project dimensions are read before LAYERS are declared so selection boxes,
text and timing use the same layout. Recomposition is explicit, not a crop.
"""
import json
from pathlib import Path
from dx_studio import *

CFG = json.loads(Path(__file__).with_name('project.json').read_text())
W, H, END = CFG['width'], CFG['height'], CFG['duration']
from dx_studio.composition import layout_for
RESPONSIVE_COMPOSITION = True
COMPOSITION_EXEMPT_LAYERS = {'background'}
VERTICAL = H > W
SCHEMA = [
    {'key':'bg', 'type':'color', 'label':'Background', 'default':'#F5F3ED'},
    {'key':'ink', 'type':'color', 'label':'Text', 'default':'#182126'},
    {'key':'accent', 'type':'color', 'label':'Accent', 'default':'#5056F4'},
    {'key':'surface', 'type':'color', 'label':'Cards', 'default':'#FFFFFF'},
    {'key':'highlight', 'type':'color', 'label':'Highlight', 'default':'#D9F86F'},
    {'key':'eyebrow', 'type':'text', 'label':'Opening label', 'default':'YOUR IDEA. YOUR FINAL CUT.', 'at':0.8},
    {'key':'title', 'type':'text', 'label':'Opening headline', 'default':'Make the story.\nKeep the layers.', 'at':1},
    {'key':'problem', 'type':'text', 'label':'Problem headline', 'default':'One small change.\nA whole new render?', 'at':5},
    {'key':'payoff', 'type':'text', 'label':'Payoff headline', 'default':'Change the words.\nKeep your work.', 'at':9},
    {'key':'closing', 'type':'text', 'label':'Closing headline', 'default':'Your first cut\nis a starting point.', 'at':13},
    {'key':'label_before', 'type':'text', 'label':'Before label', 'default':'A FLAT VIDEO'},
    {'key':'label_after', 'type':'text', 'label':'After label', 'default':'AN EDITABLE PROJECT'},
    {'key':'row1', 'type':'text', 'label':'Layer example 1', 'default':'Headline'},
    {'key':'row2', 'type':'text', 'label':'Layer example 2', 'default':'Visual'},
    {'key':'row3', 'type':'text', 'label':'Layer example 3', 'default':'Captions'},
    {'key':'before_body', 'type':'text', 'label':'Before description', 'default':'Everything baked in.'},
    {'key':'after_body', 'type':'text', 'label':'After description', 'default':'Every detail is yours.'},
    {'key':'t_problem', 'type':'time', 'label':'Problem begins', 'default':4.0},
    {'key':'t_payoff', 'type':'time', 'label':'Payoff begins', 'default':8.0},
    {'key':'t_closing', 'type':'time', 'label':'Closing begins', 'default':12.0},
    {'key':'caption_size', 'type':'number', 'label':'Caption size', 'default':42 if VERTICAL else 38, 'min':22, 'max':80},
    {'key':'show_captions', 'type':'bool', 'label':'Show captions', 'default':True},
]

def geometry(layout):
    global X,Y,CW,CH,CX,TX,TY,TW,TS,CARD_X,CARD_Y,CARD_W,CARD_H,CAP_X,CAP_Y,CAP_W,CAP_H,STEP,ROW_H,ROW_Y,SMALL,NOTE_Y,EYE_Y,ALIGN
    x0,y0,x1,y1=layout['content']; X,Y=x0,y0; CW,CH=x1-x0,y1-y0; CX=(x0+x1)/2
    wide=CW/CH>1.25
    if wide:
        TX=X+CW*.025; TY=Y+CH*.40; TW=CW*.44; TS=min(80,CW*.047,CH*.15); ALIGN='l'
        EYE_Y=Y+CH*.19
        CARD_X=X+CW*.53; CARD_Y=Y+CH*.12; CARD_W=CW*.45; CARD_H=CH*.68
        NOTE_Y=Y+CH*.94
    else:
        TX=CX; TY=Y+CH*.23; TW=CW*.94; TS=min(76,CW*.085,CH*.095); ALIGN='c'
        EYE_Y=Y+CH*.065
        CARD_X=X+CW*.035; CARD_Y=Y+CH*.43; CARD_W=CW*.93; CARD_H=CH*.40
        NOTE_Y=Y+CH*.95
    SMALL=min(26,CARD_W*.04,CARD_H*.11)
    STEP=CARD_H*.23; ROW_H=CARD_H*.19; ROW_Y=CARD_Y+CARD_H*.25
    a,b,d,e=layout['captions']; CAP_X=(a+d)/2; CAP_Y=(b+e)/2; CAP_W=d-a; CAP_H=e-b
geometry(layout_for(W,H,CFG.get('composition',{}).get('presenter','none'),CFG.get('safe_area')))

def setup(p, project):
    global CAPS
    CAPS=project.captions
    geometry(project.layout)

def el_bg(c,t,p): c.set_source_rgba(*p.bg); c.paint()
def el_eyebrow(c,t,p): text(c,p.eyebrow,TX,EYE_Y,max(16,TS*.28),'bold',p.accent,align=ALIGN,maxw=TW)
def headline(c,value,t,start,p):
    for i,line in enumerate(value.split('\n')):
        text(c,line,TX,TY+i*TS*1.15,TS,'xb',p.ink,P(t,start,start+.3) if start else 1,align=ALIGN,maxw=TW)
def el_title(c,t,p): headline(c,p.title,t,0,p)
def el_problem(c,t,p): headline(c,p.problem,t,p.t_problem,p)
def el_payoff(c,t,p): headline(c,p.payoff,t,p.t_payoff,p)
def el_closing(c,t,p): headline(c,p.closing,t,p.t_closing,p)
def el_card(c,t,p):
    rrect(c,CARD_X,CARD_Y,CARD_W,CARD_H,min(28,CARD_H*.07)); fill(c,p.surface)
def el_cardlabel(c,t,p):
    text(c,p.label_after if t>=p.t_payoff else p.label_before,CARD_X+CARD_W*.05,CARD_Y+CARD_H*.15,SMALL*.75,'bold',p.accent,maxw=CARD_W*.90)
def row(c,t,p,index):
    x=CARD_X+CARD_W*.05; y=ROW_Y+index*STEP; w=CARD_W*.90
    rrect(c,x,y,w,ROW_H,min(12,ROW_H*.2)); fill(c,mixc(p.surface,p.accent,.08))
    text(c,(p.row1,p.row2,p.row3)[index],x+SMALL*.7,y+ROW_H*.67,SMALL,'semi',p.ink,maxw=w-SMALL*3)
    if t>=p.t_payoff:
        check(c,x+w-SMALL,y+ROW_H/2,SMALL*.35,P(t,p.t_payoff+.25*index,p.t_payoff+.25*index+.35),p.accent,wdt=max(2,SMALL*.1))
def el_row1(c,t,p): row(c,t,p,0)
def el_row2(c,t,p): row(c,t,p,1)
def el_row3(c,t,p): row(c,t,p,2)
def el_note(c,t,p):
    text(c,p.after_body if t>=p.t_payoff else p.before_body,CARD_X+CARD_W/2,NOTE_Y,max(20,TS*.37),'med',p.ink,align='c',maxw=CARD_W)
def el_marker(c,t,p):
    x=TX if ALIGN=='l' else TX-TW*.35
    rrect(c,x,TY+TS*1.48,TW*.7*P(t,p.t_payoff,p.t_payoff+.55),max(5,TS*.1),3);fill(c,p.highlight)
def el_captions(c,t,p):
    if p.show_captions:
        # The size setting is a maximum; shrink to the available caption region.
        size=min(p.caption_size,CAP_W*.052,CAP_H*.34)
        draw_captions(c,t,CAPS,cx=CAP_X,cy=CAP_Y,backing=p.ink,highlight=p.highlight,size=size,maxw=CAP_W*.88,maxh=CAP_H*.86)

def title_box(t): return (TX if ALIGN=='l' else TX-TW/2,TY-TS,TW,TS*2.5)
def card_box(t): return (CARD_X,CARD_Y,CARD_W,CARD_H)
def caption_box(t): return (CAP_X-CAP_W/2,CAP_Y-CAP_H/2,CAP_W,CAP_H)
LAYERS=[
    Layer('background','Background',el_bg,(0,0,W,H),0,END,params=['bg']),
    Layer('eyebrow','Opening label',el_eyebrow,lambda t:(X,EYE_Y-TS*.4,CW,TS*.6),0,END,params=['eyebrow','accent']),
    Layer('title','Opening headline',el_title,title_box,0,4,params=['title','ink']),
    Layer('problem','Problem headline',el_problem,title_box,4,8,params=['problem','t_problem']),
    Layer('marker','Payoff underline',el_marker,lambda t:(TX if ALIGN=='l' else TX-TW*.35,TY+TS*1.48,TW*.7,max(5,TS*.1)),8,12,params=['highlight','t_payoff']),
    Layer('payoff','Payoff headline',el_payoff,title_box,8,12,params=['payoff','t_payoff']),
    Layer('closing','Closing headline',el_closing,title_box,12,END,params=['closing','t_closing']),
    Layer('card','Card background',el_card,card_box,0,END,params=['surface']),
    Layer('card_label','Card label',el_cardlabel,lambda t:(CARD_X+CARD_W*.05,CARD_Y+CARD_H*.04,CARD_W*.9,CARD_H*.15),0,END,params=['label_before','label_after']),
    *[Layer(f'row{i+1}',f'Example layer {i+1}',fn,lambda t,i=i:(CARD_X+CARD_W*.05,ROW_Y+i*STEP,CARD_W*.9,ROW_H),0,END,params=[f'row{i+1}']) for i,fn in enumerate([el_row1,el_row2,el_row3])],
    Layer('note','Supporting text',el_note,lambda t:(CARD_X,NOTE_Y-TS*.42,CARD_W,TS*.6),0,END,params=['before_body','after_body']),
    Layer('captions','Captions',el_captions,caption_box,0,END,params=['caption_size','show_captions','__captions']),
]
def draw(c,t,p): render_layers(c,t,p,LAYERS)
def cues(p):
    return [dict(sound='tap',at=p.t_problem,layer='problem'),dict(sound='chime',at=p.t_payoff,layer='payoff'),dict(sound='tap',at=p.t_closing,layer='closing')]
