"""Make a separate no-narration MP4 from a freshly completed project export.

    python scripts/novoice.py <project> <out.mp4> [--mute-footage]

Run immediately after building the same saved settings. Footage audio stays unless
--mute-footage is selected. No shared export intermediates are required.
"""
import argparse
import os
from pathlib import Path
import subprocess
import sys
import tempfile
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from dx_studio import cli,audio


def make_novoice(project,out,mute_footage=False):
    pr=cli._project(project);source=Path(pr.output).resolve();destination=Path(out).resolve()
    if not source.is_file():raise ValueError('Build the project first, using the same saved settings.')
    if destination==source:raise ValueError('Use a separate output path so the voiced master is kept.')
    sources={Path(pr.media.path(item)).resolve() for item in pr.values.get('__media',[]) if item.get('file')}
    if destination in sources:raise ValueError('Do not overwrite a source asset with the no-narration export.')
    if destination.suffix.lower()!='.mp4':raise ValueError('Export to an .mp4 file')
    destination.parent.mkdir(parents=True,exist_ok=True)
    from dx_studio.mix_controls import settings as mix_settings
    from dx_studio.export_profiles import resolve
    options=resolve(pr)
    mx=mix_settings(pr);target,peak=mx.get('loudness',-14.0),mx.get('peak',-1.2)
    with tempfile.TemporaryDirectory(prefix='.dx-novoice-',dir=destination.parent) as work:
        work=Path(work)
        def chain(raw,dst,gain,limit):
            subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-y','-i',str(raw),'-af',
                            f'acompressor=threshold=-24dB:ratio=3:attack=6:release=120:makeup=4dB,volume={gain:.2f}dB,'
                            f'alimiter=limit={10**(limit/20):.4f}:attack=2:release=60:level=false',
                            '-ar',str(audio.SR),'-c:a','pcm_s24le',str(dst)],check=True)
            return audio._lufs(dst)
        def crop(path,name):
            if options['start']==0 and options['end']==pr.duration:return path
            target=work/name
            subprocess.run(['ffmpeg','-v','error','-y','-ss',str(options['start']),'-i',str(path),'-t',str(options['duration']),'-c:a','pcm_f32le',str(target)],check=True)
            return str(target)
        full=crop(audio.build_mix(pr,str(work/'full.wav')),'full-range.wav');gain,limit=8.5,peak-.55
        for _ in range(6):
            loudness,actual_peak=chain(full,work/'full-master.wav',gain,limit)
            if abs(loudness-target)<.25 and actual_peak<=peak+.05:break
            if actual_peak>peak+.05:limit-=(actual_peak-peak)+.1
            if abs(loudness-target)>=.25:gain+=(target-loudness)*1.05
        for line in pr.voices():line['muted']=True
        if mute_footage:
            for item in pr.values.get('__media',[]):
                if item.get('kind')=='video':item['muted']=True
        raw=crop(audio.build_mix(pr,str(work/'no-narration.wav')),'no-narration-range.wav');master=work/'master.wav';chain(raw,master,gain,limit)
        complete=work/'complete.mp4'
        subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-y','-i',str(source),'-i',str(master),
                        '-map','0:v:0','-map','1:a:0','-c:v','copy','-c:a','aac','-b:a','256k','-ar','48000',
                        '-t',str(options['duration']),'-movflags','+faststart',str(complete)],check=True)
        os.replace(complete,destination)
    print('wrote',destination)


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('project');parser.add_argument('output');parser.add_argument('--mute-footage',action='store_true');args=parser.parse_args()
    try:make_novoice(args.project,args.output,args.mute_footage)
    except (ValueError,OSError,RuntimeError,subprocess.SubprocessError) as error:parser.exit(1,f'Error: {error}\n')

if __name__=='__main__':main()
