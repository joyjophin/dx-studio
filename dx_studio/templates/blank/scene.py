"""A genuinely empty canvas. Added titles, media and captions stay editable."""
import json
from pathlib import Path
from dx_studio import *
CFG=json.loads(Path(__file__).with_name('project.json').read_text())
W,H,END=CFG['width'],CFG['height'],CFG['duration']
RESPONSIVE_COMPOSITION=True
COMPOSITION_EXEMPT_LAYERS={'background'}
CAPS=[]
CAP=(0,0,W,H)
SCHEMA=[{'key':'bg','type':'color','label':'Background','default':'#F4F4EC'},
        {'key':'ink','type':'color','label':'Text','default':'#111711'}]
def setup(p,project):
    global CAPS,CAP
    CAPS=project.captions;CAP=project.layout['captions']
def background(c,t,p):c.set_source_rgba(*p.bg);c.paint()
def captions(c,t,p):
    x,y,r,b=CAP
    if CAPS:draw_captions(c,t,CAPS,cx=(x+r)/2,cy=(y+b)/2,backing=p.ink,size=min(40,(b-y)*.3),maxw=(r-x)*.92)
LAYERS=[Layer('background','Background',background,(0,0,W,H),0,END,params=['bg']),
        Layer('captions','Captions',captions,lambda t:(CAP[0],CAP[1],CAP[2]-CAP[0],CAP[3]-CAP[1]),0,END,params=['__captions'])]
def draw(c,t,p):render_layers(c,t,p,LAYERS)
