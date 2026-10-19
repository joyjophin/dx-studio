"""Reproduce the assistant-folder → saved edits → moved project → MP4 workflow.

Synthetic test-pattern footage and test tones exercise timing without personal
assets or downloaded speech models. This is a scripted acceptance check, not a
claim of fresh-user usability research or a spoken-word alignment review.
"""
import argparse
import copy
import json
import subprocess
import sys
from pathlib import Path
from zipfile import ZipFile
import numpy as np
import soundfile as sf
from dx_studio.editor import Editor
from dx_studio.scaffold import create
from dx_studio.narration import import_take
from dx_studio.clips import prepare
from dx_studio.bundle import pack,verify
from dx_studio.cli import cmd_build


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--output',required=True);args=ap.parse_args()
    root=Path(args.output).resolve()
    if root.exists():ap.error('Choose a new output folder to retain previous evidence')
    root.mkdir(parents=True)
    footage=root/'synthetic-footage.mp4';recording=root/'synthetic-voice.wav'
    subprocess.run(['ffmpeg','-v','error','-y','-f','lavfi','-i','testsrc2=size=320x180:rate=30:duration=5','-f','lavfi','-i','sine=frequency=880:duration=5','-c:v','libx264','-pix_fmt','yuv420p','-c:a','aac','-shortest',str(footage)],check=True)
    sf.write(recording,.08*np.sin(2*np.pi*440*np.arange(48000*5)/48000),48000)
    results=[]
    for ratio,presenter,caption_mode in [('16:9','left-half','burned'),('9:16','bottom-right','sidecar')]:
        folder=create(root/ratio.replace(':','-'),format=ratio,presenter=presenter)
        editor=Editor(folder);editor.regen_audio=lambda:None
        values=copy.deepcopy(editor.saved);values['title']='A project you can keep editing.'
        values['__captions'][0]['text']='A caption corrected in DX Editor.'
        take=import_take(editor.pr,recording.name,recording.read_bytes(),0);values['__voice'].append(take)
        item=editor.pr.media.import_file(footage.name,footage.read_bytes(),0)
        area=editor.pr.layout['content'];item['box']=[area[0]+40,area[1]+160,min(600,area[2]-area[0]-80),220]
        values['__media'].append(item);editor.apply(values)
        values=copy.deepcopy(editor.pr.values)
        from dx_studio.audio import build_mix
        build_mix(editor.pr,str(folder/'before-split.wav'))
        values=prepare(editor.pr,values,item['id'],'split',at=2)['values'];editor.apply(values)
        build_mix(editor.pr,str(folder/'after-split.wav'))
        before,_=sf.read(folder/'before-split.wav');after,_=sf.read(folder/'after-split.wav')
        assert np.max(np.abs(before-after))<1e-6,'Splitting changed source audio timing'
        (folder/'before-split.wav').unlink();(folder/'after-split.wav').unlink()
        values['__groups']=[{'id':'group_proof','name':'Footage pair','layers':[media['id'] for media in values['__media']]}]
        values['__export'].update(profile='720p',fps=24,range=[1,4],captions=caption_mode,file='exports/launch-proof.mp4')
        editor.save(values,editor.revision);version=editor.version('Ready for handoff',editor.revision)
        archive=pack(folder,root/(ratio.replace(':','-')+'-project.zip'),include_history=True);verified=verify(archive)
        moved=root/('moved-'+ratio.replace(':','-'))
        with ZipFile(archive) as stream:stream.extractall(moved)
        reopened=Editor(moved/'project');reopened.regen_audio=lambda:None
        assert reopened.pr.values['title']=='A project you can keep editing.'
        assert len(reopened.pr.values['__media'])==2 and reopened.pr.values['__groups'][0]['name']=='Footage pair'
        assert reopened.history.get(version['id'])['name']=='Ready for handoff'
        # Check the bundled engine in its own import path, not this checkout.
        subprocess.run([sys.executable,'-c','from dx_studio.project import Project; p=Project("project"); assert p.values["title"]=="A project you can keep editing."'],cwd=moved,env={**__import__('os').environ,'PYTHONPATH':str(moved/'engine')},check=True)
        cmd_build(moved/'project')
        video=moved/'project/exports/launch-proof.mp4'
        info=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(video)]))
        v=next(s for s in info['streams'] if s['codec_type']=='video');a=next(s for s in info['streams'] if s['codec_type']=='audio')
        assert (v['width'],v['height'])==((1280,720) if ratio=='16:9' else (720,1280))
        assert abs(float(v['duration'])-float(a['duration']))<.1
        subprocess.run(['ffmpeg','-v','error','-i',str(video),'-f','null','-'],check=True)
        if caption_mode=='sidecar':assert '00:00:00,000 -->' in video.with_suffix('.srt').read_text()
        changed=copy.deepcopy(reopened.pr.values);changed['title']='A later revision';reopened.save(changed,reopened.revision)
        reopened.restore(version['id'],reopened.revision);assert reopened.pr.values['title']=='A project you can keep editing.'
        results.append({'ratio':ratio,'presenter':presenter,'captions':caption_mode,'duration':float(info['format']['duration']),'size':[v['width'],v['height']],'audio_video_delta':round(abs(float(v['duration'])-float(a['duration'])),5),'bundle_files':verified['files'],'source_audio_split_matches':True,'saved_edits_reopened':True,'settings_version_restored':True,'full_decode':True})
    report={'ok':True,'cases':results,'scope':'Synthetic sources and scripted workflow; not real speech alignment, new-user research or a long full-HD render.'}
    (root/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))

if __name__=='__main__':main()
