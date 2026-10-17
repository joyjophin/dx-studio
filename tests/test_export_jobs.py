"""Protect the completed video and stop only the running export process tree."""
from pathlib import Path
import subprocess
import sys
import json,copy,threading
import pytest
from dx_studio.editor import Editor
from dx_studio.scaffold import create
from dx_studio.cli import cmd_build


def test_cancel_stops_the_job_and_keeps_the_completed_video(tmp_path,monkeypatch):
    editor=Editor(create(tmp_path/'project',template='starter'))
    editor.regen_audio=lambda:None
    output=Path(editor.pr.output);output.write_bytes(b'previous completed video')
    launch=subprocess.Popen;release=threading.Event();captured=[];original_title=editor.pr.values['title'];original_revision=editor.revision
    def slow_job(command,**options):
        release.wait(2);captured.append(json.loads(Path(command[command.index('--settings')+1]).read_text())['title'])
        return launch([sys.executable,'-c',"import time; print('frame 0',flush=True); time.sleep(30)"],**options)
    monkeypatch.setattr('dx_studio.editor.subprocess.Popen',slow_job)
    try:
        editor.start_build(editor.pr.values,editor.revision)
        newer=copy.deepcopy(editor.pr.values);newer['title']='A newer edit';editor.save(newer,editor.revision);release.set()
        with pytest.raises(ValueError,match='already running'):editor.start_build(editor.pr.values,editor.revision)
        with pytest.raises(ValueError,match='export changed'):editor.cancel_build('another-job')
        assert editor.build['running'] and not editor.build['cancel_requested']
        editor.cancel_build(editor.build['id']);editor.build_thread.join(timeout=5)
        assert not editor.build_thread.is_alive()
        assert captured==[original_title] and editor.build['revision']==original_revision
        assert editor.build['cancelled'] and not editor.build['running'] and not editor.build['ok']
        assert output.read_bytes()==b'previous completed video'
    finally:
        release.set();editor.cancel_build()
        if editor.build_thread:editor.build_thread.join(timeout=5)


def test_failed_cli_export_keeps_previous_mp4(tmp_path,monkeypatch):
    folder=create(tmp_path/'project',template='starter');output=folder/'video.mp4';output.write_bytes(b'previous completed video')
    monkeypatch.setattr('dx_studio.audio.build_mix',lambda project,path:path)
    def fail(*args,**kwargs):raise RuntimeError('deliberate mastering failure')
    monkeypatch.setattr('dx_studio.audio.master',fail)
    with pytest.raises(RuntimeError,match='deliberate'):cmd_build(folder)
    assert output.read_bytes()==b'previous completed video'


def test_concurrent_decoders_publish_complete_media_caches(tmp_path):
    from concurrent.futures import ThreadPoolExecutor
    import soundfile as sf
    from dx_studio.project import Project
    folder=create(tmp_path/'project',template='starter')
    source=tmp_path/'clip.mp4'
    subprocess.run(['ffmpeg','-v','error','-y','-f','lavfi','-i','color=c=red:s=64x36:d=0.2',
                    '-f','lavfi','-i','sine=frequency=440:duration=0.2','-c:v','libx264','-pix_fmt','yuv420p','-c:a','aac','-shortest',str(source)],check=True)
    first=Project(folder);second=Project(folder)
    with ThreadPoolExecutor(2) as pool:
        imports=list(pool.map(lambda media:media.import_file('clip.mp4',source.read_bytes(),0),[first.media,second.media]))
    assert imports[0]['file']!=imports[1]['file']
    item=imports[0]
    with ThreadPoolExecutor(2) as pool:
        decodes=list(pool.map(lambda media:media.decode_video(item),[first.media,second.media]))
        audio=list(pool.map(lambda media:media.audio_wav(item),[first.media,second.media]))
    assert decodes[0]==decodes[1] and Path(decodes[0],'.complete').is_file()
    assert list(Path(decodes[0]).glob('f_*.jpg'))
    assert audio[0]==audio[1] and sf.info(audio[0]).frames>0
