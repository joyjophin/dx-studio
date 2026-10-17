import copy
import json
from pathlib import Path
from zipfile import ZipFile
import pytest
from dx_studio.project import Project
from dx_studio.scaffold import create
from dx_studio.bundle import pack
from dx_studio.voice import VoiceTimes
from dx_studio.timemap import scene_time, out_duration

def pixels(surface): return bytes(surface.get_data())

@pytest.mark.parametrize('ratio,size',[('9:16',(1080,1920)),('16:9',(1920,1080))])
@pytest.mark.parametrize('template',['starter','explainer'])
def test_templates_render_in_arbitrary_order(tmp_path,ratio,size,template):
    p=Project(create(tmp_path/'demo',template,ratio))
    assert (p.width,p.height)==size
    a=pixels(p.render(1,.1))
    p.render(p.duration-.01,.1);p.render(0,.1)
    assert pixels(p.render(1,.1))==a
    assert p.hits(1)

def test_saved_edits_survive_reopen_and_bundle(tmp_path):
    folder=create(tmp_path/'demo')
    p=Project(folder); p.values['title']='A changed title'
    p.values['__layers']['row1'].update(visible=False,x=123,scale=1.4)
    p.values['__captions'][0]['text']='Changed caption'
    p.apply(p.values);p.save_settings()
    loaded=Project(folder)
    assert loaded.params.title=='A changed title'
    assert not loaded.values['__layers']['row1']['visible']
    assert loaded.captions[0]['text']=='Changed caption'
    (folder/'.env').write_text('secret')
    (folder/'video.mp4').write_bytes(b'not the source')
    archive=pack(folder,tmp_path/'demo.zip')
    with ZipFile(archive) as z:
        assert 'project/settings.json' in z.namelist()
        assert 'engine/dx_studio/editor.html' in z.namelist()
        assert 'engine/LICENSE' in z.namelist()
        assert 'engine/dx_studio/fonts/OFL.txt' in z.namelist()
        assert 'project/.env' not in z.namelist()
        assert 'project/video.mp4' not in z.namelist()
        z.extractall(tmp_path/'unpacked')
    q=Project(tmp_path/'unpacked/project')
    assert pixels(q.render(1,.1))==pixels(loaded.render(1,.1))

def test_new_scene_defaults_merge_with_user_edits(tmp_path):
    folder=create(tmp_path/'demo',template='starter');p=Project(folder)
    p.values['__layers']['title']['x']=42;p.save_settings()
    cfg=json.loads((folder/'project.json').read_text());cfg['brand']={'bg':'#FFFFFF'}
    (folder/'project.json').write_text(json.dumps(cfg))
    q=Project(folder)
    assert q.values['__layers']['title']['x']==42
    assert q.values['bg']=='#FFFFFF'
    assert q.values['__layers']['background']['visible']

def test_hidden_and_transparent_layers_are_not_selectable(tmp_path):
    p=Project(create(tmp_path/'demo'))
    p.values['__layers']['row1']['visible']=False
    p.values['__layers']['row2']['opacity']=0
    p.apply(p.values)
    ids={hit['id'] for hit in p.hits(1)}
    assert 'row1' not in ids and 'row2' not in ids and 'row3' in ids

def test_cues_move_and_hide_with_their_layer(tmp_path):
    p=Project(create(tmp_path/'demo'))
    p.values['__layers']['payoff']['start']=9
    p.apply(p.values)
    assert next(c for c in p.cues() if c['sound']=='chime')['at']==9
    p.values['__layers']['payoff']['visible']=False
    assert not any(c['sound']=='chime' for c in p.cues())

def test_word_lookup_fails_loudly_and_occurrence_is_explicit(tmp_path):
    (tmp_path/'project.json').write_text(json.dumps({'voice':[{'text':'go then go','start':1,'dur':3}]}))
    vt=VoiceTimes(tmp_path)
    assert vt.word(0,'go',1)>vt.word(0,'go',0)
    with pytest.raises(ValueError): vt.word(0,'absent')
    with pytest.raises(ValueError): vt.word(0,'go',2)

@pytest.mark.parametrize('field,value',[('width',0),('height',17),('fps',0),('duration',0),('duration',float('nan')),('scene','../outside.py'),('format_version',99)])
def test_invalid_project_is_rejected_before_scene_load(tmp_path,field,value):
    folder=create(tmp_path/'demo')
    cfg=json.loads((folder/'project.json').read_text());cfg[field]=value
    (folder/'project.json').write_text(json.dumps(cfg))
    with pytest.raises(ValueError): Project(folder)

def test_brand_file_and_destination_safety(tmp_path):
    brand=tmp_path/'brand.json';brand.write_text('{"accent":"#112233"}')
    folder=create(tmp_path/'demo',brand=brand)
    assert Project(folder).values['accent']=='#112233'
    with pytest.raises(ValueError):create(folder)
    with pytest.raises(ValueError):create(tmp_path/'bad',template='../outside')

def test_paths_cannot_escape_assets(tmp_path):
    from dx_studio.paths import contained
    with pytest.raises(ValueError):contained(tmp_path,'../secrets')
    outside=tmp_path.parent/'outside-secret';outside.write_text('secret')
    (tmp_path/'link').symlink_to(outside)
    with pytest.raises(ValueError):contained(tmp_path,'link')

def test_ripple_hold_and_delete():
    edits=[{'op':'insert','at':2,'dur':1},{'op':'delete','start':5,'end':6}]
    assert out_duration(10,edits)==10
    assert scene_time(2.5,edits)==2
    assert scene_time(6,edits)==6

def test_audio_mix_is_repeatable(tmp_path):
    import numpy as np
    import soundfile as sf
    from dx_studio.audio import build_mix
    p=Project(create(tmp_path/'demo'))
    # Avoid a music-bed performance test; this still exercises random SFX.
    p.cfg.pop('music')
    build_mix(p,str(tmp_path/'a.wav'));build_mix(p,str(tmp_path/'b.wav'))
    a,_=sf.read(tmp_path/'a.wav');b,_=sf.read(tmp_path/'b.wav')
    assert np.array_equal(a,b)


def test_group_retime_moves_children_and_their_sounds(tmp_path):
    from dx_studio.layers import Layer, render_layers
    folder=create(tmp_path/'demo',template='starter')
    p=Project(folder)
    calls=[]
    def draw_child(c,t,params): calls.append(t)
    child=Layer('child','Child',draw_child,(10,10,30,30),1,3)
    parent=Layer('parent','Group',None,(0,0,100,100),0,4,children=[child])
    from dx_studio.layers import defaults_for, meta_for
    p.layers=[parent];p.layer_meta=meta_for(p.layers,5)
    p.defaults['__layers']=defaults_for(p.layers,5)
    p.values['__layers']=copy.deepcopy(p.defaults['__layers'])
    p.values['__layers']['parent']['start']=1
    from dx_studio.schema import Params
    p.params=Params(p.schema,p.values)
    from dx_studio import cairo
    c=cairo.Context(cairo.ImageSurface(cairo.FORMAT_RGB24,100,100))
    render_layers(c,2.5,p.params,p.layers)
    assert calls==[1.5]
    p.scene.cues=lambda params:[dict(sound='tap',at=1.5,layer='child')]
    assert p.cues()[0]['at']==2.5


def test_hit_outline_follows_entrance_and_user_scale(tmp_path):
    p=Project(create(tmp_path/'demo',template='starter'))
    state=p.values['__layers']['title']
    state.update(scale=1.4,x=20,enter='slide-up',enter_dur=1)
    hits=p.hits(.5)
    title=next(x for x in hits if x['id']=='title')
    x0,y0,x1,y1=p.layout['content']
    assert title['center'][0]==pytest.approx((x0+x1)/2+20)
    assert title['center'][1]>(y0+y1)/2-30
    assert title['corners'][1][0]-title['corners'][0][0]==pytest.approx((x1-x0)*1.4)
