"""Critical creator contracts: timing, protected edits, portable assets and output ranges."""
import copy
import io
import json
from pathlib import Path
import subprocess
import threading
import numpy as np
import pytest
import soundfile as sf
from dx_studio.scaffold import create
from dx_studio.project import Project
from dx_studio import transcripts,revisions
from dx_studio.creator import reorder
from dx_studio.timemap import scene_time,segments,out_duration
from dx_studio.export_profiles import resolve,sidecar


def project(tmp_path):return Project(create(tmp_path/'story',template='explainer',format='16:9'))


def timed_take(pr):
    sf.write(Path(pr.path)/'voice.wav',np.sin(np.arange(96000)*2*np.pi*440/48000)*.2,48000)
    take={'id':'voice_test','name':'Take','file':'voice.wav','start':1,'offset':0,'duration':2,'gain':1,'duck':'normal','muted':False}
    take['transcript']=transcripts.prepare(pr,take,json.dumps({'words':[{'text':'Make','start':.1,'end':.4},{'text':'clear','start':.5,'end':.8},{'text':'stories','start':1,'end':1.5}]}))
    pr.values['__voice']=[take];pr.apply(pr.values);return take


def test_transcript_captions_retime_and_protection(tmp_path):
    pr=project(tmp_path);take=timed_take(pr);caps=transcripts.captions_for(take,2);pr.values['__captions']=caps
    word=take['transcript']['words'][0];pr.values['__anchors']=[{'voice_id':take['id'],'word_id':word['id'],'text':word['text'],'layer_id':'title','offset':0}]
    pr.apply(pr.values);proposal=revisions.retime(pr,pr.values)
    original=copy.deepcopy(pr.values);applied=revisions.apply(pr,pr.values,proposal)
    assert pr.values==original and applied['__layers']['title']['start']==pytest.approx(1.1)
    pr.values['__protected']=['layer:title','__captions'];review=revisions.review(pr,pr.values,revisions.retime(pr,pr.values))
    assert all(not row['allowed'] for row in review)
    pr.values['__protected']=[];take=pr.voices()[0];take['start']+=1
    changed=revisions.apply(pr,pr.values,revisions.retime(pr,pr.values))
    assert changed['__captions'][0]['start']==pytest.approx(2.1)
    take['file']='replacement.wav';assert transcripts.visible_words(take)==[]
    assert revisions.retime(pr,pr.values)['warnings']


def test_revision_conflicts_are_atomic(tmp_path):
    pr=project(tmp_path);before=copy.deepcopy(pr.values)
    proposal={'format_version':1,'changes':[{'path':['title'],'before':pr.values['title'],'after':'Reviewed title'},{'path':['__layers','title','x'],'before':0,'after':100}]}
    pr.values['__layers']['title']['x']=20
    assert not revisions.review(pr,pr.values,proposal)[1]['allowed']
    with pytest.raises(ValueError,match='changed'):revisions.apply(pr,pr.values,proposal)
    assert pr.values['title']==before['title']
    result=revisions.apply(pr,pr.values,proposal,[0]);assert result['title']=='Reviewed title' and result['__layers']['title']['x']==20


def test_scene_order_maps_audio_captions_and_holds(tmp_path):
    pr=project(tmp_path);ids=[s['id'] for s in pr.values['__story']];reorder(pr.values,[ids[1],ids[0],*ids[2:]]);pr.apply(pr.values)
    assert pr.scene_t(.5)==pytest.approx(4.5) and pr.scene_t(4.5)==pytest.approx(.5)
    assert pr.duration==16
    pr.values['__timeline'].append({'op':'insert','at':1,'dur':.5});pr.apply(pr.values)
    assert pr.scene_t(1.25)==pytest.approx(5) and pr.duration==16.5
    spans=segments(pr.base_duration,pr.edits);assert sum(b-a for a,b,*_ in spans)==pytest.approx(16.5)
    assert any(kind=='hold' for *_,kind in spans)
    with pytest.raises(ValueError,match='before'):reorder(pr.values,ids)


@pytest.mark.parametrize('kind,body',[('bars','Before,10\nAfter,20'),('diagram','Input\nExplain the mechanism\nResult')])
def test_blocks_and_cross_project_templates_keep_editable_sources(tmp_path,kind,body):
    from dx_studio.blocks import prepare
    from dx_studio.templates_library import TemplateLibrary
    pr=project(tmp_path);pr.apply(prepare(pr,pr.values,{'kind':kind,'title':'A clear explanation','body':body,'start':0,'duration':4}))
    assert any(item['kind']=='shape' for item in pr.values['__media']);pr.render(1,.1)
    library=TemplateLibrary(tmp_path/'templates');saved=library.capture(pr,pr.values,[item['id'] for item in pr.values['__media']],'Channel chart')
    other=Project(create(tmp_path/'other',template='starter',format='9:16'));new=library.apply(other,other.values,saved['id'],0)
    other.apply(new);other.render(1,.1)
    assert len({item['id'] for item in new['__media']})==len(new['__media'])
    assert all(item['kind'] in ('text','shape') for item in new['__media'])


def test_brand_kit_roundtrip_and_missing_font_recovery(tmp_path):
    from dx_studio.brand_assets import import_font,export_kit,import_kit
    from dx_studio.text import FONT_DIR
    from dx_studio.quality import inspect
    pr=project(tmp_path);font=import_font(pr,Path(FONT_DIR)/'DXSans-Regular.ttf');pr.values['__brand_assets']['fonts']['xb']=font['file'];pr.apply(pr.values);pr.render(1,.1)
    kit=export_kit(pr,pr.values);result=import_kit(pr,kit);assert result['assets']['fonts']['xb']!=font['file']
    pr.values['__brand_assets']['fonts']['xb']='missing.ttf';pr.apply(pr.values);pr.render(1,.1)
    report=inspect(pr,threading.RLock());assert not report['ok'] and any(f['kind']=='font' for f in report['findings'])


def test_export_ranges_sidecars_and_source_clock_are_separate(tmp_path):
    pr=project(tmp_path);pr.values['__export'].update(profile='720p',fps=24,range=[1,3],captions='sidecar',file='outputs/preview.mp4');pr.apply(pr.values)
    options=resolve(pr);assert (options['width'],options['height'],options['fps'],options['duration'])==(1280,720,24,2)
    assert pr.duration==16 and pr.output.endswith('outputs/preview.mp4')
    text=sidecar(pr,1,3);assert '00:00:00,000' in text and '00:00:02,000' in text
    pr.save_settings();assert Project(pr.path).values['__export']==pr.values['__export']


def test_real_range_export_keeps_audio_and_sidecar_in_sync(tmp_path):
    from dx_studio.cli import cmd_build
    folder=create(tmp_path/'range',template='starter',format='16:9')
    cfg=json.loads((folder/'project.json').read_text());cfg.update(width=320,height=180,duration=2,fps=12,voice=[{'file':'voice.wav','start':0}]);cfg.pop('safe_area',None);cfg.pop('music',None)
    (folder/'project.json').write_text(json.dumps(cfg));(folder/'captions.json').write_text('[]')
    (folder/'scene.py').write_text("SCHEMA=[]\ndef draw(c,t,p):\n c.set_source_rgb(*( (1,0,0) if t<1 else (0,1,0) ));c.paint()\n")
    sf.write(folder/'voice.wav',np.r_[np.zeros(48000),np.sin(np.arange(48000)*2*np.pi*440/48000)*.2],48000)
    pr=Project(folder);pr.values['__captions']=[{'start':.25,'end':1.75,'text':'Cut caption','hl':None}];pr.values['__export'].update(profile='720p',range=[.5,1.5],captions='sidecar',file='outputs/cut.mp4');pr.save_settings()
    cmd_build(folder);output=folder/'outputs/cut.mp4'
    data=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_entries','stream=width,height:format=duration','-of','json',str(output)]))
    video=next(stream for stream in data['streams'] if stream.get('width'));assert (video['width'],video['height'])==(1280,720)
    assert float(data['format']['duration'])==pytest.approx(1,abs=.1)
    assert '00:00:00,000 --> 00:00:01,000' in output.with_suffix('.srt').read_text()
    decoded=tmp_path/'decoded.wav';subprocess.run(['ffmpeg','-v','error','-y','-i',str(output),'-vn',str(decoded)],check=True)
    audio,sr=sf.read(decoded);assert np.max(np.abs(audio[:int(.4*sr)]))<.001 and np.max(np.abs(audio[int(.65*sr):]))>.01


def test_caption_publication_rolls_back_if_video_cannot_publish(tmp_path,monkeypatch):
    import os
    from dx_studio.publishing import publish
    output=tmp_path/'video.mp4';output.write_bytes(b'previous video');captions=tmp_path/'video.srt';captions.write_text('previous captions');new=tmp_path/'new.mp4';new.write_bytes(b'new video');side=tmp_path/'new.srt';side.write_text('new captions')
    replace=os.replace
    def fail_video(source,destination):
        if str(source)==str(new):raise OSError('deliberate publish failure')
        return replace(source,destination)
    monkeypatch.setattr('dx_studio.publishing.os.replace',fail_video)
    with pytest.raises(OSError):publish(new,output,side)
    assert output.read_bytes()==b'previous video' and captions.read_text()=='previous captions'


def test_reordered_subtitle_import_and_invalid_portable_inputs(tmp_path):
    from dx_studio.subtitles import prepare_import,output_cues
    from dx_studio.templates_library import TemplateLibrary
    pr=project(tmp_path);ids=[s['id'] for s in pr.values['__story']];reorder(pr.values,[ids[1],ids[0],*ids[2:]]);pr.apply(pr.values)
    result=prepare_import('1\n00:00:03,000 --> 00:00:05,000\nAcross scenes',pr)
    pr.values['__captions']=result['cues']
    assert output_cues(pr)==[{'start':3,'end':4,'text':'Across scenes'},{'start':4,'end':5,'text':'Across scenes'}]
    with pytest.raises(ValueError):TemplateLibrary(tmp_path/'templates').save({'format_version':1,'name':'Broken','items':[{}],'states':{},'files':{}})
    take=timed_take(pr);take['transcript']['words'][0]['end']=100
    with pytest.raises(ValueError,match='source seconds'):transcripts.validate(take['transcript'])


from test_editor import editor_server,request


def test_creator_job_status_and_revision_preview_do_not_commit(editor_server):
    editor,port=editor_server;before=copy.deepcopy(editor.saved)
    editor.creator_jobs={'pending':{'id':'pending','running':True,'ok':False,'result':None}};editor.creator_job_lock=threading.RLock()
    status,raw=request(port,'GET','/api/creator/job?id=pending');data=json.loads(raw)
    assert status==200 and data['job']['running'] and 'ok' not in data
    proposal={'format_version':1,'source_revision':revisions.source_fingerprint(editor.pr),'changes':[{'path':['title'],'before':before['title'],'after':'Reviewed only'}]}
    headers={'Content-Type':'application/json','X-DX-Studio-Client':'1'}
    status,raw=request(port,'POST','/api/creator/revision-frame',json.dumps({'values':before,'proposal':proposal,'t':1}),headers)
    assert status==200 and json.loads(raw)['after_image'].startswith('data:image/png;base64,')
    assert editor.saved==before and editor.pr.values['title']==before['title']
