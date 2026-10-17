"""Smallest editable scene; dimensions come from project.json."""
import json
from pathlib import Path
from dx_studio import *
CFG=json.loads(Path(__file__).with_name('project.json').read_text())
W,H=CFG['width'],CFG['height']
RESPONSIVE_COMPOSITION=True
COMPOSITION_EXEMPT_LAYERS={'background'}
AREA=(60,60,W-60,H-60)
def setup(p,project):
    global AREA
    AREA=project.layout['content']
def title_box(t):
    x0,y0,x1,y1=AREA
    return (x0,(y0+y1)/2-72,x1-x0,120)
SCHEMA=[{'key':'title','type':'text','label':'Title','default':'Start with one idea.'},
        {'key':'bg','type':'color','label':'Background','default':'#F5F3ED'},
        {'key':'ink','type':'color','label':'Text','default':'#182126'}]
def background(c,t,p): c.set_source_rgba(*p.bg);c.paint()
def title(c,t,p):
    x0,y0,x1,y1=AREA
    text(c,p.title,(x0+x1)/2,(y0+y1)/2,72,'xb',p.ink,align='c',maxw=x1-x0)
LAYERS=[Layer('background','Background',background,(0,0,W,H),params=['bg']),
        Layer('title','Title',title,title_box,params=['title','ink'])]
def draw(c,t,p): render_layers(c,t,p,LAYERS)
