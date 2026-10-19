"""Launch gates: edits survive splitting, moving, recovery and cache reuse."""
import copy
import io
import json
from pathlib import Path
from zipfile import ZipFile
import pytest
from PIL import Image
from dx_studio.scaffold import create
from dx_studio.project import Project
from dx_studio.editor import Editor
from dx_studio.clips import prepare
from dx_studio.bundle import pack,verify
from dx_studio.relink import plan,restore
from test_editor import editor_server,request


def image():
    stream=io.BytesIO();Image.new('RGB',(80,40),'red').save(stream,'PNG');return stream.getvalue()


def pixels(project,t):
    surface=project.render(t,.15)
    return bytes(surface.get_data())


def test_split_and_trim_preserve_rendered_motion_and_saved_groups(tmp_path):
    project=Project(create(tmp_path/'project',template='starter'))
    item=project.media.import_file('graphic.png',image(),0)
    values=copy.deepcopy(project.values);values['__media'].append(item);project.apply(values)
    state=values['__layers'][item['id']];state.update(start=0,end=4,enter='fade',enter_dur=2,exit='fade',exit_dur=2,opacity=.6,
        keys=[dict(t=0,x=0,y=0,scale=1,rotation=0,opacity=.6),dict(t=4,x=100,y=20,scale=1.2,rotation=10,opacity=.9,ease='ease')])
    values['__groups']=[{'id':'group_test','name':'Graphics','layers':['title',item['id']]}]
    project.apply(values)
    times=[.6,1.2,1.8,3.4]
    before=[pixels(project,t) for t in times]
    result=prepare(project,values,item['id'],'split',at=1.2)
    project.apply(result['values'])
    assert [pixels(project,t) for t in times]==before
    assert result['selected'] in project.values['__groups'][0]['layers']
    project.save_settings();reopened=Project(project.path)
    assert reopened.values['__groups']==project.values['__groups']
    assert reopened.values['__media'][1]['source_offset']==1.2
    trimmed=prepare(project,values,item['id'],'trim',start=.6,end=3.5)
    project.apply(trimmed['values'])
    assert pixels(project,1.8)==before[2]
    locked=copy.deepcopy(values);locked['__layers'][item['id']]['locked']=True
    with pytest.raises(ValueError,match='Unlock'):prepare(project,locked,item['id'],'split',at=1)


def test_folder_relink_review_does_not_guess_or_overwrite(tmp_path):
    project=Project(create(tmp_path/'project'))
    item=project.media.import_file('source.png',image(),0)
    project.values['__media'].append(item);project.apply(project.values)
    target=Path(project.media.path(item));target.unlink()
    originals=tmp_path/'originals';(originals/'a').mkdir(parents=True);(originals/'b').mkdir()
    (originals/'a'/'source.png').write_bytes(image());(originals/'b'/'source.png').write_bytes(image())
    assert plan(project,originals)['files'][0]['status']=='ambiguous'
    reviewed=plan(project,originals/'a');assert reviewed['files'][0]['status']=='ready'
    assert isinstance(reviewed['files'][0]['mtime_ns'],str)
    assert restore(project,reviewed['folder'],reviewed['files'])['restored']==['assets/Media/source.png']
    before=target.read_bytes()
    with pytest.raises(ValueError,match='changed'):restore(project,reviewed['folder'],reviewed['files'])
    assert target.read_bytes()==before


def test_bundle_moves_edits_and_versions_with_matching_engine(tmp_path):
    editor=Editor(create(tmp_path/'project',template='starter'));editor.regen_audio=lambda:None
    values=copy.deepcopy(editor.saved);values['title']='Survives a move'
    editor.save(values,editor.revision);record=editor.version('Before handoff',editor.revision)
    archive=pack(editor.pr.path,tmp_path/'project.zip',include_history=True);assert verify(archive)['ok']
    moved=tmp_path/'other-computer'
    with ZipFile(archive) as stream:stream.extractall(moved)
    reopened=Project(moved/'project');assert reopened.values['title']=='Survives a move'
    from dx_studio.history import SettingsHistory
    assert SettingsHistory(moved/'project').get(record['id'])['name']=='Before handoff'
    assert (moved/'engine/dx_studio/editor-guide.js').is_file()
    with pytest.raises(ValueError,match='already exists'):pack(editor.pr.path,archive)
    changed=tmp_path/'modified.zip'
    with ZipFile(archive) as source,ZipFile(changed,'w') as output:
        for name in source.namelist():output.writestr(name,b'changed' if name=='project/scene.py' else source.read(name))
    with pytest.raises(ValueError,match='integrity'):verify(changed)


def test_preview_cache_invalidates_for_edits_and_replaced_sources(tmp_path):
    editor=Editor(create(tmp_path/'project',template='starter'))
    item=editor.pr.media.import_file('source.png',image(),0)
    values=copy.deepcopy(editor.pr.values);values['__media'].append(item);editor.apply(values)
    first=editor.frame(.5,.15);assert editor.frame(.5,.15)==first and editor.preview_cache.hits==1
    values=copy.deepcopy(editor.pr.values);values['title']='New words';editor.apply(values)
    assert editor.frame(.5,.15)!=first
    misses=editor.preview_cache.misses;Path(editor.pr.media.path(item)).unlink()
    assert editor.frame(.5,.15)!=first and editor.preview_cache.misses==misses+1
    from dx_studio.preview_cache import PreviewCache
    cache=PreviewCache(limit=8,entries=2);cache.put('a',b'1234');cache.put('b',b'5678');cache.put('c',b'9')
    assert cache.bytes<=8 and len(cache.data)<=2 and 'a' not in cache.data


def test_launch_routes_stage_clips_and_download_saved_bundle(editor_server):
    editor,port=editor_server
    assert request(port,'GET','/editor-guide.js')[0]==200
    item=editor.pr.media.import_file('source.png',image(),0)
    values=copy.deepcopy(editor.pr.values);values['__media'].append(item);editor.apply(values);editor.save(editor.pr.values,editor.revision)
    saved=Path(editor.pr.settings_path).read_bytes()
    body={'values':editor.pr.values,'id':item['id'],'operation':'split','at':1}
    status,raw=request(port,'POST','/api/media/clip',json.dumps(body),{'X-DX-Studio-Client':'1'})
    assert status==200 and len(json.loads(raw)['values']['__media'])==2
    assert Path(editor.pr.settings_path).read_bytes()==saved
    status,raw=request(port,'POST','/api/bundle','{}',{'X-DX-Studio-Client':'1'})
    assert status==200
    with ZipFile(io.BytesIO(raw)) as bundle:assert json.loads(bundle.read('DX-BUNDLE.json'))['format_version']==1


def test_bundle_refuses_incomplete_sources_without_partial_output(tmp_path):
    folder=create(tmp_path/'project',template='starter')
    (folder/'settings.json').write_text(json.dumps({'__media':[{'file':'Media/lost.mp4'}]}))
    with pytest.raises(ValueError,match='missing or excluded'):pack(folder,tmp_path/'bad.zip')
    assert not (tmp_path/'bad.zip').exists()


def test_video_scrubbing_decodes_only_requested_chunks_and_keeps_source_clock(tmp_path):
    import subprocess
    import numpy as np
    project=Project(create(tmp_path/'project',template='starter'))
    source=Path(project.media.assets)/'long.mp4'
    subprocess.run(['ffmpeg','-v','error','-y','-f','lavfi','-i','color=red:s=64x36:r=30:d=4','-f','lavfi','-i','color=green:s=64x36:r=30:d=4','-f','lavfi','-i','color=blue:s=64x36:r=30:d=4','-filter_complex','[0:v][1:v][2:v]concat=n=3:v=1:a=0[v]','-map','[v]','-c:v','libx264','-pix_fmt','yuv420p',str(source)],check=True)
    item=project.media.item_for('long.mp4',0)
    surface,w,h=project.media.video_frame(item,8.2);pixels=np.frombuffer(surface.get_data(),np.uint8).reshape(h,surface.get_stride()//4,4)
    assert pixels[h//2,w//2,0]>200 and pixels[h//2,w//2,2]<20
    root=Path(project.media.cache_dir)/(project.media.cache_key(item)+'-chunks-v1')
    assert [p.name for p in root.iterdir() if p.is_dir()]==['000002']
    assert len(list(root.rglob('f_*.jpg')))<=120
    surface,w,h=project.media.video_frame(item,4.2);pixels=np.frombuffer(surface.get_data(),np.uint8).reshape(h,surface.get_stride()//4,4)
    assert pixels[h//2,w//2,1]>100 and pixels[h//2,w//2,2]<20
    assert project.media._frame_bytes<=64*1024*1024
