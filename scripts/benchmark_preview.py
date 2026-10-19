"""Measure cold/warm scrubbing in a ten-minute synthetic editing project.

No full-length render or real-time playback claim is made. All fixture media is
generated locally, including a test tone standing in for recorded narration.
"""
import argparse
import json
import statistics
import subprocess
import tempfile
import time
from pathlib import Path
from dx_studio.scaffold import create
from dx_studio.editor import Editor

SCENE='''from dx_studio import *
import json
from pathlib import Path
CFG=json.loads(Path(__file__).with_name('project.json').read_text())
W,H=CFG['width'],CFG['height']
AREA=(100,100,W-100,H-100)
RESPONSIVE_COMPOSITION=True
COMPOSITION_EXEMPT_LAYERS={'background'}
SCHEMA=[{'key':'title','type':'text','label':'Headline','default':'Explain one idea at a time.'}]
def setup(p,project):
 global AREA
 AREA=project.layout['content']
def background(c,t,p):
 c.set_source_rgb(.95,.95,.97);c.paint()
def box(index):
 x0,y0,x1,y1=AREA
 col=index%4;row=index//4
 w=(x1-x0)/4-16;h=(y1-y0-130)/5-16
 return x0+col*(w+16),y0+110+row*(h+16),w,h
def title(c,t,p):
 x0,y0,x1,y1=AREA
 text(c,p.title,(x0+x1)/2,y0+48,44,'bold',hexc('#252333'),align='c',maxw=x1-x0)
def draw_card(index):
 def draw(c,t,p):
  x,y,w,h=box(index);rrect(c,x,y,w,h,14);fill(c,hexc('#5056F4'),.15+.04*(index%5))
  text(c,str(index+1),x+w/2,y+h/2,28,'bold',hexc('#352AA5'),align='c')
 return draw
LAYERS=[Layer('background','Background',background,(0,0,W,H),locked=True)]
for scene in range(30):
 a,b=scene*20,(scene+1)*20
 LAYERS.append(Layer('headline_'+str(scene),'Headline '+str(scene+1),title,lambda t:(AREA[0],AREA[1],AREA[2]-AREA[0],90),a,b,params=['title']))
 for index in range(20):
  LAYERS.append(Layer('card_'+str(scene)+'_'+str(index),'Card '+str(index+1),draw_card(index),lambda t,i=index:box(i),a,b))
def draw(c,t,p):render_layers(c,t,p,LAYERS)
'''


def fixture(folder,ratio='16:9'):
    folder=create(folder,template='starter',format=ratio)
    cfg=json.loads((folder/'project.json').read_text());cfg.update(duration=600,chapters=[[i*20,(i+1)*20,'Scene '+str(i+1)] for i in range(30)])
    (folder/'project.json').write_text(json.dumps(cfg));(folder/'scene.py').write_text(SCENE)
    (folder/'captions.json').write_text(json.dumps([{'start':i*3,'end':i*3+2.5,'show_end':i*3+2.5,'text':'An editable caption for the next idea.'} for i in range(200)]))
    video=folder/'assets/test-pattern.mp4'
    subprocess.run(['ffmpeg','-v','error','-y','-f','lavfi','-i','testsrc2=size=320x180:rate=30:duration=2','-c:v','libx264','-pix_fmt','yuv420p',str(video)],check=True)
    import numpy as np
    import soundfile as sf
    sf.write(folder/'assets/test-tone.wav',.05*np.sin(2*np.pi*440*np.arange(48000*2)/48000),48000)
    editor=Editor(folder);values=editor.pr.values
    item=editor.pr.media.item_for('test-pattern.mp4',0);item.update(t0=0,dur=600,loop=True,box=[100,100,160,90],muted=True)
    values['__media'].append(item)
    values['__voice']=[{'id':'voice_'+str(i),'name':'Synthetic test tone '+str(i+1),'file':'assets/test-tone.wav','start':i*10,'offset':0,'duration':2,'gain':1,'duck':'none','muted':False} for i in range(60)]
    editor.pr.apply(values);editor.pr.save_settings()
    return editor


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--output',required=True);ap.add_argument('--frames',type=int,default=24);ap.add_argument('--project',help='Keep the generated project in a new folder');args=ap.parse_args()
    if not 4<=args.frames<=100:ap.error('Choose 4–100 sample frames')
    with tempfile.TemporaryDirectory(prefix='dx-benchmark-') as work:
        editor=fixture(Path(args.project) if args.project else Path(work)/'project')
        times=[i*(600-1/30)/(args.frames-1) for i in range(args.frames)]
        cold=[];warm=[]
        for dest in (cold,warm):
            for t in times:
                start=time.perf_counter();editor.frame(t,.25);dest.append((time.perf_counter()-start)*1000)
        from dx_studio.doctor import report
        result={'fixture':{'seconds':600,'declared_scene_layers':len(editor.pr.layer_meta),'caption_cues':200,'voice_takes':60,'looping_video':True,'samples':args.frames,'preview_scale':.25},'environment':report(),'cold_median_ms':round(statistics.median(cold),2),'cold_max_ms':round(max(cold),2),'warm_median_ms':round(statistics.median(warm),2),'cache_hits':editor.preview_cache.hits,'cache_bytes':editor.preview_cache.bytes,'scope':'Sampled scrub frames and repeated-frame cache reuse. Synthetic sources; no full-length export or real-time playback guarantee.'}
        Path(args.output).write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))

if __name__=='__main__':main()
