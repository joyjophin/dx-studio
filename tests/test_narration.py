"""Check the important contract: saved takes, real samples, trim/ripple and replacement sources."""
import copy
import json
from zipfile import ZipFile
from pathlib import Path
import numpy as np
import pytest
import soundfile as sf
from dx_studio.project import Project
from dx_studio.scaffold import create
from dx_studio.narration import import_take
from dx_studio.audio import build_mix, SR
from dx_studio.preflight import inspect_project


def quiet_project(tmp_path):
    folder=create(tmp_path/'demo',template='starter')
    cfg=json.loads((folder/'project.json').read_text());cfg.pop('music',None)
    (folder/'project.json').write_text(json.dumps(cfg))
    pr=Project(folder);pr.cues=lambda:[]
    return pr


def test_legacy_narration_defaults_and_saved_takes_override_sources(tmp_path):
    pr=quiet_project(tmp_path);source=Path(pr.path)/'voice.wav'
    sf.write(source,np.sin(np.arange(SR)*2*np.pi*440/SR)*.2,SR)
    cfg=pr.cfg;cfg['voice']=[{'file':'voice.wav','start':1,'text':'Original script'}]
    (Path(pr.path)/'project.json').write_text(json.dumps(cfg));pr=Project(pr.path)
    assert pr.voices()[0]['duration']==1 and pr.voices()[0]['id']=='voice_0'
    pr.values['__voice'][0].update(start=2,offset=.25,duration=.5,gain=.6,muted=True)
    pr.save_settings();reopened=Project(pr.path)
    assert reopened.voices()==pr.voices()
    pr.values['__voice']=[];pr.save_settings();assert Project(pr.path).voices()==[]
    assert cfg['voice'][0]['start']==1


def test_import_replacement_trim_and_ripple_are_audible_only_where_expected(tmp_path):
    pr=quiet_project(tmp_path)
    source=tmp_path/'recorded.wav';samples=np.r_[np.zeros(SR//2),np.sin(np.arange(SR//2)*2*np.pi*440/SR)*.3]
    sf.write(source,samples,SR)
    take=import_take(pr,'Recorded take.wav',source.read_bytes(),1)
    assert pr.voices()==[] # staging never changes settings
    take.update(offset=.5,duration=.25)
    pr.values['__voice']=[take];pr.apply(pr.values)
    raw=tmp_path/'mix.wav';build_mix(pr,raw);audio,_=sf.read(raw)
    assert np.max(np.abs(audio[:SR]))==0 and np.max(np.abs(audio[SR:SR+SR//4]))>.1
    assert np.max(np.abs(audio[SR+SR//4:]))==0
    # A hold before the take shifts it; the inserted section is silent.
    pr.values['__timeline']=[{'op':'insert','at':.5,'dur':.5}];pr.apply(pr.values)
    build_mix(pr,raw);audio,_=sf.read(raw)
    assert np.max(np.abs(audio[:int(1.5*SR)]))==0
    assert np.max(np.abs(audio[int(1.5*SR):int(1.75*SR)]))>.1
    pr.save_settings()
    from dx_studio.bundle import pack
    archive=pack(pr.path,tmp_path/'portable.zip')
    with ZipFile(archive) as bundle:bundle.extractall(tmp_path/'unpacked')
    reopened=Project(tmp_path/'unpacked/project')
    assert reopened.voices()==pr.voices() and (Path(reopened.path)/take['file']).exists()
    original=Path(pr.path)/take['file'];replacement=import_take(pr,'New take.wav',source.read_bytes(),0)
    before=copy.deepcopy(take);take['file']=replacement['file']
    assert {k:v for k,v in take.items() if k!='file'}=={k:v for k,v in before.items() if k!='file'}
    assert original.exists() and replacement['file']!=before['file']
    take['muted']=True;build_mix(pr,raw);assert np.max(np.abs(sf.read(raw)[0]))==0


def test_invalid_trim_missing_and_muted_sources(tmp_path):
    pr=quiet_project(tmp_path)
    take={'id':'voice_test','file':'missing.wav','name':'Missing take','start':0,'offset':0,'duration':1,'gain':1,'duck':'normal','muted':False}
    pr.values['__voice']=[take];pr.apply(pr.values)
    assert not inspect_project(pr)['ok']
    take['muted']=True;assert inspect_project(pr)['ok']
    for field,value in [('gain',float('nan')),('offset',-1),('file','../outside.wav')]:
        values=copy.deepcopy(pr.values);values['__voice'][0][field]=value
        with pytest.raises(ValueError):pr.apply(values)


def test_saved_bus_levels_mutes_and_missing_audio_are_used_by_the_mix(tmp_path):
    pr=quiet_project(tmp_path);source=Path(pr.path)/'voice.wav'
    sf.write(source,np.sin(np.arange(SR)*2*np.pi*440/SR)*.2,SR)
    take=import_take(pr,'Take.wav',source.read_bytes(),1)
    pr.values['__voice']=[take];pr.apply(pr.values);raw=tmp_path/'mix.wav'
    build_mix(pr,raw);full=sf.read(raw)[0]
    pr.values['__mix']['voice']=.5;build_mix(pr,raw);half=sf.read(raw)[0]
    assert np.allclose(half,full*.5)
    pr.values['__mix'].update(voice_muted=True,loudness=-18,peak=-2)
    build_mix(pr,raw);assert np.max(np.abs(sf.read(raw)[0]))==0
    # Muting a bus skips missing audio too; unmuting asks for repair.
    take['file']='missing.wav';pr.cfg['music']={'file':'missing-music.wav'}
    pr.values['__mix']['music_muted']=True
    assert inspect_project(pr)['ok']
    pr.save_settings();assert Project(pr.path).values['__mix']['loudness']==-18
    pr.values['__mix']['voice_muted']=False;assert not inspect_project(pr)['ok']
    values=copy.deepcopy(pr.values);values['__mix']['peak']=float('nan')
    with pytest.raises(ValueError):pr.apply(values)
