"""Export both ratios, then decode and inspect them with FFmpeg/ffprobe."""
import json
import subprocess
import tempfile
from pathlib import Path
from dx_studio.scaffold import create
from dx_studio.cli import cmd_build

def main():
    with tempfile.TemporaryDirectory(prefix='dx-smoke-') as d:
        cases=[('9:16',(1080,1920),'starter','none'),('16:9',(1920,1080),'starter','none'),
               ('9:16',(1080,1920),'explainer','bottom-band'),('16:9',(1920,1080),'explainer','left-half')]
        for ratio,size,template,presenter in cases:
            p=create(Path(d)/(ratio.replace(':','-')+'-'+presenter),template=template,format=ratio,presenter=presenter)
            cfg=json.loads((p/'project.json').read_text());cfg.update(duration=1,fps=12)
            (p/'project.json').write_text(json.dumps(cfg))
            # Keep the shortened fixture valid under caption timing preflight.
            captions=p/cfg.get('captions','captions.json')
            if captions.is_file():
                cues=json.loads(captions.read_text())
                cues=[dict(cue,show_end=min(cue.get('show_end',cue.get('end',cfg['duration'])),cfg['duration']))
                      for cue in cues if cue['start']<cfg['duration']]
                captions.write_text(json.dumps(cues))
            cmd_build(p)
            raw=subprocess.check_output(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(p/'video.mp4')])
            info=json.loads(raw);video=next(s for s in info['streams'] if s['codec_type']=='video')
            assert (video['width'],video['height'])==size
            assert abs(float(info['format']['duration'])-1)<.1
            assert any(s['codec_type']=='audio' for s in info['streams'])
            subprocess.run(['ffmpeg','-v','error','-i',str(p/'video.mp4'),'-f','null','-'],check=True)
            print('PASS',ratio,size,presenter,'duration, audio and full decode')
if __name__=='__main__':main()
