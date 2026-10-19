"""Inspect the completed temporary MP4 before publishing over a previous master."""
import json
import subprocess
from fractions import Fraction


def verify(path,options):
    result=subprocess.run(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(path)],capture_output=True,text=True,check=True,timeout=60)
    data=json.loads(result.stdout)
    video=next((s for s in data.get('streams',[]) if s.get('codec_type')=='video'),None)
    audio=next((s for s in data.get('streams',[]) if s.get('codec_type')=='audio'),None)
    if not video or not audio:raise ValueError('The encoded MP4 is missing video or audio. Your previous export is kept.')
    if (video.get('width'),video.get('height'))!=(options['width'],options['height']):raise ValueError('The encoded video dimensions do not match the export profile.')
    if abs(float(Fraction(video.get('avg_frame_rate','0')))-options['fps'])>.01:raise ValueError('The encoded frame rate does not match the export profile.')
    duration=float(data.get('format',{}).get('duration',0))
    if abs(duration-options['duration'])>1/options['fps']+.05:raise ValueError('The encoded video duration does not match the export range.')
    return {'duration':duration,'width':video['width'],'height':video['height'],'fps':options['fps']}
