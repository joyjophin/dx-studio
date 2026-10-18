import copy
import json
from pathlib import Path
import shutil
import subprocess
import pytest
from dx_studio.motion import bezier, BUILTINS, MotionLibrary, capture, prepare, validate_style
from dx_studio.layers import transform_at
from dx_studio.project import Project
from dx_studio.scaffold import create


def test_bezier_matches_browser_and_bounds_animated_scale_opacity():
    points=[.15,1.4,.75,-.2]
    samples=[0,.001,.1,.25,.5,.8,.999,1]
    expected=[bezier(t,points) for t in samples]
    node=shutil.which('node')
    if node:
        script="const fs=require('fs'),vm=require('vm');vm.runInThisContext(fs.readFileSync('dx_studio/editor-motion.js','utf8'));console.log(JSON.stringify("+json.dumps(samples)+".map(t=>DXMotion.bezier(t,"+json.dumps(points)+"))));"
        actual=json.loads(subprocess.check_output([node,'-e',script],cwd=Path(__file__).resolve().parents[1],text=True))
        assert actual==pytest.approx(expected,abs=1e-12)
    for t in samples:assert bezier(t,[0,0,1,1])==pytest.approx(t,abs=1e-8)
    a=dict(t=0,x=0,y=0,scale=1,rotation=0,opacity=1)
    b=dict(t=1,x=100,y=0,scale=.01,rotation=0,opacity=0,ease='custom',bezier=[.1,3,.2,3])
    result=transform_at({'keys':[a,b]},.5)
    assert result['x']>100 and result['scale']>0 and 0<=result['opacity']<=1


def test_motion_keeps_placement_windows_and_original_values_with_stagger(tmp_path):
    pr=Project(create(tmp_path/'video'))
    values=copy.deepcopy(pr.values);values['__layers']['title'].update(x=140,y=30,scale=1.4)
    before=copy.deepcopy(values)
    result=prepare(pr,values,BUILTINS[1],['title','problem'],.6,.15)
    title=result['states']['title'];problem=result['states']['problem']
    assert values==before
    assert title['x']==140 and title['scale']==1.4 and title['keys'][0]['x']==60
    assert title['keys'][-1]['x']==140 and title['keys'][-1]['scale']==1.4
    for identifier,state in result['states'].items():
        assert (state['start'],state['end'])==(before['__layers'][identifier]['start'],before['__layers'][identifier]['end'])
    assert problem['keys'][0]['t']==.15
    calm=prepare(pr,values,BUILTINS[1],['title'],.6,calm=True)['states']['title']
    assert all(k['x']==140 and k['y']==30 and k['scale']==1.4 for k in calm['keys'])
    assert calm['keys'][0]['opacity']==0 and calm['keys'][-1]['opacity']==1
    values['__layers']['problem']['locked']=True
    assert prepare(pr,values,BUILTINS[0],['title','problem'],.6)['skipped']==['problem']
    with pytest.raises(ValueError,match='fit each'):prepare(pr,values,BUILTINS[0],['title'],9)


def test_capture_library_portability_and_custom_curve_render_roundtrip(tmp_path):
    pr=Project(create(tmp_path/'video'));values=copy.deepcopy(pr.values)
    state=prepare(pr,values,BUILTINS[0],['title'],1)['states']['title']
    state['keys'][-1].update(ease='custom',bezier=[.42,0,1,1])
    style=capture('My reveal',state);assert style['keys'][-1]['bezier']==[.42,0,1,1]
    library=MotionLibrary(tmp_path/'library'/'motion.json');saved=library.save(style)
    assert library.get(saved['id'])==saved
    assert validate_style(json.loads(json.dumps(saved)))==style
    with pytest.raises(ValueError,match='unique'):library.save(style)
    with pytest.raises(ValueError,match='Included'):library.delete('rise')
    values['__layers']['title']=state;pr.apply(values);pr.save_settings()
    surface=pr.render(.5,.2);pixels=bytes(surface.get_data())
    reopened=Project(pr.path);surface=reopened.render(.5,.2)
    assert bytes(surface.get_data())==pixels
    assert reopened.hits(.5)==pr.hits(.5)
    library.delete(saved['id']);assert all(s['id']!=saved['id'] for s in library.list())


def test_invalid_curve_is_rejected_before_project_changes_and_entrance_delay_works(tmp_path):
    pr=Project(create(tmp_path/'video'));before=pr.values;values=copy.deepcopy(before)
    state=values['__layers']['title'];state.update(enter='fade',enter_delay=.4,enter_dur=.4)
    pr.apply(values)
    assert 'title' not in {h['id'] for h in pr.hits(.2)}
    assert 'title' in {h['id'] for h in pr.hits(.6)}
    broken=copy.deepcopy(values);broken['__layers']['title']['keys']=[dict(t=1,ease='custom',bezier=[2,0,1,1])]
    with pytest.raises(ValueError,match='Bezier'):pr.apply(broken)
    assert pr.values is values
