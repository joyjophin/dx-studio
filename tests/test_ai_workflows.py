"""Important invariants for AI handoffs and source reloads: saved work survives."""
import copy
import json
from pathlib import Path
import pytest
from dx_studio.editor import Editor
from dx_studio.scaffold import create
from dx_studio.history import SaveConflict
from dx_studio.handoff import export


def editor(tmp_path,**kwargs):
    ed=Editor(create(tmp_path/'project',**kwargs));ed.regen_audio=lambda:None
    return ed


def test_blank_handoff_carries_custom_constraints_and_editable_titles(tmp_path):
    ed=editor(tmp_path,template='blank',width=1440,height=1440,duration=24,presenter='bottom-right')
    values=copy.deepcopy(ed.saved)
    values['__media']=[{'id':'my-title','kind':'text','name':'Opening title','text':'Why this matters',
        'box':[250,200,900,120],'t0':0,'dur':5,'size':72,'color':'#111711','weight':'semi','align':'c'}]
    ed.save(values,ed.revision)
    doc=export(ed.pr,'Build on my title',ed.revision,ed.source_revision)
    assert (doc['constraints']['width'],doc['constraints']['height'])==(1440,1440)
    assert doc['constraints']['source_duration_seconds']==24
    assert doc['constraints']['presenter']=='bottom-right'
    assert doc['editable_values']['__media'][0]['text']=='Why this matters'
    assert 'my-title' in {layer['id'] for layer in doc['layers']}
    assert json.loads(doc['files']['settings.json'])['__media'][0]['id']=='my-title'
    assert len(list((Path(ed.pr.path)/'.dx-studio/ai-handoffs').glob('*.json')))==1
    ed.pr.render(1,.1)


def test_source_reload_rejects_stale_save_and_preserves_creator_values(tmp_path):
    ed=editor(tmp_path,template='starter')
    values=copy.deepcopy(ed.saved);values['title']='My chosen headline';values['__layers']['title']['x']=23
    ed.save(values,ed.revision)
    scene=Path(ed.pr.path)/'scene.py'
    # Equal-length substitutions exercise same-second Python bytecode invalidation.
    scene.write_text(scene.read_text().replace('Start with one idea.','Start with our idea.'))
    status=ed.disk_status();assert status['changed']
    with pytest.raises(SaveConflict):ed.save(ed.saved,ed.revision)
    ed.reload_source(ed.revision,status['revision'])
    assert ed.pr.defaults['title']=='Start with our idea.'
    assert ed.pr.values['title']=='My chosen headline'
    assert ed.pr.values['__layers']['title']['x']==23
    assert not ed.disk_status()['changed']


def test_failed_reload_keeps_working_scene_and_blocks_loss_of_saved_controls(tmp_path):
    ed=editor(tmp_path,template='starter');scene=Path(ed.pr.path)/'scene.py';source=scene.read_text()
    values=copy.deepcopy(ed.saved);values['title']='Keep this';ed.save(values,ed.revision)
    expected=ed.frame(1,.1)
    scene.write_text('this is not valid python !!!')
    with pytest.raises(SyntaxError):ed.reload_source(ed.revision,ed.disk_status()['revision'])
    assert ed.frame(1,.1)==expected
    scene.write_text(source.replace("'key':'title'","'key':'headline'").replace('p.title','p.headline'))
    with pytest.raises(ValueError,match='removed controls'):ed.reload_source(ed.revision,ed.disk_status()['revision'])
    assert json.loads(Path(ed.pr.settings_path).read_text())['title']=='Keep this'


def test_external_settings_reload_cannot_be_overwritten_by_stale_tab(tmp_path):
    ed=editor(tmp_path,template='starter')
    old=ed.revision;Path(ed.pr.settings_path).write_text(json.dumps({'title':'From my AI chat'}))
    with pytest.raises(SaveConflict):ed.save(ed.saved,old)
    status=ed.disk_status();assert status['changed'] and 'settings.json' in status['files']
    ed.reload_source(old,status['revision'])
    assert ed.pr.values['title']=='From my AI chat'
    assert ed.source_generation==1
    assert not ed.disk_status()['changed']


def test_templates_and_skeleton_reject_invalid_dimensions_before_creating(tmp_path):
    with pytest.raises(ValueError):create(tmp_path/'bad',template='blank',width=1001,height=1080)
    assert not (tmp_path/'bad').exists()
    for name in ('showcase','comparison'):
        folder=create(tmp_path/name,template=name,format='9:16')
        ed=Editor(folder);ed.pr.render(1,.1)
        if name=='showcase':assert (folder/'assets/make-it-click.flac').is_file()
