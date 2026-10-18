import copy
import json
import math
from pathlib import Path
from zipfile import ZipFile
import numpy as np
import pytest
from dx_studio.composition import layout_for, PRESENTER_PRESETS
from dx_studio.project import Project
from dx_studio.scaffold import create
from dx_studio.bundle import pack


def overlaps(a,b):
    return max(a[0],b[0]) < min(a[2],b[2]) and max(a[1],b[1]) < min(a[3],b[3])


@pytest.mark.parametrize('size',[(1920,1080),(1080,1920),(640,360)])
@pytest.mark.parametrize('preset',list(PRESENTER_PRESETS))
def test_layout_rectangles_are_inside_frame_and_clear_of_presenter(size,preset):
    w,h=size;layout=layout_for(w,h,preset)
    for key in ('content','captions','presenter'):
        r=layout[key]
        if r:
            assert 0 <= r[0] < r[2] <= w
            assert 0 <= r[1] < r[3] <= h
    assert not overlaps(layout['content'],layout['captions'])
    if layout['presenter']:
        assert not overlaps(layout['content'],layout['presenter'])
        assert not overlaps(layout['captions'],layout['presenter'])


@pytest.mark.parametrize('ratio',['16:9','9:16'])
@pytest.mark.parametrize('template',['explainer','starter'])
@pytest.mark.parametrize('preset',[x for x in PRESENTER_PRESETS if x!='none'])
def test_templates_keep_presenter_pixels_clear_at_every_beat(tmp_path,ratio,template,preset):
    pr=Project(create(tmp_path/'video',template=template,format=ratio,presenter=preset))
    assert pr.composition_supported
    x0,y0,x1,y1=pr.layout['presenter'];scale=.2
    expected=np.array([237,243,245],dtype=np.uint8)  # Cairo's BGR storage for #F5F3ED.
    for t in (0,1,5,9,13,pr.duration-.01):
        if t >= pr.duration: continue
        surface=pr.render(t,scale)
        pixels=np.frombuffer(surface.get_data(),np.uint8).reshape(surface.get_height(),surface.get_stride()//4,4)
        zone=pixels[math.ceil(y0*scale)+2:math.floor(y1*scale)-2,math.ceil(x0*scale)+2:math.floor(x1*scale)-2,:3]
        assert np.all(zone==expected),(ratio,template,preset,t)
        for hit in pr.hits(t):
            if hit['id']=='background': continue
            points=hit['corners']
            bounds=[min(x[0] for x in points),min(x[1] for x in points),max(x[0] for x in points),max(x[1] for x in points)]
            assert not overlaps(bounds,pr.layout['presenter']),(hit['id'],preset,t)


def test_editor_preference_reflows_without_losing_edits_and_survives_bundle(tmp_path):
    folder=create(tmp_path/'video',format='16:9')
    pr=Project(folder);before=pr.hits(1)
    values=copy.deepcopy(pr.values);values['title']='My custom title';values['__composition']='left-half'
    values['__layers']['row1']['visible']=False
    pr.apply(values);pr.save_settings()
    assert pr.layout['content'][0]>pr.width/2
    assert pr.params.title=='My custom title' and not pr.values['__layers']['row1']['visible']
    assert before!=pr.hits(1)
    saved=Project(folder)
    assert saved.layout==pr.layout
    archive=pack(folder,tmp_path/'video.zip')
    with ZipFile(archive) as z:
        assert json.loads(z.read('project/settings.json'))['__composition']=='left-half'
        assert 'engine/dx_studio/composition.py' in z.namelist()


def test_bad_preset_is_rejected_without_overwriting_current_state(tmp_path):
    pr=Project(create(tmp_path/'video'));before=pr.values
    values=copy.deepcopy(before);values['__composition']='unknown'
    with pytest.raises(ValueError): pr.apply(values)
    assert pr.values is before
    with pytest.raises(ValueError): create(tmp_path/'bad',presenter='unknown')
    assert not (tmp_path/'bad').exists()


def test_invalid_safe_area_is_rejected():
    with pytest.raises(ValueError):layout_for(1920,1080,'none',{'content':[-5,0,1920,1080]})


def test_portrait_defaults_are_centred_and_presenter_halves_mirror():
    for w,h in [(1080,1920),(720,1280)]:
        for preset in ['none','bottom-left','bottom-right','bottom-band']:
            layout=layout_for(w,h,preset)
            for key in ['content','captions']:
                assert (layout[key][0]+layout[key][2])/2==pytest.approx(w/2)
        left=layout_for(w,h,'left-half');right=layout_for(w,h,'right-half')
        for key in ['content','captions']:
            assert left[key][0]==pytest.approx(w-right[key][2])
            assert left[key][2]==pytest.approx(w-right[key][0])
    custom={'content':[80,170,900,1560],'captions':[80,1370,900,1550]}
    layout=layout_for(1080,1920,safe_area=custom)
    assert layout['content'][::2]==[80,900] and layout['captions']==custom['captions']


def test_new_portrait_templates_centre_layer_groups_at_each_beat(tmp_path):
    for template in ['explainer','starter']:
        pr=Project(create(tmp_path/template,template=template,format='9:16'))
        assert pr.layout['content'][0]==pr.width-pr.layout['content'][2]==130
        assert pr.layout['captions'][0]==pr.width-pr.layout['captions'][2]==130
        for t in [1,5,9,13]:
            if t>=pr.duration:continue
            groups={'title','problem','payoff','closing','card','row1','row2','row3','note','captions'}
            hits=[hit for hit in pr.hits(t) if hit['id'] in groups]
            assert hits
            assert all(hit['center'][0]==pytest.approx(pr.width/2) for hit in hits)
            pr.render(t,.1)  # selection and render share the same responsive geometry


def test_overlap_check_catches_manual_moves_into_presenter_area(tmp_path):
    from dx_studio.composition import presenter_collisions
    pr=Project(create(tmp_path/'video',format='16:9',presenter='left-half'))
    assert presenter_collisions(pr,[1,5,9,13])==[]
    pr.values['__layers']['title']['x']=-1000
    pr.apply(pr.values)
    assert 'title' in presenter_collisions(pr,[1])


def test_caption_font_size_keeps_wrapped_block_in_reserved_band(tmp_path):
    pr=Project(create(tmp_path/'video',format='16:9',presenter='left-half'))
    pr.values['caption_size']=80
    pr.values['__captions'][0]['text']='Words visuals and timing should stay clear of the talking head.'
    pr.apply(pr.values)
    s=pr.render(1,.2)
    px=np.frombuffer(s.get_data(),np.uint8).reshape(s.get_height(),s.get_stride()//4,4)
    x0,y0,x1,y1=pr.layout['presenter']
    region=px[2:int(y1*.2)-2,2:int(x1*.2)-2,:3]
    assert np.all(region==np.array([237,243,245],dtype=np.uint8))


def test_short_music_export_keeps_its_length_when_fade_is_longer():
    from dx_studio.audio import fade_in, SR
    signal=np.ones(SR)
    faded=fade_in(signal,1500)
    assert len(faded)==SR
    assert faded[0]==0 and faded[-1]==1
    assert np.all(signal==1)
