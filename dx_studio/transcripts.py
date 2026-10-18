"""Source-relative word timings with stable identities and explicit provenance."""
import copy
import json
import math
import uuid
from .paths import contained


def validate(transcript):
    if not isinstance(transcript,dict) or not isinstance(transcript.get('file'),str): raise ValueError('Transcript needs its source file')
    words=transcript.get('words')
    if not isinstance(words,list) or len(words)>10000: raise ValueError('Use at most 10,000 timed words per take')
    source_duration=transcript.get('source_duration',86400)
    if not isinstance(source_duration,(int,float)) or isinstance(source_duration,bool) or not math.isfinite(source_duration) or not 0<source_duration<=86400:raise ValueError('Invalid transcript source duration')
    seen=set();last=-1
    for word in words:
        if not isinstance(word,dict) or not isinstance(word.get('id'),str) or word['id'] in seen: raise ValueError('Timed words need unique IDs')
        if not isinstance(word.get('text'),str) or not word['text'].strip() or len(word['text'])>200: raise ValueError('Each word needs text of at most 200 characters')
        a,b=word.get('start'),word.get('end')
        if any(isinstance(x,bool) or not isinstance(x,(int,float)) or not math.isfinite(x) for x in (a,b)) or not 0<=a<b<=min(86400,source_duration+.05) or a<last: raise ValueError('Word times must be ordered, finite source seconds')
        last=a;seen.add(word['id'])


def prepare(project,take,text):
    """Accept standard word JSON; never pretend phrase timings are word alignment."""
    if not isinstance(text,str) or len(text)>2000000: raise ValueError('Use timed-word JSON smaller than 2 MB')
    data=json.loads(text)
    raw=data.get('words') if isinstance(data,dict) else data
    if not isinstance(raw,list) or not raw: raise ValueError('Use a words array with text, start and end for each word')
    words=[]
    for word in raw:
        if isinstance(word,list) and len(word)==3: word={'text':word[0],'start':word[1],'end':word[2]}
        if not isinstance(word,dict): raise ValueError('Invalid timed word')
        words.append({'id':'word_'+uuid.uuid4().hex[:12],'text':word.get('text',word.get('word','')),'start':word.get('start'),'end':word.get('end')})
    transcript={'file':take['file'],'method':'imported','words':words}
    validate(transcript)
    import soundfile as sf
    info=sf.info(contained(project.path,take['file']))
    if any(word['end']>info.duration+.05 for word in words): raise ValueError('Word timings extend beyond this source recording; use source-relative times')
    transcript['source_duration']=info.duration
    return transcript


def visible_words(take):
    tr=take.get('transcript') or {}
    if tr.get('file')!=take['file']: return []
    a,b=take['offset'],take['offset']+take['duration']
    return [dict(word,start=max(take['start'],take['start']+word['start']-a),
                 end=min(take['start']+take['duration'],take['start']+word['end']-a))
            for word in tr.get('words',[]) if word['end']>a and word['start']<b]


def captions_for(take,maximum=6):
    maximum=int(maximum)
    if not 1<=maximum<=12: raise ValueError('Choose 1–12 words per caption')
    words=visible_words(take)
    if not words: raise ValueError('Import or transcribe word timings for the current recording first')
    result=[];phrase=[]
    for word in words:
        phrase.append(word)
        if len(phrase)>=maximum or word['text'].endswith(('.', '?', '!')):
            result.append(phrase);phrase=[]
    if phrase: result.append(phrase)
    return [{'id':'caption_'+uuid.uuid4().hex[:12],'start':part[0]['start'],'end':part[-1]['end'],
             'text':' '.join(w['text'] for w in part),'hl':None,'word_highlight':True,
             'voice_id':take['id'],'word_ids':[w['id'] for w in part],
             'words':[dict(w) for w in part]} for part in result]


def speech_status():
    import importlib.util
    from pathlib import Path
    root=Path.home()/'.cache/dx_studio/asr/sherpa-onnx-nemo-parakeet-tdt-0.6b-v2-int8'
    files=('encoder.int8.onnx','decoder.int8.onnx','joiner.int8.onnx','tokens.txt')
    return {'installed':importlib.util.find_spec('sherpa_onnx') is not None,
            'model_ready':all((root/f).is_file() for f in files),'language':'English','model_folder':str(root)}


def recognize(project,take):
    """Optional cached offline adapter. It never installs packages or downloads a model."""
    status=speech_status()
    if not status['installed'] or not status['model_ready']: raise ValueError('Optional local speech support is not set up. Import timed-word JSON, or follow docs/TRANSCRIPTS.md to install speech support.')
    import sherpa_onnx
    import soundfile as sf
    import numpy as np
    from scipy.signal import resample_poly
    from pathlib import Path
    root=Path(status['model_folder'])
    rec=sherpa_onnx.OfflineRecognizer.from_transducer(encoder=str(root/'encoder.int8.onnx'),decoder=str(root/'decoder.int8.onnx'),joiner=str(root/'joiner.int8.onnx'),tokens=str(root/'tokens.txt'),model_type='nemo_transducer',num_threads=4)
    info=sf.info(contained(project.path,take['file']))
    if info.duration>3600: raise ValueError('Split recordings longer than an hour before transcription')
    a,sr=sf.read(contained(project.path,take['file']),dtype='float32')
    if a.ndim>1:a=a.mean(axis=1)
    divisor=math.gcd(sr,16000);a=resample_poly(a,16000//divisor,sr//divisor)
    stream=rec.create_stream();stream.accept_waveform(16000,np.asarray(a,dtype='float32'));rec.decode_stream(stream)
    words=[]
    for token,stamp in zip(stream.result.tokens,stream.result.timestamps):
        if token.startswith(' ') or not words: words.append({'text':token.strip(),'start':float(stamp),'end':float(stamp)+.08})
        else:words[-1]['text']+=token;words[-1]['end']=float(stamp)+.08
    for i,word in enumerate(words):word['end']=min(info.duration,words[i+1]['start'] if i+1<len(words) else word['end']+.27)
    words=[w for w in words if w['text'] and w['end']>w['start']]
    result=prepare(project,take,json.dumps(words));result['method']='local-asr';return result
