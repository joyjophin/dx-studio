"""MAKE IT CLICK — an original, editable ten-second motion study.

All frames are sampled analytically: no video, rendered text, private artwork,
external fonts or stateful simulation. The portrait layout is composed afresh.
"""
import json
import math
from pathlib import Path
import numpy as np
from dx_studio import *

CFG = json.loads(Path(__file__).with_name('project.json').read_text())
W, H = CFG['width'], CFG['height']
PORTRAIT = H > W
RESPONSIVE_COMPOSITION = True
COMPOSITION_EXEMPT_LAYERS = {'paper', 'grid', 'chapter_wipe'}

SCHEMA = [
    {'key':key,'type':'color','label':label,'default':value,'group':'Art direction'}
    for key,label,value in [('ink','Ink','#111711'),('paper','Ivory','#F4F4EC'),('acid','Citron','#D8FC71')]
] + [
    {'key':key,'type':'text','label':label,'default':value,'at':at,'group':group}
    for key,label,value,at,group in [
        ('brand','Brand','DX Studio',.9,'Identity'),
        ('edition','Film label','A MOTION STUDY',.9,'Identity'),
        ('hook','Opening headline','Complex.',1,'01 / Complexity'),
        ('hook_body','Opening support','Every idea starts somewhere.',1,'01 / Complexity'),
        ('clear','Clarity headline','Clear.',3.2,'02 / Clarity'),
        ('clear_body','Clarity support','Find the thread. Make it click.',3.2,'02 / Clarity'),
        ('yours','Editable headline','Yours.',6,'03 / Ownership'),
        ('yours_body','Editable support','Every word. Every frame. Every layer.',6,'03 / Ownership'),
        ('poster_line1','Poster headline','Less noise.',6,'03 / Ownership'),
        ('poster_line2','Poster emphasis','More signal.',6,'03 / Ownership'),
        ('poster_label','Poster small print','THE ART OF EXPLAINING',6,'03 / Ownership'),
        ('type_label','Type track label','Typography',6,'03 / Ownership'),
        ('motion_label','Motion track label','Motion',6,'03 / Ownership'),
        ('audio_label','Audio track label','Sound',6,'03 / Ownership'),
        ('end_line1','Closing line one','Make the story.',8.8,'04 / Signature'),
        ('end_line2','Closing line two','Keep the layers.',8.8,'04 / Signature'),
        ('end_note','Closing note','OPEN SOURCE. ENDLESS POSSIBILITIES.',8.8,'04 / Signature'),
        ('footer','Footer','DESIGNED TO EXPLAIN',1,'Identity'),
    ]
]


def geometry(layout, reserve_captions=False):
    global X,Y,CW,CH,CX,AX,AY,AS,TX,TY,TS,SW,SY,FY,HY
    x0,y0,x1,y1=layout['content']
    if not reserve_captions:y1=layout['captions'][3]
    X,Y=x0,y0; CW,CH=x1-x0,y1-y0; CX=(x0+x1)/2
    if CW/CH>1.15:
        TX=X+8; TY=Y+CH*.47; TS=min(174,CW*.103); SW=CW*.49; SY=TY+92
        AX=X+CW*.735; AY=Y+CH*.49; AS=min(CW*.445/760,CH*.83/760)
        HY=Y+28; FY=y1-22
    else:
        TX=X; TY=Y+CH*.205; TS=min(154,CW*.19); SW=CW; SY=TY+78
        AX=CX; AY=Y+CH*.61; AS=min(CW*.98/760,CH*.50/760)
        HY=Y+26; FY=y1-20

from dx_studio.composition import layout_for
geometry(layout_for(W,H,'none',CFG.get('safe_area')))

CAPS=[]
CAPTION_BOX=(0,0,1,1)
def setup(p, project):
    global CAPS,CAPTION_BOX
    CAPS=project.captions
    a,b,d,e=project.layout['captions'];CAPTION_BOX=(a,b,d-a,e-b)
    geometry(project.layout, bool(CAPS))

def optional_captions(c,t,p):
    if CAPS:
        x,y,w,h=CAPTION_BOX
        draw_captions(c,t,CAPS,cx=x+w/2,cy=y+h/2,size=min(38,h*.30),maxw=w*.94,maxh=h*.9,backing=p.ink,highlight=p.acid)


def ease(t,a,b): return P(t,a,b,eio)

def line(c,pts,col,width=1,a=1):
    c.new_path()
    for i,point in enumerate(pts): (c.move_to if i==0 else c.line_to)(*point)
    stroke(c,col,width,a)

def rect(c,x,y,w,h,col,r=0,a=1):
    rrect(c,x,y,w,h,r); fill(c,col,a)

def art(c): c.translate(AX,AY); c.scale(AS,AS)

def reveal(c,t,start,dy=55):
    u=P(t,start,start+.58,eo)
    c.translate(0,dy*(1-u))
    return u

INVERTED=False
def text_col(t,p): return p.ink if INVERTED else p.paper

def bg(c,t,p):
    c.set_source_rgba(*p.ink);c.paint()
    # A directional sweep replaces a crossfade: it lands exactly on the beat.
    v=ease(t,2.08,2.48)
    if v: rect(c,W*(1-v),0,W*v,H,p.acid)
    v=ease(t,4.30,4.65)
    if v: rect(c,0,H*(1-v),W,H*v,p.ink)

def grid(c,t,p):
    col=text_col(t,p)
    # Engineering register: fine enough to disappear at reading distance.
    for x in range(0,W+1,80): line(c,[(x,0),(x,H)],col,.7,.028)
    for y in range(0,H+1,80): line(c,[(0,y),(W,y)],col,.7,.028)

def brand(c,t,p):
    col=text_col(t,p)
    # Three open planes form a small mark; a motif, rather than a stock icon.
    x=X+4;y=HY-10
    for i in range(3):
        line(c,[(x,y+i*5),(x+13,y-7+i*5),(x+26,y+i*5),(x+13,y+7+i*5),(x,y+i*5)],col,1.7)
    text(c,p.brand,X+43,HY+8,26,'semi',col,track=-.025)
    text(c,p.edition,X+CW,HY+8,16 if not PORTRAIT else 18,'med',col,align='r',track=.10,maxw=CW*.42)

def footer(c,t,p):
    col=text_col(t,p)
    line(c,[(X,FY-32),(X+CW,FY-32)],col,1,.22)
    text(c,p.footer,X,FY,15 if not PORTRAIT else 18,'med',col,track=.12)
    # One continuous rail, with a small travelling endpoint.
    x=X+CW-160; y=FY-6
    line(c,[(x,y),(x+160,y)],col,2,.2)
    q=clamp(t/9.5)
    line(c,[(x,y),(x+160*q,y)],col,2)


def title(c,t,p,key,start,end):
    a=reveal(c,t,start,70)
    a*=1-ease(t,end-.20,end)
    text(c,getattr(p,key),CX if PORTRAIT else TX,TY,TS,'semi',text_col(t,p),a,align='c' if PORTRAIT else 'l',track=-.065,maxw=SW)

def support(c,t,p,key,start,end):
    a=reveal(c,t,start+.18,24)*(1-ease(t,end-.2,end))
    text(c,getattr(p,key),CX if PORTRAIT else TX,SY,30 if not PORTRAIT else 36,'reg',text_col(t,p),a*.78,align='c' if PORTRAIT else 'l',track=-.02,maxw=SW)

def opener(c,t,p): title(c,t,p,'hook',0,2.2)
def opener_support(c,t,p): support(c,t,p,'hook_body',0,2.2)
def clearer(c,t,p): title(c,t,p,'clear',2.3,4.5)
def clearer_support(c,t,p): support(c,t,p,'clear_body',2.3,4.5)
def ownership(c,t,p): title(c,t,p,'yours',4.6,7.5)
def ownership_support(c,t,p): support(c,t,p,'yours_body',4.6,7.5)

# A toroidal ribbon mesh. Disorder is a geometric deformation, not random noise.
# Two families of curves reveal a solid surface without raster imagery.
THETA=np.linspace(0,math.tau,180)
CURVES=[]
for phi in np.linspace(0,math.tau,42,endpoint=False):
    CURVES.append((THETA,np.full_like(THETA,phi),False))
for theta in np.linspace(0,math.tau,36,endpoint=False):
    CURVES.append((np.full_like(THETA,theta),THETA,True))

def surface(c,t,p):
    art(c)
    intro=P(t,0,.8,eo);c.scale(.90+.10*intro,.90+.10*intro)
    settle=ease(t,1.72,2.70)
    leave=ease(t,4.22,4.59)
    c.translate(0,-80*leave);c.scale(1-.12*leave,1-.12*leave)
    alpha=intro*(1-leave)
    turn=min(t,1.75)*.14 + settle*.28
    rx=.85+settle*.12;rz=-.58+turn
    sx,cx=math.sin(rx),math.cos(rx);sz,cz=math.sin(rz),math.cos(rz)
    output=[]
    for theta,phi,meridian in CURVES:
        dis=(1-settle)
        radius=205+dis*28*np.sin(3*theta+phi*2)
        tube=83+dis*18*np.cos(2*theta-phi)
        x=(radius+tube*np.cos(phi))*np.cos(theta)
        y=(radius+tube*np.cos(phi))*np.sin(theta)
        z=tube*np.sin(phi)+dis*65*np.sin(2*theta+phi*3)
        y,z=y*cx-z*sx,y*sx+z*cx
        x,y=x*cz-y*sz,x*sz+y*cz
        # Perspective keeps the foreground lines perceptibly larger.
        q=1050/(1050-z)
        output.append((float(np.mean(z)),x*q,y*q,z,meridian))
    for depth,x,y,z,meridian in sorted(output,key=lambda q:q[0]):
        depth_a=.28+.72*clamp((depth+260)/520)
        col=p.ink if INVERTED else mixc(p.paper,p.acid,.40)
        if meridian: col=p.ink if INVERTED else p.acid
        line(c,list(zip(x,y)),col,.95 if meridian else 1.5,alpha*depth_a*(.42 if meridian else .86))
    # Fine registration marks make the abstract object feel deliberately made.
    a=alpha*P(t,.35,.8)
    for x,y in [(-345,0),(345,0),(0,-322),(0,322)]:
        line(c,[(x-5,y),(x+5,y)],text_col(t,p),1,a*.55)
        line(c,[(x,y-5),(x,y+5)],text_col(t,p),1,a*.55)


def halo(c,t,p):
    art(c)
    # A single orbit draws out of the resolved surface, then locks in place.
    u=P(t,2.55,3.35,eio);a=u*(1-ease(t,4.2,4.5))
    c.save();c.rotate(-.28)
    c.scale(1,.78)
    c.arc(0,0,346,-1.6,-1.6+math.tau*u)
    stroke(c,p.ink,1.2,a*.5)
    for ang in (-1.6,.5,2.6):
        x,y=346*math.cos(ang),346*math.sin(ang)
        c.arc(x,y,6,0,math.tau);fill(c,p.ink,a)
        c.arc(x,y,13,0,math.tau);stroke(c,p.ink,1,a*.6)
    c.restore()

# Each plane, its headline, the selection overlay and each track are separate
# editor layers. Their motion shares an analytic transform, never a baked image.
def plane_ctx(c,t):
    art(c)
    u=P(t,4.53,5.18,eo);end=ease(t,7.23,7.60)
    c.translate(0,70*(1-u)-70*end)
    c.rotate(math.radians(lerp(13,-7,u)+7*end))
    c.scale(.86+.14*u,.86+.14*u)

def plane(c,t,p,index):
    u=P(t,4.6+index*.09,5.2+index*.09,eo)
    shift=(2-index)*42*u
    x=-292+shift;y=-254-shift
    col=p.acid if index==0 else (mixc(p.ink,p.paper,.15) if index==1 else p.paper)
    rect(c,x,y,584,420,col,14)
    rrect(c,x,y,584,420,14);stroke(c,p.paper,1,.16 if index<2 else .5)
    if index<2:
        # Exposed edges are real separate cards, with fine etched rules.
        line(c,[(x+28,y+382),(x+556,y+382)],p.paper,1,.35)

def plane_0(c,t,p):plane(c,t,p,0)
def plane_1(c,t,p):plane(c,t,p,1)
def plane_2(c,t,p):plane(c,t,p,2)

def poster_label(c,t,p):
    text(c,p.poster_label,-250,-200,13,'med',p.ink,track=.12,maxw=490)

def poster_headline(c,t,p):
    # Two lines with optical, not mathematical, spacing.
    text(c,p.poster_line1,-250,-83,65,'semi',p.ink,track=-.055,maxw=496)
    text(c,p.poster_line2,-250,-9,65,'semi',p.ink,track=-.055,maxw=496)

def poster_graphic(c,t,p):
    u=P(t,5.08,5.75,eio)
    for i in range(13):
        x=-250+i*39.5
        height=24+30*math.sin(i*.31+.2)**2
        rect(c,x,77-height,23,height*u,p.ink,2)
    line(c,[(-250,102),(250,102)],p.ink,1,.20)

def selection(c,t,p):
    a=window(t,5.55,5.88,7.10,7.38)
    rect(c,-263,-145,526,156,p.acid,0,a*.12)
    c.rectangle(-263,-145,526,156);stroke(c,p.ink,1.4,a*.70)
    for x in (-263,263):
        for y in (-145,11):
            rect(c,x-4,y-4,8,8,p.ink,1,a)
    # Small original pointer; its final click is paired with a linked cue.
    x=lerp(330,210,P(t,5.6,6.05,eio));y=lerp(90,-6,P(t,5.6,6.05,eio))
    c.move_to(x,y);c.line_to(x+4,y+29);c.line_to(x+12,y+20);c.line_to(x+22,y+21);c.close_path();fillp(c,p.ink,a);stroke(c,p.paper,1.6,a)

def track(c,t,p,index):
    art(c)
    u=P(t,5.03+index*.12,5.58+index*.12,eo);a=u*(1-ease(t,7.2,7.5))
    y=245+index*43+25*(1-u);x=-290
    label=(p.type_label,p.motion_label,p.audio_label)[index]
    text(c,label,x,y+18,13,'med',p.paper,a*.6,maxw=100)
    x=-170;w=456
    rect(c,x,y,w,27,mixc(p.ink,p.paper,.08),5,a)
    if index==2:
        for i in range(62):
            h=(.2+.8*abs(math.sin(i*.63)*math.cos(i*.21)))*17
            line(c,[(x+10+i*7,y+13-h/2),(x+10+i*7,y+13+h/2)],p.acid,2,a*.75)
    else:
        for i,(off,width) in enumerate(((0,135),(141,180),(327,129))):
            rect(c,x+off,y,width*u,27,p.acid if index==0 else p.paper,5,a*(.9 if index==0 else .35))
    playx=-170+456*P(t,5.2,7.1,lin)
    line(c,[(playx,y-3),(playx,y+30)],p.paper,1,a*.9)

def typography_track(c,t,p):track(c,t,p,0)
def motion_track(c,t,p):track(c,t,p,1)
def sound_track(c,t,p):track(c,t,p,2)


def signature(c,t,p):
    u=P(t,7.63,8.26,eo)
    if PORTRAIT:
        x=CX; y=Y+CH*.20;size=min(114,CW*.145)
        text(c,p.brand,x,y+35*(1-u),size,'semi',p.paper,u,align='c',track=-.06,maxw=CW)
        text(c,p.end_line1,x,y+120,40,'reg',p.paper,u,align='c',track=-.03,maxw=CW)
        text(c,p.end_line2,x,y+172,40,'reg',p.paper,u,align='c',track=-.03,maxw=CW)
    else:
        text(c,p.brand,TX,TY-28+55*(1-u),128,'semi',p.paper,u,track=-.06,maxw=SW)
        text(c,p.end_line1,TX,TY+66,47,'reg',p.paper,u,track=-.03,maxw=SW)
        text(c,p.end_line2,TX,TY+124,47,'reg',p.paper,u,track=-.03,maxw=SW)

def signature_note(c,t,p):
    u=P(t,8.15,8.7)
    if PORTRAIT: text(c,p.end_note,CX,Y+CH*.887,17,'med',p.acid,u,align='c',track=.10,maxw=CW)
    else:text(c,p.end_note,TX,SY+120,17,'med',p.acid,u,track=.10,maxw=SW)

def monogram(c,t,p):
    art(c)
    u=P(t,7.48,8.24,eo);a=u
    # The three planes resolve into a sculptural open-source signature.
    c.translate(0,-15 if PORTRAIT else 0)
    for i in range(3):
        y=(i-1)*76
        spread=1+.08*(1-u);ww=288*spread;hh=135*spread
        pts=[(-ww,y),(0,y-hh),(ww,y),(0,y+hh),(-ww,y)]
        line(c,pts,p.acid if i==0 else p.paper,2.5,a*(1-i*.24))
    # A short glint, then complete stillness for the final 1.2 seconds.
    q=window(t,8.05,8.25,8.55,8.85)
    line(c,[(-288,-76),(0,-211)],p.acid,5,q)


def card_visibility(fn):
    def draw_card(c,t,p):
        a=P(t,4.5,4.83)*(1-ease(t,7.22,7.62))
        if a<.001:return
        c.push_group();fn(c,t,p);c.pop_group_to_source();c.paint_with_alpha(a)
    return draw_card

# The fade is shared so card surfaces and their editable contents stay together.
plane_0,plane_1,plane_2,poster_label,poster_headline,poster_graphic,selection = [
    card_visibility(fn) for fn in (plane_0,plane_1,plane_2,poster_label,poster_headline,poster_graphic,selection)]

def title_box(t):return (TX,TY-TS,SW,TS*1.15)
def support_box(t):return (TX,SY-42,SW,55)
def art_box(t):return (AX-380*AS,AY-380*AS,760*AS,760*AS)
def signature_box(t):
    return (X,Y+CH*.20-130,CW,320) if PORTRAIT else (TX,TY-156,SW,296)
def note_box(t):
    return (X,Y+CH*.887-26,CW,36) if PORTRAIT else (TX,SY+98,SW,32)
def track_box(i):return lambda t:(AX-300*AS,AY+(240+i*43)*AS,600*AS,40*AS)

LAYERS=[
    Layer('paper','Ink / citron sweep',bg,(0,0,W,H),0,10,group='Stage',params=['ink','acid']),
    Layer('grid','Fine grid',grid,(0,0,W,H),0,10,group='Stage',params=['paper']),
    Layer('brand','Brand signature',brand,lambda t:(X,HY-28,CW,55),0,10,group='Identity',params=['brand','edition']),
    Layer('footer','Footer / progress',footer,lambda t:(X,FY-36,CW,50),0,10,group='Identity',params=['footer']),
    Layer('hook','Complex.',opener,title_box,0,2.25,group='01 / Complexity',params=['hook','paper']),
    Layer('hook_support','Opening support',opener_support,support_box,0,2.25,group='01 / Complexity',params=['hook_body']),
    Layer('clear','Clear.',clearer,title_box,2.25,4.5,group='02 / Clarity',params=['clear']),
    Layer('clear_support','Clarity support',clearer_support,support_box,2.25,4.5,group='02 / Clarity',params=['clear_body']),
    Layer('surface','Ribbon sculpture',surface,art_box,0,4.65,group='01 / Complexity',params=['paper','acid']),
    Layer('orbit','Resolved orbit',halo,art_box,2.5,4.5,group='02 / Clarity',params=['ink']),
    Layer('yours','Yours.',ownership,title_box,4.5,7.6,group='03 / Ownership',params=['yours']),
    Layer('yours_support','Ownership support',ownership_support,support_box,4.5,7.6,group='03 / Ownership',params=['yours_body']),
    Layer('back_plane','Citron plane',plane_0,lambda t:(-292+84*P(t,4.6,5.2),-254-84*P(t,4.6,5.2),584,420),4.5,7.6,group='03 / Ownership',params=['acid'],motion=plane_ctx),
    Layer('mid_plane','Middle plane',plane_1,lambda t:(-292+42*P(t,4.69,5.29),-254-42*P(t,4.69,5.29),584,420),4.5,7.6,group='03 / Ownership',params=['ink'],motion=plane_ctx),
    Layer('front_plane','Ivory poster',plane_2,(-292,-254,584,420),4.5,7.6,group='03 / Ownership',params=['paper'],motion=plane_ctx,children=[
        Layer('poster_label','Poster label',poster_label,(-250,-215,490,24),4.5,7.6,group='03 / Ownership',params=['poster_label']),
        Layer('poster_headline','Poster typography',poster_headline,(-250,-137,496,140),4.5,7.6,group='03 / Ownership',params=['poster_line1','poster_line2']),
        Layer('poster_graphic','Signal rhythm',poster_graphic,(-250,20,500,85),4.5,7.6,group='03 / Ownership',params=['ink']),
        Layer('selection','Selection / pointer',selection,(-269,-151,606,180),5.5,7.5,group='03 / Ownership',params=['acid']),
    ]),
    Layer('type_track','Typography track',typography_track,track_box(0),5,7.5,group='03 / Ownership',params=['type_label']),
    Layer('motion_track','Motion track',motion_track,track_box(1),5,7.5,group='03 / Ownership',params=['motion_label']),
    Layer('sound_track','Sound track',sound_track,track_box(2),5,7.5,group='03 / Ownership',params=['audio_label']),
    Layer('signature','DX Studio / closing',signature,signature_box,7.6,10,group='04 / Signature',params=['brand','end_line1','end_line2']),
    Layer('signature_note','Open source',signature_note,note_box,7.6,10,group='04 / Signature',params=['end_note']),
    Layer('monogram','Three open planes',monogram,art_box,7.6,10,group='04 / Signature',params=['acid','paper']),
    Layer('captions','Optional captions',optional_captions,lambda t:CAPTION_BOX,0,10,group='Captions',params=['__captions'],alive=lambda t:bool(CAPS)),
]

def draw(c,t,p):
    global INVERTED
    render_layers(c,t,p,LAYERS[:1])
    # Exact moving-matte inversion: fine lines and type switch colour only
    # where the citron wipe has reached them, without a muddy crossfade.
    v=ease(t,2.08,2.48)
    rx,ry,rw,rh=W*(1-v),0,W*v,H*(1-ease(t,4.30,4.65))
    if t>=4.65:rw=0
    for inverse in (False,True):
        if inverse and rw*rh<.01:continue
        c.save();c.new_path()
        if not inverse:c.rectangle(0,0,W,H)
        c.rectangle(rx,ry,rw,rh)
        c.set_fill_rule(cairo.FILL_RULE_EVEN_ODD);c.clip();c.set_fill_rule(cairo.FILL_RULE_WINDING)
        INVERTED=inverse
        render_layers(c,t,p,LAYERS[1:]);c.restore()
    INVERTED=False
def cues(p):
    return [dict(sound='tap',at=.12,gain=.22,layer='hook'),
            dict(sound='slide',at=2.08,gain=.23,layer='paper'),
            dict(sound='tick',at=2.67,gain=.24,layer='orbit'),
            dict(sound='slide',at=4.3,gain=.18,layer='paper'),
            *[dict(sound='tap',at=4.72+i*.09,gain=.17,layer=lid) for i,lid in enumerate(('back_plane','mid_plane','front_plane'))],
            dict(sound='click',at=6.05,gain=.17,layer='selection'),
            dict(sound='paper',at=7.62,gain=.14,layer='monogram')]
